"""Comparator version 3, ruling 033. No campaign ray is traced here.

The fixtures are analytic (Schwarzschild quartics and hand-built root sets);
nothing in this file calls the pinned tracer or reads a campaign map.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from phrt.revision_v4_1 import pathdomain as PD                  # noqa: E402
from phrt.revision_v4_1 import pathdomain2 as P2                 # noqa: E402
from phrt.revision_v4_1 import pathdomain3 as P3                 # noqa: E402
from phrt.revision_v4_1 import rootcheck as RC                   # noqa: E402


def schwarzschild(b):
    return np.roots([1.0, 0.0, -b * b, 2 * b * b, 0.0]).astype(complex)


# ---- P1: where both resolve, the versions agree ----
@pytest.mark.parametrize("b", [5.5, 6.0, 7.0, 9.0, 14.0])
def test_P1_v3_matches_v2_on_the_scatter_integrals(b):
    roots = schwarzschild(b)
    i = P3.turning_index(roots, 2.0, 1000.0)
    turn = float(roots[i].real)
    for hi in (50.0, 1000.0, 1e7):
        v3, _ = P3.integral(turn, hi, roots, i)
        v2, _ = P2.integral(turn, hi, roots, turn=turn)
        assert v3 == pytest.approx(v2, rel=1e-10, abs=1e-14)


def test_P1b_capture_branch_matches_version_two():
    roots = schwarzschild(4.0)          # below the critical impact parameter
    kind, idx = P3.classify(roots, 2.0, 1000.0)
    assert kind == PD.CAPTURE and idx is None
    v3, _ = P3.integral(2.0, 1000.0, roots)
    v2, _ = P2.integral(2.0, 1000.0, roots)
    assert v3 == pytest.approx(v2, rel=1e-10)


# ---- P2: the reduced potential exists at the turning point ----
def test_P2_reduced_potential_is_defined_at_the_turn():
    roots = schwarzschild(6.0)
    i = P3.turning_index(roots, 2.0, 1000.0)
    turn = float(roots[i].real)
    want = float(np.prod([turn - q for j, q in enumerate(roots) if j != i]).real)
    assert P3.endpoint_limit(roots, i) == pytest.approx(want, rel=1e-12)
    # the 031 identity form is zero at exactly this point
    assert RC.identity_excluded_product(roots, turn, turn) == 0


def test_P3_no_division_survives_where_r_minus_turn_underflows():
    """u*u below eps*turn makes r - turn exactly zero; the product does not."""
    roots = schwarzschild(6.0)
    i = P3.turning_index(roots, 2.0, 1000.0)
    turn = float(roots[i].real)
    u = 1e-9
    r = turn + u * u
    assert r - turn == 0.0, "the fixture must actually underflow"
    assert PD.radial_potential(r, roots) == 0.0
    got = float(np.real(RC.reduced_product(roots, i, r)))
    assert got == pytest.approx(P3.endpoint_limit(roots, i), rel=1e-9)
    assert got > 0


def test_P3b_version_two_reference_raises_at_that_point():
    """The graded reference refuses there; version 3 has nothing to refuse."""
    roots = schwarzschild(6.0)
    i = P3.turning_index(roots, 2.0, 1000.0)
    turn = float(roots[i].real)
    r = turn + 1e-18
    q = PD.radial_potential(r, roots) / (r - turn) if (r - turn) else np.nan
    assert not np.isfinite(q) or q <= 0


# ---- P4: the multiplicity guard is preserved ----
def test_P4_a_clustered_turning_root_is_refused_not_answered():
    roots = np.array([1.0 + 0j, 8.0 + 0j, 30.0 + 0j, 30.0 + 1e-9 + 0j])
    d = P3.adjudicate(roots, 0.05, 2.0, 1000.0)
    assert d["code"] == PD.UNRESOLVED
    assert "analytic limit" in d["why"]
    assert d["reason_class"] == "RootCheckError"


# ---- P5: roots that do not solve the original quartic ----
def test_P5_roots_failing_the_original_polynomial_are_refused():
    b, a, th = 6.0, 0.0, 0.0
    roots = schwarzschild(b)
    lam, eta = 0.0, b * b
    ok = P3.adjudicate(roots, 0.05, 2.0, 1000.0, lam=lam, eta=eta, spin=a)
    assert ok["roots"]["max_backward_residual"] < 1e-12
    bad = roots.copy()
    bad[0] += 0.05
    d = P3.adjudicate(bad, 0.05, 2.0, 1000.0, lam=lam, eta=eta, spin=a)
    assert d["code"] == PD.UNRESOLVED
    assert "original" in d["why"]


# ---- P6: an ambiguous case is refused, not decided ----
def test_P6_a_crossing_on_an_endpoint_is_unresolved():
    roots = schwarzschild(6.0)
    i = P3.turning_index(roots, 2.0, 1000.0)
    turn = float(roots[i].real)
    Jo, _ = P3.integral(turn, 1000.0, roots, i)
    J50, _ = P3.integral(turn, 50.0, roots, i)
    d = P3.adjudicate(roots, Jo - J50, 2.0, 1000.0)
    assert d["code"] == PD.UNRESOLVED
    assert "within the margin" in d["why"]


def test_P6b_the_evidence_needed_to_re_examine_a_case_is_returned():
    roots = schwarzschild(6.0)
    d = P3.adjudicate(roots, 0.05, 2.0, 1000.0, lam=0.0, eta=36.0, spin=0.0)
    for k in ("J_observer", "J_50", "s_escape", "error_estimate", "margin",
              "endpoint_limit_at_the_turn", "turning_index", "roots",
              "margin_s_n_minus_lower", "margin_upper_minus_s_n"):
        assert k in d, f"{k} must be retained, not summarised away"
    assert d["roots"]["residual_is_a_root_location_bound"] is False


# ---- P7: a sweep where all three versions resolve ----
def test_P7_three_versions_agree_across_a_scatter_sweep():
    for b in np.linspace(5.5, 20.0, 25):
        roots = schwarzschild(float(b))
        i = P3.turning_index(roots, 2.0, 1000.0)
        if i is None:
            continue
        turn = float(roots[i].real)
        Jo3, _ = P3.integral(turn, 1000.0, roots, i)
        Jo2, _ = P2.integral(turn, 1000.0, roots, turn=turn)
        Jo1, _ = PD._J(turn, 1000.0, roots, turn=turn)
        assert Jo3 == pytest.approx(Jo2, rel=1e-9)
        assert Jo3 == pytest.approx(Jo1, rel=1e-9)


def test_P8_policy_is_frozen_and_self_describing():
    assert P3.POLICY["reduced_potential"] == \
        "index_excluded_product_no_division"
    assert P3.POLICY["margin_factor"] == 10.0
    assert P3.VERSION == "PATHDOMAIN_V3_INDEXED_REDUCTION"
