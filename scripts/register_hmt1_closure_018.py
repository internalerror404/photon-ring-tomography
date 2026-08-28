#!/usr/bin/env python3
"""HMT1_CLOSURE_RECORD_018. Items 1 to 5 of REVIEWER_RULING_HMT1_SOURCE_RESOLUTION_018.

Record only. Closes HMT-1 and fixes the scope of what its validation established.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from phrt.numerics import pin

pin()

from phrt.attestation import attest  # noqa: E402
from phrt.config import sha256_file  # noqa: E402

FZ2 = ROOT / "artifacts" / "configs" / "HMT1_SEALED_HELD_OUT_MAIN_FREEZE_V2.json"
COR = ROOT / "artifacts" / "configs" / "HMT1_SEALED_MAIN_CORRECTION_AND_RETIREMENT_017.json"
VAL = ROOT / "artifacts" / "configs" / "HMT1_VALIDATION_RECORD_AMENDMENT_015.json"
SA = ROOT / "artifacts" / "gates" / "hmt1_main_stage_a_gates.json"
OUT = ROOT / "artifacts" / "configs" / "HMT1_CLOSURE_RECORD_018.json"


def main() -> int:
    sa = json.loads(SA.read_text())
    doc = {
        "schema": "phrt-record-amendment/1",
        "id": "HMT1_CLOSURE_RECORD_018",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "ruling": "REVIEWER_RULING_HMT1_SOURCE_RESOLUTION_018",
        "kind": "RECORD_ONLY",
        "recomputation": "none",
        "accepted_commit": "f3525590c578ed8c6373161b379c462d79c16af6",

        "dispositions": {
            "HMT1_MAIN_STAGE_A_FIREWALL_PASS": {
                "finding": "the two-stage split held. Stage A decided every "
                           "source-side gate from the source alone, one failed, "
                           "and stage B refused to import an operator. No "
                           "held-out truth was evaluated and no "
                           "endpoint-derived quantity was computed under any "
                           "filename",
                "contrast_with_the_previous_attempt": "the same class of "
                                                      "problem was found only "
                                                      "after the operator had "
                                                      "run, which is what spent "
                                                      "that bank",
            },
            "HMT1_MAIN_SOURCE_RESOLUTION_CONTRACT_FAILURE": {
                "finding": "the declared two_hotspot_trajectories range admits "
                           "configurations the declared evaluation grid cannot "
                           "resolve. One truth of 96 placed both spots 0.34 "
                           "log-radial cells apart with radial widths of 0.23 "
                           "and 0.32 cells, at a radius where one cell is "
                           "about 10 M and the blob widths are 2 to 3 M",
                "reading": "not an extractor defect and not a reference "
                           "defect. The source model and the evaluation grid "
                           "were specified independently and their contract "
                           "was never checked. That is the thing HMT-2 stage 0 "
                           "exists to establish",
            },
            "HMT1_MAIN_SCIENCE_NOT_RUN": {
                "finding": "no sealed held-out scientific result exists for "
                           "HMT-1. Two banks were retired before evaluation "
                           "and the third was refused at stage A",
                "reading": "the held-out claim was never made, rather than "
                           "made and withdrawn",
            },
            "HMT1_MAIN_NO_FURTHER_SEALED_BANK": {
                "finding": "HMT-1 draws no further bank",
                "reading": "drawing again under the same source-grid contract "
                           "would reproduce the same failure with a different "
                           "index",
            },
        },

        "canary": {
            "bank_seed": 20260921,
            "token": "HMT1_SOURCE_RESOLUTION_FAILURE_CANARY",
            "failing_truth": "two_hotspot_trajectories index 5",
            "measured_g10c_cells": {"radial": 0.475235, "azimuthal": 2.576218},
            "geometry": "spots at r = 46.44 and 43.01 M, separation 0.34 "
                        "log-radial cells, sigma_r 0.23 and 0.32 cells on the "
                        "16-point log-radial grid",
            "permitted_use": "regression test only",
            "forbidden_use": "held-out evidence, and any aggregate success "
                             "statistic",
            "stage_a_gates": sa["gates"],
        },

        "validation_scope_amendment": {
            "applies_to": "HMT1_VALIDATION_RECORD_AMENDMENT_015 and the "
                          "validation result it records",
            "scope": "DOMINANT_OR_BLENDED_FEATURE_DESCRIPTOR",
            "not": "TWO_INDEPENDENT_TRAJECTORY_RECOVERY",
            "reason": "the validation endpoint read a single peak position per "
                      "age. For a family with more than one feature that "
                      "quantity describes whichever feature dominates, or the "
                      "blend of them when the grid cannot separate them. It "
                      "was never a measurement of two independent "
                      "trajectories, and the material reduction the validation "
                      "reported must be read at that scope",
            "unchanged": "the validation's numbers, gates, controls and "
                         "deterministic pair stand as recorded. This narrows "
                         "what they mean, not what they are",
        },

        "closed": {
            "study": "HMT-1",
            "further_banks": "none",
            "successor": "HMT-2 stage 0, source-only",
            "successor_branch": "research/hmt2_resolution_aware_feature_measure_v0",
        },
        "not_authorized": ["HMT-2 validation", "a new sealed bank",
                           "order leakage", "geometry mismatch", "VLBI",
                           "machine learning"],
        "inputs": {
            "sealed_main_freeze_v2_sha256": sha256_file(FZ2),
            "correction_017_sha256": sha256_file(COR),
            "validation_amendment_015_sha256": sha256_file(VAL),
        },
        "attestation": attest([FZ2, COR, VAL]),
    }
    OUT.write_text(json.dumps(doc, indent=2, default=str) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}\n  sha256 {sha256_file(OUT)}")
    print(f"  {len(doc['dispositions'])} dispositions recorded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
