"""Scoring half of the HMT-2 stage 1 endpoint completion.

The first thing this does is check that the primary endpoint reproduces
bitwise. Everything else is only worth reading if it does.
"""
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
from run_hmt1_score import paired_relative

FZ = ROOT / "artifacts" / "configs" / "HMT2_STAGE1_RESOLUTION_AWARE_MORPHOLOGY_VALIDATION_V0.json"
AMD = ROOT / "artifacts" / "configs" / "HMT2_STAGE1_ENDPOINT_COMPLETION_AMENDMENT_020.json"
OUT = ROOT / "artifacts" / "gates" / "hmt2_stage1_completion_gates.json"
LEDGER = ROOT / "artifacts" / "gates" / "hmt2_correctness_gates.json"
T_PHYS, T_CC, T_CCP = "PHYSICAL_END_TO_END", "CLASS_CONDITIONAL", "CC_PROJLAB"
BOOT = {"n_resamples": 10000, "seed": 20260941, "level": 0.95}
KEY = ["class", "arm", "estimator", "snr0"]


def _endpoint(sc, targets):
    rows = []
    for (cname, snr, est), g in sc.groupby(["class", "snr0", "estimator"]):
        d = g[g.arm == "DIRECT_PHYSICAL"].set_index(["family", "index"])
        for arm in sorted(g.arm.unique()):
            if arm == "DIRECT_PHYSICAL":
                continue
            a = g[g.arm == arm].set_index(["family", "index"])
            idx = d.index.intersection(a.index)
            cells = np.array([f for f, _ in idx])
            row = {"class": cname, "arm": arm, "estimator": est, "snr0": snr,
                   "n_truths": len(idx)}
            for t in targets:
                col = f"{t}_all_state_error"
                if col not in d.columns:
                    continue
                dv = d.loc[idx, col].to_numpy()
                av = a.loc[idx, col].to_numpy()
                r = paired_relative(dv, av, cells, BOOT["n_resamples"],
                                    BOOT["seed"], BOOT["level"])
                row[f"{t}_direct"] = float(dv.mean())
                row[f"{t}_arm"] = float(av.mean())
                row[f"{t}_median_reduction"] = r["median"]
                row[f"{t}_ci_low"] = r["median_ci_low"]
                row[f"{t}_ci_high"] = r["median_ci_high"]
                row[f"{t}_improves"] = bool(r["median"] > 0
                                            and r["median_ci_low"] > 0)
            rows.append(row)
    return pd.DataFrame(rows)


def finish(st) -> int:
    fz, t0 = st["fz"], st["t0"]
    sc = pd.DataFrame(st["score_rows"])
    stt = pd.DataFrame(st["state_rows"])
    spn = pd.DataFrame(st["span_rows"])

    end = _endpoint(sc, (T_PHYS, T_CC, T_CCP))

    # ---- item 8: bitwise reproduction of every primary endpoint cell -------
    prev = st["prev_end"]
    # Only the primary endpoint cells. stable_multi_* is deliberately excluded:
    # item 9 requires it extended to both estimators and both SNRs, so stage 1
    # holds NaN where this run holds a number, and comparing them would report
    # the requested completion as a reproduction failure.
    suffixes = ("_direct", "_arm", "_median_reduction", "_ci_low", "_ci_high")
    cols = sorted(c for c in prev.columns
                  if c.startswith((T_PHYS, T_CC)) and c.endswith(suffixes)
                  and c in end.columns)
    a = prev.set_index(KEY).sort_index()
    b = end.set_index(KEY).sort_index()
    shared = a.index.intersection(b.index)
    diffs = []
    for c in cols:
        x = a.loc[shared, c].to_numpy(dtype=float)
        y = b.loc[shared, c].to_numpy(dtype=float)
        bad = ~((x == y) | (np.isnan(x) & np.isnan(y)))
        for i in np.flatnonzero(bad):
            diffs.append({"cell": str(shared[i]), "column": c,
                          "stage_1": float(x[i]), "completion": float(y[i]),
                          "abs_delta": float(abs(x[i] - y[i]))})
    reproduced = len(diffs) == 0

    # ---- companions --------------------------------------------------------
    nd_end = _endpoint(sc.rename(columns={
        f"{T_PHYS}_non_dead_error": f"{T_PHYS}_all_state_error_ND",
        f"{T_CC}_non_dead_error": f"{T_CC}_all_state_error_ND"}), ())
    nd_rows = []
    for (cname, snr, est), g in sc.groupby(["class", "snr0", "estimator"]):
        d = g[g.arm == "DIRECT_PHYSICAL"].set_index(["family", "index"])
        for arm in sorted(g.arm.unique()):
            if arm == "DIRECT_PHYSICAL":
                continue
            aa = g[g.arm == arm].set_index(["family", "index"])
            idx = d.index.intersection(aa.index)
            cells = np.array([f for f, _ in idx])
            row = {"class": cname, "arm": arm, "estimator": est, "snr0": snr}
            for t in (T_PHYS, T_CC):
                dv = d.loc[idx, f"{t}_non_dead_error"].to_numpy()
                av = aa.loc[idx, f"{t}_non_dead_error"].to_numpy()
                r = paired_relative(dv, av, cells, BOOT["n_resamples"],
                                    BOOT["seed"], BOOT["level"])
                row[f"{t}_non_dead_direct"] = float(dv.mean())
                row[f"{t}_non_dead_arm"] = float(av.mean())
                row[f"{t}_non_dead_median_reduction"] = r["median"]
                row[f"{t}_non_dead_ci_low"] = r["median_ci_low"]
                row[f"{t}_non_dead_improves"] = bool(
                    r["median"] > 0 and r["median_ci_low"] > 0)
                row[f"{t}_saturation_direct"] = float(
                    d.loc[idx, f"{t}_saturation_fraction"].mean())
                row[f"{t}_saturation_arm"] = float(
                    aa.loc[idx, f"{t}_saturation_fraction"].mean())
            nd_rows.append(row)
    nd = pd.DataFrame(nd_rows)

    # per-family effects and intervals
    fam_rows = []
    for (cname, snr, est, fam), g in sc.groupby(["class", "snr0", "estimator",
                                                 "family"]):
        d = g[g.arm == "DIRECT_PHYSICAL"].set_index("index")
        for arm in sorted(g.arm.unique()):
            if arm == "DIRECT_PHYSICAL":
                continue
            aa = g[g.arm == arm].set_index("index")
            idx = d.index.intersection(aa.index)
            cells = np.array([fam] * len(idx))
            row = {"class": cname, "arm": arm, "estimator": est, "snr0": snr,
                   "family": fam, "n_truths": len(idx)}
            for t in (T_PHYS, T_CC):
                dv = d.loc[idx, f"{t}_all_state_error"].to_numpy()
                av = aa.loc[idx, f"{t}_all_state_error"].to_numpy()
                r = paired_relative(dv, av, cells, BOOT["n_resamples"],
                                    BOOT["seed"], BOOT["level"])
                row[f"{t}_median_reduction"] = r["median"]
                row[f"{t}_ci_low"] = r["median_ci_low"]
                row[f"{t}_ci_high"] = r["median_ci_high"]
                row[f"{t}_improves"] = bool(r["median"] > 0
                                            and r["median_ci_low"] > 0)
            fam_rows.append(row)

    # stable multi endpoint, both estimators and both SNRs
    stab_rows = []
    for (cname, snr, est), g in sc.groupby(["class", "snr0", "estimator"]):
        d = g[g.arm == "DIRECT_PHYSICAL"].set_index(["family", "index"])
        for arm in sorted(g.arm.unique()):
            if arm == "DIRECT_PHYSICAL":
                continue
            aa = g[g.arm == arm].set_index(["family", "index"])
            idx = d.index.intersection(aa.index)
            dv = d.loc[idx, "stable_multi_cost_normalized"].to_numpy()
            av = aa.loc[idx, "stable_multi_cost_normalized"].to_numpy()
            m = np.isfinite(dv) & np.isfinite(av)
            if not m.any():
                continue
            cells = np.array([f for f, _ in idx])[m]
            r = paired_relative(dv[m], av[m], cells, BOOT["n_resamples"],
                                BOOT["seed"], BOOT["level"])
            stab_rows.append({
                "class": cname, "arm": arm, "estimator": est, "snr0": snr,
                "direct": float(dv[m].mean()), "arm_cost": float(av[m].mean()),
                "median_reduction": r["median"], "ci_low": r["median_ci_low"],
                "ci_high": r["median_ci_high"],
                "improves": bool(r["median"] > 0 and r["median_ci_low"] > 0),
                "n_truths": int(m.sum())})

    # stable age-resolved morphology interval
    span_rows = []
    for (cname, arm, est, snr), g in spn.groupby(["class", "arm", "estimator",
                                                  "snr0"]):
        span_rows.append({
            "class": cname, "arm": arm, "estimator": est, "snr0": snr,
            "epsilon": st["eps"], "quantile": st["quant"],
            "L_stable_morphology_M": float(
                np.quantile(g.pass_to_age_M.to_numpy(), 1.0 - st["quant"])),
            "mean_reach_M": float(g.pass_to_age_M.mean()),
            "fraction_nonzero": float((g.pass_to_age_M > 0).mean()),
            "n_realizations": int(len(g))})

    run_id = make_run_id("HMT2S1C", st["reg"].sha256)
    run_dir = ROOT / "artifacts" / "runs" / run_id
    (run_dir / "tables").mkdir(parents=True, exist_ok=True)
    (run_dir / "gates").mkdir(parents=True, exist_ok=True)
    man = RunManifest(run_id=run_id, experiment_id="HMT2_STAGE1_COMPLETION",
                      seeds=fz["bank"], started_at=st["started"],
                      attestation=attest([FZ, AMD]),
                      extra={"run_dir": str(run_dir.relative_to(ROOT)),
                             "numerics": st["numerics"]})
    man.add_input(FZ)

    all_draws = int(stt.draw.nunique()) if not stt.empty else 0
    both_est = int(len({r["estimator"] for r in stab_rows}))
    both_snr = int(len({r["snr0"] for r in stab_rows}))
    forced = 0 if stt.empty else int(
        ((stt.state.isin(("BLENDED", "AMBIGUOUS")))
         & (stt.measure == "assignment")).sum())
    companions = int(all(f"{t}_median_reduction" in end.columns
                         for t in (T_PHYS, T_CC, T_CCP)))

    gates = [
        Gate("HMT2C_G1_pinned_numerical_environment",
             "PASS" if st["numerics"]["all_single_threaded"] else "FAIL",
             measured=1, threshold=1),
        Gate("HMT2C_G2_primary_endpoint_reproduces_bitwise",
             "NOT_RUN" if st["scratch"] else ("PASS" if reproduced else "FAIL"),
             measured=len(diffs), threshold=0,
             note=(f"not comparable in scratch mode: a reduced bank scores a "
                   f"different truth set" if st["scratch"] else
                   f"{len(cols)} columns x {len(shared)} cells compared "
                   f"exactly, stable_multi excluded as item 9 extends it")),
        Gate("HMT2C_G3_no_selection_performed", "PASS", measured=0, threshold=0,
             note="hyperparameters read from the stage 1 selection table; this "
                  "runner has no sweep"),
        Gate("HMT2C_G4_all_draws_decomposed",
             "PASS" if all_draws == int(fz["bank"]["noise_draws_per_truth"])
             else "FAIL", measured=all_draws,
             threshold=int(fz["bank"]["noise_draws_per_truth"]),
             note="distinct noise draws present in the per-state table"),
        Gate("HMT2C_G5_stable_multi_both_estimators_and_snrs",
             "PASS" if both_est == 2 and both_snr == 2 else "FAIL",
             measured=both_est * both_snr, threshold=4,
             note=f"{both_est} estimators x {both_snr} SNRs"),
        Gate("HMT2C_G6_both_class_conditional_companions",
             "PASS" if companions else "FAIL", measured=companions, threshold=1,
             note="analytic-label and projected-label companions both present"),
        Gate("HMT2C_G7_blended_not_forced_into_two_tracks",
             "PASS" if forced == 0 else "FAIL", measured=forced, threshold=0),
        Gate("HMT2C_G8_non_dead_companion_emitted",
             "PASS" if len(nd) else "FAIL", measured=len(nd), threshold=1),
        Gate("HMT2C_G9_saturation_fractions_emitted",
             "PASS" if f"{T_PHYS}_saturation_arm" in nd.columns else "FAIL",
             measured=1, threshold=1),
        Gate("HMT2C_G10_per_family_effects_emitted",
             "PASS" if len(fam_rows) else "FAIL", measured=len(fam_rows),
             threshold=1),
        Gate("HMT2C_G11_stable_age_interval_emitted",
             "PASS" if len(span_rows) else "FAIL", measured=len(span_rows),
             threshold=1),
    ]
    for g in gates:
        man.add_gate(g)
    sub = {g.name: g.to_dict() for g in man.gates}
    failed = sorted(n for n, v in sub.items()
                    if v["status"] not in ("PASS", "NOT_RUN"))
    token = ("HMT2_S1_ENDPOINT_COMPLETION_PASS" if not failed
             else "HMT2_S1_ENDPOINT_COMPLETION_DEFECT")

    if not st["scratch"]:
        for name, rows in (
                ("hmt2_stage1c_scores", st["score_rows"]),
                ("hmt2_stage1c_endpoint", end.to_dict("records")),
                ("hmt2_stage1c_non_dead", nd_rows),
                ("hmt2_stage1c_per_family", fam_rows),
                ("hmt2_stage1c_stable_multi", stab_rows),
                ("hmt2_stage1c_stable_interval", span_rows),
                ("hmt2_stage1c_states", st["state_rows"]),
                ("hmt2_stage1c_reproduction_diffs", diffs)):
            if rows:
                man.add_output(write_table(rows, name,
                                           out_dir=run_dir / "tables"))
                write_table(rows, name)

    doc = json.dumps({"experiment": "HMT2_STAGE1_COMPLETION", "run_id": run_id,
                      "stop_token": token, "failed_gates": failed,
                      "primary_endpoint_reproduced_bitwise": reproduced,
                      "n_reproduction_diffs": len(diffs),
                      "gates": sub,
                      "summary": {s: sum(1 for v in sub.values()
                                         if v["status"] == s)
                                  for s in ("PASS", "FAIL", "NOT_RUN")}},
                     indent=2, default=str) + "\n"
    (run_dir / "gates" / "hmt2_stage1_completion_gates.json").write_text(doc)
    if not st["scratch"]:
        OUT.write_text(doc)
        merge_gate_file(man.gates, run_id, path=LEDGER)
    mp = man.write(st["reg"].path, st["reg"].sha256,
                   runtime_seconds=time.time() - t0)
    print("\ngates")
    for g in man.gates:
        print(f"  {g.name:52s} {g.status}")
    print(f"\nprimary endpoint reproduces bitwise: {reproduced}"
          f" ({len(diffs)} differing cells)")
    print(f"stop token: {token}\nmanifest {mp}\ntotal {time.time() - t0:.0f}s")
    return 0 if not failed else 1
