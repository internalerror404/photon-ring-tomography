"""R1 held-out main: score the sealed bank once, then stop.

Nothing is selected here. Every hyperparameter comes from the R0C
repair-validation selection, the endpoint and threshold come from the R1
freeze, and the bootstrap count and seed were fixed before a single main truth
was rendered. The only decisions this module makes are arithmetic.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np

from phrt.io.manifests import Gate, RunManifest, make_run_id, merge_gate_file
from phrt.io.tables import write_table
from phrt.metrics.cluster_bootstrap import (anchored_span_interval,
                                            mean_difference_interval,
                                            per_truth_pass_fraction,
                                            running_max)
from phrt.metrics.data_prior_split import (reference_subspace_errors,
                                           subspace_errors)
from phrt.metrics.level_structure import component_errors
from phrt.metrics.stable_depth import anchored_depth_surface
from phrt.pilot_r0 import _apply, score, statistics_for
from phrt.pilot_r0_pairs import bayes_bound, pair_experiment
from phrt.sources.near_null import amplitude_for_target, realized_separation

ROOT = Path(__file__).resolve().parents[2]
ARMS = ("DIRECT_PHYSICAL", "RESOLVED_PHYSICAL", "UNRESOLVED_IMAGE", "TOTAL_FLUX")
EPSILONS = (0.25, 0.35, 0.50)
QUANTILES = (0.80, 0.90, 0.95)


def run(P: dict) -> int:
    t0, fz, fh = P["t0"], P["freeze"], P["freeze_hash"]
    ages, eta, eta_struct = P["ages"], P["eta"], P["eta_struct"]
    red, scorer, terms = P["red"], P["scorer"], P["terms"]
    truth_coef, truth_vals, truth_family = (P["truth_coef"], P["truth_vals"],
                                            P["truth_family"])
    regimes = list(P["regimes"])
    ctx = P["ctx"]
    prim = fz["primary"]
    eps_p, q_p = float(prim["epsilon"]), float(prim["quantile"])
    ref = float(prim["reference_snr"])
    thresh = float(prim["threshold_M"])
    a_anchor = float(fz["metrics"]["a_anchor_M"])
    a_old = float(fz["metrics"]["old_band_boundary_M"])
    a_max = float(ages[-1])
    old_mask = ages >= a_old
    master, streams = P["master"], P["streams"]
    n_draws = int(fz["noise"]["draws_per_truth"])
    selected = P["selected"]
    level = P["level_basis"]
    Wn = scorer.weights
    d = P["dimension"]

    depth_rows, age_rows, fam_rows, dw_rows, ls_rows, rt_rows = \
        [], [], [], [], [], []
    # per-truth material the bootstrap needs, kept only for the primary cell
    boot = {}

    for arm in ARMS:
        op = red[arm]
        for snr in P["snr_grid"]:
            for est in P["estimators"]:
                hp = selected[(arm, est, float(snr))]
                for regime in regimes:
                    Xr = truth_coef[regime]
                    Vr = truth_vals[regime]
                    n_t = Xr.shape[0]
                    r_t = time.time()
                    acc_n, acc_a, acc_s, per_draw = [], [], [], []
                    for draw in range(n_draws + 1):
                        noiseless = draw == n_draws
                        nz = (np.zeros((n_t, d)) if noiseless
                              else op.noise_statistic(
                                  np.random.default_rng(
                                      [master, streams["noise_draws"],
                                       int(snr), draw]), n_t))
                        b = statistics_for(op, Xr, snr, nz)
                        xr, _ = _apply(est, op, b, hp, ctx)
                        xr = xr / snr
                        nrm, abse, nrm_s, _ = score(scorer, terms[regime], xr,
                                                    eta, eta_struct)
                        acc_n.append(nrm); acc_a.append(abse); acc_s.append(nrm_s)
                        if noiseless:
                            continue
                        per_draw.append(nrm)
                        sub = subspace_errors(op, Xr, xr, snr, P["rho"])
                        rsub = reference_subspace_errors(
                            red["DIRECT_PHYSICAL"], Xr, xr, snr, P["rho"])
                        dw_rows.append({
                            "arm": arm, "estimator": est, "snr0": snr,
                            "regime": regime, "draw": draw,
                            "error_data_supported": float(np.mean(
                                sub["error_data_supported"])),
                            "error_weak": float(np.mean(sub["error_weak"])),
                            "n_data_directions": sub["n_data_directions"],
                            "error_in_reference_data_subspace": float(np.mean(
                                rsub["error_in_reference_data_subspace"])),
                            "error_outside_reference_data_subspace": float(
                                np.mean(rsub[
                                    "error_outside_reference_data_subspace"])),
                            "n_reference_data_directions":
                                rsub["n_reference_data_directions"],
                            "note": "a weak-subspace improvement is a prior "
                                    "effect, not measured recovery",
                            "freeze_sha256": fh})
                        if draw == 0:
                            recon_values = xr @ P["design"].T
                            ls = component_errors(Vr, recon_values, level, Wn)
                            ls_rows.append({
                                "arm": arm, "estimator": est, "snr0": snr,
                                "regime": regime,
                                "n_level_modes": ls["n_level_modes"],
                                "error_level_absolute": float(np.median(
                                    ls["error_level_absolute"])),
                                "error_structure_absolute": float(np.median(
                                    ls["error_structure_absolute"])),
                                "error_level_normalized": float(np.median(
                                    ls["error_level_normalized"])),
                                "error_structure_normalized": float(np.median(
                                    ls["error_structure_normalized"])),
                                "level_fraction_of_truth": float(np.median(
                                    ls["level_fraction_of_truth"])),
                                "old_band_error_level_normalized": float(
                                    np.median(
                                        ls["error_level_normalized"][:, old_mask])),
                                "old_band_error_structure_normalized": float(
                                    np.median(ls["error_structure_normalized"]
                                              [:, old_mask])),
                                "definition":
                                    "x = P_level x + P_structure x, P_level the "
                                    "orthogonal projection onto spatially "
                                    "constant fields. Diagnostic; no threshold",
                                "freeze_sha256": fh})

                    nrm_all = np.concatenate(acc_n[:-1])
                    ns_all = np.concatenate(acc_s[:-1])
                    abs_all = np.concatenate(acc_a[:-1])
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
                            "primary": bool(surf["epsilon"] == eps_p
                                            and surf["quantile"] == q_p),
                            "retired_endpoint": bool(surf["epsilon"] == 0.50
                                                     and surf["quantile"] == 0.90),
                            "L_stable_anchor_structure": st["L_stable_anchor"],
                            "T_stable_anchor_structure": st["T_stable_anchor"],
                            "registered_metric_saturated":
                                bool(surf["T_stable_anchor"] >= a_max),
                            "freeze_sha256": fh})

                    if float(snr) == ref:
                        stacked = np.stack(per_draw, axis=1)   # (n_t, draws, a)
                        rmx, sel_ages = running_max(stacked, ages, a_anchor)
                        boot[(arm, est, regime)] = {
                            "pass_fraction": per_truth_pass_fraction(rmx, eps_p),
                            "ages": sel_ages,
                            "old_norm": nrm_all[:, old_mask].reshape(
                                n_draws, n_t, -1).mean(axis=(0, 2)),
                            "old_abs": abs_all[:, old_mask].reshape(
                                n_draws, n_t, -1).mean(axis=(0, 2))}
                        fams = truth_family[regime]
                        rep = np.concatenate([fams] * n_draws)
                        for fam in sorted(set(fams)):
                            m = rep == fam
                            if not m.any():
                                continue
                            fs = anchored_depth_surface(ages, nrm_all[m],
                                                        [eps_p], [q_p],
                                                        a_anchor, a_max)[0]
                            fam_rows.append({
                                "arm": arm, "estimator": est, "snr0": snr,
                                "regime": regime, "family": fam,
                                "n_truths": int(m.sum()),
                                "L_stable_anchor": fs["L_stable_anchor"],
                                "old_band_normalized_error":
                                    float(np.mean(nrm_all[m][:, old_mask])),
                                "old_band_absolute_error":
                                    float(np.mean(abs_all[m][:, old_mask])),
                                "freeze_sha256": fh})

                    med = np.median(nrm_all, axis=0)
                    med_s = np.median(ns_all, axis=0)
                    meda = np.median(abs_all, axis=0)
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
                        "regime": regime, "n_truths": n_t,
                        "n_draws": n_draws + 1, "seconds": time.time() - r_t,
                        "freeze_sha256": fh})
        print(f"  {arm}: done at {time.time() - t0:.0f}s")

    P["out"] = dict(depth_rows=depth_rows, age_rows=age_rows,
                    fam_rows=fam_rows, dw_rows=dw_rows, ls_rows=ls_rows,
                    rt_rows=rt_rows)
    P["out"]["null_rows"], null_summary = _null_pairs(P)
    P["null_summary"] = null_summary
    P["boot"] = boot
    return _bootstrap_and_write(P)


def _null_pairs(P: dict) -> tuple[list[dict], dict]:
    """The committed control bank, scored against the Gaussian Bayes bound.

    The directions were hashed before the main test and are regenerated from
    the same stream here; the amplitude that realises each registered
    separation is a property of the operator, not a choice, so it is solved at
    run time. A method above the equal-prior bound beyond Monte-Carlo tolerance
    is reading information the likelihood does not contain, which is a defect
    and never a success.
    """
    from scipy import stats

    fz, fh = P["freeze"], P["freeze_hash"]
    bank = json.loads((ROOT / "artifacts" / "manifests"
                       / "r1_null_pair_control_bank.json").read_text())
    if bank["control_bank_sha256"] != fz["null_pair_control_bank"]["sha256"]:
        raise ValueError("the null control bank on disk is not the committed one")
    payload = bank["payload"]
    red = P["red"]
    rows, bad_hash = [], 0
    for rec in payload["records"]:
        target, j = float(rec["target_mahalanobis"]), int(rec["pair"])
        rng = np.random.default_rng([payload["master_seed"],
                                     payload["seed_stream"],
                                     int(round(target * 1000)), j])
        u = rng.standard_normal(P["dimension"])
        u /= max(float(np.linalg.norm(u)), 1e-300)
        import hashlib as _h
        if _h.sha256(np.ascontiguousarray(u, dtype="<f8")
                     .tobytes()).hexdigest() != rec["direction_hash"]:
            bad_hash += 1
            continue
        for arm in ARMS:
            op = red[arm]
            alpha = amplitude_for_target(op, u, target)
            if not np.isfinite(alpha):
                rows.append({"arm": arm, "target_delta": target, "pair": j,
                             "disposition": "NOT_APPLICABLE",
                             "reason": "the arm cannot realise this separation "
                                       "along this direction",
                             "realized_delta": 0.0, "bayes_accuracy": 0.5,
                             "observed_accuracy": float("nan"),
                             "exceeds_bayes": False, "freeze_sha256": fh})
                continue
            res = pair_experiment(op, u, alpha,
                                  np.random.default_rng(
                                      [payload["master_seed"],
                                       payload["seed_stream"], 7,
                                       int(round(target * 1000)), j,
                                       ARMS.index(arm)]), 256)
            pb = bayes_bound(res["realized_delta"])
            n = 2 * res["n_trials"]
            mc = 2.0 * float(np.sqrt(max(pb * (1 - pb), 1e-12) / n))
            rows.append({
                "arm": arm, "target_delta": target, "pair": j,
                "realized_delta": res["realized_delta"],
                "relative_delta_error":
                    abs(res["realized_delta"] - target) / max(target, 1e-300),
                "bayes_accuracy": pb, "observed_accuracy": res["accuracy"],
                "monte_carlo_tolerance": mc,
                "exceeds_bayes": bool(res["accuracy"] > pb + mc),
                "disposition": "SUPPORTED", "reason": "",
                "freeze_sha256": fh})
    tested = [r for r in rows if r["disposition"] == "SUPPORTED"]
    leak = [r for r in tested if r["exceeds_bayes"]]
    p_one = float(stats.norm.sf(2.0))
    expected = len(tested) * p_one
    p_excess = (float(stats.binom.sf(len(leak) - 1, len(tested), p_one))
                if tested else 1.0)
    summary = {"n_tested": len(tested), "n_exceeding": len(leak),
               "expected_exceedances": expected, "binomial_p_excess": p_excess,
               "defect": bool(p_excess < 0.01),
               "direction_hash_mismatches": bad_hash,
               "rule": "a defect requires an excess beyond binomial "
                       "multiplicity, not a single two-sigma excursion"}
    print(f"null pairs: {summary['n_tested']} tested, "
          f"{summary['n_exceeding']} above the Bayes bound "
          f"(expected {expected:.1f}, binomial p = {p_excess:.3f}), "
          f"hash mismatches {bad_hash}")
    return rows, summary


def _bootstrap_and_write(P: dict) -> int:
    fz, fh, reg = P["freeze"], P["freeze_hash"], P["reg"]
    prim = fz["primary"]
    bs = fz["bootstrap"]
    n_res, seed = int(bs["n_resamples"]), int(bs["seed"])
    a_anchor = float(fz["metrics"]["a_anchor_M"])
    q_p = float(prim["quantile"])
    boot = P["boot"]
    rows = []
    for est in (prim["primary_estimator"], prim["confirmatory_estimator"],
                "TIKHONOV_TEMPORAL", "WIENER_GAUSSIAN", "LINEAR_STATE_SPACE"):
        for regime in P["regimes"]:
            key_d = ("DIRECT_PHYSICAL", est, regime)
            key_r = ("RESOLVED_PHYSICAL", est, regime)
            if key_d not in boot or key_r not in boot:
                continue
            bd, br = boot[key_d], boot[key_r]
            span = anchored_span_interval(bd["pass_fraction"],
                                          br["pass_fraction"], bd["ages"],
                                          q_p, a_anchor, n_res, seed)
            onorm = mean_difference_interval(bd["old_norm"], br["old_norm"],
                                             n_res, seed)
            oabs = mean_difference_interval(bd["old_abs"], br["old_abs"],
                                            n_res, seed)
            rows.append({
                "estimator": est, "regime": regime,
                "contrast": "RESOLVED_PHYSICAL - DIRECT_PHYSICAL",
                "delta_L_level_M": span["point_estimate"],
                "delta_L_level_ci_low": span["ci_low"],
                "delta_L_level_ci_high": span["ci_high"],
                "delta_L_level_excludes_zero": span["excludes_zero"],
                "span_direct_M": span["span_reference"],
                "span_resolved_M": span["span_arm"],
                "old_band_normalized_reduction": onorm["point_estimate"],
                "old_band_normalized_ci_low": onorm["ci_low"],
                "old_band_normalized_ci_high": onorm["ci_high"],
                "old_band_normalized_excludes_zero": onorm["excludes_zero"],
                "old_band_absolute_reduction": oabs["point_estimate"],
                "old_band_absolute_ci_low": oabs["ci_low"],
                "old_band_absolute_ci_high": oabs["ci_high"],
                "old_band_absolute_excludes_zero": oabs["excludes_zero"],
                "n_truths": span["n_truths"], "n_resamples": n_res,
                "seed": seed, "unit": span["unit"], "freeze_sha256": fh})
    P["out"]["bootstrap_rows"] = rows
    prim_row = next((r for r in rows
                     if r["estimator"] == prim["primary_estimator"]
                     and r["regime"] == prim["regime"]), None)
    if prim_row:
        print(f"bootstrap, {prim['primary_estimator']} on {prim['regime']}: "
              f"delta_L = {prim_row['delta_L_level_M']:.0f} M, 95% CI "
              f"[{prim_row['delta_L_level_ci_low']:.0f}, "
              f"{prim_row['delta_L_level_ci_high']:.0f}]")

    run_id = make_run_id("R1", reg.sha256)
    man = RunManifest(
        run_id=run_id, experiment_id="R1_HELD_OUT_MAIN",
        seeds={"master": P["master"], "streams": P["streams"],
               "bootstrap_seed": seed},
        started_at=P["started"], attestation=P["attestation"],
        extra={"freeze_sha256": fh, "ruling": fz["ruling"],
               "sealed_bank_commitment":
                   fz["sealed_bank"]["commitment_sha256"],
               "null_pair_control_bank":
                   fz["null_pair_control_bank"]["sha256"],
               "uncertainty_disposition": fz["uncertainty"]["disposition"],
               **P["provenance"]})
    man.add_input(ROOT / "artifacts" / "configs" / "R1_MAIN_FREEZE.json")
    for g in P["integrity_gates"]:
        man.add_gate(g)
    ns = P.get("null_summary", {})
    if ns:
        man.add_gate(Gate("R1_G5_null_pair_control_bank",
                          "FAIL" if ns["defect"] or ns["direction_hash_mismatches"]
                          else "PASS",
                          measured=ns["n_exceeding"],
                          threshold=round(ns["expected_exceedances"], 2),
                          note=f"{ns['n_tested']} committed pairs scored "
                               f"against the equal-prior Gaussian Bayes bound; "
                               f"binomial p for the excess "
                               f"{ns['binomial_p_excess']:.3f}; "
                               f"{ns['direction_hash_mismatches']} direction "
                               f"hash mismatches. {ns['rule']}"))
    for name, rows_ in (("r1_stable_depth", P["out"]["depth_rows"]),
                        ("r1_age_errors", P["out"]["age_rows"]),
                        ("r1_family_depth", P["out"]["fam_rows"]),
                        ("r1_data_weak_errors", P["out"]["dw_rows"]),
                        ("r1_level_structure", P["out"]["ls_rows"]),
                        ("r1_bootstrap", P["out"]["bootstrap_rows"]),
                        ("r1_null_pairs", P["out"].get("null_rows", [])),
                        ("r1_runtime", P["out"]["rt_rows"])):
        if rows_:
            man.add_output(write_table(rows_, name))
    mp = man.write(reg.path, reg.sha256, runtime_seconds=time.time() - P["t0"])
    merge_gate_file(man.gates, run_id)
    print(f"manifest {mp}")
    print(f"total {time.time() - P['t0']:.0f}s")
    return 0
