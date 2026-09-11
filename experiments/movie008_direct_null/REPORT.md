# Mahakal II Movie008 — direct-null twin-movie experiment

**Return:** `MOVIE008_DIRECT_NULL_TWIN_IDENTIFICATION_PASS_MOVIE_FIDELITY_FAIL`  
**Registered gate:** `MOVIE008_DIRECT_NULL_TWIN_MOVIE_FAIL`

## Executive result

Movie008 tests the causal question left unresolved by Movie007's union-support comparison: can the first indirect Kerr image distinguish and reconstruct the correct old spatial movie when the direct observations are exactly identical?

The answer is split. At `SNR0=300` and registered target source norm `alpha=0.08`, direct-only data are exactly identical between balanced positive twins and give the required 50% identity accuracy. Direct plus order 1 identifies the correct twin in **100% of 480 held-out sign/draw cases**, with median four-coefficient relative error **0.2700** and 90th-percentile error **0.4034**. These causal-identification and coefficient endpoints pass.

The stricter movie endpoint does not: only **12.92%** of labelled cases pass every active historical frame, against the registered 95% requirement. Movie008 therefore establishes causal twin identification and low-dimensional historical-target recovery, **not** reliable frame-by-frame movie reconstruction at the registered signal level.

## Frozen target and nuisance construction

The source model has 595 coefficients. Before fresh sources were generated, q8 selected four source-orthonormal modes from a 210-dimensional old non-axisymmetric target after profiling a declared 385-dimensional nuisance movie. Their q8 conditional singular values are `91.3922, 90.7556, 89.6611, 87.0778`. The direct target response is exactly zero at q8 and q12; q8/q12 conditional-mode response correlations exceed `0.99999995`.

Sixty fresh nuisance backgrounds were combined with sixty fresh two-, three-, and four-mode target directions. Both signs were retained, giving twins `1+b±alpha h`. Four paired noise draws were used per twin. Within a pair, the direct observations—including noise—are byte-identical. The minimum q12 order-1 twin separation at the primary setting is **14.372** in the shared whitened norm.

## Primary endpoints

| Endpoint | Direct only | Direct + order 1 | Registered requirement |
|---|---:|---:|---:|
| Twin identity accuracy | 50.00% | **100.00%** | labelled >=95%; direct exactly 50% |
| Median four-mode relative error | 1.000 | **0.270** | labelled <=0.35 |
| 90th-percentile four-mode error | 1.000 | **0.403** | labelled <=0.60 |
| All-active-frame movie pass | 0% | **12.92%** | labelled >=95% |

All three complexity groups have 100% labelled identity accuracy. Their all-frame movie pass rates are 13.75% (two-mode), 11.25% (three-mode), and 13.75% (four-mode).

The pair-likelihood selector—an upper-bound diagnostic given the two exact clean candidates—also reaches 100% with order 1 and is an exact tie with direct data. It is not blind movie reconstruction.

## Why identity passes while the movie gate fails

The four coefficient vector is recovered well enough to select its sign, but the movie gate is an intersection across every active frame. At the primary setting, active-frame pass rates range from approximately 55.6% at `tau=-8M` to 95.0% at `tau=-24M`; only 62 of 480 cases pass all active frames. Most failures miss one to four active frames rather than the entire sequence.

Median spatial correlations are near one at most active frames, but low-amplitude and mode-cancellation frames amplify coefficient noise in relative-error and correlation tests. A clear pair-level signal can therefore identify which movie occurred while remaining insufficient for the registered 95%-reliable frame sequence.

## Secondary estimators and sensitivity

At the primary setting, the frozen Movie007 ridge and TSVD estimators preserve nearly all twin-identity information (99.79%) but perform worse on the target and movie endpoints: median coefficient error is about 0.437 and movie pass is 4.17–4.58%. The nuisance-profiled conditional GLS is the strongest tested estimator.

At `SNR0=100, alpha=0.08`, labelled identity remains 99.17%, but median coefficient error is 0.803 and movie pass is zero. At `SNR0=300, alpha=0.04`, identity remains 100%, median error doubles to 0.540, and movie pass falls to 2.08%.

## Numerical and provenance checks

- q8/q12 direct twin response: exactly zero;
- paired noisy direct observations: byte-identical;
- maximum q8/q12 twin-response discrepancy: `1.402e-4` relative and `2.021e-3` whitened;
- minimum analytic emissivity bound: `0.7215`;
- scalar/batched estimates agree exactly or to floating-point precision; movie-metric differences are below `6e-16` in error and `1.2e-16` in correlation;
- independent readback checks: all pass;
- new physical calls: **0**; Paper I units used: **0**.

The first scalar implementation hit the local time limit before writing fresh scientific outputs. Its failure is retained. An algebraically equivalent batched implementation was committed before rerun and passed the scalar/batch fixture.

## Postplanned diagnostic—not a result upgrade

After the registered failure was known, unchanged primary estimates were subjected to shrinkage and exact affine signal-amplitude readbacks. Scalar shrinkage raises movie pass only to 16.67%; fixed-norm projection reaches 18.54%. Reusing the same test directions and noise suggests the strict threshold would cross 95% near much larger target amplitude (`alpha≈0.40`).

This curve is postplanned and same-test. It does not rescue Movie008 and is not evidence of a fresh 95%-reliable movie. It only motivates a separately registered signal-threshold replication or a better noise-aware temporal estimator.

## Scientific conclusion

Movie008 gives stronger causal evidence than an average-error comparison: the direct image is mathematically and numerically unable to choose between two positive old histories, while the first indirect image chooses the correct one without error in this finite model. But successful identification of a low-dimensional historical alternative is not yet a reliable movie. The registered all-frame fidelity claim fails at `alpha=0.08`.

The supported statement is:

> Under the declared four-mode target and 385-dimensional nuisance model, first-indirect Kerr light identifies the correct member of direct-indistinguishable positive historical twins and recovers their low-dimensional coefficients at SNR0=300, but the signal is not sufficient for 95%-reliable frame-by-frame reconstruction at the registered amplitude.

This remains one Kerr chart with ideal order labels and an in-model target. It does not establish arbitrary, off-basis, full-annulus, visibility-domain, or telescope movie recovery.
