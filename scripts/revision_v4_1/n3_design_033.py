#!/usr/bin/env python3
"""N3 of ruling 033: the adaptive integration design, costed. Zero queries.

Ruling 033 retires the 18-endpoint layout prospectively and asks for one
domain-aware adaptive structure on D026 evaluating the SAME fixed detector
integral. This stage designs it and prices it from archived geometry alone --
no ray is traced, no path integral is recomputed, and no new sampling is done
to prepare the plan.

The cost model is built from three measurable inputs, all cached:

* the emitting boundary's length per order, from the transition-cell census;
* the accuracy the area budget demands of that boundary, which sets how deep a
  bracketed bisection has to go;
* the field's interpolation error, measured by carrying the coarse profile's
  own transfer field onto the fine profile's nodes and comparing.

The third is the one that decides whether the interior needs new samples at
all, and it is a comparison of two archived maps rather than a forecast.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

import h5py
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from phrt.geometry.raymap import horizon_radius, read            # noqa: E402
from phrt.revision_v4_1 import domain as D                       # noqa: E402
from phrt.revision_v4_1 import fractional as FR                  # noqa: E402
from phrt.revision_v4_1 import leaf2 as L2                       # noqa: E402
from phrt.revision_v4_1 import measure as M                      # noqa: E402
from phrt.revision_v4_1 import pathdomain3 as P3                 # noqa: E402
from phrt.revision_v4_1.common_sky import DetectorGrid           # noqa: E402

MAPS = ROOT / "artifacts" / "raymaps"
AART = ROOT / "artifacts" / "e3_pilot" / "aart_out"
BANDS = {"core": AART / ("core/LensingBands_a_0.5_i_50.0_dx0_0.4_dx1_0.08"
                         "_dx2_0.02.h5"),
         "fine": AART / ("fine/LensingBands_a_0.5_i_50.0_dx0_0.2_dx1_0.04"
                         "_dx2_0.01.h5")}
HULL = ROOT / ("artifacts/revisions/mahakal_v4_1/G1C_20260907T075203Z_d252697"
               "/CLOSEOUT_ARRAYS_029.npz")
GEOMETRY, SPIN, INC, D_OBS, R_OUTER = "a050_i050", 0.5, 50.0, 1000.0, 50.0
SIGMA, T_REF = 0.011341986814407566, -978.6055123201214
AREA_BUDGET, COMPONENT_BUDGET, HULL_BUDGET = 1.0e-3, 5.0e-4, 2.5e-4
N_TIMES = 8
FIELD_CHANNELS = ("emission_indicator_chi", "redshift_cubed_g3",
                  "source_azimuth_phi_s", "source_coordinate_time_t_s")


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def transition_mask(state, n_alpha: int) -> np.ndarray:
    E = (state == D.CERTIFIED_EMITTING).reshape(n_alpha, n_alpha)
    m = np.zeros_like(E)
    m[:-1, :] |= E[:-1, :] != E[1:, :]
    m[1:, :] |= E[:-1, :] != E[1:, :]
    m[:, :-1] |= E[:, :-1] != E[:, 1:]
    m[:, 1:] |= E[:, :-1] != E[:, 1:]
    return m.reshape(-1)


def measure_inputs() -> dict:
    """Boundary length, band area and field interpolation error, per order."""
    rh = horizon_radius(SPIN)
    grid = DetectorGrid(-25.0, 25.0, -25.0, 25.0, 0.4)
    hz = np.load(HULL)
    out = {}
    for n in (0, 1, 2):
        rec = {}
        for prof in ("core", "fine"):
            with h5py.File(BANDS[prof], "r") as h:
                band = h[f"mask{n}"][:]
            rm = read(MAPS / f"{GEOMETRY}_n{n}_{prof}.h5")
            cells = M.build_ray_cells(rm.alpha, rm.beta, M.NODAL_DUAL_CLIPPED)
            ov = FR.triple_overlap(cells, grid, hz[f"tess_{n}e"],
                                   hz[f"tess_{n}i"])
            st, _ = D.classify_points(band, rm.source_r, rm.source_phi,
                                      rm.coordinate_time, rm.redshift, rh,
                                      R_OUTER)
            active = ov.active_area > 0
            tm = transition_mask(st, np.unique(rm.alpha).size) & active
            pitch = float(np.diff(np.unique(rm.alpha))[0])
            # a transition band is about two cells across, so the boundary
            # length it brackets is about half the flagged area divided by
            # the cell width
            length = float(0.5 * ov.active_area[tm].sum() / pitch) \
                if tm.any() else 0.0
            rec[prof] = {
                "pitch_M": pitch,
                "band_active_area": float(ov.active_area.sum()),
                "transition_parents": int(tm.sum()),
                "transition_area": float(ov.active_area[tm].sum()),
                "boundary_length_estimate_M": length,
                "unresolved_support_area": float(
                    ov.active_area[(st == D.UNRESOLVED) & active].sum()),
            }
            if prof == "fine":
                rec["field_interpolation"] = field_error(n, rm, band, st)
        out[f"n{n}"] = rec
    return out


def field_error(n: int, fine_rm, fine_band, fine_state) -> dict:
    """Carry the coarse field onto the fine nodes and measure the difference.

    This is the question the interior of the design turns on: if the archived
    coarse profile already represents the transferred field to better than the
    component budget, the interior needs no new samples and the whole cost
    lives on the boundary. It is measured on two archived maps, not assumed.
    """
    core = read(MAPS / f"{GEOMETRY}_n{n}_core.h5")
    ca = np.unique(core.alpha)
    cb = np.unique(core.beta)
    ok = np.isfinite(core.redshift) & np.isfinite(core.source_r)
    out = {}
    for name, arr in (("redshift", core.redshift),
                      ("source_r", core.source_r),
                      ("coordinate_time", core.coordinate_time)):
        g = np.where(ok, arr, np.nan).reshape(ca.size, cb.size)
        ia = np.clip(np.searchsorted(ca, fine_rm.alpha) - 1, 0, ca.size - 2)
        ib = np.clip(np.searchsorted(cb, fine_rm.beta) - 1, 0, cb.size - 2)
        ta = (fine_rm.alpha - ca[ia]) / (ca[ia + 1] - ca[ia])
        tb = (fine_rm.beta - cb[ib]) / (cb[ib + 1] - cb[ib])
        v = ((1 - ta) * (1 - tb) * g[ia, ib] + ta * (1 - tb) * g[ia + 1, ib]
             + (1 - ta) * tb * g[ia, ib + 1] + ta * tb * g[ia + 1, ib + 1])
        ref = np.where(np.isfinite(getattr(fine_rm, name)),
                       getattr(fine_rm, name), np.nan)
        m = (fine_state == D.CERTIFIED_EMITTING) & np.isfinite(v) \
            & np.isfinite(ref)
        if not m.any():
            out[name] = {"comparable_nodes": 0}
            continue
        scale = float(np.nanmax(np.abs(ref[m])))
        rel = np.abs(v[m] - ref[m]) / max(scale, 1e-30)
        out[name] = {
            "comparable_nodes": int(m.sum()),
            "coverage_of_emitting_nodes": float(
                m.sum() / max((fine_state == D.CERTIFIED_EMITTING).sum(), 1)),
            "median_relative_error": float(np.median(rel)),
            "p95_relative_error": float(np.quantile(rel, 0.95)),
            "max_relative_error": float(rel.max()),
            "nodes_above_the_component_budget": int(
                np.count_nonzero(rel > COMPONENT_BUDGET)),
            "fraction_above_the_component_budget": float(
                np.count_nonzero(rel > COMPONENT_BUDGET) / m.sum()),
        }
    return out


def cost_model(inp: dict) -> dict:
    """Expected and worst-case new native evaluations for the adaptive design."""
    per_order = {}
    exp_tot = worst_tot = 0
    for n in (0, 1, 2):
        rec = inp[f"n{n}"]["fine"]
        A = rec["band_active_area"]
        L = rec["boundary_length_estimate_M"]
        w = rec["pitch_M"]
        # the boundary strip may contribute at most delta * L of area error
        delta = AREA_BUDGET * A / L if L > 0 else w
        depth = max(0, int(np.ceil(np.log2(max(w / delta, 1.0)))))
        segments = int(np.ceil(L / w)) if w > 0 else 0
        # per segment: two bracketing evaluations plus one per bisection level
        expected = segments * (2 + depth)
        # worst case: the bracket fails once and the depth doubles, and every
        # segment hides a second crossing
        worst = 2 * segments * (2 + 2 * depth)
        fi = inp[f"n{n}"].get("field_interpolation", {})
        frac = max((v.get("fraction_above_the_component_budget", 0.0)
                    for v in fi.values() if isinstance(v, dict)), default=0.0)
        interior = int(np.ceil(frac * rec["transition_parents"] * 4))
        per_order[f"n{n}"] = {
            "band_area": A, "boundary_length_M": L, "seed_pitch_M": w,
            "required_boundary_resolution_M": delta,
            "bisection_depth": depth, "boundary_segments": segments,
            "expected_boundary_calls": expected,
            "worst_case_boundary_calls": worst,
            "interior_calls_from_measured_field_error": interior,
            "expected_total": expected + interior,
            "worst_case_total": worst + 4 * interior,
        }
        exp_tot += expected + interior
        worst_tot += worst + 4 * interior
    return {"per_order": per_order, "expected_new_native_evaluations": exp_tot,
            "worst_case_new_native_evaluations": worst_tot}


def design(inp: dict, cost: dict) -> dict:
    exp = cost["expected_new_native_evaluations"]
    worst = cost["worst_case_new_native_evaluations"]
    val = int(np.ceil(0.05 * exp)) + 192
    return {
        "id": "ADAPTIVE_DOMAIN_AWARE_D026_V1",
        "quantity": ("the same fixed detector transfer integral: "
                     "y_d = sum over the emitting set of |D_d ^ dA| chi f, "
                     "for all three orders, the eight accepted observer times "
                     "and the declared field channels"),
        "unchanged": {"detector": "D026", "pitch_M": 0.4, "sigma": SIGMA,
                      "clock_reference_M": T_REF, "observer_times": N_TIMES,
                      "orders": [0, 1, 2],
                      "source_annulus": "horizon exclusive to 50 inclusive",
                      "intended_full_detector_domain": "unchanged"},
        "field_channels": list(FIELD_CHANNELS),
        "structure": {
            "mesh": "one quadtree per order over the declared aperture, "
                    "seeded by the archived core map and refined locally",
            "seeds": "the core and fine maps supply initial data and a fixed "
                     "independent check; neither is re-traced at every depth",
            "boundary": "crossings localised as one-dimensional bracketed "
                        "events on verified branches, with the version 3 "
                        "comparator deciding each bracket",
            "interior": "smooth interiors are not refined at boundary density; "
                        "their refinement is driven by the measured field "
                        "interpolation error",
            "assembly": "leaf-clipped sparse fragments, ruling 032 rule, with "
                        f"the sign-aware envelopes of {L2.BOUND_RULE}",
            "deduplication": "one native evaluation per distinct (alpha, beta, "
                             "order); one valid transfer tuple serves all eight "
                             "observer times and every declared test function "
                             "algebraically",
            "multiple_crossings": "each bracket is tested for sign changes at "
                                  "both ends and subdivided when more than one "
                                  "is present; tangencies and disconnected "
                                  "support stay detectable rather than assumed "
                                  "absent",
        },
        "error_budget_tracked_separately": {
            "hull_geometry": {"budget": HULL_BUDGET,
                              "status": "already qualified at 9.592e-08 "
                                        "band-normalised, ruling 029"},
            "emitting_boundary": {"budget": AREA_BUDGET,
                                  "controlled_by": "bisection depth per order"},
            "field_quadrature_and_interpolation": {
                "budget": COMPONENT_BUDGET,
                "controlled_by": "interior refinement driven by the measured "
                                 "core-to-fine interpolation error"},
            "numerical_reference": {
                "status": "COMPARATOR_NUMERICALLY_VALIDATED_ON_TESTED_COHORTS",
                "policy": P3.POLICY},
            "unknown_support": {
                "status": "carried as a sign-aware response envelope; where no "
                          "envelope exists the result stays unqualified",
                "note": "the order-2 missing-centre area is a coverage warning "
                        "and is not a measured lost-light fraction"},
        },
        "refinement_indicators": ["emitting boundary uncertainty",
                                  "declared field interpolation error",
                                  "geometric cell size"],
        "targets_or_singular_modes_used_to_refine": False,
        "convergence_evidence": {
            "two_successive_late_refinement_comparisons": "required; the last "
                                                          "two depths of each "
                                                          "order's boundary "
                                                          "refinement",
            "independent_check": "a held-out five per cent of the mesh plus "
                                 "the 192-point independent panel, evaluated "
                                 "with the alternate comparator",
            "planned_independent_validation_calls": val,
        },
        "coverage": "the full declared aperture for every order; any region "
                    "left out is reported as an explicit unbounded remainder, "
                    "never as agreement",
        "stopping_rules": {
            "early_stop": "when both late refinements agree inside every "
                          "tracked budget",
            "hard_stop": "when the worst-case remaining calls would breach the "
                         "funded allowance; the run refuses to start rather "
                         "than deliver partial arms",
            "unfunded_endpoint": "the campaign does not start",
        },
        "payload_cache_key": ["screen_alpha", "screen_beta", "order",
                              "geometry", "observer_convention", "backend",
                              "numerical_policy", "precision"],
        "lost_I2_cache": "not available; values are not reconstructed from "
                         "coordinates and are not counted as reusable",
        "cost": cost,
        "funding": {
            "expected_new_native_evaluations": exp,
            "worst_case_new_native_evaluations": worst,
            "independent_validation_calls": val,
            "expected_total_with_validation": exp + val,
            "worst_case_total_with_validation": worst + val,
            "second_batch_remaining_after_this_ruling": 854,
            "fits_the_remaining_balance": bool(worst + val <= 854),
            "comparison_to_the_retired_uniform_layout": 444720,
            "reduction_factor_expected": 444720 / max(exp, 1),
            "note": "an expected cost is not a guarantee; the worst case is "
                    "what an allowance has to cover",
        },
        "physical_execution": "requires a later ruling; nothing here is a "
                              "permission to sample",
    }


def main(out: Path) -> int:
    t0 = time.time()
    inp = measure_inputs()
    cost = cost_model(inp)
    des = design(inp, cost)
    rep = {
        "stage": "N3", "ruling": "PAPER_I_FEASIBILITY_AND_CLOSEOUT_RULING_033",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "commit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                 capture_output=True, text=True).stdout.strip(),
        "new_physical_queries": 0, "new_sampling_to_prepare_this_plan": 0,
        "measured_inputs": inp, "design": des,
    }
    (out / "ADAPTIVE_INTEGRATION_DESIGN_033.json").write_text(
        json.dumps(rep, indent=2) + "\n")
    print(json.dumps({
        "stage": "N3",
        "expected": cost["expected_new_native_evaluations"],
        "worst_case": cost["worst_case_new_native_evaluations"],
        "validation": des["funding"]["independent_validation_calls"],
        "fits_854": des["funding"]["fits_the_remaining_balance"],
        "seconds": round(time.time() - t0)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main((ROOT / sys.argv[1]).resolve()))
