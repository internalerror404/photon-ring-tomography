#!/usr/bin/env python3
"""Emit the governance dashboard: the three counts plus the full gate roll."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from phrt import provenance
from phrt.io.dashboard import gate_counts, summary_block


def main() -> int:
    c = gate_counts()
    prov = provenance.collect()
    doc = {"schema": "phrt-gate-dashboard/1",
           "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "git_commit": prov.git_commit, **c}
    (ROOT / "artifacts" / "GATE_DASHBOARD.json").write_text(
        json.dumps(doc, indent=2) + "\n")

    gates = json.loads((ROOT / "artifacts" / "gates"
                        / "correctness_gates.json").read_text())["gates"]
    roll = ["| gate | status | disposition | measured | threshold |",
            "|---|---|---|---:|---:|"]
    for k in sorted(gates):
        v = gates[k]
        m = v.get("measured", "–")
        m = f"{m:.4g}" if isinstance(m, float) else str(m)
        t = v.get("threshold", "–")
        t = f"{t:.4g}" if isinstance(t, float) else str(t)
        roll.append(f"| `{k}` | {v['status']} | "
                    f"{('`' + v['disposition'] + '`') if v.get('disposition') else '–'} "
                    f"| {m} | {t} |")

    (ROOT / "artifacts" / "reports" / "GATE_DASHBOARD.md").write_text(
        f"""# GATE DASHBOARD

- commit `{prov.git_commit}`
- {c['total_gates']} gates, {c['passing']} passing

{summary_block()}

## Full roll

{chr(10).join(roll)}
""")
    print("wrote artifacts/GATE_DASHBOARD.json")
    print("wrote artifacts/reports/GATE_DASHBOARD.md")
    for k in ("active_blocking_failures", "preserved_literal_failures",
              "future_phase_not_run"):
        print(f"  {k}: {c[k]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
