"""Gaussian (Wiener) posterior under a prior fitted on the prior-fit families.

The prior is estimated only from truths in the prior-fit split. Fitting it on
anything a validation or test score is later read from would be leakage, so the
fit takes an explicit split label and the caller records it.

Shrinkage is a frozen grid parameter, not a fitted one: with 512 movies per
family and a coefficient dimension in the hundreds, the sample covariance is
poorly conditioned, and letting the data choose the shrinkage would be a second,
unregistered tuning loop.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from phrt.inverse.reduced import ReducedOperator


@dataclass(frozen=True)
class GaussianPrior:
    mean: np.ndarray
    covariance: np.ndarray
    shrinkage: float
    n_fit: int
    fit_split: str

    @property
    def precision(self) -> np.ndarray:
        return np.linalg.inv(self.covariance)


def fit_gaussian_prior(X: np.ndarray, shrinkage: float,
                       fit_split: str = "prior_fit_train") -> GaussianPrior:
    """Shrunk sample prior from coefficient vectors, one per row.

    Shrinks toward a scaled identity, the standard Ledoit-Wolf target, with the
    scale set by the average sample variance so the target is on the same scale
    as the data rather than an arbitrary unit.
    """
    X = np.atleast_2d(X)
    mu = X.mean(axis=0)
    Xc = X - mu
    S = (Xc.T @ Xc) / max(X.shape[0] - 1, 1)
    target = np.eye(S.shape[0]) * (np.trace(S) / S.shape[0])
    C = (1.0 - shrinkage) * S + shrinkage * target
    # a floor keeps the prior invertible when a direction is unexcited in the
    # fit set; without it the posterior would be undefined rather than merely
    # uninformative there
    floor = 1e-12 * max(float(np.trace(C)) / C.shape[0], 1e-300)
    C = C + floor * np.eye(C.shape[0])
    return GaussianPrior(mean=mu, covariance=C, shrinkage=shrinkage,
                         n_fit=int(X.shape[0]), fit_split=fit_split)


def wiener_from_statistic(op: ReducedOperator, b: np.ndarray,
                          prior: GaussianPrior):
    """Posterior mean and covariance from the sufficient statistic.

    y = A x + eta with eta ~ N(0, I) and x ~ N(mu, Sigma) gives
        posterior precision = Sigma^-1 + G
        posterior mean      = (Sigma^-1 + G)^-1 (Sigma^-1 mu + b)
    The covariance does not depend on the data, so it is returned once and
    reused across draws by the caller.
    """
    P = prior.precision
    M = P + op.gram
    cov = np.linalg.inv(M)
    rhs_prior = P @ prior.mean
    if b.ndim > 1:
        return (cov @ (b + rhs_prior).T).T, cov
    return cov @ (b + rhs_prior), cov


def wiener_dense(A: np.ndarray, y: np.ndarray, prior: GaussianPrior):
    """Dense Gaussian reference for R0_G8."""
    P = prior.precision
    M = P + A.T @ A
    cov = np.linalg.inv(M)
    return cov @ (A.T @ y + P @ prior.mean), cov
