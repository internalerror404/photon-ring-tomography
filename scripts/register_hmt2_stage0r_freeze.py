#!/usr/bin/env python3
"""HMT2_STAGE0R_SOURCE_ONLY_CORRECTION_V0.

Items 4 to 11 of REVIEWER_RULING_HMT2_STAGE0_019. A correction of the stage 0
accounting and language over the same sources. No redraw, no new bank, no
operator.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from phrt.numerics import pin

pin()

from phrt.attestation import attest  # noqa: E402
from phrt.config import sha256_file  # noqa: E402

S0 = ROOT / "artifacts" / "configs" / "HMT2_STAGE0_SOURCE_OBJECT_AND_RESOLUTION_AUDIT_V0.json"
OUT = ROOT / "artifacts" / "configs" / "HMT2_STAGE0R_SOURCE_ONLY_CORRECTION_V0.json"


def main() -> int:
    s0 = json.loads(S0.read_text())
    doc = {
        "schema": "phrt-hmt2-stage0r-freeze/1",
        "id": "HMT2_STAGE0R_SOURCE_ONLY_CORRECTION_V0",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "ruling": "REVIEWER_RULING_HMT2_STAGE0_019",
        "status": "FROZEN_BEFORE_CORRECTION_RUN",
        "branch": "research/hmt2_resolution_aware_feature_measure_v0",
        "corrects": s0["id"],
        "corrects_sha256": sha256_file(S0),
        "accepted_execution_commit": "2e478b49394fc6a199ad702911d0852a4a002d19",

        "unchanged_from_stage_0": {
            "sources": s0["bank"]["n_truths"] + 24 + 1,
            "bank_seed": s0["bank"]["bank_seed"],
            "commitments": s0["bank"]["commitments"],
            "family_ranges": "the original six, verbatim, with no separation cut",
            "prominence_fraction": s0["classification"]["prominence_fraction"],
            "dead_fraction": s0["classification"]["dead_fraction"],
            "levels": [[g["n_radial"], g["n_azimuthal"], g["n_temporal"]]
                       for g in s0["grids"]["nested"]],
            "classes": ["L448_contrast", "L896_radial_enriched"],
            "rule": "item 5. No redraw and no new source bank. Stage 0R is the "
                    "same computation over the same objects with the "
                    "accounting corrected and the output widened",
        },

        "prohibitions": {
            "ray_map": "not imported",
            "observation_operator": "not constructed",
            "guard": "item 10. The source-only guard is called before any work "
                     "and again after all computation, and the booleans "
                     "recorded in the run document are derived from the final "
                     "inspection rather than written as literals. The first "
                     "run wrote them as literals, which records an intention "
                     "rather than an observation",
        },

        "withheld_pending_this_correction": {
            "quantity": "two-hotspot projection merger rates",
            "values": [0.356, 0.262],
            "reason": "item 3. Those rates counted every state the finest grid "
                      "labelled MULTI_RESOLVED, including states the two "
                      "finest grids disagreed about. A merger rate over states "
                      "whose multiplicity is itself unresolved measures the "
                      "classifier as much as the projection",
            "status": "not canonical until recomputed over reconciled stable "
                      "states",
        },

        "per_age_projection_table": {
            "name": "hmt2_stage0r_per_age",
            "columns": ["family", "index", "age_M", "class",
                        "label_fine", "label_coarser", "label_reconciled",
                        "label_projected", "cardinality_pre",
                        "cardinality_post", "matched_position_cost_cells",
                        "unbalanced_cost_cells", "unbalanced_cost_normalized",
                        "canary", "off_manifold"],
            "rule": "item 7. One row per age per class, so every rate below is "
                    "recomputable from the table rather than trusted",
            "normalization": "unbalanced cost divided by the cost of a single "
                             "wholly unmatched feature, which is the largest "
                             "distance the level-0 grid admits. A normalized "
                             "cost of 1.0 therefore means one feature gained "
                             "or lost",
        },

        "merger_rate_strata": {
            "STABLE_MULTI_RESOLVED": {
                "definition": "the two finest levels agree on "
                              "MULTI_RESOLVED",
                "carries_claim": True,
            },
            "AMBIGUOUS_FINE_MULTI": {
                "definition": "the finest level says MULTI_RESOLVED and the "
                              "next coarser disagrees",
                "carries_claim": False,
                "role": "reported so the size of the disagreement is visible "
                        "rather than absorbed",
            },
            "ALL_FINEST_MULTI": {
                "definition": "every state the finest level calls "
                              "MULTI_RESOLVED, which is the union of the two "
                              "above and what stage 0 reported",
                "carries_claim": False,
                "role": "reported for continuity with the withheld numbers",
            },
            "rule": "item 8. Only STABLE_MULTI_RESOLVED may carry the "
                    "scientific merger-rate claim",
        },

        "language_corrections": {
            "positional_convergence": "the convergence figure is a matched "
                                      "position cost. It excludes unmatched "
                                      "features by construction, so it is "
                                      "positional convergence and not complete "
                                      "grid convergence",
            "cardinality": "reported as differing by at most one feature, "
                           "which is what was measured, rather than as "
                           "agreement",
            "grids": "factor-two refinement grids, not node-nested grids. "
                     "Only the azimuthal axis nests: phi at 32 points is a "
                     "subset of phi at 64. The radial axis is 16 then 32 "
                     "points spanning a fixed log range, and the temporal axis "
                     "40 then 80 over a fixed interval, and in both cases the "
                     "coarse nodes are not fine nodes. Stage 0's freeze "
                     "asserted that every coarse node is a fine node, and that "
                     "is false for two of the three axes",
            "representation_floor": "an unbalanced total cost, not an ordinary "
                                    "displacement. Its large values are "
                                    "dominated by the penalty for a feature "
                                    "gained or lost, not by a distance",
        },

        "preserved_findings": [
            "HMT2_STAGE0_CANARY_BLENDED_61_OF_61",
            "HMT2_STAGE0_TWO_HOTSPOT_MIXED_RESOLUTION_REGIME",
            "HMT2_STAGE0_L448_REPRESENTATION_LIMIT",
            "HMT2_STAGE0_L896_RADIAL_ENRICHMENT_BENEFIT",
        ],
        "gates": {
            "HMT2R_G1_pinned_numerical_environment": "structural",
            "HMT2R_G2_source_only_before": 0,
            "HMT2R_G3_source_only_after": 0,
            "HMT2R_G4_same_sources_as_stage_0": 0,
            "HMT2R_G5_no_redraw": "structural",
            "HMT2R_G6_per_age_table_complete": 0,
            "HMT2R_G7_strata_partition_the_finest_multi_states": 0,
            "HMT2R_G8_canary_excluded_from_aggregates": 0,
            "HMT2R_G9_declared_gate_coverage": "structural",
        },
        "gate_notes": {
            "HMT2R_G4_same_sources_as_stage_0": "truth seeds that differ from "
                                                "the stage 0 bank. Must be "
                                                "zero: item 5 forbids a redraw",
            "HMT2R_G7_strata_partition_the_finest_multi_states":
                "STABLE_MULTI_RESOLVED and AMBIGUOUS_FINE_MULTI must partition "
                "ALL_FINEST_MULTI exactly, with no state in both and none "
                "left over",
        },
        "after": "STOP if any corrected source-only gate fails. Item 11",
        "on_pass": "HMT2_STAGE1_RESOLUTION_AWARE_MORPHOLOGY_VALIDATION_V0 is "
                   "authorized by item 12, and is a separate registration",
        "not_authorized": ["order leakage", "geometry mismatch", "VLBI",
                           "machine learning",
                           "a new pixel-movie reconstruction campaign"],
        "attestation": attest([S0]),
    }
    OUT.write_text(json.dumps(doc, indent=2, default=str) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}\n  sha256 {sha256_file(OUT)}")
    print(f"  {len(doc['gates'])} gates, {len(doc['merger_rate_strata']) - 1} strata")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
