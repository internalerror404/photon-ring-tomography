"""The three background regimes, and the constrained estimator's feasibility."""
import numpy as np
import pytest

from phrt.inverse.background import (REGIMES, axisymmetric_design,
                                     background_error, estimate_from_field,
                                     joint, oracle)
from phrt.inverse.constrained import safe_step, solve
from phrt.sources.contrast import build

SPIN, R_IN, R_OUT = 0.5, 1.8660386527060988, 49.98205255591607
TLO, THI = -128.82234649196255, 29.0
NR, NP, NT = 16, 32, 40


@pytest.fixture(scope="module")
def env():
    r = np.exp(np.linspace(np.log(R_IN), np.log(R_OUT), NR))
    phi = np.linspace(0.0, 2 * np.pi, NP, endpoint=False)
    t = np.linspace(TLO, THI, NT)
    R, P, T = np.meshgrid(r, phi, t, indexing="ij")
    gr, gp, gt = R.ravel(), P.ravel(), T.ravel()
    ti = np.tile(np.arange(NT), NR * NP)
    b, fl, traj, dj, bg, diag = build(np.random.default_rng(5),
                                      "circular_hotspot_trajectory", SPIN,
                                      R_IN, R_OUT, gr, gp, gt, ti, NT)
    des = axisymmetric_design(gr, gt, R_IN, R_OUT, t_min=TLO, t_max=THI)
    return gr, gp, gt, dj, bg, des


def test_three_regimes_are_declared():
    assert REGIMES == ("oracle_known", "estimated_from_data", "joint_inversion")


def test_oracle_is_exact_by_definition(env):
    *_, bg, _ = env
    b_hat, _ = oracle(bg)
    assert background_error(b_hat, bg)["relative_error"] == 0.0


def test_estimated_background_is_positive_and_reports_its_clipping(env):
    gr, gp, gt, dj, bg, des = env
    b_hat, info = estimate_from_field(bg + dj, des)
    assert b_hat.min() > 0.0
    for k in ("n_clipped", "clipped_fraction", "min_before_clip"):
        assert k in info


def test_estimated_background_is_wrong_but_not_useless(env):
    # it must be genuinely imperfect -- otherwise the regime is oracle in
    # disguise -- while still beating a flat guess
    gr, gp, gt, dj, bg, des = env
    b_hat, _ = estimate_from_field(bg + dj, des)
    err = background_error(b_hat, bg)["relative_error"]
    flat = background_error(np.full_like(bg, bg.mean()), bg)["relative_error"]
    assert 0.0 < err < flat


def test_the_background_model_cannot_absorb_the_fluctuation(env):
    # a background rich enough to fit dj would make the contrast split
    # meaningless, so the axisymmetric design must leave most of it behind
    gr, gp, gt, dj, bg, des = env
    coef, *_ = np.linalg.lstsq(des, dj, rcond=None)
    absorbed = np.linalg.norm(des @ coef) / np.linalg.norm(dj)
    # exact, not merely small: the fluctuation has zero azimuthal mean at every
    # radius and age, so it is orthogonal to any axisymmetric model
    assert absorbed < 1e-10, absorbed


def test_joint_inversion_runs_and_stays_positive(env):
    gr, gp, gt, dj, bg, des = env
    q, _ = np.linalg.qr(des)
    b_hat, info = joint(bg + dj, des, q)
    assert b_hat.min() > 0.0
    assert info["n_iterations"] == 12


def test_background_error_reports_bias_and_minimum(env):
    *_, bg, _ = env
    e = background_error(bg * 1.05, bg)
    assert e["bias"] > 0.0 and e["relative_error"] == pytest.approx(0.05, rel=1e-6)


def test_constrained_solver_returns_a_feasible_field():
    rng = np.random.default_rng(3)
    n_pts, n_coef = 240, 24
    D = rng.normal(size=(n_pts, n_coef))
    x_true = rng.normal(size=n_coef)
    bgnd = np.abs(D @ x_true) + 0.5           # feasible by construction
    A = rng.normal(size=(180, n_coef))
    y = A @ x_true
    G = A.T @ A
    x, info = solve(D, lambda v: G @ v, A.T @ y, bgnd,
                    np.zeros(n_coef), step=safe_step(np.linalg.norm(A, 2)),
                    n_iter=300)
    assert info["worst_violation"] < 1e-6, info
    assert info["n_infeasible_points"] == 0


def test_constrained_solver_enforces_a_binding_constraint():
    # a background so small that the unconstrained solution violates it
    rng = np.random.default_rng(7)
    D = np.eye(12)
    x_true = rng.normal(size=12)
    A = rng.normal(size=(40, 12))
    y = A @ x_true
    tight = np.full(12, 0.05)
    x, info = solve(D, lambda v: (A.T @ A) @ v, A.T @ y, tight, np.zeros(12),
                    step=safe_step(np.linalg.norm(A, 2)), n_iter=400)
    assert (D @ x + tight).min() > -1e-6
    assert info["n_infeasible_points"] == 0
