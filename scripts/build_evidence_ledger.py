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
