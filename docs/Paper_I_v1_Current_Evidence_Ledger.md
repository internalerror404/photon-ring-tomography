# Paper I — current evidence ledger

Regenerated from canonical artifacts by `scripts/build_evidence_ledger.py`.
Nothing here is typed by hand; every number is read from a frozen table or
freeze, and the ledger is rebuilt rather than edited.

- generated 2026-08-28T15:26:51Z
- registry sha256 `2ba66f0209fe1cdec97b8cf5862494c22fb94704318f9601a7a1f9eb4b783796`
- canonical artifact freeze v2: **591 artifacts**,
  campaign commit `8345068676b15ce8f96a76da9d92b159db215f1d`
- gates: **208** total, **189** passing,
  **0** active blocking failures,
  **8** preserved literal failures,
  **11** belonging to phases not yet in scope

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

Bank seed 20260921 is preserved as `HMT1_SOURCE_RESOLUTION_FAILURE_CANARY`: **regression test
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
from the final module inspection. 169 sources over six families, one of
them the preserved HMT-1 failure canary and excluded from every aggregate
below. The remaining 168 are classified at every age by topographic
prominence, reconciled across the two finest of three nested grids.

What the source objects are, before any measurement:

| state | fraction of 10248 audited states |
|---|---:|
| `SINGLE_RESOLVED` | 53.7% |
| `MULTI_RESOLVED` | 32.9% |
| `BLENDED` | 2.6% |
| `DEAD` | 8.2% |
| `AMBIGUOUS` | 2.6% |

**Canonical merger rates** (ruling 020 item 1), on the `STABLE_MULTI_RESOLVED`
stratum — states both finest levels agree are multi-resolved:

| family | class | rate |
|---|---|---:|
| `two_hotspot_trajectories` | `L448_contrast` | **0.299** |
| `two_hotspot_trajectories` | `L896_radial_enriched` | **0.136** |
| `m2_structural_mode` | either class | 0.000 |

The pooled 0.356 and 0.262 over all states the finest
level calls multi remain in the record as what the finest grid alone would say,
and carry no claim. The `AMBIGUOUS_FINE_MULTI` stratum merges at
0.687 and 1.000 — states whose multiplicity the grid
cannot settle are mostly states the projection merges, which is the expected
direction and is why they are scored by the blended measure rather than
dropped.

Minimum representable feature width in the claim-bearing class is
2.00 M. Below it a projected feature is a grid artefact and the
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
| `PHYSICAL_END_TO_END` | +0.130 | +0.120 |
| `CLASS_CONDITIONAL` | +0.146 | +0.122 |

Stage 1's pass rule was improvement with a bootstrap bound clear of zero and
**carried no effect-size floor at all**, which is recorded as a defect of the
rule rather than of the result. The sealed main below is judged against a
declared floor.

Does not license: a held-out claim of any kind.

---

## HMT-2 sealed main — held-out resolution-aware morphology recovery

**Token `HMT2_MAIN_PHYSICAL_MORPHOLOGY_RECOVERY_PASS`**, 19 of 19 gates, on
60 truths drawn after the freeze was committed and never seen during
any tuning. The 16 hyperparameters came from the stage 1 selection split
unchanged and the runner has no sweep. Six source-side gates were decided
before any operator was imported; stage B reproduced all 60 bank
commitments.

Endpoint is the **all-state resolution-aware morphology error**: one error per
(truth, age) computed by the measure its reconciled state label selects —
assignment, blended or amplitude — each normalized to its own worst case,
aggregated with **no state excluded**. Materiality was declared before the bank
was drawn: median ≥ 0.10 and bootstrap lower bound ≥ 0.05.

| class | arm | est | physical | CI low | material | class-cond. | CI low | material |
|---|---|---|---:|---:|---|---:|---:|---|
| `L896_radial_enriched` | `RESOLVED_PHYSICAL` | Ridge | +0.164 | +0.116 | **yes** | +0.158 | +0.114 | **yes** |
| `L896_radial_enriched` | `RESOLVED_PHYSICAL` | TSVD | +0.133 | +0.101 | **yes** | +0.160 | +0.092 | **yes** |
| `L896_radial_enriched` | `UNRESOLVED_IMAGE` | Ridge | +0.000 | +0.000 | no | +0.000 | -0.000 | no |
| `L896_radial_enriched` | `UNRESOLVED_IMAGE` | TSVD | +0.015 | -0.042 | no | +0.009 | -0.036 | no |
| `L896_radial_enriched` | `TOTAL_FLUX` | Ridge | -0.020 | -0.050 | no | -0.024 | -0.058 | no |
| `L896_radial_enriched` | `TOTAL_FLUX` | TSVD | +0.036 | -0.025 | no | +0.045 | -0.021 | no |
| `L448_contrast` | `RESOLVED_PHYSICAL` | Ridge | +0.101 | +0.064 | **yes** | +0.132 | +0.099 | **yes** |
| `L448_contrast` | `RESOLVED_PHYSICAL` | TSVD | +0.061 | +0.033 | no | +0.162 | +0.095 | **yes** |
| `L448_contrast` | `UNRESOLVED_IMAGE` | Ridge | +0.000 | +0.000 | no | +0.000 | +0.000 | no |
| `L448_contrast` | `UNRESOLVED_IMAGE` | TSVD | +0.000 | +0.000 | no | +0.000 | +0.000 | no |
| `L448_contrast` | `TOTAL_FLUX` | Ridge | +0.011 | -0.035 | no | -0.002 | -0.025 | no |
| `L448_contrast` | `TOTAL_FLUX` | TSVD | +0.044 | +0.002 | no | +0.018 | +0.002 | no |

**Established.** In the claim-bearing class the resolved arm reduces the
morphology error against the direct image by 0.164 (ridge) and 0.133
(TSVD) on the physical end-to-end target, with lower bounds 0.116 and
0.101. Both controls behave: the unresolved-image arm reaches at most
+0.015 and total flux +0.036, neither material, so the benefit
is attributable to resolving the orders rather than to the extra photons an
unresolved second image also carries.

**Per family, the aggregate is not uniform.** 5 of 12
family–estimator cells are material on the physical target and 4 of
12 on both targets. Ten truths per family makes every interval here
wide, so no family claim is supported in either direction.

| family | est | physical | CI low | material | both targets |
|---|---|---:|---:|---|---|
| `circular_hotspot_trajectory` | Ridge | -0.022 | -0.200 | no | no |
| `circular_hotspot_trajectory` | TSVD | -0.051 | -0.115 | no | no |
| `flare_birth_motion_decay` | Ridge | +0.381 | +0.191 | **yes** | **yes** |
| `flare_birth_motion_decay` | TSVD | +0.377 | +0.065 | **yes** | no |
| `m1_rotating_crescent` | Ridge | +0.204 | +0.030 | no | no |
| `m1_rotating_crescent` | TSVD | +0.212 | +0.049 | no | no |
| `m2_structural_mode` | Ridge | +0.320 | +0.146 | **yes** | **yes** |
| `m2_structural_mode` | TSVD | +0.243 | +0.165 | **yes** | **yes** |
| `plunging_feature` | Ridge | +0.111 | +0.084 | **yes** | **yes** |
| `plunging_feature` | TSVD | +0.097 | +0.071 | no | no |
| `two_hotspot_trajectories` | Ridge | +0.178 | -0.006 | no | no |
| `two_hotspot_trajectories` | TSVD | +0.135 | -0.087 | no | no |

**Seven dispositions** (`HMT2_MAIN_RECORD_AMENDMENT_021`, ruling 021):

- **`HMT2_MAIN_AGGREGATE_PHYSICAL_MORPHOLOGY_ERROR_REDUCTION_CONFIRMED`** — in the claim-bearing class at the reference SNR the resolved arm reduces the all-state resolution-aware morphology error against the direct image by a median 0.164 under ridge and 0.133 under TSVD on the physical end-to-end target, with paired bootstrap lower bounds 0.116 and 0.101.
- **`HMT2_MAIN_ORDER_RESOLUTION_ATTRIBUTION_SUPPORTED`** — the unresolved-image control reaches at most 0.015 in the claim-bearing class and the total-flux control reaches 0.036, neither material. The benefit is attributable to resolving the photon-ring orders and not to the additional photons an unresolved second image also carries, nor to the extra flux constraint alone.
- **`HMT2_MAIN_MULTI_FEATURE_RECOVERY_NEGATIVE`** — two-feature recovery reaches materiality in no cell. In the claim-bearing class the median reductions are 0.137 to 0.187 and the absolute assignment cost stays between 1.208 and 1.302 on a scale where 1.0 is one whole feature wrong. The measure resolves that a state has two features and recovers the morphology of one. It does not recover the pair. This is a negative result and is preserved as one.
- **`HMT2_MAIN_STABLE_MORPHOLOGY_INTERVAL_NEGATIVE`** — the stable morphology interval is 0 M for every arm, estimator, class and SNR. There is no age window over which recovered morphology holds steady. At the reference SNR the resolved arm does not even extend how far back morphology stays in tolerance. A per-age error reduction is not a history interval.
- **`HMT2_MAIN_FAMILY_HETEROGENEITY_PRESERVED`** — 5 of 12 family-estimator cells are material on the physical end-to-end target and 4 of 12 on both targets. circular_hotspot_trajectory is negative under both estimators. The aggregate is not a uniform improvement and must not be quoted as one. Ten truths per family makes these intervals wide, so no family claim is supported in either direction; the heterogeneity is what is recorded, not a ranking.
- **`HMT2_MAIN_DIRECT_BASELINE_SATURATION_QUALIFICATION`** — in the claim-bearing class 55.8% of direct-image states sit at the measure's ceiling, against 42.0% for the resolved arm. The mean substantially counts how many states failed outright rather than how far off the recovered morphology was. The direct baseline is partly floor-limited, which flatters the difference, and the gain must be read with the saturation fractions beside it.
- **`HMT2_MAIN_ACCURATE_HISTORICAL_MOVIE_RECOVERY_NOT_ESTABLISHED`** — absolute all-state error for the resolved arm remains 0.598 to 0.650 on a scale whose worst case is 1.0, with no stable interval and no two-feature recovery. A material reduction in a morphology error is not accurate recovery of a historical movie, and this campaign does not establish the latter at any point. Nothing here licenses a statement about arbitrary or realistic accretion-flow histories.

**Reduced scope, accepted.** 96 truths and 8 noise draws
were authorized; 60 and 4 were executed. The reduction was
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
`bb65f5615e2dff7a...`, committed before the bank was drawn;
`artifacts/provenance/HMT2_SEALED_MAIN_BANK_HASHES.json` `fb723492b627d4c0...`;
`artifacts/tables/hmt2_main_endpoint.parquet` `c89cdcf8861f943e...`;
`artifacts/reports/HMT2_SEALED_MAIN.md` `8d6ede758df73641...`.

**Does not license.**

- **Two-feature recovery.** Material in no cell; the absolute assignment cost
  stays between 1.203 and 1.302 where 1.0 is one whole feature
  wrong, on the 17 truths of 60 that carry a stable
  multi-resolved state at all. A negative result, preserved as one.
- **A stable morphology interval.** 0 M for every arm, estimator,
  class and SNR. At the reference SNR the resolved arm's mean reach,
  3.06 M, is *lower* than the direct image's 3.32 M; at
  tenfold SNR the ordering reverses (3.45 M against
  2.92 M). A per-age error reduction is not a history interval.
- **Accurate historical movie recovery.** Absolute error for the resolved arm
  remains 0.598 to 0.650 against a worst case of 1.0, and
  55.8% of direct-image states sit at the measure's ceiling, so the
  mean substantially counts how many states failed outright. Nothing here
  licenses a statement about arbitrary or realistic accretion-flow histories.
- One geometry, one operator family, two source classes, six source families.

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
