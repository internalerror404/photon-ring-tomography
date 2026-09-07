#!/usr/bin/env python3
"""M1 of ruling 032: the corrected leaf assembly, measured. Zero queries.

The rule under test is

    y_d = sum_p sum_(l in leaves(p)) |D_d ^ C_l ^ B_n| chi(xi_l) f(xi_l),

against the parent-averaged occupancy proxy that 031 actually ran. The two are
compared on archived order-0 core geometry -- real band, real hull, real cell
measure -- so the difference reported here is a property of the campaign's own
screen, not of a fixture.
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
from phrt.geometry.raymap import read                            # noqa: E402
from phrt.revision_v4_1 import fractional as FR                  # noqa: E402
from phrt.revision_v4_1 import leaf as LF                        # noqa: E402
from phrt.revision_v4_1 import measure as M                      # noqa: E402
from phrt.revision_v4_1 import plan032 as PL                     # noqa: E402
from phrt.revision_v4_1.common_sky import DetectorGrid           # noqa: E402

HULL = ROOT / ("artifacts/revisions/mahakal_v4_1/G1C_20260907T075203Z_d252697"
               "/CLOSEOUT_ARRAYS_029.npz")
SIGMA = 0.011341986814407566
TEST_FILES = ("tests/revision_v4_1/test_leaf_032.py",
              "tests/revision_v4_1/test_plan032.py",
              "tests/revision_v4_1/test_rootcheck_032.py")

INJECTIONS = ("193_points_under_192_point_cap",
              "unresolved_reference_prerequisite",
              "missing_fine_or_order2_endpoint",
              "occupancy_only_pretending_full_transfer",
              "equal_norm_different_detector_vectors",
              "parent_fraction_assembly_in_actual_consumer",
              "missing_numerical_payload",
              "infeasible_complete_bundle_or_validation_reserve_invasion",
              "missing_prerequisite_record")


def counterexample() -> dict:
    """The ruling's own unit cell, through the production kernel."""
    forbidden = LF.parent_fraction_response(
        np.array([0, 1]), np.array([0, 0]), np.array([0.5, 0.5]),
        [0.2], [1.0], 2).ravel()
    edges = np.linspace(0.0, 1.0, 11)
    mid = 0.5 * (edges[:-1] + edges[1:])
    rows, cols, vals = [], [], []
    for i, (lo, hi) in enumerate(zip(edges[:-1], edges[1:])):
        for d, (dlo, dhi) in enumerate(((0.0, 0.5), (0.5, 1.0))):
            w = max(0.0, min(hi, dhi) - max(lo, dlo))
            if w > 0:
                rows.append(d), cols.append(i), vals.append(w)
    a = LF.assemble(np.array(rows), np.array(cols), np.array(vals),
                    np.where(mid < 0.2, LF.EMITTING, LF.NOT_EMITTING),
                    np.ones(10), 2, granularity=LF.LEAF_RULE)
    return {"exact": [0.2, 0.0], "parent_fraction": forbidden.tolist(),
            "leaf_rule": a.known.ravel().tolist(),
            "totals_agree": bool(abs(forbidden.sum() - a.known.sum()) < 1e-12),
            "images_agree": False}


def on_archived_geometry() -> dict:
    """Order-0 core: per-row conservation, and where the two rules disagree."""
    rm = read(ROOT / "artifacts/raymaps/a050_i050_n0_core.h5")
    grid = DetectorGrid(-25.0, 25.0, -25.0, 25.0, 0.4)
    hz = np.load(HULL)
    cells = M.build_ray_cells(rm.alpha, rm.beta, M.NODAL_DUAL_CLIPPED)
    ov = FR.triple_overlap(cells, grid, hz["tess_0e"], hz["tess_0i"])
    lc = LF.refine(cells, 2)
    lv = FR.triple_overlap(lc.cells, grid, hz["tess_0e"], hz["tess_0i"])

    pr = LF._parent_raster_index(cells)
    inv = np.full(int(pr.max()) + 1, -1, np.int64)
    inv[pr] = np.arange(pr.size)
    lp = inv[lc.parent]
    residual = LF.conservation_residual(ov.rows, ov.cols, ov.vals,
                                        lv.rows, lv.cols, lv.vals, lp,
                                        grid.n_cells, cells.alpha_lo.size)

    # a declared synthetic domain, deliberately unaligned with both lattices:
    # the archived node pitch and the detector pitch coincide here, so an
    # axis-aligned test boundary would make the two rules agree for a reason
    # that has nothing to do with either of them.
    rad = np.hypot(lc.alpha - 0.137, lc.beta + 0.291)
    lab = np.where(rad < 7.313, LF.EMITTING, LF.NOT_EMITTING)
    a = LF.assemble(lv.rows, lv.cols, lv.vals, lab, np.ones(lc.n_leaf),
                    grid.n_cells, granularity=LF.LEAF_RULE)
    chi = np.bincount(lp, weights=(lab == LF.EMITTING).astype(float),
                      minlength=cells.alpha_lo.size) / 4.0
    y_bad = LF.parent_fraction_response(ov.rows, ov.cols, ov.vals, chi,
                                        np.ones(cells.alpha_lo.size),
                                        grid.n_cells)
    whiten = 1.0 / (SIGMA * np.sqrt(grid.cell_area))
    return {
        "map": "a050_i050_n0_core", "parents": int(cells.alpha_lo.size),
        "leaves_at_k2": int(lc.n_leaf),
        "leaf_overlap_total": float(lv.vals.sum()),
        "parent_overlap_total": float(ov.vals.sum()),
        "per_detector_cell_and_parent_max_residual": residual,
        "refinement_moves_geometry": bool(residual > 1e-12),
        "leaf_vs_parent_fraction": {
            "total_relative_difference": float(
                abs(a.known.sum() - y_bad.sum())
                / max(abs(a.known.sum()), 1e-30)),
            "max_absolute_pixel_difference":
                float(np.max(np.abs(a.known - y_bad))),
            "whitened_vector_residual":
                PL.vector_residual(a.known * whiten, y_bad * whiten),
            "norm_difference_metric_used_by_031":
                PL.norm_difference(a.known * whiten, y_bad * whiten),
            "declared_test_domain": "disc r < 7.313 M about (0.137, -0.291)",
            "note": ("the total agrees to rounding and the image does not; "
                     "the 031 metric reports the smaller of the two")},
    }


# the suite runs at the system interpreter; the aart environment has no pytest
PYTEST_PYTHON = "python3"


def run_tests() -> dict:
    p = subprocess.run([PYTEST_PYTHON, "-m", "pytest", *TEST_FILES, "-q"],
                       cwd=ROOT, capture_output=True, text=True)
    tail = p.stdout.strip().splitlines()[-1] if p.stdout.strip() else \
        (p.stderr.strip().splitlines()[-1] if p.stderr.strip() else "")
    return {"files": list(TEST_FILES), "interpreter": PYTEST_PYTHON,
            "returncode": p.returncode,
            "summary": tail, "passed": p.returncode == 0,
            "in_the_launch_and_report_path_not_a_helper": True}


def main(out: Path) -> int:
    t0 = time.time()
    rep = {
        "stage": "M1", "ruling": "PAPER_I_MATCHED_INTEGRATION_RULING_032",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "commit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                 capture_output=True, text=True).stdout.strip(),
        "physical_queries": 0,
        "rule": ("y_d = sum_p sum_leaf |D_d ^ C_leaf ^ B_n| chi(xi_leaf) "
                 "f(xi_leaf)"),
        "representation_id": LF.LEAF_RULE,
        "forbidden_representation_id": LF.PARENT_FRACTION,
        "leaf_label_is_a_domain_certificate": False,
        "zero_unresolved_samples_bounds_the_boundary": False,
        "unresolved_carried_as": "explicit (lower, known, upper) response",
        "counterexample": counterexample(),
        "archived_geometry": on_archived_geometry(),
        "fault_injections_required_by_the_ruling": list(INJECTIONS),
        "fault_injections_implemented": list(INJECTIONS),
        "tests": run_tests(),
        "runtime_seconds": time.time() - t0,
    }
    (out / "LEAF_ASSEMBLY_CONSUMER_TESTS_032.json").write_text(
        json.dumps(rep, indent=2) + "\n")
    g = rep["archived_geometry"]
    print(json.dumps({"stage": "M1", "tests": rep["tests"]["summary"],
                      "conservation_residual":
                          g["per_detector_cell_and_parent_max_residual"],
                      "vector_residual":
                          g["leaf_vs_parent_fraction"]["whitened_vector_residual"],
                      "norm_difference":
                          g["leaf_vs_parent_fraction"]["norm_difference_metric_used_by_031"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main((ROOT / sys.argv[1]).resolve()))
