"""The resolution-aware morphology measure. Items 15 and 16 of ruling 019."""
import numpy as np
import pytest

from phrt.metrics.feature_sets import cell_metric
from phrt.metrics.morphology import (aggregate_all_states, assignment_error,
                                     blended_error, dead_error, state_error)


@pytest.fixture(scope="module")
def axes():
    r = np.exp(np.linspace(np.log(1.87), np.log(50.0), 16))
    p = np.linspace(0.0, 2 * np.pi, 32, endpoint=False)
    return r, p, cell_metric(r, p)


def _blob(r, p, r0, sr, p0, sp, amp=1.0):
    dr = (r[:, None] - r0) / sr
    dp = ((p[None, :] - p0 + np.pi) % (2 * np.pi) - np.pi) / sp
    return amp * np.exp(-0.5 * (dr ** 2 + dp ** 2))


def test_a_perfect_reconstruction_scores_zero(axes):
    r, p, met = axes
    f = [{"r": 10.0, "phi": 1.0}, {"r": 30.0, "phi": 4.0}]
    assert assignment_error(f, f, met)["error"] == pytest.approx(0.0)


def test_finding_nothing_scores_the_worst_case(axes):
    r, p, met = axes
    f = [{"r": 10.0, "phi": 1.0}, {"r": 30.0, "phi": 4.0}]
    assert assignment_error(f, [], met)["error"] == pytest.approx(1.0)


def test_inventing_features_is_penalised(axes):
    """A method must not improve by reporting more features than exist."""
    r, p, met = axes
    truth = [{"r": 10.0, "phi": 1.0}]
    honest = assignment_error(truth, [{"r": 10.1, "phi": 1.02}], met)["error"]
    padded = assignment_error(
        truth, [{"r": 10.1, "phi": 1.02}, {"r": 40.0, "phi": 3.0}], met)["error"]
    assert padded > honest


def test_every_error_is_bounded(axes):
    r, p, met = axes
    a = [{"r": 2.0, "phi": 0.0}] * 3
    b = [{"r": 49.0, "phi": np.pi}] * 2
    assert 0.0 <= assignment_error(a, b, met)["error"] <= 1.0


def test_blended_error_is_zero_for_an_identical_field(axes):
    r, p, met = axes
    f = _blob(r, p, 12.0, 3.0, 2.0, 0.5)
    assert blended_error(f, f, r, p, met)["error"] == pytest.approx(0.0, abs=1e-12)


def test_blended_error_grows_as_the_centroid_moves(axes):
    r, p, met = axes
    f = _blob(r, p, 12.0, 3.0, 2.0, 0.5)
    near = blended_error(f, _blob(r, p, 13.0, 3.0, 2.1, 0.5), r, p, met)["error"]
    far = blended_error(f, _blob(r, p, 30.0, 3.0, 5.0, 0.5), r, p, met)["error"]
    assert far > near


def test_dead_states_are_scored_on_amplitude_only(axes):
    r, p, met = axes
    f = 1e-8 * _blob(r, p, 10.0, 2.0, 1.0, 0.4)
    assert dead_error(f, f)["error"] == pytest.approx(0.0)
    assert dead_error(f, 3.0 * f)["error"] > 0.0


def test_a_blended_state_is_never_scored_by_assignment(axes):
    """Item 16: blended states may not be forced into two-track scoring."""
    r, p, met = axes
    f = _blob(r, p, 12.0, 3.0, 2.0, 0.5)
    for label in ("BLENDED", "AMBIGUOUS"):
        out = state_error(label, f, f, [{"r": 12.0, "phi": 2.0}],
                          [{"r": 1.0, "phi": 0.0}] * 4, r, p, met)
        assert out["measure"] == "blended"
        assert out["error"] == pytest.approx(0.0, abs=1e-12)


def test_resolved_states_use_the_assignment_measure(axes):
    r, p, met = axes
    f = _blob(r, p, 12.0, 3.0, 2.0, 0.5)
    for label in ("SINGLE_RESOLVED", "MULTI_RESOLVED"):
        assert state_error(label, f, f, [{"r": 12.0, "phi": 2.0}],
                           [], r, p, met)["measure"] == "assignment"


def test_the_aggregate_drops_nothing_and_splits_by_kind():
    rows = [{"error": 0.1, "measure": "assignment"},
            {"error": 0.5, "measure": "blended"},
            {"error": 0.3, "measure": "blended"},
            {"error": 0.0, "measure": "amplitude"}]
    out = aggregate_all_states(rows)
    assert out["n_states"] == 4
    assert out["all_state_error"] == pytest.approx(0.225)
    assert out["n_blended"] == 2 and out["blended_error"] == pytest.approx(0.4)
    assert out["n_assignment"] == 1 and out["n_amplitude"] == 1


def test_the_aggregate_cannot_be_improved_by_dropping_hard_states():
    """The point of an all-state endpoint, stated as a test."""
    rows = [{"error": 0.1, "measure": "assignment"},
            {"error": 0.9, "measure": "blended"}]
    full = aggregate_all_states(rows)["all_state_error"]
    easy = aggregate_all_states(rows[:1])["all_state_error"]
    assert easy < full
