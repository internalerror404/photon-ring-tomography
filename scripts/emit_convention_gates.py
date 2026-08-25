#!/usr/bin/env python3
"""Split the convention gate into its three specific claims, and record the two
withdrawn/not-applicable dispositions."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from phrt.config import load_registry
from phrt.io.manifests import Gate, RunManifest, gate_from_tolerance, make_run_id, merge_gate_file


def main() -> int:
    t0 = time.time()
    reg = load_registry()
    g8 = json.loads((ROOT / "artifacts" / "e3_pilot" / "e3_validation.json").read_text())
    g8t = json.loads((ROOT / "artifacts" / "e3_pilot" / "g8t_retarded_time.json").read_text())["summary"]

    run_id = make_run_id("CONV", reg.sha256)
    man = RunManifest(run_id=run_id, experiment_id="CONVENTION_GATES")
    man.add_input(reg.path)

    r = float(g8["cross_tracer"]["worst_relative_difference"])
    man.add_gate(gate_from_tolerance(
        "G8r_source_radius_no_adjustment", r, 1e-9,
        note=f"AART against kgeo on equatorial source radius over "
             f"{g8['cross_tracer']['rays_checked']} stratified rays, compared on raw "
             f"screen coordinates with no sign flip, axis swap, angle offset or "
             f"rescaling applied to either side. The radius map needs no "
             f"adjustment of any kind."))

    man.add_gate(gate_from_tolerance(
        "G8t_emission_time_no_offset", abs(float(g8t["common_time_offset"])), 1e-6,
        note=f"fitted common additive offset between AART and kgeo emission "
             f"times over {g8t['rays_compared']} stratified rays. The two codes "
             f"share a time origin outright; no offset is removed anywhere, and "
             f"the pairwise-difference gate G8t_retarded_time_validation "
             f"({g8t['time_difference_max_absolute']:.3e} M) would hold even if "
             f"they did not."))

    man.add_gate(gate_from_tolerance(
        "G8phi_rigid_origin_alignment",
        float(g8t["azimuth_residual_after_rigid_offset_max"]), 1e-8,
        note=f"azimuth DOES need an alignment, and it is a single rigid rotation: "
             f"phi_kgeo = phi_aart + pi/2, exact to "
             f"{g8t['azimuth_offset_deviation_from_exact_quarter_turn']:.3e}, with "
             f"residual {g8t['azimuth_residual_after_rigid_offset_max']:.3e} rad "
             f"after one global constant and a spread across orders of "
             f"{g8t['azimuth_offset_spread_across_orders']:.3e} rad. A reflection "
             f"was tested and rejected. The repository adopts AART's origin. "
             f"Unlike radius and time, this gate certifies alignment, not the "
             f"absence of a difference."))

    man.add_gate(Gate(
        "E3_pilot_no_convention_adjustment", "NOT_RUN", disposition="REPLACED",
        note="a single gate could not distinguish 'needed no adjustment' "
             "(radius, time) from 'needed exactly one rigid rotation' (azimuth). "
             "Replaced by G8r_source_radius_no_adjustment, "
             "G8t_emission_time_no_offset and G8phi_rigid_origin_alignment."))

    man.add_gate(Gate(
        "G7b_pointwise_cross_grid_field_metric", "NOT_RUN",
        disposition="WITHDRAWN_INVALID_CONVERGENCE_METRIC",
        measured=0.366, threshold=0.05,
        note="compared transfer-field values between resolutions at matched "
             "screen points and read 0.366. Invalid as a convergence metric: "
             "AART's landing coordinates are analytic in (alpha, beta) and "
             "agree with the grid-free kgeo to 2.6e-15 (n=0), 1.1e-13 (n=1) and "
             "2.2e-12 (n=2) at BOTH resolutions, so the per-ray fields carry no "
             "discretisation error. Two profiles never evaluate the same point, "
             "so the number measured the field gradient across the grid offset "
             "-- band steepness -- not convergence. Superseded by the "
             "quadrature-weighted G7b_transfer_field_convergence, which PASSES "
             "at 2.192e-02. The failing value is preserved here rather than "
             "deleted."))

    mp = man.write(reg.path, reg.sha256, runtime_seconds=time.time() - t0)
    merge_gate_file(man.gates, run_id)
    for g in man.gates:
        m = g.measured
        ms = f"{m:.3e}" if isinstance(m, float) else str(m)
        dis = f"  [{g.disposition}]" if g.disposition else ""
        print(f"  {g.name:42s} {g.status:8s} {ms:>12s}{dis}")
    return 1 if man.failed_gates else 0


if __name__ == "__main__":
    raise SystemExit(main())
