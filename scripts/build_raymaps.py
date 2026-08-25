#!/usr/bin/env python3
"""P1-E3 -- generate physical Kerr ray maps with AART.

Runs in the pinned physics environment (see PHYSICS_ENV below), because AART
2.1.10 is incompatible with current scipy. AART itself is never modified: it is
imported and called through its documented entry points, and the incompatibility
is handled by giving it the interpreter it expects.

Pilot scope, as authorized: one geometry, a* = 0.5 and i = 50 degrees, orders
n = 0, 1, 2. This is one of the spin-angle combinations in AART's own README
example, so reproducing the official example and generating the pilot geometry
are the same run.

Emission model, declared here rather than discovered later:
  * equatorial, optically thin, geometrically thin;
  * fluid on circular Keplerian orbits outside the ISCO, plunging inside it
    (AART's own gfactorf convention, betaphi = betar = 1);
  * observed specific intensity carries g^GFACTOR_EXPONENT, matching the
    exponent used in AART's documented radial-intensity example.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from phrt.geometry.raymap import (EMISSION_R_OUTER, RayMap, horizon_radius,
                                  sha256, validity, write)

PHYSICS_ENV = "/tmp/aartvenv/bin/python"
GFACTOR_EXPONENT = 3.0
SUB_KEPLERIAN = 1.0
D_OBS = 1000.0
LIMITS = 25.0
THETA_DISK = np.pi / 2          # equatorial; radians, despite AART's docstring
NPOINTS_CRITICAL = 60

# Registered pilot resolutions. `core` is the pilot's working profile; the
# others exist for the convergence study and differ only in dx.
PROFILES = {
    "coarse": dict(dx0=0.8, dx1=0.16, dx2=0.04, npointsS=60),
    "core":   dict(dx0=0.4, dx1=0.08, dx2=0.02, npointsS=60),
    "fine":   dict(dx0=0.2, dx1=0.04, dx2=0.01, npointsS=60),
}


from phrt.config import geometry_id  # noqa: E402  (single source of truth)


def _guard_overwrite(path: Path, spin: float) -> None:
    """Refuse to overwrite a map that was generated for a different spin.

    The id collision that made this necessary is described in
    phrt.config.geometry_id. A silent overwrite of one geometry's maps by
    another's is not recoverable from the artifacts alone.
    """
    if not path.exists():
        return
    import h5py

    with h5py.File(path, "r") as f:
        existing = float(f["meta"].attrs["spin"])
    if abs(existing - spin) > 1e-15:
        raise SystemExit(
            f"refusing to overwrite {path.name}: it holds spin {existing!r} and "
            f"this run has spin {spin!r}. The geometry ids collide.")


def run_aart(spin: float, inc: float, profile: str, out_dir: Path) -> dict:
    """Call AART's documented entry points and return the raw arrays."""
    import h5py
    import aart.lensingbands as lbm
    import aart.raytracing as rtm
    from aart import intensity_f as obsint
    from aart.misc import rms

    cfg = PROFILES[profile]
    out_dir.mkdir(parents=True, exist_ok=True)
    params = dict(spins=[spin], i_angles=[inc], npointsS=cfg["npointsS"],
                  limits=LIMITS, thetad=THETA_DISK, D_obs=D_OBS, p_image=0,
                  dx0=cfg["dx0"], dx1=cfg["dx1"], dx2=cfg["dx2"], bvapp=0,
                  path=str(out_dir) + "/")

    t0 = time.time()
    lbm.clb(**params)
    t_bands = time.time() - t0
    t0 = time.time()
    rtm.raytrace(**params)
    t_rays = time.time() - t0

    tag = f"a_{spin}_i_{inc}_dx0_{cfg['dx0']}_dx1_{cfg['dx1']}_dx2_{cfg['dx2']}"
    bands = out_dir / f"LensingBands_{tag}.h5"
    rays = out_dir / f"Rays_a_{spin}_i_{inc}_bv_0_dx0_{cfg['dx0']}_dx1_{cfg['dx1']}_dx2_{cfg['dx2']}.h5"

    data = {}
    with h5py.File(bands, "r") as f, h5py.File(rays, "r") as r:
        isco = rms(spin)
        thetao = inc * np.pi / 180.0
        for n in (0, 1, 2):
            grid = f[f"grid{n}"][:]
            mask = f[f"mask{n}"][:]
            rs, phi = r[f"rs{n}"][:], r[f"phi{n}"][:]
            t, sign = r[f"t{n}"][:], r[f"sign{n}"][:]
            # AART's own redshift, called directly on the flat band arrays so no
            # reshape round-trip is needed and no filename aliasing is involved.
            # betaphi = betar = sub_kep = 1: fully Keplerian outside the ISCO,
            # AART's own plunging solution inside it. gfactorf returns a
            # full-length array with zeros off the band mask.
            gfac = obsint.gfactorf(grid, mask, sign, spin, isco, rs, phi,
                                   thetao, 1.0, 1.0, SUB_KEPLERIAN)
            data[n] = dict(grid=grid, mask=mask, rs=rs, phi=phi, t=t,
                           sign=sign, g=np.asarray(gfac).reshape(-1),
                           dx=cfg[f"dx{n}"])
    data["_timing"] = {"lensing_bands_seconds": t_bands, "raytrace_seconds": t_rays}
    data["_files"] = {"bands": str(bands), "rays": str(rays)}
    return data


def to_raymap(raw: dict, n: int, spin: float, inc: float, profile: str,
              t_reference: float) -> RayMap:
    d = raw[n]
    rs, phi, t = d["rs"], d["phi"], d["t"]
    valid = validity(rs, phi, t, spin, d["mask"])

    # Retarded age: non-negative, increasing into the past. One reference time
    # is shared across all orders of a geometry, otherwise each order would be
    # measured from its own zero and the delay ladder between orders -- the
    # entire point of the experiment -- would be subtracted away.
    delay = np.where(valid, t_reference - t, np.nan)

    g = np.where(np.isfinite(d["g"]), d["g"], np.nan)
    weight = np.where(valid, np.power(np.abs(g), GFACTOR_EXPONENT), 0.0)
    return RayMap(
        geometry_id=geometry_id(spin, inc), order=n, spin=spin,
        inclination_deg=inc, profile=profile,
        alpha=d["grid"][:, 0].copy(), beta=d["grid"][:, 1].copy(),
        source_r=rs.copy(), source_phi=np.mod(phi, 2 * np.pi),
        winding_phi=phi.copy(), delay=np.nan_to_num(delay, nan=0.0),
        coordinate_time=t.copy(), redshift=g,
        transfer_weight=weight,
        pixel_area=np.full(rs.size, d["dx"] ** 2),
        radial_sign=d["sign"].copy(), valid=valid,
        metadata={"dx": d["dx"], "t_reference": float(t_reference),
                  "gfactor_exponent": GFACTOR_EXPONENT,
                  "emission_r_outer": EMISSION_R_OUTER,
                  "horizon_radius": horizon_radius(spin),
                  "d_obs": D_OBS, "limits": LIMITS,
                  "npoints_critical": PROFILES[profile]["npointsS"]},
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--spin", type=float, default=0.5)
    ap.add_argument("--inclination", type=float, default=50.0)
    ap.add_argument("--profile", default="core", choices=sorted(PROFILES))
    ap.add_argument("--out", type=Path, default=ROOT / "artifacts" / "raymaps")
    ap.add_argument("--scratch", type=Path,
                    default=ROOT / "artifacts" / "e3_pilot" / "aart_out")
    args = ap.parse_args()

    t0 = time.time()
    raw = run_aart(args.spin, args.inclination, args.profile,
                   args.scratch / args.profile)

    # shared reference time across the three orders
    finite_t = np.concatenate([raw[n]["t"][np.isfinite(raw[n]["t"])] for n in (0, 1, 2)])
    t_reference = float(np.max(finite_t))

    gid = geometry_id(args.spin, args.inclination)
    written = []
    for n in (0, 1, 2):
        rm = to_raymap(raw, n, args.spin, args.inclination, args.profile, t_reference)
        target = args.out / f"{gid}_n{n}_{args.profile}.h5"
        _guard_overwrite(target, args.spin)
        p = write(rm, target)
        written.append({"path": str(p.relative_to(ROOT)), "sha256": sha256(p),
                        **rm.summary()})
        s = rm.summary()
        print(f"  n={n} {s['n_valid']:>7d}/{s['n_rays']:<7d} valid "
              f"({s['valid_fraction']*100:5.1f}%)  "
              f"r in [{s['source_r_range'][0]:.3f}, {s['source_r_range'][1]:.3f}]  "
              f"delay in [{s['delay_range'][0]:.2f}, {s['delay_range'][1]:.2f}]  "
              f"area {s['total_quadrature_area']:.4g}")

    manifest = {
        "geometry_id": gid, "spin": args.spin, "inclination_deg": args.inclination,
        "profile": args.profile, "t_reference": t_reference,
        "timing": raw["_timing"], "aart_files": raw["_files"],
        "runtime_seconds": time.time() - t0, "maps": written,
    }
    mp = args.out / f"{gid}_{args.profile}_manifest.json"
    mp.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"\nwrote {mp}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
