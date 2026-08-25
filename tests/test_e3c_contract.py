"""The E3C v2 contract helpers, exercised on cases that have bitten before.

The depth contract exists because a supremum cannot distinguish a history
detectable all the way back from a detectable island beyond a gap. These tests
pin that distinction rather than assuming the implementation preserves it.
"""
from __future__ import annotations

import numpy as np
import pytest

from phrt.audits.e3c_contract import (DISPOSITIONS, EXACT_RANK_VALUE,
                                      RESERVED_FOR_E3D, check_disposition,
                                      check_no_reserved_fields, detectability,
                                      restrict_spectrum)

AGES = np.arange(0.0, 40.0, 4.0)          # 10 ages, 4 M apart


def test_contiguous_set_agrees_with_the_supremum():
    d = detectability(AGES, [1, 1, 1, 1, 0, 0, 0, 0, 0, 0])
    assert d["oldest_detectable_age_probe"] == 12.0
    assert d["largest_contiguous_detectable_depth"] == 12.0
    assert d["detectable_set_is_contiguous"] is True
    assert d["n_detectable_runs"] == 1


def test_island_beyond_a_gap_is_where_the_two_differ():
    """The supremum says 36 M; only 8 M of history is actually usable."""
    d = detectability(AGES, [1, 1, 1, 0, 0, 0, 0, 0, 1, 1])
    assert d["oldest_detectable_age_probe"] == 36.0
    assert d["largest_contiguous_detectable_depth"] == 8.0
    assert d["largest_contiguous_start_M"] == 0.0
    assert d["largest_contiguous_end_M"] == 8.0
    assert d["detectable_set_is_contiguous"] is False
    assert d["n_detectable_runs"] == 2


def test_longest_run_wins_even_when_it_is_not_the_first():
    d = detectability(AGES, [1, 0, 0, 1, 1, 1, 1, 0, 0, 0])
    assert d["largest_contiguous_detectable_depth"] == 12.0
    assert d["largest_contiguous_start_M"] == 12.0
    assert d["largest_contiguous_end_M"] == 24.0


def test_nothing_detectable_is_reported_as_such():
    d = detectability(AGES, [0] * 10)
    assert d["oldest_detectable_age_probe"] == -1.0
    assert d["largest_contiguous_detectable_depth"] == 0.0
    assert d["n_detectable_runs"] == 0
    assert set(d["age_threshold_mask"]) == {"0"}


def test_mask_is_complete_and_aligned_with_the_grid():
    mask = [1, 0, 1, 1, 0, 0, 1, 0, 0, 1]
    d = detectability(AGES, mask)
    assert d["age_threshold_mask"] == "".join(str(b) for b in mask)
    assert len(d["age_threshold_mask"]) == AGES.size


def test_single_detectable_age_has_zero_contiguous_span():
    """One isolated point is not a recoverable span, and says so."""
    d = detectability(AGES, [0, 0, 1, 0, 0, 0, 0, 0, 0, 0])
    assert d["oldest_detectable_age_probe"] == 8.0
    assert d["largest_contiguous_detectable_depth"] == 0.0


def test_restrict_spectrum_strips_the_reserved_effective_dimension():
    raw = {"numerical_rank": 10, "operational_rank": 8, "nullity": 0,
           "sigma_max": 1.0, "sigma_min_positive": 0.1, "kappa_positive": 10.0,
           "stable_rank": 3.0, "trace_information": 5.0,
           "effective_rank": 4.2, "operational_nullity": 2}
    out = restrict_spectrum(raw, "C224")
    assert "effective_rank" not in out
    assert out["exact_rank"] == EXACT_RANK_VALUE
    assert out["structural_certificate"] is None
    assert out["source_class"] == "C224"
    assert out["operator_notation"] == "A_C = mathcal A Q_C"


def test_reserved_field_check_names_the_offender():
    check_no_reserved_fields(["a", "b"], "fine")
    for name in RESERVED_FOR_E3D:
        with pytest.raises(ValueError, match=name):
            check_no_reserved_fields(["a", name], "table")


def test_only_registered_dispositions_are_accepted():
    for d in DISPOSITIONS:
        assert check_disposition(d, "x") == d
    with pytest.raises(ValueError):
        check_disposition("PROBABLY_FINE", "x")
