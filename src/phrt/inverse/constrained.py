"""Non-negativity-constrained contrast estimator.

HMT-1 item 11 requires a constrained estimator alongside the two classical
linear ones. The constraint that matters for this source model is physical
rather than statistical: the *total* emissivity ``b + dj`` cannot be negative,
even though ``dj`` alone is free to change sign.

Projected gradient on the whitened least-squares objective, with the projection
applied in field space where the constraint lives. It is iterative and cannot
reuse a cached spectral factorisation, which is why the freeze restricts it to
the primary SNR and the estimated-background regime rather than running it
everywhere and quietly dropping cells that got slow.
"""
from __future__ import annotations

import numpy as np


def solve(design: np.ndarray, gram_action, rhs: np.ndarray,
          background: np.ndarray, x0: np.ndarray, *, step: float,
          n_iter: int = 200, tol: float = 1e-10) -> tuple:
    """Minimise ||A x - y||^2 subject to design @ x >= -background.

    ``gram_action`` applies ``A^T A`` and ``rhs`` is ``A^T y``, so the caller
    keeps whatever factorisation it already has. The projection is a clip in
    field space followed by a least-squares pull back to coefficients: exact
    projection onto the feasible set of coefficients would be a QP, and this
    inexact but declared alternative is what runs.
    """
    D = np.asarray(design, float)
    b = np.asarray(background, float).ravel()
    x = np.asarray(x0, float).copy()
    Dpinv_rcond = 1e-12
    history = []
    for k in range(n_iter):
        grad = gram_action(x) - rhs
        x_new = x - step * grad
        field = D @ x_new
        viol = np.minimum(field + b, 0.0)
        if np.any(viol < 0.0):
            corrected = field - viol          # lift into the feasible set
            x_new, *_ = np.linalg.lstsq(D, corrected, rcond=Dpinv_rcond)
        move = float(np.linalg.norm(x_new - x) / max(np.linalg.norm(x), 1e-300))
        history.append(move)
        x = x_new
        if move < tol:
            break
    field = D @ x
    return x, {"n_iterations": k + 1, "final_relative_move": history[-1],
               "n_infeasible_points": int((field + b < -1e-9).sum()),
               "worst_violation": float(max(0.0, -(field + b).min()))}


def safe_step(sigma_max: float) -> float:
    """A step below the inverse Lipschitz constant of the quadratic."""
    return 1.0 / max(float(sigma_max) ** 2, 1e-300)
