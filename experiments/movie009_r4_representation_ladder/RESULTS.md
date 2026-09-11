# Movie009-R4 — historical representation ladder

**Return:** `MOVIE009_R4_REPRESENTATION_LADDER_NO_WINNER`

With the true shared background supplied, six linear historical decoders were tested on the exact Movie009-R2 population.

| Representation | Span95 | Span90 | Median error | Differential pass | q8/q12 whitened |
|---|---:|---:|---:|---:|---:|
| Unweighted PCA, rank 96 | 10M | 14M | 0.16348 | 29.69% | 1.1504 |
| Unweighted PCA, rank 192 | **12M** | **22M** | 0.16228 | 32.81% | 1.1646 |
| Unweighted PCA, rank 384 | 8M | 12M | 0.19095 | 21.88% | 1.1626 |
| Measurement-weighted PCA, rank 96 | **12M** | **22M** | **0.15884** | 34.38% | 1.1835 |
| Measurement-weighted PCA, rank 192 | 8M | 10M | 0.19518 | **37.50%** | 1.1405 |
| Measurement-weighted PCA, rank 384 | 6M | 6M | 0.27871 | 14.06% | 1.1785 |

The source representation itself becomes much more accurate with rank. The test projection-floor error falls from 0.276 at unweighted rank 96 to 0.178 at unweighted rank 384 and 0.168 at measurement-weighted rank 384; the last representation can express all active frames for 95.31% of test movies before inversion.

The inverse does not realize that capacity. Higher rank opens weakly constrained directions, so recovery is nonmonotone and ultimately worsens. No variant approaches the required 90% differential all-frame pass. Every fitted reconstruction also fails the q8/q12 whitened criterion, remaining near 1.14–1.18 against the 0.1 limit.

This closes simple linear PCA rank and source-metric weighting as the missing ingredient. The next experiment should use a nonlinear, dynamics-aware continuous historical model that is evaluated directly by the frozen Kerr renderer rather than reconstructed through a global linear PCA decoder.

No new physical call or Paper-I unit was used.