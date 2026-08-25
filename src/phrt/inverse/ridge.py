"""Identity-penalty ridge, in reduced coordinates and dense reference form."""
from __future__ import annotations

import numpy as np

from phrt.inverse.reduced import ReducedOperator


def ridge_from_statistic(op: ReducedOperator, b: np.ndarray,
                         rel_lambda: float) -> np.ndarray:
    """x_hat = (G + lam I)^-1 b with lam = rel_lambda * lambda_max(G).

    b = A^T y always lies in the row space of A, so the component of the solve
    outside span(V) -- which would be b/lam -- is exactly zero and is not
    computed. Dropping it silently would be wrong for a general right-hand side;
    it is correct here because of where b comes from, and R0_G8 checks it.
    """
    lam = rel_lambda * op.s[0] ** 2
    inv = 1.0 / (op.s ** 2 + lam)
    return (np.atleast_2d(b) @ op.V * inv) @ op.V.T if b.ndim > 1 else \
        op.V @ (inv * (op.V.T @ b))


def ridge_dense(A: np.ndarray, y: np.ndarray, rel_lambda: float) -> np.ndarray:
    """Normal-equation reference for R0_G8."""
    G = A.T @ A
    lam = rel_lambda * float(np.linalg.eigvalsh(G)[-1])
    return np.linalg.solve(G + lam * np.eye(A.shape[1]), A.T @ y)
