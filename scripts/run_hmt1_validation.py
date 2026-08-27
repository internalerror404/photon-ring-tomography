#!/usr/bin/env python3
"""HMT-1 validation: historical feature and contrast tomography.

Under HMT1_VALIDATION_FREEZE_V0. The endpoint is not pixel error. It is whether
a compressed physical description of the past survives the operator: where a
feature was, how it moved, how bright it was, when it appeared and faded.

The source is a positive axisymmetric background carrying a signed fluctuation.
The operator sees the total emissivity; the reconstruction sees whatever is left
after a background obtained per regime, and only the fluctuation is inverted.
That split is exact by construction -- the fluctuation has zero azimuthal mean at
every radius and age, and every m = 0 direction is projected out of the contrast
class -- so a background error cannot hide inside a feature result.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from phrt.numerics import pin, record as numerics_record, require_single_threaded

pin()

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from phrt.attestation import attest  # noqa: E402
from phrt.config import load_registry  # noqa: E402
from phrt.geometry.raymap import read  # noqa: E402
from phrt.geometry.sampling import common_count, stratified_subsample  # noqa: E402
from phrt.inverse.background import (axisymmetric_design, background_error,  # noqa: E402
                                     estimate_from_field)
from phrt.io.manifests import Gate, RunManifest, gate_from_tolerance, make_run_id, merge_gate_file  # noqa: E402
from phrt.io.tables import write_table  # noqa: E402
from phrt.metrics.features import (aggregate, extract, generative_peak_error,  # noqa: E402
                                   normalized_errors)
from phrt.operators.physical import PhysicalOperator  # noqa: E402
from phrt.sources.contrast import FAMILIES, OFF_MANIFOLD, build  # noqa: E402
from phrt.sources.localized_basis import LocalizedBasis  # noqa: E402
from phrt.sources.physical_basis import PhysicalBasis  # noqa: E402

FZ = ROOT / "artifacts" / "configs" / "HMT1_VALIDATION_FREEZE_V0.json"
R1 = ROOT / "artifacts" / "configs" / "R1_MAIN_FREEZE.json"
PARAM_KEYS = ("radial", "angular", "amplitude", "mode_m1", "mode_m2")
# The pattern families have m equally good maxima; folding the azimuthal
# comparison by m is a property of the source, not a tolerance.
M_FOLD = {"m1_rotating_crescent": 1, "m2_structural_mode": 2}


def truth_seed(family, split, regime, i, seed):
    payload = json.dumps({"family": family, "split": split, "regime": regime,
                          "n": 8, "seed": seed, "model": "contrast"},
                         sort_keys=True).encode()
    return int(hashlib.sha256(payload + f"|{i}".encode()).hexdigest()[:16], 16) % (2 ** 63)


def commitment(family, split, regime, seed):
    return hashlib.sha256(json.dumps(
        {"family": family, "split": split, "regime": regime, "n": 8,
         "seed": seed, "model": "contrast"}, sort_keys=True).encode()).hexdigest()


def unit_source(b):
    u = np.zeros(b.dimension)
    for a in range(b.n_radial):
        u[(a * b.n_azimuthal + 0) * b.n_temporal + 0] = 1.0
    return u


def spectral_filter(kind, s, scale, hyper):
    sc = s * scale
    if kind == "TSVD":
        keep = sc >= hyper * sc.max()
        f = np.zeros_like(sc)
        f[keep] = 1.0 / sc[keep]
        return f
    return sc / (sc ** 2 + hyper * sc.max() ** 2)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--regimes", default="")
    ap.add_argument("--families", default="")
    args = ap.parse_args()
    t0 = time.time()
    numerics = require_single_threaded()
    started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    fz = json.loads(FZ.read_text())
    r1 = json.loads(R1.read_text())
    reg = load_registry()
    seeds = fz["seeds"]
    per_cell = fz["counts"]["truths_per_family_split_regime"]
    n_draws = fz["counts"]["noise_draws_per_truth"]
    arms_wanted = fz["arms"]
    snr_p, snr_s = fz["snr"]["primary"], fz["snr"]["secondary"]
    span = fz["primary_endpoints"]["stable_feature_interval"]
    boot = fz["primary_endpoints"]["old_band_feature_error"]["bootstrap"]
    old_b = float(fz["primary_endpoints"]["old_band_feature_error"]["old_band_boundary_M"])
    M = fz["pass_criteria"]["material_benefit_under_both_classical_estimators"]
    eg = fz["evaluation_grid"]
    lim = fz["resource_limits"]

    spin = float(fz["geometry"]["a_star"])
    r_in, r_out = (float(r1["physical_model"]["r_inner_M"]),
                   float(r1["physical_model"]["r_outer_M"]))
    t_lo, t_hi = (float(r1["observation"]["basis_t_min"]),
                  float(r1["observation"]["basis_t_max"]))
    t_obs = np.asarray(r1["observation"]["observer_times_M"], float)
    NR, NP, NT = eg["n_radial"], eg["n_azimuthal"], eg["n_temporal"]
    r_axis = np.exp(np.linspace(np.log(r_in), np.log(r_out), NR))
    phi_axis = np.linspace(0.0, 2 * np.pi, NP, endpoint=False)
    t_axis = np.linspace(t_lo, t_hi, NT)
    Rg, Pg, Tg = np.meshgrid(r_axis, phi_axis, t_axis, indexing="ij")
    gr, gp, gt = Rg.ravel(), Pg.ravel(), Tg.ravel()
    t_index = np.tile(np.arange(NT), NR * NP)
    ages = np.arange(0.0, float(r1["metrics"]["age_grid_max_M"]) + 1e-9,
                     float(span["age_grid_step_M"]))
    half = float(span["probe_half_width_M"])
    old_mask = ages >= old_b
    obs_span = float(t_obs.max() - t_obs.min())
    r_span = r_out - r_in

    regimes = ([x for x in args.regimes.split(",") if x] or fz["counts"]["regimes"])
    fams = ([x for x in args.families.split(",") if x] or FAMILIES)

    committed = fz["split_rule"]["commitments"]
    recomputed = {f"{f}|{s}|{g}": commitment(f, s, g, seeds["bank_seed"])
                  for f in FAMILIES for s in fz["counts"]["splits"]
                  for g in fz["counts"]["regimes"]}
    commitments_ok = recomputed == committed

    rng = np.random.default_rng(seeds["subsample_seed"])
    base = common_count([stratified_subsample(
        read(ROOT / "artifacts" / "raymaps" / f"a050_i050_n{n}_core.h5"),
        int(r1["observation"]["rays_per_order"]), rng)
        for n in r1["physical_model"]["orders"]], rng)
    n_orders, n_rays = len(base), base[0].n_rays

    # contrast class: every m = 0 direction removed
    basis = LocalizedBasis(r_in, r_out, t_lo, t_hi, 4, 7, 16)
    keep = np.array([lab["azimuthal_mode"] != 0 for lab in basis.labels()])
    D_full = basis.design(gr, gp, gt)
    D = D_full[:, keep]
    bdes = axisymmetric_design(gr, gt, r_in, r_out, t_min=t_lo, t_max=t_hi)

    run_id = make_run_id("HMT1", reg.sha256)
    run_dir = ROOT / "artifacts" / "runs" / run_id
    (run_dir / "tables").mkdir(parents=True, exist_ok=True)
    (run_dir / "gates").mkdir(parents=True, exist_ok=True)
    man = RunManifest(run_id=run_id, experiment_id="HMT1_VALIDATION", seeds=seeds,
                      started_at=started, attestation=attest([FZ, R1]),
                      extra={"stage": "validation", "regimes": regimes,
                             "families": fams, "arms": arms_wanted,
                             "contrast_class_dimension": int(keep.sum()),
                             "run_dir": str(run_dir.relative_to(ROOT)),
                             "numerics": numerics_record()})
    man.add_input(FZ)

    # ---- operators, one set for every regime -------------------------------
    ones = np.ones((1, n_orders))
    cfg = {"DIRECT_PHYSICAL": dict(orders=[base[0]]),
           "RESOLVED_PHYSICAL": dict(orders=base),
           "UNRESOLVED_IMAGE": dict(orders=base, mixer=ones),
           "TOTAL_FLUX": dict(orders=base, mixer=ones, collapse="total_flux")}
    ops = {n: PhysicalOperator(design=lambda r, p, t: basis.design(r, p, t)[:, keep],
                               dimension=int(keep.sum()), observer_times=t_obs,
                               **c) for n, c in cfg.items() if n in arms_wanted}
    bops = {n: PhysicalOperator(
        design=lambda r, p, t: axisymmetric_design(r, t, r_in, r_out,
                                                   t_min=t_lo, t_max=t_hi),
        dimension=bdes.shape[1], observer_times=t_obs, **c)
        for n, c in cfg.items() if n in arms_wanted}

    ref_basis = PhysicalBasis(r_in, r_out, t_lo, t_hi, 4, 7, 8)
    s_ref = float(np.sqrt(np.mean(PhysicalOperator(
        orders=[base[0]], observer_times=t_obs, design=ref_basis.design,
        dimension=ref_basis.dimension).matvec(unit_source(ref_basis)) ** 2)))

    worst = {"adjoint": 0.0, "identity": 0.0, "zero_mean": 0.0,
             "azimuthal": 0.0, "positivity": 0.0, "background_floor": 0.0,
             "determinism": 0.0, "generative_radial_cells": 0.0,
             "generative_azimuthal_cells": 0.0}
    svd = {}
    for aname, op in ops.items():
        U, s, Vt = np.linalg.svd(op.to_dense(), full_matrices=False)
        svd[aname] = (U, s, Vt)
        x = np.random.default_rng(5).normal(size=op.shape[1])
        y = np.random.default_rng(6).normal(size=op.shape[0])
        worst["adjoint"] = max(worst["adjoint"],
                               abs(float(y @ op.matvec(x)) - float(x @ op.rmatvec(y)))
                               / max(abs(float(y @ op.matvec(x))), 1e-300))
        got = op.forward_analytic(
            lambda r, p, t, _x=x: basis.design(r, p, t)[:, keep] @ _x)
        want = op.matvec(x)
        worst["identity"] = max(worst["identity"],
                                float(np.abs(got - want).max())
                                / max(float(np.abs(want).max()), 1e-300))
    print(f"operators ready, contrast class {int(keep.sum())}, "
          f"{time.time() - t0:.0f}s")

    bank_rows, sel_rows, score_rows, bgerr_rows, joint_rows = [], [], [], [], []
    grids = {"TSVD": [10 ** (-k / 2) for k in range(15)],
             "RIDGE_IDENTITY": [10 ** (-k / 2) for k in range(21)]}

    nrng = np.random.default_rng(seeds["noise_seed"])
    all_keys = [(f, s, g, i) for g in regimes for f in fams
                for s in fz["counts"]["splits"] for i in range(per_cell)]
    Z = {k: [nrng.normal(size=(n_orders, n_rays, t_obs.size))
             for _ in range(n_draws)] for k in all_keys}

    truths = {}
    for k in all_keys:
        family, split, regime, i = k
        trng = np.random.default_rng(truth_seed(*k, seeds["bank_seed"]))
        b, fluct, traj, dj, bg, diag = build(trng, family, spin, r_in, r_out,
                                             gr, gp, gt, t_index, NT)
        truths[k] = {"b": b, "fluct": fluct, "traj": traj, "dj": dj, "bg": bg,
                     "diag": diag}
        worst["zero_mean"] = max(worst["zero_mean"], diag["zero_mean_max_abs"])
        worst["azimuthal"] = max(worst["azimuthal"], diag["azimuthal_mean_max_abs"])
        worst["positivity"] = max(worst["positivity"], max(0.0, -diag["min_total"]))
        worst["background_floor"] = max(worst["background_floor"],
                                        max(0.0, 1e-6 - diag["min_background"]))
        f1 = extract(dj, gt, ages, r_axis, phi_axis, half)
        f2 = extract(dj, gt, ages, r_axis, phi_axis, half)
        worst["determinism"] = max(worst["determinism"], max(
            float(np.abs(np.asarray(f1[c]) - np.asarray(f2[c])).max())
            for c in ("r_h", "phi_h", "A_h", "a_m1", "a_m2")))
        truths[k]["features"] = f1
        gerr = generative_peak_error(traj, ages, f1, r_axis, phi_axis,
                                     m_fold=M_FOLD.get(family, 1))
        for a, b_ in (("generative_radial_cells", "radial_cells"),
                      ("generative_azimuthal_cells", "azimuthal_cells")):
            if np.isfinite(gerr[b_]):
                worst[a] = max(worst[a], gerr[b_])
        bank_rows.append({"family": family, "split": split, "regime": regime,
                          "generative_radial_cells": gerr["radial_cells"],
                          "generative_azimuthal_cells": gerr["azimuthal_cells"],
                          "generative_ages_scored": gerr["n_ages_scored"],
                          "index": i, "truth_seed": truth_seed(*k, seeds["bank_seed"]),
                          "contrast_fraction": diag["contrast_fraction"],
                          "peak_fraction_of_background":
                              diag["achieved_peak_fraction_of_background"],
                          "min_total": diag["min_total"],
                          "min_background": diag["min_background"],
                          "zero_mean_max_abs": diag["zero_mean_max_abs"],
                          "azimuthal_mean_max_abs": diag["azimuthal_mean_max_abs"],
                          "positivity_scale": diag["positivity_scale"]})
    print(f"banks built, {len(truths)} truths, {time.time() - t0:.0f}s")

    state = dict(fz=fz, man=man, run_dir=run_dir, run_id=run_id, reg=reg, t0=t0,
                 ops=ops, bops=bops, svd=svd, D=D, bdes=bdes, s_ref=s_ref,
                 truths=truths, Z=Z, ages=ages, half=half, old_mask=old_mask,
                 r_axis=r_axis, phi_axis=phi_axis, gt=gt, gr=gr, obs_span=obs_span,
                 r_span=r_span, grids=grids, snr_p=snr_p, snr_s=snr_s,
                 regimes=regimes, fams=fams, arms=arms_wanted, boot=boot, M=M,
                 span=span, seeds=seeds, worst=worst, numerics=numerics, lim=lim,
                 commitments_ok=commitments_ok, bank_rows=bank_rows,
                 sel_rows=sel_rows, score_rows=score_rows, bgerr_rows=bgerr_rows,
                 joint_rows=joint_rows, n_draws=n_draws, keep=keep, basis=basis)
    from run_hmt1_score import score_and_finish
    return score_and_finish(state)


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT / "scripts"))
    raise SystemExit(main())
