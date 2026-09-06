"""The source-function metric, so a spectrum is not a statement about a basis.

Ledger C03. A singular value of ``C^{-1/2} A`` lives in coefficient
coordinates: rescale a basis function and the number moves while the physical
source does not. The archived localized probes are each normalized to unit L2
individually, which is not orthogonalization -- overlapping probes stay
overlapping, and the Gram is never formed.

Declare the model norm on the registered domain, form ``H_ij = <q_i, q_j>``,
factor ``H = R^T R`` and analyse ``A R^{-1}`` by triangular solve. This is a
chosen model norm on a nondimensional domain, not a claim about proper volume.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class SourceMetric:
    """The Gram of the declared source functions, and its factor."""

    H: np.ndarray
    R: np.ndarray                 # H = R^T R, upper triangular
    condition: float
    n_quadrature: int
    domain: str

    def to_physical(self, B: np.ndarray) -> np.ndarray:
        """B R^{-1} by triangular solve, never an explicit inverse."""
        from scipy.linalg import solve_triangular
        return solve_triangular(self.R, np.asarray(B, float).T,
                                lower=False, trans="T").T


def gram(values: np.ndarray, weights: np.ndarray) -> np.ndarray:
    """H_ij = sum_q w_q q_i(x_q) q_j(x_q), with the full cross terms kept."""
    V = np.asarray(values, float)          # (n_points, n_functions)
    w = np.asarray(weights, float)
    if V.shape[0] != w.size:
        raise ValueError(f"{V.shape[0]} sample points against {w.size} weights")
    H = V.T @ (w[:, None] * V)
    return 0.5 * (H + H.T)


def factor(H: np.ndarray, *, domain: str, n_quadrature: int,
           rtol: float = 1e-12) -> SourceMetric:
    """Cholesky where the Gram allows it, symmetric square root otherwise."""
    H = 0.5 * (np.asarray(H, float) + np.asarray(H, float).T)
    w = np.linalg.eigvalsh(H)
    if w.min() <= rtol * max(float(w.max()), 1.0):
        # Rank deficient or nearly so: report it rather than adding a ridge.
        raise ValueError(
            f"source Gram is singular to rtol={rtol:g} (min eigenvalue "
            f"{w.min():.3e} against max {w.max():.3e}). The declared functions "
            "are dependent on this domain; remove them with a certificate "
            "rather than regularizing the metric")
    R = np.linalg.cholesky(H).T
    return SourceMetric(H=H, R=R, condition=float(w.max() / w.min()),
                        n_quadrature=int(n_quadrature), domain=domain)
