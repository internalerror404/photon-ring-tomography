"""An exact-in-class bank must have a representation floor of exactly zero."""
import numpy as np
import pytest

from phrt.metrics.level_structure import level_subspace
from phrt.metrics.scoring import evaluation_grid
from phrt.sources.localized_basis import LocalizedBasis
from phrt.sources.structural import (BUILDERS, FAMILIES, in_class_bank,
                                     project_to_class, structure_fraction)

SPIN, R_IN, R_OUT = 0.5, 1.8660386527060988, 49.98205255591607
TLO, THI, NT = -128.82234649196255, 29.0, 40


@pytest.fixture(scope="module")
def env():
    r, p, t = evaluation_grid(R_IN, R_OUT, TLO, THI, n_t=NT)
    lev = level_subspace(t, TLO, THI, 8)
    ti = np.clip(np.searchsorted(np.linspace(TLO, THI, NT), t), 0, NT - 1)
    b = LocalizedBasis(R_IN, R_OUT, TLO, THI, 6, 11, 16)
    return r, p, t, lev, ti, b, b.design(r, p, t)


def test_projection_is_idempotent(env):
    r, p, t, lev, ti, b, D = env
    rng = np.random.default_rng(0)
    v = BUILDERS["circular_single_hotspot"](rng, SPIN, 29.99)(r, p, t)
    _, v1 = project_to_class(v, D)
    _, v2 = project_to_class(v1, D)
    assert np.linalg.norm(v2 - v1) / np.linalg.norm(v1) < 1e-10


@pytest.mark.parametrize("bank,target", [
    ("constant_flux_structural", None),
    ("structure_balanced_050", 0.50),
    ("structure_balanced_080", 0.80)])
def test_bank_truths_are_exactly_in_class(env, bank, target):
    r, p, t, lev, ti, b, D = env
    rng = np.random.default_rng(3)
    Q, _ = np.linalg.qr(D)
    for fam in FAMILIES:
        raw = BUILDERS[fam](rng, SPIN, 29.99)(r, p, t)
        coef, v, diag = in_class_bank(bank, raw, D, lev, ti, NT, target)
        floor = np.linalg.norm(v - Q @ (Q.T @ v)) / max(np.linalg.norm(v), 1e-300)
        assert floor < 1e-10, (bank, fam, floor)
        assert np.allclose(D @ coef, v, atol=1e-8 * max(abs(v).max(), 1.0))


def test_reprojection_residual_is_reported_not_hidden(env):
    r, p, t, lev, ti, b, D = env
    rng = np.random.default_rng(5)
    raw = BUILDERS["circular_crescent"](rng, SPIN, 29.99)(r, p, t)
    _, _, diag = in_class_bank("constant_flux_structural", raw, D, lev, ti, NT, None)
    # constant-flux division is not linear in the coefficients, so the second
    # projection genuinely moves the field. The number must be present.
    assert "reprojection_residual_relative" in diag
    assert diag["reprojection_residual_relative"] >= 0.0


def test_negative_mass_is_measured(env):
    r, p, t, lev, ti, b, D = env
    rng = np.random.default_rng(7)
    raw = BUILDERS["plunging_hotspot"](rng, SPIN, 29.99)(r, p, t)
    _, v, diag = in_class_bank("structure_balanced_050", raw, D, lev, ti, NT, 0.50)
    assert "negative_mass_relative" in diag
    assert diag["negative_mass_relative"] == pytest.approx(
        float(np.linalg.norm(np.minimum(v, 0.0)) / np.linalg.norm(v)), rel=1e-9)


def test_structure_fraction_survives_the_projection(env):
    r, p, t, lev, ti, b, D = env
    rng = np.random.default_rng(11)
    raw = BUILDERS["circular_two_hotspots"](rng, SPIN, 29.99)(r, p, t)
    _, v, diag = in_class_bank("structure_balanced_050", raw, D, lev, ti, NT, 0.50)
    assert structure_fraction(v, lev) == pytest.approx(
        diag["achieved_structure_fraction"], rel=1e-9)
    assert 0.30 < diag["achieved_structure_fraction"] < 0.70
