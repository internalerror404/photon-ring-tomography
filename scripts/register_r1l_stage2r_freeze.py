#!/usr/bin/env python3
"""R1L_STAGE2R_VALIDATION_FREEZE_012 -- frozen before any new truth is generated.

REVIEWER_RULING_R1L_STAGE2_011 items 8 to 11.

Stage 2R-B differs from stage 2 in one decisive way: the truths are **exactly in
the class**. Stage 2R-A showed that analytic truths carry a structural
representation floor that puts the span criterion out of reach over most of the
age grid, and worse, that the floor makes the null estimator the best-scoring
one -- so the selection collapsed the direct arm, and at L448 every arm, and the
endpoint compared nothing against nothing.

Exact-in-class banks remove the floor by construction. The remaining error is
then reconstruction error and nothing else, which is the quantity the endpoint
was always meant to measure.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from phrt.attestation import attest
from phrt.config import load_registry, sha256_file
from phrt.sources.orbits import isco_radius, velocity_field_record

S2 = ROOT / "artifacts" / "configs" / "R1L_STAGE2_VALIDATION_ACTIVATION_010.json"
R1 = ROOT / "artifacts" / "configs" / "R1_MAIN_FREEZE.json"
G2RA = ROOT / "artifacts" / "gates" / "r1l_2ra_gates.json"
OUT = ROOT / "artifacts" / "configs" / "R1L_STAGE2R_VALIDATION_FREEZE_012.json"

BANKS = ["constant_flux_structural", "structure_balanced_050",
         "structure_balanced_080"]
FAMILIES = ["circular_single_hotspot", "circular_two_hotspots",
            "circular_crescent", "plunging_hotspot"]
SPLITS = ["selection", "pilot"]
PER_CELL = 8
DRAWS = 4
SEED = 20260906


def commitment(bank, family, split):
    return hashlib.sha256(json.dumps(
        {"bank": bank, "family": family, "split": split, "n": PER_CELL,
         "seed": SEED, "in_class": True}, sort_keys=True).encode()).hexdigest()


def main() -> int:
    reg = load_registry()
    r1 = json.loads(R1.read_text())
    s2 = json.loads(S2.read_text())
    g2ra = json.loads(G2RA.read_text())
    spin = float(r1["physical_model"]["spin"])
    cells = {f"{b}|{f}|{s}": commitment(b, f, s)
             for b in BANKS for f in FAMILIES for s in SPLITS}

    doc = {
        "schema": "phrt-r1l-stage2r-freeze/1",
        "id": "R1L_STAGE2R_VALIDATION_FREEZE_012",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "ruling": "REVIEWER_RULING_R1L_STAGE2_011 items 8 to 11",
        "status": "FROZEN_BEFORE_ANY_NEW_TRUTH_IS_GENERATED",
        "supersedes_for_the_endpoint": "R1L_STAGE2_VALIDATION_ACTIVATION_010",
        "authorizing_evidence": {
            "stage2r_a_disposition": g2ra["stop_token"],
            "why_exact_in_class": "stage 2R-A measured the structural "
                                  "representation floor age by age and found the "
                                  "epsilon = 0.25 criterion unreachable in more "
                                  "than 90 percent of age cells at L224 and more "
                                  "than 40 percent at L1056. It also showed the "
                                  "floor makes the null estimator score best, so "
                                  "the selection collapsed the direct arm at "
                                  "every class and every arm at L448. Both "
                                  "effects are properties of the floor, and an "
                                  "exact-in-class bank has none",
        },

        # ------------------------------------------------------------ item 9
        "source_banks": {
            "construction": "exact-in-class. Each family render is projected onto "
                            "the class by least squares on the evaluation grid, "
                            "the coefficients are kept, and the truth is the "
                            "synthesis of those coefficients. The truth is then "
                            "in the span of the class to machine precision and "
                            "the representation floor is zero by construction",
            "shaping_applies_after_projection": "the bank shaping -- constant "
                                                "flux, or the structure-balanced "
                                                "offset -- is applied to the "
                                                "projected field, and the result "
                                                "is re-projected, so the shaped "
                                                "truth is in class as well. Both "
                                                "operations are checked, not "
                                                "assumed",
            "banks": BANKS,
            "excluded": "baseline_one_positive. It is a secondary control and "
                        "may not carry the primary endpoint; stage 2 pooled it "
                        "in and that is recorded as "
                        "R1L_S2_PRIMARY_INCLUDED_SECONDARY_BANK",
            "target_structure_fraction": {"constant_flux_structural": None,
                                          "structure_balanced_050": 0.50,
                                          "structure_balanced_080": 0.80},
            "positivity_ceiling_rule": "unchanged from stage 2: a target above "
                                       "what a non-negative field of that shape "
                                       "allows is kept at the ceiling and "
                                       "flagged. Projection onto the class can "
                                       "also break strict positivity; the "
                                       "residual negativity is measured and "
                                       "reported rather than clipped away",
        },
        "classes": {"primary": "L1056", "controls": ["L448", "L224"],
                    "rule": "L1056 carries the endpoint. L448 and L224 are "
                            "reported as controls and cannot supply a pass"},
        "families": FAMILIES,
        "source_motion": {
            "circular": {"orbit_law": "Kerr prograde circular geodesic, "
                                      "1/(r^{3/2} + a)",
                         "r_centre_M": [isco_radius(spin), 29.989231533549642]},
            "plunging": {"orbit_law": "radial plunge on the ISCO's conserved E "
                                      "and L",
                         "r_centre_M": [1.8660254037844386, isco_radius(spin)]},
            "velocity_field_for_g3": velocity_field_record(spin),
        },
        "arms": ["DIRECT_PHYSICAL", "RESOLVED_PHYSICAL", "UNRESOLVED_IMAGE",
                 "TOTAL_FLUX"],
        "estimators": {"TSVD": "primary", "RIDGE_IDENTITY": "confirmatory",
                       "ML": "NOT_AUTHORIZED",
                       "grids": {"TSVD": s2["estimators"]["TSVD"]["grid"],
                                 "RIDGE_IDENTITY":
                                     s2["estimators"]["RIDGE_IDENTITY"]["grid"]}},
        "snr": {"primary": 100.0, "secondary": 1000.0,
                "rule": "no other SNR may carry a claim"},
        "counts": {"banks": BANKS, "families": FAMILIES, "splits": SPLITS,
                   "truths_per_bank_family_split": PER_CELL,
                   "n_cells": len(cells),
                   "n_truths": len(cells) * PER_CELL,
                   "noise_draws_per_truth": DRAWS},
        "seeds": {"bank_seed": SEED, "noise_seed": 20260907,
                  "bootstrap_seed": 20260908, "null_pair_seed": 20260909,
                  "subsample_seed": int(r1["observation"]["subsample_seed"])},
        "split_commitments": cells,

        # ----------------------------------------------------------- item 10
        "materiality": {
            "median_paired_relative_reduction": 0.10,
            "bootstrap_lower_bound": 0.05,
            "min_families_improved": 3,
            "positive_in_every_primary_bank": True,
            "null_controls_pass": True,
            "estimator_confirmation": "TSVD and ridge must both meet the "
                                      "standard on the same class",
            "statistic": "(E_old_structure(direct) - E_old_structure(arm)) / "
                         "E_old_structure(direct), per truth, aggregated with "
                         "equal weight over bank-family cells",
            "bootstrap": {"kind": "paired truth-cluster", "unit": "truth",
                          "n_resamples": 10000, "level": 0.95,
                          "seed": 20260908},
        },

        # ----------------------------------------------------------- item 11
        "stable_structure_span": {
            "exact_in_class_only": True,
            "epsilon": 0.25, "quantile": 0.95,
            "definition": "T_stable_anchor = sup{T >= a_anchor : "
                          "Pr[sup_{a_anchor <= a <= T} E_structure(a) <= "
                          "epsilon] >= q}, supremum inside the probability, per "
                          "truth",
            "a_anchor_M": 0.0,
            "age_grid_step_M": 2.0,
            "probe_half_width_M": 3.0,
            "threshold_M": 8.0,
            "statistic": "L_stable_structure(resolved) - "
                         "L_stable_structure(direct) >= 8 M at the registered "
                         "SNR",
            "registered_snr": 100.0,
        },

        "selection": {
            "rule": "lexicographic on the selection split, minimizing old-band "
                    "structure error at SNR0 = 100",
            "degenerate_selection_diagnostic": "the selected hyperparameter is "
                                               "reported for every (class, arm, "
                                               "estimator) and a selection at "
                                               "the maximal-regularization end "
                                               "of its grid is flagged. Stage 2 "
                                               "collapsed to that end without "
                                               "anyone noticing, and a flag is "
                                               "cheaper than rediscovering it",
            "no_retuning": "no hyperparameter may be revisited after any pilot "
                           "truth is scored",
        },
        "gates": {
            "R1L_2RB_G1_pinned_numerical_environment": "structural",
            "R1L_2RB_G2_split_commitments_reproduce": "structural",
            "R1L_2RB_G3_split_disjointness": "structural",
            "R1L_2RB_G4_truths_are_exactly_in_class": 1e-10,
            "R1L_2RB_G5_representation_floor_is_zero": 1e-10,
            "R1L_2RB_G6_secondary_bank_absent": "structural",
            "R1L_2RB_G7_adjoint": 1e-8,
            "R1L_2RB_G8_analytic_shaping_matches_grid_truth": 1e-9,
            "R1L_2RB_G9_null_controls": 0.05,
            "R1L_2RB_G10_source_balance_within_tolerance": "structural",
            "R1L_2RB_G11_resource_limits": "structural",
        },
        "resource_limits": {"wall_clock_seconds": 7200, "peak_rss_mb": 12000,
                            "on_exceeded": "R1L_STAGE2R_B_IMPLEMENTATION_DEFECT",
                            "no_silent_reduction": True},
        "numerical_environment": {"pinned": True,
                                  "variables": s2["numerical_environment"]["variables"]},
        "dispositions": {
            "R1L_STAGE2R_B_MATERIAL_RESOLVED_AND_UNRESOLVED":
                "materiality met for resolved and unresolved at L1056",
            "R1L_STAGE2R_B_MATERIAL_RESOLVED_ONLY":
                "materiality met for resolved at L1056, not unresolved",
            "R1L_STAGE2R_B_NO_MATERIAL_EFFECT":
                "banks sound, materiality not met. A reportable result",
            "R1L_STAGE2R_B_SOURCE_BANK_FAILURE":
                "an exact-in-class bank could not be built within tolerance",
            "R1L_STAGE2R_B_IMPLEMENTATION_DEFECT":
                "a gate failed, a limit was exceeded, or a commitment did not "
                "reproduce",
            "exactly_one": True,
        },
        "scope": {
            "authorized": ["R1L_STAGE_2R_B"],
            "not_authorized": ["sealed main", "geometry mismatch",
                               "order leakage", "VLBI", "ML"],
            "stop_after": "R1L_STAGE_2R_B",
            "forbidden_language": "an exact-in-class result is an upper bound on "
                                  "what the operator can do for this class. It "
                                  "is not a claim about real source histories, "
                                  "which are not in anyone's basis",
        },
        "provenance": {"stage2_freeze_sha256": sha256_file(S2),
                       "r1_freeze_sha256": sha256_file(R1),
                       "registry_sha256": reg.sha256,
                       "raymap_sha256": r1["physical_model"]["raymap_sha256"]},
    }
    doc["attestation"] = attest([S2, R1])
    OUT.write_text(json.dumps(doc, indent=2) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}")
    print(f"  sha256 {sha256_file(OUT)}")
    print(f"  {len(cells)} cells, {len(cells) * PER_CELL} truths, "
          f"{DRAWS} draws, primary L1056")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
