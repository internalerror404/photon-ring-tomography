# R0 CANARY RECONSTRUCTION PILOT

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

- start commit `7d610121adc95fb641ab5692d37d2b761b082039`
- end commit `e1619fa046a765e4da0e8482e81301ac5f434b1c`
- branch `research/paper1_r0_canary_reconstruction_v0`
- accepted scientific base `0ef341dae3b21bc2bdd0e54a18971cff208af783`
- freeze `artifacts/configs/R0_CANARY_RECONSTRUCTION_PILOT_FREEZE.json`
  sha256 `e9c3a2d32a8bc24f638b0cb6e8fb573a72334b5e577afad9ed2b0aab5d009381`, copied into every result row
- registry sha256 `2ba66f0209fe1cdec97b8cf5862494c22fb94704318f9601a7a1f9eb4b783796`
- ray maps:
  - `a050_i050_n0_core.h5` `78e77e81f399c552...`
  - `a050_i050_n1_core.h5` `8d0b047a9dc2ecdd...`
  - `a050_i050_n2_core.h5` `a1fc26b81c9143ca...`
- environment sha256 `00bf00f9bb7f2905ea69b970f9f75880c0f7ea32fca29da43b1f46bb212fe7d1`
- hardware `Linux`, `x86_64`,
  4 logical CPUs
- scope: a* = 0.5, i = 50 deg, class C224. **Not geometry-wide, and not
  arbitrary movie recovery.**

## Correctness gates

| gate | status | measured | threshold |
|---|---|---:|---:|
| `R0_G1_dense_matrix_free_parity` | **PASS** | 2.173e-15 | 1e-10 |
| `R0_G2_physical_adjoint` | **PASS** | 6.395e-14 | 1e-08 |
| `R0_G3_G10q_quadrature_noise_invariance` | **PASS** | 7.257e-16 | 1e-10 |
| `R0_G4_mixing_covariance` | **PASS** | 5.423e-16 | 1e-10 |
| `R0_G5_basis_round_trip` | **PASS** | 0 | 1e-10 |
| `R0_G6_age_probe_normalization` | **PASS** | 5.551e-05 | 0.005 |
| `R0_G7_right_censoring` | **PASS** | 4 | 4 |
| `R0_G8_estimator_closed_form` | **PASS** | 2.169e-15 | 1e-09 |
| `R0_G12_reduced_statistic_equivalence` | **PASS** | 0.02456 | 0.08 |
| `R0_G9_noise_replay` | **PASS** | 1 | 1 |
| `R0_G10_null_pair_calibration` | **PASS** | 2.22e-16 | 0.02 |
| `R0_G11_split_hash_disjointness` | **PASS** | 0 | 0 |

Every gate passed, so R0B was authorized. `R0_G12` is an addition beyond the
launch list, explained in Deviations.

## Frozen source bank

Splits, with pairwise content-hash overlap:

- sizes: {"prior_fit_train": 2048, "validation_in_class": 512, "validation_off_grid": 320, "validation_ood": 256, "future_main_test": 320}
- worst pairwise overlap: **0**, disjoint = True
- positivity: every physical family renders a strictly positive intensity; signed null perturbations sit on the positive baseline
- held-out OOD family: `moving_flare_birth_decay`, never in the prior fit

Off-grid regime, measured rather than asserted:

| family | structure residual | fluctuation fraction | degenerate constant fraction |
|---|---|---|---|
| single_orbiting_hotspot | 0.846 | 0.05564 | 0 |
| two_independent_hotspots | 0.844 | 0.08837 | 0 |
| rotating_asymmetric_crescent | 0.788 | 0.2532 | 0 |
| correlated_extended_field | 0.7634 | 0.1013 | 0 |
| moving_flare_birth_decay | 0.8768 | 0.006703 | 0 |

The structure residual is the fraction of the *varying* part of the movie that
C224 cannot represent. The plain residual relative to the whole movie is not
reported as the regime statistic because every family sits on a positive
constant baseline that is exactly in class, which dilutes it to near zero and
would make a genuinely off-grid truth look in-class.

Future main-test bank: **generated and hashed, not rendered and not scored**.
Commitment sha256 `d7e472d34d21f54e00b1fee3454e6395ce1b9e248727785bef707e780cc1d31e`,
{"single_orbiting_hotspot": 64, "two_independent_hotspots": 64, "rotating_asymmetric_crescent": 64, "correlated_extended_field": 64, "moving_flare_birth_decay": 64}.

## Estimator verification and frozen grids

Closed-form parity is in `R0_G8` above: every estimator matches its dense
reference to better than 1e-9 in float64, and the state-space precision built
sequentially matches a directly formed tridiagonal.

Frozen hyperparameter grids, created before the first validation score:

- `TSVD`: {"cut_on": "sigma_i / sigma_max", "grid": "15 points"}
- `RIDGE_IDENTITY`: {"cut_on": "lambda / lambda_max(G)", "grid": "21 points"}
- `TIKHONOV_TEMPORAL`: {"cut_on": "lambda / lambda_max(A^T C^-1 A)", "grid": "21 points"}
- `WIENER_GAUSSIAN`: {"cut_on": "covariance shrinkage", "grid": "13 points"}
- `LINEAR_STATE_SPACE`: {"process_noise": "7 points", "observation_noise": "1 points", "note": "observation noise is fixed at the declared whitened scale; the arm may not choose its own sigma"}

Selection is lexicographic on validation data only, per arm, estimator and SNR.
The oracle variant is computed and carried as `ORACLE_UPPER_BOUND` in
`r0_pilot_estimator_selection.parquet`; it is never selected from.

## What the metric can reach at best: the representation floor

The truths are rendered analytically at the class's resolvable scale, so even
the exact least-squares projection of a truth onto C224 leaves a residual. That
residual belongs to the class and the truth, not to any estimator or arm, and
it is the floor every number below sits on. Reporting reconstruction errors
without it would invite reading a class-approximation limit as a reconstruction
result.

On `validation_in_class`, over the age grid:

- registered normalized error, floor: **0.063 to 0.071** (median over truths, per age)
- structure-normalized error, floor: **0.406 to 0.426**

The anchored span the floor itself achieves, cell by cell. This is the ceiling
on any estimator's depth within the declared class:

| epsilon | q | registered | structure |
|---|---|---|---|
| 0.25 | 0.80 | 120 | 0 |
| 0.25 | 0.90 | 120 | 0 |
| 0.25 | 0.95 | 120 | 0 |
| 0.35 | 0.80 | 120 | 0 |
| 0.35 | 0.90 | 120 | 0 |
| 0.35 | 0.95 | 120 | 0 |
| 0.50 | 0.80 | 120 | 0 |
| 0.50 | 0.90 | 120 | 0 |
| 0.50 | 0.95 | 120 | 0 |

The structure column is the consequential one. Its median floor of
0.41 to 0.43 sits below the loosest registered
epsilon of 0.50, but a
median is not a quantile: across truths, the largest fraction that clears any
registered epsilon at the anchor is **62%**, and the smallest
registered q is 80%. **No estimator can produce a non-zero
structure-normalized anchored depth in this pilot**, not because the estimators
fail but because the declared class cannot represent the age-local structure of
enough of these truths to within any registered tolerance. The epsilon grid is
not changed after the fact -- the freeze forbids it -- so the floor is reported
beside it and the structure columns below are read against the floor, not
against zero.

## Validation-only reconstruction

Primary point `T_stable_anchor(epsilon = 0.50, q = 0.90)`, reported as the
anchored span `L_stable_anchor = T_stable_anchor - a_anchor` with
`a_anchor = 0 M`, on `validation_in_class`, best estimator per arm
and SNR:

| SNR_0 | DIRECT | RESOLVED | UNRESOLVED | TOTAL_FLUX | resolved - direct | best estimator |
|---|---|---|---|---|---|---|
| 1 | 120 | 120 | 120 | 120 | 0 | WIENER_GAUSSIAN |
| 3 | 120 | 120 | 120 | 120 | 0 | WIENER_GAUSSIAN |
| 10 | 120 | 120 | 120 | 120 | 0 | WIENER_GAUSSIAN |
| 30 | 120 | 120 | 120 | 120 | 0 | WIENER_GAUSSIAN |
| 100 | 120 | 120 | 120 | 120 | 0 | WIENER_GAUSSIAN |
| 300 | 120 | 120 | 120 | 120 | 0 | TSVD |
| 1000 | 120 | 120 | 120 | 120 | 0 | TSVD |
| 3000 | 120 | 120 | 120 | 120 | 0 | TSVD |
| 10000 | 120 | 120 | 120 | 120 | 0 | WIENER_GAUSSIAN |
| 30000 | 120 | 120 | 120 | 120 | 0 | TSVD |
| 100000 | 120 | 120 | 120 | 120 | 0 | RIDGE_IDENTITY |
| 1000000 | 120 | 120 | 120 | 120 | 0 | TSVD |

**Headline at the registered primary point: no positive resolved-minus-direct gain at any SNR.**
Read the next section before reading anything into that.
The largest gain over the sweep is **0.0 M**, against an age-grid
step of 4 M; a gain of at least one step at two or more consecutive
SNR values is absent.

### Can the registered endpoint measure anything here?

Ask this before asking whether the arms differ. A cell in which every arm is
pinned at the age-grid ceiling, or every arm is zero, compares two censored
numbers and says nothing either way.

At the registered primary point epsilon = 0.50, q = 0.90, **30%**
of rows are right-censored and the best estimator in every arm at every SNR sits
at the ceiling 120 M. The primary point is therefore
**uninformative**.

The ceiling cannot be raised. The largest delay in the frozen ray set is
119.8 M, so
no ray in this observation carries information about an age beyond it. A
saturated depth here is a statement about the tolerance, not about how far back
the arm can see.

Cell by cell over the registered surface, `validation_in_class`, best estimator
per arm and SNR:

| epsilon | q | can measure | SNRs with a gain >= step | max gain (M) | min gain (M) | consecutive | primary |
|---|---|---|---|---|---|---|---|
| 0.25 | 0.80 | True | 0 | 0 | 0 | False | False |
| 0.25 | 0.90 | True | 11 | 44 | 0 | True | False |
| 0.25 | 0.95 | True | 12 | 44 | 8 | True | False |
| 0.35 | 0.80 | False | 0 | 0 | 0 | False | False |
| 0.35 | 0.90 | True | 0 | 0 | 0 | False | False |
| 0.35 | 0.95 | False | 0 | 0 | 0 | False | False |
| 0.50 | 0.80 | False | 0 | 0 | 0 | False | False |
| 0.50 | 0.90 | False | 0 | 0 | 0 | False | True |
| 0.50 | 0.95 | False | 0 | 0 | 0 | False | False |

**4 of 9 registered cells can measure at all, and 2 of those show a resolved-over-direct gain of at least one grid step at two or more consecutive SNR values.**

### Anchored stable-span surface

The full (epsilon, q) surface of `L_stable_anchor` in M at the reference
SNR_0 = 100, best estimator in each cell, `validation_in_class`. The age-grid
ceiling is 120 M, so a cell reading 120 is censored, not
measured. Resolved stack:

| epsilon | q = 0.8 | q = 0.9 | q = 0.95 |
|---|---|---|---|
| 0.25 | 120 | 88 | 84 |
| 0.35 | 120 | 120 | 120 |
| 0.5 | 120 | 120 | 120 |

Direct channel:

| epsilon | q = 0.8 | q = 0.9 | q = 0.95 |
|---|---|---|---|
| 0.25 | 120 | 68 | 52 |
| 0.35 | 120 | 120 | 120 |
| 0.5 | 120 | 120 | 120 |

### The informative cell, SNR by SNR

The strongest measuring cell of the registered surface is **epsilon = 0.25, q = 0.95**. It is not the registered primary point, and it is reported here as what it is: a registered cell of the frozen surface, not a tolerance chosen after seeing the answer. The primary point stays where it was frozen.

| SNR_0 | DIRECT | RESOLVED | UNRESOLVED | TOTAL_FLUX | resolved - direct |
|---|---|---|---|---|---|
| 1 | 68 | 76 | 68 | 0 | 8 |
| 3 | 64 | 72 | 64 | 0 | 8 |
| 10 | 48 | 68 | 48 | 0 | 20 |
| 30 | 48 | 80 | 60 | 0 | 32 |
| 100 | 52 | 84 | 60 | 0 | 32 |
| 300 | 52 | 88 | 64 | 0 | 36 |
| 1000 | 60 | 88 | 76 | 0 | 28 |
| 3000 | 64 | 104 | 80 | 0 | 40 |
| 10000 | 68 | 108 | 84 | 0 | 40 |
| 30000 | 72 | 112 | 104 | 0 | 40 |
| 100000 | 76 | 120 | 104 | 0 | 44 |
| 1000000 | 92 | 120 | 120 | 0 | 28 |

### Full interval reporting at the reference SNR_0 = 100

Every endpoint, not just the span. `secondary_*` is the unanchored longest
passing run: it is reported with both endpoints and is **not** depth from the
present.

| arm | estimator | a_anchor | T_stable^anchor | L_stable^anchor | frac at anchor | run start | run end | run span | runs | censored | L^anchor structure |
|---|---|---|---|---|---|---|---|---|---|---|---|
| DIRECT_PHYSICAL | WIENER_GAUSSIAN | 0 | 120 | 120 | 1 | 0 | 120 | 120 | 1 | True | 0 |
| RESOLVED_PHYSICAL | WIENER_GAUSSIAN | 0 | 120 | 120 | 1 | 0 | 120 | 120 | 1 | True | 0 |
| TOTAL_FLUX | WIENER_GAUSSIAN | 0 | 120 | 120 | 0.9922 | 0 | 120 | 120 | 1 | True | 0 |
| UNRESOLVED_IMAGE | WIENER_GAUSSIAN | 0 | 120 | 120 | 1 | 0 | 120 | 120 | 1 | True | 0 |

### Paired direct-versus-resolved age-error curves

Same truths and the same coupled resolved noise draw in both arms, so the
difference is paired. Reference SNR_0 = 100, `validation_in_class`, median over
truths; the floor column is the class-approximation limit from the section
above.

| age (M) | direct E | resolved E | resolved - direct | floor | resolved - direct, structure |
|---|---|---|---|---|---|
| 0 | 0.1309 | 0.1245 | -0.006419 | 0.06365 | -0.03274 |
| 12 | 0.1061 | 0.09913 | -0.006947 | 0.06411 | -0.03009 |
| 24 | 0.09205 | 0.08891 | -0.003146 | 0.06428 | -0.01573 |
| 36 | 0.1082 | 0.09015 | -0.01808 | 0.06454 | -0.06311 |
| 48 | 0.1742 | 0.09885 | -0.07533 | 0.06373 | -0.2589 |
| 60 | 0.2434 | 0.1022 | -0.1412 | 0.06367 | -0.4571 |
| 72 | 0.3243 | 0.1318 | -0.1925 | 0.06474 | -0.4955 |
| 84 | 0.405 | 0.1923 | -0.2127 | 0.06339 | -0.2262 |
| 96 | 0.4909 | 0.3315 | -0.1594 | 0.06559 | -0.1281 |
| 108 | 1.138 | 0.8954 | -0.2426 | 0.06646 | 0.1908 |
| 120 | 2.076 | 1.593 | -0.4827 | 0.06782 | 0.6522 |

A negative difference means the resolved stack is closer to the truth at that
age.

Old-band error beyond the frozen boundary 57.7 M, median over ages,
absolute and normalized, with the structure companion:

| arm | old-band normalized | old-band absolute | old-band structure-normalized |
|---|---|---|---|
| DIRECT_PHYSICAL | 0.3945 | 0.5016 | 1.062 |
| RESOLVED_PHYSICAL | 0.1958 | 0.2427 | 0.944 |
| TOTAL_FLUX | 0.6398 | 0.7956 | 1.659 |
| UNRESOLVED_IMAGE | 0.2562 | 0.3196 | 1.044 |

Data-supported versus weak-subspace error, `validation_in_class`:

| arm | estimator | data-supported error | weak-subspace error |
|---|---|---|---|
| DIRECT_PHYSICAL | LINEAR_STATE_SPACE | 1.751 | 6.082 |
| DIRECT_PHYSICAL | RIDGE_IDENTITY | 0.9799 | 1.396 |
| DIRECT_PHYSICAL | TIKHONOV_TEMPORAL | 1.461 | 5.82 |
| DIRECT_PHYSICAL | TSVD | 0.8183 | 1.377 |
| DIRECT_PHYSICAL | WIENER_GAUSSIAN | 1.234 | 0.7551 |
| RESOLVED_PHYSICAL | LINEAR_STATE_SPACE | 4.767 | 2.613 |
| RESOLVED_PHYSICAL | RIDGE_IDENTITY | 0.7125 | 0.4825 |
| RESOLVED_PHYSICAL | TIKHONOV_TEMPORAL | 1.487 | 2.305 |
| RESOLVED_PHYSICAL | TSVD | 0.738 | 0.4761 |
| RESOLVED_PHYSICAL | WIENER_GAUSSIAN | 1.421 | 0.2182 |
| TOTAL_FLUX | LINEAR_STATE_SPACE | 1.338 | 99.1 |
| TOTAL_FLUX | RIDGE_IDENTITY | 0.4314 | 1.95 |
| TOTAL_FLUX | TIKHONOV_TEMPORAL | 2.736e+05 | 3.341e+09 |
| TOTAL_FLUX | TSVD | 0.4591 | 1.921 |
| TOTAL_FLUX | WIENER_GAUSSIAN | 0.2781 | 2.304 |
| UNRESOLVED_IMAGE | LINEAR_STATE_SPACE | 4.069 | 4.551 |
| UNRESOLVED_IMAGE | RIDGE_IDENTITY | 0.8712 | 0.8905 |
| UNRESOLVED_IMAGE | TIKHONOV_TEMPORAL | 3.799 | 4.331 |
| UNRESOLVED_IMAGE | TSVD | 0.939 | 0.8693 |
| UNRESOLVED_IMAGE | WIENER_GAUSSIAN | 1.402 | 0.4981 |

A weak-subspace improvement is a prior effect and is never described as
measured recovery.

Coverage, probabilistic estimators only:

| estimator | level | median coverage |
|---|---|---|
| LINEAR_STATE_SPACE | 0.5 | 0.9911 |
| LINEAR_STATE_SPACE | 0.9 | 0.9999 |
| LINEAR_STATE_SPACE | 0.95 | 1 |
| WIENER_GAUSSIAN | 0.5 | 0.8216 |
| WIENER_GAUSSIAN | 0.9 | 0.942 |
| WIENER_GAUSSIAN | 0.95 | 0.951 |

Joint calibration, the sharper statement: the ratio of the mean squared
Mahalanobis distance to its expectation under the reported posterior. One means
calibrated, above one means the posterior is too narrow, below one means it
is too wide.

| arm | estimator | mean chi2 / dof | median p | clipped directions | supported directions |
|---|---|---|---|---|---|
| DIRECT_PHYSICAL | LINEAR_STATE_SPACE | 0.0165 | 1 | 0 | 224 |
| DIRECT_PHYSICAL | WIENER_GAUSSIAN | 5.794 | 2.934e-13 | 0 | 224 |
| RESOLVED_PHYSICAL | LINEAR_STATE_SPACE | 0.01545 | 1 | 0 | 224 |
| RESOLVED_PHYSICAL | WIENER_GAUSSIAN | 5.782 | 5.328e-13 | 0 | 224 |
| TOTAL_FLUX | LINEAR_STATE_SPACE | 0.02341 | 1 | 0 | 224 |
| TOTAL_FLUX | WIENER_GAUSSIAN | 6.548 | 7.438e-32 | 0 | 224 |
| UNRESOLVED_IMAGE | LINEAR_STATE_SPACE | 0.01649 | 1 | 0 | 224 |
| UNRESOLVED_IMAGE | WIENER_GAUSSIAN | 5.798 | 2.407e-13 | 0 | 224 |

The posterior covariance is positive definite in exact arithmetic but is formed
by inverting a near-singular shrunk prior plus a Gram, so directions the data
and the prior barely constrain are clipped at a relative floor. The count is
reported rather than absorbed into a diagonal jitter: how much of a posterior
is numerically unsupported is exactly what a calibration statement must not
hide.

TSVD, ridge and temporal Tikhonov carry `NOT_APPLICABLE` coverage rows rather
than a fabricated interval.

Runtime: median 0.30 s per (arm, estimator, SNR, regime)
block, peak RSS 735 MB, direct linear solves with no
iterative scheme.

## Null and incremental-history pairs

Theoretical equal-prior Gaussian Bayes bound `P_Bayes = Phi(delta/2)` against
the realized accuracy, per arm and per registered separation. A method above
the bound beyond Monte-Carlo tolerance is reading information that is not in
the data, which is a defect and not a success:

| arm | delta | P_Bayes | observed | observed - bound | MC tolerance | pairs | above bound |
|---|---|---|---|---|---|---|---|
| DIRECT_PHYSICAL | 0.25 | 0.5497 | 0.5521 | 0.00241 | 0.04397 | 40 | 2 |
| DIRECT_PHYSICAL | 0.50 | 0.5987 | 0.5951 | -0.003589 | 0.04332 | 40 | 0 |
| DIRECT_PHYSICAL | 1.00 | 0.6915 | 0.6923 | 0.0008227 | 0.04083 | 40 | 1 |
| DIRECT_PHYSICAL | 2.00 | 0.8413 | 0.8408 | -0.0005733 | 0.03229 | 40 | 1 |
| DIRECT_PHYSICAL | 4.00 | 0.9772 | 0.9764 | -0.0008827 | 0.01318 | 40 | 1 |
| RESOLVED_PHYSICAL | 0.25 | 0.5497 | 0.5461 | -0.003596 | 0.04397 | 40 | 2 |
| RESOLVED_PHYSICAL | 0.50 | 0.5987 | 0.6005 | 0.001782 | 0.04332 | 40 | 2 |
| RESOLVED_PHYSICAL | 1.00 | 0.6915 | 0.6924 | 0.0009692 | 0.04083 | 40 | 2 |
| RESOLVED_PHYSICAL | 2.00 | 0.8413 | 0.8402 | -0.00111 | 0.03229 | 40 | 1 |
| RESOLVED_PHYSICAL | 4.00 | 0.9772 | 0.9786 | 0.001363 | 0.01318 | 40 | 0 |
| TOTAL_FLUX | 0.25 | 0.5497 | 0.5456 | -0.004182 | 0.04397 | 40 | 0 |
| TOTAL_FLUX | 0.50 | 0.5987 | 0.5916 | -0.007154 | 0.04332 | 40 | 0 |
| TOTAL_FLUX | 1.00 | 0.6915 | 0.6938 | 0.002385 | 0.04083 | 40 | 3 |
| TOTAL_FLUX | 2.00 | 0.8413 | 0.8435 | 0.002112 | 0.03229 | 40 | 1 |
| TOTAL_FLUX | 4.00 | 0.9772 | 0.9772 | -3.774e-06 | 0.01318 | 40 | 0 |
| UNRESOLVED_IMAGE | 0.25 | 0.5497 | 0.5439 | -0.005793 | 0.04397 | 40 | 0 |
| UNRESOLVED_IMAGE | 0.50 | 0.5987 | 0.5937 | -0.005005 | 0.04332 | 40 | 0 |
| UNRESOLVED_IMAGE | 1.00 | 0.6915 | 0.6896 | -0.001863 | 0.04083 | 40 | 1 |
| UNRESOLVED_IMAGE | 2.00 | 0.8413 | 0.8416 | 0.000208 | 0.03229 | 40 | 0 |
| UNRESOLVED_IMAGE | 4.00 | 0.9772 | 0.9777 | 0.0004357 | 0.01318 | 40 | 0 |

Null-pair calibration summary:

- pairs tested: 800
- realized-vs-target relative error: max 1.33e-15
- above the equal-prior Bayes bound beyond Monte-Carlo tolerance:
  **17**, against **18.2**
  expected under a calibrated null
- binomial p for that excess: 0.645 -> defect = False

a defect requires an excess beyond binomial multiplicity, not a single two-sigma excursion.

Incremental-history pairs, built weak under the direct arm:

- median separation per unit coefficient, direct: **7.304e-02**
- median separation per unit coefficient, resolved: **6.578e+00**
- median ratio: **90.1x**

Read carefully. The ratio is large by construction -- the direction is chosen
inside the direct arm's least-determined half-spectrum -- so it demonstrates
that the higher orders *see* directions the direct image does not. It is not a
statement that those directions are recovered at any particular SNR; that is
what the depth table above measures, and the two must not be conflated.

## What needs repairing before R1

Two independent triggers below, either of which is enough on its own.

The registered primary endpoint cannot measure this observation. The repairs
below are declared in the proposed R1 freeze rather than applied here, because
applying them after seeing the pilot is exactly what a freeze exists to
prevent.

1. **Re-point the primary tolerance at something the observation can resolve.**
   At epsilon = 0.50 the registered normalized error sits far below tolerance at
   every age out to the physical age ceiling, for every arm and every SNR, so
   the endpoint is right-censored rather than measured -- and the ceiling cannot
   be raised, because no ray in this observation carries information past it.
   The registered surface already contains cells that measure; the primary point
   has to be one of them, named before any test truth is rendered.

2. **Draw in-class truths from the span of C224.** The launch contrasts off-grid
   truths, which are not in the span of C224, with in-class ones. In this pilot
   both are rendered analytically and only the parameter scales differ, so the
   in-class regime carries a representation residual of its own and the
   structure-normalized companion is floored at zero everywhere: the class
   cannot represent the age-local structure to within any registered epsilon, so
   the companion measures the class rather than the estimator and cannot
   corroborate the registered metric. Projecting the in-class truths onto the
   class, or drawing their coefficients directly, makes that floor zero and
   leaves the off-grid regime -- where being outside the span is the whole point
   -- untouched.

3. **Recalibrate the probabilistic estimators, or stop reporting their
   posteriors.** `UNCALIBRATED_UNCERTAINTY` is a registered stop condition and
   this pilot hits it. The marginal coverage looks acceptable, which is exactly
   why the joint statistic is the one that matters: taken over all 224
   coefficients at once, the Wiener posterior is several times too narrow and
   the state-space posterior is one to two orders of magnitude too wide, with no
   directions clipped, so neither is a numerical artefact. The Gaussian prior is
   fitted on the prior-fit families and then applied to a validation mix that
   includes an off-grid and a held-out family; the mis-specification is the
   prior's, not the solver's. Until it is fixed, no uncertainty statement from
   this line may be carried into a main test, and none is made here beyond
   reporting the miscalibration itself.

None of this is an implementation defect. Every correctness gate passes, the
estimator closed forms match their dense references to better than 1e-14, the
noise replay is bitwise identical, the splits are disjoint by content hash and
the null pairs are calibrated against the Gaussian Bayes bound. What the pilot
found is that the endpoint chosen in advance is the wrong instrument for this
observation and that the fitted prior does not transfer to the validation mix.
Finding that before the main test is what a pilot is for.

## Proposed held-out R1 freeze

`artifacts/configs/R0_PROPOSED_R1_MAIN_FREEZE.json`. No test score appears
anywhere in it or here: the main-test truths were hashed but never rendered.

## Deviations

- **Start commit is not a documentation-only descendant of the accepted base.** The launch permits such a descendant; the start commit additionally carries the G10q measurement-model correction and the accepted E3B/E3C work. Starting from the bare base is impossible under this launch's own frozen model: at 0ef341d the forward coefficient is g^3 with a flat per-row sigma and no G10q gate exists, so the required whitened row is absent and R0_G3 would stop immediately with QUADRATURE_NOISE_DEFECT. Verified by inspecting the operator at both commits.
- **Governance documents supplied mid-flight.** The launch v1.0, PAPER_I_V2_RECONSTRUCTION_AMENDMENT_002, the activation ruling v1.2 and the freeze template v1.0 were supplied after registration began; the v1 evidence ledger, the v2 reconstruction handoff and the v2 experiment registry were not. Every convention those three would have supplied is pinned explicitly in the pilot freeze, and the template is now vendored at schemas/R0_CANARY_RECONSTRUCTION_PILOT_FREEZE_TEMPLATE_v1.0.json and checked leaf by leaf at registration.
- **AGE_INTERVAL_SEMANTICS_AMENDMENT_003 supersedes the launch's depth vocabulary.** The primary endpoint is the anchored T_stable^anchor with the supremum over the age window inside the probability, taken per truth, and it is reported as the span L_stable^anchor from a frozen anchor. The launch's T_contig is retained only as the secondary unanchored longest passing run, reported with both endpoints and never called depth from the present.
- **D_hist(T) and d_eff(T) are withheld from the R0 metric list.** PAPER_I_V2_PRE_E3C_AMENDMENT_001 item 6 reserves them for E3D, and the activation ruling restates that they are E3D quantities. E3D is deferred and not started, so R0 emits neither under any name; the interval statistics replace them. The withholding and its reason are recorded in the freeze rather than left as a silent omission.
- **The representation floor is reported as a first-class result.** The in-class truths are rendered analytically at the class's resolvable scale rather than drawn from the span of C224, so the exact projection onto the class already leaves a residual. Without that floor beside them the error and depth tables would read as estimator or arm results when part of what they measure is the class.
- **The registered E(a) saturates and the structure-normalized companion is reported beside it.** The registered denominator ||W_a x|| is dominated by the positive baseline every family carries and every estimator recovers trivially. The companion removes the age-local constant from residual and truth alike. Both are reported at every cell; neither replaces the other, and the registered one remains the registered one.
- **R0_G12 added beyond the launch's gate list.** The pilot simulates in the sufficient statistic b = A^T y rather than in y. That is exact for every estimator used, and is what makes the pilot tractable, but only if the reduced noise is sampled with covariance G rather than white. The gate checks it against a full-space Monte-Carlo simulation.
- **Smoke class C48 factorized as 4 x 3 x 4, not 2 x 3 x 8.** The radial factor is a cubic B-spline basis and requires at least four modes. The declared dimension is unchanged and the constraint is recorded in the freeze.
- **Existing modules reused rather than rewritten**: src/phrt/inverse/base.py already provided dense TSVD and ridge solves, and the operator, basis, ray maps and E3C age-probe machinery are reused under frozen semantics, as the launch permits.
- **Scoring uses a declared structured evaluation grid**, not the ray coordinates of any one arm. Scoring on the resolved arm's own sampling points would give it an advantage in precisely the comparison being made.
- **Null-pair defect rule accounts for multiplicity.** With hundreds of pairs each tested at a two-sigma one-sided tolerance, a few exceedances are expected under a calibrated null; a defect is declared only when the count exceeds its binomial expectation at p < 0.01.
- **ARMS.index replaces hash(arm) in the null-pair seed.** Python salts string hashes per process, which made the null-pair results differ between runs and would have violated the bitwise replay R0_G9 requires.
- **LINEAR_STATE_SPACE is a prior-structure model, not a filter.** The observation couples every temporal mode, so no sequential observation recursion applies; the estimator is the batch linear-Gaussian solution under a random-walk prior across the temporal index, and R0_G8 checks both the sequential precision construction and the batch solve.

## Artifacts

- `artifacts/configs/R0_CANARY_RECONSTRUCTION_PILOT_FREEZE.json` `e9c3a2d32a8bc24f...`
- `artifacts/configs/AGE_INTERVAL_SEMANTICS_AMENDMENT_003.json` `3395460cdb5f038a...`
- `artifacts/configs/R0_PROPOSED_R1_MAIN_FREEZE.json` `417987c11894ad74...`
- `artifacts/manifests/r0_source_bank_manifest.json` `bdc536c582f4ff9c...`
- `artifacts/manifests/r0_split_hash_manifest.json` `25f271581c958e8a...`
- `artifacts/manifests/r0_future_test_hash_commitment.json` `9387e2a157f93dd1...`
- `artifacts/manifests/r0_null_pair_summary.json` `c4be3c8641694fcf...`
- `artifacts/tables/r0_pilot_age_errors.parquet` `595fec0531a03aca...`
- `artifacts/tables/r0_pilot_stable_depth.parquet` `cada27432385a67c...`
- `artifacts/tables/r0_pilot_estimator_selection.parquet` `bb91afa4ce431058...`
- `artifacts/tables/r0_pilot_data_weak_errors.parquet` `2d1536d1ca1b9966...`
- `artifacts/tables/r0_pilot_coverage.parquet` `ee52bf87ff8e5b25...`
- `artifacts/tables/r0_pilot_null_pairs.parquet` `a528f2835560dbca...`
- `artifacts/tables/r0_pilot_incremental_pairs.parquet` `7fc9f9207782482f...`
- `artifacts/tables/r0_pilot_runtime.parquet` `da7fa1321eee10fd...`
- `artifacts/tables/r0_pilot_arm_contrasts.parquet` `a297fb54ce5a23be...`
- `artifacts/tables/r0_pilot_representation_floor.parquet` `05f88052ce3df62f...`
- `artifacts/tables/r0_pilot_representation_floor_depth.parquet` `7c93a5128cc59b57...`
- `artifacts/gates/r0_correctness_gates.json` `196312fd3bbed2b5...`

This report cannot list its own digest without changing it. `artifacts/reports/R0_CANARY_RECONSTRUCTION_PILOT.md` is hashed
in `artifacts/provenance/R0_CANARY_RECONSTRUCTION_ARTIFACT_MANIFEST.json`, which
is written after it and carries the full-length digest of every artifact above
alongside the nine provenance fields.

## Next requested authorization

**R0_REPAIR_REQUIRED**

The registered primary endpoint is right-censored for every arm at every SNR, so it compares two censored numbers and cannot answer the question either way. That is not a null result and it is not an implementation defect. Elsewhere on the same registered surface, at epsilon = 0.25, q = 0.95, the resolved stack exceeds the direct channel by up to 44 M at 12 of 12 SNR values. There is something to test, but not against this endpoint. The probabilistic estimators' joint posteriors are miscalibrated, which is the registered UNCALIBRATED_UNCERTAINTY stop condition, so no uncertainty statement from this line may be carried into a main test. The 3 repairs named above are small, are specified, and are declared in the proposed R1 freeze rather than applied after the fact.

No outcome here licenses a geometry-wide claim or a claim of arbitrary movie
recovery. The pilot is one geometry, a* = 0.5 and i = 50 degrees, and one source
class, C224.
