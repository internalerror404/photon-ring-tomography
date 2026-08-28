#!/usr/bin/env python3
"""HMT1_SEALED_HELD_OUT_MAIN_FREEZE_V2.

Items 6, 7 and 8 of REVIEWER_RULING_HMT1_VALIDATION_015. Registered and
committed before any held-out truth is generated and before any operator is
applied to one.

The sealed hyperparameters are read out of the corrected validation's own
selection table rather than retyped, so the freeze cannot disagree with the run
that produced them.
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

VFZ = ROOT / "artifacts" / "configs" / "HMT1_VALIDATION_FREEZE_V0.json"
AMD = ROOT / "artifacts" / "configs" / "HMT1_VALIDATION_RECORD_AMENDMENT_015.json"
SEL = ROOT / "artifacts" / "tables" / "hmt1_selection.parquet"
OUT = ROOT / "artifacts" / "configs" / "HMT1_SEALED_HELD_OUT_MAIN_FREEZE_V2.json"

# Item 9: exactly one new bank seed. Two banks are already retired -- 20260915
# for the smoke-test peek, 20260917 for the partial endpoint exposure through
# hmt1_main_noiseless_control -- and both are listed so stage A can refuse to
# redraw either. There is no seed search here and no redraw-until-pass loop:
# this seed is fixed now, and whatever bank it produces is the bank.
SEED = 20260921
RETIRED_SEEDS = (20260915, 20260917)
N_PER_FAMILY = 16
N_NOISE_DRAWS = 8
NOISELESS_DRAWS = 1


def commitment(family, i_max, seed):
    """Seed commitment for the held-out split.

    The payload carries split='sealed_main_heldout', which is a string no
    validation commitment used, so no validation truth seed can recur here by
    construction rather than by checking afterwards. It is checked afterwards
    as well, by HMT1M_G3.
    """
    payload = json.dumps({"family": family, "split": "sealed_main_heldout",
                          "n": i_max, "seed": seed, "model": "contrast"},
                         sort_keys=True).encode()
    return hashlib.sha256(payload).hexdigest()


def main() -> int:
    vfz = json.loads(VFZ.read_text())
    sel = pd.read_parquet(SEL)

    sealed = {}
    for r in sel.itertuples():
        sealed[f"{r.regime}|{r.arm}|{r.estimator}"] = {
            "hyperparameter": float(r.selected_hyperparameter),
            "validation_selection_error": float(r.selection_error),
            "grid_size": int(r.n_grid),
            "at_max_regularization_end": bool(r.at_max_regularization_end),
        }
    assert len(sealed) == 24, len(sealed)
    assert not any(v["at_max_regularization_end"] for v in sealed.values())

    fams = list(vfz["feature_families"]["declared"])
    regimes = list(vfz["background_regimes"]["declared"])

    doc = {
        "schema": "phrt-hmt1-sealed-main-freeze/1",
        "id": "HMT1_SEALED_HELD_OUT_MAIN_FREEZE_V2",
        "supersedes": "HMT1_SEALED_HELD_OUT_MAIN_FREEZE_V1",
        "retired_bank_seeds": list(RETIRED_SEEDS),
        "retirement_records": ["HMT1_SEALED_MAIN_BANK_V1_RETIREMENT_016",
                               "HMT1_SEALED_MAIN_CORRECTION_AND_RETIREMENT_017"],
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "ruling": "REVIEWER_RULING_HMT1_MAIN_017",
        "status": "SEALED_BEFORE_ANY_HELD_OUT_TRUTH_OR_OPERATOR_EVALUATION",
        "branch": "research/hmt1_historical_feature_contrast_tomography_v0",

        "inherits": {
            "validation_freeze": "HMT_1_HISTORICAL_FEATURE_AND_CONTRAST_TOMOGRAPHY_V0",
            "validation_freeze_sha256": sha256_file(VFZ),
            "record_amendment": "HMT1_VALIDATION_RECORD_AMENDMENT_015",
            "record_amendment_sha256": sha256_file(AMD),
            "unchanged": "geometry, source model, contrast construction, "
                         "reconstruction class, arms, estimators, feature "
                         "extraction, normalisation denominators, aggregate, "
                         "endpoints, materiality, tolerances and family "
                         "agreement are inherited verbatim from the "
                         "validation freeze. This freeze changes the truths "
                         "and nothing else",
        },

        "design": {
            "truths_per_family": N_PER_FAMILY,
            "families": fams,
            "n_families": len(fams),
            "n_truths": N_PER_FAMILY * len(fams),
            "regimes": regimes,
            "regime_reading": "each held-out truth is evaluated under all "
                              "three background regimes, so the regime "
                              "comparison is paired on the same truth. The "
                              "ruling says '16 fresh truths per family, 6 "
                              "families, 3 background regimes', which reads "
                              "as 96 truths seen three ways rather than 288 "
                              "separate draws. Recording the reading because "
                              "the other one is available and would change "
                              "the count",
            "noise_draws_per_truth": N_NOISE_DRAWS,
            "noiseless_control_draws": NOISELESS_DRAWS,
            "noiseless_control_role": "reported alongside the noisy draws and "
                                      "gated by HMT1M_G15. It is not part of "
                                      "the endpoint statistic: an endpoint "
                                      "averaged over a draw that has no noise "
                                      "would report a number no instrument "
                                      "can produce",
            "snr_primary": vfz["snr"]["primary"],
            "snr_secondary": vfz["snr"]["secondary"],
            "arms": list(vfz["arms"]),
            "estimators_authorized": ["TSVD", "RIDGE_IDENTITY"],
            "estimators_withdrawn": {
                "NONNEGATIVE_CONSTRAINED": "WITHDRAWN_UNSELECTED",
            },
            "estimators_not_authorized": {"ML": "NOT_AUTHORIZED"},
            "estimator_scope_note":
                "item 12. NONNEGATIVE_CONSTRAINED was declared in the "
                "validation freeze as a control and never implemented, so it "
                "has no selected hyperparameter. Selecting one now is the "
                "retuning item 8 of ruling 015 forbids, so it is withdrawn as "
                "unselected rather than run. ML was never authorized. "
                "HMT1M_G19 checks that the estimators actually run are exactly "
                "the authorized set and that no withdrawn or unauthorized one "
                "appears",
        },

        "regime_roles": {
            "estimated_from_data": "CLAIM_BEARING. The reported result is the "
                                   "one obtained here",
            "oracle_known": "confirmatory only",
            "joint_inversion": "confirmatory only",
            "rule": "a result that exists only under a confirmatory regime is "
                    "reported as background-assisted and does not pass",
        },

        "sealed_hyperparameters": {
            "values": sealed,
            "provenance": "selected on the validation selection split by the "
                          "corrected scorer, canonical run "
                          "HMT1_20260827T224512Z_2ba66f02",
            "all_interior": "no selected value sits at either end of its "
                            "grid, which is what HMT1_G12 checked and passed "
                            "in the validation",
            "rule": "used verbatim. The sealed main performs no selection "
                    "sweep at all -- there is no code path in the main runner "
                    "that evaluates a second hyperparameter",
        },

        "prohibited_in_the_sealed_main": [
            "hyperparameter selection or retuning of any kind",
            "changing an estimator or adding one",
            "changing the feature list scored for any family",
            "changing any normalisation denominator",
            "changing any tolerance, epsilon, quantile or materiality bar",
            "excluding a family, a truth, an arm or a regime after seeing it",
            "adding a source family or an off-manifold control to the endpoint",
            "re-running with a different seed and reporting the better run",
        ],

        "endpoints": {
            "primary": vfz["primary_endpoints"],
            "secondary": vfz["secondary_endpoints"],
            "note": "inherited verbatim. Reproduced here so the sealed "
                    "document is self-contained and a later edit to the "
                    "validation freeze cannot silently move this endpoint",
        },
        "pass_criteria": {
            **vfz["pass_criteria"],
            "claim_bearing_regime": "estimated_from_data",
        },

        "dispositions": {
            "HMT1_MAIN_FEATURE_RECOVERY_PASS":
                "every criterion met in the claim-bearing regime",
            "HMT1_MAIN_BACKGROUND_ASSISTED_ONLY":
                "criteria met only under a confirmatory regime",
            "HMT1_MAIN_MATERIAL_ERROR_REDUCTION_NO_STABLE_INTERVAL":
                "material feature-error reduction with no positive stable "
                "feature interval",
            "HMT1_MAIN_NO_MATERIAL_EFFECT":
                "banks sound, materiality not met. A reportable result",
            "HMT1_MAIN_SOURCE_BANK_FAILURE":
                "a held-out bank could not be built within the contrast-model "
                "tolerances",
            "HMT1_MAIN_IMPLEMENTATION_DEFECT":
                "a gate failed, a limit was exceeded, a commitment did not "
                "reproduce, or a committed bank hash did not match",
        },
        "exactly_one_disposition": True,
        "gate_failure_forces_defect_token": True,

        "two_stage_execution": {
            "rule": "item 9. All final source and feature hashes are "
                    "committed before any operator is applied to a held-out "
                    "truth",
            "stage_a": {
                "script": "scripts/run_hmt1_main_bank.py",
                "does": "draws the held-out truths, extracts their features, "
                        "and writes per-truth sha256 of the emissivity field "
                        "and of the extracted feature history",
                "output": "artifacts/provenance/HMT1_MAIN_BANK_HASHES.json",
                "touches_no_operator": True,
            },
            "stage_b": {
                "script": "scripts/run_hmt1_main.py",
                "does": "rebuilds the same bank, verifies every hash against "
                        "the committed file, and only then applies the "
                        "operator",
                "on_mismatch": "HMT1_MAIN_IMPLEMENTATION_DEFECT",
            },
        },

        "seeds": {
            "bank_seed": SEED,
            "noise_seed": SEED + 2,
            "bootstrap_seed": SEED + 1,
            "null_pair_seed": SEED + 3,
            "subsample_seed": int(vfz["seeds"]["subsample_seed"]),
            "freshness": "different values from the validation seeds, and the "
                         "seed commitment payload carries "
                         "split='sealed_main_heldout', a string no validation "
                         "commitment used. Disjointness is therefore by "
                         "construction and is checked as well",
        },
        "commitments": {f: commitment(f, N_PER_FAMILY, SEED) for f in fams},

        "gates": {
            # decided in stage A, from the source alone, before any operator
            # is imported. Item 10
            "HMT1M_G1_pinned_numerical_environment": "structural",
            "HMT1M_G2_held_out_commitment_reproduces": "structural",
            "HMT1M_G3_disjoint_from_validation_and_retired_truths": 0,
            "HMT1M_G4_contrast_zero_spatial_mean": 1e-10,
            "HMT1M_G4b_azimuthal_zero_mean": 1e-10,
            "HMT1M_G5_total_emissivity_nonnegative": 0.0,
            "HMT1M_G6_background_strictly_positive": 1e-6,
            "HMT1M_G10_feature_extraction_deterministic": 1e-9,
            "HMT1M_G10c_truth_extraction_matches_independent_windowed_reference": 1.0,
            "HMT1M_G17_off_manifold_bank_built": "structural",
            # decided in stage B, after the operator
            "HMT1M_G7_adjoint": 1e-8,
            "HMT1M_G8_operator_truth_identity": 1e-9,
            "HMT1M_G9_null_controls": 0.05,
            "HMT1M_G11_off_manifold_excluded_from_endpoints": 0,
            "HMT1M_G12_sealed_hyperparameters_used_unchanged": 0,
            "HMT1M_G13_declared_gate_coverage": "structural",
            "HMT1M_G14_resource_limits": "structural",
            "HMT1M_G15_noise_path_is_live": 0,
            "HMT1M_G16_bank_hashes_match_committed": 0,
            "HMT1M_G18_stage_a_source_gates_passed": 0,
            "HMT1M_G19_estimator_scope": 0,
            "HMT1M_G20_endpoint_lineage_firewall": 0,
        },
        "gate_stages": {
            "stage_a": ["HMT1M_G1_pinned_numerical_environment",
                        "HMT1M_G2_held_out_commitment_reproduces",
                        "HMT1M_G3_disjoint_from_validation_and_retired_truths",
                        "HMT1M_G4_contrast_zero_spatial_mean",
                        "HMT1M_G4b_azimuthal_zero_mean",
                        "HMT1M_G5_total_emissivity_nonnegative",
                        "HMT1M_G6_background_strictly_positive",
                        "HMT1M_G10_feature_extraction_deterministic",
                        "HMT1M_G10c_truth_extraction_matches_independent_windowed_reference",
                        "HMT1M_G17_off_manifold_bank_built"],
            "rule": "every source-side gate is decided before an operator is "
                    "imported, and stage B refuses to import one unless all of "
                    "them passed",
        },
        "retired_gate": {
            "HMT1M_G10b_truth_extraction_recovers_generative_parameters":
                "FAIL / RETIRED_RAW_TRAJECTORY_PROXY_INVALID_FOR_WINDOWED_"
                "FEATURE. Preserved in the correction record, not re-run",
        },
        "gate_notes": {
            "HMT1M_G3_disjoint_from_validation_and_retired_truths":
                "held-out seeds that also appear in the validation bank or in "
                "any bank this freeze has retired. Must be zero, so a retired "
                "bank cannot be redrawn under a new name",
            "HMT1M_G10c_truth_extraction_matches_independent_windowed_reference":
                "one evaluation-grid cell, the same frozen threshold the "
                "retired G10b carried. The reference windows the analytic "
                "field first and then finds its maxima, which is the question "
                "the extractor answers; the retired proxy compared against the "
                "instantaneous generative centre, which a feature moving "
                "inside the window does not occupy. Validated on 396 truths "
                "before this freeze: the complete validation bank, three "
                "scratch banks and the analytic canaries in the test suite",
            "HMT1M_G18_stage_a_source_gates_passed":
                "stage B emits this after confirming stage A's gate file shows "
                "no failure. It is a record of the check, not the check "
                "itself: the check happens before the operator imports",
            "HMT1M_G19_estimator_scope":
                "symmetric difference between the estimators actually run and "
                "the authorized set, plus any withdrawn estimator that ran. "
                "Must be zero",
            "HMT1M_G20_endpoint_lineage_firewall":
                "blocked tables that reached disk anyway. Must be zero. The "
                "firewall screens column lineage rather than filenames, "
                "because the table that leaked last time was named for a "
                "control and carried per-arm medians of the old-band feature "
                "error",
        },
        "resource_limits": dict(vfz["resource_limits"],
                                on_exceeded="HMT1_MAIN_IMPLEMENTATION_DEFECT"),
        "numerical_environment": vfz["numerical_environment"],

        "scope": {
            "authorized": "the HMT-1 sealed held-out main, and nothing else",
            "not_authorized": ["order leakage", "geometry mismatch", "VLBI",
                               "machine learning",
                               "a new pixel-movie reconstruction campaign"],
            "after": "STOP",
        },
        "attestation": attest([VFZ, AMD]),
    }
    OUT.write_text(json.dumps(doc, indent=2, default=str) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}\n  sha256 {sha256_file(OUT)}")
    print(f"  {N_PER_FAMILY} x {len(fams)} = {N_PER_FAMILY * len(fams)} held-out "
          f"truths, {len(regimes)} regimes, {N_NOISE_DRAWS} noisy draws "
          f"+ {NOISELESS_DRAWS} noiseless")
    print(f"  {len(sealed)} sealed hyperparameters, {len(doc['gates'])} gates")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
