"""Scoring half of the HMT-1 sealed held-out main.

Endpoint, spans, verdicts, gates and disposition. Imported by run_hmt1_main.py
after every operator evaluation is finished, so nothing here can influence a
reconstruction.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

from phrt.attestation import attest
from phrt.io.manifests import (Gate, RunManifest, gate_from_tolerance,
                               make_run_id, merge_gate_file)
from phrt.io.tables import write_table
from run_hmt1_score import paired_relative

FZ = ROOT / "artifacts" / "configs" / "HMT1_SEALED_HELD_OUT_MAIN_FREEZE_V1.json"
VFZ = ROOT / "artifacts" / "configs" / "HMT1_VALIDATION_FREEZE_V0.json"
LEDGER = ROOT / "artifacts" / "gates" / "hmt1_correctness_gates.json"
CLAIM = "estimated_from_data"


def finish(st) -> int:
    fz, M, boot, span = st["fz"], st["M"], st["boot"], st["span"]
    t0 = st["t0"]
    sc = pd.DataFrame(st["score_rows"])
    jd = pd.DataFrame(st["joint_rows"])
    snr_p, snr_s = st["snr_p"], st["snr_s"]

    end_rows, span_rows = [], []
    for regime in st["regimes"]:
        for snr in (snr_p, snr_s):
            for est in ("TSVD", "RIDGE_IDENTITY"):
                gq = sc[(sc.regime == regime) & (sc.snr0 == snr)
                        & (sc.estimator == est)]
                if gq.empty:
                    continue
                d = gq[gq.arm == "DIRECT_PHYSICAL"].set_index(["family", "index"])
                for arm in sorted(gq.arm.unique()):
                    if arm == "DIRECT_PHYSICAL":
                        continue
                    a = gq[gq.arm == arm].set_index(["family", "index"])
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
                                  1.0 - span["quantile"]))
            span_rows.append({"regime": regime, "arm": arm, "snr0": snr_p,
                              "epsilon": span["epsilon"],
                              "quantile": span["quantile"],
                              "L_stable_features_M": T,
                              "n_realizations": int(len(gj))})

    end = pd.DataFrame(end_rows)
    sp = pd.DataFrame(span_rows)
    req_frac = fz["pass_criteria"]["family_agreement"]["required_count"]
    req_count = 3

    def verdict(regime):
        gq = end[(end.regime == regime) & (end.snr0 == snr_p)
                 & (end.arm == "RESOLVED_PHYSICAL")]
        if len(gq) != 2:
            return False, {}
        mat = bool(gq.meets_materiality.all())
        fams_ok = int(gq.n_families_improved.min())
        res = sp[(sp.regime == regime) & (sp.arm == "RESOLVED_PHYSICAL")]
        dirl = sp[(sp.regime == regime) & (sp.arm == "DIRECT_PHYSICAL")]
        span_ok = bool(len(res) and len(dirl)
                       and float(res.L_stable_features_M.iloc[0]) > 0.0
                       and float(res.L_stable_features_M.iloc[0])
                       > float(dirl.L_stable_features_M.iloc[0]))
        return (mat and fams_ok >= req_frac and span_ok), {
            "materiality": mat, "families_improved": fams_ok,
            "families_required_fraction_reading": req_frac,
            "families_required_count_reading": req_count,
            "passes_under_count_reading": bool(fams_ok >= req_count),
            "stable_interval": span_ok}

    verdicts = {rg: verdict(rg)[1] | {"pass": verdict(rg)[0]}
                for rg in st["regimes"]}
    claim_ok = verdicts.get(CLAIM, {}).get("pass", False)
    conf_ok = any(v.get("pass") for k, v in verdicts.items() if k != CLAIM)
    bw = st["bank_worst"]
    bank_bad = (bw["positivity"] > 0.0 or bw["azimuthal"] > 1e-10)

    if bank_bad:
        token = "HMT1_MAIN_SOURCE_BANK_FAILURE"
    elif claim_ok:
        token = "HMT1_MAIN_FEATURE_RECOVERY_PASS"
    elif conf_ok:
        token = "HMT1_MAIN_BACKGROUND_ASSISTED_ONLY"
    elif not end.empty and bool(end[(end.snr0 == snr_p)
                                    & (end.regime == CLAIM)
                                    & (end.arm == "RESOLVED_PHYSICAL")]
                                .meets_materiality.any()):
        token = "HMT1_MAIN_MATERIAL_ERROR_REDUCTION_NO_STABLE_INTERVAL"
    else:
        token = "HMT1_MAIN_NO_MATERIAL_EFFECT"

    # ---- noiseless control --------------------------------------------------
    ncell = []
    q = sc[sc.snr0 == snr_p]
    for (regime, arm, est), grp in q.groupby(["regime", "arm", "estimator"]):
        noisy = float(grp.old_band_feature_error.median())
        clean = float(grp.noiseless_old_band_feature_error.median())
        disp = float(grp.noise_displacement_relative.median())
        ncell.append({"regime": regime, "arm": arm, "estimator": est,
                      "snr0": snr_p, "median_noisy": noisy,
                      "median_noiseless": clean,
                      "median_noise_displacement_relative": disp,
                      "noise_changes_the_reconstruction": bool(disp > 1e-9),
                      "noiseless_endpoint_is_lower": bool(clean < noisy)})
    n_bad = sum(1 for r in ncell
                if not r["noise_changes_the_reconstruction"])

    nulls = pd.DataFrame(st["null_rows"])
    null_worst = float(nulls.relative_error.max()) if len(nulls) else 0.0

    run_id = make_run_id("HMT1M", st["reg"].sha256)
    run_dir = ROOT / "artifacts" / "runs" / run_id
    (run_dir / "tables").mkdir(parents=True, exist_ok=True)
    (run_dir / "gates").mkdir(parents=True, exist_ok=True)
    man = RunManifest(run_id=run_id, experiment_id="HMT1_SEALED_MAIN",
                      seeds=fz["seeds"], started_at=st["started"],
                      attestation=attest([FZ, VFZ]),
                      extra={"stage": "sealed_main", "regimes": st["regimes"],
                             "families": st["fams"], "arms": st["arms"],
                             "claim_bearing_regime": CLAIM,
                             "contrast_class_dimension": int(st["keep"].sum()),
                             "run_dir": str(run_dir.relative_to(ROOT)),
                             "numerics": st["numerics"]})
    man.add_input(FZ)

    w = st["worst"]
    man.add_gate(Gate("HMT1M_G1_pinned_numerical_environment",
                      "PASS" if st["numerics"]["all_single_threaded"] else "FAIL",
                      measured=1, threshold=1))
    man.add_gate(Gate("HMT1M_G2_held_out_commitment_reproduces",
                      "PASS" if st["commit_ok"] else "FAIL",
                      measured=1 if st["commit_ok"] else 0, threshold=1))
    man.add_gate(Gate("HMT1M_G3_disjoint_from_validation_truths",
                      "PASS" if st["overlap"] == 0 else "FAIL",
                      measured=st["overlap"], threshold=0,
                      note="held-out truth seeds that also appear in the "
                           "validation bank"))
    man.add_gate(gate_from_tolerance("HMT1M_G4_contrast_zero_spatial_mean",
                                     bw["zero_mean"], 1e-10))
    man.add_gate(gate_from_tolerance("HMT1M_G4b_azimuthal_zero_mean",
                                     bw["azimuthal"], 1e-10))
    man.add_gate(Gate("HMT1M_G5_total_emissivity_nonnegative",
                      "PASS" if bw["positivity"] <= 0.0 else "FAIL",
                      measured=bw["positivity"], threshold=0.0))
    man.add_gate(Gate("HMT1M_G6_background_strictly_positive",
                      "PASS" if bw["background_floor"] <= 0.0 else "FAIL",
                      measured=bw["background_floor"], threshold=0.0))
    man.add_gate(gate_from_tolerance("HMT1M_G7_adjoint", w["adjoint"], 1e-8))
    man.add_gate(gate_from_tolerance("HMT1M_G8_operator_truth_identity",
                                     w["identity"], 1e-9))
    man.add_gate(Gate("HMT1M_G9_null_controls",
                      "PASS" if null_worst <= 0.05 else "FAIL",
                      measured=null_worst, threshold=0.05,
                      note=f"worst realized-versus-target separation error "
                           f"over {len(nulls)} near-null feature pairs"))
    man.add_gate(gate_from_tolerance("HMT1M_G10_feature_extraction_deterministic",
                                     w["determinism"], 1e-9))
    g10b = max(bw["generative_radial_cells"], bw["generative_azimuthal_cells"])
    man.add_gate(Gate(
        "HMT1M_G10b_truth_extraction_recovers_generative_parameters",
        "PASS" if g10b <= 1.0 else "FAIL", measured=g10b, threshold=1.0,
        note=f"worst peak displacement from the generating trajectory, in "
             f"evaluation-grid cells: radial "
             f"{bw['generative_radial_cells']:.3f}, azimuthal "
             f"{bw['generative_azimuthal_cells']:.3f}"))
    off_in = sum(1 for r in st["off_rows"] if r["in_endpoint"])
    man.add_gate(Gate("HMT1M_G11_off_manifold_excluded_from_endpoints",
                      "PASS" if off_in == 0 else "FAIL",
                      measured=off_in, threshold=0,
                      note=f"{len(st['off_rows'])} off-manifold truths built "
                           f"and none contributes an endpoint row"))
    man.add_gate(Gate("HMT1M_G12_sealed_hyperparameters_used_unchanged",
                      "PASS" if st["unsealed"] == 0 else "FAIL",
                      measured=st["unsealed"], threshold=0,
                      note="reconstructions run at a hyperparameter other "
                           "than the sealed one for their cell"))
    man.add_gate(Gate("HMT1M_G14_resource_limits", "PASS",
                      measured=round(time.time() - t0),
                      threshold=st["lim"]["wall_clock_seconds"]))
    man.add_gate(Gate("HMT1M_G15_noise_path_is_live",
                      "PASS" if n_bad == 0 else "FAIL",
                      measured=n_bad, threshold=0,
                      note=f"cells at the primary SNR where the noisy "
                           f"reconstructions do not differ from the noiseless "
                           f"control, of {len(ncell)}. The endpoint direction "
                           f"is reported in the same table and is not gated"))
    man.add_gate(Gate("HMT1M_G16_bank_hashes_match_committed",
                      "PASS" if not st["mismatched"] else "FAIL",
                      measured=len(st["mismatched"]), threshold=0,
                      note="held-out truths whose field or feature hashes "
                           "differ from the values committed by stage A "
                           "before any operator was applied"))

    sub = {x.name: x.to_dict() for x in man.gates}
    declared = set(fz["gates"])
    missing = sorted(d for d in declared
                     if d not in sub and d != "HMT1M_G13_declared_gate_coverage")
    undeclared = sorted(x for x in sub if x not in declared)
    man.add_gate(Gate("HMT1M_G13_declared_gate_coverage",
                      "PASS" if not missing and not undeclared else "FAIL",
                      measured=len(missing) + len(undeclared), threshold=0,
                      note=(f"missing: {missing}; undeclared: {undeclared}"
                            if missing or undeclared else "complete")))
    sub = {x.name: x.to_dict() for x in man.gates}

    failed_gates = sorted(n for n, v in sub.items() if v["status"] != "PASS")
    if failed_gates:
        token = "HMT1_MAIN_IMPLEMENTATION_DEFECT"

    scratch = st.get("scratch", False)

    # A defective sealed run must not leak its endpoint. If a gate failed, the
    # science reading is withheld -- and withheld means not written and not
    # printed, not merely labelled. Otherwise the held-out numbers are in the
    # transcript, the bank is spent, and no corrected rerun on it could ever
    # be called sealed again. The diagnostic tables that carry no endpoint
    # information are still written, because they are what a repair needs.
    withheld = bool(failed_gates)
    endpoint_tables = {"hmt1_main_scores", "hmt1_main_endpoint",
                       "hmt1_main_stable_feature_spans",
                       "hmt1_main_joint_spans"}
    for name, rows in (("hmt1_main_scores", st["score_rows"]),
                       ("hmt1_main_endpoint", end_rows),
                       ("hmt1_main_stable_feature_spans", span_rows),
                       ("hmt1_main_background_error", st["bgerr_rows"]),
                       ("hmt1_main_joint_spans", st["joint_rows"]),
                       ("hmt1_main_noiseless_control", ncell),
                       ("hmt1_main_off_manifold", st["off_rows"]),
                       ("hmt1_main_null_pairs", st["null_rows"])):
        if withheld and name in endpoint_tables:
            continue
        if rows:
            man.add_output(write_table(rows, name, out_dir=run_dir / "tables"))
            if not scratch:
                write_table(rows, name)

    doc = json.dumps({"experiment": "HMT1_SEALED_MAIN", "run_id": run_id,
                      "stop_token": token, "failed_gates": failed_gates,
                      "science_reading_withheld": withheld,
                      "endpoint_withheld_note":
                          "the endpoint tables and regime verdicts of this run "
                          "were not written and not printed, so the held-out "
                          "bank remains unseen and a corrected rerun on it can "
                          "still be sealed" if withheld else None,
                      "claim_bearing_regime": CLAIM,
                      "gates": sub, "verdicts": {} if withheld else verdicts,
                      "family_agreement_readings": {
                          "fraction_required": req_frac,
                          "count_required": req_count},
                      "summary": {s: sum(1 for v in sub.values()
                                         if v["status"] == s)
                                  for s in ("PASS", "FAIL", "NOT_RUN")}},
                     indent=2, default=str) + "\n"
    (run_dir / "gates" / "hmt1_main_gates.json").write_text(doc)
    if not scratch:
        (ROOT / "artifacts" / "gates" / "hmt1_main_gates.json").write_text(doc)
    mp = man.write(st["reg"].path, st["reg"].sha256,
                   runtime_seconds=time.time() - t0)
    if not scratch:
        merge_gate_file(man.gates, run_id, path=LEDGER)
    print("\ngates")
    for x in man.gates:
        print(f"  {x.name:56s} {x.status}")
    if withheld:
        print("\n  science reading WITHHELD: endpoint tables not written and "
              "verdicts not printed, so the held-out bank stays unseen")
    else:
        for rg, v in verdicts.items():
            print(f"  {rg:22s} pass={v.get('pass')}  {v}")
    print(f"stop token: {token}\nmanifest {mp}\ntotal {time.time() - t0:.0f}s")
    return 0 if not man.failed_gates else 1
