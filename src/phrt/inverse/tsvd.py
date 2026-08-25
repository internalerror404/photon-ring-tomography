"""Truncated SVD in reduced coordinates, with the dense reference it is checked against."""
from __future__ import annotations

import numpy as np

from phrt.inverse.reduced import ReducedOperator


def tsvd_from_statistic(op: ReducedOperator, b: np.ndarray,
                        rel_cut: float) -> np.ndarray:
    """x_hat from b = A^T y, keeping directions with sigma_i / sigma_max >= rel_cut.

    In terms of the usual formula x = sum_i v_i (u_i^T y) / s_i, the identity
    u_i^T y = (v_i^T b) / s_i turns the solve into a diagonal rescaling of the
    sufficient statistic, so no operator application is needed per solve.
    ``b`` may be a single vector or a stack of them, one per row.
    """
    keep = op.s >= rel_cut * op.s[0]
    if not keep.any():
        return np.zeros_like(np.atleast_2d(b))[0] if b.ndim == 1 \
            else np.zeros_like(b)
    inv = np.zeros_like(op.s)
    inv[keep] = 1.0 / op.s[keep] ** 2
    return (np.atleast_2d(b) @ op.V * inv) @ op.V.T if b.ndim > 1 else \
        op.V @ (inv * (op.V.T @ b))


def tsvd_dense(A: np.ndarray, y: np.ndarray, rel_cut: float) -> np.ndarray:
    """The explicit SVD formula, used only as the R0_G8 reference."""
    U, s, Vt = np.linalg.svd(A, full_matrices=False)
    keep = s >= rel_cut * s[0]
    if not keep.any():
        return np.zeros(A.shape[1])
    return Vt[keep].T @ ((U[:, keep].T @ y) / s[keep])
