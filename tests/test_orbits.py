"""The source must move the way the redshift baked into the ray maps assumes."""
import numpy as np
import pytest

from phrt.geometry.schwarzschild import kerr_keplerian_u
from phrt.sources.orbits import (circular_energy_angular_momentum,
                                 circular_radius_bounds, horizon_radius,
                                 isco_radius, kerr_omega, pattern_omega,
                                 plunge_omega, velocity_field_record)


def test_isco_reduces_to_schwarzschild():
    assert isco_radius(0.0) == pytest.approx(6.0)
    assert isco_radius(0.5) == pytest.approx(4.233002529530826)
    assert isco_radius(0.5, -1) > isco_radius(0.5, +1)


def test_circular_constants_match_the_schwarzschild_isco():
    E, L = circular_energy_angular_momentum(6.0, 0.0)
    assert float(E) == pytest.approx(np.sqrt(8.0 / 9.0))
    assert float(L) == pytest.approx(np.sqrt(12.0))


def test_omega_matches_the_independent_kerr_four_velocity():
    r = np.array([5.0, 8.0, 20.0, 45.0])
    u0, _, _, u3 = kerr_keplerian_u(0.5, r)
    assert np.allclose(u3 / u0, kerr_omega(r, 0.5), rtol=1e-12)


def test_plunge_is_continuous_with_the_circular_law_at_the_isco():
    for a in (0.0, 0.5, 0.9):
        r_isco = isco_radius(a)
        assert plunge_omega(r_isco, a) == pytest.approx(kerr_omega(r_isco, a), rel=1e-12)


def test_pattern_law_switches_at_the_isco_and_stays_finite():
    a = 0.5
    r = np.linspace(horizon_radius(a) + 1e-3, 45.0, 400)
    w = pattern_omega(r, a)
    assert np.all(np.isfinite(w))
    assert np.all(w > 0.0)
    outside = r >= isco_radius(a)
    assert np.all(np.diff(w[outside]) < 0.0)   # circular: inner material turns faster


def test_plunging_pattern_approaches_the_horizon_angular_velocity():
    # inside the ISCO the plunge is not a faster circular orbit: frame dragging
    # locks it to Omega_H = a / (2 r_+) at the horizon, so the rate turns over
    # rather than diverging. A family that kept using Omega_K inside would spin
    # its features up without bound instead.
    a = 0.5
    omega_h = a / (2.0 * horizon_radius(a))
    assert float(pattern_omega(horizon_radius(a) + 1e-6, a)) == pytest.approx(
        omega_h, rel=1e-4)
    r = np.linspace(horizon_radius(a) + 1e-3, isco_radius(a), 200)
    assert float(pattern_omega(r, a).max()) > float(pattern_omega(isco_radius(a), a))


def test_newtonian_law_is_materially_wrong_where_the_old_bank_drew_spots():
    # the R0/R1 families drew circular hotspots from r = 3 M, inside the
    # prograde ISCO, and advected them at r^{-3/2}. Both are recorded here as
    # measured discrepancies rather than asserted as harmless.
    a = 0.5
    assert 3.0 < isco_radius(a)
    rel = abs(3.0 ** -1.5 - float(pattern_omega(3.0, a))) / float(pattern_omega(3.0, a))
    assert rel > 0.15


def test_circular_bounds_start_at_the_isco():
    lo, hi = circular_radius_bounds(0.5, 29.99)
    assert lo == pytest.approx(isco_radius(0.5))
    assert hi == pytest.approx(29.99)


def test_velocity_field_record_is_complete():
    rec = velocity_field_record(0.5)
    for k in ("metric", "spin", "sense", "outside_isco", "inside_isco",
              "isco_radius_M", "horizon_radius_M", "matches_raymap_fluid"):
        assert k in rec
    assert rec["horizon_radius_M"] == pytest.approx(1.8660254037844386)
