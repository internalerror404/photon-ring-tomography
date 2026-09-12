# CACHE_REBUILD_001 - completed cache rebuild, finite-basis numerical gate failed

**Disposition:** `CACHE_REBUILD_001_COMPLETE_NUMERICAL_GATE_FAIL`.
**Registration:** `af1a93803f8a24959e63fdd64a5368d2f793a1ea`, before the first physical call.
**Branch:** `research/mahakal_II_cache_rebuild001_20260912`.

The authorized Paper-II-only physical computation actually ran to completion. This is a new cache and new implementation, not recovery of the original R2 execution. The original 93d990... source, original R2 records, and old input byte hashes remain unrecovered.

## Results

| Check | Outcome |
|---|---|
| Separated ray transfers | 26,752; 26,624 cache rays plus 128 validation/refinement calls |
| Independent compactified ODE transfers | 64; all paired trajectory checks passed |
| Ray validity | All scheduled cache rays emitting inside [6,13]M; no dropped ray |
| Analytic numerical fields | 89 fields, all 267 direct/order1/stacked checks passed |
| Worst analytic q8/q12 relative discrepancy | 7.993054267570888e-6, threshold 5e-4 |
| Worst analytic q8/q12 whitened discrepancy | 0.0001848876899178873, threshold 0.1 |
| Direct-null historical probes | All 64 feature probes exactly zero in direct q8 and q12 |
| Unit-coefficient basis checks | 1,643/1,785 passed; 142 failed, spanning 76 distinct columns |
| Worst basis relative discrepancy | 0.13412914380662044 |
| Worst basis whitened discrepancy | 0.1738557761133685 |
| Matrix/per-ray contraction | Maximum absolute disagreement 1.734723475976807e-18 |
| Source Gram Cholesky residual | 1.2987156904783766e-16 |
| Core numerical run | 23.1838 seconds; peak RSS 246,944 KiB |
| Paper-I units / new movie fits / posterior fits | 0 / 0 / 0 |

All four raw ray arrays, four 832x595 operators, the source Gram and factor, direct-reference noise calibration, and the 15x32x64 support weights were saved. No regularization choice was manufactured: validation selection and scientific inference are not part of this run.

The 64 independent trajectory checks have maximum [radius, wrapped phase, delay, redshift] differences [5.302425165609748e-13, 5.967937255491051e-11, 5.366445066101733e-10, 1.3433698597964394e-14]. The two formulations share the screen/invariant and redshift conventions, so their agreement does not independently validate those common assumptions.

## Basis failures: do not collapse two different effects

Direct: 28 of 595 fail the relative criterion, none the whitened criterion. Order1: 36 fail relative and 21 fail whitened, with no overlap. The stacked arm has the same counts as order1. Across all three arms this gives 142 failed column-arm checks; it is not 142 different source coefficients.

The worst relative case has q12 raw response norm 2.341218513032e-9 and whitened discrepancy only 4.097259294265558e-6. Its large relative ratio occurs for a very weak column. However, the 21 order1 columns failing the absolute whitened criterion are not explained away by a tiny relative denominator. No failures were rescaled, pruned or relabelled.

The producer's broader all-unit-column gate therefore fails. This conservative panel was prospectively added for the NEW implementation; it is not the old Movie007 fitted-field endpoint and does not revoke Movie007's recorded result. Nor does it prove that this integration discrepancy caused the old R2 movie failure. Passing the analytic panel cannot qualify every fitted linear combination, every posterior sample, or a continuum forward operator.

## Readback

A postplanned, no-new-physics audit verified all 53,632 hash-chain ledger events, paired every begin/end, matched every cache tuple and weight to its ledger, checked the four saved arrays, and exactly reproduced all 1,785 basis discrepancy metrics and gate decisions. Source hashes remained unchanged.

A second postplanned replay recomputed all 89 analytic responses using pixel-block sums instead of the producer's bincount accumulation. All 267 gate decisions agree; maximum absolute metric difference is 1.6650403079562796e-12. This is independent summation code, not independent source physics.

## Release boundary

The frozen source, qualification records and cache exist. Missing old artifacts are no longer necessary to build this NEW cache from readable source. The cache has NOT passed its broad registered numerical qualification, and no natural historical movie has been recovered in this run.

For a scientific successor, retain the required 12M/95% movie, 95% identification, 90% differential and actual clean/fitted q8/q12 gates. Numerical accuracy must be evaluated for the proposed representation and actual fitted fields, without using a passing analytic subset to erase this failed all-column panel. A coefficient-independent, source-knot-aware pixel-integration test is a reasonable next numerical hypothesis, not a demonstrated fix. No additional physical run or posterior experiment was performed here.

GitHub contains readable source plus compact registration/completion/readback records and output hashes. The full binary caches, per-ray ledger and complete per-field panels are in the accompanying artifact ZIP; their presence in GitHub is not claimed. All original experiment branches and Paper-I ledgers remain untouched.
