#!/usr/bin/env python3
"""Q2 preexecution freeze: everything fixed before the first outcome exists.

Ruling 026 requires a genuine preexecution commit, not a snapshot written
after the diagnostics. This script produces only the freeze. It reads no
result, computes no response and decides nothing from data. The Q2 runner
refuses to start unless the freeze it is handed matches the tree.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

GEOMETRY = "a050_i050"
ORDERS = (0, 1, 2)
PROFILES = ("coarse", "core", "fine")
SIGMA = 0.011341986814407566
OBSERVER_TIMES = [0.0, 2.857142857142857, 5.714285714285714,
                  8.571428571428571, 11.428571428571429, 14.285714285714286,
                  17.142857142857142, 20.0]

# D026. Declared from geometry: the original order-0 screen limit and its core
# spacing. Not a telescope resolution and not a replacement for the archived
# 0.02 M design, which stays in the record as a different measurement.
DETECTOR = {"alpha_bounds_M": [-25.0, 25.0], "beta_bounds_M": [-25.0, 25.0],
            "pitch_M": 0.4, "cells": [125, 125]}

# One absolute clock for every profile. Each archived map recentred its own
# delays on that profile's latest order-0 arrival, which is exactly the
# per-profile recentring the ruling forbids; the three references differ by
# up to 0.69 M. The core profile's reference is adopted as the fixed origin
# and every profile's delays are re-expressed against it. Offsets are signed
# and are never clipped: under this origin the fine profile's earliest
# arrival precedes zero.
CLOCK = {"absolute_reference_coordinate_time_M": -978.6055123201214,
         "source": "artifacts/raymaps/a050_i050_n0_core.h5 metadata "
                   "t_reference",
         "rule": "delay_common = t_reference_absolute - coordinate_time",
         "per_profile_recentring": "forbidden",
         "negative_offsets": "recorded, never clipped to zero"}

SCREEN_FIELDS = ["1", "alpha/25", "beta/25", "(alpha/25)^2", "(beta/25)^2",
                 "alpha*beta/625"]
TRANSFERRED_FIELDS = ["g^3",
                      "g^3*cos(2*pi*(t_obs-delay)/20)",
                      "g^3*sin(2*pi*(t_obs-delay)/20)",
                      "g^3*cos(2*pi*(t_obs-delay)/40)",
                      "g^3*sin(2*pi*(t_obs-delay)/40)"]

TOLERANCES = {"fixed_detector_response_relative": 1.0e-3,
              "mask_symmetric_difference_relative": 1.0e-3,
              "corrected_area_relative": 1.0e-3,
              "exact_fixture_relative": 1.0e-12,
              "exact_fixture_absolute": 1.0e-12,
              "successive_late_refinement_pairs_required": 2,
              "applies_to": "every order and every declared field, not an "
                            "average",
              "adjustment_after_results": "forbidden"}

CODE = ["src/phrt/revision_v4_1/measure.py",
        "src/phrt/revision_v4_1/acquisition.py",
        "src/phrt/revision_v4_1/common_sky.py",
        "scripts/revision_v4_1/q0_measure_inventory.py",
        "scripts/revision_v4_1/q1_measure_specification.py",
        "scripts/revision_v4_1/q2_freeze.py",
        "scripts/revision_v4_1/q2_fixed_detector_convergence.py",
        "tests/revision_v4_1/test_c13_measure.py",
        "tests/revision_v4_1/test_r3a_construction.py",
        "artifacts/configs/R1_MAIN_FREEZE.json",
        "artifacts/revisions/mahakal_v4_1/R2_REPLAY_TARGET_MANIFEST.json"]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main(out: Path) -> int:
    files = list(CODE) + [f"artifacts/raymaps/{GEOMETRY}_n{n}_{p}.h5"
                          for p in PROFILES for n in ORDERS]
    missing = [f for f in files if not (ROOT / f).exists()]
    if missing:
        raise SystemExit(f"cannot freeze, files absent: {missing}")
    dirty = subprocess.run(["git", "status", "--porcelain", "--", *files],
                           cwd=ROOT, capture_output=True, text=True).stdout
    freeze = {
        "schema": "phrt-input-freeze/1", "id": "R3A_QC_026_INPUT_FREEZE",
        "ruling": "PAPER_I_R3A_RULING_026", "stage": "Q2",
        "written_before_any_q2_outcome_exists": True,
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "commit_at_freeze_time": subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True,
            text=True).stdout.strip(),
        "frozen_files_clean_in_git": dirty.strip() == "",
        "uncommitted_among_frozen_files": dirty.strip().splitlines(),
        "environment": {"python": "3.11.15", "numpy": "1.26.4",
                        "scipy": "1.11.4",
                        "pytest_interpreter": "system python3"},
        "geometry": {"id": GEOMETRY, "spin": 0.5, "inclination_deg": 50,
                     "orders": list(ORDERS), "new_geometries": "forbidden"},
        "profiles_compared": list(PROFILES),
        "detector_D026": {
            **DETECTOR, "sigma": SIGMA,
            "sigma_fixed_during_all_refinement": True,
            "snr_recalibration": "forbidden",
            "observer_times_M": OBSERVER_TIMES,
            "observer_times_source": "artifacts/configs/R1_MAIN_FREEZE.json "
                                     "observation.observer_times_M",
            "interpretation": "a newly declared ideal fixed aperture, not an "
                              "EHT forecast and not a replacement that makes "
                              "the archived 0.02 M design pass"},
        "clock": CLOCK,
        "measure": {
            "convention": "NODAL_DUAL_CLIPPED_TO_DECLARED_DOMAIN",
            "specified_in": "src/phrt/revision_v4_1/measure.py",
            "archives_rewritten": False},
        "field_suite": {"screen_fields": SCREEN_FIELDS,
                        "transferred_fields": TRANSFERRED_FIELDS,
                        "valid_mask_applied_to_every_field": True,
                        "all_orders_and_all_observer_times": True,
                        "target_modes_inspected": False},
        "metrics": {
            "response_error": "||W y_fine - W y_coarse|| / max(||W y_fine||, "
                              "floor)",
            "response_floor": "1e-12 * the same order's constant-field "
                              "response norm",
            "mask_error": "symmetric difference area / union area, from an "
                          "exact rectangle-set intersection",
            "area_error": "|A_fine - A_coarse| / max(A_fine, A_coarse)",
            "empty_mask_or_zero_signal": "reported explicitly, never divided "
                                         "into a floor"},
        "tolerances": TOLERANCES,
        "target": {
            "indices": "the accepted 72 columns, unchanged",
            "reselection": "forbidden",
            "target_spectra_operational_counts_estimators":
                "not computed in this stage",
            "only_permitted_target_operation": "the analytical uniform "
                                               "order-weight bound recorded "
                                               "in Q1"},
        "guards": ["input_hashes", "fixed_target_indices", "fixed_detector",
                   "fixed_sigma", "fresh_output_directory"],
        "outcome_labels": {
            "pass": "R3A_FIXED_DETECTOR_QUADRATURE_READY_FOR_REVIEW",
            "fail": "R3A_QUADRATURE_NOT_YET_QUALIFIED"},
        "stop_before_R3B": True,
        "n_files": len(files),
        "files": {f: sha(ROOT / f) for f in sorted(files)},
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(freeze, indent=2) + "\n")
    print(f"wrote {out}")
    print(f"  commit {freeze['commit_at_freeze_time'][:12]}, "
          f"{len(files)} files, clean={freeze['frozen_files_clean_in_git']}")
    if not freeze["frozen_files_clean_in_git"]:
        print("  NOTE: frozen files are not all committed yet; commit this "
              "freeze together with them before running Q2")
    return 0


if __name__ == "__main__":
    raise SystemExit(main((ROOT / sys.argv[1]).resolve()))
