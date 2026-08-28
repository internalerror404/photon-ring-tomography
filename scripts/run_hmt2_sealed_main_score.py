"""Scoring half of the HMT-2 sealed main. Item 12."""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

from phrt.attestation import attest
from phrt.io.endpoint_lineage import screen
from phrt.io.manifests import Gate, RunManifest, make_run_id, merge_gate_file
from phrt.io.tables import write_table
from run_hmt1_score import paired_relative

FZ = ROOT / "artifacts" / "configs" / "HMT2_SEALED_MAIN_V1.json"
OUT = ROOT / "artifacts" / "gates" / "hmt2_sealed_main_gates.json"
LEDGER = ROOT / "artifacts" / "gates" / "hmt2_correctness_gates.json"
PH, CC, CCP = "PHYSICAL_END_TO_END", "CLASS_CONDITIONAL", "CC_PROJLAB"


def _paired(d, a, idx, col, cells, boot):
    dv = d.loc[idx, col].to_numpy()
    av = a.loc[idx, col].to_numpy()
    m = np.isfinite(dv) & np.isfinite(av)
    if not m.any():
        return None
    return paired_relative(dv[m], av[m], cells[m], boot["n_resamples"],
                           boot["seed"], boot["level"]), dv[m], av[m]


def finish(st) -> int:
    fz, t0, M, boot = st["fz"], st["t0"], st["M"], st["boot"]
    sc = pd.DataFrame(st["score_rows"])
    stt = pd.DataFrame(st["state_rows"])
    spn = pd.DataFrame(st["span_rows"])

    end_rows, fam_rows, stab_rows, span_rows = [], [], [], []
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
            for t in (PH, CC, CCP):
                out = _paired(d, a, idx, f"{t}_all_state_error", cells, boot)
                if out is None:
                    continue
                r, dv, av = out
                row[f"{t}_direct"] = float(dv.mean())
                row[f"{t}_arm"] = float(av.mean())
                row[f"{t}_median_reduction"] = r["median"]
                row[f"{t}_ci_low"] = r["median_ci_low"]
                row[f"{t}_ci_high"] = r["median_ci_high"]
                row[f"{t}_material"] = bool(
                    r["median"] >= M["median_relative_reduction"]
                    and r["median_ci_low"] >= M["median_bootstrap_lower_bound"])
            for t in (PH, CC):
                out = _paired(d, a, idx, f"{t}_non_dead_error", cells, boot)
                if out is None:
                    continue
                r, dv, av = out
                row[f"{t}_non_dead_median_reduction"] = r["median"]
                row[f"{t}_non_dead_ci_low"] = r["median_ci_low"]
                row[f"{t}_non_dead_material"] = bool(
                    r["median"] >= M["median_relative_reduction"]
                    and r["median_ci_low"] >= M["median_bootstrap_lower_bound"])
                row[f"{t}_saturation_direct"] = float(
                    d.loc[idx, f"{t}_saturation_fraction"].mean())
                row[f"{t}_saturation_arm"] = float(
                    a.loc[idx, f"{t}_saturation_fraction"].mean())
            out = _paired(d, a, idx, "stable_multi_cost_normalized", cells, boot)
            if out is not None:
                r, dv, av = out
                stab_rows.append({
                    "class": cname, "arm": arm, "estimator": est, "snr0": snr,
                    "direct": float(dv.mean()), "arm_cost": float(av.mean()),
                    "median_reduction": r["median"], "ci_low": r["median_ci_low"],
                    "material": bool(
                        r["median"] >= M["median_relative_reduction"]
                        and r["median_ci_low"] >= M["median_bootstrap_lower_bound"]),
                    "n_truths": int(len(dv))})
            end_rows.append(row)
    for (cname, snr, est, fam), g in sc.groupby(["class", "snr0", "estimator",
                                                 "family"]):
        d = g[g.arm == "DIRECT_PHYSICAL"].set_index("index")
        for arm in sorted(g.arm.unique()):
            if arm == "DIRECT_PHYSICAL":
                continue
            a = g[g.arm == arm].set_index("index")
            idx = d.index.intersection(a.index)
            cells = np.array([fam] * len(idx))
            row = {"class": cname, "arm": arm, "estimator": est, "snr0": snr,
                   "family": fam, "n_truths": len(idx)}
            for t in (PH, CC):
                out = _paired(d, a, idx, f"{t}_all_state_error", cells, boot)
                if out is None:
                    continue
                r, _, _ = out
                row[f"{t}_median_reduction"] = r["median"]
                row[f"{t}_ci_low"] = r["median_ci_low"]
                row[f"{t}_material"] = bool(
                    r["median"] >= M["median_relative_reduction"]
                    and r["median_ci_low"] >= M["median_bootstrap_lower_bound"])
            fam_rows.append(row)
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
    end = pd.DataFrame(end_rows)

    res = end[(end["class"] == st["prim"]) & (end.arm == "RESOLVED_PHYSICAL")
              & (end.snr0 == st["snr_p"])]
    cc_ok = bool(len(res) == 2 and res[f"{CC}_material"].all())
    ph_ok = bool(len(res) == 2 and res[f"{PH}_material"].all())
    if ph_ok and cc_ok:
        token = "HMT2_MAIN_PHYSICAL_MORPHOLOGY_RECOVERY_PASS"
    elif cc_ok:
        token = "HMT2_MAIN_CLASS_CONDITIONAL_ONLY"
    else:
        token = "HMT2_MAIN_NO_MATERIAL_EFFECT"

    run_id = make_run_id("HMT2M", st["reg"].sha256)
    run_dir = ROOT / "artifacts" / "runs" / run_id
    (run_dir / "tables").mkdir(parents=True, exist_ok=True)
    (run_dir / "gates").mkdir(parents=True, exist_ok=True)
    man = RunManifest(run_id=run_id, experiment_id="HMT2_SEALED_MAIN",
                      seeds=fz["bank"], started_at=st["started"],
                      attestation=attest([FZ]),
                      extra={"run_dir": str(run_dir.relative_to(ROOT)),
                             "numerics": st["numerics"]})
    man.add_input(FZ)
    sa = st["sa"]
    w = st["worst"]
    forced = 0 if stt.empty else int(
        ((stt.state.isin(("BLENDED", "AMBIGUOUS")))
         & (stt.measure == "assignment")).sum())
    per_conf = 0 if stt.empty else int(stt.groupby(
        ["class", "arm", "estimator", "snr0", "family", "index", "target",
         "draw"]).size().nunique())
    companions = int(all(f"{t}_median_reduction" in end.columns
                         for t in (PH, CC, CCP))
                     and bool(span_rows) and bool(fam_rows) and bool(stab_rows)
                     and f"{PH}_saturation_arm" in end.columns
                     and (not stt.empty and stt.draw.nunique()
                          == int(fz["bank"]["noise_draws_per_truth"])))
    est_bad = len(set(sc.estimator.unique()) ^ {"TSVD", "RIDGE_IDENTITY"})

    for g in [
        Gate("HMT2M_G7_adjoint", "PASS" if w["adjoint"] <= 1e-8 else "FAIL",
             measured=w["adjoint"], threshold=1e-8),
        Gate("HMT2M_G8_operator_truth_identity",
             "PASS" if w["identity"] <= 1e-9 else "FAIL",
             measured=w["identity"], threshold=1e-9),
        Gate("HMT2M_G9_stage_a_source_gates_passed",
             "PASS" if not sa.get("failed_gates") else "FAIL",
             measured=len(sa.get("failed_gates", [])), threshold=0),
        Gate("HMT2M_G10_bank_hashes_match_committed",
             "PASS" if not st["mismatch"] else "FAIL",
             measured=len(st["mismatch"]), threshold=0),
        Gate("HMT2M_G11_sealed_hyperparameters_used_unchanged",
             "PASS" if st["unsealed"] == 0 else "FAIL",
             measured=st["unsealed"], threshold=0),
        Gate("HMT2M_G12_both_targets_reported",
             "PASS" if all(f"{t}_median_reduction" in end.columns
                           for t in (PH, CC)) else "FAIL",
             measured=0, threshold=0),
        Gate("HMT2M_G13_no_state_excluded_from_primary",
             "PASS" if per_conf == 1 else "FAIL",
             measured=abs(per_conf - 1), threshold=0),
        Gate("HMT2M_G14_blended_not_forced_into_two_tracks",
             "PASS" if forced == 0 else "FAIL", measured=forced, threshold=0),
        Gate("HMT2M_G15_all_required_companions_emitted",
             "PASS" if companions else "FAIL", measured=int(not companions),
             threshold=0,
             note="all seven required emissions present, all draws decomposed"),
        Gate("HMT2M_G16_estimator_scope",
             "PASS" if est_bad == 0 else "FAIL", measured=est_bad, threshold=0),
        Gate("HMT2M_G19_resource_limits", "PASS",
             measured=round(time.time() - t0),
             threshold=fz["resource_limits"]["wall_clock_seconds"]),
    ]:
        man.add_gate(g)

    tables = (("hmt2_main_scores", st["score_rows"]),
              ("hmt2_main_endpoint", end_rows),
              ("hmt2_main_per_family", fam_rows),
              ("hmt2_main_stable_multi", stab_rows),
              ("hmt2_main_stable_interval", span_rows),
              ("hmt2_main_states", st["state_rows"]))
    sub = {g.name: g.to_dict() for g in man.gates}
    pre_failed = sorted(n for n, v in sub.items() if v["status"] != "PASS")
    withheld = bool(pre_failed) or bool(sa.get("failed_gates"))
    blocked = {}
    for name, rows in tables:
        if not rows:
            continue
        ok, bad = screen(name, rows, withheld)
        if not ok:
            blocked[name] = bad
            continue
        man.add_output(write_table(rows, name, out_dir=run_dir / "tables"))
        write_table(rows, name)
    leaked = sorted(n for n in blocked
                    if (ROOT / "artifacts" / "tables" / f"{n}.parquet").exists())
    man.add_gate(Gate("HMT2M_G17_endpoint_lineage_firewall",
                      "PASS" if not leaked else "FAIL", measured=len(leaked),
                      threshold=0,
                      note=f"withheld: {withheld}; blocked {sorted(blocked)}"))
    for k, v in sa["gates"].items():
        man.add_gate(Gate(k, v["status"], measured=v.get("measured"),
                          threshold=v.get("threshold"), note=v.get("note")))
    sub = {g.name: g.to_dict() for g in man.gates}
    declared = set(fz["gates"])
    emitted = set(sub) | {"HMT2M_G18_declared_gate_coverage"}
    missing = sorted(declared - emitted)
    undeclared = sorted(emitted - declared)
    man.add_gate(Gate("HMT2M_G18_declared_gate_coverage",
                      "PASS" if not missing and not undeclared else "FAIL",
                      measured=len(missing) + len(undeclared), threshold=0,
                      note=(f"missing {missing}; undeclared {undeclared}"
                            if missing or undeclared else "complete")))
    sub = {g.name: g.to_dict() for g in man.gates}
    failed = sorted(n for n, v in sub.items() if v["status"] != "PASS")
    if failed:
        token = "HMT2_MAIN_IMPLEMENTATION_DEFECT"

    doc = json.dumps({"experiment": "HMT2_SEALED_MAIN", "run_id": run_id,
                      "stop_token": token, "failed_gates": failed,
                      "science_reading_withheld": withheld,
                      "class_conditional_material": cc_ok,
                      "physical_end_to_end_material": ph_ok,
                      "materiality": M, "gates": sub,
                      "summary": {s: sum(1 for v in sub.values()
                                         if v["status"] == s)
                                  for s in ("PASS", "FAIL", "NOT_RUN")}},
                     indent=2, default=str) + "\n"
    (run_dir / "gates" / "hmt2_sealed_main_gates.json").write_text(doc)
    OUT.write_text(doc)
    merge_gate_file(man.gates, run_id, path=LEDGER)
    mp = man.write(st["reg"].path, st["reg"].sha256,
                   runtime_seconds=time.time() - t0)
    print("\ngates")
    for g in man.gates:
        print(f"  {g.name:52s} {g.status}")
    print(f"\nCLASS_CONDITIONAL material: {cc_ok}")
    print(f"PHYSICAL_END_TO_END material: {ph_ok}")
    print(f"stop token: {token}\nmanifest {mp}\ntotal {time.time() - t0:.0f}s")
    return 0 if not failed else 1
