# Transfer audit return: T0, T1 and the G1 closeout

Status: **TRANSFER_AUDIT_029_REVIEW_READY**

| component | status |
| --- | --- |
| curved refinement | **DEMONSTRATED** |
| full hull qualification | **QUALIFIED** |
| contour brackets | **LOCAL_BRACKETS_RESOLVED** |
| domain completeness | **PENDING_ARRAYS_NOT_PRESERVED** |
| primitive diagnosis | **CAUSE_IDENTIFIED** |
| repair validation | **NOT_RUN** |
| transfer accuracy | **NOT_QUALIFIED** |
| overall quadrature | **NOT_QUALIFIED** |
| governance | **COMPLETE** |

R3B is not authorized and was not begun.

## 1. The four G1 gaps were real

All four hold, and I accept them. The tighter-root comparison was declared and never executed. The shifted check measured radius error over mean radius, not band and response. The tessellation check normalised each shape's area change by that shape's own area. The final boolean took the last pair and the shifted radius and ignored the rest, and its width flag tested a positive total area rather than local nesting.

The tessellation arithmetic is confirmed exactly. At 4096 samples the band-normalised error is 2.456e-05 against a 1e-6 budget -- your 2.46e-5, not the 3e-7 I reported. **That reported pass was wrong.** Refining the tessellation, which costs no physical roots, fixes it:

| samples | band-normalised | detector response |
| --- | ---: | ---: |
| 4096 | 2.456e-05 | 4.606e-06 |
| 16384 | 1.535e-06 | 2.879e-07 |
| 65536 | 9.592e-08 | 1.800e-08 |

Chosen: 65536. The convergence is second order, as an inscribed polygon on a smooth curve should be.

The missing checks now run, on the same candidate and the same 237 marks, with no new ladder and no new fit family:

| check | order | band symdiff | inner+outer | response | budget | pass |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| shifted | 0 | 4.123e-12 | 4.123e-12 | 1.189e-10 | 2.5e-04 | yes |
| shifted | 1 | 7.143e-10 | 7.143e-10 | 1.203e-09 | 2.5e-04 | yes |
| shifted | 2 | 9.383e-09 | 9.383e-09 | 5.718e-10 | 2.5e-04 | yes |
| tighter root | 0 | 3.674e-16 | 1.362e-16 | 3.459e-15 | 2.5e-05 | yes |
| tighter root | 1 | 5.842e-14 | 5.825e-14 | 3.695e-13 | 2.5e-05 | yes |
| tighter root | 2 | 1.665e-11 | 1.664e-11 | 4.987e-11 | 2.5e-05 | yes |

| order | min local band width (M) | positive at every angle | total area positive |
| --- | ---: | --- | --- |
| 0 | 2.1227e+01 | True | True |
| 1 | 4.6974e-01 | True | True |
| 2 | 2.5904e-02 | True | True |

The final boolean is now the conjunction of every requirement: `two_late_pairs_all_metrics`=True, `shifted_band_and_response`=True, `tighter_root_executed`=True, `tighter_root_passes`=True, `tessellation_band_normalised`=True, `tessellation_response`=True, `local_nesting_positive_width`=True, `topology_simple`=True, `arrays_exported`=True.

Hull geometry: **QUALIFIED**. Arrays are exported and hashed (`CLOSEOUT_ARRAYS_029.npz`, `192eb9598c27ed2f`) so the next stage does not regenerate them.

## 2. The transfer failures are not solver failures

The census covers every component, not the radius. In the core profile the failures are joint: `source_r`, `source_phi`, `coordinate_time` and `radial_sign` go non-finite together on 224 order-1 and 456 order-2 samples, while `redshift` stays finite on all of them -- so the redshift there is a downstream value computed against a landing that does not exist.

Instrumenting the pinned evaluator, expression for expression and with no arithmetic changed, names the first invalid operation for every one of the 680:

| order | cohort | n | emits NaN | first invalid operation |
| --- | --- | ---: | ---: | --- |
| 1 | failure | 224 | 224 | NUMERICAL_FINITE_BUT_NONPHYSICAL_SOURCE_RADIUS = 193, PHYSICAL_LANDING_AT_OR_INSIDE_HORIZON = 31 |
| 1 | control | 200 | 0 | HEALTHY = 200 |
| 2 | failure | 456 | 456 | NUMERICAL_FINITE_BUT_NONPHYSICAL_SOURCE_RADIUS = 339, PHYSICAL_LANDING_AT_OR_INSIDE_HORIZON = 117 |
| 2 | control | 200 | 0 | HEALTHY = 200 |

**No numerical primitive fails.** Radial roots, elliptic arguments and angular integrals are finite everywhere, `source_radius2/3` returns a finite value at every point, and no warning is raised. The NaN is emitted by the library's own final mask, which sets NaN wherever the computed source radius is at or below the horizon after `nan_to_num` and a clamp. The archive therefore records a *deliberate marker*, and my earlier description of 680 deterministic solver failures that retry could not recover was wrong: nothing was retried into failure, because nothing had failed in the sense I claimed.

A finite radius is not automatically physics, and the split is sharp and tracks the turning-point branch:

| order | on the real-turning branch | negative radius | plunge-like radius | range |
| --- | ---: | ---: | ---: | --- |
| 1 | 193 | 193 | 31 | [-3.456e+05, 1.866] |
| 2 | 339 | 339 | 117 | [-2.031e+04, 1.863] |

Every point on the real-turning branch returns a large **negative** source radius -- down to -3.5e5 M -- which is the analytic expression evaluated outside its domain, not a landing. Every point on the complex-turning branch returns a radius just at or below the horizon, which is a plausible plunge. The clamp maps both to the same NaN, so the archive cannot distinguish an out-of-domain evaluation from a captured ray, and neither can any consumer of it.

That is the reproducible cause the ruling asked for, and it also settles the physical-versus-numerical question in both directions: roughly a fifth of the 680 look like genuine non-emission, and the rest are a numerical domain failure that must not be recorded as physical zero.

**T2 was not attempted.** A repair needs its own holdout freeze, and this finding changes what a repair should be: the useful fix is a domain condition that decides which branch expression is valid at a point, not a rearrangement of an expression that never raised. That is a design decision for you, not one to take inside a stage that was authorised to find the cause.

## 3. Corrections to my own record

- The tessellation pass was wrong, by a factor of about 25 in the metric that matters.

- "Deterministic solver failures under the pinned policy" is withdrawn. No primitive fails; the 0/680 recovery was a re-run of a deliberate marker.

- The contour arrays were dropped by the V1 writer. Only counts survive, so the located contour cannot be integrated without re-deriving it. That is disclosed and not reconstructed here: re-deriving it is a second transfer batch, and this ruling's batch belongs to the audit. Domain completeness stays **PENDING_ARRAYS_NOT_PRESERVED**.

- V2 did not consume the contour; it classified archived centre rays. Its unchanged partial response is therefore not a measurement of what happens after the contour is integrated, and I should not have presented it beside the contour result as though it were.

## 4. Governance and resources

The boundary paths charged after `solve_hulls` returned, so an oversized batch would have run to completion before being refused. Reservation now precedes every physical call, the attempt ledger is written after every reservation and completion so an exception cannot lose a charge, and a routine that overruns its reservation is refused rather than absorbed. Four injections cover over-budget, exception, missing-gate and wrong-cost cases. The freeze also pins the installed backend sources by hash.

Boundary: 7110 of the 8,000 closeout allowance, 890 left, against a lifetime ceiling of 34,300 with 26,300 spent before this ruling. Transfer: 1080 of the second batch's 20,000, all of it inside the 4,000 initial-diagnosis cap, so the independent-validation reserve is untouched. The first pilot is closed at its actual 17,912 and its headroom is not a credit. No third batch, no paid resources.

Completion is fail-closed over 16 conditions with 0 failed and 0 unrecorded. Whole suite: 589 passed in 120.35s (0:02:00).

The next decision is yours: what the domain condition should be for choosing between the two branch expressions, and whether re-deriving the contour arrays is worth a batch before that is settled.
