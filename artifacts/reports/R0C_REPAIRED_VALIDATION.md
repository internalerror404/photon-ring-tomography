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
- execution commit `759064d037e347cd42740820461f8e59bfd37a8b`, head tree
  `05c9b784720d2f92f19a9826440f01af8aa97989`
- freeze committed at that commit: **True**;
  tracked changes 0, untracked 1,
  porcelain sha256 `b230d1c04d7afbbd...`
- registry `2ba66f0209fe1cdec97b8cf5862494c22fb94704318f9601a7a1f9eb4b783796`, environment `00bf00f9bb7f2905ea69b970f9f75880c0f7ea32fca29da43b1f46bb212fe7d1`
- scope: a* = 0.5, i = 50 deg, class C224, validation only. **Not
  geometry-wide, and not arbitrary movie recovery.**

Unlike the pilot, that attestation is evidence rather than an assertion: the
check behind the pilot's `dirty_tree: false` matched no path in this layout and
could only ever say clean.

## Correctness gates

| gate | status | measured | threshold | disposition |
|---|---|---:|---:|---|
| `R0_G13_freeze_commit_attestation` | ABSENT | – | – | – |
| `R0_G1_dense_matrix_free_parity` | ABSENT | – | – | – |
| `R0_G2_physical_adjoint` | ABSENT | – | – | – |
| `R0_G3_G10q_quadrature_noise_invariance` | ABSENT | – | – | – |
| `R0_G4_mixing_covariance` | ABSENT | – | – | – |
| `R0_G5_basis_round_trip` | ABSENT | – | – | – |
| `R0_G6a_declared_probe_unit_norm` | ABSENT | – | – | – |
| `R0_G6b_independent_quadrature_crosscheck` | ABSENT | – | – | – |
| `R0_G7_right_censoring` | ABSENT | – | – | – |
| `R0_G8_estimator_closed_form` | ABSENT | – | – | – |
| `R0_G9_noise_replay` | ABSENT | – | – | – |
| `R0_G10_null_pair_calibration` | ABSENT | – | – | – |
| `R0_G11_split_hash_disjointness` | **PASS** | 0 | 0 | – |
| `R0_G12_reduced_statistic_equivalence` | ABSENT | – | – | – |
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

| arm | estimator | data-supported | weak-subspace |
|---|---|---|---|
| DIRECT_PHYSICAL | LINEAR_STATE_SPACE | 1.182 | 6.268 |
| DIRECT_PHYSICAL | RIDGE_IDENTITY | 0.8438 | 1.548 |
| DIRECT_PHYSICAL | TIKHONOV_TEMPORAL | 0.6883 | 5.912 |
| DIRECT_PHYSICAL | TSVD | 0.9794 | 1.548 |
| DIRECT_PHYSICAL | WIENER_GAUSSIAN | 1.127 | 0.8678 |
| RESOLVED_PHYSICAL | LINEAR_STATE_SPACE | 4.215 | 3.454 |
| RESOLVED_PHYSICAL | RIDGE_IDENTITY | 0.8901 | 0.7236 |
| RESOLVED_PHYSICAL | TIKHONOV_TEMPORAL | 2.007 | 3.124 |
| RESOLVED_PHYSICAL | TSVD | 1.062 | 0.7225 |
| RESOLVED_PHYSICAL | WIENER_GAUSSIAN | 1.304 | 0.4597 |
| TOTAL_FLUX | LINEAR_STATE_SPACE | 0.7061 | 103.1 |
| TOTAL_FLUX | RIDGE_IDENTITY | 0.3563 | 2.034 |
| TOTAL_FLUX | TIKHONOV_TEMPORAL | 1.711e+05 | 3.399e+09 |
| TOTAL_FLUX | TSVD | 0.6285 | 2.035 |
| TOTAL_FLUX | WIENER_GAUSSIAN | 0.2724 | 2.324 |
| UNRESOLVED_IMAGE | LINEAR_STATE_SPACE | 2.69 | 5.679 |
| UNRESOLVED_IMAGE | RIDGE_IDENTITY | 0.9201 | 1.181 |
| UNRESOLVED_IMAGE | TIKHONOV_TEMPORAL | 1.396 | 5.113 |
| UNRESOLVED_IMAGE | TSVD | 1.127 | 1.181 |
| UNRESOLVED_IMAGE | WIENER_GAUSSIAN | 1.242 | 0.7048 |

A weak-subspace improvement is a prior effect and is never described as measured
recovery. The data-supported column is the one that decides whether a prior-free
estimator is using information the higher orders supply.

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
| lower data-supported error | False |
| held-out family `IN_CLASS_OOD` meets the threshold | True |
| every off-grid regime also meets the threshold | False |
| in-span membership and split disjointness | True |
| posterior calibration within band | False |

Runtime: median 0.24 s per (arm, estimator, SNR, regime)
block over 960 blocks.

## Artifacts

- `artifacts/configs/R0C_REPAIRED_SOURCE_AND_CALIBRATION_FREEZE.json` `5a59d5e6203d9657...`
- `artifacts/CANONICAL_ARTIFACT_FREEZE_V2.json` `f7a14b33fd5d42ce...`
- `docs/amendments/R0_REPAIR_AMENDMENT_004.md` `503733a111dff0ce...`
- `artifacts/manifests/r0c_future_test_hash_commitment.json` `b6bfbd00b03b3153...`
- `artifacts/manifests/r0c_split_hash_manifest.json` `4fd93375498372c2...`
- `artifacts/tables/r0c_age_errors.parquet` `2d37c5f7b57353a5...`
- `artifacts/tables/r0c_stable_depth.parquet` `5cdf43376b369099...`
- `artifacts/tables/r0c_family_depth.parquet` `66e7b810655bdb81...`
- `artifacts/tables/r0c_estimator_selection.parquet` `840eaf1e076ba366...`
- `artifacts/tables/r0c_data_weak_errors.parquet` `0988ad5b6df9dceb...`
- `artifacts/tables/r0c_calibration.parquet` `c35919dd59a779fb...`
- `artifacts/tables/r0c_covariance_scales.parquet` `f6c02b2c523fc9de...`
- `artifacts/tables/r0c_representation_floor.parquet` `1de8cfd9a4b8bcbf...`
- `artifacts/tables/r0c_representation_floor_depth.parquet` `4c6bb80e50d3bcc5...`
- `artifacts/tables/r0c_runtime.parquet` `50ebba649c03edfc...`
- `artifacts/gates/correctness_gates.json` `b635af5d8bad3109...`

`artifacts/reports/R0C_REPAIRED_VALIDATION.md` is hashed in the artifact manifest, which is written after it.

## Stop

**RECONSTRUCTION_NEGATIVE_RESULT**

The repair took and the observability gain is real, but the reconstruction-level gain does not meet the frozen criteria on the repaired bank. This is a scientific result, not a defect: the correctness gates pass, the splits are disjoint, and the higher orders demonstrably see directions the direct image does not. What is absent is a stable-depth gain of the required size under the prior-free estimators.

No result here licenses a geometry-wide claim or a claim of arbitrary movie
recovery. One geometry, a* = 0.5 and i = 50 degrees; one source class, C224.
