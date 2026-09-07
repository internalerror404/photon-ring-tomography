#!/usr/bin/env python3
"""I2 of ruling 031: integrate the emitting domain, don't relabel rays.

The declared representation is the implicit one: the validity indicator is
evaluated inside adaptive cut cells and the unresolved boundary area is
carried as an explicit budget. This is not a claim to have reconstructed the
contour. A sample's absence is never taken to mean its cell is empty, and a
missing node or a failed quadrature is never taken as zero.
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
sys.path.insert(0, str(ROOT / "scripts" / "revision_v4_1"))
from phrt.geometry.raymap import read, horizon_radius        # noqa: E402
from phrt.revision_v4_1 import domain as D                   # noqa: E402
from phrt.revision_v4_1 import fractional as FR              # noqa: E402
from phrt.revision_v4_1 import measure as M                  # noqa: E402
from phrt.revision_v4_1 import pathdomain as PD              # noqa: E402
from phrt.revision_v4_1 import pathdomain2 as P2             # noqa: E402
from phrt.revision_v4_1 import query as Q                    # noqa: E402
from phrt.revision_v4_1.common_sky import DetectorGrid       # noqa: E402
from t1_first_invalid_primitive import instrument            # noqa: E402

MAPS = ROOT / "artifacts" / "raymaps"
AART = ROOT / "artifacts/e3_pilot/aart_out"
BANDS = {"core": AART / "core/LensingBands_a_0.5_i_50.0_dx0_0.4_dx1_0.08_dx2_0.02.h5",
         "fine": AART / "fine/LensingBands_a_0.5_i_50.0_dx0_0.2_dx1_0.04_dx2_0.01.h5"}
GEOMETRY, SPIN, D_OBS, R_OUTER = "a050_i050", 0.5, 1000.0, 50.0
ORDERS, SIGMA, T_REF = (0, 1, 2), 0.011341986814407566, -978.6055123201214
T_OBS = [0.0, 2.857142857142857, 5.714285714285714, 8.571428571428571,
         11.428571428571429, 14.285714285714286, 17.142857142857142, 20.0]
SUB = 2                     # 2x2 sub-cells inside each transition cell
COMPONENT_TOL, TOTAL_TOL = 5.0e-4, 1.0e-3


def transition_cells(state, alpha, beta):
    """Cells whose emitting status differs from a neighbour on the grid."""
    ua = np.unique(alpha)
    n = ua.size
    E = (state == D.CERTIFIED_EMITTING).reshape(n, n)
    m = np.zeros_like(E)
    m[:-1, :] |= E[:-1, :] != E[1:, :]
    m[1:, :] |= E[:-1, :] != E[1:, :]
    m[:, :-1] |= E[:, :-1] != E[:, 1:]
    m[:, 1:] |= E[:, :-1] != E[:, 1:]
    return np.flatnonzero(m.reshape(-1))


def main(out: Path, freeze: Path, hull_npz: Path) -> int:
    t0 = time.time()
    out.mkdir(parents=True, exist_ok=False)
    guard = Q.Guard(freeze, ledger_path=out / "ATTEMPT_LEDGER_031.json")
    fz = json.loads(freeze.read_text())
    cap = int(fz["ledger"]["integration_pilot_max"])
    rh = horizon_radius(SPIN)
    grid = DetectorGrid(-25.0, 25.0, -25.0, 25.0, 0.4)
    hz = np.load(hull_npz)
    hulls = {k[5:]: hz[k] for k in hz.files if k.startswith("tess_")}
    whiten = 1.0 / (SIGMA * np.sqrt(grid.cell_area))
    spent_here = 0
    rows, per_order = [], {}

    for prof in ("core", "fine"):
        with h5py.File(BANDS[prof], "r") as h:
            band = {n: h[f"mask{n}"][:] for n in ORDERS}
        for n in ORDERS:
            rm = read(MAPS / f"{GEOMETRY}_n{n}_{prof}.h5")
            cells = M.build_ray_cells(rm.alpha, rm.beta, M.NODAL_DUAL_CLIPPED)
            ov = FR.triple_overlap(cells, grid, hulls[f"{n}e"],
                                   hulls[f"{n}i"])
            st, _ = D.classify_points(band[n], rm.source_r, rm.source_phi,
                                      rm.coordinate_time, rm.redshift, rh,
                                      R_OUTER)
            emit = st == D.CERTIFIED_EMITTING
            chi = emit.astype(float)          # the baseline: centre indicator
            tc = transition_cells(st, rm.alpha, rm.beta)
            tc = tc[ov.active_area[tc] > 0]
            need = tc.size * SUB * SUB
            budget = min(cap - spent_here, guard.remaining(Q.TRANSFER) - 4000)
            if need > budget:
                keep = max(0, budget // (SUB * SUB))
                tc = tc[np.argsort(-ov.active_area[tc])[:keep]]
                need = tc.size * SUB * SUB
            unres_area = 0.0
            if tc.size:
                wa = (cells.alpha_hi - cells.alpha_lo)[tc]
                wb = (cells.beta_hi - cells.beta_lo)[tc]
                off = (np.arange(SUB) + 0.5) / SUB - 0.5
                aa = (cells.alpha_lo[tc] + 0.5 * wa)[:, None, None] \
                    + (wa[:, None, None] * off[None, :, None])
                bb = (cells.beta_lo[tc] + 0.5 * wb)[:, None, None] \
                    + (wb[:, None, None] * off[None, None, :])
                aa, bb = aa.reshape(-1), np.broadcast_to(
                    bb, aa.shape[:1] + (1,)).reshape(-1) if False else \
                    np.repeat(bb.reshape(tc.size, -1), 1, 0).reshape(-1)
                aa = np.repeat(cells.alpha_lo[tc] + 0.5 * wa, SUB * SUB) \
                    + np.tile(np.repeat(off, SUB), tc.size) \
                    * np.repeat(wa, SUB * SUB)
                bb = np.repeat(cells.beta_lo[tc] + 0.5 * wb, SUB * SUB) \
                    + np.tile(np.tile(off, SUB), tc.size) \
                    * np.repeat(wb, SUB * SUB)
                tok = guard.reserve(Q.TRANSFER, aa.size,
                                    f"I2_cut_cells_{prof}_n{n}")
                try:
                    rec = instrument(aa, bb, n)
                except BaseException as exc:
                    guard.abort(tok, f"{type(exc).__name__}: {exc}")
                    raise
                nf = int(rec["output_is_nan"].sum())
                guard.complete(tok, aa.size - nf, nf)
                spent_here += aa.size
                sub = np.zeros(aa.size)
                unres = np.zeros(aa.size, bool)
                for j in range(aa.size):
                    d = P2.adjudicate(rec["roots"][:, j],
                                      float(rec["G_theta"][j]), rh, D_OBS,
                                      R_OUTER)
                    if d["code"] == PD.VALID:
                        sub[j] = 1.0
                    elif d["code"] == PD.UNRESOLVED:
                        unres[j] = True
                s = sub.reshape(tc.size, SUB * SUB)
                u = unres.reshape(tc.size, SUB * SUB)
                chi[tc] = s.mean(1)
                # unresolved sub-cells are neither one nor zero: they are the
                # budget, and they are never rounded to empty
                unres_area = float(np.sum(u.mean(1) * cells.area[tc]))
            y = np.zeros((grid.n_cells, 1))
            np.add.at(y, ov.rows, (ov.vals * chi[ov.cols])[:, None])
            y0 = np.zeros((grid.n_cells, 1))
            np.add.at(y0, ov.rows, (ov.vals * emit[ov.cols])[:, None])
            per_order[f"{prof}_n{n}"] = {
                "transition_cells_found": int(tc.size),
                "sub_cells_evaluated": int(need),
                "emitting_area_centre_indicator":
                    float((ov.vals * emit[ov.cols]).sum()),
                "emitting_area_cut_cell":
                    float((ov.vals * chi[ov.cols]).sum()),
                "unresolved_boundary_area": unres_area,
                "domain_change_relative": float(
                    abs((ov.vals * chi[ov.cols]).sum()
                        - (ov.vals * emit[ov.cols]).sum())
                    / max((ov.vals * emit[ov.cols]).sum(), 1e-30)),
                "unresolved_area_fraction": float(
                    unres_area / max((ov.vals * chi[ov.cols]).sum(), 1e-30)),
                "response_whitened_norm": float(np.linalg.norm(y * whiten)),
                "response_change_vs_centre_indicator": float(
                    np.linalg.norm((y - y0) * whiten)
                    / max(np.linalg.norm(y0 * whiten), 1e-30)),
            }
            print(f"  {prof} n{n}: {tc.size} transition cells, {need} sub "
                  f"evaluations, domain change "
                  f"{per_order[f'{prof}_n{n}']['domain_change_relative']:.3e}, "
                  f"unresolved area fraction "
                  f"{per_order[f'{prof}_n{n}']['unresolved_area_fraction']:.2e}",
                  flush=True)

    for n in ORDERS:
        a, b = per_order.get(f"core_n{n}"), per_order.get(f"fine_n{n}")
        if not (a and b):
            continue
        rows.append({
            "order": n, "pair": "core->fine",
            "emitting_area_relative": abs(
                b["emitting_area_cut_cell"] - a["emitting_area_cut_cell"])
            / max(b["emitting_area_cut_cell"], 1e-30),
            "response_relative": abs(
                b["response_whitened_norm"] - a["response_whitened_norm"])
            / max(b["response_whitened_norm"], 1e-30),
            "domain_change_error_core": a["domain_change_relative"],
            "domain_change_error_fine": b["domain_change_relative"],
            "unresolved_budget_core": a["unresolved_area_fraction"],
            "unresolved_budget_fine": b["unresolved_area_fraction"]})

    rep = {
        "stage": "I2", "ruling": "PAPER_I_DOMAIN_INTEGRATION_RULING_031",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "commit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                 capture_output=True, text=True).stdout.strip(),
        "representation": "IMPLICIT_DOMAIN_INDICATOR_CUT_CELL_QUADRATURE",
        "claim_to_have_reconstructed_the_contour": False,
        "sample_absence_implies_cell_absence": False,
        "unresolved_treated_as_zero": False,
        "sub_cells_per_transition_cell": SUB * SUB,
        "per_order": per_order, "profile_pairs": rows,
        "tolerances": {"component": COMPONENT_TOL, "total": TOTAL_TOL},
        "qualified": bool(rows and all(
            r["emitting_area_relative"] < TOTAL_TOL
            and r["response_relative"] < COMPONENT_TOL for r in rows)),
        "guard": guard.snapshot(), "runtime_seconds": time.time() - t0,
    }
    (out / "EMISSION_DOMAIN_INTEGRATION_031.json").write_text(
        json.dumps(rep, indent=2) + "\n")
    for r in rows:
        print(f"  n{r['order']}: emitting area {r['emitting_area_relative']:.3e}"
              f", response {r['response_relative']:.3e}")
    print(f"  qualified {rep['qualified']}; charged {guard.spent[Q.TRANSFER]}, "
          f"remaining {guard.remaining(Q.TRANSFER)}; {time.time()-t0:.0f}s")
    return 0


if __name__ == "__main__":
    a = [(ROOT / x).resolve() for x in sys.argv[1:4]]
    raise SystemExit(main(*a))
