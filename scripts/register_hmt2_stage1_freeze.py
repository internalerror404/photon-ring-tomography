#!/usr/bin/env python3
"""HMT2_STAGE1_RESOLUTION_AWARE_MORPHOLOGY_VALIDATION_V0.

Items 12 to 18 of REVIEWER_RULING_HMT2_STAGE0_019. Authorized because stage 0R
passed every corrected source-only gate. Registered before any validation truth
is drawn.
"""
from __future__ import annotations

import hashlib
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
from phrt.metrics.features import BIRTH_FRACTION  # noqa: E402

S0 = ROOT / "artifacts" / "configs" / "HMT2_STAGE0_SOURCE_OBJECT_AND_RESOLUTION_AUDIT_V0.json"
S0R = ROOT / "artifacts" / "configs" / "HMT2_STAGE0R_SOURCE_ONLY_CORRECTION_V0.json"
S0RG = ROOT / "artifacts" / "gates" / "hmt2_stage0r_gates.json"
VFZ = ROOT / "artifacts" / "configs" / "HMT1_VALIDATION_FREEZE_V0.json"
OUT = ROOT / "artifacts" / "configs" / "HMT2_STAGE1_RESOLUTION_AWARE_MORPHOLOGY_VALIDATION_V0.json"

SEED = 20260941
PER_FAMILY = 6      # per split
N_DRAWS = 4
SELECTION_DRAWS = 2
SPLITS = ("selection", "pilot")


def commitment(family, split, n, seed):
    return hashlib.sha256(json.dumps(
        {"family": family, "split": f"hmt2_stage1_{split}", "n": n,
         "seed": seed, "model": "contrast"}, sort_keys=True).encode()).hexdigest()


def main() -> int:
    s0 = json.loads(S0.read_text())
    vfz = json.loads(VFZ.read_text())
    g0r = json.loads(S0RG.read_text())
    if g0r["failed_gates"]:
        print(f"stage 0R failed {g0r['failed_gates']}; item 11 says stop",
              file=sys.stderr)
        return 1
    fams = list(s0["source_families"]["declared"])

    doc = {
        "schema": "phrt-hmt2-stage1-freeze/1",
        "id": "HMT2_STAGE1_RESOLUTION_AWARE_MORPHOLOGY_VALIDATION_V0",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "ruling": "REVIEWER_RULING_HMT2_STAGE0_019",
        "status": "FROZEN_BEFORE_ANY_VALIDATION_TRUTH",
        "branch": "research/hmt2_resolution_aware_feature_measure_v0",
        "authorized_by": "item 12, stage 0R having passed every corrected "
                         "source-only gate",
        "stage_0r_gates_sha256": sha256_file(S0RG),

        "what_stage_1_is": "the first HMT-2 stage that constructs an operator. "
                           "It asks whether resolving the photon ring orders "
                           "improves a resolution-aware description of the "
                           "past, measured on every state the source presents "
                           "rather than only the states that happen to be "
                           "cleanly resolved",

        "source_model": {
            "families": fams,
            "ranges": "the original six declared ranges, verbatim. Item 13",
            "minimum_separation_cut": "none. Item 13. Stage 0R measured what "
                                      "these ranges contain; a cut would "
                                      "remove the very states the endpoint is "
                                      "designed to score",
            "expected_windowed_multiplicity":
                s0["source_families"]["expected_windowed_multiplicity"],
        },

        "classes": {
            "primary": {
                "id": "L896_radial_enriched",
                "radial": 8, "azimuthal": 7, "temporal": 16,
                "dimension_after_m0_removal": 768,
                "role": "the primary bounded class. Item 13",
                "why": "stage 0R measured its stable-state merger rate at "
                       "0.136 against 0.299 for the current class, and its "
                       "representation floor about an order of magnitude "
                       "lower",
            },
            "control": {
                "id": "L448_contrast",
                "radial": 4, "azimuthal": 7, "temporal": 16,
                "dimension_after_m0_removal": 384,
                "role": "representation-limited control. Item 13",
                "why": "it is the class HMT-1 used, and carrying it makes the "
                       "cost of the representation limit visible in the same "
                       "run rather than by comparison across runs",
            },
        },

        "targets": {
            "CLASS_CONDITIONAL": {
                "reference": "the best in-class approximation of the source "
                             "object",
                "reads": "how much of what the class can represent the "
                         "estimator recovers",
                "claim_it_supports": "a class-conditional result, and nothing "
                                     "more",
            },
            "PHYSICAL_END_TO_END": {
                "reference": "the analytic source object itself",
                "reads": "how much of what is actually there the estimator "
                         "recovers",
                "claim_it_supports": "a physical historical-recovery claim",
            },
            "rule": "item 14. Improvement on CLASS_CONDITIONAL alone is a "
                    "class-conditional result. A physical claim requires "
                    "improvement on PHYSICAL_END_TO_END as well. Both are "
                    "reported for every arm, estimator and SNR, always "
                    "together and always named",
        },

        "endpoints": {
            "primary": {
                "id": "all_state_resolution_aware_morphology_error",
                "definition": "one error per (truth, age) computed by the "
                              "measure appropriate to that state's reconciled "
                              "label, aggregated over all states without "
                              "exclusion",
                "per_state_measure": {
                    "SINGLE_RESOLVED": "set-valued unbalanced assignment cost "
                                       "on the one feature",
                    "MULTI_RESOLVED": "set-valued unbalanced assignment cost "
                                      "over the feature set",
                    "BLENDED": "normalised discrepancy in centroid, size and "
                               "mode content -- what a one-peak field "
                               "supports",
                    "AMBIGUOUS": "the BLENDED measure, because a state whose "
                                 "multiplicity the analysis grid cannot settle "
                                 "must not be scored as though it had a "
                                 "definite feature count",
                    "DEAD": "amplitude discrepancy only; no position is "
                            "defined",
                },
                "normalisation": "each per-state measure is expressed in units "
                                 "of its own worst case, so states of "
                                 "different kinds combine without one kind "
                                 "dominating by having a larger natural scale",
                "no_exclusions": "item 16. BLENDED and AMBIGUOUS states are "
                                 "in the primary endpoint and are never forced "
                                 "into two-track scoring",
            },
            "secondary_conditional": {
                "id": "set_valued_positions_and_tracks",
                "restricted_to": "reconciled STABLE_MULTI_RESOLVED states",
                "rule": "item 15. Conditional by construction and reported as "
                        "such: it says what recovery looks like where the "
                        "source is cleanly resolved, and carries no claim "
                        "about the rest",
            },
        },

        "bank": {
            "truths_per_family_per_split": PER_FAMILY,
            "splits": list(SPLITS),
            "n_families": len(fams),
            "n_truths": PER_FAMILY * len(fams) * len(SPLITS),
            "noise_draws_per_truth": N_DRAWS,
            "selection_draws_per_truth": SELECTION_DRAWS,
            "bank_seed": SEED,
            "split_rule": "hyperparameters are chosen on the selection split "
                          "and nowhere else; the endpoint is read on the pilot "
                          "split, on truths no hyperparameter saw",
            "fresh": "a new validation bank, disjoint from every HMT-1 bank "
                     "and from the stage 0 audit bank by commitment string",
            "commitments": {f"{f}|{sp}": commitment(f, sp, PER_FAMILY, SEED)
                            for f in fams for sp in SPLITS},
            "size_note": "an earlier draft declared 8 per family with no split "
                         "at all, which left nowhere disjoint to select "
                         "hyperparameters. Corrected before any truth was "
                         "drawn",
            "not_a_sealed_main": "item 17. This is a validation. No held-out "
                                 "sealed bank is created, and none is "
                                 "authorized",
        },
        "evaluation": {
            "comparison_grid": [16, 32, 40],
            "rule": "the state's *label* comes from the converged source "
                    "analysis on the two finest refinement levels; the "
                    "*measurement* happens on the declared evaluation grid. "
                    "That split is what resolution-aware means here: a state "
                    "is scored for what it is, measured where the instrument "
                    "looks. Scoring the label on the coarse grid would let the "
                    "grid decide what the source contains, which is the HMT-1 "
                    "failure",
        },

        "arms": list(vfz["arms"]),
        "estimators": {
            "authorized": ["TSVD", "RIDGE_IDENTITY"],
            "rule": "item 17, classical only",
            "ML": "NOT_AUTHORIZED",
            "NONNEGATIVE_CONSTRAINED": "WITHDRAWN_UNSELECTED, carried forward "
                                       "from ruling 017 item 12",
            "selection": "on a selection split disjoint from the reported "
                         "split, by the same rule the HMT-1 validation used",
        },
        "snr": {"primary": vfz["snr"]["primary"],
                "secondary": vfz["snr"]["secondary"]},

        "classification": {
            "prominence_fraction": BIRTH_FRACTION,
            "dead_fraction": BIRTH_FRACTION,
            "levels": [[g["n_radial"], g["n_azimuthal"], g["n_temporal"]]
                       for g in s0["grids"]["nested"]][-2:],
            "reconciliation": "the reconciled label from the two finest "
                              "refinement levels, as in stage 0R",
            "note": "the source-side classification is computed exactly as "
                    "stage 0R computed it, on the same two finest refinement "
                    "levels, so a state's label does not depend on which stage "
                    "is looking at it. An earlier draft of this freeze took "
                    "the two coarsest levels while claiming the two finest; "
                    "corrected before any truth was drawn",
            "cost_note": "the source classification is per truth, not per arm "
                         "or draw, so using the finest level costs 48 "
                         "classifications rather than 48 times the arm, "
                         "estimator, SNR and draw product. The reconstruction "
                         "is evaluated on the same grids through the separable "
                         "factors, which needs no dense design",
        },

        "gates": {
            "HMT2S1_G1_pinned_numerical_environment": "structural",
            "HMT2S1_G2_commitments_reproduce": "structural",
            "HMT2S1_G3_bank_disjoint_from_stage_0_and_hmt1": 0,
            "HMT2S1_G4_contrast_zero_spatial_mean": 1e-10,
            "HMT2S1_G5_total_emissivity_nonnegative": 0.0,
            "HMT2S1_G6_adjoint": 1e-8,
            "HMT2S1_G7_operator_truth_identity": 1e-9,
            "HMT2S1_G8_both_targets_reported": 0,
            "HMT2S1_G9_no_state_excluded_from_primary": 0,
            "HMT2S1_G10_blended_not_forced_into_two_tracks": 0,
            "HMT2S1_G11_secondary_restricted_to_stable_states": 0,
            "HMT2S1_G12_estimator_scope": 0,
            "HMT2S1_G13_no_sealed_bank_created": 0,
            "HMT2S1_G14_declared_gate_coverage": "structural",
            "HMT2S1_G15_resource_limits": "structural",
        },
        "gate_notes": {
            "HMT2S1_G8_both_targets_reported": "endpoint rows missing either "
                                               "target. Must be zero: item 14 "
                                               "requires both, and reporting "
                                               "one alone is how a "
                                               "class-conditional result gets "
                                               "read as a physical one",
            "HMT2S1_G9_no_state_excluded_from_primary": "states present in the "
                                                        "source classification "
                                                        "and absent from the "
                                                        "primary endpoint. "
                                                        "Must be zero",
            "HMT2S1_G10_blended_not_forced_into_two_tracks": "BLENDED or "
                                                             "AMBIGUOUS states "
                                                             "scored by a "
                                                             "multi-feature "
                                                             "measure. Must be "
                                                             "zero",
            "HMT2S1_G13_no_sealed_bank_created": "held-out sealed banks "
                                                 "created by this stage. Must "
                                                 "be zero",
        },

        "pass_criteria": {
            "class_conditional": "resolved arm improves on the direct image, "
                                 "both estimators, interval excluding zero",
            "physical_end_to_end": "the same, against the analytic source",
            "reading": "improvement on the first alone is reported as "
                       "CLASS_CONDITIONAL_ONLY and is not a historical "
                       "recovery claim",
        },
        "dispositions": {
            "HMT2_S1_PHYSICAL_MORPHOLOGY_RECOVERY_PASS":
                "improvement on both targets",
            "HMT2_S1_CLASS_CONDITIONAL_ONLY":
                "improvement on CLASS_CONDITIONAL and not on "
                "PHYSICAL_END_TO_END",
            "HMT2_S1_NO_MATERIAL_EFFECT":
                "banks sound, neither target improves materially",
            "HMT2_S1_SOURCE_BANK_FAILURE":
                "a declared bank could not be built within tolerances",
            "HMT2_S1_IMPLEMENTATION_DEFECT":
                "a gate failed, a limit was exceeded, or a commitment did not "
                "reproduce",
        },
        "gate_failure_forces_defect_token": True,
        "resource_limits": {"wall_clock_seconds": 14400,
                            "on_exceeded": "HMT2_S1_IMPLEMENTATION_DEFECT"},
        "numerical_environment": vfz["numerical_environment"],
        "after": "STOP for reviewer adjudication. Item 18",
        "not_authorized": ["a sealed held-out main", "order leakage",
                           "geometry mismatch", "VLBI", "machine learning",
                           "a new pixel-movie reconstruction campaign"],
        "inherits": {"stage_0_sha256": sha256_file(S0),
                     "stage_0r_sha256": sha256_file(S0R),
                     "hmt1_validation_freeze_sha256": sha256_file(VFZ)},
        "attestation": attest([S0, S0R, VFZ]),
    }
    OUT.write_text(json.dumps(doc, indent=2, default=str) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}\n  sha256 {sha256_file(OUT)}")
    print(f"  {PER_FAMILY} x {len(fams)} x {len(SPLITS)} = "
          f"{PER_FAMILY * len(fams) * len(SPLITS)} truths, "
          f"{len(doc['gates'])} gates, 2 targets")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
