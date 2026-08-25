"""R0B pilot core: selection, scoring, paired arm comparison and null pairs.

Kept out of the runner script so the scoring logic is importable and testable
rather than living inside a main().

Two rules are enforced structurally rather than by convention:

* hyperparameters are selected on validation data only, per arm, estimator and
  SNR, by the frozen lexicographic objective. The oracle variant is computed
  too, but it is labelled ORACLE_UPPER_BOUND and never selected from.
* the same truth and the *same* resolved noise draw feed every arm, so an arm
  comparison is paired and the difference is not contaminated by resampling.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
from scipy import stats

from phrt.inverse.reduced import ReducedOperator
from phrt.inverse.ridge import ridge_from_statistic
from phrt.inverse.smoothness import tikhonov_from_statistic
from phrt.inverse.state_space import state_space_from_statistic
from phrt.inverse.tsvd import tsvd_from_statistic
from phrt.inverse.wiener import wiener_from_statistic
from phrt.io.manifests import RunManifest, make_run_id
from phrt.io.tables import write_table
from phrt.metrics.calibration import coverage_rows
from phrt.metrics.data_prior_split import subspace_errors
from phrt.metrics.stable_depth import anchored_depth_surface
from phrt.sources.near_null import (amplitude_for_target,
                                    direction_for_separation,
                                    realized_separation)

ROOT = Path(__file__).resolve().parents[2]
ARMS = ("DIRECT_PHYSICAL", "RESOLVED_PHYSICAL", "UNRESOLVED_IMAGE", "TOTAL_FLUX")
EPSILONS = (0.25, 0.35, 0.50)
QUANTILES = (0.80, 0.90, 0.95)
PRIMARY_EPS, PRIMARY_Q = 0.50, 0.90


def coefficients_of(design: np.ndarray, values: np.ndarray) -> np.ndarray:
    """Least-squares coefficients of rendered movies, one per row.

    For an in-class truth this is exact; for an off-grid truth it is the best
    in-class approximation, and the residual is what makes the regime hard.
    """
    return np.linalg.lstsq(design, values.T, rcond=None)[0].T


def statistics_for(op: ReducedOperator, x: np.ndarray, snr: float,
                   noise: np.ndarray) -> np.ndarray:
    """b = G x_snr + xi for a stack of truths sharing one noise draw per row.

    The SNR enters as a scaling of the operator, equivalently of the source
    amplitude: a higher SNR_0 means the same source produces a larger whitened
    response. Scaling the noise instead would be the same model but would make
    the noise draw depend on the SNR and break the pairing across the sweep.
    """
    return snr * op.forward_statistic(x) + noise


def _resolver(est: str, op: ReducedOperator, hp, ctx):
    """The data-independent part of a solve, built once and cached.

    For every estimator here the map from the sufficient statistic to the
    estimate is a fixed matrix determined by the arm and the hyperparameter --
    it does not depend on the data or on the SNR. Rebuilding it inside the draw
    loop was inverting the same 224 x 224 matrix thousands of times.
    """
    key = (est, op.arm, float(hp))
    hit = ctx["cache"].get(key)
    if hit is not None:
        return hit
    if est == "TSVD":
        keep = op.s >= hp * op.s[0]
        inv = np.zeros_like(op.s)
        inv[keep] = 1.0 / op.s[keep] ** 2
        val = ("diag", inv, None, None)
    elif est == "RIDGE_IDENTITY":
        lam = hp * op.s[0] ** 2
        val = ("diag", 1.0 / (op.s ** 2 + lam), None, None)
    elif est == "TIKHONOV_TEMPORAL":
        lam = hp * op.s[0] ** 2
        val = ("dense", np.linalg.inv(op.gram + lam * ctx["LtL"]), None, None)
    elif est == "WIENER_GAUSSIAN":
        pr = ctx["priors"][hp]
        P_ = np.linalg.inv(pr.covariance)
        cov = np.linalg.inv(P_ + op.gram)
        val = ("dense_offset", cov, cov @ (P_ @ pr.mean), cov)
    elif est == "LINEAR_STATE_SPACE":
        cov = np.linalg.inv(ctx["ss_prec"][hp] + op.gram)
        val = ("dense", cov, None, cov)
    else:
        raise ValueError(est)
    ctx["cache"][key] = val
    return val


def _apply(est: str, op: ReducedOperator, b: np.ndarray, hp, ctx) -> tuple:
    kind, R, offset, cov = _resolver(est, op, hp, ctx)
    b2 = np.atleast_2d(b)
    if kind == "diag":
        x = ((b2 @ op.V) * R) @ op.V.T
    elif kind == "dense":
        x = b2 @ R.T
    else:
        x = b2 @ R.T + offset[None, :]
    return (x if b.ndim > 1 else x[0]), cov


def score(scorer, terms, coefficients, eta, eta_struct):
    """Registered and structure-normalized age-error curves.

    The registered metric is returned unchanged. The structure metric removes
    the age-local constant from both residual and truth, because the registered
    denominator is dominated by a positive baseline that every estimator
    recovers trivially -- which makes the registered stable depth saturate.
    """
    p, s_, m_, t_norm = terms
    abs_e = scorer.errors(coefficients, p, s_)
    res_s, truth_s = scorer.structure_errors(coefficients, p, s_, m_)
    return (abs_e / np.maximum(t_norm, eta), abs_e,
            res_s / np.maximum(truth_s, eta_struct), res_s)


def lexicographic_best(cands: list[dict]) -> dict:
    """The frozen selection rule.

    maximize L_stable_anchor, then minimize old-band normalized error, then
    old-band absolute error, then prefer the stronger regularizer on a tie. The
    tie-break is last and is defined as the larger hyperparameter for the
    penalty-style estimators and the smaller retained rank for TSVD, both of
    which mean 'regularize harder'.
    """
    return sorted(cands, key=lambda c: (-c["L_stable_anchor"], c["old_norm"],
                                        c["old_abs"], -c["strength"]))[0]


def run_pilot(P: dict) -> int:
    t0 = P["t0"]
    fz, reg = P["freeze"], P["reg"]
    Wn, ages, eta = P["Wn"], P["ages"], P["eta"]
    design, truths, bank = P["design"], P["truths"], P["bank"]
    red, snr_grid, rho = P["red"], P["snr_grid"], P["rho"]
    grids = fz["hyperparameter_grids"]
    ctx = {"LtL": P["LtL"], "priors": P["priors"], "ss_prec": P["ss_prec"],
           "cache": {}}
    d = P["basis"].dimension
    a_old = float(fz["metrics"]["old_band_boundary_M"])
    a_anchor = float(fz["metrics"]["a_anchor_M"])
    old_mask = ages >= a_old
    a_max = float(ages[-1])
    master, streams = P["master"], P["streams"]

    estimators = {
        "TSVD": grids["TSVD"]["grid"],
        "RIDGE_IDENTITY": grids["RIDGE_IDENTITY"]["grid"],
        "TIKHONOV_TEMPORAL": grids["TIKHONOV_TEMPORAL"]["grid"],
        "WIENER_GAUSSIAN": grids["WIENER_GAUSSIAN"]["grid"],
        "LINEAR_STATE_SPACE": grids["LINEAR_STATE_SPACE"]["process_noise"],
    }
    strength = {"TSVD": lambda h: h,          # larger cut = harder truncation
                "RIDGE_IDENTITY": lambda h: h,
                "TIKHONOV_TEMPORAL": lambda h: h,
                "WIENER_GAUSSIAN": lambda h: h,
                "LINEAR_STATE_SPACE": lambda h: -h}   # smaller q = stiffer prior

    regimes = {
        "validation_in_class": [f for (s, f) in bank if s == "validation_in_class"],
        "validation_off_grid": [f for (s, f) in bank if s == "validation_off_grid"],
        "validation_ood": [f for (s, f) in bank if s == "validation_ood"],
    }
    truth_vals = {r: np.concatenate([truths[(r, f)] for f in fams])
                  for r, fams in regimes.items()}
    truth_fam = {r: np.concatenate([[f] * truths[(r, f)].shape[0] for f in fams])
                 for r, fams in regimes.items()}
    truth_coef = {r: coefficients_of(design, v) for r, v in truth_vals.items()}
    scorer = P["scorer"]
    # p_a and s_a per truth, computed once per regime and reused across every
    # arm, SNR, estimator and hyperparameter
    t_pre = time.time()
    terms = {}
    for r, v in truth_vals.items():
        p_, s_, m_ = scorer.truth_terms(v)
        terms[r] = (p_, s_, m_, np.sqrt(np.maximum(s_, 0.0)))
    # eta for the structure metric, frozen on the prior-fit split by the same
    # 5 % - of - median rule as the registered eta
    pf_terms = scorer.truth_terms(P["prior_fit_values"])
    _, s_pf, m_pf = pf_terms
    tn_struct = np.sqrt(np.maximum(s_pf - m_pf ** 2
                                   / np.maximum(scorer.h, 1e-300), 0.0))
    pos = tn_struct[tn_struct > 0]
    eta_struct = float(0.05 * np.median(pos)) if pos.size else 1e-12
    print(f"eta_struct frozen at {eta_struct:.6g}")
    print(f"truth terms precomputed in {time.time() - t_pre:.0f}s")
    n_draws = max(1, int(round(P["counts"]["noise_draws_per_validation_truth_and_snr"]
                               * P["scale"])))
    print(f"validation truths: "
          + ", ".join(f"{r}={v.shape[0]}" for r, v in truth_vals.items())
          + f"; noise draws {n_draws} plus one noiseless control")

    sel_rows, age_rows, depth_rows, dw_rows, cov_rows, rt_rows = [], [], [], [], [], []

    # ---- representation floor ---------------------------------------------
    # The truths are rendered analytically at the class's resolvable scale, so
    # even the exact least-squares projection onto C224 leaves a residual. That
    # residual is a property of the class and the truth, not of any estimator,
    # and it is the floor every row below sits on. Reporting estimator errors
    # without it would invite reading a class-approximation limit as an
    # estimator or an arm result.
    floor_rows, floor_depth = [], []
    for regime in regimes:
        nrm, abse, nrm_s, abs_s = score(scorer, terms[regime],
                                        truth_coef[regime], eta, eta_struct)
        for surf in anchored_depth_surface(ages, nrm, EPSILONS, QUANTILES,
                                           a_anchor, a_max):
            floor_depth.append({"regime": regime, "metric": "registered",
                                **surf, "freeze_sha256": P["freeze_hash"]})
        for surf in anchored_depth_surface(ages, nrm_s, EPSILONS, QUANTILES,
                                           a_anchor, a_max):
            floor_depth.append({"regime": regime, "metric": "structure",
                                **surf, "freeze_sha256": P["freeze_hash"]})
        med, med_s = np.median(nrm, axis=0), np.median(nrm_s, axis=0)
        meda = np.median(abse, axis=0)
        for k, a in enumerate(ages):
            floor_rows.append({
                "regime": regime, "retarded_age": float(a),
                "median_normalized_error": float(med[k]),
                "median_structure_normalized_error": float(med_s[k]),
                "median_absolute_error": float(meda[k]),
                "in_old_band": bool(old_mask[k]),
                "definition": "error of the exact least-squares projection of "
                              "the truth onto C224, noiseless. No estimator can "
                              "beat this within the declared class",
                "freeze_sha256": P["freeze_hash"]})
    fl = np.array([r["median_structure_normalized_error"] for r in floor_rows
                   if r["regime"] == "validation_in_class"])
    print(f"representation floor, in-class: structure-normalized median "
          f"{fl.min():.3f}-{fl.max():.3f} over the age grid")

    # ---- selection on validation_in_class, then scoring on every regime ----
    for arm in ARMS:
        op = red[arm]
        for snr in snr_grid:
            # one resolved noise draw set, shared by every arm at this SNR
            nrng = np.random.default_rng([master, streams["noise_draws"],
                                          int(snr)])
            for est, grid in estimators.items():
                sel_t = time.time()
                # ---- selection pass, validation_in_class only --------------
                Xv = truth_coef["validation_in_class"]
                Vv = truth_vals["validation_in_class"]
                noise = op.noise_statistic(nrng, Xv.shape[0])
                b = statistics_for(op, Xv, snr, noise)
                cands = []
                for hp in grid:
                    xr, cov = _apply(est, op, b, hp, ctx)
                    nrm, abse, nrm_s, abs_s = score(
                        scorer, terms["validation_in_class"], xr / snr, eta,
                        eta_struct)
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
                sel_rows.append({
                    "arm": arm, "estimator": est, "snr0": snr,
                    "selected_hyperparameter": best["hp"],
                    "selection_rule": "lexicographic_validation",
                    "selected_T_stable_anchor": best["T_stable_anchor"],
                    "selected_L_stable_anchor": best["L_stable_anchor"],
                    "a_anchor_M": a_anchor,
                    "selected_old_band_normalized_error": best["old_norm"],
                    "oracle_hyperparameter": oracle["hp"],
                    "oracle_old_band_normalized_error": oracle["old_norm"],
                    "oracle_label": "ORACLE_UPPER_BOUND",
                    "n_grid": len(grid),
                    "selection_seconds": time.time() - sel_t,
                    "freeze_sha256": P["freeze_hash"]})
                hp = best["hp"]

                # ---- scoring pass on every validation regime ---------------
                for regime in regimes:
                    Xr, Vr = truth_coef[regime], truth_vals[regime]
                    fams = truth_fam[regime]
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
                        nrm, abse, nrm_s, abs_s = score(
                            scorer, terms[regime], xr / snr, eta, eta_struct)
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
                            "freeze_sha256": P["freeze_hash"]})
                        if draw == 0:
                            for cr in coverage_rows(est, Xr, xr / snr, cov):
                                cov_rows.append({"arm": arm, "snr0": snr,
                                                 "regime": regime, **cr,
                                                 "freeze_sha256": P["freeze_hash"]})
                    nrm_all = np.concatenate(acc_nrm[:-1]) if n_draws else acc_nrm[0]
                    ns_all = (np.concatenate(acc_ns[:-1]) if n_draws
                              else acc_ns[0])
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
                            "regime": regime, "hyperparameter": hp,
                            "primary": bool(surf["epsilon"] == PRIMARY_EPS
                                            and surf["quantile"] == PRIMARY_Q),
                            **surf,
                            # the structure-normalized companion, same
                            # definition, denominator with the age-local
                            # constant removed from residual and truth alike
                            "T_stable_anchor_structure": st["T_stable_anchor"],
                            "L_stable_anchor_structure": st["L_stable_anchor"],
                            "secondary_reach_M_structure": st["secondary_reach_M"],
                            "secondary_longest_run_span_M_structure":
                                st["secondary_longest_run_span_M"],
                            "fraction_at_anchor_structure":
                                st["fraction_at_anchor"],
                            "registered_metric_saturated":
                                bool(surf["T_stable_anchor"] >= a_max),
                            "structure_metric_saturated":
                                bool(st["T_stable_anchor"] >= a_max),
                            "age_interval_amendment":
                                "AGE_INTERVAL_SEMANTICS_AMENDMENT_003",
                            "freeze_sha256": P["freeze_hash"]})
                    med_s = np.median(ns_all, axis=0)
                    med = np.median(nrm_all, axis=0)
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
                            "freeze_sha256": P["freeze_hash"]})
                    rt_rows.append({
                        "arm": arm, "estimator": est, "snr0": snr,
                        "regime": regime, "n_truths": int(Xr.shape[0]),
                        "n_draws": n_draws + 1,
                        "seconds": time.time() - r_t,
                        "peak_rss_mb": float(
                            __import__("resource").getrusage(
                                __import__("resource").RUSAGE_SELF).ru_maxrss / 1024.0),
                        "iterations": 1,
                        "note": "direct linear solve; no iterative scheme",
                        "freeze_sha256": P["freeze_hash"]})
        print(f"  {arm}: done at {time.time() - t0:.0f}s")

    P["out"] = dict(sel_rows=sel_rows, age_rows=age_rows, depth_rows=depth_rows,
                    dw_rows=dw_rows, cov_rows=cov_rows, rt_rows=rt_rows,
                    floor_rows=floor_rows, floor_depth=floor_depth)
    return finish(P)


def finish(P: dict) -> int:
    """Null pairs, incremental-history pairs, bootstrap and artifact writing."""
    from phrt.pilot_r0_pairs import pairs_and_artifacts
    return pairs_and_artifacts(P)
