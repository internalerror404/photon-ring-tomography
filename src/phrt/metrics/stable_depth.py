"""Stable historical depth, and the reach/contiguity statistics beside it.

Three different questions, deliberately not collapsed into one number:

``T_reach``   the oldest age whose error clears the threshold at all -- a
              supremum, and so blind to holes, exactly as in the E3C v2 depth
              contract.
``T_contig``  the longest contiguous run of passing ages, which is the span a
              historical reconstruction could actually use.
``T_stable``  the oldest age up to which a *quantile* q of truths pass at
              tolerance epsilon, i.e. a statement about a population of movies
              rather than about one lucky draw.

Right-censoring is reported rather than hidden: a depth sitting on the last age
of the grid is a lower bound and is never emitted as an exact endpoint.
"""
from __future__ import annotations

import numpy as np


def passing_mask(errors: np.ndarray, epsilon: float) -> np.ndarray:
    """(n_truths, n_ages) boolean: normalized error at or below tolerance."""
    return np.asarray(errors) <= epsilon


def quantile_pass(mask: np.ndarray, q: float) -> np.ndarray:
    """Per-age fraction of truths passing, thresholded at the quantile level.

    An age counts as stable when at least a fraction ``q`` of truths pass there.
    """
    frac = mask.mean(axis=0)
    return frac >= q


def depth_statistics(ages: np.ndarray, stable: np.ndarray,
                     a_max: float) -> dict:
    """T_reach, T_contig and the censoring flag from a per-age pass mask."""
    ages = np.asarray(ages, float)
    ok = np.asarray(stable, bool)
    if not ok.any():
        return {"T_reach": -1.0, "T_contig": 0.0, "T_stable": -1.0,
                "contig_start_M": -1.0, "contig_end_M": -1.0,
                "n_passing_runs": 0, "is_contiguous": False,
                "right_censored": False,
                "age_pass_mask": "".join("0" for _ in ok)}
    idx = np.flatnonzero(ok)
    runs = np.split(idx, np.flatnonzero(np.diff(idx) > 1) + 1)
    spans = [(float(ages[r[0]]), float(ages[r[-1]])) for r in runs]
    lengths = [hi - lo for lo, hi in spans]
    k = int(np.argmax(lengths))
    reach = float(ages[idx[-1]])
    # T_stable is the depth of the run that starts at the present: history is
    # only usable if it connects back to now
    first_run = runs[0]
    t_stable = float(ages[first_run[-1]]) if ages[first_run[0]] <= ages[0] + 1e-9 \
        else 0.0
    return {"T_reach": reach,
            "T_contig": float(lengths[k]),
            "T_stable": t_stable,
            "contig_start_M": float(spans[k][0]),
            "contig_end_M": float(spans[k][1]),
            "n_passing_runs": len(runs),
            "is_contiguous": len(runs) == 1,
            "right_censored": bool(np.isclose(reach, a_max)),
            "age_pass_mask": "".join("1" if b else "0" for b in ok)}


def stable_depth_surface(ages: np.ndarray, errors: np.ndarray,
                         epsilons, quantiles, a_max: float) -> list[dict]:
    """The full (epsilon, q) surface, every cell reported."""
    out = []
    for eps in epsilons:
        mask = passing_mask(errors, eps)
        for q in quantiles:
            stats = depth_statistics(ages, quantile_pass(mask, q), a_max)
            out.append({"epsilon": float(eps), "quantile": float(q),
                        "n_truths": int(mask.shape[0]), **stats})
    return out
