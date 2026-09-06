"""What survives when the rest of the source is unknown.

Ledger C08. ``||B q||^2`` is a known-remainder quantity: it holds every other
source component fixed. The question this campaign asks is what remains
distinguishable when they are not, so the target response is residualized
against everything the nuisance can produce:

    B_cond = (I - U_n U_n^T) B_o R_o^{-1}

with ``U_n`` an orthonormal basis of the nuisance column space from a
rank-revealing factorization. No SNR cutoff and no ridge enter that projector:
either a direction is reachable by the nuisance or it is not, and softening
that decision would quietly hand back information the data does not contain.

The identity is never materialized; the projection is two thin products.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class ConditionalSpectrum:
    """Target information with and without the nuisance profiled out."""

    s_known: np.ndarray           # singular values of B_o
    s_conditional: np.ndarray     # singular values of B_cond
    nuisance_rank: int
    target_dimension: int
    rtol: float
    n_operational_known: int
    n_operational_conditional: int

    @property
    def information_known(self) -> float:
        return float(np.sum(self.s_known ** 2))

    @property
    def information_conditional(self) -> float:
        return float(np.sum(self.s_conditional ** 2))


def nuisance_basis(B_n: np.ndarray, rtol: float = 1e-12
                   ) -> tuple[np.ndarray, int]:
    """Orthonormal basis of col(B_n), by rank-revealing SVD."""
    B_n = np.asarray(B_n, float)
    if B_n.size == 0 or B_n.shape[1] == 0:
        return np.zeros((B_n.shape[0], 0)), 0
    U, s, _ = np.linalg.svd(B_n, full_matrices=False)
    if s.size == 0:
        return np.zeros((B_n.shape[0], 0)), 0
    keep = s > rtol * s[0]
    return U[:, keep], int(keep.sum())


def residualize(B_o: np.ndarray, U_n: np.ndarray) -> np.ndarray:
    """(I - U_n U_n^T) B_o without forming the identity."""
    B_o = np.asarray(B_o, float)
    if U_n.shape[1] == 0:
        return B_o.copy()
    return B_o - U_n @ (U_n.T @ B_o)


def conditional_spectrum(B_o: np.ndarray, B_n: np.ndarray, *,
                         rtol: float = 1e-12, rho: float = 1.0
                         ) -> ConditionalSpectrum:
    """Known-remainder and nuisance-adjusted spectra for one target block."""
    B_o = np.asarray(B_o, float)
    U_n, rank = nuisance_basis(B_n, rtol)
    B_cond = residualize(B_o, U_n)
    s_known = np.linalg.svd(B_o, compute_uv=False) if B_o.shape[1] else \
        np.zeros(0)
    s_cond = np.linalg.svd(B_cond, compute_uv=False) if B_cond.shape[1] else \
        np.zeros(0)
    return ConditionalSpectrum(
        s_known=s_known, s_conditional=s_cond, nuisance_rank=rank,
        target_dimension=int(B_o.shape[1]), rtol=float(rtol),
        n_operational_known=int(np.sum(s_known >= rho)),
        n_operational_conditional=int(np.sum(s_cond >= rho)))
