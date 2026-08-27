#!/usr/bin/env python3
"""R1L_DETERMINISTIC_NUMERICS_AMENDMENT_009 -- record-only.

REVIEWER_RULING_R1L_REPRODUCIBILITY_009 items 1 to 4. Records the accepted
commits, preserves the standing disposition, states each canonical-status
repair and why it was needed, and declares the pinned numerical environment
before any pinned run is executed.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from phrt.attestation import attest
from phrt.config import load_registry, sha256_file
from phrt.numerics import PINNED_ENV

FREEZE = ROOT / "artifacts" / "configs" / "R1L_LOCALIZED_AUDIT_FREEZE.json"
OUT = ROOT / "artifacts" / "configs" / "R1L_DETERMINISTIC_NUMERICS_AMENDMENT_009.json"


def main() -> int:
    reg = load_registry()
    probe = subprocess.run(
        [sys.executable, "-c",
         "import sys; sys.path.insert(0, 'src');"
         "from phrt.numerics import pin; pin(); import numpy;"
         "from phrt.numerics import record; import json; print(json.dumps(record()))"],
        cwd=ROOT, capture_output=True, text=True)
    pinned_probe = (json.loads(probe.stdout) if probe.returncode == 0
                    else {"error": probe.stderr.strip()[-400:]})

    doc = {
        "schema": "phrt-record-amendment/1",
        "id": "R1L_DETERMINISTIC_NUMERICS_AMENDMENT_009",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "ruling": "REVIEWER_RULING_R1L_REPRODUCIBILITY_009",
        "kind": "RECORD_ONLY_PLUS_ENVIRONMENT_DECLARATION",
        "recomputation": "none by this amendment. It declares the environment "
                         "the pinned runs must execute under and repairs "
                         "canonical status text; the runs themselves follow",

        "accepted_and_preserved_commits": [
            "e536443f9fd975665f277f70fdb687e04b1d2bdc",
            "0ae6b80a08b0ecf8e337e73070d10f2b9146198b",
            "7cef3b0d1e1732356afeb3e8abda5114c18ada03",
        ],
        "preserved_disposition": "R1L_STAGE1_REPRODUCTION_DISCREPANCY_STOP",

        # ------------------------------------------------------------ item 3
        "canonical_status_repairs": {
            "a_stale_unlock_token": {
                "defect": "the stage-1 report's closing section still carried "
                          "R1L_STAGE_1_PASS_VALIDATION_PILOT_UNLOCKED while the "
                          "run that produced its numbers was under a "
                          "reproduction STOP. A reader taking the closing token "
                          "as the status would have read the stage as unlocked",
                "repair": "the canonical stage-1 status is now the deterministic "
                          "reproduction disposition whenever that disposition is "
                          "not PASS. The audit's own finding is reported beside "
                          "it as R1L_STAGE_1_AUDIT_FINDINGS_COMPLETE, explicitly "
                          "labelled as a statement about the operator with no "
                          "standing to unlock a stage",
                "principle": "an audit whose numbers are not yet reproducible "
                             "cannot authorize the next stage on the strength of "
                             "its own findings",
            },
            "b_artifact_manifest_stop_token": {
                "defect": "R1L_STAGE1_ARTIFACT_MANIFEST.json recorded the same "
                          "stale unlock token as its stop_token",
                "repair": "stop_token now carries the canonical status, and the "
                          "manifest additionally names canonical_stage1_status, "
                          "audit_finding, deterministic_reproduction and "
                          "blocking_gate as separate fields so the three cannot "
                          "be conflated again",
            },
            "c_gate_dashboard": {
                "repair": "rebuilt after the blocking gate was added",
                "active_blocking_failures_after_rebuild": 1,
                "named": ["R1L_G12_deterministic_reproduction"],
            },
            "d_blocking_gate": {
                "added": "R1L_G12_deterministic_reproduction",
                "initial_status": "FAIL",
                "why_fail_before_computation": "deterministic reproduction is "
                                               "unproven until the pinned pair "
                                               "runs, and an unproven gate that "
                                               "defaults to pass is the failure "
                                               "mode this campaign has already "
                                               "been caught by",
                "also_added": "R1L_G11_pinned_numerical_environment, an in-run "
                              "gate that interrogates the loaded thread pools "
                              "rather than reading back the environment",
            },
            "e_full_rank_phrase": {
                "was": "C224's direct arm reported full column rank it did not "
                       "have",
                "defect": "the phrase says the reported rank was wrong. It was "
                          "not. C224's direct arm has exactly the rank it "
                          "reports; the rank is a true statement about the 224 "
                          "global coefficients. The error was mine in inferring "
                          "an epoch-local claim from it, and the corrected "
                          "wording in ruling 008 item 3a fixed the inference "
                          "while this phrase survived elsewhere and still "
                          "impugned the number",
                "now": "C224's direct arm has the full column rank it reports, "
                       "and that number is correct. What it does not carry is "
                       "any claim about epoch-local identifiability, on which "
                       "C224 is silent",
            },
        },

        # ---------------------------------------------------------- items 5-7
        "pinned_numerical_environment": {
            "variables": PINNED_ENV,
            "when": "set before Python imports NumPy. Thread-pool sizes are read "
                    "once when the threading runtime initialises behind the "
                    "first numeric import, so a pin applied after that is "
                    "decoration",
            "enforcement": "phrt.numerics.pin() raises if any numeric module is "
                           "already in sys.modules rather than silently "
                           "no-opping, because a pin that appears to succeed and "
                           "did not is worse than no pin",
            "assertion": "phrt.numerics.require_single_threaded() interrogates "
                         "the runtime that actually loaded and aborts unless "
                         "every pool reports one thread. An empty pool list is "
                         "also an abort: NumPy here always loads OpenBLAS, so "
                         "finding no pool means the interrogation failed",
            "measured_under_the_pin": pinned_probe,
            "measured_without_the_pin": "threadpool_info reports 4 OpenBLAS "
                                        "threads on this machine",
            "dependency_added": "threadpoolctl 3.6.0, so the pool state can be "
                                "measured rather than asserted. This changes the "
                                "environment digest and is declared here rather "
                                "than discovered in a later diff",
            "registry_sha256": reg.sha256,
        },
        "run_isolation": {
            "rule": "every run writes to artifacts/runs/<run_id>/, and the "
                    "canonical artifacts/tables and gate files are written only "
                    "by an explicit --promote on a full six-class run",
            "partial_runs_refused": "--promote raises if fewer than six classes "
                                    "are selected",
            "why_structural": "three L224-only diagnostic invocations previously "
                              "overwrote full-ladder tables, CSVs and the gate "
                              "file. A convention would not have prevented that; "
                              "a separate output path does",
        },
        "preserved_runs_for_comparison": json.loads(
            (ROOT / "artifacts" / "preserved" / "PRESERVED_RUNS.json").read_text()),

        "instructions_discharged": [
            "1 accept and preserve the three commits",
            "2 preserve R1L_STAGE1_REPRODUCTION_DISCREPANCY_STOP",
            "3a remove the stale PASS/UNLOCKED token from the report",
            "3b replace the artifact-manifest stop token",
            "3c rebuild the gate dashboard",
            "3d add a blocking deterministic-reproduction gate",
            "3e replace the remaining full-rank phrase",
            "4 commit this amendment",
            "5 pin the numerical environment before NumPy is imported",
            "6 record and assert effective BLAS thread-pool state",
            "7 isolate every run under a run-specific output directory",
        ],
        "not_yet_done_at_the_time_of_this_amendment": [
            "8 two complete six-class pinned runs",
            "9 exact equality between them",
            "10 comparison against every preserved run",
            "11 or 12 the resulting disposition",
        ],
        "provenance": {"freeze_sha256": sha256_file(FREEZE)},
    }
    doc["attestation"] = attest([FREEZE])
    OUT.write_text(json.dumps(doc, indent=2) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}")
    print(f"  sha256 {sha256_file(OUT)}")
    print(f"  pinned probe pools: "
          f"{[p.get('num_threads') for p in pinned_probe.get('threadpool_state', [])]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
