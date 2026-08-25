"""The E3D class ladder must be nested, and 'nested' must mean something exact.

C224 -> C448_T -> C528_S -> C1056_ST enrich the temporal and spatial factors.
The azimuthal and temporal factors are literal prefixes, so their columns are
preserved. The radial factor is a cubic B-spline basis, and refining it moves
the knots: the individual columns are NOT preserved, but the function space is
nested. Rank and Gram-monotonicity statements depend on the space nesting, not
on the columns, so that is what is asserted -- and the distinction is written
down here so a later reader is not misled by the word 'nested'.
"""
from __future__ import annotations

import numpy as np

from phrt.sources.physical_basis import (azimuthal_design, radial_design,
                                         temporal_design)

R_IN, R_OUT, T_MIN, T_MAX = 2.0, 50.0, -160.0, 30.0


def _projection_residual(small: np.ndarray, large: np.ndarray) -> float:
    """Max residual of projecting the smaller design onto the larger's span."""
    Q, _ = np.linalg.qr(large)
    return float(np.abs(small - Q @ (Q.T @ small)).max())


def test_azimuthal_enrichment_preserves_columns():
    phi = np.linspace(0.0, 2 * np.pi, 401, endpoint=False)
    assert np.array_equal(azimuthal_design(phi, 11)[:, :7], azimuthal_design(phi, 7))


def test_temporal_enrichment_preserves_columns():
    t = np.linspace(T_MIN, T_MAX, 401)
    assert np.array_equal(temporal_design(t, T_MIN, T_MAX, 16)[:, :8],
                          temporal_design(t, T_MIN, T_MAX, 8))


def test_radial_enrichment_nests_the_space_not_the_columns():
    r = np.linspace(R_IN, R_OUT, 601)
    small, large = radial_design(r, R_IN, R_OUT, 4), radial_design(r, R_IN, R_OUT, 6)
    # the space is nested ...
    assert _projection_residual(small, large) < 1e-10
    # ... and the columns are not preserved, which is why the test says so
    assert not np.allclose(large[:, :4], small)


def test_enriched_space_strictly_contains_the_registered_one():
    r = np.linspace(R_IN, R_OUT, 601)
    small, large = radial_design(r, R_IN, R_OUT, 4), radial_design(r, R_IN, R_OUT, 6)
    assert np.linalg.matrix_rank(large) > np.linalg.matrix_rank(small)
    assert _projection_residual(large, small) > 1e-3
