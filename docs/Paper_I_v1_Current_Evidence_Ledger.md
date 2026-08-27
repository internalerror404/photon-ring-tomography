# Paper I — current evidence ledger

Regenerated from canonical artifacts by `scripts/build_evidence_ledger.py`.
Nothing here is typed by hand; every number is read from a frozen table or
freeze, and the ledger is rebuilt rather than edited.

- generated 2026-08-27T19:49:27Z
- registry sha256 `2ba66f0209fe1cdec97b8cf5862494c22fb94704318f9601a7a1f9eb4b783796`
- canonical artifact freeze v2: **369 artifacts**,
  campaign commit `8345068676b15ce8f96a76da9d92b159db215f1d`
- gates: **208** total, **189** passing,
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

## R1L stage 1 — localized operator and rank audit

Established, with no estimator involved, at `a* = 0.5`, `i = 50` degrees.
Canonical under two pinned six-class runs that agreed on every scientific cell.

Compact temporal support turns "the direct image cannot see this epoch" from a
condition number into a null-space fact. Old-epoch structural support is the
subspace of old temporal functions orthogonal to the level projector; entries
are operational ranks.

| localized | direct rank | direct exact-zero cols | direct old-struct | resolved old-struct | unresolved old-struct | global | direct rank | direct exact-zero cols |
|---|---:|---:|---:|---:|---:|---|---:|---:|
| `L224` | 140 | 84 | 0 | 38 | 21 | `C224` | 224 | 0 |
| `L448` | 252 | 196 | 0 | 93 | 46 | `C448_T` | 411 | 0 |
| `L1056` | 523 | 517 | 0 | 185 | 91 | `C1056_ST` | 911 | 0 |

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
| 100 | `RESOLVED_PHYSICAL` | TSVD | +0.168 | +0.099 | +0.116 | +0.039 | 3/4 | no |
| 100 | `RESOLVED_PHYSICAL` | RIDGE_IDENTITY | +0.178 | +0.096 | +0.098 | +0.000 | 3/4 | no |
| 100 | `UNRESOLVED_IMAGE` | TSVD | +0.009 | -0.084 | -0.024 | -0.079 | 3/4 | no |
| 100 | `UNRESOLVED_IMAGE` | RIDGE_IDENTITY | +0.019 | -0.073 | -0.029 | -0.100 | 3/4 | no |
| 1000 | `RESOLVED_PHYSICAL` | TSVD | +0.275 | +0.198 | +0.259 | +0.210 | 4/4 | **yes** |
| 1000 | `RESOLVED_PHYSICAL` | RIDGE_IDENTITY | +0.304 | +0.225 | +0.286 | +0.237 | 4/4 | **yes** |
| 1000 | `UNRESOLVED_IMAGE` | TSVD | +0.085 | +0.019 | +0.078 | +0.042 | 3/4 | no |
| 1000 | `UNRESOLVED_IMAGE` | RIDGE_IDENTITY | +0.116 | +0.031 | +0.104 | +0.067 | 3/4 | **yes** |

Source banks, after projection into the class:

| bank | role | achieved f_struct | max negative mass | physical primary |
|---|---|---:|---:|---|
| `constant_flux_structural` | `SIGNED_CONSTANT_FLUX_STRUCTURAL_DIAGNOSTIC` | 0.807 | 0.1966 | no |
| `structure_balanced_050` | `STRUCTURE_BALANCED_050` | 0.520 | 0.0001 | **yes** |
| `structure_balanced_080` | `HIGH_STRUCTURE_NOMINAL_080_REALIZED_066` | 0.660 | 0.0007 | **yes** |

Six dispositions, recorded separately:

- **`R1L_STAGE2R_GATE_COMPLETION_REPRODUCTION_PASS`** — every pre-existing cell
  bitwise identical across the gate-completed rerun, 12 of 12 declared gates.
- **`R1L_STAGE2R_PHYSICAL_SOURCE_MATERIALITY_NOT_MET`** — at SNR₀ = 100 the
  medians clear the bar and the cell-balanced means do not. Read as
  `PREREGISTERED_PHYSICAL_SOURCE_MATERIALITY_NOT_MET`: a bar not cleared, not an
  effect shown to be zero. The central estimates are positive.
- **`R1L_STAGE2R_SIGNED_DIAGNOSTIC_MATERIAL_EFFECT`** — the signed constant-flux
  bank alone shows 0.358 (TSVD) and
  0.399 (ridge) and was carrying
  the pooled all-banks result. A linear inverse-problem finding; it is not a
  non-negative emissivity history and may not carry a source claim.
- **`R1L_STAGE2R_HIGH_SNR_PHYSICAL_VALIDATION_PASS`** — at SNR₀ = 1000 the
  resolved arm meets every criterion on both estimators and 4/4 families.
  Secondary: a result at tenfold higher normalized SNR does not substitute for
  the registered point.
- **`R1L_STAGE2R_STABLE_SPAN_NEGATIVE_RESULT`** — ΔL = 0 M
  against 8 M under both noise semantics at both SNRs, with the stricter joint
  truth-and-noise statistic agreeing with the averaged one.
- **`R1L_STAGE2R_SCIENTIFIC_STOP`** — `sealed_main_authorized = false`.

Does not license: a physical-source reconstruction claim at the reference SNR; a
stable structural history interval at any SNR; any statement about arbitrary or
realistic accretion-flow histories. The design is a representation-matched,
zero-floor best-case benchmark.

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
