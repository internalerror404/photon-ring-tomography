# Kerr transfer-chart pilot003 — prospective experiment registration

Base: b24ed2a4bad9e30bc08d31a82a52652dbb242ec8. Separate Paper-II experiment, no Paper-I or canonical map changes. The existing 854-unit allowance is not used.

## Fixed problem
M=1, a=0.5, inclination=50 degrees, finite observer r=100, static observer normalization. Thin equatorial emitting annulus r in [6,20], prograde circular timelike emitters. Trace backward to the THIRD equatorial crossing (order2), on an exterior scattering branch. Use lambda=L/E in [0.5,2] and z=log(r_turn-r_critical(lambda)) in [-1.5,-1.3]. Beta<0 initially decreases mu=cos(theta); phase/time signs are explicit. This is a declared Bardeen impact-parameter integration plane, not an exact finite-distance telescope angular calibration. Retain the alpha/beta chart Jacobian.

A geometry-only scout preceded this registration. It chose an emitting outgoing patch with sampled source radii 6.59–16.90 M, before any surrogate-error or detector-error outcomes. A solver-development defect was found: a single global polar quadrature under-resolved the azimuthal integrand at low lambda. It was replaced with fixed pi/4 phase panels BEFORE this registration. Old code, scout values and three development comparisons are retained; they are not fresh test data.

## References and gates
Primary B: separated angular-phase and turning-point-regularized radial quadratures, then scalar root inversion; 64 points per integral/panel, 96-point refinement. Independent A: compactified-radius/polar second-order ODE with equator event counting, no radial roots or analytical crossing time. DOP853 rtol=2e-11, atol=2e-12. They share constants, metric and final redshift formula, not the ray-integration algorithm.

128 withheld points, RNG seed53003; first48 additionally use independent ODE. Fixed tolerances: source radius2e-6 M, source phase2e-7 rad, travel time2e-6 M, redshift2e-7. Domain/branch must agree; failures retained and block claimed qualification.

## Fixed comparison
81 physical calibration tuples on a9x9 chart grid. Strong classical tensor cubics at9,17,33 nodes per axis. Data neural map: two32-wide tanh hidden layers, three scaled outputs (r_source,phi,T). Physics-informed candidate: same hidden widths, one bounded source-radius output, supervised on same81 values plus fixed17x17 collocations enforcing the separated radial integral equation. Its phase/time follow from the fixed quadratures, not independent neural fits. Physics weight1, residual scale0.001, supervised radius scale10. This additional equation information is disclosed.

Three seeds11,22,33; float64 CPU one thread; Adam2500 steps at0.003 followed by LBFGS200 iterations. No fit-family/penalty/tolerance sweep. Freeze each learned map into a33x33 tensor cubic with saved coefficients. Deployed spline queries do no physical quadrature. Compare frozen vs unfrozen output separately.

## Detector
One fixed4x4 array of chart rectangles mapped to curved impact-plane pixels. All methods use the same area Jacobian and noise sigma0.01 with variance sigma^2 times full pixel area. Tensor Gauss orders6,10,16; independently integrate ODE values at order3 per pixel for a matched-rule reference check. Eight observer times0..20.64 diagnostic columns: g^3 times1, cos/sin(2pi(t-T)/20), cos/sin(2pi(t-T)/40), (r-10)/10, cos(phi), sin(phi). Maximum PER-CHANNEL relative whitened detector-vector error is primary, target5e-4. Zero reference norm gives undefined relative error, not a pass. No averaging away failed channels.

## Bounds, budget and scope
Numerical comparison on this patch, not a global interval/continuum certificate. Test monotonic radial-residual bounds at withheld points; do not promote sampled residual maxima into unsampled bounds. Test area Jacobian, source linearity, clock invariance, source four-velocity normalization and domain/extrapolation refusal. No source inversion, NeRF movie, Kiran deployment, other Kerr geometries or additional charts.

Caps:10000 separated endpoint solves,220 independent ODE rays,1600 equation-precomputation points,6 neural fits,1800seconds compute envelope,4GiB memory. Count repeated differentiable training quadratures separately; they are not free or independent truth samples. Save attempts, numerical payloads, source/config hashes, all seed outcomes and failures. Stop rather than silently extending the scope.
