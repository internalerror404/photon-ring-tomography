#!/usr/bin/env python3
"""Require the clean stage-1 rerun to reproduce the dirty run exactly.

REVIEWER_RULING_R1L_STAGE1_008 item 5. The correct stage-1 numbers were produced
by a run whose own runner was uncommitted. That is a governance defect and the
remedy is not an argument that the edit was harmless -- it is a clean rerun that
has to land on the same numbers.

Equality here is exact on every numeric cell, not a tolerance. The two runs use
the same seeds, the same rays and the same committed code, so any difference at
all is a defect rather than a rounding artefact, and the ruling says stop on
one.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from phrt.config import sha256_file

PRESERVED = ROOT / "artifacts" / "preserved" / "r1l_stage1_dirty_run"
TAB = ROOT / "artifacts" / "tables"
OUT = ROOT / "artifacts" / "provenance" / "R1L_STAGE1_REPRODUCTION.json"
DIRTY_RUN = "R1L_20260827T044757Z_2ba66f02"
KEYS = ["source_class", "arm", "temporal_mode", "retarded_age", "parent", "child"]


def canonical(df: pd.DataFrame) -> pd.DataFrame:
    by = [c for c in KEYS if c in df.columns]
    d = df.sort_values(by).reset_index(drop=True) if by else df.reset_index(drop=True)
    return d[sorted(d.columns)]


def compare(a: pd.DataFrame, b: pd.DataFrame) -> dict:
    a, b = canonical(a), canonical(b)
    if a.shape != b.shape:
        return {"equal": False, "reason": f"shape {a.shape} vs {b.shape}"}
    if list(a.columns) != list(b.columns):
        return {"equal": False, "reason": "column sets differ"}
    diffs = {}
    for c in a.columns:
        x, y = a[c], b[c]
        if pd.api.types.is_numeric_dtype(x) and pd.api.types.is_numeric_dtype(y):
            xv, yv = x.to_numpy(), y.to_numpy()
            bad = ~((xv == yv) | (pd.isna(xv) & pd.isna(yv)))
            if bad.any():
                i = int(np.argmax(bad))
                diffs[c] = {"n_differing": int(bad.sum()), "first_row": i,
                            "preserved": float(xv[i]), "rerun": float(yv[i]),
                            "abs_diff": float(abs(xv[i] - yv[i]))}
        elif not x.equals(y):
            diffs[c] = {"n_differing": int((x != y).sum()), "kind": "non-numeric"}
    return {"equal": not diffs, "n_rows": int(len(a)),
            "n_columns": int(len(a.columns)), "differing_columns": diffs}


def main() -> int:
    t0 = time.time()
    if not PRESERVED.exists():
        raise SystemExit(f"{PRESERVED} is missing; nothing to reproduce against")
    tables = sorted(p.stem for p in PRESERVED.glob("r1l_*.parquet"))
    results, all_equal = {}, True
    for name in tables:
        new = TAB / f"{name}.parquet"
        if not new.exists():
            results[name] = {"equal": False, "reason": "rerun did not emit it"}
            all_equal = False
            continue
        r = compare(pd.read_parquet(PRESERVED / f"{name}.parquet"),
                    pd.read_parquet(new))
        r["preserved_sha256"] = sha256_file(PRESERVED / f"{name}.parquet")
        r["rerun_sha256"] = sha256_file(new)
        results[name] = r
        all_equal &= r["equal"]

    mans = sorted((ROOT / "artifacts" / "manifests").glob("R1L_*.json"))
    clean = json.loads(mans[-1].read_text())
    a = clean["attestation"]
    clean_tree = bool(a.get("clean")) and bool(a.get("preregistered"))
    gates = json.loads((ROOT / "artifacts" / "gates"
                        / "r1l_stage1_gates.json").read_text())
    failing = [k for k, v in gates["gates"].items() if v["status"] != "PASS"]

    verdict = ("R1L_STAGE1_CLEAN_REPRODUCTION_CONFIRMED"
               if all_equal and clean_tree and not failing
               else "R1L_STAGE1_REPRODUCTION_DISCREPANCY_STOP")
    doc = {
        "schema": "phrt-reproduction/1",
        "id": "R1L_STAGE1_CLEAN_RERUN",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "ruling": "REVIEWER_RULING_R1L_STAGE1_008 item 5",
        "equality_rule": "exact on every numeric cell, no tolerance. Same seeds, "
                         "same rays, same committed code, so any difference is a "
                         "defect",
        "preserved_run": DIRTY_RUN,
        "clean_run": clean["run_id"],
        "clean_run_attestation": {k: a.get(k) for k in
                                  ("execution_commit", "clean", "preregistered",
                                   "n_tracked_changes", "n_untracked",
                                   "porcelain_registered_sha256")},
        "code_edited_between_runs": False,
        "gates_failing_on_clean_run": failing,
        "all_canonical_tables_equal": bool(all_equal),
        "n_tables_compared": len(tables),
        "tables": results,
        "verdict": verdict,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(doc, indent=2) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}")
    for name, r in results.items():
        n = r.get("n_rows", "?")
        print(f"  {'EQUAL' if r['equal'] else 'DIFFER'}  {name:34s} rows {n}"
              + ("" if r["equal"] else f"  {r.get('reason', r.get('differing_columns'))}"))
    print(f"  clean tree: {clean_tree}   gates failing: {failing or 'none'}")
    print(f"  verdict: {verdict}")
    print(f"total {time.time() - t0:.0f}s")
    return 0 if verdict.endswith("CONFIRMED") else 1


if __name__ == "__main__":
    raise SystemExit(main())
