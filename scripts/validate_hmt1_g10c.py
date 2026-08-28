#!/usr/bin/env python3
"""Validate HMT1M_G10c before any replacement held-out truth exists.

Item 7 of REVIEWER_RULING_HMT1_MAIN_017: the complete validation bank, several
scratch banks, and the analytic canaries (those live in
tests/test_windowed_reference.py and run with the suite).

This touches no operator and no held-out bank.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from phrt.numerics import pin

pin()

import numpy as np  # noqa: E402

from phrt.io.tables import write_table  # noqa: E402
from phrt.metrics.features import extract  # noqa: E402
from phrt.metrics.windowed_reference import (peak_agreement,  # noqa: E402
                                             windowed_peak)
from phrt.sources.contrast import FAMILIES, OFF_MANIFOLD, build  # noqa: E402

VFZ = ROOT / "artifacts" / "configs" / "HMT1_VALIDATION_FREEZE_V0.json"
R1 = ROOT / "artifacts" / "configs" / "R1_MAIN_FREEZE.json"
OUT = ROOT / "artifacts" / "provenance" / "HMT1_G10C_VALIDATION.json"
HALF = 3.0
SCRATCH_SEEDS = (770001, 770002, 770003)


def vseed(family, split, regime, i, seed):
    p = json.dumps({"family": family, "split": split, "regime": regime,
                    "n": 8, "seed": seed, "model": "contrast"},
                   sort_keys=True).encode()
    return int(hashlib.sha256(p + f"|{i}".encode()).hexdigest()[:16], 16) % (2 ** 63)


def main() -> int:
    t0 = time.time()
    vfz = json.loads(VFZ.read_text())
    r1 = json.loads(R1.read_text())
    eg = vfz["evaluation_grid"]
    NR, NP, NT = eg["n_radial"], eg["n_azimuthal"], eg["n_temporal"]
    r_in = float(r1["physical_model"]["r_inner_M"])
    r_out = float(r1["physical_model"]["r_outer_M"])
    t_lo = float(r1["observation"]["basis_t_min"])
    t_hi = float(r1["observation"]["basis_t_max"])
    spin = float(vfz["geometry"]["a_star"])
    r_axis = np.exp(np.linspace(np.log(r_in), np.log(r_out), NR))
    phi_axis = np.linspace(0.0, 2 * np.pi, NP, endpoint=False)
    t_axis = np.linspace(t_lo, t_hi, NT)
    R, P, T = np.meshgrid(r_axis, phi_axis, t_axis, indexing="ij")
    gr, gp, gt = R.ravel(), P.ravel(), T.ravel()
    ti = np.tile(np.arange(NT), NR * NP)
    ages = np.arange(0.0, float(r1["metrics"]["age_grid_max_M"]) + 1e-9,
                     float(vfz["primary_endpoints"]["stable_feature_interval"]
                           ["age_grid_step_M"]))

    rows = []

    def score(bank, family, key, seed):
        rng = np.random.default_rng(seed)
        _, fl, _, dj, _, _ = build(rng, family, spin, r_in, r_out, gr, gp, gt,
                                   ti, NT)
        f = extract(dj, gt, ages, r_axis, phi_axis, HALF)
        ref = windowed_peak(fl, t_axis, ages, r_in, r_out, NR, NP, HALF)
        a = peak_agreement(f, ref, r_axis, phi_axis)
        rows.append({"bank": bank, "family": family, "key": key,
                     "truth_seed": seed, **a,
                     "worst_cells": max(a["radial_cells"], a["azimuthal_cells"])})

    for family in vfz["counts"]["families"]:
        for split in vfz["counts"]["splits"]:
            for regime in vfz["counts"]["regimes"]:
                for i in range(vfz["counts"]["truths_per_family_split_regime"]):
                    s = vseed(family, split, regime, i, vfz["seeds"]["bank_seed"])
                    score("validation", family, f"{split}|{regime}|{i}", s)
        print(f"  validation {family}: {time.time() - t0:.0f}s")

    for sseed in SCRATCH_SEEDS:
        for family in list(FAMILIES) + list(OFF_MANIFOLD):
            for i in range(4):
                s = int(hashlib.sha256(
                    f"g10c_scratch|{sseed}|{family}|{i}".encode()
                ).hexdigest()[:16], 16) % (2 ** 63)
                score(f"scratch_{sseed}", family, str(i), s)
        print(f"  scratch {sseed}: {time.time() - t0:.0f}s")

    write_table(rows, "hmt1_g10c_validation")
    worst = max(r["worst_cells"] for r in rows)
    per_bank = {}
    for r in rows:
        per_bank[r["bank"]] = max(per_bank.get(r["bank"], 0.0), r["worst_cells"])
    per_family = {}
    for r in rows:
        per_family[r["family"]] = max(per_family.get(r["family"], 0.0),
                                      r["worst_cells"])
    doc = {
        "schema": "phrt-g10c-validation/1",
        "id": "HMT1_G10C_VALIDATION",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "ruling": "REVIEWER_RULING_HMT1_MAIN_017",
        "gate": "HMT1M_G10c_truth_extraction_matches_independent_windowed_reference",
        "threshold_cells": 1.0,
        "n_truths_scored": len(rows),
        "banks": sorted(per_bank),
        "worst_cells_overall": worst,
        "worst_cells_by_bank": per_bank,
        "worst_cells_by_family": per_family,
        "n_over_threshold": sum(1 for r in rows if r["worst_cells"] > 1.0),
        "held_out_bank_touched": False,
        "operator_imported": False,
        "analytic_canaries": "tests/test_windowed_reference.py",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(doc, indent=2, default=str) + "\n")
    print(f"\nwrote {OUT.relative_to(ROOT)}")
    print(f"  {len(rows)} truths, worst {worst:.3f} cells, "
          f"{doc['n_over_threshold']} over threshold")
    for k, v in sorted(per_family.items()):
        print(f"    {k:30s} {v:.3f}")
    print(f"total {time.time() - t0:.0f}s")
    return 0 if doc["n_over_threshold"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
