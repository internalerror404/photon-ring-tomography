"""Boundary-validity canaries, ruling 028. No physical query is made here."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from phrt.revision_v4_1 import domain as D                   # noqa: E402
from phrt.revision_v4_1 import query as Q                    # noqa: E402

EXACT = 1e-12


# ---- B1: physics and gaps are different states --------------------------
def test_B1_outside_the_annulus_is_certified_zero_not_missing_data():
    band = np.ones(4, bool)
    r = np.array([10.0, 99.0, np.nan, 10.0])
    fin = np.array([10.0, 99.0, np.nan, 10.0])
    st, pr = D.classify_points(band, r, fin, fin, np.ones(4), 1.87, 50.0)
    assert st[0] == D.CERTIFIED_EMITTING
    assert st[1] == D.CERTIFIED_NON_EMITTING
    assert st[2] == D.UNRESOLVED and pr[2] == D.RADIAL_ROOT
    t = D.tally(st, pr, np.ones(4))
    assert t["certified_non_emitting_is_not_a_defect"] is True
    assert t["by_state"][D.CERTIFIED_NON_EMITTING]["n"] == 1
    assert t["by_state"][D.UNRESOLVED]["n"] == 1


def test_B2_a_solver_failure_never_becomes_a_physical_boundary():
    band = np.ones(3, bool)
    r = np.array([np.nan, np.nan, 20.0])
    st, pr = D.classify_points(band, r, r, r, np.ones(3), 1.87, 50.0)
    assert set(st[:2]) == {D.UNRESOLVED}
    assert D.CERTIFIED_NON_EMITTING not in set(st[:2]), (
        "an unsolved ray must never be recorded as zero emission")
    assert (pr[:2] == D.RADIAL_ROOT).all()


def test_B3_a_solved_landing_with_no_redshift_is_unresolved():
    band = np.ones(1, bool)
    st, pr = D.classify_points(band, np.array([10.0]), np.array([1.0]),
                               np.array([1.0]), np.array([np.nan]), 1.87,
                               50.0)
    assert st[0] == D.UNRESOLVED and pr[0] == D.REDSHIFT


def test_B4_a_point_outside_the_band_is_unresolved_not_zero():
    st, pr = D.classify_points(np.zeros(1, bool), np.array([np.nan]),
                               np.array([np.nan]), np.array([np.nan]),
                               np.array([1.0]), 1.87, 50.0)
    assert st[0] == D.UNRESOLVED and pr[0] == D.NEVER_EVALUATED


# ---- B5: the response bound is conditional on its envelope --------------
def test_B5_response_bound_is_explicit_about_its_envelope():
    u = np.array([0.01, 0.0, 0.04])
    m = np.array([2.0, 5.0, 3.0])
    b = D.response_bound(u, m, 0.5, 0.16)
    want = np.sqrt((4 * 1e-4 + 9 * 1.6e-3) / (0.25 * 0.16))
    assert b["whitened_response_bound"] == pytest.approx(want, rel=1e-12)
    assert b["bound_is_conditional_on_the_envelope"] is True
    assert b["cells_with_uncertain_support"] == 2
    with pytest.raises(ValueError):
        D.response_bound(u, m[:2], 0.5, 0.16)
    with pytest.raises(ValueError):
        D.response_bound(-u, m, 0.5, 0.16)


# ---- B6: the guard refuses, it does not fall back -----------------------
def _freeze(tmp, files, ledger=None, commit="deadbeef"):
    p = tmp / "fz.json"
    p.write_text(json.dumps({
        "commit_at_freeze_time": commit, "detector": {}, "clock": {},
        "solver_policy": {"spin": 0.5, "inclination_deg": 50.0,
                          "d_obs": 1000.0},
        "selection_rule": {},
        "ledger": ledger or {"transfer_remaining": 10,
                             "boundary_remaining": 10},
        "files": files}))
    return p


def test_B6_guard_refuses_a_changed_input(tmp_path):
    f = tmp_path / "x.txt"
    f.write_text("a")
    # an absolute path is accepted by the guard, so the fixture does not
    # need to live inside the repository to exercise the hash check
    fz = _freeze(tmp_path, {str(f): Q.sha(f)})
    f.write_text("b")
    with pytest.raises(Q.GuardFailure, match="frozen inputs changed"):
        Q.Guard(fz, allow_dirty=True)


def test_B7_guard_refuses_a_missing_pin(tmp_path):
    p = tmp_path / "fz.json"
    p.write_text(json.dumps({"commit_at_freeze_time": None, "files": {},
                             "detector": {}, "clock": {}}))
    with pytest.raises(Q.GuardFailure, match="does not pin"):
        Q.Guard(p, allow_dirty=True)


def test_B8_guard_meters_and_stops_at_the_cap(tmp_path):
    fz = _freeze(tmp_path, {}, {"transfer_remaining": 5,
                                "boundary_remaining": 0}, commit=None)
    g = Q.Guard(fz, allow_dirty=True)
    g.charge(Q.TRANSFER, 3, "probe")
    assert g.remaining(Q.TRANSFER) == 2
    with pytest.raises(Q.GuardFailure, match="cap reached"):
        g.charge(Q.TRANSFER, 3, "too many")
    with pytest.raises(Q.GuardFailure, match="cap reached"):
        g.charge(Q.BOUNDARY, 1, "none left")
    assert g.snapshot()["spent_this_run"][Q.TRANSFER] == 3, (
        "a refused call must not be charged")


def test_B9_guard_refuses_a_freeze_from_another_commit(tmp_path):
    fz = _freeze(tmp_path, {}, commit="0" * 40)
    with pytest.raises(Q.GuardFailure, match="different commit"):
        Q.Guard(fz, allow_dirty=True)


# ---- B10: the state vocabulary is closed --------------------------------
def test_B10_every_sample_lands_in_exactly_one_state():
    rng = np.random.default_rng(7)
    n = 500
    band = rng.random(n) < 0.7
    r = np.where(rng.random(n) < 0.2, np.nan, rng.uniform(1.0, 90.0, n))
    ph = np.where(np.isfinite(r), rng.random(n), np.nan)
    t = np.where(np.isfinite(r), rng.random(n), np.nan)
    g = np.where(rng.random(n) < 0.05, np.nan, rng.random(n))
    st, pr = D.classify_points(band, r, ph, t, g, 1.87, 50.0)
    assert set(np.unique(st)) <= set(D.STATES)
    counts = sum(int((st == s).sum()) for s in D.STATES)
    assert counts == n, "the states must partition, not overlap"
    u = st == D.UNRESOLVED
    assert (pr[u] != "").all(), "every gap must name the primitive that failed"
