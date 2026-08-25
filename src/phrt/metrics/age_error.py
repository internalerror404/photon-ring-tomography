"""Age-resolved reconstruction error.

The error is measured through a compact window in retarded age, applied to the
*source function*, not to the coefficient vector: a coefficient-space norm would
weight the classes' basis functions by an arbitrary normalisation and would not
be comparable between an in-class and an off-grid truth.

    E(a)     = ||W_a (xhat - x)||_2 / max(||W_a x||_2, eta)
    E_abs(a) = ||W_a (xhat - x)||_2

``eta`` is a frozen floor, not a per-truth one. A per-truth floor would make the
normalised error incomparable across truths and would flatter reconstructions of
faint epochs, which is exactly where the historical claim lives.
"""
from __future__ import annotations

import numpy as np


def age_window_weights(source_times: np.ndarray, age: float,
                       half_width: float) -> np.ndarray:
    """W_a as a Gaussian window on retarded age, centred at ``age``.

    ``source_times`` are the emission times of the evaluation points; the
    retarded age of a point observed at t_obs is ``t_obs - t_source``, and the
    caller passes the already-formed age axis.
    """
    return np.exp(-0.5 * ((source_times + age) / half_width) ** 2)


def windowed_norm(values: np.ndarray, weights: np.ndarray) -> float:
    return float(np.sqrt(np.sum((weights * values) ** 2)))


def age_error_curve(truth_values: np.ndarray, recon_values: np.ndarray,
                    window_stack: np.ndarray, eta: float) -> dict:
    """E(a) and E_abs(a) over a stack of windows, one row per age.

    ``window_stack`` has shape (n_ages, n_points); the values are the source
    function sampled at the same points for truth and reconstruction.
    """
    diff = recon_values - truth_values
    abs_err = np.sqrt(np.einsum("ap,p->a", window_stack ** 2, diff ** 2))
    truth_norm = np.sqrt(np.einsum("ap,p->a", window_stack ** 2,
                                   truth_values ** 2))
    rel = abs_err / np.maximum(truth_norm, eta)
    return {"absolute": abs_err, "normalized": rel, "truth_norm": truth_norm}


def freeze_eta(truth_norms: np.ndarray, fraction: float = 0.05) -> float:
    """eta = fraction * median over prior-fit truths and ages with ||W_a x|| > 0.

    Computed once, on the prior-fit split only, before any validation score is
    read. Recomputing it per regime would let a hard regime lower its own bar.
    """
    positive = truth_norms[truth_norms > 0.0]
    if positive.size == 0:
        return 1e-12
    return float(fraction * np.median(positive))
