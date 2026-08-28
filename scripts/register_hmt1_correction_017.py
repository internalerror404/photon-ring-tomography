#!/usr/bin/env python3
"""HMT1_SEALED_MAIN_CORRECTION_AND_RETIREMENT_017.

Items 1, 2, 3, 4 and 12 of REVIEWER_RULING_HMT1_MAIN_017. Record only.
Written and committed before any replacement truth is drawn.
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
RET = ROOT / "artifacts" / "configs" / "HMT1_SEALED_MAIN_BANK_V1_RETIREMENT_016.json"
G10C = ROOT / "artifacts" / "provenance" / "HMT1_G10C_VALIDATION.json"
OUT = ROOT / "artifacts" / "configs" / "HMT1_SEALED_MAIN_CORRECTION_AND_RETIREMENT_017.json"

RUN = "HMT1M_20260828T005146Z_2ba66f02"


def main() -> int:
    doc = {
        "schema": "phrt-record-amendment/1",
        "id": "HMT1_SEALED_MAIN_CORRECTION_AND_RETIREMENT_017",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "ruling": "REVIEWER_RULING_HMT1_MAIN_017",
        "kind": "RECORD_ONLY",
        "recomputation": "none",
        "written_before_replacement_truth_drawn": True,

        "preserved_run": {
            "run_id": RUN,
            "disposition": "HMT1_MAIN_IMPLEMENTATION_DEFECT",
            "gates": "17 of 18 passed",
            "failed": "HMT1M_G10b_truth_extraction_recovers_generative_parameters",
        },

        "HMT1_MAIN_PARTIAL_ENDPOINT_EXPOSURE": {
            "finding": "the withholding was incomplete. "
                       "hmt1_main_noiseless_control was written under the "
                       "withholding rule and carried median_noisy and "
                       "median_noiseless: per-arm medians of the old-band "
                       "feature error for the direct and resolved arms, at the "
                       "primary SNR, in all three regimes",
            "why_it_happened": "the withholding worked on a list of table "
                               "names and that table was classified as a "
                               "control. The classification was mine and it "
                               "was wrong: the table's name described its "
                               "purpose, not its columns",
            "consequence": "old-band endpoint aggregates for the arms that "
                           "carry the comparison were exposed for the bank "
                           "drawn under bank_seed 20260917. That bank can no "
                           "longer produce a sealed result",
            "remedy": "the firewall now screens column lineage rather than "
                      "filenames, in phrt.io.endpoint_lineage, with a test "
                      "asserting that the exact columns which leaked are "
                      "caught and that renaming a table changes nothing. "
                      "Gate HMT1M_G20 checks after the fact that no blocked "
                      "table reached disk",
            "self_assessment": "I reported the previous run as having kept the "
                               "bank unseen. That statement was wrong, and the "
                               "reviewer caught what I missed",
        },

        "retired_banks": {
            "20260915": {
                "reason": "stage B smoke tested on it before the sealed run",
                "record": "HMT1_SEALED_MAIN_BANK_V1_RETIREMENT_016",
            },
            "20260917": {
                "reason": "HMT1_MAIN_PARTIAL_ENDPOINT_EXPOSURE",
                "record": "HMT1_SEALED_MAIN_CORRECTION_AND_RETIREMENT_017",
                "permanence": "permanent. Gate HMT1M_G3 refuses any held-out "
                              "seed belonging to a retired bank, so neither "
                              "can be redrawn under another name",
            },
        },

        "preserved_gate_failure": {
            "gate": "HMT1M_G10b_truth_extraction_recovers_generative_parameters",
            "status": "FAIL",
            "token": "RETIRED_RAW_TRAJECTORY_PROXY_INVALID_FOR_WINDOWED_FEATURE",
            "reading": "the gate compared the extracted peak against the "
                       "instantaneous generative centre. The extractor reports "
                       "the argmax of the windowed field, and a feature that "
                       "moves inside the window does not occupy that centre. "
                       "The 1.201-cell failure was the proxy's error, not the "
                       "extractor's",
            "not_rerun": True,
        },

        "replacement_gate": {
            "gate": "HMT1M_G10c_truth_extraction_matches_independent_windowed_reference",
            "threshold_cells": 1.0,
            "threshold_unchanged": "the same frozen one-cell threshold the "
                                   "retired gate carried",
            "independence": [
                "evaluates the analytic source, not the sampled array the "
                "extractor reads",
                "samples several times finer per evaluation cell and takes a "
                "plain argmax, where the extractor takes a coarse argmax and "
                "refines it parabolically",
                "shares no code path with extract beyond numpy",
                "shares the declared window, deliberately, so that it measures "
                "the extractor rather than the difference between two windows",
            ],
            "validation": json.loads(G10C.read_text()) if G10C.exists() else None,
        },

        "estimator_scope": {
            "TSVD": "AUTHORIZED",
            "RIDGE_IDENTITY": "AUTHORIZED",
            "NONNEGATIVE_CONSTRAINED": "WITHDRAWN_UNSELECTED",
            "ML": "NOT_AUTHORIZED",
            "gate": "HMT1M_G19_estimator_scope",
            "note": "NONNEGATIVE_CONSTRAINED was declared as a control in the "
                    "validation freeze and never implemented, so it has no "
                    "selected hyperparameter. Selecting one now is the "
                    "retuning ruling 015 item 8 forbids. Withdrawn rather than "
                    "run, and the gate refuses any run that includes it",
        },

        "structural_changes": {
            "source_gates_moved_to_stage_a": "item 10. Every gate decidable "
                                             "from the source alone is decided "
                                             "before an operator is imported, "
                                             "and stage B refuses to import one "
                                             "unless all of them passed. The "
                                             "operator imports are inside a "
                                             "function called after that check, "
                                             "so the ordering is a property of "
                                             "the file",
            "endpoint_lineage_firewall": "item 11",
            "one_new_bank_seed": "item 9. 20260921, fixed now. No seed search "
                                 "and no redraw-until-pass loop: whatever bank "
                                 "this seed produces is the bank",
        },

        "unchanged_by_this_correction": [
            "production truth features", "extract()", "normalized_errors()",
            "endpoint definitions", "denominators", "tolerances",
            "materiality bars", "hyperparameters", "source families",
            "family ranges", "arms", "SNRs",
        ],
        "not_authorized": ["geometry mismatch", "order leakage", "VLBI",
                           "machine learning",
                           "a new pixel-movie reconstruction campaign"],
        "after_execution": "STOP, regardless of scientific disposition",
        "freeze_v2_sha256": sha256_file(FZ2),
        "retirement_016_sha256": sha256_file(RET),
        "attestation": attest([FZ2, RET]),
    }
    OUT.write_text(json.dumps(doc, indent=2, default=str) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}\n  sha256 {sha256_file(OUT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
