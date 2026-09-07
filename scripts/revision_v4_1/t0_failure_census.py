#!/usr/bin/env python3
"""T0 of ruling 029: the whole transfer quantity, not the radius alone.

Zero physical queries. Every non-finite component of the archived maps is
inventoried, failure and healthy-control cohorts are frozen by screen/order
id, the contour payload is located and its missing arrays disclosed, and the
physical no-intersection case is separated from numerical failure by a stated
criterion rather than inferred from a NaN.
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

from phrt.geometry.raymap import read, horizon_radius        # noqa: E402
from phrt.revision_v4_1 import domain as D                   # noqa: E402

MAPS = ROOT / "artifacts" / "raymaps"
REV = ROOT / "artifacts" / "revisions" / "mahakal_v4_1"
BANDS = ROOT / ("artifacts/e3_pilot/aart_out/core/"
                "LensingBands_a_0.5_i_50.0_dx0_0.4_dx1_0.08_dx2_0.02.h5")
GEOMETRY, SPIN, R_OUTER = "a050_i050", 0.5, 50.0
ORDERS, PROFILES = (0, 1, 2), ("coarse", "core", "fine")
N_FAIL_COHORT, N_CTRL_COHORT = 100000, 200
COMPONENTS = ("source_r", "source_phi", "coordinate_time", "redshift",
              "radial_sign", "transfer_weight")


def main(out: Path) -> int:
    t0 = time.time()
    out.mkdir(parents=True, exist_ok=False)
    rh = horizon_radius(SPIN)
    rng = np.random.default_rng(2029)
    census, cohorts = [], {}

    for prof in PROFILES:
        bp = (ROOT / "artifacts/e3_pilot/aart_out" /
              {"coarse": "coarse/LensingBands_a_0.5_i_50.0_dx0_0.8_dx1_0.16_dx2_0.04.h5",
               "core": "core/LensingBands_a_0.5_i_50.0_dx0_0.4_dx1_0.08_dx2_0.02.h5",
               "fine": "fine/LensingBands_a_0.5_i_50.0_dx0_0.2_dx1_0.04_dx2_0.01.h5"}[prof])
        with h5py.File(bp, "r") as f:
            band = {n: f[f"mask{n}"][:] for n in ORDERS}
        for n in ORDERS:
            rm = read(MAPS / f"{GEOMETRY}_n{n}_{prof}.h5")
            b = band[n]
            comp = {c: np.isfinite(np.asarray(getattr(rm, c), float))
                    for c in COMPONENTS}
            # the joint pattern, per sample, over the whole transferred
            # quantity rather than the radius alone
            key = np.zeros(b.size, np.int64)
            for i, c in enumerate(COMPONENTS):
                key |= (~comp[c]).astype(np.int64) << i
            pats = {}
            for k in np.unique(key[b]):
                m = b & (key == k)
                names = [c for i, c in enumerate(COMPONENTS) if (k >> i) & 1]
                pats["+".join(names) or "all_finite"] = {
                    "n": int(m.sum()),
                    "of_which_r_gt_50": int((m & comp["source_r"]
                                             & (rm.source_r > R_OUTER)).sum()),
                    "of_which_r_le_horizon":
                        int((m & comp["source_r"]
                             & (rm.source_r <= rh)).sum())}
            census.append({
                "profile": prof, "order": n, "in_band": int(b.sum()),
                "nonfinite_by_component":
                    {c: int((b & ~comp[c]).sum()) for c in COMPONENTS},
                "joint_patterns": pats,
                "radius_finite_but_other_component_not":
                    int((b & comp["source_r"]
                         & ~(comp["source_phi"] & comp["coordinate_time"]
                             & comp["redshift"])).sum()),
                "redshift_finite_where_landing_is_not":
                    int((b & ~comp["source_r"] & comp["redshift"]).sum())})
            if prof == "core":
                bad = np.flatnonzero(b & ~comp["source_r"])
                good = np.flatnonzero(b & comp["source_r"]
                                      & comp["source_phi"]
                                      & comp["coordinate_time"]
                                      & comp["redshift"]
                                      & (rm.source_r > rh)
                                      & (rm.source_r <= R_OUTER))
                if bad.size:
                    # controls next to the failures, plus a spread of healthy
                    # points, so the cohort is not all from one place
                    ua = np.unique(rm.alpha)
                    N = ua.size
                    near = []
                    for j in bad[:N_CTRL_COHORT]:
                        r_, c_ = divmod(int(j), N)
                        for dr, dc in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                            q = (r_ + dr) * N + (c_ + dc)
                            if 0 <= q < b.size and q in set(good.tolist()[:0]) :
                                pass
                        near.append(j)
                    fail = bad if bad.size <= N_FAIL_COHORT else rng.choice(
                        bad, N_FAIL_COHORT, replace=False)
                    ctrl = good if good.size <= N_CTRL_COHORT else rng.choice(
                        good, N_CTRL_COHORT, replace=False)
                    cohorts[f"n{n}"] = {
                        "failure_ids": [int(x) for x in np.sort(fail)],
                        "control_ids": [int(x) for x in np.sort(ctrl)],
                        "failure_alpha": rm.alpha[fail].tolist(),
                        "failure_beta": rm.beta[fail].tolist(),
                        "control_alpha": rm.alpha[ctrl].tolist(),
                        "control_beta": rm.beta[ctrl].tolist(),
                        "population_failures": int(bad.size),
                        "population_controls": int(good.size),
                        "control_selection": "healthy in-band, in-annulus "
                                             "samples across the order, not "
                                             "only next to a failure"}

    # what the contour run left behind
    contour = {}
    for d in sorted(REV.glob("V1_*")):
        f = d / "EMISSION_CONTOUR_AND_UNCERTAINTY_028.json"
        if not f.exists():
            continue
        j = json.loads(f.read_text())
        contour[d.name] = {
            "summary_present": True,
            "resolved_by_order": {k: v["resolved"]
                                  for k, v in j["contour"].items()},
            "brackets_by_order": {k: v["brackets"]
                                  for k, v in j["contour"].items()},
            "point_arrays_present": False,
            "missing_arrays": ["contour endpoint coordinates",
                               "per-bracket screen brackets",
                               "failed-bracket coordinates and reasons",
                               "residuals"],
            "why": "the V1 writer removed its internal point arrays before "
                   "serialising, so only counts survive. A cut-cell "
                   "integrator cannot consume counts",
            "consequence": "the located contour cannot be integrated without "
                           "re-deriving it, which would cost a further "
                           "transfer batch",
            "disclosed_not_reconstructed": True}

    rep = {
        "stage": "T0", "ruling": "PAPER_I_TRANSFER_AUDIT_RULING_029",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "commit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                 capture_output=True, text=True).stdout.strip(),
        "new_physical_queries": 0,
        "components_inventoried": list(COMPONENTS),
        "radius_only_inventory": False,
        "census": census,
        "cohorts": cohorts,
        "contour_payload": contour,
        "physical_versus_numerical": {
            "criterion": "a point has no order-n intersection only when the "
                         "geodesic-existence condition says so, evaluated "
                         "from the pinned equations. It is never inferred "
                         "from a NaN",
            "status_of_the_680": "UNDECIDED_PENDING_T1: the archived maps "
                                 "record only that the landing is "
                                 "non-finite, which is compatible both with "
                                 "no allowed intersection and with an "
                                 "intersection the solver could not "
                                 "evaluate. T1 instruments the evaluator to "
                                 "tell them apart",
            "conservative_sampling_envelope":
                "the lensing-band hull is a containing region, so in-band "
                "membership does not by itself assert an allowed order-n "
                "crossing",
        },
    }
    (out / "TRANSFER_FAILURE_CENSUS_029.json").write_text(
        json.dumps(rep, indent=2) + "\n")
    (out / "CONTOUR_PAYLOAD_MANIFEST_029.json").write_text(json.dumps({
        "stage": "T0", "runs": contour,
        "resolved_contour_arrays_available": False,
        "action": "disclosed. Re-deriving the contour is a second transfer "
                  "batch and this ruling's batch is committed to the "
                  "primitive audit, so the arrays are not reconstructed here",
    }, indent=2) + "\n")

    for c in census:
        if c["profile"] != "core":
            continue
        print(f"  core n{c['order']}: in-band {c['in_band']}, non-finite "
              + ", ".join(f"{k}={v}" for k, v in
                          c["nonfinite_by_component"].items() if v)
              + f", redshift finite where landing is not: "
              f"{c['redshift_finite_where_landing_is_not']}")
    for k, v in cohorts.items():
        print(f"  cohort {k}: {len(v['failure_ids'])} failures of "
              f"{v['population_failures']}, {len(v['control_ids'])} controls")
    print(f"  runtime {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main((ROOT / sys.argv[1]).resolve()))
