"""Background estimation for the contrast model, in three declared regimes.

HMT-1 item 6. The contrast object is ``j = b + dj``, and how ``b`` is obtained
decides what a feature result means. Handing the exact background to the
reconstructor makes the problem easier in a way no observation could, so the
three regimes are kept apart and named:

``oracle_known``
    ``b`` supplied exactly. An upper-bound control. A result that exists only
    here is background-assisted, not unconditional.

``estimated_from_data``
    ``b`` estimated by a fixed low-order axisymmetric procedure from the arm's
    own data, before ``dj`` is touched. **This is the regime a paper-grade
    result has to survive**, and it is the only one whose estimate can be wrong
    in the way a real analysis would be wrong.

``joint_inversion``
    ``b`` and ``dj`` inferred together under separate constraints. Reported; it
    may support the estimated regime but cannot substitute for it.

The estimator is fixed here rather than chosen after seeing a residual, and its
own error is reported per regime so a feature result can be attributed to the
operator rather than to a lucky background.
"""
from __future__ import annotations

import numpy as np

from phrt.sources.physical_basis import radial_design

BACKGROUND_FLOOR = 1e-6
REGIMES = ("oracle_known", "estimated_from_data", "joint_inversion")


def axisymmetric_design(grid_r, grid_t, r_inner, r_outer, n_radial=4,
                        n_temporal=6, t_min=None, t_max=None) -> np.ndarray:
    """Low-order axisymmetric design: radial B-splines x smooth temporal modes.

    Deliberately poorer than the contrast class. A background model rich enough
    to absorb the fluctuation would make the split meaningless, so the temporal
    factor here is a handful of global cosines while ``dj`` lives on compact
    hats.
    """
    r = np.asarray(grid_r, float)
    t = np.asarray(grid_t, float)
    lo = float(t.min() if t_min is None else t_min)
    hi = float(t.max() if t_max is None else t_max)
    R = radial_design(r, r_inner, r_outer, n_radial)
    u = np.clip((t - lo) / max(hi - lo, 1e-30), 0.0, 1.0)
    T = np.column_stack([np.cos(np.pi * k * u) for k in range(n_temporal)])
    return (R[:, :, None] * T[:, None, :]).reshape(r.size, -1)


def estimate_from_field(values: np.ndarray, design: np.ndarray,
                        floor: float = BACKGROUND_FLOOR) -> tuple:
    """Least-squares axisymmetric fit, clipped to stay strictly positive.

    Clipping is recorded rather than silent: a background that had to be lifted
    is one whose estimate went unphysical, and the amount matters when reading
    the feature result that follows it.
    """
    v = np.asarray(values, float).ravel()
    coef, *_ = np.linalg.lstsq(design, v, rcond=None)
    b = design @ coef
    n_clipped = int((b < floor).sum())
    return np.maximum(b, floor), {"n_clipped": n_clipped,
                                  "clipped_fraction": n_clipped / max(b.size, 1),
                                  "min_before_clip": float(b.min())}


def oracle(b_true: np.ndarray) -> tuple:
    return np.asarray(b_true, float), {"n_clipped": 0, "clipped_fraction": 0.0,
                                       "min_before_clip": float(np.min(b_true))}


def joint(values: np.ndarray, design: np.ndarray, level_free: np.ndarray,
          n_iter: int = 12, floor: float = BACKGROUND_FLOOR) -> tuple:
    """Alternate between the axisymmetric background and the contrast residual.

    ``level_free`` projects out whatever the contrast class can already express,
    so the background is fitted to what is left rather than competing with the
    fluctuation for the same directions. Twelve sweeps, fixed in advance; the
    move is monotone in the residual and this is not a convergence claim.
    """
    v = np.asarray(values, float).ravel()
    b = np.full_like(v, float(np.mean(v)))
    info = {}
    for _ in range(n_iter):
        b, info = estimate_from_field(v - level_free @ (level_free.T @ (v - b)),
                                      design, floor)
    info["n_iterations"] = n_iter
    return b, info


def background_error(b_hat: np.ndarray, b_true: np.ndarray) -> dict:
    """How wrong the background was, so a feature result can be attributed."""
    a, t = np.asarray(b_hat, float), np.asarray(b_true, float)
    n = max(float(np.linalg.norm(t)), 1e-300)
    return {"relative_error": float(np.linalg.norm(a - t) / n),
            "max_absolute_error": float(np.abs(a - t).max()),
            "bias": float(np.mean(a - t)),
            "min_estimate": float(a.min())}
