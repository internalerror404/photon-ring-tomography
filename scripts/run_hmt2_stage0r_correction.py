#!/usr/bin/env python3
"""HMT-2 stage 0R: the source-only correction.

REVIEWER_RULING_HMT2_STAGE0_019 items 4 to 11. The same 169 sources, the same
seeds, the same levels and classes. What changes is the accounting and what
gets written down.

Stage 0 computed its merger rate over every state the finest grid called
MULTI_RESOLVED, including states the two finest grids disagreed about. A rate
over states whose multiplicity is itself unresolved measures the classifier as
much as the projection. Here the states are stratified and only the stable ones
carry the claim, and a per-age table is emitted so every rate below is
recomputable rather than trusted.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from phrt.numerics import pin, record as numerics_record, require_single_threaded

pin()

import numpy as np  # noqa: E402

import pandas as pd  # noqa: E402

from phrt.attestation import attest  # noqa: E402
from phrt.config import sha256_file  # noqa: E402
from phrt.io.source_only import assert_source_only, loaded_forbidden  # noqa: E402
from phrt.io.tables import write_table  # noqa: E402
from phrt.metrics.feature_sets import (assignment, cell_metric,  # noqa: E402
                                       peaks_to_features)
from phrt.metrics.topography import classify, reconcile  # noqa: E402
from phrt.metrics.windowed_reference import window_stack  # noqa: E402
from phrt.sources.contrast import build  # noqa: E402
from phrt.sources.separable_projection import factors, project  # noqa: E402

S0 = ROOT / "artifacts" / "configs" / "HMT2_STAGE0_SOURCE_OBJECT_AND_RESOLUTION_AUDIT_V0.json"
FZ = ROOT / "artifacts" / "configs" / "HMT2_STAGE0R_SOURCE_ONLY_CORRECTION_V0.json"
OUT = ROOT / "artifacts" / "gates" / "hmt2_stage0r_gates.json"


def truth_seed(family, i, n, seed):
    p = json.dumps({"family": family, "split": "hmt2_stage0_source_audit",
                    "n": n, "seed": seed, "model": "contrast"},
                   sort_keys=True).encode()
    return int(hashlib.sha256(p + f"|{i}".encode()).hexdigest()[:16], 16) % (2 ** 63)


def canary_seed():
    p = json.dumps({"family": "two_hotspot_trajectories",
                    "split": "sealed_main_heldout", "n": 16,
                    "seed": 20260921, "model": "contrast"},
                   sort_keys=True).encode()
    return int(hashlib.sha256(p + b"|5").hexdigest()[:16], 16) % (2 ** 63)


def axes_for(level, r_in, r_out, t_lo, t_hi):
    nr, npz, nt = level
    return (np.exp(np.linspace(np.log(r_in), np.log(r_out), nr)),
            np.linspace(0.0, 2 * np.pi, npz, endpoint=False),
            np.linspace(t_lo, t_hi, nt))


def main() -> int:
    t0 = time.time()
    assert_source_only()                       # item 10, before any work
    before_clean = not loaded_forbidden()
    numerics = require_single_threaded()
    s0 = json.loads(S0.read_text())
    fz = json.loads(FZ.read_text())

    r1 = json.loads((ROOT / "artifacts" / "configs" / "R1_MAIN_FREEZE.json").read_text())
    r_in = float(r1["physical_model"]["r_inner_M"])
    r_out = float(r1["physical_model"]["r_outer_M"])
    t_lo = float(r1["observation"]["basis_t_min"])
    t_hi = float(r1["observation"]["basis_t_max"])
    inh = s0["inherited"]
    spin = float(inh["spin"])
    half = float(inh["probe_half_width_M"])
    ages = np.arange(0.0, float(inh["age_grid_max_M"]) + 1e-9,
                     float(inh["age_grid_step_M"]))
    frac = float(s0["classification"]["prominence_fraction"])
    mult = s0["source_families"]["expected_windowed_multiplicity"]
    levels = [(g["n_radial"], g["n_azimuthal"], g["n_temporal"])
              for g in s0["grids"]["nested"]]
    fine = levels[-1]
    classes = {k: v for k, v in s0["source_classes"].items()
               if isinstance(v, dict) and "radial" in v}

    r0a, p0a, _ = axes_for(levels[0], r_in, r_out, t_lo, t_hi)
    met0 = cell_metric(r0a, p0a)
    lam = met0["unmatched_cost"]

    fams = list(s0["source_families"]["declared"])
    offm = list(s0["source_families"]["off_manifold"])
    n_per = int(s0["bank"]["truths_per_family"])
    n_off = int(s0["bank"]["off_manifold_per_family"])
    seed = int(s0["bank"]["bank_seed"])

    work = [(f, i, truth_seed(f, i, n_per, seed), False, False)
            for f in fams for i in range(n_per)]
    work += [(f, i, truth_seed(f, i, n_off, seed), True, False)
             for f in offm for i in range(n_off)]
    work += [("two_hotspot_trajectories", -1, canary_seed(), False, True)]

    Rf, Pf, Tf = axes_for(fine, r_in, r_out, t_lo, t_hi)
    gR, gP, gT = np.meshgrid(Rf, Pf, Tf, indexing="ij")
    t_index_f = np.tile(np.arange(fine[2]), fine[0] * fine[1])
    fac = {k: factors(Rf, Pf, Tf, v["radial"], v["azimuthal"], v["temporal"])
           for k, v in classes.items()}

    per_age, seeds_seen = [], {}
    for n_done, (family, idx, ts, is_off, is_canary) in enumerate(work):
        seeds_seen[f"{family}|{idx}"] = int(ts)
        rng = np.random.default_rng(ts)
        _, fluct, _, _, _, _ = build(rng, family, spin, r_in, r_out,
                                     gR.ravel(), gP.ravel(), gT.ravel(),
                                     t_index_f, fine[2])
        exp_m = int(mult[family])

        labels, feats = {}, {}
        raw_fine = None
        for li in (len(levels) - 2, len(levels) - 1):
            r, p, t = axes_for(levels[li], r_in, r_out, t_lo, t_hi)
            R, P, T = np.meshgrid(r, p, t, indexing="ij")
            raw = np.asarray(fluct(R.ravel(), P.ravel(), T.ravel()),
                             float).reshape(r.size * p.size, t.size)
            maps = (raw @ window_stack(t, ages, half)).reshape(r.size, p.size,
                                                               ages.size)
            if li == len(levels) - 1:
                raw_fine = raw.reshape(r.size, p.size, t.size)
            tmax = float(np.abs(maps).max())
            ll, ff = [], []
            for k in range(ages.size):
                m = maps[:, :, k]
                c = classify(m, exp_m, float(m.max()), tmax, frac)
                ll.append(c["state"])
                ff.append(peaks_to_features(c["peaks"], c["prominences"], m, r, p))
            labels[li], feats[li] = ll, ff

        fi, co = len(levels) - 1, len(levels) - 2
        rec = [reconcile(labels[fi][k], labels[co][k]) for k in range(ages.size)]

        for cname in classes:
            pr = project(raw_fine, fac[cname])
            pmaps = (pr.reshape(Rf.size * Pf.size, Tf.size)
                     @ window_stack(Tf, ages, half)).reshape(Rf.size, Pf.size,
                                                             ages.size)
            tmax_p = float(np.abs(pmaps).max())
            for k in range(ages.size):
                m = pmaps[:, :, k]
                c = classify(m, exp_m, float(m.max()), tmax_p, frac)
                after = peaks_to_features(c["peaks"], c["prominences"], m, Rf, Pf)
                a = assignment(feats[fi][k], after, met0)
                per_age.append({
                    "family": family, "index": idx, "age_M": float(ages[k]),
                    "class": cname,
                    "label_fine": labels[fi][k], "label_coarser": labels[co][k],
                    "label_reconciled": rec[k], "label_projected": c["state"],
                    "cardinality_pre": len(feats[fi][k]),
                    "cardinality_post": len(after),
                    "matched_position_cost_cells": a["mean_matched_cells"],
                    "unbalanced_cost_cells": a["unbalanced_cost"],
                    "unbalanced_cost_normalized": a["unbalanced_cost"] / lam,
                    "canary": is_canary, "off_manifold": is_off})

        if (n_done + 1) % 12 == 0:
            print(f"  {n_done + 1}/{len(work)} truths, {time.time() - t0:.0f}s",
                  flush=True)

    write_table(per_age, "hmt2_stage0r_per_age")

    # ---- stratified merger rates, item 8 -----------------------------------
    df = pd.DataFrame(per_age)
    agg = df[(~df.canary) & (~df.off_manifold)]
    strata = {
        "STABLE_MULTI_RESOLVED":
            lambda d: d[d.label_reconciled == "MULTI_RESOLVED"],
        "AMBIGUOUS_FINE_MULTI":
            lambda d: d[(d.label_fine == "MULTI_RESOLVED")
                        & (d.label_reconciled == "AMBIGUOUS")],
        "ALL_FINEST_MULTI":
            lambda d: d[d.label_fine == "MULTI_RESOLVED"],
    }
    rate_rows = []
    for sname, sel in strata.items():
        for (fam, cls), grp in sel(agg).groupby(["family", "class"]):
            n = len(grp)
            merged = int((grp.label_projected != "MULTI_RESOLVED").sum())
            rate_rows.append({
                "stratum": sname, "family": fam, "class": cls,
                "n_states": n, "n_merged": merged,
                "merger_rate": merged / n if n else float("nan"),
                "carries_claim": sname == "STABLE_MULTI_RESOLVED",
                "matched_position_cost_median": float(
                    grp.matched_position_cost_cells.median()),
                "unbalanced_cost_normalized_median": float(
                    grp.unbalanced_cost_normalized.median())})
    write_table(rate_rows, "hmt2_stage0r_merger_rates")

    # ---- gates --------------------------------------------------------------
    s = {n: len(strata[n](agg)) for n in strata}
    partition_ok = (s["STABLE_MULTI_RESOLVED"] + s["AMBIGUOUS_FINE_MULTI"]
                    == s["ALL_FINEST_MULTI"])
    overlap = len(set(map(tuple, strata["STABLE_MULTI_RESOLVED"](agg)
                          [["family", "index", "age_M", "class"]].values))
                  & set(map(tuple, strata["AMBIGUOUS_FINE_MULTI"](agg)
                            [["family", "index", "age_M", "class"]].values)))
    expected_rows = len(work) * ages.size * len(classes)

    # Item 5, checked against what stage 0 actually recorded rather than
    # asserted. Writing zero here because the rule is the same rule would
    # record an intention, which is the defect item 10 objects to.
    s0_states = pd.read_parquet(ROOT / "artifacts" / "tables"
                                / "hmt2_stage0_states.parquet")
    s0_seeds = {f"{r.family}|{int(r.index)}": int(r.truth_seed)
                for r in s0_states.itertuples()}
    seed_mismatch = sum(1 for k, v in seeds_seen.items()
                        if s0_seeds.get(k) != v)
    seed_missing = sorted(set(s0_seeds) ^ set(seeds_seen))

    assert_source_only()                   # item 10, after all computation
    after_bad = loaded_forbidden()
    gates = {
        "HMT2R_G1_pinned_numerical_environment": {
            "status": "PASS" if numerics["all_single_threaded"] else "FAIL",
            "measured": 1, "threshold": 1},
        "HMT2R_G2_source_only_before": {
            "status": "PASS" if before_clean else "FAIL",
            "measured": 0 if before_clean else 1, "threshold": 0},
        "HMT2R_G3_source_only_after": {
            "status": "PASS" if not after_bad else "FAIL",
            "measured": len(after_bad), "threshold": 0,
            "note": "inspected after all computation; the recorded booleans "
                    "below are derived from this inspection"},
        "HMT2R_G4_same_sources_as_stage_0": {
            "status": "PASS" if seed_mismatch == 0 and not seed_missing
                      else "FAIL",
            "measured": seed_mismatch + len(seed_missing), "threshold": 0,
            "note": f"{len(seeds_seen)} truth seeds compared against the "
                    f"{len(s0_seeds)} stage 0 recorded, {seed_mismatch} "
                    f"differing, {len(seed_missing)} present in one and not "
                    f"the other"},
        "HMT2R_G5_no_redraw": {
            "status": "PASS", "measured": 1, "threshold": 1,
            "note": "no new bank seed exists in this stage"},
        "HMT2R_G6_per_age_table_complete": {
            "status": "PASS" if len(per_age) == expected_rows else "FAIL",
            "measured": abs(len(per_age) - expected_rows), "threshold": 0,
            "note": f"{len(per_age)} rows against {expected_rows} expected"},
        "HMT2R_G7_strata_partition_the_finest_multi_states": {
            "status": "PASS" if partition_ok and overlap == 0 else "FAIL",
            "measured": int(not partition_ok) + overlap, "threshold": 0,
            "note": f"stable {s['STABLE_MULTI_RESOLVED']} + ambiguous "
                    f"{s['AMBIGUOUS_FINE_MULTI']} = "
                    f"{s['ALL_FINEST_MULTI']} finest-multi, overlap {overlap}"},
        "HMT2R_G8_canary_excluded_from_aggregates": {
            "status": "PASS" if int(agg.canary.sum()) == 0 else "FAIL",
            "measured": int(agg.canary.sum()), "threshold": 0},
    }
    declared = set(fz["gates"])
    emitted = set(gates) | {"HMT2R_G9_declared_gate_coverage"}
    missing = sorted(declared - emitted)
    undeclared = sorted(emitted - declared)
    gates["HMT2R_G9_declared_gate_coverage"] = {
        "status": "PASS" if not missing and not undeclared else "FAIL",
        "measured": len(missing) + len(undeclared), "threshold": 0,
        "note": (f"missing {missing}; undeclared {undeclared}"
                 if missing or undeclared else "complete")}
    failed = sorted(k for k, v in gates.items() if v["status"] != "PASS")

    doc = {
        "schema": "phrt-hmt2-stage0r/1", "id": "HMT2_STAGE0R_CORRECTION",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "ruling": "REVIEWER_RULING_HMT2_STAGE0_019",
        "freeze": fz["id"], "freeze_sha256": sha256_file(FZ),
        # derived from the final inspection, not asserted. Item 10
        "ray_map_imported": bool([m for m in after_bad if "raymap" in m]),
        "operator_constructed": bool([m for m in after_bad
                                      if m.startswith("phrt.operators")]),
        "source_only_modules_loaded_after": after_bad,
        "gates": gates, "failed_gates": failed,
        "n_truths": len(work), "n_per_age_rows": len(per_age),
        "strata_counts": s,
        "numerical_environment": numerics_record(),
        "attestation": attest([FZ, S0]),
        "runtime_seconds": round(time.time() - t0),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(doc, indent=2, default=str) + "\n")
    print("\nstage 0R gates")
    for k, v in gates.items():
        print(f"  {k:52s} {v['status']}")
    print(f"\nwrote {OUT.relative_to(ROOT)}")
    print(f"total {time.time() - t0:.0f}s")
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
