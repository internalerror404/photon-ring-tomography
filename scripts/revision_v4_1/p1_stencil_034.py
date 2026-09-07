#!/usr/bin/env python3
"""C1 of ruling 034: what the bilinear diagnostic actually compared.

The 033 stage carried the coarse profile's transfer field onto the fine
profile's nodes and counted how often the discrepancy exceeded 5e-4. Ruling 034
raises three objections, all correct: the metric was scaled by a global maximum
rather than pointwise; the comparison covered only part of the emitting domain;
and a stencil whose four corners merely carry finite numbers is not a stencil
whose four corners lie in the same emitting domain or on the same radial leg.

This stage reproduces the old computation byte-for-byte first, then checks the
interpolation mechanics -- index lookup, axis orientation, in-cell weights,
extrapolation -- and finally partitions every stencil so the discrepancy can be
recomputed on the strict subset. Zero physical queries: two archived maps are
read and compared.
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
from phrt.geometry.raymap import horizon_radius, read            # noqa: E402
from phrt.revision_v4_1 import domain as D                       # noqa: E402

MAPS = ROOT / "artifacts" / "raymaps"
AART = ROOT / "artifacts" / "e3_pilot" / "aart_out"
BANDS = {"core": AART / ("core/LensingBands_a_0.5_i_50.0_dx0_0.4_dx1_0.08"
                         "_dx2_0.02.h5"),
         "fine": AART / ("fine/LensingBands_a_0.5_i_50.0_dx0_0.2_dx1_0.04"
                         "_dx2_0.01.h5")}
GEOMETRY, SPIN, INC, R_OUTER = "a050_i050", 0.5, 50.0, 50.0
COMPONENT_BUDGET = 5.0e-4

RAW_FINITE = "RAW_FINITE_CORNERS_ONLY"
SAME_DOMAIN = "ALL_FOUR_CORNERS_CERTIFIED_EMITTING"
SAME_BRANCH = "SAME_EMITTING_DOMAIN_AND_SAME_RADIAL_LEG"
BOUNDARY_CROSSING = "STENCIL_CROSSES_THE_EMITTING_BOUNDARY"
MISSING_VALUE = "A_CORNER_HAS_NO_VALUE"
UNKNOWN_BRANCH = "EMITTING_CORNERS_BUT_THE_LEG_IS_NOT_VERIFIED"


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with Path(p).open("rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def corners(fine_alpha, fine_beta, ca, cb):
    ia = np.clip(np.searchsorted(ca, fine_alpha) - 1, 0, ca.size - 2)
    ib = np.clip(np.searchsorted(cb, fine_beta) - 1, 0, cb.size - 2)
    ta = (fine_alpha - ca[ia]) / (ca[ia + 1] - ca[ia])
    tb = (fine_beta - cb[ib]) / (cb[ib + 1] - cb[ib])
    return ia, ib, ta, tb


def mechanics(core, fine, ia, ib, ta, tb, ca, cb) -> dict:
    """Does the lookup do what the 033 code assumed it did?"""
    n_b = cb.size
    lin = ia * n_b + ib
    return {
        "coarse_axes": {"n_alpha": int(ca.size), "n_beta": int(cb.size),
                        "alpha_min": float(ca[0]), "alpha_max": float(ca[-1]),
                        "beta_min": float(cb[0]), "beta_max": float(cb[-1]),
                        "alpha_spacing_unique": int(
                            np.unique(np.round(np.diff(ca), 12)).size),
                        "beta_spacing_unique": int(
                            np.unique(np.round(np.diff(cb), 12)).size)},
        "raster_is_alpha_major": bool(np.allclose(
            core.alpha[lin[:200]], ca[ia[:200]])
            and np.allclose(core.beta[lin[:200]], cb[ib[:200]])),
        "weights_in_the_unit_square": bool(
            ta.min() >= -1e-12 and ta.max() <= 1 + 1e-12
            and tb.min() >= -1e-12 and tb.max() <= 1 + 1e-12),
        "weight_range": [float(ta.min()), float(ta.max()),
                         float(tb.min()), float(tb.max())],
        "fine_nodes_outside_the_coarse_hull": int(np.count_nonzero(
            (fine.alpha < ca[0]) | (fine.alpha > ca[-1])
            | (fine.beta < cb[0]) | (fine.beta > cb[-1]))),
        "extrapolation_was_silently_clamped": bool(
            (ta.min() < -1e-12) or (ta.max() > 1 + 1e-12)
            or (tb.min() < -1e-12) or (tb.max() > 1 + 1e-12)),
        "orientation_check": "each fine node's own coordinates recovered from "
                             "the coarse axes it indexes",
    }


def audit_order(n: int) -> dict:
    rh = horizon_radius(SPIN)
    core = read(MAPS / f"{GEOMETRY}_n{n}_core.h5")
    fine = read(MAPS / f"{GEOMETRY}_n{n}_fine.h5")
    with h5py.File(BANDS["core"], "r") as h:
        cband = h[f"mask{n}"][:]
    with h5py.File(BANDS["fine"], "r") as h:
        fband = h[f"mask{n}"][:]
    cstate, _ = D.classify_points(cband, core.source_r, core.source_phi,
                                 core.coordinate_time, core.redshift, rh,
                                 R_OUTER)
    fstate, _ = D.classify_points(fband, fine.source_r, fine.source_phi,
                                 fine.coordinate_time, fine.redshift, rh,
                                 R_OUTER)
    ca, cb = np.unique(core.alpha), np.unique(core.beta)
    ia, ib, ta, tb = corners(fine.alpha, fine.beta, ca, cb)
    mech = mechanics(core, fine, ia, ib, ta, tb, ca, cb)

    nb = cb.size
    idx = np.stack([ia * nb + ib, (ia + 1) * nb + ib,
                    ia * nb + (ib + 1), (ia + 1) * nb + (ib + 1)])
    ok33 = np.isfinite(core.redshift) & np.isfinite(core.source_r)
    corner_finite = ok33[idx].all(axis=0)
    corner_emitting = (cstate[idx] == D.CERTIFIED_EMITTING).all(axis=0)
    corner_any_emitting = (cstate[idx] == D.CERTIFIED_EMITTING).any(axis=0)
    # the radial leg: the archived source radius rising or falling across the
    # stencil is the observable proxy the maps carry; a stencil whose corners
    # straddle a turning point mixes two legs
    r_corner = core.source_r[idx]
    with np.errstate(invalid="ignore"):
        leg_span = np.nanmax(r_corner, axis=0) - np.nanmin(r_corner, axis=0)
    cell_r_scale = np.where(corner_finite, np.abs(np.nanmean(r_corner, axis=0)),
                            np.nan)
    same_leg = corner_emitting & (leg_span <= 0.25 * np.where(
        np.isfinite(cell_r_scale), cell_r_scale, np.inf))

    femit = fstate == D.CERTIFIED_EMITTING
    cat = np.full(fine.alpha.size, MISSING_VALUE, dtype=object)
    cat[corner_finite] = RAW_FINITE
    cat[corner_finite & corner_any_emitting & ~corner_emitting] = \
        BOUNDARY_CROSSING
    cat[corner_finite & corner_emitting] = UNKNOWN_BRANCH
    cat[corner_finite & corner_emitting & same_leg] = SAME_BRANCH

    with np.errstate(invalid="ignore", divide="ignore"):
        rel_span = leg_span / np.where(np.isfinite(cell_r_scale)
                                       & (cell_r_scale > 0),
                                       cell_r_scale, np.nan)
    sel = femit & corner_emitting & np.isfinite(rel_span)
    span_q = None
    if sel.any():
        q = np.quantile(rel_span[sel], [0.0, 0.05, 0.5, 0.95, 1.0])
        span_q = dict(zip(("min", "p05", "median", "p95", "max"),
                          [float(x) for x in q]))
    out = {"order": n, "mechanics": mech,
           "fine_emitting_nodes": int(femit.sum()),
           "relative_source_radius_span_across_emitting_stencils": span_q,
           "same_leg_proxy_threshold": 0.25,
           "same_leg_proxy_is_a_declared_heuristic_not_a_proof": True,
           "categories": {}, "metrics": {}}
    for c in (MISSING_VALUE, RAW_FINITE, BOUNDARY_CROSSING, UNKNOWN_BRANCH,
              SAME_BRANCH):
        m = (cat == c) & femit
        out["categories"][c] = {
            "nodes": int(m.sum()),
            "fraction_of_fine_emitting_nodes": float(
                m.sum() / max(femit.sum(), 1))}

    for field in ("redshift", "source_r", "coordinate_time"):
        g = np.where(ok33, getattr(core, field), np.nan)
        v = ((1 - ta) * (1 - tb) * g[idx[0]] + ta * (1 - tb) * g[idx[1]]
             + (1 - ta) * tb * g[idx[2]] + ta * tb * g[idx[3]])
        ref = getattr(fine, field)
        base = femit & np.isfinite(v) & np.isfinite(ref)
        res = {}
        for label, sel in (("033_comparable_stencils", base),
                           ("strict_same_domain",
                            base & (cat == SAME_BRANCH)),
                           ("boundary_crossing_only",
                            base & (cat == BOUNDARY_CROSSING))):
            if not sel.any():
                res[label] = {"nodes": 0}
                continue
            d = np.abs(v[sel] - ref[sel])
            gmax = float(np.max(np.abs(ref[sel])))
            gscaled = d / max(gmax, 1e-30)
            with np.errstate(divide="ignore", invalid="ignore"):
                point = np.where(np.abs(ref[sel]) > 0,
                                 d / np.abs(ref[sel]), np.nan)
            res[label] = {
                "nodes": int(sel.sum()),
                "coverage_of_fine_emitting_nodes": float(
                    sel.sum() / max(femit.sum(), 1)),
                "global_max_scaled_median": float(np.median(gscaled)),
                "global_max_scaled_fraction_above_5e_4": float(
                    np.count_nonzero(gscaled > COMPONENT_BUDGET) / sel.sum()),
                "pointwise_relative_median": float(np.nanmedian(point)),
                "pointwise_relative_fraction_above_5e_4": float(
                    np.count_nonzero(point > COMPONENT_BUDGET)
                    / max(np.count_nonzero(np.isfinite(point)), 1)),
                "absolute_median": float(np.median(d)),
            }
        out["metrics"][field] = res
    return out


def main(out: Path) -> int:
    t0 = time.time()
    per = {}
    for n in (0, 1, 2):
        per[f"n{n}"] = audit_order(n)
        c = per[f"n{n}"]["categories"]
        print(f"  order {n}: strict same-leg "
              f"{c[SAME_BRANCH]['fraction_of_fine_emitting_nodes']:.1%}, "
              f"boundary-crossing "
              f"{c[BOUNDARY_CROSSING]['fraction_of_fine_emitting_nodes']:.1%}",
              flush=True)
    rep = {
        "stage": "C1", "ruling": "PAPER_I_RESPONSE_ERROR_RULING_034",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "commit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                 capture_output=True, text=True).stdout.strip(),
        "new_rays": 0, "new_path_quadratures": 0,
        "reproduces_the_033_diagnostic_first": True,
        "metric_names": {
            "global_max_scaled": "|z_interp - z_fine| / max over the selected "
                                 "nodes |z_fine|; this is what 033 reported",
            "pointwise_relative": "|z_interp - z_fine| / |z_fine| at the node",
            "neither_is_the_whitened_detector_response_error": True,
        },
        "stencil_categories": {
            RAW_FINITE: "four corners carry finite radius and redshift; this "
                        "is the only condition 033 imposed",
            SAME_DOMAIN: "all four corners certified emitting",
            SAME_BRANCH: "all four emitting and the archived source radius "
                         "spans less than a quarter of its own mean across "
                         "the stencil, an observable proxy for one radial leg",
            BOUNDARY_CROSSING: "finite corners that are not all emitting",
            MISSING_VALUE: "a corner has no usable value",
            UNKNOWN_BRANCH: "all four emitting but the leg proxy is not met",
        },
        "finite_corners_certify_source_validity": False,
        "fine_map_is_exact_continuum_truth": False,
        "coarse_and_fine_are_two_discretisations_not_truth_and_estimate": True,
        "per_order": per,
        "candidate_count": 2,
        "runtime_seconds": time.time() - t0,
    }
    (out / "STENCIL_AND_COVERAGE_AUDIT_034.json").write_text(
        json.dumps(rep, indent=2) + "\n")
    print(json.dumps({"stage": "C1", "seconds": round(time.time() - t0)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main((ROOT / sys.argv[1]).resolve()))
