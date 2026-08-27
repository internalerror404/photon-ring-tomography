#!/usr/bin/env python3
"""Require the gate-completed 2R-B rerun to reproduce 151229d bitwise.

Reviewer ruling item 10. Every scientific cell that existed before the repair
must be identical; only newly added diagnostic fields and newly added tables may
appear. Any change to a pre-existing value means the gate completion altered the
experiment rather than describing it, which is the one outcome the repair was
not allowed to have.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from phrt.numerics import pin

pin()

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

BASE = "151229d45c08012e8aa5197f389cce49784b6080"
TAB = ROOT / "artifacts" / "tables"
OUT = ROOT / "artifacts" / "provenance" / "R1L_2RB_GATE_COMPLETION_REPRODUCTION.json"
KEYS = ["source_class", "arm", "estimator", "snr0", "bank", "family", "index",
        "split", "retarded_age", "target_separation_sigma", "scope", "draw",
        "noise_semantics"]


def at_base(rel: str) -> pd.DataFrame | None:
    out = subprocess.run(["git", "show", f"{BASE}:{rel}"], cwd=ROOT,
                         capture_output=True)
    if out.returncode != 0:
        return None
    tmp = ROOT / ".git" / "_cmp.parquet"
    tmp.write_bytes(out.stdout)
    df = pd.read_parquet(tmp)
    tmp.unlink()
    return df


def normalize(df, cols):
    by = [c for c in KEYS if c in cols]
    d = df.sort_values(by).reset_index(drop=True) if by else df.reset_index(drop=True)
    return d[sorted(cols)]


def main() -> int:
    t0 = time.time()
    results, identical = {}, True
    for p in sorted(TAB.glob("r1l_2rb_*.parquet")):
        rel = str(p.relative_to(ROOT))
        old = at_base(rel)
        new = pd.read_parquet(p)
        if old is None:
            results[p.stem] = {"status": "NEW_TABLE", "n_rows": int(len(new)),
                               "columns": sorted(new.columns)}
            continue
        shared = sorted(set(old.columns) & set(new.columns))
        added = sorted(set(new.columns) - set(old.columns))
        dropped = sorted(set(old.columns) - set(new.columns))
        a, b = normalize(old, shared), normalize(new, shared)
        if a.shape != b.shape:
            results[p.stem] = {"status": "SHAPE_CHANGED", "added_columns": added,
                               "dropped_columns": dropped,
                               "rows_before": int(len(a)), "rows_after": int(len(b))}
            identical = False
            continue
        diffs = {}
        for c in shared:
            x, y = a[c], b[c]
            if pd.api.types.is_numeric_dtype(x) and pd.api.types.is_numeric_dtype(y):
                xv, yv = x.to_numpy(float), y.to_numpy(float)
                bad = ~((xv == yv) | (np.isnan(xv) & np.isnan(yv)))
            else:
                bad = (x != y).to_numpy()
            if bad.any():
                i = int(np.argmax(bad))
                diffs[c] = {"n_differing": int(bad.sum()), "row": i,
                            "before": str(a[c].iloc[i]), "after": str(b[c].iloc[i])}
        results[p.stem] = {
            "status": "IDENTICAL" if not diffs else "CHANGED",
            "n_rows": int(len(b)), "n_shared_columns": len(shared),
            "added_columns": added, "dropped_columns": dropped,
            "differing_columns": diffs}
        identical &= not diffs and not dropped

    verdict = ("R1L_STAGE2R_GATE_COMPLETION_PASS" if identical
               else "R1L_STAGE2R_GATE_COMPLETION_FAIL_STOP")
    doc = {"schema": "phrt-reproduction/3",
           "id": "R1L_2RB_GATE_COMPLETION_REPRODUCTION",
           "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "baseline_commit": BASE,
           "rule": "every pre-existing scientific cell must be bitwise "
                   "identical. New diagnostic columns and new tables are "
                   "permitted; a dropped column or a changed value is not",
           "all_preexisting_cells_identical": bool(identical),
           "tables": results, "verdict": verdict}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(doc, indent=2, default=str) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}")
    for k, v in results.items():
        extra = (f"  +{len(v.get('added_columns', []))} new cols"
                 if v.get("added_columns") else "")
        print(f"  {v['status']:14s} {k}{extra}")
    print(f"  verdict: {verdict}")
    print(f"total {time.time() - t0:.0f}s")
    return 0 if identical else 1


if __name__ == "__main__":
    raise SystemExit(main())
