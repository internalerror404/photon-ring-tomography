# Movie010 Stage A — isolated off-basis historical features

**Return:** `MOVIE010_STAGEA_FAIL`  
**Registered neural Stage B:** not run, because the classical pass was a prerequisite.

Movie010 replaced Movie009's off-basis shared background by a low-order background lying in the intersection of the old and rich source spaces. The four analytic old-feature families remained unprojected and support-exactly absent from the direct image.

The rich 1617-dimensional labelled ridge still identifies 100% of individual siblings and 100% of sibling pairs, with median paired movie-error reductions of 70.7–80.6% across all four families. Clean and fitted q8/q12 gates pass. However its registered 95%-reliable total-movie span remains 0M; the anchor frame passes for 83.6% rather than the required 95%, and tau=-28M passes for 15.4%. The stage therefore remains negative.

| Method | SNR | Arm | Identification | Pair-both | Median support error | Span95 |
|---|---:|---|---:|---:|---:|---:|
| old595 ridge | 300 | direct | 50% | 0% | 0.906 | 0M |
| old595 ridge | 300 | labelled | 100% | 100% | 0.339 | 2M |
| rich1617 ridge | 300 | direct | 50% | 0% | 0.982 | 0M |
| rich1617 ridge | 300 | labelled | 100% | 100% | 0.235 | 0M |

The result isolates the remaining issue more cleanly: even with a representable current background, fitting off-basis historical structure with a globally regularized finite tensor basis causes enough temporal/spatial leakage that the 95% contiguous-movie criterion fails. This is not a forward-integration failure and does not erase the perfect twin identification.

No new physical calls or Paper-I units were used. A neural successor requires a new registration and fresh train/validation/test populations; Movie010's test set cannot be reused as a neural held-out set after these outcomes.
