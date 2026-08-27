#!/usr/bin/env python3
"""R1L_STAGE1_DIRTY_EXECUTION_G8_MASK_FIX -- record-only amendment.

REVIEWER_RULING_R1L_STAGE1_008 items 2 and 3. Nothing is recomputed here. The
amendment records that the scientifically correct stage-1 execution was not a
clean preregistered run, and it records the three language corrections the
ruling requires in the stage-1 report.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from phrt.attestation import attest
from phrt.config import sha256_file

MANS = ROOT / "artifacts" / "manifests"
FREEZE = ROOT / "artifacts" / "configs" / "R1L_LOCALIZED_AUDIT_FREEZE.json"
OUT = ROOT / "artifacts" / "configs" / "R1L_STAGE1_DIRTY_EXECUTION_AMENDMENT_008.json"
CLEAN_FAILED = "R1L_20260827T044412Z_2ba66f02"
DIRTY_CORRECT = "R1L_20260827T044757Z_2ba66f02"


def att(run_id: str) -> dict:
    return json.loads((MANS / f"{run_id}.json").read_text())["attestation"]


def main() -> int:
    a_clean, a_dirty = att(CLEAN_FAILED), att(DIRTY_CORRECT)
    doc = {
        "schema": "phrt-record-amendment/1",
        "id": "R1L_STAGE1_DIRTY_EXECUTION_G8_MASK_FIX",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "ruling": "REVIEWER_RULING_R1L_STAGE1_008",
        "kind": "RECORD_ONLY",
        "recomputation": "none. No operator is rebuilt, no spectrum recomputed "
                         "and no gate re-evaluated by this amendment",
        "preserved_commits": [
            "291d387b3e911954ee0e0567e70e2a807a99544c",
            "3a6786c0e92f268db1b071ee8bcebaa060709c00",
        ],

        "the_defect": {
            "summary": "the stage-1 execution that produced every reported number "
                       "ran against a working tree carrying an uncommitted edit to "
                       "the runner itself, so it is not a clean preregistered run",
            "sequence": [
                {"run_id": CLEAN_FAILED,
                 "attestation": "clean, preregistered",
                 "outcome": "FAIL R1L_G8_unreached_columns_are_exactly_zero at "
                            "2.801e+02",
                 "cause": "the reached-temporal-mode mask was built from a single "
                          "observer time, t_obs[0], while the operator samples the "
                          "source at t_obs - delay for all eight. The newest "
                          "temporal functions were therefore called unreached and "
                          "compared against nonzero columns",
                 "verdict": "a clean run of an incorrect harness. The operator was "
                            "never wrong; the mask was"},
                {"run_id": DIRTY_CORRECT,
                 "attestation": "not clean, not preregistered",
                 "n_tracked_changes": a_dirty.get("n_tracked_changes"),
                 "porcelain_registered": a_dirty.get("porcelain_registered"),
                 "outcome": "all ten gates PASS",
                 "verdict": "a correct harness run dirty. Every stage-1 number "
                            "reported so far comes from this run"},
            ],
            "attestation_worked": "the machinery recorded preregistered = false "
                                  "and named the single changed path. The failure "
                                  "was in the reporting, not the instrumentation: "
                                  "the stage-1 report and its artifact manifest "
                                  "marked the execution attestation authoritative "
                                  "and did not surface that it was dirty",
            "classification": "DIRTY_EXECUTION_OF_CORRECTED_HARNESS",
            "is_a_scientific_defect": False,
            "is_a_governance_defect": True,
            "why_not_scientific": "the edit was confined to the boolean mask used "
                                  "by one gate and to the sample set the nesting "
                                  "residual is measured on. It cannot change a "
                                  "singular value, a rank or an information volume, "
                                  "because none of those are computed from the mask",
            "why_governance": "a run whose own runner was uncommitted cannot be "
                              "distinguished after the fact from a run whose "
                              "harness was tuned until the gates passed. The "
                              "distinction has to be structural, not asserted",
            "remedy": "item 5 of the ruling: rerun stage 1 from a completely clean "
                      "tree with no code edits and require equality of every "
                      "canonical numerical result. Both earlier runs are preserved",
        },

        "attestations": {
            "clean_but_failed": {k: a_clean.get(k) for k in
                                 ("execution_commit", "clean", "preregistered",
                                  "n_tracked_changes", "n_untracked",
                                  "porcelain_registered_sha256")},
            "correct_but_dirty": {k: a_dirty.get(k) for k in
                                  ("execution_commit", "clean", "preregistered",
                                   "n_tracked_changes", "n_untracked",
                                   "porcelain_registered", "porcelain_registered_sha256")},
        },

        # ------------------------------------------------------------ item 3
        "report_language_amendments": {
            "a_full_rank_claim": {
                "was": "C224 reports full column rank 224 of 224 for the direct "
                       "image with zero nullity. The full rank was a property of "
                       "global support, not of the measurement.",
                "defect": "true as arithmetic, overreaching as inference. Full "
                          "column rank on C224 is a statement about the global "
                          "temporal subspace and is not evidence either way about "
                          "epoch-local identifiability",
                "now": "C224 is full rank on its own global temporal subspace. "
                       "That establishes identifiability of the 224 global "
                       "coefficients and does not establish epoch-local "
                       "identifiability, which is a different question that C224 "
                       "cannot pose because no coefficient is confined to an epoch",
            },
            "b_where_orders_contribute": {
                "was": "the higher orders contribute exactly where the direct "
                       "image is blind and nowhere else. On modes 4 to 7 the three "
                       "arms are identical to the digit.",
                "defect": "false at mode 4. Direct reaches 25 of 28 there against "
                          "28 for resolved, so mode 4 is incomplete rather than "
                          "saturated, and the sentence asserted saturation",
                "now": "higher-order gains occur where the direct image is blind "
                       "or incomplete. Modes 5 to 7 agree across arms. Modes 3 and "
                       "4 receive incremental directions, 9 to 28 and 25 to 28. "
                       "Modes 0 to 2 are at zero for the direct image",
                "measured": {"mode_3": {"direct": 9, "resolved": 28, "unresolved": 21},
                             "mode_4": {"direct": 25, "resolved": 28, "unresolved": 28},
                             "mode_5": {"direct": 28, "resolved": 28, "unresolved": 28},
                             "mode_6": {"direct": 28, "resolved": 28, "unresolved": 28},
                             "mode_7": {"direct": 22, "resolved": 22, "unresolved": 22}},
            },
            "c_delay_versus_spatial": {
                "was": "the old-epoch information the higher orders carry is in "
                       "their delay structure, not in their spatial imprint.",
                "defect": "stated as a universal mechanism when it is a reading of "
                          "two registered counterfactual arms. DELAY_ONLY and "
                          "SPATIAL_ONLY are specific substitutions -- one "
                          "substitutes every order's spatial map for order 0's, "
                          "the other substitutes every order's delay for order "
                          "0's -- and they license a claim about those "
                          "substitutions, not about spatial remapping in general",
                "now": "under the registered counterfactual, delay diversity is "
                       "necessary and dominant for old-epoch structural support: "
                       "SPATIAL_ONLY matches the direct image at operational rank "
                       "0 and DELAY_ONLY exceeds the full resolved stack. This is "
                       "not a universal claim that spatial remapping has no effect",
            },
        },

        "instructions_discharged": [
            "1 preserve both commits",
            "2 record R1L_STAGE1_DIRTY_EXECUTION_G8_MASK_FIX",
            "3a C224 full rank is a global-subspace statement, not epoch-local "
            "identifiability",
            "3b higher-order gains occur where direct is blind or incomplete; "
            "modes 5-7 agree, modes 3-4 incremental",
            "3c delay diversity necessary and dominant under the registered "
            "counterfactual, not a universal claim",
            "4 commit the final runner and this amendment",
        ],
        "provenance": {
            "freeze_sha256": sha256_file(FREEZE),
            "runner": "scripts/run_r1l_operator_audit.py",
            "runner_sha256": sha256_file(ROOT / "scripts" / "run_r1l_operator_audit.py"),
            "runner_is_final": True,
        },
    }
    doc["attestation"] = attest([FREEZE])
    OUT.write_text(json.dumps(doc, indent=2) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}")
    print(f"  sha256 {sha256_file(OUT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
