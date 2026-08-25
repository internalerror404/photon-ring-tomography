"""AGE_INTERVAL_SEMANTICS_AMENDMENT_003.

Four distinct quantities that the earlier contract collapsed into one, and one
that it got subtly wrong.

``T_reach``
    the oldest detectable age. A supremum, blind to holes.

``longest_detectable_run_start_M`` / ``_end_M`` / ``_span_M``
    the longest detectable run anywhere on the grid, and its length. Useful, but
    *not* "depth from the present": at high inclination a single detectable
    interval can begin at a positive age, so a long run can sit entirely in the
    past with nothing connecting it to now. It is never labelled as continuous
    history from the anchor.

``contiguous_detectable_end_from_anchor_M`` / ``_span_M``
    the stretch that actually connects to the anchor, which is the only one that
    can be called history from the present.

``T_stable_anchor(epsilon, q)``
    the anchored continuous depth, and the one a reconstruction claim rests on:

        sup { T >= a_anchor :
              Pr[ sup_{a_anchor <= a <= T} E(a) <= epsilon ] >= q }

    Note the order of operations. The supremum over the age window is taken
    *inside* the probability, per truth: a truth counts only if the whole window
    from the anchor out to T is good for that truth. The earlier implementation
    thresholded the per-age passing fraction instead, which asks a weaker
    question -- it allows a different subset of truths to fail at each age and
    still calls the window stable.

``L_stable_anchor = T_stable_anchor - a_anchor``

The anchor is frozen from the admissible source and probe support before any
reconstruction result is observed, never from where the curves happen to look
good.
"""
from __future__ import annotations

import numpy as np


def admissible_anchor(ages: np.ndarray, half_width: float,
                      source_time_min: float, source_time_max: float,
                      n_sigma: float = 3.0) -> dict:
    """The youngest age whose probe is fully supported by the experiment.

    A probe centred at retarded age ``a`` occupies source times near ``-a``
    within ``n_sigma * half_width``. It is admissible when that support lies
    inside the reachable source-time window. Choosing the anchor this way makes
    it a property of the observation, fixed before any error curve exists.
    """
    ages = np.asarray(ages, float)
    lo = -ages - n_sigma * half_width
    hi = -ages + n_sigma * half_width
    ok = (lo >= source_time_min) & (hi <= source_time_max)
    idx = int(np.argmax(ok)) if ok.any() else -1
    return {"a_anchor_M": float(ages[idx]) if idx >= 0 else float("nan"),
            "admissible": bool(ok.any()),
            "n_sigma": n_sigma,
            "source_time_min_M": float(source_time_min),
            "source_time_max_M": float(source_time_max),
            "rule": "youngest age whose probe support lies inside the reachable "
                    "source-time window; frozen before any reconstruction result"}


def interval_statistics(ages: np.ndarray, mask, a_anchor: float) -> dict:
    """T_reach, the longest run and its endpoints, and the anchored run.

    ``mask`` is the per-age detectability or pass mask for a single curve.
    """
    ages = np.asarray(ages, float)
    ok = np.asarray(mask, bool)
    base = {"a_anchor_M": float(a_anchor),
            "age_mask": "".join("1" if b else "0" for b in ok)}
    if not ok.any():
        return {**base, "oldest_detectable_age_probe": -1.0,
                "longest_detectable_run_start_M": -1.0,
                "longest_detectable_run_end_M": -1.0,
                "longest_detectable_run_span_M": 0.0,
                "n_detectable_runs": 0, "is_contiguous": False,
                "contiguous_detectable_end_from_anchor_M": -1.0,
                "contiguous_detectable_span_from_anchor_M": 0.0,
                "anchor_is_detectable": False}
    idx = np.flatnonzero(ok)
    runs = np.split(idx, np.flatnonzero(np.diff(idx) > 1) + 1)
    spans = [(float(ages[r[0]]), float(ages[r[-1]])) for r in runs]
    lengths = [hi - lo for lo, hi in spans]
    k = int(np.argmax(lengths))

    # anchored run: the contiguous stretch containing the anchor, if any
    ai = int(np.argmin(np.abs(ages - a_anchor)))
    if ok[ai]:
        j = ai
        while j + 1 < ok.size and ok[j + 1]:
            j += 1
        t_anchor = float(ages[j])
        anchored = True
    else:
        t_anchor = -1.0
        anchored = False
    return {**base,
            "oldest_detectable_age_probe": float(ages[idx[-1]]),
            "longest_detectable_run_start_M": float(spans[k][0]),
            "longest_detectable_run_end_M": float(spans[k][1]),
            "longest_detectable_run_span_M": float(lengths[k]),
            "n_detectable_runs": len(runs),
            "is_contiguous": len(runs) == 1,
            "contiguous_detectable_end_from_anchor_M": t_anchor,
            "contiguous_detectable_span_from_anchor_M":
                max(0.0, t_anchor - a_anchor) if anchored else 0.0,
            "anchor_is_detectable": anchored}


def anchored_stable_depth(ages: np.ndarray, errors: np.ndarray, epsilon: float,
                          q: float, a_anchor: float) -> dict:
    """T_stable_anchor over a population of truths.

    ``errors`` is (n_truths, n_ages). For each candidate endpoint T the running
    supremum of E(a) over [a_anchor, T] is taken per truth, and T qualifies when
    the fraction of truths whose running supremum stays at or below epsilon is
    at least q. The running supremum is what makes this a statement about a
    usable stretch of history rather than about isolated ages.
    """
    ages = np.asarray(ages, float)
    E = np.atleast_2d(np.asarray(errors, float))
    sel = ages >= a_anchor
    if not sel.any():
        return {"epsilon": float(epsilon), "quantile": float(q),
                "a_anchor_M": float(a_anchor), "T_stable_anchor": -1.0,
                "L_stable_anchor": 0.0, "n_truths": int(E.shape[0]),
                "fraction_at_anchor": 0.0}
    a_sel = ages[sel]
    run_max = np.maximum.accumulate(E[:, sel], axis=1)
    frac = (run_max <= epsilon).mean(axis=0)
    good = frac >= q
    if not good.any():
        return {"epsilon": float(epsilon), "quantile": float(q),
                "a_anchor_M": float(a_anchor), "T_stable_anchor": -1.0,
                "L_stable_anchor": 0.0, "n_truths": int(E.shape[0]),
                "fraction_at_anchor": float(frac[0])}
    # the qualifying set is a prefix because the running supremum is monotone,
    # so the supremum is the last qualifying endpoint
    t = float(a_sel[np.flatnonzero(good)[-1]])
    return {"epsilon": float(epsilon), "quantile": float(q),
            "a_anchor_M": float(a_anchor), "T_stable_anchor": t,
            "L_stable_anchor": float(t - a_anchor),
            "n_truths": int(E.shape[0]),
            "fraction_at_anchor": float(frac[0])}


def anchored_surface(ages, errors, epsilons, quantiles, a_anchor) -> list[dict]:
    return [anchored_stable_depth(ages, errors, e, q, a_anchor)
            for e in epsilons for q in quantiles]


AMENDMENT = "AGE_INTERVAL_SEMANTICS_AMENDMENT_003"

# The pre-amendment names, kept here only so that a table or a row can be
# checked for their absence. Nothing may emit them again.
RETIRED_FIELDS = ("largest_contiguous_detectable_depth",
                  "largest_contiguous_start_M",
                  "largest_contiguous_end_M",
                  "best_mode_largest_contiguous_detectable_depth")


def observation_anchor(ages, half_width, observer_times, delay_windows,
                       n_sigma: float = 3.0) -> dict:
    """The anchor of one observation, from its reachable source-time window.

    A probe centred at age ``a`` sits at source time ``-a``. The source times an
    observation can reach at all are ``t_obs - delay``, so they run from
    ``min(t_obs) - max(delay)`` to ``max(t_obs) - min(delay)``. The minimum
    delay is what makes the young end non-trivial: at high inclination no photon
    in the frozen ray set leaves the source later than tens of M before the last
    observer sample, so the youngest fully supported probe centre is a positive
    age and the present is simply not observed. That is the case the amendment
    exists for, and it is recorded rather than rounded down to zero.

    ``delay_windows`` is the per-order ``[delay_min, delay_max]`` list the
    operator was built from.
    """
    t = np.asarray(observer_times, float)
    d_min = min(float(w[0]) for w in delay_windows)
    d_max = max(float(w[1]) for w in delay_windows)
    out = admissible_anchor(ages, half_width, float(t.min()) - d_max,
                            float(t.max()) - d_min, n_sigma)
    out.update({"delay_min_M": d_min, "delay_max_M": d_max,
                "observer_time_min_M": float(t.min()),
                "observer_time_max_M": float(t.max())})
    return out


def grid_anchor(anchors) -> dict:
    """The anchor admissible in every geometry of a grid: the oldest of them.

    Reported alongside the per-geometry anchors, never in place of them. A depth
    measured from each geometry's own anchor answers "how much continuous
    history from the youngest epoch this observation can see"; a depth measured
    from the grid anchor answers the same question on one common footing. They
    are different questions and both are stated.
    """
    vals = [float(a["a_anchor_M"]) for a in anchors]
    if not anchors or not all(a["admissible"] for a in anchors):
        return {"grid_anchor_M": float("nan"), "admissible": False,
                "n_geometries": len(anchors),
                "rule": "at least one geometry admits no fully supported probe "
                        "centre on the age grid"}
    return {"grid_anchor_M": float(max(vals)), "admissible": True,
            "n_geometries": len(anchors),
            "per_geometry_anchor_M": vals,
            "rule": "oldest of the per-geometry youngest admissible probe "
                    "centres, so it is admissible in every geometry; frozen "
                    "from the reachable source-time windows before any "
                    "detectability or reconstruction result was read"}


def amend_depth_row(row: dict, ages, a_anchor: float, prefix: str = "") -> dict:
    """Re-derive one stored depth row's interval statistics from its own mask.

    This is a rename plus two additions, and the cross-check is the point: the
    reach and the longest-run span it derives from ``age_threshold_mask`` must
    equal the values the row already carries under the retired names. If they
    do not, the mask and the summary disagree and the row is not reassemblable,
    which is a stop rather than something to paper over.
    """
    mask = row[f"{prefix}age_threshold_mask"]
    ages = np.asarray(ages, float)
    ok = np.array([c == "1" for c in mask], dtype=bool)
    if ok.size != ages.size:
        raise ValueError(f"mask length {ok.size} does not match age grid "
                         f"{ages.size}")
    st = interval_statistics(ages, ok, a_anchor)
    stored_reach = row.get(f"{prefix}oldest_detectable_age_probe")
    if stored_reach is not None and stored_reach >= 0 \
            and not np.isclose(st["oldest_detectable_age_probe"], stored_reach):
        raise ValueError(f"reach re-derived from the mask "
                         f"({st['oldest_detectable_age_probe']}) disagrees with "
                         f"the stored value ({stored_reach})")
    stored_span = row.get(f"{prefix}largest_contiguous_detectable_depth")
    if stored_span is not None and not np.isclose(
            st["longest_detectable_run_span_M"], stored_span):
        raise ValueError(f"longest-run span re-derived from the mask "
                         f"({st['longest_detectable_run_span_M']}) disagrees "
                         f"with the stored value ({stored_span})")
    out = {k: v for k, v in row.items() if k not in RETIRED_FIELDS}
    out.update({
        f"{prefix}a_anchor_M": float(a_anchor),
        f"{prefix}longest_detectable_run_span_M":
            st["longest_detectable_run_span_M"],
        f"{prefix}longest_detectable_run_start_M":
            st["longest_detectable_run_start_M"],
        f"{prefix}longest_detectable_run_end_M":
            st["longest_detectable_run_end_M"],
        f"{prefix}contiguous_detectable_end_from_anchor_M":
            st["contiguous_detectable_end_from_anchor_M"],
        f"{prefix}contiguous_detectable_span_from_anchor_M":
            st["contiguous_detectable_span_from_anchor_M"],
        f"{prefix}anchor_is_detectable": st["anchor_is_detectable"],
        f"{prefix}n_detectable_runs": st["n_detectable_runs"],
        "age_interval_amendment": AMENDMENT})
    return out
