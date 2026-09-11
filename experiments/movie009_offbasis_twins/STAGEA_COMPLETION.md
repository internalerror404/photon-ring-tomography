# Movie009 Stage A — natural off-basis direct-null twins

**Return:** `MOVIE009_STAGEA_FAIL`  
**Neural Stage B:** not authorized and not run, because the preregistered classical feasibility gate failed.

The experiment generated 64 held-out analytic twin pairs across narrow-hotspot, shearing-spiral, split/merge, and completely held-out radial-plume families. Every twin difference is support-exactly absent from the direct q8/q12 acquisition; the maximum direct twin difference is numerical zero in the recorded calculation. Clean and fitted q8/q12 gates pass.

The rich 1617-dimensional labelled ridge identifies 100% of individual siblings and 100% of sibling pairs at SNR0=300. It reduces median old-movie error versus direct by 71.6–80.9% across all four families, including 77.3% on the held-out radial-plume family. However, its registered 95%-reliable contiguous total-movie span is 0M, so the Stage-A movie gate fails.

| Method | SNR | Arm | Identification | Pair-both | Median support error | Span95 |
|---|---:|---|---:|---:|---:|---:|
| old595 ridge | 300 | direct | 50% | 0% | 0.594 | 0M |
| old595 ridge | 300 | labelled | 100% | 100% | 0.330 | 0M |
| rich1617 ridge | 300 | direct | 50% | 0% | 0.970 | 0M |
| rich1617 ridge | 300 | labelled | 100% | 100% | 0.223 | 0M |

Post-result readback localizes the failure. The labelled rich reconstruction passes most old frames from -6M through -26M at roughly 75–100% rates, but only 47.3% pass the anchor frame tau=0 and 18.2% pass tau=-28M. The shared analytic background was itself outside both reconstruction classes, so the endpoint simultaneously tested off-basis current-background reconstruction and off-basis old-history reconstruction. This is a valid negative result, not a numerical-integration failure.

The first source-admission attempt failed before accepting a source because the original compact polynomial window was incompatible with the nine-frame activity rule. Amendment 001 replaced it by a compact C2 plateau before any accepted source or inverse outcome. The source-independent rich operator cache was retained.

No new physical calls or Paper-I units were used. The result does not authorize changing Movie009 thresholds or launching its preregistered neural Stage B.
