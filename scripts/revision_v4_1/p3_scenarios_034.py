#!/usr/bin/env python3
"""C2b of ruling 034: a cost scenario driven by response error, not node counts.

The 033 scenario extrapolated from the fraction of nodes crossing a threshold.
Ruling 034 shows why that cannot work: a field can fail at every node and
integrate to zero on the detector. The replacement asks the question the other
way round -- how much of the measured whitened response error is carried by how
little of the support?

By the triangle inequality the whitened response error is bounded by the sum of
per-node contributions

    c_p = || W O[:, p] ||_2 * |F_hat[p] - F_ref[p]|,

so refining the nodes with the largest c_p and leaving the rest alone bounds
what remains by the tail sum. That gives a defensible node count for a target,
and it is a bound rather than a forecast: the true error is generally smaller
because the contributions partly cancel.

Zero physical queries.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import time
from pathlib import Path

import h5py
import numpy as np
from scipy import sparse

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts" / "revision_v4_1"))
from phrt.geometry.raymap import horizon_radius, read            # noqa: E402
from phrt.revision_v4_1 import domain as D                       # noqa: E402
from phrt.revision_v4_1 import fractional as FR                  # noqa: E402
from phrt.revision_v4_1 import measure as M                      # noqa: E402
from phrt.revision_v4_1.common_sky import DetectorGrid           # noqa: E402
from p2_response_034 import (BANDS, GEOMETRY, HULL, MAPS, R_OUTER,  # noqa: E402
                             SCREEN, SIGMA, SPIN, build_fields)

COMPONENT_BUDGET = 5.0e-4
TARGETS = (0.5, 0.9, 0.99)


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with Path(p).open("rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def concentration(n: int) -> dict:
    rh = horizon_radius(SPIN)
    grid = DetectorGrid(-25.0, 25.0, -25.0, 25.0, 0.4)
    hz = np.load(HULL)
    core = read(MAPS / f"{GEOMETRY}_n{n}_core.h5")
    fine = read(MAPS / f"{GEOMETRY}_n{n}_fine.h5")
    with h5py.File(BANDS["fine"], "r") as h:
        fband = h[f"mask{n}"][:]
    fstate, _ = D.classify_points(fband, fine.source_r, fine.source_phi,
                                  fine.coordinate_time, fine.redshift, rh,
                                  R_OUTER)
    emit = fstate == D.CERTIFIED_EMITTING
    ca, cb = np.unique(core.alpha), np.unique(core.beta)
    ia = np.clip(np.searchsorted(ca, fine.alpha) - 1, 0, ca.size - 2)
    ib = np.clip(np.searchsorted(cb, fine.beta) - 1, 0, cb.size - 2)
    ta = (fine.alpha - ca[ia]) / (ca[ia + 1] - ca[ia])
    tb = (fine.beta - cb[ib]) / (cb[ib + 1] - cb[ib])
    nb = cb.size
    idx = np.stack([ia * nb + ib, (ia + 1) * nb + ib,
                    ia * nb + (ib + 1), (ia + 1) * nb + (ib + 1)])
    ok = np.isfinite(core.redshift) & np.isfinite(core.source_r)
    w4 = np.stack([(1 - ta) * (1 - tb), ta * (1 - tb),
                   (1 - ta) * tb, ta * tb])

    def carry(field):
        g = np.where(ok, getattr(core, field), np.nan)
        return np.einsum("ij,ij->j", w4, g[idx])

    z_hat, t_hat = carry("redshift"), carry("coordinate_time")
    support = emit & np.isfinite(z_hat) & np.isfinite(t_hat) \
        & np.isfinite(fine.redshift) & np.isfinite(fine.coordinate_time)

    cells = M.build_ray_cells(fine.alpha, fine.beta, M.NODAL_DUAL_CLIPPED)
    ov = FR.triple_overlap(cells, grid, hz[f"tess_{n}e"], hz[f"tess_{n}i"])
    keep = support[ov.cols]
    uniq, inv = np.unique(ov.cols[keep], return_inverse=True)
    O = sparse.csr_matrix((ov.vals[keep], (ov.rows[keep], inv)),
                          shape=(grid.n_cells, uniq.size))
    whiten = 1.0 / (SIGMA * np.sqrt(grid.cell_area))

    F_ref, labels = build_fields(fine.alpha[uniq], fine.beta[uniq],
                                 fine.redshift[uniq],
                                 fine.coordinate_time[uniq],
                                 np.ones(uniq.size, bool))
    F_hat, _ = build_fields(fine.alpha[uniq], fine.beta[uniq], z_hat[uniq],
                            t_hat[uniq], np.ones(uniq.size, bool))
    dF = F_hat - F_ref
    # || W O[:, p] ||_2 for every supported node
    colnorm = whiten * np.sqrt(np.asarray(O.multiply(O).sum(axis=0)).ravel())
    tr = slice(len(SCREEN), None)
    y_ref = (O @ F_ref[:, tr]) * whiten
    y_hat = (O @ F_hat[:, tr]) * whiten
    true_abs = float(np.max(np.linalg.norm(y_hat - y_ref, axis=0)))
    denom = float(np.max(np.linalg.norm(y_ref, axis=0)))

    c = colnorm * np.max(np.abs(dF[:, tr]), axis=1)
    order = np.argsort(-c)
    cum = np.cumsum(c[order])
    total = float(cum[-1]) if cum.size else 0.0
    out = {
        "order": n, "supported_nodes": int(uniq.size),
        "triangle_bound_on_the_worst_transferred_channel": total,
        "measured_worst_transferred_absolute_error": true_abs,
        "reference_norm": denom,
        "bound_is_conservative_by": (total / true_abs) if true_abs > 0 else None,
        "budget_absolute": COMPONENT_BUDGET * denom,
        "concentration": {},
    }
    for f in TARGETS:
        k = int(np.searchsorted(cum, f * total) + 1) if total > 0 else 0
        out["concentration"][f"{f:.2f}"] = {
            "nodes": k, "fraction_of_support": k / max(uniq.size, 1)}
    # how many nodes must be refined for the tail bound to fall inside budget
    need = COMPONENT_BUDGET * denom
    k = int(np.searchsorted(-(total - cum), -need) + 1) if total > need else 0
    out["nodes_whose_refinement_brings_the_tail_bound_inside_budget"] = k
    out["fraction_of_support_needing_refinement"] = k / max(uniq.size, 1)
    out["already_inside_budget"] = bool(total <= need)
    return out


def main(out: Path) -> int:
    t0 = time.time()
    resp = json.loads(
        (out / "RESPONSE_ERROR_AND_OMITTED_SUPPORT_034.json").read_text())
    per = {}
    for n in (0, 1, 2):
        per[f"n{n}"] = concentration(n)
        c = per[f"n{n}"]
        print(f"  order {n}: {c['supported_nodes']} supported, "
              f"{c['nodes_whose_refinement_brings_the_tail_bound_inside_budget']}"
              f" ({c['fraction_of_support_needing_refinement']:.1%}) would have "
              f"to be refined", flush=True)
    scen = {}
    tot4 = 0
    for n in (0, 1, 2):
        k = per[f"n{n}"]["nodes_whose_refinement_brings_the_tail_bound_inside_budget"]
        scen[f"n{n}"] = {
            "nodes_to_refine": k,
            "at_2x2_per_node": 4 * k,
            "note": "a scenario at one declared refinement factor, not a "
                    "measured call count",
        }
        tot4 += 4 * k
    rep = {
        "stage": "C2b", "ruling": "PAPER_I_RESPONSE_ERROR_RULING_034",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "commit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                 capture_output=True, text=True).stdout.strip(),
        "new_rays": 0,
        "method": ("per-node contribution c_p = ||W O[:,p]||_2 * "
                   "|F_hat[p] - F_ref[p]|, ranked; the tail sum bounds what is "
                   "left after refining the head. A bound, not a forecast: the "
                   "true error is smaller because contributions cancel."),
        "measured_response_error": {
            f"n{n}": resp["per_order"][f"n{n}"]["whitened_relative_error"]
            for n in (0, 1, 2)},
        "per_order": per,
        "scenario_at_2x2": scen,
        "scenario_total_at_2x2": tot4,
        "compare_033_interior_scenario": 49037,
        "compare_033_expected_total": 101416,
        "these_are_scenarios_not_measured_efficiency": True,
        "boundary_term_is_not_negligible_in_either_model": True,
        "omitted_support_is_not_covered_by_any_of_these_numbers": True,
        "runtime_seconds": time.time() - t0,
    }
    (out / "RESPONSE_BASED_COST_SCENARIOS_034.json").write_text(
        json.dumps(rep, indent=2) + "\n")
    print(json.dumps({"stage": "C2b", "scenario_total_at_2x2": tot4,
                      "seconds": round(time.time() - t0)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main((ROOT / sys.argv[1]).resolve()))
