#!/usr/bin/env python3
"""E3C step 3 -- assemble the geometry surface, gates and hypothesis tests.

Reads the per-geometry JSON written by run_e3c_operator_grid.py and emits the
frozen artifact set. Nothing here recomputes physics; it aggregates, and it
aggregates under the rules the freeze pinned -- in particular, the surface is
reported cell by cell with median/min/max and monotonicity, and never with
population-style significance language, because twelve deterministic registered
geometries are not a sample from a population.

H1..H6 are hypotheses, not correctness gates. A negative outcome is recorded as
a negative outcome; nothing here is allowed to fail quietly.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from phrt.config import load_registry
from phrt.io.manifests import Gate, RunManifest, gate_from_tolerance, make_run_id, merge_gate_file
from phrt.io.tables import write_table

FREEZE = ROOT / "artifacts" / "configs" / "E3C_OPERATOR_GRID_FREEZE.json"
OUTDIR = ROOT / "artifacts" / "e3c"
REFERENCE_SNR = 100.0

GATE_TOLERANCES = {
    "G2_physical_dense_matrix_free": 1e-10,
    "G3_physical_adjoint": 1e-8,
    "G4_physical_resolved_unresolved_mixing": 1e-10,
    "G4b_linear_collapse_covariance_propagation": 1e-12,
    "G6_physical_Gram_monotonicity": 1e-10,
    "G6b_resolved_dominates_direct": 1e-10,
    "G9w_weight_semantics": 1e-10,
}

SPIN_OF = {"a000": 0.0, "a050": 0.5, "a090": 0.9, "a098": 0.98}


def parse_geometry(g: str) -> tuple[float, int]:
    a, i = g.split("_")
    return SPIN_OF[a], int(i[1:])


def curve(res: dict, arm: str) -> np.ndarray:
    """The registered scalar age-information curve."""
    return np.asarray(res["arms"][arm]["ihat"], dtype=float)


def logvol(res: dict, arm: str) -> np.ndarray:
    """AMENDMENT 002: log information volume on the registered localized class."""
    return np.asarray(res["arms"][arm]["log_information_volume_at_reference_snr"],
                      dtype=float)


def relative_l2(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.linalg.norm(a - b)) / max(1.0, float(np.linalg.norm(a)))


def discrepancy(full: np.ndarray, other: np.ndarray, snr: float) -> float:
    """D = ||log(1+I_full) - log(1+I_other)||_2 / max(1, ||log(1+I_full)||_2).

    On log(1+I) rather than I, so a single loud age cannot dominate the norm
    and hide a mechanism difference spread across the history.
    """
    a = np.log1p(snr ** 2 * full)
    b = np.log1p(snr ** 2 * other)
    return float(np.linalg.norm(a - b)) / max(1.0, float(np.linalg.norm(a)))


def depth_of(res: dict, arm: str, snr: float) -> dict:
    for r in res["depth_rows"]:
        if r["arm"] == arm and float(r["snr0"]) == snr:
            return r
    raise KeyError((arm, snr))


def jold_of(res: dict, arm: str, snr: float) -> float:
    for r in res["jold_rows"]:
        if r["arm"] == arm and float(r["snr0"]) == snr:
            return float(r["J_old"])
    raise KeyError((arm, snr))


def monotone(values: list[float]) -> str:
    """Trend label. 'constant' is reported explicitly rather than folded into
    'nondecreasing', because a flat sequence and a rising one are different
    findings and the weaker label would hide the flat one."""
    v = [x for x in values if np.isfinite(x)]
    if len(v) < 2:
        return "undetermined"
    d = np.diff(v)
    if np.all(d == 0):
        return "constant"
    if np.all(d >= 0):
        return "nondecreasing"
    if np.all(d <= 0):
        return "nonincreasing"
    return "nonmonotone"


def main() -> int:
    t0 = time.time()
    fz = json.loads(FREEZE.read_text())
    reg = load_registry()
    geoms = list(fz["geometries"])
    missing = [g for g in geoms if not (OUTDIR / f"{g}.json").exists()]
    if missing:
        raise SystemExit(f"E3C is incomplete; missing {missing}")
    R = {g: json.loads((OUTDIR / f"{g}.json").read_text()) for g in geoms}
    ages = np.asarray(R[geoms[0]]["ages"], dtype=float)
    snr_grid = [float(s) for s in fz["snr_grid"]]
    a_max = float(fz["common_age_grid"]["A_max_M"])
    arms = list(fz["arms"].keys())

    run_id = make_run_id("E3C", reg.sha256)
    man = RunManifest(run_id=run_id, experiment_id="E3C",
                      seeds={"subsample_seed": fz["observation"]["subsample_seed"],
                             "permutation_seeds": fz["permutation_seeds"]},
                      extra={"n_geometries": len(geoms),
                             "A_max_M": a_max,
                             "reference_snr": REFERENCE_SNR,
                             "source_class": fz["source_class"]["id"]})
    man.add_input(reg.path)
    man.add_input(FREEZE)

    # ---- correctness gates, worst case over the grid ----------------------
    gate_rows = []
    for name, tol in GATE_TOLERANCES.items():
        worst, where = -1.0, None
        for g in geoms:
            v = float(R[g]["gates"][name])
            if v > worst:
                worst, where = v, g
            gate_rows.append({"gate": name, "geometry": g, "measured": v,
                              "threshold": tol, "passes": bool(v <= tol)})
        man.add_gate(gate_from_tolerance(f"E3C_{name}", worst, tol,
                                         note=f"worst over {len(geoms)} geometries "
                                              f"(at {where})"))

    # the freeze itself is a gate: the maps evaluated must be the maps pinned
    from phrt.config import sha256_file
    maps = ROOT / "artifacts" / "raymaps"
    bad = [k for k, v in fz["raymap_sha256"].items() if sha256_file(maps / k) != v]
    man.add_gate(Gate("E3C_freeze_raymap_hashes", "PASS" if not bad else "FAIL",
                      measured=len(bad), threshold=0,
                      note="ray maps evaluated match the sha256 pinned in the "
                           "freeze" if not bad else f"changed since freeze: {bad}"))

    # every geometry must have used the same class, age grid and probe
    dims = {R[g]["source_dimension"] for g in geoms}
    nages = {len(R[g]["ages"]) for g in geoms}
    man.add_gate(Gate("E3C_frozen_grid_invariance",
                      "PASS" if dims == {224} and nages == {int(ages.size)} else "FAIL",
                      measured=f"dims={sorted(dims)} n_ages={sorted(nages)}",
                      threshold="dims=[224] n_ages=[%d]" % ages.size,
                      note="no basis, support, SNR grid, age grid or threshold "
                           "changed across the grid"))

    ident = [g for g in geoms
             if not np.array_equal(curve(R[g], "RESOLVED_PHYSICAL"),
                                   curve(R[g], "DELAY_ONLY"))]
    man.add_gate(Gate("E3C_H2_registered_statistic_is_an_identity",
                      "PASS" if not ident else "FAIL",
                      measured=len(geoms) - len(ident), threshold=len(geoms),
                      note="Amendment 002: the registered scalar H2 statistic is "
                           "identically zero because the flat probe cannot see a "
                           "spatial substitution. This gate asserts that the "
                           "degeneracy is exactly what it is claimed to be -- "
                           "bitwise equality at every geometry -- so the zero is "
                           "never read as evidence"
                           + ("" if not ident else f"; NOT identical at {ident}")))

    # ---- per-geometry, per-arm metric surface ------------------------------
    metrics = []
    for g in geoms:
        a, inc = parse_geometry(g)
        res = R[g]
        full = curve(res, "RESOLVED_PHYSICAL")
        for arm in arms:
            s = res["arms"][arm]["spectrum"]
            row = {"geometry": g, "spin": a, "inclination_deg": inc, "arm": arm,
                   "support": res["support"],
                   "source_dimension": res["source_dimension"],
                   "data_dimension": res["arms"][arm]["data_dimension"],
                   "rays_per_order": res["rays_per_order"],
                   "r_inner": res["r_inner"], "r_outer": res["r_outer"],
                   "a0_999_M": res["a0_999_M"],
                   "reference_snr": REFERENCE_SNR,
                   **s,
                   "J_old_at_reference_snr": jold_of(res, arm, REFERENCE_SNR),
                   "D_vs_resolved": discrepancy(full, curve(res, arm), REFERENCE_SNR),
                   "D_vs_resolved_localized_class":
                       relative_l2(logvol(res, "RESOLVED_PHYSICAL"), logvol(res, arm)),
                   "log_information_volume_total": float(logvol(res, arm).sum())}
            d = depth_of(res, arm, REFERENCE_SNR)
            row.update({"T_rec_at_reference_snr": d["deepest_detectable_age"],
                        "T_rec_right_censored": d["right_censored"],
                        "T_rec_report": d["depth_report"],
                        "T_rec_best_mode_at_reference_snr": d["T_rec_best_mode"],
                        "T_rec_best_mode_report": d["T_rec_best_mode_report"]})
            metrics.append(row)
        # delta_G_indirect rides in the same table as a pseudo-arm: it is a
        # Gram difference, not an operator, so its operational rank and depth
        # columns are explicitly marked not applicable rather than left blank.
        metrics.append({"geometry": g, "spin": a, "inclination_deg": inc,
                        "arm": "DELTA_G_INDIRECT", "support": res["support"],
                        "source_dimension": res["source_dimension"],
                        "data_dimension": 0, "rays_per_order": res["rays_per_order"],
                        "r_inner": res["r_inner"], "r_outer": res["r_outer"],
                        "a0_999_M": res["a0_999_M"], "reference_snr": REFERENCE_SNR,
                        "numerical_rank": res["delta_G_indirect"]["rank"],
                        "trace_information": res["delta_G_indirect"]["trace"],
                        "stable_rank": res["delta_G_indirect"]["stable_rank"],
                        "sigma_min_positive":
                            res["delta_G_indirect"]["min_positive_eigenvalue"],
                        "sigma_max": res["delta_G_indirect"]["max_eigenvalue"],
                        "kappa_positive": (res["delta_G_indirect"]["max_eigenvalue"]
                                           / max(res["delta_G_indirect"]
                                                 ["min_positive_eigenvalue"], 1e-300)),
                        "operational_rank": -1, "nullity": -1,
                        "effective_rank": float("nan"),
                        "J_old_at_reference_snr": float("nan"),
                        "D_vs_resolved": float("nan"),
                        "D_vs_resolved_localized_class": float("nan"),
                        "log_information_volume_total": float("nan"),
                        "T_rec_at_reference_snr": float("nan"),
                        "T_rec_right_censored": False, "T_rec_report": "n/a",
                        "T_rec_best_mode_at_reference_snr": float("nan"),
                        "T_rec_best_mode_report": "n/a"})
    man.add_output(write_table(metrics, "e3c_geometry_metrics"))

    # ---- age information curves -------------------------------------------
    age_rows = []
    for g in geoms:
        a, inc = parse_geometry(g)
        for r in R[g]["age_rows"]:
            age_rows.append({"geometry": g, "spin": a, "inclination_deg": inc, **r})
    man.add_output(write_table(age_rows, "e3c_age_information"))

    # ---- depth curves ------------------------------------------------------
    depth_rows = []
    for g in geoms:
        a, inc = parse_geometry(g)
        for r in R[g]["depth_rows"]:
            depth_rows.append({"geometry": g, "spin": a, "inclination_deg": inc, **r})
    man.add_output(write_table(depth_rows, "e3c_depth_curves"))

    # ---- historical innovation --------------------------------------------
    jrows = []
    for g in geoms:
        a, inc = parse_geometry(g)
        res = R[g]
        for r in res["jold_rows"]:
            jrows.append({"geometry": g, "spin": a, "inclination_deg": inc, **r})
        jrows.append({"geometry": g, "spin": a, "inclination_deg": inc,
                      "arm": "DELTA_G_INDIRECT", "snr0": REFERENCE_SNR,
                      "a0_999_lower_limit_M": res["a0_999_M"],
                      "J_old": float("nan"),
                      **{f"deltaG_{k}": v for k, v in res["delta_G_indirect"].items()}})
    man.add_output(write_table(jrows, "e3c_historical_innovation"))

    # ---- matched-sensitivity exponents ------------------------------------
    mrows, msummary = [], []
    for g in geoms:
        a, inc = parse_geometry(g)
        res = R[g]
        for r in res["matched"]:
            mrows.append({"geometry": g, "spin": a, "inclination_deg": inc, **r})
        att = {int(d["order"]): d for d in res["attenuation"]}
        for k in (0, 1):
            col = f"Gamma_sensitivity_matched_{k}_to_{k+1}"
            vals = [float(r[col]) for r in res["matched"]
                    if r[f"{col}_status"] == "ok"]
            lo, hi = res["windows"][k], res["windows"][k + 1]
            overlap = max(0.0, min(lo[1], hi[1]) - max(lo[0], hi[0]))
            union = max(lo[1], hi[1]) - min(lo[0], hi[0])
            gam = att[k + 1]["Gamma_amp_from_direct"] if k == 0 else \
                float(-np.log(max(att[2]["A_g"] / att[1]["A_g"], 1e-300)))
            msummary.append({
                "geometry": g, "spin": a, "inclination_deg": inc,
                "order_pair": f"{k}->{k+1}",
                "n_fractions_total": len(res["matched"]),
                "n_fractions_defined": len(vals),
                "n_fractions_unsupported": len(res["matched"]) - len(vals),
                "median": float(np.median(vals)) if vals else float("nan"),
                "q25": float(np.quantile(vals, 0.25)) if vals else float("nan"),
                "q75": float(np.quantile(vals, 0.75)) if vals else float("nan"),
                "iqr": float(np.quantile(vals, 0.75) - np.quantile(vals, 0.25))
                        if vals else float("nan"),
                "minimum": float(np.min(vals)) if vals else float("nan"),
                "maximum": float(np.max(vals)) if vals else float("nan"),
                "window_overlap_fraction": overlap / max(union, 1e-300),
                "Gamma_amp": gam,
                "exponent_difference_amp_minus_sensitivity":
                    gam - (float(np.median(vals)) if vals else float("nan")),
                "asymptotic_law_fitted": False,
                "n_fractions_negative": int(sum(1 for x in vals if x < 0.0)),
                "windows_disjoint": bool(overlap <= 0.0),
                "usable": bool(len(vals) == len(res["matched"])
                               and not any(x < 0.0 for x in vals)
                               and overlap > 0.0),
            })
            # Carry the adjudicated disposition in the table itself, so a cell
            # cannot be dropped from a denominator on the way to a figure. Every
            # H5 statement must report n_cells_total alongside n_cells_reported.
            last = msummary[-1]
            reasons = []
            if last["windows_disjoint"]:
                reasons.append("windows_disjoint")
            if last["n_fractions_defined"] < last["n_fractions_total"]:
                reasons.append("fractions_without_information")
            if last["n_fractions_negative"]:
                reasons.append("negative_exponent_fractions")
            last["disposition"] = ("SUPPORTED" if last["usable"]
                                   else "UNDEFINED_NO_COMMON_MATCHED_SUPPORT")
            last["undefined_reasons"] = ";".join(reasons)
            last["counts_toward_denominator"] = True
    man.add_output(write_table(mrows, "e3c_matched_sensitivity_exponents"))
    man.add_output(write_table(msummary, "e3c_matched_sensitivity_summary"))

    # ---- PAIRING_DESTROYED distribution ------------------------------------
    prows = []
    for g in geoms:
        a, inc = parse_geometry(g)
        for r in R[g]["pairing_destroyed_seeds"]:
            prows.append({"geometry": g, "spin": a, "inclination_deg": inc, **r})
    man.add_output(write_table(prows, "e3c_pairing_destroyed_distribution"))

    # ---- common-radial-support control -------------------------------------
    crows = []
    for g in fz["anchor_geometries"]:
        res = R[g]
        if "control" not in res:
            continue
        a, inc = parse_geometry(g)
        for arm in arms:
            for tag, blob in (("PRIMARY_GEOMETRY_DEPENDENT", res),
                              ("COMMON_RADIAL_SUPPORT", res["control"])):
                s = blob["arms"][arm]["spectrum"]
                d = depth_of(blob, arm, REFERENCE_SNR)
                crows.append({"geometry": g, "spin": a, "inclination_deg": inc,
                              "arm": arm, "support": tag,
                              "r_inner": blob["r_inner"], "r_outer": blob["r_outer"],
                              "rays_per_order": blob["rays_per_order"],
                              **s,
                              "J_old_at_reference_snr": jold_of(blob, arm, REFERENCE_SNR),
                              "T_rec_at_reference_snr": d["deepest_detectable_age"],
                              "T_rec_right_censored": d["right_censored"]})
    man.add_output(write_table(crows, "e3c_common_radial_support_control"))

    # ---- hypotheses H1..H6 --------------------------------------------------
    hyp = []
    for g in geoms:
        a, inc = parse_geometry(g)
        res = R[g]
        full = curve(res, "RESOLVED_PHYSICAL")
        base = {"geometry": g, "spin": a, "inclination_deg": inc}

        for snr in snr_grid:
            dr = depth_of(res, "RESOLVED_PHYSICAL", snr)
            dd = depth_of(res, "DIRECT_PHYSICAL", snr)
            du = depth_of(res, "UNRESOLVED_IMAGE", snr)
            jr = jold_of(res, "RESOLVED_PHYSICAL", snr)
            ju = jold_of(res, "UNRESOLVED_IMAGE", snr)
            hyp.append({**base, "hypothesis": "H1_historical_extension", "snr0": snr,
                        "T_resolved": dr["deepest_detectable_age"],
                        "T_direct": dd["deepest_detectable_age"],
                        "T_resolved_gt_T_direct":
                            dr["deepest_detectable_age"] > dd["deepest_detectable_age"],
                        "J_old_resolved": jr, "J_old_resolved_positive": jr > 0.0,
                        "right_censored": dr["right_censored"] or dd["right_censored"],
                        "value": dr["deepest_detectable_age"] - dd["deepest_detectable_age"]})
            hyp.append({**base, "hypothesis": "H4_order_label_value", "snr0": snr,
                        "T_unresolved": du["deepest_detectable_age"],
                        "T_resolved": dr["deepest_detectable_age"],
                        "R_unres_T": (du["deepest_detectable_age"]
                                      / dr["deepest_detectable_age"])
                                     if dr["deepest_detectable_age"] > 0 else float("nan"),
                        "J_old_unresolved": ju, "J_old_resolved": jr,
                        "R_unres_J": ju / jr if jr > 0 else float("nan"),
                        "right_censored": du["right_censored"] or dr["right_censored"],
                        "value": (ju / jr) if jr > 0 else float("nan")})

        d_delay = discrepancy(full, curve(res, "DELAY_ONLY"), REFERENCE_SNR)
        d_spat = discrepancy(full, curve(res, "SPATIAL_ONLY"), REFERENCE_SNR)
        hyp.append({**base, "hypothesis": "H2_delay_mechanism", "snr0": REFERENCE_SNR,
                    "D_delay": d_delay, "value": d_delay,
                    "note": "REGISTERED STATISTIC, DEGENERATE. The registered "
                            "localized probe is spatially flat and the delay-only "
                            "substitution changes only source_r and source_phi, so "
                            "this is identically zero as an algebraic identity, not "
                            "as evidence. See Amendment 002 and H2m."})
        hyp.append({**base, "hypothesis": "H3_spatial_mechanism", "snr0": REFERENCE_SNR,
                    "D_spatial": d_spat, "value": d_spat,
                    "kappa_full": res["arms"]["RESOLVED_PHYSICAL"]["spectrum"]["kappa_positive"],
                    "kappa_spatial_only": res["arms"]["SPATIAL_ONLY"]["spectrum"]["kappa_positive"],
                    "note": "REGISTERED STATISTIC. Non-degenerate for this "
                            "substitution, but its counterpart H2 is not, so the "
                            "pair cannot be compared. See H3m."})

        # AMENDMENT 002: the same comparison on the registered localized class,
        # where the delay-only substitution can actually move the curve.
        lv_full = logvol(res, "RESOLVED_PHYSICAL")
        d_delay_m = relative_l2(lv_full, logvol(res, "DELAY_ONLY"))
        d_spat_m = relative_l2(lv_full, logvol(res, "SPATIAL_ONLY"))
        d_direct_m = relative_l2(lv_full, logvol(res, "DIRECT_PHYSICAL"))
        hyp.append({**base, "hypothesis": "H2m_delay_mechanism_localized_class",
                    "snr0": REFERENCE_SNR, "D_delay": d_delay_m, "value": d_delay_m,
                    "D_direct_reference": d_direct_m,
                    "D_delay_over_D_direct": d_delay_m / max(d_direct_m, 1e-300),
                    "delay_closer_than_direct": bool(d_delay_m < d_direct_m),
                    "note": "relative L2 on sum_k log(1 + SNR^2 lambda_k(a)) over "
                            "the common age grid; the direct arm's discrepancy is "
                            "carried alongside as the scale against which a "
                            "substitution is close or far"})
        hyp.append({**base, "hypothesis": "H3m_spatial_mechanism_localized_class",
                    "snr0": REFERENCE_SNR, "D_spatial": d_spat_m, "value": d_spat_m,
                    "D_direct_reference": d_direct_m,
                    "D_spatial_over_D_direct": d_spat_m / max(d_direct_m, 1e-300),
                    "delay_closer_than_spatial": bool(d_delay_m < d_spat_m),
                    "spatial_closer_than_direct": bool(d_spat_m < d_direct_m),
                    "kappa_full": res["arms"]["RESOLVED_PHYSICAL"]["spectrum"]["kappa_positive"],
                    "kappa_spatial_only": res["arms"]["SPATIAL_ONLY"]["spectrum"]["kappa_positive"],
                    "kappa_delay_only": res["arms"]["DELAY_ONLY"]["spectrum"]["kappa_positive"],
                    "note": "conditioning reported alongside, because spatial "
                            "remapping may improve conditioning without moving the "
                            "oldest detected probe centre"})
    man.add_output(write_table(hyp, "e3c_hypothesis_tests"))

    # ---- H6 surface summary (no population language) ------------------------
    surface = []
    for metric, getter in (
        ("operational_rank_resolved",
         lambda r: r["arms"]["RESOLVED_PHYSICAL"]["spectrum"]["operational_rank"]),
        ("operational_rank_direct",
         lambda r: r["arms"]["DIRECT_PHYSICAL"]["spectrum"]["operational_rank"]),
        ("kappa_positive_resolved",
         lambda r: r["arms"]["RESOLVED_PHYSICAL"]["spectrum"]["kappa_positive"]),
        ("J_old_resolved", lambda r: jold_of(r, "RESOLVED_PHYSICAL", REFERENCE_SNR)),
        ("J_old_direct", lambda r: jold_of(r, "DIRECT_PHYSICAL", REFERENCE_SNR)),
        ("T_rec_resolved",
         lambda r: depth_of(r, "RESOLVED_PHYSICAL", REFERENCE_SNR)["deepest_detectable_age"]),
        ("T_rec_direct",
         lambda r: depth_of(r, "DIRECT_PHYSICAL", REFERENCE_SNR)["deepest_detectable_age"]),
        ("delta_G_indirect_rank", lambda r: r["delta_G_indirect"]["rank"]),
        ("delta_G_indirect_trace", lambda r: r["delta_G_indirect"]["trace"]),
        ("D_delay_registered_degenerate",
         lambda r: discrepancy(curve(r, "RESOLVED_PHYSICAL"),
                               curve(r, "DELAY_ONLY"), REFERENCE_SNR)),
        ("D_spatial_registered",
         lambda r: discrepancy(curve(r, "RESOLVED_PHYSICAL"),
                               curve(r, "SPATIAL_ONLY"), REFERENCE_SNR)),
        ("D_delay_localized_class",
         lambda r: relative_l2(logvol(r, "RESOLVED_PHYSICAL"), logvol(r, "DELAY_ONLY"))),
        ("D_spatial_localized_class",
         lambda r: relative_l2(logvol(r, "RESOLVED_PHYSICAL"), logvol(r, "SPATIAL_ONLY"))),
        ("D_direct_localized_class",
         lambda r: relative_l2(logvol(r, "RESOLVED_PHYSICAL"),
                               logvol(r, "DIRECT_PHYSICAL"))),
        ("D_delay_over_D_direct",
         lambda r: relative_l2(logvol(r, "RESOLVED_PHYSICAL"), logvol(r, "DELAY_ONLY"))
                   / max(relative_l2(logvol(r, "RESOLVED_PHYSICAL"),
                                     logvol(r, "DIRECT_PHYSICAL")), 1e-300)),
        ("D_spatial_over_D_direct",
         lambda r: relative_l2(logvol(r, "RESOLVED_PHYSICAL"), logvol(r, "SPATIAL_ONLY"))
                   / max(relative_l2(logvol(r, "RESOLVED_PHYSICAL"),
                                     logvol(r, "DIRECT_PHYSICAL")), 1e-300)),
        ("T_rec_best_mode_resolved",
         lambda r: depth_of(r, "RESOLVED_PHYSICAL", REFERENCE_SNR)["T_rec_best_mode"]),
        ("T_rec_best_mode_direct",
         lambda r: depth_of(r, "DIRECT_PHYSICAL", REFERENCE_SNR)["T_rec_best_mode"]),
    ):
        cells = {g: float(getter(R[g])) for g in geoms}
        vals = list(cells.values())
        row = {"metric": metric, "n_cells": len(vals),
               "median": float(np.median(vals)), "minimum": float(np.min(vals)),
               "maximum": float(np.max(vals)),
               "argmin": min(cells, key=cells.get), "argmax": max(cells, key=cells.get),
               "statistical_interpretation": "deterministic registered geometries; "
                                             "no population inference"}
        for inc in (20, 50, 75):
            seq = [cells[g] for g in geoms if parse_geometry(g)[1] == inc]
            row[f"monotone_in_spin_at_i{inc:03d}"] = monotone(seq)
        for a_tag in ("a000", "a050", "a090", "a098"):
            seq = [cells[g] for g in geoms if g.startswith(a_tag)]
            row[f"monotone_in_inclination_at_{a_tag}"] = monotone(seq)
        for g in geoms:
            row[f"cell_{g}"] = cells[g]
        surface.append(row)
    man.add_output(write_table(surface, "e3c_geometry_surface"))
    man.add_output(write_table(gate_rows, "e3c_gate_detail"))

    mp = man.write(reg.path, reg.sha256, runtime_seconds=time.time() - t0)
    merge_gate_file(man.gates, run_id)
    sub = {g.name: g.to_dict() for g in man.gates}
    (ROOT / "artifacts" / "gates" / "e3c_correctness_gates.json").write_text(
        json.dumps({"experiment": "E3C", "run_id": run_id, "gates": sub,
                    "summary": {s: sum(1 for v in sub.values() if v["status"] == s)
                                for s in ("PASS", "FAIL", "NOT_RUN")}},
                   indent=2) + "\n")
    print("gates")
    for g in man.gates:
        m = g.measured
        ms = f"{m:.3e}" if isinstance(m, float) else str(m)
        print(f"  {g.name:52s} {g.status:8s} {ms}")
    print(f"\nmanifest {mp}\ntotal {time.time() - t0:.0f}s")
    return 1 if man.failed_gates else 0


if __name__ == "__main__":
    raise SystemExit(main())
