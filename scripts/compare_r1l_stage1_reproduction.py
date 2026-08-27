#!/usr/bin/env python3
"""Deterministic-reproduction check for R1L stage 1.

REVIEWER_RULING_R1L_REPRODUCIBILITY_009 items 9, 10 and 12. Two separate
questions, held apart because they carry different evidential weight.

Item 9 -- the pinned pair. Two complete six-class runs executed in separate
processes from one clean committed tree under the pinned numerical environment.
Every normalized scientific cell must be exactly equal. There is no tolerance
here and there should not be: identical code, identical seeds, identical rays
and a serial BLAS leave nothing that may legitimately differ. A mismatch is
``R1L_STAGE1_DETERMINISTIC_REPRODUCTION_FAIL_STOP``.

Item 10 -- the preserved runs. The pinned baseline is compared against every
stage-1 run that predates the pin. Those ran with a multithreaded BLAS whose
reduction order was never recorded, so their last bits are not reproducible and
demanding bitwise equality of them would be demanding something the environment
cannot deliver. What is demanded is exact agreement on every *discrete*
scientific conclusion -- ranks, nullities, exact-zero column counts, operational
ranks, detectability flags. Continuous differences are reported, with their
magnitudes, and not treated as failures.

The blocking gate ``R1L_G12_deterministic_reproduction`` is emitted either way,
so the canonical gate set carries the status rather than a report sentence.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from phrt.numerics import pin

pin()

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from phrt.config import sha256_file  # noqa: E402
from phrt.io.manifests import Gate, merge_gate_file  # noqa: E402

RUNS = ROOT / "artifacts" / "runs"
PRESERVED = ROOT / "artifacts" / "preserved"
OUT = ROOT / "artifacts" / "provenance" / "R1L_STAGE1_REPRODUCTION.json"
GATE = "R1L_G12_deterministic_reproduction"
KEYS = ["source_class", "arm", "temporal_mode", "retarded_age", "parent", "child"]
NUMERICAL_ZERO = 1e-12
TABLES = ("r1l_class_spectra", "r1l_temporal_mode_visibility",
          "r1l_old_structural_support", "r1l_age_information",
          "r1l_class_nesting", "r1l_temporal_supports")


def normalize(df: pd.DataFrame) -> pd.DataFrame:
    """Row order and column order made canonical, so equality tests content."""
    by = [c for c in KEYS if c in df.columns]
    d = df.sort_values(by).reset_index(drop=True) if by else df.reset_index(drop=True)
    return d[sorted(d.columns)]


def is_discrete(x: pd.Series) -> bool:
    """A rank, a count, a nullity or a flag. Any of these differing is fatal."""
    return (pd.api.types.is_bool_dtype(x) or pd.api.types.is_integer_dtype(x)
            or not pd.api.types.is_numeric_dtype(x))


def diff_table(a: pd.DataFrame, b: pd.DataFrame) -> dict:
    a, b = normalize(a), normalize(b)
    if a.shape != b.shape or list(a.columns) != list(b.columns):
        return {"exactly_equal": False, "discrete_equal": False,
                "reason": f"shape/columns differ: {a.shape} vs {b.shape}"}
    cols, worst, n_above, disc_bad = {}, 0.0, 0, []
    for c in a.columns:
        x, y = a[c], b[c]
        disc = is_discrete(x)
        if pd.api.types.is_numeric_dtype(x) and pd.api.types.is_numeric_dtype(y):
            xv, yv = x.to_numpy(dtype=float), y.to_numpy(dtype=float)
            bad = ~((xv == yv) | (np.isnan(xv) & np.isnan(yv)))
            if not bad.any():
                continue
            scale = np.maximum(np.abs(xv), np.abs(yv))
            rel = np.where(scale > 0, np.abs(xv - yv) / np.maximum(scale, 1e-300), 0.0)
            sig = bad & (scale > NUMERICAL_ZERO)
            srel = float(rel[sig].max()) if sig.any() else 0.0
            worst = max(worst, srel)
            n_above += int(sig.sum())
            i = int(np.argmax(np.where(sig if sig.any() else bad, rel, -1.0)))
            cols[c] = {"discrete": bool(disc), "n_differing": int(bad.sum()),
                       "n_differing_above_noise_floor": int(sig.sum()),
                       "worst_relative_difference_above_floor": srel,
                       "example": {"row": i, "a": float(xv[i]), "b": float(yv[i]),
                                   "abs_diff": float(abs(xv[i] - yv[i]))}}
            if disc:
                disc_bad.append(c)
        elif not x.equals(y):
            cols[c] = {"discrete": True, "n_differing": int((x != y).sum()),
                       "kind": "non-numeric"}
            disc_bad.append(c)
    return {"exactly_equal": not cols, "discrete_equal": not disc_bad,
            "differing_discrete_columns": disc_bad,
            "worst_relative_difference_above_floor": worst,
            "n_differing_cells_above_noise_floor": n_above,
            "n_rows": int(len(a)), "differing_columns": cols}


def load(d: Path, name: str) -> pd.DataFrame | None:
    p = d / f"{name}.parquet"
    return pd.read_parquet(p) if p.exists() else None


def compare_dirs(a: Path, b: Path) -> dict:
    out = {}
    for name in TABLES:
        da, db = load(a, name), load(b, name)
        if da is None or db is None:
            out[name] = {"exactly_equal": False, "discrete_equal": False,
                         "reason": f"missing in {'a' if da is None else 'b'}"}
        else:
            out[name] = diff_table(da, db)
    return out


def roll(res: dict) -> dict:
    return {"all_exactly_equal": all(v["exactly_equal"] for v in res.values()),
            "all_discrete_equal": all(v["discrete_equal"] for v in res.values()),
            "worst_relative_difference_above_floor":
                max((v.get("worst_relative_difference_above_floor", 0.0)
                     for v in res.values()), default=0.0),
            "n_differing_cells_above_noise_floor":
                sum(v.get("n_differing_cells_above_noise_floor", 0)
                    for v in res.values())}


def run_meta(run_id: str) -> dict:
    p = ROOT / "artifacts" / "manifests" / f"{run_id}.json"
    if not p.exists():
        return {"run_id": run_id, "manifest": "missing"}
    d = json.loads(p.read_text())
    a = d.get("attestation", {})
    n = d.get("numerics", {})
    return {"run_id": run_id,
            "execution_commit": a.get("execution_commit"),
            "clean": a.get("clean"), "preregistered": a.get("preregistered"),
            "n_tracked_changes": a.get("n_tracked_changes"),
            "n_untracked": a.get("n_untracked"),
            "classes": d.get("classes"),
            "pinned_environment": n.get("pinned_environment"),
            "threadpool_state": n.get("threadpool_state"),
            "all_pools_single_threaded": n.get("all_pools_single_threaded"),
            "gate_status": d.get("gate_status")}


def main() -> int:
    t0 = time.time()
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", default="", help="first pinned run id")
    ap.add_argument("--b", default="", help="second pinned run id")
    args = ap.parse_args()

    doc = {"schema": "phrt-reproduction/2",
           "id": "R1L_STAGE1_DETERMINISTIC_REPRODUCTION",
           "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "ruling": "REVIEWER_RULING_R1L_REPRODUCIBILITY_009 items 9, 10, 12",
           "noise_floor": NUMERICAL_ZERO,
           "noise_floor_rule": "applies only to the preserved-run comparison of "
                               "item 10. The pinned pair of item 9 is compared "
                               "with no floor and no tolerance"}

    if not (args.a and args.b):
        doc["verdict"] = "R1L_STAGE1_DETERMINISTIC_REPRODUCTION_PENDING"
        doc["pinned_pair"] = {"status": "not yet executed"}
        status, measured = "FAIL", 0
        note = ("no pinned pair has been executed, so deterministic "
                "reproduction is unproven. Blocking by default")
    else:
        da, db = RUNS / args.a / "tables", RUNS / args.b / "tables"
        for d in (da, db):
            if not d.exists():
                raise SystemExit(f"{d} is missing; run the pinned pair first")
        ma, mb = run_meta(args.a), run_meta(args.b)
        res = compare_dirs(da, db)
        r = roll(res)
        pinned_ok = (r["all_exactly_equal"]
                     and bool(ma.get("all_pools_single_threaded"))
                     and bool(mb.get("all_pools_single_threaded"))
                     and bool(ma.get("preregistered")) and bool(mb.get("preregistered"))
                     and ma.get("execution_commit") == mb.get("execution_commit"))
        doc["pinned_pair"] = {"a": ma, "b": mb, "tables": res, **r,
                              "same_execution_commit":
                                  ma.get("execution_commit") == mb.get("execution_commit"),
                              "equality_rule": "exact on every normalized "
                                               "scientific cell, no tolerance",
                              "passes": bool(pinned_ok)}

        prior = {}
        for pdir in sorted(PRESERVED.glob("r1l_stage1_*")):
            res_p = compare_dirs(da, pdir)
            prior[pdir.name] = {"tables": res_p, **roll(res_p)}
        doc["preserved_runs"] = {
            "rule": "exact agreement on all discrete scientific conclusions; "
                    "continuous differences reported, bitwise equality not "
                    "required because those runs used an unrecorded "
                    "multithreaded reduction order",
            "index": json.loads((PRESERVED / "PRESERVED_RUNS.json").read_text())
            if (PRESERVED / "PRESERVED_RUNS.json").exists() else {},
            "comparisons": prior,
            "all_discrete_conclusions_agree":
                all(v["all_discrete_equal"] for v in prior.values())}

        ok = pinned_ok and doc["preserved_runs"]["all_discrete_conclusions_agree"]
        doc["verdict"] = ("R1L_STAGE1_DETERMINISTIC_REPRODUCTION_PASS" if ok
                          else "R1L_STAGE1_DETERMINISTIC_REPRODUCTION_FAIL_STOP")
        status = "PASS" if ok else "FAIL"
        measured = r["n_differing_cells_above_noise_floor"] if not pinned_ok else 0
        note = ("two pinned six-class runs agree on every normalized scientific "
                "cell, and every discrete conclusion agrees with the preserved "
                "runs" if ok else
                "the pinned pair did not reproduce exactly, or a discrete "
                "conclusion moved against a preserved run")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(doc, indent=2, default=str) + "\n")
    merge_gate_file([Gate(GATE, status, measured=measured, threshold=0, note=note)],
                    doc.get("pinned_pair", {}).get("a", {}).get("run_id", "none"))
    print(f"wrote {OUT.relative_to(ROOT)}")
    if "pinned_pair" in doc and doc["pinned_pair"].get("tables"):
        for k, v in doc["pinned_pair"]["tables"].items():
            print(f"  pinned pair  {'EQUAL ' if v['exactly_equal'] else 'DIFFER'}  {k}")
        for name, v in doc["preserved_runs"]["comparisons"].items():
            print(f"  vs {name:34s} discrete_equal={v['all_discrete_equal']}  "
                  f"worst_rel={v['worst_relative_difference_above_floor']:.3e}")
    print(f"  gate {GATE}: {status}")
    print(f"  verdict: {doc['verdict']}")
    print(f"total {time.time() - t0:.0f}s")
    return 0 if doc["verdict"].endswith("PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
