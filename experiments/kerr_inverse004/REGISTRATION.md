# Mahakal II Kerr inverse004 — prospective development registration

Base commit 9fd5478ac39fe25fcea025176bd735fe9fc4dc36, a separate Paper-II branch. No Paper-I, old maps or previous result files modified. Zero new rays, physical path quadratures or hull/critical roots. Paper-I 854 units untouched.

Protocol SHA256: 2ee39cec63779f532c1a0c11ffa382e33a7a5b1e60b6913d4c2605222d2d156c.
Input manifest SHA256: 1c33d58816befbbdfd4bc4aa2791104fff074ddafde6b3b870acc5fb67093442.
Both local files were written before new source outcomes or fitting. The protocol content and executed source will be included in the final package.

## Fixed observation
Use authenticated chart003 reference tuples and frozen classical cubics at 9/17/33 nodes per axis. The prior chart is Kerr spin0.5, inclination50deg, observer100M, third equatorial crossing, emitting annulus6..20M. Same 4x4 impact-plane pixels, eight observer times0..20M, same full-pixel-area covariance. Define source tbar=t_observer-T+145. This is one order2 patch, not a direct-vs-resolved comparison or a whole-image movie experiment. Jacobian interpolation uses the saved33x33 chart setup and is checked against the independent saved reference weights; no geometry root is recomputed.

## Targeted linear inverse
j=1+sum c_k b_k+alpha1 e1+alpha2 e2. Seven nuisance columns:1,R,R^2,cos(psi),sin(psi),cos(2psi),sin(2psi); R=(r-11)/5; psi=phi-Omega(r)tbar; Omega=1/(r^1.5+0.5). Unit-peak event templates are Gaussian: e1 centered(r,tbar)=(8.5,1), widths(1.5,3); e2 centered(13.5,13), widths(1.7,3). Shapes/locations are known only for this targeted test; unknown amplitudes. No continuum-source Gram claim.

Reference uses cached16x16 physical values per pixel, checked against cached10x10. Compare reference and9/17/33 cubics; fixed quadrature16. Noise density0.01 primary and0.001 high-SNR stress. Thirty-two coefficient truths (RNG400410), 64 noise draws each (RNG400411); background normal std0.08, event amplitudes uniform[0,0.7], first16 truths exactly zero-event. Full least-squares/pseudoinverse with1e-12 tolerance; independently verify nuisance-profiled result. Record singular information, bias, errors in standard-error units and nominal95% joint-target ellipse coverage. Separate source assumptions, repeated noise draws and physics accuracy.

## Neural source comparison
Two scenarios, same background coefficients drawn with seed1729 and std0.08: no event or amplitudes(0.5,0.35). Physical reference16x16 generates observations. Noise density0.001. Data-only and robust advection PINN, training quadratures3x3 versus8x8, three seeds11/22/33:24 fits total. Two tanh hidden layers width32, inputs scaled radius/time and sin/cos of phi harmonics1..3, one contrast output around fixed baseline1. Same initial weights and observations in paired quadrature/method comparisons; same1000 Adam steps(lr0.002)+LBFGS100 strong-Wolfe. Equal steps, not equal walltime. No hyperparameter search.

PINN adds0.03 times mean robust penalty of z=(j_t+Omega*j_phi)/0.03; penalty z^2 if|z|<=1, otherwise2|z|-1. Fixed256 collocations over r[6.5,17],phi[-7.56,-7.07],tbar[-7,26]. This prior is correct for the rotating background but not the source events. It is not extra photon information.

Evaluate contrast error on128 cached independent ray endpoints crossed with37 observer times: a chart-pullback metric, not global source history. Re-render each frozen model at3/8/16/24 quadrature; inspect response and gradient changes. Numerical acceptance: relative response difference<=5e-4 AND whitened norm<=0.1; still numerical refinement, not interval proof. Negative outputs and failed checks remain in records.

## Limits and delivery
New neural fits<=24, CPUfloat64 one thread,4GiB,1200seconds training envelope. All code and input hashes freeze before outcomes; save per-fit models/arrays. New source truth generation and cached rendering are authorized here, not production ray calls. This is a registered local development experiment, not a sealed journal benchmark. All failures, exceptions and post-planned diagnostics retained. The result is allowed to show weak event identifiability, inaccurate neural reconstruction, or no benefit of finer training quadrature.
