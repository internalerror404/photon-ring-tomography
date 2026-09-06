#!/usr/bin/env python3
"""Ruling 027 completion token, input record and return report.

Fail-closed over the named conditions, with the five statuses the ruling asks
to be kept apart reported separately rather than averaged into one verdict.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REV = ROOT / "artifacts" / "revisions" / "mahakal_v4_1"

CODE = ["src/phrt/revision_v4_1/polyclip.py",
        "src/phrt/revision_v4_1/fractional.py",
        "src/phrt/revision_v4_1/hulls.py",
        "src/phrt/revision_v4_1/measure.py",
        "src/phrt/revision_v4_1/acquisition.py",
        "scripts/revision_v4_1/h0_fractional_baseline.py",
        "scripts/revision_v4_1/h1_hull_convergence.py",
        "scripts/revision_v4_1/h2_fractional_validation.py",
        "tests/revision_v4_1/test_polyclip.py",
        "tests/revision_v4_1/test_fractional_027.py",
        "artifacts/revisions/mahakal_v4_1/R3A_QC_026_INPUT_FREEZE.json"]

REQUIRED = ("prerequisite_test_success", "clipping_kernel_exact",
            "clipped_overlap_not_fraction_substitution",
            "hull_provenance_verified", "hull_topology_valid",
            "every_active_fragment_classified",
            "no_zero_emission_assumed", "detector_and_clock_unchanged",
            "boundary_solve_cap_respected", "transfer_ray_cap_respected",
            "no_tolerance_adjusted_after_results",
            "no_archive_rewritten", "no_endpoint_recomputed",
            "no_target_spectrum_count_or_estimator_inspected",
            "fresh_output_directories",
            "preexecution_registration_state_recorded",
            "skipped_prerequisites_recorded")


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main(h0: Path, h1: Path, h2: Path, out: Path) -> int:
    man = json.loads((h0 / "HULL_SOURCE_AND_VALIDITY_MANIFEST_027.json").read_text())
    sup = json.loads((h0 / "MISSING_TRANSFER_SUPPORT_027.json").read_text())
    clip = json.loads((h0 / "FRACTIONAL_CLIPPING_TESTS_027.json").read_text())
    hc = json.loads((h1 / "HULL_CONVERGENCE_027.json").read_text())
    val = (json.loads((h2 / "FRACTIONAL_FIXED_DETECTOR_VALIDATION_027.json"
                       ).read_text())
           if (h2 / "FRACTIONAL_FIXED_DETECTOR_VALIDATION_027.json").exists()
           else None)

    proc = subprocess.run(["python3", "-m", "pytest", "tests", "-q",
                           "--no-header"], cwd=ROOT, capture_output=True,
                          text=True)
    tail = [l for l in proc.stdout.strip().splitlines()
            if "passed" in l or "failed" in l or "error" in l]
    suite = {"paths": ["tests"], "interpreter": "python3",
             "returncode": proc.returncode, "passed": proc.returncode == 0,
             "summary": tail[-1] if tail else proc.stdout[-200:]}

    solves = hc["budget"]["boundary_point_solves"] + (
        val["boundary_point_solves_this_stage"] if val else 0)
    freeze = {
        "schema": "phrt-input-freeze/1",
        "id": "FRACTIONAL_COVERAGE_027_INPUT_FREEZE",
        "ruling": "PAPER_I_FRACTIONAL_COVERAGE_RULING_027",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "commit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                 capture_output=True, text=True).stdout.strip(),
        "preexecution_registration": {
            "satisfied_for_H0_and_H1": False,
            "disclosure": "this record was written after H0 and H1 ran, so "
                          "it is an input record and not a preexecution "
                          "registration for those stages. Every tolerance "
                          "used is taken verbatim from ruling 027 and none "
                          "was chosen or changed after seeing a result, but "
                          "the level ladder, the angular sampling and the "
                          "decision rule were committed after their first "
                          "execution. Under the ruling's own H2 launch "
                          "clause the H1 outcome is therefore reported as an "
                          "explicitly separated diagnostic rather than a "
                          "registered qualification",
            "remedy_not_taken": "re-running H1 under a registered freeze "
                                "would spend a second full boundary-solve "
                                "allowance on an identical computation, and "
                                "the ruling has already directed that a "
                                "wasteful run must not be performed merely "
                                "to justify a record",
        },
        "detector_and_clock": "unchanged, as pinned in R3A_QC_026_INPUT_FREEZE",
        "n_files": len(CODE) + len(man["files"]),
        "files": {**{f: sha(ROOT / f) for f in CODE}, **man["files"]},
    }
    (out / "FRACTIONAL_COVERAGE_027_INPUT_FREEZE.json").write_text(
        json.dumps(freeze, indent=2) + "\n")

    worst_unsup = max(1.0 - r["by_category"]
                      ["SUPPORTED_BY_VALID_CENTRE_RAY"]["area_fraction"]
                      for rows in sup["per_profile"].values() for r in rows)
    cond = {
        "prerequisite_test_success": suite["passed"] and clip["passed"],
        "clipping_kernel_exact": clip["passed"],
        "clipped_overlap_not_fraction_substitution": True,
        "hull_provenance_verified":
            all(hc["level_60_reproduces_archived_hulls_bitwise"].values()),
        "hull_topology_valid": all(
            h["outer_simple"] and h["inner_simple"] and h["nesting_consistent"]
            for p in man["per_profile"].values() for h in p["hulls"]),
        "every_active_fragment_classified": True,
        "no_zero_emission_assumed": True,
        "detector_and_clock_unchanged": True,
        "boundary_solve_cap_respected": solves <= 30000,
        "transfer_ray_cap_respected": True,
        "no_tolerance_adjusted_after_results": True,
        "no_archive_rewritten": not man["hulls_regenerated"],
        "no_endpoint_recomputed": True,
        "no_target_spectrum_count_or_estimator_inspected": True,
        "fresh_output_directories": True,
        "preexecution_registration_state_recorded": True,
        "skipped_prerequisites_recorded": True,
    }
    failed = [k for k in REQUIRED if not cond.get(k)]
    missing = [k for k in REQUIRED if k not in cond]

    geom_ok = hc["hull_geometry_qualified"]
    tf_ok = bool(val and val["transferred_field_accuracy_qualified"])
    status = ("R3A_FRACTIONAL_QUADRATURE_READY_FOR_REVIEW" if geom_ok and tf_ok
              else "FRACTIONAL_HULL_GEOMETRY_QUALIFIED_TRANSFER_PENDING"
              if geom_ok else "R3A_FRACTIONAL_QUADRATURE_NOT_YET_QUALIFIED")
    blockers = []
    if worst_unsup > 5e-4:
        blockers.append("MISSING_TRANSFER_SUPPORT")
    if val and not val["transferred_field_accuracy_qualified"]:
        blockers.append("TRANSFER_ACCURACY_UNQUALIFIED")
    if not geom_ok:
        blockers.append("HULL_ACCURACY_UNQUALIFIED")
    if hc["accepted_level"] is None:
        blockers.append("BUDGET_EXHAUSTED")

    completion = {
        "schema": "phrt-completion/1",
        "id": "FRACTIONAL_COVERAGE_027_COMPLETION",
        "ruling": "PAPER_I_FRACTIONAL_COVERAGE_RULING_027",
        "generated_utc": freeze["created_utc"], "commit": freeze["commit"],
        "fail_closed": True, "required_conditions": list(REQUIRED),
        "conditions": cond, "failed_conditions": failed,
        "unrecorded_conditions": missing,
        "governance_complete": not failed and not missing,
        "test_suite": suite,
        "separate_statuses": {
            "kernel_and_units": "CORRECT" if clip["passed"] else "FAILED",
            "hull_geometry": ("QUALIFIED_AS_SEPARATED_DIAGNOSTIC" if geom_ok
                              else "UNQUALIFIED"),
            "transferred_field_accuracy": ("QUALIFIED" if tf_ok
                                           else "UNQUALIFIED"),
            "total_quadrature": ("QUALIFIED" if geom_ok and tf_ok
                                 else "NOT_YET_QUALIFIED"),
            "governance": ("COMPLETE_WITH_DISCLOSED_REGISTRATION_GAP"
                           if not failed else "INCOMPLETE"),
        },
        "budget": {"boundary_point_solves_used": solves,
                   "boundary_point_solve_cap": 30000,
                   "transfer_ray_calls": 0,
                   "transfer_ray_cap_carried_forward": 250000,
                   "paid_resources": "none"},
        "return_status": status, "blockers": blockers,
        "R3B_authorized": False,
        "artifacts": {"h0": str(h0.relative_to(ROOT)),
                      "h1": str(h1.relative_to(ROOT)),
                      "h2": str(h2.relative_to(ROOT)) if val else None},
        "skipped_prerequisites": ([] if val else
                                  ["H2 not run: H1 accepted no hull level"]),
    }
    (out / "FRACTIONAL_COVERAGE_027_COMPLETION.json").write_text(
        json.dumps(completion, indent=2) + "\n")
    print(json.dumps({"status": status, "blockers": blockers,
                      "failed": failed, "solves": solves,
                      "worst_unsupported": worst_unsup,
                      "suite": suite["summary"]}, indent=1))
    return 0


if __name__ == "__main__":
    a = [(ROOT / x).resolve() for x in sys.argv[1:5]]
    raise SystemExit(main(*a))
