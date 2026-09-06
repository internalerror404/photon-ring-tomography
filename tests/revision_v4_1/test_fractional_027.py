"""Fractional-coverage canaries, ruling 027 phase H0.

Geometry and units only. No target spectrum, no operational count, no
estimator, and no transfer ray is traced anywhere in this file.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from phrt.revision_v4_1 import acquisition as ACQ            # noqa: E402
from phrt.revision_v4_1 import fractional as FR              # noqa: E402
from phrt.revision_v4_1 import measure as M                  # noqa: E402
from phrt.revision_v4_1 import polyclip as PC                # noqa: E402
from phrt.revision_v4_1.common_sky import DetectorGrid       # noqa: E402

EXACT = 1e-12


def rect(x0, x1, y0, y1):
    return np.array([[x0, y0], [x1, y0], [x1, y1], [x0, y1]], float)


def grid2(xa, xb):
    return np.repeat(xa, xb.size), np.tile(xb, xa.size)


# ---- F1: the substitution the ruling forbids is detectably different -----
def test_F1_whole_cell_fraction_times_uncut_overlap_is_not_the_overlap():
    """The reviewer's counterexample, reproduced as a standing canary.

    One unit cell emits only in its leftmost fifth and straddles two
    half-width detector pixels. The clipped overlap puts (0.2, 0) on the
    detector columns. Scaling the uncut overlaps by the whole-cell emitting
    fraction puts (0.1, 0.1): the same total, the wrong image. A canary that
    checked only the total would pass on the wrong construction, which is
    exactly the point.
    """
    x = np.array([0.5, 1.5])
    a, b = grid2(x, x)
    cells = M.build_ray_cells(a, b, M.CENTER_CELL_EXTENDED)   # unit cells
    assert np.allclose(cells.area, 1.0, rtol=EXACT)
    g = DetectorGrid(0.0, 2.0, 0.0, 2.0, 0.5)                 # half-width
    one = rect(0.0, 0.2, 0.0, 1.0)                            # leftmost fifth
    ov = FR.triple_overlap(cells, g, one, None)

    p = int(np.argmax(ov.active_area))
    assert float(ov.active_area[p]) == pytest.approx(0.2, rel=1e-12)
    assert float(ov.cut_fraction[p]) == pytest.approx(0.2, rel=1e-12)

    def by_column(vec):
        return vec.reshape(g.n_beta, g.n_alpha).sum(0)[:2]

    m = ov.cols == p
    got = np.bincount(ov.rows[m], weights=ov.vals[m], minlength=g.n_cells)
    assert np.allclose(by_column(got), [0.2, 0.0], rtol=1e-12, atol=1e-14)

    # the forbidden substitution, computed only to show that it differs
    O_uncut, _ = ACQ.overlap_operator(cells, g, np.ones(a.size, bool))
    sub = np.asarray(O_uncut[:, p].todense()).ravel() * ov.cut_fraction[p]
    assert np.allclose(by_column(sub), [0.1, 0.1], rtol=1e-12, atol=1e-14)
    assert float(sub.sum()) == pytest.approx(float(got.sum()), rel=1e-12), (
        "the totals agree, which is why a total cannot detect this")
    assert not np.allclose(sub, got), "and the images must differ"


# ---- F2: conservation ----------------------------------------------------
def test_F2_clipped_overlap_conserves_the_band_area():
    x = np.linspace(-2.0, 2.0, 9)
    a, b = grid2(x, x)
    cells = M.build_ray_cells(a, b, M.NODAL_DUAL_CLIPPED)
    g = DetectorGrid(-2.0, 2.0, -2.0, 2.0, 0.35)
    outer = PC.grid_coverage  # noqa: F841  (kept for symmetry of reading)
    o = np.stack([1.7 * np.cos(t := 2 * np.pi * np.arange(97) / 97),
                  1.7 * np.sin(t)], axis=1)
    i = 0.6 * o
    ov = FR.triple_overlap(cells, g, o, i)
    want = abs(PC.signed_area(o)) - abs(PC.signed_area(i))
    assert float(ov.vals.sum()) == pytest.approx(want, rel=1e-11)
    assert float(ov.active_area.sum()) == pytest.approx(want, rel=1e-11)
    assert (ov.active_area <= cells.area * (1 + 1e-12)).all(), (
        "a fragment cannot exceed its own cell")


# ---- F3: the hole survives ----------------------------------------------
def test_F3_the_band_hole_is_not_filled_in():
    x = np.linspace(-2.0, 2.0, 33)
    a, b = grid2(x, x)
    cells = M.build_ray_cells(a, b, M.NODAL_DUAL_CLIPPED)
    g = DetectorGrid(-2.0, 2.0, -2.0, 2.0, 0.4)
    t = 2 * np.pi * np.arange(200) / 200
    o = np.stack([1.8 * np.cos(t), 1.8 * np.sin(t)], axis=1)
    i = np.stack([1.2 * np.cos(t), 1.2 * np.sin(t)], axis=1)
    ov = FR.triple_overlap(cells, g, o, i)
    r = np.hypot(a, b)
    assert float(ov.active_area[r < 1.0].sum()) == pytest.approx(0.0,
                                                                 abs=1e-12)
    assert float(ov.active_area[(r > 1.3) & (r < 1.7)].sum()) > 0


# ---- F4: slivers are kept -----------------------------------------------
def test_F4_partial_fragments_are_kept_not_rounded_away():
    x = np.linspace(-1.0, 1.0, 21)
    a, b = grid2(x, x)
    cells = M.build_ray_cells(a, b, M.NODAL_DUAL_CLIPPED)
    g = DetectorGrid(-1.0, 1.0, -1.0, 1.0, 0.25)
    o = rect(-0.503, 0.497, -0.501, 0.499)     # deliberately off-lattice
    ov = FR.triple_overlap(cells, g, o, None)
    part = (ov.cut_fraction > 1e-15) & (ov.cut_fraction < 1 - 1e-12)
    assert part.sum() > 0, "an off-lattice rectangle must cut some cells"
    assert float(ov.active_area.sum()) == pytest.approx(1.0 * 1.0, rel=1e-11)
    assert (ov.active_area[part] > 0).all()


# ---- F5: permutation invariance -----------------------------------------
def test_F5_hull_vertex_rotation_does_not_change_the_operator():
    x = np.linspace(-1.5, 1.5, 13)
    a, b = grid2(x, x)
    cells = M.build_ray_cells(a, b, M.NODAL_DUAL_CLIPPED)
    g = DetectorGrid(-1.5, 1.5, -1.5, 1.5, 0.3)
    t = 2 * np.pi * np.arange(41) / 41
    o = np.stack([1.1 * np.cos(t), 1.1 * np.sin(t)], axis=1)
    base = FR.triple_overlap(cells, g, o, None)
    for k in (1, 13, 40):
        r = FR.triple_overlap(cells, g, np.roll(o, k, axis=0), None)
        assert np.allclose(np.sort(r.active_area), np.sort(base.active_area),
                           rtol=1e-12, atol=1e-14)
        assert np.allclose(r.active_area, base.active_area, rtol=1e-12,
                           atol=1e-14)


# ---- F6: units survive the fractional parent ----------------------------
def test_F6_active_area_is_the_parent_area_for_inherited_noise():
    """`a_p` is the ACTIVE fragment area, and L = O diag(a)^-1 still holds."""
    x = np.linspace(-1.0, 1.0, 9)
    a, b = grid2(x, x)
    cells = M.build_ray_cells(a, b, M.NODAL_DUAL_CLIPPED)
    g = DetectorGrid(-1.0, 1.0, -1.0, 1.0, 0.3)
    t = 2 * np.pi * np.arange(60) / 60
    o = np.stack([0.83 * np.cos(t), 0.83 * np.sin(t)], axis=1)
    ov = FR.triple_overlap(cells, g, o, None)
    act = ov.active_area
    live = act > 0
    from scipy import sparse
    O = sparse.csr_matrix((ov.vals, (ov.rows, ov.cols)),
                          shape=(g.n_cells, act.size))[:, live]
    ap = act[live]
    rng = np.random.default_rng(5)
    f = rng.normal(size=(int(live.sum()), 2))            # brightness
    z = f * ap[:, None]                                  # integrated flux
    L = ACQ.postprocessing_matrix(O, ap)
    assert np.allclose(np.asarray(O @ f), np.asarray(L @ z), rtol=1e-12)
    C = ACQ.inherited_covariance(O, ap, 0.21)
    assert np.allclose(C, C.T, rtol=1e-12)
    assert np.linalg.eigvalsh(C).min() > -1e-12 * max(np.abs(C).max(), 1.0)
    with pytest.raises(ACQ.AcquisitionError, match="zero area"):
        ACQ.postprocessing_matrix(O, np.where(ap == ap.min(), 0.0, ap))


# ---- F7: detector noise does not shrink with the emitting fraction ------
def test_F7_detector_variance_is_the_whole_cell_however_little_emits():
    g = DetectorGrid(-1.0, 1.0, -1.0, 1.0, 0.5)
    C = ACQ.detector_covariance(g, 0.3, 2)
    assert np.allclose(C, 0.09 * g.cell_area, rtol=EXACT)
    assert C.size == 2 * g.n_cells, "one variance per cell per observer time"


# ---- F8: every active fragment is classified ----------------------------
def test_F8_support_classification_is_total_and_never_assumes_zero():
    n = 6
    act = np.array([1.0, 1.0, 1.0, 1.0, 0.0, 0.0])
    band = np.array([True, True, True, False, True, False])
    valid = np.array([True, False, False, False, False, False])
    r = np.array([10.0, 10.0, 99.0, 10.0, 10.0, 10.0])
    fin = np.array([True, False, True, True, True, True])
    lab, tally = FR.classify_support(act, band, valid, r, fin, 1.87, 50.0)
    assert lab[0] == FR.SUPPORTED
    assert lab[1] == FR.SOLVER_UNRESOLVED
    assert lab[2] == FR.OUTSIDE_ANNULUS
    assert lab[3] == FR.NO_BAND_DATA
    assert tally["zero_emission_assumed_anywhere"] is False
    assert sum(v["fragments"] for v in tally["by_category"].values()) == 4
    assert tally["total_active_area"] == pytest.approx(4.0, rel=EXACT)
    with pytest.raises(PC.PolygonError, match="could not be classified"):
        FR.classify_support(act, band, valid, np.array([np.nan] * n), band,
                            1.87, 50.0)


# ---- F9: a non-nested hull pair is refused -------------------------------
def test_F9_inner_hull_outside_outer_is_refused():
    x = np.linspace(-2.0, 2.0, 9)
    a, b = grid2(x, x)
    cells = M.build_ray_cells(a, b, M.NODAL_DUAL_CLIPPED)
    g = DetectorGrid(-2.0, 2.0, -2.0, 2.0, 0.5)
    outer = rect(-0.5, 0.5, -0.5, 0.5)
    inner = rect(0.9, 1.9, 0.9, 1.9)          # disjoint, not a hole
    with pytest.raises(PC.PolygonError, match="negative band coverage"):
        FR.triple_overlap(cells, g, outer, inner)


# ---- F10: the aperture crops rather than absorbs -------------------------
def test_F10_flux_outside_the_aperture_is_reported_not_dropped():
    x = np.linspace(-2.0, 2.0, 17)
    a, b = grid2(x, x)
    cells = M.build_ray_cells(a, b, M.NODAL_DUAL_CLIPPED)
    g = DetectorGrid(-1.0, 1.0, -1.0, 1.0, 0.25)      # smaller than the cells
    o = rect(-1.6, 1.6, -1.6, 1.6)
    ov = FR.triple_overlap(cells, g, o, None)
    assert ov.accounting["band_area_outside"] > 0
    assert ov.accounting["captured_fraction"] == pytest.approx(
        4.0 / (3.2 ** 2), rel=1e-11)
    assert float(ov.vals.sum()) == pytest.approx(4.0, rel=1e-11)
