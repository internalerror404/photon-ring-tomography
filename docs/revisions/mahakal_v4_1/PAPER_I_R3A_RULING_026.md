# PAPER_I_R3A_RULING_026

Reviewed repository: internalerror404/photon-ring-tomography  
Branch: research/mahakal_v4_1  
Reviewed commit: 5d56f7e9ef30087fee2eef6ef8c4c6306615adcb  
Disposition: R3A_BLOCK_CONFIRMED_C13_REPAIR_AND_FIXED_DETECTOR_CONVERGENCE_AUTHORIZED

This is an author-directed project review. It is not a journal referee decision.
The review read the connected repository report, implementation, tests and input
record. Fifteen independent arithmetic/finite-volume checks were executed locally;
no raw Kerr maps, physical target operators, or reported 539-test suite were rerun.

## 1. Decisions

Accept the BLOCKED return and the decision to stop before R3B. Accept the overlap
kernel and canaries as evidence for the operations actually tested, not as a
certificate of a continuum-accurate acquisition. Preserve both R3A directories and
all FAIL outcomes. Assign the new issue **C13 / QUADRATURE_GEOMETRY_MISMATCH_026**.
It extends the correction ledger; do not renumber C01-C12 or rewrite their records.

Choose route 3: fix one detector and converge the ray/quadrature representation
into it. A nonuniform common-refinement mesh is permitted internally as an exact
integration device. It is not a replacement detector or three per-order cameras.
The old 1e-12 detector-pitch test remains FAIL_AS_WRITTEN. Its use as a universal
quadrature-invariance gate is retired prospectively, not relaxed into a pass.
R3B and a new submission freeze remain blocked.

## 2. C13: confirmed inconsistency, scoped materiality

scripts/build_raymaps.py::to_raymap stores d['dx']**2, while alpha/beta come from
AART's returned grid. common_sky.py turns sqrt(pixel_area) into a square footprint.
The reported realized spacings differ from nominal dx in seven of nine audited
profile/order combinations. Thus the coordinates and alleged tessellating cells
cannot both describe the same uniform pixel partition. An arbitrary quadrature
weight need not equal neighbor spacing squared, but it must not simultaneously be
claimed as the exact geometric area of a different cell lattice.

Interior square-cell correction factors reported for the reference core profile:

| order | realized/nominal area | row-amplitude factor at fixed sigma |
|---|---:|---:|
| 0 | 1 | 1 |
| 1 | (250/249)^2 = 1.008048257286 | 250/249 = 1.004016064257 |
| 2 | (700/699)^2 = 1.002863276989 | 700/699 = 1.001430615165 |

These are not yet a complete boundary-corrected physical measure. Verify BOTH
axes; delta_alpha squared is not adequate for a rectangular/nonuniform grid.
Determine from raw metadata/generator semantics whether samples are nodes or
cell centers and what domain is being integrated. For endpoint-inclusive nodes
on a declared finite interval, midpoint dual cells clipped at the endpoints have
half-width boundary cells. Giving every endpoint a full cell enlarges the domain.
If full center cells are intended, record their extended domain and compare
profiles on a fixed domain rather than changing it with pitch. Never extrapolate
transfer values outside the sampled region merely to complete a detector cell.

Required new representations separate nominal request pitch, realized x/y nodes,
cell edges, geometric area, validity/domain mask, and any effective quadrature
weight after subsampling. A stratum's aggregate weight is not the geometric
footprint of its retained ray. Raw files remain immutable; corrected geometry and
weights are versioned sidecars or a new record type with old/new hashes.

Disposition:
CONFIRMED_GEOMETRY_WEIGHT_INCONSISTENCY; ARCHIVED_NUMERICS_REPRODUCIBLE_UNDER_LEGACY_MEASURE;
PHYSICAL_REVALIDATION_REQUIRED. No old endpoint, score or manuscript number has
been recomputed or declared changed by this ruling.

The old S0 check against the same nominal dx cannot independently validate the
geometric area. A field-convergence test that excludes area is not an area audit.
Add independent partition, endpoint, beta-axis, rectangular-cell, invalid-mask,
and physical-path tests. Keep the old defect-detection canary separately named;
its pass does not certify corrected weights.

## 3. The detector-pitch criterion mixes different questions

For a single order represented by a nonoverlapping cell field f on a fixed screen,
with integrated detector data and white noise density sigma, define

    y_D = integral_D f,
    Var(y_D) = sigma^2 |D|,
    I_detector = sigma^(-2) sum_D |D| mean_D(f)^2.

Writing P_D for piecewise detector averaging gives

    I_ray - I_detector = sigma^(-2) ||f - P_D f||_L2^2 >= 0.

For multiple test fields the same identity applies to their summed quadratic
norms. This is an elementary conditional-variance/orthogonal-projection identity,
not an empirical Kerr claim. It presupposes a genuine within-order cell partition
and explicit zero/support treatment. Overlapping or gapped nominal rectangles
must not be silently substituted for that premise. The all-order summed sky has
cross terms and is not generally bounded by a sum of separate-order traces under
a different noise experiment.

Exact area overlap can therefore preserve total flux while detector averaging
loses information. A finer detector changes the measurement. For nested detector
partitions information increases toward the continuous piecewise-field value;
it need not plateau at a ray pitch when boundaries are misaligned. Calling the
entire difference an overlap error or an artificial physical loss is unjustified.
It is the exact response of the chosen piecewise reconstruction and detector;
its error relative to the true sky must instead be estimated by ray refinement.

True representation invariance keeps the detector, field, aperture, response and
noise fixed and merely subdivides integration cells carrying the SAME field.
That identity still deserves a machine-precision test. Page 12, equation (16),
of the supplied Mahakal PDF uses sqrt(DeltaOmega); its equal-value split/merge
condition is this representation test, not equality between different detectors.

The new hierarchy is:
A. exact geometry/algebra identities: retain 1e-12 on well-conditioned normalized
fixtures and separate relative/absolute scaling near zero;
B. fixed-detector ray/field approximation: a newly registered 1e-3 relative response
and mask budget, tested over at least two successive refinement pairs;
C. later R3B operational conclusions: only after model-specific error propagation
shows the threshold conclusions are stable. Passing a few construction fields
alone is not an inverse-problem error certificate.

The 1e-3 criterion is a NEW prospective numerical-accuracy budget, not a passed
version of the old 1e-12 test. A relative response-norm error epsilon bounds the
corresponding squared norm by 2 epsilon + epsilon^2 (0.2001% at 1e-3), for that
response. It says nothing universal about poorly conditioned inverse estimates.
Preserve failed levels. No tolerance changes after observing the new campaign.

## 4. Correct the commensurability claim

The supplied spacings are rational and hence mathematically commensurate:

    50/125 = 58017 h, 20/249 = 11650 h, 14/699 = 2905 h,
    h = 2/290085 M = 6.894530913e-6 M.

This does NOT prove actual origins or all boundaries align at that h. Those are
separate conditions. It refutes the stated mathematical impossibility from the
three pitches alone. A uniform screen covering roughly 50 M per side at this
pitch would require about 5.3e13 cells, so a common aligned UNIFORM grid can still
be impractical. Do not try to build it.

Use the union of verified ray-cell edges as a nonuniform integration overlay,
clipped to fixed bounds and optionally refined by detector edges. For three square
grids with 126, 250 and 700 samples per axis, at most 127+251+701 edges per axis
are needed before padding, at most 1078^2 cells. Sparse occupied rectangles and
sweep integration can avoid materializing even that tensor product. This is an
upper bound under the reported square-grid structure, not a verified memory/run
measurement. It resolves the representational alignment issue; it does NOT
resolve ray-sampling error or lensing-band boundaries.

## 5. The area sequence is evidence of unresolved accuracy, not impossibility

Using only the reported nine-table ratios, retaining every original valid sample,
and changing nothing else, the order-0 areas become approximately

    2514.4873 -> 2495.5200 -> 2485.2422 M^2,

rather than 2554.88 -> 2495.52 -> 2465.40. The last spacing-only discrepancy is
0.4136% relative to the fine value, above the NEW 0.1% mask budget. Boundary
clipping has NOT been applied to these numbers. They are arithmetic sensitivity
checks, not a corrected map campaign.

Three moving values neither prove asymptotic nonconvergence nor locate all error
at the lensing-band edge. Profile-dependent outer cell extents, weights, field of
view, valid/invalid rasterization and true boundary approximation are confounded.
At a common fixed domain measure area AND symmetric-difference area between masks.
Equal total areas alone can hide compensating boundary errors. Also compare the
noise-whitened detector RESPONSE vectors, per order and per field, not only a
summed scalar trace that can conceal errors.

## 6. What C13 implies for accepted R2

R2 remains numerically accepted for its explicitly frozen legacy measure. It is
not automatically a revalidated corrected-measure physical result. Direct support
zeros remain zeros under positive row reweighting at fixed rays and source basis.

There is a useful exact bound for the ISOLATED uniform-core area correction.
Let B=[B_o B_n], fix all rays, masks, source metric, target/nuisance spaces and
sigma, and multiply order rows by sqrt(r_n). If r_min I <= D <= r_max I, then

    r_min min_v ||B_o u+B_n v||^2
      <= min_v ||D^(1/2)(B_o u+B_n v)||^2
      <= r_max min_v ||B_o u+B_n v||^2.

Thus r_min F_cond <= F_cond,new <= r_max F_cond. This remains true after profiling;
the nuisance projection itself is allowed to change. Here r_min=1 and
r_max=(250/249)^2. The first three conditional singular-value intervals are

    [1.437164901, 1.442936648],
    [1.345873269, 1.351278382],
    [0.806280438, 0.809518512].

Exactly two still cross rho=1 for that isolated correction. The conditional trace
is bounded by [7.198318098, 7.256252014]. This is an analytical sensitivity bound,
not a numerical rerun or a bound for a new detector, endpoint clipping, changing
valid masks, new rays, or morphology estimators. C13 must not be dismissed as
harmless for those other operations. Record this narrow certificate and do not
repeat the old R2 replay merely to erase a defect label.

## 7. Chosen prospective acquisition and staged authorization

Preserve the 0.02 M detector as the old declared diagnostic. For the NEW fixed-
detector convergence experiment adopt D026: [-25,25] x [-25,25] M, pitch 0.4 M,
125 x 125 cells, eight inherited observer times, actual sigma
0.011341986814407566 held fixed. This aperture uses the original declared order-0
screen limit and the pitch is its core spacing. It is a separately declared ideal
measurement, not a replacement that makes the old detector pass or an EHT claim.
Document cropped flux relative to the earlier padded screen. Verify raw coverage;
outside-grid contributions are zero only where the lensing/source mask certifies
zero, not merely because a file has no samples there.

Use corrected geometric nodal-dual or explicitly justified center-cell measures
on fixed integration domains. Keep the same absolute observer-time reference
across profiles: do not recenter each profile by its own sampled extremum. Any
signed offset under the fixed reference is recorded, never clipped to zero.

First audit existing maps and the three existing profiles at D026. If they fail,
same-geometry numerical refinement is authorized only under the bounded plan in
NEXT_STAGE_026.yaml. This narrowly supersedes review 025's no-new-ray restriction
for deterministic resolution validation, not for new physics or new geometries.
Before evaluations, commit the corrected-measure specification, actual-node and
mask conventions, full dependency freeze, independent target-free refinement
rule and resource bound. No paid resource acquisition is authorized. If the pinned
tracer cannot evaluate the declared points, or the resource cap is insufficient,
return a precise blocker instead of changing the tracer, tolerance or target.

The old 72 target indices, source norm and nuisance model stay fixed. No target
singular values, operational counts or reconstructions are inspected in R3A-QC.
The sole target-related operation allowed is the analytical C13 bound above.
Stop with a construction/error-budget report before any R3B comparison.

## 8. Signal and covariance units must be explicit

Let O_dp=|D_d intersect P_p| and a_p=|P_p|. Then O maps brightness to integrated
flux. For parent INTEGRATED flux z_p=a_p f_p, the postprocessing matrix is
L=O diag(a)^(-1), NOT O. With C_z=sigma^2 diag(a), inherited covariance is
L C_z L.T = sigma^2 O diag(1/a) O.T. Equivalently brightness covariance is
sigma^2 diag(1/a), acted on by O.

The current C5b test places O next to a covariance written in flux units. It is
not evidence of correctly wired physical inherited noise. C7 establishes a
generic contraction identity for an arbitrary linear map, not this unit match.
Add a non-unit, unequal-area fixture showing agreement of brightness and flux
representations. Define raw, integrated and whitened matrices distinctly. The
single-sky detector assigns sigma^2 |D_d| ONCE, after order summation. Never
interchange it with inherited covariance merely to obtain a preferred result.

## 9. Governance and output rules

Keep old maps, freezes, R2 runs, source code and archived tables immutable. New
weight/cell records, corrected constructors and runs use fresh names/directories.
The submitted R3A input record is written by r3a_build.py after its construction
diagnostics; treat it as their snapshot, not proof of prior committed execution.
No target information was inspected, so this is a development/diagnostic record,
not grounds to demand another identical run. The new scientific-accuracy campaign
must have a genuine preexecution commit and complete map/config/test dependencies,
including all profiles it reads. Use fail-closed completion checks that include
test return codes and missing/skipped physical prerequisites; the current build
status only combines two diagnosis flags and is not an adequate final gate.

Return the C13 inventory and dependency overlay, separate interior-weight and
boundary/domain corrections, corrected field/mask convergence, covariance-unit
canaries, cost/provenance and all NOT_RUN items. A constructor can be correct
while quadrature remains unqualified. Report them separately. Do not end with
R3B authorized; R3B needs the next review.

## Sources and checks

Primary sources at reviewed commit: scripts/build_raymaps.py;
src/phrt/revision_v4_1/common_sky.py; scripts/revision_v4_1/r3a_build.py;
tests/revision_v4_1/test_r3a_construction.py; the report, mapping manifest and
input record in R3A_20260906T190955Z_bbce382. The supplied paper's equation (16)
and split/merge statement are on page 12. NumPy's official linspace documentation
confirms that the endpoint is included by default and the spacing depends on num:
https://numpy.org/doc/stable/reference/generated/numpy.linspace.html . This does
not determine AART's cell-boundary semantics; the pinned generator must be traced.

review026/checks_026.py and CHECKS_026.json contain the independent calculations
performed for this ruling, with explicit scope and software versions. They do not
substitute for testing the corrected production path against authenticated HDF5.
