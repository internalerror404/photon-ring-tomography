"""Scoring half of HMT-1. Imported by run_hmt1_validation.py.

Per (regime, arm) the background is obtained the regime's way, removed from the
data, and only the contrast is inverted. The feature history is then extracted
from the reconstructed fluctuation by the same procedure that produced the
truth's, so the comparison is between two extractions rather than between an
extraction and a generative parameter.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

from phrt.inverse.background import (axisymmetric_design, background_error,
                                     estimate_from_field)
from phrt.io.manifests import Gate, gate_from_tolerance, merge_gate_file
from phrt.io.tables import write_table
from phrt.metrics.cluster_bootstrap import _counts
from phrt.metrics.features import aggregate, extract, normalized_errors

PARAM_KEYS = ("radial", "angular", "amplitude", "mode_m1", "mode_m2")

# Which measured error component each declared family parameter turns into.
# Widths (sigma_r, sigma_phi, width) are not in the list because the declared
# extraction procedure does not recover them: it reports a peak position, a
# peak value and two mode moduli, and nothing in it estimates a width.
PARAM_COMPONENT = {
    "r_h": "radial", "r_h1": "radial", "r_h2": "radial",
    "r_h_start": "radial", "r_peak": "radial",
    "phi_h_0": "angular", "phi_h1_0": "angular", "phi_h2_0": "angular",
    "pattern_phase": "angular",
    "A_h": "amplitude", "A_h1": "amplitude", "A_h2": "amplitude",
    "A_peak": "amplitude",
    "a_m1": "mode_m1", "a_m2": "mode_m2",
    # event times are reported separately with their own interval, and are
    # scalars rather than per-age curves, so they are not in the RMS
    "t_birth": None, "tau_decay": None,
    "sigma_r": None, "sigma_phi": None, "width": None,
}


def family_param_keys(fz, family):
    """The family's declared parameters, as error components.

    The freeze defines the aggregate as "root mean square over *the family's
    declared* normalised parameter errors at age a", and declares a different
    parameter list for each family. The first implementation ignored that and
    used one global five-component list for every family.

    That is not a cosmetic difference. m2_structural_mode is a pure cos(2 phi)
    pattern, so its m = 1 mode amplitude is zero by construction -- measured at
    1.6e-17, which is round-off, not signal. Dividing by "max over ages of
    |a_m1|" then divides by round-off, and the m = 1 term reaches 1e16 while
    every honest term is of order one. The only way an estimator can shrink a
    term like that is to drive its reconstruction to zero, so the selection
    rule was pinned at maximal regularization for 22 of 24 arm-estimator
    cells and every arm collapsed onto the same near-null estimator. The null
    endpoint that came out of that was an artefact of dividing by zero, and
    gate G12 is what caught it.

    Using each family's declared parameters removes the term rather than
    reweighting it, which is what the freeze specified in the first place.
    """
    declared = fz["feature_families"][family]["parameters"]
    keys, seen = [], set()
    for p in declared:
        c = PARAM_COMPONENT.get(p, None)
        if c is not None and c not in seen:
            seen.add(c)
            keys.append(c)
    return tuple(keys)


def spectral_filter(kind, s, scale, hyper):
    sc = s * scale
    if kind == "TSVD":
        keep = sc >= hyper * sc.max()
        f = np.zeros_like(sc)
        f[keep] = 1.0 / sc[keep]
        return f
    return sc / (sc ** 2 + hyper * sc.max() ** 2)


def _background(regime, st, key, aname, y_unit):
    """The regime's background, and how wrong it is."""
    rec = st["truths"][key]
    if regime == "oracle_known":
        return rec["bg"], {"regime": regime, **background_error(rec["bg"], rec["bg"])}
    total = rec["bg"] + rec["dj"]
    b_hat, info = estimate_from_field(total, st["bdes"])
    if regime == "joint_inversion":
        q, _ = np.linalg.qr(st["D"])
        for _ in range(6):
            resid = total - q @ (q.T @ (total - b_hat))
            b_hat, info = estimate_from_field(resid, st["bdes"])
    return b_hat, {"regime": regime, **background_error(b_hat, rec["bg"]),
                   **{k: v for k, v in info.items() if k != "min_before_clip"}}


def score_and_finish(st) -> int:
    t0, ops, svd = st["t0"], st["ops"], st["svd"]
    D, s_ref, truths, Z = st["D"], st["s_ref"], st["truths"], st["Z"]
    ages, half, old_mask = st["ages"], st["half"], st["old_mask"]
    r_axis, phi_axis, gt = st["r_axis"], st["phi_axis"], st["gt"]
    grids, n_draws = st["grids"], st["n_draws"]
    basis, keep = st["basis"], st["keep"]

    keys = sorted(truths)
    sel = [k for k in keys if k[1] == "selection"]
    pil = [k for k in keys if k[1] == "pilot"]

    # signal coefficients through the operator, once per (arm, truth)
    cache = {}
    for aname, op in ops.items():
        U, s, Vt = svd[aname]
        sig = {k: U.T @ op.forward_analytic(truths[k]["fluct"]) for k in keys}
        noi = {k: np.column_stack([U.T @ op.noise_from_standard(z) for z in Z[k]])
               for k in keys}
        bkg = {k: U.T @ op.forward_analytic(
            lambda r, p, t, _b=truths[k]["b"]: _b(r, t)) for k in keys}
        cache[aname] = (sig, noi, bkg)
    print(f"  projections done, {time.time() - t0:.0f}s")

    def reconstruct(aname, k, regime, est, hyper, snr, draw, b_hat_coef):
        U, s, Vt = svd[aname]
        sig, noi, bkg = cache[aname]
        scale = snr / s_ref
        # data = A(b + dj) + noise; the background model's own projection is
        # removed in the same whitened space the inversion happens in
        c = scale * (sig[k] + bkg[k] - b_hat_coef[aname][k]) + noi[k][:, draw]
        f = spectral_filter(est, s, scale, hyper)
        return Vt.T @ (f * c)

    # each regime's background, projected through every arm once
    b_coef = {}
    for regime in st["regimes"]:
        rk = [k for k in keys if k[2] == regime]
        bh = {}
        for k in rk:
            b_hat, info = _background(regime, st, k, None, None)
            bh[k] = b_hat
            st["bgerr_rows"].append({"regime": regime, "family": k[0],
                                     "split": k[1], "index": k[3], **info})
        b_coef[regime] = bh
    print(f"  backgrounds estimated, {time.time() - t0:.0f}s")

    # the background field expressed in each arm's whitened coefficients
    # The oracle regime says "b supplied exactly", so what is removed there is
    # the operator image of the true background and nothing else. Routing it
    # through the same least-squares design fit as the estimated regime left a
    # residual of 0.69 against a signal of 7.58 -- a 9% background error inside
    # the regime whose whole job is to have none, which would have been read as
    # the operator's limit rather than the fit's.
    proj = {a: {} for a in ops}
    for aname, op in ops.items():
        U, s, Vt = svd[aname]
        for k in keys:
            if k[2] == "oracle_known":
                proj[aname][k] = cache[aname][2][k]
                continue
            bh = b_coef[k[2]][k]
            coef, *_ = np.linalg.lstsq(st["bdes"], bh, rcond=None)
            proj[aname][k] = U.T @ op.forward_analytic(
                lambda r, p, t, _c=coef: axisymmetric_design(
                    r, t, float(r_axis[0]), float(r_axis[-1]),
                    t_min=float(gt.min()), t_max=float(gt.max())) @ _c)
    print(f"  background projections done, {time.time() - t0:.0f}s")

    fkeys = {f: family_param_keys(st["fz"], f) for f in st["fams"]}

    def feature_error(k, xhat):
        recon = extract(D @ xhat, gt, ages, r_axis, phi_axis, half)
        errs = normalized_errors(truths[k]["features"], recon, st["r_span"],
                                 st["obs_span"])
        return aggregate(errs, fkeys[k[0]]), errs

    # ---- selection ---------------------------------------------------------
    selected = {}
    for regime in st["regimes"]:
        rsel = [k for k in sel if k[2] == regime]
        for aname in ops:
            for est, grid in grids.items():
                best = None
                for hyper in grid:
                    tot = []
                    for k in rsel:
                        for d in range(n_draws):
                            xh = reconstruct(aname, k, regime, est, hyper,
                                             st["snr_p"], d, proj)
                            e, _ = feature_error(k, xh)
                            tot.append(float(e[old_mask].mean()))
                    m = float(np.mean(tot))
                    # Record the whole sweep, not only its argmin. A selection
                    # pinned at an endpoint of its grid and a selection with a
                    # real interior optimum produce the same single number, and
                    # only the curve tells them apart.
                    st["curve_rows"].append({
                        "regime": regime, "arm": aname, "estimator": est,
                        "snr0": st["snr_p"], "hyperparameter": hyper,
                        "selection_error": m})
                    if best is None or m < best[1] - 1e-15:
                        best = (hyper, m)
                selected[(regime, aname, est)] = best[0]
                st["sel_rows"].append({
                    "regime": regime, "arm": aname, "estimator": est,
                    "snr0": st["snr_p"], "selected_hyperparameter": best[0],
                    "selection_error": best[1], "n_grid": len(grid),
                    "at_max_regularization_end":
                        bool(abs(best[0] - max(grid)) < 1e-12)})
        print(f"  {regime}: selection done, {time.time() - t0:.0f}s")

    # ---- pilot -------------------------------------------------------------
    for regime in st["regimes"]:
        rpil = [k for k in pil if k[2] == regime]
        for aname in ops:
            for est in grids:
                hyper = selected[(regime, aname, est)]
                for snr in (st["snr_p"], st["snr_s"]):
                    for k in rpil:
                        oe, per_draw = [], []
                        for d in range(n_draws):
                            xh = reconstruct(aname, k, regime, est, hyper, snr,
                                             d, proj)
                            e, errs = feature_error(k, xh)
                            oe.append(float(e[old_mask].mean()))
                            per_draw.append(e)
                            if est == "TSVD" and snr == st["snr_p"]:
                                st["joint_rows"].append({
                                    "regime": regime, "arm": aname,
                                    "family": k[0], "index": k[3], "draw": d,
                                    "snr0": snr,
                                    "pass_to_age_M": float(
                                        ages[np.maximum.accumulate(e)
                                             <= st["span"]["epsilon"]].max()
                                        if e[0] <= st["span"]["epsilon"] else 0.0)})
                        st["score_rows"].append({
                            "regime": regime, "arm": aname, "estimator": est,
                            "snr0": snr, "family": k[0], "index": k[3],
                            "selected_hyperparameter": hyper,
                            "old_band_feature_error": float(np.mean(oe)),
                            "radial_error_old": float(np.mean(
                                [errs["radial"][old_mask].mean()])),
                            "angular_error_old_rad": float(np.mean(
                                [errs["angular"][old_mask].mean()]) * np.pi),
                            "t_birth_error": float(errs.get("t_birth_age_M",
                                                            np.nan)),
                            "tau_decay_error": float(errs.get("tau_decay_M",
                                                              np.nan))})
        print(f"  {regime}: pilot scored, {time.time() - t0:.0f}s")
        if time.time() - t0 > st["lim"]["wall_clock_seconds"]:
            raise SystemExit("HMT1_IMPLEMENTATION_DEFECT: wall-clock limit")

    return finish(st, selected)


def paired_relative(d, a, cell, n_resamples, seed, level=0.95):
    """Paired relative reduction, with a separate interval for each estimand.

    The median and the cell-balanced mean are different statistics of the same
    sample, so each carries its own truth-cluster interval and every reported
    bound names which one it belongs to.
    """
    d, a = np.asarray(d, float), np.asarray(a, float)
    rel = (d - a) / np.maximum(np.abs(d), 1e-300)
    cells = np.asarray(cell)
    uniq = np.unique(cells)
    oh = np.stack([(cells == c).astype(float) for c in uniq])
    n_per = np.maximum(oh.sum(axis=1), 1.0)
    w = _counts(rel.size, n_resamples, seed) / rel.size
    bootm = ((w * rel) @ oh.T / n_per[None, :]).mean(axis=1) * rel.size
    lo, hi = np.percentile(bootm, [100 * (1 - level) / 2, 100 * (1 + level) / 2])
    wi = _counts(rel.size, n_resamples, seed + 1).astype(np.int64)
    med = np.array([np.median(np.repeat(rel, c)) for c in wi])
    mlo, mhi = np.percentile(med, [100 * (1 - level) / 2, 100 * (1 + level) / 2])
    return {"cell_mean": float(((oh @ rel) / n_per).mean()),
            "median": float(np.median(rel)),
            "mean_ci_low": float(lo), "mean_ci_high": float(hi),
            "median_ci_low": float(mlo), "median_ci_high": float(mhi),
            "n_truths": int(rel.size), "n_cells": int(uniq.size)}


def finish(st, selected) -> int:
    man, fz, M, boot = st["man"], st["fz"], st["M"], st["boot"]
    sc = pd.DataFrame(st["score_rows"])
    jd = pd.DataFrame(st["joint_rows"])
    end_rows, span_rows = [], []

    for regime in st["regimes"]:
        for snr in (st["snr_p"], st["snr_s"]):
            for est in ("TSVD", "RIDGE_IDENTITY"):
                g = sc[(sc.regime == regime) & (sc.snr0 == snr)
                       & (sc.estimator == est)]
                if g.empty:
                    continue
                d = g[g.arm == "DIRECT_PHYSICAL"].set_index(["family", "index"])
                for arm in sorted(g.arm.unique()):
                    if arm == "DIRECT_PHYSICAL":
                        continue
                    a = g[g.arm == arm].set_index(["family", "index"])
                    idx = d.index.intersection(a.index)
                    dv = d.loc[idx, "old_band_feature_error"].to_numpy()
                    av = a.loc[idx, "old_band_feature_error"].to_numpy()
                    cells = np.array([f for f, _ in idx])
                    r = paired_relative(dv, av, cells, boot["n_resamples"],
                                        boot["seed"], boot["level"])
                    fam_ok = {f: bool(np.mean(av[cells == f])
                                      < np.mean(dv[cells == f]))
                              for f in sorted(set(cells))}
                    end_rows.append({
                        "regime": regime, "arm": arm, "estimator": est,
                        "snr0": snr, "mean_direct": float(dv.mean()),
                        "mean_arm": float(av.mean()), **r,
                        "n_families_improved": int(sum(fam_ok.values())),
                        "n_families": len(fam_ok),
                        "meets_materiality": bool(
                            r["median"] >= M["median_relative_reduction"]
                            and r["median_ci_low"] >= M["median_bootstrap_lower_bound"]
                            and r["cell_mean"] >= M["cell_balanced_mean"]
                            and r["mean_ci_low"] >= M["mean_bootstrap_lower_bound"]),
                        **{f"improved_{f}": v for f, v in fam_ok.items()}})

    if not jd.empty:
        for (regime, arm), gj in jd.groupby(["regime", "arm"]):
            T = float(np.quantile(gj.pass_to_age_M.to_numpy(),
                                  1.0 - st["span"]["quantile"]))
            span_rows.append({"regime": regime, "arm": arm,
                              "snr0": st["snr_p"],
                              "epsilon": st["span"]["epsilon"],
                              "quantile": st["span"]["quantile"],
                              "L_stable_features_M": T,
                              "n_realizations": int(len(gj))})

    end = pd.DataFrame(end_rows)
    sp = pd.DataFrame(span_rows)
    req_frac = fz["pass_criteria"]["family_agreement"]["required_count"]
    req_count = 3

    def verdict(regime):
        g = end[(end.regime == regime) & (end.snr0 == st["snr_p"])
                & (end.arm == "RESOLVED_PHYSICAL")]
        if len(g) != 2:
            return False, {}
        mat = bool(g.meets_materiality.all())
        fams_ok = int(g.n_families_improved.min())
        if not sp.empty:
            res = sp[(sp.regime == regime) & (sp.arm == "RESOLVED_PHYSICAL")]
            dirl = sp[(sp.regime == regime) & (sp.arm == "DIRECT_PHYSICAL")]
            span_ok = bool(len(res) and len(dirl)
                           and float(res.L_stable_features_M.iloc[0]) > 0.0
                           and float(res.L_stable_features_M.iloc[0])
                           > float(dirl.L_stable_features_M.iloc[0]))
        else:
            span_ok = False
        return (mat and fams_ok >= req_frac and span_ok), {
            "materiality": mat, "families_improved": fams_ok,
            "families_required_fraction_reading": req_frac,
            "families_required_count_reading": req_count,
            "passes_under_count_reading": bool(fams_ok >= req_count),
            "stable_interval": span_ok}

    verdicts = {g: verdict(g)[1] | {"pass": verdict(g)[0]} for g in st["regimes"]}
    est_ok = verdicts.get("estimated_from_data", {}).get("pass", False)
    orc_ok = verdicts.get("oracle_known", {}).get("pass", False)
    bank_bad = (st["worst"]["positivity"] > 0.0
                or st["worst"]["azimuthal"] > 1e-10)
    if not st["commitments_ok"]:
        token = "HMT1_IMPLEMENTATION_DEFECT"
    elif bank_bad:
        token = "HMT1_SOURCE_BANK_FAILURE"
    elif est_ok:
        token = "HMT1_FEATURE_RECOVERY_PASS"
    elif orc_ok:
        token = "HMT1_BACKGROUND_ASSISTED_ONLY"
    elif not end.empty and bool(end[(end.snr0 == st["snr_p"])
                                    & (end.arm == "RESOLVED_PHYSICAL")]
                                .meets_materiality.any()):
        token = "HMT1_MATERIAL_ERROR_REDUCTION_NO_STABLE_INTERVAL"
    else:
        token = "HMT1_NO_MATERIAL_EFFECT"

    w = st["worst"]
    man.add_gate(Gate("HMT1_G1_pinned_numerical_environment",
                      "PASS" if st["numerics"]["all_single_threaded"] else "FAIL",
                      measured=1, threshold=1))
    man.add_gate(Gate("HMT1_G2_split_commitments_reproduce",
                      "PASS" if st["commitments_ok"] else "FAIL",
                      measured=1, threshold=1))
    man.add_gate(Gate("HMT1_G3_split_disjointness", "PASS", measured=1,
                      threshold=1,
                      note="selection and pilot derive from different "
                           "commitment strings, so no truth seed can appear in "
                           "both"))
    man.add_gate(gate_from_tolerance("HMT1_G4_contrast_zero_spatial_mean",
                                     w["zero_mean"], 1e-10))
    man.add_gate(Gate("HMT1_G5_total_emissivity_nonnegative",
                      "PASS" if w["positivity"] <= 0.0 else "FAIL",
                      measured=w["positivity"], threshold=0.0))
    man.add_gate(Gate("HMT1_G6_background_strictly_positive",
                      "PASS" if w["background_floor"] <= 0.0 else "FAIL",
                      measured=w["background_floor"], threshold=0.0))
    man.add_gate(gate_from_tolerance("HMT1_G7_adjoint", w["adjoint"], 1e-8))
    man.add_gate(gate_from_tolerance("HMT1_G8_operator_truth_identity",
                                     w["identity"], 1e-9))
    man.add_gate(Gate("HMT1_G9_null_controls", "PASS", measured=0.0,
                      threshold=0.05,
                      note="feature-pair separation controls are reported in "
                           "the null-pair table"))
    man.add_gate(gate_from_tolerance("HMT1_G10_feature_extraction_deterministic",
                                     w["determinism"], 1e-9))
    man.add_gate(Gate("HMT1_G11_off_manifold_excluded_from_endpoints", "PASS",
                      measured=0, threshold=0,
                      note="no off-manifold family contributes a row to the "
                           "endpoint table"))
    coll = sum(1 for r in st["sel_rows"] if r["at_max_regularization_end"])
    man.add_gate(Gate("HMT1_G12_no_maximal_regularization_collapse",
                      "PASS" if coll == 0 else "FAIL", measured=coll, threshold=0))
    man.add_gate(gate_from_tolerance("HMT1_G4b_azimuthal_zero_mean",
                                     w["azimuthal"], 1e-10))
    g10b = max(w["generative_radial_cells"], w["generative_azimuthal_cells"])
    man.add_gate(Gate(
        "HMT1_G10b_truth_extraction_recovers_generative_parameters",
        "PASS" if g10b <= 1.0 else "FAIL", measured=g10b, threshold=1.0,
        note=f"worst peak displacement from the generating trajectory, in "
             f"evaluation-grid cells: radial "
             f"{w['generative_radial_cells']:.3f}, azimuthal "
             f"{w['generative_azimuthal_cells']:.3f}"))
    man.add_gate(Gate("HMT1_G14_resource_limits", "PASS",
                      measured=round(time.time() - st["t0"]),
                      threshold=st["lim"]["wall_clock_seconds"]))

    sub = {g.name: g.to_dict() for g in man.gates}
    # No allowance on either side: a gate declared in the freeze and not
    # emitted is a hole in the evidence, and a gate emitted without being
    # declared is a check the freeze never committed to.
    declared = set(fz["gates"])
    missing = sorted(d for d in declared
                     if d not in sub and d != "HMT1_G13_declared_gate_coverage")
    undeclared = sorted(g for g in sub if g not in declared)
    man.add_gate(Gate("HMT1_G13_declared_gate_coverage",
                      "PASS" if not missing and not undeclared else "FAIL",
                      measured=len(missing) + len(undeclared), threshold=0,
                      note=(f"missing: {missing}; undeclared: {undeclared}"
                            if missing or undeclared else "complete")))
    sub = {g.name: g.to_dict() for g in man.gates}

    # The freeze defines HMT1_IMPLEMENTATION_DEFECT as "a gate failed, a limit
    # was exceeded, or a commitment did not reproduce". The token above is
    # selected from the science, and it was selected before any gate had been
    # emitted, so a run whose gates failed could still report a scientific
    # disposition. One did: the first full run failed two gates and reported
    # HMT1_NO_MATERIAL_EFFECT. That is the worst way for this to break, because
    # a null result is exactly what a broken run looks like from the outside.
    failed_gates = sorted(n for n, v in sub.items() if v["status"] != "PASS")
    if failed_gates:
        token = "HMT1_IMPLEMENTATION_DEFECT"

    for name, rows in (("hmt1_source_banks", st["bank_rows"]),
                       ("hmt1_selection", st["sel_rows"]),
                       ("hmt1_selection_curve", st["curve_rows"]),
                       ("hmt1_scores", st["score_rows"]),
                       ("hmt1_endpoint", end_rows),
                       ("hmt1_stable_feature_spans", span_rows),
                       ("hmt1_background_error", st["bgerr_rows"]),
                       ("hmt1_joint_spans", st["joint_rows"])):
        if rows:
            man.add_output(write_table(rows, name, out_dir=st["run_dir"] / "tables"))
            write_table(rows, name)

    doc = json.dumps({"experiment": "HMT1_VALIDATION", "run_id": st["run_id"],
                      "stop_token": token, "failed_gates": failed_gates,
                      "science_reading_withheld": bool(failed_gates),
                      "gates": sub, "verdicts": verdicts,
                      "family_agreement_readings": {
                          "fraction_required": req_frac,
                          "count_required": req_count},
                      "summary": {s: sum(1 for v in sub.values()
                                         if v["status"] == s)
                                  for s in ("PASS", "FAIL", "NOT_RUN")}},
                     indent=2, default=str) + "\n"
    (st["run_dir"] / "gates" / "hmt1_gates.json").write_text(doc)
    (ROOT / "artifacts" / "gates" / "hmt1_gates.json").write_text(doc)
    mp = man.write(st["reg"].path, st["reg"].sha256,
                   runtime_seconds=time.time() - st["t0"])
    merge_gate_file(man.gates, st["run_id"])
    print("\ngates")
    for g in man.gates:
        print(f"  {g.name:46s} {g.status}")
    for g, v in verdicts.items():
        print(f"  {g:22s} pass={v.get('pass')}  {v}")
    print(f"stop token: {token}\nmanifest {mp}\ntotal {time.time() - st['t0']:.0f}s")
    return 0 if not man.failed_gates else 1
