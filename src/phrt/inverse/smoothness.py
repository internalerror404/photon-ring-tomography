"""Temporal Tikhonov: a first-difference penalty across the temporal basis index.

The class is a product basis, radial x azimuthal x temporal, flattened
radial-major. The penalty therefore acts on the temporal index within each
spatial block, and building it requires knowing that layout -- getting the
stride wrong would penalise across spatial modes instead and quietly change
what the estimator regularises.
"""
from __future__ import annotations

import numpy as np

from phrt.inverse.reduced import ReducedOperator


def temporal_difference_operator(n_radial: int, n_azimuthal: int,
                                 n_temporal: int) -> np.ndarray:
    """First differences along the temporal index, one block per spatial mode."""
    n_spatial = n_radial * n_azimuthal
    d = n_spatial * n_temporal
    rows = []
    for sp in range(n_spatial):
        base = sp * n_temporal
        for k in range(n_temporal - 1):
            r = np.zeros(d)
            r[base + k] = -1.0
            r[base + k + 1] = 1.0
            rows.append(r)
    return np.array(rows)


def tikhonov_from_statistic(op: ReducedOperator, b: np.ndarray,
                            rel_lambda: float, LtL: np.ndarray) -> np.ndarray:
    """x_hat = (G + lam L^T L)^-1 b, lam = rel_lambda * lambda_max(G).

    Unlike the identity penalty this does not diagonalise in the singular basis,
    so it is a dense solve in the coefficient dimension. That is cheap at d in
    the hundreds and is the honest way to do it.
    """
    G = op.gram
    lam = rel_lambda * op.s[0] ** 2
    M = G + lam * LtL
    if b.ndim > 1:
        return np.linalg.solve(M, b.T).T
    return np.linalg.solve(M, b)


def tikhonov_dense(A: np.ndarray, y: np.ndarray, rel_lambda: float,
                   L: np.ndarray) -> np.ndarray:
    """Augmented-system reference for R0_G8."""
    G = A.T @ A
    lam = rel_lambda * float(np.linalg.eigvalsh(G)[-1])
    aug = np.vstack([A, np.sqrt(lam) * L])
    rhs = np.concatenate([y, np.zeros(L.shape[0])])
    return np.linalg.lstsq(aug, rhs, rcond=None)[0]
