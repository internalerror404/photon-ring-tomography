# PAPER_I_TRANSFER_AUDIT_RULING_029

Repository: internalerror404/photon-ring-tomography  
Branch: research/mahakal_v4_1  
Reviewed commit: 7067c4ed3a270648d54410d601dd63e053f780be  
Disposition: TRANSFER_PRIMITIVE_AUDIT_AUTHORIZED_WITH_TARGETED_G1_CLOSEOUT

Author-directed project review, not a journal referee decision. Sources are the
committed V1/G1/V2 records and implementations. Fifteen local arithmetic and
synthetic checks were executed; no real hull, transfer-ray, target-operator or
585-test-suite execution was performed by this review.

## 1. Decision

Accept the 028 return as useful pilot evidence, and retain NOT_QUALIFIED for
complete physical quadrature. The transferred field is the main next work item.
The curved approximation is a substantial numerical improvement. However, the
published G1 qualification flag does not enforce all the prescribed tests; accept
CURVED_HULL_REFINEMENT_DEMONSTRATED with QUALIFICATION_CLOSEOUT_PENDING, not an
unqualified declaration that every aspect of geometry is closed.

Do not repeat the old straight-hull ladder or the accepted R2 spectrum. Close the
specific missing checks on the same curved candidate, preferably from saved
arrays, while instrumenting the transfer pipeline to identify its first invalid
primitive. Authorize the bounded second transfer batch described below. No R3B,
new geometry, target change, estimator, or submission freeze is authorized.

Preserve all original results, tokens and code. Add this disposition as an overlay;
never turn the archived 028 flags into a different historical execution record.
C13 remains open for complete physical revalidation. Do not invent a new defect
number for a tracer cause that has not yet been identified.

## 2. What the source supports

V1 reproduces source radius on 200 sampled points per order under the same pinned
calculate_observables implementation. This establishes radius-path replay, not
independent validation of the entire transfer (r, phi, t, g^3). That distinction
matters because query.trace_points returns radius, radial sign, time and azimuth,
but does not evaluate redshift.

The 1191 successful bisections out of 1212 attempted brackets establish local
screen brackets, subject to the sampled branch/finite checks. They do not establish
all components of the continuous emission boundary. Twenty-one failed brackets,
unsearched equal-sign cells and potential tangencies remain. Label the contour
LOCAL_BRACKETS_RESOLVED_DOMAIN_COMPLETENESS_PENDING. A radial-sign match alone is
not a complete geodesic branch identity. Preserve the acknowledged rotated-segment
check as nearby-contour consistency, not point-identity validation.

The contour runner drops its _pts arrays before writing its JSON, leaving aggregate
counts instead of the endpoint/point data needed by a downstream cut-cell integrator.
V2 does not consume V1 contours: it still classifies archived center rays. Its
roughly 0.38 partial-response discrepancy is therefore not a measurement of the
benefit of integrating the new physical contour. It correctly shows that the old
available transfer samples remain insufficient. Do not conclude that the annulus
has ceased to matter before the bracket geometry is propagated into fragments.

Solver recovery 0/680 is accepted as zero recovery under that identical policy.
The report lists primitive names but supplies no per-point first-failure diagnosis.
Repeating a deterministic numerical expression shows repeatability, not that its
physical value cannot be recovered. No particular numerical defect is established
yet. In particular, distinguish genuine lack of an allowed order-n equatorial
intersection inside a conservative sampling envelope from failure to evaluate an
intersection that exists. Only a verified physical existence condition, not a NaN,
may support physical non-emission.

## 3. Targeted G1 closeout, not another hull campaign

The two curved-ladder pairs and their small reported differences are accepted as
refinement evidence. The source nevertheless has these gaps:

1. ROOT_TOL is declared but no tighter-root comparison is executed or exported.
2. The shifted test checks pointwise radius error normalized by mean radius, not
   the prescribed band-relative inner/outer disagreement and detector response.
3. Tessellation compares each enclosing polygon's total area against itself at
   twice the resolution. It does not test the thin band or the measured response.
4. The qualification boolean uses only the last pair and the shifted-radius flag;
   it omits the first late pair, tessellation, tighter-root and topology gates.
   band_width_positive is computed from positive total band area, not local nesting.

A numerical example using the committed order-2 tessellation figures makes the
third issue concrete. The inner and outer absolute area changes are approximately
2.4308158e-5 and 2.4898406e-5 M^2; their sum is 4.9206564e-5 M^2. Each enclosing
shape changes by about 2.94e-7 relatively, but this sum divided by the band area
is about 2.46e-5. Even dividing by the SUM of the two band areas gives 1.23e-5.
Because |area(A)-area(B)| <= area(A symmetric_difference B), this is a conservative
lower bound on the band-union-normalized sum of boundary disagreements. The quoted
per-shape number therefore does not certify a 1e-6 band-geometric tessellation
error. It does not refute the much looser 2.5e-4 main hull budget either.

Keep all thresholds unchanged. Compute the actual band/boundary and response
comparisons for tessellation; make the geometry diagnostic band-normalized, and
separately verify its response error. Re-evaluate the saved shifted candidate in
the original metrics. Perform the missing tenfold-tighter-root check on the same
curve and native parameterization. Test actual topology, holes, local nesting and
width; positive area alone is insufficient. Export curve knots, coefficients,
fitted roots, shifted/tighter roots, comparison arrays and hashes, not just summaries.

Use already available authenticated arrays first. If numerical payloads were not
saved, record that reproducibility limitation and recreate only the necessary
fixed-candidate inputs; do not call them previously saved or independently measured.
Increasing tessellation does not require new physical roots. No new fit family,
mark-count sweep, tolerance selection or target-informed geometry selection is allowed.
A passed closeout can promote the SAME candidate prospectively. Missing gates must
produce a pending/blocked status even when the measured refinement looks excellent.

## 4. Transfer audit and same-equation numerical repair

T0: inventory all archived nonfinite fields and the 680 radius failures, including
finite-radius failures in time, azimuth or redshift that the old recovery subset
could not reveal. Record screen/order IDs, masks, source-domain labels, numerical
branches and hashes. Save actual intermediate arrays before any zero filling.
Healthy-radius equality is not a substitute for whole-transfer comparison.

T1: instrument the pinned evaluator without changing its arithmetic. On a frozen
representative set of failures and nearby healthy controls, record the FIRST invalid
operation, not merely the final NaN: constants of motion, radial-root pattern and
residuals, elliptic arguments/domain, polar crossing/order and available geodesic
path, time/azimuth integrals, and the declared redshift/velocity calculation.
Possible sites are a diagnostic checklist, not claims of causes. Preserve both
finite and nonfinite outcomes and legitimate no-intersection cases separately.

T2: after a reproducible cause is identified, permit ONE documented numerical repair
of that cause, solving the same physical equations. Examples, conditional on actual
evidence, include stable root ordering, branch-safe brackets, cancellation-free
algebra, or precision escalation. Do not indiscriminately clip radicands, take
absolute values to force real roots, alter order labels, change the emission annulus,
or update the upstream package silently. The original evaluator stays intact;
produce a versioned candidate with the source-level difference and justification.

Verify the candidate with an independent evaluation of the SAME equations on a
frozen holdout, such as multiprecision or independent quadrature with explicit
branch and error checks. It is a diagnostic comparator, not a silent production
backend replacement. Confirm r, wrapped phi via complex phase, common-origin time,
radial branch/sign where defined, and g^3 under the existing velocity model. Compare
healthy points as well as failures. Same-code radius replay is not this check.
Set scale-aware field tolerances before repair outcomes, trace them to the unchanged
5e-4 component and 1e-3 total response budgets, and report measured residuals.
No numerical repair is promoted merely because it changes NaN to a finite number.

If no reproducible cause is found, stop T2 and return the primitive evidence, not
another uninformative repeated 0/680. If the cause is known but its physical result
remains unresolved, preserve UNKNOWN and the missing-response blocker. If physical
absence is verified, classify only the proven domain accordingly. Do not infer
that whole fragments are non-emitting from one point.

T3: apply accepted contour/support records to the fractional geometry only after
location and interpolation uncertainty are represented. Compare partial responses
on identical known support separately from missing-support and full-response bounds.
The same detector, clock, sigma and field suite remain fixed. No new information
spectrum or estimator is involved. Lack of a validated envelope remains a blocker,
not an invitation to drop difficult pixels.

## 5. Query guards, counters and prospective scope

The transfer entry point charges before calculate_observables, but G1.solve_at
and V2 call solve_hulls BEFORE guard.charge. An over-budget root batch can therefore
execute before refusal. Repair the new wrapper to verify/reserve before execution,
then persist attempted/finished/failed counts even if the solver or report crashes.
Check the actual freeze file against its committed bytes as well as its inputs;
include the installed backend source dependencies and numerical policy. Do not
claim an append-only runtime reservation was already present in 028.

Reserve is a resource allocation, not a requirement to spend arbitrary calls.
The 3300 independent transfer evaluations are recorded as performed; do not claim
4000 were performed or demand 700 duplicate calls just to fill a reservation.
Prospective validation must instead meet its stated scientific coverage and gates.

Boundary lifetime spend is 26300 and the old remaining amount is 3700. Authorize
at most 8000 ADDITIONAL boundary point solves solely for fixed-candidate closeout,
raising the cumulative ceiling to 34300. This explicit 4300 increase accommodates
missing tighter/shifted-root payloads if no cache exists; use fewer when possible.
It is not authorization for a larger hull ladder or a new geometry.

Transfer spend is 17912. Close the first pilot with its actual count; unused pilot
headroom is not a separate new allowance. Authorize a SECOND batch of at most
20000 new screen/order evaluations, within the unchanged lifetime ceiling 250000.
First at most 4000 are for instrumented diagnosis and healthy controls. Hold at
least 4000 of the batch for independent validation; count all baseline, alternate
precision, failed and retried point evaluations. The remainder may be used only
for a registered cause-specific repair and support validation. If the decision
gate fails, do not spend the rest on unplanned retries. No third batch is authorized.

Keep peak memory <=8 GiB, existing resources only, no paid acquisition. Reconcile
elapsed compute already charged under 027/028; use only the remaining part of its
cumulative two-hour envelope or return the time-budget blocker. A query-count
increase is not a hidden reset of elapsed time. Preserve all aborted prior work.

Freeze instrumented code and cohorts before queries. If T1 establishes a cause,
commit a separate repair/holdout freeze before T2 outcomes. Use new filenames for
code and results; do not alter a frozen input during execution. No background work
is implied by delivery of this document.

## 6. Return contract

Return separate dispositions for curved-ladder evidence, full hull qualification,
local contour brackets, continuous-domain completeness, solver primitive diagnosis,
repair validation, full transferred field and overall quadrature. Geometry and
solver-scope statuses must not be collapsed into one optimistic flag.

Required outputs include source/dependency hashes, preexecution guards and fault
injection results, full numerical geometry payloads, per-point failure taxonomy,
healthy/control and independent holdout tables, contour endpoints/uncertainty,
resource ledger and exact NOT_RUN items. An overall ready-to-review token does
not assert numerical qualification. Stop before R3B in all cases.

The manuscript remains an information-boundary study; the older uploaded version
still claims validated physical transfer and order-summed results in sections 5,
6.4 and 10.1. Do not update those claims from partial-response diagnostics. A revised
submission must map every retained claim to the ultimately validated operator and
its actual scope, rather than to a growing test count.

## Evidence

All repository paths at reviewed commit:
- G1_20260907T002858Z_ecddc92/CURVED_HULL_VALIDATION_028.json under artifacts/revisions/mahakal_v4_1/.
- V1_20260907T002421Z_9a6cf49/{EMISSION_CONTOUR_AND_UNCERTAINTY_028,SOLVER_FAILURE_AND_RECOVERY_028}.json.
- V2_20260907T003312Z_85ef3cb/{BOUNDARY_VALIDITY_028_RETURN.md,RESOURCE_LEDGER_028.json}.
- scripts/revision_v4_1/{g1_curved_hull,v1_contour_pilot,v2_partial_response}.py.
- src/phrt/revision_v4_1/query.py.
AART's official documentation separates its lensing-band envelopes and transferred
source coordinates; it is background, not evidence for the cause of these 680
failures: https://github.com/iAART/aart . No upstream substitution is authorized.
review029/checks_029.py and CHECKS_029.json record the local checks and their scope.
