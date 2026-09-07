#!/usr/bin/env python3
"""V0 of ruling 028: corrections, point-vs-fragment status, and the freeze.

Zero new physical queries. Everything here reads cached archives, records the
interpretation corrections the ruling requires, separates point status from
fragment certification, diagnoses which pinned primitive failed where one did,
and writes the input snapshot that must be committed before V1 or G1 may
issue a single physical call.
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
from phrt.revision_v4_1 import fractional as FR              # noqa: E402
from phrt.revision_v4_1 import measure as M                  # noqa: E402
from phrt.revision_v4_1.common_sky import DetectorGrid       # noqa: E402

MAPS = ROOT / "artifacts" / "raymaps"
REV = ROOT / "artifacts" / "revisions" / "mahakal_v4_1"
BANDS = ROOT / ("artifacts/e3_pilot/aart_out/core/"
                "LensingBands_a_0.5_i_50.0_dx0_0.4_dx1_0.08_dx2_0.02.h5")
GEOMETRY, SPIN, INC, D_OBS, R_OUTER = "a050_i050", 0.5, 50.0, 1000.0, 50.0
ORDERS, PROFILES = (0, 1, 2), ("coarse", "core", "fine")
SIGMA, T_REF, PITCH = 0.011341986814407566, -978.6055123201214, 0.4
CODE = ["src/phrt/revision_v4_1/domain.py",
        "src/phrt/revision_v4_1/query.py",
        "src/phrt/revision_v4_1/polyclip.py",
        "src/phrt/revision_v4_1/fractional.py",
        "src/phrt/revision_v4_1/hulls.py",
        "src/phrt/revision_v4_1/measure.py",
        "src/phrt/revision_v4_1/acquisition.py",
        "scripts/revision_v4_1/v0_overlay_and_freeze.py",
        "scripts/revision_v4_1/v1_contour_pilot.py",
        "scripts/revision_v4_1/g1_curved_hull.py",
        "tests/revision_v4_1/test_polyclip.py",
        "tests/revision_v4_1/test_fractional_027.py",
        "tests/revision_v4_1/test_boundary_028.py",
        "artifacts/configs/R1_MAIN_FREEZE.json",
        "artifacts/revisions/mahakal_v4_1/R2_REPLAY_TARGET_MANIFEST.json"]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main(out: Path) -> int:
    t0 = time.time()
    out.mkdir(parents=True, exist_ok=False)
    rh = horizon_radius(SPIN)
    grid = DetectorGrid(-25.0, 25.0, -25.0, 25.0, PITCH)

    rows = []
    with h5py.File(BANDS, "r") as f:
        hulls = {n: (f[f"hull_{n}e"][:], f[f"hull_{n}i"][:]) for n in ORDERS}
    for prof in PROFILES:
        bp = (ROOT / "artifacts/e3_pilot/aart_out" /
              ({"coarse": "coarse/LensingBands_a_0.5_i_50.0_dx0_0.8_dx1_0.16_dx2_0.04.h5",
                "core": "core/LensingBands_a_0.5_i_50.0_dx0_0.4_dx1_0.08_dx2_0.02.h5",
                "fine": "fine/LensingBands_a_0.5_i_50.0_dx0_0.2_dx1_0.04_dx2_0.01.h5"}[prof]))
        for n in ORDERS:
            rm = read(MAPS / f"{GEOMETRY}_n{n}_{prof}.h5")
            with h5py.File(bp, "r") as f:
                band = f[f"mask{n}"][:]
            cells = M.build_ray_cells(rm.alpha, rm.beta, M.NODAL_DUAL_CLIPPED)
            ov = FR.triple_overlap(cells, grid, *hulls[n])
            st, pr = D.classify_points(band, rm.source_r, rm.source_phi,
                                       rm.coordinate_time, rm.redshift,
                                       rh, R_OUTER)
            act = ov.active_area
            rows.append({"profile": prof, "order": n,
                         "n_samples": int(rm.alpha.size),
                         "geometric_band_area": float(act.sum()),
                         "centre_classified": D.tally(st, pr, act),
                         "fragments_with_positive_area":
                             int(np.count_nonzero(act > 0)),
                         "partially_cut_fragments":
                             int(np.count_nonzero((ov.cut_fraction > 1e-12)
                                                  & (ov.cut_fraction
                                                     < 1 - 1e-12)))})
            print(f"  {prof:<7} n{n}: emitting "
                  f"{rows[-1]['centre_classified']['by_state'][D.CERTIFIED_EMITTING]['area_fraction']:.4f}"
                  f"  non-emitting "
                  f"{rows[-1]['centre_classified']['by_state'][D.CERTIFIED_NON_EMITTING]['area_fraction']:.4f}"
                  f"  unresolved "
                  f"{rows[-1]['centre_classified']['by_state'][D.UNRESOLVED]['area_fraction']:.4f}",
                  flush=True)

    # Reconcile spend from the record rather than from a hand edit: every
    # run that issued physical calls wrote its guard snapshot, so the ledger
    # is summed from those instead of being asserted.
    prior = {"transfer": 0, "boundary": 0}
    seen = []
    for f in sorted(REV.glob("*/*.json")):
        try:
            g = json.loads(f.read_text()).get("guard")
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        if not isinstance(g, dict) or "spent_this_run" not in g:
            continue
        key = (f.parent.name, tuple(sorted(g["spent_this_run"].items())))
        if key in seen:
            continue
        seen.append(key)
        for k, v in g["spent_this_run"].items():
            prior[k] = prior.get(k, 0) + int(v)
    ledger = {"boundary_spent_lifetime": 18000 + prior["boundary"],
              "boundary_lifetime_cap": 30000,
              "boundary_remaining": 12000 - prior["boundary"],
              "prior_spend_reconciled_from_run_records": prior,
              "runs_counted": [k[0] for k in seen],
              "boundary_independent_check_reserve_min": 4000,
              "transfer_spent_lifetime": prior["transfer"],
              "transfer_lifetime_cap": 250000,
              "transfer_remaining": 20000 - prior["transfer"],
              "transfer_pilot_max": 20000,
              "transfer_initial_diagnostic_max": 4000,
              "transfer_independent_validation_reserve_min": 4000,
              "aborted_9000_boundary_solves_remain_charged": True,
              "counts_failures_retries_and_vectorised_interior_calls": True}
    freeze = {
        "schema": "phrt-input-freeze/1",
        "id": "BOUNDARY_VALIDITY_028_INPUT_FREEZE",
        "ruling": "PAPER_I_BOUNDARY_VALIDITY_RULING_028",
        "written_before_any_new_physical_query": True,
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "commit_at_freeze_time": None,
        "detector": {"name": "D026", "alpha": [-25.0, 25.0],
                     "beta": [-25.0, 25.0], "pitch_M": PITCH,
                     "cells": [grid.n_alpha, grid.n_beta], "sigma": SIGMA},
        "clock": {"absolute_reference_coordinate_time_M": T_REF,
                  "per_profile_recentering": "forbidden",
                  "negative_offsets": "recorded, never clipped"},
        "solver_policy": {
            "entry_point": "aart.raytracing_f.calculate_observables",
            "spin": SPIN, "inclination_deg": INC, "d_obs": D_OBS,
            "backend_substitution": "forbidden",
            "failed_value_zero_fill": "forbidden",
            "retry": "same physical equations, prospectively declared "
                     "numeric configuration only",
            "bracketing": "safeguarded bisection on a finite continuous "
                          "branch; a sign change alone does not certify "
                          "continuity, and equal signs do not exclude roots",
            "screen_bracket_required": True,
            "root_residual_alone_is_not_a_position_bound": True},
        "selection_rule": {
            "contour": "seeds from cached samples and declared geometry; "
                       "radial lines between an in-annulus and an "
                       "out-of-annulus cached sample of the same order",
            "target_information": "forbidden as a selection input",
            "declared_before_any_query": True},
        "target": {"indices": "the accepted 72, unchanged",
                   "reselection": "forbidden",
                   "spectra_counts_estimators": "not computed"},
        "accuracy": {"band_symdiff": 2.5e-4, "boundaries_symdiff": 2.5e-4,
                     "hull_only_response": 2.5e-4, "shifted_hull_check": 2.5e-4,
                     "tighter_root_check": 2.5e-5,
                     "transfer_and_emission_boundary_response": 5.0e-4,
                     "total_response_mask_area": 1.0e-3,
                     "integration_or_tessellation": 1.0e-6,
                     "exact_fixture": 1.0e-12,
                     "thinness_relaxes_geometry": False},
        "ledger": ledger,
        "n_files": len(CODE),
        "files": {},
    }
    missing = [f for f in CODE if not (ROOT / f).exists()]
    if missing:
        raise SystemExit(f"cannot freeze, files absent: {missing}")
    freeze["files"] = {f: sha(ROOT / f) for f in sorted(CODE)}
    freeze["commit_at_freeze_time"] = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True,
        text=True).stdout.strip()
    dirty = subprocess.run(["git", "status", "--porcelain", "--", *CODE],
                           cwd=ROOT, capture_output=True, text=True).stdout
    freeze["registered_tree_clean"] = dirty.strip() == ""
    freeze["uncommitted"] = dirty.strip().splitlines()
    (out / "BOUNDARY_VALIDITY_028_INPUT_FREEZE.json").write_text(
        json.dumps(freeze, indent=2) + "\n")

    (out / "POINT_STATUS_028.json").write_text(json.dumps({
        "stage": "V0", "new_physical_queries": 0,
        "warning": "these are CENTRE-CLASSIFIED areas. A fragment is labelled "
                   "by its centre ray, which certifies nothing about the "
                   "fragment: a centre outside the emission annulus says "
                   "nothing about the part of its cell inside, and a valid "
                   "centre does not make the transfer accurate across the "
                   "cell. Resolving that needs the contour, which is V1",
        "states": list(D.STATES),
        "certified_non_emitting_is_physics_not_a_gap": True,
        "rows": rows,
    }, indent=2) + "\n")
    print(f"  freeze at {freeze['commit_at_freeze_time'][:12]}, clean="
          f"{freeze['registered_tree_clean']}")
    print(f"  runtime {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main((ROOT / sys.argv[1]).resolve()))
