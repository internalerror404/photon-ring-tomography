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

