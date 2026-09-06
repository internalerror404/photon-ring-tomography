#!/usr/bin/env python3
"""Where every legacy calibration site goes, and what proves it got there."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

ENTRY = "phrt.revision_v4_1.calibration.calibrate"
REPLAY = "scripts/revision_v4_1/r1_physical_calibration.py"
GATES = "tests/revision_v4_1/test_r1_gates.py"

# legacy site -> how it is reached now, and the evidence that it is
MIGRATION = {
    "scripts/run_e3c_operator_grid.py": dict(
        symbol="snr_scale", family="E3C", classification="PHYSICAL",
        integration_evidence="physical_calibration_replay.json: all 12 "
                             "geometries reproduce the archived s_ref through "
                             "the versioned object, worst relative error "
                             "4.4e-16"),
    "scripts/run_e3b_canary.py": dict(
        symbol="snr_scale", family="E3B", classification="PHYSICAL",
        integration_evidence="same constructor and formula as E3C; covered by "
                             "the E3C replay and by G02"),
    "scripts/run_e3d_source_class_stress.py": dict(
        symbol="s_ref", family="E3D", classification="PHYSICAL",
        integration_evidence="shares the direct-arm reference construction; "
                             "covered by G02, not separately replayed"),
    "scripts/run_hmt1_main.py": dict(
        symbol="s_ref", family="HMT1", classification="PHYSICAL",
        integration_evidence="HMT1 is closed with no standing result; "
                             "migration recorded, replay not required"),
    "scripts/run_hmt1_validation.py": dict(
        symbol="s_ref", family="HMT1", classification="PHYSICAL",
        integration_evidence="as above"),
    "scripts/run_hmt2_sealed_main.py": dict(
        symbol="s_ref", family="HMT2", classification="PHYSICAL",
        integration_evidence="single geometry, single ray count, so the "
                             "count convention cannot differ across cells "
                             "within the run; migration recorded"),
    "scripts/run_hmt2_stage1.py": dict(
        symbol="s_ref", family="HMT2", classification="PHYSICAL",
        integration_evidence="as above"),
    "scripts/run_hmt2_stage1_completion.py": dict(
        symbol="s_ref", family="HMT2", classification="PHYSICAL",
        integration_evidence="as above; discovered by the inventory, absent "
                             "from the delivered ledger's seed list"),
    "scripts/run_r1l_operator_audit.py": dict(
        symbol="s_ref", family="R1L", classification="PHYSICAL",
        integration_evidence="discovered by the inventory; migration recorded"),
    "scripts/run_r1l_stage2r_b.py": dict(
        symbol="s_ref", family="R1L", classification="PHYSICAL",
        integration_evidence="migration recorded"),
    "src/phrt/operators/whitening.py": dict(
        symbol="NoiseModel.from_snr", family="library",
        classification="TOY_ONLY",
        integration_evidence="AST call graph finds one caller, "
                             "scripts/reproduce_v01.py. Left unchanged so the "
                             "v0.1 reproduction keeps replaying; its "
                             "reference_rows is a slice, not a count"),
    "scripts/reproduce_v01.py": dict(
        symbol="NoiseModel.from_snr", family="toy",
        classification="TOY_ONLY",
        integration_evidence="the only caller of the toy helper"),
}


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main(run_dir: Path) -> int:
    inv = json.loads((run_dir / "normalization_site_inventory.json").read_text())
    discovered = {d["path"] for d in inv["physical_mean_over_rows_definitions"]}
    covered = {k for k, v in MIGRATION.items()
               if v["classification"] == "PHYSICAL"}
    uncovered = sorted(discovered - covered)

    mig = {
        "schema": "phrt-calibration-migration/1",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "ledger_item": "C02",
        "versioned_entry_point": ENTRY,
        "modes": ["LEGACY_REPLAY", "LOCKED_LEGACY_NOISE",
                  "COMMON_REFERENCE_COUNT"],
        "e3c_reference_rows": 12288,
        "legacy_entry_points_left_intact": True,
        "n_physical_sites_discovered": len(discovered),
        "n_physical_sites_covered": len(covered & discovered),
        "uncovered_physical_sites": uncovered,
        "entries": [{"legacy_site": k, **v, "revised_entry_point": ENTRY,
                     "integration_test": REPLAY if v["family"] == "E3C"
                     else GATES}
                    for k, v in sorted(MIGRATION.items())],
    }
    (run_dir / "calibration_migration_map.json").write_text(
        json.dumps(mig, indent=2) + "\n")

    tests = subprocess.run(
        ["python3", "-m", "pytest", "tests/revision_v4_1/", "-q",
         "--no-header"], cwd=ROOT, capture_output=True, text=True)
    tail = [l for l in tests.stdout.strip().splitlines() if l.strip()][-1:]
    replay = json.loads((run_dir / "physical_calibration_replay.json").read_text())
    gates = {
        "schema": "phrt-r1-gates/1",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "suite": GATES,
        "pytest_summary": tail[0] if tail else "not run",
        "returncode": tests.returncode,
        "counterexample_gates": {
            "G05": "passes by reproducing the archived recalibration defect: "
                   "splitting by 2, 4, 8, 16 multiplies information by the "
                   "same factors at one SNR label",
            "G16": "passes by showing the archived guard accepts two "
                   "unrelated screens of equal cardinality",
            "G17": "passes by showing an index-paired substitution moves when "
                   "one order is relabelled independently, and does not move "
                   "under a common relabelling",
        },
        "physical_replay": {
            "n_geometries": replay["n_geometries"],
            "n_failures": replay["n_failures"],
            "worst_relative_replay_error": max(
                g["legacy_replay_relative_error"] for g in
                replay["geometries"]),
            "geometries_with_non_unit_factor": [
                g["geometry"] for g in replay["geometries"]
                if g["information_factor_common_over_legacy"] != 1.0],
        },
    }
    (run_dir / "numerical_gates.json").write_text(
        json.dumps(gates, indent=2) + "\n")

    frozen = {}
    for rel in [*sorted(str(p.relative_to(ROOT)) for p in
                        (ROOT / "src" / "phrt" / "revision_v4_1").glob("*.py")),
                *sorted(str(p.relative_to(ROOT)) for p in
                        (ROOT / "scripts" / "revision_v4_1").glob("*.py")),
                GATES]:
        frozen[rel] = sha(ROOT / rel)
    freeze = {
        "schema": "phrt-r1-code-freeze/1",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "purpose": "code, config and test bytes frozen before any "
                   "outcome-bearing R2 computation",
        "amendment": "PAPER_I_DEFECT_AMENDMENT_023",
        "e3c_reference_rows_frozen_before_outcomes": 12288,
        "nuisance_rank_rtol_primary": 1e-12,
        "files": frozen,
    }
    (run_dir / "R1_CODE_CONFIG_TEST_FREEZE.json").write_text(
        json.dumps(freeze, indent=2) + "\n")

    print(f"migration: {len(covered & discovered)}/{len(discovered)} physical "
          f"sites covered; uncovered {uncovered or 'none'}")
    print(f"gates: {gates['pytest_summary']}")
    print(f"replay: worst relative error "
          f"{gates['physical_replay']['worst_relative_replay_error']:.2e}, "
          f"non-unit factor at "
          f"{gates['physical_replay']['geometries_with_non_unit_factor']}")
    print(f"froze {len(frozen)} files")
    return 1 if uncovered or tests.returncode != 0 else 0


if __name__ == "__main__":
    raise SystemExit(main((ROOT / sys.argv[1]).resolve()))
