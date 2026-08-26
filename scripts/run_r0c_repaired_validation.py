#!/usr/bin/env python3
"""R0C -- repaired-source and calibrated-uncertainty validation.

Validation only. The held-out main test was hashed at registration under the
corrected generator semantics and is neither rendered into data nor scored here.

What changed from the pilot, all of it declared in the R0C freeze before this
ran: in-class truths are exactly in the span of C224, the regime axis separates
representation mismatch from family shift, every fitted quantity is refitted on
the repaired bank, the primary endpoint is the validation-selected (0.25, 0.95)
cell, and the posterior covariance carries one scalar per estimator family
fitted on its own split.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from phrt.attestation import attest
from phrt.config import load_registry
from phrt.geometry.raymap import read
from phrt.geometry.sampling import common_count, stratified_subsample
from phrt.governance import r0_provenance
from phrt.inverse.reduced import reduce_operator
from phrt.inverse.smoothness import temporal_difference_operator
from phrt.inverse.state_space import random_walk_precision
from phrt.inverse.wiener import fit_gaussian_prior
from phrt.metrics.age_error import freeze_eta
from phrt.metrics.scoring import AgeScorer, evaluation_grid
from phrt.operators.physical import PhysicalOperator
from phrt.pilot_r0c import coefficients_for, run
from phrt.sources.bank import BankContext, build_split, disjointness_report
from phrt.sources.in_span import (IN_SPAN_TOLERANCE, constant_coefficients,
                                  in_span_movie, in_span_residual)
from phrt.sources.physical_basis import PhysicalBasis

FREEZE = ROOT / "artifacts" / "configs" / "R0C_REPAIRED_SOURCE_AND_CALIBRATION_FREEZE.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scale", type=float, default=1.0)
    ap.add_argument("--ray-scale", type=float, default=1.0)
    args = ap.parse_args()

    t0 = time.time()
    started = time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime())
    att = attest([FREEZE])
    if not att.get("preregistered"):
        print("STOP: R0C must run against a committed freeze in a clean tree. "
              f"tracked changes {att.get('n_tracked_changes')}, untracked "
              f"{att.get('n_untracked')}, freeze committed "
              f"{att['files'][0]['committed_at_execution_commit']}")
        return 2

    fz = json.loads(FREEZE.read_text())
    fh = hashlib.sha256(FREEZE.read_bytes()).hexdigest()
    reg = load_registry()
    sc, obs = fz["source_class"], fz["observation"]
    sca = args.scale

    def n_of(v):
        return max(8, int(round(v * sca)))

    # ---- operators ---------------------------------------------------------
    n_rays = max(64, int(obs["rays_per_order"] * args.ray_scale))
    rng = np.random.default_rng(int(obs["subsample_seed"]))
    maps = [read(ROOT / "artifacts" / "raymaps" / f"a050_i050_n{n}_core.h5")
            for n in fz["physical_model"]["orders"]]
    base = common_count([stratified_subsample(m, n_rays, rng) for m in maps], rng)
    t_obs = np.asarray(obs["observer_times_M"], float)
    basis = PhysicalBasis(*sc["radial_support_M"], *sc["temporal_support_M"])
    kw = dict(observer_times=t_obs, design=basis.design, dimension=basis.dimension)
    ops = {
        "RESOLVED_PHYSICAL": PhysicalOperator(orders=base, **kw),
        "DIRECT_PHYSICAL": PhysicalOperator(orders=[base[0]], **kw),
        "UNRESOLVED_IMAGE": PhysicalOperator(orders=base,
                                             mixer=np.ones((1, len(base))), **kw),
        "TOTAL_FLUX": PhysicalOperator(orders=base, collapse="total_flux", **kw),
    }
    red = {a: reduce_operator(op.to_dense(), a) for a, op in ops.items()}
    rq, pq, tq = evaluation_grid(basis.r_inner, basis.r_outer,
                                 basis.t_min, basis.t_max)
    design = basis.design(rq, pq, tq)
    const_coef, const_resid = constant_coefficients(design)
    print(f"class d={basis.dimension}, evaluation points={rq.size}, "
          f"resolved rows={ops['RESOLVED_PHYSICAL'].shape[0]}, "
          f"constant-in-class residual {const_resid:.2e}")

    ages = np.arange(0.0, float(fz["metrics"]["age_grid_max_M"]) + 1e-9,
                     float(fz["metrics"]["age_grid_step_M"]))
    h_probe = float(fz["source_families"]["resolution_bounds"]
                    ["probe_half_width_M"])
    scorer = AgeScorer.build(design, tq, ages, h_probe)
    ctx = BankContext(fz["source_families"]["resolved_ranges"],
                      (basis.r_inner, basis.r_outer), (basis.t_min, basis.t_max))

    # ---- banks -------------------------------------------------------------
    master = int(fz["seeds"]["master"])
    streams = fz["seeds"]["streams"]
    regimes = fz["source_regimes"]
    splits = fz["splits"]

    def make(regime, split, offset, per_family):
        spec = regimes[regime]
        out = []
        for fam in spec["families"]:
            movies = build_split(fam, f"{split}:{regime}", n_of(per_family),
                                 master, offset, ctx,
                                 off_grid=spec["off_grid"])
            if spec["in_span"]:
                movies = [in_span_movie(m, basis, rq, pq, tq, const_coef)
                          for m in movies]
                for m in movies:
                    m.split = f"{split}:{regime}"
            out.extend(movies)
        return out

    bank = {}
    bank[("prior_fit_train", "IN_CLASS_ID")] = make(
        "IN_CLASS_ID", "prior_fit_train", streams["prior_fit_train"],
        splits["prior_fit_train"]["per_family"])
    for r in regimes:
        bank[("uncertainty_calibration", r)] = make(
            r, "uncertainty_calibration", streams["uncertainty_calibration"],
            splits["uncertainty_calibration"]["per_regime"])
        bank[("repair_validation", r)] = make(
            r, "repair_validation", streams["repair_validation"],
            splits["repair_validation"]["per_family_by_regime"][r])

    groups = {}
    for (split, r), mv in bank.items():
        groups.setdefault(f"{split}:{r}", []).extend(mv)
    disj = disjointness_report(groups)
    if not disj["disjoint"]:
        print("STOP: DATA_SPLIT_LEAKAGE", disj["pairwise_overlap"])
        return 3
    print("splits: " + ", ".join(f"{k}={len(v)}" for k, v in groups.items()))

    # ---- render, and check in-span membership where it is claimed ----------
    rendered = {k: np.array([m(rq, pq, tq) for m in v]) for k, v in bank.items()}
    for k, v in rendered.items():
        if v.min() < 0:
            print(f"STOP: IMPLEMENTATION_DEFECT negative intensity in {k}")
            return 4
    r2 = np.linspace(basis.r_inner, basis.r_outer, 257)
    p2 = np.linspace(0.0, 2 * np.pi, 257)
    t2 = np.linspace(basis.t_min, basis.t_max, 257)
    D2 = basis.design(r2, p2, t2)
    devs, n_in_span = [0.0], 0
    for (split, r), mv in bank.items():
        if not regimes[r]["in_span"]:
            continue
        for m in mv:
            devs.append(in_span_residual(m, D2, r2, p2, t2))
            n_in_span += 1
    worst_in_span = float(max(devs))
    print(f"in-span membership: worst relative residual {worst_in_span:.2e} "
          f"over {n_in_span} truths, off the projection grid")
    if worst_in_span > IN_SPAN_TOLERANCE:
        print(f"STOP: R0_G14 in-span membership {worst_in_span:.2e} exceeds "
              f"{IN_SPAN_TOLERANCE:g}")
        return 5

    # ---- refits, all on the repaired bank ----------------------------------
    pf = rendered[("prior_fit_train", "IN_CLASS_ID")]
    pf_coef = coefficients_for(bank[("prior_fit_train", "IN_CLASS_ID")], pf, design)
    Wn = scorer.weights
    pf_norms = np.sqrt(np.einsum("ap,np->na", Wn ** 2, pf ** 2))
    eta = freeze_eta(pf_norms.ravel())
    _, s_pf, m_pf = scorer.truth_terms(pf)
    tn = np.sqrt(np.maximum(s_pf - m_pf ** 2
                            / np.maximum(scorer.h, 1e-300), 0.0))
    pos = tn[tn > 0]
    eta_struct = float(0.05 * np.median(pos)) if pos.size else 1e-12
    print(f"refit on the repaired bank: eta {eta:.6g}, eta_struct {eta_struct:.6g}")

    priors = {sh: fit_gaussian_prior(pf_coef, float(sh))
              for sh in fz["hyperparameter_grids"]["WIENER_GAUSSIAN"]["grid"]}
    LtL = temporal_difference_operator(basis.n_radial, basis.n_azimuthal,
                                       basis.n_temporal)
    LtL = LtL.T @ LtL
    ss_prec = {q: random_walk_precision(basis.n_radial, basis.n_azimuthal,
                                        basis.n_temporal, float(q))
               for q in fz["hyperparameter_grids"]["LINEAR_STATE_SPACE"]
               ["process_noise"]}

    truth_vals, truth_coef, terms = {}, {}, {}
    for r in regimes:
        v = rendered[("repair_validation", r)]
        truth_vals[r] = v
        truth_coef[r] = coefficients_for(bank[("repair_validation", r)], v, design)
        p_, s_, m_ = scorer.truth_terms(v)
        terms[r] = (p_, s_, m_, np.sqrt(np.maximum(s_, 0.0)))
    cal_vals = np.concatenate([rendered[("uncertainty_calibration", r)]
                               for r in regimes])
    cal_movies = [m for r in regimes
                  for m in bank[("uncertainty_calibration", r)]]
    cal_coef = coefficients_for(cal_movies, cal_vals, design)

    # a mid-grid hyperparameter for the calibration fit, declared not tuned
    cal_hp = {
        "WIENER_GAUSSIAN": float(
            fz["hyperparameter_grids"]["WIENER_GAUSSIAN"]["grid"][
                len(fz["hyperparameter_grids"]["WIENER_GAUSSIAN"]["grid"]) // 2]),
        "LINEAR_STATE_SPACE": float(
            fz["hyperparameter_grids"]["LINEAR_STATE_SPACE"]["process_noise"][
                len(fz["hyperparameter_grids"]["LINEAR_STATE_SPACE"]
                    ["process_noise"]) // 2]),
    }

    P = {"t0": t0, "started": started, "attestation": att, "freeze": fz,
         "freeze_hash": fh, "reg": reg, "ages": ages, "scorer": scorer,
         "design": design, "red": red, "rho": float(fz["subspaces"]["rho"]),
         "snr_grid": [float(s) for s in fz["physical_model"]["snr0_grid"]],
         "eta": eta, "eta_struct": eta_struct, "priors": priors, "LtL": LtL,
         "ss_prec": ss_prec, "truth_vals": truth_vals, "truth_coef": truth_coef,
         "terms": terms, "regimes": list(regimes), "master": master,
         "streams": streams, "dimension": basis.dimension,
         "cal_coef": cal_coef, "cal_vals": cal_vals,
         "calibration_hyperparameter": cal_hp,
         "n_draws": max(1, int(round(4 * sca))),
         "disj": disj, "worst_in_span": worst_in_span,
         "in_span_tol": IN_SPAN_TOLERANCE, "n_in_span": n_in_span,
         "regime_counts": {k: len(v) for k, v in groups.items()},
         "provenance": r0_provenance()}
    return run(P)


if __name__ == "__main__":
    raise SystemExit(main())
