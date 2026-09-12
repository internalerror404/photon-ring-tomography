# Mahakal II Movie015 — multi-family parametric background beam

**Return:** `MOVIE015_PARAMETRIC_BACKGROUND_BEAM_FAIL`

Movie015 replaced Movie014's local Gaussian perturbations around one coefficient-space MAP with a global library of 3,072 backgrounds spanning the registered single-hotspot, double-hotspot, and flare/drift families. Both background and historical family were inferred from the data.

## Primary result at SNR0=300

| Method | Identification | Pair-both | Median error | Span95 | Span90 | Differential pass |
|---|---:|---:|---:|---:|---:|---:|
| Direct only | 50.00% | 0.00% | 0.84345 | 0M | 0M | 0.00% |
| Single parametric MAP | 98.24% | 96.48% | 0.29536 | 2M | 6M | 18.75% |
| Parametric beam | 98.24% | 96.48% | 0.29536 | 2M | 6M | 18.75% |

The experiment passes authentication, exact direct nullness, the registered 80% background-coverage improvement, causal identification, all-family improvement, and every q8/q12 gate. It fails the 8M reliable-span gate, the 50% differential-movie gate, and the requirement that posterior averaging beat the single parametric MAP.

## What improved

The median minimum order-1 background forecast error fell from Movie014's 446.09 whitened units to **32.98**, a 92.6% reduction. Background-family accuracy was **75.39%**. Every one of 128 paired cases improved in all four historical families, with median error reductions of approximately 61–67%.

## Remaining bottleneck

The posterior still collapses to essentially one joint hypothesis. A postplanned diagnostic supplied the exact shared background while retaining the same 4,096-element family-blind historical library. It achieved 98.44% identification but only 6M 95%-reliable span, median error 0.2433, and 23.05% differential-movie pass.

Therefore background search is necessary but no longer sufficient. The finite historical template grid is now the main approximation. The next experiment should continuously refine the historical dynamics and infer its family without supplying the answer.

## Numerical scope

- clean q8/q12 worst whitened discrepancy: 0.005513 — pass;
- fitted q8/q12 worst whitened discrepancy: 0.005263 — pass;
- new physical calls: 0;
- Paper-I units: 0.
