"""Reduced-coordinate simulation of a whitened linear-Gaussian experiment.

For a whitened operator ``A`` (so the noise is ``N(0, I)``), every estimator used
in this pilot -- TSVD, ridge, temporal Tikhonov, the Wiener posterior mean, and
the batch linear-Gaussian smoother -- depends on the data only through the
sufficient statistic

    b = A^T y = G x + xi,     G = A^T A,     xi = A^T eta ~ N(0, G).

Working in ``b`` instead of ``y`` is exact, not an approximation: ``A^T y`` is a
sufficient statistic for ``x`` in the Gaussian model, and the estimators are
functions of it. It replaces an ``n_rows``-dimensional simulation (36 864 rows
for the resolved arm) with a ``d``-dimensional one (224), which is what makes a
pilot of this size run at all.

The reduction has one trap worth stating: ``xi`` is *not* white. Its covariance
is ``G``, so sampling it as ``V S z`` with ``z ~ N(0, I_d)`` is required, and
sampling white noise in coefficient space instead would quietly make every arm
look better conditioned than it is. ``R0_G12`` checks the reduction against a
full-space simulation on the smoke instance rather than trusting this note.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class ReducedOperator:
    """The SVD of a whitened restricted operator ``A_C``, plus derived pieces.

    ``A_C = U diag(s) V^T`` with ``V`` of shape ``(d, k)``. Everything the
    estimators need is a function of ``(s, V)``; ``U`` is never materialised
    because no estimator here depends on it.
    """

    s: np.ndarray           # singular values, descending, length k
    V: np.ndarray           # right singular vectors, (d, k)
    dimension: int          # d
    n_rows: int             # rows of A_C, recorded for reporting only
    arm: str = ""

    @property
    def gram(self) -> np.ndarray:
        return (self.V * self.s ** 2) @ self.V.T

    def forward_statistic(self, x: np.ndarray) -> np.ndarray:
        """G x, the clean part of the sufficient statistic."""
        return self.V @ (self.s ** 2 * (self.V.T @ x))

    def noise_statistic(self, rng: np.random.Generator,
                        size: int = 1) -> np.ndarray:
        """Draws of xi = A^T eta ~ N(0, G), as (size, d).

        Sampled as V diag(s) z with z ~ N(0, I_k), which reproduces the exact
        covariance V s^2 V^T. Drawing white noise in coefficient space would be
        the wrong distribution and would flatter every arm.
        """
        z = rng.standard_normal((size, self.s.size))
        return (z * self.s) @ self.V.T

    def project_data_weak(self, snr0: float, rho: float = 1.0):
        """(P_data, P_weak) at this SNR, as the index set and its complement.

        Returned as boolean masks over the singular directions rather than dense
        projectors, because d can be 1056 and the masks are what the callers
        actually need.
        """
        keep = (snr0 * self.s) >= rho
        return keep, ~keep


def reduce_operator(A: np.ndarray, arm: str = "") -> ReducedOperator:
    """SVD of a dense whitened operator, dropping exactly-zero directions."""
    U, s, Vt = np.linalg.svd(A, full_matrices=False)
    keep = s > 0.0
    return ReducedOperator(s=s[keep], V=Vt[keep].T, dimension=A.shape[1],
                           n_rows=A.shape[0], arm=arm)
