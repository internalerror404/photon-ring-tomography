# CACHE_REBUILD_001 - prospective Paper-II-only physical cache rebuild

Date: 2026-09-12. Status at freeze: source written and model-free tests passed; no physical calls or numerical-probe outcomes generated.

## Authorization and lineage
The user explicitly authorized a separately registered Paper-II-only cache rebuild, including new ray integrations. This changes the prior cache-reuse-only restriction for THIS bounded rebuild. It does not authorize Paper-I units or alter any previous result. Parent governance commit: bd1fadb4ef5642fbb8574aa1df00850b866b46d1. Protected Paper-I ref: research/mahakal_v4_1 at 084fb45fedae99f203393dbc1e9cdda9ab250c2d.

The original R2 source 93d990c11e39a5cb7bd127967bf65bff07fe28d3c118630077e88d4457c26c2a and old execution records remain unrecovered. This is a NEW implementation/cache identity, not bytewise R2 reproduction, and no old hash is replaced. Existing R3 and later experiment identities are not reused.

## Exact source provenance
source/kerr_chart003_original.py is the unmodified readable repository Kerr solver: experiments/kerr_chart003/source/kerr.py at e93c659f16ac1d8723968c13dea9f91e8bea66ef, Git blob e0537f82d9cc71dde9ce46b44be010d31bb52712, SHA256 2e8150cb114ba5e89d86da46a265642c077ed9319f697c72af4041cc018e219d, 7145 bytes. It is NOT the inaccessible later Movie007 source identity.

rebuild.py supplies new isolated accounting, pixel quadrature, source-linear operators and support construction. It replaces the imported module's log_attempt callback with a new Paper-II-only bounded hash-chain ledger; the ray equations are unchanged. Every transfer begins and ends in that ledger. Its wrapper additionally requires r in [6,13], narrower than the ancestor module's status interval [6,20]. No physical source response is used to select or discard rays.

numerical_fields.py copies six analytic-source functions verbatim from authenticated available R2 V4 source 39cfbcf12c1918eb86a1ef842714fa900bb3204ed0078e692d243740ce4cadff, then adds a fixed numerical-probe schedule. The 17 pre-execution tests use artificial arrays only, not Kerr integrations or the registered numerical fields. Actual files and this registration are locally hash-frozen in provenance/SOURCE_FREEZE.json before any physical outcome.

## Fixed acquisition
M=1, a=0.5, inclination 50 degrees, static observer radius 100M; scalar optically thin equatorial source with prograde circular redshift law. Chart lambda in [0.5,3.0], z=log(r_turn-r_critical) in [0.3,0.7]. Orders 0 and 1, 8x8 chart pixels each. Tensor Gauss-Legendre q8 and q12 within each pixel; neither is interpolated from the other. Internal separated-ray Gauss rule n=64. Source time tau=tobs-delay+100M, tobs=0,2,...,24M. Raw integrated pixel flux is sum(chart quadrature weight * screen Jacobian * g^3 * source value).

Pixel noise standard deviation is sigma_Omega * sqrt(q12 full pixel area), shared across q8/q12 and orders. sigma_Omega is fixed by q12 direct constant-source whitened RMS=300; SNR100 uses three times that density. No noisy scientific observations are generated here.

## Basis and support: explicit new implementation choices
5 clamped cubic radial B-splines, knots [6,6,6,6,9.5,13,13,13,13]; Fourier factors [1,cos(phi),sin(phi),...,cos(3phi),sin(3phi)]; 17 compact linear temporal hats centered uniformly on [-32,28]. Coefficient order radial,angular,temporal; dimension 595. Source Gram uses trapezoidal r dr and dt on 32 radial and 31 temporal points and periodic equal azimuth weights on 64 points. These explicit details are NEW source definitions, not a claim of exact missing Movie007 code recovery. No reconstruction penalty or validation-selected regularization record is invented.

Support uses q12 ray-area weights times g^6 and a 1.5M temporal Gaussian over all 13 observations. Nearest-cell assignment on r=linspace(6,13,32), phi=linspace(-pi,pi,64,endpoint=False); ties use numpy.rint, periodic azimuth, clipped radial indices. Apply Gaussian smoothing sigma=(2,2), mode=(nearest,wrap), truncate=4, and normalize each of tau=0,-2,...,-28M. Full-annulus control uses normalized trapezoidal r dr with equal periodic phi weights. These are discrete geometry-defined weights, not uncertainty bands or full-source coverage certificates.

## Physical schedule and budgets
First: seed 2026091201 draws 32 uniform chart points, reused across orders. At each point/order compute separated n64, separated n128, and independent compactified ODE (rtol=2e-11, atol=2e-12, DOP853, max_step=.015). Total 128 separated checks and 64 ODE checks. Stop before full cache on any failed ray check.

Then: 8192 q8 and 18432 q12 ray transfers; total 26624 cache transfers. Expected whole-run counts: 26752 separated transfers and 64 ODE transfers. Hard caps 28000 separated and 80 ODE; 900 seconds wall time, 8GiB address space, one BLAS thread, CPU float64. Each transfer includes its own critical/turning and crossing-root operations; there is no separate unlogged scouting or physical call. Zero Paper-I units. Cache stages save immutable q/order arrays. No retry or extension is authorized after a physical failure.

## Qualification schedule
1. Every scheduled ray must emit in [6,13] with finite positive area/redshift/delay and matching crossing leg in the independent check. ODE versus n64, and n128 versus n64, component tolerances [r,wrapped_phi,delay,g] = [2e-6,2e-7,2e-6,2e-7]. These compare formulations sharing the same invariants/redshift conventions; they do not independently validate those common physical assumptions.
2. Build all four 832x595 operators, the source Gram and support. Verify per-ray versus matrix contraction <=1e-12 using seed 2026091203, Cholesky residual <=1e-12, nonnegative normalized support to 1e-12, and exact saved-array readback.
3. Seed 2026091202 produces 89 fixed numerical probes: constant field, 8 backgrounds for each of three families, and 8 twin pairs for each of four historical families. No admission or rejection. These are numerical qualification fields, not validation/test populations for a future inference experiment. Audit direct, order1 and stacked responses separately. Historical-feature direct responses must be <=1e-10 whitened.
4. Also audit EVERY one of 595 raw unit-coefficient basis columns in each of those three arms. No response-dependent scaling or pruning.
5. For both analytic probes and basis columns retain the original q8/q12 thresholds: relative norm <=5e-4 AND whitened L2 norm <=0.1. Report each failed field/column. A complete run failing any mandatory gate returns CACHE_REBUILD_001_COMPLETE_NUMERICAL_GATE_FAIL, not PASS. This all-column test is a new conservative qualification panel, not a reinterpretation of Movie007's tested-field gate. Passing this finite panel is not a uniform continuum/operator error bound for every coefficient combination.

## Scope and completion
This run ends after cache construction and numerical qualification. It does not reconstruct movies, train models, select regularization, infer a posterior, or measure 12M/95%, 95% identification or 90% differential gates. Those inherited scientific gates remain unchanged for a separately source-frozen successor. In particular, no REGULARIZATION_SELECTION.json is fabricated to satisfy an old loader.

Save real source, registration and hash freeze, environment, complete BEGIN/END ledger including failures, q8/q12 arrays, four operators, support and Gram, all 64 cross-checks, 267 analytic and 1785 basis arm checks, exact input/output hashes, and completion/failure. Incomplete runs have no passing subset endpoint. Public compact records must explicitly distinguish deposited source/records from binaries delivered in the full package.
