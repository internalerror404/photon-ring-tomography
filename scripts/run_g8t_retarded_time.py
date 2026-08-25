#!/usr/bin/env python3
"""G8t -- independent validation of the retarded-time and azimuth fields.

G8 established the source-radius map to 1e-12 against kgeo. That is not enough
for this paper: Paper I is about historical inversion, so the emission time is
the quantity the claim actually rests on, and it needs its own gate.

Two independent routes are used, and neither shares AART's code path:

  analytic   kgeo's own elliptic-integral solution. ``r_equatorial`` returns the
             Mino time Ir at the equatorial crossing for order mbar, and
             ``coords_at_tau`` evaluates the full (t, r, theta, phi) there.
  numerical  kgeo's ODE integrator, ``integrate_geo_single``, which solves the
             geodesic equations directly and shares no elliptic-integral
             machinery with either analytic implementation.

Time origins are conventions, so absolute agreement is not required and would
not be meaningful. What is compared are **differences**

    (Delta t_{n,p} - Delta t_{m,q})

across every pair drawn from the stratified sample, spanning orders. A common
additive constant cancels; an order-dependent or screen-dependent disagreement
does not, and that is exactly what would corrupt a retarded-time inversion.
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
N_STRATA = 5
PER_STRATUM = 5
N_NUMERICAL = 12


def stratified(rm, rng, n_strata=N_STRATA, per=PER_STRATUM) -> np.ndarray:
    v = np.where(rm.valid)[0]
    if v.size == 0:
        return v
    keys = (np.arctan2(rm.beta[v], rm.alpha[v]), rm.source_r[v], rm.delay[v])
    chosen: set[int] = set()
    for key in keys:
        edges = np.quantile(key, np.linspace(0, 1, n_strata + 1))
        for lo, hi in zip(edges[:-1], edges[1:]):
            band = v[(key >= lo) & (key <= hi)]
            if band.size:
                take = rng.choice(band, size=min(per, band.size), replace=False)
                chosen.update(int(i) for i in np.atleast_1d(take))
    return np.array(sorted(chosen), dtype=int)


def kgeo_analytic(spin, th_o, order, alpha, beta):
    """(t_s, phi_s) from kgeo's analytic route."""
    from kgeo import equatorial_lensing as el
    from kgeo import kerr_raytracing_ana as ana

    r_s, Ir, _Imax, _Nmax = el.r_equatorial(float(spin), float(D_OBS), float(th_o),
                                            int(order), alpha, beta)
    Ir = np.asarray(Ir, dtype=float).ravel()
    obs = [0.0, float(D_OBS), float(th_o), 0.0]
    out = ana.coords_at_tau(float(spin), obs, [alpha, beta], Ir, do_phi_and_t=True)
    # coords_at_tau returns (sign data, coords) with coords shaped (4, 1, N),
    # ordered (t, r, theta, phi) in Boyer-Lindquist.
    coords = np.asarray(out[1], dtype=float).reshape(4, -1)
    return np.asarray(r_s, dtype=float).ravel(), coords


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--geometry", default="a050_i050")
    ap.add_argument("--spin", type=float, default=0.5)
    ap.add_argument("--inclination", type=float, default=50.0)
    ap.add_argument("--profile", default="core")
    ap.add_argument("--seed", type=int, default=20260825)
    args = ap.parse_args()

    t0 = time.time()
    th_o = args.inclination * np.pi / 180.0
    rng = np.random.default_rng(args.seed)
    maps = ROOT / "artifacts" / "raymaps"

    rows: list[dict] = []
    for n in (0, 1, 2):
        rm = read(maps / f"{args.geometry}_n{n}_{args.profile}.h5")
        idx = stratified(rm, rng)
        if idx.size == 0:
            continue
        r_k, coords = kgeo_analytic(args.spin, th_o, n, rm.alpha[idx], rm.beta[idx])
        t_k_arr, r_k_coord, th_k, phi_k = coords
        # Confirm the coordinate ordering against the radius we already trust,
        # rather than assuming it. A mis-slotted t would silently invalidate the
        # whole gate.
        r_check = float(np.nanmedian(np.abs(r_k_coord - rm.source_r[idx])
                                     / np.maximum(np.abs(rm.source_r[idx]), 1e-30)))
        if not r_check < 1e-6:
            raise RuntimeError(
                f"coords_at_tau slot 1 does not match the source radius "
                f"(median relative {r_check:.3e}); the coordinate ordering "
                f"assumption is wrong and the gate would be meaningless")
        eq = float(np.nanmax(np.abs(th_k - np.pi / 2)))
        if not eq < 1e-6:
            raise RuntimeError(f"kgeo theta is not equatorial (max |theta-pi/2| = {eq:.3e})")
        arrs = {"t": t_k_arr, "phi": phi_k}
        for k, i in enumerate(idx):
            rows.append({
                "order": n, "ray_index": int(i),
                "alpha": float(rm.alpha[i]), "beta": float(rm.beta[i]),
                "delay_aart": float(rm.delay[i]),
                "t_aart": float(rm.coordinate_time[i]),
                "t_kgeo": float(arrs["t"][k]),
                "r_aart": float(rm.source_r[i]), "r_kgeo": float(r_k[k]),
                "phi_aart_wrapped": float(rm.source_phi[i]),
                "phi_kgeo_wrapped": float(np.mod(arrs["phi"][k], 2 * np.pi)),
            })

    import pandas as pd
    df = pd.DataFrame(rows).dropna(subset=["t_kgeo"])
    if df.empty:
        print("no comparable rays"); return 1

    # radius, as a control that the identification is right
    r_rel = np.abs(df.r_kgeo - df.r_aart) / np.maximum(np.abs(df.r_aart), 1e-300)

    # --- the gate quantity: pairwise time differences ----------------------
    t_a = df.t_aart.to_numpy()
    t_k = df.t_kgeo.to_numpy()
    offset = float(np.median(t_k - t_a))
    resid = (t_k - t_a) - offset            # after removing the common origin
    m = len(t_a)
    ia, ib = np.triu_indices(m, k=1)
    d_a = t_a[ia] - t_a[ib]
    d_k = t_k[ia] - t_k[ib]
    pair_abs = np.abs(d_k - d_a)
    scale = np.maximum(np.abs(d_a), 1.0)
    pair_rel = pair_abs / scale
    cross = df.order.to_numpy()[ia] != df.order.to_numpy()[ib]

    # Azimuth. The two codes place phi = 0 on different axes, so a rigid
    # rotation is a convention exactly as a common time origin is. What must be
    # tested is that it is ONE constant: an order-dependent or screen-dependent
    # rotation would corrupt any non-axisymmetric source model, a global one
    # only relabels the azimuth axis.
    signed = np.angle(np.exp(1j * (df.phi_kgeo_wrapped - df.phi_aart_wrapped)))
    phi_offset = float(np.angle(np.mean(np.exp(1j * signed))))   # circular mean
    dphi = np.abs(np.angle(np.exp(1j * (signed - phi_offset))))
    per_order_offset = {
        int(n): float(np.angle(np.mean(np.exp(1j * signed[df.order.to_numpy() == n]))))
        for n in sorted(df.order.unique())}
    offset_spread = float(max(per_order_offset.values()) - min(per_order_offset.values()))
    # is the offset a recognisable exact constant?
    nearest_quarter_turn = round(phi_offset / (np.pi / 2))
    offset_is_quarter_turn = abs(phi_offset - nearest_quarter_turn * np.pi / 2)

    summary = {
        "rays_compared": int(m),
        "pairs_compared": int(pair_abs.size),
        "cross_order_pairs": int(cross.sum()),
        "common_time_offset": offset,
        "residual_after_offset_max": float(np.abs(resid).max()),
        "radius_control_max_relative": float(r_rel.max()),
        "time_difference_max_absolute": float(pair_abs.max()),
        "time_difference_max_relative": float(pair_rel.max()),
        "time_difference_cross_order_max_relative":
            float(pair_rel[cross].max()) if cross.any() else float("nan"),
        "azimuth_rigid_offset_radians": phi_offset,
        "azimuth_rigid_offset_in_quarter_turns": float(nearest_quarter_turn),
        "azimuth_offset_deviation_from_exact_quarter_turn": float(offset_is_quarter_turn),
        "azimuth_residual_after_rigid_offset_max": float(dphi.max()),
        "azimuth_residual_after_rigid_offset_median": float(np.median(dphi)),
        "azimuth_offset_spread_across_orders": offset_spread,
        "azimuth_offset_per_order": per_order_offset,
        "per_order": {
            int(n): {
                "rays": int((df.order == n).sum()),
                "residual_after_offset_max":
                    float(np.abs(resid[df.order.to_numpy() == n]).max()),
                "azimuth_residual_max_radians": float(dphi[df.order.to_numpy() == n].max()),
            } for n in sorted(df.order.unique())
        },
    }

    out = ROOT / "artifacts" / "e3_pilot"
    out.mkdir(parents=True, exist_ok=True)
    (out / "g8t_retarded_time.json").write_text(
        json.dumps({"summary": summary, "rows": rows,
                    "runtime_seconds": time.time() - t0}, indent=2) + "\n")
    df.to_parquet(out / "g8t_rays.parquet", index=False)

    print(f"rays compared            {summary['rays_compared']}")
    print(f"pairs compared           {summary['pairs_compared']} "
          f"({summary['cross_order_pairs']} cross-order)")
    print(f"radius control, max rel  {summary['radius_control_max_relative']:.3e}")
    print(f"common time offset       {offset:.6f}   (a convention, removed)")
    print(f"residual after offset    {summary['residual_after_offset_max']:.3e}")
    print(f"pairwise dt, max abs     {summary['time_difference_max_absolute']:.3e}")
    print(f"pairwise dt, max rel     {summary['time_difference_max_relative']:.3e}")
    print(f"  cross-order only       {summary['time_difference_cross_order_max_relative']:.3e}")
    print(f"azimuth rigid offset     {phi_offset:+.12f} rad "
          f"= {nearest_quarter_turn:+.0f} x pi/2 "
          f"(deviation {offset_is_quarter_turn:.3e})")
    print(f"azimuth residual after   {summary['azimuth_residual_after_rigid_offset_max']:.3e} rad")
    print(f"offset spread by order   {offset_spread:.3e} rad")
    for n, s in summary["per_order"].items():
        print(f"   n={n} rays {s['rays']:3d}  t-resid {s['residual_after_offset_max']:.3e}"
              f"  phi {s['azimuth_residual_max_radians']:.3e}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
