#!/usr/bin/env python3
"""V2 of ruling 028: partial-response diagnostics on the qualified geometry.

The hull is the curved candidate G1 accepted, regenerated from the pinned
equations at the same marks -- which also reproduces its geometry
independently. Responses are computed only where transfer data exists and are
labelled partial, because that is what they are. Certified non-emitting area
is physics and is never counted as missing.
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
from phrt.revision_v4_1 import domain as D                   # noqa: E402
from phrt.revision_v4_1 import fractional as FR              # noqa: E402
from phrt.revision_v4_1 import hulls as HU                   # noqa: E402
from phrt.revision_v4_1 import measure as M                  # noqa: E402
from phrt.revision_v4_1 import polyclip as PC                # noqa: E402
from phrt.revision_v4_1 import query as Q                    # noqa: E402
from phrt.revision_v4_1.common_sky import DetectorGrid       # noqa: E402

sys.path.insert(0, str(ROOT / "scripts" / "revision_v4_1"))
from g1_curved_hull import fit_closed_curve, marks_at, tessellate  # noqa: E402

MAPS = ROOT / "artifacts" / "raymaps"
AART = ROOT / "artifacts" / "e3_pilot" / "aart_out"
BANDS = {"coarse": AART / "coarse/LensingBands_a_0.5_i_50.0_dx0_0.8_dx1_0.16_dx2_0.04.h5",
         "core": AART / "core/LensingBands_a_0.5_i_50.0_dx0_0.4_dx1_0.08_dx2_0.02.h5",
         "fine": AART / "fine/LensingBands_a_0.5_i_50.0_dx0_0.2_dx1_0.04_dx2_0.01.h5"}
GEOMETRY, SPIN, INC, LIMITS = "a050_i050", 0.5, 50.0, 25.0
ORDERS, PROFILES = (0, 1, 2), ("coarse", "core", "fine")
PAIRS = (("coarse", "core"), ("core", "fine"))
SIGMA, T_REF, R_OUTER = 0.011341986814407566, -978.6055123201214, 50.0
T_OBS = [0.0, 2.857142857142857, 5.714285714285714, 8.571428571428571,
         11.428571428571429, 14.285714285714286, 17.142857142857142, 20.0]
SCREEN = ("1", "alpha/25", "beta/25", "(alpha/25)^2", "(beta/25)^2",
          "alpha*beta/625")
TRANSFER = ("g^3", "g^3*cos20", "g^3*sin20", "g^3*cos40", "g^3*sin40")
COMPONENT_TOL, TOTAL_TOL, AREA_TOL = 5.0e-4, 1.0e-3, 1.0e-3
TESS = 4096


def main(out: Path, freeze: Path, g1_dir: Path) -> int:
    t0 = time.time()
    guard = Q.Guard(freeze)
    g1 = json.loads((g1_dir / "CURVED_HULL_VALIDATION_028.json").read_text())
    marks = g1["accepted_marks"]
    if marks is None or not g1["hull_geometry_qualified"]:
        raise SystemExit("G1 did not qualify a curved hull")
    out.mkdir(parents=True, exist_ok=False)
    rh = horizon_radius(SPIN)
    grid = DetectorGrid(-25.0, 25.0, -25.0, 25.0, 0.4)

    mx, my, _, _ = marks_at(SPIN, INC, marks)
    hs, st = HU.solve_hulls(mx, my, SPIN, INC, LIMITS)
    guard.charge(Q.BOUNDARY, st["solves"], "v2_regenerate_accepted_hull")
    square = hs["0e"]
    curved = {k: (square if k == "0e" else tessellate(fit_closed_curve(v),
                                                      TESS))
              for k, v in hs.items()}
    repro = {}
    for n in ORDERS:
        a = abs(PC.signed_area(curved[f"{n}e"])) - abs(
            PC.signed_area(curved[f"{n}i"]))
        want = [p for p in g1["pairs"] if p["order"] == n][-1]["eta_band"]
        repro[str(n)] = {"band_area": a, "g1_last_pair_eta_band": want}

    rows, built = [], {}
    for prof in PROFILES:
        with h5py.File(BANDS[prof], "r") as f:
            band = {n: f[f"mask{n}"][:] for n in ORDERS}
        for n in ORDERS:
            rm = read(MAPS / f"{GEOMETRY}_n{n}_{prof}.h5")
            cells = M.build_ray_cells(rm.alpha, rm.beta, M.NODAL_DUAL_CLIPPED)
            ov = FR.triple_overlap(cells, grid, curved[f"{n}e"],
                                   curved[f"{n}i"])
            state, prim = D.classify_points(band[n], rm.source_r,
                                            rm.source_phi,
                                            rm.coordinate_time, rm.redshift,
                                            rh, R_OUTER)
            tal = D.tally(state, prim, ov.active_area)
            emit = state == D.CERTIFIED_EMITTING
            a, b = rm.alpha, rm.beta
            delay = T_REF - rm.coordinate_time
            g3 = np.where(emit, np.abs(rm.redshift) ** 3, 0.0)
            cols, labels = [], []
            for nm, v in zip(SCREEN, (np.ones(a.size), a / 25, b / 25,
                                      (a / 25) ** 2, (b / 25) ** 2,
                                      a * b / 625)):
                cols.append(v)
                labels.append(f"screen:{nm}")
            for it, t in enumerate(T_OBS):
                ph = np.where(emit, t - delay, 0.0)
                for nm, v in zip(TRANSFER, (g3,
                                            g3 * np.cos(2 * np.pi * ph / 20),
                                            g3 * np.sin(2 * np.pi * ph / 20),
                                            g3 * np.cos(2 * np.pi * ph / 40),
                                            g3 * np.sin(2 * np.pi * ph / 40))):
                    cols.append(np.nan_to_num(v, nan=0.0))
                    labels.append(f"transferred:{nm}")
            F = np.stack(cols, axis=1)
            keep = np.ones(ov.cols.size, bool)
            keep_t = emit[ov.cols]
            y = np.zeros((grid.n_cells, F.shape[1]))
            np.add.at(y, ov.rows[keep],
                      ov.vals[keep, None] * F[ov.cols[keep], :len(SCREEN)]
                      @ np.eye(len(SCREEN), F.shape[1]))
            yt = np.zeros((grid.n_cells, F.shape[1] - len(SCREEN)))
            np.add.at(yt, ov.rows[keep_t],
                      ov.vals[keep_t, None] * F[ov.cols[keep_t], len(SCREEN):])
            y = np.hstack([y[:, :len(SCREEN)], yt]) / (
                SIGMA * np.sqrt(grid.cell_area))
            built[(prof, n)] = {
                "y": y, "labels": labels, "tally": tal,
                "geometric_band_area": float(ov.active_area.sum()),
                "certified_emitting_area":
                    tal["by_state"][D.CERTIFIED_EMITTING]["area"],
                "certified_non_emitting_area":
                    tal["by_state"][D.CERTIFIED_NON_EMITTING]["area"],
                "unresolved_area": tal["by_state"][D.UNRESOLVED]["area"]}

    for c, f in PAIRS:
        for n in ORDERS:
            A, B = built[(c, n)], built[(f, n)]
            per = {}
            for j, nm in enumerate(B["labels"]):
                per.setdefault(nm, []).append(j)
            floor = 1e-12 * float(np.linalg.norm(B["y"][:, 0]))
            res = {}
            for nm, js in per.items():
                vf = np.concatenate([B["y"][:, j] for j in js])
                vc = np.concatenate([A["y"][:, j] for j in js])
                nf = float(np.linalg.norm(vf))
                e = float(np.linalg.norm(vf - vc))
                res[nm] = {"relative": e / max(nf, floor),
                           "zero_response": bool(nf <= floor)}
            worst = max(res, key=lambda k: res[k]["relative"])
            def rel(k):
                x, y_ = A[k], B[k]
                return abs(y_ - x) / max(x, y_, 1e-30)
            rows.append({
                "pair": f"{c}->{f}", "order": n, "worst_field": worst,
                "worst_relative": res[worst]["relative"],
                "per_field": res,
                "geometric_band_area_relative": rel("geometric_band_area"),
                "certified_emitting_area_relative":
                    rel("certified_emitting_area"),
                "unresolved_area_relative": rel("unresolved_area"),
                "component_passes": bool(res[worst]["relative"]
                                         < COMPONENT_TOL),
                "emitting_area_passes":
                    bool(rel("certified_emitting_area") < AREA_TOL)})
            print(f"  {c}->{f} n{n}: worst {res[worst]['relative']:.3e} "
                  f"({worst})  band area {rel('geometric_band_area'):.2e}  "
                  f"emitting area {rel('certified_emitting_area'):.3e}",
                  flush=True)

    rep = {
        "stage": "V2", "ruling": "PAPER_I_BOUNDARY_VALIDITY_RULING_028",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "commit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                 capture_output=True, text=True).stdout.strip(),
        "hull": {"accepted_marks": marks, "regenerated_from_pinned_equations":
                 True, "reproduction": repro},
        "responses_are": "PARTIAL, on the support that has transfer data. "
                         "They are not full physical response errors, and the "
                         "missing contributions were not computed",
        "certified_non_emitting_counted_as_missing": False,
        "domain_states": {f"{p}_n{n}": {
            "geometric_band_area": built[(p, n)]["geometric_band_area"],
            "certified_emitting": built[(p, n)]["certified_emitting_area"],
            "certified_non_emitting": built[(p, n)]["certified_non_emitting_area"],
            "unresolved": built[(p, n)]["unresolved_area"]}
            for p in PROFILES for n in ORDERS},
        "tolerances": {"component": COMPONENT_TOL, "total": TOTAL_TOL,
                       "area": AREA_TOL},
        "comparisons": [{k: v for k, v in r.items() if k != "per_field"}
                        for r in rows],
        "per_field": {f"{r['pair']}_n{r['order']}": r["per_field"]
                      for r in rows},
        "transferred_field_accuracy_qualified":
            bool(all(r["component_passes"] and r["emitting_area_passes"]
                     for r in rows)),
        "guard": guard.snapshot(),
        "runtime_seconds": time.time() - t0,
    }
    (out / "FULL_DOMAIN_PARTIAL_RESPONSE_028.json").write_text(
        json.dumps(rep, indent=2) + "\n")
    print(f"  qualified {rep['transferred_field_accuracy_qualified']}; "
          f"boundary spent {guard.spent[Q.BOUNDARY]}, remaining "
          f"{guard.remaining(Q.BOUNDARY)}; {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    a = [(ROOT / x).resolve() for x in sys.argv[1:4]]
    raise SystemExit(main(*a))
