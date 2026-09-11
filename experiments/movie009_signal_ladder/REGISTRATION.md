# Mahakal II Movie009 — direct-null movie signal-strength ladder

**Lineage:** successor to Movie008 at `9fec2492b818ccf37e409e9644638913b61e96b5`. Movie008 established exact direct nullness, 100% first-indirect twin identification, and four-mode coefficient recovery at `SNR0=300, alpha=0.08`, but failed its preregistered 95%-all-active-frame movie endpoint. Its post-outcome reuse diagnostic suggested a crossing near a much larger amplitude; that diagnostic fixes the rationale for this experiment but is not evidence for its result.

**Question:** on a fresh source/noise population, what is the smallest predeclared source-norm amplitude at which the first indirect Kerr image supports a 95%-reliable frame-by-frame movie while the direct image remains exactly unable to distinguish the twins?

This is a registered development replication and phase diagram, not a replacement of Movie008. No new ray, geodesic integral, physical quadrature, visibility model, or Paper-I unit is authorized.

## 1. Frozen physical and source-space inputs

Reuse, by exact hash, the Movie008 inputs and frozen q8-selected mode bank:

- Movie007 `PHYSICAL_AND_OPERATOR_ARRAYS.npz`: `54204f14b8c834fb3c54dc012c9827e711f339fc6c30251802fea71ac6d8274e`;
- Movie007 `SUPPORT_WEIGHTS.npz`: `72080e09e722b01a821d2989d706f21eccfc9ce7671d1fa2f18f66bcd56a7952`;
- Movie007 `REGULARIZATION_SELECTION.json`: `f3739497a08973bec6ed0b5c174188ad1b2321b469efa06750de2b43bcddf090`;
- frozen `MODE_BANK.npz`: `da24a26323d615b8f1896be6caa5b9f571601c70446c5bc95e916a7abd0029e1`.

The physical model remains one Kerr chart at `a=0.5`, inclination `50 deg`, observer radius `100M`, ideal labels for direct order `n=0` and first indirect order `n=1`, and the 595-dimensional source basis used by Movie007/008. The four source-orthonormal old nonaxisymmetric modes were selected before Movie008 sources from a 210-dimensional exact direct-null target after profiling a declared 385-dimensional nuisance movie. They are not reselected here.

The q8 operator is used for inference. q12 supplies clean observations and numerical comparison. Direct response must remain exactly zero at both rules.

## 2. Fresh source and noise population

Use new independent seeds:

- nuisance backgrounds: `81061`;
- two-/three-/four-mode target directions: `81062`;
- Gaussian noise: `81063`;
- paired history-cluster bootstrap: `81064`.

Generate 60 accepted directions: 20 each with two, three, or four nonzero coordinates in the frozen four-mode bank. A direction is accepted using truth geometry only when it has at least eight active old frames under the unchanged Movie008 order-1 support metric and activity rule, with activity on both halves of the old interval. No reconstruction outcome is used.

Each pair receives one smooth nuisance background in the registered 385-dimensional nuisance space, certified coefficient envelope at most 0.25. Both signs are retained as positive twins `j=1+b +/- alpha h`. A candidate direction is eligible only if the analytic coefficient envelope guarantees emissivity at least 0.5 for both twins at the largest registered amplitude. Record all accepted/rejected direction candidates and positivity bounds.

For every pair and amplitude, use two signs and four paired noise draws. Within each pair/draw, direct data and direct noise are byte-identical between signs. Fresh source/noise outcomes from Movie008 are not reused.

## 3. Fixed signal ladder and estimators

Primary SNR: `SNR0=300`. Secondary stress: `SNR0=100`. The predeclared source-norm amplitudes are

`alpha in {0.08, 0.16, 0.24, 0.32, 0.40, 0.48}`.

All six amplitudes are reported; none is selected by fitting a curve. The experiment may return no crossing.

Primary labelled estimator: the nuisance-profiled four-mode conditional GLS already defined in Movie008. Primary direct estimator: the exact zero target estimate, because the direct target response is identically zero. The exact pair-likelihood selector is retained only as a candidate-pair upper-bound diagnostic. No ridge/TSVD/NeRF/PINO/Kiran candidate is tuned or promoted in this experiment.

The source/movie metric, frame times `tau=-6,-8,...,-28M`, relative-activity rule, frame thresholds (`relative error <=0.35`, weighted structural correlation `>=0.75`), and all-active-frame conjunction are unchanged from Movie008.

## 4. Primary threshold endpoint

For every SNR and amplitude report:

- direct and labelled twin-identity accuracy;
- median and 90th-percentile four-mode coefficient relative error;
- all-active-frame movie pass rate;
- per-time frame pass/error/correlation summaries;
- per-complexity-group movie pass and identity;
- q8/q12 twin-response differences;
- minimum analytic emissivity bound;
- conditional Gaussian prediction for coefficient RMS error.

At `SNR0=300`, define `alpha_star` as the smallest tested amplitude satisfying all of:

1. direct identity exactly 50%;
2. labelled identity at least 95%;
3. labelled all-active-frame movie pass at least 95%;
4. 2,000-resample paired history-cluster bootstrap lower 2.5% endpoint for movie pass at least 90%;
5. each of the two-/three-/four-mode groups has movie pass at least 90%;
6. every direction has at least eight active frames;
7. analytic emissivity lower bound at least 0.5;
8. q8/q12 twin-response discrepancy at most `5e-4` relatively and `0.1` whitened;
9. exact direct q8/q12 nullness and byte-identical paired direct observations;
10. no physical call and no Paper-I unit.

If the first passing grid point is `alpha_k`, report the threshold only as the tested bracket `(alpha_{k-1}, alpha_k]`; do not infer a continuous critical amplitude. If no point passes, report `alpha_star > 0.48` under this ladder.

## 5. Interpretation and limits

A passing result would establish a fresh-population contrast threshold for reliable reconstruction of a four-mode, measurement-supported, direct-null historical movie on one Kerr chart. It would not establish arbitrary-morphology, off-basis, full-annulus, multi-chart, visibility-domain, telescope, or observational movie recovery. It would also not turn the post-outcome Movie008 amplitude diagnostic into a prospective result.

A failed result remains informative and does not authorize changing the amplitude grid, frame thresholds, source activity rule, estimator, source family, or bootstrap requirement.

## 6. Resource and governance limits

- new physical calls: exactly zero;
- Paper-I convention-B units: exactly zero;
- fresh pairs: 60; signs: 2; draws: 4; amplitudes: 6; SNRs: 2;
- CPU float64, one BLAS thread, <=8 GiB working memory;
- source and input hashes committed before generating fresh backgrounds, directions, noise, or outcomes;
- save candidate ledger, backgrounds, directions, standardized noise, coefficient estimates, per-frame metrics, aggregate/group curves, bootstrap distributions, analytic predictions, and exact provenance.
