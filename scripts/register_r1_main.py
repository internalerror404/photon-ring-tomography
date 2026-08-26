#!/usr/bin/env python3
"""Register the R1 held-out main freeze.

The sealed bank is not touched here. Its commitment was written at R0C
registration under the corrected generator semantics, before any operator
existed for it, and this script only re-verifies that digest: it does not
regenerate the records, does not render them, and does not put them through an
operator. The null-pair control bank is generated and hashed separately, also
without being scored.

Everything a result could later be accused of having been chosen after the fact
is fixed here: the endpoint, the threshold, the estimator roles, the noise-draw
count, the bootstrap count and seed, and the disposition of uncertainty.
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

R0C = ROOT / "artifacts" / "configs" / "R0C_REPAIRED_SOURCE_AND_CALIBRATION_FREEZE.json"
COMMITMENT = ROOT / "artifacts" / "manifests" / "r0c_future_test_hash_commitment.json"
OUT = ROOT / "artifacts" / "configs" / "R1_MAIN_FREEZE.json"
NULL_OUT = ROOT / "artifacts" / "manifests" / "r1_null_pair_control_bank.json"

PINNED_COMMITMENT = ("93608e7a7578fe892269ac20297af5d3f22bc1f860bbdba71b9aa0a8"
                     "33aa3f1e")
R0C_ARTIFACT_COMMIT = "446fa00d0fadece4648118f29871bc615a16d9d7"
R0C_EXECUTION_COMMIT = "b6e481ab133015e9d7089fcbe6cfd81496200057"
RULING = "REVIEWER_RULING_R0C_005"

# Frozen before any main truth is scored.
N_NOISE_DRAWS = 8
BOOTSTRAP_RESAMPLES = 10000
BOOTSTRAP_SEED = 20260901
NULL_PAIR_SEED_STREAM = 21000
NULL_PAIRS_PER_TARGET = 200

# Retired by R0_REPAIR_AMENDMENT_004; must not appear in an active gate list.
RETIRED_GATES = ("R0_G6_age_probe_normalization",)


def canonical(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      default=float).encode()


def git(*a: str) -> str:
    return subprocess.run(["git", *a], cwd=ROOT, capture_output=True,
                          text=True).stdout.strip()


def main() -> int:
    t0 = time.time()
    reg = load_registry()
    prov = provenance.collect()
    r0c = json.loads(R0C.read_text())

    # ---- the sealed bank: verified, not regenerated ------------------------
    commit_doc = json.loads(COMMITMENT.read_text())
    got = commit_doc["commitment_sha256"]
    if got != PINNED_COMMITMENT:
        print(f"STOP: the main-test commitment on disk is {got}, the ruling "
              f"preserves {PINNED_COMMITMENT}")
        return 2
    recomputed = hashlib.sha256(canonical(commit_doc["payload"])).hexdigest()
    if recomputed != PINNED_COMMITMENT:
        print(f"STOP: the commitment does not hash its own payload "
              f"({recomputed})")
        return 2
    if commit_doc["scored"] or commit_doc["operator_applied"] \
            or commit_doc["statistic_formed"]:
        print("STOP: the sealed bank has already been touched by an operator")
        return 2
    per_regime = commit_doc["n_per_regime"]
    print(f"sealed bank verified: {commit_doc['n_records']} records, "
          f"{per_regime}, scored={commit_doc['scored']}")

    # ---- null-pair control bank: generated and hashed, never scored --------
    targets = [float(x) for x in r0c["null_pairs"]["targets"]]
    dimension = int(r0c["source_class"]["dimension"])
    null_records = []
    for target in targets:
        for i in range(NULL_PAIRS_PER_TARGET):
            rng = np.random.default_rng(
                [int(r0c["seeds"]["master"]), NULL_PAIR_SEED_STREAM,
                 int(round(target * 1000)), i])
            direction = rng.standard_normal(dimension)
            direction /= max(float(np.linalg.norm(direction)), 1e-300)
            null_records.append({
                "target_mahalanobis": target, "pair": i,
                "direction_hash": hashlib.sha256(
                    np.ascontiguousarray(direction, dtype="<f8")
                    .tobytes()).hexdigest()})
    null_payload = {
        "seed_stream": NULL_PAIR_SEED_STREAM,
        "master_seed": int(r0c["seeds"]["master"]),
        "targets": targets,
        "pairs_per_target": NULL_PAIRS_PER_TARGET,
        "construction": r0c["null_pairs"]["incremental_history_pairs"],
        "bayes_bound": r0c["null_pairs"]["bayes_bound"],
        "defect_rule": r0c["null_pairs"]["defect_rule"],
        "records": null_records,
    }
    null_hash = hashlib.sha256(canonical(null_payload)).hexdigest()
    NULL_OUT.write_text(json.dumps({
        "schema": "phrt-r1-null-control-bank/1",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "ruling": RULING,
        "control_bank_sha256": null_hash,
        "n_records": len(null_records),
        "rendered": False, "operator_applied": False, "scored": False,
        "note": "directions only, hashed before the main test. Amplitudes are "
                "solved at run time to realise each registered Mahalanobis "
                "separation, which is a property of the operator and not a "
                "choice",
        "payload": null_payload}, indent=2, default=float) + "\n")
    print(f"null-pair control bank: {len(null_records)} pairs, "
          f"sha256 {null_hash}")

    # ---- gates: retired names must not survive into an active list ---------
    gates = {k: v for k, v in r0c["gates"].items() if k not in RETIRED_GATES}
    dropped = [k for k in r0c["gates"] if k in RETIRED_GATES]

    fz = {
        "schema": "phrt-r1-main-freeze/1",
        "experiment_id": "R1_HELD_OUT_MAIN",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "ruling": RULING,
        "status": "FROZEN_BEFORE_ANY_MAIN_TRUTH_IS_SCORED",

        "provenance": {
            **r0_provenance(),
            "r0c_freeze_sha256": hashlib.sha256(R0C.read_bytes()).hexdigest(),
            "r0c_config_sha256": r0c["provenance"]["r0c_config_sha256"],
            "r0c_execution_commit": R0C_EXECUTION_COMMIT,
            "r0c_artifact_commit": R0C_ARTIFACT_COMMIT,
            "r1_registration_head": git("rev-parse", "HEAD"),
            "registry_sha256": reg.sha256,
            "environment_sha256": prov.environment_sha256,
            "commit_field_rule":
                "a run's identity is execution_commit, taken from the "
                "start-of-run attestation. manifest_build_commit is recorded "
                "separately and git_commit is deprecated",
            "r1_config_sha256": None,
        },

        "scope": {
            "authorized": ["R1_HELD_OUT_MAIN"],
            "not_authorized": ["R2", "R3", "R4", "R5", "E3D_rerun", "ML",
                               "geometry_mismatch", "order_leakage", "VLBI"],
            "geometry": "a050_i050", "spin": 0.5, "inclination_deg": 50.0,
            "source_class": "C224",
            "forbidden_language": "no result may be described as "
                                  "geometry-wide or as arbitrary movie recovery",
        },

        "sealed_bank": {
            "commitment_sha256": PINNED_COMMITMENT,
            "n_records": commit_doc["n_records"],
            "n_per_regime": per_regime,
            "rule": "preserved from R0C registration. Not regenerated, not "
                    "hardened, not inspected through the operator and not "
                    "scored before this freeze was committed",
            "off_grid_ood_caveat":
                "the OFF_GRID_OOD bank has a smaller representation floor "
                "than OFF_GRID_ID -- 0.016 to 0.115 against 0.803 to 0.814 "
                "structure-normalized in R0C. It is a mild-mismatch "
                "diagnostic. Its passing is not evidence of broad off-grid "
                "robustness and is not to be reported as such, and it is not "
                "replaced with a harder bank after the fact",
        },
        "null_pair_control_bank": {
            "sha256": null_hash, "n_pairs": len(null_records),
            "targets": targets, "pairs_per_target": NULL_PAIRS_PER_TARGET,
            "committed_before_scoring": True,
        },

        "primary": {
            "regime": "IN_CLASS_ID",
            "reference_snr": 100.0,
            "epsilon": 0.25, "quantile": 0.95,
            "statistic": "delta_L_level = L_stable_anchor(resolved) "
                         "- L_stable_anchor(direct) under the registered "
                         "baseline-inclusive metric",
            "metric_name": "baseline-inclusive historical field fidelity",
            "naming_rule":
                "at the reference SNR this is stable reconstruction of the "
                "age-local emissivity level under the registered "
                "baseline-inclusive field metric. It is not detailed movie "
                "morphology recovery and must not be described as such",
            "threshold_M": 8.0,
            "primary_estimator": "TSVD",
            "confirmatory_estimator": "RIDGE_IDENTITY",
            "family_rule": "at least three of the four IN_CLASS_ID prior-fit "
                           "families improve by at least 8 M",
            "success_requires": [
                "delta_L_level >= 8 M for TSVD",
                "delta_L_level >= 8 M in the same direction for ridge",
                "at least three of four prior-fit families improve by >= 8 M",
                "95% interval for aggregate delta_L_level with lower bound "
                "above zero",
                "95% interval for the direct-minus-resolved old-band "
                "normalized error reduction with lower bound above zero",
                "the same for the old-band absolute error",
                "lower error for resolved than direct inside the direct "
                "channel's own data subspace",
            ],
        },

        "bootstrap": {
            "kind": "paired truth-cluster",
            "unit": "truth; every noise draw belonging to a resampled truth "
                    "travels with it, because draws sharpen one history and "
                    "do not add histories",
            "n_resamples": BOOTSTRAP_RESAMPLES,
            "seed": BOOTSTRAP_SEED,
            "level": 0.95,
            "frozen_before_scoring": True,
        },

        "noise": {
            "draws_per_truth": N_NOISE_DRAWS,
            "noiseless_control": 1,
            "coupling": "the direct, unresolved and total-flux arms are "
                        "derived from the same resolved draw through the "
                        "declared linear readouts, so every arm comparison is "
                        "paired at the level of the draw",
            "independent_unit": "the truth, not the truth-noise pair",
        },

        "diagnostics": {
            "level_structure_projector": {
                "definition": "x = P_level x + P_structure x with P_level the "
                              "orthogonal projection onto fields constant in "
                              "space at each source time",
                "spanned_by": "the class's own temporal modes rendered "
                              "spatially uniform, so the subspace lies inside "
                              "C224",
                "reported": ["error_level_absolute", "error_level_normalized",
                             "error_structure_absolute",
                             "error_structure_normalized"],
                "status": "deterministic diagnostic; no threshold, no "
                          "tolerance and nothing to select on",
            },
            "common_direct_subspace": {
                "definition": "every arm's coefficient error projected onto "
                              "the direct channel's own P_data",
                "why": "each arm's P_data has its own dimension -- 154 for "
                       "direct and 202 for resolved in R0C -- so comparing "
                       "each arm on its own subspace penalises the arm that "
                       "sees more",
                "status": "deterministic diagnostic",
            },
            "structural_recovery_onset": {
                "definition": "the smallest SNR_0 on the frozen grid at which "
                              "L_stable_anchor under the structure metric "
                              "exceeds zero, reported for direct and resolved",
                "rule": "reported over the already frozen SNR grid; no new "
                        "SNR may be chosen after scoring",
            },
        },

        "secondary_outcomes": [
            "held-out family generalization on IN_CLASS_OOD",
            "structural recovery onset for direct and resolved",
            "both off-grid regimes preserved; a failure narrows the claim and "
            "does not invalidate an exact-in-class result",
            "null-pair controls against the equal-prior Gaussian Bayes bound "
            "under the multiplicity rule",
            "the full nine-cell endpoint surface, with the retired "
            "(0.50, 0.90) cell and its censoring disposition",
        ],

        "estimators": {
            "TSVD": "primary",
            "RIDGE_IDENTITY": "confirmatory",
            "TIKHONOV_TEMPORAL": "secondary",
            "WIENER_GAUSSIAN": "point estimate only",
            "LINEAR_STATE_SPACE": "point estimate only",
            "ML": "NOT_AUTHORIZED",
            "hyperparameters": "selected on the R0C repair-validation bank and "
                               "frozen; no re-tuning on any main-test truth",
        },
        "hyperparameter_grids": r0c["hyperparameter_grids"],

        "uncertainty": {
            "disposition": "WITHDRAWN",
            "reason": "the R0C joint calibration gate failed literally: the "
                      "state-space posterior sits at 0.497 against a frozen "
                      "lower bound of 0.5 and Wiener within the band. The rule "
                      "was one scalar per estimator family and the branch was "
                      "frozen in advance",
            "forbidden": ["credible intervals", "posterior movies",
                          "coverage statements",
                          "adjusting the band to rescue the result",
                          "fitting another scale after seeing validation",
                          "rescuing Wiener alone"],
            "retained_as": "point estimators",
        },

        "endpoint_surface": r0c["endpoint"]["surface"],
        "retired_endpoint": r0c["endpoint"]["retired"],
        "retired_gates": {
            **r0c.get("retired_gates", {}),
            "dropped_from_the_active_list_here": dropped,
        },
        "gates": gates,

        "metrics": r0c["metrics"],
        "physical_model": r0c["physical_model"],
        "observation": r0c["observation"],
        "source_class": r0c["source_class"],
        "source_families": r0c["source_families"],
        "source_regimes": r0c["source_regimes"],
        "in_span_construction": r0c["in_span_construction"],
        "subspaces": r0c["subspaces"],
        "artifact_policy": r0c["artifact_policy"],

        "dispositions": {
            "R1_PASS_WITH_SCOPE_RESTRICTION":
                "the exact-in-class aggregate primary passes, TSVD and ridge "
                "agree, at least three of four prior-fit families pass, "
                "common-subspace and old-band level errors improve, and every "
                "integrity control passes. Expected to be the strongest "
                "defensible outcome: one geometry, one source class, no "
                "detailed structure at the reference SNR, off-grid recovery "
                "failing, and uncertainty withdrawn",
            "R1_PASS":
                "reserved for a result that also supports the broader "
                "registered secondary claims",
            "R1_NEGATIVE_RESULT":
                "the sealed exact-in-class main bank fails the primary "
                "criterion",
            "R1_IMPLEMENTATION_OR_LEAKAGE_DEFECT":
                "commitment hashes, clean-tree attestation, source "
                "membership, paired noise, null controls or split isolation "
                "fail. No scientific interpretation is drawn",
        },
        "stop_after": "R1 main only. No R2 to R5, no E3D rerun, no ML, no "
                      "geometry mismatch, no order leakage, no VLBI",
    }

    fz["provenance"]["r1_config_sha256"] = hashlib.sha256(
        canonical(fz)).hexdigest()
    OUT.write_text(json.dumps(fz, indent=2, default=float) + "\n")

    att = attest([OUT, R0C, COMMITMENT, NULL_OUT])
    print(f"wrote {OUT.relative_to(ROOT)}")
    print(f"  r1_config_sha256   {fz['provenance']['r1_config_sha256']}")
    print(f"  primary            IN_CLASS_ID, SNR 100, eps 0.25, q 0.95, "
          f"TSVD vs ridge, delta >= 8 M")
    print(f"  noise draws        {N_NOISE_DRAWS} paired + 1 noiseless control")
    print(f"  bootstrap          {BOOTSTRAP_RESAMPLES} truth clusters, "
          f"seed {BOOTSTRAP_SEED}")
    print(f"  uncertainty        {fz['uncertainty']['disposition']}")
    print(f"  retired gates      dropped from the active list: {dropped}")
    print(f"  active gates       {len(gates)}")
    print(f"  tree clean         {att.get('clean')} "
          f"(tracked {att.get('n_tracked_changes')}, "
          f"untracked {att.get('n_untracked')})")
    print(f"total {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
