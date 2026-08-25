"""AGE_INTERVAL_SEMANTICS_AMENDMENT_003.

The amendment exists because a span length is not a depth from the present.
These tests pin that distinction on the case that motivated it -- a detectable
island beyond a hole -- and on the case the ruling warns about, a long run that
never touches the anchor.
"""
from __future__ import annotations

import numpy as np
import pytest

from phrt.metrics.age_intervals import (admissible_anchor, anchored_stable_depth,
                                        interval_statistics)

AGES = np.arange(0.0, 40.0, 4.0)     # 10 ages, 4 M apart


def test_contiguous_from_anchor_agrees_with_reach_when_there_is_no_hole():
    s = interval_statistics(AGES, [1, 1, 1, 1, 0, 0, 0, 0, 0, 0], 0.0)
    assert s["oldest_detectable_age_probe"] == 12.0
    assert s["longest_detectable_run_span_M"] == 12.0
    assert s["contiguous_detectable_end_from_anchor_M"] == 12.0
    assert s["contiguous_detectable_span_from_anchor_M"] == 12.0
    assert s["is_contiguous"] is True


def test_island_beyond_a_hole_is_not_history_from_the_anchor():
    """The a098_i020 SPATIAL_ONLY case, in miniature."""
    s = interval_statistics(AGES, [1, 1, 1, 0, 0, 0, 0, 0, 1, 1], 0.0)
    assert s["oldest_detectable_age_probe"] == 36.0        # reach
    assert s["longest_detectable_run_span_M"] == 8.0       # longest run anywhere
    assert s["longest_detectable_run_start_M"] == 0.0
    assert s["longest_detectable_run_end_M"] == 8.0
    assert s["contiguous_detectable_end_from_anchor_M"] == 8.0
    assert s["n_detectable_runs"] == 2


def test_longest_run_may_not_touch_the_anchor_at_all():
    """The ruling's warning case: a long run entirely in the past.

    The longest run is 12 M, but nothing connects it to the present, so the
    anchored span must be zero rather than 12 M.
    """
    s = interval_statistics(AGES, [0, 0, 1, 1, 1, 1, 0, 0, 0, 0], 0.0)
    assert s["longest_detectable_run_span_M"] == 12.0
    assert s["longest_detectable_run_start_M"] == 8.0
    assert s["anchor_is_detectable"] is False
    assert s["contiguous_detectable_end_from_anchor_M"] == -1.0
    assert s["contiguous_detectable_span_from_anchor_M"] == 0.0


def test_anchor_is_derived_from_admissible_support_not_from_results():
    a = admissible_anchor(AGES, half_width=3.0, source_time_min=-200.0,
                          source_time_max=50.0)
    assert a["admissible"] and a["a_anchor_M"] == 0.0
    # a window that excludes the present pushes the anchor out, and says so
    b = admissible_anchor(AGES, half_width=3.0, source_time_min=-200.0,
                          source_time_max=-12.0)
    assert b["a_anchor_M"] > 0.0


def test_positive_anchor_shifts_the_span_but_not_the_endpoint():
    s = interval_statistics(AGES, [0, 0, 1, 1, 1, 1, 0, 0, 0, 0], 8.0)
    assert s["contiguous_detectable_end_from_anchor_M"] == 20.0
    assert s["contiguous_detectable_span_from_anchor_M"] == 12.0


def test_anchored_depth_takes_the_supremum_inside_the_probability():
    """The order of operations is the whole point of the amendment.

    Truth A is good early then bad; truth B is good throughout. At q = 0.5 the
    running-supremum rule must stop where A fails, because only B survives past
    it -- a per-age fraction rule would keep going.
    """
    E = np.array([[0.1] * 4 + [0.9] * 6,
                  [0.1] * 10])
    r = anchored_stable_depth(AGES, E, epsilon=0.5, q=1.0, a_anchor=0.0)
    assert r["T_stable_anchor"] == 12.0        # A fails from age 16 on
    r2 = anchored_stable_depth(AGES, E, epsilon=0.5, q=0.5, a_anchor=0.0)
    assert r2["T_stable_anchor"] == 36.0       # B alone carries q = 0.5


def test_anchored_depth_is_monotone_in_tolerance_and_antitone_in_quantile():
    rng = np.random.default_rng(0)
    E = rng.uniform(0.0, 1.0, (64, AGES.size))
    loose = anchored_stable_depth(AGES, E, 0.9, 0.5, 0.0)["T_stable_anchor"]
    tight = anchored_stable_depth(AGES, E, 0.2, 0.5, 0.0)["T_stable_anchor"]
    assert loose >= tight
    lowq = anchored_stable_depth(AGES, E, 0.5, 0.5, 0.0)["T_stable_anchor"]
    highq = anchored_stable_depth(AGES, E, 0.5, 0.95, 0.0)["T_stable_anchor"]
    assert lowq >= highq


def test_nothing_detectable_reports_no_depth_rather_than_zero_depth():
    s = interval_statistics(AGES, [0] * 10, 0.0)
    assert s["oldest_detectable_age_probe"] == -1.0
    assert s["contiguous_detectable_end_from_anchor_M"] == -1.0
    assert s["longest_detectable_run_span_M"] == 0.0
