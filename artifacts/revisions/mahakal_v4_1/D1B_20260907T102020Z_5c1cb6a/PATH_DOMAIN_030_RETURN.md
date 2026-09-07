# Path-domain return: the requested crossings do not exist

Status: **PATH_DOMAIN_030_REVIEW_READY**

| component | status |
| --- | --- |
| marker semantics | **CONFIRMED** |
| root branch classification | **CORRECTED** |
| event existence | **VALIDATED_ABSENCES_NO_REPAIR_JUSTIFIED** |
| source domain completeness | **PENDING_CONTOUR_ARRAYS** |
| whole transfer accuracy | **NOT_QUALIFIED** |
| quadrature | **NOT_QUALIFIED** |
| governance | **COMPLETE** |

Ready does not mean the physical quadrature is qualified. R3B, a new R2 spectrum, an estimator and a submission freeze remain unauthorized.

## 1. The answer is that the events are not there

Every one of the 680 archived failures is a **validated physical absence**. The requested crossing does not exist on the ray:

| classification | count | meaning |
| --- | ---: | --- |
| `NO_NTH_EXTERIOR_CROSSING_ESCAPE` | 532 | the ray scatters and escapes before the requested crossing would occur |
| `NO_NTH_EXTERIOR_CROSSING_CAPTURE` | 148 | the crossing would occur after the ray reaches the horizon |

That is exactly the hypothesis you set out, and it lands on the same split my provisional labels had guessed at for the wrong reason: the 532 negative-radius cases are crossings requested after escape, and the 148 sub-horizon cases are crossings requested after capture. **No repair is justified.** The library's exclusion was numerically appropriate; only its reason was inadequately represented.

All 596 healthy controls come back `VALID_EMITTING_EVENT`. On the 880 precommitted holdout points, from a different profile and never previously inspected: 0 invented events and 0 missed events against the library's own mask, with {'VALID_EMITTING_EVENT': 720, 'NO_NTH_EXTERIOR_CROSSING_ESCAPE': 118, 'NO_NTH_EXTERIOR_CROSSING_CAPTURE': 42}.

The two quadratures agree on every point -- 1276/1276 development and 880/880 holdout.

That took a correction of my own. A first comparator, a single fixed-order Gauss-Legendre rule, disagreed on 57 development and 30 holdout points at separations up to 3.7e-2 -- far too large to be boundary cases. The cause was the comparator, not the predicate: on a capture path whose largest interior root sits just below the horizon the integrand peaks sharply at r_+, and a global rule misses it. Graded panels resolve it and the disagreement goes to zero. I report that because a comparator that agrees only after being fixed is worth less than one that agreed from the start.

## 2. Corrections accepted

**The physical labels were provisional and are replaced.** My `PLUNGE` and `NUMERICAL_FINITE_BUT_NONPHYSICAL_SOURCE_RADIUS` followed the sign of the raw radius with no trajectory-duration test. The raw arrays are preserved; the labels are superseded by the path-domain codes, which consult the radial path and never the sign. A canary reads the module source to keep it that way.

**The real-turning-branch naming is withdrawn.** A small imaginary part on the outer root does not establish an accessible exterior turn. The predicate now requires a root that is real, outside the horizon and inside the observer, and four real roots all inside the horizon are a capture.

**Your scalar fixture reproduces.** For b=6, M=1, observer at 1000M the escape Mino parameter comes out 0.809163488 against your 0.80916349 -- agreement to 2e-9. The last 1e-7 is the analytic tail beyond the quadrature limit, which is now added in closed form rather than truncated.

**The counter correction is accepted.** Three T1 runs were executed: {'T1_20260907T074951Z_3d42022': 480, 'T1_20260907T075031Z_c35cb34': 1080, 'T1_20260907T075138Z_1113f3e': 1080}, totalling 2640. My 029 summary reported only the last. The second batch had 17360 remaining, not 18,920. This is an overlay; no old record is rewritten.

## 3. What changes in the maps

Nothing numerical. Those points were already excluded by the archived validity mask, so no stored value moves. What changes is that their exclusion becomes a validated physical absence rather than an unexplained gap:

| order | in band | unresolved before | reclassified | unresolved after |
| --- | ---: | ---: | ---: | ---: |
| 0 | 15597 | 279 | 0 | 279 |
| 1 | 11145 | 51579 | 224 | 51355 |
| 2 | 4976 | 485480 | 456 | 485024 |

So `MISSING_TRANSFER_SUPPORT` is discharged for these points. No positive recovery of lost events was required and none is claimed.

## 4. What is still open

- The contour arrays are still absent, so the located emission boundary cannot be integrated. Re-deriving them is a separate decision and I did not spend the batch on it.

- Event existence is not within-cell transfer accuracy. The common-sky quadrature still needs its own convergence evidence, and the transferred-field response remains unqualified.

## 5. Governance and resources

Transfer: 2156 evaluations, all within the 3000 decision-point cap, leaving 15204 of the second batch. Independent validation used 880 and is reported as used rather than rounded up to the 4,000 reserve. No new boundary calls, no third batch, no paid resources.

Completion is fail-closed over 14 conditions with 0 failed. Whole suite: 597 passed in 41.91s.

