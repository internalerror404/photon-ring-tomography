# Mahakal II Movie008 — direct-null twin-movie recovery

**Base:** audited Movie007 commit `e93c659f16ac1d8723968c13dea9f91e8bea66ef`.  
**Question:** can the first indirect Kerr image select and reconstruct the correct old spatial movie when two positive histories give exactly the same direct observations?  
**Status:** registered before the Movie008 mode bank, fresh backgrounds, twin signs, noise, estimates, or endpoints are generated. This is a development experiment, not an externally sealed main.

The pre-registration repository audit inspected the Paper-II lineage, the complete Movie007 artifact, and the q8/q12 operators. It found the exact direct-null subspace and inspected its q12 stability. That operator-only knowledge is disclosed and is not presented as a held-out Movie008 result. The fresh held-out elements are the nuisance backgrounds, target-mode combinations, signs, and noise draws.

No new ray, Kerr quadrature, ODE trajectory, hull/root, or Paper-I unit is authorized. Paper I remains unchanged with 854 convention-B units.

## 1. Authenticated physical inputs

Use the Movie007 artifact with full-package SHA256
`3bfbc5ec24d14a17515dc3c3beadc3e95ca2b9b5eea40922ebb614f67289edad`.
Required source/array identities are checked before computation. The physical setting remains:

- Kerr `a=0.5`, inclination `50 degrees`, static observer at `100M`;
- the common chart `lambda in [0.5,3.0]`, `z in [0.3,0.7]`;
- direct `n=0` and first-indirect `n=1` ideal order labels;
- 8x8 detector pixels per order and 13 observer times `0,2,...,24M`;
- q8 source-linear operators for construction/inference and q12 operators for clean data generation/numerical readback;
- the same direct-reference noise-density calibration at `SNR0=300`, with `SNR0=100` secondary;
- the same 595-dimensional movie basis, source Gram, and pixel-integrated covariance.

The exact Movie007 executed source is now deposited post-execution under `experiments/movie007_support/executed_source/`; its frozen hashes must match the audit. Movie006 has no final movie endpoint and supplies no Movie008 result.

## 2. Exact direct-null target and declared nuisance model

The 595 coefficient ordering is radial x angular x temporal, with 5 clamped cubic radial B-splines, seven real angular factors `[1,cos(phi),sin(phi),...,cos(3phi),sin(3phi)]`, and 17 compact linear temporal B-splines.

Define the **210-dimensional target parent space** by:

- all five radial factors;
- the six non-axisymmetric angular factors;
- temporal basis indices 0 through 6.

Those temporal functions end before the sampled direct retarded-time footprint. The q8 and q12 direct target matrices must therefore be exactly zero, not merely below a tolerance.

Define the **385-dimensional nuisance space** by:

- every radial/angular factor with temporal indices 7 through 16 (350 coefficients);
- all five radial factors with the axisymmetric angular factor and old temporal indices 0 through 6 (35 coefficients).

This is an explicit restricted source model. Other old non-axisymmetric directions are excluded from the nuisance model. Supported005 already showed that sufficiently flexible signed nuisance spaces can absorb selected historical targets; Movie008 does not claim identification against arbitrary source histories.

## 3. Frozen four-mode historical movie bank

Using q8 only:

1. source-normalize the 210 target parent space with its exact sub-Gram;
2. whiten the stacked q8 direct+order1 rows using the shared SNR300 covariance;
3. project target responses orthogonally away from the q8 nuisance response space using relative rank tolerance `1e-12`;
4. take the first four right singular vectors of that conditional operator;
5. fix each sign by making its largest-magnitude coefficient positive;
6. save the mode coefficients, conditional responses, singular values, parent/nuisance indices, and hashes before generating a source.

The audit found q8 conditional singular values approximately `91.3922, 90.7556, 89.6611, 87.0778` for these four modes and near-identical q12 responses. These numbers are design inputs already inspected, not fresh endpoints. The frozen bank must be source-orthonormal to `1e-10`, exactly direct-null at both q8 and q12, and have q8/q12 conditional response correlations above `0.99999`. Failure blocks the source experiment; no alternate mode count or mode-selection rule is allowed.

## 4. Fresh positive twin histories

Generate 60 fresh nuisance backgrounds with seed `80061`. Coefficients are restricted to the 385-dimensional nuisance space, smoothed and harmonic-weighted by the frozen implementation, then rescaled by an analytic B-spline/Fourier coefficient envelope so their absolute contrast is at most 0.25 everywhere in the declared source box.

Generate target directions with seed `80062` in three fixed complexity groups, 20 pairs each:

1. one-mode: one of the four frozen modes, cycled deterministically;
2. two-mode: two nonzero Gaussian coefficients, normalized in the four-mode Euclidean/source norm;
3. four-mode: four Gaussian coefficients, normalized in the same norm.

A direction is accepted using truth geometry only when its order1-support-weighted movie is active on at least eight frames among `tau=-6,-8,...,-28M`, including at least one frame in each half of that interval. The first accepted candidates are used, with at most 500 candidates per group. No reconstruction quantity enters acceptance.

For each background `b_i` and unit target direction `h_i`, form the balanced twins

`j_i^+ = 1 + b_i + alpha h_i`,  `j_i^- = 1 + b_i - alpha h_i`.

Primary target source norm: `alpha=0.08`. Secondary amplitude: `alpha=0.04`. The analytic coefficient envelope must guarantee `j>=0.5` everywhere for both signs. Both signs are retained; no favorable sign selection.

## 5. Paired observations

Generate clean data with q12. Within each background/direction/noise draw:

- the plus and minus twins receive the same direct noise realization;
- the plus and minus twins receive the same order1 noise realization;
- direct and labelled arms share the identical direct rows and noise;
- four draws use seed `80063`;
- `SNR0=300` is primary and `SNR0=100` secondary.

Required construction gates:

- q8 and q12 direct clean twin difference is exactly zero;
- paired noisy direct observations are byte-identical between signs;
- every primary-amplitude q12 labelled twin separation is at least 5 in the shared whitened norm;
- q8/q12 labelled twin-response discrepancy is at most `5e-4` relatively and `0.1` whitened.

## 6. Frozen estimators

### Primary: nuisance-profiled four-mode GLS

Use the q8 nuisance projector and frozen four-mode target response. No test-dependent regularization or threshold is selected. Estimate all four target coefficients from the nuisance-residualized data by the Moore-Penrose/normal-equation solution at relative tolerance `1e-12`.

For direct-only data the target operator is exactly zero. The registered direct estimate is the zero four-vector; no prior-generated target completion is credited as measured recovery.

### Secondary: frozen Movie007 whole-movie estimators

Apply the already frozen Movie007 ridge and TSVD choices without retuning:

- direct ridge exponent `1`, TSVD cutoff `1e-3`;
- labelled ridge exponent `-2`, TSVD cutoff `3e-3`.

Project their 595-dimensional reconstructions onto the frozen four-mode bank and report both target-component and full-movie behavior. These secondary results test whether the broad Movie007 estimator preserves the causal signal; they cannot replace the primary finite-target result.

A pair-likelihood selector computed from the two known clean candidates is reported only as an upper-bound diagnostic, not as blind movie reconstruction.

## 7. Primary causal endpoints

The primary population contains 60 backgrounds x 2 signs x 4 paired noise draws = 480 reconstructions at each SNR/amplitude condition. Bootstrap resampling uses the 60 twin-pair/background clusters with 2,000 resamples, seed `80064`; both signs and all draws move together.

For the primary amplitude and SNR300 report:

1. **Twin identity:** nearest of the two true four-mode coefficient vectors. Direct accuracy must be exactly 50% under balanced paired twins; labelled accuracy must be at least 95%.
2. **Target coefficient recovery:** median relative four-vector error at most 0.35 and 90th percentile at most 0.60 for labelled data.
3. **Old-movie component recovery:** render the true and estimated target components on the fixed 32x64 source grid. Use an order1-only geometry-defined support kernel, not Movie007's union support. A truth frame is active when its weighted RMS is at least 20% of that history's maximum; every history must have at least eight active registered old frames. A frame passes at relative error at most 0.35 and weighted correlation at least 0.75. At least 95% of labelled history/sign/draw cases must pass every active frame.
4. **Direct-null causality:** the direct estimator must produce identical outputs for both signs under the shared-noise construction; any direct candidate preference is model/prior completion, not data evidence.
5. **Family consistency:** labelled twin accuracy at least 90% in each of the one-, two-, and four-mode groups.
6. **Numerical gates:** all authentication, source-orthonormality, direct-null, q8/q12 response, positivity, and linear-algebra replay checks pass.

A positive return is named `MOVIE008_DIRECT_NULL_TWIN_MOVIE_PASS`. It supports the statement that order1 selects and reconstructs the correct member of a direct-indistinguishable finite movie pair under the declared source/nuisance model. It does **not** establish arbitrary, off-basis, full-annulus, visibility-domain, or telescope movie recovery.

The secondary amplitude, SNR100, Movie007 ridge/TSVD, full source-box errors, and any failed family are retained regardless of outcome. Thresholds, mode count, nuisance definition, amplitudes, or source acceptance are not changed after results.

## 8. Resources and delivery

- New physical calls: exactly zero.
- Fresh backgrounds: 60; target directions: 60; both signs retained.
- Four paired draws; two SNR levels; two amplitudes.
- CPU float64, one BLAS thread, no paid resource, at most 8GiB working memory.
- Commit the mode-bank source/configuration before fresh source outcomes.
- Save source/mode hashes, target/nuisance indices, twin coefficients, clean/noisy data checks, primary and secondary estimates, per-frame metrics, bootstrap results, and one predeclared four-mode visualization (pair index 50, draw 1, SNR300, primary amplitude).
- Deposit executable source in GitHub before the fresh source run. Binary Movie007 inputs may remain in the authenticated artifact package, but their hashes and expected shapes are recorded.
