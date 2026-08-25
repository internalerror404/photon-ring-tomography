"""Off-grid truths: rendered analytically, deliberately outside span(C224).

An off-grid truth is the same physical family with its feature scales refined
by the frozen factor, so the structure is finer than the class can represent.
It is evaluated directly at the ray coordinates and never projected onto the
class first -- projecting it would make it in-class by construction and destroy
the thing the regime is meant to measure.

The projection residual is computed and recorded so "off-grid" is a measured
property of each truth rather than a label.
"""
from __future__ import annotations

import numpy as np


def projection_residual(values: np.ndarray, design: np.ndarray) -> dict:
    """How much of a rendered movie lies outside the span of the class.

    ``design`` is the class design matrix evaluated at the same coordinates.
    Returns the relative L2 residual of the least-squares projection, which is
    zero for an in-class truth and strictly positive for a genuinely off-grid one.
    """
    coef, *_ = np.linalg.lstsq(design, values, rcond=None)
    resid = values - design @ coef
    denom = max(float(np.linalg.norm(values)), 1e-300)
    return {"relative_projection_residual": float(np.linalg.norm(resid) / denom),
            "projected_coefficients": coef}
