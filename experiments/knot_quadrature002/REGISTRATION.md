# KNOT_QUADRATURE_002 - prospective same-pixel numerical integration experiment

Status: source and 17 model-free tests complete; zero new physical calls and no new numerical outcomes at this registration. User authorized continuing Paper-II experiments after CACHE_REBUILD_001. Parent completion: f3da13716bb82dd4cd4dff8efa515f119d39d749. Paper I remains protected at 084fb45fedae99f203393dbc1e9cdda9ab250c2d on research/mahakal_v4_1; zero Paper-I units or writes.

## Question and lineage
CACHE_REBUILD_001 remains COMPLETE_NUMERICAL_GATE_FAIL: 142 of 1785 raw basis column-arm checks fail, while its 89 analytic fields pass. A postplanned read-only audit of the supplied complete cache verified all 37 artifact-manifest entries and all original ledger/array relationships before design. The sampled q12 chart shows monotone radius versus z and monotone delay versus z within each order, but small lambda-direction reversals in order 1. This motivates root isolation with explicit sampled extrema rather than blindly assuming lambda monotonicity.

Hypothesis: source temporal-hat breakpoints crossing a pixel prevent uniform tensor quadrature from integrating the basis sufficiently accurately. The experiment changes quadrature only, never the physical detector pixels, source basis, movie support, noise calibration, source amplitude or pass thresholds. It does not test movie recovery or establish the cause of the original, still-unrecovered R2 failure.

## Frozen input and model
Use the byte-authenticated CACHE_REBUILD_001 physical/operator arrays b8a9774cc2f8d0dc5e157da7655c75e002497ef9f8c3a2d56fc7c96d1f4fe6b9 and support 9426ca216e18560d59812555b2cd0c851932554a7ab5f47a4552bdefaebe0294. All other input bytes are listed in SOURCE_FREEZE.json. Replay all 1785 original basis metrics to tolerance 1e-12 and exactly reproduce 142 failures before new quadrature.

Use the identical readable Kerr solver 2e8150cb114ba5e89d86da46a265642c077ed9319f697c72af4041cc018e219d with n=64 internal separated quadrature. Reuse the accepted 64-ray ODE cross-check as prior finite evidence; no new ODE validation is claimed. Every new solver call is still required to return finite, positive-redshift, positive-area emission in r in [6,13].

Acquisition: a=0.5, inclination 50 degrees, observer radius 100M; lambda in [0.5,3], z in [0.3,0.7], 8x8 pixels, orders 0/1, 13 observer times 0:2:24. Four original 832x595 source operators and source Gram are the baseline. Source convention tau=tobs-delay+100M; baseline-one integrated intensity uses area*g^3.

Retain the original CACHE001 q12 pixel areas, sigma300, and support for all comparisons. No renormalization of individual basis columns or rays. Retain the existing five radial cubic splines, m<=3 Fourier factors, and 17 temporal hats centered uniformly on [-32,28].

## Methods, fixed before outcomes
U1: original unsplit q8/q12 operators, replay only.
U2: UNIFORM2 control: divide each physical chart pixel into 2x2 equal rectangles, use independent local tensor q8 and q12. This adds quadrature points, not observations.
K: KNOT primary: coefficient-independent partition at the union of all delay levels tobs+100-temporal_center across all 13 observations, plus radius=9.5 (the internal radial knot). Use local q8/q12, not an interpolated q12 from q8. The name q8/q12 here denotes local composite rules and must not be confused with the old unsplit rule.

For each pixel, first find intersections of those level sets with each constant-z pixel edge. Isolate roots on 17 fixed lambda samples per edge; sampled sign reversals trigger bounded scalar extremum finding, after which sign-bracketed roots use Brent with coordinate tolerance 2e-13 and residual tolerance 2e-9. Split the lambda integral at all these intersections. At each outer Gauss node, evaluate five z samples and require the registered signed monotonicity, find bracketed inner level crossings, and split the z integral at them. Merge coordinate roots separated by at most 2e-12; preserve pixel endpoints.

This is deterministic numerical root isolation, NOT an interval-arithmetic proof that every possible contour or extremum was found. Nonmonotonicity, root failures, invalid rays, or budget exhaustion stop the run as incomplete. Finite q8/q12 agreement cannot certify the continuum, even if the panel passes.

All coefficients and source histories are absent from partition construction. U2 and K need not consume equal work: report ray counts and nodes, and do not claim equal-cost superiority or isolate the temporal contribution from the added radial partition.

## Numerical panels and endpoints
For U2 and K test all 595 unit-coefficient basis fields in direct, order1, and stacked arms (1785 checks per method), with BOTH relative L2 <=5e-4 and noise-whitened L2 <=0.1. Zero reference norms use the same fixed denominator floor 1e-15. No column pruning, response-dependent scaling or weak-column exemption.

Analytic panel: retain all original 89 fields and add 89 fresh coefficient-independent probes using seed 2026091204 and the exact same parameter formulas; no source admission. There are 534 field-arm checks per method. All compact historical-feature direct responses must remain <=1e-10 whitened. These are numerical probes, not held-out inference test histories.

Require integrated pixel areas to agree with the frozen q12 pixel areas within 1e-8 relatively, for every pixel/order/rule/method. Check saved operator arrays by exact readback. Record the spectral norm of Sigma^-1(A8-A12)H^-1/2 as a diagnostic over the finite source-norm unit ball, not a continuum certificate or new pass rule.

KNOT_QUADRATURE_002_PASS requires complete schedule, unchanged source/input hashes, exact baseline replay, all area/readback checks, and every K basis/analytic/direct-null check passing. The U2 control may fail without blocking K's gate, but every U2 failure remains reported. If numerical panels complete and K fails, return KNOT_QUADRATURE_002_COMPLETE_GATE_FAIL. Any timeout, missing case or solver failure returns KNOT_QUADRATURE_002_INCOMPLETE, never a subset pass.

## Resources and records
CPU float64, one BLAS thread, 8GiB address-space cap, 1200-second whole-run wall limit, at most 600000 new separated ray calls. Exact-coordinate memoization is allowed and counted separately. Every physical cache miss has BEGIN and END/ERROR records in a hash-linked, streamed gzip ledger. Internal roots of each geodesic solver belong to that ray call; numerical contour searches call the same ledger-wrapped solver, with no unlogged physics. No retries or budget extensions within this registration.

Freeze and deposit actual source/configuration and input hashes before outcomes. Save all method ray tuples, weights, pixel membership, nodes, outer partitions, operators, analytic source parameters, all numerical checks, environment, complete ledger, completion/failure and final hashes. Full binary artifacts may be delivered as an exact ZIP if the connector cannot deposit them; state the GitHub-versus-package boundary honestly.

This stage performs zero movie fits, zero posterior runs, no source-label inference and no validation selection. It does not repair original R2 provenance. The 12M/95% total-movie, 95% identification, 90% pair-both/differential and actual fitted q8/q12 scientific gates remain for a separately registered inference successor, alongside calibrated uncertainty and fresh sources/noise.
