#!/usr/bin/env python3
"""HMT2_STAGE0_SOURCE_OBJECT_AND_RESOLUTION_AUDIT_V0.

Item 7 of REVIEWER_RULING_HMT1_SOURCE_RESOLUTION_018. Registered and committed
before any random source bank is drawn.

Stage 0 asks one question HMT-1 never asked: given these source families and
these grids, what is actually there to be measured. It imports no ray map and
builds no observation operator, so nothing here can be an inverse-problem
result.
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

import numpy as np  # noqa: E402

from phrt.attestation import attest  # noqa: E402
from phrt.config import sha256_file  # noqa: E402
from phrt.metrics.features import BIRTH_FRACTION  # noqa: E402

VFZ = ROOT / "artifacts" / "configs" / "HMT1_VALIDATION_FREEZE_V0.json"
CLO = ROOT / "artifacts" / "configs" / "HMT1_CLOSURE_RECORD_018.json"
R1 = ROOT / "artifacts" / "configs" / "R1_MAIN_FREEZE.json"
OUT = ROOT / "artifacts" / "configs" / "HMT2_STAGE0_SOURCE_OBJECT_AND_RESOLUTION_AUDIT_V0.json"

SEED = 20260931
PER_FAMILY = 24
GRIDS = ((16, 32, 40), (32, 64, 80), (64, 128, 160))

# What a peak-finder should see in the windowed field, per family, declared
# before any bank is drawn. This is a property of the generative form, not a
# measurement: an m = 2 pattern has two lobes whatever the grid does with them.
EXPECTED_MULTIPLICITY = {
    "circular_hotspot_trajectory": 1,
    "two_hotspot_trajectories": 2,
    "m1_rotating_crescent": 1,
    "m2_structural_mode": 2,
    "flare_birth_motion_decay": 1,
    "plunging_feature": 1,
    "three_hotspot_cluster": 3,
    "counter_rotating_pair": 2,
    "radially_drifting_arc": 1,
}


def commitment(family, n, seed):
    return hashlib.sha256(json.dumps(
        {"family": family, "split": "hmt2_stage0_source_audit", "n": n,
         "seed": seed, "model": "contrast"}, sort_keys=True).encode()).hexdigest()


def main() -> int:
    vfz = json.loads(VFZ.read_text())
    r1 = json.loads(R1.read_text())
    fams = list(vfz["feature_families"]["declared"])
    off = list(vfz["feature_families"]["off_manifold_controls"]["families"])

    doc = {
        "schema": "phrt-hmt2-stage0-freeze/1",
        "id": "HMT2_STAGE0_SOURCE_OBJECT_AND_RESOLUTION_AUDIT_V0",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "ruling": "REVIEWER_RULING_HMT1_SOURCE_RESOLUTION_018",
        "status": "FROZEN_BEFORE_ANY_SOURCE_BANK_IS_DRAWN",
        "branch": "research/hmt2_resolution_aware_feature_measure_v0",
        "predecessor": "HMT1_CLOSURE_RECORD_018",
        "predecessor_sha256": sha256_file(CLO),

        "question": "given these source families and these grids, what is "
                    "there to be measured. HMT-1 specified a source model and "
                    "an evaluation grid independently and never checked the "
                    "contract between them; the sealed main failed on exactly "
                    "that. Stage 0 establishes the contract before any "
                    "estimator is asked to honour it",

        "prohibitions": {
            "ray_map": "not imported. Item 8",
            "observation_operator": "not constructed. Item 8",
            "consequence": "no quantity produced here is an inverse-problem "
                           "result, and none can be read as one",
            "separation_cut": "not imposed. Item 9. The original six family "
                              "parameter ranges are preserved exactly as HMT-1 "
                              "declared them, because the audit's job is to "
                              "measure what those ranges contain, not to "
                              "repair them in advance",
        },

        "source_families": {
            "declared": fams,
            "off_manifold": off,
            "ranges": "inherited verbatim from HMT_1_HISTORICAL_FEATURE_AND_"
                      "CONTRAST_TOMOGRAPHY_V0",
            "expected_windowed_multiplicity": EXPECTED_MULTIPLICITY,
            "multiplicity_note": "declared from the generative form before any "
                                 "bank is drawn. It is what distinguishes a "
                                 "BLENDED state from a SINGLE_RESOLVED one: "
                                 "the field shows one peak either way, and "
                                 "only the source model knows whether "
                                 "something was lost",
        },

        "bank": {
            "truths_per_family": PER_FAMILY,
            "n_families": len(fams),
            "n_truths": PER_FAMILY * len(fams),
            "off_manifold_per_family": 8,
            "bank_seed": SEED,
            "commitments": {f: commitment(f, PER_FAMILY, SEED)
                            for f in fams + off},
            "size_note": "the bank size is declared for cost and is not a "
                         "grid reduction. Item 10 forbids reducing the final "
                         "grid because a source is expensive; it does not fix "
                         "how many sources are audited",
        },

        "grids": {
            "nested": [{"n_radial": a, "n_azimuthal": b, "n_temporal": c,
                        "level": i} for i, (a, b, c) in enumerate(GRIDS)],
            "nesting": "each level doubles every axis, so every coarse node is "
                       "a fine node and the levels are directly comparable",
            "construction_grid": "the finest level. The source object is built "
                                 "once, at the highest resolution, so that only "
                                 "the analysis resolution varies across levels. "
                                 "Building at each level would confound the "
                                 "grid's effect on the object with its effect "
                                 "on the measurement",
            "analysis_grids": "all three levels",
            "cell_metric": "the level-0 grid, (16, 32, 40), so that distances "
                           "reported at different levels are in the same units "
                           "-- the units HMT-1's one-cell tolerance was written "
                           "in",
            "streaming": "levels are processed one truth at a time and never "
                         "held together. Item 10",
        },

        "source_classes": {
            "L448_contrast": {
                "radial": 4, "azimuthal": 7, "temporal": 16,
                "dimension_before_m0_removal": 448,
                "dimension_after": 384,
                "role": "the class HMT-1 used",
            },
            "L896_radial_enriched": {
                "radial": 8, "azimuthal": 7, "temporal": 16,
                "dimension_before_m0_removal": 896,
                "dimension_after": 768,
                "role": "nested radial enrichment. Item 11. The radial "
                        "direction is doubled and nothing else changes, "
                        "because the HMT-1 failure was radial: two spots 0.34 "
                        "log-radial cells apart with sub-cell widths",
                "nested_in_radius": "the 4-function radial space is contained "
                                    "in the 8-function one, so the enrichment "
                                    "adds resolution and removes nothing",
            },
            "projection": "separable least squares, mode by mode. The basis "
                          "and the grid are both tensor products, so the "
                          "projection factorises and the finest grid never "
                          "needs a dense design matrix",
        },

        "classification": {
            "states": ["SINGLE_RESOLVED", "MULTI_RESOLVED", "BLENDED", "DEAD",
                       "AMBIGUOUS"],
            "rule": "topographic prominence. Every local maximum of the "
                    "windowed field is assigned the height it stands above the "
                    "highest saddle connecting it to any higher maximum. A "
                    "maximum counts as a resolved feature when its prominence "
                    "reaches the frozen fraction of the age's global maximum",
            "prominence_fraction": BIRTH_FRACTION,
            "dead_fraction": BIRTH_FRACTION,
            "constants_note": "both reuse the birth fraction already declared "
                              "in the campaign's event-time definition. No new "
                              "tuned constant is introduced by this audit",
            "definitions": {
                "DEAD": "the age's global maximum is below the dead fraction "
                        "of the truth's maximum over all ages",
                "SINGLE_RESOLVED": "exactly one prominent peak, and the family "
                                   "expects one",
                "MULTI_RESOLVED": "two or more prominent peaks",
                "BLENDED": "exactly one prominent peak where the family "
                           "expects more. Something is present that the grid "
                           "does not separate",
                "AMBIGUOUS": "the label disagrees between the two finest "
                             "levels",
            },
            "stability_requirement": "item 12. AMBIGUOUS is defined as "
                                     "instability between the final two "
                                     "refinement levels rather than by a "
                                     "tolerance band, so the requirement is "
                                     "the definition rather than a check "
                                     "bolted onto it",
        },

        "feature_measure": {
            "kind": "set-valued. Item 13",
            "element": ["r", "phi", "amplitude", "prominence"],
            "distance": "Euclidean in level-0 grid cells, radial measured in "
                        "log r cells and azimuthal in wrapped phi cells",
            "assignment": "optimal injective assignment minimising total "
                          "distance, computed exactly over all matchings",
            "unbalanced_penalty": "an unmatched feature costs the largest "
                                  "distance the level-0 grid admits, "
                                  "sqrt((n_radial - 1)^2 + (n_azimuthal / 2)^2) "
                                  "cells. Derived from the grid rather than "
                                  "chosen, so creating or destroying a feature "
                                  "costs exactly as much as the worst possible "
                                  "mismatch",
            "forbidden": "a single global argmax for a multi-feature family. "
                         "That is what HMT-1 did, and it is why its validation "
                         "scope is now DOMINANT_OR_BLENDED_FEATURE_DESCRIPTOR",
        },

        "reporting": {
            "BLENDED": ["centroid_r", "centroid_phi", "total_contrast",
                        "second_moment_rr", "second_moment_pp",
                        "second_moment_rp", "a_m1", "a_m2",
                        "multiplicity_label"],
            "BLENDED_note": "item 14. No two trajectories are forced through a "
                            "one-peak field. What a blended state supports is "
                            "a centroid, a size and a mode content, and those "
                            "are what it reports",
            "MULTI_RESOLVED": ["peak_r", "peak_phi", "peak_amplitude",
                               "cardinality", "track_id"],
            "MULTI_RESOLVED_note": "item 15. Tracks are associated across ages "
                                   "by the same assignment metric",
        },

        "quantities": {
            "per_family_and_class": [
                "fraction_single_resolved", "fraction_multi_resolved",
                "fraction_blended", "fraction_dead", "fraction_ambiguous",
                "grid_convergence_error_cells",
                "projection_induced_merger_rate",
                "minimum_representable_width",
                "feature_measure_representation_floor",
            ],
            "grid_convergence_error_cells": "assignment error between the "
                                            "feature sets measured at the two "
                                            "finest levels",
            "projection_induced_merger_rate": "fraction of MULTI_RESOLVED "
                                              "(truth, age) states that stop "
                                              "being MULTI_RESOLVED once the "
                                              "field is projected onto the "
                                              "class",
            "minimum_representable_width": "the input Gaussian width at which "
                                           "the projected width reaches twice "
                                           "the input width. A class property, "
                                           "measured by projecting blobs of "
                                           "decreasing width, not by drawing "
                                           "sources",
            "feature_measure_representation_floor": "assignment error between "
                                                    "the analytic field's "
                                                    "feature set and its own "
                                                    "best in-class "
                                                    "approximation. The floor "
                                                    "any estimator faces before "
                                                    "noise",
        },

        "canary": {
            "id": "HMT1_SOURCE_RESOLUTION_FAILURE_CANARY",
            "source": "HMT-1 bank seed 20260921, two_hotspot_trajectories "
                      "index 5",
            "role": "named regression only. Item 17",
            "excluded_from": "every aggregate success statistic and every "
                             "per-family fraction",
            "construction_note": "its parameters are a property of the seed "
                                 "and not of the construction grid, so "
                                 "building it at the finest level reproduces "
                                 "the same two spots 0.34 log-radial cells "
                                 "apart",
        },

        "after": "STOP. Item 18",
        "not_authorized": ["HMT-2 validation", "a new sealed bank",
                           "order leakage", "geometry mismatch", "VLBI",
                           "machine learning"],
        "numerical_environment": vfz["numerical_environment"],
        "inherited": {
            "validation_freeze_sha256": sha256_file(VFZ),
            "r1_freeze_sha256": sha256_file(R1),
            "age_grid_step_M": float(vfz["primary_endpoints"]
                                     ["stable_feature_interval"]["age_grid_step_M"]),
            "probe_half_width_M": float(vfz["primary_endpoints"]
                                        ["stable_feature_interval"]["probe_half_width_M"]),
            "age_grid_max_M": float(r1["metrics"]["age_grid_max_M"]),
            "spin": float(vfz["geometry"]["a_star"]),
            "inclination_deg": float(vfz["geometry"]["inclination_deg"]),
        },
        "attestation": attest([VFZ, CLO, R1]),
    }
    OUT.write_text(json.dumps(doc, indent=2, default=str) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}\n  sha256 {sha256_file(OUT)}")
    print(f"  {PER_FAMILY} x {len(fams)} = {PER_FAMILY * len(fams)} truths, "
          f"{len(GRIDS)} grids, 2 source classes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
