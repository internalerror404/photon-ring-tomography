# Mahakal II pilot 002 — prospective development registration

Parent experiment: 292cb6c29d899bc2549cc27680efd878ecf802e4. Paper I remains at 518c255e25b404da70960e96b914c4167938f691.

The locally written protocol.json, SHA256 a183a05790a8f6e23ab7ed46fe31c8231187f8581386e80327fda74805ed6664, is frozen before model training. This is a registered development pilot, not a sealed publication experiment. Complete code, settings, arrays, unsuccessful outcomes and deviations will accompany the return. Five reference-engineering preflight points were evaluated before this registration and are not holdouts.

## A. Physical forward primitive

Schwarzschild M=1, a=0. A null ray starts at r=100, reaches a simple closest approach rt=3+d and returns to r=100. log(d) ranges from -5 to log(2). Compute total angular sweep and coordinate time independently by factored radial quadrature (r=rt+s^2) and by DOP853 integration of u''+u=3u^2 with dt/dpsi=1/[b*u^2*(1-2u)] and event stopping. The time-agreement gate is 2e-6 M.

Twenty-four common log(d)-spaced labels train raw-impact, log-coordinate, and analytical-leading-log residual neural surrogates. Cubic log-coordinate and residual splines are classical controls. The justified leading term is -6 sqrt(3) log(d/2), not an assumption that the residual vanishes. Seeds 101,202,303; two32-unit tanh layers; 1600 Adam steps and up to100 LBFGS iterations. No hyperparameter or phase-loss sweep.

Test on96 independent point coordinates and a fixed12-pixel impact-parameter strip, using exact db/dlog(d) weights and full pixel-width whitening. Constant and cos/sin temporal fields with periods20,40 use24/48-point detector quadrature. This is actual Schwarzschild propagation but NOT an order-labelled disk renderer, a=0.5 Kerr geometry, source-validity/redshift calibration, or a Paper I rerun.

## B. Transient-aware inverse

Use the same manufactured distributed-delay acquisition as pilot001, not the physical scattering primitive in A. Every method has the same periodic-feature source MLP. Compare data-only, quadratic advection PINN, and an innovation-aware Huber PINN. With z=(j_t+0.8j_phi)/0.05, minimizing (z-s)^2+2|s| over s gives the threshold1 Huber penalty and s=soft_threshold(z,1). This permits nonzero source innovations rather than imposing source-free evolution.

Each physics method chooses one global lambda from [0.03,0.1,0.3,1.0] using independent noisy validation observations for two validation histories (matched and single-transient), NEVER source-truth error. Freeze those choices before test fits. Main histories use two new random backgrounds, each with matched, single-old-event and double-old-event variants. The double-event family is absent from validation. Three noise/initialization seeds101,202,303. All-order fits for all six histories; direct fits reused across the exactly observationally identical old-history variants. A Fourier/time-spline ridge baseline is predefined, with training-data GCV only.

Training:16 pixels/order,5 times,8-node pixel quadrature; truth48 nodes; sigma density0.01;256 physics collocation points;700 Adam steps and60 LBFGS iterations. Primary error is relative older-source contrast j-1 error on[-0.95,-0.38]; retain heldout observation error, event contribution, data fit, positivity and exact same-data ambiguity diagnostics. Six histories and three seeds do not establish astrophysical population confidence.

## Preservation and stopping

CPU only; no paid resources. Separate Paper II allowance of at most2500 geodesic-primitive evaluations,110 neural fits and2700 seconds execution. None of the854 Paper I units is used or relabelled. Failed physical reference validation blocks surrogate training. No threshold changes after holdout outcomes. The full NeRF/PINO/Kiran system and actual Kerr historical imaging are NOT claimed validated by these component tests.
