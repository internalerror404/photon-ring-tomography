#!/usr/bin/env python3
"""Build Paper I from canonical post-G10q artifacts only.

Every number in the manuscript is fetched through the claim ledger, which
refuses any path outside artifacts/CANONICAL_ARTIFACT_FREEZE.json. A pre-G10q
table therefore cannot reach the paper: it is not in the freeze, so the lookup
raises instead of returning a stale value.

Outputs
    artifacts/manuscript/PAPER_I.md          the manuscript
    artifacts/manuscript/PAPER_I.html        compiled, for visual inspection
    artifacts/manuscript/CLAIM_LEDGER.json   every number and where it came from
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from phrt import provenance
from phrt.config import load_registry
from phrt.io.dashboard import gate_counts
from phrt.manuscript.ledger import ClaimLedger
from phrt.manuscript.render import page

OUT = ROOT / "artifacts" / "manuscript"
# The v2 freeze is the accepted post-E3C-v2 line and is the only one that
# contains the R1 tables. v1 is preserved as the record of the v1 manuscript and
# is used only if v2 is absent.
FREEZE_V2 = ROOT / "artifacts" / "CANONICAL_ARTIFACT_FREEZE_V2.json"
FREEZE_V1 = ROOT / "artifacts" / "CANONICAL_ARTIFACT_FREEZE.json"
FREEZE_PATH = FREEZE_V2 if FREEZE_V2.exists() else FREEZE_V1

MET = "artifacts/tables/e3c_geometry_metrics.parquet"
SURF = "artifacts/tables/e3c_geometry_surface.parquet"
HYP = "artifacts/tables/e3c_hypothesis_tests.parquet"
DEP = "artifacts/tables/e3c_depth_curves.parquet"
MS = "artifacts/tables/e3c_matched_sensitivity_summary.parquet"
PDS = "artifacts/tables/e3c_pairing_destroyed_distribution.parquet"
CTL = "artifacts/tables/e3c_common_radial_support_control.parquet"
QNT = "artifacts/tables/e3c_weighted_delay_quantiles.parquet"
DGR = "artifacts/tables/e3c_incremental_indirect_gram.parquet"
DSP = "artifacts/tables/e3d_class_spectra.parquet"
DDP = "artifacts/tables/e3d_depth_by_class.parquet"
DNS = "artifacts/tables/e3d_class_nesting.parquet"
DSM = "artifacts/tables/e3d_operator_smoke.parquet"
BSP = "artifacts/tables/e3b_singular_spectra.parquet"
BMS = "artifacts/tables/e3b_matched_support_attenuation.parquet"
GATES = "artifacts/gates/correctness_gates.json"
E3CFZ = "artifacts/configs/E3C_OPERATOR_GRID_FREEZE.json"
SUPS = "artifacts/SUPERSEDED_PRE_G10Q.json"
CANON = ("artifacts/CANONICAL_ARTIFACT_FREEZE_V2.json" if FREEZE_V2.exists()
         else "artifacts/CANONICAL_ARTIFACT_FREEZE.json")

# R1 held-out main
R1D = "artifacts/tables/r1_stable_depth.parquet"
R1F = "artifacts/tables/r1_family_depth.parquet"
R1B = "artifacts/tables/r1_bootstrap.parquet"
R1L = "artifacts/tables/r1_level_structure.parquet"
R1W = "artifacts/tables/r1_data_weak_errors.parquet"
R1N = "artifacts/tables/r1_null_pairs.parquet"
R1FZ = "artifacts/configs/R1_MAIN_FREEZE.json"

REF = 100.0
CANARY = "a050_i050"
SPINS = ["a000", "a050", "a090", "a098"]
INCS = [20, 50, 75]
CLASSES = ["C224", "C448_T", "C528_S", "C1056_ST"]
ARMS = ["DIRECT_PHYSICAL", "RESOLVED_PHYSICAL", "UNRESOLVED_IMAGE", "TOTAL_FLUX",
        "DELAY_ONLY", "SPATIAL_ONLY", "EQUALIZED_ORDER_SENSITIVITY",
        "PAIRING_DESTROYED"]
D = "\n"

TITLE = ("Photon-Ring Retarded-Time Tomography I: Class-Dependent "
         "Identifiability, the Separation of Historical Reach from Algebraic "
         "Rank, and Held-Out Reconstruction of Age-Local Emissivity Level in "
         "Near-Critical Null Geodesics")


def surface_table(surf: pd.DataFrame, metric: str, fmt: str = "{:.0f}") -> str:
    r = surf.loc[surf.metric == metric].iloc[0]
    out = ["| a\\* \\ i | 20° | 50° | 75° | trend in inclination |",
           "|---|---:|---:|---:|---|"]
    for a in SPINS:
        cells = [r[f"cell_{a}_i{i:03d}"] for i in INCS]
        out.append(f"| {float(a[1:]) / 100:.2f} | "
                   + " | ".join(fmt.format(c) for c in cells)
                   + f" | {r[f'monotone_in_inclination_at_{a}']} |")
    out.append("| **trend in spin** | "
               + " | ".join(r[f"monotone_in_spin_at_i{i:03d}"] for i in INCS) + " | |")
    return "\n".join(out)


def main() -> int:
    t0 = time.time()
    OUT.mkdir(parents=True, exist_ok=True)
    fz = json.loads(FREEZE_PATH.read_text())
    L = ClaimLedger(root=ROOT, freeze=fz["artifacts"])
    reg, prov, counts = load_registry(), provenance.collect(), gate_counts()
    e3cfz = json.loads((ROOT / E3CFZ).read_text())
    gdoc = json.loads((ROOT / GATES).read_text())["gates"]

    met, surf, hyp = L.frame(MET), L.frame(SURF), L.frame(HYP)
    dep, ms, pds = L.frame(DEP), L.frame(MS), L.frame(PDS)
    ctl, dsp, ddp = L.frame(CTL), L.frame(DSP), L.frame(DDP)
    dns, qnt = L.frame(DNS), L.frame(QNT)
    c: dict[str, str] = {}

    # ---- structural constants ---------------------------------------------
    c["ngeom"] = L.literal("grid.n_geometries", len(e3cfz["geometries"]),
                           str(len(e3cfz["geometries"])),
                           source=f"{E3CFZ} /geometries",
                           prose="registered geometries")
    c["dim224"] = L.json("class.C224.dimension", E3CFZ, "/source_class/dimension",
                         fmt="{:d}", prose="dimension of the registered source class")
    c["amax"] = L.json("grid.A_max", E3CFZ, "/common_age_grid/A_max_M", fmt="{:.0f}",
                       prose="common age-grid ceiling, M")
    c["astep"] = L.json("grid.age_step", E3CFZ, "/common_age_grid/step_M", fmt="{:.0f}",
                        prose="age-grid spacing, M")
    c["q999"] = L.json("grid.max_Q0999", E3CFZ,
                       "/common_age_grid/max_Q_0999_over_grid_M", fmt="{:.1f}",
                       prose="largest 99.9% weighted delay quantile on the grid, M")
    c["araw"] = L.json("grid.A_max_raw", E3CFZ,
                       "/common_age_grid/raw_before_rounding_M", fmt="{:.1f}",
                       prose="age ceiling before rounding, M")
    c["h"] = L.json("probe.half_width", E3CFZ, "/localized_probe/half_width_h_M",
                    fmt="{:.0f}", prose="localized probe half width, M")
    c["nrays"] = L.json("obs.rays_per_order", E3CFZ, "/observation/rays_per_order",
                        fmt="{:d}", prose="rays retained per order")
    c["ntimes"] = L.json("obs.n_times", E3CFZ, "/observation/n_observer_times",
                         fmt="{:d}", prose="observer-time samples")
    c["tspan"] = L.json("obs.span", E3CFZ, "/observation/observer_span_M", fmt="{:.0f}",
                        prose="observer-time span, M")
    c["nseeds"] = L.count("control.seeds", PDS, where={"geometry": CANARY},
                          prose="frozen permutation seeds per geometry")

    # ---- gates -------------------------------------------------------------
    def gate(name: str, fmt: str = "{:.3g}") -> tuple[str, str, str]:
        st = L.json(f"gate.{name}.status", GATES, f"/gates/{name}/status",
                    prose=f"status of gate {name}")
        m = gdoc[name].get("measured")
        mv = (L.json(f"gate.{name}.measured", GATES, f"/gates/{name}/measured",
                     fmt=fmt, prose=f"measured value of gate {name}")
              if isinstance(m, (int, float)) and not isinstance(m, bool) else str(m))
        th = gdoc[name].get("threshold", "–")
        return st, mv, (f"{th:.3g}" if isinstance(th, float) else str(th))

    gate_names = [f"E3C_{k}" for k in
                  ("G2_physical_dense_matrix_free", "G3_physical_adjoint",
                   "G4_physical_resolved_unresolved_mixing",
                   "G4b_linear_collapse_covariance_propagation",
                   "G6_physical_Gram_monotonicity", "G6b_resolved_dominates_direct",
                   "G9w_weight_semantics", "freeze_raymap_hashes",
                   "frozen_grid_invariance",
                   "H2_registered_statistic_is_an_identity")] + \
                 ["E3D_adjoint", "E3D_dense_smoke_comparison", "E3D_Gram_monotonicity",
                  "E3D_class_nesting", "E3D_enrichment_does_not_lose_rank",
                  "G10q_continuum_noise_quadrature_invariance"]
    rows = ["| gate | status | measured | threshold |", "|---|---|---:|---:|"]
    for k in gate_names:
        st, mv, th = gate("E3C_" + k[4:] if False else k)
        rows.append(f"| `{k}` | **{st}** | {mv} | {th} |")
    c["gate_table"] = D.join(rows)
    c["g10q"] = L.json("gate.G10q.measured.copy", GATES,
                       "/gates/G10q_continuum_noise_quadrature_invariance/measured",
                       fmt="{:.1e}", prose="split/merge quadrature invariance, "
                                           "corrected convention")
    c["g10q_bad"] = L.json("gate.G10q_retired.measured", GATES,
                           "/gates/G10q_retired_flat_sigma_convention/measured",
                           fmt="{:.0f}",
                           prose="split/merge invariance under the retired convention")
    c["npass"] = L.literal("gates.pass", counts["passing"], str(counts["passing"]),
                           source=GATES, prose="gates passing")
    c["nactive"] = L.literal("gates.active", counts["active_blocking_failures"],
                             str(counts["active_blocking_failures"]), source=GATES,
                             prose="active blocking failures")
    c["npres"] = L.literal("gates.preserved", counts["preserved_literal_failures"],
                           str(counts["preserved_literal_failures"]), source=GATES,
                           prose="preserved literal failures")
    c["nnr"] = L.literal("gates.not_run", counts["future_phase_not_run"],
                         str(counts["future_phase_not_run"]), source=GATES,
                         prose="gates registered but not yet in scope")
    c["pres_table"] = D.join(
        ["| preserved failure | adjudicated disposition |", "|---|---|"] +
        [f"| `{k}` | `{vv}` |" for k, vv
         in counts["preserved_literal_failure_dispositions"].items()])

    # ---- H1 -----------------------------------------------------------------
    c["h1_depth"] = L.count("H1.T_resolved_gt_direct", HYP, where={
        "hypothesis": "H1_historical_extension", "snr0": REF,
        "resolved_probe_deeper_than_direct": True},
        prose="geometries where resolved depth exceeds direct depth at the "
              "reference SNR")
    c["h1_j"] = L.count("H1.J_old_positive", HYP, where={
        "hypothesis": "H1_historical_extension", "snr0": REF,
        "J_old_resolved_positive": True},
        prose="geometries with strictly positive resolved historical innovation")
    c["ncens"] = L.count("depth.right_censored", DEP, where={"right_censored": True},
                         prose="right-censored depth entries")
    c["ndepth"] = L.count("depth.rows", DEP, prose="depth entries in total")
    for i in INCS:
        c[f"trec{i}"] = L.table(f"H1.T_resolved.i{i:03d}", MET,
                                "oldest_detectable_age_probe_at_reference_snr", agg="median", fmt="{:.0f}",
                                where={"arm": "RESOLVED_PHYSICAL",
                                       "inclination_deg": i},
                                prose=f"median resolved depth at i = {i} deg")
        c[f"tdir{i}"] = L.table(f"H1.T_direct.i{i:03d}", MET,
                                "oldest_detectable_age_probe_at_reference_snr", agg="median", fmt="{:.0f}",
                                where={"arm": "DIRECT_PHYSICAL",
                                       "inclination_deg": i},
                                prose=f"median direct depth at i = {i} deg")
        c[f"nspin{i}"] = L.table(f"H1.T_resolved.distinct_spins.i{i:03d}", MET,
                                 "oldest_detectable_age_probe_at_reference_snr", agg="nunique", fmt="{:d}",
                                 where={"arm": "RESOLVED_PHYSICAL",
                                        "inclination_deg": i},
                                 prose=f"distinct resolved depths across the four "
                                       f"spins at i = {i} deg")
    _nspin = sorted({int(met[(met.arm == "RESOLVED_PHYSICAL")
                             & (met.inclination_deg == i)]
                         .oldest_detectable_age_probe_at_reference_snr.nunique()) for i in INCS})
    c["spin_flat"] = L.derived(
        "H1.T_resolved.spin_flat", _nspin == [1], "a single value" if _nspin == [1]
        else "more than one value",
        inputs=[f"H1.T_resolved.distinct_spins.i{i:03d}" for i in INCS],
        expression="the four spins give one distinct depth at every inclination",
        prose="whether recoverable depth depends on spin at fixed inclination")
    c["surf_trec_res"] = surface_table(surf, "oldest_detectable_age_probe_resolved")
    c["surf_trec_dir"] = surface_table(surf, "oldest_detectable_age_probe_direct")
    c["surf_jold_res"] = surface_table(surf, "J_old_resolved", "{:.2f}")
    c["surf_jold_dir"] = surface_table(surf, "J_old_direct", "{:.2f}")

    # ---- H2m / H3m ----------------------------------------------------------
    c["dreg"] = L.table("H2.registered.max", HYP, "D_delay", agg="max", fmt="{:.1e}",
                        where={"hypothesis": "H2_delay_mechanism"},
                        prose="largest value of the registered scalar H2 statistic "
                              "anywhere on the grid")
    c["ddel"] = L.table("H2m.D_delay.median", HYP, "D_delay", agg="median",
                        fmt="{:.3f}",
                        where={"hypothesis": "H2m_delay_mechanism_localized_class"},
                        prose="median delay-only discrepancy on the localized class")
    c["dspa"] = L.table("H3m.D_spatial.median", HYP, "D_spatial", agg="median",
                        fmt="{:.3f}",
                        where={"hypothesis": "H3m_spatial_mechanism_localized_class"},
                        prose="median spatial-only discrepancy on the localized class")
    c["ddir"] = L.table("H3m.D_direct.median", HYP, "D_direct_reference", agg="median",
                        fmt="{:.3f}",
                        where={"hypothesis": "H3m_spatial_mechanism_localized_class"},
                        prose="median direct-arm discrepancy, the reference scale")
    c["nclose"] = L.count("H3m.delay_closer", HYP, where={
        "hypothesis": "H3m_spatial_mechanism_localized_class",
        "delay_closer_than_spatial": True},
        prose="geometries where delay-only is closer to the full operator than "
              "spatial-only")
    c["rdel"] = L.table("H2m.ratio.median", HYP, "D_delay_over_D_direct", agg="median",
                        fmt="{:.2f}",
                        where={"hypothesis": "H2m_delay_mechanism_localized_class"},
                        prose="median D_delay / D_direct")
    c["rspa"] = L.table("H3m.ratio.median", HYP, "D_spatial_over_D_direct",
                        agg="median", fmt="{:.2f}",
                        where={"hypothesis": "H3m_spatial_mechanism_localized_class"},
                        prose="median D_spatial / D_direct")
    h2m = hyp[hyp.hypothesis == "H2m_delay_mechanism_localized_class"].set_index("geometry")
    h3m = hyp[hyp.hypothesis == "H3m_spatial_mechanism_localized_class"].set_index("geometry")
    c["mech_table"] = D.join(
        ["| geometry | D_delay (registered) | D_delay | D_spatial | D_direct | "
         "D_delay / D_direct | D_spatial / D_direct |", "|---|---:|---:|---:|---:|---:|---:|"] +
        [f"| `{g}` | {hyp[(hyp.hypothesis == 'H2_delay_mechanism') & (hyp.geometry == g)].D_delay.iloc[0]:.1e} "
         f"| {h2m.loc[g, 'D_delay']:.4f} | {h3m.loc[g, 'D_spatial']:.4f} "
         f"| {h3m.loc[g, 'D_direct_reference']:.4f} "
         f"| {h2m.loc[g, 'D_delay_over_D_direct']:.3f} "
         f"| {h3m.loc[g, 'D_spatial_over_D_direct']:.3f} |"
         for g in e3cfz["geometries"]])

    # ---- H4 -----------------------------------------------------------------
    for k, col in (("rt", "R_unres_T"), ("rj", "R_unres_J")):
        for agg in ("min", "max", "median"):
            c[f"{k}_{agg}"] = L.table(f"H4.{col}.{agg}", HYP, col, agg=agg,
                                      fmt="{:.2f}",
                                      where={"hypothesis": "H4_order_label_value",
                                             "snr0": REF},
                                      prose=f"{agg} of {col} at the reference SNR")
    h4 = hyp[(hyp.hypothesis == "H4_order_label_value") & (hyp.snr0 == REF)]
    c["h4_table"] = D.join(
        ["| geometry | T(unresolved) / T(resolved) | J_old(unresolved) / J_old(resolved) |",
         "|---|---:|---:|"] +
        [f"| `{r.geometry}` | {r.R_unres_T:.3f} | {r.R_unres_J:.3f} |"
         for _, r in h4.iterrows()])

    # ---- H5 -----------------------------------------------------------------
    c["ms_total"] = L.count("H5.cells.total", MS, prose="matched-support cells")
    c["ms_sup"] = L.count("H5.cells.supported", MS,
                          where={"disposition": "SUPPORTED"},
                          prose="matched-support cells with common support")
    c["ms_undef"] = L.count("H5.cells.undefined", MS,
                            where={"disposition":
                                   "UNDEFINED_NO_COMMON_MATCHED_SUPPORT"},
                            prose="matched-support cells marked undefined")
    for agg in ("median", "min", "max"):
        c[f"diff_{agg}"] = L.table(f"H5.difference.{agg}", MS,
                                   "exponent_difference_amp_minus_sensitivity",
                                   agg=agg, fmt="{:.3f}",
                                   where={"disposition": "SUPPORTED"},
                                   prose=f"{agg} throughput-minus-sensitivity "
                                         "exponent difference, supported cells")
    sup = ms[ms.disposition == "SUPPORTED"]
    n_pos = int((sup.exponent_difference_amp_minus_sensitivity > 0).sum())
    c["diff_pos"] = L.derived("H5.difference.positive_cells", n_pos, str(n_pos),
                              inputs=["H5.cells.supported"],
                              expression="count of supported cells with "
                                         "Gamma_amp - Gamma_sensitivity > 0",
                              prose="supported cells where the sensitivity exponent "
                                    "is below the throughput exponent")
    c["canary01"] = L.table("canary.Gamma_sens.0to1", MS, "median", fmt="{:.3f}",
                            where={"geometry": CANARY, "order_pair": "0->1"},
                            prose="median matched sensitivity exponent 0 to 1 at the "
                                  "canary geometry, corrected convention")
    c["canary12"] = L.table("canary.Gamma_sens.1to2", MS, "median", fmt="{:.3f}",
                            where={"geometry": CANARY, "order_pair": "1->2"},
                            prose="median matched sensitivity exponent 1 to 2 at the "
                                  "canary geometry, corrected convention")
    c["camp01"] = L.table("canary.Gamma_amp.0to1", MS, "Gamma_amp", fmt="{:.2f}",
                          where={"geometry": CANARY, "order_pair": "0->1"},
                          prose="throughput exponent 0 to 1 at the canary geometry")
    c["camp12"] = L.table("canary.Gamma_amp.1to2", MS, "Gamma_amp", fmt="{:.2f}",
                          where={"geometry": CANARY, "order_pair": "1->2"},
                          prose="throughput exponent 1 to 2 at the canary geometry")
    c["bms01"] = L.table("canary.e3b.Gamma_sens.0to1", BMS,
                         "Gamma_sensitivity_matched_0_to_1", agg="median",
                         fmt="{:.3f}",
                         prose="independent corrected-convention value of the same "
                               "exponent from the E3B canary table")
    c["bms12"] = L.table("canary.e3b.Gamma_sens.1to2", BMS,
                         "Gamma_sensitivity_matched_1_to_2", agg="median",
                         fmt="{:.3f}",
                         prose="independent corrected-convention value of the 1 to 2 "
                               "exponent from the E3B canary table")
    c["ms_table"] = D.join(
        ["| geometry | pair | defined / 19 | median | IQR | Gamma_amp | difference | "
         "window overlap | disposition |", "|---|---|---:|---:|---:|---:|---:|---:|---|"] +
        [f"| `{r.geometry}` | {r.order_pair} | {int(r.n_fractions_defined)} | "
         f"{r['median']:.3f} | {r.iqr:.3f} | {r.Gamma_amp:.3f} | "
         f"{r.exponent_difference_amp_minus_sensitivity:.3f} | "
         f"{r.window_overlap_fraction:.3f} | "
         f"{'supported' if r.disposition == 'SUPPORTED' else '**undefined**'} |"
         for _, r in ms.iterrows()])
    c["undef_table"] = D.join(
        ["| geometry | pair | reasons |", "|---|---|---|"] +
        [f"| `{r.geometry}` | {r.order_pair} | {r.undefined_reasons.replace(';', ', ')} |"
         for _, r in ms[ms.disposition != "SUPPORTED"].iterrows()])

    # ---- H6 -----------------------------------------------------------------
    c["surf_oprank_res"] = surface_table(surf, "operational_rank_resolved")
    _r = surf.loc[surf.metric == "operational_rank_resolved"].iloc[0]
    _spin_tr = {i: _r[f"monotone_in_spin_at_i{i:03d}"] for i in INCS}
    _inc_tr = {a: _r[f"monotone_in_inclination_at_{a}"] for a in SPINS}
    _spin_words = ", ".join(f"{_spin_tr[i]} at i = {i}" for i in INCS)
    _inc_words = ", ".join(f"{_inc_tr[a]} at a* = {float(a[1:]) / 100:.2f}"
                           for a in SPINS)
    c["oprank_trend"] = L.literal(
        "surface.oprank.trend", f"{_spin_words}; {_inc_words}",
        f"{_spin_words}; {_inc_words}", source=SURF,
        prose="monotonicity of the resolved operational rank in spin at each "
              "inclination and in inclination at each spin")
    c["surf_oprank_dir"] = surface_table(surf, "operational_rank_direct")
    c["surf_kappa"] = surface_table(surf, "kappa_positive_resolved", "{:.2e}")
    c["surf_dg"] = surface_table(surf, "delta_G_indirect_rank")

    # ---- arms ----------------------------------------------------------------
    arm_rows = ["| arm | operational rank (median) | range | kappa+ (median) | "
                "J_old (median) | T_rec (median) |", "|---|---:|---|---:|---:|---:|"]
    for a in ARMS:
        s = met[met.arm == a]
        arm_rows.append(f"| `{a}` | {s.operational_rank.median():.0f} | "
                        f"{int(s.operational_rank.min())}–{int(s.operational_rank.max())} | "
                        f"{s.kappa_positive.median():.2e} | "
                        f"{s.J_old_at_reference_snr.median():.2f} | "
                        f"{s.oldest_detectable_age_probe_at_reference_snr.median():.0f} |")
    c["arm_table"] = D.join(arm_rows)
    for a in ("DIRECT_PHYSICAL", "RESOLVED_PHYSICAL", "TOTAL_FLUX"):
        c[f"op_{a}"] = L.table(f"arm.{a}.oprank.median", MET, "operational_rank",
                               agg="median", fmt="{:.0f}", where={"arm": a},
                               prose=f"median operational rank of {a}")
    # Amendment 001 item 7 moved the incremental indirect Gram out of the
    # per-arm metrics table into its own: it is a difference of Grams, not an
    # operator, and as a pseudo-arm row it borrowed columns that did not apply.
    c["dg_rank_min"] = L.table("dG.rank.min", DGR, "numerical_rank", agg="min",
                               fmt="{:d}", where={"quantity": "delta_G_indirect"},
                               prose="smallest rank of G_resolved - G_direct")
    c["dg_rank_max"] = L.table("dG.rank.max", DGR, "numerical_rank", agg="max",
                               fmt="{:d}", where={"quantity": "delta_G_indirect"},
                               prose="largest rank of G_resolved - G_direct")

    # ---- corrected canary numbers -------------------------------------------
    res_tr = float(L.frame(BSP).loc[L.frame(BSP).arm == "RESOLVED_PHYSICAL",
                                    "trace_information"].iloc[0])
    dir_tr = float(L.frame(BSP).loc[L.frame(BSP).arm == "DIRECT_PHYSICAL",
                                    "trace_information"].iloc[0])
    c["tr_res"] = L.table("canary.trace.resolved", BSP, "trace_information",
                          fmt="{:.4g}", where={"arm": "RESOLVED_PHYSICAL"},
                          prose="resolved trace information, canary geometry")
    c["tr_dir"] = L.table("canary.trace.direct", BSP, "trace_information",
                          fmt="{:.4g}", where={"arm": "DIRECT_PHYSICAL"},
                          prose="direct trace information, canary geometry")
    gain = 100.0 * (res_tr / dir_tr - 1.0)
    c["tr_gain"] = L.derived("canary.trace.gain_percent", gain, f"{gain:.2f}",
                             inputs=["canary.trace.resolved", "canary.trace.direct"],
                             expression="100 * (resolved / direct - 1)",
                             prose="trace-information gain of the resolved stack over "
                                   "the direct image, corrected convention, per cent")
    c["cop_res"] = L.table("canary.oprank.resolved", BSP, "operational_rank",
                           fmt="{:d}", where={"arm": "RESOLVED_PHYSICAL"},
                           prose="resolved operational rank, canary geometry")
    c["cop_dir"] = L.table("canary.oprank.direct", BSP, "operational_rank",
                           fmt="{:d}", where={"arm": "DIRECT_PHYSICAL"},
                           prose="direct operational rank, canary geometry")

    # ---- E3D ------------------------------------------------------------------
    c["nanch"] = L.count("E3D.anchors", DSP,
                         where={"source_class": "C224", "arm": "RESOLVED_PHYSICAL"},
                         prose="anchor geometries in the source-class stress")
    c["n224rows"] = L.count("E3D.C224.rows", DSP, where={"source_class": "C224"},
                            prose="arm-anchor combinations evaluated on C224")
    c["n224full"] = L.count("E3D.C224.full_rank", DSP,
                            where={"source_class": "C224", "full_column_rank": True},
                            prose="arm-anchor combinations with full column rank on C224")
    for cl in CLASSES[1:]:
        c[f"ndef_{cl}"] = L.count(f"E3D.{cl}.deficient", DSP,
                                  where={"source_class": cl, "full_column_rank": False},
                                  prose=f"rank-deficient arm-anchor combinations on {cl}")
    c["nul448dir"] = L.table("E3D.C448.direct.max_nullity", DSP, "nullity", agg="max",
                             fmt="{:d}", where={"source_class": "C448_T",
                                                "arm": "DIRECT_PHYSICAL"},
                             prose="largest direct-channel nullity on C448_T")
    c["nul528dir"] = L.table("E3D.C528.direct.max_nullity", DSP, "nullity", agg="max",
                             fmt="{:d}", where={"source_class": "C528_S",
                                                "arm": "DIRECT_PHYSICAL"},
                             prose="largest direct-channel nullity on C528_S")
    c["nul1056res"] = L.table("E3D.C1056.resolved.max_nullity", DSP, "nullity",
                              agg="max", fmt="{:d}",
                              where={"source_class": "C1056_ST",
                                     "arm": "RESOLVED_PHYSICAL"},
                              prose="largest resolved nullity on C1056_ST")
    c["nul1056dir"] = L.table("E3D.C1056.direct.max_nullity", DSP, "nullity",
                              agg="max", fmt="{:d}",
                              where={"source_class": "C1056_ST",
                                     "arm": "DIRECT_PHYSICAL"},
                              prose="largest direct-channel nullity on C1056_ST")
    c["nestres"] = L.table("E3D.nesting.max_residual", DNS, "projection_residual",
                           agg="max", fmt="{:.1e}",
                           prose="largest residual of projecting a parent class design "
                                 "onto its child's span")
    c["smoke"] = L.table("E3D.smoke.max", DSM, "relative_difference", agg="max",
                         fmt="{:.1e}",
                         prose="largest dense-versus-matrix-free discrepancy across "
                               "all classes")
    for cl in CLASSES:
        c[f"dim_{cl}"] = L.table(f"E3D.dim.{cl}", DSP, "source_dimension", fmt="{:d}",
                                 where={"source_class": cl},
                                 prose=f"dimension of {cl}")
        c[f"op_{cl}"] = L.table(f"E3D.oprank.{cl}", DSP, "operational_rank",
                                agg="median", fmt="{:.0f}",
                                where={"source_class": cl,
                                       "arm": "RESOLVED_PHYSICAL"},
                                prose=f"median resolved operational rank on {cl}")
        c[f"smin_{cl}"] = L.table(f"E3D.sigma_min.{cl}", DSP, "sigma_min_positive",
                                  agg="median", fmt="{:.2e}",
                                  where={"source_class": cl,
                                         "arm": "RESOLVED_PHYSICAL"},
                                  prose=f"median resolved smallest positive singular "
                                        f"value on {cl}")
    ladder = ["| class | radial | azimuthal | temporal | dimension | "
              "resolved operational rank | as a fraction | sigma_min+ |",
              "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for cl in CLASSES:
        r = dsp[(dsp.source_class == cl) & (dsp.arm == "RESOLVED_PHYSICAL")]
        dim = int(r.source_dimension.iloc[0])
        ladder.append(f"| `{cl}` | {int(r.n_radial.iloc[0])} | "
                      f"{int(r.n_azimuthal.iloc[0])} | {int(r.n_temporal.iloc[0])} | "
                      f"{dim} | {r.operational_rank.median():.0f} | "
                      f"{r.operational_rank.median() / dim:.3f} | "
                      f"{r.sigma_min_positive.median():.2e} |")
    c["ladder"] = D.join(ladder)
    frac224 = float(dsp[(dsp.source_class == "C224")
                        & (dsp.arm == "RESOLVED_PHYSICAL")]
                    .eval("operational_rank / source_dimension").median())
    frac1056 = float(dsp[(dsp.source_class == "C1056_ST")
                         & (dsp.arm == "RESOLVED_PHYSICAL")]
                     .eval("operational_rank / source_dimension").median())
    c["fracfall"] = L.derived("E3D.rank_fraction.fall", 100 * (frac224 - frac1056),
                              f"{100 * (frac224 - frac1056):.1f}",
                              inputs=["E3D.oprank.C224", "E3D.oprank.C1056_ST",
                                      "E3D.dim.C224", "E3D.dim.C1056_ST"],
                              expression="100 * (oprank/dim at C224 - oprank/dim at "
                                         "C1056_ST), resolved arm, median over anchors",
                              prose="fall in the resolved operational-rank fraction "
                                    "across the class ladder, percentage points")
    dpiv = ddp[ddp.snr0 == REF].pivot_table(index=["geometry", "arm"],
                                            columns="source_class",
                                            values="T_rec_best_mode")
    spread = (dpiv.max(axis=1) - dpiv.min(axis=1)).drop(index="PAIRING_DESTROYED",
                                                        level="arm")
    step_v = float(e3cfz["common_age_grid"]["step_M"])
    ms_steps = float(spread.max() / step_v)
    c["dsteps"] = L.derived("E3D.depth.max_move_steps", ms_steps, f"{ms_steps:.0f}",
                            inputs=["grid.age_step"],
                            expression="max over physical and mechanism arms of "
                                       "(max_class T_rec - min_class T_rec) / age_step",
                            prose="largest depth change across the class ladder, in "
                                  "grid steps, excluding the nonphysical control")
    c["dmoved"] = L.derived("E3D.depth.rows_moved", int((spread > 0).sum()),
                            str(int((spread > 0).sum())),
                            inputs=["E3D.depth.max_move_steps"],
                            expression="count of physical anchor-arm rows whose depth "
                                       "differs across the class ladder",
                            prose="physical anchor-arm rows whose depth moves across "
                                  "the ladder")
    c["drows"] = L.derived("E3D.depth.rows", int(len(spread)), str(int(len(spread))),
                           inputs=["E3D.depth.rows_moved"],
                           expression="physical anchor-arm rows in the depth table",
                           prose="physical anchor-arm rows compared across the ladder")
    # Per-arm, per-class: how many anchors are deficient and by how much. A
    # single max over anchors would print a deficit for an arm that is full rank
    # at two of the three, which is a different finding.
    n_anch = int(dsp[(dsp.source_class == "C224")
                     & (dsp.arm == "RESOLVED_PHYSICAL")].shape[0])
    rank_md = ["| arm | " + " | ".join(
        f"`{cl}` ({int(dsp[dsp.source_class == cl].source_dimension.iloc[0])})"
        for cl in CLASSES) + " |", "|---|" + "---:|" * len(CLASSES)]
    for a in [x for x in ARMS if x != "TOTAL_FLUX"]:
        cells = []
        for cl in CLASSES:
            r = dsp[(dsp.source_class == cl) & (dsp.arm == a)]
            if r.empty:
                cells.append("–")
                continue
            bad = r[~r.full_column_rank]
            cells.append("full" if bad.empty else
                         f"**{len(bad)}/{n_anch}, −{int(bad.nullity.min())} to "
                         f"−{int(bad.nullity.max())}**"
                         if len(bad) > 1 or int(bad.nullity.min()) != int(bad.nullity.max())
                         else f"**{len(bad)}/{n_anch}, −{int(bad.nullity.max())}**")
        rank_md.append(f"| `{a}` | " + " | ".join(cells) + " |")
    c["e3d_rank_table"] = D.join(rank_md)

    # ---- controls --------------------------------------------------------------
    pd_worse = int(sum(1 for g in e3cfz["geometries"]
                       if pds[pds.geometry == g].kappa_positive.max()
                       < met[(met.geometry == g)
                             & (met.arm == "RESOLVED_PHYSICAL")].kappa_positive.iloc[0]))
    c["pdbeat"] = L.derived("control.pairing.beats_physical", pd_worse, str(pd_worse),
                            inputs=["grid.n_geometries", "control.seeds"],
                            expression="geometries where the worst of the frozen seeds "
                                       "has smaller kappa+ than RESOLVED_PHYSICAL",
                            prose="geometries where even the worst permutation seed is "
                                  "better conditioned than the physical operator")
    c["pd_op_med"] = L.table("control.pairing.oprank.median", PDS, "operational_rank",
                             agg="median", fmt="{:.0f}",
                             prose="median operational rank of the destroyed-pairing "
                                   "control over all seeds and geometries")
    c["pd_kappa_max"] = L.table("control.pairing.kappa.max", PDS, "kappa_positive",
                                agg="max", fmt="{:.2e}",
                                prose="worst conditioning of the destroyed-pairing "
                                      "control over all seeds and geometries")
    c["res_kappa_med"] = L.table("arm.resolved.kappa.median", MET, "kappa_positive",
                                 agg="median", fmt="{:.2e}",
                                 where={"arm": "RESOLVED_PHYSICAL"},
                                 prose="median conditioning of the physical resolved "
                                       "operator")
    cpiv = ctl.pivot_table(index=["geometry", "arm"], columns="support",
                           values="operational_rank")
    tpiv = ctl.pivot_table(index=["geometry", "arm"], columns="support",
                           values="oldest_detectable_age_probe_at_reference_snr")
    nmv = int((cpiv["COMMON_RADIAL_SUPPORT"] != cpiv["PRIMARY_GEOMETRY_DEPENDENT"]).sum())
    mmv = int((cpiv["COMMON_RADIAL_SUPPORT"] - cpiv["PRIMARY_GEOMETRY_DEPENDENT"]).abs().max())
    tsame = int((tpiv["COMMON_RADIAL_SUPPORT"] == tpiv["PRIMARY_GEOMETRY_DEPENDENT"]).sum())
    c["ctl_moved"] = L.derived("control.support.rank_moved", nmv, str(nmv),
                               inputs=["grid.n_geometries"],
                               expression="anchor-arm combinations whose operational "
                                          "rank differs between the two supports",
                               prose="anchor-arm combinations whose rank moves under "
                                     "the common-support control")
    c["ctl_max"] = L.derived("control.support.max_move", mmv, str(mmv),
                             inputs=["control.support.rank_moved"],
                             expression="max |oprank(common) - oprank(primary)|",
                             prose="largest rank move under the common-support control")
    c["ctl_same"] = L.derived("control.support.depth_same", tsame, str(tsame),
                              inputs=["control.support.rank_moved"],
                              expression="anchor-arm combinations with identical T_rec "
                                         "under both supports",
                              prose="anchor-arm combinations whose depth is unchanged "
                                    "under the common-support control")
    c["ctl_rows"] = L.derived("control.support.rows", int(len(cpiv)), str(len(cpiv)),
                              inputs=["control.support.rank_moved"],
                              expression="anchor-arm combinations in the control",
                              prose="anchor-arm combinations in the control")

    # ---- governance --------------------------------------------------------------
    c["nsup"] = L.json("governance.superseded", SUPS, "/counts/superseded", fmt="{:d}",
                       prose="artifacts marked SUPERSEDED_MEASUREMENT_MODEL_DEFECT")
    # The freeze is the provenance root and cannot hash itself, so these three
    # are literals sourced to it rather than lookups through it.
    c["ncanon"] = L.literal("governance.canonical", fz["n_canonical_artifacts"],
                            str(fz["n_canonical_artifacts"]), source=CANON,
                            prose="artifacts in the canonical freeze")
    c["tag"] = L.literal("governance.tag", fz["campaign_tag"], fz["campaign_tag"],
                         source=CANON, prose="campaign tag")
    c["commit"] = L.literal("governance.commit", fz["campaign_commit"],
                            fz["campaign_commit"], source=CANON,
                            prose="campaign commit")
    c["regsha"] = L.literal("governance.registry_sha256", reg.sha256, reg.sha256,
                            source="configs/paper1_experiment_registry_v0.2.yaml",
                            prose="registry digest")

    # deepest quantile
    qi = qnt.loc[qnt["Q_0.999_I"].idxmax()]
    c["qgeo"] = L.literal("quantile.deepest.geometry", str(qi.geometry),
                          str(qi.geometry), source=QNT,
                          prose="geometry carrying the deepest throughput-weighted "
                                "delay quantile")
    c["qval"] = L.table("quantile.deepest.value", QNT, "Q_0.999_I", agg="max",
                        fmt="{:.1f}", prose="deepest 99.9% throughput-weighted delay "
                                            "quantile on the grid, M")
    c["qraw"] = L.table("quantile.deepest.raw_max", QNT, "delay_max_M", agg="max",
                        fmt="{:.1f}",
                        prose="largest sampled maximum ray delay on the grid, M")

    # ---- R1 held-out main --------------------------------------------------
    # Every one of these is read from a sealed-bank table. The bank was hashed
    # before the operator existed and scored once.
    r1fz = json.loads((ROOT / R1FZ).read_text())
    IC, RES, DIR = "IN_CLASS_ID", "RESOLVED_PHYSICAL", "DIRECT_PHYSICAL"
    prim_w = {"primary": True, "snr0": REF, "estimator": "TSVD"}
    c["ref"] = L.literal("r1.reference_snr", REF, f"{REF:.0f}", source=R1FZ,
                         prose="reference SNR_0")
    c["r1_eps"] = L.literal("r1.epsilon", r1fz["primary"]["epsilon"],
                            f"{r1fz['primary']['epsilon']:.2f}", source=R1FZ,
                            prose="R1 primary tolerance")
    c["r1_q"] = L.literal("r1.quantile", r1fz["primary"]["quantile"],
                          f"{r1fz['primary']['quantile']:.2f}", source=R1FZ,
                          prose="R1 primary quantile")
    c["r1_thresh"] = L.literal("r1.threshold", r1fz["primary"]["threshold_M"],
                               f"{r1fz['primary']['threshold_M']:.0f}",
                               source=R1FZ, prose="R1 primary threshold, M")
    for tag, regime in (("ic", IC), ("ood", "IN_CLASS_OOD"),
                        ("ogid", "OFF_GRID_ID"), ("ogood", "OFF_GRID_OOD")):
        for arm_tag, arm in (("dir", DIR), ("res", RES)):
            c[f"r1_{tag}_{arm_tag}"] = L.table(
                f"r1.{tag}.{arm_tag}", R1D, "L_stable_anchor", fmt="{:.0f}",
                where={**prim_w, "regime": regime, "arm": arm},
                prose=f"anchored span, {regime}, {arm}, M")
    c["r1_delta"] = L.table("r1.delta.tsvd", R1B, "delta_L_level_M", fmt="{:.0f}",
                            where={"estimator": "TSVD", "regime": IC},
                            prose="resolved minus direct anchored span, TSVD, M")
    c["r1_delta_ridge"] = L.table("r1.delta.ridge", R1B, "delta_L_level_M",
                                  fmt="{:.0f}",
                                  where={"estimator": "RIDGE_IDENTITY", "regime": IC},
                                  prose="the same under ridge, M")
    c["r1_on_lo"] = L.table("r1.oldband.norm.ci_low", R1B,
                            "old_band_normalized_ci_low", fmt="{:.3f}",
                            where={"estimator": "TSVD", "regime": IC},
                            prose="lower bound of the old-band normalized "
                                  "error reduction")
    c["r1_on"] = L.table("r1.oldband.norm", R1B, "old_band_normalized_reduction",
                         fmt="{:.3f}", where={"estimator": "TSVD", "regime": IC},
                         prose="old-band normalized error reduction")
    c["r1_oa"] = L.table("r1.oldband.abs", R1B, "old_band_absolute_reduction",
                         fmt="{:.3f}", where={"estimator": "TSVD", "regime": IC},
                         prose="old-band absolute error reduction")
    c["r1_oa_lo"] = L.table("r1.oldband.abs.ci_low", R1B,
                            "old_band_absolute_ci_low", fmt="{:.3f}",
                            where={"estimator": "TSVD", "regime": IC},
                            prose="its lower bound")
    c["r1_nboot"] = L.literal("r1.bootstrap.n", r1fz["bootstrap"]["n_resamples"],
                              f"{r1fz['bootstrap']['n_resamples']:d}",
                              source=R1FZ, prose="bootstrap resamples")
    r1f = L.frame(R1F)
    r1fs = r1f[(r1f.estimator == "TSVD") & (r1f.snr0 == REF) & (r1f.regime == IC)]
    piv = r1fs.pivot_table(index="family", columns="arm", values="L_stable_anchor")
    n_meet = int(((piv[RES] - piv[DIR]) >= r1fz["primary"]["threshold_M"]).sum())
    c["r1_nfam"] = L.literal("r1.families.meeting", n_meet, str(n_meet),
                             source=R1F,
                             prose="prior-fit families reaching the threshold")
    c["r1_nfam_tot"] = L.literal("r1.families.total", len(piv), str(len(piv)),
                                 source=R1F, prose="prior-fit families")
    lw = {"regime": IC, "snr0": REF, "estimator": "TSVD"}
    c["r1_levfrac"] = L.table("r1.level.fraction", R1L, "level_fraction_of_truth",
                              fmt="{:.1%}", where={**lw, "arm": DIR},
                              prose="fraction of a truth's age-window norm that "
                                    "is its spatially constant part")
    for tag, arm in (("dir", DIR), ("res", RES)):
        c[f"r1_lev_{tag}"] = L.table(f"r1.level.error.{tag}", R1L,
                                     "error_level_normalized", fmt="{:.3f}",
                                     where={**lw, "arm": arm},
                                     prose=f"level error, {arm}")
        c[f"r1_str_{tag}"] = L.table(f"r1.structure.error.{tag}", R1L,
                                     "error_structure_normalized", fmt="{:.3f}",
                                     where={**lw, "arm": arm},
                                     prose=f"structure error, {arm}")
        c[f"r1_ostr_{tag}"] = L.table(f"r1.oldband.structure.{tag}", R1L,
                                      "old_band_error_structure_normalized",
                                      fmt="{:.3f}", where={**lw, "arm": arm},
                                      prose=f"old-band structure error, {arm}")
        c[f"r1_sub_{tag}"] = L.table(f"r1.subspace.{tag}", R1W,
                                     "error_in_reference_data_subspace",
                                     agg="median", fmt="{:.3f}",
                                     where={"regime": IC, "snr0": REF,
                                            "estimator": "TSVD", "arm": arm},
                                     prose=f"error inside the direct channel's "
                                           f"own data subspace, {arm}")
    r1dep = L.frame(R1D)
    stw = r1dep[r1dep.primary & (r1dep.regime == IC) & (r1dep.estimator == "TSVD")]

    def _onset(arm):
        q = stw[stw.arm == arm].sort_values("snr0")
        pos = q[q.L_stable_anchor_structure > 0]
        return ((float(pos.snr0.iloc[0]),
                 float(pos.L_stable_anchor_structure.iloc[0]))
                if len(pos) else (float("nan"), 0.0))

    on_d, sp_d = _onset(DIR)
    on_r, sp_r = _onset(RES)
    c["r1_onset"] = L.literal("r1.structure.onset", on_r, f"{on_r:.0f}",
                              source=R1D,
                              prose="SNR_0 at which nonzero age-local structure "
                                    "recovery first appears, both arms")
    c["r1_span_str_dir"] = L.literal("r1.structure.span.direct", sp_d,
                                     f"{sp_d:.0f}", source=R1D,
                                     prose="structural span at onset, direct, M")
    c["r1_span_str_res"] = L.literal("r1.structure.span.resolved", sp_r,
                                     f"{sp_r:.0f}", source=R1D,
                                     prose="structural span at onset, resolved, M")
    c["r1_ndir_dir"] = L.table("r1.subspace.dim.direct", R1W,
                               "n_data_directions", agg="median", fmt="{:.0f}",
                               where={"regime": IC, "snr0": REF,
                                      "estimator": "TSVD", "arm": DIR},
                               prose="dimension of the direct channel's data "
                                     "subspace")
    c["r1_ndir_res"] = L.table("r1.subspace.dim.resolved", R1W,
                               "n_data_directions", agg="median", fmt="{:.0f}",
                               where={"regime": IC, "snr0": REF,
                                      "estimator": "TSVD", "arm": RES},
                               prose="dimension of the resolved stack's data "
                                     "subspace")
    r1n = L.frame(R1N)
    sup = r1n[r1n.disposition == "SUPPORTED"]
    c["r1_nnull"] = L.count("r1.null.tested", R1N,
                            where={"disposition": "SUPPORTED"},
                            prose="null-pair controls scored")
    c["r1_nnull_over"] = L.literal("r1.null.exceeding",
                                   int(sup.exceeds_bayes.sum()),
                                   str(int(sup.exceeds_bayes.sum())), source=R1N,
                                   prose="null pairs above the Bayes bound")
    c["r1_sealed"] = L.literal("r1.sealed.commitment",
                               r1fz["sealed_bank"]["commitment_sha256"],
                               r1fz["sealed_bank"]["commitment_sha256"][:16],
                               source=R1FZ, prose="sealed-bank commitment digest")
    c["r1_nsealed"] = L.literal("r1.sealed.n", r1fz["sealed_bank"]["n_records"],
                                str(r1fz["sealed_bank"]["n_records"]),
                                source=R1FZ, prose="sealed main-test truths")

    body = manuscript(c, prov)
    (OUT / "PAPER_I.md").write_text(body)
    (OUT / "PAPER_I.html").write_text(page(TITLE, body))
    ledger = L.to_dict({
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "git_commit": prov.git_commit,
        "campaign_tag": fz["campaign_tag"],
        "campaign_commit": fz["campaign_commit"],
        "registry_sha256": reg.sha256,
        "manuscript": "artifacts/manuscript/PAPER_I.md",
        "rule": "every number in the manuscript is registered here; the verifier "
                "re-derives each one from the frozen bytes and checks that the "
                "rendered string appears in the manuscript",
    })
    (OUT / "CLAIM_LEDGER.json").write_text(json.dumps(ledger, indent=2) + "\n")
    print(f"wrote artifacts/manuscript/PAPER_I.md ({len(body.split())} words)")
    print(f"wrote artifacts/manuscript/PAPER_I.html")
    print(f"wrote artifacts/manuscript/CLAIM_LEDGER.json "
          f"({ledger['n_claims']} claims over {len(ledger['artifacts_cited'])} artifacts)")
    print(f"total {time.time() - t0:.0f}s")
    return 0


def manuscript(c: dict, prov) -> str:
    from phrt.manuscript.sections import assemble
    return assemble(c, prov, TITLE)


if __name__ == "__main__":
    raise SystemExit(main())
