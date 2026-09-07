"""Static checks on the radial quartic and the turning reduction. Ruling 032.

Closed-form algebra and synthetic fixtures only: no ray is traced and no path
integral is recomputed here.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from phrt.revision_v4_1 import pathdomain as PD                 # noqa: E402
from phrt.revision_v4_1 import rootcheck as RC                  # noqa: E402


# ---- R1: the 031 residual is zero for any list at all ----
def test_R1_self_root_product_residual_is_tautological():
    for seed in range(5):
        rng = np.random.default_rng(seed)
        nonsense = rng.normal(size=4) + 1j * rng.normal(size=4)
        circ = np.prod(nonsense[:, None] - nonsense[None, :], axis=0)
        assert np.max(np.abs(circ)) == 0.0


def test_R1b_the_original_polynomial_detects_a_perturbed_root():
    c = RC.quartic_coefficients(0.5, 3.0, 4.0).ravel()
    r = np.roots(c)
    assert np.max(RC.backward_residual(c, r)) < 1e-13
    bad = r.copy()
    bad[0] += 0.05
    assert np.max(RC.backward_residual(c, bad)) > 1e-3


# ---- R2: the coefficients come from the conserved quantities ----
def test_R2_expanded_quartic_matches_the_product_of_its_own_roots():
    a = 0.5
    for lam, eta in ((3.0, 4.0), (-2.5, 11.0), (0.0, 27.0)):
        c = RC.quartic_coefficients(a, lam, eta).ravel()
        r = np.roots(c)
        assert np.allclose(np.poly(r), c, atol=1e-10)


def test_R2b_conserved_quantities_are_a_closed_form_of_the_screen():
    th = np.deg2rad(50.0)
    lam, eta = RC.conserved_quantities(np.array([3.0]), np.array([4.0]), th, 0.5)
    assert lam[0] == pytest.approx(-3.0 * np.sin(th))
    assert eta[0] == pytest.approx((9.0 - 0.25) * np.cos(th) ** 2 + 16.0)


def test_R2c_the_schwarzschild_limit_reduces_to_the_known_quartic():
    """a = 0: R(r) = r^4 - b^2 r^2 + 2 b^2 r with eta = b^2 - lam^2 + lam^2."""
    b = 6.0
    c = RC.quartic_coefficients(0.0, 0.0, b * b).ravel()
    assert np.allclose(c, [1.0, 0.0, -b * b, 2 * b * b, 0.0])
    r = np.roots(c)
    # r = 0 and r = 3M are the known Schwarzschild roots at the critical impact
    # parameter b = 3 sqrt(3); at b = 6 the outer turning point is the one the
    # path classifier would select, and the quartic reproduces it exactly
    assert np.min(np.abs(r)) == pytest.approx(0.0, abs=1e-12)
    assert np.allclose(np.polyval(c, r), 0.0, atol=1e-10)


# ---- R3: a small residual is not a root-location bound ----
def test_R3_near_multiple_roots_break_the_residual_as_a_locator():
    c = np.poly([1.0, 1.0 + 1e-7, 3.0, 5.0]).real
    r = np.roots(c)
    cond = RC.conditioning(c, r)
    assert cond["min_separation"] < 1e-5
    assert RC.CLUSTERED in cond["kind"] or RC.MULTIPLE in cond["kind"]
    assert cond["residual_is_a_root_location_bound"] is False
    # a point 1e-4 away is still a tiny backward error near the cluster
    assert RC.backward_residual(c, np.array([1.0 + 1e-4])) < 1e-8


def test_R3b_a_well_separated_root_has_a_small_newton_step():
    c = np.poly([-4.0, 0.5, 2.0, 9.0]).real
    cond = RC.conditioning(c, np.roots(c))
    assert cond["max_newton_step"] < 1e-10
    assert set(cond["kind"]) == {RC.SIMPLE}


# ---- R4: exclusion by index, not by object identity ----
def test_R4_identity_exclusion_kills_the_integrand_at_the_turn():
    """The 031 reduced product vanishes exactly where the integrand peaks."""
    roots = np.array([-3 + 0j, 0 + 0j, 1 + 0j, 2 + 0j])
    turn = float(max(q.real for q in roots if 0.5 < q.real < 10.0))
    assert RC.identity_excluded_product(roots, turn, turn) == 0
    idx = RC.turning_index(roots, 0.5, 10.0)
    assert idx == 3
    assert RC.reduced_limit(roots, idx).real == pytest.approx(5.0 * 2.0 * 1.0)


def test_R4b_the_frozen_031_code_reproduces_the_defect():
    """Named, not repaired: version 2 stays frozen as the 031 record."""
    import inspect
    from phrt.revision_v4_1 import pathdomain2 as P2
    src = inspect.getsource(P2.integral)
    assert "q is not turn" in src, "the 031 reduction is an identity test"


def test_R4c_index_exclusion_refuses_a_clustered_turning_root():
    roots = np.array([1.0 + 0j, 2.0 + 0j, 2.0 + 1e-12j, 9.0 + 0j])
    with pytest.raises(RC.RootCheckError, match="not the analytic limit"):
        RC.reduced_product(roots, 1, 2.0)


def test_R4d_no_accessible_turning_root_returns_none():
    roots = np.array([-2 + 0j, 0.4 + 0j, 1 + 1j, 1 - 1j])
    assert RC.turning_index(roots, 1.8, 1000.0) is None


# ---- R5: the endpoint limit, on an analytic fixture ----
def test_R5_reduced_integrand_tends_to_its_analytic_limit():
    """R(r)/(r - r_t) -> prod_(j != t) (r_t - r_j) as r -> r_t."""
    roots = np.array([-3 + 0j, 0.2 + 0j, 1.1 + 0j, 4.7 + 0j])
    idx = 3
    want = RC.reduced_limit(roots, idx)
    for eps in (1e-3, 1e-5, 1e-7):
        r = roots[idx].real + eps
        exact = PD.radial_potential(r, roots) / (r - roots[idx].real)
        assert abs(complex(exact) - want) < 100.0 * eps
    assert want.real == pytest.approx((4.7 + 3) * (4.7 - 0.2) * (4.7 - 1.1))
