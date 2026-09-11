# Mahakal II movie007-support — prospective registration

**Lineage:** successor to the negative full-annulus Movie006 development result. Branch base `ce780381f2ac5d7c9ef5f49a43a228c0e17dd226`; Movie006 physical/operator inputs are authenticated by byte hash before use.  
**Question:** can the direct-plus-first-indirect Kerr acquisition recover a reliable *source-plane movie on the region actually constrained by those rays*, for longer than direct imaging alone?  
**Status at registration:** support-kernel choices were informed by the disclosed Movie006 exploratory readback, but no fresh validation/test source, observation, regularization choice, reconstruction, or endpoint has been generated. This is a registered development successor, not an externally sealed main.

No new ray, geodesic integral, hull/critical root, or Paper-I unit is authorized. Paper I remains untouched with 854 convention-B units.

## 1. Fixed physical input

Reuse Movie006's locally verified Kerr chart and source-linear operators:

- `a=0.5`, inclination `50°`, static observer at `100M`;
- ideal order labels `n=0` and `n=1` on the common chart `lambda∈[0.5,3.0]`, `z∈[0.3,0.7]`;
- 8×8 detector pixels per order; 13 observer times `0,2,…,24M`;
- q8 inverse operator and q12 clean/reference operator;
- one direct-reference noise density, shared across orders, at `SNR0=300`; `SNR0=100` is a secondary stress;
- finite 595-dimensional source basis: 5 radial cubic B-splines × 7 real Fourier factors through m=3 × 17 linear temporal splines.

Required input hashes:

- `PHYSICAL_ARRAYS.npz`: `33fe02d73e1d08e5c7629cb6427b95ac1a29e1aba5821e1dd2b0cd3316bdcfc9`
- `OPERATORS.npz`: `0b77918b88d2c379bf75aad4dfd88e542ee168d325fa16ee5eb52ca6678833a7`
- Movie006 `experiment.py`: `ac30f20458ca48edd843f81fd24050653305cf85a84092ede4f7404243f4c88b`
- Movie006 `resume_inverse.py`: `303ee0a066b71f604761da92026ca6b5899012298411ac6be72a907f137fa8f7`

Movie006's physical gate must be true. This successor does not turn its local frozen-chart validation into a whole-image or continuum claim.

## 2. Geometry-defined measurement-support movie metric

The metric is fixed from q12 ray landing coordinates and transfer/noise geometry **before fresh source generation**. It is the same for direct-only and direct-plus-order-1 reconstructions.

For movie times `tau_k=0,-2,…,-28M`, each q12 ray/observer-time contribution is assigned to the nearest cell of the fixed 32×64 `(r,phi)` evaluation grid with raw weight

`pixel_weight × g^6 × exp[-(tau_ray-tau_k)^2/(2×1.5^2)]`.

The resulting radial–azimuthal histogram is smoothed by a fixed Gaussian filter with standard deviations 2 radial grid cells and 2 periodic azimuthal grid cells (approximately 0.45M and 0.20 rad). Radial boundaries use nearest-value extension; azimuth is periodic. Each frame's nonzero weights are normalized to sum one. The support metric is therefore a declared discrete pullback/coverage metric, not proper source volume and not a posterior uncertainty map.

For each frame, with contrast fields `x=j_true−1` and `y=j_hat−1`:

- weighted truth activity is `sqrt(sum W_k x^2)`;
- active weighted error is `sqrt(sum W_k (y−x)^2)/sqrt(sum W_k x^2)`;
- weighted structural correlation uses weighted means and covariance;
- inactive frames require weighted predicted contrast RMS ≤0.05.

A frame passes when active truth RMS ≥0.03, weighted relative error ≤0.35, and weighted correlation ≥0.75; inactive-frame semantics and thresholds are otherwise identical to Movie006. The full-annulus Movie006 metric is retained as a negative control and is not replaced retroactively.

## 3. Fresh source populations

Use the same three broad in-basis analytic families and projection procedure as Movie006:

1. single broad orbiting hotspot;
2. two broad orbiting hotspots;
3. flare birth–motion–decay with a weak persistent component.

New RNG seeds:

- validation candidate generation `70061`;
- in-class test candidate generation `70062`;
- off-basis stress generation `70063`;
- validation noise `70064`;
- test noise `70065`;
- bootstrap `70066`.

Accept sources using truth geometry only, never reconstruction performance. A projected candidate enters the measurement-support bank when the union-support truth is active at `tau=0`, at `tau=-28M`, and on at least 10 of 15 frames. Generate the first 12 accepted validation and 20 accepted test histories per family, with a maximum of 500 candidates per family; failure to fill a family blocks the experiment. Record every rejected candidate and reason.

Off-basis stress uses 10 fresh narrow-hotspot and 10 shearing-spiral histories without projection. It is secondary and cannot make the primary gate pass.

Every test history receives four paired Gaussian draws at each SNR. Direct-only and labelled arms use identical direct data and direct-noise realizations.

## 4. Inverse and selection

Primary estimator: the same source-normalized ridge/Tikhonov family used in Movie006, with fixed penalty and candidate grid `10^k`, `k=-6,…,3`. Select one candidate separately for direct and labelled arms using the median validation mean active **support-weighted** frame error at SNR300. Freeze both choices before test evaluation.

TSVD using the same fixed cutoff grid is retained as a secondary diagnostic if it can be evaluated from the same eigensystem without changing the primary ridge schedule. No source-family-specific or test-dependent tuning.

All reconstruction is in the 595-dimensional movie basis. No neural network, NeRF, Kiran router, or learned source prior is added in this stage. A later amortized model is authorized only after the classical support-movie feasibility gate passes.

## 5. Endpoints and success gate

Primary endpoint: the largest backward interval `[−T,0]`, on the registered 2M grid, for which at least 95% of in-class test history/draw pairs satisfy every frame under the measurement-support metric. Report 90% reliability as secondary. Use a 2,000-resample paired history-cluster bootstrap; all four draws of a sampled history move together.

Also report:

- direct versus labelled per-time error/correlation quantiles;
- per-family paired integrated support-error reduction;
- number of active frames and effective support size;
- q8/q12 clean-response and fitted-response numerical checks;
- full-annulus metric as a retained control;
- one predeclared movie visualization: flare family index 10, draw 1, SNR300, ridge.

A positive development result requires all of:

1. authenticated input/physical gate passes;
2. labelled 95%-reliable support-movie span is nonzero;
3. labelled span exceeds direct by at least 6M;
4. at least two of three in-class families have positive median paired reduction in integrated support-weighted error;
5. q8/q12 response differences remain ≤5×10⁻⁴ relatively and ≤0.1 whitened for every fresh source;
6. the result is called a measurement-supported/partial source-plane movie, not a full-annulus or observational movie.

Thresholds and support kernels are not changed after test outcomes. A negative result is retained. A successful result authorizes a separately registered multi-chart mosaic aimed at full-annulus movie recovery; it does not itself establish that stronger claim.

## 6. Resource limits

- New physical calls: exactly zero.
- Basis dimension: 595, unchanged.
- Fresh in-class test histories: 60; off-basis: 20; validation: 36.
- Four test draws and two validation draws.
- CPU float64, one BLAS thread, ≤8GiB working memory.
- Save support weights, source candidate ledger, coefficients/truth frames, regularization scores, all reconstruction/frame metrics, bootstraps, and visualization arrays.
