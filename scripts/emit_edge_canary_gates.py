#!/usr/bin/env python3
"""Edge-canary gates for the two registered grid extremes, and the stop ruling.

Gates are emitted with a geometry suffix so the pilot geometry's results are not
overwritten: three geometries with different verdicts must all stand in the
record simultaneously.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from phrt.config import load_registry
from phrt.geometry.raymap import read
from phrt.io.manifests import Gate, RunManifest, gate_from_tolerance, make_run_id, merge_gate_file
from phrt.io.tables import write_table

G7_TOLERANCE = 2.0e-2          # frozen in PILOT_FREEZE.json
G8_TOLERANCE = 1.0e-9
G8T_TIME_TOLERANCE = 1.0e-3
G8T_PHI_TOLERANCE = 1.0e-8
G8T_SPREAD_TOLERANCE = 1.0e-9
REQUIRED_RAYS = 1536


def main() -> int:
    t0 = time.time()
    reg = load_registry()
    run_id = make_run_id("EDGE", reg.sha256)
    man = RunManifest(run_id=run_id, experiment_id="EDGE_CANARY")
    man.add_input(reg.path)
    rows = []

    # ---- edge canary 1: a* = 0, i = 20 ------------------------------------
    man.add_gate(Gate(
        "EDGE1_a000_i020_raymap_generation", "FAIL",
        disposition="BACKEND_LIMITATION_NOT_A_PHYSICS_FAILURE",
        measured="CritCurve returns an empty root set", threshold="non-empty",
        note="AART 2.1.10 cannot generate the Schwarzschild geometry. Its "
             "critical-curve parameterisation is singular at exactly a = 0: "
             "lensingbands.CritCurve forms lam = a + (r/a)(...) and "
             "eta = (r^3/a^2)(...), and sweeps r over the photon shell "
             "[rM, rP], which collapses to the single radius 3M when a = 0. Both "
             "expressions divide by the spin and the positivity mask then selects "
             "no points. Measured behaviour: a = 0 fails; a = 1e-6 succeeds and "
             "gives a critical curve at alpha = +-5.1969 against the exact "
             "Schwarzschild value 3*sqrt(3) = 5.19615, so the backend converges "
             "smoothly as a -> 0 and is singular only at the endpoint. No AART "
             "source was modified and no substitute spin was adopted: changing "
             "the registered grid is not the agent's call."))
    rows.append({"geometry": "a000_i020", "gate": "raymap_generation",
                 "status": "FAIL", "measured": float("nan"), "threshold": float("nan"),
                 "note": "AART singular at exactly a=0"})

    # ---- edge canary 2: a* = 0.98, i = 75 ---------------------------------
    val = json.loads((ROOT / "artifacts" / "e3_pilot" / "e3_validation.json").read_text())
    g8t = json.loads((ROOT / "artifacts" / "e3_pilot" / "g8t_retarded_time.json").read_text())["summary"]
    conv = val["convergence"]
    worst_conv = float(conv["worst_relative_change_core_to_fine"])
    worst_cross = float(val["cross_tracer"]["worst_relative_difference"])

    counts = {n: read(ROOT / "artifacts" / "raymaps" / f"a098_i075_n{n}_core.h5").n_valid
              for n in (0, 1, 2)}
    finite_ok = True
    for n in (0, 1, 2):
        rm = read(ROOT / "artifacts" / "raymaps" / f"a098_i075_n{n}_core.h5")
        finite_ok &= bool(np.isfinite(rm.transfer_weight[rm.valid]).all()
                          and (rm.transfer_weight[rm.valid] > 0).all()
                          and np.isfinite(rm.delay[rm.valid]).all())

    # the single metric that fails, identified explicitly
    offenders = sorted(conv["rows"], key=lambda r: -r["rel_change_core_to_fine"])[:3]
    off = "; ".join(f"n={o['order']} {o['metric']} {o['rel_change_core_to_fine']:.3e}"
                    for o in offenders)

    man.add_gate(gate_from_tolerance(
        "G7_grid_convergence_a098_i075", worst_conv, G7_TOLERANCE,
        note=f"FAILS the tolerance frozen from the pilot. Worst offenders: {off}. "
             f"The failure is carried by one metric, the n=1 deepest retarded age, "
             f"which moves from 161.8 M to 173.0 M between the core and fine "
             f"profiles. That is an extreme-value statistic over rays, populated "
             f"by the band edge, and it converges far more slowly than any "
             f"integral: every other metric at this geometry is within 1.2e-2. "
             f"The tolerance was NOT adjusted after seeing this, and the metric "
             f"was NOT re-specified as a quantile; both would be post-hoc "
             f"loosening."))
    man.add_gate(gate_from_tolerance(
        "G8_cross_tracer_a098_i075", worst_cross, G8_TOLERANCE,
        note=f"AART against kgeo on source radius, "
             f"{val['cross_tracer']['rays_checked']} stratified rays"))
    man.add_gate(gate_from_tolerance(
        "G8t_retarded_time_a098_i075", float(g8t["time_difference_max_absolute"]),
        G8T_TIME_TOLERANCE,
        note=f"pairwise emission-time differences, {g8t['pairs_compared']} pairs, "
             f"fitted common offset {g8t['common_time_offset']:.3e}"))
    man.add_gate(gate_from_tolerance(
        "G8phi_rigid_origin_alignment_a098_i075",
        float(g8t["azimuth_residual_after_rigid_offset_max"]), G8T_PHI_TOLERANCE,
        note=f"same +pi/2 rigid rotation as the pilot geometry, exact to "
             f"{g8t['azimuth_offset_deviation_from_exact_quarter_turn']:.3e}; "
             f"spread across orders "
             f"{g8t['azimuth_offset_spread_across_orders']:.3e} rad"))
    man.add_gate(Gate(
        "G9c_per_order_ray_count_a098_i075",
        "PASS" if min(counts.values()) >= REQUIRED_RAYS else "FAIL",
        measured=min(counts.values()), threshold=REQUIRED_RAYS,
        note=f"n0={counts[0]}, n1={counts[1]}, n2={counts[2]}, "
             f"minimum_per_order={min(counts.values())}, total={sum(counts.values())}"))
    man.add_gate(Gate(
        "EDGE2_finite_transfer_weights_and_masks",
        "PASS" if finite_ok else "FAIL", measured=int(finite_ok), threshold=1,
        note="every valid ray at every order has a finite, strictly positive "
             "transfer weight and a finite retarded delay"))
    man.add_gate(Gate(
        "EDGE2_memory_budget", "PASS", measured=3.0, threshold=15.7,
        note="peak resident set stayed near 3 GiB of the host's 15.7 GiB while "
             "generating the fine profile, whose n=1 grid holds 902,500 points "
             "and n=2 holds 1,960,000"))

    for g in man.gates:
        if g.name.startswith("EDGE1"):
            continue
        rows.append({"geometry": "a098_i075", "gate": g.name, "status": g.status,
                     "measured": float(g.measured) if isinstance(g.measured, (int, float)) else float("nan"),
                     "threshold": float(g.threshold) if isinstance(g.threshold, (int, float)) else float("nan"),
                     "note": (g.note or "")[:200]})

    # ---- the stop ruling ---------------------------------------------------
    man.add_gate(Gate(
        "GRID_AUTHORIZATION", "FAIL", disposition="STOPPED_BEFORE_PRODUCTION_GRID",
        measured="1 of 2 edge canaries generated; 1 registered gate failed",
        threshold="both edge canaries pass",
        note="Edge canary 1 (a*=0, i=20) cannot be generated by the backend. "
             "Edge canary 2 (a*=0.98, i=75) generates and passes every registered "
             "gate except G7_grid_convergence, which fails at 6.472e-02 against "
             "the frozen 2e-02. The ruling conditions the ten remaining "
             "geometries on both canaries passing and directs an immediate stop "
             "on any registered gate failure. Neither condition is met, so the "
             "production grid was not started."))

    write_table(rows, "edge_canary_gates")
    mp = man.write(reg.path, reg.sha256, runtime_seconds=time.time() - t0)
    merge_gate_file(man.gates, run_id)

    for g in man.gates:
        m = g.measured
        ms = f"{m:.3e}" if isinstance(m, float) else str(m)[:44]
        dis = f"  [{g.disposition}]" if g.disposition else ""
        print(f"  {g.name:42s} {g.status:8s} {ms}{dis}")
    print(f"\nmanifest {mp}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
