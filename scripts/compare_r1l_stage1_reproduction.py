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
NUMERICAL_ZERO = 1e-12          # the campaign's standard "is this zero" tolerance
KEYS = ["source_class", "arm", "temporal_mode", "retarded_age", "parent", "child"]


def latest_full_run(mans: Path) -> Path:
    """The newest stage-1 manifest that covers every class.

    Selecting by timestamp alone is wrong: a diagnostic invocation restricted to
    one class writes a manifest too, and picking it up would attach the wrong
    provenance to a full-ladder comparison.
    """
    full = [p for p in sorted(mans.glob("R1L_*.json"))
            if len(json.loads(p.read_text()).get("extra", {}).get("classes", [])) >= 6]
    if not full:
        raise SystemExit("no full-ladder R1L run manifest found")
    return full[-1]


def canonical(df: pd.DataFrame) -> pd.DataFrame:
    by = [c for c in KEYS if c in df.columns]
    d = df.sort_values(by).reset_index(drop=True) if by else df.reset_index(drop=True)
    return d[sorted(d.columns)]


def is_discrete(x: pd.Series) -> bool:
    """A rank, a count, a nullity or a flag: any of these differing is fatal.

    Split out from the continuous spectral quantities because the two carry
    completely different evidential weight. A rank that moved means the audit
    reached a different conclusion. A singular value that moved in its last bits
    means the reduction order changed.
    """
    return (pd.api.types.is_bool_dtype(x) or pd.api.types.is_integer_dtype(x)
            or not pd.api.types.is_numeric_dtype(x))


def compare(a: pd.DataFrame, b: pd.DataFrame) -> dict:
    a, b = canonical(a), canonical(b)
    if a.shape != b.shape:
        return {"equal": False, "reason": f"shape {a.shape} vs {b.shape}"}
    if list(a.columns) != list(b.columns):
        return {"equal": False, "reason": "column sets differ"}
    diffs, worst_rel, n_disc, n_cont = {}, 0.0, 0, 0
    discrete_differ = []
    for c in a.columns:
        x, y = a[c], b[c]
        disc = is_discrete(x)
        n_disc += disc
        n_cont += not disc
        if pd.api.types.is_numeric_dtype(x) and pd.api.types.is_numeric_dtype(y):
            xv = x.to_numpy(dtype=float)
            yv = y.to_numpy(dtype=float)
            bad = ~((xv == yv) | (np.isnan(xv) & np.isnan(yv)))
            if bad.any():
                scale = np.maximum(np.abs(xv), np.abs(yv))
                rel = np.where(scale > 0, np.abs(xv - yv) / np.maximum(scale, 1e-300),
                               0.0)
                # A relative difference between two numerically-zero
                # quantities is not a discrepancy, it is a ratio of noise. Null
                # singular values and the class-nesting residual are exactly
                # that: unfloored they dominate the summary with ratios near one
                # while the quantities themselves are 1e-37 and 1e-107. The
                # floor is the campaign's existing numerical-zero tolerance,
                # not a value chosen after seeing these numbers.
                floor = NUMERICAL_ZERO
                sig = bad & (scale > floor)
                i = int(np.argmax(np.where(sig if sig.any() else bad, rel, -1.0)))
                srel = float(rel[sig].max()) if sig.any() else 0.0
                worst_rel = max(worst_rel, srel)
                diffs[c] = {"discrete": bool(disc),
                            "n_differing": int(bad.sum()),
                            "n_differing_above_noise_floor": int(sig.sum()),
                            "noise_floor": floor,
                            "worst_relative_difference_above_floor": srel,
                            "worst_relative_difference_unfloored":
                                float(rel[bad].max()),
                            "at_row": i, "preserved": float(xv[i]),
                            "rerun": float(yv[i]),
                            "abs_diff": float(abs(xv[i] - yv[i]))}
                if disc:
                    discrete_differ.append(c)
        elif not x.equals(y):
            diffs[c] = {"discrete": True, "n_differing": int((x != y).sum()),
                        "kind": "non-numeric"}
            discrete_differ.append(c)
    return {"equal": not diffs,
            "discrete_results_equal": not discrete_differ,
            "differing_discrete_columns": discrete_differ,
            "worst_relative_difference": worst_rel,
            "n_rows": int(len(a)), "n_columns": int(len(a.columns)),
            "n_discrete_columns": int(n_disc), "n_continuous_columns": int(n_cont),
            "differing_columns": diffs}


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

    clean = json.loads(latest_full_run(ROOT / "artifacts" / "manifests").read_text())
    a = clean["attestation"]
    clean_tree = bool(a.get("clean")) and bool(a.get("preregistered"))
    gates = json.loads((ROOT / "artifacts" / "gates"
                        / "r1l_stage1_gates.json").read_text())
    failing = [k for k, v in gates["gates"].items() if v["status"] != "PASS"]

    discrete_equal = all(r.get("discrete_results_equal", False) for r in results.values())
    worst_rel = max((r.get("worst_relative_difference", 0.0)
                     for r in results.values()), default=0.0)
    n_above = sum(d.get("n_differing_above_noise_floor", 0)
                  for r in results.values()
                  for d in r.get("differing_columns", {}).values())
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
        "all_discrete_results_equal": bool(discrete_equal),
        "worst_relative_difference_above_noise_floor": worst_rel,
        "n_differing_cells_above_noise_floor": int(n_above),
        "noise_floor": NUMERICAL_ZERO,
        "noise_floor_rule": f"a cell counts toward the relative-difference "
                            f"summary only if max(|preserved|, |rerun|) exceeds "
                            f"{NUMERICAL_ZERO:g}, the campaign's existing "
                            f"numerical-zero tolerance. Cells below it are still "
                            f"compared and recorded, but a ratio of two "
                            f"numerically-zero quantities is not a discrepancy. "
                            f"The floor was not chosen after seeing these numbers",
        "discrete_vs_continuous": "ranks, nullities, exact-zero counts, "
                                  "operational ranks and detectability flags are "
                                  "discrete; singular values, condition numbers "
                                  "and information volumes are continuous. A "
                                  "discrete difference means the audit reached a "
                                  "different conclusion; a continuous one at "
                                  "last-bit magnitude means the reduction order "
                                  "changed",
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
    print(f"  discrete results equal: {discrete_equal}   "
          f"worst relative difference above floor: {worst_rel:.3e}   "
          f"cells above floor: {n_above}")
    print(f"  clean tree: {clean_tree}   gates failing: {failing or 'none'}")
    print(f"  verdict: {verdict}")
    print(f"total {time.time() - t0:.0f}s")
    return 0 if verdict.endswith("CONFIRMED") else 1


if __name__ == "__main__":
    raise SystemExit(main())
