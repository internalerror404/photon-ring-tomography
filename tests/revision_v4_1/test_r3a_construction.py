"""R3A construction canaries.

Correctness of a construction, not a result. No target spectrum is computed
anywhere in this file, and no detector parameter is chosen by looking at one.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest
from scipy import sparse

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from phrt.geometry.raymap import read  # noqa: E402
from phrt.revision_v4_1 import covariance  # noqa: E402
from phrt.revision_v4_1.common_sky import (DetectorGrid,  # noqa: E402
                                           detector_noise_covariance,
                                           overlap_matrix, overlap_triplets)

MAPS = ROOT / "artifacts" / "raymaps"
GEOMETRY = "a050_i050"
RTOL = 1e-10


def _maps():
    if not (MAPS / f"{GEOMETRY}_n0_core.h5").exists():
        pytest.skip("ray maps not present in this tree")
    return [read(MAPS / f"{GEOMETRY}_n{n}_core.h5") for n in (0, 1, 2)]


def _grid(pitch=0.4):
    return DetectorGrid(-25.0, 25.0, -25.0, 25.0, pitch)


# ---- 1: coordinates, not counts ----------------------------------------
def test_C1_registration_uses_screen_coordinates_not_counts():
    """Two orders with equal ray counts but different screens must differ."""
    g = _grid(0.5)
    n = 64
    rng = np.random.default_rng(0)
    a1, b1 = rng.uniform(-5, 5, n), rng.uniform(-5, 5, n)
    a2, b2 = a1 + 7.0, b1 - 3.0            # same count, elsewhere on the sky
    v = np.ones(n, bool)
    L1, _ = overlap_matrix(a1, b1, 0.25, g, v)
    L2, _ = overlap_matrix(a2, b2, 0.25, g, v)
    assert L1.shape == L2.shape
    assert (L1 - L2).nnz > 0, "equal counts produced an identical mapping"


# ---- 2: permutation invariance -----------------------------------------
def test_C2_independent_row_permutations_do_not_change_the_sky():
    g = _grid(0.5)
    rng = np.random.default_rng(1)
    n = 128
    a, b = rng.uniform(-6, 6, n), rng.uniform(-6, 6, n)
    v = np.ones(n, bool)
    x = rng.normal(size=n)
    L, _ = overlap_matrix(a, b, 0.25, g, v)
    base = L @ x
    for seed in range(5):
        p = np.random.default_rng(seed).permutation(n)
        Lp, _ = overlap_matrix(a[p], b[p], 0.25, g, v[p])
        assert np.allclose(Lp @ x[p], base, rtol=RTOL, atol=1e-12)


# ---- 3 and 4: flux conservation with boundary accounting ---------------
def test_C3_integrated_flux_is_conserved_up_to_what_leaves_the_field():
    g = _grid(0.5)
    rng = np.random.default_rng(2)
    n = 200
    a, b = rng.uniform(-4, 4, n), rng.uniform(-4, 4, n)
    v = np.ones(n, bool)
    cell = 0.25
    L, acc = overlap_matrix(a, b, cell, g, v)
    assert acc["captured_fraction"] == pytest.approx(1.0, rel=RTOL)
    x = np.full(n, 3.0)                    # constant surface brightness
    assert float((L @ x).sum()) == pytest.approx(3.0 * cell * n, rel=RTOL)

    # a cell straddling the edge loses exactly the area outside
    edge = DetectorGrid(0.0, 1.0, 0.0, 1.0, 0.5)
    Le, ae = overlap_matrix(np.array([0.0]), np.array([0.5]), 1.0,
                            edge, np.array([True]))
    # the ray cell spans alpha [-0.5, 0.5] and beta [0, 1]; the field is
    # [0, 1] x [0, 1], so half of it lands and half leaves
    assert ae["area_outside_field_of_view"] == pytest.approx(0.5, rel=1e-12)
    assert ae["captured_fraction"] == pytest.approx(0.5, rel=1e-12)


def test_C4_single_sky_all_order_total_flux_is_the_sum_of_orders():
    g = _grid(0.5)
    rng = np.random.default_rng(3)
    tot_direct, tot_sky = 0.0, np.zeros(g.n_cells)
    for k, cell in enumerate((0.25, 0.09, 0.04)):
        n = 60 + 10 * k
        a, b = rng.uniform(-5, 5, n), rng.uniform(-5, 5, n)
        v = np.ones(n, bool)
        L, _ = overlap_matrix(a, b, cell, g, v)
        x = np.full(n, 2.0)
        tot_sky += L @ x
        tot_direct += 2.0 * cell * n
    assert float(tot_sky.sum()) == pytest.approx(tot_direct, rel=RTOL)


# ---- 5: refinement must not manufacture information --------------------
def test_C5_detector_refinement_converges_on_the_real_tiled_geometry():
    """At fixed noise density, refinement converges once it resolves the rays.

    The declared test fields are smooth in screen coordinates and the real
    order-0 map tiles its own grid without overlap, so once the detector pitch
    reaches the ray cell scale there is nothing left to resolve and the
    whitened information stops moving.

    An earlier version of this canary used randomly scattered synthetic cells.
    Those overlap, real adaptive maps do not, and the overlap alone made the
    information climb. The fixture was wrong, not the construction.
    """
    rm = _maps()[0]
    a, b, v = rm.alpha, rm.beta, rm.valid
    cell = float(np.unique(rm.pixel_area)[0])
    A = np.stack([np.ones(a.size), 0.01 * a, 0.01 * b], axis=1)
    seq = {}
    for pitch in (1.6, 0.8, 0.4, 0.2, 0.1):
        g = DetectorGrid(-25.2, 25.2, -25.2, 25.2, pitch)
        L, acc = overlap_matrix(a, b, cell, g, v)
        assert acc["captured_fraction"] == pytest.approx(1.0, rel=1e-12), (
            "the declared field of view must contain every valid ray cell")
        C = detector_noise_covariance(g, 1.0, 1)
        B = (L @ A) / np.sqrt(C)[:, None]
        seq[pitch] = float(np.sum(B ** 2))
    ray_scale = np.sqrt(cell)
    assert ray_scale == pytest.approx(0.4, rel=1e-9)
    below = [p_ for p_ in seq if p_ <= ray_scale]
    vals = [seq[p_] for p_ in sorted(below, reverse=True)]
    worst = max(abs(x / vals[0] - 1.0) for x in vals)
    assert worst < 1e-12, (
        f"information still moving below the ray scale: {seq}")
    assert seq[1.6] < seq[0.4], (
        "a detector coarser than the rays should lose information, and this "
        "fixture must actually exercise that or the plateau is vacuous")


def test_C5b_the_two_noise_models_are_not_interchangeable():
    """Recorded as a difference, not resolved into an ordering.

    Ruling 025: a positive-semidefinite comparison against the ideal stack
    cannot be assumed for a different detector-noise experiment. So this
    checks that the two covariances differ and asserts no inequality between
    them. The contraction claim belongs to the inherited-noise model alone and
    is tested in C7.
    """
    rng = np.random.default_rng(24)
    n = 80
    a, b = rng.uniform(-3, 3, n), rng.uniform(-3, 3, n)
    v = np.ones(n, bool)
    cell = 0.09
    g = DetectorGrid(-4.0, 4.0, -4.0, 4.0, 0.5)
    L, _ = overlap_matrix(a, b, cell, g, v)
    Ld = np.asarray(L.todense())
    C_parent = np.diag(np.full(n, cell))           # sigma = 1
    inherited = Ld @ C_parent @ Ld.T               # L C L^T
    detector = np.diag(detector_noise_covariance(g, 1.0, 1))
    assert inherited.shape == detector.shape
    diff = float(np.abs(inherited - detector).max())
    assert diff > 1e-6, (
        "the two noise models happened to coincide on this fixture, which "
        "would make the distinction untestable here")
    # deliberately no assertion about which carries more information


# ---- 6: forward and adjoint agree --------------------------------------
def test_C6_forward_and_adjoint_are_consistent():
    g = _grid(0.5)
    rng = np.random.default_rng(5)
    n = 150
    a, b = rng.uniform(-6, 6, n), rng.uniform(-6, 6, n)
    L, _ = overlap_matrix(a, b, 0.25, g, np.ones(n, bool))
    for _ in range(20):
        x, y = rng.normal(size=n), rng.normal(size=g.n_cells)
        assert float(y @ (L @ x)) == pytest.approx(
            float((L.T @ y) @ x), rel=RTOL, abs=1e-12)


# ---- 7: inherited postprocessing contracts -----------------------------
def test_C7_inherited_noise_postprocessing_contracts_information():
    """L A with L C L^T is a compression of the same parent experiment."""
    rng = np.random.default_rng(6)
    n, k = 40, 4
    A = rng.normal(size=(n, k))
    C = np.diag(rng.uniform(0.5, 2.0, n))
    F_parent = covariance.whiten(A, C)
    F0 = F_parent.B.T @ F_parent.B
    g = DetectorGrid(-2.0, 2.0, -2.0, 2.0, 1.0)
    a, b = rng.uniform(-1.9, 1.9, n), rng.uniform(-1.9, 1.9, n)
    L, _ = overlap_matrix(a, b, 0.04, g, np.ones(n, bool))
    Ld = np.asarray(L.todense())
    keep = np.asarray(np.abs(Ld).sum(axis=1)).ravel() > 0
    w = covariance.mixed_whiten(A, Ld[keep], C)
    F = w.B.T @ w.B
    gap = np.linalg.eigvalsh(F0 - F)
    assert gap.min() > -1e-9 * max(float(np.abs(F0).max()), 1.0), (
        f"the compression added information: {gap.min():.3e}")


def test_C7b_identity_mixing_is_an_exact_reexpression():
    rng = np.random.default_rng(7)
    A = rng.normal(size=(12, 3))
    C = np.diag(rng.uniform(0.5, 2.0, 12))
    a = covariance.whiten(A, C)
    b = covariance.mixed_whiten(A, np.eye(12), C)
    assert np.abs(a.B.T @ a.B - b.B.T @ b.B).max() < 1e-10


# ---- 8: detector noise is assigned once --------------------------------
def test_C8_detector_noise_is_added_once_not_once_per_order():
    g = DetectorGrid(-1.0, 1.0, -1.0, 1.0, 0.5)
    C = detector_noise_covariance(g, 1.0, 3)
    assert C.size == g.n_cells * 3
    assert np.allclose(C, g.cell_area), (
        "the per-cell variance must be the detector's, independent of how "
        "many image orders landed on it")
    # three orders summed onto one screen: the signal adds, the noise does not
    rng = np.random.default_rng(8)
    per_order = [rng.normal(size=g.n_cells) for _ in range(3)]
    summed = sum(per_order)
    stacked_noise = 3 * g.cell_area          # what noise-per-order would give
    once = float(detector_noise_covariance(g, 1.0, 1)[0])
    assert once == pytest.approx(g.cell_area, rel=1e-12)
    assert once < stacked_noise, (
        "assigning noise per image order would inflate the variance by the "
        "number of orders")
    assert summed.shape == (g.n_cells,)


# ---- 9: one time origin across orders ----------------------------------
def test_C9_no_cross_order_time_reference_drift():
    """One geometry-wide time origin, verified rather than assumed.

    The archive's convention is that ``coordinate_time + delay`` is a single
    constant across every ray of every order -- delay is measured back from
    the latest arrival in the geometry, which is order 0's. My first version of
    this canary assumed ``coordinate_time - delay`` was constant and was wrong
    about the sign; the check below is the invariant the data actually holds,
    and it is exactly what a shared origin means.
    """
    maps = _maps()
    origins = []
    for rm in maps:
        v = rm.valid
        s_ = rm.coordinate_time[v] + rm.delay[v]
        spread = float(np.ptp(s_))
        assert spread < 1e-6, (
            f"order {rm.order}: coordinate_time + delay is not constant, "
            f"spread {spread:.3e}")
        origins.append(float(s_[0]))
    drift = max(origins) - min(origins)
    assert drift < 1e-6, f"orders disagree on the time origin: {origins}"


def test_C9b_delay_is_nonnegative_and_orders_are_ordered():
    maps = _maps()
    med = []
    for rm in maps:
        v = rm.valid
        assert float(rm.delay[v].min()) >= -1e-9
        med.append(float(np.median(rm.delay[v])))
    assert med[0] < med[1] < med[2], (
        f"median delay must increase with image order: {med}")


# ---- 10: the stored quadrature weight against the grid it was measured on --
def test_C10_stored_pixel_area_is_checked_against_the_realized_grid():
    """`pixel_area` is the nominal dx squared; the grid spacing is not.

    AART is asked for a cell size and lays down `npoints` samples across the
    band, so the realized spacing is span/(npoints-1) and only coincides with
    the request when the division happens to come out even. The stored solid
    angle per ray is then wrong by an order-dependent factor, which is the
    one kind of error an order-resolved experiment cannot absorb.

    This canary does not assert that the archive is clean -- it is not. It
    asserts that the discrepancy is measured, so that no later construction
    can quietly adopt one of the two values without saying which.
    """
    seen = {}
    for n, rm in enumerate(_maps()):
        ua = np.unique(rm.alpha)
        delta = float((ua[-1] - ua[0]) / (ua.size - 1))
        stored = float(np.unique(rm.pixel_area)[0])
        seen[n] = delta ** 2 / stored
        assert np.unique(rm.beta).size == ua.size, (
            "the two screen axes must share a sampling for a square cell to "
            "mean anything")
    assert seen[0] == pytest.approx(1.0, rel=1e-12), (
        "order 0 is the one core-profile order whose grid divides evenly; if "
        "that changed, every number in the R3A record needs re-deriving")
    assert max(abs(v - 1.0) for v in seen.values()) > 1e-6, (
        "the archived pixel_area/grid-spacing discrepancy has disappeared "
        "from the maps this suite reads. That is either a repair, which must "
        "be recorded and re-reviewed, or the wrong maps.")


# ---- 11: refinement approaches the ray ceiling and never passes it --------
def test_C11_refinement_never_manufactures_information():
    """The substantive canary behind the convergence study.

    A detector that resolves the rays completely can recover what the rays
    carry and no more. Refinement may therefore climb, but the climb has a
    ceiling set by the ray sampling itself, and a construction that crossed
    it would be inventing signal out of quadrature.
    """
    rm = _maps()[2]
    a, b, v = rm.alpha, rm.beta, rm.valid
    cell = float(np.unique(rm.pixel_area)[0])
    A = np.stack([np.ones(a.size), 0.01 * a, 0.01 * b], axis=1)
    ceiling = float(cell * np.sum(A[v] ** 2))
    vals = []
    for k in (4, 2, 1, 0.5):
        g = DetectorGrid(-25.4, 25.4, -25.0, 25.4, np.sqrt(cell) * k)
        rows, cols, w, _ = overlap_triplets(a, b, cell, g, v)
        uniq, inv = np.unique(rows, return_inverse=True)
        y = np.zeros((uniq.size, 3))
        np.add.at(y, inv, w[:, None] * A[cols])
        vals.append(float(np.sum(y ** 2) / g.cell_area))
    assert all(x <= y * (1 + 1e-12) for x, y in zip(vals, vals[1:])), (
        f"refinement must not lose information on a fixed field: {vals}")
    assert max(vals) <= ceiling * (1 + 1e-9), (
        f"refinement passed the ray-level ceiling {ceiling}: {vals}")
    assert vals[-1] < ceiling * (1 - 1e-6), (
        "this fixture must still be short of the ceiling, or it is not "
        "exercising the gap it was written to watch")


# ---- 12: the overlap is exact when the two lattices are commensurate ------
def test_C12_mapping_is_exact_on_a_commensurate_lattice():
    """Where the deficit comes from, isolated.

    Give the detector the order's own footprint and origin and the same
    overlap rule reproduces the ray-level value to machine precision at every
    pitch. The error in the shared-grid study is misalignment between two
    lattices, not the conservative overlap, and this canary is what entitles
    the record to say so.
    """
    rm = _maps()[2]
    a, b, v = rm.alpha, rm.beta, rm.valid
    ua = np.unique(a)
    cell = float((ua[-1] - ua[0]) / (ua.size - 1)) ** 2
    h = 0.5 * np.sqrt(cell)
    A = np.stack([np.ones(a.size), 0.01 * a, 0.01 * b], axis=1)
    ceiling = float(cell * np.sum(A[v] ** 2))
    for k in (1, 0.5, 0.25):
        g = DetectorGrid(float(a[v].min() - h), float(a[v].max() + h + 1e-9),
                         float(b[v].min() - h), float(b[v].max() + h + 1e-9),
                         float(np.sqrt(cell)) * k)
        rows, cols, w, _ = overlap_triplets(a, b, cell, g, v)
        uniq, inv = np.unique(rows, return_inverse=True)
        y = np.zeros((uniq.size, 3))
        np.add.at(y, inv, w[:, None] * A[cols])
        got = float(np.sum(y ** 2) / g.cell_area)
        assert got == pytest.approx(ceiling, rel=1e-10), (
            f"commensurate lattice at k={k} should be exact: "
            f"{got / ceiling - 1:+.3e}")
