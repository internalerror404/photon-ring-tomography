# PAPER_I_BOUNDARY_VALIDITY_RULING_028

Repository: internalerror404/photon-ring-tomography  
Branch: research/mahakal_v4_1  
Reviewed commit: 6f76ee56f024f4e5895b89325dc43d4db08863b3  
Disposition: PHYSICAL_CONTOUR_PILOT_AUTHORIZED_HULL_TOLERANCE_RETAINED

Author-directed project decision, not a journal referee report. The review read
committed H0/H1/H2 code, results and completion records, and ran 22 independent
synthetic checks. It did not run real hulls, transfer rays, a target operator, or
the reported 574-test suite. Separate source findings, mathematical deductions,
and prospective authorizations throughout.

## 1. Decisions

Accept R3A_FRACTIONAL_QUADRATURE_NOT_YET_QUALIFIED. Preserve the existing failures,
C13, raw maps, numerical results, and disclosed registration deviation.

AUTHORIZE a first, capped 20000-screen/order-evaluation pilot to locate the
physical r_source=50 contour and diagnose/recover numerically unresolved transfer
support. This uses the unspent 250000 allowance; it is not an additional allowance.
A solver-failure boundary is NOT a physical zero-emission contour. It may be
mapped for diagnosis, but may not be used to remove emission from the model.

RETAIN the 2.5e-4 band-relative geometry and hull-only response criteria, the 5e-4
transfer/emission-boundary component criterion, and the 1e-3 total requirements.
A band being two or three ray cells thick is not a reason to dilute its physical
geometry criterion. Ray-cell thickness is a numerical-resolution property.

AUTHORIZE one prospectively specified, validated curved-boundary candidate using
cached root solutions and targeted independent boundary solves. This changes
approximation, not the continuum problem or thresholds. Remaining boundary budget
is 12000 solves, not a new 30000. No compulsory repetition of failed old runs.
R3B remains blocked, and no new R2 spectrum or reconstruction is authorized.

## 2. Interpretation corrections required before the pilot

### 2.1 A center classification is not an area-resolved physical exclusion

fractional.py::classify_support sums each cut cell's area according to its CENTER
ray. The reported roughly 21% outside-annulus share for order 1 is therefore a
center-labeled geometric-area diagnostic. It is not yet a measured continuous
area enclosed by the physical emission-boundary contour. Preserve its numbers
with that meaning. SUPPORTED_BY_VALID_CENTRE_RAY similarly describes availability
at a center, not validated transfer accuracy over its whole cut cell.

At a reliably solved point with r_source>50, emission is zero under the declared
source model. A whole fragment is zero only after the physical predicate has
been established over the fragment. Once a non-emitting fragment is certified,
it is not missing transfer data and does not need a fictitious brightness value.

Use three geometric statuses: certified emitting, certified non-emitting, and
unresolved. Within emitting/possibly-emitting support, separately record transfer
availability and error. Unresolved numerical values are not a new physical mask.
The existing finite-output predicate describes evaluability, not an astrophysical
surface. It must not silently turn numerical solver failures into black pixels.

H2 currently computes unsupported = 1 - supported_fraction, counting outside-
annulus cells with failures and unsampled cells, and then requires that total to
be below a tolerance. That is not a valid final completeness gate when the model
contains genuinely non-emitting regions. Keep it as an old diagnostic; the new
gate must measure unresolved potentially emitting support and its possible
response, excluding only certified physical zeros.

### 2.2 Fixed hull agreement is not complete geometry convergence

H2's active_area_total is the geometric band before the emission predicate. Its
profile-independent value is an expected consistency result of using one hull,
not a proof that the full emitting domain Omega_n converged. Its transferred
responses use only center-supported fragments, with the missing contribution
not computed. Their discrepancies remain valid PARTIAL_RESPONSE diagnostics,
not a completed full-response error estimate.

The order-0 discrepancy changing from about 0.050 to 0.025 does not isolate an
exact geometric share of the old error. Differences between norms do not add
like vector contributions, and the omitted support changes too. To attribute
causes, compare error vectors under controlled support/field changes or report
bounds. Keep 'fractional geometry reduces the measured discrepancy' rather than
'exactly half was geometric'. The unchanged order-2 discrepancy shows that this
change alone was insufficient; it does not prove all geometric error is absent.

### 2.3 R2 count and budget language

Given the readback ratio bounds [0.500081210,1.008048257], the existing profiled-
Fisher inequality gives conditional singular intervals approximately
[1.016312,1.442937], [0.951753,1.351278], [0.570173,0.809519]. Conditional on the
same retained rows, metric, nuisance family and fixed sigma, at least ONE and at
most TWO operational modes are guaranteed. The exact corrected count has not
been computed. 'Only one is certified' is not 'the count changed to one'. Keep
the isolated interior-pitch result and the legacy-measure R2 acceptance intact.

18000/30000 boundary solves means 12000 remain. The remaining transfer allowance
is 250000. BUDGET_EXHAUSTED overstates the actual counters: the proposed uniform
linear-polygon completion is projected not to fit the remainder. Preserve the
old token with an overlay PROJECTED_UNIFORM_POLYGON_PLAN_OVER_REMAINING_BUDGET.
Count the aborted 9000 solves permanently. 'Thousands, not millions' for new
contours is a planning hypothesis, not yet an observed cost.

## 3. Physical contour and solver audit

For each fixed image order/branch define F_n(alpha,beta)=r_n(alpha,beta)-50 where
the transfer is well-defined. Continue the zero set using bracketed, safeguarded
solves seeded from the archived inside/outside samples and geometry. Verify
branches, finite values, residuals and screen-location brackets. A sign change
across a pole or a switch of geodesic branch is not a valid root bracket. A root
solver's success flag is not a physical certificate.

Do not assume a globally star-shaped r=50 contour, one root per radial line, or
that equal endpoint signs exclude roots. Check for multiple crossings, closed
components and near-tangencies using a declared two-dimensional cell/continuation
plan. Retain ambiguous cells rather than joining unrelated branches. The apparent
horizon/order boundary and r=50 boundary remain distinct; handle any verified
lower-radius boundary under its own physical condition.

A scalar residual alone does not bound screen-location error. Record brackets or
an independently justified gradient lower bound. For a contour uncertainty tube,
propagate its symmetric-difference area and possible detector response. Preserve
the existing triple-intersection rule. Root endpoints are not a substitute for
validating integration over the emitting fragment.

For solver-unresolved points, record which primitive failed: radial roots or
branch selection, polar intersection/order count, azimuth/time integral,
redshift, floating-point conditioning, or missing previous evaluation. Audit raw
pre-nan_to_num values when needed. A NaN does not identify a differentiable
'solver-validity contour' to root-find. A success/failure classifier can guide
sampling but may not define no-emission support.

Retry the SAME physical equations using a prospectively declared bracket,
continuation, tolerance or stable evaluation policy. Record original and retry
outcomes and all costs; do not alter physical cutoffs. Independent cross-checks
may be diagnostic only, never a silent backend substitution. If the same-model
result remains unresolved, preserve UNKNOWN_SOLVER and bound its possible signal
only with validated envelopes, otherwise return a blocker. No extrapolation
across a singularity and no replacement of missing brightness by zero.

For uncertain support U_d in detector cell d and a validated field envelope M_d,

    |delta y_d| <= M_d |U_d|,
    ||W delta y|| <= sqrt(sum_d (M_d |U_d|)^2/(sigma^2 |D_d|)).

Use bounds for each declared field/time. A sampled maximum is not automatically
an envelope, and a small uncertain area does not imply a small response. Retain
root/source-boundary error within the inherited 5e-4 transfer/emission component
and enforce the full 1e-3 error and mask/area budgets. Do not require physical
non-emission to occupy a small fraction of the lensing band.

## 4. Thin-band accuracy and a cheaper candidate representation

The original 2.5e-4 band-relative and independent-boundary criteria stand. For a
thin strip of width w displaced by delta, the relative symmetric difference is
approximately 2|delta|/w, not delta divided by the detector or outer-hull scale.
Thin bands need more accurate boundaries to meet the same relative geometric
claim. An identical integrated detector flux can hide a displaced thin band;
detector-response agreement does not retroactively qualify a failed hull metric.

A narrower detector-only error certificate could be a different future claim.
It is NOT the full hull qualification authorized here and must not silently
replace it. The present alternative is to improve the boundary approximation.

The n=3840 cost estimate applies to the present straight-chord representation
and all-five-boundaries solve wrapper. It is not a universal requirement. Allow
one declared curved interpolation of the root-defined boundary, checked by new
root evaluations at independent parameters. Examples are a periodic cubic radial
representation on a validated smooth star-shaped segment, or a piecewise parametric
curve where that representation is not valid. Keep the order-0 outer square exact
and retain real corners/endpoints. Do not smooth a physical discontinuity, silently
convexify, enforce a chosen width by clipping, or cross inner/outer branches.

Cached roots can support the candidate; they are development inputs, not fresh
validation. New midpoint/quarter-point or shifted parameters must solve the
pinned boundary equations and test the candidate away from its knots. Only solve
boundaries/orders requiring refinement; do not automatically recompute the other
four roots for every requested point. Preserve the old equations, safety factors,
clamps and branch conventions, recording when these make a hull a coverage
envelope rather than an exact emitting contour.

Densifying a validated CURVED candidate into a polygon for the existing overlap
kernel is allowed, with a separate tessellation/integration error budget of 1e-6
or tighter. Inserting points on the old straight edges is still not a new physical
hull. Keep two successive late comparisons, shifted fresh-root verification,
root-residual/tolerance checks, topology and positive-width tests. A fit passing
at its own interpolation nodes proves nothing about between-node geometry.
The cached critical-curve parameterization is also an input approximation: test
its sensitivity where it affects new boundary roots rather than assuming it exact.

A synthetic analytic thin-band test in checks_028.py demonstrates possibility,
not a Kerr result: at 128 nodes per boundary, a straight polygon's relative
boundary disagreement is about 9.64e-2, whereas a periodic cubic checked against
fresh analytic values is about 4.19e-6. This does not guarantee the real candidate
will pass or prescribe that interpolant where its smoothness assumptions fail.

Two small H1 source issues also need correct labels in the new implementation:
- The shifted-sample test uses 2.5e-4; only the tenfold-tighter-root comparison uses
  2.5e-5. h1_hull_convergence.py applies ROOT_TOL to both. Neither was run, so this
  does not change the present failure, but do not budget an unregistered stricter
  shift test as if the ruling required it.
- hulls.py::region_measures integrates squared radius with trapezoids. Including
  polygon vertex angles does not make that quadrature exact on straight edges.
  The measured refinement residual is useful; call it approximate quadrature,
  not exact polygon area. Use the checked clipping kernel or actual angle-crossing
  analytic integration as appropriate, preserving a separate integration test.

## 5. Resource and execution authorization

TRANSFER PILOT: at most 20000 new screen/order transfer evaluations in the first
batch of the carried-forward allowance. Reserve at least 4000 of those for
independent contour/support validation, not fitting. Begin with at most 4000
queries to diagnose solver failures, brackets, topology and cost. Continue within
the fixed pilot plan only if same-branch evaluations and recorded costs support
it. No second transfer batch is launched without reviewing this pilot. Count
vector-batch elements, all solved orders, failures and retries. Cached reads cost
zero new evaluations but require hashes and provenance.

HULL CANDIDATE: at most the remaining 12000 boundary-point solves. Reserve at least
4000 for independent shifted/root checks before allocating fit/refinement calls.
One candidate representation and its sampling rule must be committed before new
validation roots. No success is promised within this budget. Count internal full
transfer evaluations against BOTH applicable ledgers. The lifetime counters stay
30000 boundary and 250000 transfer evaluations unless a later ruling changes them.
Keep the inherited 8 GiB and cumulative two-hour compute envelope; reconcile time
already consumed before launch rather than silently resetting it. No paid resources.

Registration gap: accept the disclosure, not compliance. Change the overlay to
AUDIT_COMPLETE_WITH_PREREGISTRATION_FAILURE. The existing condition
preexecution_registration_state_recorded is not equivalent to
preexecution_registration_satisfied. The new numerical entry points must refuse
any uncached physical query before a committed input freeze is verified. Freeze
code, rule, hull/cache inputs, maps, solver configuration, selection plan, tests,
and budget counters. Require a clean registered tree and fresh output directory;
write phase-specific execution identities. Guard physical calls, not just the
final report. Do not backdate, delete or rerun historical diagnostics merely to
make their metadata appear prospective.

Maintain independent statuses for kernel/units, hull representation, physical
emission-domain contours, unresolved solver support, field accuracy, overall
quadrature and registration. Report known non-emission separately from uncertainty.
Only a full valid-domain/field comparison can eventually clear the total gate.
Return BOUNDARY_VALIDITY_028_REVIEW_READY or BOUNDARY_VALIDITY_028_BLOCKED with
actual counters and every NOT_RUN item; neither token authorizes R3B.

## Evidence and checked background

All repository references are at reviewed commit unless stated otherwise:
- H2_20260906T225008Z_4031c21/FRACTIONAL_COVERAGE_027_RETURN.md and COMPLETION.json.
- H1_20260906T224502Z_4031c21/HULL_CONVERGENCE_027.json.
- scripts/revision_v4_1/h1_hull_convergence.py and h2_fractional_validation.py.
- src/phrt/revision_v4_1/fractional.py and hulls.py.
- src/phrt/geometry/sampling.py and raymap.py, traced in the preceding review.
The attached manuscript equation (2), page 6, uses a physical validity factor in
the transfer map. It is an older manuscript, not the new numerical evidence.
SciPy's official brentq documentation requires a continuous function with opposite
endpoint signs: https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.brentq.html .
That mathematical condition does not certify continuity or branch correctness for
any particular ray function. No dependency upgrade is authorized.

review028/checks_028.py and CHECKS_028.json contain the independently executed
synthetic checks and their environment. They are not a physical-operator rerun or
an execution of the agent's full suite.
