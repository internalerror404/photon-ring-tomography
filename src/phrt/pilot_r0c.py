"""R0C repaired validation: four source regimes, refits, calibrated posteriors.

Everything the pilot fitted is refitted here, because the bank it was fitted on
no longer exists. The four regimes separate two questions the pilot's single
"in-class" arm confounded: whether the operator can reconstruct a movie that is
*in* the class, and how that degrades when the truth lies outside it.

Selection is on the repair-validation bank, per the amendment. The covariance
scaling is fitted on its own split and never on the split it is judged on.
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

import numpy as np

from phrt.inverse.reduced import ReducedOperator
from phrt.io.manifests import Gate, RunManifest, make_run_id, merge_gate_file
from phrt.io.tables import write_table
from phrt.metrics.calibration import PROBABILISTIC
from phrt.metrics.data_prior_split import subspace_errors
from phrt.metrics.stable_depth import anchored_depth_surface
from phrt.inverse.uncertainty import mahalanobis_calibration
from phrt.pilot_r0 import (_apply, coefficients_of, lexicographic_best, score,
                           statistics_for)

ROOT = Path(__file__).resolve().parents[2]
ARMS = ("DIRECT_PHYSICAL", "RESOLVED_PHYSICAL", "UNRESOLVED_IMAGE", "TOTAL_FLUX")
EPSILONS = (0.25, 0.35, 0.50)
QUANTILES = (0.80, 0.90, 0.95)
PRIMARY_EPS, PRIMARY_Q = 0.25, 0.95        # validation-selected, frozen in R0C
RETIRED_EPS, RETIRED_Q = 0.50, 0.90        # kept in every table
SELECTION_REGIME = "IN_CLASS_ID"


def coefficients_for(movies, values, design) -> np.ndarray:
    """Stored coefficients where a truth has them, least squares otherwise.

    An in-span truth carries the exact coefficient vector it was built from, so
    projecting it again would only add rounding. An off-grid truth has no exact
    representation and its best in-class approximation is the right comparison.
    """
    stored = [m.extra.get("coefficients") for m in movies]
    if all(c is not None for c in stored):
        return np.asarray(stored, float)
    return coefficients_of(design, values)


def fit_covariance_scale(est: str, samples) -> dict:
    """One scalar per estimator family, from the calibration split alone.

    ``cov -> s * cov`` with ``s`` chosen to put the mean squared Mahalanobis
    distance on its expectation. The single scalar is fitted across every arm
    and every SNR on the calibration split, because the raw ratio varies by
    orders of magnitude over the sweep and a scalar fitted at one operating
    point would be a scalar fitted to nothing. The geometric mean is the right
    centre for a quantity that is judged by its ratio to one.

    One number per family, applied everywhere. A scale per arm, per SNR and per
    family would let the uncertainty layer absorb any miscalibration rather than
    report it, which is what the amendment forbids.
    """
    ratios = []
    for truth_coef, est_coef, cov in samples:
        r = float(mahalanobis_calibration(truth_coef, est_coef, cov)["ratio"])
        if np.isfinite(r) and r > 0:
            ratios.append(r)
    if not ratios:
        return {"estimator": est, "scale": 1.0, "unscaled_ratio": float("nan"),
                "n_operating_points": 0,
                "rule": "no finite ratio on the calibration split"}
    logs = np.log(np.asarray(ratios))
    s = float(np.exp(logs.mean()))
    return {"estimator": est, "scale": s,
            "unscaled_ratio": s,
            "unscaled_ratio_min": float(min(ratios)),
            "unscaled_ratio_max": float(max(ratios)),
            "unscaled_ratio_spread_decades":
                float((logs.max() - logs.min()) / np.log(10.0)),
            "n_operating_points": len(ratios),
            "rule": "cov -> s * cov, s the geometric mean of the raw joint "
                    "ratios over every arm and SNR on the "
                    "uncertainty_calibration split; one scalar per estimator "
                    "family"}


def run(P: dict) -> int:
    t0, started = P["t0"], P["started"]
    fz, reg = P["freeze"], P["reg"]
    ages, eta, eta_struct = P["ages"], P["eta"], P["eta_struct"]
    design, red, snr_grid, rho = P["design"], P["red"], P["snr_grid"], P["rho"]
    scorer, terms = P["scorer"], P["terms"]
    truth_coef, truth_vals = P["truth_coef"], P["truth_vals"]
    regimes = list(P["regimes"])
    grids = fz["hyperparameter_grids"]
    ctx = {"LtL": P["LtL"], "priors": P["priors"], "ss_prec": P["ss_prec"],
           "cache": {}}
    a_old = float(fz["metrics"]["old_band_boundary_M"])
    a_anchor = float(fz["metrics"]["a_anchor_M"])
    a_max = float(ages[-1])
    old_mask = ages >= a_old
    master, streams = P["master"], P["streams"]
    fh = P["freeze_hash"]
    d = P["dimension"]

    estimators = {
        "TSVD": grids["TSVD"]["grid"],
        "RIDGE_IDENTITY": grids["RIDGE_IDENTITY"]["grid"],
        "TIKHONOV_TEMPORAL": grids["TIKHONOV_TEMPORAL"]["grid"],
        "WIENER_GAUSSIAN": grids["WIENER_GAUSSIAN"]["grid"],
        "LINEAR_STATE_SPACE": grids["LINEAR_STATE_SPACE"]["process_noise"],
    }
    strength = {"TSVD": lambda h: h, "RIDGE_IDENTITY": lambda h: h,
                "TIKHONOV_TEMPORAL": lambda h: h, "WIENER_GAUSSIAN": lambda h: h,
                "LINEAR_STATE_SPACE": lambda h: -h}

    # ---- representation floor, per regime ---------------------------------
    floor_rows, floor_depth = [], []
    for r in regimes:
        nrm, abse, nrm_s, _ = score(scorer, terms[r], truth_coef[r], eta,
                                    eta_struct)
        for metric, E in (("registered", nrm), ("structure", nrm_s)):
            for surf in anchored_depth_surface(ages, E, EPSILONS, QUANTILES,
                                               a_anchor, a_max):
                floor_depth.append({"regime": r, "metric": metric, **surf,
                                    "freeze_sha256": fh})
        med, med_s = np.median(nrm, axis=0), np.median(nrm_s, axis=0)
        meda = np.median(abse, axis=0)
        for k, a in enumerate(ages):
            floor_rows.append({
                "regime": r, "retarded_age": float(a),
                "median_normalized_error": float(med[k]),
                "median_structure_normalized_error": float(med_s[k]),
                "median_absolute_error": float(meda[k]),
                "in_old_band": bool(old_mask[k]),
                "definition": "error of the exact least-squares projection of "
                              "the truth onto C224, noiseless",
                "freeze_sha256": fh})
    fl = {r: (min(x["median_structure_normalized_error"] for x in floor_rows
                  if x["regime"] == r),
              max(x["median_structure_normalized_error"] for x in floor_rows
                  if x["regime"] == r)) for r in regimes}
    print("representation floor, structure-normalized: "
          + ", ".join(f"{r}={lo:.3f}-{hi:.3f}" for r, (lo, hi) in fl.items()))

    P["floor_rows"], P["floor_depth"] = floor_rows, floor_depth
    P["estimators"], P["strength"], P["ctx"] = estimators, strength, ctx
    P["old_mask"], P["a_anchor"], P["a_max"] = old_mask, a_anchor, a_max

    # Selection first, then calibration, then scoring. The posterior's
    # calibration depends on how hard the estimator regularises, so a scalar
    # fitted at some other hyperparameter than the one the estimator will
    # actually use is fitted to a different posterior. The hyperparameter comes
    # from validation selection, which is where it is supposed to come from; the
    # scalar itself still sees only the uncertainty_calibration split, and that
    # split is never scored.
    P["sel_rows"], P["selected"] = _select_all(P)
    P["scales"], P["scale_rows"] = _fit_scales(P)
    return _score_all(P)


def _select_all(P: dict) -> tuple[list[dict], dict]:
    """The frozen lexicographic rule, on the repair-validation bank."""
    ages, eta, eta_struct = P["ages"], P["eta"], P["eta_struct"]
    red, scorer, terms = P["red"], P["scorer"], P["terms"]
    truth_coef = P["truth_coef"]
    estimators, strength, ctx = P["estimators"], P["strength"], P["ctx"]
    old_mask, a_anchor, a_max = P["old_mask"], P["a_anchor"], P["a_max"]
    master, streams, fh = P["master"], P["streams"], P["freeze_hash"]
    rows, selected = [], {}
    for arm in ARMS:
        op = red[arm]
        for snr in P["snr_grid"]:
            nrng = np.random.default_rng([master, streams["noise_draws"],
                                          int(snr)])
            for est, grid in estimators.items():
                sel_t = time.time()
                Xs = truth_coef[SELECTION_REGIME]
                b = statistics_for(op, Xs, snr,
                                   op.noise_statistic(nrng, Xs.shape[0]))
                cands = []
                for hp in grid:
                    xr, _ = _apply(est, op, b, hp, ctx)
                    nrm, abse, _, _ = score(scorer, terms[SELECTION_REGIME],
                                            xr / snr, eta, eta_struct)
                    surf = anchored_depth_surface(ages, nrm, [PRIMARY_EPS],
                                                  [PRIMARY_Q], a_anchor,
                                                  a_max)[0]
                    cands.append({
                        "hp": float(hp),
                        "L_stable_anchor": surf["L_stable_anchor"],
                        "T_stable_anchor": surf["T_stable_anchor"],
                        "old_norm": float(np.mean(nrm[:, old_mask])),
                        "old_abs": float(np.mean(abse[:, old_mask])),
                        "strength": float(strength[est](hp))})
                best = lexicographic_best(cands)
                oracle = sorted(cands, key=lambda c: c["old_norm"])[0]
                selected[(arm, est, float(snr))] = best["hp"]
                rows.append({
                    "arm": arm, "estimator": est, "snr0": snr,
                    "selection_regime": SELECTION_REGIME,
                    "selected_hyperparameter": best["hp"],
                    "selection_rule": "lexicographic on the repair-validation "
                                      "bank, primary cell (0.25, 0.95)",
                    "selected_L_stable_anchor": best["L_stable_anchor"],
                    "selected_old_band_normalized_error": best["old_norm"],
                    "oracle_hyperparameter": oracle["hp"],
                    "oracle_old_band_normalized_error": oracle["old_norm"],
                    "oracle_label": "ORACLE_UPPER_BOUND", "n_grid": len(grid),
                    "selection_seconds": time.time() - sel_t,
                    "freeze_sha256": fh})
    print(f"selection: {len(rows)} (arm, estimator, SNR) cells")
    return rows, selected


def _fit_scales(P: dict) -> tuple[dict, list[dict]]:
    """One scalar per estimator family, on the calibration split only."""
    red, ctx, fh = P["red"], P["ctx"], P["freeze_hash"]
    master, streams = P["master"], P["streams"]
    cal_coef = P["cal_coef"]
    scales, rows = {}, []
    for est in P["estimators"]:
        if est not in PROBABILISTIC:
            continue
        samples = []
        for arm in ARMS:
            op = red[arm]
            for snr in P["snr_grid"]:
                hp = P["selected"][(arm, est, float(snr))]
                nrng = np.random.default_rng(
                    [master, streams["uncertainty_calibration"], int(snr),
                     ARMS.index(arm)])
                b = statistics_for(op, cal_coef, snr,
                                   op.noise_statistic(nrng, cal_coef.shape[0]))
                xr, cov = _apply(est, op, b, hp, ctx)
                if cov is not None:
                    samples.append((cal_coef, xr / snr, cov))
        rec = fit_covariance_scale(est, samples)
        scales[est] = rec["scale"]
        rows.append({**rec,
                     "hyperparameter": "the selected one at each (arm, SNR)",
                     "fitted_over": "every arm and SNR on the "
                                    "uncertainty_calibration split, at the "
                                    "hyperparameter selection chose there",
                     "freeze_sha256": fh})
        print(f"covariance scale {est}: s = {rec['scale']:.4g} over "
              f"{rec['n_operating_points']} operating points, raw ratio spans "
              f"{rec.get('unscaled_ratio_spread_decades', float('nan')):.1f} "
              f"decades")
    return scales, rows


def _score_all(P: dict) -> int:
    fz, fh = P["freeze"], P["freeze_hash"]
    ages, eta, eta_struct = P["ages"], P["eta"], P["eta_struct"]
    red, snr_grid, rho = P["red"], P["snr_grid"], P["rho"]
    scorer, terms = P["scorer"], P["terms"]
    truth_coef = P["truth_coef"]
    regimes = list(P["regimes"])
    estimators, strength, ctx = P["estimators"], P["strength"], P["ctx"]
    old_mask, a_anchor, a_max = P["old_mask"], P["a_anchor"], P["a_max"]
    master, streams = P["master"], P["streams"]
    d, t0 = P["dimension"], P["t0"]
    n_draws = int(P["n_draws"])

    age_rows, depth_rows, dw_rows, cov_rows, rt_rows = [], [], [], [], []
    sel_rows = P["sel_rows"]
    for arm in ARMS:
        op = red[arm]
        for snr in P["snr_grid"]:
            for est in estimators:
                hp = P["selected"][(arm, est, float(snr))]
                for regime in regimes:
                    Xr = truth_coef[regime]
                    acc_nrm, acc_abs, acc_ns = [], [], []
                    r_t = time.time()
                    for draw in range(n_draws + 1):
                        noiseless = draw == n_draws
                        nz = (np.zeros((Xr.shape[0], d)) if noiseless
                              else op.noise_statistic(
                                  np.random.default_rng(
                                      [master, streams["noise_draws"],
                                       int(snr), draw]), Xr.shape[0]))
                        bb = statistics_for(op, Xr, snr, nz)
                        xr, cov = _apply(est, op, bb, hp, ctx)
                        nrm, abse, nrm_s, _ = score(scorer, terms[regime],
                                                    xr / snr, eta, eta_struct)
                        acc_nrm.append(nrm); acc_abs.append(abse)
                        acc_ns.append(nrm_s)
                        if noiseless:
                            continue
                        sub = subspace_errors(op, Xr, xr / snr, snr, rho)
                        dw_rows.append({
                            "arm": arm, "estimator": est, "snr0": snr,
                            "regime": regime, "draw": draw,
                            "error_data_supported": float(np.mean(
                                sub["error_data_supported"])),
                            "error_weak": float(np.mean(sub["error_weak"])),
                            "error_total": float(np.mean(sub["error_total"])),
                            "n_data_directions": sub["n_data_directions"],
                            "n_weak_directions": sub["n_weak_directions"],
                            "note": "a weak-subspace improvement is a prior "
                                    "effect, not measured recovery",
                            "freeze_sha256": fh})
                        if draw == 0 and est in PROBABILISTIC and cov is not None:
                            s = P["scales"].get(est, 1.0)
                            j = mahalanobis_calibration(Xr, xr / snr, s * cov)
                            cov_rows.append({
                                "arm": arm, "estimator": est, "snr0": snr,
                                "regime": regime, "covariance_scale": s,
                                "scaled_joint_ratio": j["ratio"],
                                "median_pvalue": j["median_pvalue"],
                                "clipped_directions": j["clipped_directions"],
                                "supported_directions":
                                    j["numerically_supported_directions"],
                                "disposition": "SUPPORTED",
                                "freeze_sha256": fh})
                    nrm_all = np.concatenate(acc_nrm[:-1]) if n_draws else acc_nrm[0]
                    ns_all = np.concatenate(acc_ns[:-1]) if n_draws else acc_ns[0]
                    surf_s = {(x["epsilon"], x["quantile"]): x
                              for x in anchored_depth_surface(
                                  ages, ns_all, EPSILONS, QUANTILES, a_anchor,
                                  a_max)}
                    for surf in anchored_depth_surface(ages, nrm_all, EPSILONS,
                                                       QUANTILES, a_anchor,
                                                       a_max):
                        st = surf_s[(surf["epsilon"], surf["quantile"])]
                        depth_rows.append({
                            "arm": arm, "estimator": est, "snr0": snr,
                            "regime": regime, "hyperparameter": hp, **surf,
                            "primary": bool(surf["epsilon"] == PRIMARY_EPS
                                            and surf["quantile"] == PRIMARY_Q),
                            "retired_endpoint": bool(
                                surf["epsilon"] == RETIRED_EPS
                                and surf["quantile"] == RETIRED_Q),
                            "endpoint_label": (
                                "VALIDATION_SELECTED_PRIMARY_FROM_PREREGISTERED_SURFACE"
                                if (surf["epsilon"] == PRIMARY_EPS
                                    and surf["quantile"] == PRIMARY_Q)
                                else "NONDISCRIMINATING_RIGHT_CENSORED_ENDPOINT"
                                if (surf["epsilon"] == RETIRED_EPS
                                    and surf["quantile"] == RETIRED_Q)
                                else "SURFACE_CELL"),
                            "T_stable_anchor_structure": st["T_stable_anchor"],
                            "L_stable_anchor_structure": st["L_stable_anchor"],
                            "registered_metric_saturated":
                                bool(surf["T_stable_anchor"] >= a_max),
                            "structure_metric_saturated":
                                bool(st["T_stable_anchor"] >= a_max),
                            "freeze_sha256": fh})
                    med, med_s = np.median(nrm_all, axis=0), np.median(ns_all, axis=0)
                    meda = np.median(np.concatenate(acc_abs[:-1]) if n_draws
                                     else acc_abs[0], axis=0)
                    for k, a in enumerate(ages):
                        age_rows.append({
                            "arm": arm, "estimator": est, "snr0": snr,
                            "regime": regime, "retarded_age": float(a),
                            "median_normalized_error": float(med[k]),
                            "median_structure_normalized_error": float(med_s[k]),
                            "median_absolute_error": float(meda[k]),
                            "in_old_band": bool(old_mask[k]),
                            "freeze_sha256": fh})
                    rt_rows.append({
                        "arm": arm, "estimator": est, "snr0": snr,
                        "regime": regime, "n_truths": int(Xr.shape[0]),
                        "n_draws": n_draws + 1, "seconds": time.time() - r_t,
                        "iterations": 1,
                        "note": "direct linear solve; no iterative scheme",
                        "freeze_sha256": fh})
        print(f"  {arm}: done at {time.time() - t0:.0f}s")

    P["out"] = dict(sel_rows=sel_rows, age_rows=age_rows, depth_rows=depth_rows,
                    dw_rows=dw_rows, cov_rows=cov_rows, rt_rows=rt_rows,
                    floor_rows=P["floor_rows"], floor_depth=P["floor_depth"],
                    scale_rows=P["scale_rows"])
    return _finish(P)


def _finish(P: dict) -> int:
    import pandas as pd
    fz, reg, fh = P["freeze"], P["reg"], P["freeze_hash"]
    out = P["out"]
    band = fz["uncertainty_calibration"]["acceptance_band_joint_ratio"]

    cov = pd.DataFrame(out["cov_rows"])
    if len(cov):
        worst = cov.groupby("estimator").scaled_joint_ratio.median()
        in_band = {e: bool(band[0] <= v <= band[1]) for e, v in worst.items()}
        calibrated = all(in_band.values())
    else:
        worst, in_band, calibrated = pd.Series(dtype=float), {}, False
    uncertainty = "CALIBRATED" if calibrated else "UNCERTAINTY_WITHDRAWN"
    print(f"uncertainty: {uncertainty} "
          + ", ".join(f"{e}={v:.3g}" for e, v in worst.items()))

    run_id = make_run_id("R0C", reg.sha256)
    man = RunManifest(
        run_id=run_id, experiment_id="R0C_REPAIRED_VALIDATION",
        seeds={"master": P["master"], "streams": P["streams"]},
        started_at=P["started"], attestation=P["attestation"],
        extra={"freeze_sha256": fh, "amendment": "R0_REPAIR_AMENDMENT_004",
               "uncertainty_disposition": uncertainty,
               "regimes": list(P["regimes"]), **P["provenance"]})
    man.add_input(ROOT / "artifacts" / "configs"
                  / "R0C_REPAIRED_SOURCE_AND_CALIBRATION_FREEZE.json")

    man.add_gate(Gate("R0_G14_in_span_membership",
                      "PASS" if P["worst_in_span"] <= P["in_span_tol"] else "FAIL",
                      measured=P["worst_in_span"], threshold=P["in_span_tol"],
                      note=f"worst relative residual over "
                           f"{P['n_in_span']} IN_CLASS truths, measured on "
                           f"coordinates other than the projection grid"))
    # A mechanical FAIL here is a registered branch, not a defect: the freeze
    # declares in advance that a posterior outside the band is withdrawn rather
    # than repaired after the fact. The status stays FAIL because the band was
    # missed; the disposition says the miss was ruled on before it happened.
    man.add_gate(Gate("R0_G15_uncertainty_calibration_band",
                      "PASS" if calibrated else "FAIL",
                      measured=float(worst.max()) if len(worst) else float("nan"),
                      threshold=band[1],
                      disposition=None if calibrated else uncertainty,
                      note=f"one scalar per estimator family fitted on the "
                           f"uncertainty_calibration split at the selected "
                           f"hyperparameter and evaluated here: "
                           + ", ".join(f"{e}={v:.4g}" for e, v in worst.items())
                           + f". Band {band}. Outcome {uncertainty}"
                           + ("" if calibrated else
                              ". The estimators are retained as point "
                              "estimators; no credible interval, posterior "
                              "movie or coverage statement follows from them")))
    man.add_gate(Gate("R0_G11_split_hash_disjointness",
                      "PASS" if P["disj"]["disjoint"] else "FAIL",
                      measured=P["disj"]["worst_overlap"], threshold=0,
                      note=f"content-hash overlap across "
                           f"{len(P['disj']['sizes'])} splits"))

    for name, rows in (("r0c_age_errors", out["age_rows"]),
                       ("r0c_stable_depth", out["depth_rows"]),
                       ("r0c_estimator_selection", out["sel_rows"]),
                       ("r0c_data_weak_errors", out["dw_rows"]),
                       ("r0c_calibration", out["cov_rows"]),
                       ("r0c_covariance_scales", out["scale_rows"]),
                       ("r0c_runtime", out["rt_rows"]),
                       ("r0c_representation_floor", out["floor_rows"]),
                       ("r0c_representation_floor_depth", out["floor_depth"])):
        if rows:
            man.add_output(write_table(rows, name))

    (ROOT / "artifacts" / "manifests" / "r0c_split_hash_manifest.json").write_text(
        json.dumps({"schema": "phrt-r0c-splits/1", **P["disj"],
                    "regimes": {k: v for k, v in P["regime_counts"].items()}},
                   indent=2) + "\n")
    mp = man.write(reg.path, reg.sha256, runtime_seconds=time.time() - P["t0"])
    merge_gate_file(man.gates, run_id)
    P["uncertainty"] = uncertainty
    print(f"manifest {mp}")
    print(f"total {time.time() - P['t0']:.0f}s")
    return 0
