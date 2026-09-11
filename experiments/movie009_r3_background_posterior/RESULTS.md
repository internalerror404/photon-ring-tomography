# Mahakal II Movie009-R3 — background-posterior result

**Return:** `MOVIE009_R3_BACKGROUND_POSTERIOR_FAIL`

The deterministic 65-hypothesis background beam was evaluated on the exact examined Movie009-R2 population. It used the validation-selected rank-96 latent ridge, the frozen Kerr rows, the same four noise draws, and no new physical calculations.

| Method | Identity | Pair-both | Median error | Span95 | Span90 | Differential pass |
|---|---:|---:|---:|---:|---:|---:|
| R2 point estimate / beam K=1 | 99.61% | 99.22% | 0.23390 | 6M | 8M | 29.69% |
| Posterior-beam MAP, K=9 | 100% | 100% | **0.21113** | 6M | 10M | 23.44% |
| Posterior-beam MAP, K=65 | 100% | 100% | 0.21433 | 6M | 10M | 23.05% |
| Posterior mean, K=65 | 100% | 100% | 0.21426 | 6M | 10M | 23.05% |
| True background + same latent representation | 100% | 100% | 0.16348 | 10M | 14M | 29.69% |

Every family, including held-out radial plume, retains a positive median paired improvement. The beam improves median error and the 90%-reliable endpoint, but it does not improve the 95%-reliable span or all-active differential movie fidelity.

The posterior score collapses to one hypothesis in the median case: effective size 1.0 and maximum posterior weight 1.0. Expanding from K=9 to K=65 adds no meaningful recovery. This means the fixed Gaussian one-direction-at-a-time beam does not represent the useful nonlinear/background uncertainty set.

More importantly, supplying the true background to the same rank-96 latent-ridge representation still gives only 10M span, 29.69% differential pass, and a q8/q12 fitted-field discrepancy near 1.15 whitened units. Background uncertainty is therefore not the sole remaining obstacle. The latent historical representation/inverse and its numerical stability are binding.

The result does not invalidate the earlier analytic-family oracle, which used the correct feature-family model and achieved substantially stronger recovery. It shows that a rank-96 linear PCA decoder cannot reproduce that oracle merely by improving background handling.

Next experiment: a dynamics-aware continuous historical representation evaluated without a true family label, first as a mechanism panel on the preserved population and then, if successful, on a fresh confirmation population.
