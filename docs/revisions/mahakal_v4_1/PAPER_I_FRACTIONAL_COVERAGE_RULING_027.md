# PAPER_I_FRACTIONAL_COVERAGE_RULING_027

Repository: internalerror404/photon-ring-tomography  
Branch: research/mahakal_v4_1  
Reviewed commit: 37cbb76ad8e00b8461e67dff68ddf5becd949e7e  
Disposition: FRACTIONAL_COVERAGE_AUTHORIZED_HULL_AND_TRANSFER_ACCURACY_SEPARATE

Author-directed project ruling, not a journal referee decision. This review read
the connected source, Q0/Q1 records, Q2 freeze and return, Q3 budget assessment,
and completion record. It ran 22 independent synthetic geometry/arithmetic
checks. It did not rerun archived HDF5 maps, Kerr operators, or the 552-test suite.

## 1. Decisions and scope

Accept the R3A_QUADRATURE_NOT_YET_QUALIFIED return, the distinction between correct
construction and unqualified physical quadrature, and the decision not to spend
the ray allowance on the projected binary-raster refinement. Q0/Q1 provide the
required new measure and unit-accounting foundation; no duplicate replay of those
steps is required by this ruling. C13 remains the governing defect, not a new C14.

AUTHORIZE a versioned cut-cell/fractional-coverage representation on the fixed
D026 detector. This is a new numerical representation of the same continuum
measurement and validity domain, not a new physical source, noise model, or
acquisition. Its geometry is qualified separately from its transfer-field
integration. Fractional coverage is not presumed to pass and the old failures
remain literal failures.

REQUIRE hull-geometry error at most 2.5e-4 relative to EACH order's band area,
and a hull-induced whitened detector-response change at most 2.5e-4 for every
applicable declared field/time. Require two consecutive late comparisons and an
independently shifted boundary sampling. These are new component budgets within,
not replacements for, the existing overall 1e-3 response/mask/area requirement.

Start with geometry-only operations and hull refinement. Additional transfer-ray
queries are conditional, charged against the existing unspent allowance, and are
not needed merely to clip polygons. Stop for review before R3B. No target spectrum,
new estimator, source enrichment, detector retuning or submission freeze is
allowed. Deliver all records and protocols directly to GitHub.

## 2. Findings accepted and wording qualified

The Q0 record reports 63 maps with both axes audited and 16 matching nominal and
realized INTERIOR weights. The clipped-node measure also changes boundary weights,
even in a map whose interior spacing agrees. Thus 16/63 is not a claim that those
16 full archived measures are correct at every endpoint. Preserve the separate
interior-pitch and domain-edge components, including order 0's -1.20% core total
from clipping and the reported 57.8% order-2 valid area in boundary-adjacent cells.

The Q2 freeze and completion record support an executed, fixed-detector comparison
with a common absolute clock, signed offsets, and 17 of 18 aggregate checks failing.
The nineteen true completion conditions describe a properly completed assessment,
not a passed quadrature result. The reported 552 passing tests are not promoted
here to independently rerun tests.

The binary mask is a plausible important source of slow convergence, but the
available two successive error ratios do not isolate it as the sole cause. They
also do not establish a mathematical lower bound on every possible adaptive
scheme. Q3_BUDGET_ASSESSMENT extrapolates a rate from two pairs and multiplies an
estimated boundary count by a predicted refinement factor. Preserve that useful
planning estimate, including the 11.652x figure, with the alias
MODEL_BASED_BINARY_RASTER_COST_PROJECTION. Withdraw 'provably cannot qualify' and
'universal lower bound'. No wasteful run is needed to justify the prudent stop.

Fractional geometry may reduce binary-raster error. It does not guarantee a
particular convergence order for redshift, source coordinates, delay, validity,
or their combined detector response. Measure those contributions separately.

## 3. The fractional object is a clipped region, not just one scalar weight

Let C_p be a corrected nodal-dual integration cell, D_d a fixed detector pixel,
B_n the lensing-band region and V_n the source-emission validity region. Write
Omega_n = B_n intersect V_n within the declared integration domain/aperture.
For a piecewise-constant brightness approximation f_np on the active fragment,

    S_np = C_np intersect Omega_n,
    a_np = |S_np|,
    O_n[d,p] = |D_d intersect C_np intersect Omega_n|,
    y_d = sum_n sum_p O_n[d,p] f_np.

The cell-wide fraction phi_np = a_np / |C_np| is a useful diagnostic. In general,
O_n[d,p] is NOT phi_np times the unclipped detector/cell overlap. A band may occupy
only the left part of a cell while that cell straddles two detector pixels.
Clipping must occur at the intersection that is actually integrated. Retain all
fragments, holes and components; do not replace a band by its filled outer hull.

Use a pinned robust polygon/triangle clipping implementation, with declared
floating-point predicates, area accounting and topology tests. 'Exact overlap'
means exact for the declared polygonal representation up to the checked arithmetic
error; it does not mean the polygons are the exact geodesic boundaries. Do not
silently snap boundaries, repair invalid polygons, drop slivers, or discard small
positive areas to obtain a pass. Zero-area rows are omitted explicitly. A sliver
policy, if necessary, must be fixed beforehand and charged to the error budget.

The existing P6 remains required: subdivide the SAME active set with the SAME field
and fixed detector. Recomputing a different hull or a different interpolated field
is not that representation-invariance test. Add a counterexample proving that
phi times uncut overlap can be wrong despite correct total flux.

## 4. A band hull is not the complete source-validity mask

The repository's geometry/raymap.py::validity applies band membership AND finite
source radius/azimuth/coordinate time AND r_plus < source_r <= 50. The paper's
continuum equation (2), pages 6-7, includes this validity factor; changing its
numerical representation must not silently delete part of that model.

AART's public documentation describes separate inner/outer band hulls and a
separate ray-tracing stage supplying source coordinates and emission time. It
identifies hull_0i with the apparent horizon and hull_0e with the domain edges.
Use the pinned generator's exact conventions; do not replace hull_0i by an assumed
critical-curve shadow or use today's upstream code instead of the pinned backend.

Clip geometric band boundaries first, but keep the emission-domain boundary and
solver validity distinct. If r=50 or another declared source-validity boundary
cuts a fragment, resolve it using the same physical predicate, bounded quadrature,
or targeted root/ray checks. A failed numerical evaluation is not proof of zero
emission. Absence of valid nodes on the edge of a sampled box also does not certify
that unsampled exterior emission is absent: use the verified continuous/polygonal
band enclosure and source-domain checks. D026 itself remains a fixed aperture.

A cell center can be outside B_n even when |C_p intersect B_n| > 0. The new geometry
must inspect all candidate cut cells, not only cells whose old center was valid.
Their area may be known without new rays; their g^3, source position, and delay may
not be. Do not copy NaNs/zeros from masked nodes, extrapolate across the horizon,
or multiply a new positive fraction by a value that was never computed there.

Missing-transfer cases have three explicit outcomes: reuse valid same-branch
samples with a tested local error bound; perform targeted interior evaluations
under the remaining allowance; or report MISSING_TRANSFER_SUPPORT. Geometry-only
progress is legitimate even when transfer integration remains blocked.

## 5. Hull accuracy: measure the thin band, not the large enclosing shape

For hull-resolution level N let P_out,N and P_in,N be the actual generated
polygons, and B_N = (P_out,N minus P_in,N) intersect D026. For a comparison of
levels N and M define

    eta_band = |B_N symmetric_difference B_M| / |B_N union B_M|,
    eta_boundaries = (|(P_out,N symmetric_difference P_out,M) intersect D026|
                    + |(P_in,N symmetric_difference P_in,M) intersect D026|)
                    / |B_N union B_M|.

Require BOTH <= 2.5e-4, per order, for the last TWO successive resolution pairs.
The second metric prevents inner/outer errors from compensating. Normalize by the
band union, not outer-hull area or the 2500 M^2 aperture. Handle empty domains
explicitly rather than silently dividing by a floor. Also retain per-detector-cell
symmetric-difference areas, minimum band widths, topology and distance diagnostics.
Distance alone is not an accuracy gate without a validated conversion to area.

Use nominal npointsS levels [60,120,240,480,960,1920], stopping at the first level
with two qualifying pairs and the independent check. The actual number of unique
vertices/curve solves may differ because of reflection or generator conventions;
report both. No assertion is made that 60, 240 or 1920 must be sufficient.

Each refinement must solve the pinned defining boundary equations at genuinely
new parameter locations. Inserting midpoints on an existing polygon edge is not
refining the physical hull. Keep branches, endpoints, symmetries and point ordering
explicit. Require no self intersections, correct inner/outer nesting where the
model requires it, and unchanged topology under refinement. Do not silently apply
convexification to a nonconvex sampled curve.

At the candidate accepted resolution, perform a half-step shift in the generator's
native parameter with required endpoints preserved. It must satisfy the same area
and response tests; agreement of nested levels alone can hide common aliasing.
Also rerun the boundary solves with a tenfold tighter root tolerance, where
supported, and require the geometry/response discrepancy <= 2.5e-5 (one tenth of
the hull budget). Use root brackets or independently checked residual/position
bounds where available. These numerical checks establish resolution qualification,
not a theorem about the exact continuum curve.

A regular unit-circle N-gon gives a useful warning, not a Kerr prediction:
its relative area error is 1 - sin(2*pi/N)/(2*pi/N), about 1.827e-3 at N=60.
A clipping routine can integrate that polygon to machine precision while missing
the true domain by much more than the hull budget. The accompanying tests verify
this and a thin-band example where small outer-shape error becomes large band error.

## 6. Keep boundary and transfer integration errors separate

For the fixed whitened detector map W and a bounded, held-fixed test field f,
compare y(B_N,f) with y(B_M,f), changing only the hull. Require this relative
response change <= 2.5e-4 for each applicable field and observer time. Use the
previous common denominator convention and report genuinely zero responses
explicitly. In addition, retain the stacked-time comparison from Q2.

A useful conservative check on a fixed field is

    |delta y_d| <= M_d |D_d intersect (Omega_N symmetric_difference Omega_M)|,
    ||W delta y|| <= sqrt(sum_d (M_d delta_area_d)^2/(sigma^2 |D_d|)).

M_d must bound the field on the uncertainty region, not merely be the largest
sample seen there. A bound for a specified piecewise interpolant is valid for that
interpolant; it is not a bound for the unknown physical field without further
validation. Missing/unbounded transfer support blocks that particular bound.
Screen-polynomial moments may be integrated directly on clipped polygons without
any ray call. Transfer fields require the separate validation below.

Then hold a qualified hull fixed and refine the transfer/validity representation.
Allocate 5e-4 to response changes from field quadrature and emission-boundary
resolution, and at most 1e-6 to aggregate numerical integration error; exact small
fixtures keep 1e-12. Use these as component diagnostics with a common normalization.
The total end-to-end response/mask/area checks remain <= 1e-3 for every order and
field, over two late pairs and an independent shifted/holdout check. No component
sum or pass is a substitute for checking the total. Jointly vary hull and transfer
levels at the final checks so independently small changes cannot conceal coupling.

If every ray profile is clipped to the very same polygon, identical masks follow
by construction. That is a geometry-consistency check, NOT evidence that the hull
is physically converged. The independent hull hierarchy must carry that evidence.
Conversely, refining the hull at fixed sparse transfer samples does not certify
transfer accuracy. Do not label the whole Q2 failure 'binary rasterization only'
unless controlled, same-field ablations actually establish that scope.

## 7. Noise and units after fractional clipping

For the NEW active-fragment inherited-noise benchmark use parent integrated flux
z_np=a_np f_np, C_parent=sigma^2 diag(a_np), L=O diag(1/a_np). Then
C_inherited=sigma^2 O diag(1/a_np) O.T, summing independent order contributions.
Remove zero-area fragments before inversion; use stable factorizations for tiny
fragments rather than undocumented flooring. This defines a new matched parent
experiment and is not automatically the archived R2 stochastic experiment.

The SINGLE_SKY_DETECTOR_NOISE variance remains sigma^2 |D_d| once per FULL detector
cell per observer time. Do not shrink its noise to the emitting fraction or add
noise per order. Keep brightness and integrated-flux input conventions explicit
and test them on unequal, fractional areas. All data-processing comparisons must
refer to the same chosen parent experiment; no ordering is presumed for different
noise experiments.

## 8. The adopted-measure R2 interval remains uncertified

Accept preservation of the narrow uniform-core bound from review 026. Do not
promote the wider [0.987978457,1.008048257] TOTAL-AREA-ratio calculation to a proof
that the clipped/subsampled R2 operator still has exactly two operational modes.
Its hypothetical intervals miss rho=1, but totals are not pointwise row bounds.

sampling.py assigns each selected ray its stratum area divided by the take count,
then applies normalization and possible common-count trimming. The relevant ratios
are q_new,i/q_old,i AFTER all those operations on identical retained indices.
Those ratios can differ from each order's total-area ratio. An optional weights-only
readback may export their min/max and verify the fixed-index assumption without
forming a target operator. Only an actual bound on every effective row licenses
reuse of the profiled-Fisher inequality. Otherwise keep the broader calculation
explicitly hypothetical and R2 accepted solely under its frozen legacy measure.
No new R2 spectrum is required or authorized here.

## 9. Bounded execution and return

Run H0 (archive hull provenance and clipping canaries), H1 (geometry-only hull
hierarchy), then H2 (controlled transferred-field validation). Store new geometry,
coverage operators, validity records and reports separately; never rewrite raw
maps or previous freezes. Fix D026, sigma=0.011341986814407566, the eight times,
and absolute coordinate-time origin -978.6055123201214 M. Signed delays remain
signed. The accepted 72 target indices and full-L224 nuisance model stay unchanged.

The old 250000 new screen/order-ray-evaluation allowance is still unspent according
to the return. Carry it forward, do not add another allowance. Use at most two
predeclared batches of at most 125000, counting invalid calls and retries. Boundary
curve generation is now separately authorized up to 30000 boundary-point solves,
including failed and repeated solves. Charge any full source-transfer ray calls
inside a boundary routine to the ray cap as well. Keep the cumulative new work
within 8 GiB peak memory and two hours on existing resources, with no paid purchase.
Stop on a cap, unsupported pinned interface, unresolved topology, or insufficient
accuracy; do not spend to a target-informed detector setting.

Commit the protocol, implementation, curve-sampling rule, actual dependency hashes,
field/validity integration rule and budget before the new outcome-bearing phase.
Boundary outcomes may choose how far along the frozen hierarchy to proceed; they
may not change its criteria. If missing transfer data need queries, freeze their
selection rule from geometry/declared-field residuals before that batch. Record
actual execution commits and per-phase counters. A boundary-only success must not
produce a full quadrature-ready token.

Return FRACTIONAL_HULL_GEOMETRY_QUALIFIED_TRANSFER_PENDING if only geometry passes;
R3A_FRACTIONAL_QUADRATURE_READY_FOR_REVIEW if all component and total checks pass;
or R3A_FRACTIONAL_QUADRATURE_NOT_YET_QUALIFIED with the exact blocker. Stop before
any R3B target information comparison. This stage determines whether fractional
coverage solves the identified numerical problem, not whether it preserves two modes.

## Evidence and independent checks

At reviewed commit: Q0 C13_MAP_MEASURE_INVENTORY.json; Q1 measure/unit records;
Q2 R3A_QC_026_RETURN.md, Q3_BUDGET_ASSESSMENT.json and R3A_QC_026_COMPLETION.json;
R3A_QC_026_INPUT_FREEZE.json; src/phrt/geometry/{raymap,sampling}.py;
src/phrt/revision_v4_1/acquisition.py; scripts/revision_v4_1/q2_fixed_detector_convergence.py.
The user-supplied Mahakal manuscript equation (2), pages 6-7, supplies the continuum
validity-weighted measurement; it is not the latest correction record.

External primary background checked: AART's official README separates band hulls
from transferred ray fields (https://github.com/iAART/aart), and AMReX's embedded-
boundary documentation distinguishes regular, cut and covered cells
(https://amrex-codes.github.io/amrex/docs_html/EB_Chapter.html). These support the
methodological context, not the numerical tolerances, which are project decisions.

review027/checks_027.py and CHECKS_027.json record 22 locally executed synthetic
checks using NumPy and Shapely. This does not require a change to the pinned physics
backend or prescribe Shapely as the production implementation. No real hull
convergence, transfer run, or repository-suite pass is claimed by these fixtures.
