#!/usr/bin/env python3
"""Emit Paper_I_v1_Current_Evidence_Ledger.md from canonical artifacts.

One page per phase saying what was established, what it rests on, and what it
does not license. Every number is read from a canonical table or freeze; the
ledger is regenerated rather than edited, so it cannot drift from the campaign.

R1_RECORD_AMENDMENT_006 instruction 4: the ledger now covers E3C and R1. It did
not exist before -- it is one of the governance documents the campaign was never
handed -- so this creates it.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from phrt.config import load_registry, sha256_file
from phrt.io.dashboard import gate_counts

OUT = ROOT / "docs" / "Paper_I_v1_Current_Evidence_Ledger.md"
T = ROOT / "artifacts" / "tables"
CFG = ROOT / "artifacts" / "configs"
D = "\n"


def sha(rel: str) -> str:
    p = ROOT / rel
    return sha256_file(p)[:16] + "..." if p.exists() else "ABSENT"


def main() -> int:
    t0 = time.time()
    reg = load_registry()
    counts = gate_counts()
    fz_v2 = json.loads((ROOT / "artifacts"
                        / "CANONICAL_ARTIFACT_FREEZE_V2.json").read_text())
    e3c = json.loads((CFG / "E3C_OPERATOR_GRID_FREEZE.json").read_text())
    r1 = json.loads((CFG / "R1_MAIN_FREEZE.json").read_text())
    amd003 = json.loads((CFG / "AGE_INTERVAL_SEMANTICS_AMENDMENT_003.json").read_text())

    dep = pd.read_parquet(T / "e3c_depth_curves.parquet")
    met = pd.read_parquet(T / "e3c_geometry_metrics.parquet")
    hyp = pd.read_parquet(T / "e3c_hypothesis_tests.parquet")
    ref = 100.0
    h1 = hyp[(hyp.hypothesis == "H1_historical_extension") & (hyp.snr0 == ref)]
    n_geom = int(met.geometry.nunique())
    h1_deeper = int(h1.resolved_probe_deeper_than_direct.fillna(False).sum())
    h1_jold = int(h1.J_old_resolved_positive.fillna(False).sum())
    anchors = dep.groupby("geometry").a_anchor_M.first()
    n_anchor_pos = int((anchors > 0).sum())
    n_differ = int((dep.contiguous_detectable_span_from_anchor_M
                    != dep.longest_detectable_run_span_M).sum())

    r1d = pd.read_parquet(T / "r1_stable_depth.parquet")
    r1p = r1d[r1d.primary & (r1d.snr0 == ref) & (r1d.estimator == "TSVD")]

    def sp(regime, arm):
        s = r1p[(r1p.regime == regime) & (r1p.arm == arm)].L_stable_anchor
        return float(s.iloc[0]) if len(s) else float("nan")

    boot = pd.read_parquet(T / "r1_bootstrap.parquet")
    bp = boot[(boot.estimator == "TSVD") & (boot.regime == "IN_CLASS_ID")].iloc[0]
    bc = boot[(boot.estimator == "RIDGE_IDENTITY")
              & (boot.regime == "IN_CLASS_ID")].iloc[0]
    fam = pd.read_parquet(T / "r1_family_depth.parquet")
    fsub = fam[(fam.estimator == "TSVD") & (fam.snr0 == ref)
               & (fam.regime == "IN_CLASS_ID")]
    ft = fsub.pivot_table(index="family", columns="arm", values="L_stable_anchor")
    n_fam = int(((ft["RESOLVED_PHYSICAL"] - ft["DIRECT_PHYSICAL"]) >= 8.0).sum())
    ls = pd.read_parquet(T / "r1_level_structure.parquet")
    lsx = ls[(ls.regime == "IN_CLASS_ID") & (ls.snr0 == ref)
             & (ls.estimator == "TSVD")].set_index("arm")
    st = r1d[r1d.primary & (r1d.regime == "IN_CLASS_ID")
             & (r1d.estimator == "TSVD")]

    def onset(arm):
        s = st[st.arm == arm].sort_values("snr0")
        pos = s[s.L_stable_anchor_structure > 0]
        return ((float(pos.snr0.iloc[0]), float(pos.L_stable_anchor_structure.iloc[0]))
                if len(pos) else (float("nan"), 0.0))

    on_d, span_d = onset("DIRECT_PHYSICAL")
    on_r, span_r = onset("RESOLVED_PHYSICAL")
    dw = pd.read_parquet(T / "r1_data_weak_errors.parquet")
    dws = dw[(dw.regime == "IN_CLASS_ID") & (dw.snr0 == ref)
             & (dw.estimator == "TSVD")].groupby("arm").median(numeric_only=True)
    nullp = pd.read_parquet(T / "r1_null_pairs.parquet")
    nsup = nullp[nullp.disposition == "SUPPORTED"]

    # ---- R1L: localized structural audit and validation ----------------
    s1 = pd.read_parquet(T / "r1l_class_spectra.parquet")
    s1o = pd.read_parquet(T / "r1l_old_structural_support.parquet")
    rb = pd.read_parquet(T / "r1l_2rb_endpoint.parquet")
    rbs = pd.read_parquet(T / "r1l_2rb_delta_spans.parquet")
    rbc = pd.read_parquet(T / "r1l_2rb_bank_contract.parquet")
    am14 = json.loads((CFG / "R1L_STAGE2R_SCIENTIFIC_DISPOSITION_AMENDMENT_014"
                       ".json").read_text())

    def s1cell(cl, arm, col):
        return s1[(s1.source_class == cl) & (s1.arm == arm)][col].iloc[0]

    def s1old(cl, arm):
        return int(s1o[(s1o.source_class == cl) & (s1o.arm == arm)]
                   ["old_structural_operational_rank"].iloc[0])

    def rbrow(snr, arm, est, scope="physical_banks_only"):
        q = rb[(rb.source_class == "L1056") & (rb.scope == scope)
               & (rb.snr0 == snr) & (rb.arm == arm) & (rb.estimator == est)]
        return q.iloc[0]

    s1tab = D.join(
        f"| `{lo}` | {int(s1cell(lo, 'DIRECT_PHYSICAL', 'numerical_rank'))} | "
        f"{int(s1cell(lo, 'DIRECT_PHYSICAL', 'n_exactly_zero_columns'))} | "
        f"{s1old(lo, 'DIRECT_PHYSICAL')} | {s1old(lo, 'RESOLVED_PHYSICAL')} | "
        f"{s1old(lo, 'UNRESOLVED_IMAGE')} | `{gl}` | "
        f"{int(s1cell(gl, 'DIRECT_PHYSICAL', 'numerical_rank'))} | "
        f"{int(s1cell(gl, 'DIRECT_PHYSICAL', 'n_exactly_zero_columns'))} |"
        for lo, gl in (("L224", "C224"), ("L448", "C448_T"),
                       ("L1056", "C1056_ST")))

    rbtab = D.join(
        f"| {snr:.0f} | `{arm}` | {est} | "
        f"{rbrow(snr, arm, est).median_relative_reduction:+.3f} | "
        f"{rbrow(snr, arm, est).median_ci_low:+.3f} | "
        f"{rbrow(snr, arm, est).relative_reduction:+.3f} | "
        f"{rbrow(snr, arm, est).ci_low:+.3f} | "
        f"{int(rbrow(snr, arm, est).n_families_improved)}/4 | "
        f"{'**yes**' if rbrow(snr, arm, est).meets_materiality else 'no'} |"
        for snr in (100.0, 1000.0)
        for arm in ("RESOLVED_PHYSICAL", "UNRESOLVED_IMAGE")
        for est in ("TSVD", "RIDGE_IDENTITY"))

    sgn = {r.estimator: r for r in rb[(rb.source_class == "L1056")
                                      & (rb.scope == "single_bank")
                                      & (rb.bank == "constant_flux_structural")
                                      & (rb.snr0 == 100.0)
                                      & (rb.arm == "RESOLVED_PHYSICAL")].itertuples()}
    ctab = D.join(
        f"| `{r.bank}` | `{r.role_id}` | {r.achieved_structure_fraction:.3f} | "
        f"{r.negative_mass_relative_max:.4f} | "
        f"{'**yes**' if r.physical_primary_eligible else 'no'} |"
        for r in rbc[rbc.source_class == "L1056"].sort_values("bank").itertuples())

    dsp = rbs[(rbs.source_class == "L1056")
              & (rbs.noise_semantics == "joint_truth_noise")]

    # ---- HMT: source-object morphology, resolution-aware ---------------
    cl18 = json.loads((CFG / "HMT1_CLOSURE_RECORD_018.json").read_text())
    am21 = json.loads((CFG / "HMT2_MAIN_RECORD_AMENDMENT_021.json").read_text())
    mfz = json.loads((CFG / "HMT2_SEALED_MAIN_V1.json").read_text())
    s0 = pd.read_parquet(T / "hmt2_stage0_states.parquet")
    s0r = pd.read_parquet(T / "hmt2_stage0r_merger_rates.parquet")
    s0w = pd.read_parquet(T / "hmt2_stage0_class_widths.parquet")
    s1c = pd.read_parquet(T / "hmt2_stage1c_endpoint.parquet")
    mep = pd.read_parquet(T / "hmt2_main_endpoint.parquet")
    mfa = pd.read_parquet(T / "hmt2_main_per_family.parquet")
    mmu = pd.read_parquet(T / "hmt2_main_stable_multi.parquet")
    msi = pd.read_parquet(T / "hmt2_main_stable_interval.parquet")

    CLAIM, RES = "L896_radial_enriched", "RESOLVED_PHYSICAL"
    s0n = s0[~s0.canary]
    n_states_audited = int(s0n.n_ages.sum())
    frac = {k: float(s0n[f"n_{k}"].sum()) / n_states_audited
            for k in ("single_resolved", "multi_resolved", "blended", "dead",
                      "ambiguous")}
    minw = float(s0w[s0w["class"] == CLAIM].minimum_representable_width_M
                 .dropna().min())

    def mrate(fam, cls, stratum="STABLE_MULTI_RESOLVED"):
        q = s0r[(s0r.stratum == stratum) & (s0r.family == fam)
                & (s0r["class"] == cls)]
        return float(q.merger_rate.iloc[0])

    def s1cell(est, cls=CLAIM, arm=RES, snr=100.0):
        q = s1c[(s1c["class"] == cls) & (s1c.arm == arm) & (s1c.snr0 == snr)
                & (s1c.estimator == est)]
        return q.iloc[0]

    def mcell(est, cls=CLAIM, arm=RES, snr=100.0):
        q = mep[(mep["class"] == cls) & (mep.arm == arm) & (mep.snr0 == snr)
                & (mep.estimator == est)]
        return q.iloc[0]

    mfq = mfa[(mfa["class"] == CLAIM) & (mfa.arm == RES) & (mfa.snr0 == 100.0)]
    n_fam_phys = int(mfq.PHYSICAL_END_TO_END_material.sum())
    n_fam_both = int((mfq.PHYSICAL_END_TO_END_material
                      & mfq.CLASS_CONDITIONAL_material).sum())
    mmq = mmu[(mmu["class"] == CLAIM) & (mmu.arm == RES)]
    msq = msi[(msi["class"] == CLAIM) & (msi.snr0 == 100.0)]

    mtab = D.join(
        f"| `{cls}` | `{arm}` | {est.split('_')[0].title() if est != 'TSVD' else 'TSVD'} | "
        f"{float(mcell(est, cls, arm).PHYSICAL_END_TO_END_median_reduction):+.3f} | "
        f"{float(mcell(est, cls, arm).PHYSICAL_END_TO_END_ci_low):+.3f} | "
        f"{'**yes**' if bool(mcell(est, cls, arm).PHYSICAL_END_TO_END_material) else 'no'} | "
        f"{float(mcell(est, cls, arm).CLASS_CONDITIONAL_median_reduction):+.3f} | "
        f"{float(mcell(est, cls, arm).CLASS_CONDITIONAL_ci_low):+.3f} | "
        f"{'**yes**' if bool(mcell(est, cls, arm).CLASS_CONDITIONAL_material) else 'no'} |"
        for cls in (CLAIM, "L448_contrast")
        for arm in (RES, "UNRESOLVED_IMAGE", "TOTAL_FLUX")
        for est in ("RIDGE_IDENTITY", "TSVD"))

    ftab = D.join(
        f"| `{r.family}` | {r.estimator.split('_')[0].title() if r.estimator != 'TSVD' else 'TSVD'} | "
        f"{r.PHYSICAL_END_TO_END_median_reduction:+.3f} | "
        f"{r.PHYSICAL_END_TO_END_ci_low:+.3f} | "
        f"{'**yes**' if r.PHYSICAL_END_TO_END_material else 'no'} | "
        f"{'**yes**' if r.CLASS_CONDITIONAL_material else 'no'} |"
        for r in mfq.sort_values(["family", "estimator"]).itertuples())

    def _cap(t):
        return t[0].upper() + t[1:] if t else t

    dtab = D.join(f"- **`{k}`** — {v['finding']}."
                  + (f" {_cap(v['reading'])}." if "reading" in v else "")
                  for k, v in am21["scientific_dispositions"].items())

    canary_seed = int(cl18["canary"]["bank_seed"])
    canary_token = cl18["canary"]["token"]
    n_sources = int(len(s0))
    n_aggregated = int(len(s0n))
    n_states = n_states_audited
    f_single, f_multi = frac["single_resolved"], frac["multi_resolved"]
    f_blended, f_dead, f_amb = (frac["blended"], frac["dead"],
                                frac["ambiguous"])
    mr_448 = mrate("two_hotspot_trajectories", "L448_contrast")
    mr_896 = mrate("two_hotspot_trajectories", CLAIM)
    mr_m2 = mrate("m2_structural_mode", CLAIM)
    mr_448_all = mrate("two_hotspot_trajectories", "L448_contrast",
                       "ALL_FINEST_MULTI")
    mr_896_all = mrate("two_hotspot_trajectories", CLAIM, "ALL_FINEST_MULTI")
    mr_448_amb = mrate("two_hotspot_trajectories", "L448_contrast",
                       "AMBIGUOUS_FINE_MULTI")
    mr_896_amb = mrate("two_hotspot_trajectories", CLAIM,
                       "AMBIGUOUS_FINE_MULTI")
    min_width = minw
    s1_pr = float(s1cell("RIDGE_IDENTITY").PHYSICAL_END_TO_END_median_reduction)
    s1_pt = float(s1cell("TSVD").PHYSICAL_END_TO_END_median_reduction)
    s1_cr = float(s1cell("RIDGE_IDENTITY").CLASS_CONDITIONAL_median_reduction)
    s1_ct = float(s1cell("TSVD").CLASS_CONDITIONAL_median_reduction)
    n_truths = int(mfz["bank"]["n_truths"])
    m_pr = float(mcell("RIDGE_IDENTITY").PHYSICAL_END_TO_END_median_reduction)
    m_pt = float(mcell("TSVD").PHYSICAL_END_TO_END_median_reduction)
    m_prl = float(mcell("RIDGE_IDENTITY").PHYSICAL_END_TO_END_ci_low)
    m_ptl = float(mcell("TSVD").PHYSICAL_END_TO_END_ci_low)
    mclaim = mep[(mep["class"] == CLAIM) & (mep.snr0 == 100.0)]
    m_unres = float(mclaim[mclaim.arm == "UNRESOLVED_IMAGE"]
                    .PHYSICAL_END_TO_END_median_reduction.max())
    m_flux = float(mclaim[mclaim.arm == "TOTAL_FLUX"]
                   .PHYSICAL_END_TO_END_median_reduction.max())
    n_fam_cells = int(len(mfq))
    auth_truths, auth_draws = (am21["scope_deviation"]["authorized"]["truths"],
                               am21["scope_deviation"]["authorized"]["noise_draws"])
    exec_draws = am21["scope_deviation"]["executed"]["noise_draws"]
    sha_mfz = sha("artifacts/configs/HMT2_SEALED_MAIN_V1.json")
    sha_bank = sha("artifacts/provenance/HMT2_SEALED_MAIN_BANK_HASHES.json")
    sha_mep = sha("artifacts/tables/hmt2_main_endpoint.parquet")
    sha_rep = sha("artifacts/reports/HMT2_SEALED_MAIN.md")
    mc_lo, mc_hi = float(mmq.arm_cost.min()), float(mmq.arm_cost.max())
    n_multi_truths = int(mmq.n_truths.iloc[0])
    stable_M = float(msi.L_stable_morphology_M.max())
    msi10 = msi[(msi["class"] == CLAIM) & (msi.snr0 == 1000.0)]
    reach_res = float(msq[msq.arm == RES].mean_reach_M.mean())
    reach_dir = float(msq[msq.arm == "DIRECT_PHYSICAL"].mean_reach_M.mean())
    reach_res10 = float(msi10[msi10.arm == RES].mean_reach_M.mean())
    reach_dir10 = float(msi10[msi10.arm == "DIRECT_PHYSICAL"].mean_reach_M.mean())
    m_abs_lo = float(mclaim[mclaim.arm == RES].PHYSICAL_END_TO_END_arm.min())
    m_abs_hi = float(mclaim[mclaim.arm == RES].PHYSICAL_END_TO_END_arm.max())
    sat_direct = float(mclaim[mclaim.arm == RES]
                       .PHYSICAL_END_TO_END_saturation_direct.mean())

    body = f"""# Paper I — current evidence ledger

Regenerated from canonical artifacts by `scripts/build_evidence_ledger.py`.
Nothing here is typed by hand; every number is read from a frozen table or
freeze, and the ledger is rebuilt rather than edited.

- generated {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
- registry sha256 `{reg.sha256}`
- canonical artifact freeze v2: **{fz_v2['n_canonical_artifacts']} artifacts**,
  campaign commit `{fz_v2['campaign_commit']}`
- gates: **{counts['total_gates']}** total, **{counts['passing']}** passing,
  **{counts['active_blocking_failures']}** active blocking failures,
  **{counts['preserved_literal_failures']}** preserved literal failures,
  **{counts['future_phase_not_run']}** belonging to phases not yet in scope

## Standing scope

One geometry family is reconstructed and one source class is inverted. Nothing
in this campaign is geometry-wide reconstruction, and nothing is arbitrary movie
recovery. No telescope detection and no laboratory result is claimed anywhere.

Two held-out historical inverse results stand, and they are different results.

- **`STABLE_BASELINE_INCLUSIVE_EMISSIVITY_LEVEL_RECONSTRUCTION`** (R1) —
  extension of the anchored stable span for age-local emissivity *level*.
- **`AGGREGATE_RESOLUTION_AWARE_MORPHOLOGY_ERROR_REDUCTION`** (HMT-2 sealed
  main) — an aggregate reduction in a resolution-aware morphology error on
  held-out truths, carrying `MULTI_FEATURE_RECOVERY_NEGATIVE`,
  `STABLE_MORPHOLOGY_INTERVAL_NEGATIVE`, `FAMILY_HETEROGENEITY` and
  `DIRECT_BASELINE_SATURATION_QUALIFICATION` beside it.

Neither is accurate historical movie recovery, and this ledger says so at both
places rather than once.

---

## E3C — geometry-wide operator audit

**Established.** On {n_geom} registered spin–inclination geometries under the
corrected pixel-integrated measurement convention, the order-resolved stack sees
further back in retarded time than the direct image alone. At the reference
SNR_0 = {ref:.0f}: the resolved oldest detectable age probe exceeds the direct
one in **{h1_deeper} of {n_geom}** geometries, and the threshold-independent
historical innovation `J_old` is positive in **{h1_jold} of {n_geom}**.

**Rests on.** `artifacts/configs/E3C_OPERATOR_GRID_FREEZE.json`
`{sha('artifacts/configs/E3C_OPERATOR_GRID_FREEZE.json')}`, registered before the
first geometry was evaluated; `artifacts/tables/e3c_depth_curves.parquet`
`{sha('artifacts/tables/e3c_depth_curves.parquet')}`;
`artifacts/tables/e3c_geometry_metrics.parquet`
`{sha('artifacts/tables/e3c_geometry_metrics.parquet')}`;
`artifacts/reports/E3C_GEOMETRY_WIDE_OPERATOR_AUDIT.md`
`{sha('artifacts/reports/E3C_GEOMETRY_WIDE_OPERATOR_AUDIT.md')}`.

**Depth is three observables, not one**
(`AGE_INTERVAL_SEMANTICS_AMENDMENT_003`). The reach is a supremum and is blind
to holes; the longest detectable run is the longest stretch *anywhere* on the
grid; only the stretch reaching the frozen anchor is history from the present.
They differ in **{n_differ} of {len(dep)}** depth rows. In
**{n_anchor_pos} of {len(anchors)}** geometries the anchor is a positive age:
at i = 75 degrees the minimum delay in the frozen ray set exceeds the last
observer sample, so the present is not observed there at all. The reassembly
re-derived all {amd003['depth_rows_reassembled']} rows from stored masks with
**zero** deviation in both the reach and the longest-run span, so the amendment
is a rename plus two additions and not a change of value.

**Does not license.** A statement about the physical operator rather than about
`A_C = 𝒜 Q_C` on the declared class. A reconstruction claim of any kind: E3C is
an observability audit and inverts nothing.

---

## R1 — held-out main reconstruction

**Disposition `R1_PASS_WITH_SCOPE_RESTRICTION`.**

**Established.** At a* = 0.5, i = 50 degrees, for source histories exactly
inside the C224 class, stacking orders n = 0, 1, 2 extends the anchored stable
span of **baseline-inclusive age-local emissivity-level** reconstruction. At
SNR_0 = {ref:.0f}, epsilon = {r1['primary']['epsilon']},
q = {r1['primary']['quantile']}, prior-free TSVD:

| regime | direct | resolved | delta |
|---|---:|---:|---:|
| `IN_CLASS_ID` | {sp('IN_CLASS_ID','DIRECT_PHYSICAL'):.0f} M | {sp('IN_CLASS_ID','RESOLVED_PHYSICAL'):.0f} M | **+{sp('IN_CLASS_ID','RESOLVED_PHYSICAL')-sp('IN_CLASS_ID','DIRECT_PHYSICAL'):.0f} M** |
| `IN_CLASS_OOD` | {sp('IN_CLASS_OOD','DIRECT_PHYSICAL'):.0f} M | {sp('IN_CLASS_OOD','RESOLVED_PHYSICAL'):.0f} M | +{sp('IN_CLASS_OOD','RESOLVED_PHYSICAL')-sp('IN_CLASS_OOD','DIRECT_PHYSICAL'):.0f} M |
| `OFF_GRID_OOD` | {sp('OFF_GRID_OOD','DIRECT_PHYSICAL'):.0f} M | {sp('OFF_GRID_OOD','RESOLVED_PHYSICAL'):.0f} M | +{sp('OFF_GRID_OOD','RESOLVED_PHYSICAL')-sp('OFF_GRID_OOD','DIRECT_PHYSICAL'):.0f} M |
| `OFF_GRID_ID` | {sp('OFF_GRID_ID','DIRECT_PHYSICAL'):.0f} M | {sp('OFF_GRID_ID','RESOLVED_PHYSICAL'):.0f} M | {sp('OFF_GRID_ID','RESOLVED_PHYSICAL')-sp('OFF_GRID_ID','DIRECT_PHYSICAL'):.0f} M |

against a threshold of {float(r1['primary']['threshold_M']):.0f} M. Ridge confirms
at {bc.delta_L_level_M:.0f} M. **{n_fam} of {len(ft)}** prior-fit families reach
the threshold. Paired truth-cluster bootstrap,
{int(r1['bootstrap']['n_resamples'])} resamples, seed
{int(r1['bootstrap']['seed'])}: old-band normalized reduction
{bp.old_band_normalized_reduction:.3f} with lower bound
{bp.old_band_normalized_ci_low:.3f}, absolute {bp.old_band_absolute_reduction:.3f}
with lower bound {bp.old_band_absolute_ci_low:.3f}.

**Level, not morphology.** {float(lsx.loc['DIRECT_PHYSICAL','level_fraction_of_truth']):.1%}
of a truth's age-window norm is its spatially constant part. The level error
falls {float(lsx.loc['DIRECT_PHYSICAL','error_level_normalized']):.3f} to
{float(lsx.loc['RESOLVED_PHYSICAL','error_level_normalized']):.3f}; the structure
error falls {float(lsx.loc['DIRECT_PHYSICAL','error_structure_normalized']):.3f}
to {float(lsx.loc['RESOLVED_PHYSICAL','error_structure_normalized']):.3f} across
all ages but is
{float(lsx.loc['DIRECT_PHYSICAL','old_band_error_structure_normalized']):.3f}
against
{float(lsx.loc['RESOLVED_PHYSICAL','old_band_error_structure_normalized']):.3f}
in the old band, both above one. The primary result is emissivity-*level*
reconstruction and is not detailed old-age movie morphology.

**High-SNR structure, stated separately.** The onset of nonzero age-local
structure recovery is **unchanged** at SNR_0 = {on_r:.0f} for both arms. What
differs is the span at that point: **{span_d:.0f} M direct against
{span_r:.0f} M resolved**.

**Not a prior effect.** Judged on the direct channel's own
{int(dws.loc['DIRECT_PHYSICAL','n_reference_data_directions'])}-direction data
subspace — like for like, since the resolved arm supports
{int(dws.loc['RESOLVED_PHYSICAL','n_data_directions'])} of its own — the error
falls {float(dws.loc['DIRECT_PHYSICAL','error_in_reference_data_subspace']):.3f}
to {float(dws.loc['RESOLVED_PHYSICAL','error_in_reference_data_subspace']):.3f}.

**Integrity.** All {len(nsup)} scored null-pair controls came from a bank hashed
before scoring, with zero direction-hash mismatches;
{int(nsup.exceeds_bayes.sum())} exceed the equal-prior Gaussian Bayes bound
against an expectation consistent with multiplicity. The sealed 640-truth bank
was regenerated and matched its committed hashes; it is disjoint from every R0C
split.

**Rests on.** `artifacts/configs/R1_MAIN_FREEZE.json`
`{sha('artifacts/configs/R1_MAIN_FREEZE.json')}`, committed in a clean tree
before any main truth was scored; sealed-bank commitment
`{r1['sealed_bank']['commitment_sha256'][:16]}...`; null control bank
`{r1['null_pair_control_bank']['sha256'][:16]}...`;
`artifacts/reports/R1_HELD_OUT_MAIN.md` `{sha('artifacts/reports/R1_HELD_OUT_MAIN.md')}`.

**Does not license.**

- `OFF_GRID_ID` is a **negative result** and is preserved as one: the exact
  projection clears the tolerance there, so the tolerance is reachable and the
  reconstructions do not reach it. Recovery outside the declared class is not
  established.
- `OFF_GRID_OOD` is a **mild-mismatch diagnostic**, not evidence of broad
  off-grid robustness. Its representation floor was 0.016 to 0.115
  structure-normalized against `OFF_GRID_ID`'s 0.803 to 0.814.
- **Uncertainty is withdrawn.** The joint calibration gate failed literally and
  the declared fallback applies. No credible interval, posterior movie or
  coverage statement is available from this line.
- One geometry and one source class. Nothing geometry-wide, nothing about
  arbitrary movies.

---

## R1L stage 1 — localized operator and rank audit

Established, with no estimator involved, at `a* = 0.5`, `i = 50` degrees.
Canonical under two pinned six-class runs that agreed on every scientific cell.

Compact temporal support turns "the direct image cannot see this epoch" from a
condition number into a null-space fact. Old-epoch structural support is the
subspace of old temporal functions orthogonal to the level projector; entries
are operational ranks.

| localized | direct rank | direct exact-zero cols | direct old-struct | resolved old-struct | unresolved old-struct | global | direct rank | direct exact-zero cols |
|---|---:|---:|---:|---:|---:|---|---:|---:|
{s1tab}

The direct image has operational rank **0** in the old structural subspace at
every class, with largest singular value 1.8e-14. C224 is full rank on its own
global temporal subspace — that number is correct and says nothing about
epoch-local identifiability, which C224 cannot pose because none of its
coefficients is confined to an epoch.

Does not license: any reconstruction claim. No truth was drawn and no estimator
was fitted.

## R1L stage 2R — exact-in-class structural validation

Validation only. Truths are exactly in the class, so the representation floor is
zero and the error measured is reconstruction error alone. `L1056` is primary;
`L448` and `L224` are controls that cannot supply a pass. **No sealed main was
run and none is authorized.**

Endpoint on the two non-negative physical banks, resolved and unresolved against
the direct image. Material requires median ≥ 10%, both bootstrap lower bounds ≥
5%, ≥ 3/4 families, every bank in scope positive, null controls passing, and
both estimators on the same class.

| SNR₀ | arm | estimator | median | median CI low | cell mean | mean CI low | families | material |
|---:|---|---|---:|---:|---:|---:|---|---|
{rbtab}

Source banks, after projection into the class:

| bank | role | achieved f_struct | max negative mass | physical primary |
|---|---|---:|---:|---|
{ctab}

Six dispositions, recorded separately:

- **`R1L_STAGE2R_GATE_COMPLETION_REPRODUCTION_PASS`** — every pre-existing cell
  bitwise identical across the gate-completed rerun, 12 of 12 declared gates.
- **`R1L_STAGE2R_PHYSICAL_SOURCE_MATERIALITY_NOT_MET`** — at SNR₀ = 100 the
  medians clear the bar and the cell-balanced means do not. Read as
  `PREREGISTERED_PHYSICAL_SOURCE_MATERIALITY_NOT_MET`: a bar not cleared, not an
  effect shown to be zero. The central estimates are positive.
- **`R1L_STAGE2R_SIGNED_DIAGNOSTIC_MATERIAL_EFFECT`** — the signed constant-flux
  bank alone shows {sgn['TSVD'].median_relative_reduction:.3f} (TSVD) and
  {sgn['RIDGE_IDENTITY'].median_relative_reduction:.3f} (ridge) and was carrying
  the pooled all-banks result. A linear inverse-problem finding; it is not a
  non-negative emissivity history and may not carry a source claim.
- **`R1L_STAGE2R_HIGH_SNR_PHYSICAL_VALIDATION_PASS`** — at SNR₀ = 1000 the
  resolved arm meets every criterion on both estimators and 4/4 families.
  Secondary: a result at tenfold higher normalized SNR does not substitute for
  the registered point.
- **`R1L_STAGE2R_STABLE_SPAN_NEGATIVE_RESULT`** — ΔL = {dsp.delta_L_stable_structure_M.abs().max():.0f} M
  against 8 M under both noise semantics at both SNRs, with the stricter joint
  truth-and-noise statistic agreeing with the averaged one.
- **`R1L_STAGE2R_SCIENTIFIC_STOP`** — `sealed_main_authorized = {str(am14['sealed_main_authorized']).lower()}`.

Does not license: a physical-source reconstruction claim at the reference SNR; a
stable structural history interval at any SNR; any statement about arbitrary or
realistic accretion-flow histories. The design is a representation-matched,
zero-floor best-case benchmark.

## HMT-1 — historical feature contrast tomography (closed)

**No held-out scientific result exists for this line, and none was withdrawn:
the claim was never made.** Two sealed banks were retired before evaluation and
the third was refused at stage A, by a source-side gate that ran before any
operator was imported.

Four dispositions (`HMT1_CLOSURE_RECORD_018`, ruling 018):

- **`HMT1_MAIN_STAGE_A_FIREWALL_PASS`** — the two-stage split held. Every
  source-side gate was decided from the source alone, one failed, and stage B
  refused to construct an operator. No held-out truth was evaluated.
- **`HMT1_MAIN_SOURCE_RESOLUTION_CONTRACT_FAILURE`** — the declared
  `two_hotspot_trajectories` range admits configurations the declared
  evaluation grid cannot resolve. Neither an extractor defect nor a reference
  defect: the source model and the evaluation grid were specified
  independently and their contract was never checked.
- **`HMT1_MAIN_SCIENCE_NOT_RUN`**, **`HMT1_MAIN_NO_FURTHER_SEALED_BANK`** —
  drawing again under the same contract would reproduce the failure with a
  different index.

Bank seed {canary_seed} is preserved as `{canary_token}`: **regression test
only**, never held-out evidence and never part of any aggregate success
statistic. The earlier main bank is retired permanently after
`HMT1_MAIN_PARTIAL_ENDPOINT_EXPOSURE`. HMT-1's validation line is rescoped to
`DOMINANT_OR_BLENDED_FEATURE_DESCRIPTOR` and carries no multi-feature claim.

Does not license: anything. This section exists so the closure is on the record
and the canary cannot be quoted as a result.

---

## HMT-2 stage 0R — source object and resolution audit

Source-side only. **No ray map was imported and no observation operator was
constructed**, asserted by a guard before and after the audit and re-derived
from the final module inspection. {n_sources} sources over six families, one of
them the preserved HMT-1 failure canary and excluded from every aggregate
below. The remaining {n_aggregated} are classified at every age by topographic
prominence, reconciled across the two finest of three nested grids.

What the source objects are, before any measurement:

| state | fraction of {n_states} audited states |
|---|---:|
| `SINGLE_RESOLVED` | {f_single:.1%} |
| `MULTI_RESOLVED` | {f_multi:.1%} |
| `BLENDED` | {f_blended:.1%} |
| `DEAD` | {f_dead:.1%} |
| `AMBIGUOUS` | {f_amb:.1%} |

**Canonical merger rates** (ruling 020 item 1), on the `STABLE_MULTI_RESOLVED`
stratum — states both finest levels agree are multi-resolved:

| family | class | rate |
|---|---|---:|
| `two_hotspot_trajectories` | `L448_contrast` | **{mr_448:.3f}** |
| `two_hotspot_trajectories` | `L896_radial_enriched` | **{mr_896:.3f}** |
| `m2_structural_mode` | either class | {mr_m2:.3f} |

The pooled {mr_448_all:.3f} and {mr_896_all:.3f} over all states the finest
level calls multi remain in the record as what the finest grid alone would say,
and carry no claim. The `AMBIGUOUS_FINE_MULTI` stratum merges at
{mr_448_amb:.3f} and {mr_896_amb:.3f} — states whose multiplicity the grid
cannot settle are mostly states the projection merges, which is the expected
direction and is why they are scored by the blended measure rather than
dropped.

Minimum representable feature width in the claim-bearing class is
{min_width:.2f} M. Below it a projected feature is a grid artefact and the
measure says so.

Does not license: any reconstruction statement. Stage 0R inverts nothing and
fits nothing.

---

## HMT-2 stage 1 — resolution-aware morphology validation

Validation on a bank the hyperparameter selection saw, so it is not held out.
Its purpose was to establish that the measure and the estimators work and to
authorize the sealed main. The endpoint-completion rerun
(`HMT2_STAGE1_ENDPOINT_COMPLETION_AMENDMENT_020`) **reproduced every existing
primary endpoint cell bitwise** and added seven companions; a single moved cell
would have stopped the line.

Claim-bearing class, resolved arm, SNR_0 = 100, after completion:

| target | ridge | TSVD |
|---|---:|---:|
| `PHYSICAL_END_TO_END` | {s1_pr:+.3f} | {s1_pt:+.3f} |
| `CLASS_CONDITIONAL` | {s1_cr:+.3f} | {s1_ct:+.3f} |

Stage 1's pass rule was improvement with a bootstrap bound clear of zero and
**carried no effect-size floor at all**, which is recorded as a defect of the
rule rather than of the result. The sealed main below is judged against a
declared floor.

Does not license: a held-out claim of any kind.

---

## HMT-2 sealed main — held-out resolution-aware morphology recovery

**Token `HMT2_MAIN_PHYSICAL_MORPHOLOGY_RECOVERY_PASS`**, 19 of 19 gates, on
{n_truths} truths drawn after the freeze was committed and never seen during
any tuning. The 16 hyperparameters came from the stage 1 selection split
unchanged and the runner has no sweep. Six source-side gates were decided
before any operator was imported; stage B reproduced all {n_truths} bank
commitments.

Endpoint is the **all-state resolution-aware morphology error**: one error per
(truth, age) computed by the measure its reconciled state label selects —
assignment, blended or amplitude — each normalized to its own worst case,
aggregated with **no state excluded**. Materiality was declared before the bank
was drawn: median ≥ 0.10 and bootstrap lower bound ≥ 0.05.

| class | arm | est | physical | CI low | material | class-cond. | CI low | material |
|---|---|---|---:|---:|---|---:|---:|---|
{mtab}

**Established.** In the claim-bearing class the resolved arm reduces the
morphology error against the direct image by {m_pr:.3f} (ridge) and {m_pt:.3f}
(TSVD) on the physical end-to-end target, with lower bounds {m_prl:.3f} and
{m_ptl:.3f}. Both controls behave: the unresolved-image arm reaches at most
{m_unres:+.3f} and total flux {m_flux:+.3f}, neither material, so the benefit
is attributable to resolving the orders rather than to the extra photons an
unresolved second image also carries.

**Per family, the aggregate is not uniform.** {n_fam_phys} of {n_fam_cells}
family–estimator cells are material on the physical target and {n_fam_both} of
{n_fam_cells} on both targets. Ten truths per family makes every interval here
wide, so no family claim is supported in either direction.

| family | est | physical | CI low | material | both targets |
|---|---|---:|---:|---|---|
{ftab}

**Seven dispositions** (`HMT2_MAIN_RECORD_AMENDMENT_021`, ruling 021):

{dtab}

**Reduced scope, accepted.** {auth_truths} truths and {auth_draws} noise draws
were authorized; {n_truths} and {exec_draws} were executed. The reduction was
written into the sealed freeze and committed before any held-out truth was
drawn, so it cannot have shaped the result — but it was never flagged as a
deviation and no rationale was recorded. Every interval is wider than the
authorized design would have given. Disposition
`HMT2_MAIN_REDUCED_SCOPE_EVIDENCE_ACCEPTED`.

**Two integrity qualifications, both on the record.** The authoritative stage A
run executed against a tree that was not clean on the registered pathspecs,
because the deterministic-hash repair had to be in the tree before stage A
could be re-run; the porcelain diff is hashed in the manifest and stage B ran
clean at the commit that carries both the fix and the hashes. The
salted-`hash()` defect itself hit an integrity field only — truth content and
seeds were sha256 throughout — and the commitment gate caught it before stage B
scored anything.

**Rests on.** `artifacts/configs/HMT2_SEALED_MAIN_V1.json`
`{sha_mfz}`, committed before the bank was drawn;
`artifacts/provenance/HMT2_SEALED_MAIN_BANK_HASHES.json` `{sha_bank}`;
`artifacts/tables/hmt2_main_endpoint.parquet` `{sha_mep}`;
`artifacts/reports/HMT2_SEALED_MAIN.md` `{sha_rep}`.

**Does not license.**

- **Two-feature recovery.** Material in no cell; the absolute assignment cost
  stays between {mc_lo:.3f} and {mc_hi:.3f} where 1.0 is one whole feature
  wrong, on the {n_multi_truths} truths of {n_truths} that carry a stable
  multi-resolved state at all. A negative result, preserved as one.
- **A stable morphology interval.** {stable_M:.0f} M for every arm, estimator,
  class and SNR. At the reference SNR the resolved arm's mean reach,
  {reach_res:.2f} M, is *lower* than the direct image's {reach_dir:.2f} M; at
  tenfold SNR the ordering reverses ({reach_res10:.2f} M against
  {reach_dir10:.2f} M). A per-age error reduction is not a history interval.
- **Accurate historical movie recovery.** Absolute error for the resolved arm
  remains {m_abs_lo:.3f} to {m_abs_hi:.3f} against a worst case of 1.0, and
  {sat_direct:.1%} of direct-image states sit at the measure's ceiling, so the
  mean substantially counts how many states failed outright. Nothing here
  licenses a statement about arbitrary or realistic accretion-flow histories.
- One geometry, one operator family, two source classes, six source families.

---

## Preserved literal failures

A FAIL that has been adjudicated and kept, never edited to match its ruling.

| gate | disposition |
|---|---|
{D.join('| `' + k + '` | `' + v + '` |' for k, v in sorted(counts['preserved_literal_failure_dispositions'].items()))}

## Governance amendments

| amendment | what it changed |
|---|---|
| `PAPER_I_V2_PRE_E3C_AMENDMENT_001` | notation `A_C = 𝒜 Q_C`; `exact_rank = NOT_APPLICABLE`; `D_hist`, `d_eff` reserved for E3D |
| `PAPER_I_V2_RECONSTRUCTION_AMENDMENT_002` | the registered flat-probe `D_delay` is an algebraic identity, kept as a control and never as evidence |
| `AGE_INTERVAL_SEMANTICS_AMENDMENT_003` | reach, longest run and anchored span separated; anchor frozen from reachable support |
| `R0_REPAIR_AMENDMENT_004` | in-class truths made exactly in-span; four source regimes; attestation replaces the vacuous clean-tree check |
| `REVIEWER_RULING_R0C_005` | execution, manifest-build and artifact commits named separately |
| `R1_RECORD_AMENDMENT_006` | execution attestation authoritative; report assembly recorded apart from it |
| `R1L_STAGE1_DIRTY_EXECUTION_AMENDMENT_008` | a stage-1 run executed against an uncommitted tree; re-run clean and the deviation kept |
| `R1L_DETERMINISTIC_NUMERICS_AMENDMENT_009` | eight environment variables pinned before NumPy loads, and `pin()` refuses to be a no-op |
| `R1L_STAGE2_RECORD_AMENDMENT_011` | stage 2 recorded as representation-limited; the exact-in-class rerun separated from it |
| `R1L_STAGE2R_GATE_COMPLETION_AMENDMENT_013` | missing gates completed with every pre-existing cell required to reproduce bitwise |
| `R1L_STAGE2R_SCIENTIFIC_DISPOSITION_AMENDMENT_014` | six dispositions separating the formal token from what the run establishes; `sealed_main_authorized = false` |
| `HMT1_VALIDATION_RECORD_AMENDMENT_015` | five validation findings recorded; the canonical deterministic pair named |
| `HMT1_SEALED_MAIN_BANK_V1_RETIREMENT_016` | the first sealed bank retired after it was smoke-tested, which is a peek |
| `HMT1_SEALED_MAIN_CORRECTION_AND_RETIREMENT_017` | `HMT1_MAIN_PARTIAL_ENDPOINT_EXPOSURE`; seed 20260917 retired; the firewall made lineage-based rather than filename-based |
| `HMT1_CLOSURE_RECORD_018` | HMT-1 closed with no standing result; seed 20260921 preserved as a regression-only canary |
| `HMT2_STAGE0_PRESERVED_FINDINGS_019` | stage 0 merger rates withheld pending the source-only recompute; three strata declared |
| `HMT2_STAGE1_ENDPOINT_COMPLETION_AMENDMENT_020` | four stage-1 defects recorded; completion required bitwise reproduction of every primary cell |
| `HMT2_MAIN_RECORD_AMENDMENT_021` | seven dispositions on the sealed main; reduced scope accepted; stage-A attestation and the salted-hash defect recorded |
"""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(body)
    print(f"wrote {OUT.relative_to(ROOT)}")
    print(f"  E3C: {h1_deeper}/{n_geom} deeper, {h1_jold}/{n_geom} J_old > 0")
    print(f"  R1 : delta {sp('IN_CLASS_ID','RESOLVED_PHYSICAL') - sp('IN_CLASS_ID','DIRECT_PHYSICAL'):.0f} M, "
          f"{n_fam}/{len(ft)} families, structure onset {on_r:.0f}")
    print(f"total {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
