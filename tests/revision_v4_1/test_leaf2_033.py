"""Sign-aware response envelopes, ruling 033. No physical query is made here."""
from __future__ import annotations

import importlib.util
import itertools
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from phrt.revision_v4_1 import fractional as FR                 # noqa: E402
from phrt.revision_v4_1 import leaf as LF                       # noqa: E402
from phrt.revision_v4_1 import leaf2 as L2                      # noqa: E402
from phrt.revision_v4_1 import measure as M                     # noqa: E402
from phrt.revision_v4_1.common_sky import DetectorGrid          # noqa: E402

HELPER = ROOT / ("docs/revisions/mahakal_v4_1/review033/"
                 "signed_bounds_and_checks_033.py")
HULL = ROOT / ("artifacts/revisions/mahakal_v4_1/G1C_20260907T075203Z_d252697"
               "/CLOSEOUT_ARRAYS_029.npz")
RAYMAP = ROOT / "artifacts/raymaps/a050_i050_n0_core.h5"


def helper():
    spec = importlib.util.spec_from_file_location("rev033", HELPER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def box(field, label, w=0.25, prov=L2.EXACT_VALUE):
    env = L2.point_envelope(np.array(field, float), np.array(label), prov)
    a = L2.assemble_bounds(np.array([0]), np.array([0]), np.array([w]), env, 1,
                           granularity=LF.LEAF_RULE)
    return float(a.lower.ravel()[0]), float(a.upper.ravel()[0])


# ---- S1: the defect the ruling named ----
def test_S1_negative_field_interval_is_not_the_032_box():
    lo, hi = box([-2.0], [LF.UNRESOLVED])
    assert (lo, hi) == (-0.5, 0.0)
    # the 032 construction: known + sum w |f|, with known = 0 here
    old_lo, old_hi = 0.0, 0.5
    assert not old_lo <= -0.5 <= old_hi, "the old box excluded a valid value"


def test_S1b_the_032_consumer_still_produces_the_old_box():
    """Version 1 is frozen and is shown to be the thing being replaced."""
    a = LF.assemble(np.array([0]), np.array([0]), np.array([0.25]),
                    np.array([LF.UNRESOLVED]), np.array([-2.0]), 1,
                    granularity=LF.LEAF_RULE)
    assert (float(a.lower.ravel()[0]), float(a.upper.ravel()[0])) == (0.0, 0.5)


# ---- S2: the nonnegative case it was right about is unchanged ----
def test_S2_nonnegative_field_case_is_preserved():
    assert box([2.0], [LF.UNRESOLVED]) == (0.0, 0.5)
    assert box([1.0], [LF.EMITTING]) == (0.25, 0.25)
    assert box([1.0], [LF.NOT_EMITTING]) == (0.0, 0.0)


def test_S2b_a_certain_negative_field_has_a_degenerate_interval():
    assert box([-2.0], [LF.EMITTING]) == (-0.5, -0.5)


# ---- S3: a magnitude bound is symmetric ----
def test_S3_magnitude_only_envelope_is_symmetric():
    env = L2.magnitude_envelope(np.array([2.0]), np.array([LF.UNRESOLVED]))
    a = L2.assemble_bounds(np.array([0]), np.array([0]), np.array([0.25]),
                           env, 1, granularity=LF.LEAF_RULE)
    assert (float(a.lower.ravel()[0]), float(a.upper.ravel()[0])) == (-0.5, 0.5)


# ---- S4: every indicator corner is inside the box ----
def test_S4_exhaustive_indicator_corners_are_enclosed():
    rows = np.array([0, 0, 1])
    cols = np.array([0, 1, 2])
    w = np.array([0.2, 0.3, 0.4])
    f = np.array([[-2.0, 3.0], [5.0, -1.0], [-4.0, -2.0]])
    env = L2.point_envelope(f, np.array([LF.UNRESOLVED] * 3))
    a = L2.assemble_bounds(rows, cols, w, env, 2, granularity=LF.LEAF_RULE)
    for bits in itertools.product((0.0, 1.0), repeat=3):
        y = np.zeros((2, 2))
        np.add.at(y, rows, w[:, None] * np.array(bits)[:, None] * f)
        assert a.encloses(y), f"corner {bits} escaped the enclosure"


# ---- S5: general signed intervals ----
def test_S5_random_points_inside_general_intervals_are_enclosed():
    rng = np.random.default_rng(33)
    rows = np.array([0, 0, 1])
    cols = np.array([0, 1, 2])
    w = np.array([0.2, 0.3, 0.4])
    fl = rng.uniform(-4, 1, (3, 2))
    fh = fl + rng.uniform(0, 5, (3, 2))
    env = L2.Envelope(np.array([0.0, 0.2, 0.4]), np.array([0.6, 0.9, 1.0]),
                      fl, fh, L2.VALIDATED_ENVELOPE)
    a = L2.assemble_bounds(rows, cols, w, env, 2, granularity=LF.LEAF_RULE)
    for _ in range(500):
        f = fl + rng.random((3, 2)) * (fh - fl)
        chi = env.chi_lo + rng.random(3) * (env.chi_hi - env.chi_lo)
        y = np.zeros((2, 2))
        np.add.at(y, rows, w[:, None] * chi[:, None] * f)
        assert a.encloses(y, atol=1e-14)


# ---- S6: a missing bound is a blocker, never a zero ----
def test_S6_non_finite_envelope_is_refused():
    env = L2.point_envelope(np.array([np.nan]), np.array([LF.UNRESOLVED]))
    with pytest.raises(L2.EnvelopeMissing, match="not a zero"):
        L2.assemble_bounds(np.array([0]), np.array([0]), np.array([1.0]),
                           env, 1, granularity=LF.LEAF_RULE)


def test_S6b_a_point_sample_is_not_an_envelope():
    env = L2.point_envelope(np.array([1.0]), np.array([LF.UNRESOLVED]),
                            L2.SAMPLE_ONLY)
    with pytest.raises(L2.EnvelopeMissing, match="not an envelope"):
        L2.assemble_bounds(np.array([0]), np.array([0]), np.array([1.0]),
                           env, 1, granularity=LF.LEAF_RULE)


# ---- S7: malformed inputs ----
def test_S7_reversed_and_out_of_range_intervals_are_refused():
    with pytest.raises(LF.LeafError, match="reversed"):
        L2.Envelope(np.array([0.0]), np.array([1.0]), np.array([[3.0]]),
                    np.array([[2.0]]), L2.VALIDATED_ENVELOPE).validate()
    with pytest.raises(LF.LeafError, match=r"\[0, 1\]"):
        L2.Envelope(np.array([0.0]), np.array([1.1]), np.array([[0.0]]),
                    np.array([[1.0]]), L2.VALIDATED_ENVELOPE).validate()
    env = L2.point_envelope(np.array([1.0]), np.array([LF.UNRESOLVED]))
    with pytest.raises(LF.LeafError, match="cannot be negative"):
        L2.assemble_bounds(np.array([0]), np.array([0]), np.array([-0.1]),
                           env, 1, granularity=LF.LEAF_RULE)
    with pytest.raises(LF.LeafError, match="cannot be negative"):
        L2.magnitude_envelope(np.array([-1.0]), np.array([LF.UNRESOLVED]))


def test_S7b_granularity_and_count_guards_carry_over():
    env = L2.point_envelope(np.array([1.0]), np.array([LF.UNRESOLVED]))
    with pytest.raises(LF.LeafError, match="refusing assembly"):
        L2.assemble_bounds(np.array([0]), np.array([0]), np.array([1.0]),
                           env, 1, granularity=LF.PARENT_FRACTION)
    a = L2.assemble_bounds(np.array([0]), np.array([0]), np.array([1.0]),
                           env, 1, granularity=LF.LEAF_RULE)
    with pytest.raises(LF.LeafError, match="NOT_EVALUATED"):
        L2.bind(a, {"found": 1})
    L2.bind(a, dict.fromkeys(LF.COUNT_FIELDS, 0))


# ---- S8: agreement with the reviewer's own utility ----
@pytest.mark.skipif(not HELPER.is_file(), reason="review helper not present")
def test_S8_agrees_with_the_reviewers_interval_utility():
    mod = helper()
    rng = np.random.default_rng(7)
    for _ in range(50):
        m, nd, nf = 6, 3, 2
        rows = rng.integers(0, nd, m)
        w = rng.uniform(0, 2, m)
        cl = rng.uniform(0, 1, m)
        ch = np.clip(cl + rng.uniform(0, 1, m), 0, 1)
        fl = rng.uniform(-5, 5, (m, nf))
        fh = fl + rng.uniform(0, 5, (m, nf))
        want_lo, want_hi = mod.interval_sum(rows, w, cl, ch, fl, fh, nd)
        env = L2.Envelope(cl, ch, fl, fh, L2.VALIDATED_ENVELOPE)
        got = L2.assemble_bounds(rows, np.arange(m), w, env, nd,
                                 granularity=LF.LEAF_RULE)
        assert np.allclose(got.lower, want_lo, rtol=1e-12, atol=1e-12)
        assert np.allclose(got.upper, want_hi, rtol=1e-12, atol=1e-12)


# ---- S9: production path on archived geometry ----
@pytest.mark.skipif(not (HULL.is_file() and RAYMAP.is_file()),
                    reason="archived geometry not present")
def test_S9_signed_field_enclosure_on_the_real_order_zero_band():
    """A signed field over the real band: the nominal response is enclosed."""
    from phrt.geometry.raymap import read

    rm = read(RAYMAP)
    grid = DetectorGrid(-25.0, 25.0, -25.0, 25.0, 0.4)
    hz = np.load(HULL)
    cells = M.build_ray_cells(rm.alpha, rm.beta, M.NODAL_DUAL_CLIPPED)
    ov = FR.triple_overlap(cells, grid, hz["tess_0e"], hz["tess_0i"])

    # a signed channel of the declared kind: a coordinate time measured
    # against an absolute reference is negative over part of the screen
    t = rm.coordinate_time
    finite = np.isfinite(t)
    f = np.where(finite, t - float(np.nanmedian(t)), np.nan)
    assert np.nanmin(f) < 0 < np.nanmax(f), "the field must change sign"
    assert not finite.all(), "this map does carry cells with no transfer value"

    rng = np.random.default_rng(1)
    label = np.where(rng.random(cells.alpha_lo.size) < 0.10, LF.UNRESOLVED,
                     np.where(rng.random(cells.alpha_lo.size) < 0.5,
                              LF.EMITTING, LF.NOT_EMITTING))
    env = L2.point_envelope(f, label)
    # a cell without a transfer value has no envelope, and that is a blocker
    with pytest.raises(L2.EnvelopeMissing):
        L2.assemble_bounds(ov.rows, ov.cols, ov.vals, env, grid.n_cells,
                           granularity=LF.LEAF_RULE)
    # the enclosure is then taken on the supported overlaps, and the
    # unsupported ones are carried as a count rather than as a zero
    keep = finite[ov.cols]
    unsupported = int(np.count_nonzero(~keep))
    assert unsupported > 0
    env = L2.point_envelope(np.where(finite, f, 0.0), label)
    ov_rows, ov_cols, ov_vals = ov.rows[keep], ov.cols[keep], ov.vals[keep]
    a = L2.assemble_bounds(ov_rows, ov_cols, ov_vals, env, grid.n_cells,
                           granularity=LF.LEAF_RULE)
    assert np.all(a.lower <= a.upper)
    # every realisation of the unresolved indicator lies inside the box
    for _ in range(20):
        chi = np.where(label == LF.EMITTING, 1.0,
                       np.where(label == LF.NOT_EMITTING, 0.0,
                                rng.random(label.size)))
        y = np.zeros((grid.n_cells, 1))
        np.add.at(y, ov_rows,
                  (ov_vals * chi[ov_cols] * f[ov_cols])[:, None])
        assert a.encloses(y, atol=1e-9)
    # and the 032 one-sided pile does not enclose every realisation. Take
    # the one that resolves every uncertain leaf to emitting: wherever the
    # field there is negative the true response drops BELOW the 032 lower
    # bound, which is fixed at the all-absent value.
    old = LF.assemble(ov_rows, ov_cols, ov_vals, label, np.where(finite, f, 0.0),
                      grid.n_cells, granularity=LF.LEAF_RULE)
    chi = np.where(label == LF.NOT_EMITTING, 0.0, 1.0)
    y = np.zeros((grid.n_cells, 1))
    np.add.at(y, ov_rows, (ov_vals * chi[ov_cols] * f[ov_cols])[:, None])
    assert a.encloses(y, atol=1e-9), "the sign-aware box must hold"
    escaped = int(np.count_nonzero((y < old.lower - 1e-9)
                                   | (y > old.upper + 1e-9)))
    assert escaped > 0, "on a signed field the 032 box must fail somewhere"


# ---- ruling 034: the error radius needs an explicit reference and norm ----
def test_S10_half_width_is_the_radius_about_the_midpoint_only():
    a = L2.BoundedAssembly(np.zeros((1, 1)), np.full((1, 1), 2.0))
    about_zero = L2.box_radius_about(a, np.zeros((1, 1)))
    about_mid = L2.box_radius_about(a, L2.midpoint(a))
    assert about_zero["per_channel_euclidean"][0] == 2.0
    assert about_mid["per_channel_euclidean"][0] == 1.0


def test_S10b_per_channel_and_joint_are_different_aggregations():
    a = L2.BoundedAssembly(-np.ones((1, 2)), np.ones((1, 2)))
    r = L2.box_radius_about(a, np.zeros((1, 2)))
    assert np.array_equal(r["per_channel_euclidean"], np.ones(2))
    assert r["joint_euclidean_over_the_whole_stack"] == pytest.approx(
        np.sqrt(2.0))
    # the 033 helper reduced this stack with a matrix one-norm, which is
    # neither figure
    assert float(np.linalg.norm(0.5 * (a.upper - a.lower), ord=1)) == 1.0


def test_S10c_the_reference_response_must_match_the_enclosure():
    a = L2.BoundedAssembly(np.zeros((2, 1)), np.ones((2, 1)))
    with pytest.raises(LF.LeafError, match="the response it is about"):
        L2.box_radius_about(a, np.zeros((3, 1)))
    with pytest.raises(L2.EnvelopeMissing):
        L2.box_radius_about(a, np.full((2, 1), np.nan))


def test_S10d_whitening_is_one_nonnegative_value_per_detector_row():
    a = L2.BoundedAssembly(np.zeros((2, 1)), np.ones((2, 1)))
    r = L2.box_radius_about(a, np.zeros((2, 1)), whitening=np.array([1.0, 3.0]))
    assert r["per_channel_euclidean"][0] == pytest.approx(np.sqrt(1.0 + 9.0))
    with pytest.raises(LF.LeafError, match="one nonnegative value"):
        L2.box_radius_about(a, np.zeros((2, 1)), whitening=np.array([-1.0, 1.0]))


def test_S10e_agrees_with_the_reviewers_box_helper():
    helper_mod = helper() if HELPER.is_file() else None
    if helper_mod is None:
        pytest.skip("review helper not present")
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "rev034", ROOT / "docs/revisions/mahakal_v4_1/review034/"
                        "response_checks_034.py")
    if not spec or not spec.loader:
        pytest.skip("034 helper not present")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    rng = np.random.default_rng(34)
    for _ in range(25):
        lo = rng.normal(size=(4, 3))
        hi = lo + rng.uniform(0, 2, (4, 3))
        nom = rng.normal(size=(4, 3))
        w = rng.uniform(0, 2, 4)
        per, joint = mod.box_radius_about(lo, hi, nom, w)
        got = L2.box_radius_about(L2.BoundedAssembly(lo, hi), nom, w)
        assert np.allclose(got["per_channel_euclidean"], per, rtol=1e-12)
        assert got["joint_euclidean_over_the_whole_stack"] == pytest.approx(
            joint, rel=1e-12)
