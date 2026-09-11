# Movie010 Stage A — background-controlled off-basis twins

**Return:** `MOVIE010_STAGEA_FAIL`  
**Neural Stage B:** not authorized and not run.

Movie010 replaced Movie009's shared off-basis background by an unknown background lying exactly in the frozen 595-dimensional class and used fresh analytic old-feature twins. Direct twin identification remains 50% with pair-both 0%; both labelled classical estimators identify 100% of siblings and 100% of pairs. Clean q8/q12 gates pass, and the rich 1617-dimensional fitted-field gate passes.

At SNR0=300:

| Method | Arm | Identification | Pair-both | Median support error | Span95 | Span90 |
|---|---|---:|---:|---:|---:|---:|
| old595 ridge | direct | 50% | 0% | 0.861 | 0M | 0M |
| old595 ridge | labelled | 100% | 100% | 0.274 | 4M | 6M |
| rich1617 ridge | direct | 50% | 0% | 0.986 | 0M | 0M |
| rich1617 ridge | labelled | 100% | 100% | 0.210 | 0M | 0M |

The rich labelled estimator reduces median error in every one of 128 paired cases per family: 80.6% narrow hotspot, 70.3% shearing spiral, 80.9% split/merge, and 79.2% held-out radial plume. Nevertheless, the preregistered 95%-reliable total-movie span remains 0M. Frame pass rates are 95–96% at -6M/-8M, roughly 84–88% through -10M to -24M, 76% at -26M, 31% at -28M, and 73% at the anchor.

The new diagnosis is precise. The background is in the old 595-dimensional class, but the 1617-dimensional comparison class uses a non-nested temporal B-spline grid, so it does not contain the old background exactly. The old595 arm reconstructs the anchor well but lacks the angular bandwidth for the old features; the rich arm improves the old features but reintroduces a background representation mismatch. This is a basis-nesting failure, not a physical integration failure or an inability to distinguish the twins.

The next justified experiment is a separately registered nested enrichment that contains the full 595-dimensional class exactly and adds higher azimuthal harmonics. No threshold or Movie010 result is changed. No new physical calls or Paper-I units were used.