#!/usr/bin/env python3
"""T1 of ruling 029: where does the pinned evaluator first go invalid?

The arithmetic is not changed. Every expression below is copied from
``aart.raytracing_f.calculate_observables`` in its original order; the only
addition is that each intermediate is kept so the first invalid operation can
be named per point instead of guessed from the final NaN.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
import warnings
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from phrt.revision_v4_1 import domain as D                   # noqa: E402
from phrt.revision_v4_1 import query as Q                    # noqa: E402

SPIN, INC, D_OBS = 0.5, 50.0, 1000.0

NO_INTERSECTION = "PHYSICAL_NO_ALLOWED_INTERSECTION"
PLUNGE = "PHYSICAL_LANDING_AT_OR_INSIDE_HORIZON"
RADIAL_NONFINITE = "NUMERICAL_SOURCE_RADIUS_NONFINITE"
ROOTS_NONFINITE = "NUMERICAL_RADIAL_ROOTS_NONFINITE"
ELLIPTIC_NONFINITE = "NUMERICAL_ELLIPTIC_ARGUMENT_NONFINITE"
ANGULAR_NONFINITE = "NUMERICAL_ANGULAR_INTEGRAL_NONFINITE"
HEALTHY = "HEALTHY"


def instrument(alpha, beta, mbar, theta_o=None, a=SPIN, distance=D_OBS):
    """calculate_observables, expression for expression, with the workings kept."""
    from aart.raytracing_f import (angular_integrals, angular_turning_points,
                                   conserved_quantities, delta_phi, delta_t,
                                   radial_integrals, radial_turning_points,
                                   source_radius2, source_radius3)
    from scipy.special import ellipkinc as ellipf
    theta_o = (INC * np.pi / 180.0) if theta_o is None else theta_o
    alpha = np.asarray(alpha, float)
    beta = np.asarray(beta, float)
    rec = {}
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        lam, eta = conserved_quantities(alpha, beta, theta_o, a)
        pm_o = np.sign(beta)
        r1, r2, r3, r4 = radial_turning_points(alpha, beta, lam, eta, a)
        mask2 = np.ones(r1.shape, dtype=bool)
        mask2[np.abs(r4.imag) > 1e-13] = False
        mask3 = np.invert(mask2)
        u_p, u_m, theta_p, theta_m = angular_turning_points(alpha, beta, lam,
                                                            eta, a)
        G_theta, G_phi, G_t = angular_integrals(mbar, beta, u_p, u_m, theta_p,
                                                theta_m, pm_o, theta_o, a)
        r31, r32, r41, r42 = r3 - r1, r3 - r2, r4 - r1, r4 - r2
        k = r32 * r41 / r31 / r42
        taumax = np.zeros(alpha.shape)
        arg = np.arcsin(np.sqrt(r31[mask2] / r41[mask2])).real
        Jmax = 2 / np.sqrt(r31[mask2] * r42[mask2]) * ellipf(arg,
                                                             k[mask2].real)
        taumax[mask2] = Jmax.real
        r_sign = np.ones(r1.shape)
        s0 = np.ones(taumax[mask2].shape)
        s0[G_theta[mask2] > taumax[mask2]] = -1
        r_sign[mask2] = s0
        rs2 = source_radius2(distance, r1[mask2], r2[mask2], r3[mask2],
                             r4[mask2], G_theta[mask2])
        rs3 = source_radius3(distance, r1[mask3], r2[mask3], r3[mask3],
                             r4[mask3], G_theta[mask3])
        raw = np.zeros(alpha.shape)
        raw[mask2] = rs2.real
        raw[mask3] = rs3.real
        raw_nonfinite = np.zeros(alpha.shape, bool)
        raw_nonfinite[mask2] = ~np.isfinite(rs2.real)
        raw_nonfinite[mask3] = ~np.isfinite(rs3.real)
        rs = np.nan_to_num(raw.copy())
        r_p = 1 + np.sqrt(1 - a ** 2)
        clamped = rs <= r_p
        rs[clamped] = r_p
        I_r, I_phi, I_t = radial_integrals(rs, distance, r1, r2, r3, r4, a,
                                           beta, mask2, mask3, lam, eta,
                                           r_sign)
        dt = delta_t(I_t, G_t, a)
        dphi = delta_phi(I_phi, G_phi, lam)
    rec.update({
        "lam": lam, "eta": eta, "roots_finite": np.isfinite(
            np.stack([r1.real, r2.real, r3.real, r4.real])).all(0),
        "r4_imag": np.abs(r4.imag), "turning_branch": mask2,
        "k_finite": np.isfinite(k.real), "arcsin_arg_finite": np.ones(
            alpha.shape, bool), "taumax": taumax,
        "G_theta_finite": np.isfinite(G_theta),
        "raw_source_radius": raw, "raw_nonfinite": raw_nonfinite,
        "clamped_to_horizon": clamped, "r_p": r_p,
        "delta_t_finite": np.isfinite(dt), "delta_phi_finite": np.isfinite(dphi),
        "warnings": sorted({str(w.message)[:120] for w in caught}),
    })
    rec["arcsin_arg_finite"][mask2] = np.isfinite(arg)
    # the emitted NaN: exactly the library's own final mask
    rec["output_is_nan"] = clamped
    return rec


def classify(rec):
    """The FIRST operation that is invalid, per point."""
    n = rec["raw_source_radius"].size
    out = np.full(n, HEALTHY, dtype=object)
    bad = rec["output_is_nan"]
    out[bad & ~rec["roots_finite"]] = ROOTS_NONFINITE
    rest = bad & rec["roots_finite"]
    out[rest & ~rec["arcsin_arg_finite"]] = ELLIPTIC_NONFINITE
    rest = rest & rec["arcsin_arg_finite"]
    out[rest & ~rec["G_theta_finite"]] = ANGULAR_NONFINITE
    rest = rest & rec["G_theta_finite"]
    out[rest & rec["raw_nonfinite"]] = RADIAL_NONFINITE
    rest = rest & ~rec["raw_nonfinite"]
    # a finite radius that the library itself clamps: a physical landing at
    # or inside the horizon, which is not a solver failure at all
    out[rest] = PLUNGE
    return out


def main(out: Path, freeze: Path, t0: Path) -> int:
    t_start = time.time()
    out.mkdir(parents=True, exist_ok=False)
    guard = Q.Guard(freeze, ledger_path=out / "ATTEMPT_LEDGER_029.json")
    census = json.loads((t0 / "TRANSFER_FAILURE_CENSUS_029.json").read_text())
    rows, arrays = [], {}
    for key, coh in census["cohorts"].items():
        n = int(key[1:])
        for tag in ("failure", "control"):
            a = np.array(coh[f"{tag}_alpha"], float)
            b = np.array(coh[f"{tag}_beta"], float)
            tok = guard.reserve(Q.TRANSFER, a.size,
                                f"instrumented_{tag}_n{n}")
            try:
                rec = instrument(a, b, n)
            except BaseException as exc:
                guard.abort(tok, f"{type(exc).__name__}: {exc}")
                raise
            guard.complete(tok, a.size, int(rec["output_is_nan"].sum()))
            lab = classify(rec)
            u, c = np.unique(lab, return_counts=True)
            rows.append({
                "order": n, "cohort": tag, "n": int(a.size),
                "emitted_nan": int(rec["output_is_nan"].sum()),
                "first_invalid_primitive": dict(zip(u.tolist(), c.tolist())),
                "raw_radius_nonfinite": int(rec["raw_nonfinite"].sum()),
                "roots_nonfinite": int((~rec["roots_finite"]).sum()),
                "elliptic_arg_nonfinite":
                    int((~rec["arcsin_arg_finite"]).sum()),
                "angular_integral_nonfinite":
                    int((~rec["G_theta_finite"]).sum()),
                "turning_branch_mask2": int(rec["turning_branch"].sum()),
                "raw_radius_range_where_clamped": [
                    float(np.nanmin(rec["raw_source_radius"]
                                    [rec["clamped_to_horizon"]]))
                    if rec["clamped_to_horizon"].any() else None,
                    float(np.nanmax(rec["raw_source_radius"]
                                    [rec["clamped_to_horizon"]]))
                    if rec["clamped_to_horizon"].any() else None],
                "horizon_r_p": rec["r_p"],
                "warnings": rec["warnings"]})
            arrays[f"n{n}_{tag}"] = {
                "alpha": a.tolist(), "beta": b.tolist(),
                "raw_source_radius": rec["raw_source_radius"].tolist(),
                "raw_nonfinite": rec["raw_nonfinite"].tolist(),
                "clamped": rec["clamped_to_horizon"].tolist(),
                "turning_branch": rec["turning_branch"].tolist(),
                "first_invalid": lab.tolist()}
            print(f"  n{n} {tag}: {int(rec['output_is_nan'].sum())}/{a.size} "
                  f"emit NaN; first invalid "
                  + ", ".join(f"{x}={y}" for x, y in zip(u, c)), flush=True)

    rep = {
        "stage": "T1", "ruling": "PAPER_I_TRANSFER_AUDIT_RULING_029",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "commit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                 capture_output=True, text=True).stdout.strip(),
        "arithmetic_changed": False,
        "method": "calculate_observables reproduced expression for "
                  "expression, with every intermediate retained",
        "primitive_vocabulary": [NO_INTERSECTION, PLUNGE, RADIAL_NONFINITE,
                                 ROOTS_NONFINITE, ELLIPTIC_NONFINITE,
                                 ANGULAR_NONFINITE, HEALTHY],
        "cohorts": rows, "arrays": arrays,
        "guard": guard.snapshot(),
        "runtime_seconds": time.time() - t_start,
    }
    (out / "FIRST_INVALID_PRIMITIVE_029.json").write_text(
        json.dumps(rep, indent=2) + "\n")
    print(f"  transfer spent {guard.spent[Q.TRANSFER]}, remaining "
          f"{guard.remaining(Q.TRANSFER)}; {time.time() - t_start:.0f}s")
    return 0


if __name__ == "__main__":
    a = [(ROOT / x).resolve() for x in sys.argv[1:4]]
    raise SystemExit(main(*a))
