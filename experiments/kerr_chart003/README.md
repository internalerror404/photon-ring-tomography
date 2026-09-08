# Mahakal II — Kerr transfer chart, pilot003

Executed independent Kerr emitting-crossing pilot. **One rotating-Kerr order2 chart; not full image validation or source-history recovery.**

Start with SUMMARY.json and PER_MODEL_RESULTS.csv. Main result: a classical9x9 tensor cubic passes the fixed5e-4 max-channel response target with2.4993e-4 relative error. A physics-informed endpoint network improves its data-only neural counterpart at all three seeds but remains above target (median1.5301e-3). Both were frozen into explicit splines and evaluated independently. Three classical grids demonstrate refinement to3.2375e-7.

Spin0.5, inclination50degrees, finite observer100M; source annulus6..20M and circular prograde emission. The third equatorial crossing is computed by separated quadrature and checked with an independently integrated compactified geodesic ODE.128 withheld primary comparisons;48 independently traced rays plus144 independent detector nodes. These methods share the specified physics, not numerical path integration.

Registration commit9d9972a60469b57c80a66454b699cba366513cdc preceded calibration/training/test outcomes; geometry-only scouting and a polar-quadrature repair preceded registration and are retained. The knot-split integration supplement followed the primary result, with no candidate changes. A partial optimizer timeout is disclosed.

## Reproduction

Copy source/ and protocol.json to a NEW writable directory, install requirements.txt, then run:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python source/run_all.py
```

No external map is loaded. All arrays/checkpoints are supplied in the accompanying full package. run_all.py refuses an existing completed training run. The main evaluation has no new candidate sweep or inference fit; the matrix/noise/support/threshold remain fixed. Results include errors for all seeds, independent method discrepancies and ray-attempt accounting. The unchanged main experiment does not require the timeout-recovery script; it is retained as an execution-history record.

The interval-style radial error estimate is conditional on the exact equation residual; its floating-point evaluation is not a certified global enclosure. The actual rendered patch is only0.0368706M^2 in a declared impact-parameter plane; finite observer screen-angle calibration and the rest of the image are not established.

Paper I and its854-unit allowance are unchanged. This experiment lives only on the separate Paper-II branch.

## Interpretation

The data-only neural median maximum error is0.26292%; the integral-physics neural median is0.15301%; the81-ray classical cubic is0.024993%, below the0.05% target. Paired physics improvements are67.90%,11.72%,34.73%, whose median is34.73%. That is different from the relative change of group medians. The physics model has additional equation information and a reduced output factorization; their contributions have not been separately isolated.

ODE-vs-quadrature maximum errors on48 withheld rays are2.87e-12M in radius,3.30e-10rad in phase,2.11e-9M in time, and2.78e-14 in redshift. Independent144-node matched-rule detector discrepancy is1.65e-10 relatively. Those are numerical verification results on tested points and diagnostic fields, not a global proof of continuous quadrature or complete emitting-domain coverage.

The full report, attempt ledger, frozen coefficients and model weights are retained in the delivered experiment package. This source directory supports an independent fresh reproduction without any proprietary ray map. No source inverse, NeRF movie, Kiran router or cross-geometry neural operator is implemented in this local forward pilot.
