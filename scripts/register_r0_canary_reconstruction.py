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
from phrt.sources.physical_basis import (DEFAULT_N_AZIMUTHAL,
                                         DEFAULT_N_RADIAL,
                                         DEFAULT_N_TEMPORAL,
                                         PhysicalBasis)
from phrt.metrics.age_intervals import AMENDMENT as AGE_AMENDMENT
from phrt.metrics.age_intervals import observation_anchor

OUT = ROOT / "artifacts" / "configs" / "R0_CANARY_RECONSTRUCTION_PILOT_FREEZE.json"
ACCEPTED_BASE = "0ef341dae3b21bc2bdd0e54a18971cff208af783"
# The nine provenance fields the activation ruling requires on the freeze and on
# every result manifest. Pinned literally; four of them the ruling states.
MEASUREMENT_CORRECTION_COMMIT = "d6869f8d1c08889fee34e91d392c2bbc1bc9a62f"
E3C_EXECUTION_CODE_COMMIT = "546763ed29e2be3fb129ec707cb07ee37a4f7db8"
E3C_ARTIFACT_COMMIT = "7d610121adc95fb641ab5692d37d2b761b082039"
E3C_FREEZE_SHA256 = ("7ab28bcd14674fb6544b577f19c00301f09e45ffec805cfcc"
                     "29896c53634bf1b")
E3C_REGISTRY_SHA256 = ("2ba66f0209fe1cdec97b8cf5862494c22fb94704318f9601a"
                       "7a1f9eb4b783796")
TEMPLATE = ("schemas/R0_CANARY_RECONSTRUCTION_PILOT_FREEZE_TEMPLATE_v1.0.json")
# Null until the amendment commit exists; then pinned literally. See the note
# recorded next to the field in the freeze.
AGE_AMENDMENT_COMMIT = "f034f19829623efa1f29bdcf27f95e10bd2de62e"
# The tree state the pilot started from, pinned rather than read from HEAD:
# re-running the registration after the freeze commit would otherwise move
# the recorded start commit forward and misdescribe where the work began.
START_COMMIT = "7d610121adc95fb641ab5692d37d2b761b082039"
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


def leaves(node, prefix: str = ""):
    """Every leaf path of the launch template, as dotted keys."""
    if isinstance(node, dict) and node:
        for k, v in node.items():
            yield from leaves(v, f"{prefix}.{k}" if prefix else k)
    else:
        yield prefix, node


def dig(doc: dict, path: str):
    cur = doc
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None, False
        cur = cur[part]
    return cur, True


def check_template(freeze: dict) -> list[str]:
    """Every template leaf must map to a filled value in the freeze.

    The template ships with ``null`` and ``FILL...`` markers. This refuses to
    register a freeze in which any of them survived, or in which a mapping
    points at a key that does not exist -- either way the freeze would look
    complete while leaving a registered choice open.
    """
    tpl = json.loads((ROOT / TEMPLATE).read_text())
    mapping = freeze["template_conformance"]
    bad = []
    for path, _ in leaves(tpl):
        # a template leaf under a mapped parent is covered by that parent
        target = None
        for depth in range(path.count(".") + 1, 0, -1):
            head = ".".join(path.split(".")[:depth])
            if head in mapping:
                target = mapping[head]
                break
        if target is None:
            bad.append(f"{path}: no entry in template_conformance")
            continue
        value, present = dig(freeze, target)
        if not present:
            bad.append(f"{path} -> {target}: missing from the freeze")
        elif value is None or (isinstance(value, str)
                               and value.upper().startswith("FILL")):
            bad.append(f"{path} -> {target}: still unfilled ({value!r})")
    return bad


def main() -> int:
    reg = load_registry()
    prov = provenance.collect()
    sup = canary_support()
    r_in, r_out = sup["r_inner_M"], sup["r_outer_M"]
    t_obs = list(np.linspace(0.0, OBSERVER_SPAN, N_OBSERVER_TIMES))
    max_delay = max(w[1] for w in sup["delay_windows_M"].values())
    t_lo = float(min(t_obs) - max_delay) - 3.0 * PROBE_HALF_WIDTH
    t_hi = float(max(t_obs)) + 3.0 * PROBE_HALF_WIDTH

    # AGE_INTERVAL_SEMANTICS_AMENDMENT_003. The anchor is frozen here, from the
    # reachable source-time window of this observation, before a single movie
    # exists -- so it cannot be chosen to flatter a depth curve later.
    age_grid = np.arange(0.0, max_delay + OBSERVER_SPAN + 3.0 * PROBE_HALF_WIDTH,
                         AGE_STEP)
    anchor = observation_anchor(age_grid, PROBE_HALF_WIDTH, t_obs,
                                list(sup["delay_windows_M"].values()))
    if not anchor["admissible"]:
        raise SystemExit("no admissible probe centre on the R0 age grid")
    a_anchor = float(anchor["a_anchor_M"])

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
            "start_commit": START_COMMIT,
            "head_at_registration": git("rev-parse", "HEAD"),
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

            # The nine fields the activation ruling requires the freeze and
            # every result manifest to record separately. The execution commit
            # and the artifact commit are kept apart on purpose: one is the code
            # that ran E3C, the other is the tree its outputs were committed in,
            # and a single ambiguous "commit" field cannot say which is which.
            "accepted_base_commit": ACCEPTED_BASE,
            "measurement_correction_commit": MEASUREMENT_CORRECTION_COMMIT,
            "e3c_execution_code_commit": E3C_EXECUTION_CODE_COMMIT,
            "e3c_artifact_commit": E3C_ARTIFACT_COMMIT,
            "e3c_age_interval_amendment_commit": AGE_AMENDMENT_COMMIT,
            "e3c_age_interval_amendment_commit_note":
                "The amendment, its tests, the reassembled derived E3C tables "
                "and this freeze are committed together, so this field names the "
                "commit that contains this very file. A commit cannot carry its "
                "own hash: it is null in that commit and pinned literally in the "
                "single-file commit immediately after, which changes nothing "
                "else.",
            "head_before_amendment_commit": (
                git("rev-parse", f"{AGE_AMENDMENT_COMMIT}^")
                if AGE_AMENDMENT_COMMIT else git("rev-parse", "HEAD")),
            "e3c_freeze_sha256": E3C_FREEZE_SHA256,
            "e3c_registry_sha256": E3C_REGISTRY_SHA256,
            "ray_map_manifest_sha256": None,   # filled below, over the digests
            "r0_config_sha256": None,          # filled below, over this document
            "self_digest_rule":
                "r0_config_sha256 is sha256 over the canonical JSON of this "
                "document with r0_config_sha256 itself set to null, so the field "
                "can live inside the document it describes; "
                "ray_map_manifest_sha256 is sha256 over the canonical JSON of "
                "the sorted physical_model.raymap_sha256 map",
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

        "source_class": {
            "id": "C224",
            "dimension": int(PhysicalBasis(r_in, r_out, t_lo, t_hi).dimension),
            "n_radial": DEFAULT_N_RADIAL,
            "n_azimuthal": DEFAULT_N_AZIMUTHAL,
            "n_temporal": DEFAULT_N_TEMPORAL,
            "factorization": f"{DEFAULT_N_RADIAL} cubic B-splines in log r x "
                             f"{DEFAULT_N_AZIMUTHAL} real Fourier modes "
                             f"(|m| <= {(DEFAULT_N_AZIMUTHAL - 1) // 2}) x "
                             f"{DEFAULT_N_TEMPORAL} DCT modes in source time",
            "column_order": "radial-major, then azimuthal, then temporal",
            "radial_support_M": [r_in, r_out],
            "temporal_support_M": [t_lo, t_hi],
            "basis_sha256": hashlib.sha256(json.dumps(
                {"n_radial": DEFAULT_N_RADIAL,
                 "n_azimuthal": DEFAULT_N_AZIMUTHAL,
                 "n_temporal": DEFAULT_N_TEMPORAL,
                 "r_inner_M": r_in, "r_outer_M": r_out,
                 "t_min_M": t_lo, "t_max_M": t_hi},
                sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
            "synthesis_rule": "Q_C is applied exactly once; the class is the "
                              "same object in every arm",
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
            "source_class_factorization": {
                "n_radial": 4, "n_azimuthal": 3, "n_temporal": 4, "dimension": 48,
                "constraint": "the radial factor is a cubic B-spline basis, so "
                              "n_radial >= 4 is required; a 2 x 3 x 8 "
                              "factorization of the same dimension is not "
                              "constructible and raises rather than silently "
                              "degrading the basis"},
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
                "probe_half_width_M": PROBE_HALF_WIDTH,
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
            "resolved_ranges_note":
                "the block below is the fully expanded form the runner reads; "
                "no range is resolved at run time from a 'same_ranges_as' "
                "reference, so what was frozen is exactly what is used",
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
                    "maximize T_stable_anchor(epsilon=0.50, q=0.90)",
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
            "age_grid_step_M": AGE_STEP,
            "age_grid_max_M": float(np.ceil((max_delay - min(t_obs)) / AGE_STEP)
                                    * AGE_STEP),
            "age_grid_rule": "the oldest age any ray in the frozen set carries, "
                             "max(delay) - min(t_obs), rounded up to the age "
                             "step. Ages beyond it are unreachable by "
                             "construction, so a depth sitting on the ceiling is "
                             "right-censored and reported as a lower bound",
            "E_of_a": "||W_a(xhat - x)||_2 / max(||W_a x||_2, eta)",
            "E_abs_of_a": "||W_a(xhat - x)||_2",
            "eta_rule": "0.05 * median over prior-fit truths and ages with "
                        "||W_a x|| > 0 of ||W_a x||_2, frozen before scoring",
            "eta_value": None,
            "stable_depth_surface": {"epsilon": [0.25, 0.35, 0.50],
                                     "q": [0.80, 0.90, 0.95]},
            "age_interval_amendment": AGE_AMENDMENT,
            "a_anchor_M": a_anchor,
            "anchor_rule": anchor["rule"],
            "anchor_derivation": {
                "probe_centre": "a probe at age a occupies source time -a "
                                "within 3 half widths",
                "reachable_source_time_M": [anchor["source_time_min_M"],
                                            anchor["source_time_max_M"]],
                "delay_min_M": anchor["delay_min_M"],
                "delay_max_M": anchor["delay_max_M"],
                "frozen_before": "any movie is rendered or any error curve exists",
            },
            "primary_point": "T_stable_anchor(epsilon=0.50, q=0.90)",
            "T_stable_anchor":
                "sup { T >= a_anchor : Pr[ sup_{a_anchor <= a <= T} E(a) <= "
                "epsilon ] >= q }. The supremum over the age window is inside "
                "the probability and is taken per truth: a truth counts only if "
                "the whole window from the anchor out to T is good for that "
                "truth. Thresholding the per-age passing fraction instead asks "
                "a weaker question and is not what is reported.",
            "L_stable_anchor": "T_stable_anchor - a_anchor",
            "secondary_unanchored_interval":
                "a longest stable interval anywhere on the grid may be reported "
                "with both endpoints; it must not be called depth from the present",
            "also_reported": ["oldest_detectable_age_probe",
                              "longest_detectable_run_span_M with both endpoints",
                              "contiguous_detectable_span_from_anchor_M",
                              "recent/middle/old band errors",
                              "data-supported and weak-subspace errors",
                              "calibration and coverage", "runtime",
                              "iterations", "peak memory"],
            "withheld_from_the_launch_list": {
                "fields": ["D_hist(T)", "d_eff(T)"],
                "reason": "PAPER_I_V2_PRE_E3C_AMENDMENT_001 item 6 reserves "
                          "D_hist, d_eff and the retired alias effective_rank "
                          "for E3D, and the activation ruling restates that they "
                          "are E3D quantities. E3D is deferred and not started, "
                          "so R0 does not emit them under any name. The interval "
                          "statistics above replace them in the R0 return.",
            },
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

    # Expand every family to explicit numeric ranges. A reference like
    # "same_ranges_as" would have to be resolved at run time, and a freeze whose
    # meaning depends on run-time resolution is not frozen.
    fam = freeze["source_families"]["families"]
    spot = {"r_centre_M": fam["single_orbiting_hotspot"]["r_centre_M"],
            "sigma_r_M": fam["single_orbiting_hotspot"]["sigma_r_M"],
            "sigma_phi_rad": fam["single_orbiting_hotspot"]["sigma_phi_rad"]}
    resolved = {
        "single_orbiting_hotspot": dict(spot),
        "two_independent_hotspots": dict(spot),
        "rotating_asymmetric_crescent": {
            "r_peak_M": fam["rotating_asymmetric_crescent"]["r_peak_M"],
            "width_M": fam["rotating_asymmetric_crescent"]["width_M"],
            "asymmetry_modes": fam["rotating_asymmetric_crescent"]["asymmetry_modes"]},
        "correlated_extended_field": {
            "radial_correlation_M":
                fam["correlated_extended_field"]["radial_correlation_M"],
            "azimuthal_modes": fam["correlated_extended_field"]["azimuthal_modes"]},
        "moving_flare_birth_decay": {
            **spot,
            "rise_M": fam["moving_flare_birth_decay"]["rise_M"],
            "decay_M": fam["moving_flare_birth_decay"]["decay_M"]},
    }
    resolved["off_grid_refinement"] = float(
        freeze["source_families"]["off_grid"]["refinement_factor"])
    freeze["source_families"]["resolved_ranges"] = resolved
    freeze["source_families"]["baseline_intensity"] = 1.0

    # ---- template conformance ------------------------------------------
    # The launch shipped a skeleton with null and FILL markers. Rather than
    # rename this freeze's keys to match it and lose the more explicit names,
    # every leaf of the template is mapped to the place in this document that
    # satisfies it, and the mapping is checked mechanically. A template leaf
    # with no entry, or an entry pointing at a missing or still-unfilled value,
    # fails registration.
    freeze["template"] = TEMPLATE
    freeze["template_conformance"] = {
        "schema_version": "schema",
        "phase": "experiment_id",
        "profile": "experiment_id",
        "status": "provenance.r0_config_sha256",
        "identity.repository": "provenance.repository",
        "identity.start_commit": "provenance.start_commit",
        "identity.branch": "provenance.branch",
        "identity.environment_hash": "environment.environment_sha256",
        "identity.hardware": "environment.hardware",
        "governance.amendment": "governance.amendments",
        "governance.geometry_wide_claim_forbidden": "scope.forbidden_language",
        "governance.main_test_scoring_forbidden": "scope.not_authorized",
        "governance.ml_forbidden": "estimators.not_authorized",
        "geometry.geometry_id": "physical_model.geometry",
        "geometry.spin": "physical_model.spin",
        "geometry.inclination_deg": "physical_model.inclination_deg",
        "geometry.orders": "physical_model.orders",
        "geometry.map_manifest_hash": "provenance.ray_map_manifest_sha256",
        "source_class.name": "physical_model.source_class",
        "source_class.dimension": "source_class.dimension",
        "source_class.radial_modes": "source_class.n_radial",
        "source_class.azimuthal_real_modes": "source_class.n_azimuthal",
        "source_class.temporal_modes": "source_class.n_temporal",
        "source_class.basis_hash": "source_class.basis_sha256",
        "source_class.radial_support_M": "source_class.radial_support_M",
        "source_class.temporal_support_M": "source_class.temporal_support_M",
        "operator.operator_hashes": "physical_model.raymap_sha256",
        "operator.whitened_row": "physical_model.whitened_row",
        "operator.noise_density": "physical_model.noise",
        "operator.arm_specific_noise_scale_forbidden": "physical_model.noise",
        "operator.g10q_required": "gates.R0_G3_G10q_quadrature_noise_invariance",
        "snr0_grid": "physical_model.snr0_grid",
        "observation_arms": "observation.arms_primary",
        "diagnostic_arms": "observation.arms_diagnostic",
        "source_families.prior_fit": "split.prior_fit_families",
        "source_families.held_out_ood": "split.held_out_ood_family",
        "source_families.control": "split.control_families",
        "source_families.parameter_ranges": "source_families.resolved_ranges",
        "source_families.positivity_rule": "source_families.positivity_construction",
        "source_families.off_grid_rule": "source_families.off_grid",
        "pilot_counts": "pilot_counts",
        "null_pair_targets": "null_pairs.targets",
        "estimators.required": "estimators.required",
        "estimators.conditional": "estimators.conditional",
        "estimators.forbidden": "estimators.not_authorized",
        "estimators.hyperparameter_grids": "hyperparameter_grids",
        "estimators.selection_rule": "hyperparameter_grids.selection.objective_lexicographic",
        "metrics.epsilon_grid": "metrics.stable_depth_surface.epsilon",
        "metrics.q_grid": "metrics.stable_depth_surface.q",
        "metrics.primary_epsilon": "metrics.stable_depth_surface.epsilon",
        "metrics.primary_q": "metrics.stable_depth_surface.q",
        "metrics.eta_rule": "metrics.eta_rule",
        "metrics.old_band_rule": "metrics.old_band_rule",
        "metrics.projector_rule": "subspaces.P_data",
        "metrics.right_censoring_required": "gates.R0_G7_right_censoring",
        "splits.seed_bank": "seeds.streams",
        "splits.content_hash_method": "seeds.content_hash_method",
        "splits.future_main_test_hash_commitment": "split.future_main_test",
        "splits.test_truth_access_forbidden": "split.test_truth_access",
        "correctness_gates": "gates",
        "artifact_policy": "artifact_policy",
    }

    # fields the template asks for that this freeze did not previously name
    freeze["provenance"]["repository"] = "internalerror404/photon-ring-tomography"
    freeze["governance"] = {
        "amendments": ["PAPER_I_V2_PRE_E3C_AMENDMENT_001",
                       "PAPER_I_V2_RECONSTRUCTION_AMENDMENT_002",
                       AGE_AMENDMENT],
        "ruling": "PAPER_I_R0_ACTIVATION_AFTER_E3C_V2 v1.2",
        "geometry_wide_claim_forbidden": True,
        "main_test_scoring_forbidden": True,
        "ml_forbidden": True,
    }
    freeze["split"]["control_families"] = ["near_null_combinations"]
    freeze["split"]["test_truth_access"] = (
        "forbidden. The R1 main test truths are committed by content hash only; "
        "they are neither rendered nor scored in R0")
    freeze["split"]["future_main_test"] = (
        "a hash commitment over the R1 test truth parameters is written from the "
        "future_main_test seed stream without rendering or scoring any of them")
    freeze["artifact_policy"] = {
        "figures_from_canonical_tables_only": True,
        "test_truth_hyperparameter_tuning_forbidden": True,
        "posthoc_threshold_change_forbidden": True,
        "failed_artifacts_preserved": True,
        "sha256_manifest_required": True,
    }
    freeze["metrics"]["primary_epsilon"] = 0.50
    freeze["metrics"]["primary_q"] = 0.90

    # ---- the two self-referential digests -------------------------------
    freeze["provenance"]["ray_map_manifest_sha256"] = hashlib.sha256(
        json.dumps(freeze["physical_model"]["raymap_sha256"], sort_keys=True,
                   separators=(",", ":")).encode()).hexdigest()
    freeze["provenance"]["r0_config_sha256"] = None
    freeze["provenance"]["r0_config_sha256"] = hashlib.sha256(
        json.dumps(freeze, sort_keys=True, separators=(",", ":"),
                   default=float).encode()).hexdigest()

    unfilled = check_template(freeze)
    if unfilled:
        raise SystemExit("template not satisfied: " + "; ".join(unfilled))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(freeze, indent=2, default=float) + "\n")
    digest = hashlib.sha256(OUT.read_bytes()).hexdigest()
    print(f"wrote {OUT.relative_to(ROOT)}")
    print(f"  freeze file sha256   {digest}")
    print(f"  r0_config_sha256     {freeze['provenance']['r0_config_sha256']}")
    print(f"  ray_map_manifest     {freeze['provenance']['ray_map_manifest_sha256']}")
    print(f"  a_anchor_M           {a_anchor:g}")
    print(f"  start commit  {freeze['provenance']['start_commit']}")
    print(f"  branch        {freeze['provenance']['branch']}")
    print(f"  support       r in [{r_in:.3f}, {r_out:.3f}] M")
    print(f"  old band      a > {a0_999:.3f} M")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
