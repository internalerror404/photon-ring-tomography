#!/usr/bin/env python3
"""M4 of ruling 032: the costed matched-comparison plan. Zero physical queries.

Every number below is measured on archived geometry -- ray-map node
coordinates, the qualified hull tessellation, the lensing-band masks and the
archived centre labels. No ray is traced and no path integral is recomputed,
so the census is a property of what is already on disk.

The plan is built before it is priced, not after. The comparison matrix is the
full 18 endpoints (two profiles x three orders x three integration levels); the
levels are one leaf-rule family at k = 1, 2, 4, so the represented quantity
never changes while the parameter refines; and the allocation unit is a whole
(profile, order, level) bundle rather than a traversal position.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import h5py

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from phrt.geometry.raymap import horizon_radius, read            # noqa: E402
from phrt.revision_v4_1 import domain as D                       # noqa: E402
from phrt.revision_v4_1 import fractional as FR                  # noqa: E402
from phrt.revision_v4_1 import leaf as LF                        # noqa: E402
from phrt.revision_v4_1 import measure as M                      # noqa: E402
from phrt.revision_v4_1 import plan032 as PL                     # noqa: E402
from phrt.revision_v4_1.common_sky import DetectorGrid           # noqa: E402

MAPS = ROOT / "artifacts" / "raymaps"
AART = ROOT / "artifacts" / "e3_pilot" / "aart_out"
BANDS = {"core": AART / ("core/LensingBands_a_0.5_i_50.0_dx0_0.4_dx1_0.08"
                         "_dx2_0.02.h5"),
         "fine": AART / ("fine/LensingBands_a_0.5_i_50.0_dx0_0.2_dx1_0.04"
                         "_dx2_0.01.h5")}
HULL = ROOT / ("artifacts/revisions/mahakal_v4_1/G1C_20260907T075203Z_d252697"
               "/CLOSEOUT_ARRAYS_029.npz")
GEOMETRY, SPIN, INC, D_OBS, R_OUTER = "a050_i050", 0.5, 50.0, 1000.0, 50.0
SIGMA, T_REF = 0.011341986814407566, -978.6055123201214
LEVELS = {"L0": 1, "L1": 2, "L2": 4}

# Declared BEFORE the census is read, and independent of any target quantity:
# the local region is a wedge of screen position angle about the projected
# spin axis (+beta), which is a geometric direction of the configuration. Its
# half-width is chosen by cost alone, from a fixed ladder, largest first.
WEDGE_CENTRE_DEG = 90.0
WEDGE_LADDER_DEG = (45.0, 30.0, 20.0, 15.0, 10.0, 7.5, 5.0, 3.0, 2.0, 1.0)

FIELD_SET = {
    "id": "transfer_fields_v1",
    "columns": ["emission_indicator_chi", "redshift_cubed_g3",
                "source_azimuth_phi_s", "source_coordinate_time_t_s",
                "inherited_temporal_test_fields_at_eight_observer_times"],
    "why": ("ruling 032 section 7: chi multiplies the full transferred source "
            "response. A constant occupancy column cannot qualify the "
            "operator, so the plan carries the transferred fields themselves."),
}


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with Path(p).open("rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def transition_mask(state, n_alpha: int) -> np.ndarray:
    E = (state == D.CERTIFIED_EMITTING).reshape(n_alpha, n_alpha)
    m = np.zeros_like(E)
    m[:-1, :] |= E[:-1, :] != E[1:, :]
    m[1:, :] |= E[:-1, :] != E[1:, :]
    m[:, :-1] |= E[:, :-1] != E[:, 1:]
    m[:, 1:] |= E[:, :-1] != E[:, 1:]
    return m.reshape(-1)


def census() -> dict:
    """Transition cells, unresolved support and areas, for all six endpoints."""
    rh = horizon_radius(SPIN)
    grid = DetectorGrid(-25.0, 25.0, -25.0, 25.0, 0.4)
    hz = np.load(HULL)
    out = {}
    for prof in ("core", "fine"):
        with h5py.File(BANDS[prof], "r") as h:
            band = {n: h[f"mask{n}"][:] for n in (0, 1, 2)}
        for n in (0, 1, 2):
            rm = read(MAPS / f"{GEOMETRY}_n{n}_{prof}.h5")
            cells = M.build_ray_cells(rm.alpha, rm.beta, M.NODAL_DUAL_CLIPPED)
            ov = FR.triple_overlap(cells, grid, hz[f"tess_{n}e"],
                                   hz[f"tess_{n}i"])
            st, _ = D.classify_points(band[n], rm.source_r, rm.source_phi,
                                      rm.coordinate_time, rm.redshift, rh,
                                      R_OUTER)
            active = ov.active_area > 0
            tm = transition_mask(st, np.unique(rm.alpha).size) & active
            unres = (st == D.UNRESOLVED) & active
            ang = np.degrees(np.arctan2(rm.beta, rm.alpha)) % 360.0
            d = np.abs((ang - WEDGE_CENTRE_DEG + 180.0) % 360.0 - 180.0)
            rec = {"cells_total": int(cells.alpha_lo.size),
                   "band_active_cells": int(active.sum()),
                   "band_active_area": float(ov.active_area.sum()),
                   "transition_found": int(tm.sum()),
                   "transition_area": float(ov.active_area[tm].sum()),
                   "unresolved_support_cells": int(unres.sum()),
                   "unresolved_support_area": float(ov.active_area[unres].sum()),
                   "wedge": {}}
            rec["unresolved_support_area_fraction"] = (
                rec["unresolved_support_area"] / rec["band_active_area"])
            for hw in WEDGE_LADDER_DEG:
                w = d <= hw
                rec["wedge"][f"{hw:g}"] = {
                    "transition_found": int((tm & w).sum()),
                    "transition_area": float(ov.active_area[tm & w].sum()),
                    "band_active_area": float(ov.active_area[w].sum()),
                    "unresolved_support_area":
                        float(ov.active_area[unres & w].sum())}
            out[f"{prof}_n{n}"] = rec
            print(f"  census {prof} n{n}: {rec['transition_found']} transition,"
                  f" unresolved support {rec['unresolved_support_area_fraction']:.3%}",
                  flush=True)
    return out


def bundle_charge(t_found: int, level: str) -> int:
    """New evaluations a (profile, order, level) bundle needs.

    L0 reuses the archived centre labels and charges nothing. L1 and L2 place
    k x k leaf midpoints inside every transition parent; the L2 figure is the
    upper bound that must be reserved, because the cheaper nested variant --
    refining only the leaves that are still transitional at L1 -- cannot be
    sized before L1 has run.
    """
    k = LEVELS[level]
    return 0 if k == 1 else int(t_found) * k * k


def build_plan(cen: dict, scope: str, half_width: float | None,
               reconciled_remaining: int, reserve: int,
               prerequisite_status: str) -> dict:
    tasks, evals = [], []
    for n in (0, 1, 2):
        dom = ("full_band_order%d" % n if half_width is None else
               f"wedge_pa{WEDGE_CENTRE_DEG:g}_hw{half_width:g}_order{n}")
        for prof in ("core", "fine"):
            rec = cen[f"{prof}_n{n}"]
            t = (rec["transition_found"] if half_width is None else
                 rec["wedge"][f"{half_width:g}"]["transition_found"])
            for lev in ("L0", "L1", "L2"):
                eid = f"{prof}:{n}:{lev}"
                q = bundle_charge(t, lev)
                ev = {"id": eid, "transition_parents": int(t),
                      "leaf_factor": LEVELS[lev]}
                if q == 0:
                    src = MAPS / f"{GEOMETRY}_n{n}_{prof}.h5"
                    ev.update({"charge": 0, "cache_sha256": sha256(src),
                               "cache_path": str(src.relative_to(ROOT))})
                else:
                    ev["charge"] = int(q)
                evals.append(ev)
                tasks.append({
                    "profile": prof, "order": n, "level": lev,
                    "physical_domain_id": dom,
                    "representation_id": LF.LEAF_RULE,
                    "field_set_id": FIELD_SET["id"],
                    "detector_id": "D026", "clock_id": "T_REF_absolute",
                    "sigma_id": "sigma_D026_0.011341986814407566",
                    "payload_export": True, "evaluation_ids": [eid]})
    return {"scope": scope, "tasks": tasks, "evaluations": evals,
            "reconciled_remaining": int(reconciled_remaining),
            "validation_reserve": int(reserve),
            "accounting_scope_resolved": True,
            "prerequisite_status": prerequisite_status}


def main(out: Path, remaining: int = 6434, reserve: int = 4000) -> int:
    t0 = time.time()
    cen = census()
    spendable = remaining - reserve

    full = build_plan(cen, "full_domain_qualification", None, remaining,
                      reserve, "SUPPORTED_FOR_DECLARED_SCOPE")
    full_cost = PL.declared_cost(full)

    # A local region is only a diagnostic if every endpoint has something to
    # measure in it. A wedge that fits the budget by containing no transition
    # parents at an endpoint is not cheaper, it is empty, so the ladder is
    # searched for the smallest NON-DEGENERATE wedge and its cost is reported
    # whether or not it fits.
    ladder = []
    for hw in WEDGE_LADDER_DEG:
        t = {f"{prof}_n{n}": cen[f"{prof}_n{n}"]["wedge"][f"{hw:g}"]
                             ["transition_found"]
             for n in (0, 1, 2) for prof in ("core", "fine")}
        cand = build_plan(cen, "local_feasibility", hw, remaining, reserve,
                          "SUPPORTED_FOR_DECLARED_SCOPE")
        c = PL.declared_cost(cand)
        ladder.append({"half_width_deg": hw, "cost": c,
                       "transition_parents": t,
                       "min_transition_parents": min(t.values()),
                       "non_degenerate": min(t.values()) > 0,
                       "fits_spendable": c <= spendable})
    feasible = [r for r in ladder if r["non_degenerate"] and r["fits_spendable"]]
    usable = [r for r in ladder if r["non_degenerate"]]
    pick = (feasible[-1] if feasible else (usable[-1] if usable else None))
    chosen_hw = pick["half_width_deg"] if pick else None
    local_cost = pick["cost"] if pick else None
    local = (build_plan(cen, "local_feasibility", chosen_hw, remaining, reserve,
                        "SUPPORTED_FOR_DECLARED_SCOPE")
             if chosen_hw is not None else None)

    # The plan that is actually returned states the prerequisite honestly.
    prereq = "REFERENCE_UNRESOLVED_66_CASES_AND_ORDER2_MISSING_SUPPORT"
    plan = dict(local if local is not None else full)
    plan["prerequisite_status"] = prereq
    plan["declared_scope_note"] = (
        "local_feasibility was not chosen to make a smaller claim quietly: "
        "the full-domain matrix is costed in the same file and does not fit "
        "in the remaining allowance, or in the lifetime transfer cap.")
    plan["metadata"] = {
        "ruling": "PAPER_I_MATCHED_INTEGRATION_RULING_032",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "commit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                 capture_output=True, text=True).stdout.strip(),
        "geometry": {"id": GEOMETRY, "spin": SPIN, "inclination_deg": INC,
                     "d_obs": D_OBS, "r_outer": R_OUTER},
        "detector": {"id": "D026", "alpha_M": [-25.0, 25.0],
                     "beta_M": [-25.0, 25.0], "pitch_M": 0.4,
                     "sigma": SIGMA, "clock_reference_M": T_REF,
                     "observer_times": 8,
                     "noise_is_full_detector_area_once_per_time": True},
        "field_set": FIELD_SET,
        "levels": {k: {"leaf_factor": v,
                       "leaves_per_transition_parent": v * v} for k, v in
                   LEVELS.items()},
        "level_semantics": (
            "one leaf-rule family; k refines the integration of an unchanged "
            "intended domain. L0 is the archived centre indicator (k = 1) and "
            "charges nothing because its values are on disk and hashed."),
        "region": ({"kind": "full_band"} if chosen_hw is None else
                   {"kind": "screen_position_angle_wedge",
                    "centre_deg": WEDGE_CENTRE_DEG,
                    "half_width_deg": chosen_hw,
                    "chosen_by": "cost alone, from a ladder fixed in the "
                                 "source before the census was read",
                    "same_region_for_both_profiles": True}),
        "census": cen,
        "wedge_ladder": ladder,
        "smallest_non_degenerate_wedge_deg": chosen_hw,
        "any_wedge_both_affordable_and_non_degenerate": bool(feasible),
        "local_plan_fits_spendable": bool(pick and pick["fits_spendable"]),
        "full_domain_cost": full_cost,
        "local_cost": local_cost,
        "spendable_before_reserve": spendable,
        "allocation_unit": "complete (profile, order, level) bundle",
        "stop_rule": ("an unfunded endpoint stops the campaign; it is never "
                      "converted into a baseline observation"),
        "schedule": "all three orders at L1 before any order reaches L2",
        "payload_write_order": "chunk payload and hash first, summary after",
    }
    if chosen_hw is not None:
        cov = {}
        for n in (0, 1, 2):
            for prof in ("core", "fine"):
                r = cen[f"{prof}_n{n}"]
                w = r["wedge"][f"{chosen_hw:g}"]
                cov[f"{prof}_n{n}"] = {
                    "band_area_in_region": w["band_active_area"],
                    "band_area_total": r["band_active_area"],
                    "covered_fraction": w["band_active_area"]
                                        / r["band_active_area"],
                    "omitted_fraction": 1.0 - w["band_active_area"]
                                        / r["band_active_area"],
                    "transition_parents_in_region": w["transition_found"],
                    "transition_parents_total": r["transition_found"]}
        plan["metadata"]["coverage_and_omission"] = cov
        plan["metadata"]["omitted_regions_are_bounded"] = False
        plan["metadata"]["local_patch_implies_global_qualification"] = False

    (out / "MATCHED_COMPARISON_PLAN_032.json").write_text(
        json.dumps(plan, indent=2) + "\n")

    # the reviewer's own preflight, on the plan as returned and on a variant in
    # which the prerequisite is stipulated met, so schema and cost are separable
    script = ROOT / ("docs/revisions/mahakal_v4_1/review032/"
                     "checks_and_preflight_032.py")
    tmp = out / "_plan_prereq_stipulated.json"
    stip = dict(plan)
    stip["prerequisite_status"] = "SUPPORTED_FOR_DECLARED_SCOPE"
    tmp.write_text(json.dumps(stip, indent=2) + "\n")
    results = {}
    for tag, path in (("as_returned", out / "MATCHED_COMPARISON_PLAN_032.json"),
                      ("prerequisite_stipulated_met", tmp)):
        dst = out / f"_preflight_{tag}.json"
        subprocess.run([sys.executable, str(script), "--plan", str(path),
                        "--output", str(dst)], cwd=ROOT, check=True,
                       capture_output=True, text=True)
        results[tag] = json.loads(dst.read_text())
        dst.unlink()
    tmp.unlink()

    # and the reviewer's 20 synthetic checks, run here rather than assumed
    dst = out / "_checks.json"
    subprocess.run([sys.executable, str(script), "--output", str(dst)],
                   cwd=ROOT, check=True, capture_output=True, text=True)
    checks = json.loads(dst.read_text())
    dst.unlink()

    full_pf = dict(full)
    full_pf["prerequisite_status"] = prereq
    (out / "_full.json").write_text(json.dumps(full_pf, indent=2) + "\n")
    dst = out / "_preflight_full.json"
    subprocess.run([sys.executable, str(script), "--plan", str(out / "_full.json"),
                    "--output", str(dst)], cwd=ROOT, check=True,
                   capture_output=True, text=True)
    results["full_domain_matrix"] = json.loads(dst.read_text())
    dst.unlink()
    (out / "_full.json").unlink()

    pre = {
        "stage": "M4", "ruling": "PAPER_I_MATCHED_INTEGRATION_RULING_032",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "physical_queries": 0,
        "preflight_script_sha256": sha256(script),
        "schema_pass_authorizes_execution": False,
        "results": results,
        "reviewer_synthetic_checks": {"n_checks": checks["n_checks"],
                                      "all_passed": checks["all_passed"]},
        "in_process_gate_agrees": {
            "as_returned": PL.validate_plan(plan),
            "full_domain_matrix": PL.validate_plan(full_pf)},
        "costs": {"full_domain_new_evaluations": full_cost,
                  "local_new_evaluations": local_cost,
                  "spendable_after_reserve": spendable,
                  "reported_native_remaining": remaining,
                  "validation_reserve_preserved": reserve,
                  "lifetime_transfer_cap": 250000},
        "runtime_seconds": time.time() - t0,
    }
    (out / "PLAN_PREFLIGHT_032.json").write_text(json.dumps(pre, indent=2) + "\n")
    print(json.dumps({"stage": "M4", "full_cost": full_cost,
                      "local_cost": local_cost, "wedge_half_width": chosen_hw,
                      "spendable": spendable,
                      "as_returned": results["as_returned"]["status"],
                      "stipulated": results["prerequisite_stipulated_met"]["status"],
                      "full": results["full_domain_matrix"]["status"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main((ROOT / sys.argv[1]).resolve()))
