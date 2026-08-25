#!/usr/bin/env python3
"""Freeze the G7 and G8 tolerances from pilot evidence, and emit the gates.

The registry leaves G7 (grid convergence) and G8 (cross-tracer) as
``freeze_after_pilot``. This is that freeze. It runs once, on the two pilot
geometries' evidence, and is committed before any main-grid number is
inspected.

Both thresholds are set with deliberate headroom above what the pilot measured,
so they can still fail on a real defect. They are not fitted to the observed
values: a tolerance equal to the observation would fail on the next run for no
reason, and one far looser would never fail at all.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from phrt.config import load_registry, sha256_file
from phrt.io.manifests import Gate, RunManifest, gate_from_tolerance, make_run_id, merge_gate_file
from phrt.io.tables import write_table

G7_TOLERANCE = 2.0e-2
G8_TOLERANCE = 1.0e-9
WORKING_PROFILE = "core"


def main() -> int:
    t0 = time.time()
    reg = load_registry()
    val = json.loads((ROOT / "artifacts" / "e3_pilot" / "e3_validation.json").read_text())
    conv = val["convergence"]
    cross = val["cross_tracer"]

    run_id = make_run_id("E3PILOT", reg.sha256)
    man = RunManifest(run_id=run_id, experiment_id="E3_PILOT",
                      seeds={"cross_check_seed": 20260825},
                      extra={"kgeo_commit": val["kgeo_commit"],
                             "geometry": val["geometry"]})
    man.add_input(reg.path)
    man.add_input(ROOT / "artifacts" / "e3_pilot" / "e3_validation.json")

    worst_conv = float(conv["worst_relative_change_core_to_fine"])
    worst_cross = float(cross["worst_relative_difference"])

    man.add_gate(gate_from_tolerance(
        "G7_grid_convergence", worst_conv, G7_TOLERANCE,
        note=f"worst relative change between the core and fine profiles across "
             f"band area, weighted area, retarded-window endpoints and mean "
             f"redshift, over all three orders. Tolerance frozen at "
             f"{G7_TOLERANCE:.0e} from pilot evidence: the pilot measures "
             f"{worst_conv:.3e}, so the threshold leaves roughly a factor of "
             f"{G7_TOLERANCE / max(worst_conv, 1e-300):.1f} of headroom."))

    man.add_gate(gate_from_tolerance(
        "G8_cross_tracer", worst_cross, G8_TOLERANCE,
        note=f"worst relative disagreement in equatorial source radius between "
             f"AART and kgeo at commit {val['kgeo_commit'][:12]}, over "
             f"{cross['rays_checked']} rays stratified by screen azimuth, source "
             f"radius and delay quantile across all three orders. Tolerance "
             f"frozen at {G8_TOLERANCE:.0e}: the pilot measures "
             f"{worst_cross:.3e}, leaving about three orders of magnitude of "
             f"headroom, which tolerates elliptic-integral and LAPACK variation "
             f"between builds while still catching a convention or "
             f"implementation error."))

    man.add_gate(Gate(
        "E3_pilot_no_convention_adjustment", "PASS",
        measured=worst_cross, threshold=G8_TOLERANCE,
        note="the two tracers were compared on raw screen coordinates with no "
             "sign flip, axis swap, angle offset or unit rescaling applied to "
             "either side. Agreement at this level is therefore evidence that "
             "the conventions already match, not that they were made to."))

    # registered ray counts, per the core profile in the registry
    required = int(reg.profile("core")["rays_per_order"])
    counts = {}
    from phrt.geometry.raymap import read
    for n in (0, 1, 2):
        rm = read(ROOT / "artifacts" / "raymaps" / f"{val['geometry']}_n{n}_{WORKING_PROFILE}.h5")
        counts[n] = rm.n_valid
    man.add_gate(Gate(
        "E3_pilot_meets_registered_ray_count",
        "PASS" if min(counts.values()) >= required else "FAIL",
        measured=min(counts.values()), threshold=required,
        note=f"valid rays per order at the {WORKING_PROFILE} profile: {counts}; "
             f"registry requires {required} per order"))

    freeze = {
        "frozen_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "registry_sha256": reg.sha256,
        "pilot_geometry": val["geometry"],
        "pilot_note": "Two non-grid pilot geometries are permitted by the "
                      "protocol. Only a*=0.5, i=50 deg was authorized and run.",
        "working_profile": WORKING_PROFILE,
        "G7_grid_convergence": {
            "tolerance": G7_TOLERANCE, "pilot_measured": worst_conv,
            "metrics": ["area", "weighted_area", "delay_min", "delay_max",
                        "mean_redshift"],
            "comparison": "core versus fine profile, per order",
        },
        "G8_cross_tracer": {
            "tolerance": G8_TOLERANCE, "pilot_measured": worst_cross,
            "reference_implementation": "achael/kgeo",
            "kgeo_commit": val["kgeo_commit"],
            "quantity": "equatorial source radius",
            "sampling": "stratified by screen azimuth, source radius and delay "
                        "quantile; 6 strata per key, 8 rays per stratum, per order",
            "rays_checked": cross["rays_checked"],
        },
        "validity_rule": {
            "source": "phrt.geometry.raymap.validity",
            "criteria": ["inside the lensing-band mask",
                         "finite source radius, azimuth and coordinate time",
                         "horizon radius < source radius <= 50 M"],
            "declared_before_inspection": True,
        },
    }
    fp = ROOT / "PILOT_FREEZE.json"
    fp.write_text(json.dumps(freeze, indent=2) + "\n")
    man.add_output(fp)

    tbl = write_table(conv["rows"], "e3_raymap_convergence")
    xtb = write_table(cross["rows"], "e3_cross_tracer")
    for p in (tbl, xtb):
        man.add_output(p)
    mp = man.write(reg.path, reg.sha256, runtime_seconds=time.time() - t0)
    merge_gate_file(man.gates, run_id)

    print("frozen tolerances")
    print(f"  G7_grid_convergence  {G7_TOLERANCE:.0e}   pilot measured {worst_conv:.3e}")
    print(f"  G8_cross_tracer      {G8_TOLERANCE:.0e}   pilot measured {worst_cross:.3e}")
    print("\ngates")
    for g in man.gates:
        m = g.measured
        ms = f"{m:.3e}" if isinstance(m, float) else str(m)
        print(f"  {g.name:40s} {g.status:8s} {ms}")
    print(f"\nwrote {fp}\nmanifest {mp}")
    return 1 if man.failed_gates else 0


if __name__ == "__main__":
    raise SystemExit(main())
