# Mahakal II Movie014 — background-posterior analysis-by-synthesis

**Return:** `MOVIE014_BACKGROUND_POSTERIOR_FAIL`

Movie014 retained a 16-member local Gaussian beam of backgrounds compatible with the direct image and inferred the historical feature family from a fixed 4,096-template analytic library. It used fresh validation/test populations, exact direct-null historical features, and zero new Kerr calls.

## Primary result at SNR0=300

| Method | Identification | Pair-both | Median error | Span95 | Differential pass |
|---|---:|---:|---:|---:|---:|
| Single background MAP | 85.94% | 71.88% | 0.79968 | 0M | 3.91% |
| Background posterior beam | 85.94% | 71.88% | 0.79968 | 0M | 3.91% |

The posterior beam therefore fails the identification, reliable-span, differential-movie, and improvement-over-point-MAP gates. It passes authentication, exact direct nullness, source positivity/population fill, positive median improvement in all four families, and every q8/q12 clean/fitted numerical gate.

## Diagnosis

The posterior almost always collapses to one joint hypothesis: the median effective hypothesis count at SNR300 is approximately 1.0. More importantly, the local beam around the direct MAP does not cover the true first-indirect background forecast. The median minimum forecast error across the beam is approximately **446 whitened units**, with a long tail approaching 2,000.

This rules out the idea that a few local Gaussian perturbations around one coefficient-space MAP are enough. The direct-background uncertainty relevant to order 1 is nonlinear and/or multimodal. The next experiment must search across distinct analytic background families and nonlinear basins, then marginalize those hypotheses jointly with family-blind historical dynamics.

## Numerical scope

- clean q8/q12 worst whitened discrepancy at SNR300: 0.005513 — pass;
- fitted posterior q8/q12 worst whitened discrepancy at SNR300: 0.003054 — pass;
- new physical calls: 0;
- Paper-I units: 0;
- one Kerr chart, ideal order labels, finite sigma-point beam and finite analytic feature library.
