"""The governance counts must partition the FAIL rows, with no silent third case."""
from __future__ import annotations

import json

from phrt.config import repo_root
from phrt.io.dashboard import gate_counts, summary_block


def test_counts_partition_the_gate_file():
    p = repo_root() / "artifacts" / "gates" / "correctness_gates.json"
    gates = json.loads(p.read_text())["gates"]
    c = gate_counts()
    assert c["total_gates"] == len(gates)
    n_fail = sum(1 for v in gates.values() if v["status"] == "FAIL")
    assert c["active_blocking_failures"] + c["preserved_literal_failures"] == n_fail
    assert c["passing"] + n_fail + c["future_phase_not_run"] == c["total_gates"]


def test_every_preserved_failure_names_its_disposition():
    c = gate_counts()
    assert len(c["preserved_literal_failure_dispositions"]) == \
        c["preserved_literal_failures"]
    assert all(bool(v) for v in c["preserved_literal_failure_dispositions"].values())


def test_summary_block_reports_all_three_counts():
    b = summary_block()
    for k in ("active_blocking_failures", "preserved_literal_failures",
              "future_phase_not_run"):
        assert k in b


def test_no_active_blocking_failures():
    """If this fails, a FAIL has appeared that nobody has adjudicated."""
    c = gate_counts()
    assert c["active_blocking_failures"] == 0, c["active_blocking_failure_names"]
