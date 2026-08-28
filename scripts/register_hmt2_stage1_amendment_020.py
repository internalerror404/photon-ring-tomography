#!/usr/bin/env python3
"""HMT2_STAGE1_ENDPOINT_COMPLETION_AMENDMENT_020.

Items 1 to 10 of REVIEWER_RULING_HMT2_STAGE1_020. Committed before any
recomputation, so the record of what was wrong cannot be shaped by what the
recomputation shows.
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

S1 = ROOT / "artifacts" / "configs" / "HMT2_STAGE1_RESOLUTION_AWARE_MORPHOLOGY_VALIDATION_V0.json"
S0R = ROOT / "artifacts" / "configs" / "HMT2_STAGE0R_SOURCE_ONLY_CORRECTION_V0.json"
G1 = ROOT / "artifacts" / "gates" / "hmt2_stage1_gates.json"
OUT = ROOT / "artifacts" / "configs" / "HMT2_STAGE1_ENDPOINT_COMPLETION_AMENDMENT_020.json"


def main() -> int:
    doc = {
        "schema": "phrt-record-amendment/1",
        "id": "HMT2_STAGE1_ENDPOINT_COMPLETION_AMENDMENT_020",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "ruling": "REVIEWER_RULING_HMT2_STAGE1_020",
        "kind": "RECORD_AND_RECOMPUTATION_MANDATE",
        "accepted_commit": "112cd830b5a6df78d9e9e11ab43cb6d5fca89308",
        "written_before_recomputation": True,

        "canonical_stage_0r": {
            "stable_merger_rate_L448_contrast": 0.299,
            "stable_merger_rate_L896_radial_enriched": 0.136,
            "stratum": "STABLE_MULTI_RESOLVED, reconciled across the two "
                       "finest refinement levels",
            "status": "CANONICAL",
            "supersedes": "the pooled 0.356 and 0.262, which remain in the "
                          "record as what the finest grid alone would say and "
                          "carry no claim",
        },

        "formal_token_preserved": "HMT2_S1_PHYSICAL_MORPHOLOGY_RECOVERY_PASS",
        "formal_token_reading": "the registered pass criteria were met. The "
                                "criteria are what the token reports, and the "
                                "dispositions below say what the run actually "
                                "establishes",

        "scientific_dispositions": {
            "HMT2_S1_SUBSTANTIVE_ALL_STATE_MORPHOLOGY_ERROR_REDUCTION": {
                "finding": "the resolved arm in the primary class reduces the "
                           "all-state morphology error against the direct "
                           "image by a median 0.120 and 0.130 at SNR 100 and "
                           "0.122 and 0.141 at SNR 1000, on both classical "
                           "estimators, on both targets, with paired "
                           "bootstrap intervals excluding zero",
                "robustness": "the resolved arm wins on all three measure "
                              "kinds, so the reduction is not carried by one "
                              "state class",
            },
            "HMT2_S1_ACCURATE_MORPHOLOGY_RECOVERY_NOT_ESTABLISHED": {
                "finding": "absolute all-state error remains 0.66 for the "
                           "resolved arm on a scale whose worst case is 1.0, "
                           "and the conditional cost on stable "
                           "multi-resolved states stays above 1.0, meaning "
                           "more than one whole feature wrong on average",
                "reading": "a material reduction in a morphology error is not "
                           "accurate morphology recovery, and this run does "
                           "not establish the latter",
            },
            "HMT2_S1_UNRESOLVED_NO_CONFIRMED_GAIN": {
                "finding": "the unresolved-image arm reaches improvement in "
                           "neither class on either target",
                "reading": "the benefit is attributable to resolving the "
                           "photon-ring orders rather than to the additional "
                           "photons an unresolved second image also carries",
            },
            "HMT2_S1_ESTIMATOR_ROBUST_TWO_FEATURE_RESULT_NOT_RUN": {
                "finding": "the stable multi-resolved endpoint was computed "
                           "for TSVD at the primary SNR only",
                "reading": "no estimator-robust statement about two-feature "
                           "recovery exists. The 1.451 to 1.376 figure is one "
                           "estimator at one SNR and must not be read as an "
                           "estimator-robust result",
            },
        },

        "defects_recorded": {
            "HMT2_S1_PASS_RULE_HAS_NO_EFFECT_SIZE_FLOOR": {
                "defect": "the improvement test is median > 0 with a bootstrap "
                          "lower bound > 0, and carries no materiality "
                          "threshold at all. HMT-1 required a median of 0.10 "
                          "and a lower bound of 0.05; stage 1 requires only "
                          "that the interval clear zero",
                "consequence": "an arbitrarily small effect with a tight "
                               "interval satisfies the rule. The measured "
                               "effect is 0.12 to 0.14 and would clear an "
                               "HMT-1-style floor, so the disposition does not "
                               "change, but the rule that produced it is "
                               "weaker than the number makes it look",
                "evidence": "UNRESOLVED_IMAGE in the primary class under ridge "
                            "records a median of 0.0001 with a lower bound of "
                            "0.0000, and misses only because the bound is not "
                            "strictly positive",
                "not_repaired_by_recomputation": "changing the pass rule now "
                                                 "would be moving a criterion "
                                                 "after seeing the result. It "
                                                 "is recorded, and the "
                                                 "recomputation reports effect "
                                                 "sizes and intervals so a "
                                                 "floor can be applied by "
                                                 "inspection",
            },
            "HMT2_S1_PER_KIND_TABLE_FIRST_NOISE_DRAW_ONLY": {
                "defect": "the per-state table was written from the first "
                          "noise draw of four. The per-kind decomposition that "
                          "the report used to argue the gain is not carried by "
                          "one state class therefore rests on a quarter of the "
                          "evidence",
                "repaired_by": "item 9. All draws are decomposed",
            },
            "HMT2_S1_STABLE_MULTI_ENDPOINT_TSVD_ONLY": {
                "defect": "the stable multi-resolved accumulation was gated on "
                          "the estimator being TSVD and the SNR being primary",
                "repaired_by": "item 9. Both estimators and both SNRs",
            },
            "HMT2_S1_CLASS_CONDITIONAL_LABEL_SEMANTICS_AMBIGUITY": {
                "defect": "the class-conditional target compares against the "
                          "in-class projection's maps and features while "
                          "selecting the per-state measure from the *analytic* "
                          "source label. A state the analytic field resolves "
                          "into two features may be merged into one by the "
                          "projection, and it is then scored by the "
                          "multi-feature measure against a reference that has "
                          "one. Which label should govern the class-conditional "
                          "target was never decided",
                "repaired_by": "item 9. Both companions are emitted, "
                               "analytic-label and projected-label, so the "
                               "choice is visible rather than implicit",
            },
        },

        "recomputation_contract": {
            "same": ["validation bank", "operators", "hyperparameters", "SNRs",
                     "noise draws"],
            "forbidden": ["new truth", "selection", "any change to a primary "
                          "endpoint cell"],
            "bitwise_requirement": "every existing primary endpoint cell must "
                                   "reproduce bitwise. Item 8",
            "on_change": "STOP. Item 10. A recomputation that moves a primary "
                         "cell is not a completion, it is a different run, and "
                         "the difference has to be explained before anything "
                         "is added to it",
            "noise_stream_note": "the noise draws are generated by one stream "
                                 "over the full key list including the "
                                 "selection split. The recomputation scores "
                                 "only the pilot split but must still advance "
                                 "the stream over the selection keys in the "
                                 "same order, or the pilot noise differs and "
                                 "nothing reproduces",
            "emit": ["all-draw per-kind decompositions", "non-DEAD companion",
                     "saturation fractions",
                     "per-family effects and intervals",
                     "stable multi endpoint for both estimators and both SNRs",
                     "analytic-label and projected-label class-conditional "
                     "companions",
                     "stable age-resolved morphology interval"],
        },

        "inputs": {"stage_1_freeze_sha256": sha256_file(S1),
                   "stage_0r_freeze_sha256": sha256_file(S0R),
                   "stage_1_gates_sha256": sha256_file(G1)},
        "attestation": attest([S1, S0R]),
    }
    OUT.write_text(json.dumps(doc, indent=2, default=str) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}\n  sha256 {sha256_file(OUT)}")
    print(f"  {len(doc['scientific_dispositions'])} dispositions, "
          f"{len(doc['defects_recorded'])} defects recorded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
