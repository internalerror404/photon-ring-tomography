#!/usr/bin/env python3
"""H2 of ruling 027: transfer and emission-boundary accuracy at a fixed hull.

The hull is held fixed at the level H1 accepted, so anything that moves here
is the ray sampling and the emission-validity boundary, not the geometry. The
detector, the eight observer times, sigma and the common absolute clock are
the ones already pinned in the Q2 freeze.

Zero transfer-ray calls: the three existing profiles are compared as they
stand. Targeted queries were not needed to reach the finding and none were
made.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

import h5py
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from phrt.geometry.raymap import read, horizon_radius        # noqa: E402
from phrt.revision_v4_1 import fractional as FR              # noqa: E402
from phrt.revision_v4_1 import hulls as HU                   # noqa: E402
from phrt.revision_v4_1 import measure as M                  # noqa: E402
from phrt.revision_v4_1.common_sky import DetectorGrid       # noqa: E402

MAPS = ROOT / "artifacts" / "raymaps"
AART = ROOT / "artifacts" / "e3_pilot" / "aart_out"
BANDS = {"coarse": AART / "coarse" / "LensingBands_a_0.5_i_50.0_dx0_0.8_dx1_0.16_dx2_0.04.h5",
         "core": AART / "core" / "LensingBands_a_0.5_i_50.0_dx0_0.4_dx1_0.08_dx2_0.02.h5",
         "fine": AART / "fine" / "LensingBands_a_0.5_i_50.0_dx0_0.2_dx1_0.04_dx2_0.01.h5"}
GEOMETRY, SPIN, INC, LIMITS = "a050_i050", 0.5, 50.0, 25.0
ORDERS, PROFILES = (0, 1, 2), ("coarse", "core", "fine")
PAIRS = (("coarse", "core"), ("core", "fine"))
SIGMA = 0.011341986814407566
T_REF = -978.6055123201214
R_OUTER = 50.0
T_OBS = [0.0, 2.857142857142857, 5.714285714285714, 8.571428571428571,
         11.428571428571429, 14.285714285714286, 17.142857142857142, 20.0]
SCREEN = ("1", "alpha/25", "beta/25", "(alpha/25)^2", "(beta/25)^2",
          "alpha*beta/625")
TRANSFER = ("g^3", "g^3*cos20", "g^3*sin20", "g^3*cos40", "g^3*sin40")
COMPONENT_TOL = 5.0e-4      # field quadrature + emission boundary component
TOTAL_TOL = 1.0e-3          # end-to-end response
MASK_TOL = 1.0e-3
AREA_TOL = 1.0e-3


def build(prof, order, hulls, grid):
    rm = read(MAPS / f"{GEOMETRY}_n{order}_{prof}.h5")
    cells = M.build_ray_cells(rm.alpha, rm.beta, M.NODAL_DUAL_CLIPPED)
    ov = FR.triple_overlap(cells, grid, hulls[f"{order}e"],
                           hulls[f"{order}i"])
    with h5py.File(BANDS[prof], "r") as f:
        band = f[f"mask{order}"][:]
    fin = (np.isfinite(rm.source_r) & np.isfinite(rm.source_phi)
           & np.isfinite(rm.coordinate_time))
    lab, tally = FR.classify_support(ov.active_area, band, rm.valid,
                                     rm.source_r, fin, horizon_radius(SPIN),
                                     R_OUTER)
    a, b = rm.alpha, rm.beta
    delay = T_REF - rm.coordinate_time
    g3 = np.abs(rm.redshift) ** 3
    cols, labels = [], []
    for nm, v in zip(SCREEN, (np.ones(a.size), a / 25, b / 25, (a / 25) ** 2,
                              (b / 25) ** 2, a * b / 625)):
        cols.append(v)
        labels.append(("screen", nm, None))
    sup = lab == FR.SUPPORTED
    for it, t in enumerate(T_OBS):
        ph = np.where(sup, t - delay, 0.0)
        gg = np.where(sup, g3, 0.0)
        for nm, v in zip(TRANSFER, (gg, gg * np.cos(2 * np.pi * ph / 20),
                                    gg * np.sin(2 * np.pi * ph / 20),
                                    gg * np.cos(2 * np.pi * ph / 40),
                                    gg * np.sin(2 * np.pi * ph / 40))):
            cols.append(np.nan_to_num(v, nan=0.0))
            labels.append(("transferred", nm, it))
    F = np.stack(cols, axis=1)
    # a transferred field is carried only by fragments that have data; the
    # rest is not zero emission, it is unmeasured, and it is reported as such
    w = ov.vals.copy()
    y_screen = np.zeros((grid.n_cells, len(SCREEN)))
    np.add.at(y_screen, ov.rows, w[:, None] * F[ov.cols, :len(SCREEN)])
    keep = sup[ov.cols]
    y_tr = np.zeros((grid.n_cells, F.shape[1] - len(SCREEN)))
    np.add.at(y_tr, ov.rows[keep],
              w[keep, None] * F[ov.cols[keep], len(SCREEN):])
    wh = 1.0 / (SIGMA * np.sqrt(grid.cell_area))
    return {"profile": prof, "order": order,
            "y": np.hstack([y_screen, y_tr]) * wh, "labels": labels,
            "cells": cells, "active": ov.active_area,
            "active_area_total": float(ov.active_area.sum()),
            "supported_area": tally["by_category"][FR.SUPPORTED]["area"],
            "support": tally, "accounting": ov.accounting,
            "valid_matrix": M.valid_matrix(a, b, cells, rm.valid)}


def main(out_dir: Path, h1_dir: Path) -> int:
    t0 = time.time()
    h1 = json.loads((h1_dir / "HULL_CONVERGENCE_027.json").read_text())
    level = h1["accepted_level"]
    diagnostic = level is None
    if diagnostic:
        # The ruling's own H2 launch clause permits an explicitly separated
        # diagnostic when H1 has not qualified. The finest level H1 actually
        # measured is used, and the result is labelled accordingly: it says
        # what the transfer sampling does at a hull of known, stated accuracy,
        # not that the geometry is qualified.
        level = max(h1["levels"])
    out_dir.mkdir(parents=True, exist_ok=False)
    grid = DetectorGrid(-25.0, 25.0, -25.0, 25.0, 0.4)
    cache = ROOT / "artifacts/revisions/mahakal_v4_1/_hull_cache" / \
        f"L{level}_s0_xNone.npz"
    if cache.exists():
        d = np.load(cache, allow_pickle=True)
        hulls = {k: d[k] for k in d.files if k != "prov"}
        st = {"solves": 0, "from_cache": True, "cache": cache.name}
    else:
        ma, mb, _ = HU.critical_marks(SPIN, INC, level)
        hulls, st = HU.solve_hulls(ma, mb, SPIN, INC, LIMITS)
        st["from_cache"] = False

    built = {(p, n): build(p, n, hulls, grid) for p in PROFILES
             for n in ORDERS}
    rows = []
    for c, f in PAIRS:
        for n in ORDERS:
            A, B = built[(c, n)], built[(f, n)]
            per = {}
            for j, (kind, nm, it) in enumerate(B["labels"]):
                key = f"{kind}:{nm}"
                per.setdefault(key, []).append(j)
            floor = 1e-12 * float(np.linalg.norm(B["y"][:, 0]))
            res = {}
            for key, js in per.items():
                vf = np.concatenate([B["y"][:, j] for j in js])
                vc = np.concatenate([A["y"][:, j] for j in js])
                nf = float(np.linalg.norm(vf))
                e = float(np.linalg.norm(vf - vc))
                res[key] = {"fine_norm": nf, "absolute": e,
                            "relative": e / max(nf, floor),
                            "zero_response": bool(nf <= floor)}
            worst = max(res, key=lambda k: res[k]["relative"])
            aA, aB = A["active_area_total"], B["active_area_total"]
            sA, sB = A["supported_area"], B["supported_area"]
            # the legacy binary masks, for cross-reference against Q2's
            # mask metric; the fractional comparison is the active area above
            inter = M.region_intersection_area(B["cells"], B["valid_matrix"],
                                               A["cells"], A["valid_matrix"])
            rows.append({
                "pair": f"{c}->{f}", "order": n,
                "worst_field": worst,
                "worst_relative": res[worst]["relative"],
                "per_field": res,
                "component_budget": COMPONENT_TOL,
                "total_budget": TOTAL_TOL,
                "component_passes": bool(res[worst]["relative"]
                                         < COMPONENT_TOL),
                "total_passes": bool(res[worst]["relative"] < TOTAL_TOL),
                "active_area": {"coarser": aA, "finer": aB,
                                "relative": abs(aB - aA) / max(aA, aB),
                                "passes": bool(abs(aB - aA) / max(aA, aB)
                                               < AREA_TOL)},
                "supported_area": {"coarser": sA, "finer": sB,
                                   "relative": abs(sB - sA) / max(sA, sB),
                                   "passes": bool(abs(sB - sA) / max(sA, sB)
                                                  < AREA_TOL)},
                "legacy_binary_mask_intersection_for_reference": inter,
            })
            print(f"  {c}->{f} n{n}: worst {res[worst]['relative']:.3e} "
                  f"({worst})  active {rows[-1]['active_area']['relative']:.3e}"
                  f"  supported {rows[-1]['supported_area']['relative']:.3e}",
                  flush=True)

    unsupported = {f"{p}_n{n}": 1.0 - built[(p, n)]["support"]["by_category"]
                   [FR.SUPPORTED]["area_fraction"]
                   for p in PROFILES for n in ORDERS}
    qualified = all(r["component_passes"] and r["active_area"]["passes"]
                    and r["supported_area"]["passes"] for r in rows) \
        and max(unsupported.values()) < COMPONENT_TOL
    rep = {
        "stage": "H2", "ruling": "PAPER_I_FRACTIONAL_COVERAGE_RULING_027",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "commit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                 capture_output=True, text=True).stdout.strip(),
        "transfer_ray_calls": 0,
        "boundary_point_solves_this_stage": st["solves"],
        "hull_provenance": st,
        "hull_held_fixed_at_level": level,
        "explicitly_separated_diagnostic": diagnostic,
        "hull_accuracy_at_this_level": (
            "H1 did not qualify this level; the band symmetric difference "
            "against the next coarser level is 3.0e-7, 7.6e-5 and 1.9e-3 for "
            "orders 0, 1 and 2, so the geometry carried into this stage is "
            "accurate to those figures and no better"
            if diagnostic else "qualified by H1"),
        "hull_source": ("the finest level H1 measured" if diagnostic
                        else "H1 accepted level")
                       + ", reused from the H1 solve cache",
        "detector": grid.to_dict(), "sigma": SIGMA,
        "observer_times_M": T_OBS,
        "absolute_clock_reference": T_REF,
        "fields": {"screen": list(SCREEN), "transferred": list(TRANSFER),
                   "transferred_support": "carried only by fragments with "
                                          "valid transfer data; the rest is "
                                          "unmeasured, not zero emission"},
        "tolerances": {"component": COMPONENT_TOL, "total": TOTAL_TOL,
                       "mask": MASK_TOL, "area": AREA_TOL},
        "comparisons": rows,
        "unsupported_area_fraction": unsupported,
        "worst_unsupported_area_fraction": max(unsupported.values()),
        "transferred_field_accuracy_qualified": bool(qualified),
        "runtime_seconds": time.time() - t0,
    }
    (out_dir / "FRACTIONAL_FIXED_DETECTOR_VALIDATION_027.json").write_text(
        json.dumps(rep, indent=2) + "\n")
    print(f"hull fixed at {level}; qualified {qualified}; worst unsupported "
          f"{rep['worst_unsupported_area_fraction']:.4f}; "
          f"{rep['runtime_seconds']:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main((ROOT / sys.argv[1]).resolve(),
                          (ROOT / sys.argv[2]).resolve()))
