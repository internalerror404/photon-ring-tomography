"""The completion token must fail closed, and the guards must refuse.

Review 024 gate_hardening.inject_failure_tests: seven conditions the protocol
says must stop execution. Each is injected here and the run is required not to
report success. A test suite that only exercises the happy path cannot tell a
working gate from an absent one.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from phrt.revision_v4_1 import guards  # noqa: E402
from phrt.revision_v4_1.completion import (REQUIRED, SUCCESS,  # noqa: E402
                                           Completion)


def _all_good() -> Completion:
    c = Completion()
    for name in REQUIRED:
        c.record(name, True, "fixture")
    return c


def test_the_happy_path_does_reach_success():
    """Otherwise every failure test below would pass for the wrong reason."""
    assert _all_good().token == SUCCESS


def test_an_unrecorded_condition_fails_closed():
    c = Completion()
    for name in REQUIRED[:-1]:
        c.record(name, True, "fixture")
    assert c.token != SUCCESS
    assert REQUIRED[-1] in c.never_recorded_names()


def test_injection_1_failed_prerequisite_test():
    c = _all_good()
    c.record("prerequisite_test_success", False, "a gate failed")
    assert c.token == "R1_BLOCKED"


def test_injection_2_modified_or_missing_input(tmp_path):
    f = tmp_path / "in.txt"
    f.write_text("original")
    freeze = tmp_path / "freeze.json"
    freeze.write_text(json.dumps({"files": {"in.txt": guards.sha256(f)}}))
    assert guards.verify_inputs(freeze, tmp_path)["all_match"]

    f.write_text("tampered")
    with pytest.raises(guards.GuardFailure, match="input freeze violated"):
        guards.verify_inputs(freeze, tmp_path)

    f.unlink()
    with pytest.raises(guards.GuardFailure, match="missing"):
        guards.verify_inputs(freeze, tmp_path)

    c = _all_good()
    c.record("verified_input_and_target_hashes", False, "input modified")
    assert c.token == "R1_BLOCKED"


def test_injection_3_changed_target_columns(tmp_path):
    man = tmp_path / "manifest.json"
    man.write_text(json.dumps({"n_target_columns": 72,
                               "n_nuisance_columns": 152,
                               "target_column_indices": [0, 1, 2]}))
    t = np.zeros(224, bool)
    t[[0, 1, 2]] = True
    n = ~t
    # counts must match the manifest for the index check to be the one that
    # fires, so the fixture declares the real counts
    man.write_text(json.dumps({"n_target_columns": int(t.sum()),
                               "n_nuisance_columns": int(n.sum()),
                               "target_column_indices": [0, 1, 2]}))
    assert guards.verify_target_columns(man, t, n)["n_target"] == 3

    drifted = np.zeros(224, bool)
    drifted[[0, 1, 5]] = True
    with pytest.raises(guards.GuardFailure, match="indices differ"):
        guards.verify_target_columns(man, drifted, ~drifted)

    fewer = np.zeros(224, bool)
    fewer[[0, 1]] = True
    with pytest.raises(guards.GuardFailure, match="selection drifted"):
        guards.verify_target_columns(man, fewer, ~fewer)


def test_injection_4_unpromoted_source_gram():
    c = _all_good()
    c.record("source_metric_promotion", False,
             "Gram relative change 1.9e-05 against the 1e-6 bar")
    assert c.token == "R2_NUMERICALLY_UNRESOLVED"


def test_injection_5_nuisance_rank_moves_though_counts_agree():
    """The original reporting path looked only at operational counts."""
    rows = [{"rtol": 1e-13, "nuisance_rank": 151, "ops": 2},
            {"rtol": 1e-12, "nuisance_rank": 152, "ops": 2},
            {"rtol": 1e-11, "nuisance_rank": 152, "ops": 2}]
    counts_agree = len({r["ops"] for r in rows}) == 1
    ranks_agree = len({r["nuisance_rank"] for r in rows}) == 1
    assert counts_agree and not ranks_agree
    c = _all_good()
    c.record("stable_nuisance_rank_and_operational_counts_across_registered_"
             "tolerances", counts_agree and ranks_agree,
             "nuisance rank moved across tolerances")
    assert c.token == "R2_NUMERICALLY_UNRESOLVED"


def test_injection_6_operational_count_moves():
    c = _all_good()
    c.record("stable_nuisance_rank_and_operational_counts_across_registered_"
             "tolerances", False, "operational count 2 -> 3 at rtol 1e-11")
    assert c.token == "R2_NUMERICALLY_UNRESOLVED"


def test_injection_7_existing_output_directory(tmp_path):
    d = tmp_path / "run"
    d.mkdir()
    (d / "already.json").write_text("{}")
    with pytest.raises(guards.GuardFailure, match="already exists"):
        guards.require_fresh_output_dir(d)
    assert guards.require_fresh_output_dir(tmp_path / "clean").is_dir()


def test_non_finite_outputs_fail_closed():
    c = _all_good()
    c.record("finite_numeric_outputs", False, "a singular value was nan")
    assert c.token == "R2_NUMERICALLY_UNRESOLVED"


def test_empty_target_is_a_non_success_disposition():
    c = _all_good()
    c.empty_target = True
    assert c.token == "R2_EMPTY_TARGET_NO_SUCCESS"
    assert not c.ok
