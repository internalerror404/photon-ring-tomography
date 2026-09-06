#!/usr/bin/env python3
"""H1 of ruling 027: qualify the hull hierarchy. Zero transfer rays.

Boundary solves only. Each level re-runs AART's own root equations at more
arclength marks on the critical curve, so a finer polygon is a finer boundary
and not a denser file.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

import h5py
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from phrt.geometry.raymap import read                        # noqa: E402
from phrt.revision_v4_1 import fractional as FR              # noqa: E402
from phrt.revision_v4_1 import hulls as HU                   # noqa: E402
from phrt.revision_v4_1 import measure as M                  # noqa: E402
from phrt.revision_v4_1.common_sky import DetectorGrid       # noqa: E402

MAPS = ROOT / "artifacts" / "raymaps"
ARCHIVE = (ROOT / "artifacts/e3_pilot/aart_out/core/"
           "LensingBands_a_0.5_i_50.0_dx0_0.4_dx1_0.08_dx2_0.02.h5")
GEOMETRY, SPIN, INC, LIMITS = "a050_i050", 0.5, 50.0, 25.0
ORDERS = (0, 1, 2)
SIGMA = 0.011341986814407566
LEVELS = (60, 120, 240, 480)
N_UNIFORM = 400_000
BAND_TOL = 2.5e-4          # band-relative symmetric difference
BOUND_TOL = 2.5e-4         # inner + outer, normalised by band union
RESP_TOL = 2.5e-4          # hull-only whitened response change
ROOT_TOL = 2.5e-5          # tighter-root and shifted-sample discrepancy
QUAD_TOL = 1.0e-6          # aggregate numerical integration
SOLVE_CAP = 30_000
# A first execution generated every level and then aborted in the angular
# lookup before any comparison. Those solves were really performed, so they
# are carried into the budget rather than forgotten, and hulls are cached
# from here on so no level is ever solved twice again.
PRIOR_SOLVES_SPENT = 9000
CACHE = ROOT / "artifacts" / "revisions" / "mahakal_v4_1" / "_hull_cache"
PROFILE = "core"
FIELDS = ("1", "alpha/25", "beta/25", "(alpha/25)^2", "(beta/25)^2",
          "alpha*beta/625")


def screen_fields(a, b):
    return np.stack([np.ones(a.size), a / 25.0, b / 25.0, (a / 25.0) ** 2,
                     (b / 25.0) ** 2, a * b / 625.0], axis=1)


def main(out_dir: Path) -> int:
    t0 = time.time()
    out_dir.mkdir(parents=True, exist_ok=False)
    grid = DetectorGrid(-25.0, 25.0, -25.0, 25.0, 0.4)
    budget = {"boundary_point_solves": PRIOR_SOLVES_SPENT,
              "spent_on_an_aborted_first_execution": PRIOR_SOLVES_SPENT,
              "transfer_ray_calls": 0, "cap": SOLVE_CAP}
    CACHE.mkdir(parents=True, exist_ok=True)

    maps = {n: read(MAPS / f"{GEOMETRY}_n{n}_{PROFILE}.h5") for n in ORDERS}
    cells = {n: M.build_ray_cells(m.alpha, m.beta, M.NODAL_DUAL_CLIPPED)
             for n, m in maps.items()}
    fields = {n: screen_fields(m.alpha, m.beta) for n, m in maps.items()}
    whiten = 1.0 / (SIGMA * np.sqrt(grid.cell_area))

    def build(level, shifted=False, xtol=None):
        tag = f"L{level}_s{int(shifted)}_x{xtol}"
        f = CACHE / f"{tag}.npz"
        if f.exists():
            d = np.load(f, allow_pickle=True)
            return ({k: d[k] for k in d.files if k != "prov"},
                    {**json.loads(str(d["prov"])), "from_cache": True})
        mk = HU.shifted_marks if shifted else HU.critical_marks
        ma, mb, prov = mk(SPIN, INC, level)
        hs, st = HU.solve_hulls(ma, mb, SPIN, INC, LIMITS, xtol=xtol)
        budget["boundary_point_solves"] += st["solves"]
        prov = {**prov, **st, "xtol": xtol, "from_cache": False}
        np.savez(f, **hs, prov=json.dumps(prov))
        return hs, prov

    def response(hs, n):
        ov = FR.triple_overlap(cells[n], grid, hs[f"{n}e"], hs[f"{n}i"])
        y = np.zeros((grid.n_cells, len(FIELDS)))
        np.add.at(y, ov.rows, ov.vals[:, None] * fields[n][ov.cols])
        return y * whiten, ov

    levels, provs = {}, {}
    for L in LEVELS:
        hs, prov = build(L)
        levels[L], provs[L] = hs, prov
        print(f"level {L}: {prov['solves']} solves, "
              f"{prov['failures']} failures, {time.time() - t0:.0f}s",
              flush=True)

    # the archived hulls must be exactly what level 60 reproduces
    with h5py.File(ARCHIVE, "r") as f:
        repro = {n: bool(np.array_equal(levels[60][f"{n}i"], f[f"hull_{n}i"][:])
                         and np.array_equal(levels[60][f"{n}e"],
                                            f[f"hull_{n}e"][:]))
                 for n in ORDERS}

    star = {f"{n}{s}": HU.star_check(levels[LEVELS[-1]][f"{n}{s}"])
            for n in ORDERS for s in ("i", "e")}

    pairs, resp_cache = [], {}
    for L in LEVELS:
        resp_cache[L] = {n: response(levels[L], n) for n in ORDERS}
    for a, b in zip(LEVELS[:-1], LEVELS[1:]):
        for n in ORDERS:
            m = HU.region_measures(levels[b][f"{n}e"], levels[b][f"{n}i"],
                                   levels[a][f"{n}e"], levels[a][f"{n}i"],
                                   N_UNIFORM)
            m2 = HU.region_measures(levels[b][f"{n}e"], levels[b][f"{n}i"],
                                    levels[a][f"{n}e"], levels[a][f"{n}i"],
                                    2 * N_UNIFORM)
            u = m["band_union"]
            eta_b = m["band_symmetric_difference"] / u
            eta_e = (m["outer_symmetric_difference"]
                     + m["inner_symmetric_difference"]) / u
            yb, _ = resp_cache[b][n]
            ya, _ = resp_cache[a][n]
            nb = np.linalg.norm(yb)
            per = {FIELDS[k]: float(np.linalg.norm(yb[:, k] - ya[:, k])
                                    / max(np.linalg.norm(yb[:, k]),
                                          1e-12 * nb))
                   for k in range(len(FIELDS))}
            resp = max(per.values())
            quad = abs(m2["band_symmetric_difference"]
                       - m["band_symmetric_difference"]) / u
            pairs.append({
                "pair": f"{a}->{b}", "order": n, **m,
                "eta_band": eta_b, "eta_boundaries": eta_e,
                "hull_only_response_relative": resp,
                "hull_only_response_per_field": per,
                "worst_field": max(per, key=per.get),
                "angular_quadrature_self_check": quad,
                "quadrature_within_budget": bool(quad < QUAD_TOL),
                "band_passes": bool(eta_b < BAND_TOL),
                "boundaries_passes": bool(eta_e < BOUND_TOL),
                "response_passes": bool(resp < RESP_TOL),
                "all_pass": bool(eta_b < BAND_TOL and eta_e < BOUND_TOL
                                 and resp < RESP_TOL)})
            print(f"  {a}->{b} n{n}: band {eta_b:.3e} bnd {eta_e:.3e} "
                  f"resp {resp:.3e} quad {quad:.2e}", flush=True)

    def pair_ok(tag):
        rows = [p for p in pairs if p["pair"] == tag]
        return len(rows) == len(ORDERS) and all(p["all_pass"] for p in rows)

    accepted, checks = None, {}
    for i in range(2, len(LEVELS)):
        if pair_ok(f"{LEVELS[i - 1]}->{LEVELS[i]}") and \
                pair_ok(f"{LEVELS[i - 2]}->{LEVELS[i - 1]}"):
            accepted = LEVELS[i]
            break

    if accepted is not None:
        for tag, kw in (("half_step_shift", {"shifted": True}),
                        ("tighter_root", {"xtol": 1.49012e-9})):
            if budget["boundary_point_solves"] + 10 * accepted > SOLVE_CAP:
                checks[tag] = {"run": False,
                               "reason": "BOUNDARY_SOLVE_CAP_WOULD_BE_EXCEEDED"}
                continue
            hs, prov = build(accepted, **kw)
            rows = []
            for n in ORDERS:
                m = HU.region_measures(levels[accepted][f"{n}e"],
                                       levels[accepted][f"{n}i"],
                                       hs[f"{n}e"], hs[f"{n}i"], N_UNIFORM)
                yb, _ = resp_cache[accepted][n]
                ya, _ = response(hs, n)
                nb = np.linalg.norm(yb)
                r = max(float(np.linalg.norm(yb[:, k] - ya[:, k])
                              / max(np.linalg.norm(yb[:, k]), 1e-12 * nb))
                        for k in range(len(FIELDS)))
                e = m["band_symmetric_difference"] / m["band_union"]
                rows.append({"order": n, "band_discrepancy": e,
                             "response_discrepancy": r,
                             "passes": bool(e < ROOT_TOL and r < ROOT_TOL)})
                print(f"  {tag} n{n}: band {e:.3e} resp {r:.3e}", flush=True)
            checks[tag] = {"run": True, "level": accepted,
                           "tolerance": ROOT_TOL, "provenance": prov,
                           "rows": rows,
                           "passes": all(x["passes"] for x in rows)}

    qualified = (accepted is not None
                 and all(c.get("passes") for c in checks.values())
                 and len(checks) == 2)
    rep = {
        "stage": "H1", "ruling": "PAPER_I_FRACTIONAL_COVERAGE_RULING_027",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "commit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                 capture_output=True, text=True).stdout.strip(),
        "transfer_ray_calls": 0,
        "levels": list(LEVELS),
        "solves_per_direction": HU.SOLVES_PER_DIRECTION,
        "level_provenance": {str(k): v for k, v in provs.items()},
        "level_60_reproduces_archived_hulls_bitwise": repro,
        "star_shaped_at_finest_level": star,
        "tolerances": {"band": BAND_TOL, "boundaries": BOUND_TOL,
                       "hull_only_response": RESP_TOL,
                       "independent_check": ROOT_TOL,
                       "angular_quadrature": QUAD_TOL},
        "pairs": pairs,
        "accepted_level": accepted,
        "independent_checks": checks,
        "hull_geometry_qualified": bool(qualified),
        "budget": budget,
        "budget_exhausted": budget["boundary_point_solves"] > SOLVE_CAP,
        "transferred_fields": "not evaluated in H1; their support is limited "
                              "to fragments with valid transfer data and that "
                              "is an H2 question",
        "runtime_seconds": None,
    }
    rep["runtime_seconds"] = time.time() - t0
    (out_dir / "HULL_CONVERGENCE_027.json").write_text(
        json.dumps(rep, indent=2) + "\n")
    (out_dir / "HULL_ERROR_BUDGET_027.json").write_text(json.dumps({
        "stage": "H1",
        "declared_before_results": True,
        "band_symdiff_relative": BAND_TOL,
        "inner_plus_outer_symdiff_relative": BOUND_TOL,
        "hull_only_response_relative": RESP_TOL,
        "independent_shift_and_root_discrepancy": ROOT_TOL,
        "aggregate_numerical_integration_relative": QUAD_TOL,
        "denominator": "the band union of the compared pair, inside D026, "
                       "per order; never the outer hull and never the screen",
        "measured": [{"pair": p["pair"], "order": p["order"],
                      "eta_band": p["eta_band"],
                      "eta_boundaries": p["eta_boundaries"],
                      "hull_only_response": p["hull_only_response_relative"],
                      "angular_quadrature": p["angular_quadrature_self_check"]}
                     for p in pairs],
        "boundary_solves_used": budget["boundary_point_solves"],
        "boundary_solve_cap": SOLVE_CAP,
        "transfer_rays_used": 0,
    }, indent=2) + "\n")
    print(f"accepted level {accepted}, qualified {qualified}, "
          f"solves {budget['boundary_point_solves']}/{SOLVE_CAP}, "
          f"{rep['runtime_seconds']:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main((ROOT / sys.argv[1]).resolve()))
