"""Gate G1: the independent v0.1 operator against the original construction."""
import numpy as np
import pytest

from phrt.operators.v01_toy import (ATTENUATION, GAMMA, H, K, M, MAX_DELAY, NMAX,
                                    RS, RT, SEED, V01Operator, V01Spec, W,
                                    reference_dense, retarded_age_of_index)

SPEC = V01Spec.build()
ARMS = [(name, resolved, N) for name in ("identical", "diverse")
        for resolved in (True, False) for N in range(NMAX + 1)]


def test_registered_constants_are_self_consistent():
    assert H == W + NMAX * 4 == 44
    assert RT * RS == 24
    assert np.isclose(ATTENUATION[NMAX], np.exp(-GAMMA * NMAX))


@pytest.mark.parametrize("name,resolved,N", ARMS)
def test_matrix_free_equals_original_style_dense(name, resolved, N):
    op = V01Operator(N, SPEC.projections(name), resolved)
    ref = reference_dense(N, SPEC.projections(name), resolved)
    assert op.to_dense().shape == ref.shape
    assert np.abs(op.to_dense() - ref).max() == 0.0


@pytest.mark.parametrize("name,resolved,N", ARMS[::5])
def test_hand_written_adjoint(name, resolved, N):
    op = V01Operator(N, SPEC.projections(name), resolved)
    rng = np.random.default_rng(N)
    for _ in range(5):
        x, y = rng.normal(size=op.shape[1]), rng.normal(size=op.shape[0])
        a, b = float(y @ op.matvec(x)), float(x @ op.rmatvec(y))
        assert abs(a - b) / max(abs(a), abs(b), 1e-300) < 1e-8


def test_projections_are_orthonormal_rows():
    """P_n = Q[:, :M].T with Q orthogonal, so P P^T = I_M exactly."""
    for name in ("identical", "diverse"):
        for P in SPEC.projections(name):
            assert P.shape == (M, K)
            assert np.abs(P @ P.T - np.eye(M)).max() < 1e-12


def test_identical_arm_reuses_one_projection():
    ps = SPEC.projections("identical")
    assert all(np.array_equal(ps[0], p) for p in ps)


def test_diverse_arm_uses_distinct_projections():
    ps = SPEC.projections("diverse")
    assert not any(np.allclose(ps[0], p) for p in ps[1:])


def test_prior_basis_is_orthonormal_and_24_dimensional():
    B = SPEC.prior_basis
    assert B.shape == (H * K, RT * RS)
    assert np.abs(B.T @ B - np.eye(RT * RS)).max() < 1e-10


def test_direct_channel_reads_the_newest_window():
    """Order 0 samples source-time indices [MAX_DELAY, H); deeper orders reach
    further back. Index H-1 is the most recent sample, i.e. retarded age 0."""
    assert MAX_DELAY == NMAX * 4 == 20
    assert MAX_DELAY + W == H
    assert retarded_age_of_index(H - 1) == 0
    assert retarded_age_of_index(0) == H - 1


def test_order_windows_tile_the_history_exactly():
    covered = set()
    for n in range(NMAX + 1):
        lo = MAX_DELAY - n * 4
        covered |= set(range(lo, lo + W))
    assert covered == set(range(H))


def test_max_order_outside_range_is_refused():
    with pytest.raises(ValueError):
        V01Operator(NMAX + 1, SPEC.projections("diverse"), True)


def test_canonical_ranks_match_the_reference_table():
    """The six headline ranks of the v0.1 identifiability table at N = NMAX."""
    from phrt.audits.rank import spectrum_of

    expected = {("identical", True): (88, 16), ("diverse", True): (216, 24),
                ("identical", False): (48, 16), ("diverse", False): (48, 23)}
    for (name, resolved), (full, restricted) in expected.items():
        A = V01Operator(NMAX, SPEC.projections(name), resolved).to_dense()
        assert spectrum_of(A).numerical_rank == full
        assert spectrum_of(A @ SPEC.prior_basis).numerical_rank == restricted


def test_analytic_cap_predicts_the_identical_arm():
    """rank(P) * RT = 2 * 8 = 16, the cap a common sampler imposes however many
    delayed orders are stacked. The reference table reports 16 for every N."""
    from phrt.audits.rank import spectrum_of

    P = SPEC.projections("identical")[0]
    assert np.linalg.matrix_rank(P) * RT == 16
    for N in range(NMAX + 1):
        A = V01Operator(N, SPEC.projections("identical"), True).to_dense()
        assert spectrum_of(A @ SPEC.prior_basis).numerical_rank == 16
