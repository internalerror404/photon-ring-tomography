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

    Two normalisations, because the obvious one is misleading here. Every
    physical family sits on a positive constant baseline, and a constant is
    exactly representable in the class, so a residual taken relative to the full
    movie norm is dominated by a part that is in-class by construction: a
    strongly off-grid localized feature can still show a relative residual of a
    per cent or less. ``relative_projection_residual_structure`` divides instead
    by the norm of the fluctuation about the mean, which is the part the class
    is actually being asked to represent, and is the number the off-grid regime
    should be judged on.
    """
    coef, *_ = np.linalg.lstsq(design, values, rcond=None)
    resid = values - design @ coef
    r_norm = float(np.linalg.norm(resid))
    full = max(float(np.linalg.norm(values)), 1e-300)
    fluct = max(float(np.linalg.norm(values - values.mean())), 1e-300)
    return {"relative_projection_residual": r_norm / full,
            "relative_projection_residual_structure": r_norm / fluct,
            "fluctuation_fraction": fluct / full,
            "is_degenerate_constant": bool(fluct / full < 1e-9),
            "projected_coefficients": coef}
