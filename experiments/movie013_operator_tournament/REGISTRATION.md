# Mahakal II Movie013 — controlled operator tournament

**Base:** completed Movie011 nested-enrichment closeout `20804753cb80fd3786b5bdf71495bfb65ed3c3e4`.  
**Status:** registered before constructing any Movie013 operator variant, selecting any Movie013 regularization value, or evaluating any tournament endpoint.  
**Purpose:** determine whether the present movie-recovery limit comes from the physical ray-to-pixel map, a merely equivalent coordinate representation, the source representation, or background/history conditioning.

No new Kerr ray, path integral, ODE trajectory, hull/critical root, visibility sample, or Paper-I unit is authorized.

## 1. Repository ruling carried forward

The canonical Paper-II line currently establishes:

- Movie007: positive measured-support recovery, but its union-support endpoint mixes historical-time reach and added spatial coverage;
- Movie008: exact direct-null twin identification and low-dimensional coefficient recovery pass, while the registered all-active-frame movie endpoint fails;
- Movie009: natural off-basis twins are identified but the total-movie span fails when both background and old feature are off the inverse class;
- Movie010: putting the unknown background in the old 595-dimensional class preserves identification but a nonnested rich basis still gives 0M 95%-reliable span;
- Movie011: exact nested angular enrichment removes the background-containment defect, but smooth quadratic ridge still gives 0M reliable span;
- Movie012 Retarded Latent Field is separately frozen and remains an active learned-prior experiment, not an input result for Movie013.

Movie013 does not overwrite or relabel any of those outcomes.

## 2. Frozen samples and acquisition

Use the complete authenticated Movie007 artifact with its exact:

- 36 validation and 60 held-out in-basis movie coefficients;
- 20 deterministic off-basis histories (10 narrow hotspots and 10 shearing spirals), regenerated from the executed source and seeds;
- validation and test Gaussian-noise streams;
- q8 inverse and q12 reference operators for direct order `n=0` and first indirect order `n=1`;
- 8x8 pixels per order, 13 observer times, one direct-reference noise density shared across orders;
- union measurement-support and full-annulus movie metrics;
- frame rule `relative error <=0.35` and structural correlation `>=0.75`.

All variants receive the same source histories, q12 clean observations, direct/order-1 noise realizations, arm pairing, validation budget, and test rows. A baseline replay must reproduce the archived Movie007 regularization selections and aggregate/off-basis results before any variant is interpreted.

Required input hashes are taken from the Movie007 manifest and include:

- `PHYSICAL_AND_OPERATOR_ARRAYS.npz`: `54204f14b8c834fb3c54dc012c9827e711f339fc6c30251802fea71ac6d8274e`;
- `SUPPORT_WEIGHTS.npz`: `72080e09e722b01a821d2989d706f21eccfc9ce7671d1fa2f18f66bcd56a7952`;
- `REGULARIZATION_SELECTION.json`: `f3739497a08973bec6ed0b5c174188ad1b2321b469efa06750de2b43bcddf090`;
- executed `movie007_run.py`: `8b80d533cd48400570e505423053a6557e4a2ea6f3d82367adfd5c88b34e5cf1`;
- executed `offbasis.py`: `54c1e0ca0f1b2e2d94c34604eecb19c44c4c96a9e59b377f74b303b35aac4b97`.

## 3. Operator variants

### O0 — `RAY595_BASELINE`

The existing 595-dimensional physical ray-to-pixel operator, source Gram, quadratic penalty, and validation-selected ridge procedure. This is the reproduction control.

### O1 — `RETARDED_TIME_DCT_EQUIVALENT`

Whiten O0 first, then apply an orthogonal 13-point DCT independently to each pixel/order time series. Transform observations and operator rows together; retain the same source metric and penalty. Because this is an orthogonal row-coordinate change, its Gram, fitted movie, and likelihood information should be identical to O0. Any material recovery change is an implementation failure, not an operator discovery.

### O2 — `GREEN_NESTED_1445`

Keep the same q8/q12 physical ray samples and detector integration, but represent the continuous source with the exact nested class used by the completed Movie011 mechanics: five original cubic radial splines, real angular harmonics through `m=8`, and the same 17 temporal splines. Dimension `5 x 17 x 17 = 1445`. The original 595-dimensional class must embed exactly. Use the declared source `L2(r dr dphi dtau)` metric and identity ridge in source-orthonormal coordinates. Select one exponent per arm on the frozen Movie007 validation bank only.

This variant changes the source representation, not the underlying Kerr propagation or detector acquisition.

### O3 — `HISTORICAL_INNOVATION_1445`

Use the same nested physical operator as O2, but split source-normalized coordinates into an old compact target (temporal indices 0–6) and the complementary recent/background nuisance coordinates (indices 7–16). Fit both jointly with separate nonnegative ridge strengths selected on the same validation population from a fixed 5x5 exponent grid. Algebraically evaluate the equivalent Schur/block system; do not discard direct rows or pretend nuisance projection creates new photons.

This variant tests whether background/history conditioning, rather than the Kerr map itself, is the practical inverse bottleneck.

### O4 — `DELAY_RESOLVED_ORACLE` (secondary only)

If implemented, split each q12 pixel/order integral into fixed retarded-time bins before summation, with bin noise derived from the same area-noise density. This changes the acquisition by assuming delay-resolved readout. It is reported only as an upper-bound diagnostic and cannot win the primary same-data tournament.

## 4. Selection and evaluation

Primary noise level is `SNR0=300`; `SNR0=100` is secondary. Each non-equivalent variant receives the same ridge-candidate count. No family-specific or test-dependent tuning. O1 inherits O0 settings because it is mathematically equivalent.

For every variant and arm report:

- in-basis validation score and frozen regularization choice;
- held-out median support error, 95%/90% reliable span, per-family paired reduction, and full-annulus control;
- off-basis narrow-hotspot and shearing-spiral errors and spans on the exact archived samples;
- q8/q12 clean and fitted response discrepancies;
- numerical rank, leading/threshold singular values, and effective dimension;
- wall time and peak matrix memory;
- for O3, old-target and nuisance contributions separately;
- for O1, maximum coefficient, prediction, Gram, and objective disagreement from O0.

## 5. Gates and interpretation

Mechanics gates:

1. every input hash and the Movie007 baseline replay pass;
2. O1 matches O0 to `1e-10` in fitted coefficients/movie values and to `1e-12` relatively in the whitened Gram;
3. O2/O3 contain O0 exactly to `1e-11` on source grid and q8/q12 ray coordinates;
4. q8/q12 clean and fitted discrepancies remain <=`5e-4` relatively and <=`0.1` whitened;
5. no new physical call or Paper-I unit is used.

A non-equivalent variant is a practical tournament winner only if, on the same held-out data, it:

- reduces labelled off-basis median active-frame error by at least 20% relative to O0 in both off-basis families **or** produces a nonzero 90%-reliable off-basis span in at least one family;
- preserves the in-basis labelled 95%-reliable span within 2M of O0 and does not worsen in-basis median error by more than 5%;
- passes every mechanics and q8/q12 gate.

The tournament may validly conclude that no operator representation wins. Orthogonal row/source coordinate changes cannot increase Fisher information when covariance and regularization are transformed consistently. A gain from O2 is attributed to source representation; a gain from O3 to target/nuisance regularization or conditioning; only O4 changes the acquisition.

## 6. Limits

- CPU float64, one BLAS thread, <=8GiB working memory, <=45 minutes.
- Preserve all validation scores, selected hyperparameters, singular diagnostics, off-basis parameter ledgers, numerical failures, and negative endpoints.
- Movie012 learned-prior results, if produced concurrently elsewhere, cannot alter Movie013 definitions or thresholds.
