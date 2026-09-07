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

