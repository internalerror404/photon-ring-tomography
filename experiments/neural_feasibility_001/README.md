# Mahakal neural-physics feasibility: executed 8 September 2026

This is a separate, manufactured-problem development study. It is NOT a repaired Kerr renderer, production Kiran benchmark, full FNO implementation, or real historical movie reconstruction. No production ray budget was consumed. The paper and its accepted numerical results are unchanged.

## Executed scope

42 neural fits in CPU float64 across seeds 11,22,33: 27 inverse neural fields, 9 scalar delay surrogates, 6 reduced spectral neural operators. Two supplemental classical inverse models give 18 fits. Direct fits are reused for two exactly observationally indistinguishable source histories, not counted twice as training. The full result arrays/checkpoints and a 2,442-word analysis are in the accompanying ChatGPT experiment package. This repository directory provides the complete executable source and its recorded results summary.

Run in a fresh directory with Python, NumPy, SciPy, PyTorch and pandas:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python run_all.py
```

The code produces every per-seed metric, training trace, model state, source prediction and resolution check. No internet or external dataset is required. The local protocol preceded neural training; it was not externally preregistered. The analytical one-parameter forward comparator was added before forward training. Classical inverse baselines were supplementary crosschecks added after the neural screen, with their regularization chosen by training-data GCV, not test-truth error. No statistical population guarantee is claimed from three seeds.

## Main executed findings (median over three seeds)

Old-source contrast error with all three synthetic delay channels:

| Model | Assumed dynamics correct | Compact old transient violates assumed dynamics |
|---|---:|---:|
| Data-only neural field |20.15%|21.26%|
| Soft advection PINN |3.64%|60.70%|
| Hard-characteristic neural field |6.61%|67.04%|
| Flexible Fourier/spline ridge |14.02%|12.77%|
| Known-flow Fourier control |1.44%|66.77%|

The source prior helps substantially when correct, but erases a genuine transient when wrong. The metric scores j-1 on old times, not a dominant constant background. Direct data for the two truths are identical; all-order data have whitened separation 34.8207. Thus direct-only old reconstruction from the flow law is conditional extrapolation, not additional measured information.

Manufactured forward delay tau=-log(x)+0.08(x-1), x in [exp(-8),1], with exact ODE x*tau'=-1+0.08*x and tau(1)=0. Actual integrated cos(3*tau) detector errors:

| Model | Relative detector error |
|---|---:|
| Raw-coordinate supervised neural network |24.4757%|
| Raw-coordinate PINN |0.8191%|
| Log-coordinate cubic spline |0.10344%|
| Known-log residual PINN |0.003197%|
| Known-log plus one fitted linear residual coefficient |6.12e-14%|

Factor the justified analytical structure before learning a residual. The analytical control is best on this deliberately simple residual; the result is not proof that a neural method beats a good physical solver.

A four-Fourier-mode operator trained at five times and constrained at 128 physics times reduces held-out field error from 0.8371% to 0.02581% on 96 new coefficient fields evaluated on 127x37 points. It fails a sixth-mode input with 100% relative error because the encoder excludes that mode. Continuous evaluation and denser-grid generalization are not freedom from source-model assumptions.

A geometry-supported four-corner lookup into a 64x32 latent grid matches dense evaluation to 4.44e-16. Dropping two contributing corners gives 21.22% relative error. This is a bounded-access proxy inspired by Kiran, not measured speedup or deployment of its learned memory. Local-feature neural fields already exist; sparse interpolation alone is not a novelty claim.

## Mathematical constraints on the next architecture

A data-plus-physics objective has curvature A^T C^-1 A + lambda L^T L. Only the first term is information from measurements. A hard dynamics law changes the admitted source class. Two histories with identical observations cannot be separated by a deterministic estimator without extra assumptions.

A compensating common delay shift and source-time translation preserves both observations and autonomous advection. In the executed example it gives 19.57% fixed-coordinate source-contrast error with 5.55e-17 maximum data error. This is a clock/source-phase ambiguity, demonstrating why a jointly learned source and renderer need independent calibration.

A pointwise sensitivity mask is not an identifiable-subspace projector: A=(1,1)/sqrt(2) senses both locations but cannot see their difference. Use noise/source-normalized response modes and separate data-supported structure, dynamics-conditioned completion and unresolved uncertainty. A neural map cannot raise the rank of the physical measurement Jacobian; it can restrict the parameterized source class.

Keep the forward renderer source-linear under the fixed optically thin model. Learn smooth, calibrated residuals or fixed-source-independent kernels rather than an arbitrary nonlinear source-to-image surrogate. Preserve emitting-domain boundaries, valid-event masks, pixel integration and covariance; a NeRF decoder does not repair those by itself.

## Numerical checking and limits

Analytical truth pixel integrals at 48 vs 96 nodes agree to max 1.53e-11 absolute. Every fitted inverse model was re-rendered at 8/24/48 nodes: maximum relative 8-vs-48 discrepancy 6.46e-7; 24-vs-48 1.67e-16. No actual Kerr maps, 691-test production suite, true GR quadratures, or frozen Mahakal truth banks were run. No current-operator accuracy or scientific novelty is claimed.

Primary references for borrowed ideas:
- PINO: https://arxiv.org/html/2111.03794v4
- Function-space neural operators: https://jmlr.org/papers/v24/21-1524.html
- Existing physics-informed black-hole neural fields: https://arxiv.org/html/2602.08029v2
- Existing multiresolution latent-grid neural fields: https://research.nvidia.com/publication/2022-07_instant-neural-graphics-primitives-multiresolution-hash-encoding

A promising next design is a separately calibrated, singularity-aware forward surrogate plus a flexible neural emissivity field, soft dynamics with explicit transient innovations, and physics-support-aware local access. These experiments test the ingredients and limitations; they do not validate the complete combined system.
