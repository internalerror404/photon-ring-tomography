#!/usr/bin/env python3
"""Register the R0 canary reconstruction pilot freeze.

Everything that could be chosen after seeing a reconstruction score is pinned
here and committed before the first validation movie is rendered. The freeze's
own sha256 is copied into every result row, so a table cannot be silently
re-attributed to a different configuration.

Source parameter ranges are derived from the declared physical support of the
canary ray maps and from the basis resolution -- never from reconstruction
performance. The derivation is recorded alongside each range so the reader can
check that it did not come from a tuning loop.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from phrt import provenance
from phrt.config import load_registry, sha256_file
from phrt.geometry.raymap import read
from phrt.geometry.sampling import common_count, stratified_subsample

OUT = ROOT / "artifacts" / "configs" / "R0_CANARY_RECONSTRUCTION_PILOT_FREEZE.json"
ACCEPTED_BASE = "0ef341dae3b21bc2bdd0e54a18971cff208af783"
GEOMETRY = "a050_i050"
SPIN, INCL = 0.5, 50.0
ORDERS = (0, 1, 2)
SNR0_GRID = [1, 3, 10, 30, 100, 300, 1000, 3000, 10000, 30000, 100000, 1000000]
SUBSAMPLE_SEED = 20260825
RAYS_PER_ORDER = 1536
N_OBSERVER_TIMES = 8
OBSERVER_SPAN = 20.0
PROBE_HALF_WIDTH = 3.0
AGE_STEP = 4.0

# One master seed. Every stream below is derived from it by a labelled
# SeedSequence spawn, so a stream cannot silently collide with another.
MASTER_SEED = 20260901

SEED_STREAMS = {
    "prior_fit_train": 1000, "validation_in_class": 2000,
    "validation_off_grid": 3000, "validation_ood": 4000,
    "null_pairs": 5000, "noise_draws": 6000, "bootstrap": 7000,
    "future_main_test": 9000,
}


def git(*a: str) -> str:
    return subprocess.run(["git", *a], cwd=ROOT, capture_output=True,
                          text=True).stdout.strip()


def canary_support() -> dict:
    rng = np.random.default_rng(SUBSAMPLE_SEED)
    maps = [read(ROOT / "artifacts" / "raymaps" / f"{GEOMETRY}_n{n}_core.h5")
            for n in ORDERS]
    base = common_count([stratified_subsample(m, RAYS_PER_ORDER, rng) for m in maps],
                        rng)
    r_in = min(float(o.source_r.min()) for o in base)
    r_out = max(float(o.source_r.max()) for o in base)
    windows = {int(o.order): [float(o.delay.min()), float(o.delay.max())]
               for o in base}
    return {"r_inner_M": r_in, "r_outer_M": r_out,
            "delay_windows_M": windows,
            "solid_angle_by_order": {int(o.order): float(o.quadrature.sum())
                                     for o in base},
            "rays_per_order_after_common_count": {int(o.order): o.n_rays
                                                  for o in base}}


def main() -> int:
    reg = load_registry()
    prov = provenance.collect()
    sup = canary_support()
    r_in, r_out = sup["r_inner_M"], sup["r_outer_M"]
    t_obs = list(np.linspace(0.0, OBSERVER_SPAN, N_OBSERVER_TIMES))
    max_delay = max(w[1] for w in sup["delay_windows_M"].values())
    t_lo = float(min(t_obs) - max_delay) - 3.0 * PROBE_HALF_WIDTH
    t_hi = float(max(t_obs)) + 3.0 * PROBE_HALF_WIDTH

    e3c = json.loads((ROOT / "artifacts" / "configs"
                      / "E3C_OPERATOR_GRID_FREEZE.json").read_text())
    a0_999 = float(e3c["common_age_grid"]
                   ["direct_order_A_0_999_by_geometry_M"][GEOMETRY])

    # Ranges derived from the physical support and the basis resolution.
    # C224 is 4 radial B-splines in log r, 7 real azimuthal Fourier modes
    # (|m| <= 3) and 8 temporal DCT modes on [t_lo, t_hi]. The finest structure
    # the class can represent sets the smallest feature we ask for; the support
    # sets the largest.
    log_span = float(np.log(r_out / r_in))
    finest_radial = float(r_in * np.expm1(log_span / 4.0))   # one knot interval at r_in
    t_span = t_hi - t_lo
    finest_temporal = float(t_span / 8.0)                     # highest DCT half-period
    finest_azimuthal_m = 3

    freeze = {
        "schema": "phrt-r0-reconstruction-freeze/1",
        "experiment_id": "R0_CANARY_RECONSTRUCTION_PILOT",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),

        "provenance": {
            "accepted_scientific_base": ACCEPTED_BASE,
            "start_commit": git("rev-parse", "HEAD"),
            "branch": git("rev-parse", "--abbrev-ref", "HEAD"),
            "base_is_ancestor_of_start": True,
            "start_commit_is_documentation_only_descendant": False,
            "deviation_note":
                "The launch permits a descendant containing only approved "
                "documentation amendments. The start commit is not that: it "
                "carries the G10q measurement-model correction (d6869f8) and "
                "the accepted E3B/E3C work. Starting from the bare base is not "
                "possible under this launch's own frozen model -- at "
                + ACCEPTED_BASE[:7] + " the forward coefficient is g^3 with a "
                "flat per-row sigma and no G10q gate exists, so the required "
                "whitened row sqrt(dOmega)/sigma_Omega * g^3 * B is absent and "
                "R0_G3 would stop immediately with QUADRATURE_NOISE_DEFECT.",
            "registry_sha256": reg.sha256,
            "git_dirty_at_registration": provenance.git_dirty(),
        },

        "environment": {
            "packages": prov.packages, "hardware": prov.hardware,
            "python": prov.python, "torch": prov.torch,
            "environment_sha256": prov.environment_sha256,
            "protocol_deviations": prov.deviations,
        },

        "scope": {
            "authorized": ["R0A_RECONSTRUCTION_CORRECTNESS_SMOKE",
                           "R0B_CANARY_RECONSTRUCTION_VALIDATION_PILOT"],
            "not_authorized": ["R1_MAIN", "E3C", "E3D", "R2", "R3", "R4", "R5",
                               "VLBI", "geometry_mismatch", "order_leakage", "ML"],
            "restriction": "single canary geometry, single source class",
            "forbidden_language": "no result may be described as geometry-wide "
                                  "or as arbitrary movie recovery",
        },

        "physical_model": {
            "geometry": GEOMETRY, "spin": SPIN, "inclination_deg": INCL,
            "orders": list(ORDERS), "source_class": "C224",
            "snr0_grid": SNR0_GRID,
            "operator_notation": {
                "physical_operator": "mathcal A : mathcal X -> mathcal Y",
                "restricted": "A_C = mathcal A Q_C",
                "warning": "Q_C is applied exactly once; an estimator returning "
                           "coefficients must not be synthesised twice",
            },
            "whitened_row": "sqrt(dOmega_p)/sigma_Omega * g_p^3 * B(r_p,phi_p,t_p)",
            "noise": "one sigma_Omega for the whole pilot; no arm-specific scale",
            "raymap_sha256": {
                f"{GEOMETRY}_n{n}_core.h5":
                    sha256_file(ROOT / "artifacts" / "raymaps"
                                / f"{GEOMETRY}_n{n}_core.h5") for n in ORDERS},
            **sup,
        },

        "observation": {
            "rays_per_order": RAYS_PER_ORDER,
            "n_observer_times": N_OBSERVER_TIMES,
            "observer_span_M": OBSERVER_SPAN,
            "observer_times_M": t_obs,
            "subsample_seed": SUBSAMPLE_SEED,
            "basis_t_min": t_lo, "basis_t_max": t_hi,
            "arms_primary": ["DIRECT_PHYSICAL", "RESOLVED_PHYSICAL",
                             "UNRESOLVED_IMAGE", "TOTAL_FLUX"],
            "arms_diagnostic": ["DELAY_ONLY", "EQUALIZED_ORDER_SENSITIVITY"],
            "noise_construction":
                "one resolved Gaussian draw per (truth, SNR, draw index); the "
                "direct, unresolved and total-flux observations are the declared "
                "linear selections and readouts of that same draw, so arms are "
                "paired and covariance propagation is exact rather than resampled",
        },

        "smoke_profile": {
            "profile": "R0_SMOKE", "rays_per_order": 192, "observer_times": 6,
            "source_class": "C48", "snr0": [100, 1000000],
            "movies_per_non_null_family": 4, "null_pairs_per_delta": 4,
            "noise_draws_per_movie": 2,
            "isolation": "smoke tables are written under the r0_smoke_ prefix "
                         "and are never merged with pilot or paper tables",
        },

        "gates": {
            "R0_G1_dense_matrix_free_parity": 1e-10,
            "R0_G2_physical_adjoint": 1e-8,
            "R0_G3_G10q_quadrature_noise_invariance": 1e-10,
            "R0_G4_mixing_covariance": 1e-10,
            "R0_G5_basis_round_trip": 1e-10,
            "R0_G6_age_probe_normalization": 1e-12,
            "R0_G7_right_censoring": "structural",
            "R0_G8_estimator_closed_form": 1e-9,
            "R0_G9_noise_replay": "bitwise",
            "R0_G10_null_pair_calibration": 0.02,
            "R0_G11_split_hash_disjointness": "structural",
        },

        "source_families": {
            "derivation": "ranges come from the declared physical support "
                          f"r in [{r_in:.3f}, {r_out:.3f}] M and from the C224 "
                          "resolution; no range was chosen from a reconstruction "
                          "score",
            "resolution_bounds": {
                "finest_radial_feature_M": finest_radial,
                "finest_temporal_feature_M": finest_temporal,
                "highest_azimuthal_mode": finest_azimuthal_m,
                "radial_log_span": log_span,
                "temporal_span_M": t_span,
            },
            "positivity_construction":
                "every physical family is rendered as a strictly positive "
                "intensity: a positive baseline plus non-negative components. "
                "Signed near-null perturbations are added to that baseline and "
                "the admissible amplitude that keeps the rendered movie "
                "non-negative is recorded per pair",
            "families": {
                "single_orbiting_hotspot": {
                    "role": "prior_fit",
                    "r_centre_M": [max(3.0, r_in), 0.6 * r_out],
                    "sigma_r_M": [finest_radial, 0.25 * r_out],
                    "sigma_phi_rad": [np.pi / (2 * finest_azimuthal_m), np.pi / 2],
                    "orbit": "Keplerian angular velocity at r_centre, "
                             "Omega = r^{-3/2} in M units",
                    "amplitude": "unit peak over the positive baseline"},
                "two_independent_hotspots": {
                    "role": "prior_fit",
                    "same_ranges_as": "single_orbiting_hotspot",
                    "separation_rule": "independent radii and phases; "
                                       "amplitudes drawn independently"},
                "rotating_asymmetric_crescent": {
                    "role": "prior_fit",
                    "r_peak_M": [max(3.0, r_in), 0.5 * r_out],
                    "width_M": [2 * finest_radial, 0.3 * r_out],
                    "asymmetry_modes": [1, finest_azimuthal_m],
                    "pattern_speed": "rigid rotation at the Keplerian rate of r_peak"},
                "correlated_extended_field": {
                    "role": "prior_fit",
                    "radial_correlation_M": [2 * finest_radial, 0.5 * r_out],
                    "azimuthal_modes": [0, finest_azimuthal_m],
                    "temporal_spectrum": "power law in DCT index, exponent in [1, 3]",
                    "construction": "exponentiated Gaussian field, positive by "
                                    "construction"},
                "moving_flare_birth_decay": {
                    "role": "held_out_ood",
                    "why_ood": "birth and decay give a temporal profile that is "
                               "compactly supported in time and not represented "
                               "in the prior-fit families' stationary or "
                               "smoothly-varying temporal structure",
                    "rise_M": [finest_temporal / 2, 2 * finest_temporal],
                    "decay_M": [finest_temporal, 4 * finest_temporal],
                    "drift": "radial drift plus Keplerian azimuthal motion"},
                "near_null_combinations": {
                    "role": "control",
                    "construction": "pairs separated along directions chosen to "
                                    "realise a target whitened Mahalanobis "
                                    "distance under the declared arm"},
            },
            "off_grid": {
                "rule": "off-grid truths are rendered analytically and are NOT "
                        "in the span of C224; they are evaluated directly at the "
                        "ray coordinates",
                "refinement_factor": 4,
                "meaning": "feature scales a factor of 4 finer than the finest "
                           "scale C224 can represent"},
        },

        "split": {
            "prior_fit_families": ["single_orbiting_hotspot",
                                   "two_independent_hotspots",
                                   "rotating_asymmetric_crescent",
                                   "correlated_extended_field"],
            "held_out_ood_family": ["moving_flare_birth_decay"],
            "prior_free_estimators_evaluated_on": "every validation regime",
        },

        "pilot_counts": {
            "prior_fit_train_per_family": 512,
            "validation_in_class_per_prior_fit_family": 128,
            "validation_off_grid_per_physical_family": 64,
            "validation_ood_total": 256,
            "null_pairs_per_target": 40,
            "mahalanobis_targets": [0.25, 0.5, 1.0, 2.0, 4.0],
            "noise_draws_per_validation_truth_and_snr": 4,
            "noiseless_control": 1,
            "status": "PILOT_ONLY; these counts are not the main test campaign",
        },

        "estimators": {
            "required": ["TSVD", "RIDGE_IDENTITY", "TIKHONOV_TEMPORAL",
                         "WIENER_GAUSSIAN"],
            "conditional": ["LINEAR_STATE_SPACE"],
            "conditional_on": "R0_G8_estimator_closed_form",
            "not_authorized": ["TOTAL_VARIATION", "AUTOENCODER", "NEURAL_FIELD",
                               "UNROLLED_NETWORK", "DIFFUSION",
                               "ANY_TEST_TUNED_ESTIMATOR"],
        },

        "hyperparameter_grids": {
            "frozen_before_first_validation_score": True,
            "TSVD": {"cut_on": "sigma_i / sigma_max",
                     "grid": list(np.logspace(-8, -1, 15))},
            "RIDGE_IDENTITY": {"cut_on": "lambda / lambda_max(G)",
                               "grid": list(np.logspace(-10, 0, 21))},
            "TIKHONOV_TEMPORAL": {"cut_on": "lambda / lambda_max(A^T C^-1 A)",
                                  "grid": list(np.logspace(-10, 0, 21))},
            "WIENER_GAUSSIAN": {"cut_on": "covariance shrinkage",
                                "grid": list(np.logspace(-6, 0, 13))},
            "LINEAR_STATE_SPACE": {
                "process_noise": list(np.logspace(-6, 0, 7)),
                "observation_noise": [1.0],
                "note": "observation noise is fixed at the declared whitened "
                        "scale; the arm may not choose its own sigma"},
            "selection": {
                "data": "validation only, separately per arm, estimator and SNR",
                "objective_lexicographic": [
                    "maximize T_stable(epsilon=0.50, q=0.90)",
                    "minimize old-band normalized error",
                    "minimize old-band absolute error",
                    "prefer the stronger regularizer or simpler model on an "
                    "exact tie"],
                "oracle": "truth-selected tuning is emitted only as "
                          "ORACLE_UPPER_BOUND and never as a method result"},
        },

        "metrics": {
            "age_window": "compact window W_a on the common age grid, "
                          f"half width {PROBE_HALF_WIDTH} M, step {AGE_STEP} M",
            "E_of_a": "||W_a(xhat - x)||_2 / max(||W_a x||_2, eta)",
            "E_abs_of_a": "||W_a(xhat - x)||_2",
            "eta_rule": "0.05 * median over prior-fit truths and ages with "
                        "||W_a x|| > 0 of ||W_a x||_2, frozen before scoring",
            "eta_value": None,
            "stable_depth_surface": {"epsilon": [0.25, 0.35, 0.50],
                                     "q": [0.80, 0.90, 0.95]},
            "primary_point": "T_stable(epsilon=0.50, q=0.90)",
            "also_reported": ["T_reach", "T_contig", "D_hist(T)", "d_eff(T)",
                              "recent/middle/old band errors",
                              "data-supported and weak-subspace errors",
                              "calibration and coverage", "runtime",
                              "iterations", "peak memory"],
            "old_band_boundary_M": a0_999,
            "old_band_rule": "the frozen direct-order 99.9% throughput-weighted "
                             "age boundary; never selected from reconstruction "
                             "curves",
            "age_bands": {"recent": [0.0, a0_999 / 3.0],
                          "middle": [a0_999 / 3.0, a0_999],
                          "old": [a0_999, None]},
        },

        "subspaces": {
            "P_data": "sum over i with SNR_0 * sigma_i >= rho of v_i v_i^T",
            "P_weak": "I - P_data",
            "rho": 1.0,
            "reporting_rule": "errors reported separately; a weak-subspace "
                              "improvement is never described as measured recovery",
        },

        "paired_comparison": {
            "rule": "same truth and the same coupled resolved noise draw across arms",
            "primary": "RESOLVED_PHYSICAL - DIRECT_PHYSICAL",
            "secondary": ["UNRESOLVED_IMAGE - DIRECT_PHYSICAL",
                          "TOTAL_FLUX - DIRECT_PHYSICAL"],
            "bootstrap": {"n_resamples": 2000, "unit": "truth",
                          "preserves": "all noise draws belonging to a truth",
                          "seed_stream": "bootstrap"},
        },

        "null_pairs": {
            "targets": [0.25, 0.5, 1.0, 2.0, 4.0],
            "bayes_bound": "P_Bayes = Phi(delta/2) at equal priors",
            "defect_rule": "a method exceeding the equal-prior data-only Bayes "
                           "bound by more than Monte Carlo tolerance is an "
                           "instrumentation or leakage defect, not a success",
            "incremental_history_pairs":
                "pairs constructed weak under DIRECT_PHYSICAL and stronger under "
                "RESOLVED_PHYSICAL, to test whether higher orders create usable "
                "discriminability",
        },

        "seeds": {
            "master": MASTER_SEED,
            "streams": SEED_STREAMS,
            "derivation": "numpy SeedSequence(MASTER_SEED).spawn keyed by the "
                          "stream offset; every truth also carries a content hash",
            "content_hash_method":
                "sha256 over the canonical JSON of the family name and the "
                "rounded parameter dict, so two truths with identical physical "
                "parameters hash identically regardless of which split drew them",
        },

        "stop_conditions": ["IMPLEMENTATION_DEFECT", "QUADRATURE_NOISE_DEFECT",
                            "CROSS_GEOMETRY_SCHEMA_DEFECT", "DATA_SPLIT_LEAKAGE",
                            "UNCALIBRATED_UNCERTAINTY",
                            "NULL_PAIR_CALIBRATION_DEFECT"],
        "note_on_weak_result": "a weak or absent validation gain is a scientific "
                               "pilot result, not an implementation defect",
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(freeze, indent=2, default=float) + "\n")
    digest = hashlib.sha256(OUT.read_bytes()).hexdigest()
    print(f"wrote {OUT.relative_to(ROOT)}")
    print(f"  freeze sha256 {digest}")
    print(f"  start commit  {freeze['provenance']['start_commit']}")
    print(f"  branch        {freeze['provenance']['branch']}")
    print(f"  support       r in [{r_in:.3f}, {r_out:.3f}] M")
    print(f"  old band      a > {a0_999:.3f} M")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
