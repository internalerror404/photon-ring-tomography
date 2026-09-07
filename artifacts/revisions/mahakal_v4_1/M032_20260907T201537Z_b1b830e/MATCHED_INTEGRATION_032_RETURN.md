# MATCHED_INTEGRATION_032_RETURN

Status: **MATCHED_INTEGRATION_032_PLAN_BLOCKED**

Ruling: PAPER_I_MATCHED_INTEGRATION_RULING_032  
Commit: b1b830e16b2fc55569a3ef0211c67cb036105510  
New physical queries: **0**. No ray traced, no path integral recomputed, no hull root solved, no target operator touched.

## 1. Leaf assembly

The response is now assembled leaf by leaf,

    y_d = sum_p sum_(l in leaves(p)) |D_d ^ C_l ^ B_n| chi(xi_l) f(xi_l),

with each child keeping its own detector and hull overlap. The parent-averaged occupancy proxy is implemented once, named `PARENT_AVERAGED_OCCUPANCY_PROXY`, and refused by both the plan validator and the report writer.

On the ruling's own counterexample the leaf rule pays [0.2, 0.0] where the proxy pays [0.1, 0.1]; the totals agree and the images do not.

On archived order-0 core geometry -- real band, real hull, real cell measure -- refining every parent into four children leaves the overlap unchanged per (detector cell, parent) to 6.939e-18. That is the check that separates a refinement of the integration from a change of the geometry, and a total-only check would not have made it: on a declared test domain the two rules differ by 8.220e-02 in whitened vector residual while the 031 metric -- the difference of norms -- reports 1.232e-02, 6.7 times smaller.

Unresolved leaves are carried as an explicit (lower, known, upper) response rather than a boolean. A finite leaf label is not a domain certificate and zero unresolved samples is not zero boundary error; both are asserted in tests rather than in prose.

Nine fault injections run in the launch and report path: 193_points_under_192_point_cap, unresolved_reference_prerequisite, missing_fine_or_order2_endpoint, occupancy_only_pretending_full_transfer, equal_norm_different_detector_vectors, parent_fraction_assembly_in_actual_consumer, missing_numerical_payload, infeasible_complete_bundle_or_validation_reserve_invasion, missing_prerequisite_record. 
Suite, the three new files: 51 passed in 97.26s (0:01:37). Whole repository: 658 passed, 2 warnings in 141.07s (0:02:21).

## 2. Comparator

The 031 shared-input check was tautological. Over 2000 random quadruples the quantity it reported is exactly 0.0e+00: it is zero for any list at all. Replaced by the original quartic built from the conserved quantities,

    R(r) = r^4 + (a^2 - lam^2 - eta) r^2 + 2((lam - a)^2 + eta) r - a^2 eta,

evaluated by complex Horner with a scale-aware backward residual. It detects a root perturbed by 1e-8 in 200 of 200 synthetic cases, where the old check reported zero.

The turning-point reduction excluded its root by Python object identity. `classify_path` returns `max(ext)` as a plain float, so `q is not turn` is true for every element, the factor (r - turn) survives, and the reduced potential vanishes at the endpoint where the integrand peaks: on the analytic fixture the 031 form returns 0.0 and the correct limit is 124.74. The corrected reduction excludes by verified index and refuses a clustered or multiple turning root instead of returning a number. Frozen 031 code is unchanged; the correction is a separate candidate.

A static association, offered as an association and not a diagnosis: all 66 unresolved-reference points have an accessible turning root, and their turning root sits close to its neighbours -- median separation 0.539 M, maximum 1.514 M. In the 428 agreeing cases the median is 4.321 M and 140 have no turning root at all. Every root in both groups is simple and solves the quartic to 2.5e-15, so this is not a root-finding failure. It is consistent with the endpoint defect above and it does not establish the cause: I1 discarded the reference's reason codes and integral values at write time, and recovering them needs a recomputation this ruling does not authorize.

## 3. Payloads

The 031 integration pilot left summaries and ledgers only. Of its 6000 charged sub-evaluations, **0** labels, transfer values or detector vectors survive anywhere -- inside the repository or outside it. Their screen coordinates can be reconstructed from the frozen selection rule, which recovers where the evaluations were and not what they returned. Any re-evaluation is a new charge. The 030 per-point adjudication arrays do survive (2552 rows across two files, hashed here) but they are labels for the 030 cohort, not leaf labels on any refinement of this matrix.

## 4. The comparison, costed

Census of the archived geometry. Transition parents are cells whose emitting status differs from a neighbour and whose dual meets the band; the last two columns are the new evaluations an L1 and an L2 bundle would need.

| endpoint | ray cells | transition parents | unresolved support (area) | L1 cost | L2 cost |
| --- | --- | --- | --- | --- | --- |
| core n0 | 15876 | 331 | 0.43% | 1324 | 5296 |
| fine n0 | 62500 | 661 | 0.22% | 2644 | 10576 |
| core n1 | 62500 | 1584 | 2.63% | 6336 | 25344 |
| fine n1 | 250000 | 3183 | 2.29% | 12732 | 50928 |
| core n2 | 490000 | 5177 | 13.93% | 20708 | 82832 |
| fine n2 | 1440000 | 11300 | 11.25% | 45200 | 180800 |

Full 18-endpoint matrix: **444720 new evaluations**. The spendable balance is 2434 under the native-only convention and -2372 under the other -- a negative number, because that convention leaves less than the reserve itself -- and the entire lifetime transfer cap is 250000. The full-domain comparison does not fit in the remaining allowance, and it does not fit in the lifetime cap either. I am saying so before the first query, as the ruling requires, rather than discovering it in a partial run.

The fallback the ruling allows -- a complete local diagnostic with an explicit scope -- does not rescue it. The region family was fixed in the source before the census was read: a wedge of screen position angle about 90.0 deg, the same region for both profiles, half-width taken from a fixed ladder.

| half-width (deg) | cost | min transition parents | non-degenerate | fits spendable |
| --- | --- | --- | --- | --- |
| 45 | 101220 | 28 | True | False |
| 30 | 69520 | 19 | True | False |
| 20 | 46800 | 12 | True | False |
| 15 | 35200 | 10 | True | False |
| 10 | 23340 | 6 | True | False |
| 7.5 | 17440 | 4 | True | False |
| 5 | 11860 | 4 | True | False |
| 3 | 7060 | 0 | False | False |
| 2 | 4740 | 0 | False | False |
| 1 | 2180 | 0 | False | True |

Every wedge that fits the spendable balance contains **zero** transition parents at order 0, in both profiles: it would refine a region where the emission boundary does not pass, and report an endpoint that measured nothing as an endpoint that agreed. The smallest wedge with something to measure at all six endpoints has half-width 5.0 deg and costs 11860, which is 4.9 times the spendable balance and more than the whole reported remainder. A degenerate endpoint is refused by the plan validator rather than costed at zero, so no affordable member of this family can be returned as a plan.

Even the affordable end of that ladder would cover under half a percent of any band. A local patch of that size cannot qualify D026 globally and its omitted regions are not bounded by anything measured here; both facts are recorded in the plan rather than left implicit.

## 5. Why the plan is blocked anyway

**REFERENCE_CONFIRMATION_INCOMPLETE.** 66 of 494 primary-reference comparisons did not resolve, 62 of them at order 2, and no validated bound or prospectively justified scope exclusion exists. Order 2 is a required endpoint of the matrix; the launch condition cannot be met for any compliant plan.
*Cost to clear:* re adjudication of the 66 66; fresh holdout within the 192 point cap 192; total new evaluations 258. *Needs:* new physical queries; forbidden by 032.

**ORDER2_MISSING_TRANSFER_SUPPORT.** Cells whose dual overlaps the order-2 band but whose archived centre ray has no usable transfer datum carry 13.9% of the core band area and 11.3% of the fine band area. An unresolved support fraction of that size is orders of magnitude above the 1e-3 area budget and the 5e-4 response budget, so no order-2 comparison could be qualified even if it ran.
*Cost to clear:* not costable without new sampling of those cells. *Needs:* new physical queries; forbidden by 032.

**ACCOUNTING_CONVENTION_UNRESOLVED.** The second batch has 6434 left under the native-only convention and 1628 under the convention 032 states for independent end-to-end reference evaluations. Under the second convention the remaining balance is already below the 4000 validation reserve, so nothing is spendable; which convention governs is the reviewer's call.
*Cost to clear:* 0. *Needs:* a ruling on the convention.

**NO_AFFORDABLE_NON_DEGENERATE_LOCAL_REGION.** On the declared wedge ladder, every region that fits the 2434 spendable evaluations contains zero transition parents at order 0, and the smallest region that has something to measure at all six endpoints (half-width 5.0 deg) costs 11860. A local diagnostic that measures nothing at an endpoint is not a cheaper comparison, it is an empty one; the fallback scope is therefore not available either.
*Cost to clear:* 11860. *Needs:* an allowance 032 does not grant.

**FULL_DOMAIN_MATRIX_EXCEEDS_EVERY_ALLOWANCE.** The 18-endpoint full-domain matrix costs 444720 new evaluations. That is 183 times the 2434 spendable under the more generous convention, and 1.78 times the entire 250000 lifetime transfer cap.
*Cost to clear:* 444720. *Needs:* an allowance 032 explicitly does not grant.

The preflight agrees. On the plan as returned it reports `PLAN_BLOCKED` with ['PLAN_PLUS_VALIDATION_EXCEEDS_RECONCILED_BUDGET', 'PREREQUISITE_NOT_READY']; with the prerequisite stipulated met purely to separate schema from science it reports `PLAN_BLOCKED`, which authorizes nothing. On the full-domain matrix it reports ['PLAN_PLUS_VALIDATION_EXCEEDS_RECONCILED_BUDGET', 'PREREQUISITE_NOT_READY'].

## 6. Accounting

The component counters are kept apart: 13566 native tracer evaluations, 10806 primary path integrations, 4806 independent end-to-end reference integrations, across eight executions including the aborted 120-attempt run. A quadrature abscissa is not counted as a new ray; an independent end-to-end evaluation is not written off as cached algebra.

Under the native-only convention in force through 029-031 the second batch has spent 13566 of 20000 and has 6434 left. Under the convention this ruling states for independent end-to-end reference evaluations it has spent 18372 and has 1628 left -- below the 4000 response-validation reserve, so nothing at all is spendable. I am not choosing between them: the balance is recorded as unresolved and the reserve is untouched.

Boundary: 33410 spent, 890 remaining, 0 new calls. No third batch, no new allowance.

## 7. Governance and manuscript

Governance is AUDIT_COMPLETE_WITH_PROTOCOL_DEVIATIONS. The four 031 deviations stay on the record: the allocation error, the 302-point cap overrun, the unmet reference-confirmation gate, and the partial and mismatched comparison. Nothing written under 029, 030 or 031 has been edited and the 031 token remains `DOMAIN_INTEGRATION_031_BLOCKED`.

Section 5's 'Validated Computational Operator' statement and the order-resolution attribution in section 10.1 are not restored. This delivery produced no matched comparison, and a plan is not evidence. No manuscript rebuild and no submission-ready claim is made.

This return authorizes nothing. No new physical query has been made and none should be made before the next ruling.
