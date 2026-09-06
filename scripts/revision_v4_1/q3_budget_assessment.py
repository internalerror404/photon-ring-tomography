#!/usr/bin/env python3
"""Q3 trigger assessment: can the authorized budget reach the Q2 criteria?

Ruling 026 authorizes bounded same-geometry refinement only if a complete
preexecution plan can be committed, and instructs that an insufficient cap be
returned as a precise blocker rather than worked around. This computes what
the observed rates demand, against the cap, before any ray is traced.

Two data points per metric is the minimum a rate can be estimated from, and
that limitation is reported rather than hidden. It does not need to be precise
to settle the question: the shortfall is orders of magnitude.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from phrt.geometry.raymap import read                       # noqa: E402
from phrt.revision_v4_1 import measure as M                 # noqa: E402

MAPS = ROOT / "artifacts" / "raymaps"
GEOMETRY = "a050_i050"
CAP = {"total_new_screen_order_ray_evaluations_maximum": 250000,
       "batches_maximum": 2, "evaluations_per_batch_maximum": 125000,
       "peak_memory_GiB_maximum": 8, "wall_clock_hours_maximum": 2}


def main(out_dir: Path, q2_dir: Path) -> int:
    conv = json.loads((q2_dir / "FIXED_DETECTOR_PROFILE_CONVERGENCE.json"
                       ).read_text())
    tol = conv["tolerances"]
    early = {c["order"]: c for c in conv["comparisons"]
             if c["pair"] == "coarse->core"}
    late = {c["order"]: c for c in conv["comparisons"]
            if c["pair"] == "core->fine"}

    geo = {}
    for n in (0, 1, 2):
        rm = read(MAPS / f"{GEOMETRY}_n{n}_fine.h5")
        cells = M.build_ray_cells(rm.alpha, rm.beta, M.NODAL_DUAL_CLIPPED)
        v = rm.valid
        V = M.valid_matrix(rm.alpha, rm.beta, cells, v)
        # boundary cells of the valid region, and hence its perimeter
        e = V & ~(np.roll(V, 1, 0) & np.roll(V, -1, 0)
                  & np.roll(V, 1, 1) & np.roll(V, -1, 1))
        d = cells.axis_alpha.spacing
        geo[n] = {"fine_spacing_M": d,
                  "fine_valid_rays": int(v.sum()),
                  "fine_boundary_cells": int(e.sum()),
                  "valid_area_M2": float(cells.area[v].sum()),
                  "approximate_boundary_length_M": float(e.sum()) * d,
                  "declared_domain_half_width_M":
                      cells.axis_alpha.domain_hi}

    rows = []
    for n in (0, 1, 2):
        g = geo[n]
        for metric, key in (("response", "worst_relative_response_error"),
                            ("mask", None), ("area", None)):
            if metric == "response":
                e1, e2 = early[n][key], late[n][key]
                target = tol["fixed_detector_response_relative"]
            elif metric == "mask":
                e1 = early[n]["mask"]["relative_error"]
                e2 = late[n]["mask"]["relative_error"]
                target = tol["mask_symmetric_difference_relative"]
            else:
                e1 = early[n]["area"]["relative_error"]
                e2 = late[n]["area"]["relative_error"]
                target = tol["corrected_area_relative"]
            if e2 <= target:
                rows.append({"order": n, "metric": metric, "late_error": e2,
                             "target": target, "already_meets_target": True})
                continue
            # both pairs halve the spacing, so the observed order is
            # log2(e_early / e_late)
            p = float(np.log2(e1 / e2)) if e2 > 0 and e1 > 0 else float("nan")
            if not np.isfinite(p) or p <= 0:
                rows.append({"order": n, "metric": metric, "late_error": e2,
                             "target": target, "already_meets_target": False,
                             "observed_order": p,
                             "note": "no convergence rate can be estimated "
                                     "from these two pairs"})
                continue
            shrink = (e2 / target) ** (1.0 / p)          # spacing must divide by
            d_new = g["fine_spacing_M"] / shrink
            uniform = g["fine_valid_rays"] * shrink ** 2
            adaptive = g["approximate_boundary_length_M"] / d_new
            rows.append({
                "order": n, "metric": metric,
                "early_pair_error": e1, "late_pair_error": e2,
                "target": target, "already_meets_target": False,
                "observed_order_from_two_pairs": p,
                "spacing_must_shrink_by": shrink,
                "required_spacing_M": d_new,
                "uniform_refinement_new_in_band_evaluations": uniform,
                "boundary_adaptive_new_evaluations_lower_bound": adaptive,
                "uniform_over_cap":
                    uniform / CAP["total_new_screen_order_ray_evaluations_maximum"],
                "adaptive_over_cap":
                    adaptive / CAP["total_new_screen_order_ray_evaluations_maximum"],
            })

    need = [r for r in rows if not r["already_meets_target"]
            and "adaptive_over_cap" in r]
    worst_u = max(r["uniform_over_cap"] for r in need)
    worst_a = max(r["adaptive_over_cap"] for r in need)
    cheapest_a = min(r["adaptive_over_cap"] for r in need)
    feasible = worst_a <= 1.0

    rep = {
        "stage": "Q3_TRIGGER_ASSESSMENT", "ruling": "PAPER_I_R3A_RULING_026",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "commit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                 capture_output=True, text=True).stdout.strip(),
        "no_rays_traced": True,
        "purpose": "decide, before tracing anything, whether the authorized "
                   "cap can reach the registered Q2 criteria",
        "cap": CAP,
        "geometry_inputs": geo,
        "rate_estimated_from": "two successive pairs, the minimum from which "
                               "a rate can be estimated; the shortfall below "
                               "is large enough that the estimate's precision "
                               "does not change the conclusion",
        "requirements": rows,
        "worst_uniform_multiple_of_cap": worst_u,
        "worst_boundary_adaptive_multiple_of_cap": worst_a,
        "cheapest_boundary_adaptive_multiple_of_cap": cheapest_a,
        "cap_is_sufficient": feasible,
        "status": "Q3_AUTHORIZED_AND_PLANNED" if feasible
                  else "R3A_QC_REFINEMENT_BUDGET_OR_CAPABILITY_BLOCKED",
        "diagnosis": {
            "dominant_error": "binary rasterization of region boundaries -- "
                              "the lensing-band rim for orders 1 and 2, the "
                              "shadow rim and the screen rim for order 0",
            "why_the_response_metric_is_worse_than_the_area_metric":
                "a whitened response is a vector over detector cells and "
                "observer times, so a boundary cell that flips contributes "
                "its whole amplitude to the L2 difference while contributing "
                "almost nothing to a total. Order 0's areas agree to 0.19% "
                "while its responses differ by 5.0%, which is exactly the "
                "compensating-boundary case the ruling warned a scalar total "
                "would conceal",
            "convergence_is_first_order":
                "a node is either in the band or out of it, so the "
                "represented boundary moves in steps of the spacing and the "
                "error falls like the spacing, not its square",
            "more_rays_is_the_wrong_instrument":
                "the deficit is in how the boundary is represented, not in "
                "how many samples sit inside it",
        },
        "tracer_capability": {
            "can_the_pinned_backend_evaluate_non_uniform_points": True,
            "evidence": "aart.raytracing.raytrace reads gridN/maskN from the "
                        "lensing-band file and passes the point array "
                        "straight to rt.rt, which takes an arbitrary "
                        "supergrid. Only lensingbands.grid_mask insists on a "
                        "uniform linspace, and it is a generator, not the "
                        "tracer. An adaptive point set could therefore be "
                        "traced by the same pinned backend and the same "
                        "physical model",
            "conclusion": "this is a BUDGET blocker, not a capability one. "
                          "The tracer would do the work; there is no "
                          "authorized allowance large enough to ask it for",
        },
        "representation_gap": {
            "observation": "the deficit is first order because a node is "
                           "either inside the band or outside it, so the "
                           "represented boundary moves in whole cells",
            "what_would_change_the_order": "fractional cell coverage at the "
                                           "region boundary instead of binary "
                                           "node classification",
            "is_the_information_already_available": True,
            "where": "aart.lensingbands.hulls returns the inner and outer "
                     "band curves that grid_mask already tests node "
                     "membership against, and matplotlib.path is already the "
                     "membership test. Cutting boundary cells against those "
                     "curves would give a coverage fraction rather than a "
                     "step, on the maps that already exist and with no new "
                     "rays at all",
            "for_order_0": "the shadow rim has the same treatment available; "
                           "the screen rim is a declared domain edge and is "
                           "already exact under clipped dual cells",
            "what_is_not_claimed": "that this would pass. The hulls are "
                                   "themselves polygons built from a finite "
                                   "number of marks on the critical curve "
                                   "(npointsS=60 here), so their own "
                                   "resolution would become the limiting "
                                   "error and has not been measured",
            "not_authorized_here": "changing the representation is not a "
                                   "bounded refinement of the existing one "
                                   "and is outside what ruling 026 "
                                   "authorizes. It is reported as the "
                                   "cheapest identified route, not adopted",
        },
        "what_was_not_done": [
            "no ray was traced and no batch was submitted",
            "no tolerance was adjusted",
            "no tracer, target, detector or sigma was changed",
            "no paid resource was acquired",
        ],
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "Q3_BUDGET_ASSESSMENT.json").write_text(
        json.dumps(rep, indent=2) + "\n")

    print(f"cap {CAP['total_new_screen_order_ray_evaluations_maximum']} "
          f"new evaluations in {CAP['batches_maximum']} batches")
    for r in rows:
        if r["already_meets_target"]:
            print(f"  n{r['order']} {r['metric']:<9} already within budget "
                  f"({r['late_error']:.3e})")
            continue
        print(f"  n{r['order']} {r['metric']:<9} {r['late_pair_error']:.3e} -> "
              f"{r['target']:.0e}: order {r['observed_order_from_two_pairs']:.2f}, "
              f"spacing /{r['spacing_must_shrink_by']:.4g}, uniform "
              f"{r['uniform_refinement_new_in_band_evaluations']:.3g} "
              f"({r['uniform_over_cap']:.3g}x cap), adaptive "
              f"{r['boundary_adaptive_new_evaluations_lower_bound']:.3g} "
              f"({r['adaptive_over_cap']:.3g}x cap)")
    print(f"  worst adaptive requirement is {worst_a:.4g}x the cap")
    print(f"  status {rep['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main((ROOT / sys.argv[1]).resolve(),
                          (ROOT / sys.argv[2]).resolve()))
