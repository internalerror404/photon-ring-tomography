#!/usr/bin/env python3
"""Weighted retarded-delay quantiles, replacing the retired sampled maximum.

The sampled maximum ray delay is an extreme-value statistic: it is set by
whichever single ray happens to sit closest to the band edge, so it does not
converge under refinement and must not be used as a recoverable depth. These
quantiles are integrals over the band and do converge.

Three weightings, because they answer different questions:

  solid angle       where the band's *area* sits in retarded time;
  throughput        where its *flux* sits, dOmega * g^3;
  Fisher            where its *sensitivity to a localized source amplitude*
                    sits -- the only one of the three that bears on what can
                    actually be recovered.
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from phrt.config import load_registry
from phrt.geometry.raymap import read
from phrt.io.manifests import Gate, RunManifest, make_run_id, merge_gate_file
from phrt.io.tables import write_table

QUANTILES = (0.50, 0.90, 0.99, 0.999)
PROFILES = ("coarse", "core", "fine")


def weighted_quantile(x: np.ndarray, w: np.ndarray, q: float) -> float:
    o = np.argsort(x)
    x, w = x[o], w[o]
    c = np.cumsum(w)
    if c[-1] <= 0:
        return float("nan")
    return float(np.interp(q * c[-1], c, x))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--geometry", default="a098_i075")
    args = ap.parse_args()

    t0 = time.time()
    reg = load_registry()
    rows = []
    for prof in PROFILES:
        for n in (0, 1, 2):
            p = ROOT / "artifacts" / "raymaps" / f"{args.geometry}_n{n}_{prof}.h5"
            if not p.exists():
                continue
            rm = read(p)
            v = rm.valid
            d = rm.delay[v]
            area = rm.pixel_area[v]
            g3 = np.power(np.abs(rm.redshift[v]), 3.0)
            weights = {
                "solid_angle": area,
                "throughput": area * g3,
                # Fisher weight for a localized amplitude: the squared forward
                # coefficient carried by the row, integrated with its quadrature.
                "fisher": area * g3 ** 2,
            }
            for wname, w in weights.items():
                row = {"geometry": args.geometry, "profile": prof, "order": n,
                       "weighting": wname, "n_valid": int(v.sum()),
                       "sampled_max_RETIRED": float(d.max()),
                       "total_weight": float(w.sum())}
                for q in QUANTILES:
                    row[f"q{q:g}"] = weighted_quantile(d, w, q)
                rows.append(row)

    import pandas as pd
    df = pd.DataFrame(rows)

    run_id = make_run_id("DQ", reg.sha256)
    man = RunManifest(run_id=run_id, experiment_id="DELAY_QUANTILES",
                      extra={"geometry": args.geometry})
    man.add_input(reg.path)

    # convergence of each quantile, core -> fine
    worst = {}
    for wname in ("solid_angle", "throughput", "fisher"):
        w_worst = 0.0
        for n in (0, 1, 2):
            c = df[(df.weighting == wname) & (df.order == n) & (df.profile == "core")]
            f = df[(df.weighting == wname) & (df.order == n) & (df.profile == "fine")]
            if c.empty or f.empty:
                continue
            for q in QUANTILES:
                a, b = float(c[f"q{q:g}"].iloc[0]), float(f[f"q{q:g}"].iloc[0])
                w_worst = max(w_worst, abs(a - b) / max(abs(b), 1e-300))
        worst[wname] = w_worst
        man.add_gate(Gate(f"DQ_{wname}_quantile_convergence", "PASS" if w_worst <= 2e-2 else "FAIL",
                          measured=w_worst, threshold=2e-2,
                          note=f"worst core-to-fine relative change across "
                               f"q = {QUANTILES}, all three orders, "
                               f"{wname}-weighted"))

    # the retired statistic, kept as a resolution-tagged diagnostic
    mx = df[df.weighting == "solid_angle"].pivot_table(
        index="order", columns="profile", values="sampled_max_RETIRED")
    mx_worst = float((mx["fine"] - mx["core"]).abs().div(mx["fine"].abs()).max())
    man.add_gate(Gate(
        "G7_grid_convergence_raw_max", "FAIL",
        disposition="RETIRED_NONCONVERGENT_EXTREME_STATISTIC",
        measured=mx_worst, threshold=2e-2,
        note=f"the sampled maximum ray delay, retained as a resolution-tagged "
             f"diagnostic only. It is no longer a convergence gate and must not "
             f"be used as a recoverable depth. Core-to-fine change {mx_worst:.3e} "
             f"against the weighted quantiles' "
             f"{max(worst.values()):.3e}."))

    tbl = write_table(rows, f"delay_quantiles_{args.geometry}")
    man.add_output(tbl)
    mp = man.write(reg.path, reg.sha256, runtime_seconds=time.time() - t0)
    merge_gate_file(man.gates, run_id)

    print(f"=== {args.geometry}: weighted delay quantiles (M), core profile ===")
    core = df[df.profile == "core"]
    print(f"{'order':>5} {'weighting':>12} " + " ".join(f"{'q'+format(q,'g'):>9}" for q in QUANTILES)
          + f" {'max (retired)':>14}")
    for _, r in core.iterrows():
        print(f"{int(r.order):>5} {r.weighting:>12} "
              + " ".join(f"{r['q'+format(q,'g')]:>9.2f}" for q in QUANTILES)
              + f" {r.sampled_max_RETIRED:>14.2f}")
    print("\ncore -> fine convergence")
    for k, v in worst.items():
        print(f"  {k:>12}-weighted quantiles  {v:.3e}")
    print(f"  {'sampled max':>12} (retired)         {mx_worst:.3e}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
