"""The contrast model's two constraints, and what the extractor can recover."""
import numpy as np
import pytest

from phrt.metrics.features import (aggregate, event_times, extract,
                                   generative_peak_error,
                                   normalized_errors, peak_position)
from phrt.sources.contrast import (FAMILIES, OFF_MANIFOLD, build,
                                   background_field)
from phrt.sources.movie import wrapped_angle
from phrt.sources.orbits import isco_radius

SPIN, R_IN, R_OUT = 0.5, 1.8660386527060988, 49.98205255591607
TLO, THI = -128.82234649196255, 29.0
NR, NP, NT = 16, 32, 40


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


@pytest.mark.parametrize("family", FAMILIES)
def test_zero_spatial_mean_at_every_age(grid, family):
    *_, diag = _build(grid, family, 3)
    assert diag["zero_mean_max_abs"] < 1e-10, (family, diag["zero_mean_max_abs"])


@pytest.mark.parametrize("family", FAMILIES)
def test_total_emissivity_is_nonnegative(grid, family):
    *_, diag = _build(grid, family, 5)
    assert diag["min_total"] >= 0.0, (family, diag["min_total"])
    assert diag["min_background"] > 0.0


@pytest.mark.parametrize("family", FAMILIES)
def test_the_fluctuation_is_genuinely_signed(grid, family):
    # the whole point of the contrast model: dj changes sign while b + dj does
    # not. A dj that never went negative would just be a positive bank again.
    _, _, _, dj, _, _ = _build(grid, family, 7)
    assert dj.min() < 0.0 and dj.max() > 0.0, family


def test_background_is_positive_everywhere_without_clipping(grid):
    r, phi, t, gr, gp, gt, ti = grid
    b, _ = background_field(np.random.default_rng(11), R_IN, R_OUT)
    assert b(gr, gt).min() > 0.0


def test_analytic_fluctuation_matches_the_grid_construction(grid):
    # the operator samples where the rays land, so the callable must reproduce
    # the grid-built field it is scored against
    r, phi, t, gr, gp, gt, ti = grid
    _, fluct, _, dj, _, _ = _build(grid, "circular_hotspot_trajectory", 13)
    got = np.asarray(fluct(gr, gp, gt), float)
    assert np.abs(got - dj).max() / max(np.abs(dj).max(), 1e-300) < 1e-9


def test_peak_refinement_beats_the_grid(grid):
    r, phi, t, gr, gp, gt, ti = grid
    # a blob centred between two azimuth cells: the unrefined argmax cannot
    # find it, the parabolic refinement should get close
    target = float(phi[5] + 0.5 * (phi[1] - phi[0]))
    m = np.exp(-0.5 * ((r[:, None] - 12.0) / 3.0) ** 2) * np.exp(
        -0.5 * (wrapped_angle(phi[None, :] - target) / 0.5) ** 2)
    _, phi_hat, _ = peak_position(m, r, phi)
    step = float(phi[1] - phi[0])
    assert abs(float(wrapped_angle(np.array([phi_hat - target]))[0])) < 0.35 * step


@pytest.mark.parametrize("family", ["circular_hotspot_trajectory",
                                    "plunging_feature"])
def test_extraction_recovers_the_generative_trajectory(grid, family):
    r, phi, t, gr, gp, gt, ti = grid
    _, _, traj, dj, _, _ = _build(grid, family, 17)
    ages = np.arange(0.0, 60.0 + 1e-9, 2.0)
    got = extract(dj, gt, ages, r, phi, 3.0)
    want_r = np.array([traj(a)["r_h"] for a in ages])
    want_p = np.array([traj(a)["phi_h"] for a in ages])
    # radius to within a grid cell in log r, angle to within two azimuth cells
    cell_r = float(np.exp(np.diff(np.log(r))[0])) - 1.0
    assert np.median(np.abs(got["r_h"] - want_r) / want_r) < 2.0 * cell_r
    dphi = np.abs(wrapped_angle(got["phi_h"] - want_p))
    assert np.median(dphi) < 2.0 * float(phi[1] - phi[0]), np.median(dphi)


def test_extraction_is_deterministic(grid):
    r, phi, t, gr, gp, gt, ti = grid
    _, _, _, dj, _, _ = _build(grid, "m1_rotating_crescent", 19)
    ages = np.arange(0.0, 40.0 + 1e-9, 2.0)
    a = extract(dj, gt, ages, r, phi, 3.0)
    b = extract(dj, gt, ages, r, phi, 3.0)
    for k, v in a.items():
        assert np.array_equal(np.asarray(v), np.asarray(b[k])), k


def test_flare_event_times_are_recovered(grid):
    r, phi, t, gr, gp, gt, ti = grid
    _, _, traj, dj, _, _ = _build(grid, "flare_birth_motion_decay", 23)
    ages = np.arange(0.0, 120.0 + 1e-9, 2.0)
    got = extract(dj, gt, ages, r, phi, 3.0)
    want = traj(0.0)
    assert np.isfinite(got["t_birth_age_M"]) and np.isfinite(got["tau_decay_M"])
    # birth age within a quarter of the observation span of the generative one
    assert abs(got["t_birth_age_M"] - want["t_birth_age_M"]) < 0.25 * 120.0


def test_event_times_are_nan_rather_than_zero_on_a_dead_field():
    # a silent field must not report a confident birth at age zero
    e = event_times(np.arange(0.0, 20.0, 2.0), np.zeros(10))
    assert np.isnan(e["t_birth_age_M"]) and np.isnan(e["tau_decay_M"])


def test_normalized_errors_and_aggregate(grid):
    r, phi, t, gr, gp, gt, ti = grid
    _, _, _, dj, _, _ = _build(grid, "two_hotspot_trajectories", 29)
    ages = np.arange(0.0, 40.0 + 1e-9, 2.0)
    tr = extract(dj, gt, ages, r, phi, 3.0)
    errs = normalized_errors(tr, tr, R_OUT - R_IN, 20.0)
    agg = aggregate(errs, ("radial", "angular", "amplitude", "mode_m1", "mode_m2"))
    assert agg.shape == ages.shape
    assert float(agg.max()) == 0.0        # a field against itself


@pytest.mark.parametrize("family", OFF_MANIFOLD)
def test_off_manifold_families_build_and_obey_the_same_constraints(grid, family):
    *_, diag = _build(grid, family, 31)
    assert diag["zero_mean_max_abs"] < 1e-10
    assert diag["min_total"] >= 0.0


def test_circular_families_stay_outside_the_isco(grid):
    for seed in range(20):
        _, _, _, _, _, diag = _build(grid, "circular_hotspot_trajectory", seed)
        assert diag["feature_params"]["r_h"] > isco_radius(SPIN)
        _, _, _, _, _, dp = _build(grid, "plunging_feature", seed)
        assert dp["feature_params"]["r_h_start"] < isco_radius(SPIN)


@pytest.mark.parametrize("family", FAMILIES)
def test_azimuthal_mean_is_zero_at_every_radius_and_age(grid, family):
    # stronger than the ruling's single spatial mean per age, and it is what
    # makes the background/contrast split identifiable at all
    *_, diag = _build(grid, family, 37)
    assert diag["azimuthal_mean_max_abs"] < 1e-12, family


@pytest.mark.parametrize("family", FAMILIES)
def test_local_contrast_is_order_unity_not_a_whisper(grid, family):
    # scaling the fluctuation globally sets its amplitude from the single worst
    # point in the domain and collapses the contrast to a few percent. Scaling
    # against the local background keeps it physical.
    *_, diag = _build(grid, family, 41)
    peak = diag["achieved_peak_fraction_of_background"]
    assert 0.25 < peak <= 0.85, (family, peak)


@pytest.mark.parametrize("family", FAMILIES)
def test_an_axisymmetric_model_cannot_absorb_the_fluctuation(grid, family):
    from phrt.inverse.background import axisymmetric_design
    r, phi, t, gr, gp, gt, ti = grid
    _, _, _, dj, _, _ = _build(grid, family, 43)
    des = axisymmetric_design(gr, gt, R_IN, R_OUT, t_min=TLO, t_max=THI)
    coef, *_ = np.linalg.lstsq(des, dj, rcond=None)
    absorbed = np.linalg.norm(des @ coef) / np.linalg.norm(dj)
    assert absorbed < 1e-10, (family, absorbed)


@pytest.mark.parametrize("family", FAMILIES)
def test_generative_peak_error_is_within_one_grid_cell(grid, family):
    """G10b, on every declared family rather than only the easy ones."""
    r, phi, t, gr, gp, gt, ti = grid
    _, _, traj, dj, _, _ = _build(grid, family, 17)
    ages = np.arange(0.0, 60.0 + 1e-9, 2.0)
    got = extract(dj, gt, ages, r, phi, 3.0)
    m = 2 if family == "m2_structural_mode" else 1
    e = generative_peak_error(traj, ages, got, r, phi, m_fold=m)
    assert e["n_ages_scored"] > 0
    assert e["radial_cells"] <= 1.0, e
    assert e["azimuthal_cells"] <= 1.0, e


def test_generative_peak_error_detects_a_displaced_trajectory(grid):
    """A gate that cannot fail is not evidence.

    Feed the same extraction a trajectory shifted by a known number of cells
    and check the measure reports that shift, in both coordinates. Without
    this, G10b passing would only show that the arithmetic runs.
    """
    r, phi, t, gr, gp, gt, ti = grid
    _, _, traj, dj, _, _ = _build(grid, "circular_hotspot_trajectory", 17)
    ages = np.arange(0.0, 60.0 + 1e-9, 2.0)
    got = extract(dj, gt, ages, r, phi, 3.0)
    d_logr = float(np.log(r[-1] / r[0]) / (r.size - 1))
    d_phi = float(2.0 * np.pi / phi.size)

    for shift_r, shift_p in ((3.0, 0.0), (0.0, 4.0)):
        def moved(a, sr=shift_r, sp=shift_p):
            v = dict(traj(a))
            v["r_h"] = v["r_h"] * np.exp(sr * d_logr)
            v["phi_h"] = float(wrapped_angle(
                np.array([v["phi_h"] + sp * d_phi]))[0])
            return v
        e = generative_peak_error(moved, ages, got, r, phi)
        assert e["radial_cells"] == pytest.approx(shift_r, abs=0.5), e
        assert e["azimuthal_cells"] == pytest.approx(shift_p, abs=0.5), e


def test_generative_peak_error_skips_ages_where_the_feature_is_dead(grid):
    """The flare is only scored while it is alive, and that is most of it."""
    r, phi, t, gr, gp, gt, ti = grid
    _, _, traj, dj, _, _ = _build(grid, "flare_birth_motion_decay", 5)
    ages = np.arange(0.0, 120.0 + 1e-9, 2.0)
    got = extract(dj, gt, ages, r, phi, 3.0)
    e = generative_peak_error(traj, ages, got, r, phi)
    assert 0 < e["n_ages_scored"] < ages.size
