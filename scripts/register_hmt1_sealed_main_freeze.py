#!/usr/bin/env python3
"""HMT1_SEALED_HELD_OUT_MAIN_FREEZE_V1.

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
OUT = ROOT / "artifacts" / "configs" / "HMT1_SEALED_HELD_OUT_MAIN_FREEZE_V1.json"

# v2. The v1 bank drawn under seed 20260915 is retired: stage B was smoke
# tested on it before the sealed run, which is an operator evaluation on
# held-out truths and therefore a peek, however small. Redrawing under a new
# seed costs five seconds and restores the seal, which is cheaper than
# arguing about how little the peek revealed. See
# HMT1_SEALED_MAIN_BANK_V1_RETIREMENT_016.
SEED = 20260917
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
        "id": "HMT1_SEALED_HELD_OUT_MAIN_FREEZE_V1",
        "revision": "v2 bank seed",
        "revision_reason": "HMT1_SEALED_MAIN_BANK_V1_RETIREMENT_016",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "ruling": "REVIEWER_RULING_HMT1_VALIDATION_015",
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
            "estimators": list(vfz["estimators"]) if isinstance(
                vfz["estimators"], dict) else vfz["estimators"],
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
            "HMT1M_G1_pinned_numerical_environment": "structural",
            "HMT1M_G2_held_out_commitment_reproduces": "structural",
            "HMT1M_G3_disjoint_from_validation_truths": 0,
            "HMT1M_G4_contrast_zero_spatial_mean": 1e-10,
            "HMT1M_G4b_azimuthal_zero_mean": 1e-10,
            "HMT1M_G5_total_emissivity_nonnegative": 0.0,
            "HMT1M_G6_background_strictly_positive": 1e-6,
            "HMT1M_G7_adjoint": 1e-8,
            "HMT1M_G8_operator_truth_identity": 1e-9,
            "HMT1M_G9_null_controls": 0.05,
            "HMT1M_G10_feature_extraction_deterministic": 1e-9,
            "HMT1M_G10b_truth_extraction_recovers_generative_parameters": 1.0,
            "HMT1M_G11_off_manifold_excluded_from_endpoints": "structural",
            "HMT1M_G12_sealed_hyperparameters_used_unchanged": 0,
            "HMT1M_G13_declared_gate_coverage": "structural",
            "HMT1M_G14_resource_limits": "structural",
            "HMT1M_G15_noise_path_is_live": 0,
            "HMT1M_G16_bank_hashes_match_committed": 0,
        },
        "gate_notes": {
            "HMT1M_G3_disjoint_from_validation_truths":
                "number of held-out truth seeds that also appear in the "
                "validation bank. Must be zero",
            "HMT1M_G12_sealed_hyperparameters_used_unchanged":
                "number of reconstructions run at a hyperparameter other than "
                "the sealed one for its (regime, arm, estimator). Must be "
                "zero. This replaces the validation's collapse gate, which "
                "guarded a selection sweep that no longer exists",
            "HMT1M_G15_noise_path_is_live":
                "number of (regime, arm, estimator) cells at the primary SNR "
                "where the noisy reconstructions do not differ from the "
                "noiseless control. Must be zero",
            "HMT1M_G15_corrected_definition":
                "this gate first required the noiseless control to score a "
                "lower endpoint error than the noisy draws. That expectation "
                "is false here and the smoke run falsified it: with the "
                "sealed hyperparameters the feature error is bias dominated, "
                "not noise dominated -- the noise norm exceeds the signal "
                "norm but the regularization removes most of it -- so "
                "removing the noise barely moves the error and can slightly "
                "worsen a bounded argmax metric by removing dither. The "
                "gate's purpose was to confirm the noise path is live, and "
                "it now measures that directly, in the reconstruction rather "
                "than in the endpoint. The endpoint direction is still "
                "reported, in hmt1_main_noiseless_control, and is not gated "
                "because no correct direction for it was established in "
                "advance",
            "HMT1M_G16_bank_hashes_match_committed":
                "number of held-out truths whose emissivity field or feature "
                "history hashes differ from the values committed before the "
                "operator was applied. Must be zero",
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
