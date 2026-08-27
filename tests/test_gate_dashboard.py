"""The governance counts must partition the FAIL rows, with no silent third case."""
from __future__ import annotations

import json

from phrt.config import repo_root
from pathlib import Path

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


# Gates that are FAIL by design while the thing they guard is unproven. Each
# needs a written adjudication, so the entry carries the document that rules on
# it. This is not a mute list: an unlisted FAIL still breaks the build, and a
# listed one has to point at a real file.
# Empty is the healthy state. R1L_G12_deterministic_reproduction was listed
# here while deterministic reproduction was unproven and was removed when the
# pinned pair passed, which is the lifecycle this list is meant to have.
DECLARED_BLOCKING: dict[str, str] = {}


def test_no_unadjudicated_blocking_failures():
    """If this fails, a FAIL has appeared that nobody has adjudicated."""
    c = gate_counts()
    undeclared = [n for n in c["active_blocking_failure_names"]
                  if n not in DECLARED_BLOCKING]
    assert not undeclared, undeclared


def test_every_declared_blocking_gate_has_its_adjudication_on_disk():
    root = Path(__file__).resolve().parents[1]
    for gate, doc in DECLARED_BLOCKING.items():
        assert (root / doc).exists(), f"{gate} cites {doc}, which is missing"


def test_declared_blocking_gates_are_not_stale():
    """A gate that has started passing must leave the declared list.

    Otherwise the list becomes a place where failures go to be forgotten, which
    is the opposite of what declaring them is for.
    """
    c = gate_counts()
    failing = set(c["active_blocking_failure_names"])
    stale = [g for g in DECLARED_BLOCKING if g not in failing]
    assert not stale, f"passing gates still declared as blocking: {stale}"
