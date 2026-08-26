"""Paired bootstrap whose resampling unit is the truth, not the truth-noise pair.

Noise draws sharpen the estimate of how one source history behaves; they do not
add source histories. Resampling draws independently would treat eight draws of
one truth as eight independent observations and shrink the interval by a factor
of the square root of eight for nothing. The cluster is the truth: when a truth
is drawn, every draw belonging to it comes with it.

The arms are paired by construction -- same truth, same coupled resolved noise
draw -- so a resample applies the same index set to both arms and the interval
is on their difference, not on two independent intervals that happen to overlap.

Everything here is exact rather than sampled twice over: a bootstrap resample is
a multinomial count vector over truths, so the whole ensemble of resamples is
one matrix product against the per-truth summaries. Ten thousand resamples cost
one matmul.
"""
from __future__ import annotations

import numpy as np


def running_max(errors: np.ndarray, ages: np.ndarray, a_anchor: float):
    """Per-row running supremum from the anchor outward, and the ages kept.

    The supremum inside the probability is what makes the anchored depth a
    statement about a usable stretch rather than about isolated ages, so it is
    taken once here and reused by every resample.
    """
    ages = np.asarray(ages, float)
    sel = ages >= a_anchor
    return np.maximum.accumulate(np.asarray(errors, float)[..., sel], axis=-1), \
        ages[sel]


def per_truth_pass_fraction(run_max: np.ndarray, epsilon: float) -> np.ndarray:
    """(n_truths, n_ages) fraction of a truth's draws whose window stays good.

    ``run_max`` is (n_truths, n_draws, n_ages) or (n_truths, n_ages).
    """
    ok = np.asarray(run_max) <= epsilon
    return ok.mean(axis=1) if ok.ndim == 3 else ok.astype(float)


def _counts(n_truths: int, n_resamples: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return rng.multinomial(n_truths, np.full(n_truths, 1.0 / n_truths),
                           size=n_resamples).astype(float)


def anchored_span_interval(pass_fraction_a: np.ndarray,
                           pass_fraction_b: np.ndarray, ages: np.ndarray,
                           q: float, a_anchor: float, n_resamples: int,
                           seed: int, level: float = 0.95) -> dict:
    """Interval on ``L_stable^anchor(b) - L_stable^anchor(a)``, paired by truth.

    ``a`` is the reference arm and ``b`` the arm under test, both given as
    per-truth pass fractions on the same truths in the same order.
    """
    n = pass_fraction_a.shape[0]
    if pass_fraction_b.shape[0] != n:
        raise ValueError("the two arms must be scored on the same truths")
    w = _counts(n, n_resamples, seed) / n

    def spans(pf):
        good = (w @ pf) >= q                       # (n_resamples, n_ages)
        # the qualifying set is a prefix, so the span is the last qualifying age
        any_good = good.any(axis=1)
        last = np.where(any_good, good.shape[1] - 1
                        - np.argmax(good[:, ::-1], axis=1), -1)
        out = np.where(any_good, ages[np.clip(last, 0, None)] - a_anchor, 0.0)
        return out

    sa, sb = spans(pass_fraction_a), spans(pass_fraction_b)
    d = sb - sa
    lo, hi = np.percentile(d, [100 * (1 - level) / 2, 100 * (1 + level) / 2])

    def point(pf):
        good = pf.mean(axis=0) >= q
        if not good.any():
            return 0.0
        return float(ages[np.flatnonzero(good)[-1]] - a_anchor)

    return {"point_estimate": point(pass_fraction_b) - point(pass_fraction_a),
            "span_reference": point(pass_fraction_a),
            "span_arm": point(pass_fraction_b),
            "ci_low": float(lo), "ci_high": float(hi), "level": level,
            "excludes_zero": bool(lo > 0.0),
            "n_truths": int(n), "n_resamples": int(n_resamples), "seed": int(seed),
            "unit": "truth; every noise draw of a resampled truth travels with it"}


def mean_difference_interval(per_truth_a: np.ndarray, per_truth_b: np.ndarray,
                             n_resamples: int, seed: int,
                             level: float = 0.95) -> dict:
    """Interval on ``mean(a) - mean(b)`` over truths, paired.

    Written as reference minus arm so that a positive value is an improvement
    for the arm, and the lower bound above zero is the thing to require.
    """
    a = np.asarray(per_truth_a, float)
    b = np.asarray(per_truth_b, float)
    n = a.size
    if b.size != n:
        raise ValueError("the two arms must be scored on the same truths")
    w = _counts(n, n_resamples, seed) / n
    d = w @ (a - b)
    lo, hi = np.percentile(d, [100 * (1 - level) / 2, 100 * (1 + level) / 2])
    return {"point_estimate": float(np.mean(a - b)),
            "mean_reference": float(np.mean(a)), "mean_arm": float(np.mean(b)),
            "ci_low": float(lo), "ci_high": float(hi), "level": level,
            "excludes_zero": bool(lo > 0.0),
            "n_truths": int(n), "n_resamples": int(n_resamples), "seed": int(seed),
            "unit": "truth"}
