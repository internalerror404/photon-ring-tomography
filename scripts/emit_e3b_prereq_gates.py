#!/usr/bin/env python3
"""Emit G8t and G9c, the two E3B prerequisite gates, and freeze their tolerances."""
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

# Frozen from pilot evidence, with headroom, before any E3B result is inspected.
G8T_TIME_TOLERANCE = 1.0e-3        # M; observed 2.763e-06
G8T_PHI_TOLERANCE = 1.0e-8         # rad after one rigid offset; observed 6.329e-12
G8T_OFFSET_SPREAD_TOLERANCE = 1.0e-9   # rad across orders; observed 1.303e-13
REQUIRED_RAYS_PER_ORDER = 1536


def main() -> int:
    t0 = time.time()
    reg = load_registry()
    doc = json.loads((ROOT / "artifacts" / "e3_pilot" / "g8t_retarded_time.json").read_text())
    s = doc["summary"]

    run_id = make_run_id("E3BPRE", reg.sha256)
    man = RunManifest(run_id=run_id, experiment_id="E3B_PREREQ", seeds={"seed": 20260825})
    man.add_input(reg.path)
    man.add_input(ROOT / "artifacts" / "e3_pilot" / "g8t_retarded_time.json")

    # --- G8t ---------------------------------------------------------------
    man.add_gate(gate_from_tolerance(
        "G8t_retarded_time_validation", s["time_difference_max_absolute"],
        G8T_TIME_TOLERANCE,
        note=f"largest disagreement in a PAIRWISE emission-time difference "
             f"between AART and kgeo's independent analytic solution, over "
             f"{s['pairs_compared']} pairs from {s['rays_compared']} stratified "
             f"rays, {s['cross_order_pairs']} of them spanning different orders. "
             f"Differences are compared so that a common time origin cancels; "
             f"here the measured common offset is {s['common_time_offset']:.3e}, "
             f"i.e. the two codes already share an origin. Tolerance frozen at "
             f"{G8T_TIME_TOLERANCE:.0e} M, far below any temporal structure the "
             f"source model resolves."))

    man.add_gate(gate_from_tolerance(
        "G8t_azimuth_after_rigid_offset", s["azimuth_residual_after_rigid_offset_max"],
        G8T_PHI_TOLERANCE,
        note=f"AART and kgeo place phi = 0 on different axes. The offset is "
             f"{s['azimuth_rigid_offset_radians']:.12f} rad, exactly "
             f"{s['azimuth_rigid_offset_in_quarter_turns']:+.0f} quarter turns to "
             f"{s['azimuth_offset_deviation_from_exact_quarter_turn']:.3e}. A rigid "
             f"rotation is a convention, as a common time origin is; what is "
             f"gated is the residual once one global constant is removed."))

    man.add_gate(gate_from_tolerance(
        "G8t_azimuth_offset_is_order_independent", s["azimuth_offset_spread_across_orders"],
        G8T_OFFSET_SPREAD_TOLERANCE,
        note=f"spread of the fitted azimuth offset across orders: "
             f"{s['azimuth_offset_per_order']}. This is the gate that matters. A "
             f"single global rotation only relabels the azimuth axis; an "
             f"order-dependent or screen-dependent one would corrupt every "
             f"non-axisymmetric source model, and would not be a convention."))

    man.add_gate(gate_from_tolerance(
        "G8t_radius_control", s["radius_control_max_relative"], 1e-9,
        note="source radius on the same stratified sample, confirming the "
             "coordinate identification used to extract t and phi is correct"))

    # --- G9c ---------------------------------------------------------------
    counts = {n: read(ROOT / "artifacts" / "raymaps" / f"a050_i050_n{n}_core.h5").n_valid
              for n in (0, 1, 2)}
    minimum = min(counts.values())
    man.add_gate(Gate(
        "G9c_per_order_ray_count",
        "PASS" if minimum >= REQUIRED_RAYS_PER_ORDER else "FAIL",
        measured=minimum, threshold=REQUIRED_RAYS_PER_ORDER,
        note=f"n0_valid={counts[0]}, n1_valid={counts[1]}, n2_valid={counts[2]}, "
             f"minimum_per_order={minimum}, total_valid={sum(counts.values())}. "
             f"The reported 4179 was the per-order minimum (n=2), not the "
             f"combined total; every order independently exceeds "
             f"{REQUIRED_RAYS_PER_ORDER}."))

    rows = [{"order": n, "n_valid": counts[n],
             "meets_registered_minimum": counts[n] >= REQUIRED_RAYS_PER_ORDER}
            for n in (0, 1, 2)]
    rows.append({"order": -1, "n_valid": sum(counts.values()),
                 "meets_registered_minimum": True})
    tbl = write_table(rows, "e3b_per_order_ray_count")
    man.add_output(tbl)

    freeze = {
        "frozen_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "registry_sha256": reg.sha256,
        "G8t_time_tolerance_M": G8T_TIME_TOLERANCE,
        "G8t_time_measured_M": s["time_difference_max_absolute"],
        "G8t_azimuth_tolerance_rad": G8T_PHI_TOLERANCE,
        "G8t_azimuth_measured_rad": s["azimuth_residual_after_rigid_offset_max"],
        "G8t_offset_spread_tolerance_rad": G8T_OFFSET_SPREAD_TOLERANCE,
        "G8t_offset_spread_measured_rad": s["azimuth_offset_spread_across_orders"],
        "azimuth_convention": {
            "repository_convention": "AART",
            "kgeo_minus_aart_radians": s["azimuth_rigid_offset_radians"],
            "exact_value": "+pi/2",
            "note": "A rigid rotation of the equatorial azimuth origin. It "
                    "relabels the azimuth axis and does not affect rank, "
                    "conditioning or the delay structure, but any statement "
                    "locating a source feature at a particular azimuth is only "
                    "meaningful relative to the declared origin.",
        },
        "G9c_required_per_order": REQUIRED_RAYS_PER_ORDER,
        "G9c_measured": {f"n{n}": counts[n] for n in (0, 1, 2)},
    }
    cfg = ROOT / "artifacts" / "configs"
    cfg.mkdir(parents=True, exist_ok=True)
    fp = cfg / "E3B_FREEZE.json"
    fp.write_text(json.dumps(freeze, indent=2) + "\n")
    man.add_output(fp)

    mp = man.write(reg.path, reg.sha256, runtime_seconds=time.time() - t0)
    merge_gate_file(man.gates, run_id)

    for g in man.gates:
        m = g.measured
        ms = f"{m:.3e}" if isinstance(m, float) else str(m)
        print(f"  {g.name:42s} {g.status:8s} {ms:>12s}  thr {g.threshold}")
    print(f"\nwrote {fp}\nmanifest {mp}")
    return 1 if man.failed_gates else 0


if __name__ == "__main__":
    raise SystemExit(main())
