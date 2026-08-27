#!/usr/bin/env python3
"""HMT_1_HISTORICAL_FEATURE_AND_CONTRAST_TOMOGRAPHY_V0 -- preregistration.

Frozen before any new truth is drawn and before any operator is scored, per
items 1 and 2 of the authorizing ruling.

R1L stopped a specific claim: at the reference SNR, under a scalar-intensity
operator and non-negative physical banks, we did not show a material,
estimator-robust source result that also yields a stable contiguous interval of
old spatial morphology. HMT-1 does not reopen that endpoint. It asks a different
and narrower question.

Rather than asking whether every historical pixel is recovered, it asks whether
a *compressed physical description* of the past is recovered: where a feature
was, how it moved, how bright it was, when it appeared and when it faded. A
movie rendered from a recovered trajectory is still a movie; it is simply a
model-conditioned one, and the difference is stated rather than blurred.

The source model changes with the question. Motion and morphology live in the
contrast field, not in the constant background, so the object here is

    j = b(r, t) + dj(r, phi, t),   b > 0,   <dj(., t)> = 0,   b + dj >= 0

with dj signed. The total emissivity stays non-negative, which is what makes
this a physical source model rather than the signed diagnostic bank R1L had to
disqualify. That bank motivates the hypothesis and counts as no evidence for it.
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

R1 = ROOT / "artifacts" / "configs" / "R1_MAIN_FREEZE.json"
R1L = ROOT / "artifacts" / "configs" / "R1L_STAGE2R_VALIDATION_FREEZE_012.json"
AM14 = (ROOT / "artifacts" / "configs"
        / "R1L_STAGE2R_SCIENTIFIC_DISPOSITION_AMENDMENT_014.json")
OUT = ROOT / "artifacts" / "configs" / "HMT1_VALIDATION_FREEZE_V0.json"

FAMILIES = ["circular_hotspot_trajectory", "two_hotspot_trajectories",
            "m1_rotating_crescent", "m2_structural_mode",
            "flare_birth_motion_decay", "plunging_feature"]
OFF_MANIFOLD = ["three_hotspot_cluster", "counter_rotating_pair",
                "radially_drifting_arc"]
REGIMES = ["oracle_known", "estimated_from_data", "joint_inversion"]
SPLITS = ["selection", "pilot"]
ARMS = ["DIRECT_PHYSICAL", "RESOLVED_PHYSICAL", "UNRESOLVED_IMAGE", "TOTAL_FLUX"]
PER_CELL = 8
DRAWS = 4
SEED = 20260910
EPS, QUANT = 0.25, 0.95


def commitment(family, split, regime):
    return hashlib.sha256(json.dumps(
        {"family": family, "split": split, "regime": regime, "n": PER_CELL,
         "seed": SEED, "model": "contrast"}, sort_keys=True).encode()).hexdigest()


def main() -> int:
    reg = load_registry()
    r1 = json.loads(R1.read_text())
    am14 = json.loads(AM14.read_text())
    spin = float(r1["physical_model"]["spin"])
    cells = {f"{f}|{s}|{g}": commitment(f, s, g)
             for f in FAMILIES for s in SPLITS for g in REGIMES}

    doc = {
        "schema": "phrt-hmt1-freeze/1",
        "id": "HMT_1_HISTORICAL_FEATURE_AND_CONTRAST_TOMOGRAPHY_V0",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "ruling": "Reviewer authorization of HMT-1",
        "status": "FROZEN_BEFORE_ANY_NEW_TRUTH_OR_OPERATOR_SCORE",
        "branch": "research/hmt1_historical_feature_contrast_tomography_v0",

        "relation_to_r1l": {
            "r1l_stop_preserved": True,
            "r1l_dispositions": list(am14["dispositions"]),
            "sealed_commitments": "preserved unscored. HMT-1 neither reopens "
                                  "nor scores them",
            "not_a_rescue": "HMT-1 does not re-run, re-scope or re-tune the "
                            "R1L endpoint. It is a different question with new "
                            "banks, a new source model and new endpoints",
            "signed_bank_status": "the R1L signed constant-flux diagnostic "
                                  "motivates the contrast hypothesis and counts "
                                  "as no evidence for it. Its truths are not "
                                  "reused",
        },

        "claim_taxonomy": {
            "not_attempted_arbitrary_movie": "for an unconstrained field, any "
                                             "v with A v = 0 makes j and j + v "
                                             "indistinguishable, so no "
                                             "estimator of any kind can "
                                             "determine which occurred. This is "
                                             "a theorem about the operator, not "
                                             "a limitation of method",
            "attempted_here": "bounded, model-conditioned recovery of feature "
                              "trajectories and low-order mode histories within "
                              "a declared family",
            "not_attempted_real_astronomical": "order leakage, geometry "
                                               "uncertainty, sparse Fourier "
                                               "sampling, calibration, "
                                               "scattering, realistic transfer "
                                               "and real data are all out of "
                                               "scope and separately staged",
            "forbidden_language": "no HMT-1 result may be described as "
                                  "recovering an arbitrary or pixel-by-pixel "
                                  "film of the past",
        },

        # ------------------------------------------------------------ item 3
        "geometry": {"a_star": spin, "inclination_deg": 50.0,
                     "geometry_id": r1["physical_model"]["geometry"],
                     "orders": r1["physical_model"]["orders"],
                     "raymap_sha256": r1["physical_model"]["raymap_sha256"]},

        # ------------------------------------------------------------ item 4
        "source_model": {
            "form": "j(r, phi, t) = b(r, t) + dj(r, phi, t)",
            "background_positive": "b(r, t) > 0, axisymmetric",
            "zero_spatial_mean": "<dj(., t)> over the evaluation grid = 0 at "
                                 "every age",
            "total_nonnegative": "b + dj >= 0 everywhere",
            "why_signed_dj_is_legitimate": "dj is a brightness fluctuation "
                                           "about a positive background, not an "
                                           "emissivity. The physical field that "
                                           "must stay non-negative is b + dj, "
                                           "and it does",
            "zero_mean_is_imposed_azimuthally": {
                "constraint": "<dj(r, ., t)>_phi = 0 at every radius and age",
                "implies_the_ruling": "an azimuthally zero-mean field also has "
                                      "zero spatial mean at each age, so this "
                                      "is a strengthening rather than a "
                                      "substitution",
                "why": "a fluctuation with an axisymmetric part is exactly "
                       "indistinguishable from a background carrying that same "
                       "part. No procedure in any of the three regimes can "
                       "attribute it, so leaving it in would hand the "
                       "estimated-background regime a systematic error "
                       "unrelated to the operator and it would then be read as "
                       "one. Measured before the strengthening, an "
                       "axisymmetric background model absorbed 29 percent of "
                       "the fluctuation; after it, 1e-16",
                "also_the_physical_line": "an azimuthally flat component is "
                                          "background by any reading of "
                                          "'motion and morphology live in the "
                                          "contrast field'"},
            "multiplicative_form_note": "j = b(1 + delta) with <delta> = 0 is "
                                        "equivalent to the additive form only "
                                        "when the mean is taken azimuthally at "
                                        "fixed r. Under the azimuthal "
                                        "constraint above the two coincide "
                                        "exactly, because b is axisymmetric and "
                                        "<b s>_phi = b <s>_phi. Under the "
                                        "weaker global spatial mean they do "
                                        "not, and that is the reading the first "
                                        "draft of this freeze warned about",
            "amplitude_parameterisation": {
                "form": "dj = b * s, with s of zero azimuthal mean and peak "
                        "|s| drawn per truth",
                "peak_fraction_of_background": [0.30, 0.80],
                "why_local_not_global": "scaling the fluctuation against the "
                                        "global worst point sets its amplitude "
                                        "where the background is thinnest and "
                                        "collapsed the achieved contrast to "
                                        "between 0.9 and 12 percent. That is a "
                                        "parameterisation artefact, not a "
                                        "weak-signal finding, and every family "
                                        "would have failed for a reason "
                                        "unrelated to the operator",
                "achieved_after_the_fix": "peak fluctuation of 0.5 to 0.8 of "
                                          "the local background, with the total "
                                          "emissivity strictly positive"},
            "tolerances": {"zero_mean_relative": 1e-10,
                           "positivity_floor": 0.0,
                           "background_positive_floor": 1e-6},
        },

        # ------------------------------------------------------------ item 5
        "feature_families": {
            "declared": FAMILIES,
            "n_families": len(FAMILIES),
            "circular_hotspot_trajectory": {
                "parameters": ["r_h", "phi_h_0", "A_h", "sigma_r", "sigma_phi"],
                "motion": "Kerr prograde circular geodesic outside the ISCO, "
                          "phi_h(t) = phi_h_0 + Omega_K(r_h) t",
                "r_centre_M": [isco_radius(spin), 29.989231533549642]},
            "two_hotspot_trajectories": {
                "parameters": ["r_h1", "phi_h1_0", "A_h1", "r_h2", "phi_h2_0",
                               "A_h2"],
                "motion": "two independent circular trajectories"},
            "m1_rotating_crescent": {
                "parameters": ["r_peak", "width", "a_m1", "pattern_phase"],
                "motion": "rigid rotation at Omega_K(r_peak)"},
            "m2_structural_mode": {
                "parameters": ["r_peak", "width", "a_m2", "pattern_phase"],
                "motion": "rigid rotation at Omega_K(r_peak)"},
            "flare_birth_motion_decay": {
                "parameters": ["r_h", "phi_h_0", "A_peak", "t_birth", "tau_decay"],
                "motion": "circular trajectory with a compactly supported "
                          "birth-and-decay envelope"},
            "plunging_feature": {
                "parameters": ["r_h_start", "phi_h_0", "A_h"],
                "motion": "radial plunge inside the ISCO on its conserved E and "
                          "L, angular rate u^phi / u^t",
                "r_centre_M": [1.8660254037844386, isco_radius(spin)]},
            "off_manifold_controls": {
                "families": OFF_MANIFOLD,
                "role": "control only. These lie outside the declared manifold "
                        "and may not contribute to any endpoint. They exist so "
                        "the recovery claim is bounded by the manifold rather "
                        "than assumed to generalise past it"},
            "velocity_field_for_g3": velocity_field_record(spin),
        },

        # ------------------------------------------------------------ item 6
        "background_regimes": {
            "declared": REGIMES,
            "oracle_known": {"b": "supplied exactly", "role": "upper-bound "
                             "control. A result that exists only here is called "
                             "background-assisted, not unconditional"},
            "estimated_from_data": {
                "b": "estimated by a fixed low-order axisymmetric procedure from "
                     "the arm's own data before dj is reconstructed",
                "procedure": "least squares of the declared low-order "
                             "axisymmetric design *through the arm's own "
                             "operator* against that arm's own data, then "
                             "positivity-clipped at the background floor",
                "procedure_note": "the first draft said 'azimuthal average of "
                                  "the direct-channel image back-projection'. "
                                  "The adjoint of a whitened operator is not an "
                                  "image and its azimuthal average is not a "
                                  "background, so that recipe was not "
                                  "well-posed. Fitting the same axisymmetric "
                                  "design through the operator is the "
                                  "well-posed version of the same idea, uses "
                                  "only the arm's own data, and is still fixed "
                                  "in advance. Corrected before any truth was "
                                  "drawn",
                "frozen_before_any_truth": True,
                "role": "**the regime a paper-grade result must survive**"},
            "joint_inversion": {
                "b": "inferred jointly with dj under separate smoothness and "
                     "positivity constraints",
                "role": "reported; may support but not substitute for the "
                        "estimated regime"},
        },

        # ---------------------------------------------------------- items 7-8
        "arms": ARMS,
        "snr": {"primary": 100.0, "secondary": 1000.0,
                "rule": "no other SNR may carry a claim"},
        "reconstruction_class": {
            "id": "L448_contrast",
            "basis": "4 radial cubic B-splines in log r x 7 real Fourier modes "
                     "x 16 compact temporal hats, with every m = 0 direction "
                     "projected out so the class represents dj and cannot "
                     "represent any part of b",
            "dimension_before_projection": 448,
            "dimension_after_projection": 384,
            "why_all_m0_not_just_the_level": "dj has zero azimuthal mean at "
                                             "every radius and age, so it is "
                                             "orthogonal to every axisymmetric "
                                             "field and not merely to the "
                                             "spatially constant ones. "
                                             "Projecting out only the level "
                                             "would leave the class able to "
                                             "represent axisymmetric structure "
                                             "the source model forbids, and the "
                                             "estimator would spend those "
                                             "directions competing with the "
                                             "background",
            "why_reuse": "the localized compact-support class is already "
                         "validated by the R1L stage-1 audit and its nesting, "
                         "adjoint and zero-column properties are gated. HMT-1 "
                         "changes the endpoint, not the basis",
        },
        "estimators": {
            "TSVD": "classical linear, primary",
            "RIDGE_IDENTITY": "classical linear, confirmatory",
            "NONNEGATIVE_CONSTRAINED": {
                "role": "constrained estimator required by the ruling",
                "method": "projected gradient enforcing b + dj >= 0 on the "
                          "evaluation grid",
                "scope": "primary SNR and the estimated-background regime only, "
                         "declared in advance because it is iterative and "
                         "cannot reuse the cached spectral factorisation"},
            "ML": "NOT_AUTHORIZED",
        },

        # ------------------------------------------------------------ item 9
        "evaluation_grid": {
            "n_radial": 16, "n_azimuthal": 32, "n_temporal": 40,
            "spacing": "log-spaced in radius, uniform in azimuth and source "
                       "time, equal weights. A scoring device, not a quadrature",
            "angular_cell_rad": 0.19634954084936207,
            "why_declared_here": "the grid was not pinned in the first draft of "
                                 "this freeze, and it sets the floor on "
                                 "angular and radial trajectory error -- a "
                                 "12-point azimuth would put a 0.52 rad floor "
                                 "under every angle this experiment reports. "
                                 "Added before any truth was drawn, which is "
                                 "the only time a preregistration gap can be "
                                 "closed without it becoming a tuning",
            "refinement": "the argmax is refined by parabolic interpolation on "
                          "the three cells straddling the peak in each of r and "
                          "phi, so the reported position is not quantised to "
                          "the grid. Declared here, not chosen after seeing an "
                          "error",
        },
        "feature_extraction": {
            "rule": "every recovered quantity is extracted from the "
                    "reconstructed dj by a procedure fixed here, applied "
                    "identically to truth and reconstruction",
            "per_age_slice": "the age-windowed dj field on the evaluation grid, "
                             "Gaussian window of half width 3.0 M",
            "spatial_map_at_age": "sum over source time of the window "
                                  "weights times dj, normalised by the summed "
                                  "weights, giving one (r, phi) map per age",
            "hotspot_position": "argmax of that map over (r, phi), refined by "
                                "parabolic interpolation in each coordinate, "
                                "giving r_hat(a) and phi_hat(a)",
            "hotspot_amplitude": "the value at that argmax, A_hat(a)",
            "mode_amplitudes": "a_m(a) = radially weighted projection of the "
                               "slice onto cos(m phi) and sin(m phi), "
                               "m = 1 and 2, reported as the complex modulus",
            "event_times": {
                "age_runs_backwards": "a larger age is an earlier moment, so "
                                      "the two definitions below read off the "
                                      "high-age end and the low-age end "
                                      "respectively. Stating this explicitly "
                                      "because 'earliest age' is ambiguous and "
                                      "reading it the wrong way returns a "
                                      "finite plausible number for the wrong "
                                      "event",
                "t_birth": "the LARGEST age at which A_hat(a) exceeds 0.25 of "
                           "its maximum over ages -- the earliest moment the "
                           "feature is detectable",
                "tau_decay": "the age difference between the age of the maximum "
                             "of A_hat(a) and the SMALLEST age still above 1/e "
                             "of it -- decay runs forward in time, toward "
                             "smaller ages"},
            "normalisation": {
                "radial": "|r_hat - r| divided by the declared radial support "
                          "width",
                "angular": "wrapped |phi_hat - phi| divided by pi",
                "amplitude": "|A_hat - A| divided by max over ages of |A|",
                "mode": "|a_hat_m - a_m| divided by max over ages of |a_m|",
                "event_time": "|t_hat - t| divided by the observation span"},
            "aggregate": "E_features(a) = root mean square over the family's "
                         "declared normalised parameter errors at age a",
        },
        "primary_endpoints": {
            "old_band_feature_error": {
                "statistic": "delta_E_old_features = "
                             "(E_old_features(direct) - E_old_features(arm)) / "
                             "E_old_features(direct), per truth",
                "aggregation": "equal weight over family cells",
                "old_band_boundary_M": float(r1["metrics"]["old_band_boundary_M"]),
                "bootstrap": {"kind": "paired truth-cluster", "unit": "truth",
                              "n_resamples": 10000, "level": 0.95,
                              "seed": SEED + 1,
                              "intervals": "one for the per-truth median and "
                                           "one for the cell-balanced mean, "
                                           "each named where reported"}},
            "stable_feature_interval": {
                "statistic": "L_stable_features(epsilon, q) = sup{T >= 0 : "
                             "Pr[sup_{0 <= a <= T} E_features(a) <= epsilon] "
                             ">= q}, supremum inside the probability, over "
                             "truth and noise jointly",
                "epsilon": EPS, "quantile": QUANT,
                "age_grid_step_M": 2.0, "probe_half_width_M": 3.0,
                "requirement": "strictly positive for the resolved arm, and "
                               "greater than the direct arm's"},
            "event_time_error": "reported for flare_birth_motion_decay in M, "
                                "with its own interval",
            "trajectory_error": "angular and radial error reported separately "
                                "in radians and M, not only as the normalised "
                                "aggregate",
        },

        # ----------------------------------------------------------- item 10
        "secondary_endpoints": {
            "rendered_frame_error": "relative error of the rendered dj frame",
            "perceptual": "structural similarity of rendered frames",
            "rule": "secondary. Neither may carry the primary claim, and a "
                    "perceptually convincing frame is not evidence that the "
                    "trajectory was measured",
        },

        # ----------------------------------------------------------- item 11
        "required_controls": {
            "exact_and_near_null_feature_pairs":
                "pairs of feature histories whose difference lies in or near "
                "the operator's null space, with the realized separation in "
                "sigma checked against the frozen target",
            "off_manifold_families": OFF_MANIFOLD,
            "background_estimation_error": "the error of the estimated "
                                           "background against the truth, "
                                           "reported per regime so a feature "
                                           "result can be attributed",
            "order_summation": "the UNRESOLVED_IMAGE arm at the same standing "
                               "as the resolved one",
            "estimators": ["TSVD", "RIDGE_IDENTITY", "NONNEGATIVE_CONSTRAINED"],
        },

        # ----------------------------------------------------------- item 12
        "pass_criteria": {
            "material_benefit_under_both_classical_estimators": {
                "median_relative_reduction": 0.10,
                "median_bootstrap_lower_bound": 0.05,
                "cell_balanced_mean": 0.10,
                "mean_bootstrap_lower_bound": 0.05,
                "note": "the same numeric standard R1L used, so the two "
                        "studies are comparable"},
            "nonzero_stable_feature_interval": {
                "resolved_L_stable_features_M": "> 0",
                "and_greater_than_direct": True},
            "family_agreement": {
                "declared_rule": "at least three quarters of the declared "
                                 "families, rounded up",
                "n_families": len(FAMILIES),
                "required_count": 5,
                "ambiguity_recorded": "the authorizing ruling says 'at least "
                                      "3/4 families'. Earlier rulings used "
                                      "'three of the four' when there were "
                                      "exactly four families; here there are "
                                      "six. The fraction reading is taken as "
                                      "primary because it preserves the "
                                      "stringency of the earlier rule, and the "
                                      "literal count reading (3 of 6) is also "
                                      "reported so the reviewer can see both "
                                      "and overturn this choice"},
            "survives_estimated_background": {
                "required_regime": "estimated_from_data",
                "rule": "a result that exists only under the oracle background "
                        "is reported as background-assisted and does not pass"},
            "null_controls_consistent": True,
            "exactly_one_disposition": True,
        },
        "dispositions": {
            "HMT1_FEATURE_RECOVERY_PASS":
                "every pass criterion met, including the estimated-background "
                "regime",
            "HMT1_BACKGROUND_ASSISTED_ONLY":
                "criteria met under the oracle background and not under the "
                "estimated one",
            "HMT1_MATERIAL_ERROR_REDUCTION_NO_STABLE_INTERVAL":
                "the feature error improves materially and no positive stable "
                "feature interval exists",
            "HMT1_NO_MATERIAL_EFFECT":
                "banks sound, materiality not met. A reportable result",
            "HMT1_SOURCE_BANK_FAILURE":
                "a declared bank could not be built within the contrast-model "
                "tolerances",
            "HMT1_IMPLEMENTATION_DEFECT":
                "a gate failed, a limit was exceeded, or a commitment did not "
                "reproduce",
        },

        "counts": {
            "families": FAMILIES, "splits": SPLITS, "regimes": REGIMES,
            "truths_per_family_split_regime": PER_CELL,
            "n_cells": len(cells),
            "n_truths": len(cells) * PER_CELL,
            "noise_draws_per_truth": DRAWS,
            "off_manifold_truths_per_family": PER_CELL,
        },
        "split_rule": {
            "selection": "hyperparameters chosen here and nowhere else",
            "pilot": "the reported endpoint, on truths no hyperparameter saw",
            "commitments": cells,
            "commitment_meaning": "sha256 over (family, split, regime, n, seed, "
                                  "model). The runner derives every truth seed "
                                  "from the same string and must reproduce the "
                                  "hash before scoring",
        },
        "seeds": {"bank_seed": SEED, "noise_seed": SEED + 2,
                  "bootstrap_seed": SEED + 1, "null_pair_seed": SEED + 3,
                  "subsample_seed": int(r1["observation"]["subsample_seed"])},

        "gates": {
            "HMT1_G1_pinned_numerical_environment": "structural",
            "HMT1_G2_split_commitments_reproduce": "structural",
            "HMT1_G3_split_disjointness": "structural",
            "HMT1_G4_contrast_zero_spatial_mean": 1e-10,
            "HMT1_G4b_azimuthal_zero_mean": 1e-10,
            "HMT1_G5_total_emissivity_nonnegative": 0.0,
            "HMT1_G6_background_strictly_positive": 1e-6,
            "HMT1_G7_adjoint": 1e-8,
            "HMT1_G8_operator_truth_identity": 1e-9,
            "HMT1_G9_null_controls": 0.05,
            "HMT1_G10_feature_extraction_deterministic": 1e-9,
            "HMT1_G10b_truth_extraction_recovers_generative_parameters": 1.0,
            "HMT1_G11_off_manifold_excluded_from_endpoints": "structural",
            "HMT1_G12_no_maximal_regularization_collapse": "structural",
            "HMT1_G13_declared_gate_coverage": "structural",
            "HMT1_G14_resource_limits": "structural",
        },
        "gate_notes": {
            "HMT1_G10b_truth_extraction_recovers_generative_parameters":
                "one evaluation-grid cell, in each of radius and azimuth. Read "
                "at the evaluation-grid resolution rather than at 1e-9, "
                "because extraction from a sampled field cannot beat the grid "
                "it is sampled on. The radial axis is uniform in log r, so a "
                "cell is a fixed step in log r and the tolerance does not "
                "silently change meaning with radius. Ages at which the "
                "generative amplitude has fallen below the already-declared "
                "birth fraction of its own maximum are not scored, because "
                "there the peak location is the argmax of numerical dust. The "
                "azimuthal comparison is folded by m for the pattern "
                "families, whose cos(m phi) shape has m equal maxima",
            "HMT1_G10b_registration_defect":
                "this gate was first registered with its reading written into "
                "the threshold field as prose, which left it declared but not "
                "emitted -- the exact condition HMT1_G13 exists to catch, and "
                "which it did catch on the first end-to-end run. G10 asks only "
                "that extraction be repeatable, which a deterministic "
                "extractor reading the wrong position also satisfies, so the "
                "gate was implemented rather than withdrawn. Corrected before "
                "any validation truth was scored",
            "HMT1_G4b_registration_defect":
                "G4b was emitted by the scorer before it was declared here, "
                "and the coverage computation carried a hard-coded exemption "
                "for it. Declaring it removes the exemption, so HMT1_G13 now "
                "compares the declared and emitted sets with no allowance on "
                "either side. Corrected before any validation truth was scored",
        },
        "resource_limits": {"wall_clock_seconds": 10800, "peak_rss_mb": 12000,
                            "on_exceeded": "HMT1_IMPLEMENTATION_DEFECT",
                            "no_silent_reduction": True},
        "numerical_environment": {
            "pinned": True,
            "variables": json.loads(
                (ROOT / "artifacts" / "configs"
                 / "R1L_DETERMINISTIC_NUMERICS_AMENDMENT_009.json").read_text()
            )["pinned_numerical_environment"]["variables"],
            "assertion": "every BLAS pool must report one thread, interrogated "
                         "after import"},

        # ----------------------------------------------------------- item 13
        "scope": {
            "authorized": ["HMT1_VALIDATION"],
            "not_authorized": ["sealed main", "geometry mismatch",
                               "order leakage beyond the declared unresolved "
                               "arm", "VLBI", "ML", "polarization or "
                               "multi-frequency channels"],
            "stop_after": "HMT1_VALIDATION",
            "next_stages_named_but_unauthorized": [
                "Stage C order summation and leakage",
                "Stage D geometry mismatch",
                "Stage E Fourier/VLBI projection",
                "Stage F learned priors with null-pair audits"],
        },
        "provenance": {
            "r1_freeze_sha256": sha256_file(R1),
            "r1l_stage2r_freeze_sha256": sha256_file(R1L),
            "r1l_disposition_amendment_sha256": sha256_file(AM14),
            "registry_sha256": reg.sha256,
        },
    }
    doc["attestation"] = attest([R1, R1L, AM14])
    OUT.write_text(json.dumps(doc, indent=2) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}")
    print(f"  sha256 {sha256_file(OUT)}")
    print(f"  {len(FAMILIES)} families x {len(SPLITS)} splits x "
          f"{len(REGIMES)} regimes x {PER_CELL} = {len(cells) * PER_CELL} truths")
    print(f"  family agreement required: "
          f"{doc['pass_criteria']['family_agreement']['required_count']} of "
          f"{len(FAMILIES)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
