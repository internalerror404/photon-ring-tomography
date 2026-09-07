# CACHED_RESPONSE_AUDIT_034_RETURN

Status: **CACHED_RESPONSE_AUDIT_034_REVIEW_READY**

Ruling: PAPER_I_RESPONSE_ERROR_RULING_034  
Commit: ff6250da3c461b6dbc17302c90c954f9b5ceb76e  
New rays, path quadratures, hull roots, target operators: **0**. 854 units remain, none spent under this ruling.

## 1. The 033 summaries, recomputed from the rows

The corrections are accepted and the numbers are now derived rather than narrated.

| quantity | A vs B, median absolute | max relative |
| --- | --- | --- |
| J_observer | 2.220e-16 | 9.547e-16 |
| J_50 | 2.220e-16 | 8.927e-16 |
| s_escape | 2.942e-05 | 2.267e-04 |
| tail | 0.000e+00 | 0.000e+00 |

So the blanket "agree to about 3e-16" sentence was wrong. `J_observer`, `J_50` and the tail agree near machine precision; `s_escape` differs by a median of 2.942e-05 and up to 4.186e-04. Reference A's convergence estimate, median 3.060e-04, is a third quantity again, and it is an estimate rather than the error.

The endpoint split and the distance median reproduce from the payload: {'upper_annulus': 47, 'escape': 19}, median estimated distance 1.114e-03. That distance is computed with the same quadrature, so it is not ground truth either. Root separation stays an association, not a controlled unique cause, and the indexed reduction is not claimed to have been necessary here.

## 2. The interval error report

`leaf2.envelope_response_bound` is replaced by `leaf2.box_radius_about`, which takes an explicit reference response. For the interval [0, 2] the radius about a nominal of zero is 2 and about the midpoint is 1; the old helper would have said 1 either way. The per-channel Euclidean radius over the whitened detector rows is the primary figure and the joint radius over the stack is labelled separately -- for a one-row half-width of [1, 1] those are 1 and sqrt(2), while the matrix one-norm the 033 helper used gives 1, which is neither. Agrees with the reviewer's helper to 1e-12 across randomised inputs.

## 3. What the bilinear diagnostic was actually comparing

The interpolation mechanics check out on all three orders: alpha-major raster confirmed against each node's own coordinates, in-cell weights inside the unit square, no fine node outside the coarse hull, no silent extrapolation.

The stencil partition is where the 033 reading breaks. A stencil whose four corners merely carry finite numbers is not a stencil sampling one smooth piece of the field.

| order | four emitting corners and one radial leg | crosses the boundary | a corner has no value | median relative source-radius span across a coarse cell |
| --- | --- | --- | --- | --- |
| n0 | 99.2% | 0.0% | 0.6% | 0.03 |
| n1 | 77.9% | 4.3% | 2.7% | 0.14 |
| n2 | 0.0% | 6.8% | 38.3% | 0.81 |

Restricting order 1 to the strict same-leg stencils drops the above-threshold fraction from 18.6% to 10.0%, at 77.9% coverage. Boundary-crossing stencils were inflating it, exactly as the ruling anticipated.

Order 2 is worse than that, and in a way that changes the 033 conclusion rather than qualifying it. **No** order-2 stencil passes the same-leg proxy, and the reason is visible in the last column: the archived source radius varies by a median of 0.81 of its own mean across a single coarse cell, with a minimum of 0.37. The coarse map does not resolve the order-2 field within one cell at all, so the 94.7% was measuring the failure of that representation, not a property of the interior that new sampling must pay for. The 033 sentence attributing the cost to interior sampling is withdrawn.

The proxy -- radius span under a quarter of its own mean -- is a declared heuristic, not a proof, and the span distribution is reported beside it so the threshold can be judged.

## 4. The detector-response error, measured

The eleven inherited channels -- six screen, five transferred at each of the eight accepted observer times -- built from cached tuples on both sides, carried through the same overlap areas, the same single-sky noise and the same absolute clock, compared as whitened detector vectors on identical support.

| order | screen channels | transferred, median | transferred, max | node coverage | area coverage |
| --- | --- | --- | --- | --- | --- |
| n0 | 0.0e+00 | 3.732e-03 | 9.594e-03 | 99.4% | 99.4% |
| n1 | 0.0e+00 | 2.845e-02 | 4.274e-02 | 97.3% | 97.4% |
| n2 | 0.0e+00 | 2.630e-01 | 5.116e-01 | 61.7% | 62.8% |

The screen channels come back at exactly zero. They are the control: both sides share the same overlap operator and the same geometry, so anything the machinery itself introduced would show there. Nothing does.

The transferred channels miss the 5e-4 component budget by roughly 19x at order 0, 85x at order 1 and 1000x at order 2. This is the quantity the budget is written against, and the answer is the same direction as the 033 node counts for a better reason. It says the coarse profile is not an adequate representation of the transferred field at this detector. It does not say how many rays an adequate scheme needs.

Coverage is carried, not absorbed: at order 2, 38.3% of emitting nodes have a coarse corner with no value, the comparison covers 61.7% of emitting nodes and 62.8% of emitting area, and the remainder has no response bound at all. A small residual on available support would not qualify the quadrature while that is true, and here the residual is not small either.

## 5. A cost scenario driven by the response

Per node, the whitened response error is bounded by the sum of `||W O[:,p]|| * |dF_p|`, so refining the largest contributors bounds what is left by the tail. The error is genuinely concentrated:

| order | nodes carrying 50% of the bound | 90% | nodes needed for the tail bound to reach budget | bound is conservative by |
| --- | --- | --- | --- | --- |
| n0 | 0.21% | 5.5% | 62.9% | 10x |
| n1 | 1.51% | 15.3% | 86.9% | 57x |
| n2 | 8.74% | 31.2% | 93.9% | 28x |

Half the bound sits in 0.21% of the order-0 support and 1.5% of the order-1 support, which is real leverage for an adaptive scheme. Driving the *bound* inside budget still takes 63% to 94% of the support, because the triangle inequality ignores the cancellation that makes the measured error 10x to 57x smaller than the bound. At a declared 2x2 per node that scenario is 308,656 evaluations.

Both that number and the 033 figures are scenarios. Neither is a measured call count, neither is a certified upper bound, and the 033 expected total of 101,416 splits 52,379 boundary against 49,037 interior -- so the boundary term was never negligible, and the 033 sentence saying adaptivity fixes it is withdrawn. The 4.385x figure is projection arithmetic, not a measured speedup.

What this changes for the design: a scheme that refines on the measured response contribution has real leverage, and a scheme that has to certify a triangle bound does not. Closing that gap -- an error model that earns cancellation instead of discarding it -- is the next design question, and it is cheaper to answer than any sampling campaign.

## 6. Status

| item | status |
| --- | --- |
| comparator | CLOSED_AT_TESTED_COHORT_SCOPE |
| interval report | CORRECTED_NOMINAL_AND_NORM_EXPLICIT |
| stencil diagnostics | REPRODUCED_AND_PARTITIONED_033_ATTRIBUTION_WITHDRAWN |
| partial response comparison | MEASURED_AND_OUTSIDE_BUDGET |
| missing support | CARRIED_AS_A_COVERAGE_GAP_WITH_NO_BOUND |
| cost scenarios | SCENARIOS_NOT_MEASURED_EFFICIENCY |
| physical quadrature | NOT_QUALIFIED (C13 open) |
| manuscript claim routes | DRAFTED_ADDITIVE_NO_OVERWRITE |

Suite: 691 passed, 2 warnings in 273.98s (0:04:33), run in a disposable git worktree; the authoritative archive was not written to.

This return authorizes nothing. R3B, target spectra, estimators and a submission freeze remain unauthorized, and no new physical query has been made.
