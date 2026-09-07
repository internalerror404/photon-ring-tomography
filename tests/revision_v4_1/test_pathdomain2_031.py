"""Hardened predicate guards, ruling 031. No physical query is made here."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from phrt.revision_v4_1 import pathdomain as PD                # noqa: E402
from phrt.revision_v4_1 import pathdomain2 as P2               # noqa: E402


def schwarzschild(b):
    return np.roots([1.0, 0.0, -b * b, 2 * b * b, 0.0])


# ---- G1: an invalid interior evaluation is unresolved, never dropped ----
def test_G1_negative_potential_inside_the_interval_raises():
    """Version 1 substitutes zero there; version 2 refuses."""
    roots = np.array([1.0, 2.0, 3.0, 4.0], complex)   # R < 0 on (3, 4)
    v1, _ = PD._J(3.2, 3.8, roots)
    assert v1 == 0.0, "version 1 silently returns zero, which is the hole"
    with pytest.raises(P2.DomainUnresolved, match="not positive"):
        P2.integral(3.2, 3.8, roots)


def test_G2_misordered_endpoints_and_nonfinite_limits_raise():
    roots = schwarzschild(6.0)
    with pytest.raises(P2.DomainUnresolved, match="misordered"):
        P2.integral(100.0, 10.0, roots)
    with pytest.raises(P2.DomainUnresolved, match="non-finite"):
        P2.integral(np.nan, 10.0, roots)
    assert P2.integral(5.0, 5.0, roots) == (0.0, 0.0)


def test_G3_a_nan_crossing_parameter_cannot_fall_through_to_valid():
    """The control-flow hole: NaN makes both comparisons false."""
    roots = np.array([0.2, 0.6, 1.1, 1.5], complex)
    d = P2.adjudicate(roots, np.nan, 1.866, 1000.0)
    assert d["code"] == PD.UNRESOLVED
    # and the shape of the hole, demonstrated directly
    s = np.nan
    assert not (s >= 1.0) and not (s < 0.5), (
        "with NaN both branch tests are false, so an unguarded chain would "
        "reach the final return")


def test_G4_a_negative_mino_parameter_is_unresolved():
    roots = np.array([0.2, 0.6, 1.1, 1.5], complex)
    assert P2.adjudicate(roots, -1e-9, 1.866, 1000.0)["code"] == PD.UNRESOLVED


def test_G5_a_degenerate_root_at_the_turn_is_not_forced():
    """A double root is not a simple turn; the reduced product is not finite."""
    roots = np.array([0.5, 1.0, 4.0, 4.0], complex)
    d = P2.adjudicate(roots, 0.5, 1.866, 1000.0)
    assert d["code"] in (PD.UNRESOLVED, PD.NO_ANNULUS_ON_PATH,
                         PD.OUTSIDE_ANNULUS, PD.VALID)
    if d["code"] != PD.UNRESOLVED:
        assert "margin" in d, "a resolved degenerate case must carry a margin"


def test_G6_reference_nonconvergence_is_reported_not_hidden():
    roots = np.array([1.0, 2.0, 3.0, 4.0], complex)
    with pytest.raises(P2.DomainUnresolved):
        P2.panelled(3.2, 3.8, roots)
    v, e = P2.panelled(*(4.5, 1000.0), roots=roots)
    assert np.isfinite(v) and np.isfinite(e) and e >= 0.0


def test_G7_the_tail_is_asymptotic_with_a_remainder_not_a_closed_form():
    roots = schwarzschild(6.0)
    v, rem = P2.tail(1e7, roots)
    assert rem > 0.0, "an asymptotic correction must carry a remainder"
    v2, rem2 = P2.tail(1e8, roots)
    assert rem2 < rem, "the remainder must fall with the truncation radius"
    assert "asymptotic" in P2.tail.__doc__


def test_G8_escape_boundary_overlap_is_unresolved():
    roots = schwarzschild(6.0)
    t = PD.classify_path(roots, 2.0, 1000.0)[1]
    Jo, _ = P2.integral(t, 1000.0, roots, turn=t)
    Ji, _ = P2.integral(t, 1e7, roots, turn=t)
    tv, _ = P2.tail(1e7, roots)
    d = P2.adjudicate(roots, Jo + Ji + tv, 2.0, 1000.0, margin_factor=1e6)
    assert d["code"] == PD.UNRESOLVED and "escape" in d["why"]


# ---- G9: the two versions must agree wherever both resolve --------------
def test_G9_versions_agree_where_both_resolve():
    rng = np.random.default_rng(31)
    agree = disagree = 0
    for b in rng.uniform(5.5, 40.0, 60):
        roots = schwarzschild(float(b))
        for s in rng.uniform(0.0, 1.5, 6):
            a = PD.adjudicate(roots, float(s), 2.0, 1000.0)
            c = P2.adjudicate(roots, float(s), 2.0, 1000.0)
            if PD.UNRESOLVED in (a["code"], c["code"]):
                continue
            agree += a["code"] == c["code"]
            disagree += a["code"] != c["code"]
    assert agree > 100 and disagree == 0, (agree, disagree)


def test_G10_both_margins_are_exported_with_their_uncertainty():
    roots = np.array([0.2, 0.6, 1.1, 1.5], complex)
    sH, _ = P2.integral(1.866, 1000.0, roots)
    s50, _ = P2.integral(50.0, 1000.0, roots)
    d = P2.adjudicate(roots, 0.5 * (sH + s50), 1.866, 1000.0)
    assert d["code"] == PD.VALID
    assert d["margin_G_theta_minus_s50"] > 0
    assert d["margin_sH_minus_G_theta"] > 0
    assert d["error_estimate"] >= 0 and d["margin"] > 0
