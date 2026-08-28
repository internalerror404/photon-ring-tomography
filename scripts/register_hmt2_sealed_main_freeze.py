#!/usr/bin/env python3
"""HMT2_SEALED_MAIN_V1.

Item 11 of REVIEWER_RULING_HMT2_STAGE1_020, authorized by
HMT2_S1_ENDPOINT_COMPLETION_PASS. Registered and committed before any held-out
truth is drawn.

The contract is everything the campaign has had to learn, carried forward
explicitly rather than remembered.
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

import pandas as pd  # noqa: E402

from phrt.attestation import attest  # noqa: E402
from phrt.config import sha256_file  # noqa: E402
from phrt.metrics.features import BIRTH_FRACTION  # noqa: E402

S1 = ROOT / "artifacts" / "configs" / "HMT2_STAGE1_RESOLUTION_AWARE_MORPHOLOGY_VALIDATION_V0.json"
AMD = ROOT / "artifacts" / "configs" / "HMT2_STAGE1_ENDPOINT_COMPLETION_AMENDMENT_020.json"
CG = ROOT / "artifacts" / "gates" / "hmt2_stage1_completion_gates.json"
SEL = ROOT / "artifacts" / "tables" / "hmt2_stage1_selection.parquet"
OUT = ROOT / "artifacts" / "configs" / "HMT2_SEALED_MAIN_V1.json"

SEED = 20260953
PER_FAMILY = 10
N_DRAWS = 4


def commitment(family, n, seed):
    return hashlib.sha256(json.dumps(
        {"family": family, "split": "hmt2_sealed_main_heldout", "n": n,
         "seed": seed, "model": "contrast"}, sort_keys=True).encode()).hexdigest()


def main() -> int:
    s1 = json.loads(S1.read_text())
    cg = json.loads(CG.read_text())
    if cg["stop_token"] != "HMT2_S1_ENDPOINT_COMPLETION_PASS":
        print(f"completion did not pass ({cg['stop_token']}); item 11 does not "
              f"authorize a sealed main", file=sys.stderr)
        return 1
    sel = pd.read_parquet(SEL)
    sealed = {f"{r['class']}|{r.arm}|{r.estimator}": {
        "hyperparameter": float(r.selected_hyperparameter),
        "stage_1_selection_error": float(r.selection_error),
        "at_max_regularization_end": bool(r.at_max_regularization_end)}
        for _, r in sel.iterrows()}
    assert len(sealed) == 16 and not any(
        v["at_max_regularization_end"] for v in sealed.values())
    fams = list(s1["source_model"]["families"])

    doc = {
        "schema": "phrt-hmt2-sealed-main-freeze/1",
        "id": "HMT2_SEALED_MAIN_V1",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "ruling": "REVIEWER_RULING_HMT2_STAGE1_020",
        "status": "SEALED_BEFORE_ANY_HELD_OUT_TRUTH",
        "branch": "research/hmt2_resolution_aware_feature_measure_v0",
        "authorized_by": "item 11, on HMT2_S1_ENDPOINT_COMPLETION_PASS",
        "completion_gates_sha256": sha256_file(CG),

        "inherits_verbatim": {
            "source_families": fams,
            "family_ranges": "the original six, no separation cut",
            "classes": s1["classes"],
            "arms": s1["arms"],
            "targets": s1["targets"],
            "primary_endpoint": s1["endpoints"]["primary"],
            "secondary_conditional": s1["endpoints"]["secondary_conditional"],
            "classification": s1["classification"],
            "evaluation": s1["evaluation"],
            "expected_windowed_multiplicity":
                s1["source_model"]["expected_windowed_multiplicity"],
            "prominence_fraction": BIRTH_FRACTION,
            "stage_1_freeze_sha256": sha256_file(S1),
        },

        "sealed_hyperparameters": {
            "values": sealed,
            "provenance": "the stage 1 selection split, unchanged. All 16 are "
                          "interior to their grids",
            "rule": "used verbatim. This runner contains no selection sweep",
        },

        "bank": {
            "truths_per_family": PER_FAMILY,
            "n_truths": PER_FAMILY * len(fams),
            "noise_draws_per_truth": N_DRAWS,
            "bank_seed": SEED,
            "commitments": {f: commitment(f, PER_FAMILY, SEED) for f in fams},
            "freshness": "the commitment payload carries "
                         "split='hmt2_sealed_main_heldout', a string no earlier "
                         "bank used, so no seed can recur. Checked as well",
            "held_out": True,
        },

        "pass_criteria": {
            "materiality": {
                "median_relative_reduction": 0.10,
                "median_bootstrap_lower_bound": 0.05,
                "provenance": "the numeric standard HMT-1 declared and used. "
                              "Stage 1's rule asked only that the interval "
                              "clear zero, which "
                              "HMT2_S1_PASS_RULE_HAS_NO_EFFECT_SIZE_FLOOR "
                              "records as a defect. A floor cannot be added to "
                              "a finished run without moving a criterion after "
                              "the fact, but it can and must be declared in "
                              "advance for a new one, and it is declared here",
            },
            "both_targets_required": "a physical claim requires materiality on "
                                     "PHYSICAL_END_TO_END. Materiality on "
                                     "CLASS_CONDITIONAL alone is reported as "
                                     "class-conditional and is not a physical "
                                     "claim",
            "both_estimators_required": True,
            "claim_bearing_class": s1["classes"]["primary"]["id"],
            "saturation_disclosure": "the fraction of states at the measure's "
                                     "ceiling is reported for every cell. A "
                                     "reduction that is entirely a change in "
                                     "saturation fraction is reported as such",
        },

        "must_emit": [
            "all-draw per-kind decompositions",
            "non-DEAD companion",
            "saturation fractions",
            "per-family effects and intervals",
            "stable multi endpoint for both estimators and both SNRs",
            "analytic-label and projected-label class-conditional companions",
            "stable age-resolved morphology interval",
        ],

        "two_stage_execution": {
            "rule": "every source-side gate is decided in stage A, before any "
                    "operator is imported, and the bank hashes are committed "
                    "before stage B runs. Carried forward from ruling 017 "
                    "items 9 and 10, which the HMT-1 sealed main needed and "
                    "did not have",
            "stage_a": "scripts/run_hmt2_sealed_main_bank.py",
            "stage_b": "scripts/run_hmt2_sealed_main.py",
            "on_stage_a_failure": "stage B refuses to import an operator",
        },
        "endpoint_lineage_firewall": {
            "rule": "on any failed gate no endpoint-derived quantity is "
                    "emitted under any filename. Carried forward from ruling "
                    "017 item 11",
            "module": "phrt.io.endpoint_lineage",
        },

        "dispositions": {
            "HMT2_MAIN_PHYSICAL_MORPHOLOGY_RECOVERY_PASS":
                "materiality on both targets, both estimators, claim-bearing "
                "class",
            "HMT2_MAIN_CLASS_CONDITIONAL_ONLY":
                "materiality on CLASS_CONDITIONAL and not on "
                "PHYSICAL_END_TO_END",
            "HMT2_MAIN_NO_MATERIAL_EFFECT":
                "banks sound, materiality not reached",
            "HMT2_MAIN_SOURCE_BANK_FAILURE":
                "a held-out bank could not be built within tolerances",
            "HMT2_MAIN_IMPLEMENTATION_DEFECT":
                "a gate failed, a limit was exceeded, a commitment did not "
                "reproduce, or a committed bank hash did not match",
        },
        "exactly_one_disposition": True,
        "gate_failure_forces_defect_token": True,

        "gates": {
            "HMT2M_G1_pinned_numerical_environment": "structural",
            "HMT2M_G2_commitments_reproduce": "structural",
            "HMT2M_G3_disjoint_from_every_earlier_bank": 0,
            "HMT2M_G4_contrast_zero_spatial_mean": 1e-10,
            "HMT2M_G5_total_emissivity_nonnegative": 0.0,
            "HMT2M_G6_source_classification_stable": 0,
            "HMT2M_G7_adjoint": 1e-8,
            "HMT2M_G8_operator_truth_identity": 1e-9,
            "HMT2M_G9_stage_a_source_gates_passed": 0,
            "HMT2M_G10_bank_hashes_match_committed": 0,
            "HMT2M_G11_sealed_hyperparameters_used_unchanged": 0,
            "HMT2M_G12_both_targets_reported": 0,
            "HMT2M_G13_no_state_excluded_from_primary": 0,
            "HMT2M_G14_blended_not_forced_into_two_tracks": 0,
            "HMT2M_G15_all_required_companions_emitted": 0,
            "HMT2M_G16_estimator_scope": 0,
            "HMT2M_G17_endpoint_lineage_firewall": 0,
            "HMT2M_G18_declared_gate_coverage": "structural",
            "HMT2M_G19_resource_limits": "structural",
        },
        "resource_limits": {"wall_clock_seconds": 14400,
                            "on_exceeded": "HMT2_MAIN_IMPLEMENTATION_DEFECT"},
        "numerical_environment": s1["numerical_environment"],
        "after": "STOP. Item 12",
        "not_authorized": ["order leakage", "geometry mismatch", "VLBI",
                           "machine learning",
                           "a new pixel-movie reconstruction campaign"],
        "attestation": attest([S1, AMD]),
    }
    OUT.write_text(json.dumps(doc, indent=2, default=str) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}\n  sha256 {sha256_file(OUT)}")
    print(f"  {PER_FAMILY} x {len(fams)} = {PER_FAMILY * len(fams)} held-out "
          f"truths, {len(doc['gates'])} gates, {len(sealed)} sealed "
          f"hyperparameters")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
