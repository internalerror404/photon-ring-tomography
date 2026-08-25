"""Governance counts, so a valid audit history is not read as unresolved failure.

The gate file accumulates every gate the program has ever run, and several of
its FAIL rows are deliberate: a defect preserved literally as written, a
statistic retired after it was shown not to converge, a convention retired after
it was shown to depend on pixelization. Printing a bare "N FAIL" next to those
invites the reader to count seven unresolved scientific failures where there are
none.

Three counts are therefore reported together everywhere a summary appears:

    active_blocking_failures   FAIL rows with no adjudicated disposition
    preserved_literal_failures FAIL rows carrying one
    future_phase_not_run       gates registered but not yet in scope

An adjudicated FAIL is still a FAIL. The status is never edited to match the
disposition; the disposition only says the failure has been ruled on.
"""
from __future__ import annotations

import json
from pathlib import Path

from phrt.config import repo_root


def gate_counts(path: str | Path | None = None) -> dict:
    p = Path(path) if path else repo_root() / "artifacts" / "gates" / "correctness_gates.json"
    gates = json.loads(p.read_text())["gates"]
    fails = {k: v for k, v in gates.items() if v["status"] == "FAIL"}
    active = {k: v for k, v in fails.items() if not v.get("disposition")}
    preserved = {k: v for k, v in fails.items() if v.get("disposition")}
    not_run = {k: v for k, v in gates.items() if v["status"] == "NOT_RUN"}
    return {
        "total_gates": len(gates),
        "passing": sum(1 for v in gates.values() if v["status"] == "PASS"),
        "active_blocking_failures": len(active),
        "preserved_literal_failures": len(preserved),
        "future_phase_not_run": len(not_run),
        "active_blocking_failure_names": sorted(active),
        "preserved_literal_failure_dispositions":
            {k: v["disposition"] for k, v in sorted(preserved.items())},
        "future_phase_not_run_names": sorted(not_run),
    }


def summary_block(path: str | Path | None = None) -> str:
    """The three counts, formatted for the head of any report."""
    c = gate_counts(path)
    lines = [
        f"    active_blocking_failures:   {c['active_blocking_failures']}",
        f"    preserved_literal_failures: {c['preserved_literal_failures']}",
        f"    future_phase_not_run:       {c['future_phase_not_run']}",
    ]
    out = ["```", *lines, "```", "",
           "A preserved literal failure is a FAIL that has been adjudicated and kept "
           "on the record rather than reinterpreted; the status is never edited to "
           "match the disposition. A not-run gate belongs to a phase that is not yet "
           "in scope. Neither is an unresolved scientific failure."]
    if c["preserved_literal_failures"]:
        out += ["", "| preserved failure | disposition |", "|---|---|"]
        out += [f"| `{k}` | `{v}` |" for k, v
                in c["preserved_literal_failure_dispositions"].items()]
    if c["active_blocking_failure_names"]:
        out += ["", "**Active blocking failures:** "
                + ", ".join(f"`{k}`" for k in c["active_blocking_failure_names"])]
    return "\n".join(out)
