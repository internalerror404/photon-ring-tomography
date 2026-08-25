"""The R0 depth surface, under AGE_INTERVAL_SEMANTICS_AMENDMENT_003.

The primary endpoint is anchored and its supremum is inside the probability.
The unanchored per-age-quantile interval is kept, but only as the secondary,
and these tests pin the difference so a later edit cannot quietly swap them.
"""
from __future__ import annotations

import numpy as np

from phrt.metrics.stable_depth import (anchored_depth_surface, quantile_pass,
                                       secondary_interval)

AGES = np.arange(0.0, 40.0, 4.0)          # 10 ages, 4 M apart


def cell(surface, eps, q):
    return next(c for c in surface
                if c["epsilon"] == eps and c["quantile"] == q)


def test_anchored_span_is_the_endpoint_minus_the_anchor():
    E = np.zeros((4, AGES.size))
    E[:, 6:] = 1.0                          # everything fails from 24 M on
    c = cell(anchored_depth_surface(AGES, E, [0.5], [0.9], 0.0, 36.0), 0.5, 0.9)
    assert c["T_stable_anchor"] == 20.0
    assert c["L_stable_anchor"] == 20.0
    assert c["a_anchor_M"] == 0.0


def test_a_positive_anchor_shifts_the_span_not_just_the_endpoint():
    E = np.zeros((4, AGES.size))
    E[:, 8:] = 1.0
    c = cell(anchored_depth_surface(AGES, E, [0.5], [0.9], 12.0, 36.0), 0.5, 0.9)
    assert c["T_stable_anchor"] == 28.0
    assert c["L_stable_anchor"] == 16.0     # 28 - 12, not 28


def test_the_supremum_is_inside_the_probability():
    """Two truths failing at different ages must not sum to a stable window.

    Per-age thresholding sees 50 % passing at every age and, at q = 0.5, calls
    the whole grid stable. The anchored definition asks whether the *same*
    truth is good across the whole window, and half of them are not.
    """
    E = np.zeros((2, AGES.size))
    E[0, 4:] = 1.0                          # truth A fails from 16 M
    E[1, :4] = 1.0                          # truth B fails before 16 M
    surf = anchored_depth_surface(AGES, E, [0.5], [0.5], 0.0, 36.0)
    c = cell(surf, 0.5, 0.5)
    assert c["T_stable_anchor"] == 12.0     # A alone carries the anchored window
    # the unanchored per-age statistic is the one that would have said 36
    per_age = quantile_pass(E <= 0.5, 0.5)
    assert per_age.all()
    assert c["secondary_reach_M"] == 36.0
    assert c["secondary_reach_M"] > c["T_stable_anchor"]


def test_the_secondary_run_is_reported_with_both_endpoints():
    stable = np.array([1, 1, 0, 0, 1, 1, 1, 1, 0, 0], dtype=bool)
    st = secondary_interval(AGES, stable, 0.0, 36.0)
    assert st["secondary_longest_run_start_M"] == 16.0
    assert st["secondary_longest_run_end_M"] == 28.0
    assert st["secondary_longest_run_span_M"] == 12.0
    assert st["secondary_span_from_anchor_M"] == 4.0
    assert st["n_passing_runs"] == 2
    assert "never depth from the present" in st["secondary_label"]


def test_right_censoring_is_flagged_not_hidden():
    E = np.zeros((4, AGES.size))
    c = cell(anchored_depth_surface(AGES, E, [0.5], [0.9], 0.0, 36.0), 0.5, 0.9)
    assert c["T_stable_anchor"] == 36.0
    assert c["right_censored"] is True


def test_failing_at_the_anchor_gives_no_anchored_depth():
    E = np.zeros((4, AGES.size))
    E[:, 0] = 1.0                           # nothing is good at the anchor
    c = cell(anchored_depth_surface(AGES, E, [0.5], [0.9], 0.0, 36.0), 0.5, 0.9)
    assert c["T_stable_anchor"] == -1.0
    assert c["L_stable_anchor"] == 0.0
    assert c["fraction_at_anchor"] == 0.0
    # but the unanchored run from 4 M on is real and is reported as such
    assert c["secondary_longest_run_span_M"] == 32.0


def test_the_surface_covers_every_cell():
    E = np.random.default_rng(0).random((8, AGES.size))
    surf = anchored_depth_surface(AGES, E, [0.25, 0.35, 0.5],
                                  [0.8, 0.9, 0.95], 0.0, 36.0)
    assert len(surf) == 9
    assert {(c["epsilon"], c["quantile"]) for c in surf} == {
        (e, q) for e in (0.25, 0.35, 0.5) for q in (0.8, 0.9, 0.95)}
