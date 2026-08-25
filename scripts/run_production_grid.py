#!/usr/bin/env python3
"""Generate the registered 12-geometry ray-map grid, fail-fast.

Source-independent maps only: no source model, no operator, no ML. Each
geometry is checked for integrity as soon as it is written, and the run stops
on the first failure rather than producing eleven more maps behind a broken one.

Backend is chosen by spin: the Schwarzschild point uses the S0 backend, because
AART is singular at exactly a = 0 (see artifacts/reports/S0_BACKEND_CANARY.md).
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from phrt.config import geometry_id, load_registry
from phrt.geometry.raymap import horizon_radius, read
from phrt.io.manifests import Gate, RunManifest, make_run_id, merge_gate_file
from phrt.io.tables import write_table

PHYSICS = "/tmp/aartvenv/bin/python"
PROFILE = "core"
REQUIRED_RAYS = 1536


def build(spin: float, inc: float) -> tuple[bool, str]:
    if spin == 0.0:
        cmd = [PHYSICS, str(ROOT / "scripts" / "build_raymaps_schwarzschild.py"),
               "--inclination", str(inc), "--profile", PROFILE]
    else:
        cmd = [PHYSICS, str(ROOT / "scripts" / "build_raymaps.py"),
               "--spin", str(spin), "--inclination", str(inc), "--profile", PROFILE]
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
    return r.returncode == 0, (r.stderr or r.stdout)[-400:]


def integrity(gid: str, spin: float) -> tuple[bool, dict]:
    out = {"geometry_id": gid, "spin": spin}
    try:
        maps = [read(ROOT / "artifacts" / "raymaps" / f"{gid}_n{n}_{PROFILE}.h5")
                for n in (0, 1, 2)]
    except Exception as exc:                                    # noqa: BLE001
        return False, out | {"status": f"unreadable: {exc}"}
    rh = horizon_radius(spin)
    counts = [m.n_valid for m in maps]
    finite = all(np.isfinite(m.transfer_weight[m.valid]).all()
                 and (m.transfer_weight[m.valid] > 0).all()
                 and np.isfinite(m.delay[m.valid]).all()
                 and np.isfinite(m.source_r[m.valid]).all() for m in maps)
    inside = min(float(m.source_r[m.valid].min()) for m in maps)
    ordered = all(float(maps[i].delay[maps[i].valid].min())
                  < float(maps[i + 1].delay[maps[i + 1].valid].min()) for i in range(2))
    shared_ref = len({m.metadata["t_reference"] for m in maps}) == 1
    ok = (min(counts) >= REQUIRED_RAYS and finite and inside > rh - 1e-9
          and ordered and shared_ref)
    out |= {"status": "ok" if ok else "FAILED",
            "n0": counts[0], "n1": counts[1], "n2": counts[2],
            "min_per_order": min(counts), "r_min": inside,
            "horizon": rh, "finite_weights": finite,
            "delay_windows_ordered": ordered, "shared_time_reference": shared_ref,
            "delay_min_n0": float(maps[0].delay[maps[0].valid].min()),
            "delay_min_n2": float(maps[2].delay[maps[2].valid].min()),
            "area_n0": float(np.sum(maps[0].pixel_area[maps[0].valid])),
            "area_n2": float(np.sum(maps[2].pixel_area[maps[2].valid]))}
    return ok, out


def main() -> int:
    t0 = time.time()
    reg = load_registry()
    grid = reg.geometry_grid()
    rows, failed = [], None
    print(f"registered grid: {len(grid)} geometries\n")
    for spin, inc in grid:
        gid = geometry_id(spin, inc)
        exists = all((ROOT / "artifacts" / "raymaps" / f"{gid}_n{n}_{PROFILE}.h5").exists()
                     for n in (0, 1, 2))
        if not exists:
            ok, msg = build(spin, inc)
            if not ok:
                print(f"  {gid}  BUILD FAILED\n    {msg}")
                rows.append({"geometry_id": gid, "spin": spin, "status": "BUILD_FAILED"})
                failed = gid
                break
        ok, row = integrity(gid, spin)
        row["inclination_deg"] = inc
        row["cached"] = exists
        rows.append(row)
        tag = "cached" if exists else "built "
        print(f"  {gid}  {tag}  {'ok ' if ok else 'FAIL'}  "
              f"rays {row.get('n0','?'):>6}/{row.get('n1','?'):>6}/{row.get('n2','?'):>6}  "
              f"r_min {row.get('r_min', float('nan')):.4f} (horizon {row.get('horizon', float('nan')):.4f})")
        if not ok:
            failed = gid
            break

    run_id = make_run_id("GRID", reg.sha256)
    man = RunManifest(run_id=run_id, experiment_id="PRODUCTION_GRID")
    man.add_input(reg.path)
    done = [r for r in rows if r.get("status") == "ok"]
    man.add_gate(Gate(
        "GRID_all_registered_geometries", "PASS" if len(done) == len(grid) else "FAIL",
        measured=len(done), threshold=len(grid),
        note=f"{len(done)} of {len(grid)} registered geometries generated and "
             f"integrity-checked" + (f"; stopped at {failed}" if failed else "")))
    if done:
        man.add_gate(Gate(
            "GRID_min_rays_per_order", "PASS" if min(r["min_per_order"] for r in done) >= REQUIRED_RAYS else "FAIL",
            measured=min(r["min_per_order"] for r in done), threshold=REQUIRED_RAYS,
            note="smallest per-order valid ray count across every generated geometry"))
        man.add_gate(Gate(
            "GRID_delay_windows_ordered",
            "PASS" if all(r["delay_windows_ordered"] for r in done) else "FAIL",
            measured=int(all(r["delay_windows_ordered"] for r in done)), threshold=1,
            note="each higher order's retarded window starts further into the past"))
        man.add_gate(Gate(
            "GRID_shared_time_reference",
            "PASS" if all(r["shared_time_reference"] for r in done) else "FAIL",
            measured=int(all(r["shared_time_reference"] for r in done)), threshold=1,
            note="one reference time per geometry; per-order references would "
                 "subtract away the delay ladder between orders"))
        man.add_gate(Gate(
            "GRID_no_ray_inside_horizon",
            "PASS" if all(r["r_min"] > r["horizon"] - 1e-9 for r in done) else "FAIL",
            measured=min(r["r_min"] - r["horizon"] for r in done), threshold=0.0))
    write_table(rows, "production_grid_inventory")
    mp = man.write(reg.path, reg.sha256, runtime_seconds=time.time() - t0)
    merge_gate_file(man.gates, run_id)
    print("\ngates")
    for g in man.gates:
        m = g.measured
        print(f"  {g.name:36s} {g.status:8s} {m}")
    print(f"\nmanifest {mp}\ntotal {time.time()-t0:.0f}s")
    return 1 if man.failed_gates else 0


if __name__ == "__main__":
    raise SystemExit(main())
