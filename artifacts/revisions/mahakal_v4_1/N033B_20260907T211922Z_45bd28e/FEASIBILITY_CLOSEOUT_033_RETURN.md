# FEASIBILITY_CLOSEOUT_033_RETURN

Status: **FEASIBILITY_CLOSEOUT_033_REVIEW_READY**

Ruling: PAPER_I_FEASIBILITY_AND_CLOSEOUT_RULING_033  
Commit: 9adcb3adb9b8897df6b86077831a3c6fa436d511  
Charged this ruling: **774** of the 1,024 diagnostic cap. Remaining second batch: **854**. No new hull query, no integration sampling, no target operator.

## 1. Sign-aware envelopes

`leaf.py` is unchanged and `leaf2.py` replaces the one-sided pile. On the ruling's own example -- overlap 0.25, field -2, indicator uncertain in [0,1] -- it returns [-0.5, 0] where the 032 construction returned [0, 0.5] and excluded the truth. A magnitude bound gives [-wM, +wM]; a general pair of intervals gives the extreme of the four endpoint products. A missing envelope is a blocker, and a point sample is not an envelope over its leaf: both are refused rather than filled with a zero.

Checked against the reviewer's own utility to 1e-12 across randomised signed inputs, and on the archived order-0 band with a signed coordinate-time channel, where the realisation that resolves every uncertain leaf to emitting escapes the 032 box and stays inside this one.

## 2. The comparator, and what the 66 actually were

The cause is now on the record instead of inferred, and it is not the one ruling 032 associated with them.

Reference A is the frozen 031 graded-panel reference, re-run to recover the reason I1 discarded. All 66 come back with the same one: the case lies inside its decision margin -- 47 at the upper annulus endpoint, 19 at the escape endpoint. Their true distance to that endpoint has median 1.114e-03 M of Mino parameter, while reference A's own convergence estimate has median 3.060e-04. Ten times that swallows the separation, so the reference refused -- correctly.

Reference B resolves all 66 with error estimates of median 4.474e-14 and agrees with the primary label on 66 of 66. The integral values agree between A and B to about 3e-16 relative, so reference A was never wrong about the physics; it was right about its own precision.

**What resolved them is reference precision, not the indexed root reduction.** The primary -- version 2, adaptive, still using the old division form -- also resolves all 66, at error ~1e-09. The indexed reduction stays a correctness repair validated on fixtures, and this stage does not claim it decided these points.

The 032 association survives as the mechanism rather than the cause: the unresolved points have median turning-root separation 0.539 M against 3.671 M for the resolved confirmation points, and a tighter turn is exactly what peaks the integrand where graded panels are weakest.

| cohort | n | reference B unresolved | agrees with primary | reference A unresolved |
| --- | --- | --- | --- | --- |
| development (the 66) | 66 | 0 | 66 | 66 |
| confirmation (frozen) | 192 | 0 | 192 | 7 |

Zero valid-where-the-library-marked-NaN, zero absent-where-a-value-was-given, zero forced labels, zero ambiguous cases resolved toward the archived mask. The confirmation IDs were frozen before the phase ran, drawn from 48 points in each declared scope, and every point/order ID used by rulings 029, 030 and 031 -- 3,262 of them -- was excluded.

Status: **COMPARATOR_NUMERICALLY_VALIDATED_ON_TESTED_COHORTS**. It qualifies the comparator on these cohorts, not the transferred field and not any unsampled boundary, and it authorizes no integration. The independence is bounded: the primary and reference B share the roots, the angular crossing and the path classification, and differ in the reduction algebra and the quadrature tolerance.

One governance event to disclose. The first freeze recorded a `commit_at_freeze_time` that predated the commit adding its own registered inputs, and the guard refused to arm on it. That refusal is correct and is kept in the record; nothing was charged against it. The freeze was regenerated at the commit carrying every registered input, and because the cohort selection is seeded and deterministic both freezes name the identical 66 development and 192 confirmation IDs -- verified by comparison, not asserted.

## 3. The adaptive design, costed

One quadtree per order over the declared aperture, seeded by the archived maps, refined only by boundary uncertainty and by the measured field interpolation error, with crossings localised as bracketed one-dimensional events and one transfer tuple serving all eight observer times algebraically.

| order | boundary length (M) | resolution the area budget needs (M) | bisection depth | expected calls | worst case |
| --- | --- | --- | --- | --- | --- |
| n0 | 46.0 | 5.38e-02 | 2 | 974 | 2976 |
| n1 | 52.7 | 1.37e-03 | 5 | 13872 | 50220 |
| n2 | 42.3 | 4.74e-05 | 8 | 86570 | 329384 |

Expected **101,416** new native evaluations, worst case **382,580**, plus 5,263 for the held-out check and the independent panel. Against the retired uniform layout at 444,720 that is a 4.4x reduction in the expected case. It is a real reduction and it is not enough: the remaining balance is 854.

The driver is measurable and it is not the boundary. Carrying the coarse profile's own transfer field onto the fine profile's nodes -- two archived maps, no new rays -- shows the order-2 interior is where the cost lives: 94.7% of comparable emitting nodes exceed the 5e-4 component budget in redshift and 98.1% in source radius, against 2.0% and 0.0% at order 0. The coarse profile simply does not represent the order-2 field to the accuracy the budget asks for, so the interior there needs its own samples however cleverly the boundary is found.

That is the honest shape of the problem: adaptivity fixes the boundary cost and leaves an order-2 interior sampling cost that no amount of mesh cleverness removes. A cheaper design would have to attack the field representation -- a better interpolant, or an error model that earns a coarser one -- and that is a separate piece of work, not a mesh parameter.

## 4. Accounting

Convention B. Before this ruling: 13,566 native plus 4,806 independent references = 18,372 of 20,000, leaving 1,628.

This ruling charged 774 units: 258 native, 258 reference A, 258 reference B, over 258 point/order IDs at three units each. The 258 primary path integrations rode inside their native bundles and are recorded as a component, not charged again. Development took 198 of its 384 cap and confirmation 576, against a reserve of at least 576. Remaining: **854**.

Boundary: 33,410 spent, 890 remaining, 0 new calls. No third batch, no new allowance, no paid resource. The 4,000-unit full-response reserve is recorded as suspended for the unlaunched design, and any future integration campaign must fund its own validation before it starts.

## 5. Status

| item | status |
| --- | --- |
| leaf geometry | ACCEPTED_UNCHANGED_FROM_032 |
| signed envelopes | CORRECTED_AND_TESTED |
| comparator | NUMERICALLY_VALIDATED_ON_TESTED_COHORTS |
| adaptive design | COSTED_AND_UNFUNDED |
| physical quadrature | NOT_QUALIFIED (C13 open) |
| governance | COMPLETE_WITH_ONE_DISCLOSED_GUARD_REFUSAL |

Suite: 686 passed, 2 warnings in 274.61s (0:04:34). Legacy write-capable tests were run in a disposable git worktree, so the authoritative archive was not touched.

R3B, a target spectrum, an estimator and a submission freeze remain unauthorized. Section 5's validation statement and the order-resolution attribution in sections 6.4 and 10.1 are not restored by this delivery: a validated comparator is not a validated operator, and no integration has run.
