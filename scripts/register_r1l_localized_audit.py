#!/usr/bin/env python3
"""Preregister R1L -- localized structural-history reconstruction audit.

Written before any localized operator is built, any structural bank is drawn or
any error is computed. Everything the ruling requires to be declared in advance
-- support widths, structure fractions, the orbit law, the endpoint, the arms,
the age grid and the stop rule -- is fixed here and hashed.

R1L exists to test the two criticisms that would most damage Paper I's
reconstruction claim if they were right:

  baseline domination
      the R1 primary was baseline-inclusive, and the level component carried
      98.4% of the truth norm. A metric dominated by a scalar per age slice can
      report a deep reconstruction while recovering no morphology at all.

  global temporal extrapolation
      C224's temporal factor is eight global DCT modes. Every coefficient is
      supported on the whole history, so a fit constrained where rays land also
      determines the field where none do. Depth measured this way may be
      cosine extrapolation rather than measurement.

Neither is answered by rerunning R1. Both are answered by changing exactly one
thing at a time: the temporal basis becomes compact, and the metric becomes
structural.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from phrt.attestation import attest
from phrt.config import load_registry, sha256_file
from phrt.sources.localized_basis import (LocalizedBasis, temporal_support_widths,
                                          temporal_supports)
from phrt.sources.orbits import (circular_radius_bounds, isco_radius,
                                 velocity_field_record)

R1_FREEZE = ROOT / "artifacts" / "configs" / "R1_MAIN_FREEZE.json"
E3C_FREEZE = ROOT / "artifacts" / "configs" / "E3C_OPERATOR_GRID_FREEZE.json"
OUT = ROOT / "artifacts" / "configs" / "R1L_LOCALIZED_AUDIT_FREEZE.json"

CLASSES = {"L224":  dict(n_radial=4, n_azimuthal=7,  n_temporal=8),
           "L448":  dict(n_radial=4, n_azimuthal=7,  n_temporal=16),
           "L1056": dict(n_radial=6, n_azimuthal=11, n_temporal=16)}
PARENT = {"L448": "L224", "L1056": "L448"}
AGE_STEP_M = 2.0
STRUCTURE_FRACTIONS = [0.5, 0.8]


def main() -> int:
    t0 = time.time()
    reg = load_registry()
    r1 = json.loads(R1_FREEZE.read_text())
    spin = float(r1["physical_model"]["spin"])
    t_lo = float(r1["observation"]["basis_t_min"])
    t_hi = float(r1["observation"]["basis_t_max"])
    r_in = float(r1["physical_model"]["r_inner_M"])
    r_out = float(r1["physical_model"]["r_outer_M"])
    r_isco = isco_radius(spin)
    old_r_lo = float(r1["source_families"]["families"]
                     ["single_orbiting_hotspot"]["r_centre_M"][0])

    classes = {}
    for name, cfg in CLASSES.items():
        b = LocalizedBasis(r_in, r_out, t_lo, t_hi, **cfg)
        widths = temporal_support_widths(t_lo, t_hi, cfg["n_temporal"])
        classes[name] = {
            **cfg, "dimension": b.dimension,
            "factorization": f"{cfg['n_radial']} cubic B-splines in log r x "
                             f"{cfg['n_azimuthal']} real Fourier modes x "
                             f"{cfg['n_temporal']} compact temporal hats",
            "temporal_family": "degree-one B-spline (hat) on the dyadic node set",
            "temporal_degree": 1,
            "temporal_node_spacing_M": (t_hi - t_lo) / cfg["n_temporal"],
            "temporal_support_width_M": {
                "boundary_function_at_t_min": float(widths[0]),
                "all_other_functions": float(widths[1]),
            },
            "temporal_supports_M": [[float(a), float(c)] for a, c in
                                    temporal_supports(t_lo, t_hi, cfg["n_temporal"])],
            "fraction_of_history_each_temporal_function_occupies":
                float(widths[1] / (t_hi - t_lo)),
            "mirrors_e3d_class": {"L224": "C224", "L448": "C448_T",
                                  "L1056": "C1056_ST"}[name],
        }

    doc = {
        "schema": "phrt-r1l-localized-audit-freeze/1",
        "experiment_id": "R1L_LOCALIZED_STRUCTURAL_AUDIT",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "ruling": "REVIEWER_RECOMMENDATION_R1L",
        "status": "FROZEN_BEFORE_ANY_LOCALIZED_OPERATOR_IS_BUILT",
        "purpose": {
            "tests": ["baseline domination", "global temporal extrapolation"],
            "precedes": ["geometry mismatch", "VLBI"],
            "one_variable_at_a_time": "A changes the temporal basis and holds the "
                                      "metric; B changes the metric and holds the "
                                      "basis; the audit reports both separately "
                                      "before any combined claim is made",
        },
        "provenance": {
            "r1_freeze_sha256": sha256_file(R1_FREEZE),
            "r1_execution_commit": "5f557fb606b76a95093cbf8e98d89d6f1dab9664",
            "r1_artifact_commit": "93e713c2639ffc2650b019003b58a4b893a53bf8",
            "r1_record_amendment": "R1_RECORD_AMENDMENT_006",
            "e3c_freeze_sha256": sha256_file(E3C_FREEZE),
            "registry_sha256": reg.sha256,
            "raymap_sha256": r1["physical_model"]["raymap_sha256"],
            "geometry": r1["physical_model"]["geometry"],
            "inherits": "the ray maps, the observation model, the noise model and "
                        "the four observation arms are taken from the R1 freeze "
                        "unchanged, so a difference in the result is attributable "
                        "to the basis and the metric rather than to the detector",
        },

        # ---------------------------------------------------------------- A
        "A_localized_temporal_bases": {
            "why": "a global DCT coefficient fitted where rays land also "
                   "determines the field where none land, so measured depth and "
                   "cosine extrapolation are not separable in C224. A compactly "
                   "supported coefficient whose support holds no ray is an exact "
                   "null direction instead, which is a fact about the operator "
                   "rather than a confidence about the fit",
            "classes": classes,
            "nesting_chain": ["L224", "L448", "L1056"],
            "parent_of": PARENT,
            "nesting_is_exact_by_construction":
                "the coarse dyadic node set is the even half of the fine one, so "
                "a function piecewise linear on the coarse nodes is piecewise "
                "linear on the fine nodes. Gate R1L_G2 requires literal zero to "
                "1e-12, not a small residual",
            "degree_choice": "degree one is the highest polynomial degree whose "
                             "dyadic B-spline family on a bounded interval has "
                             "dimension exactly 2^j and nests exactly. Degree two "
                             "and above need 2^j + p functions to cover the "
                             "boundary, which would break the dimension mirror "
                             "against E3D. The mirror is what makes the localized "
                             "result comparable to the global one",
            "boundary_condition": "the space vanishes at t_max, which lies in the "
                                  "unreachable pad above max(t_obs) - min(delay); "
                                  "no ray samples the field there",
            "declared_before_evaluation": True,
            "questions": [
                "does the direct image have exact old-epoch null directions",
                "do orders 1 and 2 genuinely remove some of them",
                "does the resolved advantage survive without global-cosine "
                "extrapolation",
                "how does local support change historical rank, conditioning and "
                "stable reconstruction",
            ],
        },

        # ---------------------------------------------------------------- B
        "B_structure_first_source_banks": {
            "why": "the R1 primary was baseline-inclusive and the level component "
                   "carried 98.4% of the truth norm, so a structure fraction of "
                   "0.126 was doing all the morphological work. Recovering a "
                   "scalar per age slice is a weaker claim than recovering a "
                   "history and must not be reported as the same thing",
            "primary_banks": {
                "constant_flux_structural": {
                    "construction": "every age slice is renormalized so its "
                                    "spatial mean is a fixed constant, removing "
                                    "total-level variation while retaining moving "
                                    "morphology",
                    "level_component": "constant in time by construction, so the "
                                       "level channel carries no information and "
                                       "cannot inflate the endpoint",
                    "role": "primary",
                },
                "structure_balanced_positive": {
                    "construction": "j(r, phi, t) = b(t) + s(r, phi, t) with the "
                                    "structure fraction fixed before sampling",
                    "structure_fraction_definition":
                        "||P_structure j|| / ||j||, with P_structure the "
                        "complement of the level projector of "
                        "REVIEWER_RULING_R0C_005",
                    "structure_fraction_grid": STRUCTURE_FRACTIONS,
                    "baseline_rule": "b(t) is the minimum baseline that keeps the "
                                     "rendered movie non-negative at the target "
                                     "structure fraction; it is not free to grow "
                                     "to dominate the metric",
                    "role": "primary",
                },
            },
            "secondary_bank": {
                "baseline_one_positive": {
                    "construction": "the R1 families unchanged",
                    "measured_structure_fraction_in_r1": 0.126,
                    "role": "secondary replication only. It may not carry the "
                            "primary endpoint",
                },
            },
            "declared_before_sampling": True,
        },

        # ---------------------------------------------------------------- C
        "C_physically_consistent_source_motion": {
            "defect_being_corrected": {
                "orbit_law": "the R0/R1 families advected features at the "
                             "Newtonian rate Omega = r^{-3/2}, while the ray maps "
                             "compute g from the Kerr fluid",
                "isco_violation": "circular hotspot centres were drawn from "
                                  f"r = {old_r_lo} M, inside the prograde ISCO at "
                                  f"{r_isco:.6f} M, so circular features were "
                                  "placed where no circular orbit exists",
                "why_it_survived": "the operator is linear in j and does not care "
                                   "whether j is physical, so no linear-algebra "
                                   "gate could catch it",
                "affects_r1_result": "not retroactively. The R1 banks are sealed "
                                     "and reported under the old law; R1L "
                                     "supersedes the family definition going "
                                     "forward rather than editing the record",
            },
            "circular_family": {
                "orbit_law": "Kerr prograde circular geodesic, "
                             "Omega = 1 / (r^{3/2} + a)",
                "r_centre_M": list(circular_radius_bounds(spin, 29.989231533549642)),
                "restriction": "centres strictly outside the ISCO",
                "isco_radius_M": r_isco,
            },
            "plunging_family": {
                "role": "separate family, not mixed into the circular one",
                "orbit_law": "radial plunge on the ISCO's conserved E and L, "
                             "Omega = u^phi / u^t",
                "r_centre_M": [float(1.0 + np.sqrt(1.0 - spin ** 2)), r_isco],
                "why_separate": "the plunge is not a faster circular orbit: frame "
                                "dragging locks Omega to a / (2 r_+) at the "
                                "horizon, so the rate turns over rather than "
                                "diverging. Averaging it with circular material "
                                "would describe motion that does not occur",
            },
            "velocity_field_for_g3": velocity_field_record(spin),
        },

        # ---------------------------------------------------------------- D
        "D_primary_endpoint": {
            "statistic": "delta_E_old_structure = E_old_structure(direct) "
                         "- E_old_structure(resolved)",
            "not": "baseline-inclusive stable span, which was the R1 primary and "
                   "is retired as a primary here",
            "bank": "sealed held-out structural bank",
            "reference_snr": 100.0,
            "old_band": "the old third of the reachable age range, as already "
                        "defined by the R1 band split",
            "success_requires": [
                "a paired truth-cluster bootstrap interval excluding zero",
                "lower old-band structure error in at least three of the four "
                "fitting families",
                "confirmation by both TSVD and ridge",
                "null-pair behaviour remaining likelihood-consistent",
            ],
            "coprimary_or_secondary": {
                "statistic": "delta_L_stable_structure",
                "paper_grade_positive": "delta_L_stable_structure >= 8 M at a "
                                        "prespecified moderate SNR_0, preferably "
                                        "100 and no higher than 1000",
                "prespecified_snr0": 100.0,
                "permitted_snr0_ceiling": 1000.0,
                "if_only_at_30000": "retained and reported as a negative "
                                    "practicality result, not as a positive "
                                    "structural result",
            },
            "estimators": {"primary": "TSVD", "confirmatory": "RIDGE_IDENTITY",
                           "ML": "NOT_AUTHORIZED"},
            "declared_before_scoring": True,
        },

        # ---------------------------------------------------------------- E
        "E_observation_arms": {
            "arms": ["DIRECT_PHYSICAL", "RESOLVED_PHYSICAL", "UNRESOLVED_IMAGE",
                     "TOTAL_FLUX"],
            "why_all_four": "a resolved-only success is an ideal "
                            "channel-separation result and nothing more. A "
                            "structural gain that survives UNRESOLVED_IMAGE is "
                            "the one that bears on observation, so the "
                            "unresolved arm is reported at the same standing as "
                            "the resolved one rather than as a diagnostic",
            "diagnostic_arms": ["DELAY_ONLY", "SPATIAL_ONLY",
                                "EQUALIZED_ORDER_SENSITIVITY", "PAIRING_DESTROYED"],
            "noise_coupling": "unchanged from R1: one resolved draw per "
                              "(truth, SNR, draw), the other arms are declared "
                              "linear readouts of it",
        },

        # ---------------------------------------------------------------- F
        "F_age_resolution": {
            "age_grid_step_M": AGE_STEP_M,
            "previous_step_M": 4.0,
            "probe_half_width_M": 3.0,
            "half_width_unchanged": True,
            "why": "a 4 M gain measured on a 4 M grid is one bin, and one bin is "
                   "indistinguishable from threshold behaviour. On a 2 M grid a "
                   "real 4 M gain must occupy two bins and the 8 M paper-grade "
                   "threshold occupies four",
            "quantization_of_delta_L_M": AGE_STEP_M,
            "declared_before_evaluation": True,
        },

        # ---------------------------------------------------------------- G
        "G_sequential_stop_rule": {
            "order": ["operator_rank_audit", "validation_pilot", "sealed_main"],
            "current_stage": "operator_rank_audit",
            "stop_conditions": {
                "R1L_STOP_1_indistinguishable_old_support":
                    "the localized direct and resolved operators have "
                    "indistinguishable old structural support",
                "R1L_STOP_2_no_old_band_improvement":
                    "resolved old-band structure error does not improve",
                "R1L_STOP_3_improvement_vanishes_after_order_summation":
                    "all improvement vanishes once orders are summed, i.e. it "
                    "does not survive UNRESOLVED_IMAGE",
                "R1L_STOP_4_positivity_baseline_dominates":
                    "the source bank cannot be represented without a dominant "
                    "positivity baseline",
            },
            "evaluable_at_stage_1": ["R1L_STOP_1", "R1L_STOP_3"],
            "evaluable_at_stage_2": ["R1L_STOP_2", "R1L_STOP_4"],
            "rule": "the stop conditions are evaluated in the report of the stage "
                    "that can see them, and a tripped condition ends the sequence "
                    "there. No later stage may be entered on the strength of a "
                    "condition that was not evaluated",
            "valid_negative_result": "higher-order channels improve global-DCT "
                                     "conditioning and spatially averaged "
                                     "emissivity history, but do not enable stable "
                                     "recovery of localized old morphology under "
                                     "the tested physically constrained source "
                                     "families",
            "a_negative_result_is_a_result": "the negative outcome above is "
                                             "reportable as stated and is not a "
                                             "reason to widen the design after "
                                             "seeing it",
        },

        "gates": {
            "R1L_G1_dyadic_dimension_mirror": "structural",
            "R1L_G2_exact_class_nesting": 1e-12,
            "R1L_G3_temporal_support_compactness": 0.30,
            "R1L_G4_adjoint": 1e-8,
            "R1L_G5_dense_matrix_free_parity": 1e-10,
            "R1L_G6_gram_monotonicity": 1e-10,
            "R1L_G7_enrichment_does_not_lose_rank": 0,
            "R1L_G8_unreached_columns_are_exactly_zero": 0.0,
            "R1L_G9_orbit_law_matches_raymap_fluid": 1e-12,
            "R1L_G10_circular_centres_outside_isco": "structural",
        },
        "scope": {
            "authorized": ["R1L_STAGE_1_OPERATOR_RANK_AUDIT"],
            "not_authorized": ["R1L validation pilot before stage 1 is reported",
                               "R1L sealed main before the pilot is reported",
                               "geometry mismatch", "VLBI", "order leakage", "ML",
                               "any rescoring of the sealed R1 bank"],
            "geometry": r1["physical_model"]["geometry"],
            "forbidden_language": "no localized result may be described as "
                                  "morphology recovery until the structural "
                                  "endpoint of D has been scored on a sealed bank",
        },
        "stop_after": "R1L_STAGE_1_OPERATOR_RANK_AUDIT",
    }

    doc["attestation"] = attest([R1_FREEZE, E3C_FREEZE])
    OUT.write_text(json.dumps(doc, indent=2) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}")
    print(f"  sha256 {sha256_file(OUT)}")
    for n, c in classes.items():
        w = c["temporal_support_width_M"]["all_other_functions"]
        print(f"  {n:6s} dim {c['dimension']:5d}  temporal support {w:8.4f} M  "
              f"({c['fraction_of_history_each_temporal_function_occupies']*100:.1f}% "
              f"of history, DCT is 100%)")
    print(f"  ISCO {r_isco:.6f} M; the R1 families drew circular centres from "
          f"{old_r_lo} M")
    print(f"  age grid step {AGE_STEP_M} M, was 4.0 M")
    print(f"total {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
