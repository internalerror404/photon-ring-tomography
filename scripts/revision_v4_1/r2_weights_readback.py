#!/usr/bin/env python3
"""The permitted R2 readback: effective per-row quadrature ratios only.

Ruling 027 allows an inventory of the weights the sampler actually produces,
and nothing else: no operator is built, no Fisher matrix is formed, no SVD is
run and no target column is touched. The point is narrow. An order's
total-area ratio does not bound every row it produces, because
``stratified_subsample`` builds weights from individual stratum areas and only
then rescales to the order total, so a correction that is not uniform within
an order redistributes weight between strata. This measures that
redistribution directly and turns the hypothetical interval into a bounded
one, or shows that it cannot be.
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

from phrt.geometry.raymap import RayMap, read                # noqa: E402
from phrt.geometry.sampling import common_count, stratified_subsample  # noqa: E402
from phrt.revision_v4_1 import measure as M                  # noqa: E402

MAPS = ROOT / "artifacts" / "raymaps"
REV = ROOT / "artifacts" / "revisions" / "mahakal_v4_1"
R2 = REV / "R2REPLAY_20260906T144528Z_b873908"
GEOMETRY, ORDERS = "a050_i050", (0, 1, 2)
RHO = 1.0


def with_area(rm: RayMap, area: np.ndarray) -> RayMap:
    """The same map with a different quadrature weight, in memory only."""
    d = {f: getattr(rm, f) for f in rm.__dataclass_fields__}
    d["pixel_area"] = area
    return RayMap(**d)


def draw(area_of):
    freeze = json.loads((ROOT / "artifacts/configs/R1_MAIN_FREEZE.json"
                         ).read_text())["observation"]
    rng = np.random.default_rng(int(freeze["subsample_seed"]))
    maps = [read(MAPS / f"{GEOMETRY}_n{n}_core.h5") for n in ORDERS]
    subs = [stratified_subsample(area_of(m), int(freeze["rays_per_order"]),
                                 rng) for m in maps]
    return common_count(subs, rng)


def main(out: Path) -> int:
    t0 = time.time()
    legacy = draw(lambda m: m)
    corrected = draw(lambda m: with_area(
        m, M.build_ray_cells(m.alpha, m.beta, M.NODAL_DUAL_CLIPPED).area))

    per, all_r = [], []
    for n, (a, b) in enumerate(zip(legacy, corrected)):
        if a.n_rays != b.n_rays:
            raise SystemExit(f"order {n}: retained counts differ, "
                             f"{a.n_rays} vs {b.n_rays}; the comparison is "
                             "only valid on identical retained indices")
        same = bool(np.array_equal(a.source_r, b.source_r)
                    and np.array_equal(a.delay, b.delay)
                    and np.array_equal(a.redshift, b.redshift))
        r = b.quadrature / a.quadrature
        all_r.append(r)
        per.append({"order": n, "n_rays": int(a.n_rays),
                    "identical_retained_rays": same,
                    "legacy_total": float(a.quadrature.sum()),
                    "corrected_total": float(b.quadrature.sum()),
                    "total_ratio": float(b.quadrature.sum()
                                         / a.quadrature.sum()),
                    "row_ratio_min": float(r.min()),
                    "row_ratio_max": float(r.max()),
                    "row_ratio_spread_within_order":
                        float(r.max() / r.min() - 1)})
    if not all(p["identical_retained_rays"] for p in per):
        raise SystemExit("the two draws did not retain the same rays")

    r = np.concatenate(all_r)
    lo, hi = float(r.min()), float(r.max())
    modes = json.loads((R2 / "mode_export.json").read_text())["RESOLVED_PHYSICAL"]
    sv = np.array(modes["singular_values"], float)
    iv = [[float(s * np.sqrt(lo)), float(s * np.sqrt(hi))] for s in sv]
    above = [i for i, (a, b) in enumerate(iv) if a > RHO]
    straddle = [i for i, (a, b) in enumerate(iv) if a <= RHO <= b]
    rows = [x.split(",") for x in
            (R2 / "reference_geometry_information.csv").read_text()
            .strip().splitlines()[1:]]
    tr = {float(x[5]) for x in rows if x[0] == "RESOLVED_PHYSICAL"}.pop()

    rep = {
        "stage": "R2_WEIGHTS_READBACK", "ruling": "PAPER_I_FRACTIONAL_"
        "COVERAGE_RULING_027", "permitted_scope":
            "effective quadrature ratio inventory only; no operator, no "
            "Fisher matrix, no SVD, no target column",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "commit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                 capture_output=True, text=True).stdout.strip(),
        "measure_compared": ["LEGACY_NOMINAL_DX_SQUARED_SQUARE",
                             "NODAL_DUAL_CLIPPED_TO_DECLARED_DOMAIN"],
        "same_seed_same_retained_indices": True,
        "normalisations_verified": "stratified_subsample rescale to the order "
                                   "total, then common_count trimming, both "
                                   "applied identically to the two draws",
        "per_order": per,
        "row_ratio_min_over_all_rows": lo,
        "row_ratio_max_over_all_rows": hi,
        "per_order_totals_would_have_given": [p["total_ratio"] for p in per],
        "row_bound_is_wider_than_the_total_bound": bool(
            lo < min(p["total_ratio"] for p in per) - 1e-15
            or hi > max(p["total_ratio"] for p in per) + 1e-15),
        "bound": "r_min * F_cond <= F_cond_new <= r_max * F_cond, valid after "
                 "profiling",
        "archived_conditional_singular_values": sv.tolist(),
        "certified_singular_value_intervals": iv,
        "directions_certainly_above_rho": above,
        "n_directions_certainly_above_rho": len(above),
        "directions_straddling_rho": straddle,
        "conditional_trace_archived": tr,
        "conditional_trace_interval": [tr * lo, tr * hi],
        "status": "ROW_BOUND_CERTIFIED" if not straddle
                  else "ROW_BOUND_DOES_NOT_SEPARATE_RHO",
        "legacy_R2_acceptance": "preserved under its frozen legacy measure; "
                                "nothing here recomputes or replaces it",
        "runtime_seconds": time.time() - t0,
    }
    out.mkdir(parents=True, exist_ok=True)
    (out / "R2_WEIGHTS_READBACK_027.json").write_text(
        json.dumps(rep, indent=2) + "\n")
    for p in per:
        print(f"  order {p['order']}: rows {p['n_rays']}, total ratio "
              f"{p['total_ratio']:.9f}, row ratios "
              f"[{p['row_ratio_min']:.9f}, {p['row_ratio_max']:.9f}]")
    print(f"  all rows: [{lo:.9f}, {hi:.9f}]  wider than totals: "
          f"{rep['row_bound_is_wider_than_the_total_bound']}")
    for i, (a, b) in enumerate(iv, 1):
        print(f"  sigma{i}: [{a:.9f}, {b:.9f}]")
    print(f"  above rho {len(above)}, straddling {straddle}, status "
          f"{rep['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main((ROOT / sys.argv[1]).resolve()))
