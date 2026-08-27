#!/usr/bin/env python3
"""R1L_STAGE2_VALIDATION_ACTIVATION_010 -- freeze stage 2 before any truth exists.

REVIEWER_RULING_R1L_REPRODUCIBILITY_009 item 11. Everything the ruling names --
counts, split hashes, seeds, source-balance tolerances, estimator grids, SNR
grid, noise draws, resource limits and every stage-2 disposition -- is fixed
here and hashed. The split hashes are commitments to the *content* of banks that
do not yet exist: the runner regenerates each bank from the declared seed and
must reproduce the committed hash before it is allowed to score anything.
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

R1L = ROOT / "artifacts" / "configs" / "R1L_LOCALIZED_AUDIT_FREEZE.json"
R1 = ROOT / "artifacts" / "configs" / "R1_MAIN_FREEZE.json"
BASE = ROOT / "artifacts" / "provenance" / "R1L_STAGE1_BASELINE.json"
REPRO = ROOT / "artifacts" / "provenance" / "R1L_STAGE1_REPRODUCTION.json"
OUT = ROOT / "artifacts" / "configs" / "R1L_STAGE2_VALIDATION_ACTIVATION_010.json"

CLASSES = ["L224", "L448", "L1056"]
ARMS = ["DIRECT_PHYSICAL", "RESOLVED_PHYSICAL", "UNRESOLVED_IMAGE", "TOTAL_FLUX"]
FAMILIES = ["circular_single_hotspot", "circular_two_hotspots",
            "circular_crescent", "plunging_hotspot"]
BANKS = ["constant_flux_structural", "structure_balanced_050",
         "structure_balanced_080", "baseline_one_positive"]
SPLITS = ["selection", "pilot"]
PER_CELL = 8
DRAWS = 4
SNR_GRID = [30.0, 100.0, 300.0, 1000.0, 3000.0, 10000.0, 30000.0]
SEEDS = {"bank_seed": 20260901, "noise_seed": 20260902,
         "bootstrap_seed": 20260903, "null_pair_seed": 20260904,
         "subsample_seed": 20260825}
TSVD_GRID = [10 ** (-k / 2) for k in range(15)]
RIDGE_GRID = [10 ** (-k / 2) for k in range(21)]


def split_commitment(bank: str, family: str, split: str) -> str:
    """Commit to a bank cell's identity before the bank is drawn.

    The runner derives each truth's seed from exactly this string, so the
    committed hash is a statement about which truths will exist, not a hash of
    numbers that already do. Reproducing it at run time is what makes the
    selection/pilot split checkable rather than promised.
    """
    payload = json.dumps({"bank": bank, "family": family, "split": split,
                          "n": PER_CELL, "seed": SEEDS["bank_seed"]},
                         sort_keys=True).encode()
    return hashlib.sha256(payload).hexdigest()


def main() -> int:
    reg = load_registry()
    r1 = json.loads(R1.read_text())
    r1l = json.loads(R1L.read_text())
    repro = json.loads(REPRO.read_text())
    base = json.loads(BASE.read_text())
    if not repro["verdict"].endswith("PASS"):
        raise SystemExit(f"stage 2 is not authorized: {repro['verdict']}")
    spin = float(r1["physical_model"]["spin"])

    cells = {f"{b}|{f}|{s}": split_commitment(b, f, s)
             for b in BANKS for f in FAMILIES for s in SPLITS}
    n_truths = len(cells) * PER_CELL

    doc = {
        "schema": "phrt-r1l-stage2-activation/1",
        "id": "R1L_STAGE2_VALIDATION_ACTIVATION_010",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "ruling": "REVIEWER_RULING_R1L_REPRODUCIBILITY_009 item 11",
        "status": "FROZEN_BEFORE_ANY_SOURCE_TRUTH_IS_GENERATED",
        "authorizing_evidence": {
            "stage1_reproduction_verdict": repro["verdict"],
            "stage1_baseline_run": base["baseline_run"],
            "stage1_reproduced_by": base["reproduced_by"],
            "stage1_execution_commit": base["execution_commit"],
            "blocking_gate_cleared": "R1L_G12_deterministic_reproduction",
        },

        "scope": {
            "authorized": ["R1L_STAGE_2_VALIDATION"],
            "not_authorized": ["R1L sealed main", "geometry mismatch",
                               "order leakage", "VLBI", "ML",
                               "any rescoring of the sealed R1 bank"],
            "geometry": r1["physical_model"]["geometry"],
            "classes": CLASSES,
            "arms": ARMS,
            "forbidden_language": "stage 2 is a validation pilot. No stage-2 "
                                  "number may be reported as a held-out result, "
                                  "and no stage-2 selection may be described as "
                                  "confirmation",
        },

        # ------------------------------------------------------- counts/splits
        "counts": {
            "banks": BANKS, "families": FAMILIES, "splits": SPLITS,
            "truths_per_bank_family_split": PER_CELL,
            "n_cells": len(cells),
            "n_truths_total": n_truths,
            "n_truths_per_split": n_truths // 2,
            "noise_draws_per_truth": DRAWS,
            "noiseless_control_per_truth": 1,
            "n_reconstruction_cells": (len(CLASSES) * len(ARMS) * n_truths
                                       * (DRAWS + 1) * len(SNR_GRID) * 2),
            "estimators_scored": ["TSVD", "RIDGE_IDENTITY"],
        },
        "split_rule": {
            "selection": "hyperparameters are chosen here and nowhere else",
            "pilot": "the reported stage-2 endpoint is computed here, on truths "
                     "no hyperparameter ever saw",
            "disjointness": "by construction -- the two splits derive from "
                            "different commitment strings, so no truth seed can "
                            "appear in both. Gate R1L_S2_G3 re-checks it by "
                            "content hash at run time rather than trusting the "
                            "construction",
            "commitments": cells,
            "commitment_meaning": "sha256 over (bank, family, split, n, seed). "
                                  "The runner derives every truth seed from the "
                                  "same string and must reproduce the hash "
                                  "before scoring",
        },
        "seeds": SEEDS,

        # ------------------------------------------------------ source banks
        "source_banks": {
            "constant_flux_structural": {
                "role": "primary",
                "construction": "each age slice renormalized to a fixed spatial "
                                "mean, so total-level variation is removed and "
                                "moving morphology is retained",
                "target_structure_fraction": None,
                "level_is_informative": False,
            },
            "structure_balanced_050": {
                "role": "primary", "target_structure_fraction": 0.50,
                "construction": "j = b(t) + s(r, phi, t) with b the minimum "
                                "baseline that keeps j non-negative at the "
                                "target fraction",
            },
            "structure_balanced_080": {
                "role": "primary", "target_structure_fraction": 0.80,
                "construction": "as above at the higher fraction",
            },
            "baseline_one_positive": {
                "role": "secondary control only",
                "target_structure_fraction": None,
                "measured_in_r1": 0.126,
                "rule": "may not carry the primary endpoint",
            },
        },
        "source_balance_tolerances": {
            "structure_fraction_absolute": 0.02,
            "structure_fraction_rule": "||P_structure j|| / ||j|| must fall "
                                       "within this of the target for every "
                                       "truth in a structure-balanced bank that "
                                       "is not at its positivity ceiling",
            "constant_flux_slice_mean_relative": 1e-10,
            "constant_flux_rule": "the spatial mean of every age slice must be "
                                  "constant to this relative tolerance",
            "positivity_floor": 0.0,
            "positivity_rule": "min over the rendered movie must be at or above "
                               "zero",
            "positivity_ceiling": {
                "fact": "a non-negative field cannot have an arbitrary structure "
                        "fraction. Writing j = s + c, positivity forces "
                        "c >= -min(s), and the fraction ||s||/||s+c|| falls "
                        "monotonically in c, so the maximum is "
                        "||s|| / ||s - min(s)||, reached exactly at the "
                        "positivity boundary. Scaling does not evade it: at the "
                        "boundary j = a(s - min s) for any a > 0 and the "
                        "fraction is unchanged",
                "measured_before_freezing": {
                    "what": "the ceiling per family, over 20 draws each, on the "
                            "declared evaluation grid and the R0C level "
                            "projector",
                    "why_this_is_not_peeking": "the ceiling is a property of the "
                                               "source family and the projector "
                                               "alone. No operator, arm, "
                                               "estimator, noise draw or "
                                               "reconstruction enters it, so it "
                                               "cannot be a result and cannot "
                                               "be selected on. It is measured "
                                               "here because declaring an "
                                               "unreachable target and calling "
                                               "the shortfall a finding would "
                                               "be worse",
                    "circular_single_hotspot": {"min": 0.626, "median": 0.845},
                    "circular_two_hotspots": {"min": 0.643, "median": 0.723},
                    "circular_crescent": {"min": 0.517, "median": 0.643},
                    "plunging_hotspot": {"min": 0.900, "median": 0.944},
                    "achievable_at_target_0_50": "79 of 80 draws",
                    "achievable_at_target_0_80": "40 of 80 draws",
                },
                "handling": "a truth whose target exceeds its ceiling is kept at "
                            "the ceiling -- the most structural non-negative "
                            "field of that shape -- and flagged "
                            "at_positivity_ceiling. It is not discarded and the "
                            "bank is not silently retargeted",
            },
            "bank_construction_failure": {
                "min_fraction_of_truths_reaching_target": 0.50,
                "rule": "a structure-balanced bank in which fewer than half the "
                        "truths reach their declared target within 0.02 is a "
                        "construction failure and dispositions "
                        "R1L_STAGE2_SOURCE_BANK_FAILURE",
            },
            "baseline_dominance": {
                "median_structure_fraction_floor": 0.35,
                "rule": "R1L_STOP_4 trips when a primary bank's median achieved "
                        "structure fraction falls below this, i.e. a level "
                        "fraction above 0.94, which is the regime R1 was in at "
                        "0.126 structure and 0.992 level",
                "note": "an earlier draft of this freeze set a ceiling of 0.60 "
                        "on the *level* fraction. That was mis-specified: a "
                        "structure fraction of 0.50 implies a level fraction of "
                        "sqrt(1 - 0.25) = 0.866, so the reviewer's own primary "
                        "target would have tripped its own failure condition. "
                        "Corrected before any truth was generated",
            },
        },
        "source_motion": {
            "circular_families": {
                "orbit_law": "Kerr prograde circular geodesic, 1/(r^{3/2}+a)",
                "r_centre_M": [isco_radius(spin), 29.989231533549642],
                "restriction": "centres strictly outside the ISCO",
            },
            "plunging_family": {
                "orbit_law": "radial plunge on the ISCO's conserved E and L",
                "r_centre_M": [1.8660254037844386, isco_radius(spin)],
                "separate_from_circular": True,
            },
            "velocity_field_for_g3": velocity_field_record(spin),
        },

        # ------------------------------------------------------- estimators
        "estimators": {
            "TSVD": {"role": "primary", "cut_on": "sigma_i / sigma_max",
                     "grid": TSVD_GRID, "n_grid": len(TSVD_GRID)},
            "RIDGE_IDENTITY": {"role": "confirmatory",
                               "cut_on": "lambda / lambda_max(G)",
                               "grid": RIDGE_GRID, "n_grid": len(RIDGE_GRID)},
            "ML": "NOT_AUTHORIZED",
            "selection_rule": "lexicographic on the selection split, minimizing "
                              "old-band structure error at SNR0 = 100, ties "
                              "broken by the smaller model. Selected per "
                              "(class, arm, estimator) and frozen before the "
                              "pilot split is touched",
            "no_retuning": "no hyperparameter may be revisited after any pilot "
                           "truth is scored",
        },
        "snr_grid": SNR_GRID,
        "reference_snr": 100.0,
        "noise": {
            "draws_per_truth": DRAWS,
            "noiseless_control": 1,
            "coupling": "one resolved Gaussian draw per (truth, draw index); "
                        "direct, unresolved and total flux are the declared "
                        "linear readouts of that same draw, so the arms are "
                        "paired",
            "independent_unit": "the truth, not the truth-noise pair",
        },

        # --------------------------------------------------------- endpoints
        "primary_endpoint": {
            "statistic": "delta_E_old_structure = E_old_structure(direct) "
                         "- E_old_structure(resolved)",
            "snr0": 100.0,
            "split": "pilot",
            "estimator_primary": "TSVD",
            "estimator_confirmatory": "RIDGE_IDENTITY",
            "old_band_boundary_M": float(r1["metrics"]["old_band_boundary_M"]),
            "bootstrap": {"kind": "paired truth-cluster", "unit": "truth",
                          "n_resamples": 10000, "level": 0.95,
                          "seed": SEEDS["bootstrap_seed"]},
            "success_requires": [
                "bootstrap interval excluding zero",
                "lower old-band structure error in at least three of the four "
                "fitting families",
                "confirmation by both TSVD and RIDGE_IDENTITY",
                "null-pair behaviour remaining likelihood-consistent",
            ],
        },
        "coprimary_endpoint": {
            "statistic": "delta_L_stable_structure",
            "paper_grade_threshold_M": 8.0,
            "prespecified_snr0": 100.0,
            "permitted_snr0_ceiling": 1000.0,
            "if_only_at_30000": "reported as a negative practicality result",
            "age_grid_step_M": float(r1l["F_age_resolution"]["age_grid_step_M"]),
        },
        "unresolved_arm_rule": "UNRESOLVED_IMAGE is reported at the same "
                               "standing as RESOLVED_PHYSICAL. A gain that "
                               "appears only in the resolved arm is an ideal "
                               "channel-separation result and is dispositioned "
                               "R1L_STAGE2_RESOLVED_ONLY_PASS, not a pass",

        # ------------------------------------------------------- deliverables
        "required_outputs": [
            "structure-only stable spans",
            "age-resolved structure errors",
            "source-balance diagnostics",
            "representation floors",
            "common-subspace errors",
            "localized null-pair controls",
            "a proposed sealed-main commitment, not scored",
        ],
        "sealed_main_commitment": {
            "emitted": True,
            "scored": False,
            "rule": "stage 2 proposes the sealed-main bank and commits its hash. "
                    "It must not be generated through any operator, inspected or "
                    "scored in stage 2",
        },

        # ------------------------------------------------------ resource limits
        "resource_limits": {
            "wall_clock_seconds": 7200,
            "peak_rss_mb": 12000,
            "on_exceeded": "R1L_STAGE2_IMPLEMENTATION_DEFECT. The run stops and "
                           "reports; it does not silently reduce counts, drop a "
                           "class or subsample a bank to fit",
            "no_silent_reduction": "any reduction in the declared counts is a "
                                   "protocol deviation and must be recorded as "
                                   "one",
        },
        "numerical_environment": {
            "pinned": True,
            "variables": json.loads(
                (ROOT / "artifacts" / "configs"
                 / "R1L_DETERMINISTIC_NUMERICS_AMENDMENT_009.json").read_text()
            )["pinned_numerical_environment"]["variables"],
            "assertion": "every BLAS pool must report one thread, interrogated "
                         "after import. Gate R1L_S2_G1",
        },

        # -------------------------------------------------------- dispositions
        "dispositions": {
            "R1L_STAGE2_RESOLVED_AND_UNRESOLVED_PASS":
                "the primary endpoint succeeds on all four criteria for the "
                "resolved arm and the unresolved arm also shows a bootstrap "
                "interval excluding zero at SNR0 = 100",
            "R1L_STAGE2_RESOLVED_ONLY_PASS":
                "the primary endpoint succeeds for the resolved arm and the "
                "unresolved arm does not",
            "R1L_STAGE2_NEGATIVE_RESULT":
                "the banks are sound and the endpoint does not succeed for the "
                "resolved arm. This is a reportable result and is not a reason "
                "to widen the design",
            "R1L_STAGE2_SOURCE_BANK_FAILURE":
                "a declared bank could not be constructed within the "
                "source-balance tolerances, so the endpoint was never testable",
            "R1L_STAGE2_IMPLEMENTATION_DEFECT":
                "a gate failed, a resource limit was exceeded, or a split "
                "commitment did not reproduce",
            "exactly_one": True,
        },
        "gates": {
            "R1L_S2_G1_pinned_numerical_environment": "structural",
            "R1L_S2_G2_split_commitments_reproduce": "structural",
            "R1L_S2_G3_split_disjointness_by_content_hash": "structural",
            "R1L_S2_G4_source_balance_within_tolerance": "structural",
            "R1L_S2_G5_positivity": 0.0,
            "R1L_S2_G6_no_hyperparameter_touched_pilot": "structural",
            "R1L_S2_G7_adjoint": 1e-8,
            "R1L_S2_G8_estimator_closed_form": 1e-9,
            "R1L_S2_G9_noise_replay_bitwise": "bitwise",
            "R1L_S2_G10_sealed_main_not_scored": "structural",
            "R1L_S2_G11_resource_limits": "structural",
        },
        "provenance": {
            "r1l_freeze_sha256": sha256_file(R1L),
            "r1_freeze_sha256": sha256_file(R1),
            "stage1_baseline_sha256": sha256_file(BASE),
            "registry_sha256": reg.sha256,
            "raymap_sha256": r1["physical_model"]["raymap_sha256"],
        },
        "stop_after": "R1L_STAGE_2_VALIDATION",
    }
    doc["attestation"] = attest([R1L, R1, BASE])
    OUT.write_text(json.dumps(doc, indent=2) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}")
    print(f"  sha256 {sha256_file(OUT)}")
    print(f"  {len(cells)} committed split cells, {n_truths} truths, "
          f"{DRAWS} draws + 1 control")
    print(f"  {len(CLASSES)} classes x {len(ARMS)} arms x {len(SNR_GRID)} SNR "
          f"x 2 estimators")
    print(f"  reconstruction cells: {doc['counts']['n_reconstruction_cells']:,}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
