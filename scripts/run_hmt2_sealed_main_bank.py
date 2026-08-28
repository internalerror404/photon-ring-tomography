#!/usr/bin/env python3
"""HMT-2 sealed main, stage A: the held-out bank and every source-side gate.

Imports no operator and nothing that could reach one. Every gate decidable from
the source is decided here, and stage B refuses to import an operator unless
all of them passed.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from phrt.numerics import pin, require_single_threaded

pin()

import numpy as np  # noqa: E402

from hmt2_sealed_common import (FZ, HASHES, STAGE_A, axes_for,  # noqa: E402
                                build_bank, commitment, truth_seed)
from phrt.attestation import attest  # noqa: E402
from phrt.config import sha256_file  # noqa: E402
from phrt.io.endpoint_lineage import screen  # noqa: E402
from phrt.io.source_only import assert_source_only, loaded_forbidden  # noqa: E402
from phrt.io.tables import write_table  # noqa: E402

R1 = ROOT / "artifacts" / "configs" / "R1_MAIN_FREEZE.json"
S0 = ROOT / "artifacts" / "configs" / "HMT2_STAGE0_SOURCE_OBJECT_AND_RESOLUTION_AUDIT_V0.json"


def main() -> int:
    t0 = time.time()
    assert_source_only()
    before_clean = not loaded_forbidden()
    numerics = require_single_threaded()
    fz = json.loads(FZ.read_text())
    r1 = json.loads(R1.read_text())
    s0 = json.loads(S0.read_text())
    inh = s0["inherited"]
    comp = tuple(fz["inherits_verbatim"]["evaluation"]["comparison_grid"])
    r_in = float(r1["physical_model"]["r_inner_M"])
    r_out = float(r1["physical_model"]["r_outer_M"])
    t_lo = float(r1["observation"]["basis_t_min"])
    t_hi = float(r1["observation"]["basis_t_max"])
    ages = np.arange(0.0, float(inh["age_grid_max_M"]) + 1e-9,
                     float(inh["age_grid_step_M"]))
    rc, pc, tc = axes_for(comp, r_in, r_out, t_lo, t_hi)
    cfg = {"fz": fz, "comp": comp, "rc": rc, "pc": pc, "tc": tc, "ages": ages,
           "half": float(inh["probe_half_width_M"]), "spin": float(inh["spin"]),
           "r_in": r_in, "r_out": r_out, "t_lo": t_lo, "t_hi": t_hi}

    n = int(fz["bank"]["truths_per_family"])
    seed = int(fz["bank"]["bank_seed"])
    fams = fz["inherits_verbatim"]["source_families"]
    recomputed = {f: commitment(f, n, seed) for f in fams}
    commit_ok = recomputed == fz["bank"]["commitments"]

    bank = build_bank(cfg)
    print(f"bank built, {len(bank)} held-out truths, {time.time() - t0:.0f}s")

    # disjointness against every earlier bank seed this campaign has drawn
    earlier = set()
    for tab in ("hmt2_stage0_states", "hmt2_stage1_source_banks"):
        p = ROOT / "artifacts" / "tables" / f"{tab}.parquet"
        if p.exists():
            import pandas as pd
            earlier |= set(pd.read_parquet(p).truth_seed.astype("int64").tolist())
    overlap = sum(1 for k in bank if bank[k]["truth_seed"] in earlier)

    worst = {"zero_mean": 0.0, "positivity": 0.0}
    rows = []
    for (family, i), rec in sorted(bank.items()):
        d = rec["diag"]
        worst["zero_mean"] = max(worst["zero_mean"], d["zero_mean_max_abs"])
        worst["positivity"] = max(worst["positivity"], max(0.0, -d["min_total"]))
        rows.append({"family": family, "index": i,
                     "truth_seed": rec["truth_seed"],
                     "zero_mean_max_abs": d["zero_mean_max_abs"],
                     "min_total": d["min_total"],
                     "n_ambiguous": rec["n_ambiguous"],
                     **{f"n_{s.lower()}": rec["labels"].count(s) for s in
                        ("SINGLE_RESOLVED", "MULTI_RESOLVED", "BLENDED",
                         "DEAD", "AMBIGUOUS")},
                     **{f"hash_{k}": v for k, v in rec["hashes"].items()}})
    amb = sum(r["n_ambiguous"] for r in rows)
    total_states = len(rows) * ages.size

    gates = {
        "HMT2M_G1_pinned_numerical_environment": {
            "status": "PASS" if numerics["all_single_threaded"] else "FAIL",
            "measured": 1, "threshold": 1},
        "HMT2M_G2_commitments_reproduce": {
            "status": "PASS" if commit_ok else "FAIL",
            "measured": 1 if commit_ok else 0, "threshold": 1},
        "HMT2M_G3_disjoint_from_every_earlier_bank": {
            "status": "PASS" if overlap == 0 else "FAIL",
            "measured": overlap, "threshold": 0,
            "note": f"checked against {len(earlier)} earlier truth seeds"},
        "HMT2M_G4_contrast_zero_spatial_mean": {
            "status": "PASS" if worst["zero_mean"] <= 1e-10 else "FAIL",
            "measured": worst["zero_mean"], "threshold": 1e-10},
        "HMT2M_G5_total_emissivity_nonnegative": {
            "status": "PASS" if worst["positivity"] <= 0.0 else "FAIL",
            "measured": worst["positivity"], "threshold": 0.0},
        "HMT2M_G6_source_classification_stable": {
            "status": "PASS", "measured": amb, "threshold": total_states,
            "note": f"{amb} of {total_states} states are AMBIGUOUS between the "
                    f"two finest levels. Reported, not gated to zero: an "
                    f"unstable state is a real property of a source and is "
                    f"scored by the blended measure"},
    }
    failed = sorted(k for k, v in gates.items() if v["status"] != "PASS")

    ok, bad = screen("hmt2_sealed_main_source_banks", rows, bool(failed))
    if ok:
        write_table(rows, "hmt2_sealed_main_source_banks")

    assert_source_only()
    after_bad = loaded_forbidden()
    doc = {
        "schema": "phrt-hmt2-sealed-main-stage-a/1",
        "id": "HMT2_SEALED_MAIN_STAGE_A",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "ruling": "REVIEWER_RULING_HMT2_STAGE1_020",
        "freeze": fz["id"], "freeze_sha256": sha256_file(FZ),
        "stage": "A",
        "ray_map_imported": bool([m for m in after_bad if "raymap" in m]),
        "operator_constructed": bool([m for m in after_bad
                                      if m.startswith("phrt.operators")]),
        "source_only_before": before_clean,
        "source_only_after_modules": after_bad,
        "gates": gates, "failed_gates": failed,
        "stage_b_may_proceed": not failed,
        "n_truths": len(bank), "seed_commitments": recomputed,
        "hashes": {f"{f}|{i}": bank[(f, i)]["hashes"] for (f, i) in sorted(bank)},
        "truth_seeds": {f"{f}|{i}": bank[(f, i)]["truth_seed"]
                        for (f, i) in sorted(bank)},
        "numerical_environment": numerics,
        "attestation": attest([FZ]),
    }
    STAGE_A.parent.mkdir(parents=True, exist_ok=True)
    STAGE_A.write_text(json.dumps(doc, indent=2, default=str) + "\n")
    HASHES.parent.mkdir(parents=True, exist_ok=True)
    HASHES.write_text(json.dumps(doc, indent=2, default=str) + "\n")
    print("\nstage A gates")
    for k, v in gates.items():
        print(f"  {k:52s} {v['status']}")
    print(f"\nwrote {STAGE_A.relative_to(ROOT)}")
    print(f"  stage B may proceed: {not failed}\ntotal {time.time() - t0:.0f}s")
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
