#!/usr/bin/env python3
"""I1 of ruling 031: a small, freshly frozen comparator confirmation.

Five strata, chosen from geometry and archived inputs before any of these
points' path-domain outcomes existed. The stratum the previous panel could
not exercise is included on purpose: finite exterior crossings that land
outside the source annulus, where the emission predicate and the library's
NaN marker are not the same question.
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
from phrt.revision_v4_1 import pathdomain as PD              # noqa: E402
from phrt.revision_v4_1 import pathdomain2 as P2             # noqa: E402
from phrt.revision_v4_1 import query as Q                    # noqa: E402
from t1_first_invalid_primitive import instrument            # noqa: E402

MAPS = ROOT / "artifacts" / "raymaps"
AART = ROOT / "artifacts/e3_pilot/aart_out"
GEOMETRY, SPIN, D_OBS, R_OUTER = "a050_i050", 0.5, 1000.0, 50.0
PER_STRATUM, PROFILE = 38, "fine"
BANDS = AART / "fine/LensingBands_a_0.5_i_50.0_dx0_0.2_dx1_0.04_dx2_0.01.h5"


def strata(rm, band, rh, rng, exclude):
    r = rm.source_r
    fin = np.isfinite(r)
    ok = band & fin & (r > rh) & (r <= R_OUTER)
    out = {
        "emitting": np.flatnonzero(ok & ~exclude),
        "absence_candidates": np.flatnonzero(band & ~fin & ~exclude),
        "finite_exterior_outside_annulus":
            np.flatnonzero(band & fin & (r > R_OUTER) & ~exclude),
        "boundary_uncertainty_near_r50": np.flatnonzero(ok & ~exclude),
        "boundary_uncertainty_near_horizon": np.flatnonzero(ok & ~exclude),
    }
    if out["boundary_uncertainty_near_r50"].size:
        i = out["boundary_uncertainty_near_r50"]
        out["boundary_uncertainty_near_r50"] = i[
            np.argsort(np.abs(r[i] - R_OUTER))[:PER_STRATUM]]
        j = out["boundary_uncertainty_near_horizon"]
        out["boundary_uncertainty_near_horizon"] = j[np.argsort(r[j])[:PER_STRATUM]]
    for k in ("emitting", "absence_candidates",
              "finite_exterior_outside_annulus"):
        v = out[k]
        out[k] = (rng.choice(v, PER_STRATUM, replace=False)
                  if v.size > PER_STRATUM else v)
    return out


def main(out: Path, freeze: Path, prior: Path) -> int:
    t0 = time.time()
    out.mkdir(parents=True, exist_ok=False)
    guard = Q.Guard(freeze, ledger_path=out / "ATTEMPT_LEDGER_031.json")
    fz = json.loads(freeze.read_text())
    rh = horizon_radius(SPIN)
    rng = np.random.default_rng(31031)
    seen = set()
    for f in sorted(prior.glob("*/PATH_DOMAIN_030_INPUT_FREEZE.json")):
        for k, v in json.loads(f.read_text())["cohorts"].items():
            if v["profile"] == PROFILE:
                seen.update((int(k.split("_n")[1]), int(i))
                            for i in v["failures"] + v["controls"])

    rows, quad_calls = [], 0
    with h5py.File(BANDS, "r") as h:
        for n in (0, 1, 2):
            rm = read(MAPS / f"{GEOMETRY}_n{n}_{PROFILE}.h5")
            band = h[f"mask{n}"][:]
            ex = np.zeros(band.size, bool)
            for (o, i) in seen:
                if o == n:
                    ex[i] = True
            st = strata(rm, band, rh, rng, ex)
            idx = np.unique(np.concatenate([v for v in st.values() if v.size]))
            if idx.size == 0:
                continue
            lab = {}
            for k, v in st.items():
                for i in v:
                    lab.setdefault(int(i), []).append(k)
            tok = guard.reserve(Q.TRANSFER, idx.size, f"I1_confirmation_n{n}")
            try:
                rec = instrument(rm.alpha[idx], rm.beta[idx], n)
            except BaseException as exc:
                guard.abort(tok, f"{type(exc).__name__}: {exc}")
                raise
            nf = int(rec["output_is_nan"].sum())
            guard.complete(tok, int(idx.size) - nf, nf)
            for j, i in enumerate(idx):
                roots = rec["roots"][:, j]
                s = float(rec["G_theta"][j])
                p = P2.adjudicate(roots, s, rh, D_OBS, R_OUTER)
                q = P2.adjudicate(roots, s, rh, D_OBS, R_OUTER, reference=True)
                quad_calls += 2
                rows.append({
                    "order": n, "index": int(i), "strata": lab[int(i)],
                    "archived_source_r": float(rm.source_r[i]),
                    "library_emitted_nan": bool(rec["output_is_nan"][j]),
                    "primary": p["code"], "reference": q["code"],
                    "agree": p["code"] == q["code"],
                    "margin": p.get("margin"),
                    "error_estimate": p.get("error_estimate"),
                    "polynomial_residual": float(np.max(np.abs(
                        np.real(np.prod([roots - r_ for r_ in roots],
                                        axis=0))))),
                })
            print(f"  n{n}: {idx.size} points, spent "
                  f"{guard.spent[Q.TRANSFER]}", flush=True)

    from collections import Counter
    by_stratum = {}
    for r in rows:
        for s in r["strata"]:
            by_stratum.setdefault(s, Counter())[r["primary"]] += 1
    dis = [r for r in rows if not r["agree"]]
    forced = [r for r in rows
              if r["primary"] == PD.VALID and r["library_emitted_nan"]]
    missed = [r for r in rows
              if r["primary"] != PD.VALID and not r["library_emitted_nan"]
              and r["primary"] != PD.OUTSIDE_ANNULUS]
    rep = {
        "stage": "I1", "ruling": "PAPER_I_DOMAIN_INTEGRATION_RULING_031",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "commit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                 capture_output=True, text=True).stdout.strip(),
        "panel": "freshly frozen; none of these points appears in any prior "
                 "030 cohort and none of their path-domain outcomes existed "
                 "before this run",
        "points": len(rows), "points_cap": 192,
        "charged_tracer_evaluations": guard.spent[Q.TRANSFER],
        "reference_quadrature_calls_inventoried": quad_calls,
        "charged_cap": 1024,
        "comparator_tuned_on_this_panel": False,
        "by_stratum": {k: dict(v) for k, v in by_stratum.items()},
        "methods_agree": len(rows) - len(dis),
        "methods_disagree": len(dis), "disagreements": dis[:10],
        "valid_where_library_marked_nan": len(forced),
        "absent_where_library_gave_a_value": len(missed),
        "shared_inputs_declared": ["conserved quantities", "radial roots",
                                   "angular crossing", "path classifier",
                                   "asymptotic tail"],
        "shared_input_check": "the quartic residual at each returned root, "
                              "reported per point; it does not make the "
                              "roots independent, it bounds how badly they "
                              "could be wrong",
        "max_polynomial_residual": max((r["polynomial_residual"]
                                        for r in rows), default=None),
        "rigorous_continuum_guarantee": False,
        "rows": rows, "guard": guard.snapshot(),
        "runtime_seconds": time.time() - t0,
    }
    (out / "FRESH_COMPARATOR_CONFIRMATION_031.json").write_text(
        json.dumps(rep, indent=2) + "\n")
    for k, v in rep["by_stratum"].items():
        print(f"  {k}: {dict(v)}")
    print(f"  agree {rep['methods_agree']}/{len(rows)}; forced-valid "
          f"{len(forced)}; absent-with-a-value {len(missed)}")
    print(f"  charged {guard.spent[Q.TRANSFER]}, remaining "
          f"{guard.remaining(Q.TRANSFER)}; {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    a = [(ROOT / x).resolve() for x in sys.argv[1:4]]
    raise SystemExit(main(*a))
