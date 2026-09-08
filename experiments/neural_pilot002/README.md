# Mahakal II pilot002 — executed physical calibration and transient tests

This is a registered development pilot, not a full historical-image reconstruction. It contains two SEPARATE experiments: an actual Schwarzschild scattering-delay primitive, and manufactured distributed-delay source inversion. The inverse experiment does not use the scattering map; no integrated Kerr/NeRF/PINO/Kiran system is claimed validated.

## What ran

99 CPU-float64 neural fits:9 forward approximations,18 inverse validation fits and72 inverse test fits. Also24 classical inverse fits and1,090 physical primitive evaluations, including ten engineering preflight calls. Paper I's branch, canonical data and854-unit remainder are unchanged. No paid resources or production-suite run.

The registration was committed before model training; the inverse penalty weights were committed before test fits. Full source was written before its corresponding execution but not committed as a complete preexecution code freeze. This is not a sealed external benchmark. All poor candidates are retained. The actual source blobs were checked against local executed files.

## Physical forward calibration

Schwarzschild M=1,a=0; a ray travels from r=100 through a simple exterior turning point rt=3+d and back to r=100, log(d) in[-5,log2]. The factored radial integral and a DOP853 solution of u''+u=3u^2, dt/dpsi=1/[b*u^2*(1-2u)] agree on96 heldout points: max time discrepancy1.1944e-8M, angular discrepancy1.9826e-9 and first-integral residual7.4329e-14. The registered time gate2e-6M passes at that finite tested scope.

Every approximation receives24 identical log(d)-spaced labels. The detector diagnostic integrates five temporal fields over12 impact-parameter intervals with the exact db/dlog(d) Jacobian and full pixel-width whitening. Independent24/48-node response references agree to max1.013e-10 relatively. This is NOT a source-crossing/redshift/emission-domain or rotating-Kerr qualification.

Maximum-channel relative detector errors, neural medians over three seeds:

| approximation | error |
|---|---:|
| raw-coordinate MLP |24.105%|
| log-coordinate MLP |0.5021%|
| analytical-log residual MLP |0.7948%|
| cubic spline in log(d) |0.001417%|

A residual cubic spline gives the same answer because the subtracted leading logarithm is linear in log(d). The known leading term is -6 sqrt(3)log(d/2), derived from the coalescing-root integral. The neural methods did not beat the classical surrogate. No runtime speedup is claimed. The forward neural models use physics through representation, not a trained geodesic-residual PINN loss.

## Innovation-aware source inverse

The new model replaces a squared source-free-advection residual by a Huber penalty. For z=(j_t+0.8j_phi)/0.05,

    min_s (z-s)^2+2|s|

has s=soft_threshold(z,1), yielding z^2 for |z|<=1 and2|z|-1 otherwise. This allows penalized source innovations without declaring every departure unphysical. It does not add measurement information.

Quadratic and innovation penalties each selected lambda0.03 from the same registered[0.03,0.1,0.3,1.0] grid using independent noisy validation observations on two histories, not reconstruction-truth error. The optimum at the grid edge is a limitation, not a reason to extend the grid after the test.

Six new histories comprise two random backgrounds, each matched or modified by single/double old events. The double-event family is absent from validation. Three seeds vary noise and initialization; these are not eighteen independent astrophysical histories. All neural fits have the same architecture and700 Adam/60 L-BFGS budget. Classical Fourier/time-spline ridge uses training-data GCV only.

Older-source contrast error, medians with all delayed channels:

| model | matched dynamics | one old event | two old events |
|---|---:|---:|---:|
| data-only neural field |12.74%|49.57%|46.47%|
| quadratic PINN |8.37%|51.28%|48.37%|
| innovation-aware PINN |9.58%|48.69%|46.40%|
| Fourier/time-spline ridge |15.16%|21.37%|61.42%|

The innovation-aware PINN beats quadratic in5/6 double-event runs, with4.28% median paired relative improvement; it wins3/6 single-event runs and loses all matched-flow pairs. It is essentially tied with data-only on the median double-event criterion. It is NOT promoted as a general winner. Significant errors remain; optimization, capacity and inverse conditioning were not causally separated.

Matched/transient histories have exactly identical direct data. Their all-order whitened separations range31.64–45.21. Direct reconstruction can supply model-conditioned completion, not distinguish such same-data histories without additional assumptions. Every learned inverse was re-rendered at8 and48 nodes: worst relative discrepancy2.987e-7. Truth48/96 quadratures agree to max5.697e-11 absolute. Nine pilot verification checks pass, not the production691-test suite.

## Reproduce

Copy source/ and requirements.txt into a fresh directory and run:

    OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python source/run002.py

The launcher refuses existing results and reproduces the setup, training, classical controls, arrays, checkpoints and verification. It was assembled after the individual executions, not itself rerun end-to-end in this session. The complete ChatGPT experiment package includes the original checkpoints, field arrays, reference arrays, full logs, protocol and a detailed2,347-word report. Tables committed here are actual derived run metrics, not proposed targets.

## Scientific direction

Use physically appropriate coordinates and independently checked reference calculations before adding a network. Next, extend reference calibration to an actual emitting source-crossing geometry. Do not infer that a successful scattering-delay spline calibrates all Kerr transfer quantities. Keep flexible source representations and strong classical baselines; the Huber innovation is an option with a measured tradeoff, not a completed historical camera.

Primary context: Gralla & Lupsasca https://arxiv.org/html/1910.12881; PINO https://arxiv.org/html/2111.03794v4; existing physics-informed black-hole neural fields https://arxiv.org/html/2602.08029v2. No novelty claim follows from simply combining those ingredients.
