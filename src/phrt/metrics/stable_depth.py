"""Stable historical depth under AGE_INTERVAL_SEMANTICS_AMENDMENT_003.

The primary endpoint is anchored:

    T_stable^anchor(eps, q) = sup { T >= a_anchor :
                                    Pr[ sup_{a_anchor <= a <= T} E(a) <= eps ] >= q }
    L_stable^anchor          = T_stable^anchor - a_anchor

with the supremum over the age window **inside** the probability, taken per
truth. A truth counts only if the whole window from the anchor out to T is good
for that truth. The pre-amendment implementation thresholded the per-age passing
fraction, which lets a different subset of truths fail at each age and still
calls the window stable; that quantity is retained below as the secondary
unanchored interval, reported with both endpoints and never called depth from
the present.

Right-censoring is reported rather than hidden: an endpoint sitting on the last
age of the grid is a lower bound and is never emitted as exact.
"""
from __future__ import annotations

import numpy as np

from phrt.metrics.age_intervals import anchored_stable_depth, interval_statistics


def passing_mask(errors: np.ndarray, epsilon: float) -> np.ndarray:
    """(n_truths, n_ages) boolean: normalized error at or below tolerance."""
    return np.asarray(errors) <= epsilon


def quantile_pass(mask: np.ndarray, q: float) -> np.ndarray:
    """Per-age fraction of truths passing, thresholded at the quantile level.

    The weaker, unanchored question. Kept because the interval structure of the
    per-age pass set is worth reporting, not because it is the depth.
    """
    return mask.mean(axis=0) >= q


def secondary_interval(ages: np.ndarray, stable: np.ndarray, a_anchor: float,
                       a_max: float) -> dict:
    """Interval structure of the per-age pass mask, all endpoints reported."""
    st = interval_statistics(ages, stable, a_anchor)
    reach = st["oldest_detectable_age_probe"]
    return {"secondary_reach_M": reach,
            "secondary_longest_run_span_M": st["longest_detectable_run_span_M"],
            "secondary_longest_run_start_M": st["longest_detectable_run_start_M"],
            "secondary_longest_run_end_M": st["longest_detectable_run_end_M"],
            "secondary_span_from_anchor_M":
                st["contiguous_detectable_span_from_anchor_M"],
            "secondary_end_from_anchor_M":
                st["contiguous_detectable_end_from_anchor_M"],
            "n_passing_runs": st["n_detectable_runs"],
            "is_contiguous": st["is_contiguous"],
            "secondary_right_censored": bool(reach >= 0
                                             and np.isclose(reach, a_max)),
            "age_pass_mask": st["age_mask"],
            "secondary_label": "unanchored; never depth from the present"}


def anchored_depth_surface(ages: np.ndarray, errors: np.ndarray, epsilons,
                           quantiles, a_anchor: float, a_max: float) -> list[dict]:
    """The full (epsilon, q) surface: anchored endpoint plus the secondary."""
    ages = np.asarray(ages, float)
    out = []
    for eps in epsilons:
        mask = passing_mask(errors, eps)
        for q in quantiles:
            a = anchored_stable_depth(ages, errors, float(eps), float(q), a_anchor)
            t = a["T_stable_anchor"]
            out.append({
                "epsilon": float(eps), "quantile": float(q),
                "n_truths": int(mask.shape[0]),
                "a_anchor_M": float(a_anchor),
                "T_stable_anchor": t,
                "L_stable_anchor": a["L_stable_anchor"],
                "fraction_at_anchor": a["fraction_at_anchor"],
                "right_censored": bool(t >= 0 and np.isclose(t, a_max)),
                **secondary_interval(ages, quantile_pass(mask, q), a_anchor, a_max)})
    return out
