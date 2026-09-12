# KNOT_QUADRATURE_002 numerical consumer contract

This is a new cache identity, not an authenticated recreation of Movie007 or the original Movie009-R2. Do not overwrite their loader hashes or manufacture a regularization selection file. A future inference experiment must pin these files under a new registration.

## Ray data

`results/KNOT_q8_n0_RAYS.npz`, `KNOT_q8_n1_RAYS.npz`, and the corresponding q12 files contain:

- `tuple`: columns [source radius, source azimuth, delay, redshift g].
- `weights`: positive screen-area quadrature weights, including the chart Jacobian, but NOT g^3.
- `pixels`: integer 0..63. Nodes are sorted pixel-major and counts per pixel are variable.
- `chart_points`: columns [lambda,z].

Do not reshape these data into [64,q*q,...]. The q8/q12 labels denote Gauss order inside the new composite subpanels. The number of physical detector rows has NOT increased.

At each observer time `to = 0,2,...,24`, set `tau = to - delay + 100`. For a total emissivity j, raw 64-pixel flux is:

```python
flux = np.bincount(pixels, weights * g**3 * j(radius, azimuth, tau), minlength=64)
```

Rows concatenate in observer-time-major, then pixel-major order (832 rows/order). A labelled stack concatenates direct rows and then order-1 rows. Always use exactly the same direct values/noise for direct-only and labelled arms.

## Operators and whitening

`results/OPERATORS.npz` contains eight 832x595 raw source-linear matrices, keys `KNOT_q8_n0`, `KNOT_q8_n1`, `KNOT_q12_n0`, `KNOT_q12_n1`, and the four UNIFORM2 control analogues. Coefficient order is radial, azimuthal, temporal (5x7x17). The matrix maps contrast coefficients to contrast flux; the constant total-emissivity baseline must be handled separately and consistently.

`inputs/REBUILT_PHYSICAL_AND_OPERATOR_ARRAYS.npz` supplies the fixed source Gram H, H_chol, source grids and sigma300/area_n0/area_n1. Noise standard deviations are `sigma300 * tile(sqrt(area_n),13)`. This is the same original CACHE001 q12 reference noise law for all methods; do not recalibrate SNR from the improved quadrature. For SNR100 multiply the noise density by 3.

`inputs/REBUILT_SUPPORT_WEIGHTS.npz` supplies unchanged `support` and `full_annulus` grids. Neither is a posterior credible region. The support metric remains a frozen discrete geometry-defined weighting, not a full-annulus or continuum recovery claim.

## Qualification scope

Read the canonical completion and postplanned audit. The all-column q8/q12 panel does not replace actual clean/fitted-field checks for a new inference model. In particular, these source-knot partitions are tailored to the retained 595-dimensional basis. A different learned interpolated decoder has additional knot surfaces and needs its own numerical qualification. No posterior-calibration, twin-identification or movie-span result is supplied by this cache stage.
