#!/usr/bin/env python3
"""V1 of ruling 028: the r_source = 50 contour, and solver recovery.

Every physical call goes through the guard, which verifies the committed
freeze and meters the ledger. A solver failure is never converted into a
physical boundary, and a failed value is never filled with zero.
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
from phrt.revision_v4_1 import measure as M                  # noqa: E402
from phrt.revision_v4_1 import query as Q                    # noqa: E402
from phrt.revision_v4_1.common_sky import DetectorGrid       # noqa: E402

MAPS = ROOT / "artifacts" / "raymaps"
BANDS = ROOT / ("artifacts/e3_pilot/aart_out/core/"
                "LensingBands_a_0.5_i_50.0_dx0_0.4_dx1_0.08_dx2_0.02.h5")
GEOMETRY, SPIN, R_OUTER = "a050_i050", 0.5, 50.0
CONTOUR_ORDERS = (1, 2)          # order 0 has no out-of-annulus samples
N_REPRO = 200                    # cache-reproduction probes per order
N_BISECT = 9                     # halvings; screen bracket / 512
N_INDEPENDENT = 150              # contour points re-derived from a shift


def straddling_pairs(alpha, beta, r, ok):
    """Adjacent cached samples on opposite sides of the annulus edge."""
    ua = np.unique(alpha)
    n = ua.size
    inn = (ok & (r <= R_OUTER)).reshape(n, n)
    out = (ok & (r > R_OUTER)).reshape(n, n)
    A = alpha.reshape(n, n)
    B = beta.reshape(n, n)
    P = []
    for sl_i, sl_j, ax in (((slice(None, -1), slice(None)),
                            (slice(1, None), slice(None)), 0),
                           ((slice(None), slice(None, -1)),
                            (slice(None), slice(1, None)), 1)):
        for lo, hi in ((inn, out), (out, inn)):
            m = lo[sl_i] & hi[sl_j]
            if not m.any():
                continue
            P.append(np.stack([A[sl_i][m], B[sl_i][m],
                               A[sl_j][m], B[sl_j][m]], axis=1))
    return np.concatenate(P) if P else np.zeros((0, 4))


def bisect(pairs, order, guard, why):
    """Safeguarded bisection on a bracket, refusing to cross a failure.

    A sign change is not on its own a certificate: both endpoints must be
    finite and on the same radial branch, and every midpoint must stay finite.
    A bracket that loses either property stops refining and is returned as
    unresolved rather than being root-found across the discontinuity.
    """
    lo = pairs[:, :2].copy()
    hi = pairs[:, 2:].copy()
    e0 = Q.trace_points(lo[:, 0], lo[:, 1], order, guard, f"{why}:lo")
    e1 = Q.trace_points(hi[:, 0], hi[:, 1], order, guard, f"{why}:hi")
    f0, f1 = e0["source_r"] - R_OUTER, e1["source_r"] - R_OUTER
    live = (np.isfinite(f0) & np.isfinite(f1) & (np.sign(f0) != np.sign(f1))
            & (e0["radial_sign"] == e1["radial_sign"]))
    dead = ~live
    reason = np.where(np.isfinite(f0) & np.isfinite(f1),
                      np.where(e0["radial_sign"] == e1["radial_sign"],
                               "NO_SIGN_CHANGE", "BRANCH_CHANGE"),
                      "ENDPOINT_NOT_FINITE")
    for _ in range(N_BISECT):
        mid = 0.5 * (lo + hi)
        em = Q.trace_points(mid[:, 0], mid[:, 1], order, guard, f"{why}:mid")
        fm = em["source_r"] - R_OUTER
        broke = live & (~np.isfinite(fm)
                        | (em["radial_sign"] != e0["radial_sign"]))
        reason = np.where(broke, "INTERIOR_NOT_FINITE_OR_BRANCH_CHANGE",
                          reason)
        live = live & ~broke
        take = live & (np.sign(fm) == np.sign(f0))
        lo = np.where(take[:, None], mid, lo)
        f0 = np.where(take, fm, f0)
        hi = np.where((live & ~take)[:, None], mid, hi)
        f1 = np.where(live & ~take, fm, f1)
    width = np.hypot(hi[:, 0] - lo[:, 0], hi[:, 1] - lo[:, 1])
    return {"point": 0.5 * (lo + hi), "resolved": live,
            "screen_bracket_M": width, "reason": reason,
            "residual": np.where(live, np.minimum(np.abs(f0), np.abs(f1)),
                                 np.nan),
            "n_unresolved": int((~live).sum())}


def main(out: Path, freeze: Path) -> int:
    t0 = time.time()
    guard = Q.Guard(freeze)
    out.mkdir(parents=True, exist_ok=False)
    rh = horizon_radius(SPIN)
    rng = np.random.default_rng(2028)
    diag, contours = {}, {}

    with h5py.File(BANDS, "r") as f:
        band = {n: f[f"mask{n}"][:] for n in (0, 1, 2)}

    # ---- A: does the pinned tracer reproduce the archive, and can it
    # recover what the archive left unresolved? -------------------------
    for n in (0, 1, 2):
        rm = read(MAPS / f"{GEOMETRY}_n{n}_core.h5")
        ok = band[n] & np.isfinite(rm.source_r)
        idx = rng.choice(np.flatnonzero(ok), size=min(N_REPRO, int(ok.sum())),
                         replace=False)
        e = Q.trace_points(rm.alpha[idx], rm.beta[idx], n, guard,
                           f"cache_reproduction_n{n}")
        d = np.abs(e["source_r"] - rm.source_r[idx])
        bad = band[n] & ~np.isfinite(rm.source_r)
        rec = {"attempted": 0, "recovered": 0}
        if bad.any():
            j = np.flatnonzero(bad)
            er = Q.trace_points(rm.alpha[j], rm.beta[j], n, guard,
                                f"solver_recovery_n{n}")
            good = np.isfinite(er["source_r"])
            rec = {"attempted": int(j.size), "recovered": int(good.sum()),
                   "still_unresolved": int((~good).sum()),
                   "recovered_inside_annulus":
                       int((good & (er["source_r"] > rh)
                            & (er["source_r"] <= R_OUTER)).sum()),
                   "recovered_outside_annulus":
                       int((good & (er["source_r"] > R_OUTER)).sum())}
        diag[str(n)] = {
            "cache_reproduction": {
                "n": int(idx.size), "max_abs_diff": float(d.max()),
                "reproduces_to_1e_12": bool(d.max() < 1e-12)},
            "solver_recovery": rec,
            "recovery_used_same_equations_and_policy": True}
        print(f"  n{n}: cache repro max diff {d.max():.3e}; recovery "
              f"{rec.get('recovered', 0)}/{rec['attempted']}", flush=True)

    # ---- B: the emission contour ---------------------------------------
    for n in CONTOUR_ORDERS:
        rm = read(MAPS / f"{GEOMETRY}_n{n}_core.h5")
        ok = band[n] & np.isfinite(rm.source_r)
        pr = straddling_pairs(rm.alpha, rm.beta, rm.source_r, ok)
        need = pr.shape[0] * (2 + N_BISECT)
        if need > guard.remaining(Q.TRANSFER) - 4000:
            keep = max(0, (guard.remaining(Q.TRANSFER) - 4000)
                       // (2 + N_BISECT))
            print(f"  n{n}: trimming {pr.shape[0]} brackets to {keep} to "
                  f"keep the independent-validation reserve", flush=True)
            pr = pr[rng.choice(pr.shape[0], size=keep, replace=False)]
        c = bisect(pr, n, guard, f"contour_n{n}")
        contours[str(n)] = {
            "brackets": int(pr.shape[0]),
            "resolved": int(c["resolved"].sum()),
            "unresolved": c["n_unresolved"],
            "unresolved_reasons": {r: int((c["reason"] == r).sum())
                                   for r in np.unique(c["reason"])
                                   if r != "resolved"},
            "screen_bracket_max_M": float(c["screen_bracket_M"]
                                          [c["resolved"]].max())
            if c["resolved"].any() else None,
            "residual_max": float(np.nanmax(c["residual"]))
            if c["resolved"].any() else None,
            "one_root_per_line_assumed": False,
            "equal_signs_treated_as_no_root": "recorded as NO_SIGN_CHANGE, "
                                              "which does not prove absence "
                                              "of a contour in that interval",
        }
        contours[str(n)]["_pts"] = c
        print(f"  n{n}: {int(c['resolved'].sum())}/{pr.shape[0]} contour "
              f"points, bracket <= "
              f"{contours[str(n)]['screen_bracket_max_M']:.2e} M", flush=True)

    # ---- C: independent re-derivation from a different bracket ----------
    indep = {}
    for n in CONTOUR_ORDERS:
        c = contours[str(n)]["_pts"]
        j = np.flatnonzero(c["resolved"])
        if j.size == 0:
            indep[str(n)] = {"run": False, "reason": "no resolved points"}
            continue
        j = rng.choice(j, size=min(N_INDEPENDENT, j.size), replace=False)
        p = c["point"][j]
        w = c["screen_bracket_M"][j][:, None]
        # a bracket rotated a quarter turn about the found point: different
        # endpoints, same equations
        off = np.stack([-(p[:, 1] - p[:, 1].mean()),
                        p[:, 0] - p[:, 0].mean()], axis=1)
        off /= np.maximum(np.hypot(off[:, 0], off[:, 1])[:, None], 1e-30)
        span = 8.0 * np.maximum(w, 1e-6)
        pr2 = np.concatenate([p - span * off, p + span * off], axis=1)
        if pr2.shape[0] * (2 + N_BISECT) > guard.remaining(Q.TRANSFER):
            indep[str(n)] = {"run": False,
                             "reason": "TRANSFER_RESERVE_INSUFFICIENT"}
            continue
        c2 = bisect(pr2, n, guard, f"independent_n{n}")
        d = np.hypot(*(c2["point"] - p).T)
        m = c2["resolved"]
        indep[str(n)] = {
            "run": True, "n": int(p.shape[0]),
            "reresolved": int(m.sum()),
            "max_position_difference_M": float(d[m].max()) if m.any() else None,
            "median_position_difference_M": float(np.median(d[m]))
            if m.any() else None,
            "bracket_is_a_different_segment_not_a_resample": True}
        print(f"  n{n} independent: {int(m.sum())}/{p.shape[0]}, max "
              f"position diff "
              f"{indep[str(n)]['max_position_difference_M']:.2e} M", flush=True)

    # ---- uncertain support and what it could do to the response ---------
    grid = DetectorGrid(-25.0, 25.0, -25.0, 25.0, 0.4)
    unc = {}
    for n in CONTOUR_ORDERS:
        rm = read(MAPS / f"{GEOMETRY}_n{n}_core.h5")
        cells = M.build_ray_cells(rm.alpha, rm.beta, M.NODAL_DUAL_CLIPPED)
        c = contours[str(n)]["_pts"]
        bad = ~c["resolved"]
        # the tube is the cells the unresolved brackets fall in
        area = 0.0
        if bad.any():
            mid = 0.5 * (c["point"][bad] + c["point"][bad])
            ia = np.clip(np.searchsorted(cells.axis_alpha.hi, mid[:, 0]), 0,
                         cells.axis_alpha.nodes.size - 1)
            ib = np.clip(np.searchsorted(cells.axis_beta.hi, mid[:, 1]), 0,
                         cells.axis_beta.nodes.size - 1)
            area = float(np.unique(np.stack([ia, ib], 1), axis=0).shape[0]
                         * cells.axis_alpha.spacing
                         * cells.axis_beta.spacing)
        unc[str(n)] = {
            "unresolved_bracket_cells_area_M2": area,
            "validated_field_envelope_available": False,
            "why": "an envelope has to bound g^3 over the uncertain tube, "
                   "and a maximum over nearby samples is not a bound. None "
                   "was established, so no response bound is claimed",
            "blocker": "UNCERTAIN_SUPPORT_RESPONSE_ENVELOPE_NOT_VALIDATED"
            if area > 0 else None}

    for k in contours:
        contours[k].pop("_pts", None)
    rep = {
        "stage": "V1", "ruling": "PAPER_I_BOUNDARY_VALIDITY_RULING_028",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "commit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                 capture_output=True, text=True).stdout.strip(),
        "guard": guard.snapshot(),
        "solver_failure_is_not_a_physical_boundary": True,
        "diagnostic": diag, "contour": contours,
        "independent_validation": indep,
        "uncertain_support": unc,
        "runtime_seconds": time.time() - t0,
    }
    (out / "EMISSION_CONTOUR_AND_UNCERTAINTY_028.json").write_text(
        json.dumps(rep, indent=2) + "\n")
    (out / "SOLVER_FAILURE_AND_RECOVERY_028.json").write_text(json.dumps({
        "stage": "V1", "primitives": list(D.PRIMITIVES),
        "policy": "same physical equations; no backend substitution; a value "
                  "that stays unresolved keeps that status and is never "
                  "filled with zero",
        "per_order": {k: v["solver_recovery"] for k, v in diag.items()},
        "guard": guard.snapshot(),
    }, indent=2) + "\n")
    print(f"  transfer evaluations {guard.spent[Q.TRANSFER]}, remaining "
          f"{guard.remaining(Q.TRANSFER)}; {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main((ROOT / sys.argv[1]).resolve(),
                          (ROOT / sys.argv[2]).resolve()))
