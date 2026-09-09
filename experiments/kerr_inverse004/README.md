# Mahakal II — local Kerr inverse004

Completed controlled inverse experiment on the previously checked order-2 Kerr patch. This is not a direct-vs-resolved comparison, global renderer or historical movie. The complete report, authenticated binary inputs, checkpoints and raw arrays are in the accompanying experiment package. This directory contains the executable code, registration, input identities and compact executed results.

## What the data determine under a declared source model

Two known-shape radial–temporal emission-pulse amplitudes remain measurable after profiling seven rotating-background coefficients. The pulse templates are azimuthally uniform Gaussians in radius/time, not two resolved moving hotspots. At noise density0.01 the target singular values are4.9947/4.1651 and amplitude standard errors0.2024/0.2383. At0.001 the errors are0.02024/0.02383. The81-tuple classical spline's worst bias is0.00769 joint-standard-error units on32 tested sources at the higher-information setting. These are conditional template-amplitude statements, not neural-image uncertainties.

Across32 prescribed coefficient vectors and64 Gaussian draws each, nominal95% joint target ellipses cover94.043% (Monte Carlo binomial interval92.929–95.029%). The exact no-event subset has5.078% false positives. Four forward maps and two noise levels reuse the paired source/noise draws;16384 estimates are not that many independent astrophysical histories.

The source amplitudes are not supplied to the inverse. Shapes, locations and widths are known in this targeted test. At the primary density, pulses of amplitude(0.5,0.35) have projected signal norm2.982 and modeled joint detection power76.5% at5% false-positive probability. Unit-template sensitivity does not ensure every smaller event is detected.

## Flexible source reconstruction

Twenty-four continuous neural inverse fits compare data-only/robust PINN and3x3/8x8 training integration. The neural models are NOT given event templates. The8x8 event-source contrast errors are16.07% data-only and15.42% PINN (three-seed medians). The PINN has a4.02% median paired improvement on the pulse case, not a universal gain; the background case has essentially no median paired advantage at8x8.

All fitted-field numerical response checks pass on this local patch, including evaluations on actual cached physical tuples rather than only the spline. Worst3x3 training-vs-reference error is5.264e-5 relatively and0.020815 whitened; worst8x8 is1.211e-7 and4.579e-5. Both meet the fixed5e-4 relative/0.1 whitened criteria. The true-reference10-vs16-node comparison is within2.90e-12 relatively for every fitted field. Finer integration improves numerics but does not resolve the remaining15–23% source error. This does not retroactively qualify the different Schwarzschild pilot's failed training quadrature.

The source-error metric is contrast j-1 on128 cached source points crossed with37 observation times. It is a chart-induced source/time distribution, not a norm over the whole source volume. These are per-instance inverse fits, not an amortized neural operator or a deployment of NeRF/Kiran. Three seeds are stochastic repeats of two fixed scenarios, not a broad family benchmark.

## Mathematical separation

For whitened target E=(I-P_N)B_T, cov_alpha=(E^T E)^-1. With a surrogate forward model, its target bias obeys

    bias_alpha = (E^T E)^-1 E^T C^-1/2 (mu_true - mu_surrogate),
    ||cov_alpha^-1/2 bias_alpha|| <= ||C^-1/2 (mu_true-mu_surrogate)||.

The source/data adjoint, nuisance-projection/full-least-squares identity, bias identity and bound were checked. A good forward map does not make an arbitrary field identifiable; a source prior supplies assumptions, not additional photon information. The bound is for the specified finite source/target model and covariance, not unknown-domain continuum error.

## Reproduce

Use a NEW directory containing source/, protocol.json, INPUT_MANIFEST.json, SOURCE_FREEZE.json and the supplied inputs/. The complete package and source-plus-input package contain the binary arrays. Compact GitHub source does not pretend those inputs are already present and never launches geodesics to replace them.

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python source/run_all.py
```

Dependencies: Python3.13, NumPy2.3.5, SciPy1.17, PyTorch2.10 CPU, pandas; matplotlib only for figures. Optimization uses float64 and one thread. Recorded neural optimization145.8seconds; walltime depends on hardware. run_all refuses existing linear results. Post-fit verification runs from summarize.py if absent and reads completed checkpoints rather than retraining.

Main registration9098fa5f5d5e and pre-outcome source freezeed32d24d3e42 are on this isolated Paper-II branch. All six executed Python source files and protocol/input identities were checked against uploaded Git blobs. Post-fit physical-response, power and source-positivity supplements are labeled post-planned; no model or threshold changed. Streaming launch was unavailable before training started; the actual first process completed24fits without restart. A plot permission failure was repaired without fitting again.

No new rays, path integrals, hull/critical roots or Paper-I modifications. The854-unit allowance remains untouched. No R3B, production-suite replay, paid-resource purchase or submission action occurred.
