"""Whitening under a full output covariance, not its diagonal.

Ledger C04. ``PhysicalOperator.channel_variance`` returns one marginal
variance per row. That is exact for the two mixers the archive uses -- the
identity and the all-ones single-output sum -- because neither puts one input
order into two output channels. It is wrong the moment a mixer does: two
channels sharing an input share its noise, and a diagonal whitening treats
them as independent.

``C_L = L C L^T`` is formed and whitened as a whole. Where the mixed
covariance is singular, the stochastic support is whitened and the
deterministic directions are returned separately rather than discarded: a
noiseless linear constraint is information, and dropping it or hiding it under
a ridge would both be wrong.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class WhitenedSystem:
    """A whitened operator plus whatever the noise cannot reach."""

    B: np.ndarray                 # stochastic support, unit covariance
    exact: np.ndarray             # rows in the null space of C_L
    rank: int
    n_exact: int
    tol: float

    @property
    def information(self) -> float:
        """Frobenius information of the stochastic part alone."""
        return float(np.sum(self.B ** 2))


def mixed_covariance(L: np.ndarray, C: np.ndarray) -> np.ndarray:
    """C_L = L C L^T, symmetrised."""
    L, C = np.asarray(L, float), np.asarray(C, float)
    if C.ndim == 1:
        C = np.diag(C)
    M = L @ C @ L.T
    return 0.5 * (M + M.T)


def whiten(A: np.ndarray, C: np.ndarray, *, rtol: float = 1e-12
           ) -> WhitenedSystem:
    """C^{-1/2} A on the stochastic support; exact rows kept separately."""
    A = np.asarray(A, float)
    C = np.asarray(C, float)
    if C.ndim == 1:
        C = np.diag(C)
    if C.shape[0] != A.shape[0]:
        raise ValueError(f"covariance is {C.shape}, operator has "
                         f"{A.shape[0]} rows")
    w, V = np.linalg.eigh(0.5 * (C + C.T))
    if w.min() < -rtol * max(abs(w).max(), 1.0):
        raise ValueError("covariance is not positive semi-definite")
    tol = rtol * max(float(w.max()), 1.0)
    keep = w > tol
    B = (V[:, keep].T @ A) / np.sqrt(w[keep])[:, None]
    exact = V[:, ~keep].T @ A
    return WhitenedSystem(B=B, exact=exact, rank=int(keep.sum()),
                          n_exact=int((~keep).sum()), tol=float(tol))


def mixed_whiten(A: np.ndarray, L: np.ndarray, C: np.ndarray, *,
                 rtol: float = 1e-12) -> WhitenedSystem:
    """Apply a mixer to the operator and whiten under the mixed covariance."""
    return whiten(np.asarray(L, float) @ np.asarray(A, float),
                  mixed_covariance(L, C), rtol=rtol)
