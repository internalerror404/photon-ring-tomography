"""Topography, set-valued features, and separable projection. HMT-2 stage 0."""
import numpy as np
import pytest

from phrt.metrics.feature_sets import (assignment, associate_tracks,
                                       blended_descriptors, cell_metric,
                                       distance, peaks_to_features)
from phrt.metrics.topography import classify, prominences, reconcile
from phrt.sources.localized_basis import LocalizedBasis
from phrt.sources.separable_projection import factors, project

R_IN, R_OUT, TLO, THI = 1.8660386527060988, 49.98205255591607, -128.82234649196255, 29.0


@pytest.fixture(scope="module")
def axes():
    r = np.exp(np.linspace(np.log(R_IN), np.log(R_OUT), 16))
    p = np.linspace(0.0, 2 * np.pi, 32, endpoint=False)
    return r, p


def _blob(r, p, r0, sr, p0, sp, amp=1.0):
    dr = (r[:, None] - r0) / sr
    dp = ((p[None, :] - p0 + np.pi) % (2 * np.pi) - np.pi) / sp
    return amp * np.exp(-0.5 * (dr ** 2 + dp ** 2))


def test_two_separated_blobs_are_multi_resolved(axes):
    r, p = axes
    f = _blob(r, p, 8.0, 1.5, 1.0, 0.4) + _blob(r, p, 30.0, 4.0, 4.0, 0.4, 0.8)
    c = classify(f, 2, float(f.max()), float(f.max()), 0.25)
    assert c["state"] == "MULTI_RESOLVED" and c["n_prominent"] == 2


def test_a_shoulder_is_blended_not_a_second_feature(axes):
    """The distinction the whole audit turns on."""
    r, p = axes
    f = _blob(r, p, 12.0, 4.0, 2.0, 0.6) + _blob(r, p, 14.0, 3.0, 2.4, 0.5, 0.08)
    c = classify(f, 2, float(f.max()), float(f.max()), 0.25)
    assert c["state"] == "BLENDED", c


def test_a_dead_age_is_dead(axes):
    r, p = axes
    f = 1e-6 * _blob(r, p, 10.0, 2.0, 1.0, 0.4)
    assert classify(f, 1, float(f.max()), 1.0, 0.25)["state"] == "DEAD"


def test_prominence_ranks_a_real_peak_above_a_bump(axes):
    r, p = axes
    f = _blob(r, p, 10.0, 2.0, 1.0, 0.4) + _blob(r, p, 32.0, 4.0, 4.0, 0.5, 0.5)
    idx, prom = prominences(f)
    assert prom[0] > prom[1] > 0
    assert len(idx) >= 2


def test_the_azimuthal_seam_does_not_create_a_peak(axes):
    """phi wraps; a blob straddling zero is one feature, not two."""
    r, p = axes
    f = _blob(r, p, 12.0, 3.0, 0.0, 0.5)
    c = classify(f, 1, float(f.max()), float(f.max()), 0.25)
    assert c["n_prominent"] == 1, c


def test_ambiguous_is_disagreement_between_levels():
    assert reconcile("MULTI_RESOLVED", "MULTI_RESOLVED") == "MULTI_RESOLVED"
    assert reconcile("MULTI_RESOLVED", "BLENDED") == "AMBIGUOUS"


def test_assignment_is_exact_and_symmetric_in_cost(axes):
    r, p = axes
    met = cell_metric(r, p)
    A = [{"r": 10.0, "phi": 1.0}, {"r": 30.0, "phi": 4.0}]
    B = [{"r": 30.2, "phi": 4.05}, {"r": 10.1, "phi": 1.02}]
    res = assignment(A, B, met)
    assert res["exact"] and res["cardinality_error"] == 0
    assert res["mean_matched_cells"] < 0.5
    assert set(res["pairs"]) == {(0, 1), (1, 0)}


def test_dropping_a_feature_is_not_free(axes):
    """A method must not score better by reporting fewer features."""
    r, p = axes
    met = cell_metric(r, p)
    A = [{"r": 10.0, "phi": 1.0}, {"r": 30.0, "phi": 4.0}]
    both = assignment(A, [{"r": 10.0, "phi": 1.0}, {"r": 30.0, "phi": 4.0}], met)
    one = assignment(A, [{"r": 10.0, "phi": 1.0}], met)
    assert one["unbalanced_cost"] > both["unbalanced_cost"]
    assert one["unbalanced_cost"] >= met["unmatched_cost"]


def test_empty_sets_are_handled(axes):
    r, p = axes
    met = cell_metric(r, p)
    assert assignment([], [], met)["unbalanced_cost"] == 0.0
    assert assignment([], [{"r": 5.0, "phi": 0.0}], met)["cardinality_error"] == 1


def test_blended_descriptors_describe_a_one_peak_field(axes):
    r, p = axes
    f = _blob(r, p, 12.0, 3.0, 2.0, 0.5)
    d = blended_descriptors(f, r, p)
    assert 8.0 < d["centroid_r"] < 18.0
    assert abs((d["centroid_phi"] - 2.0 + np.pi) % (2 * np.pi) - np.pi) < 0.3
    assert d["total_contrast"] > 0 and d["second_moment_rr"] > 0


def test_tracks_follow_a_moving_feature(axes):
    r, p = axes
    met = cell_metric(r, p)
    per_age = [[{"r": 12.0, "phi": 0.2 * k}] for k in range(6)]
    ids = associate_tracks(per_age, met)
    assert all(i == [0] for i in ids), ids


def test_separable_projection_equals_the_dense_one():
    """Exact, not an approximation, so the finest grid needs no dense design."""
    nr, npz, nt = 8, 16, 16
    r = np.exp(np.linspace(np.log(R_IN), np.log(R_OUT), nr))
    p = np.linspace(0.0, 2 * np.pi, npz, endpoint=False)
    t = np.linspace(TLO, THI, nt)
    R, P, T = np.meshgrid(r, p, t, indexing="ij")
    f = np.exp(-0.5 * ((R - 12) / 3.0) ** 2) * np.cos(P - 0.05 * T) + 0.3 * np.sin(2 * P)
    sep = project(f, factors(r, p, t, 4, 7, 16))
    b = LocalizedBasis(R_IN, R_OUT, TLO, THI, 4, 7, 16)
    D = b.design(R.ravel(), P.ravel(), T.ravel())
    keep = np.array([l["azimuthal_mode"] != 0 for l in b.labels()])
    coef, *_ = np.linalg.lstsq(D[:, keep], f.ravel(), rcond=None)
    dense = (D[:, keep] @ coef).reshape(f.shape)
    assert np.abs(sep - dense).max() / np.abs(dense).max() < 1e-10


def test_the_enriched_class_contains_the_current_one():
    """Nested in radius: enrichment adds resolution and removes nothing."""
    nr, npz, nt = 16, 32, 40
    r = np.exp(np.linspace(np.log(R_IN), np.log(R_OUT), nr))
    p = np.linspace(0.0, 2 * np.pi, npz, endpoint=False)
    t = np.linspace(TLO, THI, nt)
    R, P, T = np.meshgrid(r, p, t, indexing="ij")
    f = np.exp(-0.5 * ((R - 20) / 5.0) ** 2) * np.cos(P - 0.02 * T)
    small = project(f, factors(r, p, t, 4, 7, 16))
    big = project(f, factors(r, p, t, 8, 7, 16))
    # projecting the coarse class's output onto the rich class returns it
    again = project(small, factors(r, p, t, 8, 7, 16))
    assert np.abs(again - small).max() / np.abs(small).max() < 1e-8
    assert np.linalg.norm(f - big) <= np.linalg.norm(f - small) * (1 + 1e-9)
