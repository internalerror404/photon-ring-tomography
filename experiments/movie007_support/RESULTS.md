# Mahakal II Movie007 — actual result

**Return:** `MOVIE007_MEASUREMENT_SUPPORTED_MOVIE_PASS`

At normalized direct-reference SNR0=300, the validation-selected ridge estimator reconstructs a **28M contiguous historical source-plane movie** from the direct plus first-indirect Kerr channels at the registered 95% reliability criterion. The direct-only arm has a **0M** 95%-reliable span on the same union-of-measurements support metric. The registered gain is therefore **28M** on the 2M frame grid; all 2,000 history-cluster bootstrap resamples return that gain.

This is a deliberately bounded claim: one Kerr chart, ideal order labels, and a geometry-defined measurement-support metric. It is not full-annulus, visibility-domain, telescope, or observational black-hole movie recovery.

## Primary family results

| Family | Direct median error | Direct + order 1 | Median paired reduction | Improved pairs |
|---|---:|---:|---:|---:|
| Single broad hotspot | 0.94365 | 0.04762 | 95.41% | 80/80 |
| Two broad hotspots | 1.00306 | 0.04704 | 95.66% | 80/80 |
| Flare birth–motion–decay | 0.80693 | 0.04208 | 95.97% | 80/80 |

The labelled ridge median frame error is 0.027–0.093 over tau=0 to -28M, and median weighted structural correlation is 0.980–0.999. At tau=-28M, 99.17% of held-out history/draw pairs pass the registered frame criterion.

## Sensitivity and boundaries

At SNR0=100, the labelled ridge 95%-reliable span falls to **2M**. The full-annulus metric remains negative (median error 0.556 at SNR300), and exploratory narrow-hotspot and shearing-spiral off-basis stresses both have 0M reliable span. The positive result is therefore an in-class, high-normalized-SNR, partial-source-plane result.

A postplanned support decomposition shows that order 1 supplies 37.5% of the union-support mass at tau=0, 94.9% at tau=-4M, and effectively all of it by tau=-8M. Direct-only reconstruction passes tau=0 for 96.7% of pairs on direct rays' own support, but only 18.3% on the registered union support. Thus the gain combines new historical-time reach and new source-plane coverage rather than penalizing direct imaging for failing on its own current support.

## Numerical checks

The q8/q12 source-response gate passes for every fresh truth and every fitted movie. Worst clean discrepancy is 2.17e-6 relative and 0.02745 whitened; worst fitted discrepancy is 3.10e-6 relative and 0.02840 whitened. Independent ODE versus separated-quadrature errors are 5.21e-13M in source radius, 5.58e-11 rad in phase, 8.44e-10M in delay, and 8.66e-15 in redshift.

The execution used 26,688 separated-quadrature calls and 64 independent ODE calls. Paper I used zero units and remains unchanged.

## Correction record

The prior assistant package was empty and is not evidence. The first real run preserved the complete physical/operator cache and then stopped, before any source or inverse outcome, on a tensor-projection output-index error. The correction and source hash were committed before resume. The resumed run reused the preserved physical cache and did not alter sources, seeds, thresholds, regularization grid, or endpoints.
