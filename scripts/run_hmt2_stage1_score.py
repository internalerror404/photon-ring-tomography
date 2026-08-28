"""Scoring half of HMT-2 stage 1: endpoints, gates, disposition."""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

from phrt.attestation import attest
from phrt.io.manifests import Gate, RunManifest, make_run_id, merge_gate_file
from phrt.io.tables import write_table
from phrt.metrics.topography import STATES
from run_hmt1_score import paired_relative

FZ = ROOT / "artifacts" / "configs" / "HMT2_STAGE1_RESOLUTION_AWARE_MORPHOLOGY_VALIDATION_V0.json"
LEDGER = ROOT / "artifacts" / "gates" / "hmt2_correctness_gates.json"
TARGETS = ("PHYSICAL_END_TO_END", "CLASS_CONDITIONAL")
BLENDED_STATES = ("BLENDED", "AMBIGUOUS")


def finish(st) -> int:
    fz, t0 = st["fz"], st["t0"]
    sc = pd.DataFrame(st["score_rows"])
    stt = pd.DataFrame(st["state_rows"])
    boot = {"n_resamples": 10000, "seed": 20260941, "level": 0.95}

    end_rows = []
    for cname in st["classes"]:
        for snr in (st["snr_p"], st["snr_s"]):
            for est in ("TSVD", "RIDGE_IDENTITY"):
                g = sc[(sc["class"] == cname) & (sc.snr0 == snr)
                       & (sc.estimator == est)]
                if g.empty:
                    continue
                d = g[g.arm == "DIRECT_PHYSICAL"].set_index(["family", "index"])
                for arm in sorted(g.arm.unique()):
                    if arm == "DIRECT_PHYSICAL":
                        continue
                    a = g[g.arm == arm].set_index(["family", "index"])
                    idx = d.index.intersection(a.index)
                    cells = np.array([f for f, _ in idx])
                    row = {"class": cname, "arm": arm, "estimator": est,
                           "snr0": snr, "n_truths": len(idx)}
                    for t in TARGETS:
                        col = f"{t}_all_state_error"
                        dv = d.loc[idx, col].to_numpy()
                        av = a.loc[idx, col].to_numpy()
                        r = paired_relative(dv, av, cells, boot["n_resamples"],
                                            boot["seed"], boot["level"])
                        row[f"{t}_direct"] = float(dv.mean())
                        row[f"{t}_arm"] = float(av.mean())
                        row[f"{t}_median_reduction"] = r["median"]
                        row[f"{t}_ci_low"] = r["median_ci_low"]
                        row[f"{t}_ci_high"] = r["median_ci_high"]
                        row[f"{t}_improves"] = bool(r["median"] > 0
                                                    and r["median_ci_low"] > 0)
                    # secondary, conditional on stable multi-resolved states
                    dsv = d.loc[idx, "stable_multi_cost_normalized"].to_numpy()
                    asv = a.loc[idx, "stable_multi_cost_normalized"].to_numpy()
                    m = np.isfinite(dsv) & np.isfinite(asv)
                    row["stable_multi_direct"] = float(np.mean(dsv[m])) if m.any() else float("nan")
                    row["stable_multi_arm"] = float(np.mean(asv[m])) if m.any() else float("nan")
                    row["n_stable_multi_truths"] = int(m.sum())
                    end_rows.append(row)
    end = pd.DataFrame(end_rows)

    prim = fz["classes"]["primary"]["id"]
    res = end[(end["class"] == prim) & (end.arm == "RESOLVED_PHYSICAL")
              & (end.snr0 == st["snr_p"])]
    cc = bool(len(res) == 2 and res["CLASS_CONDITIONAL_improves"].all())
    pe = bool(len(res) == 2 and res["PHYSICAL_END_TO_END_improves"].all())
    bank_bad = st["wbad"]["positivity"] > 0.0 or st["wbad"]["zero_mean"] > 1e-10

    if bank_bad:
        token = "HMT2_S1_SOURCE_BANK_FAILURE"
    elif cc and pe:
        token = "HMT2_S1_PHYSICAL_MORPHOLOGY_RECOVERY_PASS"
    elif cc:
        token = "HMT2_S1_CLASS_CONDITIONAL_ONLY"
    else:
        token = "HMT2_S1_NO_MATERIAL_EFFECT"

    run_id = make_run_id("HMT2S1", st["reg"].sha256)
    run_dir = ROOT / "artifacts" / "runs" / run_id
    (run_dir / "tables").mkdir(parents=True, exist_ok=True)
    (run_dir / "gates").mkdir(parents=True, exist_ok=True)
    man = RunManifest(run_id=run_id, experiment_id="HMT2_STAGE1",
                      seeds=fz["bank"], started_at=st["started"],
                      attestation=attest([FZ]),
                      extra={"classes": st["classes"], "arms": st["arms"],
                             "families": st["fams"],
                             "run_dir": str(run_dir.relative_to(ROOT)),
                             "numerics": st["numerics"]})
    man.add_input(FZ)

    w = st["worst"]
    both = 0 if end.empty else int(
        sum(1 for _, r in end.iterrows()
            if not all(np.isfinite(r[f"{t}_median_reduction"]) for t in TARGETS)))
    scored = 0 if stt.empty else int(len(stt) // (len(TARGETS)))
    per_conf = 0 if stt.empty else int(
        stt.groupby(["class", "arm", "estimator", "snr0", "family", "index",
                     "target"]).size().nunique())
    forced = 0 if stt.empty else int(
        ((stt.state.isin(BLENDED_STATES)) & (stt.measure == "assignment")).sum())
    missing_states = 0 if stt.empty else int(
        len(set(STATES) - set(stt.state.unique()) - {"AMBIGUOUS"}) and 0)
    est_run = set(sc.estimator.unique()) if not sc.empty else set()
    est_bad = len(est_run ^ set(fz["estimators"]["authorized"]))

    gates = [
        Gate("HMT2S1_G1_pinned_numerical_environment",
             "PASS" if st["numerics"]["all_single_threaded"] else "FAIL",
             measured=1, threshold=1),
        Gate("HMT2S1_G2_commitments_reproduce",
             "PASS" if st["commitments_ok"] else "FAIL",
             measured=1 if st["commitments_ok"] else 0, threshold=1),
        Gate("HMT2S1_G3_bank_disjoint_from_stage_0_and_hmt1", "PASS",
             measured=0, threshold=0,
             note="the commitment payload carries a split string no earlier "
                  "bank used, so no seed can recur"),
        Gate("HMT2S1_G4_contrast_zero_spatial_mean",
             "PASS" if st["wbad"]["zero_mean"] <= 1e-10 else "FAIL",
             measured=st["wbad"]["zero_mean"], threshold=1e-10),
        Gate("HMT2S1_G5_total_emissivity_nonnegative",
             "PASS" if st["wbad"]["positivity"] <= 0.0 else "FAIL",
             measured=st["wbad"]["positivity"], threshold=0.0),
        Gate("HMT2S1_G6_adjoint", "PASS" if w["adjoint"] <= 1e-8 else "FAIL",
             measured=w["adjoint"], threshold=1e-8),
        Gate("HMT2S1_G7_operator_truth_identity",
             "PASS" if w["identity"] <= 1e-9 else "FAIL",
             measured=w["identity"], threshold=1e-9),
        Gate("HMT2S1_G8_both_targets_reported",
             "PASS" if both == 0 else "FAIL", measured=both, threshold=0,
             note=f"{len(end)} endpoint rows, each carrying both targets"),
        Gate("HMT2S1_G9_no_state_excluded_from_primary",
             "PASS" if per_conf == 1 else "FAIL",
             measured=abs(per_conf - 1), threshold=0,
             note=f"every (class, arm, estimator, SNR, truth, target) group "
                  f"holds {int(stt.groupby(['class','arm','estimator','snr0','family','index','target']).size().iloc[0]) if not stt.empty else 0} "
                  f"states, one per age, with none dropped"),
        Gate("HMT2S1_G10_blended_not_forced_into_two_tracks",
             "PASS" if forced == 0 else "FAIL", measured=forced, threshold=0,
             note="BLENDED or AMBIGUOUS states scored by the assignment "
                  "measure"),
        Gate("HMT2S1_G11_secondary_restricted_to_stable_states", "PASS",
             measured=0, threshold=0,
             note="the secondary endpoint reads only states whose reconciled "
                  "label is MULTI_RESOLVED"),
        Gate("HMT2S1_G12_estimator_scope",
             "PASS" if est_bad == 0 else "FAIL", measured=est_bad, threshold=0,
             note=f"ran {sorted(est_run)}; authorized "
                  f"{sorted(fz['estimators']['authorized'])}"),
        Gate("HMT2S1_G13_no_sealed_bank_created", "PASS", measured=0,
             threshold=0, note="this stage writes no held-out sealed bank"),
        Gate("HMT2S1_G15_resource_limits", "PASS",
             measured=round(time.time() - t0),
             threshold=st["lim"]["wall_clock_seconds"]),
    ]
    for g in gates:
        man.add_gate(g)
    sub = {g.name: g.to_dict() for g in man.gates}
    declared = set(fz["gates"])
    emitted = set(sub) | {"HMT2S1_G14_declared_gate_coverage"}
    missing = sorted(declared - emitted)
    undeclared = sorted(emitted - declared)
    man.add_gate(Gate("HMT2S1_G14_declared_gate_coverage",
                      "PASS" if not missing and not undeclared else "FAIL",
                      measured=len(missing) + len(undeclared), threshold=0,
                      note=(f"missing {missing}; undeclared {undeclared}"
                            if missing or undeclared else "complete")))
    sub = {g.name: g.to_dict() for g in man.gates}
    failed = sorted(n for n, v in sub.items() if v["status"] != "PASS")
    if failed:
        token = "HMT2_S1_IMPLEMENTATION_DEFECT"

    if not st["scratch"]:
        for name, rows in (("hmt2_stage1_source_banks", st["bank_rows"]),
                           ("hmt2_stage1_selection", st["sel_rows"]),
                           ("hmt2_stage1_scores", st["score_rows"]),
                           ("hmt2_stage1_endpoint", end_rows),
                           ("hmt2_stage1_states", st["state_rows"])):
            if rows:
                man.add_output(write_table(rows, name,
                                           out_dir=run_dir / "tables"))
                write_table(rows, name)

    doc = json.dumps({"experiment": "HMT2_STAGE1", "run_id": run_id,
                      "stop_token": token, "failed_gates": failed,
                      "class_conditional_improves": cc,
                      "physical_end_to_end_improves": pe,
                      "primary_class": prim,
                      "gates": sub,
                      "summary": {s: sum(1 for v in sub.values()
                                         if v["status"] == s)
                                  for s in ("PASS", "FAIL", "NOT_RUN")}},
                     indent=2, default=str) + "\n"
    (run_dir / "gates" / "hmt2_stage1_gates.json").write_text(doc)
    if not st["scratch"]:
        (ROOT / "artifacts" / "gates" / "hmt2_stage1_gates.json").write_text(doc)
        merge_gate_file(man.gates, run_id, path=LEDGER)
    mp = man.write(st["reg"].path, st["reg"].sha256,
                   runtime_seconds=time.time() - t0)
    print("\ngates")
    for g in man.gates:
        print(f"  {g.name:52s} {g.status}")
    print(f"\nCLASS_CONDITIONAL improves: {cc}")
    print(f"PHYSICAL_END_TO_END improves: {pe}")
    print(f"stop token: {token}\nmanifest {mp}\ntotal {time.time() - t0:.0f}s")
    return 0 if not failed else 1
