"""Path-domain canaries, ruling 030. No physical query is made here."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from phrt.revision_v4_1 import pathdomain as PD              # noqa: E402


def schwarzschild(b):
    """R(r) = r^4 - b^2 r^2 + 2 b^2 r, the null radial potential at a = 0."""
    return np.roots([1.0, 0.0, -b * b, 2 * b * b, 0.0])


def test_P1_escape_mino_matches_an_independent_quadrature():
    """The reviewer's scalar fixture: b=6, M=1, observer at 1000M."""
    roots = schwarzschild(6.0)
    kind, turn = PD.classify_path(roots, 2.0, 1000.0)
    assert kind == PD.SCATTER
    assert turn == pytest.approx(4.453363194, rel=1e-9)
    Jo, _ = PD._J(turn, 1000.0, roots, turn=turn)
    Ji, _ = PD.escape_mino(turn, roots)
    # the analytic tail beyond the quadrature limit is what makes this agree
    # to the eighth figure rather than the seventh
    assert Jo + Ji == pytest.approx(0.80916349, rel=1e-8)
    assert PD._J(turn, 1e7, roots, turn=turn)[0] + Jo == pytest.approx(
        0.80916349, rel=2e-7), "truncating at 1e7 leaves exactly 1e-7 out"


def test_P2_a_nearly_real_outer_root_inside_the_horizon_is_capture():
    """Four real roots all inside the horizon is a capture, not a scatter."""
    roots = np.array([0.2, 0.6, 1.1, 1.5], complex)
    kind, turn = PD.classify_path(roots, 1.866, 1000.0)
    assert kind == PD.CAPTURE and turn is None
    roots = np.array([0.2, 0.6, 1.1, 4.0 + 1e-14j], complex)
    kind, turn = PD.classify_path(roots, 1.866, 1000.0)
    assert kind == PD.SCATTER and turn == pytest.approx(4.0)
    roots = np.array([0.2, 0.6, 1.1, 4.0 + 1e-6j], complex)
    assert PD.classify_path(roots, 1.866, 1000.0)[0] == PD.CAPTURE, (
        "an imaginary part above tolerance is not an accessible turn")


def test_P3_a_crossing_after_the_horizon_is_not_an_event():
    roots = np.array([0.2, 0.6, 1.1, 1.5], complex)
    rh, ro = 1.866, 1000.0
    sH, _ = PD._J(rh, ro, roots)
    for s, want in ((sH * 1.5, PD.NO_CROSSING_CAPTURE),
                    (sH * 0.999999, PD.VALID)):
        d = PD.adjudicate(roots, s, rh, ro)
        assert d["code"] == want, (s, d)


def test_P4_a_turn_outside_the_annulus_never_reaches_it():
    roots = schwarzschild(200.0)
    kind, turn = PD.classify_path(roots, 1.866, 1000.0)
    assert kind == PD.SCATTER and turn > 50.0
    d = PD.adjudicate(roots, 0.001, 1.866, 1000.0)
    assert d["code"] == PD.NO_ANNULUS_ON_PATH


def test_P5_a_crossing_after_escape_is_not_an_event():
    roots = schwarzschild(6.0)
    d = PD.adjudicate(roots, 5.0, 2.0, 1000.0)
    assert d["code"] == PD.NO_CROSSING_ESCAPE


def test_P6_a_boundary_within_the_margin_is_unresolved_not_forced():
    roots = np.array([0.2, 0.6, 1.1, 1.5], complex)
    rh, ro = 1.866, 1000.0
    s50, _ = PD._J(50.0, ro, roots)
    d = PD.adjudicate(roots, s50, rh, ro, margin_factor=1e6)
    assert d["code"] == PD.UNRESOLVED
    assert "margin" in d["why"]


def test_P7_the_substitution_removes_the_turning_point_singularity():
    roots = schwarzschild(6.0)
    turn = PD.classify_path(roots, 2.0, 1000.0)[1]
    v, e = PD._J(turn, turn + 1e-3, roots, turn=turn)
    assert np.isfinite(v) and v > 0 and e < 1e-9


def test_P8_the_code_vocabulary_is_closed_and_no_sign_test_appears():
    src = (ROOT / "src/phrt/revision_v4_1/pathdomain.py").read_text()
    assert "raw_source_radius" not in src, (
        "the domain predicate must not consult the raw radius sign")
    assert set(PD.CODES) >= {PD.VALID, PD.OUTSIDE_ANNULUS,
                             PD.NO_CROSSING_CAPTURE, PD.NO_CROSSING_ESCAPE,
                             PD.NO_ANNULUS_ON_PATH, PD.UNRESOLVED}
