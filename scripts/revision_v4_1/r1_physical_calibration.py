#!/usr/bin/env python3
"""Route the real E3C operator through the versioned calibration.

Ledger C02 acceptance: a repair that only touches a helper is not a repair.
This rebuilds the archived operator -- the same ray maps, the same sampler
seeds, the same PhysicalBasis and the same PhysicalOperator constructor -- and
calibrates it through phrt.revision_v4_1.calibration instead of the inline
``sqrt(mean(clean**2))``.

Two things are then true or the run fails: LEGACY_REPLAY reproduces the
archived per-geometry s_ref to floating point, and COMMON_REFERENCE_COUNT
differs from it exactly by sqrt(m_current / m_reference) and by nothing else.
No new geodesics, no new truths, no estimator.
"""
from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from phrt.numerics import pin

pin()

import numpy as np  # noqa: E402

from phrt.geometry.raymap import read  # noqa: E402
from phrt.geometry.sampling import common_count, stratified_subsample  # noqa: E402
from phrt.operators.physical import PhysicalOperator  # noqa: E402
from phrt.revision_v4_1.calibration import (COMMON_REFERENCE_COUNT,  # noqa: E402
                                            E3C_REFERENCE_ROWS, LEGACY_REPLAY,
                                            calibrate, legacy_s_ref)
from phrt.sources.physical_basis import PhysicalBasis  # noqa: E402

FREEZE = ROOT / "artifacts" / "configs" / "E3C_OPERATOR_GRID_FREEZE.json"
MAPS = ROOT / "artifacts" / "raymaps"
E3C = ROOT / "artifacts" / "e3c"


def unit_source(basis: PhysicalBasis) -> np.ndarray:
    """j = 1 in the registered basis, exactly as the archived runner builds it."""
    u = np.zeros(basis.dimension)
    for a in range(basis.n_radial):
        u[(a * basis.n_azimuthal + 0) * basis.n_temporal + 0] = 1.0
    return u


def rebuild(geometry: str, fz: dict) -> tuple[PhysicalOperator, np.ndarray, dict]:
    """The archived direct arm for one geometry, from the frozen maps."""
    obs = fz["observation"]
    t_obs = np.asarray(obs["observer_times_M"], dtype=float)
    rng = np.random.default_rng(int(obs["subsample_seed"]))
    raw = [read(MAPS / f"{geometry}_n{n}_{fz['profile']}.h5")
           for n in fz["orders"]]
    base = common_count(
        [stratified_subsample(rm, int(obs["rays_per_order"]), rng)
         for rm in raw], rng)
    stored = json.loads((E3C / f"{geometry}.json").read_text())
    basis = PhysicalBasis(float(stored["r_inner"]), float(stored["r_outer"]),
                          float(stored["t_min"]), float(stored["t_max"]))
    # DIRECT_PHYSICAL, exactly as build_arms defines it: order 0 alone. The
    # archived s_ref is the direct arm's RMS whitened response, not the
    # resolved stack's.
    op = PhysicalOperator(orders=[base[0]], observer_times=t_obs,
                          design=basis.design, dimension=basis.dimension)
    return op, unit_source(basis), stored


def main(run_dir: Path, geometries: list[str]) -> int:
    fz = json.loads(FREEZE.read_text())
    rows, failures = [], []
    for g in geometries:
        op, unit, stored = rebuild(g, fz)
        clean = op.matvec(unit)
        m = int(clean.size)
        legacy = calibrate(clean, float(stored["reference_snr"]),
                           mode=LEGACY_REPLAY, grid_identity=g)
        common = calibrate(clean, float(stored["reference_snr"]),
                           mode=COMMON_REFERENCE_COUNT,
                           m_reference=E3C_REFERENCE_ROWS, grid_identity=g)
        archived = float(stored["s_ref"])
        replay_rel = abs(legacy.s_ref / archived - 1.0)
        # s_ref(common)/s_ref(legacy) = sqrt(E/m*) / sqrt(E/m) = sqrt(m/m*)
        predicted = math.sqrt(m / E3C_REFERENCE_ROWS)
        ratio_rel = abs((common.s_ref / legacy.s_ref) / predicted - 1.0)
        ok = replay_rel < 1e-12 and ratio_rel < 1e-12
        if not ok:
            failures.append(g)
        rows.append({
            "geometry": g, "direct_rows": m,
            "rays_per_order": int(stored["rays_per_order"]),
            "archived_s_ref": archived,
            "legacy_replay_s_ref": legacy.s_ref,
            "legacy_replay_relative_error": replay_rel,
            "reproduces_archived_bitwise_to_1e_12": replay_rel < 1e-12,
            "legacy_matches_inline_formula": abs(
                legacy.s_ref - legacy_s_ref(clean)) < 1e-15,
            "common_count_s_ref": common.s_ref,
            "m_reference": E3C_REFERENCE_ROWS,
            "sigma_legacy": legacy.sigma, "sigma_common": common.sigma,
            "information_factor_common_over_legacy":
                (legacy.sigma / common.sigma) ** 2,
            "predicted_information_factor": E3C_REFERENCE_ROWS / m,
            "ratio_check_relative_error": ratio_rel,
            "pass": ok,
        })
        print(f"  {g}: rows={m} archived={archived:.12f} "
              f"replay={legacy.s_ref:.12f} rel={replay_rel:.2e} "
              f"F_common/F_legacy={(legacy.sigma / common.sigma) ** 2:.12f} "
              f"{'OK' if ok else 'FAIL'}")

    doc = {
        "schema": "phrt-physical-calibration-replay/1",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "ledger_item": "C02",
        "what_this_proves": "the versioned calibration is wired into the same "
                            "PhysicalOperator the archived runner builds, not "
                            "into a helper: LEGACY_REPLAY reproduces each "
                            "archived s_ref and COMMON_REFERENCE_COUNT "
                            "differs from it by the row-count ratio alone",
        "e3c_reference_rows": E3C_REFERENCE_ROWS,
        "n_geometries": len(rows), "n_failures": len(failures),
        "failures": failures,
        "geometries": rows,
    }
    out = run_dir / "physical_calibration_replay.json"
    out.write_text(json.dumps(doc, indent=2) + "\n")
    print(f"wrote {out.relative_to(ROOT)}")
    return 1 if failures else 0


if __name__ == "__main__":
    args = sys.argv[1:]
    run = (ROOT / args[0]).resolve()
    geos = args[1:] or ["a000_i020", "a050_i050"]
    raise SystemExit(main(run, geos))
