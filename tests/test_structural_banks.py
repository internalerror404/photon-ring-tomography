"""The structure-first banks must actually be structure-first."""
import numpy as np
import pytest

from phrt.metrics.level_structure import level_subspace
from phrt.metrics.scoring import evaluation_grid
from phrt.sources.orbits import isco_radius
from phrt.sources.structural import (BUILDERS, FAMILIES, constant_flux,
                                     max_structure_fraction,
                                     slice_means, structure_balanced,
                                     structure_fraction)

SPIN, R_IN, R_OUT = 0.5, 1.8660386527060988, 49.98205255591607
TLO, THI, NT = -128.82234649196255, 29.0, 40


@pytest.fixture(scope="module")
def grid():
    r, p, t = evaluation_grid(R_IN, R_OUT, TLO, THI, n_t=NT)
    lev = level_subspace(t, TLO, THI, 8)
    ti = np.searchsorted(np.linspace(TLO, THI, NT), t)
    return r, p, t, lev, np.clip(ti, 0, NT - 1)


def test_every_declared_family_builds():
    rng = np.random.default_rng(0)
    assert set(BUILDERS) == set(FAMILIES) and len(FAMILIES) == 4
    for name in FAMILIES:
        m = BUILDERS[name](rng, SPIN, 29.99)
        assert m.family == name and m.content_hash


def test_circular_centres_are_outside_the_isco():
    rng = np.random.default_rng(1)
    r_i = isco_radius(SPIN)
    for _ in range(30):
        assert BUILDERS["circular_single_hotspot"](rng, SPIN, 29.99).params["r0"] > r_i
        for s in BUILDERS["circular_two_hotspots"](rng, SPIN, 29.99).params["spots"]:
            assert s["r0"] > r_i
        assert BUILDERS["circular_crescent"](rng, SPIN, 29.99).params["r_peak"] > r_i


def test_plunging_centres_are_inside_the_isco_and_outside_the_horizon():
    rng = np.random.default_rng(2)
    r_i, r_h = isco_radius(SPIN), 1.0 + np.sqrt(1 - SPIN ** 2)
    for _ in range(30):
        p = BUILDERS["plunging_hotspot"](rng, SPIN, 29.99).params
        assert r_h < p["r0"] < r_i
        assert p["orbit"] == "kerr_plunge_on_isco_constants"


def test_constant_flux_makes_every_slice_mean_equal(grid):
    r, p, t, lev, ti = grid
    rng = np.random.default_rng(3)
    v = BUILDERS["circular_single_hotspot"](rng, SPIN, 29.99)(r, p, t) + 1.0
    out, diag = constant_flux(v, ti, NT, target_mean=1.0)
    assert diag["slice_mean_after_max_relative_deviation"] < 1e-10
    m = slice_means(out, ti, NT)
    assert np.allclose(m, m[0], rtol=1e-12)


def test_constant_flux_leaves_a_dust_slice_alone(grid):
    # scaling a numerically-empty slice up to the target mean would manufacture
    # morphology and then report recovering it
    r, p, t, lev, ti = grid
    v = np.zeros_like(r)
    v[ti > 0] = 1.0
    out, diag = constant_flux(v, ti, NT, target_mean=1.0)
    assert diag["n_slices_rescaled"] == NT - 1
    assert np.all(out[ti == 0] == 0.0)


@pytest.mark.parametrize("target", [0.5, 0.8])
def test_structure_balanced_hits_its_target_or_reports_the_ceiling(grid, target):
    r, p, t, lev, ti = grid
    rng = np.random.default_rng(4)
    for name in FAMILIES:
        v = BUILDERS[name](rng, SPIN, 29.99)(r, p, t)
        j, diag = structure_balanced(v, lev, target)
        assert j.min() >= -1e-12, (name, diag)
        if diag["achievable"]:
            assert abs(diag["achieved"] - target) < 0.02, (name, diag)
        else:
            # at the ceiling: the most structural non-negative field there is
            assert diag["achieved"] == pytest.approx(
                diag["max_structure_fraction"], rel=1e-9), (name, diag)
            assert diag["achieved"] < target


def test_positivity_ceiling_is_what_bounds_the_target(grid):
    # a non-negative field's structure fraction is capped at
    # ||s|| / ||s - min s||, and scaling cannot evade it
    r, p, t, lev, ti = grid
    rng = np.random.default_rng(9)
    v = BUILDERS["circular_crescent"](rng, SPIN, 29.99)(r, p, t)
    ceil = max_structure_fraction(v, lev)["max_structure_fraction"]
    j, diag = structure_balanced(v, lev, min(ceil + 0.1, 0.999))
    assert not diag["achievable"]
    assert diag["achieved"] == pytest.approx(ceil, rel=1e-9)
    for a in (0.01, 1.0, 100.0):
        assert max_structure_fraction(a * v, lev)["max_structure_fraction"] == \
            pytest.approx(ceil, rel=1e-9)


def test_structure_balanced_beats_the_r1_baseline_one_fraction(grid):
    r, p, t, lev, ti = grid
    rng = np.random.default_rng(5)
    v = BUILDERS["circular_single_hotspot"](rng, SPIN, 29.99)(r, p, t)
    baseline_one = v + 1.0
    assert structure_fraction(baseline_one, lev) < 0.5
    j, _ = structure_balanced(v, lev, 0.8)
    assert structure_fraction(j, lev) > 0.7


def test_structure_fraction_of_a_uniform_field_is_zero(grid):
    r, p, t, lev, ti = grid
    assert structure_fraction(np.ones_like(r), lev) < 1e-12
