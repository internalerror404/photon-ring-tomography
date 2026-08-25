#!/usr/bin/env python3
"""G10q -- continuum noise/quadrature invariance of the physical operator.

Adaptive ray counts differ by orders of magnitude between lensing bands and
between geometries. If the information matrix depends on how finely the screen
happens to be pixelated, then every cross-order and cross-geometry comparison
is measuring grid density.

The test: split each selected pixel into k equal-area children carrying the
same local transfer value, and merge compatible children back into their
parent. Both must leave

    G = A^T C^-1 A

unchanged to 1e-10 relative. Under the declared model, where the datum is
pixel-integrated with Var = sigma_Omega^2 dOmega, the whitened row is
sqrt(dOmega) g^3 B / sigma_Omega and the invariance is exact.

The convention this replaces -- c = g^3 with a flat per-row sigma -- fails the
same test by a factor of k, which is recorded here rather than deleted.
"""
from __future__ import annotations

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
from phrt.operators.physical import OrderRays, PhysicalOperator
from phrt.sources.physical_basis import PhysicalBasis

GEOMETRY = "a050_i050"
SPLITS = (2, 3, 4, 8)
TOLERANCE = 1e-10
SEED = 20260825


def load_orders(n_rays: int = 400) -> list[OrderRays]:
    rng = np.random.default_rng(SEED)
    out = []
    for n in (0, 1, 2):
        m = read(ROOT / "artifacts" / "raymaps" / f"{GEOMETRY}_n{n}_core.h5")
        v = np.where(m.valid)[0]
        i = rng.choice(v, size=min(n_rays, v.size), replace=False)
        tot = float(m.pixel_area[v].sum())
        w = m.pixel_area[i] * (tot / float(m.pixel_area[i].sum()))
        out.append(OrderRays(n, m.source_r[i], m.source_phi[i], m.delay[i],
                             m.redshift[i], w))
    return out


def split_orders(orders, k: int) -> list[OrderRays]:
    """Each pixel becomes k children of area dOmega/k with identical transfer."""
    out = []
    for o in orders:
        rep = lambda a: np.repeat(a, k)          # noqa: E731
        out.append(OrderRays(o.order, rep(o.source_r), rep(o.source_phi),
                             rep(o.delay), rep(o.redshift),
                             np.repeat(o.quadrature / k, k), o.amplitude))
    return out


def merge_orders(orders, k: int) -> list[OrderRays]:
    """Merge k identical children back into one parent of the summed area."""
    out = []
    for o in orders:
        take = slice(None, None, k)
        area = o.quadrature.reshape(-1, k).sum(axis=1)
        out.append(OrderRays(o.order, o.source_r[take], o.source_phi[take],
                             o.delay[take], o.redshift[take], area, o.amplitude))
    return out


def flat_sigma_gram(orders, basis, t_obs) -> np.ndarray:
    """The retired convention: c = g^3 with a flat per-row sigma."""
    G = np.zeros((basis.dimension, basis.dimension))
    for o in orders:
        c = np.power(np.abs(o.redshift), 3.0)
        for t in t_obs:
            D = basis.design(o.source_r, o.source_phi, float(t) - o.delay) * c[:, None]
            G += D.T @ D
    return G


def main() -> int:
    t0 = time.time()
    reg = load_registry()
    orders = load_orders()
    t_obs = np.linspace(0.0, 20.0, 6)
    r_in = min(float(o.source_r.min()) for o in orders)
    r_out = max(float(o.source_r.max()) for o in orders)
    basis = PhysicalBasis(r_in, r_out,
                          float(t_obs.min() - max(o.delay.max() for o in orders)) - 9.0,
                          float(t_obs.max()) + 9.0)
    kw = dict(observer_times=t_obs, design=basis.design, dimension=basis.dimension)

    arms = {"RESOLVED": {}, "UNRESOLVED_IMAGE": {"mixer": np.ones((1, 3))},
            "TOTAL_FLUX": {"collapse": "total_flux"}}
    rows, worst = [], 0.0
    for arm, cfg in arms.items():
        base = PhysicalOperator(orders=orders, **kw, **cfg).gram()
        scale = max(1.0, float(np.linalg.norm(base, 2)))
        for k in SPLITS:
            sp = PhysicalOperator(orders=split_orders(orders, k), **kw, **cfg).gram()
            rel_s = float(np.linalg.norm(sp - base, 2)) / scale
            mg = PhysicalOperator(orders=merge_orders(split_orders(orders, k), k),
                                  **kw, **cfg).gram()
            rel_m = float(np.linalg.norm(mg - base, 2)) / scale
            worst = max(worst, rel_s, rel_m)
            rows.append({"arm": arm, "k": k, "operation": "split",
                         "relative_gram_change": rel_s, "convention": "sqrt_domega"})
            rows.append({"arm": arm, "k": k, "operation": "merge",
                         "relative_gram_change": rel_m, "convention": "sqrt_domega"})

    # the retired convention, measured on the same data
    fb = flat_sigma_gram(orders, basis, t_obs)
    fscale = max(1.0, float(np.linalg.norm(fb, 2)))
    retired_worst = 0.0
    for k in SPLITS:
        fs = flat_sigma_gram(split_orders(orders, k), basis, t_obs)
        rel = float(np.linalg.norm(fs - fb, 2)) / fscale
        retired_worst = max(retired_worst, rel)
        rows.append({"arm": "RESOLVED", "k": k, "operation": "split",
                     "relative_gram_change": rel, "convention": "retired_flat_sigma"})

    run_id = make_run_id("G10Q", reg.sha256)
    man = RunManifest(run_id=run_id, experiment_id="G10Q", seeds={"seed": SEED})
    man.add_input(reg.path)
    man.add_gate(gate_from_tolerance(
        "G10q_continuum_noise_quadrature_invariance", worst, TOLERANCE,
        note=f"worst relative change in G under pixel split and merge at "
             f"k = {SPLITS}, across the resolved, unresolved-image and "
             f"total-flux arms. Whitened row is sqrt(dOmega) g^3 B / sigma_Omega."))
    man.add_gate(Gate(
        "G10q_retired_flat_sigma_convention", "FAIL",
        disposition="RETIRED_PIXELIZATION_DEPENDENT",
        measured=retired_worst, threshold=TOLERANCE,
        note=f"the superseded convention (c = g^3, flat per-row sigma) measured "
             f"on the same rays: worst {retired_worst:.3e}, growing as k - 1. It "
             f"manufactures Fisher information out of pixel count, and since "
             f"ray counts differ by orders of magnitude between lensing bands it "
             f"silently reweighted the bands against each other. Preserved as "
             f"the reason the convention changed, not as a live failure."))

    tbl = write_table(rows, "e3b_quadrature_invariance")
    man.add_output(tbl)
    mp = man.write(reg.path, reg.sha256, runtime_seconds=time.time() - t0)
    merge_gate_file(man.gates, run_id)

    print(f"{'arm':>18} {'k':>3} {'split':>12} {'merge':>12}")
    for arm in arms:
        for k in SPLITS:
            s = next(r for r in rows if r["arm"] == arm and r["k"] == k
                     and r["operation"] == "split" and r["convention"] == "sqrt_domega")
            m = next(r for r in rows if r["arm"] == arm and r["k"] == k
                     and r["operation"] == "merge" and r["convention"] == "sqrt_domega")
            print(f"{arm:>18} {k:>3} {s['relative_gram_change']:>12.3e} "
                  f"{m['relative_gram_change']:>12.3e}")
    print(f"\nworst (sqrt-dOmega)      {worst:.3e}   tolerance {TOLERANCE:.0e}")
    print(f"worst (retired flat sigma) {retired_worst:.3e}   grows as k - 1")
    for g in man.gates:
        print(f"  {g.name:44s} {g.status}")
    return 1 if man.failed_gates else 0


if __name__ == "__main__":
    raise SystemExit(main())
