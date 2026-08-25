#!/usr/bin/env python3
"""P1-E3 -- ray-map convergence (G7) and independent cross-tracer (G8).

Runs in the pinned physics environment, because kgeo and AART live there.

G7, grid convergence
    Different resolutions produce different screen grids, so there is no
    ray-to-ray correspondence between them. What the forward operator actually
    consumes is band-integrated: the quadrature area of each band, the
    weighted area that sets the per-order amplitude, and the endpoints of the
    retarded-time window that decide which epochs the band can see. Those are
    compared across coarse, core and fine.

G8, independent cross-check
    kgeo (achael/kgeo, pinned commit in artifacts/provenance/kgeo_commit.txt)
    solves the same Kerr null geodesics by an independent analytic route.
    Rays are stratified before sampling -- by screen azimuth, by source radius,
    and by delay quantile -- so the check cannot be passed by sampling only the
    easy interior of a band. Nothing is dropped for disagreeing: the validity
    rule is fixed in phrt.geometry.raymap and refers only to finiteness and the
    declared emission annulus.
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

from phrt.geometry.raymap import read

D_OBS = 1000.0
N_STRATA = 6
PER_STRATUM = 8


def band_summary(rm) -> dict:
    v = rm.valid
    return {
        "n_valid": int(v.sum()),
        "area": float(np.sum(rm.pixel_area[v])),
        "weighted_area": float(np.sum(rm.pixel_area[v] * rm.transfer_weight[v])),
        "delay_min": float(rm.delay[v].min()),
        "delay_max": float(rm.delay[v].max()),
        "mean_redshift": float(rm.redshift[v].mean()),
        "r_min": float(rm.source_r[v].min()),
        "r_max": float(rm.source_r[v].max()),
    }


def convergence(gid: str, maps_dir: Path) -> tuple[list[dict], float]:
    profiles = ["coarse", "core", "fine"]
    rows, worst = [], 0.0
    METRICS = ("area", "weighted_area", "delay_min", "delay_max", "mean_redshift")
    for n in (0, 1, 2):
        s = {p: band_summary(read(maps_dir / f"{gid}_n{n}_{p}.h5")) for p in profiles}
        for m in METRICS:
            a, b, c = s["coarse"][m], s["core"][m], s["fine"][m]
            rel_cf = abs(b - c) / max(abs(c), 1e-300)
            rel_kc = abs(a - b) / max(abs(b), 1e-300)
            worst = max(worst, rel_cf)
            rows.append({"order": n, "metric": m, "coarse": a, "core": b, "fine": c,
                         "rel_change_coarse_to_core": rel_kc,
                         "rel_change_core_to_fine": rel_cf})
    return rows, worst


def stratified_indices(rm, rng: np.random.Generator) -> np.ndarray:
    """Sample across screen azimuth, source radius and delay, not the first K rows."""
    v = np.where(rm.valid)[0]
    if v.size == 0:
        return v
    keys = {
        "screen_azimuth": np.arctan2(rm.beta[v], rm.alpha[v]),
        "source_radius": rm.source_r[v],
        "delay": rm.delay[v],
    }
    chosen: set[int] = set()
    for key in keys.values():
        edges = np.quantile(key, np.linspace(0, 1, N_STRATA + 1))
        for lo, hi in zip(edges[:-1], edges[1:]):
            band = v[(key >= lo) & (key <= hi)]
            if band.size:
                take = rng.choice(band, size=min(PER_STRATUM, band.size), replace=False)
                chosen.update(int(i) for i in np.atleast_1d(take))
    return np.array(sorted(chosen), dtype=int)


def cross_check(gid: str, maps_dir: Path, profile: str, spin: float,
                inc: float, seed: int = 20260825) -> tuple[list[dict], float, int]:
    from kgeo import equatorial_lensing as el

    rng = np.random.default_rng(seed)
    th_o = inc * np.pi / 180.0
    rows, worst, total = [], 0.0, 0
    for n in (0, 1, 2):
        rm = read(maps_dir / f"{gid}_n{n}_{profile}.h5")
        idx = stratified_indices(rm, rng)
        if idx.size == 0:
            continue
        r_kgeo, _Ir, _Imax, nmax = el.r_equatorial(
            float(spin), float(D_OBS), float(th_o), int(n),
            rm.alpha[idx], rm.beta[idx])
        r_kgeo = np.asarray(r_kgeo, dtype=float).ravel()
        r_aart = rm.source_r[idx]
        denom = np.maximum(np.abs(r_aart), 1e-300)
        rel = np.abs(r_kgeo - r_aart) / denom
        finite = np.isfinite(rel)
        total += int(finite.sum())
        if finite.any():
            worst = max(worst, float(rel[finite].max()))
        for j, i in enumerate(idx):
            rows.append({
                "order": n, "ray_index": int(i),
                "alpha": float(rm.alpha[i]), "beta": float(rm.beta[i]),
                "source_r_aart": float(r_aart[j]),
                "source_r_kgeo": float(r_kgeo[j]),
                "relative_difference": float(rel[j]),
                "delay": float(rm.delay[i]),
                "screen_azimuth": float(np.arctan2(rm.beta[i], rm.alpha[i])),
                "kgeo_nmax_crossings": float(np.asarray(nmax).ravel()[j]),
            })
    return rows, worst, total


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--geometry", default="a050_i050")
    ap.add_argument("--spin", type=float, default=0.5)
    ap.add_argument("--inclination", type=float, default=50.0)
    ap.add_argument("--profile", default="core")
    ap.add_argument("--out", type=Path, default=ROOT / "artifacts" / "e3_pilot")
    args = ap.parse_args()

    t0 = time.time()
    maps = ROOT / "artifacts" / "raymaps"
    conv_rows, worst_conv = convergence(args.geometry, maps)
    cross_rows, worst_cross, n_checked = cross_check(
        args.geometry, maps, args.profile, args.spin, args.inclination)

    args.out.mkdir(parents=True, exist_ok=True)
    doc = {
        "geometry": args.geometry, "spin": args.spin,
        "inclination_deg": args.inclination, "profile": args.profile,
        "kgeo_commit": (ROOT / "artifacts" / "provenance" / "kgeo_commit.txt"
                        ).read_text().strip(),
        "convergence": {"worst_relative_change_core_to_fine": worst_conv,
                        "rows": conv_rows},
        "cross_tracer": {"rays_checked": n_checked,
                         "worst_relative_difference": worst_cross,
                         "rows": cross_rows},
        "runtime_seconds": time.time() - t0,
    }
    p = args.out / "e3_validation.json"
    p.write_text(json.dumps(doc, indent=2) + "\n")

    print(f"G7 convergence, worst relative change core -> fine : {worst_conv:.3e}")
    print("   per-order, per-metric core -> fine:")
    for r in conv_rows:
        print(f"     n={r['order']} {r['metric']:>14s}  core {r['core']:>12.6g}"
              f"  fine {r['fine']:>12.6g}  rel {r['rel_change_core_to_fine']:.3e}")
    print(f"\nG8 cross-tracer, {n_checked} stratified rays, "
          f"worst relative difference in source radius : {worst_cross:.3e}")
    for n in (0, 1, 2):
        sub = [r["relative_difference"] for r in cross_rows if r["order"] == n]
        if sub:
            print(f"     n={n}  {len(sub):3d} rays  max {max(sub):.3e}  "
                  f"median {np.median(sub):.3e}")
    print(f"\nwrote {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
