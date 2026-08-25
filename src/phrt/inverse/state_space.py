"""Linear-Gaussian random-walk prior across the temporal basis index.

What this is, stated precisely so it is not mistaken for a filter: the
observation couples every temporal mode at once, because each ray samples the
source at its own retarded time and the temporal factor is a set of global DCT
modes. There is therefore no sequential observation to filter, and no
Kalman/RTS recursion applies to the data. What *is* sequential is the prior: a
random walk across the temporal index k, which accumulates as a tridiagonal
precision block per spatial mode.

The estimator is consequently the batch linear-Gaussian solution under that
prior. ``R0_G8`` checks two things: that the sequentially accumulated precision
equals the batch precision, and that the resulting estimate equals the dense
Gaussian solve. Calling it a state-space model without saying which part is
sequential would overstate it.
"""
from __future__ import annotations

import numpy as np

from phrt.inverse.reduced import ReducedOperator


def random_walk_precision(n_radial: int, n_azimuthal: int, n_temporal: int,
                          process_noise: float,
                          initial_variance: float = 1e6) -> np.ndarray:
    """Precision of a random walk over the temporal index, per spatial mode.

    Built by accumulating one transition at a time, which is the sequential
    construction the gate compares against a directly formed tridiagonal.
    """
    n_spatial = n_radial * n_azimuthal
    d = n_spatial * n_temporal
    P = np.zeros((d, d))
    q = 1.0 / max(process_noise, 1e-300)
    for sp in range(n_spatial):
        base = sp * n_temporal
        P[base, base] += 1.0 / initial_variance
        for k in range(n_temporal - 1):
            i, j = base + k, base + k + 1
            P[i, i] += q
            P[j, j] += q
            P[i, j] -= q
            P[j, i] -= q
    return P


def state_space_from_statistic(op: ReducedOperator, b: np.ndarray,
                               precision: np.ndarray):
    """Batch linear-Gaussian posterior under the random-walk prior."""
    M = precision + op.gram
    cov = np.linalg.inv(M)
    if b.ndim > 1:
        return (cov @ b.T).T, cov
    return cov @ b, cov


def state_space_dense(A: np.ndarray, y: np.ndarray,
                      precision: np.ndarray):
    """Dense reference for R0_G8."""
    M = precision + A.T @ A
    cov = np.linalg.inv(M)
    return cov @ (A.T @ y), cov
