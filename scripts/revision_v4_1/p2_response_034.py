#!/usr/bin/env python3
"""C2 of ruling 034: the detector-response error the budget is written against.

The 033 stage counted how often a raw node value crossed 5e-4. Ruling 034 is
right that this cannot bound the quantity the budget is about: the reviewer's
own fixture builds an oscillatory field whose sampled discrepancies all exceed
the threshold and whose integrated difference on the detector is exactly zero.

So the comparison is redone where it belongs. The inherited eleven-field test
suite -- six screen fields and five transferred fields at each of the eight
accepted observer times -- is built from cached tuples on both sides, carried
through the SAME detector geometry, the same overlap areas, the same single-sky
noise and the same absolute clock, and compared as whitened detector vectors.
Support that only one side has is omitted from the comparison and reported as a
coverage gap, never as agreement.

Zero physical queries: two archived maps and one archived hull are read.
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
from phrt.geometry.raymap import horizon_radius, read            # noqa: E402
from phrt.revision_v4_1 import domain as D                       # noqa: E402
from phrt.revision_v4_1 import fractional as FR                  # noqa: E402
from phrt.revision_v4_1 import measure as M                      # noqa: E402
from phrt.revision_v4_1.common_sky import DetectorGrid           # noqa: E402

MAPS = ROOT / "artifacts" / "raymaps"
AART = ROOT / "artifacts" / "e3_pilot" / "aart_out"
BANDS = {"core": AART / ("core/LensingBands_a_0.5_i_50.0_dx0_0.4_dx1_0.08"
                         "_dx2_0.02.h5"),
         "fine": AART / ("fine/LensingBands_a_0.5_i_50.0_dx0_0.2_dx1_0.04"
                         "_dx2_0.01.h5")}
HULL = ROOT / ("artifacts/revisions/mahakal_v4_1/G1C_20260907T075203Z_d252697"
               "/CLOSEOUT_ARRAYS_029.npz")
HELPER = ROOT / ("docs/revisions/mahakal_v4_1/review034/"
                 "response_checks_034.py")
GEOMETRY, SPIN, INC, R_OUTER = "a050_i050", 0.5, 50.0, 50.0
SIGMA, T_REF = 0.011341986814407566, -978.6055123201214
T_OBS = [0.0, 2.857142857142857, 5.714285714285714, 8.571428571428571,
         11.428571428571429, 14.285714285714286, 17.142857142857142, 20.0]
# the inherited definitions, copied from v2_partial_response.py
SCREEN = ("1", "alpha/25", "beta/25", "(alpha/25)^2", "(beta/25)^2",
          "alpha*beta/625")
TRANSFER = ("g^3", "g^3*cos20", "g^3*sin20", "g^3*cos40", "g^3*sin40")
COMPONENT_BUDGET = 5.0e-4


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with Path(p).open("rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def helper():
    spec = importlib.util.spec_from_file_location("rev034", HELPER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def build_fields(alpha, beta, redshift, coord_time, emit):
    """The eleven inherited channels, screen first then transferred by time."""
    cols, labels = [], []
    for nm, v in zip(SCREEN, (np.ones(alpha.size), alpha / 25, beta / 25,
                              (alpha / 25) ** 2, (beta / 25) ** 2,
                              alpha * beta / 625)):
        cols.append(np.asarray(v, float))
        labels.append(f"screen:{nm}")
    g3 = np.where(emit, np.abs(redshift) ** 3, 0.0)
    delay = T_REF - coord_time
    for t in T_OBS:
        ph = np.where(emit, t - delay, 0.0)
        for nm, v in zip(TRANSFER, (g3,
                                    g3 * np.cos(2 * np.pi * ph / 20),
                                    g3 * np.sin(2 * np.pi * ph / 20),
                                    g3 * np.cos(2 * np.pi * ph / 40),
                                    g3 * np.sin(2 * np.pi * ph / 40))):
            cols.append(np.nan_to_num(np.asarray(v, float), nan=0.0))
            labels.append(f"transferred:{nm}@t={t:.6f}")
    return np.stack(cols, axis=1), labels


def order_response(n: int, cmp_fn) -> dict:
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

    # the coarse representation carried onto the fine nodes, exactly as 033
    ca, cb = np.unique(core.alpha), np.unique(core.beta)
    ia = np.clip(np.searchsorted(ca, fine.alpha) - 1, 0, ca.size - 2)
    ib = np.clip(np.searchsorted(cb, fine.beta) - 1, 0, cb.size - 2)
    ta = (fine.alpha - ca[ia]) / (ca[ia + 1] - ca[ia])
    tb = (fine.beta - cb[ib]) / (cb[ib + 1] - cb[ib])
    nb = cb.size
    idx = np.stack([ia * nb + ib, (ia + 1) * nb + ib,
                    ia * nb + (ib + 1), (ia + 1) * nb + (ib + 1)])
    ok = np.isfinite(core.redshift) & np.isfinite(core.source_r)
    w = np.stack([(1 - ta) * (1 - tb), ta * (1 - tb),
                  (1 - ta) * tb, ta * tb])

    def carry(field):
        g = np.where(ok, getattr(core, field), np.nan)
        return np.einsum("ij,ij->j", w, g[idx])

    z_hat = carry("redshift")
    t_hat = carry("coordinate_time")
    have_hat = np.isfinite(z_hat) & np.isfinite(t_hat)
    have_ref = np.isfinite(fine.redshift) & np.isfinite(fine.coordinate_time)
    support = emit & have_hat & have_ref

    cells = M.build_ray_cells(fine.alpha, fine.beta, M.NODAL_DUAL_CLIPPED)
    ov = FR.triple_overlap(cells, grid, hz[f"tess_{n}e"], hz[f"tess_{n}i"])
    keep = support[ov.cols]
    cols_kept = ov.cols[keep]
    uniq, inv = np.unique(cols_kept, return_inverse=True)
    O = sparse.csr_matrix(
        (ov.vals[keep], (ov.rows[keep], inv)),
        shape=(grid.n_cells, uniq.size))

    F_ref, labels = build_fields(fine.alpha[uniq], fine.beta[uniq],
                                 fine.redshift[uniq],
                                 fine.coordinate_time[uniq],
                                 np.ones(uniq.size, bool))
    F_hat, _ = build_fields(fine.alpha[uniq], fine.beta[uniq], z_hat[uniq],
                            t_hat[uniq], np.ones(uniq.size, bool))
    A = np.full(grid.n_cells, grid.cell_area)
    res = cmp_fn(O, F_hat, F_ref, A, SIGMA)

    emit_area = float(ov.active_area[emit].sum())
    kept_area = float(ov.vals[keep].sum())
    all_area = float(ov.vals.sum())
    rel = np.asarray(res["relative"], float)
    scr = rel[:len(SCREEN)]
    tra = rel[len(SCREEN):]
    return {
        "order": n,
        "channels": len(labels),
        "labels": labels,
        "support": {
            "fine_emitting_nodes": int(emit.sum()),
            "nodes_compared": int(uniq.size),
            "node_coverage_of_emitting": float(
                uniq.size / max(int(emit.sum()), 1)),
            "compared_overlap_area": kept_area,
            "emitting_overlap_area": emit_area,
            "band_overlap_area": all_area,
            "area_coverage_of_emitting": kept_area / max(emit_area, 1e-30),
            "area_omitted_from_the_comparison": emit_area - kept_area,
            "omitted_support_has_no_response_bound": True,
        },
        "whitened_relative_error": {
            "screen_channels": {"max": float(np.nanmax(scr)),
                                "median": float(np.nanmedian(scr))},
            "transferred_channels": {"max": float(np.nanmax(tra)),
                                     "median": float(np.nanmedian(tra)),
                                     "p95": float(np.nanquantile(tra, 0.95)),
                                     "above_component_budget": int(
                                         np.count_nonzero(
                                             tra > COMPONENT_BUDGET)),
                                     "of": int(tra.size)},
            "worst_channel": labels[int(np.nanargmax(rel))],
            "worst_value": float(np.nanmax(rel)),
        },
        "absolute_whitened_error": {
            "max": float(np.max(res["absolute"])),
            "reference_norm_max": float(np.max(res["reference_norm"]))},
        "supplied_field_L2_upper_bound": {
            "max": float(np.max(res["supplied_field_L2_upper"])),
            "note": "discrete Cauchy-Schwarz on the supplied piecewise field; "
                    "an upper bound on this comparison, not a certificate for "
                    "the sky"},
        "vectors": {"reference": res["reference_response"],
                    "estimated": res["estimated_response"]},
    }


def main(out: Path) -> int:
    t0 = time.time()
    mod = helper()
    per, arrays = {}, {}
    for n in (0, 1, 2):
        r = order_response(n, mod.compare_cached)
        arrays[f"n{n}_reference"] = r.pop("vectors")["reference"]
        per[f"n{n}"] = r
        w = r["whitened_relative_error"]
        s = r["support"]
        print(f"  order {n}: transferred max {w['transferred_channels']['max']:.3e}"
              f", screen max {w['screen_channels']['max']:.3e}, node coverage "
              f"{s['node_coverage_of_emitting']:.1%}, area coverage "
              f"{s['area_coverage_of_emitting']:.1%}", flush=True)
    # the estimated vectors were popped with the reference; rebuild the store
    np.savez_compressed(out / "CACHED_COMPOSITE_RESPONSE_034.npz", **arrays)
    rep = {
        "stage": "C2", "ruling": "PAPER_I_RESPONSE_ERROR_RULING_034",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "commit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                 capture_output=True, text=True).stdout.strip(),
        "new_rays": 0, "new_path_quadratures": 0,
        "field_manifest": {
            "screen": list(SCREEN), "transferred": list(TRANSFER),
            "observer_times": T_OBS, "channels": 6 + 5 * len(T_OBS),
            "source": "scripts/revision_v4_1/v2_partial_response.py, the "
                      "inherited definitions, copied not re-invented",
            "delay": "T_REF - coordinate_time, absolute clock reference "
                     f"{T_REF}",
            "g_cubed_from_the_carried_primitive_g": True,
            "g_is_not_interchangeable_with_g_cubed": True,
        },
        "comparison": {
            "utility": "docs/revisions/mahakal_v4_1/review034/"
                       "response_checks_034.py::compare_cached",
            "same_support_both_sides": True,
            "same_overlap_operator_both_sides": True,
            "noise": "single-sky sigma^2 over the full detector area once per "
                     "pixel",
            "metric": "norm(W(y_hat - y_ref)) / norm(W y_ref), per channel; "
                      "never a difference of norms",
        },
        "per_order": per,
        "small_residual_on_available_support_qualifies_full_quadrature": False,
        "signed_cancellation_does_not_bound_omitted_support": True,
        "runtime_seconds": time.time() - t0,
    }
    (out / "RESPONSE_ERROR_AND_OMITTED_SUPPORT_034.json").write_text(
        json.dumps(rep, indent=2) + "\n")
    print(json.dumps({"stage": "C2", "seconds": round(time.time() - t0)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main((ROOT / sys.argv[1]).resolve()))
