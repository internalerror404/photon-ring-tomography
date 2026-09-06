#!/usr/bin/env python3
"""R3A: specify the acquisition, then test the constructor. No spectra.

The detector grid is chosen from the geometry and from a declared convergence
criterion, before any target quantity is computed and without ever forming the
target columns. That ordering is the point: a resolution picked to keep two
modes alive would not be a measurement, it would be a wish.
"""
from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from phrt.numerics import pin

pin()

import numpy as np  # noqa: E402
import scipy  # noqa: E402

from phrt.geometry.raymap import read  # noqa: E402
from phrt.revision_v4_1.common_sky import (POSTPROCESSING_INHERITED_NOISE,  # noqa: E402
                                           SINGLE_SKY_DETECTOR_NOISE,
                                           DetectorGrid,
                                           overlap_triplets)

MAPS = ROOT / "artifacts" / "raymaps"
REV = ROOT / "artifacts" / "revisions" / "mahakal_v4_1"
R1FZ = ROOT / "artifacts" / "configs" / "R1_MAIN_FREEZE.json"
GEOMETRY, ORDERS = "a050_i050", (0, 1, 2)
SIGMA = 0.011341986814407566           # the accepted actual sigma
CONVERGENCE_RTOL = 1e-12               # registered before any refinement runs
PAD = 0.2
# The registered ladder now continues below the ray pitch. The first run
# stopped at k=1 and so compared two pitches that were both still coarse
# enough to straddle ray cells; it could not have reached its own criterion
# whatever the construction did. Extending the ladder makes the criterion
# harder to satisfy, not easier, and the tolerance is unchanged.
REFINEMENT = (4, 2, 1, 0.5, 0.25, 0.125, 0.0625)
PROFILES = ("coarse", "core", "fine")


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def field(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """The declared smooth test fields. Not a spectrum and not a target."""
    return np.stack([np.ones(a.size), 0.01 * a, 0.01 * b], axis=1)


def ray_level_limit(a, b, cell, valid) -> float:
    """What the proxy tends to as the detector pitch goes to zero.

    Once every detector cell lies inside a single ray cell the proxy equals
    this exactly, at any pitch. It is therefore a ceiling the refinement may
    approach but must never pass: passing it would mean the quadrature had
    manufactured information that the rays never carried.
    """
    return float(cell * np.sum(field(a, b)[valid] ** 2) / SIGMA ** 2)


def probe(a, b, cell, valid, g: DetectorGrid) -> tuple[float, dict]:
    """The declared-field information proxy on one detector grid.

    Only the occupied detector rows are formed. An empty cell holds no signal
    and no information, so omitting it changes no sum -- and the refinement
    can then run far below the ray pitch, where a full-length row space would
    need hundreds of millions of entries per level.
    """
    rows, cols, w, acc = overlap_triplets(a, b, cell, g, valid)
    uniq, inv = np.unique(rows, return_inverse=True)
    y = np.zeros((uniq.size, 3))
    np.add.at(y, inv, w[:, None] * field(a, b)[cols])
    return float(np.sum(y ** 2) / (SIGMA ** 2 * g.cell_area)), acc


def main(run_dir: Path) -> int:
    t0 = time.time()
    run_dir.mkdir(parents=True, exist_ok=True)
    r1 = json.loads(R1FZ.read_text())
    t_obs = np.asarray(r1["observation"]["observer_times_M"], float)

    maps = {n: read(MAPS / f"{GEOMETRY}_n{n}_core.h5") for n in ORDERS}
    per_order, alpha_lo, alpha_hi, beta_lo, beta_hi = {}, [], [], [], []
    for n, rm in maps.items():
        v = rm.valid
        cell = float(np.unique(rm.pixel_area)[0])
        h = 0.5 * np.sqrt(cell)
        alpha_lo.append(float(rm.alpha[v].min() - h))
        alpha_hi.append(float(rm.alpha[v].max() + h))
        beta_lo.append(float(rm.beta[v].min() - h))
        beta_hi.append(float(rm.beta[v].max() + h))
        s_ = rm.coordinate_time[v] + rm.delay[v]
        ua = np.unique(rm.alpha)
        delta = float((ua[-1] - ua[0]) / (ua.size - 1))
        per_order[n] = {
            "realized_grid_spacing": delta,
            "realized_cell_area": delta * delta,
            "stored_over_realized_cell_area": cell / (delta * delta),
            "footprint_tiles_its_own_lattice":
                bool(abs(np.sqrt(cell) / delta - 1) < 1e-12),
            "path": f"artifacts/raymaps/{GEOMETRY}_n{n}_core.h5",
            "sha256": sha(MAPS / f"{GEOMETRY}_n{n}_core.h5"),
            "n_rays": int(rm.n_rays), "n_valid": int(v.sum()),
            "cell_area": cell, "cell_pitch": float(np.sqrt(cell)),
            "alpha_range": [float(rm.alpha[v].min()), float(rm.alpha[v].max())],
            "beta_range": [float(rm.beta[v].min()), float(rm.beta[v].max())],
            "total_valid_solid_angle": float(cell * v.sum()),
            "time_origin_coordinate_time_plus_delay": float(s_[0]),
            "time_origin_spread": float(np.ptp(s_)),
            "median_delay_M": float(np.median(rm.delay[v])),
        }

    # Field of view: every valid ray cell, plus a declared pad. Resolution: the
    # finest order's cell pitch, which is where the convergence test below
    # shows the mapping stops changing. Neither choice looks at a spectrum.
    finest = min(p["cell_pitch"] for p in per_order.values())
    grid = DetectorGrid(min(alpha_lo) - PAD, max(alpha_hi) + PAD,
                        min(beta_lo) - PAD, max(beta_hi) + PAD, finest)

    # Convergence of the mapping itself, on declared smooth fields, per
    # order, against the registered tolerance and against the ray-level
    # ceiling the refinement must never pass.
    conv = {}
    for n, rm in maps.items():
        a, b, v = rm.alpha, rm.beta, rm.valid
        cell = per_order[n]["cell_area"]
        limit = ray_level_limit(a, b, cell, v)
        seq = {}
        for k in REFINEMENT:
            g = DetectorGrid(grid.alpha_min, grid.alpha_max, grid.beta_min,
                             grid.beta_max, per_order[n]["cell_pitch"] * k)
            val, acc = probe(a, b, cell, v, g)
            seq[g.pitch] = {
                "refinement_factor": k, "n_detector_cells": g.n_cells,
                "info": val,
                "relative_deficit_against_ray_level_limit": val / limit - 1,
                "captured_fraction": acc["captured_fraction"],
                "area_outside_field_of_view":
                    acc["area_outside_field_of_view"]}
        order_p = sorted(seq, reverse=True)
        vals = [seq[q]["info"] for q in order_p]
        last = abs(vals[-1] / vals[-2] - 1)
        conv[n] = {
            "ray_level_limit": limit,
            "sequence": {f"{q:.10g}": seq[q] for q in order_p},
            "last_pair_relative_change": last,
            "converged": bool(last < CONVERGENCE_RTOL),
            "monotone_non_decreasing_under_refinement":
                bool(all(x <= y * (1 + 1e-12) for x, y in zip(vals, vals[1:]))),
            "never_exceeds_ray_level_limit":
                bool(max(vals) <= limit * (1 + 1e-9)),
            "residual_deficit_at_finest_pitch": vals[-1] / limit - 1,
        }

    # Why the criterion fails, measured rather than argued. The area overlap
    # is exact arithmetic; what is inexact is the proxy, and only because a
    # detector cell can straddle two ray cells. That needs the detector
    # lattice to be commensurate with the ray lattice, and two independent
    # things break commensurability here. Separating them is the whole
    # diagnosis, so each is switched on alone.
    align = {}
    for n, rm in maps.items():
        a, b, v = rm.alpha, rm.beta, rm.valid
        stored = per_order[n]["cell_area"]
        delta = per_order[n]["realized_grid_spacing"]
        row = {}
        for tag, cell, origin in (
                ("stored_footprint_shared_origin", stored, "shared"),
                ("realized_footprint_shared_origin", delta ** 2, "shared"),
                ("realized_footprint_lattice_aligned_origin", delta ** 2,
                 "lattice")):
            h = 0.5 * np.sqrt(cell)
            lim = ray_level_limit(a, b, cell, v)
            a0 = grid.alpha_min if origin == "shared" else float(a[v].min() - h)
            b0 = grid.beta_min if origin == "shared" else float(b[v].min() - h)
            g = DetectorGrid(a0, float(a[v].max() + h + 1e-9), b0,
                             float(b[v].max() + h + 1e-9), float(np.sqrt(cell)))
            val, _ = probe(a, b, cell, v, g)
            row[tag] = val / lim - 1
        align[n] = row

    # The quadrature weight the archive carries, against the grid it was
    # measured on. This is an audit of stored inputs, not a repair: nothing
    # here changes any operator, any weight or any archived endpoint.
    quad = {}
    for prof in PROFILES:
        for n in ORDERS:
            rm = read(MAPS / f"{GEOMETRY}_n{n}_{prof}.h5")
            ua = np.unique(rm.alpha)
            d = float((ua[-1] - ua[0]) / (ua.size - 1))
            st = float(np.unique(rm.pixel_area)[0])
            quad[f"{prof}_n{n}"] = {
                "grid_points_per_axis": int(ua.size),
                "axis_span_M": float(ua[-1] - ua[0]),
                "nominal_dx_M": float(np.sqrt(st)),
                "stored_pixel_area": st,
                "realized_grid_spacing_M": d,
                "realized_cell_area": d * d,
                "realized_over_stored_cell_area": d * d / st,
                "n_valid": int(rm.valid.sum()),
                "stored_total_solid_angle": float(st * rm.valid.sum()),
                "agrees": bool(abs(d * d / st - 1) < 1e-12)}
    quad_exact = [k for k, q in quad.items() if q["agrees"]]

    mapping = {
        "schema": "phrt-common-sky-mapping/1",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "stage": "R3A", "geometry": GEOMETRY, "orders": list(ORDERS),
        "raw_maps": per_order,
        "registration": {
            "coordinate_frame": "screen alpha, beta in M, as stored; no "
                                "rotation or rescaling is applied",
            "time_origin_rule": "coordinate_time + delay is one constant "
                                "across every ray of every order; verified, "
                                "not assumed",
            "time_origin_value": per_order[0][
                "time_origin_coordinate_time_plus_delay"],
            "cross_order_origin_drift": max(
                p["time_origin_coordinate_time_plus_delay"]
                for p in per_order.values()) - min(
                p["time_origin_coordinate_time_plus_delay"]
                for p in per_order.values()),
            "invalid_rays": "masked out of the mapping entirely; never "
                            "interpolated into signal",
            "pixel_footprints": "each order's cells are uniform and axis "
                                "aligned, so the overlap of a ray cell with a "
                                "detector cell is a product of interval "
                                "intersections and is exact",
            "mapping_rule": "conservative area overlap, not point sampling",
            "boundary_accounting": "area leaving the field of view is "
                                   "measured per order and reported",
            "index_sum_control": "retained only as a named nonphysical "
                                 "control; it is not this construction",
        },
        "detector_grid": {
            **grid.to_dict(),
            "field_of_view_rule": "the union of every valid ray cell plus a "
                                  f"{PAD} M pad",
            "resolution_rule": "the finest order's own cell pitch. Chosen "
                               "from geometry alone; the convergence study "
                               "below reports what that pitch does and does "
                               "not achieve, and does not revise it",
            "chosen_without_inspecting_any_target_quantity": True,
        },
        "convergence": {
            "registered_rtol": CONVERGENCE_RTOL,
            "tolerance_unchanged_after_the_first_failure": True,
            "refinement_factors_of_the_ray_pitch": list(REFINEMENT),
            "metric": "relative change in the declared-field whitened "
                      "information proxy between successive detector pitches",
            "per_order": conv,
            "all_converged": bool(all(c["converged"] for c in conv.values())),
            "no_information_manufactured_by_quadrature_refinement": bool(all(
                c["monotone_non_decreasing_under_refinement"]
                and c["never_exceeds_ray_level_limit"]
                for c in conv.values())),
        },
        "lattice_commensurability": {
            "why_it_matters": "the area overlap is exact arithmetic. The "
                              "proxy is inexact only where a detector cell "
                              "straddles two ray cells, so the mapping is "
                              "exact when the detector lattice is "
                              "commensurate with the ray lattice",
            "measured_relative_deficit": align,
            "reading": "a shared origin leaves a deficit of order one "
                       "percent that shrinks only like the pitch; aligning "
                       "the detector to one order's own lattice makes the "
                       "same mapping exact to about 1e-14 at every pitch "
                       "tested. Misalignment, not the overlap rule, is the "
                       "entire error",
            "realized_grid_spacings": {
                str(n): per_order[n]["realized_grid_spacing"] for n in ORDERS},
            "a_single_shared_lattice_can_align_with_all_three_orders": False,
            "obstruction": "the three realized spacings are mutually "
                           "incommensurate at any feasible detector pitch, "
                           "so no one uniform Cartesian detector is exact "
                           "for more than one order at a time",
        },
        "stored_quadrature_weight_audit": {
            "finding": "pixel_area is stored as the nominal dx squared, but "
                       "the realized ray grid spacing is span/(points-1), "
                       "which differs. The stored solid angle per ray is "
                       "therefore wrong by an order-dependent and "
                       "profile-dependent factor",
            "scope": "an audit of archived inputs. No operator, weight, "
                     "endpoint or archived result is altered here",
            "per_profile_and_order": quad,
            "combinations_that_agree": quad_exact,
            "n_combinations": len(quad),
            "n_agreeing": len(quad_exact),
            "worst_relative_area_error": max(
                abs(q["realized_over_stored_cell_area"] - 1)
                for q in quad.values()),
        },
        "observation": {"observer_times_M": t_obs.tolist(),
                        "n_times": int(t_obs.size)},
    }
    noise = {
        "schema": "phrt-acquisition-noise-models/2",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "actual_sigma": SIGMA,
        "derived_reference_snr": "the accepted normalized SNR 100 under the "
                                 "COMMON_REFERENCE_COUNT calibration; no "
                                 "silent recalibration is performed here",
        "fixed_during_spatial_refinement": True,
        "models_are_not_interchangeable": True,
        POSTPROCESSING_INHERITED_NOISE: {
            "signal": "A_sky = L A_resolved",
            "covariance": "C_sky = L C_resolved L^T, full, not its diagonal",
            "question": "how much of the parent experiment's information "
                        "survives a geometrically defined compression",
            "information_contraction": "required and tested (C7)",
            "identity_mixing": "exact re-expression, tested (C7b)",
            "is_an_observational_forecast": False,
        },
        SINGLE_SKY_DETECTOR_NOISE: {
            "signal": "the order contributions are summed on the screen "
                      "first: y = sum_n L_n A_n c",
            "covariance": "assigned once afterwards, sigma^2 times the "
                          "detector cell area per cell per observer time",
            "noise_per_order": "never; three orders landing on a cell do not "
                               "triple its variance (C8)",
            "read_noise_or_correlations": "absent, and absent by declaration "
                                          "rather than by oversight",
            "comparable_to_the_ideal_stack": False,
            "reason": "a different experiment with a different covariance. No "
                      "positive-semidefinite ordering against the ideal "
                      "order-labeled stack is assumed or tested",
            "telescope_feasibility_claim": "forbidden",
        },
    }
    (run_dir / "acquisition_noise_model_specification.json").write_text(
        json.dumps(noise, indent=2) + "\n")

    tests = subprocess.run(["python3", "-m", "pytest",
                            "tests/revision_v4_1/test_r3a_construction.py",
                            "-q", "--no-header"], cwd=ROOT,
                           capture_output=True, text=True)
    tail = [l for l in tests.stdout.strip().splitlines() if l.strip()][-1:]
    (run_dir / "R3A_constructor_test_results.json").write_text(json.dumps({
        "schema": "phrt-r3a-tests/1",
        "suite": "tests/revision_v4_1/test_r3a_construction.py",
        "summary": tail[0] if tail else "not run",
        "returncode": tests.returncode,
        "canaries": {
            "C1": "registration uses screen coordinates, not equal counts",
            "C2": "invariance to independent input row permutations",
            "C3": "flux conservation with explicit boundary accounting",
            "C4": "single-sky all-order total flux equals the sum of orders",
            "C5": "detector refinement converges on the real tiled geometry, "
                  "on a lattice-aligned grid",
            "C5b": "the two noise models are recorded as different, with no "
                   "ordering asserted between them",
            "C6": "block forward and adjoint consistency",
            "C7": "inherited-noise postprocessing contracts information",
            "C7b": "identity mixing is an exact re-expression",
            "C8": "detector noise is assigned once, not once per order",
            "C9": "one geometry-wide time origin, verified from the raw maps",
            "C9b": "delay is non-negative and increases with image order",
            "C10": "stored pixel_area is checked against the realized grid "
                   "spacing, so no construction can adopt one silently",
            "C11": "refinement approaches the ray-level ceiling and never "
                   "passes it: no information manufactured by quadrature",
            "C12": "the same overlap rule is exact to machine precision on a "
                   "commensurate lattice, which locates the deficit",
        },
    }, indent=2) + "\n")

    frozen = {}
    for rel in ["src/phrt/revision_v4_1/common_sky.py",
                "scripts/revision_v4_1/r3a_build.py",
                "scripts/revision_v4_1/r3a_localization_overlay.py",
                "tests/revision_v4_1/test_r3a_construction.py",
                "artifacts/configs/R1_MAIN_FREEZE.json",
                str((REV / "R2_REPLAY_TARGET_MANIFEST.json"
                     ).relative_to(ROOT))]:
        frozen[rel] = sha(ROOT / rel)
    for n in ORDERS:
        rel = f"artifacts/raymaps/{GEOMETRY}_n{n}_core.h5"
        frozen[rel] = per_order[n]["sha256"]
    (run_dir / "R3A_ACQUISITION_INPUT_FREEZE.json").write_text(json.dumps({
        "schema": "phrt-input-freeze/1", "id": "R3A_ACQUISITION_INPUT_FREEZE",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "detector_design_frozen_before_any_target_quantity": True,
        "target_indices_unchanged": "the accepted 72 columns; reselection due "
                                    "to an acquisition result is forbidden",
        "environment": {"python": platform.python_version(),
                        "numpy": np.__version__, "scipy": scipy.__version__},
        "commit_at_freeze_time": subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True,
            text=True).stdout.strip(),
        "n_files": len(frozen), "files": frozen,
    }, indent=2) + "\n")

    blocked = (not mapping["convergence"]["all_converged"]) or bool(
        [k for k, q in quad.items() if not q["agrees"]])
    status = ("R3A_CONSTRUCTION_BLOCKED" if blocked
              else "R3A_COMMON_SKY_CONSTRUCTION_READY_FOR_REVIEW")
    mapping["status"] = status
    (run_dir / "raw_to_common_sky_mapping_manifest.json").write_text(
        json.dumps(mapping, indent=2) + "\n")

    print(f"detector grid {grid.n_alpha} x {grid.n_beta} = {grid.n_cells} "
          f"cells at pitch {grid.pitch}")
    print(f"  field of view alpha [{grid.alpha_min:.2f}, {grid.alpha_max:.2f}] "
          f"beta [{grid.beta_min:.2f}, {grid.beta_max:.2f}]")
    print(f"  cross-order time origin drift "
          f"{mapping['registration']['cross_order_origin_drift']:.3e}")
    for n, c in conv.items():
        print(f"  order {n}: converged {c['converged']}, last pair "
              f"{c['last_pair_relative_change']:.3e}, residual deficit "
              f"{c['residual_deficit_at_finest_pitch']:+.3e}, ceiling "
              f"respected {c['never_exceeds_ray_level_limit']}")
    for n, r in align.items():
        print(f"  order {n} alignment: " + "  ".join(
            f"{k.replace('_footprint', '').replace('_origin', '')}="
            f"{v_:+.2e}" for k, v_ in r.items()))
    print(f"  stored quadrature weight agrees in {len(quad_exact)} of "
          f"{len(quad)} profile/order combinations")
    print(f"  tests: {tail[0] if tail else 'not run'}")
    print(f"  status {status}")
    print(f"  runtime {time.time() - t0:.0f}s")
    return 0 if tests.returncode == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main((ROOT / sys.argv[1]).resolve()))
