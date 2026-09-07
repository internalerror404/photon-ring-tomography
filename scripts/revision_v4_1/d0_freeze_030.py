#!/usr/bin/env python3
"""D0 of ruling 030: overlays, derivation, counter reconciliation, freeze.

Zero physical calls. Records the corrections, states the path-domain
construction and its conventions, reconciles the transfer counters against
the committed attempt records, and pins the development cohort and the
precommitted holdout before a single new evaluation is made.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from phrt.geometry.raymap import read, horizon_radius        # noqa: E402

REV = ROOT / "artifacts" / "revisions" / "mahakal_v4_1"
MAPS = ROOT / "artifacts" / "raymaps"
GEOMETRY, SPIN, INC, D_OBS, R_OUTER = "a050_i050", 0.5, 50.0, 1000.0, 50.0
SPIN_V, INC_V = SPIN, INC
CODE = ["src/phrt/revision_v4_1/pathdomain.py",
        "src/phrt/revision_v4_1/query.py",
        "src/phrt/revision_v4_1/domain.py",
        "scripts/revision_v4_1/t1_first_invalid_primitive.py",
        "scripts/revision_v4_1/d0_freeze_030.py",
        "scripts/revision_v4_1/d1d2_adjudicate_030.py",
        "tests/revision_v4_1/test_pathdomain_030.py",
        "tests/revision_v4_1/test_boundary_028.py"]
BATCH2_CAP, SPENT_BEFORE_030 = 20000, 2640


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main(out: Path) -> int:
    out.mkdir(parents=True, exist_ok=False)
    rh = horizon_radius(SPIN)
    rng = np.random.default_rng(2030)

    # ---- counter reconciliation from the committed attempt records -------
    runs = {}
    for f in sorted(REV.glob("T1_*/FIRST_INVALID_PRIMITIVE_029.json")):
        runs[f.parent.name] = json.loads(f.read_text())["guard"][
            "spent_this_run"]["transfer"]
    total = sum(runs.values())
    ledger = {
        "committed_second_batch_attempts": runs,
        "second_batch_spent_before_030": total,
        "second_batch_original_cap": BATCH2_CAP,
        "second_batch_remaining": BATCH2_CAP - total,
        "summary_file_previously_reported": 18920,
        "correction": "the 029 return summarised only the last of three "
                      "executed T1 runs. All three are separately recorded "
                      "attempts and all three count, including the two that "
                      "revisited the same points",
        "old_records_rewritten": False,
        "first_pilot_closed_at": 17912,
        "transfer_lifetime_spent_before_030": 17912 + total,
        "boundary_lifetime_spent": 33410, "boundary_remaining": 890,
        "new_boundary_calls_authorised": 0,
    }

    # ---- cohorts, pinned before any new evaluation ----------------------
    coh = {}
    import h5py
    bands = {"core": ROOT / ("artifacts/e3_pilot/aart_out/core/LensingBands_"
                             "a_0.5_i_50.0_dx0_0.4_dx1_0.08_dx2_0.02.h5"),
             "fine": ROOT / ("artifacts/e3_pilot/aart_out/fine/LensingBands_"
                             "a_0.5_i_50.0_dx0_0.2_dx1_0.04_dx2_0.01.h5")}
    for prof in ("core", "fine"):
        with h5py.File(bands[prof], "r") as f:
            for n in (0, 1, 2):
                rm = read(MAPS / f"{GEOMETRY}_n{n}_{prof}.h5")
                b = f[f"mask{n}"][:]
                fin = np.isfinite(rm.source_r)
                bad = np.flatnonzero(b & ~fin)
                ok = np.flatnonzero(b & fin & (rm.source_r > rh)
                                    & (rm.source_r <= R_OUTER))
                near50 = ok[np.argsort(np.abs(rm.source_r[ok] - R_OUTER))[:60]]
                nearh = ok[np.argsort(rm.source_r[ok])[:60]]
                if prof == "core":
                    ctl = rng.choice(ok, min(80, ok.size), replace=False)
                    coh[f"dev_n{n}"] = {
                        "role": "development", "profile": prof,
                        "failures": bad.tolist(),
                        "controls": np.unique(np.concatenate(
                            [ctl, near50, nearh])).tolist()}
                else:
                    pick = rng.choice(ok, min(120, ok.size), replace=False)
                    coh[f"holdout_n{n}"] = {
                        "role": "precommitted_holdout", "profile": prof,
                        "note": "a different profile and different screen "
                                "points from the development cohort; these "
                                "have not been inspected",
                        "failures": rng.choice(
                            bad, min(80, bad.size), replace=False).tolist()
                        if bad.size else [],
                        "controls": np.unique(np.concatenate(
                            [pick, near50, nearh])).tolist()}
    n_dev = sum(len(v["failures"]) + len(v["controls"])
                for k, v in coh.items() if k.startswith("dev"))
    n_hold = sum(len(v["failures"]) + len(v["controls"])
                 for k, v in coh.items() if k.startswith("holdout"))

    freeze = {
        "schema": "phrt-input-freeze/1", "id": "PATH_DOMAIN_030_INPUT_FREEZE",
        "ruling": "PAPER_I_PATH_DOMAIN_RULING_030",
        "written_before_any_new_physical_query": True,
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "commit_at_freeze_time": subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True,
            text=True).stdout.strip(),
        "detector": {"name": "D026", "unchanged": True},
        "clock": {"absolute_reference_coordinate_time_M": -978.6055123201214},
        "solver_policy": {
            "entry_point": "aart.raytracing_f.calculate_observables",
            "spin": SPIN, "inclination_deg": INC, "d_obs": D_OBS,
            "expression_switch_on_raw_radius_sign": "forbidden",
            "force_positive_radius": "forbidden",
            "change_requested_order": "forbidden",
            "new_production_backend": "forbidden",
            "arithmetic_change": "none; the wrapper only decides whether the "
                                 "requested crossing exists"},
        "selection_rule": {
            "development": "every reported failure plus healthy controls "
                           "including the nearest to r=50 and to the horizon",
            "holdout": "precommitted, from the fine profile, different "
                       "screen points, not previously inspected",
            "target_information": "forbidden as a selection input"},
        "path_domain": {
            "mino_parameter": "s increases backward from s=0 at the "
                              "observer; it is not coordinate time and not "
                              "retarded age",
            "requested_crossing": "s_n = G_theta for the exact order, the "
                                  "same quantity the pinned evaluator forms",
            "capture": "s_H = int_{r_+}^{r_o} dr/sqrt(R); "
                       "s_50 = int_{50}^{r_o} dr/sqrt(R); an emitting "
                       "crossing needs s_n in [s_50, s_H)",
            "scatter": "J(r) = int_{r_t}^{r} dr/sqrt(R); with r_t < 50 < r_o "
                       "the annulus interval is [J_o - J(50), J_o + J(50)]",
            "turn_outside_annulus": "no annulus intersection",
            "root_branch": "an accessible exterior turn must be real, "
                           "outside the horizon and inside the observer; a "
                           "small imaginary part is not sufficient",
            "singularity": "r = r_t + u^2 removes the inverse square root at "
                           "a simple turn exactly",
            "boundary_within_margin": "DOMAIN_UNRESOLVED, never a forced "
                                      "boolean"},
        "accuracy": {"exact_fixture": 1.0e-12, "hull": 2.5e-4,
                     "transfer_emission": 5.0e-4, "total": 1.0e-3,
                     "margin_factor_on_quadrature_error": 10.0},
        "cohorts": coh,
        "cohort_sizes": {"development": n_dev, "holdout": n_hold},
        "ledger": {"transfer_remaining": BATCH2_CAP - total,
                   "boundary_remaining": 0,
                   "d1_decision_point_max": 3000,
                   "independent_validation_reserve_min": 4000,
                   **ledger},
        "files": {}, "n_files": 0,
    }
    import aart
    files = list(CODE) + [str(p) for p in
                          sorted(Path(aart.__file__).parent.glob("*.py"))]
    missing = [f for f in files if not (ROOT / f).exists()]
    if missing:
        raise SystemExit(f"cannot freeze, absent: {missing}")
    freeze["files"] = {f: sha(ROOT / f) for f in sorted(files)}
    freeze["n_files"] = len(freeze["files"])
    tracked = [f for f in freeze["files"] if not Path(f).is_absolute()]
    dirty = subprocess.run(["git", "status", "--porcelain", "--", *tracked],
                           cwd=ROOT, capture_output=True, text=True).stdout
    freeze["registered_tree_clean"] = dirty.strip() == ""
    (out / "PATH_DOMAIN_030_INPUT_FREEZE.json").write_text(
        json.dumps(freeze, indent=2) + "\n")
    (out / "RESOURCE_LEDGER_030.json").write_text(
        json.dumps(ledger, indent=2) + "\n")
    print(f"  reconciled second batch: {runs} -> {total} spent, "
          f"{BATCH2_CAP - total} remaining")
    print(f"  cohorts: development {n_dev}, precommitted holdout {n_hold}")
    print(f"  freeze at {freeze['commit_at_freeze_time'][:12]}, clean="
          f"{freeze['registered_tree_clean']}, files {freeze['n_files']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main((ROOT / sys.argv[1]).resolve()))
