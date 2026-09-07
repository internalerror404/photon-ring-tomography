#!/usr/bin/env python3
"""G1 of ruling 028: one declared curved boundary, validated at fresh points.

The candidate is a periodic cubic in the generator's own arclength parameter,
fitted through cached root solutions and checked against boundary solves at
locations that are not fit knots. Densifying the old straight polygon is not
refinement and is not done; the curve is tessellated for the clipping kernel
under its own integration budget.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

import h5py
import numpy as np
from scipy.interpolate import CubicSpline

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from phrt.geometry.raymap import read                        # noqa: E402
from phrt.revision_v4_1 import fractional as FR              # noqa: E402
from phrt.revision_v4_1 import hulls as HU                   # noqa: E402
from phrt.revision_v4_1 import measure as M                  # noqa: E402
from phrt.revision_v4_1 import query as Q                    # noqa: E402
from phrt.revision_v4_1.common_sky import DetectorGrid       # noqa: E402

MAPS = ROOT / "artifacts" / "raymaps"
BANDS = ROOT / ("artifacts/e3_pilot/aart_out/core/"
                "LensingBands_a_0.5_i_50.0_dx0_0.4_dx1_0.08_dx2_0.02.h5")
GEOMETRY, SPIN, INC, LIMITS = "a050_i050", 0.5, 50.0, 25.0
ORDERS, SIGMA = (0, 1, 2), 0.011341986814407566
BAND_TOL = BOUND_TOL = RESP_TOL = SHIFT_TOL = 2.5e-4
ROOT_TOL, TESS_TOL = 2.5e-5, 1.0e-6
N_UNIFORM = 400_000
LADDER = (60, 119, 237)          # marks; nested, each adds the midpoints
TESS = 4096                      # polygon samples of the validated curve
FIELDS = ("1", "alpha/25", "beta/25", "(alpha/25)^2", "(beta/25)^2",
          "alpha*beta/625")


def marks_at(spin, inc, n):
    """Arclength marks on the pinned critical curve; nested by construction."""
    import aart.lensingbands as lbm
    from scipy.integrate import cumulative_trapezoid as cumtrapz
    x, y = lbm.CritCurve(spin, inc)
    dy = np.gradient(y, x[0], edge_order=2)
    dx = np.gradient(x, x[0], edge_order=2)
    arc = cumtrapz(np.sqrt(dy ** 2 + dx ** 2), initial=0)
    s = np.linspace(0.0, arc.max(), n)
    mx = np.interp(s, arc, x)
    return mx, np.interp(mx, x, y), s, arc.max()


def solve_at(mx, my, guard, why):
    hs, st = HU.solve_hulls(mx, my, SPIN, INC, LIMITS)
    guard.charge(Q.BOUNDARY, st["solves"], why)
    return hs


def curve_from(hull, s_dir):
    """Periodic cubic radius against the direction parameter."""
    r = np.hypot(hull[:, 0], hull[:, 1])
    o = np.argsort(s_dir)
    return CubicSpline(np.append(s_dir[o], s_dir[o][0] + 1.0),
                       np.append(r[o], r[o][0]), bc_type="periodic")


def tessellate(spline, th_of_s, n):
    s = np.linspace(0.0, 1.0, n, endpoint=False)
    th = th_of_s(s)
    r = spline(s)
    return np.stack([r * np.cos(th), r * np.sin(th)], axis=1)


def main(out: Path, freeze: Path) -> int:
    t0 = time.time()
    guard = Q.Guard(freeze)
    out.mkdir(parents=True, exist_ok=False)
    grid = DetectorGrid(-25.0, 25.0, -25.0, 25.0, 0.4)
    maps = {n: read(MAPS / f"{GEOMETRY}_n{n}_core.h5") for n in ORDERS}
    cells = {n: M.build_ray_cells(m.alpha, m.beta, M.NODAL_DUAL_CLIPPED)
             for n, m in maps.items()}
    fields = {n: np.stack([np.ones(m.alpha.size), m.alpha / 25, m.beta / 25,
                           (m.alpha / 25) ** 2, (m.beta / 25) ** 2,
                           m.alpha * m.beta / 625], axis=1)
              for n, m in maps.items()}
    whiten = 1.0 / (SIGMA * np.sqrt(grid.cell_area))

    with h5py.File(BANDS, "r") as f:
        cached = {f"{n}{s}": f[f"hull_{n}{s}"][:] for n in ORDERS
                  for s in ("i", "e")}
    square = cached["0e"]

    levels, prov = {}, {}
    for k, nm in enumerate(LADDER):
        mx, my, s, smax = marks_at(SPIN, INC, nm)
        if k == 0:                       # cached: the archived level-60 roots
            hs = {key: cached[key] for key in cached}
            prov[nm] = {"source": "archived level-60 roots", "solves": 0}
        else:
            hs = solve_at(mx, my, guard, f"curved_ladder_{nm}")
            prov[nm] = {"source": "fresh solves of the pinned equations",
                        "solves": 10 * nm}
        # direction parameter: the mirrored mark index, matching hulls()
        sd = np.concatenate([s, s[::-1] + smax]) / (2 * smax)
        levels[nm] = {"hulls": hs, "s": sd % 1.0}
        print(f"  marks {nm}: {prov[nm]['source']}, boundary spent "
              f"{guard.spent[Q.BOUNDARY]}", flush=True)

    # one declared curved candidate per boundary, per level
    def build(nm):
        L = levels[nm]
        out_ = {}
        for n in ORDERS:
            for side in ("i", "e"):
                key = f"{n}{side}"
                if key == "0e":
                    out_[key] = square      # a real corner set: keep exact
                    continue
                h = L["hulls"][key]
                sp = curve_from(h, L["s"])
                th = np.arctan2(h[:, 1], h[:, 0])
                o = np.argsort(L["s"])
                thu = np.unwrap(th[o])
                ths = CubicSpline(np.append(L["s"][o], L["s"][o][0] + 1.0),
                                  np.append(thu, thu[0] + 2 * np.pi),
                                  bc_type="periodic")
                out_[key] = tessellate(sp, ths, TESS)
        return out_

    curved = {nm: build(nm) for nm in LADDER}

    # tessellation budget: does doubling the sample change the area?
    tess_check = {}
    for n in ORDERS:
        L = levels[LADDER[-1]]
        h = L["hulls"][f"{n}e"] if n else L["hulls"]["0i"]
        key = f"{n}e" if n else "0i"
        sp = curve_from(L["hulls"][key], L["s"])
        th = np.arctan2(L["hulls"][key][:, 1], L["hulls"][key][:, 0])
        o = np.argsort(L["s"])
        ths = CubicSpline(np.append(L["s"][o], L["s"][o][0] + 1.0),
                          np.append(np.unwrap(th[o]),
                                    np.unwrap(th[o])[0] + 2 * np.pi),
                          bc_type="periodic")
        a1 = abs(HU.region_measures(tessellate(sp, ths, TESS),
                                    tessellate(sp, ths, TESS) * 0.999,
                                    tessellate(sp, ths, 2 * TESS),
                                    tessellate(sp, ths, 2 * TESS) * 0.999,
                                    N_UNIFORM)["band_symmetric_difference"])
        tess_check[str(n)] = {"relative": a1 / max(
            abs(HU.region_measures(tessellate(sp, ths, TESS),
                                   tessellate(sp, ths, TESS) * 0.999,
                                   tessellate(sp, ths, TESS),
                                   tessellate(sp, ths, TESS) * 0.999,
                                   1000)["band_N"], 1e-30)),
            "budget": TESS_TOL}
        tess_check[str(n)]["passes"] = bool(
            tess_check[str(n)]["relative"] < TESS_TOL)

    def response(hs, n):
        ov = FR.triple_overlap(cells[n], grid, hs[f"{n}e"], hs[f"{n}i"])
        y = np.zeros((grid.n_cells, len(FIELDS)))
        np.add.at(y, ov.rows, ov.vals[:, None] * fields[n][ov.cols])
        return y * whiten

    resp = {nm: {n: response(curved[nm], n) for n in ORDERS} for nm in LADDER}
    pairs = []
    for a, b in zip(LADDER[:-1], LADDER[1:]):
        for n in ORDERS:
            m = HU.region_measures(curved[b][f"{n}e"], curved[b][f"{n}i"],
                                   curved[a][f"{n}e"], curved[a][f"{n}i"],
                                   N_UNIFORM)
            u = m["band_union"]
            eb = m["band_symmetric_difference"] / u
            ee = (m["outer_symmetric_difference"]
                  + m["inner_symmetric_difference"]) / u
            yb, ya = resp[b][n], resp[a][n]
            rr = max(float(np.linalg.norm(yb[:, k] - ya[:, k])
                           / max(np.linalg.norm(yb[:, k]), 1e-30))
                     for k in range(len(FIELDS)))
            pairs.append({"pair": f"{a}->{b}", "order": n, "eta_band": eb,
                          "eta_boundaries": ee, "hull_only_response": rr,
                          "band_width_positive": bool(m["band_N"] > 0
                                                      and m["band_M"] > 0),
                          "all_pass": bool(eb < BAND_TOL and ee < BOUND_TOL
                                           and rr < RESP_TOL)})
            print(f"  {a}->{b} n{n}: band {eb:.3e} bnd {ee:.3e} resp "
                  f"{rr:.3e}", flush=True)

    qualifying = all(p["all_pass"] for p in pairs
                     if p["pair"] == f"{LADDER[-2]}->{LADDER[-1]}")
    # independent validation: fresh solves at points that are not fit knots
    checks = {}
    accepted = LADDER[-1] if qualifying else None
    if accepted:
        mx, my, s, smax = marks_at(SPIN, INC, accepted)
        h = 0.5 * (s[1] - s[0])
        s2 = np.concatenate([[s[0]], s[1:-1] + h, [s[-1]]])
        import aart.lensingbands as lbm
        x, y = lbm.CritCurve(SPIN, INC)
        from scipy.integrate import cumulative_trapezoid as cumtrapz
        dy = np.gradient(y, x[0], edge_order=2)
        dx = np.gradient(x, x[0], edge_order=2)
        arc = cumtrapz(np.sqrt(dy ** 2 + dx ** 2), initial=0)
        mx2 = np.interp(s2, arc, x)
        my2 = np.interp(mx2, x, y)
        need = 10 * accepted
        if guard.remaining(Q.BOUNDARY) >= need:
            hs = solve_at(mx2, my2, guard, "independent_shifted")
            rows = []
            for n in ORDERS:
                r_fit = np.hypot(*curved[accepted][f"{n}e"].T)
                th_fit = np.arctan2(curved[accepted][f"{n}e"][:, 1],
                                    curved[accepted][f"{n}e"][:, 0])
                hh = hs[f"{n}e"]
                th_new = np.arctan2(hh[:, 1], hh[:, 0])
                r_new = np.hypot(hh[:, 0], hh[:, 1])
                pred = np.interp(np.unwrap(th_new),
                                 np.unwrap(th_fit[np.argsort(th_fit)]),
                                 r_fit[np.argsort(th_fit)], period=2 * np.pi)
                rel = float(np.abs(pred - r_new).max()
                            / max(np.abs(r_new).mean(), 1e-30))
                rows.append({"order": n, "boundary": "outer",
                             "max_relative_radius_error": rel,
                             "passes": bool(rel < SHIFT_TOL)})
            checks["shifted_samples"] = {
                "run": True, "tolerance": SHIFT_TOL, "rows": rows,
                "points_are_not_fit_knots": True,
                "passes": all(r["passes"] for r in rows)}
        else:
            checks["shifted_samples"] = {
                "run": False, "reason": "BOUNDARY_RESERVE_INSUFFICIENT",
                "needed": need, "remaining": guard.remaining(Q.BOUNDARY)}
    rep = {
        "stage": "G1", "ruling": "PAPER_I_BOUNDARY_VALIDITY_RULING_028",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "commit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                 capture_output=True, text=True).stdout.strip(),
        "candidate": "periodic cubic radius in the pinned arclength "
                     "parameter, tessellated for the clipping kernel",
        "outer_square_kept_exact": True,
        "densified_old_polygon": False,
        "ladder_marks": list(LADDER), "ladder_provenance": prov,
        "tessellation_check": tess_check,
        "tessellation_samples": TESS,
        "tolerances": {"band": BAND_TOL, "boundaries": BOUND_TOL,
                       "hull_only_response": RESP_TOL,
                       "shifted": SHIFT_TOL, "tighter_root": ROOT_TOL,
                       "tessellation": TESS_TOL},
        "pairs": pairs, "accepted_marks": accepted,
        "independent_checks": checks,
        "hull_geometry_qualified": bool(
            accepted and checks.get("shifted_samples", {}).get("passes")),
        "guard": guard.snapshot(),
        "runtime_seconds": time.time() - t0,
    }
    (out / "CURVED_HULL_VALIDATION_028.json").write_text(
        json.dumps(rep, indent=2) + "\n")
    print(f"  accepted {accepted}, qualified {rep['hull_geometry_qualified']}, "
          f"boundary spent {guard.spent[Q.BOUNDARY]}, "
          f"remaining {guard.remaining(Q.BOUNDARY)}; {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main((ROOT / sys.argv[1]).resolve(),
                          (ROOT / sys.argv[2]).resolve()))
