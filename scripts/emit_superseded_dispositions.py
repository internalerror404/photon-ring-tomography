#!/usr/bin/env python3
"""Record dispositions for gate entries the ruling or later work superseded.

Statuses are never edited: a gate that failed keeps FAIL. What changes is the
disposition beside it, so the file cannot show a resolved or retired entry as a
live failure.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from phrt.config import load_registry
from phrt.io.manifests import Gate, RunManifest, make_run_id, merge_gate_file

UPDATES = [
    ("EDGE1_a000_i020_raymap_generation", "FAIL", "RESOLVED_BY_S0_BACKEND",
     "AART cannot generate a* = 0 and that remains true. The registered "
     "geometry is now produced by the S0 backend (kgeo geodesics, explicit "
     "Schwarzschild velocity, kgeo redshift), which passes all 19 S0 gates. "
     "The AART limitation is preserved as a fact about the backend, not as an "
     "open blocker."),
    ("G7_grid_convergence_a098_i075", "FAIL",
     "RETIRED_NONCONVERGENT_EXTREME_STATISTIC",
     "the failure was carried entirely by the sampled maximum ray delay, which "
     "the ruling retired as a convergence metric. Superseded by the weighted "
     "delay quantiles, which converge at this geometry (solid angle 1.49e-02, "
     "throughput 1.07e-02, Fisher 1.90e-02), and by the operator-level gate, "
     "which passes at 3.088e-02."),
    ("G7b_weighted_operator_discrepancy", "FAIL",
     "WITHDRAWN_INVALID_CONVERGENCE_METRIC",
     "an earlier name for the pointwise cross-grid field comparison. AART's "
     "per-ray fields are analytic and carry no discretisation error, so "
     "comparing field values between resolutions measures the field gradient "
     "across the grid offset. Superseded by the quadrature-weighted "
     "G7b_transfer_field_convergence."),
    ("GRID_AUTHORIZATION", "FAIL", "SUPERSEDED_GRID_COMPLETE",
     "recorded when one edge canary could not be generated and another failed a "
     "then-live gate. Both were resolved by the ruling and by the S0 backend; "
     "all 12 registered geometries are now generated and integrity-checked. "
     "The stop is preserved as the correct decision at the time."),
]


def main() -> int:
    t0 = time.time()
    reg = load_registry()
    run_id = make_run_id("DISP", reg.sha256)
    man = RunManifest(run_id=run_id, experiment_id="DISPOSITIONS")
    man.add_input(reg.path)
    for name, status, disposition, note in UPDATES:
        man.add_gate(Gate(name, status, disposition=disposition, note=note))
    mp = man.write(reg.path, reg.sha256, runtime_seconds=time.time() - t0)
    merge_gate_file(man.gates, run_id)
    for g in man.gates:
        print(f"  {g.name:44s} {g.status:6s} [{g.disposition}]")
    print(f"\nmanifest {mp}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
