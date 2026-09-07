#!/usr/bin/env python3
"""D1 and D2 of ruling 030: adjudicate the domain, then validate it apart.

D1 asks, for every point in the development cohort, whether the requested
exterior equatorial crossing exists on that ray's own radial path and whether
it falls in the emitting annulus. D2 repeats the question on precommitted
holdout points with an independent quadrature, and counts invented and missed
events rather than only comparing radii.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts" / "revision_v4_1"))

from phrt.geometry.raymap import read, horizon_radius        # noqa: E402
from phrt.revision_v4_1 import pathdomain as PD              # noqa: E402
from phrt.revision_v4_1 import query as Q                    # noqa: E402
from t1_first_invalid_primitive import instrument            # noqa: E402

MAPS = ROOT / "artifacts" / "raymaps"
GEOMETRY, SPIN, D_OBS, R_OUTER = "a050_i050", 0.5, 1000.0, 50.0


def gauss_J(a, b, roots, turn=None, n=400):
    """The same integral by fixed-order Gauss-Legendre: an independent method."""
    if b <= a:
        return 0.0
    x, w = np.polynomial.legendre.leggauss(n)
    if turn is not None and abs(a - turn) < 1e-12:
        U = np.sqrt(b - turn)
        u = 0.5 * U * (x + 1)
        ww = 0.5 * U * w
        r = turn + u * u
        q = PD.radial_potential(r, roots) / (r - turn)
        return float(np.sum(ww * 2.0 / np.sqrt(np.where(q > 0, q, np.nan))))
    u = 0.5 * (b - a) * (x + 1) + a
    ww = 0.5 * (b - a) * w
    q = PD.radial_potential(u, roots)
    return float(np.sum(ww / np.sqrt(np.where(q > 0, q, np.nan))))


def independent_code(roots, s_n, rh, r_obs):
    """The same predicate, every integral by Gauss-Legendre instead of quad."""
    kind, turn = PD.classify_path(roots, rh, r_obs)
    if not np.isfinite(s_n) or kind == PD.INSIDE_OBSERVER:
        return PD.UNRESOLVED
    if kind == PD.CAPTURE:
        sH = gauss_J(rh, r_obs, roots)
        s50 = gauss_J(R_OUTER, r_obs, roots)
        if s_n >= sH:
            return PD.NO_CROSSING_CAPTURE
        return PD.OUTSIDE_ANNULUS if s_n < s50 else PD.VALID
    Jo = gauss_J(turn, r_obs, roots, turn=turn)
    if turn >= R_OUTER:
        return PD.NO_ANNULUS_ON_PATH
    J50 = gauss_J(turn, R_OUTER, roots, turn=turn)
    Jinf = gauss_J(turn, 1e7, roots, turn=turn) + PD._tail(1e7, roots)
    if s_n > Jo + Jinf:
        return PD.NO_CROSSING_ESCAPE
    return PD.VALID if Jo - J50 < s_n < Jo + J50 else PD.OUTSIDE_ANNULUS


def run_cohort(key, spec, guard, rh, why):
    n = int(key.split("_n")[1])
    rm = read(MAPS / f"{GEOMETRY}_n{n}_{spec['profile']}.h5")
    idx = np.array(spec["failures"] + spec["controls"], dtype=int)
    if idx.size == 0:
        return None
    a, b = rm.alpha[idx], rm.beta[idx]
    tok = guard.reserve(Q.TRANSFER, idx.size, why)
    try:
        rec = instrument(a, b, n)
    except BaseException as exc:
        guard.abort(tok, f"{type(exc).__name__}: {exc}")
        raise
    nf = int(rec["output_is_nan"].sum())
    guard.complete(tok, idx.size - nf, nf)
    was_failure = np.zeros(idx.size, bool)
    was_failure[:len(spec["failures"])] = True
    rows = []
    for j in range(idx.size):
        roots = rec["roots"][:, j]
        d = PD.adjudicate(roots, float(rec["G_theta"][j]), rh, D_OBS,
                          R_OUTER)
        rows.append({**d, "order": n, "index": int(idx[j]),
                     "alpha": float(a[j]), "beta": float(b[j]),
                     "archived_failure": bool(was_failure[j]),
                     "library_emitted_nan": bool(rec["output_is_nan"][j]),
                     "raw_source_radius": float(rec["raw_source_radius"][j]),
                     "independent_code": independent_code(
                         roots, float(rec["G_theta"][j]), rh, D_OBS)})
    return rows


def summarise(rows, pick):
    sel = [r for r in rows if pick(r)]
    u = {}
    for r in sel:
        u[r["code"]] = u.get(r["code"], 0) + 1
    return {"n": len(sel), "by_code": u,
            "methods_agree": sum(1 for r in sel
                                 if r["code"] == r["independent_code"]),
            "methods_disagree": [
                {"order": r["order"], "index": r["index"],
                 "primary": r["code"], "independent": r["independent_code"]}
                for r in sel if r["code"] != r["independent_code"]][:20]}


def main(out: Path, freeze: Path) -> int:
    t0 = time.time()
    out.mkdir(parents=True, exist_ok=False)
    guard = Q.Guard(freeze, ledger_path=out / "ATTEMPT_LEDGER_030.json")
    fz = json.loads(freeze.read_text())
    rh = horizon_radius(SPIN)

    dev, hold = [], []
    for key, spec in fz["cohorts"].items():
        rows = run_cohort(key, spec, guard, rh,
                          f"D1_{key}" if key.startswith("dev")
                          else f"D2_{key}")
        if rows is None:
            continue
        (dev if key.startswith("dev") else hold).extend(rows)
        print(f"  {key}: {len(rows)} points, spent "
              f"{guard.spent[Q.TRANSFER]}", flush=True)

    d1 = {"all": summarise(dev, lambda r: True),
          "archived_failures": summarise(dev, lambda r: r["archived_failure"]),
          "healthy_controls": summarise(dev, lambda r: not r["archived_failure"])}
    d2 = {"all": summarise(hold, lambda r: True),
          "archived_failures": summarise(hold, lambda r: r["archived_failure"]),
          "healthy_controls": summarise(hold, lambda r: not r["archived_failure"])}

    # invented and missed events on the holdout, against the library's own mask
    inv = [r for r in hold if r["code"] == PD.VALID and r["library_emitted_nan"]]
    miss = [r for r in hold if r["code"] != PD.VALID
            and not r["library_emitted_nan"]]
    np.savez_compressed(
        out / "PER_POINT_PATH_DOMAIN_ADJUDICATION_030.npz",
        dev=np.array([json.dumps(r) for r in dev]),
        holdout=np.array([json.dumps(r) for r in hold]))
    rep = {
        "stage": "D1_D2", "ruling": "PAPER_I_PATH_DOMAIN_RULING_030",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "commit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                 capture_output=True, text=True).stdout.strip(),
        "status_codes": list(PD.CODES),
        "expression_switched_or_sign_forced": False,
        "development": d1, "holdout": d2,
        "holdout_invented_events": len(inv),
        "holdout_missed_events": len(miss),
        "invented_examples": inv[:10], "missed_examples": miss[:10],
        "independent_method": "fixed-order Gauss-Legendre after the same "
                              "turning-point substitution, replacing "
                              "adaptive quadrature in every integral",
        "guard": guard.snapshot(),
        "runtime_seconds": time.time() - t0,
    }
    (out / "INDEPENDENT_DOMAIN_HOLDOUT_030.json").write_text(
        json.dumps(rep, indent=2) + "\n")
    print(f"  development: {d1['archived_failures']['by_code']}")
    print(f"  controls:    {d1['healthy_controls']['by_code']}")
    print(f"  holdout:     {d2['all']['by_code']}")
    print(f"  invented {len(inv)}, missed {len(miss)}; methods agree "
          f"{d1['all']['methods_agree']}/{d1['all']['n']} dev, "
          f"{d2['all']['methods_agree']}/{d2['all']['n']} holdout")
    print(f"  transfer spent {guard.spent[Q.TRANSFER]}, remaining "
          f"{guard.remaining(Q.TRANSFER)}; {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    a = [(ROOT / x).resolve() for x in sys.argv[1:3]]
    raise SystemExit(main(*a))
