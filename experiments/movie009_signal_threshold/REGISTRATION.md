# Mahakal II Movie009 — fresh signal threshold for direct-null movie recovery

**Base:** completed Movie008 branch head `9fec2492b818ccf37e409e9644638913b61e96b5`.  
**Purpose:** independently test the signal level at which the already frozen first-indirect Kerr target supports the registered 95%-reliable frame-by-frame movie criterion, using fresh nuisance backgrounds, target directions, signs, and noise.  
**Status:** registered before any Movie009 source, noise, estimate, frame metric, threshold outcome, or plot is generated.

Movie008 is not reclassified: at SNR0=300 and alpha=0.08 it passed causal twin identification and four-mode coefficient recovery but failed the strict movie endpoint, 12.92% versus 95%. Its postplanned same-test diagnostic suggested a crossing near alpha=0.40. That diagnostic motivates this fresh replication but supplies no Movie009 evidence.

No new ray, Kerr quadrature, ODE path, hull/root, or Paper-I unit is authorized.

## 1. Frozen physical and target inputs

Authenticate and reuse, without alteration:

- Movie007 q8/q12 direct and first-indirect source-linear operators, source Gram, covariance, and order-1 support weights;
- Movie008 four-mode bank SHA256 `da24a26323d615b8f1896be6caa5b9f571601c70446c5bc95e916a7abd0029e1`;
- the exact 210-dimensional old non-axisymmetric parent, 385-dimensional nuisance partition, nuisance ranks, and q8 conditional estimator;
- q12 clean data generation and q8 inference;
- direct target response exactly zero at both rules;
- one Kerr chart, ideal order labels, 8x8 pixels per order and 13 observer times.

The four target modes, nuisance space, metric, and estimator are not reselected in Movie009.

## 2. Fresh source population

Generate 60 fresh nuisance backgrounds with RNG seed `90061`, using the Movie008 nuisance-only generator and certified coefficient envelope at most 0.25.

Generate 60 fresh target directions with RNG seed `90062`, 20 each from two-, three-, and four-mode combinations. Use the same truth-geometry activity rule as Movie008: at least eight active frames among tau=-6,-8,...,-28M and activity in both temporal halves. Additionally require the unit target direction's analytic coefficient envelope to be at most 0.50, so both signs remain at least 0.51 when alpha=0.48 and the background envelope is 0.25. Accept the first candidates satisfying these truth-only conditions, with at most 500 attempts per group. No observation or reconstruction quantity enters acceptance.

For every background/direction pair retain both balanced signs `1+b±alpha h`. Four paired Gaussian noise draws use seed `90063`; plus/minus twins receive identical direct noise and identical order-1 noise. Direct and labelled arms share the same direct rows and noise.

## 3. Fixed signal ladder and estimators

Primary noise level: direct-reference `SNR0=300`. Fixed target source-norm ladder:

`alpha in {0.08, 0.16, 0.24, 0.32, 0.40, 0.48}`.

The whole ladder is evaluated; no amplitude is selected or removed after outcomes. Alpha=0.08 is an independent replication of Movie008's registered condition. Alpha=0.40 and 0.48 test the postplanned threshold prediction with fresh sources/noise.

Secondary noise level: `SNR0=100` on the same amplitude ladder.

Primary estimator: the already frozen nuisance-profiled four-mode q8 conditional GLS. Direct estimate is the registered zero vector because the target response is exactly null. No new regularization or estimator search.

## 4. Unchanged movie metric

Render true and estimated four-mode target components on the same 32x64 source grid and use the Movie008 order-1-only geometry support weights. Registered old frames are tau=-6,-8,...,-28M. A truth frame is active when its weighted RMS is at least 20% of that history's maximum; each accepted history has at least eight active frames.

An active frame passes when weighted relative error is at most 0.35 and weighted structural correlation is at least 0.75. A reconstruction passes the movie endpoint only when every active frame passes.

## 5. Primary endpoint and success criteria

For each SNR/amplitude, evaluate 60 pairs x 2 signs x 4 draws = 480 cases. Bootstrap the 60 pair clusters with 2,000 resamples, seed `90064`; both signs and all draws move together.

The primary endpoint is

`alpha_95 = the smallest predeclared SNR300 amplitude whose labelled all-active-frame movie pass rate is at least 95%`.

Movie009 passes if all conditions hold:

1. authentication, direct-null, paired-noise, positivity, q8/q12 response, and source-activity gates pass;
2. `alpha_95` exists on the ladder and is at most 0.48;
3. at `alpha_95`, labelled twin identity is at least 95%, median target error at most 0.35, and 90th-percentile target error at most 0.60;
4. at `alpha_95`, each two-/three-/four-mode group has at least 90% movie-pass rate and at least 95% twin-identity accuracy;
5. the 2.5th percentile of the pair-cluster bootstrap movie-pass rate at `alpha_95` is at least 90%;
6. direct identity remains exactly 50% and direct movie pass remains zero under byte-identical paired direct observations;
7. no claim exceeds a fresh, in-model, direct-null, one-chart, ideal-order-label movie threshold.

Report the full amplitude curve, including any nonmonotonicity, and the SNR100 secondary curve. Failure does not authorize changing the ladder, activity definition, frame thresholds, estimator, or mode bank.

A positive return is named `MOVIE009_FRESH_DIRECT_NULL_MOVIE_THRESHOLD_PASS`. It supports a signal-threshold statement, not arbitrary/off-basis/full-annulus/visibility-domain/telescope movie recovery.

## 6. Resources and provenance

- exactly zero new physical calls;
- fresh backgrounds 60, directions 60, both signs, four draws;
- CPU float64, one numerical BLAS thread, at most 8GiB;
- commit executable source and input/mode hashes before generating fresh sources;
- save accepted/rejected direction ledger, backgrounds, paired observations, estimates, all frame metrics, amplitude curves, bootstrap intervals, numerical checks, and one predeclared visualization: four-mode group pair index 50, positive sign, draw 1 at `alpha_95`;
- Paper I remains unchanged with 854 units.
