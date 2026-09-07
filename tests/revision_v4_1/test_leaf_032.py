"""Leaf-correct assembly, ruling 032. No physical query is made here.

The geometry used by the production-path tests is archived: ray maps, the
qualified hull tessellation and the lensing-band masks are read from disk, and
nothing in this file traces a ray or evaluates a path integral.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from phrt.revision_v4_1 import fractional as FR                # noqa: E402
from phrt.revision_v4_1 import leaf as LF                      # noqa: E402
from phrt.revision_v4_1 import measure as M                    # noqa: E402
from phrt.revision_v4_1.common_sky import DetectorGrid         # noqa: E402

HULLS = ROOT / ("artifacts/revisions/mahakal_v4_1/G1C_20260907T075203Z_d252697"
                "/CLOSEOUT_ARRAYS_029.npz")
RAYMAP = ROOT / "artifacts/raymaps/a050_i050_n0_core.h5"


# ---- L1: the ruling's own counterexample, through the real kernel ----
def test_L1_parent_fraction_moves_flux_and_the_leaf_rule_does_not():
    """A unit cell emitting on its leftmost fifth owes (0.2, 0), not (0.1, 0.1)."""
    # one parent [0,1]x[0,1] straddling two half-width detector cells
    rows = np.array([0, 1])
    cols = np.array([0, 0])
    vals = np.array([0.5, 0.5])
    forbidden = LF.parent_fraction_response(rows, cols, vals, [0.2], [1.0], 2)
    assert np.allclose(forbidden.ravel(), [0.1, 0.1])

    # the same parent cut into ten leaves, each keeping its own detector overlap
    edges = np.linspace(0.0, 1.0, 11)
    mid = 0.5 * (edges[:-1] + edges[1:])
    lrows, lcols, lvals = [], [], []
    for i, (lo, hi) in enumerate(zip(edges[:-1], edges[1:])):
        for d, (dlo, dhi) in enumerate(((0.0, 0.5), (0.5, 1.0))):
            w = max(0.0, min(hi, dhi) - max(lo, dlo))
            if w > 0:
                lrows.append(d), lcols.append(i), lvals.append(w)
    label = np.where(mid < 0.2, LF.EMITTING, LF.NOT_EMITTING)
    a = LF.assemble(np.array(lrows), np.array(lcols), np.array(lvals),
                    label, np.ones(10), 2, granularity=LF.LEAF_RULE)
    assert a.known[1, 0] == 0.0, "the leaf rule must not light the right pixel"
    assert a.known[0, 0] == pytest.approx(0.2, abs=1e-12)
    assert forbidden.sum() == pytest.approx(a.known.sum())   # totals agree


# ---- L2: a leaf rule is still a quadrature, not an exact contour ----
def test_L2_leaf_midpoint_is_an_approximation_not_a_certificate():
    edges = np.linspace(0.0, 1.0, 17)
    mid = 0.5 * (edges[:-1] + edges[1:])
    w = np.diff(edges)
    got = float(np.sum(w[mid < 0.2]))
    assert abs(got - 0.2) > 1e-3, "refinement changes the answer; it does not certify it"


# ---- L3: granularity mismatch is refused, not averaged ----
def test_L3_parent_labels_against_leaf_overlaps_are_refused():
    with pytest.raises(LF.LeafError, match="granularity"):
        LF.assemble(np.array([0]), np.array([5]), np.array([1.0]),
                    np.array([LF.EMITTING]), np.ones(1), 1,
                    granularity=LF.LEAF_RULE)


def test_L3b_the_named_forbidden_rule_is_refused_by_name():
    with pytest.raises(LF.LeafError, match=LF.PARENT_FRACTION):
        LF.assemble(np.array([0]), np.array([0]), np.array([1.0]),
                    np.array([LF.EMITTING]), np.ones(1), 1,
                    granularity=LF.PARENT_FRACTION)


# ---- L4: unresolved is an interval, not a number ----
def test_L4_unresolved_leaves_are_carried_as_a_bound():
    rows = np.array([0, 0])
    cols = np.array([0, 1])
    vals = np.array([0.3, 0.7])
    label = np.array([LF.EMITTING, LF.UNRESOLVED])
    a = LF.assemble(rows, cols, vals, label, np.ones(2), 1,
                    granularity=LF.LEAF_RULE)
    assert a.lower[0, 0] == pytest.approx(0.3)
    assert a.upper[0, 0] == pytest.approx(1.0)
    assert a.partial() is True
    assert a.unresolved_mass[0, 0] == pytest.approx(0.7)


def test_L4b_zero_unresolved_samples_do_not_certify_the_boundary():
    """Four finite labels inside a cell say nothing about what lies between."""
    labels = np.array([LF.NOT_EMITTING] * 4)
    assert np.count_nonzero(labels == LF.UNRESOLVED) == 0
    # a component of width 0.05 fits inside a 0.4 M cell between four samples
    assert 0.05 < 0.4 / 2


# ---- L5: every count must be present ----
def test_L5_a_missing_count_is_an_error():
    a = LF.assemble(np.array([0]), np.array([0]), np.array([1.0]),
                    np.array([LF.EMITTING]), np.ones(1), 1,
                    granularity=LF.LEAF_RULE)
    with pytest.raises(LF.LeafError, match="NOT_EVALUATED"):
        LF.bind(a, {"found": 1, "eligible": 1, "selected": 1}, {})
    LF.bind(a, dict.fromkeys(LF.COUNT_FIELDS, 0), {})


# ---- L6: a missing transfer value is not zero emission ----
def test_L6_non_finite_field_is_refused():
    with pytest.raises(LF.LeafError, match="not zero emission"):
        LF.assemble(np.array([0]), np.array([0]), np.array([1.0]),
                    np.array([LF.EMITTING]), np.array([np.nan]), 1,
                    granularity=LF.LEAF_RULE)


# ---- L7: refinement partitions the parent exactly, on synthetic axes ----
def test_L7_refine_tiles_the_parent_and_maps_children_to_parents():
    a = np.linspace(-1.0, 1.0, 5)
    cells = M.build_ray_cells(np.repeat(a, 5), np.tile(a, 5),
                              M.NODAL_DUAL_CLIPPED)
    for k in (1, 2, 3):
        lc = LF.refine(cells, k)
        assert lc.n_leaf == cells.alpha_lo.size * k * k
        assert float(lc.cells.area.sum()) == pytest.approx(
            float(cells.area.sum()), rel=1e-14)
        # every parent receives exactly k*k leaves
        assert np.all(np.bincount(lc.parent) == k * k)
        # and each leaf lies inside the parent it names
        pr = LF._parent_raster_index(cells)
        inv = np.empty(pr.max() + 1, np.int64)
        inv[pr] = np.arange(pr.size)
        p = inv[lc.parent]
        assert np.all(lc.alpha >= cells.alpha_lo[p] - 1e-12)
        assert np.all(lc.alpha <= cells.alpha_hi[p] + 1e-12)
        assert np.all(lc.beta >= cells.beta_lo[p] - 1e-12)
        assert np.all(lc.beta <= cells.beta_hi[p] + 1e-12)


# ---- L8: production path. Real band, real map, per-row conservation ----
@pytest.mark.skipif(not (HULLS.is_file() and RAYMAP.is_file()),
                    reason="archived geometry not present")
def test_L8_leaf_overlaps_sum_to_the_parent_overlap_per_detector_cell():
    """Refining the integration must not move geometry, row by row.

    This runs the production kernel on the archived order-0 core band, not a
    helper: a total-only agreement is exactly what the forbidden substitution
    also satisfies, so the residual is taken per (detector cell, parent).
    """
    import h5py
    from phrt.geometry.raymap import read

    rm = read(RAYMAP)
    grid = DetectorGrid(-25.0, 25.0, -25.0, 25.0, 0.4)
    hz = np.load(HULLS)
    outer, inner = hz["tess_0e"], hz["tess_0i"]
    cells = M.build_ray_cells(rm.alpha, rm.beta, M.NODAL_DUAL_CLIPPED)
    parent = FR.triple_overlap(cells, grid, outer, inner)

    lc = LF.refine(cells, 2)
    leaves = FR.triple_overlap(lc.cells, grid, outer, inner)
    assert float(leaves.vals.sum()) == pytest.approx(float(parent.vals.sum()),
                                                     rel=1e-12)
    pr = LF._parent_raster_index(cells)
    inv = np.full(int(pr.max()) + 1, -1, np.int64)
    inv[pr] = np.arange(pr.size)
    leaf_parent = inv[lc.parent]
    assert leaf_parent.min() >= 0
    res = LF.conservation_residual(
        parent.rows, parent.cols, parent.vals,
        leaves.rows, leaves.cols, leaves.vals, leaf_parent,
        grid.n_cells, cells.alpha_lo.size)
    assert res < 1e-12, f"leaf overlaps do not tile their parent: {res:.3e}"


@pytest.mark.skipif(not (HULLS.is_file() and RAYMAP.is_file()),
                    reason="archived geometry not present")
def test_L9_on_real_geometry_the_two_rules_differ_where_the_domain_is_cut():
    """The two assemblies agree in total and disagree per pixel."""
    import h5py
    from phrt.geometry.raymap import read

    rm = read(RAYMAP)
    grid = DetectorGrid(-25.0, 25.0, -25.0, 25.0, 0.4)
    hz = np.load(HULLS)
    cells = M.build_ray_cells(rm.alpha, rm.beta, M.NODAL_DUAL_CLIPPED)
    ov = FR.triple_overlap(cells, grid, hz["tess_0e"], hz["tess_0i"])
    lc = LF.refine(cells, 2)
    lv = FR.triple_overlap(lc.cells, grid, hz["tess_0e"], hz["tess_0i"])

    # A synthetic emitting disc, deliberately not aligned with either grid:
    # the archived node lattice and the detector lattice share a pitch here,
    # so an axis-aligned boundary would fall on cell edges and the two rules
    # would agree for a reason that has nothing to do with either of them.
    rad = np.hypot(lc.alpha - 0.137, lc.beta + 0.291)
    lab_leaf = np.where(rad < 7.313, LF.EMITTING, LF.NOT_EMITTING)
    a = LF.assemble(lv.rows, lv.cols, lv.vals, lab_leaf, np.ones(lc.n_leaf),
                    grid.n_cells, granularity=LF.LEAF_RULE)

    pr = LF._parent_raster_index(cells)
    inv = np.full(int(pr.max()) + 1, -1, np.int64)
    inv[pr] = np.arange(pr.size)
    lp = inv[lc.parent]
    num = np.bincount(lp, weights=(lab_leaf == LF.EMITTING).astype(float),
                      minlength=cells.alpha_lo.size)
    chi = num / 4.0
    y_bad = LF.parent_fraction_response(ov.rows, ov.cols, ov.vals, chi,
                                        np.ones(cells.alpha_lo.size),
                                        grid.n_cells)
    assert float(np.max(np.abs(a.known - y_bad))) > 1e-6, \
        "the two rules must differ somewhere on a cut band"
