#!/usr/bin/env python3
"""I0 of ruling 031: overlays, matched-domain inventory, accounting, freeze.

Zero physical queries. Rebuilds the mask inventory with explicit denominators,
reconciles the transfer counters from every attempt ledger rather than the
last stage's prefix, records the panel and comparator labels, and pins the
integration pilot's inputs.
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

REV = ROOT / "artifacts" / "revisions" / "mahakal_v4_1"
MAPS = ROOT / "artifacts" / "raymaps"
BANDS = ROOT / ("artifacts/e3_pilot/aart_out/core/LensingBands_"
                "a_0.5_i_50.0_dx0_0.4_dx1_0.08_dx2_0.02.h5")
GEOMETRY, SPIN, INC, D_OBS, R_OUTER = "a050_i050", 0.5, 50.0, 1000.0, 50.0
ORDERS = (0, 1, 2)
BATCH2_CAP = 20000
CODE = ["src/phrt/revision_v4_1/pathdomain2.py",
        "src/phrt/revision_v4_1/pathdomain.py",
        "src/phrt/revision_v4_1/query.py",
        "src/phrt/revision_v4_1/domain.py",
        "src/phrt/revision_v4_1/fractional.py",
        "src/phrt/revision_v4_1/polyclip.py",
        "scripts/revision_v4_1/t1_first_invalid_primitive.py",
        "scripts/revision_v4_1/i0_records_and_freeze_031.py",
        "scripts/revision_v4_1/i1_confirmation_031.py",
        "scripts/revision_v4_1/i2_domain_integration_031.py",
        "tests/revision_v4_1/test_pathdomain2_031.py",
        "tests/revision_v4_1/test_pathdomain_030.py"]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def reconcile() -> dict:
    """Every attempt ledger and guard snapshot, by execution, not by prefix."""
    runs, seen = {}, set()
    for f in sorted(REV.glob("*/ATTEMPT_LEDGER_*.json")):
        d = json.loads(f.read_text())
        runs[f.parent.name] = {"source": f.name,
                               "attempted": d["attempted"]["transfer"],
                               "completed": d["completed"]["transfer"],
                               "failed": d["failed"]["transfer"]}
        seen.add(f.parent.name)
    for f in sorted(REV.glob("*/*.json")):
        if f.parent.name in seen:
            continue
        try:
            g = json.loads(f.read_text()).get("guard")
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        if isinstance(g, dict) and "spent_this_run" in g:
            t = int(g["spent_this_run"].get("transfer", 0))
            if t:
                runs[f.parent.name] = {"source": f.name, "attempted": t,
                                       "completed": t, "failed": 0}
                seen.add(f.parent.name)
    batch2 = {k: v for k, v in runs.items()
              if k.startswith(("T1_", "D1_", "D1B_", "I1_", "I2_"))}
    spent = sum(v["attempted"] for v in batch2.values())
    return {
        "second_batch_runs": batch2,
        "second_batch_spent": spent,
        "second_batch_cap": BATCH2_CAP,
        "second_batch_remaining_upper_bound": BATCH2_CAP - spent,
        "first_pilot_closed_at": 17912,
        "lifetime_native_spend": 17912 + spent,
        "counted_per_execution_not_per_unique_point": True,
        "repeated_runs_each_charged": True,
        "unmetered_reference_integrations": {
            "status": "INVENTORIED",
            "what": "the primary and reference radial quadratures run after "
                    "the metered instrumented call and are not separately "
                    "charged as rays",
            "convention": "a quadrature abscissa is not a new ray; the "
                          "metered unit is one screen/order evaluation of "
                          "the pinned tracer",
            "end_to_end_recomputations_that_were_charged":
                "each execution charged its own full cohort, so the two 030 "
                "runs are 2156 + 2156 = 4312"},
    }


def main(out: Path) -> int:
    out.mkdir(parents=True, exist_ok=False)
    rh = horizon_radius(SPIN)
    grid = DetectorGrid(-25.0, 25.0, -25.0, 25.0, 0.4)
    hull_npz = next(REV.glob("G1C_*/CLOSEOUT_ARRAYS_029.npz"))
    hz = np.load(hull_npz)
    hulls = {k[5:]: hz[k] for k in hz.files if k.startswith("tess_")}

    # ---- matched-domain inventory, one denominator at a time ------------
    inv = {"new_physical_queries": 0,
           "why": "the 030 table counted UNRESOLVED over the whole stored "
                  "grid and reported in_band from a different mask, so its "
                  "two columns were not a common domain. Each row below "
                  "states its own denominator",
           "denominators": ["storage_grid", "archived_band",
                            "band_and_qualified_hull", "and_detector_aperture"],
           "per_order": {}}
    with h5py.File(BANDS, "r") as f:
        for n in ORDERS:
            rm = read(MAPS / f"{GEOMETRY}_n{n}_core.h5")
            band = f[f"mask{n}"][:]
            cells = M.build_ray_cells(rm.alpha, rm.beta, M.NODAL_DUAL_CLIPPED)
            ov = FR.triple_overlap(cells, grid, hulls[f"{n}e"], hulls[f"{n}i"])
            st, pr = D.classify_points(band, rm.source_r, rm.source_phi,
                                       rm.coordinate_time, rm.redshift, rh,
                                       R_OUTER)
            rows = {}
            for name, sel in (("storage_grid", np.ones(band.size, bool)),
                              ("archived_band", band),
                              ("band_and_qualified_hull",
                               band & (ov.active_area > 0)),
                              ("and_detector_aperture",
                               band & (ov.active_area > 0))):
                rows[name] = {
                    "n_samples": int(sel.sum()),
                    "cell_area": float(cells.area[sel].sum()),
                    "emitting": int((sel & (st == D.CERTIFIED_EMITTING)).sum()),
                    "non_emitting":
                        int((sel & (st == D.CERTIFIED_NON_EMITTING)).sum()),
                    "unresolved": int((sel & (st == D.UNRESOLVED)).sum())}
            rows["and_detector_aperture"]["note"] = (
                "the qualified hull already lies inside D026 for this "
                "geometry, so this row equals the previous one and the "
                "aperture removes nothing")
            rows["storage_grid"]["note"] = (
                "every sample the file stores, including the whole "
                "out-of-band remainder that was never evaluated. Its "
                "unresolved count is dominated by NO_PRIOR_EVALUATION and "
                "is not missing support inside the band")
            inv["per_order"][str(n)] = rows

    led = reconcile()
    overlay = {
        "final_panel_label": "PRECOMMITTED_PANEL_REUSED_AFTER_COMPARATOR_"
                             "CORRECTION",
        "panel_precommitted_before_first_run": True,
        "panel_disagreements_seen_before_the_correction": True,
        "original_disagreements_preserved": {"development": 57, "panel": 30},
        "primary_predicate_changed_during_correction": False,
        "primary_predicate_blob": "3f4cc4e4f641083474f3ac27feaac2e58398ae38",
        "independence_scope": "radial quadrature only. The two methods share "
                              "the conserved quantities, the radial roots, "
                              "the angular crossing parameter, the path "
                              "classifier and the asymptotic tail, so their "
                              "agreement is conditional on those inputs and "
                              "is not a verification of the whole geodesic "
                              "calculation",
        "sentinel_metric": "restricted panel agreement, not universal event "
                           "detection",
        "tail_label": "truncated asymptotic correction with a remainder "
                      "bound, not an exact closed form",
        "fixed_order_gauss_error": "no a posteriori estimate; the reference "
                                   "reports a convergence estimate from "
                                   "successive panel refinements, which is "
                                   "not an enclosure",
        "no_retroactive_compliance_claim": True,
    }
    (out / "MATCHED_DOMAIN_MASK_INVENTORY_031.json").write_text(
        json.dumps(inv, indent=2) + "\n")
    (out / "RESOURCE_LEDGER_031.json").write_text(
        json.dumps(led, indent=2) + "\n")

    freeze = {
        "schema": "phrt-input-freeze/1",
        "id": "DOMAIN_INTEGRATION_031_INPUT_FREEZE",
        "ruling": "PAPER_I_DOMAIN_INTEGRATION_RULING_031",
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
            "predicate": "pathdomain2, hardened; pathdomain v1 unchanged",
            "transfer_formula_repair": "none authorised, none made",
            "missing_node_or_failed_quadrature_as_zero": "forbidden"},
        "selection_rule": {
            "confirmation": "geometry and declared domain-margin strata: "
                            "emitting, capture absence, escape absence, "
                            "finite exterior outside the annulus, boundary "
                            "uncertainty",
            "integration": "validity-transition cells first, then known "
                           "smooth interiors; refinement by geometry and "
                           "declared field residuals only",
            "target_information": "forbidden as a selection input"},
        "representation_choice": {
            "chosen": "IMPLICIT_DOMAIN_INDICATOR_CUT_CELL_QUADRATURE",
            "declared_before_the_pilot": True,
            "why": "the V1 contour arrays are gone, so an explicit "
                   "reconstruction would spend the batch rebuilding a "
                   "boundary before testing the integral it serves",
            "not_a_claim_to_have_reconstructed_the_contour": True},
        "qualified_hull": {"file": str(hull_npz.relative_to(ROOT)),
                           "sha256": sha(hull_npz),
                           "reused_by_hash_no_new_solves": True},
        "accuracy": {"transfer_emission_component": 5.0e-4,
                     "total_response_mask_area": 1.0e-3,
                     "integration_or_tessellation": 1.0e-6,
                     "exact_fixture": 1.0e-12},
        "ledger": {"transfer_remaining": led["second_batch_remaining_upper_bound"],
                   "boundary_remaining": 0,
                   "confirmation_points_max": 192,
                   "confirmation_evaluations_max": 1024,
                   "integration_pilot_max": 6000,
                   "independent_validation_reserve_min": 4000,
                   **led},
        "overlay": overlay,
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
    freeze["registered_tree_clean"] = subprocess.run(
        ["git", "status", "--porcelain", "--", *tracked], cwd=ROOT,
        capture_output=True, text=True).stdout.strip() == ""
    (out / "DOMAIN_INTEGRATION_031_INPUT_FREEZE.json").write_text(
        json.dumps(freeze, indent=2) + "\n")
    (out / "COMPARATOR_AND_COUNTER_OVERLAY_031.md").write_text(
        "# Comparator and counter overlay, ruling 031\n\n"
        + json.dumps({**overlay, "accounting": led}, indent=2) + "\n")
    print(f"  second batch: {led['second_batch_spent']} spent across "
          f"{len(led['second_batch_runs'])} executions, "
          f"{led['second_batch_remaining_upper_bound']} remaining")
    for n, r in inv["per_order"].items():
        b = r["archived_band"]
        w = r["band_and_qualified_hull"]
        print(f"  order {n}: band {b['n_samples']} "
              f"(E{b['emitting']}/N{b['non_emitting']}/U{b['unresolved']}), "
              f"band+hull {w['n_samples']} "
              f"(E{w['emitting']}/N{w['non_emitting']}/U{w['unresolved']})")
    print(f"  freeze at {freeze['commit_at_freeze_time'][:12]}, clean="
          f"{freeze['registered_tree_clean']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main((ROOT / sys.argv[1]).resolve()))
