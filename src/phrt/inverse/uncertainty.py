"""Coverage and calibration for the probabilistic estimators.

Only the Gaussian posterior estimators have a covariance to check. Reporting a
coverage number for TSVD or ridge would be inventing one, so those are recorded
as NOT_APPLICABLE rather than filled with a plug-in interval.
"""
from __future__ import annotations

import numpy as np
from scipy import stats


def central_interval_coverage(truth: np.ndarray, mean: np.ndarray,
                              variance: np.ndarray, level: float) -> float:
    """Fraction of coefficients whose truth falls in the central interval.

    Marginal, per-coefficient coverage: it checks the diagonal of the posterior
    covariance, not its correlations. Stated because a marginally calibrated
    posterior can still be badly calibrated jointly.
    """
    z = stats.norm.ppf(0.5 + level / 2.0)
    sd = np.sqrt(np.maximum(variance, 0.0))
    inside = np.abs(truth - mean) <= z * np.maximum(sd, 1e-300)
    return float(np.mean(inside))


def mahalanobis_calibration(truth: np.ndarray, mean: np.ndarray,
                            cov: np.ndarray) -> dict:
    """Joint check: (x - mu)^T Sigma^-1 (x - mu) should be chi-square_d.

    This is the calibration statement that matters for a posterior used to make
    a historical claim, because it is sensitive to the correlations that the
    marginal coverage above ignores.
    """
    d = mean.shape[-1]
    diff = np.atleast_2d(truth - mean)
    # The posterior covariance is PD in exact arithmetic but is formed by
    # inverting a near-singular shrunk prior plus a Gram, so a Cholesky can and
    # does fail on directions the data and prior barely constrain. An
    # eigendecomposition with a relative floor is used instead, and the number
    # of clipped directions is reported: silently jittering the diagonal would
    # hide how much of the posterior is numerically unsupported, which is
    # exactly what a calibration statement should not do.
    C = 0.5 * (cov + cov.T)
    w, U = np.linalg.eigh(C)
    scale = max(float(w.max()), 1e-300)
    floor = 1e-12 * scale
    clipped = int(np.sum(w < floor))
    w = np.maximum(w, floor)
    z = (diff @ U) / np.sqrt(w)
    m2 = np.sum(z ** 2, axis=1)
    dof = int(np.sum(w > floor))
    return {"mean_mahalanobis_squared": float(np.mean(m2)),
            "expected_mahalanobis_squared": float(d),
            "ratio": float(np.mean(m2) / max(d, 1)),
            "median_pvalue": float(np.median(stats.chi2.sf(m2, df=d))),
            "clipped_directions": clipped,
            "numerically_supported_directions": dof}
