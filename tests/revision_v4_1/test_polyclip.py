"""Exactness canaries for the fractional-coverage kernel, ruling 027 H0."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from phrt.revision_v4_1 import polyclip as PC            # noqa: E402

EXACT = 1e-12


def rect(x0, x1, y0, y1):
    return np.array([[x0, y0], [x1, y0], [x1, y1], [x0, y1]], float)


def circle(n, r=1.0, cx=0.0, cy=0.0, phase=0.0):
    t = 2 * np.pi * np.arange(n) / n + phase
    return np.stack([cx + r * np.cos(t), cy + r * np.sin(t)], axis=1)


def test_K1_square_on_an_aligned_grid_is_exact():
    P = rect(0.0, 1.0, 0.0, 1.0)
    X = np.linspace(0, 1, 5)
    cov = PC.grid_coverage(P, X, X)
    assert cov.shape == (4, 4)
    assert np.allclose(cov, 0.0625, rtol=EXACT, atol=EXACT)
    assert float(cov.sum()) == pytest.approx(1.0, rel=EXACT)


def test_K2_square_on_an_offset_grid_conserves_area():
    P = rect(0.13, 0.87, -0.31, 0.42)
    X = np.linspace(-1, 1, 23)
    Y = np.linspace(-1, 1, 17)
    cov = PC.grid_coverage(P, X, Y)
    assert float(cov.sum()) == pytest.approx(0.74 * 0.73, rel=EXACT)
    assert (cov >= -EXACT).all()


def test_K3_vertical_and_horizontal_edges_on_grid_lines():
    """Degeneracies a vertex-value quadrature would get wrong."""
    P = rect(-0.5, 0.5, -0.5, 0.5)
    X = np.array([-0.5, 0.0, 0.5])
    cov = PC.grid_coverage(P, X, X)
    assert np.allclose(cov, 0.25, rtol=EXACT, atol=EXACT)


def test_K4_non_convex_polygon_split_into_two_components_by_one_cell():
    """A U clipped by a row that meets both prongs and not the base."""
    P = np.array([[0, 0], [3, 0], [3, 3], [2, 3], [2, 1], [1, 1], [1, 3],
                  [0, 3]], float)
    assert PC.is_simple(P)
    assert abs(PC.signed_area(P)) == pytest.approx(9 - 2, rel=EXACT)
    X = np.array([0.0, 3.0])
    Y = np.array([2.0, 3.0])
    cov = PC.grid_coverage(P, X, Y)
    assert float(cov[0, 0]) == pytest.approx(2.0, rel=EXACT), (
        "two disconnected prongs of width one and height one")
    full = PC.grid_coverage(P, np.linspace(0, 3, 13), np.linspace(0, 3, 13))
    assert float(full.sum()) == pytest.approx(7.0, rel=EXACT)


def test_K5_circle_area_converges_and_every_grid_agrees():
    """The kernel is exact on the polygon; the polygon is not the circle."""
    for n in (12, 60, 240):
        P = circle(n)
        want = 0.5 * n * np.sin(2 * np.pi / n)
        for grid in (np.linspace(-1.3, 1.3, 7), np.linspace(-1.3, 1.3, 64),
                     np.linspace(-1.3, 1.7, 41)):
            cov = PC.grid_coverage(P, grid, grid)
            assert float(cov.sum()) == pytest.approx(want, rel=1e-12), (
                f"n={n} grid={grid.size}")
    # the documented warning: a 60-gon is 1.827e-3 short of its circle
    n = 60
    assert 1 - (0.5 * n * np.sin(2 * np.pi / n)) / np.pi == pytest.approx(
        1.827e-3, rel=1e-3)


def test_K6_orientation_does_not_change_coverage():
    P = circle(37, 0.8, 0.1, -0.2)
    X = np.linspace(-1, 1, 19)
    a = PC.grid_coverage(P, X, X)
    b = PC.grid_coverage(P[::-1], X, X)
    assert np.allclose(a, b, rtol=EXACT, atol=EXACT)


def test_K7_vertex_rotation_does_not_change_coverage():
    """Relabelling where the ring starts is not a geometric change."""
    P = circle(29, 0.9, -0.05, 0.15)
    X = np.linspace(-1.1, 1.1, 23)
    base = PC.grid_coverage(P, X, X)
    for k in (1, 7, 28):
        assert np.allclose(PC.grid_coverage(np.roll(P, k, axis=0), X, X),
                           base, rtol=EXACT, atol=EXACT)


def test_K8_band_keeps_its_hole():
    outer, inner = circle(200, 1.0), circle(200, 0.6)
    X = np.linspace(-1.2, 1.2, 49)
    cov = PC.band_coverage(outer, inner, X, X)
    want = 0.5 * 200 * np.sin(2 * np.pi / 200) * (1 - 0.36)
    assert float(cov.sum()) == pytest.approx(want, rel=1e-12)
    centre = PC.band_coverage(outer, inner, np.array([-0.3, 0.3]),
                              np.array([-0.3, 0.3]))
    assert float(centre[0, 0]) == pytest.approx(0.0, abs=1e-12), (
        "the hole must stay empty, not be averaged over")


def test_K9_slivers_are_kept_and_are_not_negative():
    """A cell clipped to a hair of area must report that hair."""
    P = rect(0.0, 1.0, 0.0, 1e-9)
    X = np.linspace(0, 1, 11)
    Y = np.array([-1.0, 1.0])
    cov = PC.grid_coverage(P, X, Y)
    assert (cov >= 0).all()
    assert float(cov.sum()) == pytest.approx(1e-9, rel=1e-9)
    assert (cov[:, 0] > 0).all(), "no sliver may be dropped to zero"


def test_K10_disjoint_grid_gives_zero_and_enclosing_grid_gives_all():
    P = circle(50, 0.5, 5.0, 5.0)
    assert float(PC.grid_coverage(P, np.linspace(-1, 1, 5),
                                  np.linspace(-1, 1, 5)).sum()) == 0.0
    big = np.linspace(-10, 10, 3)
    assert float(PC.grid_coverage(P, big, big).sum()) == pytest.approx(
        abs(PC.signed_area(P)), rel=EXACT)


def test_K11_refining_the_grid_does_not_change_the_total():
    """Grid refinement is a bookkeeping change, not a measurement."""
    P = circle(77, 1.3, 0.07, -0.11)
    want = abs(PC.signed_area(P))
    for n in (3, 8, 33, 129, 512):
        X = np.linspace(-1.5, 1.5, n)
        assert float(PC.grid_coverage(P, X, X).sum()) == pytest.approx(
            want, rel=1e-12), f"n={n}"


def test_K12_self_intersection_is_detected():
    bow = np.array([[0, 0], [1, 1], [1, 0], [0, 1]], float)
    assert not PC.is_simple(bow)
    assert PC.is_simple(circle(9))
    assert PC.is_simple(np.array([[0, 0], [3, 0], [3, 3], [2, 3], [2, 1],
                                  [1, 1], [1, 3], [0, 3]], float))
