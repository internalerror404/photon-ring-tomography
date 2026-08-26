# Paper I — current evidence ledger

Regenerated from canonical artifacts by `scripts/build_evidence_ledger.py`.
Nothing here is typed by hand; every number is read from a frozen table or
freeze, and the ledger is rebuilt rather than edited.

- generated 2026-08-26T04:23:26Z
- registry sha256 `2ba66f0209fe1cdec97b8cf5862494c22fb94704318f9601a7a1f9eb4b783796`
- canonical artifact freeze v2: **369 artifacts**,
  campaign commit `8345068676b15ce8f96a76da9d92b159db215f1d`
- gates: **165** total, **146** passing,
  **0** active blocking failures,
  **8** preserved literal failures,
  **11** belonging to phases not yet in scope

## Standing scope

One geometry family is reconstructed and one source class is inverted. Nothing
in this campaign is geometry-wide reconstruction, and nothing is arbitrary movie
recovery. No telescope detection and no laboratory result is claimed anywhere.

---

## E3C — geometry-wide operator audit

**Established.** On 12 registered spin–inclination geometries under the
corrected pixel-integrated measurement convention, the order-resolved stack sees
further back in retarded time than the direct image alone. At the reference
SNR_0 = 100: the resolved oldest detectable age probe exceeds the direct
one in **12 of 12** geometries, and the threshold-independent
historical innovation `J_old` is positive in **12 of 12**.

**Rests on.** `artifacts/configs/E3C_OPERATOR_GRID_FREEZE.json`
`7ab28bcd14674fb6...`, registered before the
first geometry was evaluated; `artifacts/tables/e3c_depth_curves.parquet`
`90fe0b235cbaf0fa...`;
`artifacts/tables/e3c_geometry_metrics.parquet`
`ab316dafcba6b858...`;
`artifacts/reports/E3C_GEOMETRY_WIDE_OPERATOR_AUDIT.md`
`e7406f9f550f3d23...`.

**Depth is three observables, not one**
(`AGE_INTERVAL_SEMANTICS_AMENDMENT_003`). The reach is a supremum and is blind
to holes; the longest detectable run is the longest stretch *anywhere* on the
grid; only the stretch reaching the frozen anchor is history from the present.
They differ in **316 of 1152** depth rows. In
**4 of 12** geometries the anchor is a positive age:
at i = 75 degrees the minimum delay in the frozen ray set exceeds the last
observer sample, so the present is not observed there at all. The reassembly
re-derived all 1152 rows from stored masks with
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
SNR_0 = 100, epsilon = 0.25,
q = 0.95, prior-free TSVD:

| regime | direct | resolved | delta |
|---|---:|---:|---:|
| `IN_CLASS_ID` | 48 M | 80 M | **+32 M** |
| `IN_CLASS_OOD` | 48 M | 80 M | +32 M |
| `OFF_GRID_OOD` | 48 M | 80 M | +32 M |
| `OFF_GRID_ID` | 0 M | 0 M | 0 M |

against a threshold of 8 M. Ridge confirms
at 32 M. **4 of 4** prior-fit families reach
the threshold. Paired truth-cluster bootstrap,
10000 resamples, seed
20260901: old-band normalized reduction
0.332 with lower bound
0.330, absolute 0.429
with lower bound 0.419.

**Level, not morphology.** 98.4%
of a truth's age-window norm is its spatially constant part. The level error
falls 0.266 to
0.028; the structure
error falls 0.927
to 0.466 across
all ages but is
1.169
against
1.141
in the old band, both above one. The primary result is emissivity-*level*
reconstruction and is not detailed old-age movie morphology.

**High-SNR structure, stated separately.** The onset of nonzero age-local
structure recovery is **unchanged** at SNR_0 = 30000 for both arms. What
differs is the span at that point: **40 M direct against
76 M resolved**.

**Not a prior effect.** Judged on the direct channel's own
154-direction data
subspace — like for like, since the resolved arm supports
202 of its own — the error
falls 0.986
to 0.579.

**Integrity.** All 4000 scored null-pair controls came from a bank hashed
before scoring, with zero direction-hash mismatches;
78 exceed the equal-prior Gaussian Bayes bound
against an expectation consistent with multiplicity. The sealed 640-truth bank
was regenerated and matched its committed hashes; it is disjoint from every R0C
split.

**Rests on.** `artifacts/configs/R1_MAIN_FREEZE.json`
`4ef162320e09086a...`, committed in a clean tree
before any main truth was scored; sealed-bank commitment
`93608e7a7578fe89...`; null control bank
`57ee7fef85da0ff0...`;
`artifacts/reports/R1_HELD_OUT_MAIN.md` `dde24b52d62eeaf3...`.

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
| `EDGE1_a000_i020_raymap_generation` | `RESOLVED_BY_S0_BACKEND` |
| `G10q_retired_flat_sigma_convention` | `RETIRED_PIXELIZATION_DEPENDENT` |
| `G1_v01_reproduction_relative` | `FAIL_AS_WRITTEN` |
| `G7_grid_convergence_a098_i075` | `RETIRED_NONCONVERGENT_EXTREME_STATISTIC` |
| `G7_grid_convergence_raw_max` | `RETIRED_NONCONVERGENT_EXTREME_STATISTIC` |
| `G7b_weighted_operator_discrepancy` | `WITHDRAWN_INVALID_CONVERGENCE_METRIC` |
| `GRID_AUTHORIZATION` | `SUPERSEDED_GRID_COMPLETE` |
| `R0_G15_uncertainty_calibration_band` | `UNCERTAINTY_WITHDRAWN` |

## Governance amendments

| amendment | what it changed |
|---|---|
| `PAPER_I_V2_PRE_E3C_AMENDMENT_001` | notation `A_C = 𝒜 Q_C`; `exact_rank = NOT_APPLICABLE`; `D_hist`, `d_eff` reserved for E3D |
| `PAPER_I_V2_RECONSTRUCTION_AMENDMENT_002` | the registered flat-probe `D_delay` is an algebraic identity, kept as a control and never as evidence |
| `AGE_INTERVAL_SEMANTICS_AMENDMENT_003` | reach, longest run and anchored span separated; anchor frozen from reachable support |
| `R0_REPAIR_AMENDMENT_004` | in-class truths made exactly in-span; four source regimes; attestation replaces the vacuous clean-tree check |
| `REVIEWER_RULING_R0C_005` | execution, manifest-build and artifact commits named separately |
| `R1_RECORD_AMENDMENT_006` | execution attestation authoritative; report assembly recorded apart from it |
