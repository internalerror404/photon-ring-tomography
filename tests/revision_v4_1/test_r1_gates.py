"""R1 gates G01-G20.

Each gate verifies an implementation, not a physical result. Three of them --
G05, G16, G17 -- pass by *detecting* a defect: the archived behaviour is
reproduced and shown to be wrong, so a later silent repair cannot make the
gate vacuous.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from phrt.operators.physical import (OrderRays, PhysicalOperator,  # noqa: E402
                                     substitute_delay, substitute_spatial)
from phrt.revision_v4_1 import conditioning, covariance, source_metric  # noqa: E402
from phrt.revision_v4_1.calibration import (COMMON_REFERENCE_COUNT,  # noqa: E402
                                            LEGACY_REPLAY,
                                            LOCKED_LEGACY_NOISE, calibrate,
                                            fisher_information, legacy_s_ref)

RTOL = 1e-10
# Protocol: well_conditioned_fixture_relative_tolerance = 1e-10, and the
# fixture coordinate condition must stay under 1e4 so the bar is meaningful.
FIXTURE_RTOL = 1e-10
FIXTURE_COND_MAX = 1e4
SPLITS = (2, 4, 8, 16)


def _fixture(n_rows=64, n_cols=12, seed=0):
    rng = np.random.default_rng(seed)
    A = rng.normal(size=(n_rows, n_cols))
    q = rng.normal(size=n_cols)
    return A, q


def _split(A: np.ndarray, k: int) -> np.ndarray:
    """A k-way equal-area pixel split of an area-whitened operator.

    Each child carries dOmega/k, so its whitened row is the parent's over
    sqrt(k) and the total squared response is preserved.
    """
    return np.repeat(A, k, axis=0) / np.sqrt(k)


# ---- G01 ----------------------------------------------------------------
def test_G01_amplitude_and_noise_information_scaling():
    A, q = _fixture()
    base = calibrate(A @ q, 100.0, mode=LEGACY_REPLAY, grid_identity="g")
    i0 = fisher_information(A, base, q)
    for f in (1, 2, 4):
        halved = calibrate(A @ q, 100.0 * f, mode=LEGACY_REPLAY,
                           grid_identity="g")
        assert halved.sigma == pytest.approx(base.sigma / f, rel=RTOL)
        assert fisher_information(A, halved, q) == pytest.approx(
            i0 * f ** 2, rel=RTOL)
        big = calibrate(A @ q, 100.0, mode=LOCKED_LEGACY_NOISE,
                        locked_sigma=base.sigma, grid_identity="g")
        assert fisher_information(f * A, big, q) == pytest.approx(
            i0 * f ** 2, rel=RTOL)


# ---- G02 / G03 / G04 / G05 ----------------------------------------------
def test_G02_legacy_replay_reproduces_the_archived_formula():
    A, q = _fixture()
    cal = calibrate(A @ q, 100.0, mode=LEGACY_REPLAY, grid_identity="g")
    assert cal.s_ref == pytest.approx(legacy_s_ref(A @ q), rel=1e-15)
    assert cal.m_reference == cal.m_current


def test_G03_fixed_noise_split_merge_is_invariant():
    """Refining the representation of the same observation adds nothing."""
    A, q = _fixture()
    cal = calibrate(A @ q, 100.0, mode=LEGACY_REPLAY, grid_identity="g")
    i0 = fisher_information(A, cal, q)
    for k in SPLITS:
        locked = calibrate(_split(A, k) @ q, 100.0, mode=LOCKED_LEGACY_NOISE,
                           locked_sigma=cal.sigma, grid_identity=f"g/{k}")
        assert fisher_information(_split(A, k), locked, q) == pytest.approx(
            i0, rel=1e-12)


def test_G04_common_count_recalibration_is_split_invariant():
    A, q = _fixture()
    m0 = A.shape[0]
    cal = calibrate(A @ q, 100.0, mode=COMMON_REFERENCE_COUNT, m_reference=m0,
                    grid_identity="g")
    i0 = fisher_information(A, cal, q)
    worst = 0.0
    for k in SPLITS:
        Ak = _split(A, k)
        ck = calibrate(Ak @ q, 100.0, mode=COMMON_REFERENCE_COUNT,
                       m_reference=m0, grid_identity=f"g/{k}")
        worst = max(worst, abs(fisher_information(Ak, ck, q) / i0 - 1.0))
    assert worst < 1e-12, f"worst relative split discrepancy {worst:.3e}"


def test_G05_the_legacy_recalibration_counterexample_is_detected():
    """Passing here means the archived formula's defect was reproduced."""
    A, q = _fixture()
    cal = calibrate(A @ q, 100.0, mode=LEGACY_REPLAY, grid_identity="g")
    i0 = fisher_information(A, cal, q)
    for k in SPLITS:
        Ak = _split(A, k)
        bad = calibrate(Ak @ q, 100.0, mode=LEGACY_REPLAY,
                        grid_identity=f"g/{k}")
        assert fisher_information(Ak, bad, q) / i0 == pytest.approx(k, rel=1e-9)


def test_G05b_zero_reference_response_raises_rather_than_flooring():
    with pytest.raises(ValueError, match="cannot define an SNR"):
        calibrate(np.zeros(16), 100.0, mode=LEGACY_REPLAY, grid_identity="g")


# ---- G06 ----------------------------------------------------------------
def test_G06_every_physical_calibration_site_is_inventoried():
    """The migration map must cover every discovered physical site."""
    import json
    runs = sorted((ROOT / "artifacts" / "revisions" / "mahakal_v4_1").glob("*"))
    inv = next((r / "normalization_site_inventory.json" for r in runs
                if (r / "normalization_site_inventory.json").exists()), None)
    if inv is None:
        pytest.skip("R0 inventory not present in this tree")
    doc = json.loads(inv.read_text())
    assert doc["inventory_is_exhaustive"], doc["textual_ast_disagreements_open"]
    sites = {d["path"] for d in doc["physical_mean_over_rows_definitions"]}
    mig = next((r / "calibration_migration_map.json" for r in runs
                if (r / "calibration_migration_map.json").exists()), None)
    if mig is None:
        pytest.skip("R1 migration map not written yet")
    covered = {e["legacy_site"] for e in json.loads(mig.read_text())["entries"]}
    assert sites <= covered, f"uncovered physical sites: {sorted(sites - covered)}"


# ---- G07 / G08 / G09 / G10 ----------------------------------------------
def test_G07_general_mixing_needs_the_full_covariance():
    """A mixer that shares an order between channels correlates them."""
    A, q = _fixture(n_rows=6, n_cols=4)
    C = np.diag(np.linspace(0.5, 2.0, 6))
    L = np.array([[1.0, 1.0, 0, 0, 0, 0],
                  [0, 1.0, 1.0, 0, 0, 0],
                  [0, 0, 0, 1.0, 1.0, 1.0]])
    CL = covariance.mixed_covariance(L, C)
    assert abs(CL[0, 1]) > 1e-6, "the shared row must correlate the channels"
    full = covariance.mixed_whiten(A, L, C)
    diag_only = covariance.whiten(L @ A, np.diag(np.diag(CL)))
    assert not np.isclose(full.information, diag_only.information, rtol=1e-6)


def test_G07b_archived_mixers_are_exactly_diagonal():
    """Identity and all-ones single-output: no omitted cross term."""
    A, _ = _fixture(n_rows=6, n_cols=4)
    C = np.diag(np.linspace(0.5, 2.0, 6))
    for L in (np.eye(6), np.ones((1, 6))):
        CL = covariance.mixed_covariance(L, C)
        off = CL - np.diag(np.diag(CL))
        assert np.abs(off).max() < 1e-14


def test_G08_noiseless_constraints_are_kept_not_discarded():
    A, _ = _fixture(n_rows=5, n_cols=3)
    C = np.diag([1.0, 1.0, 1.0, 1.0, 0.0])         # one exact row
    w = covariance.whiten(A, C)
    assert w.n_exact == 1 and w.rank == 4
    assert np.abs(w.exact).max() > 0, "the exact constraint carries signal"


def _fisher(w) -> np.ndarray:
    """The full information matrix B^T B, not its trace."""
    return w.B.T @ w.B


def test_G09_invertible_reexpression_preserves_the_whole_fisher_matrix():
    """Trace equality is necessary and far from sufficient."""
    A, _ = _fixture(n_rows=8, n_cols=4)
    C = np.diag(np.linspace(0.5, 2.0, 8))
    F0 = _fisher(covariance.whiten(A, C))
    scale = max(float(np.abs(F0).max()), 1e-300)
    rng = np.random.default_rng(3)
    worst_matrix = worst_trace = 0.0
    for _ in range(50):
        L = rng.normal(size=(8, 8))
        while abs(np.linalg.det(L)) < 1e-3 or np.linalg.cond(L) > 1e4:
            L = rng.normal(size=(8, 8))
        F = _fisher(covariance.mixed_whiten(A, L, C))
        worst_matrix = max(worst_matrix, float(np.abs(F - F0).max()) / scale)
        worst_trace = max(worst_trace,
                          abs(np.trace(F) / np.trace(F0) - 1.0))
    assert worst_matrix < FIXTURE_RTOL, (
        f"worst full-matrix deviation {worst_matrix:.3e} against "
        f"{FIXTURE_RTOL:.0e}; trace-only deviation was {worst_trace:.3e}")


def test_G10_rank_reducing_postprocessing_contracts_in_the_loewner_order():
    """F_after <= F_before as matrices: no direction may gain information."""
    A, _ = _fixture(n_rows=8, n_cols=4)
    C = np.eye(8)
    F0 = _fisher(covariance.whiten(A, C))
    for L in (np.ones((1, 8)), np.eye(8)[:3], np.vstack([np.ones((1, 8)),
                                                         np.eye(8)[0]])):
        F = _fisher(covariance.mixed_whiten(A, L, C))
        gap = np.linalg.eigvalsh(F0 - F)
        assert gap.min() > -1e-10 * max(float(np.abs(F0).max()), 1.0), (
            f"a direction gained information: smallest eigenvalue of "
            f"F_before - F_after is {gap.min():.3e}")
        assert np.trace(F) <= np.trace(F0) + 1e-12


# ---- G11 / G19 ----------------------------------------------------------
def test_G11_source_basis_change_leaves_the_physical_spectrum_fixed():
    rng = np.random.default_rng(5)
    n_pts, n_fun = 200, 6
    V = rng.normal(size=(n_pts, n_fun))
    w = rng.uniform(0.5, 1.5, size=n_pts)
    A = rng.normal(size=(30, n_fun))
    H = source_metric.gram(V, w)
    M = source_metric.factor(H, domain="fixture", n_quadrature=n_pts)
    ref = np.linalg.svd(M.to_physical(A), compute_uv=False)
    worst_phys, worst_coord = 0.0, 0.0
    for _ in range(50):
        T = rng.normal(size=(n_fun, n_fun))
        while np.linalg.cond(T) > 1e4:
            T = rng.normal(size=(n_fun, n_fun))
        Ht = source_metric.gram(V @ T, w)
        Mt = source_metric.factor(Ht, domain="fixture", n_quadrature=n_pts)
        got = np.linalg.svd(Mt.to_physical(A @ T), compute_uv=False)
        worst_phys = max(worst_phys, float(np.abs(got / ref - 1).max()))
        coord = np.linalg.svd(A @ T, compute_uv=False)
        worst_coord = max(worst_coord,
                          float(np.linalg.cond(A @ T) / np.linalg.cond(A)))
    assert worst_phys < FIXTURE_RTOL, (
        f"physical spectrum moved by {worst_phys:.3e} against "
        f"{FIXTURE_RTOL:.0e}")
    assert worst_coord > 2.0, ("the fixture must actually stress coordinate "
                               "conditioning, else the invariance is vacuous")


def test_G19_gram_converges_under_quadrature_refinement():
    def f(x):
        return np.stack([np.ones_like(x), x, x ** 2, np.sin(3 * x)], axis=1)

    prev, rels = None, []
    for n in (200, 400, 800, 1600):
        x = (np.arange(n) + 0.5) / n
        H = source_metric.gram(f(x), np.full(n, 1.0 / n))
        if prev is not None:
            rels.append(float(np.abs(H - prev).max() / np.abs(H).max()))
        prev = H
    assert len(rels) >= 3 and rels[-1] < 1e-6, rels
    assert rels[-1] <= rels[0], "refinement must not diverge"


# ---- G12 / G13 / G14 / G15 ----------------------------------------------
def test_G12_identical_old_and_recent_responses_give_zero_conditional():
    rng = np.random.default_rng(7)
    col = rng.normal(size=(40, 1))
    spec = conditioning.conditional_spectrum(col, col.copy())
    assert spec.information_known > 0
    assert spec.information_conditional < 1e-20


def test_G13_an_independent_recent_measurement_breaks_the_degeneracy():
    rng = np.random.default_rng(8)
    shared = rng.normal(size=(40, 1))
    extra = np.zeros((40, 1))
    extra[:5] = rng.normal(size=(5, 1))            # sees only the recent part
    B_o = np.vstack([shared, np.zeros((5, 1))])
    B_n = np.vstack([shared, rng.normal(size=(5, 1))])
    assert conditioning.conditional_spectrum(
        B_o, B_n).information_conditional > 1e-6


def test_G14_nuisance_coordinate_changes_do_not_move_the_result():
    rng = np.random.default_rng(9)
    B_o = rng.normal(size=(60, 3))
    B_n = rng.normal(size=(60, 5))
    ref = conditioning.conditional_spectrum(B_o, B_n).s_conditional
    worst = 0.0
    for _ in range(30):
        K = rng.normal(size=(5, 5))
        while np.linalg.cond(K) > 1e4:
            K = rng.normal(size=(5, 5))
        got = conditioning.conditional_spectrum(B_o, B_n @ K).s_conditional
        worst = max(worst, float(np.abs(got / ref - 1).max()))
    assert worst < FIXTURE_RTOL, (
        f"worst relative deviation {worst:.3e} against {FIXTURE_RTOL:.0e}")


def test_G15_conditional_information_never_exceeds_known_remainder():
    rng = np.random.default_rng(10)
    for _ in range(40):
        B_o = rng.normal(size=(50, 4))
        B_n = rng.normal(size=(50, rng.integers(0, 8)))
        s = conditioning.conditional_spectrum(B_o, B_n)
        assert s.information_conditional <= s.information_known + 1e-9


# ---- G16 / G17: defects that must stay visible --------------------------
def _rays(n, seed, order=0):
    rng = np.random.default_rng(seed)
    return OrderRays(order=order, source_r=rng.uniform(4, 40, n),
                     source_phi=rng.uniform(0, 2 * np.pi, n),
                     delay=rng.uniform(0, 60, n),
                     redshift=rng.uniform(0.5, 1.5, n),
                     quadrature=np.full(n, 1.0 / n))


def test_G16_equal_cardinality_does_not_establish_registration():
    """The archived guard accepts two unrelated screens of the same size."""
    a, b = _rays(32, 1, 0), _rays(32, 2, 1)
    assert a.n_rays == b.n_rays
    assert not hasattr(a, "alpha") and not hasattr(a, "beta")
    op = PhysicalOperator(orders=[a, b], observer_times=np.linspace(0, 7, 8),
                          design=lambda r, p, t: np.stack(
                              [np.ones_like(r), r, np.cos(p), t], axis=1),
                          dimension=4, mixer=np.ones((1, 2)))
    assert op.n_channels == 1, "the all-ones mixer was accepted by count alone"
    assert float(np.abs(a.source_r - b.source_r).max()) > 1.0, (
        "the two orders are unrelated draws, which the guard cannot see")


def test_G17_index_paired_substitution_moves_under_reindexing():
    """A co-registered transplant would be invariant to a common relabelling."""
    base = [_rays(48, 3, 0), _rays(48, 4, 1)]
    times = np.linspace(0, 7, 8)

    def design(r, p, t):
        return np.stack([np.ones_like(r), r, np.cos(p), t], axis=1)

    def spectrum(orders):
        op = PhysicalOperator(orders=orders, observer_times=times,
                              design=design, dimension=4)
        return np.linalg.svd(op.to_dense(), compute_uv=False)

    def relabel(o, perm):
        return OrderRays(o.order, o.source_r[perm], o.source_phi[perm],
                         o.delay[perm], o.redshift[perm], o.quadrature[perm],
                         o.amplitude)

    rng = np.random.default_rng(11)
    common = rng.permutation(48)

    # A relabelling applied to every order alike keeps each ray paired with
    # the same donor ray, so it only permutes rows: the spectrum must not
    # move. This is the control that stops the gate passing for a trivial
    # reason.
    for sub in (substitute_spatial, substitute_delay):
        together = [relabel(o, common) for o in base]
        a = spectrum(sub(base, base[0]))
        b = spectrum(sub(together, together[0]))
        assert float(np.abs(a / b - 1).max()) < 1e-9, (
            "a common relabelling must be a row permutation only")

    # Relabelling one order independently of the donor is what the archived
    # sampler does -- stratified_subsample and common_count draw per order --
    # and it changes which donor ray each ray is paired with. A co-registered
    # transplant would be unmoved; an index-paired one moves.
    apart = [base[0], relabel(base[1], rng.permutation(48))]
    for sub, name in ((substitute_spatial, "DELAY_ONLY"),
                      (substitute_delay, "SPATIAL_ONLY")):
        a = spectrum(sub(base, base[0]))
        b = spectrum(sub(apart, apart[0]))
        assert float(np.abs(a / b - 1).max()) > 1e-6, (
            f"{name} did not move when one order was relabelled "
            "independently; the index-pairing defect would be invisible")


# ---- G18 ----------------------------------------------------------------
def test_G18_flux_semantics_are_runner_specific():
    orders = [_rays(24, 5, n) for n in (0, 1, 2)]
    times = np.linspace(0, 7, 8)

    def design(r, p, t):
        return np.stack([np.ones_like(r), r, np.cos(p), t], axis=1)

    e3c = PhysicalOperator(orders=orders, observer_times=times, design=design,
                           dimension=4, collapse="total_flux")
    hmt2 = PhysicalOperator(orders=orders, observer_times=times, design=design,
                            dimension=4, mixer=np.ones((1, 3)),
                            collapse="total_flux")
    assert e3c.shape[0] == 24, "E3C keeps one light curve per order"
    assert hmt2.shape[0] == 8, "HMT2 sums the orders"
    assert np.linalg.matrix_rank(hmt2.to_dense()) <= 8

    rng = np.random.default_rng(12)
    # One permutation per order, applied to every field of that order: a
    # relabelling of pixels, not a destruction of their pairing.
    permuted = []
    for o in orders:
        pi = rng.permutation(o.n_rays)
        permuted.append(OrderRays(o.order, o.source_r[pi], o.source_phi[pi],
                                  o.delay[pi], o.redshift[pi],
                                  o.quadrature[pi], o.amplitude))
    same = PhysicalOperator(orders=permuted, observer_times=times,
                            design=design, dimension=4, mixer=np.ones((1, 3)),
                            collapse="total_flux")
    assert np.allclose(hmt2.to_dense(), same.to_dense(), atol=1e-12), (
        "integrated flux must be invariant to within-order pixel order")
