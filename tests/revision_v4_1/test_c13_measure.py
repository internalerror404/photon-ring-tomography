"""C13 measure and acquisition-unit canaries, ruling 026 phase Q1.

Correctness of a corrected construction. No target spectrum, no operational
count and no estimator appears in this file, and no detector parameter is
chosen by looking at a result.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest
from scipy import sparse

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from phrt.geometry.raymap import read                       # noqa: E402
from phrt.revision_v4_1 import acquisition as ACQ           # noqa: E402
from phrt.revision_v4_1 import measure as M                 # noqa: E402
from phrt.revision_v4_1.common_sky import DetectorGrid      # noqa: E402

MAPS = ROOT / "artifacts" / "raymaps"
EXACT = 1e-12


def _nodes(lo, hi, n):
    return np.linspace(lo, hi, n)


def _grid2(xa, xb):
    return np.repeat(xa, xb.size), np.tile(xb, xa.size)


def _map(n=0, profile="core", geometry="a050_i050"):
    p = MAPS / f"{geometry}_n{n}_{profile}.h5"
    if not p.exists():
        pytest.skip("ray maps not present in this tree")
    return read(p)


# ---- P1: the dual cells partition the declared domain -------------------
def test_P1_nodal_dual_cells_tile_the_declared_domain_exactly():
    """No gap and no overlap, and the total is the declared area.

    This is the property the stored nominal square does not have, and the
    reason the repair is a set of edges rather than a replacement scalar.
    """
    for n_nodes in (2, 3, 8, 126, 250):
        x = _nodes(-7.0, 7.0, n_nodes)
        a, b = _grid2(x, x)
        cells = M.build_ray_cells(a, b, M.NODAL_DUAL_CLIPPED)
        assert cells.tiles_exactly()
        assert float(cells.area.sum()) == pytest.approx(14.0 ** 2, rel=EXACT)
        lo = np.sort(np.unique(cells.alpha_lo))
        hi = np.sort(np.unique(cells.alpha_hi))
        assert lo[0] == pytest.approx(-7.0, abs=EXACT)
        assert hi[-1] == pytest.approx(7.0, abs=EXACT)
        assert np.allclose(lo[1:], hi[:-1], atol=EXACT), "cells must abut"


# ---- P2: endpoint semantics give half-width boundary cells --------------
def test_P2_endpoint_inclusive_nodes_get_half_and_quarter_cells():
    x = _nodes(-1.0, 1.0, 5)              # spacing 0.5
    a, b = _grid2(x, x)
    cells = M.build_ray_cells(a, b, M.NODAL_DUAL_CLIPPED)
    area = cells.area.reshape(5, 5)
    assert area[2, 2] == pytest.approx(0.25, rel=EXACT)          # interior
    assert area[0, 2] == pytest.approx(0.125, rel=EXACT)         # edge
    assert area[0, 0] == pytest.approx(0.0625, rel=EXACT)        # corner
    assert np.unique(np.round(area, 12)).size == 3
    ext = M.build_ray_cells(a, b, M.CENTER_CELL_EXTENDED)
    assert np.unique(np.round(ext.area, 12)).size == 1
    assert float(ext.area.sum()) == pytest.approx(2.5 ** 2, rel=EXACT), (
        "a full cell for every node integrates a domain larger than the one "
        "the generator declared, and that has to be visible")


# ---- P3: the two axes are described separately --------------------------
def test_P3_rectangular_grid_is_not_reduced_to_one_spacing():
    """A single `delta` would be silently wrong on one axis."""
    xa, xb = _nodes(-2.0, 2.0, 5), _nodes(-1.0, 1.0, 3)   # 1.0 and 1.0? no: 1.0, 1.0
    xa, xb = _nodes(-2.0, 2.0, 5), _nodes(-3.0, 3.0, 4)   # 1.0 and 2.0
    a, b = _grid2(xa, xb)
    cells = M.build_ray_cells(a, b, M.NODAL_DUAL_CLIPPED)
    assert cells.axis_alpha.spacing == pytest.approx(1.0, rel=EXACT)
    assert cells.axis_beta.spacing == pytest.approx(2.0, rel=EXACT)
    assert cells.tiles_exactly()
    assert float(cells.area.sum()) == pytest.approx(4.0 * 6.0, rel=EXACT)
    interior = (cells.alpha_hi - cells.alpha_lo) * (cells.beta_hi - cells.beta_lo)
    assert interior.max() == pytest.approx(2.0, rel=EXACT), (
        "the largest cell is delta_alpha * delta_beta, not either squared")


# ---- P4: a non-uniform axis is refused, not averaged --------------------
def test_P4_non_uniform_axis_is_refused():
    x = np.array([-1.0, -0.4, 0.3, 1.0])
    a, b = _grid2(x, x)
    with pytest.raises(M.MeasureError, match="not uniform"):
        M.build_ray_cells(a, b, M.NODAL_DUAL_CLIPPED)


# ---- P5: the invalid mask removes area, it does not redistribute it -----
def test_P5_invalid_rays_are_dropped_not_smeared():
    x = _nodes(-1.0, 1.0, 5)
    a, b = _grid2(x, x)
    cells = M.build_ray_cells(a, b, M.NODAL_DUAL_CLIPPED)
    valid = np.ones(a.size, bool)
    valid[12] = False                                   # the centre cell
    g = DetectorGrid(-1.0, 1.0, -1.0, 1.0, 0.5)
    f = np.ones((a.size, 1))
    y_all = ACQ.detector_response(cells, g, np.ones(a.size, bool), f)
    y_hole = ACQ.detector_response(cells, g, valid, f)
    assert float(y_all.sum()) == pytest.approx(4.0, rel=EXACT)
    assert float(y_all.sum() - y_hole.sum()) == pytest.approx(0.25, rel=EXACT)
    assert (y_hole <= y_all + EXACT).all(), "masking must not add flux anywhere"


# ---- P6: representation invariance at a fixed detector ------------------
def test_P6_subdividing_cells_carrying_the_same_field_changes_nothing():
    """The identity the old detector-pitch test was reaching for.

    Keep the detector, the field, the noise and the aperture fixed and merely
    subdivide the integration cells, each child carrying its parent's value.
    Nothing measurable may move. This is a statement about the representation,
    not a claim that two different detectors agree -- which is precisely the
    conflation that made a 1e-12 detector-pitch criterion unreachable.

    The children must genuinely partition their parents. A finer nodal-dual
    mesh does not: its cell walls fall between the coarse ones, so it is a
    different representation of a different field, and an earlier version of
    this canary was wrong to use one.
    """
    g = DetectorGrid(-1.0, 1.0, -1.0, 1.0, 0.3)          # deliberately unaligned
    x = _nodes(-1.0, 1.0, 5)
    a, b = _grid2(x, x)
    parent = M.build_ray_cells(a, b, M.NODAL_DUAL_CLIPPED)
    rng = np.random.default_rng(3)
    f = rng.normal(size=(a.size, 3))
    valid = np.ones(a.size, bool)
    valid[7] = valid[18] = False          # holes must survive refinement too
    y_parent = ACQ.detector_response(parent, g, valid, f)
    assert np.abs(y_parent).max() > 0
    for k in (2, 3, 5, 8):
        child, who = M.subdivide(parent, k)
        assert np.allclose(np.bincount(who, child.area), parent.area,
                           rtol=EXACT), "children must partition their parent"
        y_child = ACQ.detector_response(child, g, valid[who], f[who])
        rel = np.abs(y_child - y_parent).max() / np.abs(y_parent).max()
        assert rel < EXACT, f"subdivision at k={k} moved the response by {rel:.3e}"


def test_P6b_subdivision_invariance_holds_on_a_real_order():
    """The same identity on an archived map, not only a hand fixture."""
    rm = _map(2, "core")
    a, b, v = rm.alpha, rm.beta, rm.valid
    keep = np.flatnonzero(v)[:400]
    sel = np.zeros(a.size, bool)
    sel[keep] = True
    cells = M.build_ray_cells(a, b, M.NODAL_DUAL_CLIPPED)
    g = DetectorGrid(-25.0, 25.0, -25.0, 25.0, 0.4)
    f = np.stack([np.ones(a.size), np.abs(rm.redshift) ** 3], axis=1)
    y0 = ACQ.detector_response(cells, g, sel, f)
    child, who = M.subdivide(cells, 4)
    y1 = ACQ.detector_response(child, g, sel[who], f[who])
    rel = np.abs(y1 - y0).max() / np.abs(y0).max()
    assert rel < EXACT, f"real-order subdivision moved the response by {rel:.3e}"


# ---- P7: brightness and integrated-flux parents agree -------------------
def test_P7_brightness_and_flux_representations_agree_on_unequal_areas():
    """`O` is not `L`. On unequal-area cells the difference is not a scale.

    The fixture is deliberately built on clipped dual cells, whose areas
    differ by a factor of four between corner and interior, so an
    implementation that used `O` where `L` belongs cannot pass by accident.
    """
    x = _nodes(-1.0, 1.0, 5)
    a, b = _grid2(x, x)
    cells = M.build_ray_cells(a, b, M.NODAL_DUAL_CLIPPED)
    area = cells.area
    assert area.max() / area.min() == pytest.approx(4.0, rel=EXACT)
    g = DetectorGrid(-1.0, 1.0, -1.0, 1.0, 0.4)
    valid = np.ones(a.size, bool)
    rng = np.random.default_rng(11)
    f = rng.normal(size=(a.size, 3))                       # brightness
    z = f * area[:, None]                                  # integrated flux
    y_b = ACQ.detector_response(cells, g, valid, f, ACQ.BRIGHTNESS_PARENT)
    y_z = ACQ.detector_response(cells, g, valid, z, ACQ.INTEGRATED_FLUX_PARENT)
    assert np.allclose(y_b, y_z, rtol=EXACT, atol=EXACT)
    O, _ = ACQ.overlap_operator(cells, g, valid)
    L = ACQ.postprocessing_matrix(O, area)
    assert np.allclose(np.asarray((O @ f)), y_b, rtol=EXACT, atol=EXACT)
    assert np.allclose(np.asarray((L @ z)), y_z, rtol=EXACT, atol=EXACT)
    assert not np.allclose(np.asarray((O @ z)), y_z), (
        "using O where L belongs must be detectable on unequal areas")


# ---- P8: the inherited covariance is the one the units imply ------------
def test_P8_inherited_covariance_matches_its_definition():
    x = _nodes(-1.0, 1.0, 5)
    a, b = _grid2(x, x)
    cells = M.build_ray_cells(a, b, M.NODAL_DUAL_CLIPPED)
    area = cells.area
    g = DetectorGrid(-1.0, 1.0, -1.0, 1.0, 0.4)
    valid = np.ones(a.size, bool)
    O, _ = ACQ.overlap_operator(cells, g, valid)
    sigma = 0.37
    C = ACQ.inherited_covariance(O, area, sigma)
    want = sigma ** 2 * np.asarray(
        (O @ sparse.diags(1.0 / area) @ O.T).todense())
    assert np.allclose(C, want, rtol=EXACT, atol=EXACT)
    assert np.allclose(C, C.T, rtol=EXACT, atol=EXACT)
    w = np.linalg.eigvalsh(C)
    assert w.min() > -EXACT * max(w.max(), 1.0), "inherited noise must be PSD"
    # the detector experiment is a different covariance and must not coincide
    D = np.diag(ACQ.detector_covariance(g, sigma, 1))
    assert not np.allclose(C, D), (
        "the inherited and single-sky covariances are different experiments")


# ---- P9: detector noise is assigned once, after the sum -----------------
def test_P9_detector_noise_is_assigned_once_after_the_order_sum():
    g = DetectorGrid(-1.0, 1.0, -1.0, 1.0, 0.5)
    one = ACQ.detector_covariance(g, 0.5, 1)
    assert one.size == g.n_cells
    assert np.allclose(one, 0.25 * g.cell_area, rtol=EXACT)
    three = ACQ.detector_covariance(g, 0.5, 3)
    assert three.size == 3 * g.n_cells
    assert np.allclose(three, one[0], rtol=EXACT), (
        "more observer times add rows, they do not raise the variance of a "
        "cell, and three image orders landing on one cell do not triple it")


# ---- P10: zero-area parents are refused rather than inverted ------------
def test_P10_zero_area_parent_is_refused():
    x = _nodes(-1.0, 1.0, 3)
    a, b = _grid2(x, x)
    cells = M.build_ray_cells(a, b, M.NODAL_DUAL_CLIPPED)
    g = DetectorGrid(-1.0, 1.0, -1.0, 1.0, 0.5)
    O, _ = ACQ.overlap_operator(cells, g, np.ones(a.size, bool))
    bad = cells.area.copy()
    bad[4] = 0.0
    with pytest.raises(ACQ.AcquisitionError, match="zero area"):
        ACQ.postprocessing_matrix(O, bad)


# ---- P11: the corrected measure is recorded beside the legacy one -------
def test_P11_legacy_and_corrected_measures_are_both_available_and_differ():
    """Neither convention is allowed to quietly stand in for the other."""
    rm = _map(1, "core")
    a, b, v = rm.alpha, rm.beta, rm.valid
    stored = float(np.unique(rm.pixel_area)[0])
    legacy = M.build_ray_cells(a, b, M.LEGACY_NOMINAL_SQUARE,
                               nominal_side=np.sqrt(stored))
    dual = M.build_ray_cells(a, b, M.NODAL_DUAL_CLIPPED)
    assert np.allclose(legacy.area, stored, rtol=EXACT)
    assert not dual.tiles_exactly() == legacy.tiles_exactly()
    assert dual.tiles_exactly()
    ratio = float(dual.area[v].sum()) / float(legacy.area[v].sum())
    assert abs(ratio - 1) > 1e-4, (
        "order 1 core is one of the maps C13 is about; if this no longer "
        "differs the archive has been changed and must be re-reviewed")


# ---- P12: the real map's cells still partition its declared screen ------
def test_P12_real_maps_partition_their_declared_screen():
    for n in (0, 1, 2):
        rm = _map(n, "core")
        cells = M.build_ray_cells(rm.alpha, rm.beta, M.NODAL_DUAL_CLIPPED)
        lims = float(np.unique(rm.alpha)[-1])
        assert cells.tiles_exactly(), f"order {n} cells do not tile"
        assert float(cells.area.sum()) == pytest.approx((2 * lims) ** 2,
                                                        rel=1e-12)
