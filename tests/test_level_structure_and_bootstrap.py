"""REVIEWER_RULING_R0C_005: the level/structure projector and the cluster bootstrap.

Both are diagnostics with no threshold to tune, which is exactly why they need
tests: nothing downstream would notice if either quietly stopped meaning what it
says.
"""
from __future__ import annotations

import numpy as np
import pytest

from phrt.metrics.cluster_bootstrap import (anchored_span_interval,
                                            mean_difference_interval,
                                            per_truth_pass_fraction,
                                            running_max)
from phrt.metrics.level_structure import component_errors, level_subspace, split

AGES = np.arange(0.0, 40.0, 4.0)


@pytest.fixture(scope="module")
def grid():
    n_r, n_phi, n_t = 6, 8, 10
    r = np.linspace(2.0, 20.0, n_r)
    phi = np.linspace(0.0, 2 * np.pi, n_phi, endpoint=False)
    t = np.linspace(-30.0, 10.0, n_t)
    R, P, T = np.meshgrid(r, phi, t, indexing="ij")
    return R.ravel(), P.ravel(), T.ravel()


def test_a_spatially_uniform_field_is_entirely_level(grid):
    _, _, t = grid
    L = level_subspace(t, t.min(), t.max(), 6)
    uniform = 1.0 + 0.3 * np.cos(2 * np.pi * (t - t.min()) / (t.max() - t.min()))
    lev, st = split(uniform, L)
    assert np.linalg.norm(st) / np.linalg.norm(uniform) < 1e-12


def test_an_azimuthal_pattern_is_entirely_structure(grid):
    _, phi, t = grid
    L = level_subspace(t, t.min(), t.max(), 6)
    lev, st = split(np.cos(3 * phi), L)
    assert np.linalg.norm(lev) / np.linalg.norm(np.cos(3 * phi)) < 1e-12


def test_the_split_is_a_decomposition(grid):
    r, phi, t = grid
    L = level_subspace(t, t.min(), t.max(), 6)
    v = 1.0 + np.cos(2 * phi) * np.exp(-((r - 8.0) / 3.0) ** 2)
    lev, st = split(v, L)
    assert np.allclose(lev + st, np.atleast_2d(v))
    assert abs(float((lev * st).sum())) < 1e-9 * float(np.linalg.norm(v) ** 2)


def test_component_errors_separate_a_level_only_error(grid):
    r, phi, t = grid
    L = level_subspace(t, t.min(), t.max(), 6)
    W = np.ones((3, t.size))
    truth = 1.0 + np.cos(2 * phi)
    recon = truth + 0.5                      # a pure level error
    out = component_errors(truth, recon, L, W)
    assert out["error_structure_absolute"].max() < 1e-10
    assert out["error_level_absolute"].min() > 0


def test_the_bootstrap_unit_is_the_truth_not_the_draw():
    """Eight draws of one truth are one observation, not eight."""
    rng = np.random.default_rng(0)
    n_truths, n_draws = 40, 8
    per_truth = rng.normal(size=n_truths)
    a = np.repeat(per_truth[:, None], n_draws, axis=1).mean(axis=1)
    wide = mean_difference_interval(a, np.zeros_like(a), 2000, 7)
    # the same data with every draw treated as its own truth
    flat = np.repeat(per_truth, n_draws)
    narrow = mean_difference_interval(flat, np.zeros_like(flat), 2000, 7)
    w_wide = wide["ci_high"] - wide["ci_low"]
    w_narrow = narrow["ci_high"] - narrow["ci_low"]
    assert w_wide > 2.0 * w_narrow, (
        "clustering by truth must not be as tight as pretending the draws are "
        f"independent: {w_wide:.4f} against {w_narrow:.4f}")


def test_a_real_span_difference_excludes_zero():
    n, d, na = 200, 4, AGES.size
    rng = np.random.default_rng(1)
    # arm b stays good further out than arm a, for every truth
    ea = rng.uniform(0.0, 0.2, (n, d, na)) + np.linspace(0, 1.2, na)
    eb = rng.uniform(0.0, 0.2, (n, d, na)) + np.linspace(0, 0.6, na)
    ma, ages = running_max(ea, AGES, 0.0)
    mb, _ = running_max(eb, AGES, 0.0)
    out = anchored_span_interval(per_truth_pass_fraction(ma, 0.5),
                                 per_truth_pass_fraction(mb, 0.5),
                                 ages, 0.9, 0.0, 2000, 11)
    assert out["point_estimate"] > 0
    assert out["excludes_zero"]


def test_no_difference_does_not_exclude_zero():
    n, d, na = 200, 4, AGES.size
    rng = np.random.default_rng(2)
    e = rng.uniform(0.0, 1.0, (n, d, na))
    m, ages = running_max(e, AGES, 0.0)
    pf = per_truth_pass_fraction(m, 0.5)
    out = anchored_span_interval(pf, pf, ages, 0.9, 0.0, 2000, 13)
    assert out["point_estimate"] == 0
    assert not out["excludes_zero"]


def test_the_bootstrap_is_reproducible():
    a = np.linspace(0.0, 1.0, 50)
    b = a * 0.5
    one = mean_difference_interval(a, b, 500, 99)
    two = mean_difference_interval(a, b, 500, 99)
    assert one["ci_low"] == two["ci_low"] and one["ci_high"] == two["ci_high"]
