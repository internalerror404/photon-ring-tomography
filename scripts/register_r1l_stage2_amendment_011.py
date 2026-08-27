#!/usr/bin/env python3
"""R1L_STAGE2_RECORD_AMENDMENT_011 -- record-only.

REVIEWER_RULING_R1L_STAGE2_011 items 1 to 6. Nothing is recomputed. The
amendment accepts stage 1 as canonical, accepts the stage-2 run mechanically,
reclassifies the emitted token, and records three defects and one reclassified
artifact.
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

S1B = ROOT / "artifacts" / "provenance" / "R1L_STAGE1_BASELINE.json"
S1R = ROOT / "artifacts" / "provenance" / "R1L_STAGE1_REPRODUCTION.json"
S2F = ROOT / "artifacts" / "configs" / "R1L_STAGE2_VALIDATION_ACTIVATION_010.json"
S2G = ROOT / "artifacts" / "gates" / "r1l_stage2_gates.json"
SEALED = ROOT / "artifacts" / "configs" / "R1L_SEALED_MAIN_COMMITMENT.json"
SEALED_NEW = (ROOT / "artifacts" / "configs"
              / "R1L_SEALED_ANALYTIC_STRESS_COMMITMENT_UNSCORED.json")
OUT = ROOT / "artifacts" / "configs" / "R1L_STAGE2_RECORD_AMENDMENT_011.json"


def main() -> int:
    s1b = json.loads(S1B.read_text())
    s1r = json.loads(S1R.read_text())
    s2g = json.loads(S2G.read_text())
    sealed = json.loads(SEALED.read_text())

    # ---- item 6: preserve the commitment under its corrected name ----------
    reclassified = dict(sealed)
    reclassified["id"] = "R1L_SEALED_ANALYTIC_STRESS_COMMITMENT_UNSCORED"
    reclassified["reclassified_from"] = {
        "id": sealed["id"], "path": str(SEALED.relative_to(ROOT)),
        "sha256": sha256_file(SEALED),
        "rule": "the original document is preserved byte for byte. This is a "
                "reclassification of what the commitment is for, not an edit to "
                "what it commits: the cell hashes, seeds and counts are "
                "unchanged",
    }
    reclassified["status"] = "COMMITTED_NOT_GENERATED_NOT_SCORED_NOT_A_SEALED_MAIN"
    reclassified["what_it_is"] = (
        "a committed analytic stress bank. It is not the sealed main of any "
        "experiment and confers no authorization to run one. Stage 2 showed the "
        "analytic banks carry a structural representation floor above the span "
        "criterion, so a sealed main over analytic truths would repeat an "
        "untestable endpoint rather than test anything")
    reclassified["may_be_scored"] = False
    reclassified["ruling"] = "REVIEWER_RULING_R1L_STAGE2_011 item 6"
    reclassified["attestation"] = attest([SEALED])
    SEALED_NEW.write_text(json.dumps(reclassified, indent=2) + "\n")

    doc = {
        "schema": "phrt-record-amendment/1",
        "id": "R1L_STAGE2_RECORD_AMENDMENT_011",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "ruling": "REVIEWER_RULING_R1L_STAGE2_011",
        "kind": "RECORD_ONLY",
        "recomputation": "none. No bank is rebuilt, no operator formed, no score "
                         "recomputed and no gate re-evaluated by this amendment",

        "stage1_canonical": {
            "accepted": True,
            "baseline_run": s1b["baseline_run"],
            "reproduced_by": s1b["reproduced_by"],
            "verdict": s1r["verdict"],
            "execution_commit": s1b["execution_commit"],
            "rule": "the stage-1 tables are canonical. Two pinned six-class runs "
                    "in separate processes agreed on every normalized scientific "
                    "cell, and every discrete conclusion agrees with both pre-pin "
                    "executions",
        },

        "stage2_mechanical_acceptance": {
            "run_id": s2g["run_id"],
            "gates_pass": s2g["summary"]["PASS"],
            "gates_total": len(s2g["gates"]),
            "accepted": "mechanically. Every gate passed and the run was clean, "
                        "preregistered and single-threaded. Mechanical acceptance "
                        "is a statement about execution, not about what the "
                        "numbers mean",
        },

        # ------------------------------------------------------------ item 3
        "emitted_token": {
            "token": "R1L_STAGE2_RESOLVED_AND_UNRESOLVED_PASS",
            "preserved": True,
            "classification": "FORMAL_PROTOCOL_TOKEN_UNDER_NONMATERIAL_CRITERIA",
            "is_a_scientific_reconstruction_pass": False,
            "why": "the declared criteria required a bootstrap interval "
                   "excluding zero and carried no effect-size threshold. With "
                   "128 paired pilot truths the bootstrap variance is small "
                   "enough that a consistent sign passes at almost any "
                   "magnitude. The unresolved arm's passing effect, the one "
                   "thing separating this token from RESOLVED_ONLY_PASS, is a "
                   "relative reduction of 9.5e-05",
            "rule": "the token is preserved because it is what the frozen rule "
                    "produced. Deleting it would hide that the rule was "
                    "satisfiable without a material effect, which is the finding",
        },

        # ------------------------------------------------------------ item 4
        "R1L_S2_PRIMARY_INCLUDED_SECONDARY_BANK": {
            "defect": "baseline_one_positive entered the pooled primary endpoint",
            "freeze_said": S2F.name + " -> source_banks.baseline_one_positive: "
                           "'secondary control only', 'may not carry the primary "
                           "endpoint'",
            "what_happened": "the endpoint pooled every pilot truth by "
                             "(class, arm, estimator, SNR) without filtering on "
                             "bank, so a quarter of the paired sample came from "
                             "the secondary control",
            "why_it_matters": "baseline_one_positive has a median structure "
                              "fraction of 0.219 against 0.50 to 0.82 for the "
                              "primary banks, and the largest representation "
                              "floor of the four. Pooling it in mixes the regime "
                              "the endpoint was written to leave behind",
            "detected_by": "the reviewer, not by a gate. No gate checked bank "
                           "eligibility for the endpoint",
            "remedy": "stage 2R-A recomputes the endpoint from the existing "
                      "per-truth scores with the secondary bank excluded, every "
                      "primary bank reported separately, and equal-weight "
                      "bank-family aggregation",
            "changes_the_final_tables": "the per-truth scores are unaffected. "
                                        "The pooled endpoint rows are superseded "
                                        "by stage 2R-A",
        },

        # ------------------------------------------------------------ item 5
        "SUPERSEDED_OPERATOR_SCORER_TRUTH_MISMATCH": {
            "defect": "the bank shaping was defined on the evaluation grid while "
                      "the data was formed from the raw family render, so the "
                      "operator and the scorer were looking at different sources "
                      "and the shaping was measured as reconstruction error",
            "observed_effect": "L224 reported RESOLVED_ONLY_PASS before the fix "
                               "and NEGATIVE_RESULT after it. The inflation was "
                               "the whole apparent advantage",
            "status": "SUPERSEDED",
            "final_state": "the shaped truth exists as a callable and reproduces "
                           "the grid-built truth to 1.46e-14 relative. Gate "
                           "R1L_S2_G13_analytic_shaping_matches_grid_truth checks "
                           "it at 1e-9 and passed",
            "changes_the_final_tables": False,
        },
        "R1L_S2_TOKEN_OMITTED_NULL_CONTROL": {
            "defect": "the disposition gated on three of the four declared "
                      "criteria, omitting null-pair likelihood consistency. A "
                      "control failure could have passed silently",
            "status": "REPAIRED",
            "final_state": "the rule now requires the null control, and the "
                           "corrected rule was re-derived against the committed "
                           "tables. The control passed, so the token is unchanged",
            "changes_the_final_tables": False,
            "note": "the null-pair control itself had an earlier defect: it drew "
                    "from the exact null space, asking directions that produce no "
                    "separation at any amplitude to realize a one-sigma "
                    "separation. It now draws from the smallest nonzero singular "
                    "directions and passes at a worst relative error well inside "
                    "tolerance",
        },

        # ------------------------------------------------------------ item 6
        "sealed_commitment": {
            "preserved_as": "R1L_SEALED_ANALYTIC_STRESS_COMMITMENT_UNSCORED",
            "path": str(SEALED_NEW.relative_to(ROOT)),
            "original_preserved_at": str(SEALED.relative_to(ROOT)),
            "original_sha256": sha256_file(SEALED),
            "n_truths": sealed["n_truths"],
            "scored": False,
            "may_be_scored": False,
            "why_not": "the analytic banks carry a structural representation "
                       "floor above the span criterion, so scoring 384 more "
                       "analytic truths would repeat an untestable endpoint",
        },

        "instructions_discharged": [
            "1 accept deterministic stage 1 as canonical",
            "2 accept the final stage-2 run mechanically, 14/14 gates",
            "3 preserve the token and classify it "
            "FORMAL_PROTOCOL_TOKEN_UNDER_NONMATERIAL_CRITERIA",
            "4 record R1L_S2_PRIMARY_INCLUDED_SECONDARY_BANK",
            "5 record SUPERSEDED_OPERATOR_SCORER_TRUTH_MISMATCH and "
            "R1L_S2_TOKEN_OMITTED_NULL_CONTROL",
            "6 preserve the sealed commitment unscored under its new name",
        ],
        "provenance": {
            "stage2_freeze_sha256": sha256_file(S2F),
            "stage1_baseline_sha256": sha256_file(S1B),
        },
    }
    doc["attestation"] = attest([S2F, S1B])
    OUT.write_text(json.dumps(doc, indent=2) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}")
    print(f"wrote {SEALED_NEW.relative_to(ROOT)}")
    print(f"  token classified: FORMAL_PROTOCOL_TOKEN_UNDER_NONMATERIAL_CRITERIA")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
