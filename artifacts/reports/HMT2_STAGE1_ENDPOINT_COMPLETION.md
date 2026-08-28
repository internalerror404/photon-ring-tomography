# HMT-2 stage 1 — endpoint completion

Amendment `HMT2_STAGE1_ENDPOINT_COMPLETION_AMENDMENT_020`, run `HMT2S1C_20260828T060401Z_2ba66f02`.
Execution commit `3c0cdc0f4e00`,
1133 s.

## Disposition

`HMT2_S1_ENDPOINT_COMPLETION_PASS` — all 11 gates pass.

**The primary endpoint reproduces bitwise: 0 differing
cells.** Same bank, same operators, same hyperparameters read from the stage 1
selection table, same SNRs, same noise draws. No selection was performed and no
truth was drawn. Everything below is an addition to a table that did not move.

One detail that had to be right: the noise draws come from a single stream over
the full key list including the selection split. This run scores only the pilot
split, so it still advances the stream over the selection keys in the same order
and discards them. Had it not, the pilot noise would differ and nothing would
have reproduced.

## 1. The effect is not an artifact of dead states

Physical target at SNR₀ = 100, dead states removed, with the fraction of states
sitting at the measure's ceiling:

| class | arm | estimator | non-dead reduction | CI low | improves | saturation direct | saturation arm |
|---|---|---|---|---|---|---|---|
| `L448_contrast` | `RESOLVED_PHYSICAL` | RIDGE_IDENTITY | +0.066 | +0.014 | **yes** | 0.573 | 0.438 |
| `L448_contrast` | `RESOLVED_PHYSICAL` | TSVD | +0.054 | +0.017 | **yes** | 0.606 | 0.413 |
| `L448_contrast` | `TOTAL_FLUX` | RIDGE_IDENTITY | +0.006 | -0.068 | no | 0.573 | 0.441 |
| `L448_contrast` | `TOTAL_FLUX` | TSVD | +0.046 | +0.020 | **yes** | 0.606 | 0.451 |
| `L448_contrast` | `UNRESOLVED_IMAGE` | RIDGE_IDENTITY | +0.000 | -0.000 | no | 0.573 | 0.548 |
| `L448_contrast` | `UNRESOLVED_IMAGE` | TSVD | +0.000 | -0.001 | no | 0.606 | 0.577 |
| `L896_radial_enriched` | `RESOLVED_PHYSICAL` | RIDGE_IDENTITY | +0.123 | +0.078 | **yes** | 0.570 | 0.416 |
| `L896_radial_enriched` | `RESOLVED_PHYSICAL` | TSVD | +0.104 | +0.059 | **yes** | 0.546 | 0.420 |
| `L896_radial_enriched` | `TOTAL_FLUX` | RIDGE_IDENTITY | -0.030 | -0.105 | no | 0.570 | 0.413 |
| `L896_radial_enriched` | `TOTAL_FLUX` | TSVD | +0.042 | +0.005 | **yes** | 0.546 | 0.409 |
| `L896_radial_enriched` | `UNRESOLVED_IMAGE` | RIDGE_IDENTITY | +0.000 | +0.000 | no | 0.570 | 0.545 |
| `L896_radial_enriched` | `UNRESOLVED_IMAGE` | TSVD | +0.025 | -0.041 | no | 0.546 | 0.382 |

The resolved arm in the primary class keeps a material reduction with dead
states removed -- so the concern raised when stage 1 was reported does not
overturn the headline.

**But the measure is saturated for most states.** 56% of
direct-image states sit at the ceiling of 1.0, falling to about 41% for the
resolved arm. When more than half the states are at the maximum, the mean is
largely counting *how many states are saturated*, and "improvement" mostly means
"fewer total failures" rather than "better estimates". That is a real
measurement, and it is not the same statement as the error decreasing smoothly.

It also explains the total-flux behaviour more fully than the dead-state
account did. `TOTAL_FLUX` under TSVD still shows a positive non-dead reduction,
because a near-null estimator produces a stable wrong answer that does not
saturate, while the direct image produces a wildly wrong one that does. The
soft spot is saturation, not dead states alone.

## 2. The two-feature result is not estimator-robust

Stable multi-resolved states only, both estimators and both SNRs, resolved arm.
Cost is normalised so 1.0 is one whole feature gained or lost.

| class | arm | estimator | SNR₀ | direct | arm | reduction | CI low | improves |
|---|---|---|---|---|---|---|---|---|
| `L448_contrast` | `RESOLVED_PHYSICAL` | RIDGE_IDENTITY | 100 | 1.469 | 1.723 | -0.182 | -0.455 | no |
| `L448_contrast` | `RESOLVED_PHYSICAL` | RIDGE_IDENTITY | 1000 | 1.477 | 1.724 | -0.192 | -0.439 | no |
| `L448_contrast` | `RESOLVED_PHYSICAL` | TSVD | 100 | 1.493 | 1.869 | -0.108 | -0.537 | no |
| `L448_contrast` | `RESOLVED_PHYSICAL` | TSVD | 1000 | 1.494 | 1.883 | -0.117 | -0.547 | no |
| `L896_radial_enriched` | `RESOLVED_PHYSICAL` | RIDGE_IDENTITY | 100 | 1.331 | 1.280 | +0.116 | +0.007 | **yes** |
| `L896_radial_enriched` | `RESOLVED_PHYSICAL` | RIDGE_IDENTITY | 1000 | 1.323 | 1.248 | +0.121 | +0.021 | **yes** |
| `L896_radial_enriched` | `RESOLVED_PHYSICAL` | TSVD | 100 | 1.451 | 1.376 | +0.097 | -0.030 | no |
| `L896_radial_enriched` | `RESOLVED_PHYSICAL` | TSVD | 1000 | 1.451 | 1.388 | +0.087 | -0.031 | no |

This is what item 9 was for, and the answer is negative. In the primary class
the ridge estimator improves the conditional cost marginally, with an interval
that barely clears zero, and **TSVD does not improve it at all** at either SNR.
In the representation-limited control class the resolved arm makes it
substantially *worse* under both estimators. Twelve truths carry these states.

`HMT2_S1_ESTIMATOR_ROBUST_TWO_FEATURE_RESULT_NOT_RUN` recorded that no such
statement existed. Now that it has been run, the statement is that two-feature
recovery is estimator-dependent and not established.

## 3. The all-state effect is heterogeneous across families

Primary class, resolved arm, SNR₀ = 100, physical target, six truths per family:

| family | estimator | reduction | CI low | improves |
|---|---|---|---|---|
| `circular_hotspot_trajectory` | RIDGE_IDENTITY | +0.066 | -0.108 | no |
| `circular_hotspot_trajectory` | TSVD | +0.079 | -0.110 | no |
| `flare_birth_motion_decay` | RIDGE_IDENTITY | +0.283 | +0.019 | **yes** |
| `flare_birth_motion_decay` | TSVD | +0.233 | +0.062 | **yes** |
| `m1_rotating_crescent` | RIDGE_IDENTITY | +0.178 | +0.011 | **yes** |
| `m1_rotating_crescent` | TSVD | +0.120 | +0.044 | **yes** |
| `m2_structural_mode` | RIDGE_IDENTITY | +0.233 | +0.062 | **yes** |
| `m2_structural_mode` | TSVD | +0.223 | -0.042 | no |
| `plunging_feature` | RIDGE_IDENTITY | +0.108 | +0.074 | **yes** |
| `plunging_feature` | TSVD | +0.099 | +0.042 | **yes** |
| `two_hotspot_trajectories` | RIDGE_IDENTITY | +0.133 | -0.013 | no |
| `two_hotspot_trajectories` | TSVD | +0.127 | +0.059 | **yes** |

Four of six families improve under each estimator, but not the same four.
`circular_hotspot_trajectory` -- the simplest family in the bank -- improves
under neither. `two_hotspot_trajectories` improves under TSVD and not ridge;
`m2_structural_mode` the reverse. With six truths per family these intervals are
wide, and the honest reading is that the aggregate effect is not uniform and no
family-level claim is supported.

## 4. The class-conditional label ambiguity has no numerical effect

| estimator | analytic label | projected label | difference |
|---|---|---|---|
| RIDGE_IDENTITY | +0.1462 | +0.1462 | 0.00e+00 |
| TSVD | +0.1217 | +0.1217 | 0.00e+00 |

The recorded defect was real -- the target compared against the in-class
projection while taking the per-state measure from the analytic label, and which
label should govern was never decided. Computing both shows the choice does not
move the number here. The ambiguity is resolved by measurement rather than by
argument, and the answer is that it did not matter.

## 5. There is no stable age-resolved morphology interval

At the campaign's declared tolerance and quantile:

| class | arm | estimator | L_stable (M) | mean reach (M) | fraction reaching |
|---|---|---|---|---|---|
| `L448_contrast` | `DIRECT_PHYSICAL` | RIDGE_IDENTITY | 0.0 | 2.10 | 0.160 |
| `L448_contrast` | `DIRECT_PHYSICAL` | TSVD | 0.0 | 2.07 | 0.167 |
| `L448_contrast` | `RESOLVED_PHYSICAL` | RIDGE_IDENTITY | 0.0 | 0.99 | 0.090 |
| `L448_contrast` | `RESOLVED_PHYSICAL` | TSVD | 0.0 | 0.40 | 0.042 |
| `L448_contrast` | `TOTAL_FLUX` | RIDGE_IDENTITY | 0.0 | 1.06 | 0.076 |
| `L448_contrast` | `TOTAL_FLUX` | TSVD | 0.0 | 1.11 | 0.083 |
| `L448_contrast` | `UNRESOLVED_IMAGE` | RIDGE_IDENTITY | 0.0 | 2.08 | 0.160 |
| `L448_contrast` | `UNRESOLVED_IMAGE` | TSVD | 0.0 | 2.06 | 0.167 |
| `L896_radial_enriched` | `DIRECT_PHYSICAL` | RIDGE_IDENTITY | 0.0 | 7.18 | 0.285 |
| `L896_radial_enriched` | `DIRECT_PHYSICAL` | TSVD | 0.0 | 3.88 | 0.167 |
| `L896_radial_enriched` | `RESOLVED_PHYSICAL` | RIDGE_IDENTITY | 0.0 | 5.32 | 0.167 |
| `L896_radial_enriched` | `RESOLVED_PHYSICAL` | TSVD | 0.0 | 7.19 | 0.160 |
| `L896_radial_enriched` | `TOTAL_FLUX` | RIDGE_IDENTITY | 0.0 | 1.25 | 0.118 |
| `L896_radial_enriched` | `TOTAL_FLUX` | TSVD | 0.0 | 1.50 | 0.111 |
| `L896_radial_enriched` | `UNRESOLVED_IMAGE` | RIDGE_IDENTITY | 0.0 | 7.18 | 0.285 |
| `L896_radial_enriched` | `UNRESOLVED_IMAGE` | TSVD | 0.0 | 0.76 | 0.049 |

Zero for every arm, class and estimator. Between 4% and 28% of realizations are
inside the tolerance at age zero at all, and the mean reach never exceeds about
7 M. So the improvement in the all-state morphology error does not produce any
age interval over which the recovered morphology stays within tolerance at 95%
confidence -- the same structural outcome HMT-1 found for its feature interval,
now measured on a resolution-aware error.

## 6. What the completion changes

Nothing in the primary endpoint, by construction and by check. What it changes
is what may be said around it:

- the all-state reduction survives the removal of dead states, so
  `HMT2_S1_SUBSTANTIVE_ALL_STATE_MORPHOLOGY_ERROR_REDUCTION` stands, with the
  saturation caveat attached to it;
- `HMT2_S1_ACCURATE_MORPHOLOGY_RECOVERY_NOT_ESTABLISHED` is strengthened: the
  stable morphology interval is zero everywhere and over half of states are at
  the measure's ceiling;
- `HMT2_S1_ESTIMATOR_ROBUST_TWO_FEATURE_RESULT_NOT_RUN` is discharged, and its
  successor finding is that the two-feature result is estimator-dependent;
- `HMT2_S1_UNRESOLVED_NO_CONFIRMED_GAIN` is unchanged;
- `HMT2_S1_PASS_RULE_HAS_NO_EFFECT_SIZE_FLOOR` stands as recorded. The rule was
  not changed after the fact. Effect sizes and intervals are reported
  throughout so a floor can be applied by inspection.

## 7. Gates

| gate | status | measured | threshold |
|---|---|---|---|
| `HMT2C_G1_pinned_numerical_environment` | PASS | 1 | 1 |
| `HMT2C_G2_primary_endpoint_reproduces_bitwise` | PASS | 0 | 0 |
| `HMT2C_G3_no_selection_performed` | PASS | 0 | 0 |
| `HMT2C_G4_all_draws_decomposed` | PASS | 4 | 4 |
| `HMT2C_G5_stable_multi_both_estimators_and_snrs` | PASS | 4 | 4 |
| `HMT2C_G6_both_class_conditional_companions` | PASS | 1 | 1 |
| `HMT2C_G7_blended_not_forced_into_two_tracks` | PASS | 0 | 0 |
| `HMT2C_G8_non_dead_companion_emitted` | PASS | 24 | 1 |
| `HMT2C_G9_saturation_fractions_emitted` | PASS | 1 | 1 |
| `HMT2C_G10_per_family_effects_emitted` | PASS | 144 | 1 |
| `HMT2C_G11_stable_age_interval_emitted` | PASS | 32 | 1 |

**STOP.** On this pass, item 11 authorizes registering one sealed main before
any held-out truth is drawn, which is a separate registration. Order leakage,
geometry mismatch, VLBI, machine learning and a new pixel-movie campaign remain
unauthorized.
