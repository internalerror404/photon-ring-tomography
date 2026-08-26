# R1 — HELD-OUT MAIN

The sealed bank was scored once. Every hyperparameter came from the R0C
repair-validation selection, the endpoint and threshold from the R1 freeze, and
the bootstrap count and seed were fixed before a main truth was rendered.

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
| `r1_config_sha256` | `ba766497f91aed4d689e48a4ca187698f6d542bc2b24b989d86fd5c7167060d7` |
| `r0c_execution_commit` | `b6e481ab133015e9d7089fcbe6cfd81496200057` |
| `r0c_artifact_commit` | `446fa00d0fadece4648118f29871bc615a16d9d7` |

- R1 freeze sha256 `4ef162320e09086a16f1e130b09a507d399438740647147560f339cd2aa60069`
- execution commit `5f557fb606b76a95093cbf8e98d89d6f1dab9664`, head tree `0e3370106cd614bc5755c381f993c8f133dc7ea4`
- freeze committed at that commit: **True**;
  tracked changes 0, untracked 1
- sealed bank commitment `93608e7a7578fe892269ac20297af5d3f22bc1f860bbdba71b9aa0a833aa3f1e`
- null-pair control bank `57ee7fef85da0ff05b0a36df75331607eca9ea76b575067b02bda8ae98002806`
- registry `2ba66f0209fe1cdec97b8cf5862494c22fb94704318f9601a7a1f9eb4b783796`, environment `00bf00f9bb7f2905ea69b970f9f75880c0f7ea32fca29da43b1f46bb212fe7d1`

A run's identity is its `execution_commit`, taken from the start-of-run
attestation, per `REVIEWER_RULING_R0C_005`. `manifest_build_commit` is recorded
separately and `git_commit` is deprecated.

## Integrity and correctness

| gate | status | measured | threshold | disposition |
|---|---|---:|---:|---|
| `R1_G1_sealed_bank_matches_commitment` | **PASS** | 0 | 0 | – |
| `R1_G2_in_span_membership` | **PASS** | 0 | 1e-10 | – |
| `R1_G3_split_isolation` | **PASS** | 0 | 0 | – |
| `R1_G4_hyperparameters_frozen_from_validation` | **PASS** | 240 | 240 | – |
| `R1_G5_null_pair_control_bank` | **PASS** | 78 | 91 | – |
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

The five `R1_G*` gates run before any operator touches a main truth: the sealed
records are regenerated from their committed stream and checked hash by hash,
in-span membership is measured away from the projection grid, the main bank is
checked against every R0C split, and every hyperparameter is read from the R0C
selection rather than chosen here.

## Primary result

`IN_CLASS_ID`, SNR_0 = 100, epsilon = 0.25,
q = 0.95, anchored span in M. Threshold **8 M**.

| regime | direct | resolved | delta TSVD | delta RIDGE_IDENTITY | >= 8 M | confirmed |
|---|---|---|---|---|---|---|
| IN_CLASS_ID | 48 | 80 | 32 | 32 | True | True |
| IN_CLASS_OOD | 48 | 80 | 32 | 32 | True | True |
| OFF_GRID_ID | 0 | 0 | 0 | 0 | False | False |
| OFF_GRID_OOD | 48 | 80 | 32 | 32 | True | True |

Paired truth-cluster bootstrap, 10000 resamples,
seed 20260901, unit the truth with every noise draw
travelling with it:

| estimator | delta L | CI low | CI high | excl. 0 | old-band norm. reduction | CI low | excl. 0 | old-band abs. reduction | CI low | excl. 0 |
|---|---|---|---|---|---|---|---|---|---|---|
| TSVD | 32 | 32 | 32 | True | 0.3321 | 0.3297 | True | 0.4294 | 0.4185 | True |
| RIDGE_IDENTITY | 32 | 32 | 32 | True | 0.3488 | 0.3466 | True | 0.4538 | 0.4408 | True |
| TIKHONOV_TEMPORAL | 28 | 24 | 32 | True | 0.4245 | 0.4158 | True | 0.5522 | 0.5329 | True |
| WIENER_GAUSSIAN | 4 | 0 | 16 | False | 0.005151 | 0.004761 | True | 0.006841 | 0.006245 | True |
| LINEAR_STATE_SPACE | 32 | 28 | 68 | True | 0.1751 | 0.1704 | True | 0.2245 | 0.2166 | True |

The interval on delta_L for the prior-free estimators is degenerate: every one of the 10000 resamples lands on the same value. That is quantisation, not precision. The anchored span is read off a 4 M age grid, so an effect several times the grid step and far larger than the truth-to-truth spread cannot move a percentile off its grid point. It should be read as *the resampling noise is smaller than one grid step*, not as an interval of width zero. The regularised estimators, whose spans sit nearer a grid boundary, do show non-degenerate intervals, which is the check that the resampling itself is working.

### Per prior-fit family

| family | direct | resolved | delta |
|---|---|---|---|
| correlated_extended_field | 48 | 80 | 32 |
| rotating_asymmetric_crescent | 48 | 80 | 32 |
| single_orbiting_hotspot | 48 | 80 | 32 |
| two_independent_hotspots | 48 | 80 | 32 |

**4 of 4** families reach 8 M.

### The frozen success list

| requirement | met |
|---|---|
| delta_L_level >= 8 M for TSVD | True |
| same direction and magnitude for RIDGE_IDENTITY | True |
| at least three of four prior-fit families improve by >= 8 M | True |
| 95% interval for aggregate delta_L_level excludes zero | True |
| 95% interval for the old-band normalized error reduction excludes zero | True |
| 95% interval for the old-band absolute error reduction excludes zero | True |
| lower error inside the direct channel's own data subspace | True |

## Level and structure are different results

`x = P_level x + P_structure x`, with `P_level` the orthogonal projection onto
fields constant in space at each source time, spanned by the class's own
temporal modes so the subspace lies inside C224. A deterministic diagnostic with
no threshold. `IN_CLASS_ID`, SNR_0 = 100, `TSVD`, median over truths:

| arm | level fraction of truth | level error | structure error | old-band level error | old-band structure error |
|---|---|---|---|---|---|
| DIRECT_PHYSICAL | 0.9838 | 0.2662 | 0.9272 | 0.6534 | 1.169 |
| RESOLVED_PHYSICAL | 0.9838 | 0.02824 | 0.4664 | 0.2169 | 1.141 |
| UNRESOLVED_IMAGE | 0.9838 | 0.08341 | 0.8787 | 0.4071 | 1.302 |
| TOTAL_FLUX | 0.9838 | 0.2274 | 1.758 | 0.2259 | 1.71 |

### Structural recovery onset

| arm | onset SNR_0 | span at onset (M) | span at reference (M) |
|---|---|---|---|
| DIRECT_PHYSICAL | 30000 | 40 | 0 |
| RESOLVED_PHYSICAL | 30000 | 76 | 0 |

Three separate things, and the difference between them is the whole point of
the projector.

**The field is overwhelmingly level.** 98.4% of the age-window norm
of a truth is its spatially constant part, which is why the registered metric is
baseline-inclusive and why an error under it is not a morphology statement.

**The level is recovered, and the resolved stack recovers it far better.** The
level error falls from 0.266 to 0.028, a factor of
9.4, and in the old band from 0.653 to 0.217.

**Structure is partly recovered on average and not at all where it would
matter.** Across all ages the structure error falls from 0.927 to
0.466, a real factor of 2.0 and below one, so
the resolved stack is recovering some age-local morphology in the median. In the
old band it is 1.169 against 1.141: both above one, essentially
unchanged, meaning neither arm recovers old-age morphology at all. And the
anchored *depth* under the structure metric is zero for every arm at the
reference SNR, because that statistic asks the far harder question of whether
95% of truths stay below tolerance across the whole
window from the anchor outward.

So the headline result is stable reconstruction of the age-local emissivity
**level** under the registered baseline-inclusive field metric. It is not
detailed movie morphology recovery at the reference SNR and must not be
described as such. The median structure improvement is real and is reported
here; it is not the endpoint and it does not survive into the old band.

## Data-supported subspace

Each arm's own `P_data` has its own dimension, so the first error columns are
not comparable across arms; the direct channel's subspace is the like-for-like
comparison.

| arm | estimator | own P_data dim | own data-supported | own weak | in direct P_data | outside direct P_data |
|---|---|---|---|---|---|---|
| DIRECT_PHYSICAL | LINEAR_STATE_SPACE | 154 | 1.209 | 6.244 | 1.209 | 6.244 |
| DIRECT_PHYSICAL | RIDGE_IDENTITY | 154 | 0.8504 | 1.54 | 0.8504 | 1.54 |
| DIRECT_PHYSICAL | TIKHONOV_TEMPORAL | 154 | 0.701 | 5.862 | 0.701 | 5.862 |
| DIRECT_PHYSICAL | TSVD | 154 | 0.986 | 1.54 | 0.986 | 1.54 |
| DIRECT_PHYSICAL | WIENER_GAUSSIAN | 154 | 1.146 | 0.8771 | 1.146 | 0.8771 |
| RESOLVED_PHYSICAL | LINEAR_STATE_SPACE | 202 | 4.147 | 3.469 | 0.7511 | 5.463 |
| RESOLVED_PHYSICAL | RIDGE_IDENTITY | 202 | 0.8875 | 0.719 | 0.4446 | 1.057 |
| RESOLVED_PHYSICAL | TIKHONOV_TEMPORAL | 202 | 1.963 | 3.115 | 0.3961 | 3.726 |
| RESOLVED_PHYSICAL | TSVD | 202 | 1.058 | 0.7172 | 0.5791 | 1.144 |
| RESOLVED_PHYSICAL | WIENER_GAUSSIAN | 202 | 1.327 | 0.4586 | 1.111 | 0.8528 |
| TOTAL_FLUX | LINEAR_STATE_SPACE | 14 | 0.7225 | 106.1 | 46.25 | 95.45 |
| TOTAL_FLUX | RIDGE_IDENTITY | 14 | 0.366 | 2.019 | 1.582 | 1.315 |
| TOTAL_FLUX | TIKHONOV_TEMPORAL | 14 | 1.71e+05 | 3.4e+09 | 1.25e+09 | 3.162e+09 |
| TOTAL_FLUX | TSVD | 14 | 0.6242 | 2.02 | 1.683 | 1.341 |
| TOTAL_FLUX | WIENER_GAUSSIAN | 14 | 0.2877 | 2.341 | 1.988 | 1.277 |
| UNRESOLVED_IMAGE | LINEAR_STATE_SPACE | 183 | 2.71 | 5.642 | 1.121 | 6.17 |
| UNRESOLVED_IMAGE | RIDGE_IDENTITY | 183 | 0.917 | 1.176 | 0.642 | 1.352 |
| UNRESOLVED_IMAGE | TIKHONOV_TEMPORAL | 183 | 1.397 | 5.058 | 0.5107 | 5.234 |
| UNRESOLVED_IMAGE | TSVD | 183 | 1.118 | 1.176 | 0.8117 | 1.41 |
| UNRESOLVED_IMAGE | WIENER_GAUSSIAN | 183 | 1.266 | 0.707 | 1.151 | 0.8798 |

## Old band beyond 57.7 M

| regime | arm | normalized | absolute | structure-normalized |
|---|---|---|---|---|
| IN_CLASS_ID | DIRECT_PHYSICAL | 0.6674 | 0.8132 | 1.18 |
| IN_CLASS_ID | RESOLVED_PHYSICAL | 0.3142 | 0.358 | 1.192 |
| IN_CLASS_ID | TOTAL_FLUX | 0.4269 | 0.5493 | 1.736 |
| IN_CLASS_ID | UNRESOLVED_IMAGE | 0.5046 | 0.5872 | 1.39 |
| IN_CLASS_OOD | DIRECT_PHYSICAL | 0.6522 | 0.6542 | 12.61 |
| IN_CLASS_OOD | RESOLVED_PHYSICAL | 0.319 | 0.3204 | 18.66 |
| IN_CLASS_OOD | TOTAL_FLUX | 0.4032 | 0.4055 | 21.88 |
| IN_CLASS_OOD | UNRESOLVED_IMAGE | 0.5139 | 0.5177 | 20.27 |
| OFF_GRID_ID | DIRECT_PHYSICAL | 0.668 | 0.6865 | 1.801 |
| OFF_GRID_ID | RESOLVED_PHYSICAL | 0.3305 | 0.3383 | 2.269 |
| OFF_GRID_ID | TOTAL_FLUX | 0.4147 | 0.4452 | 2.737 |
| OFF_GRID_ID | UNRESOLVED_IMAGE | 0.5213 | 0.5406 | 2.59 |
| OFF_GRID_OOD | DIRECT_PHYSICAL | 0.6617 | 0.6621 | 12.86 |
| OFF_GRID_OOD | RESOLVED_PHYSICAL | 0.3221 | 0.3222 | 18.85 |
| OFF_GRID_OOD | TOTAL_FLUX | 0.4032 | 0.4034 | 22.25 |
| OFF_GRID_OOD | UNRESOLVED_IMAGE | 0.5208 | 0.521 | 21.35 |

## Null-pair controls

Directions committed before scoring, amplitudes solved at run time because they
are a property of the operator. A method above the equal-prior Gaussian Bayes
bound beyond Monte-Carlo tolerance is reading information the likelihood does
not contain.

| arm | delta | P_Bayes | observed | observed - bound | MC tolerance | pairs | above bound |
|---|---|---|---|---|---|---|---|
| DIRECT_PHYSICAL | 0.25 | 0.5497 | 0.5509 | 0.001131 | 0.04397 | 200 | 8 |
| DIRECT_PHYSICAL | 0.50 | 0.5987 | 0.5993 | 0.0005808 | 0.04332 | 200 | 4 |
| DIRECT_PHYSICAL | 1.00 | 0.6915 | 0.6896 | -0.001853 | 0.04083 | 200 | 7 |
| DIRECT_PHYSICAL | 2.00 | 0.8413 | 0.8395 | -0.001892 | 0.03229 | 200 | 3 |
| DIRECT_PHYSICAL | 4.00 | 0.9772 | 0.9776 | 0.0003576 | 0.01318 | 200 | 2 |
| RESOLVED_PHYSICAL | 0.25 | 0.5497 | 0.5497 | -5.072e-05 | 0.04397 | 200 | 6 |
| RESOLVED_PHYSICAL | 0.50 | 0.5987 | 0.5946 | -0.004077 | 0.04332 | 200 | 3 |
| RESOLVED_PHYSICAL | 1.00 | 0.6915 | 0.6929 | 0.001477 | 0.04083 | 200 | 4 |
| RESOLVED_PHYSICAL | 2.00 | 0.8413 | 0.8402 | -0.001149 | 0.03229 | 200 | 1 |
| RESOLVED_PHYSICAL | 4.00 | 0.9772 | 0.977 | -0.0002772 | 0.01318 | 200 | 5 |
| TOTAL_FLUX | 0.25 | 0.5497 | 0.5485 | -0.001271 | 0.04397 | 200 | 3 |
| TOTAL_FLUX | 0.50 | 0.5987 | 0.6009 | 0.002231 | 0.04332 | 200 | 4 |
| TOTAL_FLUX | 1.00 | 0.6915 | 0.6937 | 0.002278 | 0.04083 | 200 | 8 |
| TOTAL_FLUX | 2.00 | 0.8413 | 0.8414 | 6.15e-05 | 0.03229 | 200 | 5 |
| TOTAL_FLUX | 4.00 | 0.9772 | 0.9778 | 0.0005333 | 0.01318 | 200 | 1 |
| UNRESOLVED_IMAGE | 0.25 | 0.5497 | 0.5503 | 0.0005547 | 0.04397 | 200 | 1 |
| UNRESOLVED_IMAGE | 0.50 | 0.5987 | 0.5984 | -0.0003372 | 0.04332 | 200 | 4 |
| UNRESOLVED_IMAGE | 1.00 | 0.6915 | 0.6912 | -0.0002808 | 0.04083 | 200 | 4 |
| UNRESOLVED_IMAGE | 2.00 | 0.8413 | 0.8408 | -0.0005147 | 0.03229 | 200 | 4 |
| UNRESOLVED_IMAGE | 4.00 | 0.9772 | 0.9781 | 0.0008947 | 0.01318 | 200 | 1 |

4000 committed pairs scored against the equal-prior Gaussian Bayes bound; binomial p for the excess 0.927; 0 direction hash mismatches. a defect requires an excess beyond binomial multiplicity, not a single two-sigma excursion

## Off-grid regimes

Both preserved. `OFF_GRID_OOD` carries the caveat recorded in the freeze: its
representation floor in R0C was 0.016 to 0.115 structure-normalized against
`OFF_GRID_ID`'s 0.803 to 0.814, so it is a **mild-mismatch diagnostic** and its
passing is not evidence of broad off-grid robustness.

## Uncertainty

**WITHDRAWN.** the R0C joint calibration gate failed literally: the state-space posterior sits at 0.497 against a frozen lower bound of 0.5 and Wiener within the band. The rule was one scalar per estimator family and the branch was frozen in advance Wiener and
the state-space model are retained as point estimators. No credible interval,
posterior movie or coverage statement appears anywhere in this report.

## Secondary outcomes

| outcome | met |
|---|---|
| held-out family IN_CLASS_OOD meets the threshold | True |
| both off-grid regimes meet the threshold | False |
| age-local structure is recovered at the reference SNR_0 = 100 | False |
| posterior uncertainty is available | False |

Runtime: median 0.61 s per (arm, estimator, SNR, regime)
block over 960 blocks.

## Artifacts

- `artifacts/configs/R1_MAIN_FREEZE.json` `4ef162320e09086a...`
- `artifacts/configs/REVIEWER_RULING_R0C_005.json` `858aa9b4cd2c29c5...`
- `artifacts/manifests/r0c_future_test_hash_commitment.json` `b6bfbd00b03b3153...`
- `artifacts/manifests/r1_null_pair_control_bank.json` `6f28c9593dfc3c7b...`
- `artifacts/tables/r1_stable_depth.parquet` `4d7a275bd698a2b1...`
- `artifacts/tables/r1_age_errors.parquet` `a9c288791923356c...`
- `artifacts/tables/r1_family_depth.parquet` `44fd05e04e1c37e6...`
- `artifacts/tables/r1_data_weak_errors.parquet` `dc617e74b91b68ef...`
- `artifacts/tables/r1_level_structure.parquet` `72aa18bb559b0947...`
- `artifacts/tables/r1_bootstrap.parquet` `f18db08de5748c1b...`
- `artifacts/tables/r1_null_pairs.parquet` `5bc5e7bcf2da03aa...`
- `artifacts/tables/r1_runtime.parquet` `34a30b3938e0d50f...`
- `artifacts/gates/correctness_gates.json` `1098c192f86be2e6...`

## Stop

**R1_PASS_WITH_SCOPE_RESTRICTION**

The exact-in-class aggregate primary passes: the anchored-span gain reaches the frozen threshold, the prior-free primary and confirmatory estimators agree, at least three of four prior-fit families pass, the bootstrap intervals exclude zero, the common-subspace and old-band level errors improve, and every integrity control passes. The scope is restricted by what did not: one geometry, one source class, no detailed structure at the reference SNR, off-grid recovery failing, and posterior uncertainty withdrawn.

### What may be claimed

> At the registered Kerr geometry a* = 0.5, i = 50 degrees, under ideal order-resolved image observations and for source histories exactly represented in the C224 class, stacking photon-ring orders n = 0, 1, 2 increases the stable span of baseline-inclusive age-local emissivity reconstruction relative to the direct image. The result is reproduced by prior-free TSVD and ridge estimators and survives a held-out dynamical family. It does not establish detailed morphology recovery at the reference SNR, robust off-grid inversion, calibrated posterior uncertainty, or arbitrary movie reconstruction.

Reported separately, and not merged with the statement above because one concerns level fidelity at the reference SNR and the other concerns structure at much higher SNR:

> Resolved higher orders extend the structural historical span once that regime is reached, 76 M against 40 M at SNR_0 = 30000.

The onset itself is not lowered on this bank: both arms first show nonzero structure at SNR_0 = 30000. Only the span at and beyond that point differs.

No result here licenses a geometry-wide claim or a claim of arbitrary movie
recovery. One geometry, a* = 0.5 and i = 50 degrees; one source class, C224.
