#!/usr/bin/env python3
"""G1 closeout for ruling 029: the checks the qualification flag was missing.

Same candidate, same 237 marks, same periodic cubic in chord length. No new
ladder and no new fit family. What is added is the four things the previous
flag did not actually test: the tighter-root comparison, the shifted check in
band and response metrics rather than radius, band-normalised tessellation
error, and local nesting instead of a positive total area -- with a final
boolean that is the conjunction of all of them.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts" / "revision_v4_1"))

from g1_curved_hull import fit_closed_curve, marks_at, tessellate  # noqa: E402
from phrt.geometry.raymap import read                        # noqa: E402
from phrt.revision_v4_1 import fractional as FR              # noqa: E402
from phrt.revision_v4_1 import hulls as HU                   # noqa: E402
from phrt.revision_v4_1 import measure as M                  # noqa: E402
from phrt.revision_v4_1 import polyclip as PC                # noqa: E402
from phrt.revision_v4_1 import query as Q                    # noqa: E402
from phrt.revision_v4_1.common_sky import DetectorGrid       # noqa: E402

MAPS = ROOT / "artifacts" / "raymaps"
GEOMETRY, SPIN, INC, LIMITS = "a050_i050", 0.5, 50.0, 25.0
ORDERS, MARKS, SIGMA = (0, 1, 2), 237, 0.011341986814407566
SHIFT_TOL, ROOT_TOL, TESS_TOL, BAND_TOL = 2.5e-4, 2.5e-5, 1.0e-6, 2.5e-4
N_UNIFORM, TESS_LADDER = 400_000, (4096, 16384, 65536, 262144)
FIELDS = ("1", "alpha/25", "beta/25", "(alpha/25)^2", "(beta/25)^2",
          "alpha*beta/625")


def build(hs, tess):
    return {k: (v if k == "0e" else tessellate(fit_closed_curve(v), tess))
            for k, v in hs.items()}


def responses(curved, cells, fields, grid, whiten):
    out = {}
    for n in ORDERS:
        ov = FR.triple_overlap(cells[n], grid, curved[f"{n}e"],
                               curved[f"{n}i"])
        y = np.zeros((grid.n_cells, len(FIELDS)))
        np.add.at(y, ov.rows, ov.vals[:, None] * fields[n][ov.cols])
        out[n] = y * whiten
    return out


def resp_err(a, b):
    return max(float(np.linalg.norm(b[:, k] - a[:, k])
                     / max(np.linalg.norm(b[:, k]), 1e-30))
               for k in range(len(FIELDS)))


def geom_err(A, B, n):
    m = HU.region_measures(B[f"{n}e"], B[f"{n}i"], A[f"{n}e"], A[f"{n}i"],
                           N_UNIFORM)
    u = m["band_union"]
    return {"eta_band": m["band_symmetric_difference"] / u,
            "eta_boundaries": (m["outer_symmetric_difference"]
                               + m["inner_symmetric_difference"]) / u,
            "band_N": m["band_N"], "band_M": m["band_M"]}


def local_nesting(curved, n, n_ang=200_000):
    """Positive width at every angle, not merely a positive total area."""
    th = np.linspace(0.0, 2 * np.pi, n_ang, endpoint=False)
    ro = HU.star_radius(curved[f"{n}e"], th)
    ri = HU.star_radius(curved[f"{n}i"], th)
    w = ro - ri
    return {"min_local_width_M": float(np.nanmin(w)),
            "positive_everywhere": bool(np.all(w > 0)),
            "angles_tested": int(n_ang),
            "total_area_positive": bool(
                abs(PC.signed_area(curved[f"{n}e"]))
                > abs(PC.signed_area(curved[f"{n}i"])))}


def main(out: Path, freeze: Path, g1: Path) -> int:
    t0 = time.time()
    out.mkdir(parents=True, exist_ok=False)
    guard = Q.Guard(freeze, ledger_path=out / "ATTEMPT_LEDGER_029.json")
    prev = json.loads((g1 / "CURVED_HULL_VALIDATION_028.json").read_text())
    grid = DetectorGrid(-25.0, 25.0, -25.0, 25.0, 0.4)
    maps = {n: read(MAPS / f"{GEOMETRY}_n{n}_core.h5") for n in ORDERS}
    cells = {n: M.build_ray_cells(m.alpha, m.beta, M.NODAL_DUAL_CLIPPED)
             for n, m in maps.items()}
    fields = {n: np.stack([np.ones(m.alpha.size), m.alpha / 25, m.beta / 25,
                           (m.alpha / 25) ** 2, (m.beta / 25) ** 2,
                           m.alpha * m.beta / 625], axis=1)
              for n, m in maps.items()}
    whiten = 1.0 / (SIGMA * np.sqrt(grid.cell_area))

    mx, my, s, smax = marks_at(SPIN, INC, MARKS)
    base_h, _ = Q.solve_boundary(mx, my, 5, guard, "closeout_base_237",
                                 spin=SPIN, inc_deg=INC, limits=LIMITS)

    # ---- band-normalised tessellation, refined until it meets its budget --
    tess_rows, chosen = [], None
    for t in TESS_LADDER:
        c1, c2 = build(base_h, t), build(base_h, 2 * t)
        row = {"samples": t}
        worst = 0.0
        for n in ORDERS:
            band = abs(PC.signed_area(c2[f"{n}e"])) - abs(
                PC.signed_area(c2[f"{n}i"]))
            d = sum(abs(abs(PC.signed_area(c2[k])) - abs(PC.signed_area(c1[k])))
                    for k in (f"{n}e", f"{n}i") if k != "0e")
            row[f"n{n}_band_normalised"] = d / band
            worst = max(worst, d / band)
        row["worst"] = worst
        row["passes"] = bool(worst < TESS_TOL)
        # the detector response must also stop moving
        r1, r2 = (responses(c1, cells, fields, grid, whiten),
                  responses(c2, cells, fields, grid, whiten))
        row["worst_response"] = max(resp_err(r1[n], r2[n]) for n in ORDERS)
        row["response_passes"] = bool(row["worst_response"] < TESS_TOL)
        tess_rows.append(row)
        print(f"  tess {t}: band-normalised {worst:.3e}, response "
              f"{row['worst_response']:.3e}", flush=True)
        if row["passes"] and row["response_passes"]:
            chosen = t
            break
    tess = chosen or TESS_LADDER[-1]
    curved = build(base_h, tess)
    base_resp = responses(curved, cells, fields, grid, whiten)

    # ---- shifted samples, in band and response metrics ------------------
    h = 0.5 * (s[1] - s[0])
    import aart.lensingbands as lbm
    from scipy.integrate import cumulative_trapezoid as cumtrapz
    x, y = lbm.CritCurve(SPIN, INC)
    dy = np.gradient(y, x[0], edge_order=2)
    dx = np.gradient(x, x[0], edge_order=2)
    arc = cumtrapz(np.sqrt(dy ** 2 + dx ** 2), initial=0)
    s2 = np.concatenate([[s[0]], s[1:-1] + h, [s[-1]]])
    mx2 = np.interp(s2, arc, x)
    sh_h, _ = Q.solve_boundary(mx2, np.interp(mx2, x, y), 5, guard,
                               "closeout_shifted_237", spin=SPIN, inc_deg=INC,
                               limits=LIMITS)
    sh = build(sh_h, tess)
    sh_resp = responses(sh, cells, fields, grid, whiten)
    shifted = [{"order": n, **geom_err(curved, sh, n),
                "response": resp_err(base_resp[n], sh_resp[n]),
                "tolerance": SHIFT_TOL} for n in ORDERS]
    for r in shifted:
        r["passes"] = bool(r["eta_band"] < SHIFT_TOL
                           and r["eta_boundaries"] < SHIFT_TOL
                           and r["response"] < SHIFT_TOL)
        print(f"  shifted n{r['order']}: band {r['eta_band']:.3e} bnd "
              f"{r['eta_boundaries']:.3e} resp {r['response']:.3e}", flush=True)

    # ---- tighter root tolerance, geometry and response -------------------
    tr_h, _ = Q.solve_boundary(mx, my, 5, guard, "closeout_tighter_root_237",
                               spin=SPIN, inc_deg=INC, limits=LIMITS,
                               xtol=1.49012e-9)
    tr = build(tr_h, tess)
    tr_resp = responses(tr, cells, fields, grid, whiten)
    tighter = [{"order": n, **geom_err(curved, tr, n),
                "response": resp_err(base_resp[n], tr_resp[n]),
                "tolerance": ROOT_TOL} for n in ORDERS]
    for r in tighter:
        r["passes"] = bool(r["eta_band"] < ROOT_TOL
                           and r["eta_boundaries"] < ROOT_TOL
                           and r["response"] < ROOT_TOL)
        print(f"  tighter n{r['order']}: band {r['eta_band']:.3e} bnd "
              f"{r['eta_boundaries']:.3e} resp {r['response']:.3e}", flush=True)

    topo = {}
    for n in ORDERS:
        topo[str(n)] = {**local_nesting(curved, n),
                        "outer_simple": PC.is_simple(curved[f"{n}e"][::32]),
                        "inner_simple": PC.is_simple(curved[f"{n}i"][::32]),
                        "simple_tested_on_subsample": True}
        print(f"  topology n{n}: min local width "
              f"{topo[str(n)]['min_local_width_M']:.4e}, positive everywhere "
              f"{topo[str(n)]['positive_everywhere']}", flush=True)

    npz = out / "CLOSEOUT_ARRAYS_029.npz"
    np.savez_compressed(npz, **{f"base_{k}": v for k, v in base_h.items()},
                        **{f"shifted_{k}": v for k, v in sh_h.items()},
                        **{f"tighter_{k}": v for k, v in tr_h.items()},
                        **{f"tess_{k}": v for k, v in curved.items()},
                        marks=mx, marks_beta=my, marks_shifted=mx2,
                        arclength=s)
    late = [p for p in prev["pairs"] if p["pair"] == "119->237"]
    prior = [p for p in prev["pairs"] if p["pair"] == "60->119"]
    ok = {
        "two_late_pairs_all_metrics": bool(
            all(p["all_pass"] for p in late + prior)),
        "shifted_band_and_response": all(r["passes"] for r in shifted),
        "tighter_root_executed": True,
        "tighter_root_passes": all(r["passes"] for r in tighter),
        "tessellation_band_normalised": bool(tess_rows[-1]["passes"]),
        "tessellation_response": bool(tess_rows[-1]["response_passes"]),
        "local_nesting_positive_width": all(
            v["positive_everywhere"] for v in topo.values()),
        "topology_simple": all(v["outer_simple"] and v["inner_simple"]
                               for v in topo.values()),
        "arrays_exported": npz.exists(),
    }
    rep = {
        "stage": "G1_CLOSEOUT", "ruling": "PAPER_I_TRANSFER_AUDIT_RULING_029",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "commit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                 capture_output=True, text=True).stdout.strip(),
        "candidate": "unchanged: 237 marks, periodic cubic in chord length, "
                     "outer square exact",
        "new_ladder_or_fit_family": False,
        "tessellation_ladder": tess_rows, "tessellation_chosen": tess,
        "tessellation_previously_reported_wrongly":
            "the 028 check normalised each shape's area change by that "
            "shape's own area. Band-normalised, order 2 was 2.46e-5 against "
            "a 1e-6 budget, so the reported pass was wrong",
        "two_late_pairs_from_028": late + prior,
        "shifted": shifted, "tighter_root": tighter, "topology": topo,
        "checks": ok,
        "hull_geometry_qualified": bool(all(ok.values())),
        "final_boolean_is_the_conjunction_of_every_requirement": True,
        "arrays": {"file": npz.name,
                   "sha256": hashlib.sha256(npz.read_bytes()).hexdigest()},
        "guard": guard.snapshot(),
        "runtime_seconds": time.time() - t0,
    }
    (out / "GEOMETRY_CLOSEOUT_029.json").write_text(
        json.dumps(rep, indent=2) + "\n")
    (out / "GEOMETRY_PAYLOAD_MANIFEST_029.json").write_text(json.dumps({
        "stage": "G1_CLOSEOUT", "file": npz.name,
        "sha256": rep["arrays"]["sha256"],
        "contents": ["fit roots at 237 marks", "shifted roots",
                     "tighter-root roots", "tessellated curves",
                     "mark parameters and arclength"],
        "reusable_without_new_physical_solves": True}, indent=2) + "\n")
    print(f"  qualified {rep['hull_geometry_qualified']}: "
          + ", ".join(f"{k}={v}" for k, v in ok.items()))
    print(f"  boundary spent {guard.spent[Q.BOUNDARY]}, remaining "
          f"{guard.remaining(Q.BOUNDARY)}; {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    a = [(ROOT / x).resolve() for x in sys.argv[1:4]]
    raise SystemExit(main(*a))
