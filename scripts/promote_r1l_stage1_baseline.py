#!/usr/bin/env python3
"""Promote a pinned, reproduced stage-1 run to the canonical artifacts.

REVIEWER_RULING_R1L_REPRODUCIBILITY_009 item 11. Promotion is a separate,
guarded act rather than a side effect of running, because the canonical tables
are what every downstream artifact reads and a run that has not been reproduced
has no business writing them.

Four conditions, all checked, none assumed:
  the deterministic-reproduction verdict is PASS;
  the run being promoted is one of the two runs that verdict was computed from;
  it covers the full six-class ladder;
  its attestation is clean and preregistered and every BLAS pool reported one
  thread.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from phrt.numerics import pin

pin()

import pandas as pd  # noqa: E402

from phrt.config import sha256_file  # noqa: E402
from phrt.io.manifests import Gate, merge_gate_file  # noqa: E402

RUNS = ROOT / "artifacts" / "runs"
TAB = ROOT / "artifacts" / "tables"
GATES = ROOT / "artifacts" / "gates"
REPRO = ROOT / "artifacts" / "provenance" / "R1L_STAGE1_REPRODUCTION.json"
OUT = ROOT / "artifacts" / "provenance" / "R1L_STAGE1_BASELINE.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    args = ap.parse_args()

    if not REPRO.exists():
        raise SystemExit("no reproduction record; promotion is not authorized")
    rd = json.loads(REPRO.read_text())
    if not rd["verdict"].endswith("PASS"):
        raise SystemExit(f"reproduction verdict is {rd['verdict']}; "
                         "promotion is not authorized")
    pair = {rd["pinned_pair"]["a"]["run_id"], rd["pinned_pair"]["b"]["run_id"]}
    if args.run not in pair:
        raise SystemExit(f"{args.run} is not one of the reproduced pinned runs "
                         f"{sorted(pair)}")

    man = json.loads((ROOT / "artifacts" / "manifests" / f"{args.run}.json").read_text())
    att, num = man.get("attestation", {}), man.get("numerics", {})
    if len(man.get("classes") or []) < 6:
        raise SystemExit("not a full six-class ladder")
    if not (att.get("clean") and att.get("preregistered")):
        raise SystemExit("the run's attestation is not clean and preregistered")
    if not num.get("all_pools_single_threaded"):
        raise SystemExit("the run did not record single-threaded BLAS pools")

    src = RUNS / args.run / "tables"
    promoted = {}
    for p in sorted(src.glob("r1l_*.parquet")):
        shutil.copy2(p, TAB / p.name)
        csv = p.with_suffix(".csv")
        if csv.exists():
            shutil.copy2(csv, TAB / csv.name)
        promoted[p.name] = sha256_file(TAB / p.name)

    gate_doc = json.loads((RUNS / args.run / "gates" / "r1l_stage1_gates.json").read_text())
    gate_doc["promoted"] = True
    gate_doc["promoted_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    (GATES / "r1l_stage1_gates.json").write_text(json.dumps(gate_doc, indent=2) + "\n")
    merge_gate_file([Gate(k, v["status"], measured=v.get("measured"),
                          threshold=v.get("threshold"), note=v.get("note", ""))
                     for k, v in gate_doc["gates"].items()], args.run)

    OUT.write_text(json.dumps({
        "schema": "phrt-stage-baseline/1",
        "id": "R1L_STAGE1_PINNED_BASELINE",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "ruling": "REVIEWER_RULING_R1L_REPRODUCIBILITY_009 item 11",
        "baseline_run": args.run,
        "reproduced_by": sorted(pair - {args.run})[0],
        "reproduction_verdict": rd["verdict"],
        "execution_commit": att.get("execution_commit"),
        "attestation": {k: att.get(k) for k in
                        ("clean", "preregistered", "n_tracked_changes",
                         "n_untracked", "porcelain_registered_sha256")},
        "numerics": num,
        "promoted_tables": promoted,
        "rule": "the canonical tables are byte-identical to the baseline run's "
                "own outputs, and the baseline was reproduced cell for cell by "
                "an independent process under the same pinned environment",
    }, indent=2) + "\n")

    print(f"promoted {args.run}")
    for k, v in promoted.items():
        print(f"  {k:38s} {v[:16]}...")
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
