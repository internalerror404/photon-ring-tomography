#!/usr/bin/env python3
"""Register the R0C repaired source-and-calibration freeze.

R0_REPAIR_AMENDMENT_004. The R0B pilot is accepted as positive validation
evidence, but three things it measured were not what they claimed to be, and one
thing it asserted was not checked. This freeze fixes all four before any new
truth is generated, and is committed with a clean tree so that the attestation
means something this time.

Nothing here renders a repair-validation truth. The future main-test bank is
generated, projected and hashed -- projection is what makes an exact-in-class
truth exist at all -- but no operator is ever applied to it, no statistic is
formed from it and no score is computed. That distinction is recorded in the
commitment itself rather than left to a reader's charity.
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
from phrt.attestation import attest
from phrt.config import load_registry
from phrt.governance import r0_provenance
from phrt.metrics.scoring import evaluation_grid
from phrt.sources.bank import BankContext, build_split
from phrt.sources.in_span import (IN_SPAN_TOLERANCE, constant_coefficients,
                                  in_span_movie, in_span_residual)
from phrt.sources.physical_basis import PhysicalBasis

PILOT = ROOT / "artifacts" / "configs" / "R0_CANARY_RECONSTRUCTION_PILOT_FREEZE.json"
OUT = ROOT / "artifacts" / "configs" / "R0C_REPAIRED_SOURCE_AND_CALIBRATION_FREEZE.json"
COMMIT_OUT = ROOT / "artifacts" / "manifests" / "r0c_future_test_hash_commitment.json"
SUPERSEDED = ROOT / "artifacts" / "manifests" / "r0_future_test_hash_commitment.json"

ACCEPTED_PILOT_ARTIFACT_COMMIT = "8345068676b15ce8f96a76da9d92b159db215f1d"
AMENDMENT = "R0_REPAIR_AMENDMENT_004"

PRIOR_FIT = ("single_orbiting_hotspot", "two_independent_hotspots",
             "rotating_asymmetric_crescent", "correlated_extended_field")
OOD = "moving_flare_birth_decay"

# Four regimes, so family shift and representation mismatch are separate axes.
REGIMES = {
    "IN_CLASS_ID": {"families": list(PRIOR_FIT), "in_span": True,
                    "off_grid": False, "per_family": 128},
    "IN_CLASS_OOD": {"families": [OOD], "in_span": True,
                     "off_grid": False, "per_family": 256},
    "OFF_GRID_ID": {"families": list(PRIOR_FIT), "in_span": False,
                    "off_grid": True, "per_family": 64},
    "OFF_GRID_OOD": {"families": [OOD], "in_span": False,
                     "off_grid": True, "per_family": 256},
}

MASTER_SEED = 20260901
# New offsets. Reusing the pilot's would make a repaired truth collide with a
# pilot truth of the same index, which the disjointness gate would then have to
# excuse rather than enforce.
SEED_STREAMS = {
    "prior_fit_train": 11000,
    "uncertainty_calibration": 12000,
    "repair_validation": 13000,
    "null_pairs": 14000,
    "noise_draws": 15000,
    "bootstrap": 16000,
    "future_main_test": 19000,
}
GENERATOR_VERSION = "r0c-in-span-v1"


def git(*a: str) -> str:
    return subprocess.run(["git", *a], cwd=ROOT, capture_output=True,
                          text=True).stdout.strip()


def canonical(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      default=float).encode()


def main() -> int:
    t0 = time.time()
    reg = load_registry()
    prov = provenance.collect()
    pilot = json.loads(PILOT.read_text())
    sc = pilot["source_class"]

    basis = PhysicalBasis(*sc["radial_support_M"], *sc["temporal_support_M"])
    rq, pq, tq = evaluation_grid(basis.r_inner, basis.r_outer,
                                 basis.t_min, basis.t_max)
    design = basis.design(rq, pq, tq)
    const_coef, const_resid = constant_coefficients(design)
    if const_resid > IN_SPAN_TOLERANCE:
        print(f"STOP: the class does not hold a constant "
              f"(relative residual {const_resid:.2e}); the positivity lift "
              f"would leave the span")
        return 2
    ctx = BankContext(pilot["source_families"]["resolved_ranges"],
                      (basis.r_inner, basis.r_outer), (basis.t_min, basis.t_max))

    # ---- future main test: generated, projected and hashed; never scored ----
    test_records, in_span_devs = [], []
    for regime, spec in REGIMES.items():
        for fam in spec["families"]:
            movies = build_split(fam, "future_main_test", 64, MASTER_SEED,
                                 SEED_STREAMS["future_main_test"], ctx,
                                 off_grid=spec["off_grid"])
            for m in movies:
                rec = {"regime": regime, "family": fam,
                       "in_span": spec["in_span"], "off_grid": spec["off_grid"],
                       "parameter_hash": m.content_hash}
                if spec["in_span"]:
                    ism = in_span_movie(m, basis, rq, pq, tq, const_coef)
                    dev = in_span_residual(ism, design, rq, pq, tq)
                    in_span_devs.append(dev)
                    rec.update({
                        "parameter_hash": ism.content_hash,
                        "parent_parameter_hash": m.content_hash,
                        "coefficient_hash": hashlib.sha256(
                            np.ascontiguousarray(
                                ism.extra["coefficients"], dtype="<f8"
                            ).tobytes()).hexdigest(),
                        "lift_applied": ism.extra["lift_applied"],
                        "in_span_residual": dev})
                test_records.append(rec)
    worst_in_span = max(in_span_devs) if in_span_devs else 0.0
    if worst_in_span > IN_SPAN_TOLERANCE:
        print(f"STOP: an in-span test truth has residual {worst_in_span:.2e}, "
              f"above the amendment tolerance {IN_SPAN_TOLERANCE:g}")
        return 3

    commitment_payload = {
        "generator_version": GENERATOR_VERSION,
        "source_family_parameter_record": pilot["source_families"]["resolved_ranges"],
        "projection_rule": "an in-span truth is Q_C x: the analytic family is "
                           "projected onto C224 on the declared evaluation grid, "
                           "the coefficient vector is kept, and the synthesised "
                           "movie is the truth at every coordinate",
        "in_span_rule": f"relative residual below {IN_SPAN_TOLERANCE:g}",
        "analytic_rendering_rule": "an off-grid truth is rendered analytically "
                                   "at a feature scale a factor "
                                   f"{ctx.ranges['off_grid_refinement']:g} finer "
                                   "than the finest scale C224 can represent, "
                                   "and is never projected",
        "positivity_rule": "a constant is in the class to 1e-15, so a negative "
                           "excursion after projection is lifted by a multiple "
                           "of the constant's coefficient vector; the lift is "
                           "recorded per truth",
        "baseline_intensity": pilot["source_families"]["baseline_intensity"],
        "records": test_records,
    }
    commitment = hashlib.sha256(canonical(commitment_payload)).hexdigest()

    superseded = None
    if SUPERSEDED.exists():
        old = json.loads(SUPERSEDED.read_text())
        superseded = {
            "path": str(SUPERSEDED.relative_to(ROOT)),
            "commitment_sha256": old.get("commitment_sha256"),
            "file_sha256": hashlib.sha256(SUPERSEDED.read_bytes()).hexdigest(),
            "disposition": "SUPERSEDED_R0_PILOT_TEST_COMMITMENT",
            "reason": "recorded 320 parameter hashes under the pilot's source "
                      "construction, in which no truth was in the span of C224. "
                      "The generator semantics changed, so the commitment can no "
                      "longer describe the bank it names. Preserved permanently, "
                      "never scored, never reused",
        }

    COMMIT_OUT.write_text(json.dumps({
        "schema": "phrt-r0c-test-commitment/1",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "amendment": AMENDMENT,
        "commitment_sha256": commitment,
        "n_records": len(test_records),
        "n_per_regime": {k: sum(1 for r in test_records if r["regime"] == k)
                         for k in REGIMES},
        "worst_in_span_residual": worst_in_span,
        "rendered_for_projection_and_hashing_only": True,
        "operator_applied": False,
        "statistic_formed": False,
        "estimate_computed": False,
        "scored": False,
        "note": "an exact-in-class truth cannot be hashed without being "
                "projected, and projection requires rendering. Rendering is "
                "where it stops: no operator is applied to any record here, no "
                "sufficient statistic is formed and no score exists",
        "supersedes": superseded,
        "payload": commitment_payload,
    }, indent=2, default=float) + "\n")

    # ---- the freeze --------------------------------------------------------
    fz = {
        "schema": "phrt-r0c-repair-freeze/1",
        "experiment_id": "R0C_REPAIRED_SOURCE_AND_CALIBRATION",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "amendment": AMENDMENT,
        "parent_freeze_sha256": hashlib.sha256(PILOT.read_bytes()).hexdigest(),
        "accepted_pilot_artifact_commit": ACCEPTED_PILOT_ARTIFACT_COMMIT,

        "provenance": {**r0_provenance(),
                       "r0c_registration_commit": None,
                       "branch": git("rev-parse", "--abbrev-ref", "HEAD"),
                       "head_at_registration": git("rev-parse", "HEAD"),
                       "registry_sha256": reg.sha256,
                       "environment_sha256": prov.environment_sha256,
                       "self_digest_rule":
                           "r0c_config_sha256 is sha256 over the canonical JSON "
                           "of this document with that field set to null"},

        "scope": {
            "authorized": ["R0A_CORRECTNESS_RERUN", "R0C_REPAIRED_VALIDATION"],
            "not_authorized": ["R1_MAIN", "E3D", "R2", "R3", "R4", "R5", "VLBI",
                               "geometry_mismatch", "order_leakage", "ML"],
            "restriction": "single canary geometry a* = 0.5, i = 50 deg, "
                           "class C224; validation only",
            "forbidden_language": "no result may be described as geometry-wide "
                                  "or as arbitrary movie recovery",
            "held_out_main_test": "generated and hashed only; never rendered "
                                  "into data, never scored",
        },

        "endpoint": {
            "primary": {"epsilon": 0.25, "quantile": 0.95,
                        "statistic": "L_stable_anchor",
                        "label": "VALIDATION_SELECTED_PRIMARY_FROM_PREREGISTERED_SURFACE",
                        "justification":
                            "R0B was validation only, the whole 3 x 3 "
                            "(epsilon, q) surface was frozen before it ran, this "
                            "cell is a member of that surface, and no main-test "
                            "truth was scored. Validation selection from a "
                            "preregistered endpoint family, not post-hoc test "
                            "selection",
                        "frozen_now": "no further cell may be selected after R0C"},
            "retired": {"epsilon": 0.50, "quantile": 0.90,
                        "disposition": "NONDISCRIMINATING_RIGHT_CENSORED_ENDPOINT",
                        "reason": "the best reconstruction for every arm reached "
                                  "the 120 M physical ceiling at every SNR, so "
                                  "the arm comparison was between censored "
                                  "values. Retained in every table; never "
                                  "described as a failed comparison",
                        "retained_in_tables": True},
            "surface": {"epsilon": [0.25, 0.35, 0.50], "q": [0.80, 0.90, 0.95],
                        "reported_in_full": True},
            "reference_snr": 100.0,
        },

        "source_regimes": {
            k: {**v,
                "meaning": ("exactly in the span of C224" if v["in_span"]
                            else "analytic, outside the span of C224"),
                "family_axis": ("prior-fit families" if OOD not in v["families"]
                                else "held-out flare family")}
            for k, v in REGIMES.items()},
        "regime_rationale":
            "family shift and representation mismatch are orthogonal axes. The "
            "pilot's single OOD arm confounded them: its in-class truths were "
            "analytic and carried a structure-normalized representation residual "
            "of 0.406 to 0.426, so the class itself had zero structure-normalized "
            "stable span and the experiment partly measured basis mismatch",

        "in_span_construction": {
            "rule": commitment_payload["projection_rule"],
            "positivity": commitment_payload["positivity_rule"],
            "constant_in_class_relative_residual": const_resid,
            "gate": "R0_G14_in_span_membership",
            "tolerance": IN_SPAN_TOLERANCE,
            "applies_to": ["IN_CLASS_ID", "IN_CLASS_OOD"],
        },

        "refit_on_repaired_bank": {
            "required": ["prior_fit_covariance", "state_space_process_noise",
                         "eta", "eta_structure", "regularization_selection",
                         "representation_floor", "repair_validation_hashes"],
            "reason": "every one of these depends on the source bank, and the "
                      "bank's generator semantics changed. Carrying the pilot's "
                      "values across would tune the repaired experiment on the "
                      "distribution it no longer uses",
            "pilot_values_carried_over": [],
        },

        "uncertainty_calibration": {
            "rule": "at most one declared covariance-scaling rule per estimator "
                    "family: cov -> s * cov, with a single scalar s per family",
            "fitted_on": "uncertainty_calibration split",
            "evaluated_on": "repair_validation split",
            "objective": "match the mean squared Mahalanobis distance to its "
                         "expectation on the calibration split",
            "forbidden": "a separate scale per arm, per SNR or per source "
                         "family; that would make the uncertainty layer flexible "
                         "enough to fit anything",
            "acceptance_band_joint_ratio": [0.5, 2.0],
            "on_failure": "UNCERTAINTY_WITHDRAWN: the estimator is retained as a "
                          "point estimator only, and no credible interval, "
                          "posterior movie or coverage statement enters Paper I",
            "frozen_before": "any repair-validation truth is generated",
        },

        "splits": {
            "prior_fit_train": {"regime": "IN_CLASS_ID", "per_family": 512,
                                "role": "prior fit only"},
            "uncertainty_calibration": {"per_regime": 64,
                                        "role": "covariance scaling only"},
            "repair_validation": {"per_family_by_regime":
                                  {k: v["per_family"] for k, v in REGIMES.items()},
                                  "role": "all reported scores"},
            "future_main_test": {"per_regime_family": 64,
                                 "role": "hashed only; not rendered into data"},
            "disjointness": "content hash over family, parameters, in-span flag "
                            "and lift; checked pairwise across every split",
        },

        "seeds": {"master": MASTER_SEED, "streams": SEED_STREAMS,
                  "generator_version": GENERATOR_VERSION,
                  "note": "offsets differ from the pilot's so a repaired truth "
                          "cannot collide with a pilot truth of the same index"},

        "gates": {
            **pilot["gates"],
            "R0_G6a_declared_probe_unit_norm": 1e-12,
            "R0_G6b_independent_quadrature_crosscheck": 5e-3,
            "R0_G13_freeze_commit_attestation": "structural",
            "R0_G14_in_span_membership": IN_SPAN_TOLERANCE,
            "R0_G15_uncertainty_calibration_band": [0.5, 2.0],
        },
        "retired_gates": {
            "R0_G6_age_probe_normalization":
                "split by R0_REPAIR_AMENDMENT_004. One record carried the "
                "declared-normalisation name and the 1e-12 threshold while "
                "measuring a 4001-point quadrature cross-check, so the canonical "
                "table read as though 5.551e-5 < 1e-12. The probe itself was "
                "correct; the record was not",
        },

        "estimators": pilot["estimators"],
        "hyperparameter_grids": pilot["hyperparameter_grids"],
        "physical_model": pilot["physical_model"],
        "observation": pilot["observation"],
        "source_class": sc,
        # carried verbatim from the pilot freeze so the runner reads one
        # document; the parameter ranges themselves are unchanged, only how a
        # truth is constructed from them
        "source_families": pilot["source_families"],
        "metrics": {**pilot["metrics"],
                    "primary_point": "L_stable_anchor(epsilon=0.25, q=0.95)",
                    "primary_epsilon": 0.25, "primary_q": 0.95},
        "subspaces": pilot["subspaces"],
        "paired_comparison": pilot["paired_comparison"],
        "null_pairs": pilot["null_pairs"],
        "artifact_policy": pilot["artifact_policy"],

        "future_test_commitment_sha256": commitment,
        "superseded_test_commitment": superseded,

        "proposed_main_test_criterion": {
            "status": "PROPOSED_NOT_AUTHORIZED",
            "reference_snr": 100.0,
            "primary_scalar":
                "delta_L_stable = L_stable_anchor_resolved(0.25, 0.95) "
                "- L_stable_anchor_direct(0.25, 0.95) at SNR_0 = 100",
            "threshold_M": 8.0,
            "threshold_rationale": "two age-grid steps, against a pilot showing "
                                   "effects up to 44 M. One step at two "
                                   "consecutive SNRs is too weak for a "
                                   "paper-grade claim",
            "paired_bootstrap": "interval on the old-band error reduction must "
                                "exclude zero",
            "primary_estimator": "TSVD",
            "confirmatory_estimator": "RIDGE_IDENTITY",
            "secondary_estimators": ["TIKHONOV_TEMPORAL", "WIENER_GAUSSIAN",
                                     "LINEAR_STATE_SPACE"],
            "estimator_rationale": "a prior must not be able to manufacture the "
                                   "headline, so the primary and confirmatory "
                                   "estimators are prior-free",
            "aggregate_requirements": [
                "lower old-band absolute error",
                "lower old-band structure-normalized error",
                "lower data-supported error",
                "improvement in at least three of the four prior-fit families",
                "null-pair behaviour consistent with the Bayes bound"],
            "outcome_classification": {
                "R1_PASS": "exact-in-class and held-out-family reconstruction "
                           "both pass",
                "R1_PASS_WITH_SCOPE_RESTRICTION":
                    "exact-in-class passes; OOD or off-grid fails",
                "PRIOR_ASSISTED_NOT_DATA_RESOLVED":
                    "only Wiener or state-space passes, in weak directions",
                "R1_NEGATIVE_RESULT":
                    "the observability gain persists but stable reconstruction "
                    "does not",
                "IMPLEMENTATION_OR_LEAKAGE_DEFECT":
                    "a null-pair or split gate fails; no scientific "
                    "interpretation is drawn"},
        },

        "stop_conditions": ["R1_MAIN_RECOMMENDED",
                            "R1_MAIN_RECOMMENDED_WITH_SCOPE_RESTRICTION",
                            "R0_REPAIR_FAILED", "RECONSTRUCTION_NEGATIVE_RESULT"],
    }

    fz["provenance"]["r0c_config_sha256"] = None
    fz["provenance"]["r0c_config_sha256"] = hashlib.sha256(
        canonical(fz)).hexdigest()

    OUT.write_text(json.dumps(fz, indent=2, default=float) + "\n")
    att = attest([OUT, COMMIT_OUT, PILOT])
    print(f"wrote {OUT.relative_to(ROOT)}")
    print(f"  r0c_config_sha256   {fz['provenance']['r0c_config_sha256']}")
    print(f"  primary endpoint    epsilon=0.25 q=0.95 "
          f"({fz['endpoint']['primary']['label']})")
    print(f"  retired endpoint    epsilon=0.50 q=0.90 "
          f"({fz['endpoint']['retired']['disposition']})")
    print(f"  regimes             {list(REGIMES)}")
    print(f"  constant in class   relative residual {const_resid:.2e}")
    print(f"  test commitment     {commitment}")
    print(f"    {len(test_records)} records, worst in-span residual "
          f"{worst_in_span:.2e}, scored=False")
    if superseded:
        print(f"  superseded          {superseded['commitment_sha256'][:16]}... "
              f"{superseded['disposition']}")
    print(f"  tree clean          {att.get('clean')} "
          f"(tracked {att.get('n_tracked_changes')}, "
          f"untracked {att.get('n_untracked')})")
    print(f"total {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
