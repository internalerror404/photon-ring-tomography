# Domain-integration return: the predicate is hardened, the integral is not yet converged

Status: **DOMAIN_INTEGRATION_031_BLOCKED**  
Blocker: **INTEGRATION_PILOT_ALLOCATION_EXHAUSTED_THE_CAP**

| component | status |
| --- | --- |
| sampled absences | **ACCEPTED_UNCHANGED** |
| wrapper guards | **HARDENED_AND_TESTED** |
| comparator confirmation | **AGREES_WHERE_THE_REFERENCE_RESOLVES_66_OF_494_UNRESOLVED** |
| emission domain integration | **PILOT_INCOMPLETE_CAP_CONSUMED** |
| whole transfer accuracy | **NOT_QUALIFIED** |
| detector quadrature | **NOT_QUALIFIED** |
| governance | **COMPLETE** |

R3B, a new target spectrum, an estimator and a submission freeze remain unauthorized.

## 1. Corrections accepted

The final 880-point panel is relabelled `PRECOMMITTED_PANEL_REUSED_AFTER_COMPARATOR_CORRECTION`. Its precommitment stands and the original disagreements are preserved -- {'development': 57, 'panel': 30} -- because they were seen before the comparator was revised. Your verification that the primary blob is identical across the correction is recorded with its hash.

The independence scope is corrected: the two methods differ only in the radial quadrature. They share the conserved quantities, the roots, the angular crossing parameter, the path classifier and the asymptotic tail, so their agreement is conditional on those inputs and is not a verification of the whole geodesic calculation. `_tail` is relabelled a truncated asymptotic correction and now returns a remainder bound; the reference reports a convergence estimate from successive panel refinements, not an enclosure.

**The mask table is rebuilt with one denominator per row.** The old one counted UNRESOLVED over the whole stored grid beside an in-band figure from a different mask. Within the archived band:

| order | band samples | emitting | non-emitting | unresolved | band and qualified hull |
| --- | ---: | ---: | ---: | ---: | ---: |
| 0 | 15597 | 15597 | 0 | 0 | 15597 |
| 1 | 11145 | 8531 | 2390 | 224 | 11145 |
| 2 | 4976 | 4179 | 341 | 456 | 4976 |

**The accounting correction is accepted, and is larger than you computed.** Reconciling every attempt ledger rather than the result files finds a fourth second-batch execution, `T1_20260907T074927Z` with 120 attempts, which aborted on a guard error and so left a ledger but no result file. A summary-based count cannot see it. Second-batch spend before this ruling is 7072 across 6 executions, not 6,952, and the remainder was 12928, not 13,048. That the persisted ledger caught a charge the summary missed is the point of persisting it.

## 2. The predicate is hardened in a new version

`pathdomain2` leaves the frozen 030 implementation untouched. An invalid interior evaluation is unresolved instead of a silently deleted piece of the integral. A non-finite integral, error or crossing parameter is unresolved *before* any comparison, which closes the hole where a NaN made both capture tests false and fell through to valid. A negative Mino parameter is unresolved. Both margins and their uncertainties are exported. Ten guards cover the cases you named, and a further one checks that the two versions agree wherever both resolve.

## 3. The fresh panel, including the stratum that was missing

494 points, none of them in any prior cohort and none of their outcomes existing before the freeze, charged 494 against a 1024 cap:

| stratum | outcome |
| --- | --- |
| boundary_uncertainty_near_r50 | {'VALID_EMITTING_EVENT': 114} |
| emitting | {'VALID_EMITTING_EVENT': 114} |
| boundary_uncertainty_near_horizon | {'VALID_EMITTING_EVENT': 114} |
| absence_candidates | {'NO_NTH_EXTERIOR_CROSSING_ESCAPE': 63, 'NO_NTH_EXTERIOR_CROSSING_CAPTURE': 13} |
| finite_exterior_outside_annulus | {'EXTERIOR_EVENT_OUTSIDE_SOURCE_ANNULUS': 76} |

Zero forced labels: 0 points where the predicate says valid and the library marked NaN, and 0 where it says absent and the library returned a value. The new stratum earns its place: all 76 finite exterior crossings outside the source annulus classify as `EXTERIOR_EVENT_OUTSIDE_SOURCE_ANNULUS` while the library returns a finite value, so on this panel the emission predicate and the NaN marker are demonstrably different questions.

Where the reference resolves it agrees with the primary on all 428 points. On 66 it does not resolve at all -- the panelled routine cannot form the integral, 62 of them order 2. Those are absences of confirmation, not label conflicts. Tuning the comparator on this panel is forbidden, so the non-convergence stands as a stated limitation rather than being fixed away, and the confirmation is correspondingly weaker than 494/494 would have been.

## 4. The integration pilot, and where it stopped

The declared representation was the implicit one: the validity indicator evaluated inside adaptive cut cells, with unresolved boundary area carried as a budget and never rounded to zero. What it measured is worth having:

| profile / order | transition cells | sub evaluations | domain change vs centre indicator | unresolved area fraction |
| --- | ---: | ---: | ---: | ---: |
| core_n0 | 331 | 1324 | 3.853e-03 | 0.00e+00 |
| core_n1 | 1169 | 4676 | 1.854e-03 | 0.00e+00 |
| core_n2 | 0 | 0 | 0.000e+00 | 0.00e+00 |
| fine_n0 | 0 | 0 | 0.000e+00 | 0.00e+00 |
| fine_n1 | 0 | 0 | 0.000e+00 | 0.00e+00 |
| fine_n2 | 0 | 0 | 0.000e+00 | 0.00e+00 |

**The centre indicator is not good enough.** Treating each cut cell by its centre misstates the emitting area by 3.9e-3 for order 0 and 1.9e-3 for order 1, both above the 5e-4 transfer and emission component budget. Domain-aware integration is therefore necessary, not a refinement of a already-adequate treatment. No sub-cell came back unresolved.

**But the pilot did not produce a valid comparison, and that is my allocation error.** It took transition cells greedily, largest area first, order by order and profile by profile, and the 6,000 cap was consumed by core orders 0 and 1 alone. Core order 2 and the entire fine profile got none. The profile pair figures the run printed therefore compare a cut-cell core against a centre-indicator fine, which is a comparison of two representations rather than of two samplings, and I am not presenting them as convergence. A balanced allocation across all six profile-order pairs was what this needed, and the cap for this pilot is now spent.

## 5. What would settle it

A rerun of the same pilot with the budget divided across the six pairs before the first evaluation, plus a second sub-cell level so the cut-cell treatment has its own convergence rather than one refinement. That needs roughly 12,000 evaluations; 6434 remain and 4,000 of them are the validation reserve. I am not asking for a third batch in this return; the measurement above already establishes that the centre indicator fails its budget, which is the finding this stage was for.

## 6. Governance and resources

Confirmation 494 of 1024; integration pilot 6000 of 6000; 6434 of the second batch left with the 4,000 reserve preserved (True). No new hull calls, no third batch, no paid resources.

Completion is fail-closed over 16 conditions with 0 failed. Whole suite: 607 passed, 2 warnings in 42.78s. I3 was not run and is recorded as not run: there was no comparison to validate.

