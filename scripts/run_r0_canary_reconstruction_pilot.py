#!/usr/bin/env python3
"""R0B -- canary reconstruction validation pilot.

Validation only. The held-out R1 main test set is generated and hashed as a
commitment but never rendered or scored.

Scale note. Every estimator here depends on the data only through the
sufficient statistic b = A^T y, so the pilot simulates in the coefficient
dimension rather than in the row dimension. R0_G12 checks that reduction
against a full-space simulation; without it the whole design would rest on an
unverified claim.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import resource
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from phrt.config import load_registry
from phrt.geometry.raymap import read
from phrt.geometry.sampling import common_count, stratified_subsample
from phrt.inverse.reduced import reduce_operator
from phrt.inverse.ridge import ridge_from_statistic
from phrt.inverse.smoothness import (temporal_difference_operator,
                                     tikhonov_from_statistic)
from phrt.inverse.state_space import (random_walk_precision,
                                      state_space_from_statistic)
from phrt.inverse.tsvd import tsvd_from_statistic
from phrt.inverse.wiener import fit_gaussian_prior, wiener_from_statistic
from phrt.io.manifests import RunManifest, make_run_id
from phrt.io.tables import write_table
from phrt.metrics.age_error import freeze_eta
from phrt.metrics.calibration import coverage_rows
from phrt.metrics.data_prior_split import subspace_errors
from phrt.metrics.scoring import AgeScorer, evaluation_grid
from phrt.metrics.stable_depth import anchored_depth_surface
from phrt.operators.physical import PhysicalOperator
from phrt.sources.bank import BankContext, build_split, disjointness_report
from phrt.sources.near_null import (amplitude_for_target,
                                    direction_for_separation,
                                    realized_separation)
from phrt.sources.offgrid import projection_residual
from phrt.sources.physical_basis import PhysicalBasis
from scipy import stats

FREEZE = ROOT / "artifacts" / "configs" / "R0_CANARY_RECONSTRUCTION_PILOT_FREEZE.json"
MAN_DIR = ROOT / "artifacts" / "manifests"
ARMS = ("DIRECT_PHYSICAL", "RESOLVED_PHYSICAL", "UNRESOLVED_IMAGE", "TOTAL_FLUX")
PRIOR_FIT = ("single_orbiting_hotspot", "two_independent_hotspots",
             "rotating_asymmetric_crescent", "correlated_extended_field")
OOD = "moving_flare_birth_decay"
ALL_PHYS = PRIOR_FIT + (OOD,)


def peak_mb() -> float:
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0


def build_setup(fz: dict, scale: float):
    """Operators, basis and the age-window stack, all from the freeze."""
    obs = fz["observation"]
    n_rays = max(64, int(obs["rays_per_order"] * scale))
    rng = np.random.default_rng(int(obs["subsample_seed"]))
    maps = [read(ROOT / "artifacts" / "raymaps" / f"a050_i050_n{n}_core.h5")
            for n in fz["physical_model"]["orders"]]
    base = common_count([stratified_subsample(m, n_rays, rng) for m in maps], rng)
    t_obs = np.asarray(obs["observer_times_M"], float)
    r_in = min(float(o.source_r.min()) for o in base)
    r_out = max(float(o.source_r.max()) for o in base)
    t_lo, t_hi = float(obs["basis_t_min"]), float(obs["basis_t_max"])
    basis = PhysicalBasis(r_in, r_out, t_lo, t_hi)
    kw = dict(observer_times=t_obs, design=basis.design, dimension=basis.dimension)
    ops = {
        "RESOLVED_PHYSICAL": PhysicalOperator(orders=base, **kw),
        "DIRECT_PHYSICAL": PhysicalOperator(orders=[base[0]], **kw),
        "UNRESOLVED_IMAGE": PhysicalOperator(orders=base,
                                             mixer=np.ones((1, len(base))), **kw),
        "TOTAL_FLUX": PhysicalOperator(orders=base, collapse="total_flux", **kw),
    }
    return base, basis, t_obs, ops


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scale", type=float, default=1.0,
                    help="fraction of the frozen counts, for a dry run")
    ap.add_argument("--ray-scale", type=float, default=1.0)
    args = ap.parse_args()

    t0 = time.time()
    fz = json.loads(FREEZE.read_text())
    freeze_hash = hashlib.sha256(FREEZE.read_bytes()).hexdigest()
    reg = load_registry()
    counts = fz["pilot_counts"]
    master = int(fz["seeds"]["master"])
    streams = fz["seeds"]["streams"]
    snr_grid = [float(s) for s in fz["physical_model"]["snr0_grid"]]
    rho = float(fz["subspaces"]["rho"])
    sc = args.scale

    def n_of(key, default):
        return max(1, int(round(counts.get(key, default) * sc)))

    base, basis, t_obs, ops = build_setup(fz, args.ray_scale)
    d = basis.dimension
    # A declared structured grid, shared by every arm. Scoring on one arm's ray
    # coordinates would privilege that arm in the very comparison being made.
    rq, pq, tq = evaluation_grid(basis.r_inner, basis.r_outer,
                                 basis.t_min, basis.t_max)
    design_eval = basis.design(rq, pq, tq)
    print(f"class d={d}, evaluation points={rq.size}, "
          f"resolved rows={ops['RESOLVED_PHYSICAL'].shape[0]}")

    red = {a: reduce_operator(ops[a].to_dense(), a) for a in ARMS}
    print("operators reduced: " + ", ".join(f"{a}:k={red[a].s.size}" for a in ARMS))

    # ---- age windows, on the frozen common grid ---------------------------
    h = float(fz["source_families"]["resolution_bounds"].get(
        "probe_half_width_M", 3.0))
    step = float(fz["metrics"]["age_grid_step_M"])
    ages = np.arange(0.0, float(fz["metrics"]["age_grid_max_M"]) + 1e-9, step)
    t_sc = time.time()
    scorer = AgeScorer.build(design_eval, tq, ages, h)
    Wn = scorer.weights
    print(f"age scorer built ({ages.size} ages) in {time.time() - t_sc:.0f}s")

    ctx = BankContext(fz["source_families"]["resolved_ranges"],
                      (basis.r_inner, basis.r_outer), (basis.t_min, basis.t_max))

    # ---- source bank -------------------------------------------------------
    bank = {}
    for fam in PRIOR_FIT:
        bank[("prior_fit_train", fam)] = build_split(
            fam, "prior_fit_train", n_of("prior_fit_train_per_family", 512),
            master, streams["prior_fit_train"], ctx)
        bank[("validation_in_class", fam)] = build_split(
            fam, "validation_in_class",
            n_of("validation_in_class_per_prior_fit_family", 128),
            master, streams["validation_in_class"], ctx)
    for fam in ALL_PHYS:
        bank[("validation_off_grid", fam)] = build_split(
            fam, "validation_off_grid",
            n_of("validation_off_grid_per_physical_family", 64),
            master, streams["validation_off_grid"], ctx, off_grid=True)
    bank[("validation_ood", OOD)] = build_split(
        OOD, "validation_ood", n_of("validation_ood_total", 256),
        master, streams["validation_ood"], ctx)
    # future main test: generated and hashed, never rendered or scored
    future = {}
    for fam in ALL_PHYS:
        future[fam] = build_split(fam, "future_main_test", 64, master,
                                  streams["future_main_test"], ctx)

    groups = {}
    for (split, fam), mv in bank.items():
        groups.setdefault(split, []).extend(mv)
    groups["future_main_test"] = [m for v in future.values() for m in v]
    disj = disjointness_report(groups)
    if not disj["disjoint"]:
        print("STOP: DATA_SPLIT_LEAKAGE", disj["pairwise_overlap"])
        return 3
    print("split sizes: " + ", ".join(f"{k}={len(v)}" for k, v in groups.items()))

    # ---- render truths -----------------------------------------------------
    def render(movies):
        return np.array([m(rq, pq, tq) for m in movies])

    t_render = time.time()
    truths = {k: render(v) for k, v in bank.items()}
    print(f"rendered {sum(v.shape[0] for v in truths.values())} truths "
          f"in {time.time() - t_render:.0f}s")
    for k, v in truths.items():
        if v.min() < 0:
            print(f"STOP: IMPLEMENTATION_DEFECT negative intensity in {k}")
            return 4

    # off-grid truths must actually be off grid
    og_rows = []
    for fam in ALL_PHYS:
        vals = truths[("validation_off_grid", fam)]
        pr = [projection_residual(v, design_eval) for v in vals[:24]]
        og_rows.append({
            "family": fam,
            "median_projection_residual":
                float(np.median([x["relative_projection_residual"] for x in pr])),
            "median_projection_residual_structure":
                float(np.median([x["relative_projection_residual_structure"]
                                 for x in pr])),
            "median_fluctuation_fraction":
                float(np.median([x["fluctuation_fraction"] for x in pr])),
            "degenerate_constant_fraction":
                float(np.mean([x["is_degenerate_constant"] for x in pr])),
            "note": "the structure residual is the one that characterises the "
                    "regime; the plain relative residual is diluted by the "
                    "in-class positive baseline"})
    print("off-grid structure residuals: "
          + ", ".join(f"{r['family']}={r['median_projection_residual_structure']:.3f}"
                      for r in og_rows))

    # ---- eta, frozen on the prior-fit split only ---------------------------
    pf = np.concatenate([truths[("prior_fit_train", f)] for f in PRIOR_FIT])
    pf_norms = np.sqrt(np.einsum("ap,np->na", Wn ** 2, pf ** 2))
    eta = freeze_eta(pf_norms.ravel())
    print(f"eta frozen at {eta:.6g} from the prior-fit split")

    # ---- Gaussian prior, fitted on prior-fit truths only -------------------
    pf_coef = np.linalg.lstsq(design_eval, pf.T, rcond=None)[0].T
    priors = {sh: fit_gaussian_prior(pf_coef, float(sh))
              for sh in fz["hyperparameter_grids"]["WIENER_GAUSSIAN"]["grid"]}

    LtL = temporal_difference_operator(basis.n_radial, basis.n_azimuthal,
                                       basis.n_temporal)
    LtL = LtL.T @ LtL
    ss_prec = {q: random_walk_precision(basis.n_radial, basis.n_azimuthal,
                                        basis.n_temporal, float(q))
               for q in fz["hyperparameter_grids"]["LINEAR_STATE_SPACE"]["process_noise"]}

    payload = {"freeze": fz, "freeze_hash": freeze_hash, "reg": reg,
               "ops": ops, "red": red, "basis": basis, "design": design_eval,
               "truths": truths, "bank": bank, "future": future, "eta": eta,
               "Wn": Wn, "ages": ages, "scorer": scorer,
               "prior_fit_values": pf,
               "priors": priors, "LtL": LtL,
               "ss_prec": ss_prec, "snr_grid": snr_grid, "rho": rho,
               "master": master, "streams": streams, "disj": disj,
               "og_rows": og_rows, "counts": counts, "scale": sc,
               "t0": t0, "n_eval": rq.size}
    from phrt.pilot_r0 import run_pilot
    return run_pilot(payload)


if __name__ == "__main__":
    raise SystemExit(main())
