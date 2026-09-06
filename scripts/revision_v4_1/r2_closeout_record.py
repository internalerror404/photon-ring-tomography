#!/usr/bin/env python3
"""The nine record corrections review 024 requires, and the coverage recut.

Nothing here is backdated. The original run directory keeps its bytes and its
token; this states what that token did and did not rest on.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ORIGINAL = "R0_20260906T070540Z_38e1f8a"

# Reviewer's evidence ladder, weakest to strongest.
INVENTORIED = "INVENTORIED"
ALGEBRAIC = "ALGEBRAICALLY_EQUIVALENT"
REPLAYED = "PHYSICAL_REFERENCE_REPLAYED"
INTEGRATED = "PRODUCTION_INTEGRATION_TESTED"
DEFERRED = "DEFERRED_OR_RETIRED"

COVERAGE = {
    "scripts/run_e3c_operator_grid.py": (
        INTEGRATED,
        "scripts/revision_v4_1/r1_physical_calibration.py rebuilds this "
        "runner's DIRECT_PHYSICAL operator from the frozen maps and the "
        "registered sampler seed and calibrates it through "
        "phrt.revision_v4_1.calibration; 12 geometries reproduce the archived "
        "s_ref, worst relative error 4.4e-16. Also PHYSICAL_REFERENCE_REPLAYED"),
    "scripts/run_e3b_canary.py": (
        ALGEBRAIC, "identical snr_scale formula and construction to E3C; "
                   "traced, not executed"),
    "scripts/run_e3d_source_class_stress.py": (
        ALGEBRAIC, "same direct-arm reference construction; traced, not "
                   "executed"),
    "scripts/run_hmt2_sealed_main.py": (
        ALGEBRAIC, "same formula on a single geometry and a single ray count, "
                   "so no cross-geometry count artefact is possible within "
                   "the run; traced, not executed"),
    "scripts/run_hmt2_stage1.py": (ALGEBRAIC, "as above"),
    "scripts/run_hmt2_stage1_completion.py": (
        ALGEBRAIC, "as above; discovered by the inventory, absent from the "
                   "delivered ledger's seed list"),
    "scripts/run_r1l_operator_audit.py": (
        ALGEBRAIC, "discovered by the inventory; traced, not executed"),
    "scripts/run_r1l_stage2r_b.py": (ALGEBRAIC, "traced, not executed"),
    "scripts/run_hmt1_main.py": (
        DEFERRED, "HMT-1 is closed with no standing result "
                  "(HMT1_CLOSURE_RECORD_018); no replay or integration claim"),
    "scripts/run_hmt1_validation.py": (DEFERRED, "as above"),
    "src/phrt/operators/whitening.py": (
        DEFERRED, "NoiseModel.from_snr is toy-only, single caller "
                  "reproduce_v01; left unchanged so the v0.1 reproduction "
                  "keeps replaying"),
    "scripts/reproduce_v01.py": (DEFERRED, "the toy caller"),
}


def git(*a: str) -> str:
    return subprocess.run(["git", *a], cwd=ROOT, capture_output=True,
                          text=True).stdout.strip()


def main() -> int:
    out = ROOT / "artifacts" / "revisions" / "mahakal_v4_1" / ORIGINAL
    orig_disp = json.loads((out / "correction_dispositions.json").read_text())
    levels: dict[str, int] = {}
    for lvl, _ in COVERAGE.values():
        levels[lvl] = levels.get(lvl, 0) + 1
    physical = {k: v for k, v in COVERAGE.items()
                if v[0] not in (DEFERRED,)}

    doc = {
        "schema": "phrt-record-amendment/1",
        "id": "R2_CLOSEOUT_RECORD_024",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "review": "PAPER_I_R0_R2_REVIEW_024",
        "reviewed_commit": "d15debbeefcaab31d56e2977805168d2782bd28b",
        "kind": "RECORD_AND_REPLAY_MANDATE",
        "preserves": "the original run directory, its bytes, and its token",
        "backdating": "none. The original execution is described as it was",

        "phase_provenance_corrected": {
            "R0_starting_commit": "38e1f8a758e68d0bb272085bc826152d53996931",
            "R0_execution_commit": "38e1f8a (provenance.json records this and "
                                   "is explicitly an R0 record)",
            "R1_execution_commit": "702fa36, the commit that carried the R0 "
                                   "outputs; the R1 code was written and run "
                                   "after it and committed as 9e80b65",
            "R2_execution_commit": "9e80b65 was HEAD while R2 ran; the R2 "
                                   "runner, manifest and results were first "
                                   "committed together as d15debb",
            "defect": "one provenance.json, written at R0, was allowed to "
                      "stand for all three phases. Phase-specific execution "
                      "identities were never recorded",
        },
        "freeze_gap_recorded": {
            "R1_CODE_CONFIG_TEST_FREEZE_omitted": [
                "scripts/revision_v4_1/r2_conditional_information.py",
                "the R2 target manifest"],
            "verified_by": "the freeze lists 13 files, none matching r2_*; "
                           "git log --diff-filter=A shows d15debb is the "
                           "first commit adding the R2 runner",
            "consequence": "the R2 result was computed from a runner that had "
                           "not been committed beforehand. The manifest was "
                           "written before the spectra within the process, "
                           "which is a real sequencing property and is not "
                           "the committed pre-execution snapshot the handoff "
                           "requires",
            "repair": "one clean replay from a complete committed input "
                      "freeze. Not a new campaign: the calculation is "
                      "deterministic with no truths and no estimator",
        },
        "coverage_corrected": {
            "claim_withdrawn": "10/10 physical sites covered",
            "what_that_number_was": "inventory coverage. G06 checks that the "
                                    "discovered site names appear in the "
                                    "migration map; it executes none of them. "
                                    "G02 is an algebra fixture",
            "evidence_levels": {k: {"level": v[0], "evidence": v[1]}
                                for k, v in sorted(COVERAGE.items())},
            "counts": levels,
            "physical_sites_integration_tested": sum(
                1 for v in COVERAGE.values() if v[0] == INTEGRATED),
            "physical_sites_total": len(physical),
            "rule": "a deferred or retired path is not counted as a test pass",
        },
        "terminology_corrected": {
            "information_totals": "normalized Fisher trace, tr F, in the "
                                  "declared source norm at the stated sigma. "
                                  "Not bits, not a fraction of a history",
            "0.651": "tr F_conditional / tr F_known = 0.6512158. A ratio of "
                     "normalized Fisher traces and nothing else",
            "two_operational_directions": "two linear combinations of source "
                                          "functions clearing rho = 1 under "
                                          "the declared norm and threshold. "
                                          "Not two frames, events or hotspots",
            "rank": "numerical rank and operational fraction are different "
                    "quantities and are never summarized by one phrase. "
                    "Absolute resolved numerical rank rises 224, 448, 528, "
                    "1045; the operational fraction falls 0.897 to 0.729",
            "PAIRING_DESTROYED": "a nonphysical permutation control that the "
                                 "manuscript makes quantitative claims about, "
                                 "including retained old-age sensitivity. Its "
                                 "corrected diagnostics stay in the amendment "
                                 "trail. The earlier phrase 'carries no "
                                 "claim' is withdrawn",
            "unknown_background": "already inside this operator calculation "
                                  "as part of the full L224 nuisance model. "
                                  "What is unperformed is the "
                                  "unknown-background RECONSTRUCTION "
                                  "companion, not all treatment of background "
                                  "uncertainty. The earlier wording conflated "
                                  "the two",
        },
        "completion_status_corrected": {
            "defect": "the R2 runner detected tolerance instability and "
                      "returned 0 anyway; the report generator chose its "
                      "token from operational-count agreement alone, so the "
                      "same favourable token could have been issued for "
                      "conditions the protocol says must stop execution",
            "repair": "phrt.revision_v4_1.completion computes the token from "
                      "the seven declared conditions and fails closed on an "
                      "unrecorded one; phrt.revision_v4_1.guards refuses to "
                      "start on a violated input freeze, a drifted target "
                      "column set or an existing output directory",
            "tests": "tests/revision_v4_1/test_closeout_gates.py injects all "
                     "seven failures and requires a non-success token",
        },
        "fixture_tolerances_restored": {
            "G11": "1e-9 -> 1e-10, the protocol's "
                   "well_conditioned_fixture_relative_tolerance",
            "G14": "1e-9 -> 1e-10",
            "G09_G10": "trace-only checks replaced by the full Fisher matrix: "
                       "invariance is now measured entrywise and contraction "
                       "is checked in the Loewner order, so no direction may "
                       "gain information",
            "measured_residuals": "reported in the assertion messages rather "
                                  "than hidden behind a relaxed bound",
        },
        "original_disposition_status": {
            "token_issued": "R0_R2_COMPLETE_REFERENCE_GEOMETRY",
            "review_disposition":
                "SCIENTIFIC_CANDIDATE_SUPPORTED_CLOSEOUT_REPLAY_REQUIRED",
            "preserved": True,
            "note": "the token stands in the record as what was issued, with "
                    "this amendment attached. It is not edited",
        },
        "accepted_from_the_original_run": orig_disp[
            "corrections_to_the_delivered_ledger"],
    }
    p = out.parent / "R2_CLOSEOUT_RECORD_024.json"
    p.write_text(json.dumps(doc, indent=2) + "\n")
    print(f"wrote {p.relative_to(ROOT)}")
    print(f"  coverage: {doc['coverage_corrected']['counts']}")
    print(f"  integration-tested physical sites: "
          f"{doc['coverage_corrected']['physical_sites_integration_tested']}"
          f"/{doc['coverage_corrected']['physical_sites_total']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
