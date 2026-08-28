"""G10c: the independent windowed reference, and proof it can fail."""
import numpy as np
import pytest

from phrt.metrics.features import age_maps, extract
from phrt.metrics.windowed_reference import (local_maxima, peak_agreement,
                                             window_stack, windowed_peak)
from phrt.sources.contrast import FAMILIES, OFF_MANIFOLD, build

SPIN, R_IN, R_OUT = 0.5, 1.8660386527060988, 49.98205255591607
TLO, THI = -128.82234649196255, 29.0
NR, NP, NT = 16, 32, 40
HALF = 3.0


@pytest.fixture(scope="module")
def grid():
    r = np.exp(np.linspace(np.log(R_IN), np.log(R_OUT), NR))
    phi = np.linspace(0.0, 2 * np.pi, NP, endpoint=False)
    t = np.linspace(TLO, THI, NT)
    R, P, T = np.meshgrid(r, phi, t, indexing="ij")
    ti = np.tile(np.arange(NT), NR * NP)
    return r, phi, t, R.ravel(), P.ravel(), T.ravel(), ti


def _build(grid, family, seed=0):
    r, phi, t, gr, gp, gt, ti = grid
    return build(np.random.default_rng(seed), family, SPIN, R_IN, R_OUT,
                 gr, gp, gt, ti, NT)


def test_the_reference_window_is_the_extractor_window(grid):
    """Sharing the window is required; sharing code is not.

    The reference must measure the extractor's accuracy, not the difference
    between two different windows, so the two definitions have to agree
    numerically even though neither imports the other.
    """
    r, phi, t, gr, gp, gt, ti = grid
    ages = np.arange(0.0, 40.0 + 1e-9, 2.0)
    rng = np.random.default_rng(3)
    vals = rng.normal(size=NR * NP * NT)
    got = age_maps(vals, gt, ages, HALF, (NR, NP))
    want = (vals.reshape(NR * NP, NT) @ window_stack(t, ages, HALF)).T.reshape(
        ages.size, NR, NP)
    assert np.allclose(got, want, atol=1e-12), np.abs(got - want).max()


def test_static_blob_canary():
    """A blob that does not move: the windowed peak is its centre, exactly."""
    r0, p0 = 12.0, 2.0
    t = np.linspace(TLO, THI, NT)
    ages = np.arange(0.0, 40.0 + 1e-9, 2.0)

    def src(r, phi, tt):
        dr = (np.asarray(r, float) - r0) / 3.0
        dp = (np.asarray(phi, float) - p0 + np.pi) % (2 * np.pi) - np.pi
        return np.exp(-0.5 * (dr ** 2 + (dp / 0.5) ** 2))

    ref = windowed_peak(src, t, ages, R_IN, R_OUT, NR, NP, HALF, refine=8)
    d_logr = np.log(R_OUT / R_IN) / (NR - 1)
    d_phi = 2 * np.pi / NP
    assert np.abs(np.log(ref["r"] / r0)).max() / d_logr < 0.2
    assert np.abs((ref["phi"] - p0 + np.pi) % (2 * np.pi) - np.pi).max() / d_phi < 0.2


def test_moving_blob_canary_tracks_the_window_centre():
    """A blob rotating at a known rate.

    The window is symmetric about source time -a, so the windowed peak of a
    uniformly rotating blob sits at the angle it occupies at that instant. This
    is the case the retired raw-trajectory proxy also got right; it is here so
    that a reference that silently lost the motion would be caught.
    """
    r0, p0, om = 9.0, 0.4, 0.05
    t = np.linspace(TLO, THI, NT)
    ages = np.arange(0.0, 60.0 + 1e-9, 5.0)

    def src(r, phi, tt):
        dr = (np.asarray(r, float) - r0) / 3.0
        c = p0 + om * np.asarray(tt, float)
        dp = (np.asarray(phi, float) - c + np.pi) % (2 * np.pi) - np.pi
        return np.exp(-0.5 * (dr ** 2 + (dp / 0.6) ** 2))

    ref = windowed_peak(src, t, ages, R_IN, R_OUT, NR, NP, HALF, refine=8)
    want = p0 + om * (-ages)
    d_phi = 2 * np.pi / NP
    off = np.abs((ref["phi"] - want + np.pi) % (2 * np.pi) - np.pi) / d_phi
    assert off.max() < 0.5, off


def test_local_maxima_finds_both_lobes_of_an_m2_pattern():
    """cos(2 phi) has two maxima and neither is 'the' peak."""
    t = np.linspace(TLO, THI, NT)
    ages = np.array([0.0, 10.0])

    def src(r, phi, tt):
        rad = np.exp(-0.5 * ((np.asarray(r, float) - 10.0) / 4.0) ** 2)
        return rad * np.cos(2 * np.asarray(phi, float))

    ref = windowed_peak(src, t, ages, R_IN, R_OUT, NR, NP, HALF, refine=4)
    for cr, cp, ca in ref["maxima"]:
        top = ca >= ca.max() - 1e-9
        assert top.sum() >= 2, (top.sum(), ca.max())


@pytest.mark.parametrize("family", list(FAMILIES) + list(OFF_MANIFOLD))
def test_every_family_agrees_within_one_cell(grid, family):
    r, phi, t, gr, gp, gt, ti = grid
    ages = np.arange(0.0, 120.0 + 1e-9, 2.0)
    for seed in (0, 3, 11):
        _, fl, _, dj, _, _ = _build(grid, family, seed)
        f = extract(dj, gt, ages, r, phi, HALF)
        ref = windowed_peak(fl, t, ages, R_IN, R_OUT, NR, NP, HALF, refine=4)
        a = peak_agreement(f, ref, r, phi)
        assert a["radial_cells"] <= 1.0, (family, seed, a)
        assert a["azimuthal_cells"] <= 1.0, (family, seed, a)


def test_agreement_detects_a_displaced_extractor(grid):
    """A gate that cannot fail is not evidence."""
    r, phi, t, gr, gp, gt, ti = grid
    ages = np.arange(0.0, 60.0 + 1e-9, 2.0)
    _, fl, _, dj, _, _ = _build(grid, "circular_hotspot_trajectory", 7)
    f = extract(dj, gt, ages, r, phi, HALF)
    ref = windowed_peak(fl, t, ages, R_IN, R_OUT, NR, NP, HALF, refine=4)
    assert peak_agreement(f, ref, r, phi)["azimuthal_cells"] <= 1.0

    d_phi = 2 * np.pi / NP
    d_logr = np.log(R_OUT / R_IN) / (NR - 1)
    for sr, sp in ((3.0, 0.0), (0.0, 4.0)):
        bad = dict(f)
        bad["r_h"] = np.asarray(f["r_h"], float) * np.exp(sr * d_logr)
        bad["phi_h"] = np.asarray(f["phi_h"], float) + sp * d_phi
        a = peak_agreement(bad, ref, r, phi)
        assert a["radial_cells"] == pytest.approx(sr, abs=0.6), a
        assert a["azimuthal_cells"] == pytest.approx(sp, abs=0.6), a


def test_reference_is_deterministic(grid):
    r, phi, t, gr, gp, gt, ti = grid
    ages = np.arange(0.0, 40.0 + 1e-9, 4.0)
    _, fl, _, _, _, _ = _build(grid, "m1_rotating_crescent", 2)
    a = windowed_peak(fl, t, ages, R_IN, R_OUT, NR, NP, HALF, refine=4)
    b = windowed_peak(fl, t, ages, R_IN, R_OUT, NR, NP, HALF, refine=4)
    assert np.array_equal(a["r"], b["r"]) and np.array_equal(a["phi"], b["phi"])


def test_reference_reads_the_analytic_field_not_the_sampled_one(grid):
    """Independence, checked rather than asserted.

    Corrupting the sampled array must not move the reference. If it did, the
    reference would be sharing the extractor's input and could not audit it.
    """
    r, phi, t, gr, gp, gt, ti = grid
    ages = np.arange(0.0, 40.0 + 1e-9, 4.0)
    _, fl, _, dj, _, _ = _build(grid, "circular_hotspot_trajectory", 4)
    before = windowed_peak(fl, t, ages, R_IN, R_OUT, NR, NP, HALF, refine=4)
    dj[:] = 0.0
    after = windowed_peak(fl, t, ages, R_IN, R_OUT, NR, NP, HALF, refine=4)
    assert np.array_equal(before["r"], after["r"])
    assert np.array_equal(before["phi"], after["phi"])
