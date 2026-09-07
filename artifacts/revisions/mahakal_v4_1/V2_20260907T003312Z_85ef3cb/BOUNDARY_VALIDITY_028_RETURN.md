# Boundary-validity return: V0, V1, G1 and V2

Status: **BOUNDARY_VALIDITY_028_REVIEW_READY**  
Blockers: **TRANSFER_ACCURACY_UNQUALIFIED, MISSING_TRANSFER_SUPPORT**

| component | status |
| --- | --- |
| physical contour | **RESOLVED_WITH_SCREEN_BRACKETS** |
| solver support | **UNRECOVERED_UNDER_THE_PINNED_POLICY** |
| hull geometry | **QUALIFIED** |
| overall quadrature | **NOT_QUALIFIED** |
| governance | **COMPLETE** |

R3B is not authorized and was not begun. No target information was inspected.

## 1. Corrections accepted

**A solver failure is not a physical boundary, and physics is not a gap.** The domain now carries three states. A solved ray landing outside the declared emission annulus is `CERTIFIED_NON_EMITTING` -- the model supplies zero there and no completeness budget is charged for its area. Only `UNRESOLVED` is a defect. That reclassification moves most of what the last return called missing support:

| profile | order | emitting | certified non-emitting | unresolved |
| --- | --- | ---: | ---: | ---: |
| coarse | 0 | 0.9911 | 0.0000 | 0.0089 |
| coarse | 1 | 0.7595 | 0.2075 | 0.0330 |
| coarse | 2 | 0.7416 | 0.0533 | 0.2052 |
| core | 0 | 0.9957 | 0.0000 | 0.0043 |
| core | 1 | 0.7621 | 0.2123 | 0.0256 |
| core | 2 | 0.8058 | 0.0587 | 0.1354 |
| fine | 0 | 0.9978 | 0.0000 | 0.0022 |
| fine | 1 | 0.7642 | 0.2135 | 0.0223 |
| fine | 2 | 0.8251 | 0.0687 | 0.1062 |

Order 1's 23.8% "missing" was 21.2% physics and 2.6% gap. I reported it as a single missing-support figure and that was wrong.

**These are centre labels, not fragment certificates.** Each fragment is classified by its centre ray, which says nothing about the part of a cut cell on the other side of the boundary, in either direction. The artifact says so in its own text.

**"The geometric discrepancy is completely removed" was too strong.** The active area is the band before the emission predicate, so its agreement at a fixed hull is expected by construction. And the 5.0% to 2.5% change in order 0's response is not a causal decomposition: norm differences do not subtract, and the omitted support moved too.

**R2: the count is an interval.** The row bound gives 1 <= N_operational <= 2, not a measured fall to one. The bound is sufficient, not tight, and no new R2 quantity was computed.

**Budget wording.** `BUDGET_EXHAUSTED` is retained as reported and qualified: the projected uniform-polygon completion did not fit the remaining allowance. It was never literal exhaustion, and 12,000 boundary solves were in fact available -- which is what made this stage possible.

**Two implementation notes accepted.** The shifted-sample check uses 2.5e-4 and only the tighter-root comparison uses 2.5e-5; the previous runner applied the tighter figure to both. And `region_measures` integrates squared radius by trapezoid, which including vertex angles does not make exact on straight edges -- it is a measured refinement residual, not exact polygon integration, and it is labelled that way now.

## 2. V1: the emission contour and the solver failures

Every physical call went through the guarded entry point. The pinned tracer reproduces the archived source radii **exactly** -- maximum difference 0.0e+00 over 200 probes in each of the three orders -- so the pilot and the archive are the same physics.

| order | contour brackets | resolved | screen bracket (M) | independent re-derivation |
| --- | ---: | ---: | ---: | --- |
| 1 | 595 | 595 | 1.57e-04 | 125/150 within 1.2e-03 M |
| 2 | 617 | 596 | 3.91e-05 | 148/150 within 2.5e-04 M |

Bisection is safeguarded: both endpoints must be finite and on the same radial branch, every midpoint must stay finite, and a bracket that loses either property stops and is returned unresolved with its reason rather than root-found across the discontinuity. Equal-sign intervals are recorded as `NO_SIGN_CHANGE`, which is not a proof that no contour lies in them.

The independent check re-derives a contour point from a different segment through the same equations. Its offset is a global rotation rather than the local normal, so it lands on a nearby point of the same contour rather than the identical one; the figures above are therefore a consistency bound on where the contour is, not a point-identity test, and I would build it from the local normal next time.

**Solver recovery: none.** Re-running the same equations under the same policy recovered 0 of 224 order-1 and 0 of 456 order-2 unresolved points. These are deterministic failures of the pinned primitive, not transient ones. A different policy or backend is not authorized, so they stay `UNRESOLVED` and none was filled with zero.

No response bound is claimed for the uncertain support. An envelope has to bound the field over the uncertain tube and a maximum over nearby samples is not a bound; none was established, so the blocker `UNCERTAIN_SUPPORT_RESPONSE_ENVELOPE_NOT_VALIDATED` is reported instead, over 0.0084 M^2 of unresolved bracket cells.

## 3. G1: the curved boundary qualifies

One declared candidate: a periodic cubic through the root solutions, fitted in cumulative chord length round the closed loop so the representation does not itself force star-shapedness, with the direct-order outer square kept exact. The old straight polygon was not densified.

| pair (marks) | order | band symdiff | boundaries | hull-only response |
| --- | --- | ---: | ---: | ---: |
| 60->119 | 0 | 1.003e-09 | 1.003e-09 | 2.051e-08 |
| 60->119 | 1 | 1.923e-07 | 1.923e-07 | 3.764e-07 |
| 60->119 | 2 | 1.843e-06 | 1.843e-06 | 3.563e-07 |
| 119->237 | 0 | 1.694e-10 | 1.694e-10 | 1.297e-09 |
| 119->237 | 1 | 3.067e-08 | 3.067e-08 | 2.287e-08 |
| 119->237 | 2 | 1.161e-07 | 1.161e-07 | 2.094e-08 |

Against a 2.5e-4 budget, unchanged. Tessellating the curve into a polygon for the clipping kernel costs 3.0e-07 relative, inside its own 1e-6 budget, and band widths stay positive.

The shifted-sample check ran at 2.5e-04 on 474 fresh solves of the pinned equations at locations that are not fit knots, covering every fitted boundary rather than only the outer one: worst relative radius error 5.0e-07.

For scale: the straight-chord ladder reached 1.9e-3 for order 2 at 480 marks and was projected to need 3840 marks and about 144,000 solves. The curved representation reached 1.2e-7 using 5,930. The approximation order was the binding thing, not the sample count -- the ruling's synthetic test, now measured on the real Kerr boundary.

## 4. V2: what the qualified geometry does and does not fix

The hull is held at the accepted curve, regenerated from the pinned equations at the same marks, which also reproduces its geometry independently.

| pair | order | worst partial response | geometric band area | emitting area |
| --- | --- | ---: | ---: | ---: |
| coarse->core | 0 | 6.436e-02 | 0.0e+00 | 4.596e-03 |
| coarse->core | 1 | 2.376e-01 | 8.9e-15 | 3.446e-03 |
| coarse->core | 2 | 8.553e-01 | 9.7e-14 | 7.617e-02 |
| core->fine | 0 | 2.523e-02 | 0.0e+00 | 2.093e-03 |
| core->fine | 1 | 7.755e-02 | 1.8e-15 | 2.828e-03 |
| core->fine | 2 | 3.828e-01 | 1.2e-13 | 2.293e-02 |

The geometric band is profile-independent to 1e-13, as it must be at a fixed hull. The emitting area still moves by up to 7.6e-2, and the partial responses are essentially where they were. So the qualified geometry has resolved the geometric uncertainty and none of the transfer uncertainty, which is the separation this stage existed to make. These responses are **partial**, computed on the support that has data; the missing contributions were not computed and these are not full physical response errors.

## 5. Which uncertainties are now resolved

| uncertainty | before | now |
| --- | --- | --- |
| hull geometry | 1.9e-3, unqualified | **qualified**, 1.2e-7 |
| emission-annulus boundary | centre labels only | contour located to 1.6e-4 M, 1191 of 1212 brackets |
| solver failures | 680 unresolved | **still 680**, and shown deterministic |
| transferred-field accuracy | 3.8e-1 | **3.8e-1**, unchanged |

The next binding question is the transferred field itself, not the geometry and not the annulus. Nothing in this stage was changed to obtain a favourable result: the detector, the clock, the target and every accuracy standard are the ones that were already pinned.

## 6. Governance and resources

Preregistration gated every physical call. The guard verifies the committed freeze at the query entry point and refused twice -- once when a frozen script changed after registration, once when I edited a freeze by hand instead of regenerating it. Both refusals stopped the run. The freeze generator now reconciles spend from the guard snapshots each physical run writes, so a re-registration carries the real ledger forward. Four registrations were made; the two superseded ones are preserved.

Boundary: 8300 charged by this ruling on top of the 18,000 already charged, 3700 of the 30,000 lifetime cap remaining, with 2,370 of it spent on the independent check. Transfer: 17912 of the 20,000 pilot allowance, of which 1,280 was the initial diagnostic against a 4,000 cap and 3,300 independent validation. No second batch, no paid resources.

Completion is fail-closed over 16 conditions with 0 failed and 0 unrecorded. Whole suite: 585 passed in 33.77s, return code 0. The 027 preregistration failure stays disclosed in its own record and is not backdated.

