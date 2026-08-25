#!/usr/bin/env python3
"""S0 -- exact Schwarzschild ray maps for the registered a* = 0 geometry.

Composition, chosen so that each piece comes from the source that is correct
for it:

  geodesics   kgeo, which is exact at a = 0 and reproduces AART to 2e-12 at
              every spin tested;
  bands       kgeo ``nmax_equatorial``, which labels a screen point by how many
              equatorial crossings its ray makes -- the definition of a lensing
              band, and free of the critical-curve parameterisation that makes
              AART singular at zero spin;
  velocity    the explicit Schwarzschild branch in phrt.geometry.schwarzschild,
              because kgeo's u_kep returns a non-rotating disk at a = 0;
  redshift    kgeo's own calc_redshift, fed the corrected velocity, so the
              formula stays independent of this repository.

Output is the same RayMap schema, validity rule and quadrature convention as
the AART path, so downstream code cannot tell which backend produced a map
except by reading its metadata.
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
from phrt.geometry.schwarzschild import keplerian_u

D_OBS = 1000.0
LIMITS = 25.0
GFACTOR_EXPONENT = 3.0
PROFILES = {
    "coarse": dict(dx0=0.8, dx1=0.16, dx2=0.04),
    "core":   dict(dx0=0.4, dx1=0.08, dx2=0.02),
    "fine":   dict(dx0=0.2, dx1=0.04, dx2=0.01),
}
# Band bounding boxes in M. The Schwarzschild critical curve is an exact circle
# at b = 3*sqrt(3) = 5.196 M, so the higher-order bands hug it and do not need
# the full field of view.
BAND_LIMITS = {0: LIMITS, 1: 8.0, 2: 6.0}


def conserved(alpha: np.ndarray, beta: np.ndarray, th_o: float) -> tuple[np.ndarray, np.ndarray]:
    """Bardeen's (lambda, eta) at a = 0."""
    lam = -alpha * np.sin(th_o)
    eta = (alpha ** 2) * np.cos(th_o) ** 2 + beta ** 2
    return lam, eta


def band_grid(order: int, dx: float, th_o: float):
    """Screen points whose rays make at least `order` equatorial crossings."""
    from kgeo import equatorial_lensing as el

    lim = BAND_LIMITS[order]
    n = int(np.ceil(2 * lim / dx))
    x = np.linspace(-lim, lim, n)
    A, B = np.meshgrid(x, x, indexing="ij")
    alpha, beta = A.reshape(-1), B.reshape(-1)
    nmax = np.asarray(el.nmax_equatorial(0.0, D_OBS, th_o, alpha, beta)).ravel()
    mask = np.isfinite(nmax) & (nmax >= order)
    return alpha, beta, mask


def build_order(order: int, dx: float, inc: float, t_reference: float | None):
    from kgeo import equatorial_lensing as el
    from kgeo import kerr_raytracing_ana as ana
    from kgeo.equatorial_images import calc_redshift

    th_o = inc * np.pi / 180.0
    alpha, beta, mask = band_grid(order, dx, th_o)
    n_pts = alpha.size
    rs = np.full(n_pts, np.nan)
    ts = np.full(n_pts, np.nan)
    ph = np.full(n_pts, np.nan)
    gg = np.zeros(n_pts)
    sign = np.zeros(n_pts)

    idx = np.where(mask)[0]
    if idx.size:
        r_s, Ir, _Imax, _Nmax = el.r_equatorial(0.0, D_OBS, th_o, int(order),
                                                alpha[idx], beta[idx])
        r_s = np.asarray(r_s, dtype=float).ravel()
        Ir = np.asarray(Ir, dtype=float).ravel()
        out = ana.coords_at_tau(0.0, [0.0, D_OBS, th_o, 0.0],
                                [alpha[idx], beta[idx]], Ir, do_phi_and_t=True)
        coords = np.asarray(out[1], dtype=float).reshape(4, -1)
        t_k, r_k, th_k, phi_k = coords
        if not np.nanmax(np.abs(r_k - r_s)) < 1e-6 * max(np.nanmax(np.abs(r_s)), 1.0):
            raise RuntimeError("coords_at_tau radius slot does not match r_equatorial")
        rs[idx], ts[idx], ph[idx] = r_s, t_k, phi_k

        lam, eta = conserved(alpha[idx], beta[idx], th_o)
        kr = np.asarray(el.radial_momentum_sign(0.0, th_o, alpha[idx], beta[idx],
                                                Ir, _Imax)).ravel() \
            if hasattr(el, "radial_momentum_sign") else np.ones(idx.size)
        kth = np.full(idx.size, 1.0 if order % 2 == 0 else -1.0)
        u0, u1, u2, u3 = keplerian_u(r_s)
        g = np.asarray(calc_redshift(0.0, r_s, lam, eta, kr, kth, u0, u1, u2, u3)).ravel()
        gg[idx] = np.nan_to_num(g, nan=0.0)
        sign[idx] = kr
    return dict(alpha=alpha, beta=beta, rs=rs, ts=ts, phi=ph, g=gg, sign=sign,
                mask=mask, dx=dx)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--inclination", type=float, default=20.0)
    ap.add_argument("--profile", default="core", choices=sorted(PROFILES))
    ap.add_argument("--out", type=Path, default=ROOT / "artifacts" / "raymaps")
    args = ap.parse_args()

    t0 = time.time()
    cfg = PROFILES[args.profile]
    raw = {n: build_order(n, cfg[f"dx{n}"], args.inclination, None) for n in (0, 1, 2)}
    finite = np.concatenate([raw[n]["ts"][np.isfinite(raw[n]["ts"])] for n in (0, 1, 2)])
    t_reference = float(np.max(finite))

    gid = f"a000_i{int(round(args.inclination)):03d}"
    written = []
    for n in (0, 1, 2):
        d = raw[n]
        valid = validity(d["rs"], d["phi"], d["ts"], 0.0, d["mask"])
        delay = np.where(valid, t_reference - d["ts"], np.nan)
        weight = np.where(valid, np.power(np.abs(d["g"]), GFACTOR_EXPONENT), 0.0)
        rm = RayMap(
            geometry_id=gid, order=n, spin=0.0, inclination_deg=args.inclination,
            profile=args.profile, alpha=d["alpha"], beta=d["beta"],
            source_r=np.nan_to_num(d["rs"], nan=0.0),
            source_phi=np.mod(np.nan_to_num(d["phi"], nan=0.0), 2 * np.pi),
            winding_phi=np.nan_to_num(d["phi"], nan=0.0),
            delay=np.nan_to_num(delay, nan=0.0),
            coordinate_time=np.nan_to_num(d["ts"], nan=0.0),
            redshift=d["g"], transfer_weight=weight,
            pixel_area=np.full(d["alpha"].size, d["dx"] ** 2),
            radial_sign=d["sign"], valid=valid,
            metadata={"dx": d["dx"], "t_reference": t_reference,
                      "gfactor_exponent": GFACTOR_EXPONENT,
                      "emission_r_outer": EMISSION_R_OUTER,
                      "horizon_radius": horizon_radius(0.0), "d_obs": D_OBS,
                      "band_limit": BAND_LIMITS[n],
                      "backend": "kgeo_geodesics+phrt_schwarzschild_velocity"
                                 "+kgeo_redshift",
                      "backend_reason": "AART CritCurve is singular at a=0; "
                                        "kgeo u_kep returns a non-rotating disk "
                                        "at a=0"},
        )
        target = args.out / f"{gid}_n{n}_{args.profile}.h5"
        if target.exists():
            import h5py

            with h5py.File(target, "r") as fh:
                if abs(float(fh["meta"].attrs["spin"])) > 1e-15:
                    raise SystemExit(
                        f"refusing to overwrite {target.name}: it holds a "
                        f"nonzero spin and this run is Schwarzschild")
        p = write(rm, target)
        s = rm.summary()
        written.append({"path": str(p.relative_to(ROOT)), "sha256": sha256(p), **s})
        print(f"  n={n} {s['n_valid']:>7d}/{s['n_rays']:<8d} valid ({s['valid_fraction']*100:5.2f}%)  "
              f"r [{s['source_r_range'][0]:.3f}, {s['source_r_range'][1]:.3f}]  "
              f"delay [{s['delay_range'][0]:.2f}, {s['delay_range'][1]:.2f}]  "
              f"area {s['total_quadrature_area']:.4g}")

    mp = args.out / f"{gid}_{args.profile}_manifest.json"
    mp.write_text(json.dumps({"geometry_id": gid, "spin": 0.0,
                              "inclination_deg": args.inclination,
                              "profile": args.profile, "t_reference": t_reference,
                              "runtime_seconds": time.time() - t0,
                              "maps": written}, indent=2) + "\n")
    print(f"\nwrote {mp}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
