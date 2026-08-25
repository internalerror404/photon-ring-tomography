"""Coverage bookkeeping, including the honest NOT_APPLICABLE case."""
from __future__ import annotations

import numpy as np

from phrt.inverse.uncertainty import (central_interval_coverage,
                                      mahalanobis_calibration)

PROBABILISTIC = {"WIENER_GAUSSIAN", "LINEAR_STATE_SPACE"}
LEVELS = (0.50, 0.90, 0.95)


def coverage_rows(estimator: str, truth: np.ndarray, mean: np.ndarray,
                  cov: np.ndarray | None) -> list[dict]:
    """Coverage at the registered levels, or an explicit not-applicable row.

    TSVD and ridge have no posterior. Emitting a plug-in interval for them would
    manufacture an uncertainty statement the estimator does not make.
    """
    if estimator not in PROBABILISTIC or cov is None:
        return [{"estimator": estimator, "level": float(lv),
                 "coverage": float("nan"),
                 "disposition": "NOT_APPLICABLE",
                 "reason": "point estimator with no posterior covariance"}
                for lv in LEVELS]
    var = np.diag(cov)
    # coverage over every truth in the regime, not a single draw: a
    # per-coefficient rate estimated from one movie would be noise
    truth = np.atleast_2d(truth)
    mean = np.atleast_2d(mean)
    rows = [{"estimator": estimator, "level": float(lv),
             "coverage": central_interval_coverage(truth, mean, var[None, :], lv),
             "n_truths": int(truth.shape[0]),
             "disposition": "SUPPORTED", "reason": ""}
            for lv in LEVELS]
    joint = mahalanobis_calibration(truth, mean, cov)
    rows.append({"estimator": estimator, "level": float("nan"),
                 "coverage": float("nan"), "disposition": "SUPPORTED",
                 "reason": "joint chi-square calibration", **joint})
    return rows
