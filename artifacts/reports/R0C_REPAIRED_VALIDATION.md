# R0C — REPAIRED SOURCE AND CALIBRATED UNCERTAINTY

Validation only. The held-out main test was hashed at registration under the
corrected generator semantics and was neither rendered into data nor scored.

## Identity

| provenance field | value |
|---|---|
| `accepted_base_commit` | `0ef341dae3b21bc2bdd0e54a18971cff208af783` |
| `measurement_correction_commit` | `d6869f8d1c08889fee34e91d392c2bbc1bc9a62f` |
| `e3c_execution_code_commit` | `546763ed29e2be3fb129ec707cb07ee37a4f7db8` |
| `e3c_artifact_commit` | `7d610121adc95fb641ab5692d37d2b761b082039` |
| `e3c_age_interval_amendment_commit` | `f034f19829623efa1f29bdcf27f95e10bd2de62e` |
| `e3c_freeze_sha256` | `7ab28bcd14674fb6544b577f19c00301f09e45ffec805cfcc29896c53634bf1b` |
| `e3c_registry_sha256` | `2ba66f0209fe1cdec97b8cf5862494c22fb94704318f9601a7a1f9eb4b783796` |
| `ray_map_manifest_sha256` | `d163a630842ddec4b2143f9268bc70125857e78b84aa8fa122c5ef1bfc7b3638` |
| `r0_config_sha256` | `dfc8d35eb2b7cb201409295698e9c623a10a0fa5ce730c7050e67c55f0ddb31e` |
| `r0c_config_sha256` | `7a35b76f42127509cb672986dcba865e03ab41042a97ac1551aba876a8898557` |
| `accepted_pilot_artifact_commit` | `8345068676b15ce8f96a76da9d92b159db215f1d` |

- R0C freeze `artifacts/configs/R0C_REPAIRED_SOURCE_AND_CALIBRATION_FREEZE.json`
  sha256 `5a59d5e6203d965723777be41180d81bdb39d6dd1c26867b8a59aa94e91e6e51`
| commit | value | meaning |
|---|---|---|
| `execution_commit` | `b6e481ab133015e9d7089fcbe6cfd81496200057` | where the code was when the run started |
| `manifest_build_commit` | `61a67e6464552ab7fad293a8e55f5125f6202e09` | HEAD when the manifest was built, after the run |
| `artifact_commit` | `446fa00d0fadece4648118f29871bc615a16d9d7` | the tree the outputs were committed in |

Three different things, named separately under `REVIEWER_RULING_R0C_005`. The
old single `git_commit` field reported the middle one while calling it the
first, which for an 804 s run is a commit that never described the executing
code.

- head tree `fd34366026d0e184b4a2909d1daa88592ef8cf79`
- freeze committed at that commit: **True**;
  tracked changes 2, untracked 1,
  porcelain sha256 `b93dbfd02f225ef4...`
- registry `2ba66f0209fe1cdec97b8cf5862494c22fb94704318f9601a7a1f9eb4b783796`, environment `00bf00f9bb7f2905ea69b970f9f75880c0f7ea32fca29da43b1f46bb212fe7d1`
- scope: a* = 0.5, i = 50 deg, class C224, validation only. **Not
  geometry-wide, and not arbitrary movie recovery.**

Unlike the pilot, that attestation is evidence rather than an assertion: the
check behind the pilot's `dirty_tree: false` matched no path in this layout and
could only ever say clean.

## Correctness gates

| gate | status | measured | threshold | disposition |
|---|---|---:|---:|---|
| `R0_G13_freeze_commit_attestation` | **PASS** | 1 | 1 | – |
| `R0_G1_dense_matrix_free_parity` | **PASS** | 2.173e-15 | 1e-10 | – |
| `R0_G2_physical_adjoint` | **PASS** | 6.395e-14 | 1e-08 | – |
| `R0_G3_G10q_quadrature_noise_invariance` | **PASS** | 7.257e-16 | 1e-10 | – |
| `R0_G4_mixing_covariance` | **PASS** | 5.423e-16 | 1e-10 | – |
| `R0_G5_basis_round_trip` | **PASS** | 0 | 1e-10 | – |
| `R0_G6a_declared_probe_unit_norm` | **PASS** | 0 | 1e-12 | – |
| `R0_G6b_independent_quadrature_crosscheck` | **PASS** | 5.551e-05 | 0.005 | – |
| `R0_G7_right_censoring` | **PASS** | 4 | 4 | – |
| `R0_G8_estimator_closed_form` | **PASS** | 2.169e-15 | 1e-09 | – |
| `R0_G9_noise_replay` | **PASS** | 1 | 1 | – |
| `R0_G10_null_pair_calibration` | **PASS** | 2.22e-16 | 0.02 | – |
| `R0_G11_split_hash_disjointness` | **PASS** | 0 | 0 | – |
| `R0_G12_reduced_statistic_equivalence` | **PASS** | 0.02456 | 0.08 | – |
| `R0_G14_in_span_membership` | **PASS** | 0 | 1e-10 | – |
| `R0_G15_uncertainty_calibration_band` | **FAIL** | 0.4966 | [0.5, 2.0] | UNCERTAINTY_WITHDRAWN |

## Did the repair take?

**In-span membership.** In-class truths are now defined as `Q_C x`, so
membership is a property of the truth rather than a hope about its parameters.
`R0_G14` measures the residual on coordinates other than the projection grid:
worst relative residual over 3136 IN_CLASS truths, measured on coordinates other than the projection grid

**Representation floor, per regime.** This is the error of the exact projection
of the truth onto C224 — the limit no estimator can beat within the class.

| regime | registered min | registered max | structure min | structure max |
|---|---|---|---|---|
| IN_CLASS_ID | 0 | 1.539e-08 | 0 | 8.055e-08 |
| IN_CLASS_OOD | 0 | 1.49e-08 | 0 | 9.312e-07 |
| OFF_GRID_ID | 0.06899 | 0.07468 | 0.8034 | 0.8137 |
| OFF_GRID_OOD | 0.0001808 | 0.001319 | 0.01588 | 0.1148 |

**The in-class floor is zero to 9.3e-07, against a bar of 2.5e-04** — a thousandth of the tightest registered epsilon. The structure normalisation is a ratio of two vanishing quantities, so it lands at rounding rather than at exactly zero. That is the repair working: the pilot carried a structure-normalized floor of 0.406 to 0.426 in the regime it called in-class, so part of what it measured was the class rather than the estimator. The off-grid floors are positive by construction, which is what makes them off-grid.

**Splits.** {"prior_fit_train:IN_CLASS_ID": 2048, "uncertainty_calibration:IN_CLASS_ID": 256, "repair_validation:IN_CLASS_ID": 512, "uncertainty_calibration:IN_CLASS_OOD": 64, "repair_validation:IN_CLASS_OOD": 256, "uncertainty_calibration:OFF_GRID_ID": 256, "repair_validation:OFF_GRID_ID": 256, "uncertainty_calibration:OFF_GRID_OOD": 64, "repair_validation:OFF_GRID_OOD": 256}, worst pairwise content-hash overlap
**0**, disjoint = True.

**Future main test.** Commitment `93608e7a7578fe892269ac20297af5d3f22bc1f860bbdba71b9aa0a833aa3f1e` over
640 records, {"IN_CLASS_ID": 256, "IN_CLASS_OOD": 64, "OFF_GRID_ID": 256, "OFF_GRID_OOD": 64}. Rendered for
projection and hashing only: operator applied = False,
statistic formed = False, scored = False. The
pilot's commitment is preserved as
`SUPERSEDED_R0_PILOT_TEST_COMMITMENT`.

## Endpoint

Primary: **epsilon = 0.25, q =
0.95**, label
`VALIDATION_SELECTED_PRIMARY_FROM_PREREGISTERED_SURFACE`.

Retired: **epsilon = 0.5, q =
0.9**, disposition
`NONDISCRIMINATING_RIGHT_CENSORED_ENDPOINT`. Retained in every table below, and
not described as a failed comparison.

## The headline, at SNR_0 = 100

Anchored stable span `L_stable_anchor` in M, primary estimator
`TSVD`, confirmatory `RIDGE_IDENTITY`. The age-grid
ceiling is 120 M, so a value at the ceiling is censored.

| regime | direct | resolved | delta TSVD | delta ridge | delta >= 8 M | ridge confirms | reading |
|---|---|---|---|---|---|---|---|
| IN_CLASS_ID | 48 | 80 | 32 | 32 | True | True | passes |
| IN_CLASS_OOD | 48 | 80 | 32 | 32 | True | True | passes |
| OFF_GRID_ID | 0 | 0 | 0 | 0 | False | False | fails: the projection clears the tolerance and the reconstructions do not |
| OFF_GRID_OOD | 48 | 80 | 32 | 32 | True | True | passes |

The proposed main-test threshold is **8 M**, two age-grid steps.

The exact-in-class regime and the held-out flare family both pass, with the
prior-free primary and the prior-free confirmatory estimator agreeing to the
grid step. The off-grid regime `OFF_GRID_ID` does not, and its floor shows why that is a failure rather than a non-measurement: the exact projection clears the tolerance there, so the tolerance is reachable and the reconstructions do not reach it.

### Per prior-fit family, `IN_CLASS_ID`

The main-test criterion asks for improvement in at least three of the four.

| family | direct | resolved | delta |
|---|---|---|---|
| correlated_extended_field | 48 | 80 | 32 |
| rotating_asymmetric_crescent | 48 | 80 | 32 |
| single_orbiting_hotspot | 48 | 80 | 32 |
| two_independent_hotspots | 48 | 80 | 32 |

**4 of 4** families improve; **4** reach
the 8 M threshold.

### The retired endpoint, reported not hidden

| regime | DIRECT | RESOLVED | UNRESOLVED | TOTAL_FLUX |
|---|---|---|---|---|
| IN_CLASS_ID | 64 | 96 | 80 | 0 |
| IN_CLASS_OOD | 64 | 104 | 80 | 0 |
| OFF_GRID_ID | 64 | 100 | 80 | 0 |
| OFF_GRID_OOD | 64 | 104 | 80 | 0 |

### Level fidelity and structure recovery are different results

`IN_CLASS_ID`, `TSVD`, anchored span in M under each metric. The
registered metric normalises by the whole age-window norm, which every family
carries a positive baseline into; the structure companion removes the age-local
constant from residual and truth alike. In this regime the representation floor
is zero under both, so the difference between the columns is the estimator, not
the class.

| SNR_0 | direct | resolved | delta | direct (struct) | resolved (struct) | delta (struct) |
|---|---|---|---|---|---|---|
| 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| 3 | 0 | 0 | 0 | 0 | 0 | 0 |
| 10 | 0 | 0 | 0 | 0 | 0 | 0 |
| 30 | 40 | 68 | 28 | 0 | 0 | 0 |
| 100 | 48 | 80 | 32 | 0 | 0 | 0 |
| 300 | 52 | 84 | 32 | 0 | 0 | 0 |
| 1000 | 60 | 92 | 32 | 0 | 0 | 0 |
| 3000 | 64 | 108 | 44 | 0 | 0 | 0 |
| 10000 | 68 | 112 | 44 | 0 | 0 | 0 |
| 30000 | 72 | 116 | 44 | 0 | 76 | 76 |
| 100000 | 76 | 120 | 44 | 44 | 84 | 40 |
| 1000000 | 92 | 120 | 28 | 56 | 120 | 64 |

**Read the two halves separately.** On the structure metric neither arm recovers anything at the reference SNR_0 = 100; the first non-zero structure span appears at SNR_0 = 30000, roughly 300 times the reference. So the gain reported above at the reference SNR is a gain in fidelity to the age-local *level*, not recovery of age-local *structure*. Where structure is recovered at all, the resolved advantage is larger, not smaller — but it lives at signal-to-noise ratios far above the one this campaign is anchored to.

## Paired direct-versus-resolved age-error curves

Same truths and the same coupled resolved noise draw in both arms.
`IN_CLASS_ID`, SNR_0 = 100, `TSVD`, median over truths.

| age (M) | direct E | resolved E | resolved - direct | resolved - direct, structure |
|---|---|---|---|---|
| 0 | 0.1087 | 0.1081 | -0.0006242 | -0.03426 |
| 12 | 0.03274 | 0.02714 | -0.005604 | -0.02709 |
| 24 | 0.01821 | 0.01147 | -0.006743 | -0.03778 |
| 36 | 0.04576 | 0.01322 | -0.03254 | -0.1673 |
| 48 | 0.1534 | 0.02162 | -0.1318 | -0.562 |
| 60 | 0.3489 | 0.03815 | -0.3107 | -1.02 |
| 72 | 0.5396 | 0.1018 | -0.4379 | -0.959 |
| 84 | 0.6679 | 0.2312 | -0.4367 | -0.2439 |
| 96 | 0.7427 | 0.3946 | -0.348 | 0.2576 |
| 108 | 0.7207 | 0.4883 | -0.2324 | 0.3786 |
| 120 | 0.6483 | 0.5177 | -0.1306 | 0.3824 |

A negative difference means the resolved stack is closer to the truth.

## Old-band error beyond 57.7 M

| regime | arm | normalized | absolute | structure-normalized |
|---|---|---|---|---|
| IN_CLASS_ID | DIRECT_PHYSICAL | 0.6664 | 0.8235 | 1.161 |
| IN_CLASS_ID | RESOLVED_PHYSICAL | 0.3116 | 0.3555 | 1.192 |
| IN_CLASS_ID | TOTAL_FLUX | 0.426 | 0.5535 | 1.721 |
| IN_CLASS_ID | UNRESOLVED_IMAGE | 0.5037 | 0.5794 | 1.334 |
| IN_CLASS_OOD | DIRECT_PHYSICAL | 0.6553 | 0.6576 | 12.59 |
| IN_CLASS_OOD | RESOLVED_PHYSICAL | 0.3207 | 0.3224 | 18.61 |
| IN_CLASS_OOD | TOTAL_FLUX | 0.3823 | 0.3862 | 21.81 |
| IN_CLASS_OOD | UNRESOLVED_IMAGE | 0.5132 | 0.5164 | 20.36 |
| OFF_GRID_ID | DIRECT_PHYSICAL | 0.6681 | 0.6853 | 1.848 |
| OFF_GRID_ID | RESOLVED_PHYSICAL | 0.3288 | 0.3365 | 2.473 |
| OFF_GRID_ID | TOTAL_FLUX | 0.4084 | 0.4323 | 3.037 |
| OFF_GRID_ID | UNRESOLVED_IMAGE | 0.5181 | 0.5353 | 2.767 |
| OFF_GRID_OOD | DIRECT_PHYSICAL | 0.6626 | 0.663 | 12.54 |
| OFF_GRID_OOD | RESOLVED_PHYSICAL | 0.3216 | 0.3218 | 18.79 |
| OFF_GRID_OOD | TOTAL_FLUX | 0.3813 | 0.3815 | 22.23 |
| OFF_GRID_OOD | UNRESOLVED_IMAGE | 0.5184 | 0.5188 | 21.45 |

## Data-supported versus weak subspace, `IN_CLASS_ID`

| arm | estimator | own P_data dim | own data-supported | own weak | in direct P_data | outside direct P_data |
|---|---|---|---|---|---|---|
| DIRECT_PHYSICAL | LINEAR_STATE_SPACE | 154 | 1.182 | 6.268 | 1.182 | 6.268 |
| DIRECT_PHYSICAL | RIDGE_IDENTITY | 154 | 0.8438 | 1.548 | 0.8438 | 1.548 |
| DIRECT_PHYSICAL | TIKHONOV_TEMPORAL | 154 | 0.6883 | 5.912 | 0.6883 | 5.912 |
| DIRECT_PHYSICAL | TSVD | 154 | 0.9794 | 1.548 | 0.9794 | 1.548 |
| DIRECT_PHYSICAL | WIENER_GAUSSIAN | 154 | 1.127 | 0.8678 | 1.127 | 0.8678 |
| RESOLVED_PHYSICAL | LINEAR_STATE_SPACE | 202 | 4.215 | 3.454 | 0.745 | 5.508 |
| RESOLVED_PHYSICAL | RIDGE_IDENTITY | 202 | 0.8901 | 0.7236 | 0.4476 | 1.061 |
| RESOLVED_PHYSICAL | TIKHONOV_TEMPORAL | 202 | 2.007 | 3.124 | 0.3964 | 3.759 |
| RESOLVED_PHYSICAL | TSVD | 202 | 1.062 | 0.7225 | 0.5811 | 1.151 |
| RESOLVED_PHYSICAL | WIENER_GAUSSIAN | 202 | 1.304 | 0.4597 | 1.094 | 0.8414 |
| TOTAL_FLUX | LINEAR_STATE_SPACE | 14 | 0.7061 | 103.1 | 44.77 | 92.83 |
| TOTAL_FLUX | RIDGE_IDENTITY | 14 | 0.3563 | 2.034 | 1.589 | 1.328 |
| TOTAL_FLUX | TIKHONOV_TEMPORAL | 14 | 1.711e+05 | 3.399e+09 | 1.25e+09 | 3.161e+09 |
| TOTAL_FLUX | TSVD | 14 | 0.6285 | 2.035 | 1.69 | 1.354 |
| TOTAL_FLUX | WIENER_GAUSSIAN | 14 | 0.2724 | 2.324 | 1.958 | 1.283 |
| UNRESOLVED_IMAGE | LINEAR_STATE_SPACE | 183 | 2.69 | 5.679 | 1.097 | 6.201 |
| UNRESOLVED_IMAGE | RIDGE_IDENTITY | 183 | 0.9201 | 1.181 | 0.6408 | 1.357 |
| UNRESOLVED_IMAGE | TIKHONOV_TEMPORAL | 183 | 1.396 | 5.113 | 0.5088 | 5.285 |
| UNRESOLVED_IMAGE | TSVD | 183 | 1.127 | 1.181 | 0.8148 | 1.418 |
| UNRESOLVED_IMAGE | WIENER_GAUSSIAN | 183 | 1.242 | 0.7048 | 1.131 | 0.8704 |

A weak-subspace improvement is a prior effect and is never described as measured
recovery.

**The first two error columns are not a like-for-like comparison and must not be
read as one.** Each arm's `P_data` is its own: on this canary the direct channel
supports 154 directions and the resolved stack
202, and the extra ones are precisely the weakly determined
directions the direct channel cannot see at all. A norm over the larger set is
not comparable with a norm over the smaller, and the arm that sees more is
penalised for seeing more. On its own subspace the resolved stack is
worse than the direct channel, which on
its own says nothing either way.

The last two columns are the comparison that answers the question. Both arms are
judged on the *direct channel's* data subspace, so the reduction there is a
reduction where the direct channel can already see: **the resolved stack is better**. The final column is
the error outside that subspace, where a reduction is measured recovery only for
an arm whose own `P_data` covers those directions.

## Uncertainty

One declared scalar per estimator family, `cov -> s * cov`, fitted on the
`uncertainty_calibration` split at the hyperparameter selection chose, and
evaluated here on `repair_validation`.

| estimator | s | raw ratio min | raw ratio max | spread (decades) | operating points |
|---|---|---|---|---|---|
| WIENER_GAUSSIAN | 5.592 | 0.2712 | 8.697 | 1.506 | 48 |
| LINEAR_STATE_SPACE | 0.03667 | 0.01886 | 2.68 | 2.152 | 48 |

| estimator | s | scaled joint ratio | median p | clipped directions |
|---|---|---|---|---|
| LINEAR_STATE_SPACE | 0.03667 | 0.4966 | 1 | 0 |
| WIENER_GAUSSIAN | 5.592 | 0.6023 | 1 | 0 |

Acceptance band [0.5, 2.0]. Outcome: **UNCERTAINTY_WITHDRAWN**.

Outside the band, so the declared fallback applies: Wiener and the state-space model are retained as point estimators only. No credible interval, posterior movie or coverage statement from this line enters Paper I.

## Aggregate criteria

| criterion | result |
|---|---|
| in-class delta >= 8 M, TSVD | True |
| improvement in >= 3 of 4 prior-fit families | True (4 of 4) |
| lower old-band absolute and structure-normalized error | False |
| lower error in the direct channel's own data subspace | True |
| lower error on the resolved arm's own, larger data subspace | False |
| held-out family `IN_CLASS_OOD` meets the threshold | True |
| every off-grid regime also meets the threshold | False |
| in-span membership and split disjointness | True |
| posterior calibration within band | False |

Runtime: median 0.24 s per (arm, estimator, SNR, regime)
block over 960 blocks.

## Artifacts

- `artifacts/configs/R0C_REPAIRED_SOURCE_AND_CALIBRATION_FREEZE.json` `5a59d5e6203d9657...`
- `artifacts/CANONICAL_ARTIFACT_FREEZE_V2.json` `1b4e6f2230c1e877...`
- `docs/amendments/R0_REPAIR_AMENDMENT_004.md` `503733a111dff0ce...`
- `artifacts/manifests/r0c_future_test_hash_commitment.json` `b6bfbd00b03b3153...`
- `artifacts/manifests/r0c_split_hash_manifest.json` `4fd93375498372c2...`
- `artifacts/tables/r0c_age_errors.parquet` `2d37c5f7b57353a5...`
- `artifacts/tables/r0c_stable_depth.parquet` `5cdf43376b369099...`
- `artifacts/tables/r0c_family_depth.parquet` `66e7b810655bdb81...`
- `artifacts/tables/r0c_estimator_selection.parquet` `b7dc2d2f6da46e53...`
- `artifacts/tables/r0c_data_weak_errors.parquet` `0310060b4437829a...`
- `artifacts/tables/r0c_calibration.parquet` `c35919dd59a779fb...`
- `artifacts/tables/r0c_covariance_scales.parquet` `f6c02b2c523fc9de...`
- `artifacts/tables/r0c_representation_floor.parquet` `1de8cfd9a4b8bcbf...`
- `artifacts/tables/r0c_representation_floor_depth.parquet` `4c6bb80e50d3bcc5...`
- `artifacts/tables/r0c_runtime.parquet` `d6756bdfb87682e9...`
- `artifacts/gates/correctness_gates.json` `9e00307fe72e0a25...`

`artifacts/reports/R0C_REPAIRED_VALIDATION.md` is hashed in the artifact manifest, which is written after it.

## Stop

**R1_MAIN_RECOMMENDED_WITH_SCOPE_RESTRICTION**

The primary criterion passes: the exact-in-class regime shows an anchored-span gain at or above the frozen threshold, the prior-free primary and confirmatory estimators agree, and the gain is present in at least three of the four prior-fit families. Secondary criteria do not all pass, and each one that does not narrows what a main test could claim rather than removing the effect. A main test is worth running, scoped to exactly what passed here.

The restrictions, each measured above:

- off-grid: `OFF_GRID_ID` does not meet the threshold, so a claim covers truths inside the declared class only
- old band: the absolute and normalized errors fall but the structure-normalized one does not, so the old-band gain is in the age-local level rather than in age-local structure
- structure recovery: no arm recovers age-local structure at the reference SNR_0 = 100; the first non-zero structure span appears at SNR_0 = 30000
- uncertainty: withdrawn, so no interval or coverage statement accompanies any point estimate

No result here licenses a geometry-wide claim or a claim of arbitrary movie
recovery. One geometry, a* = 0.5 and i = 50 degrees; one source class, C224.
