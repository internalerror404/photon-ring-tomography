# Mahakal II Movie013 — controlled operator tournament

**Return:** `MOVIE013_OPERATOR_TOURNAMENT_COMPLETE_NO_WINNER`

Four operator/inverse formulations were compared on the exact same frozen Movie007 source histories, q12 observations, q8 inverse rows, noise draws, validation budget, and movie metrics. No non-equivalent variant beat the original ray–pixel operator plus its 595-dimensional structured prior.

## In-basis result at SNR0=300

| Variant | Labelled median error | Span95 | Span90 |
|---|---:|---:|---:|
| Ray–pixel 595 baseline | **0.04664** | **28M** | **28M** |
| Orthogonal retarded-time DCT | **0.04664** | **28M** | **28M** |
| Nested m<=8 source class, 1445D | 0.17920 | 0M | 0M |
| Historical-innovation block ridge | 0.20329 | 0M | 0M |

The DCT is an exact equivalence control: transformed Gram matrices and right-hand sides agree at approximately 1e-15, and fitted coefficients and movies are identical.

## Exact archived off-basis result

| Variant | Narrow-hotspot error | Shearing-spiral error | Any span90 |
|---|---:|---:|---:|
| Ray–pixel 595 baseline | **0.92867** | **0.75208** | No |
| Orthogonal retarded-time DCT | **0.92867** | **0.75208** | No |
| Nested m<=8 source class | 1.30193 | 0.99754 | No |
| Historical-innovation block ridge | 2.75368 | 1.95485 | No |

Relative to baseline, nested source-normalized ridge is 40.2% worse on narrow hotspots and 32.6% worse on shearing spirals. Historical-innovation block ridge is 196.5% and 159.9% worse.

The exact-sample q8/q12 closeout finds that clean off-basis truths pass at both arms. Baseline, DCT, and nested fitted fields pass. The historical-innovation labelled fit reaches whitened discrepancy 0.12512 against the declared 0.1 limit and is mechanically disqualified in addition to losing the recovery comparison.

## Interpretation

- An invertible/orthogonal row re-expression does not create information.
- More source capacity does not imply more recoverable history. The nested labelled operator has rank 1367 and effective dimension about 239 at SNR300, yet its movie error is nearly four times baseline and its 28M span disappears.
- A separate old/background quadratic penalty is not sufficient; it amplifies weak old directions.
- The cached Kerr ray–pixel transfer is not identified as the present bottleneck on these samples. The coupling between the physical map and source prior/regularizer is the next target.
- This does not prove the present acquisition is globally optimal. Delay-resolved or visibility-domain observations would change the data and require separate experiments.

All input, baseline-replay, DCT-equivalence, exact-containment, and winner-readback checks pass. No new Kerr/geodesic/physical call or Paper-I unit was used.
