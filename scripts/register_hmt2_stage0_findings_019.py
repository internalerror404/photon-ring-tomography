#!/usr/bin/env python3
"""HMT2_STAGE0_PRESERVED_FINDINGS_019. Item 2 of REVIEWER_RULING_HMT2_STAGE0_019.

Record only. Preserves the four stage 0 findings permanently, each with the
scope it is entitled to and, where a stage 0 statement was wrong, the
correction beside it rather than in place of it.
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

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from phrt.attestation import attest  # noqa: E402
from phrt.config import sha256_file  # noqa: E402

S0 = ROOT / "artifacts" / "configs" / "HMT2_STAGE0_SOURCE_OBJECT_AND_RESOLUTION_AUDIT_V0.json"
S0R = ROOT / "artifacts" / "configs" / "HMT2_STAGE0R_SOURCE_ONLY_CORRECTION_V0.json"
TAB = ROOT / "artifacts" / "tables"
OUT = ROOT / "artifacts" / "configs" / "HMT2_STAGE0_PRESERVED_FINDINGS_019.json"


def main() -> int:
    st = pd.read_parquet(TAB / "hmt2_stage0_states.parquet")
    wd = pd.read_parquet(TAB / "hmt2_stage0_class_widths.parquet")
    pj = pd.read_parquet(TAB / "hmt2_stage0_projection.parquet")
    agg = st[(~st.canary) & (~st.off_manifold)]
    two = agg[agg.family == "two_hotspot_trajectories"]
    can = st[st.canary].iloc[0]
    mw = wd.dropna(subset=["minimum_representable_width_M"])
    pa = pj[(~pj.canary) & (~pj.off_manifold)]

    doc = {
        "schema": "phrt-record-amendment/1",
        "id": "HMT2_STAGE0_PRESERVED_FINDINGS_019",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "ruling": "REVIEWER_RULING_HMT2_STAGE0_019",
        "kind": "RECORD_ONLY",
        "accepted_commit": "2e478b49394fc6a199ad702911d0852a4a002d19",
        "qualified_by": "HMT2_STAGE0R_SOURCE_ONLY_CORRECTION_V0",

        "findings": {
            "HMT2_STAGE0_CANARY_BLENDED_61_OF_61": {
                "statement": "the HMT-1 truth that failed the sealed main "
                             "classifies BLENDED at all 61 ages, on every "
                             "grid",
                "measured": {
                    "n_blended": int(can.n_blended),
                    "n_ages": int(can.n_ages),
                    "n_multi_resolved": int(can.n_multi_resolved),
                    "n_ambiguous": int(can.n_ambiguous),
                    "positional_convergence_cells_median":
                        float(can.grid_convergence_cells_median),
                    "cardinality_disagreement_max":
                        int(can.grid_convergence_cardinality_error_max)},
                "reading": "not marginal and not unstable. A well-determined "
                           "field with one peak, from which HMT-1's gate was "
                           "demanding a resolved peak position that does not "
                           "exist. The gate was right to fail and the cause "
                           "was upstream of it",
                "scope": "this source, all ages, both finest grids",
                "unaffected_by_the_correction": True,
            },
            "HMT2_STAGE0_TWO_HOTSPOT_MIXED_RESOLUTION_REGIME": {
                "statement": "two_hotspot_trajectories occupies a mixed "
                             "resolution regime across its declared range: "
                             "part resolved, part blended, part unstable "
                             "between the two finest grids",
                "measured": {
                    "fraction_multi_resolved":
                        float(two.n_multi_resolved.sum() / two.n_ages.sum()),
                    "fraction_blended":
                        float(two.n_blended.sum() / two.n_ages.sum()),
                    "fraction_ambiguous":
                        float(two.n_ambiguous.sum() / two.n_ages.sum()),
                    "n_truths": int(len(two))},
                "reading": "the family is not uniformly resolvable and was "
                           "never checked to be. HMT-1 asked it for a resolved "
                           "peak position at every age",
                "scope": "the declared six families; the other five show no "
                         "ambiguity at all",
                "unaffected_by_the_correction": True,
            },
            "HMT2_STAGE0_L448_REPRESENTATION_LIMIT": {
                "statement": "the class HMT-1 used cannot keep a narrow radial "
                             "feature narrow, and its representation floor is "
                             "the largest of the two classes",
                "measured": {
                    "minimum_representable_width_M": {
                        f"r={int(r.r_centre_M)}": float(r.minimum_representable_width_M)
                        for _, r in mw[mw["class"] == "L448_contrast"].iterrows()},
                    "representation_floor_median_cells": float(
                        pa[pa["class"] == "L448_contrast"]
                        .representation_floor_median.median())},
                "reading": "the HMT-1 truth that failed had radial widths of "
                           "2.29 and 3.03 M at r near 45 M, where this class "
                           "broadens anything under about 6 M by a factor of "
                           "two. The failure was representable in the class "
                           "definition before any source was drawn",
                "floor_is_an_unbalanced_cost": "matched displacement plus a "
                                               "penalty per feature gained or "
                                               "lost, so large values mean a "
                                               "cardinality change and not a "
                                               "large distance",
                "unaffected_by_the_correction": True,
            },
            "HMT2_STAGE0_L896_RADIAL_ENRICHMENT_BENEFIT": {
                "statement": "doubling the radial functions, changing nothing "
                             "else, lowers the representation floor by about "
                             "an order of magnitude and narrows the minimum "
                             "representable width",
                "measured": {
                    "representation_floor_median_cells": {
                        "L448_contrast": float(
                            pa[pa["class"] == "L448_contrast"]
                            .representation_floor_median.median()),
                        "L896_radial_enriched": float(
                            pa[pa["class"] == "L896_radial_enriched"]
                            .representation_floor_median.median())},
                    "minimum_representable_width_M": {
                        f"r={int(r.r_centre_M)}": float(r.minimum_representable_width_M)
                        for _, r in mw[mw["class"] == "L896_radial_enriched"].iterrows()}},
                "reading": "the enrichment is nested in radius, so it adds "
                           "resolution and removes nothing. It improves the "
                           "floor substantially and still does not reach the "
                           "2 to 3 M widths the failing truth carried at large "
                           "radius",
                "unaffected_by_the_correction": True,
            },
        },

        "withheld_pending_stage_0r": {
            "quantity": "two-hotspot projection merger rates",
            "values": [0.356, 0.262],
            "status": "NOT_CANONICAL",
            "reason": "item 3. Taken over the finest grid's label, which "
                      "includes states the two finest grids disagree about",
        },

        "stage_0_statements_corrected": {
            "node_nesting": {
                "asserted": "each level doubles every axis, so every coarse "
                            "node is a fine node",
                "correct": "factor-two refinement, not node nesting. Only the "
                           "azimuthal axis nests: 32 equally spaced angles are "
                           "a subset of 64. The radial axis places 16 then 32 "
                           "points across a fixed log range and the temporal "
                           "axis 40 then 80 across a fixed interval, and in "
                           "neither case are the coarse nodes fine nodes",
                "verified": "checked directly on the three axes",
                "consequence": "none for any measured quantity. Nothing in the "
                               "audit assumed a shared node; the levels are "
                               "compared through the assignment metric, which "
                               "needs no common grid. The claim was wrong and "
                               "load-bearing for nothing",
            },
            "grid_convergence": {
                "asserted": "the grids themselves are converged",
                "correct": "positional convergence only. The reported figure "
                           "is a matched position cost and excludes unmatched "
                           "features by construction; the cardinality does "
                           "differ between levels, by at most one feature",
            },
            "recorded_source_only_booleans": {
                "defect": "stage 0 wrote ray_map_imported and "
                          "operator_constructed as literal false rather than "
                          "deriving them from an inspection. That records an "
                          "intention",
                "corrected_in": "stage 0R, which inspects before and after all "
                                "computation and derives the booleans from the "
                                "final inspection",
            },
        },

        "inputs": {"stage_0_freeze_sha256": sha256_file(S0),
                   "stage_0r_freeze_sha256": sha256_file(S0R)},
        "attestation": attest([S0, S0R]),
    }
    OUT.write_text(json.dumps(doc, indent=2, default=str) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}\n  sha256 {sha256_file(OUT)}")
    print(f"  {len(doc['findings'])} findings preserved, "
          f"{len(doc['stage_0_statements_corrected'])} statements corrected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
