"""Near-null pairs at a targeted whitened Mahalanobis separation.

A pair is a common positive baseline movie plus and minus a signed perturbation
along a chosen coefficient direction. The perturbation amplitude is solved so
the realised separation

    delta = || A_C (x_+ - x_-) ||_2 = 2 |alpha| || A_C u ||_2

hits the target, and is then checked against the amplitude that keeps the
rendered intensity non-negative. Both numbers are recorded per pair: a target
that cannot be reached without driving the movie negative is a fact about the
experiment, not something to quietly rescale away.
"""
from __future__ import annotations

import numpy as np

from phrt.inverse.reduced import ReducedOperator


def direction_for_separation(op: ReducedOperator, rng, kind: str = "generic",
                             weak_op: ReducedOperator | None = None
                             ) -> np.ndarray:
    """A unit coefficient direction along which to separate a pair.

    ``generic`` draws isotropically. ``incremental_history`` picks a direction
    that is weak under ``weak_op`` -- the direct arm -- and as strong as
    possible under ``op``; that is the construction that tests whether the
    higher orders create discriminability the direct image does not have.
    """
    d = op.dimension
    if kind == "generic" or weak_op is None:
        u = rng.standard_normal(d)
        return u / np.linalg.norm(u)
    # maximise ||A u|| subject to ||A_weak u|| small: the generalised problem
    # (G + eps I)^-1 applied to the weak arm's least-determined directions
    ratio_basis = weak_op.V
    ratio_s = weak_op.s
    # take the weakest half of the direct arm's spectrum, then pick the
    # combination the resolved arm sees best
    k = max(1, ratio_s.size // 2)
    W = ratio_basis[:, -k:]
    M = W.T @ op.gram @ W
    w = np.linalg.eigh(M)[1][:, -1]
    u = W @ w
    return u / np.linalg.norm(u)


def realized_separation(op: ReducedOperator, delta_x: np.ndarray) -> float:
    """|| A_C delta_x ||_2 in the whitened metric."""
    return float(np.linalg.norm(op.s * (op.V.T @ delta_x)))


def amplitude_for_target(op: ReducedOperator, u: np.ndarray,
                         target: float) -> float:
    """alpha such that ||A_C (2 alpha u)|| == target."""
    per_unit = realized_separation(op, u)
    if per_unit <= 0:
        return float("inf")
    return float(target / (2.0 * per_unit))
