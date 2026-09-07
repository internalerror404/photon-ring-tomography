# PAPER_I_DOMAIN_INTEGRATION_RULING_031

Repository: internalerror404/photon-ring-tomography  
Branch: research/mahakal_v4_1  
Reviewed commit: aa3d187039a8cceef458cecd6f608dc06264cd04  
Disposition: SAMPLED_ABSENCES_ACCEPTED_DOMAIN_AWARE_INTEGRATION_PILOT_AUTHORIZED

Author-directed project review, not a journal referee decision. This review read
connected source and JSON records and executed 22 local synthetic arithmetic,
quadrature and control-flow checks. It did not evaluate the actual 680 rays,
read back the full per-point NPZ locally, or rerun the reported 597-test suite.
No new scientific outcome is asserted beyond the scope of that evidence.

## 1. Decision: close the alleged lost-event repair, not the whole acquisition

Accept the numerical adjudication of the inspected sample set: the 680 originally
masked core points are consistently classified as 532 absent requested crossings
after escape and 148 absent requested crossings after capture. The two radial
quadrature implementations agree on those classifications and on 596 controls.
The revised calculation agrees on the 880-point comparison panel as well.
There is no evidence here requiring a replacement source-radius formula. Do not
switch branches, restore the masked samples as emission, or undertake another
attempt to recover physically absent events.

Discharge MISSING_TRANSFER_SUPPORT for those enumerated point/order IDs, under
the tested geometry, source model and numerical validation scope. Their old
exclusion was already present, so this disposition changes the reason codes, not
the original map values. Do not generalize from those points to whole cells,
other geometries, all uncomputed points, or complete source-domain integration.
Keep the accepted G1 numerical hull qualification closed; no new hull solves are
needed or authorized. Keep the legacy R2 acceptance and C13 quadrature defect's
remaining scope unchanged. R3B, new target spectra, estimators and a submission
freeze remain unauthorized.

The next approved activity is one bounded fixed-detector, domain-aware integration
pilot using the existing hull. Its first step includes making the numerical
predicate safe for previously unseen contour-adjacent points and a small fresh
comparator confirmation. This is not another 680-ray campaign or a demand to
recover a positive number of events. No production physics/backend repair is
justified by the present result.

## 2. What the comparator repair does and does not establish

The primary pathdomain.py blob is 3f4cc4e4f641083474f3ac27feaac2e58398ae38 in both
the first run's commit 57fae0f and the reviewed head. The primary predicate did
not change in the reported comparator correction. The exposed failure of a
single global Gaussian rule is therefore a substantive numerical diagnosis,
not evidence that the primary labels were tuned until they agreed.

Nevertheless, the 880 points were untouched only before the FIRST execution.
The revised comparator was then selected after 30 disagreements on that same
panel had been seen. Preserve its original precommitment, but label the revised
result PRECOMMITTED_PANEL_REUSED_AFTER_COMPARATOR_CORRECTION. Do not describe
the final result as confirmation on a still-unseen panel, nor erase the first
57 development and 30 panel disagreements. Repairing a defective numerical
reference is legitimate; the strength of the revised conclusion comes from a
correctly justified reference and subsequent checks, not from its original error.

The two methods share the conserved quantities, root array, angular crossing
G_theta, classify_path implementation, and asymptotic tail. They differ in radial
quadrature. This is alternative radial-integration evidence conditional on shared
inputs, not a fully independent geodesic/branch/order implementation. The counters
called invented/missed compare VALID_EMITTING_EVENT with the library's NaN flag
on a panel deliberately restricted to masked cases and known emitting controls.
A finite exterior event outside r=50 is not an emitting event; future confusion
matrices must compare like labels and include this case. Avoid claiming general
zero missed/invented events from a sentinel match on the restricted panel.

Before extending to new boundary points, freeze the corrected numerical reference
and its convergence tests. A small new confirmation cohort, at most 192 points,
can be folded into this pilot, selected by geometry and declared domain-margin
strata rather than target information. Include emitting, capture-absence,
escape-absence, finite exterior/outside-annulus, and boundary-uncertain cases where
available. Keep primary/reference labels unavailable to tuning after this freeze.
This is engineering confirmation with a stated finite scope, not a statistical
population guarantee. Shared root/angle inputs must be listed explicitly; check
polynomial residuals and an independent angular/event evaluation on a registered
subset, without replacing the production backend.

An analytic control used in this review illustrates why grading is reasonable
but not universally sufficient. For f_delta(x)=1/sqrt(x+delta) on [0,1], the exact
integral is 2/(sqrt(1+delta)+sqrt(delta)). At delta=1e-8 a global 64-point Gaussian
rule errs by 0.0133001; 64 graded panels reduce the error to 2.52e-10 and 128 panels
to about 2.22e-16. At delta=1e-12 the same 64 panels still err by 2.44e-5. These are
synthetic integrals, not remeasurements of the Kerr comparisons. They justify
measuring panel/tolerance convergence and margins, not trusting a fixed panel
count or agreement alone. SciPy documents quad's abserr as an estimate, and
fixed_quad supplies no a posteriori error estimate; neither is a rigorous enclosure
by default. No dependency update is required.

## 3. Numerical safeguards required before contour-adjacent use

The source has paths that were not covered by the current all-finite result:

- pathdomain._J returns a zero integrand whenever the potential (or reduced
  turning-point factor) is nonpositive. This may hide an incorrect allowed-path
  interval or roundoff instead of rejecting it. Nonfinite/negative radicands in
  an interior evaluation must return DOMAIN_UNRESOLVED, not contribute zero.
  At a verified simple turn, compute the product of the other root factors or
  another justified analytic limit; do not form a cancellation-prone 0/0 and
  silently replace the limit by zero.
- independent_code does not check finite integral results. In the capture branch,
  NaN comparisons are false and it can fall through to VALID. Add finite checks,
  quadrature-convergence/error checks and explicit uncertainty margins before
  branching. This is a demonstrated control-flow vulnerability, not a finding
  that any of the delivered finite results took that path.
- Include uncertainty at the escape endpoint as well as the annulus/horizon
  endpoints. Require nonnegative finite angular travel, appropriate root/domain
  ordering and explicit handling of degenerate/critical cases. Do not extrapolate
  the present simplified root classifier into a global certified predicate.
- _tail is a truncated asymptotic expansion, not an exact closed-form infinite
  tail. Preserve the useful correction but estimate/bound the omitted remainder
  or use a converged transformed tail. This label correction alone does not imply
  a material change at r_far=1e7.

Make these changes in a new versioned wrapper; do not overwrite the frozen
pathdomain.py. Use fault-injection tests for NaN integrals, invalid radicands,
misordered endpoints, escaped-ray uncertainty and degenerate roots. Report any
such guards encountered on the existing saved cases rather than asserting they
were never needed. If they invalidate a current point's support claim, return
that exact point and margin; do not silently force agreement with the old count.

## 4. The next integration must use a physical domain, not only old center labels

For fixed order n and detector pixel d, the intended quantity is

  y_d(t_o) = sum_n integral_{D_d intersect B_n} chi_n(xi) f_n(xi,t_o) dOmega,

where the hull B_n is a qualified sampling envelope, chi_n denotes existence and
source-annulus validity, and f_n contains the appropriate transferred field.
Known absence at one sample does not make every part of its dual cell absent.
Conversely, certified absent fragments are physical zero contributions, not
missing values that require interpolation. Preserve unresolved regions and their
possible response until bounded. Detector noise stays sigma^2 |D_d| once per
full detector pixel; do not reduce it to emitting area.

Use the signed Mino-domain margins already defined in review 030, not a new
branch expression. For capture, margins are G_theta-s_50 and s_H-G_theta; for
scattering that enters the annulus, they are G_theta-(J_o-J_50) and
(J_o+J_50)-G_theta. Their uncertainties must accompany their signs. Root existence,
annulus membership and numerical accuracy remain separate decisions.

It is not mathematically necessary to regenerate every dropped contour from V1
before integrating. Two implementations of the same continuum quantity are
allowed under a prospectively frozen choice:
A. reconstruct and export physical contour brackets/fragments using these margins,
   then integrate the correctly clipped domain; or
B. integrate the indicator implicitly with adaptive cut-cell quadrature and an
   explicit unresolved-boundary area/response budget.
Both must preserve topology/branch distinctions, detect rather than assume away
multiple crossings/tangencies, and meet the same mask/area and response criteria.
Changing representation is not permission to treat an unresolved midpoint as zero.
Do not call implicit integration full contour recovery. Choose the implementation
from geometry and target-free field accuracy, not from its eventual spectrum.

Reuse the accepted hull arrays. Start from actual cells/fragments intersecting
validity transitions and from known smooth interiors; no mandatory global raster
refinement or duplicate full hull generation. Evaluate r, phi, coordinate time
and g only at events that actually exist. Reuse one valid transfer tuple for the
eight observer times; do not charge eight new ray calls for algebraic reuse.
Interpolate azimuth via periodic phase where appropriate and never bridge a
physical branch discontinuity. Finite fields on an invalid event are not valid
brightness or an envelope.

Run identical-support comparisons to separate transfer interpolation error from
changing-domain error, then a combined fixed-detector comparison. The inherited
11 screen/transfer fields are construction diagnostics; distinguish pure geometric
screen fields from source-valid transferred fields. Their convergence does not
prove arbitrary-source inversion accuracy. Retain per-order/per-field/per-time
metrics and the same absolute clock. Unknown-support area needs a validated field
envelope to bound its missing response; sample maxima alone do not supply one.

The existing budgets remain: hull 2.5e-4, transfer/emission component 5e-4,
end-to-end response/mask/area 1e-3, and integration/tessellation 1e-6, with the
registered successive-pair and independent-check requirements. No tolerance
relaxation, detector change, source-class change or target inspection is allowed.
This is a pilot: if the remaining budget cannot establish those criteria, report
convergence and a precise remaining error, rather than escalating silently.

## 5. Repair the denominator and resource summaries without new physics

PHYSICAL_MASK_IMPACT_030 lists 485480 unresolved points next to only 4976 in-band
points for order 2. d3_return_030 sums UNRESOLVED over the entire stored grid while
reporting in_band from a different mask. The table therefore cannot mean 485480
missing points inside that band. Rebuild the zero-query overlay on explicitly
matched domains: full storage grid, archived band membership, qualified-hull
intersection, and the fixed aperture. Keep physical absence and numerical unknown
separate. Assert partition totals on each named domain; outside-envelope storage
slots are not evidence of missing in-band light. Do not infer that every point
outside an old discrete mask is physically excluded by the refined hull either.

The two committed 030 attempt ledgers each record 2156 evaluations: the first run
D1_20260907T101654Z_57fae0f and the corrected-comparator run
D1B_20260907T102020Z_5c1cb6a. Re-registration did not erase the first evaluation.
Recorded native-evaluator spend is therefore at least 4312 for 030 and 6952 in
the existing second batch, including its prior 2640. Its recorded remainder is
13048, not 15204; lifetime native-evaluator spend is at least 24864. A count of
2156 is accurate for the delivered run, not for the campaign.

The current runner reserves around instrument only, then evaluates the primary
and independent radial integrals outside that reservation. Reconcile reference
end-to-end evaluations under the existing 030 counting convention before launch;
13048 is an upper bound on spendable remainder until that is done. Do not count
every quadrature abscissa as a new screen/order ray, but do not disguise an
independent full numerical re-evaluation as a cache read. Preserve separate raw
ray, path-reference, retry and cache counters with unambiguous evaluation IDs.
No extra allowance or third batch is created by this ruling. Any unmet old
3000-decision-point condition must be disclosed, not evaluated on only the last
run. Counting corrections do not require new physical reruns.

## 6. Bounded execution and completion

I0: zero-query corrections, exact/synthetic guards, inventory/lineage readback,
full-cost reconciliation, and a new prospective code/config/cohort freeze.
I1: at most 192 fresh confirmation points and at most 1024 charged end-to-end
primary/reference evaluations, all inside the reconciled second-batch remainder.
Require zero unsupported forced labels and agreement within predeclared numerical
uncertainty on tested points; do not retune against the new panel. Failure stops
outcome-bearing integration and returns the exact cause.
I2: at most 6000 new charged evaluations for the domain-aware integration pilot,
only after I1 and input guards pass, and only while leaving at least 4000 of the
reconciled remainder reserved for independent response validation. Stop early if
resource or physical prerequisites fail. I3 uses that remaining registered
validation budget, not a new allocation. Actual usage is reported, never rounded
to a reserve. These caps are ceilings, not mandatory spend or promises of success.

No new hull root calls; boundary lifetime spend stays 33410 under 34300. Keep peak
memory <=8 GiB and the remaining part of the inherited cumulative two-hour compute
envelope after reconciling previous runtime. No paid resources. Query guards must
pin all maps, mask files, source/metric definitions, transferred-field implementations,
reference methods and the corrected freeze itself, not only source Python files.
Use a monotonic all-phase ledger, reserve before the call, persist exceptions and
reject missing conditions. Assertions of governance/holdout freshness must derive
from recorded state rather than hardcoded True values in a report generator.

Return separate statuses for sampled absence adjudication, numerical-domain guard,
fresh comparator confirmation, emitting-region integration, whole-transfer accuracy,
fixed-detector quadrature, and governance. DOMAIN_INTEGRATION_031_REVIEW_READY is
not R3B authorization. Keep every NOT_RUN and the comparator-reuse history visible.
No repeated hull/R2 campaign is requested.

## 7. Manuscript scope and provenance

A supportable revised statement is: 'At the reference geometry, the 680 audited
masked core point/order samples were classified as absent requested exterior
crossings by path-domain analysis. Two radial quadrature methods agreed on that
classification. No masked emitting event was demonstrated in this cohort and no
transfer-formula repair was made.' Add the comparison-panel history and shared
input assumptions in the numerical appendix. This does not validate all masks or
converge the fixed-detector transfer integral. Equation (2), page 6 of the supplied
older manuscript, already contains the physical validity factor chi; validated
absence belongs in that factor, not in a reconstructed-emission claim. The older
PDF is not the latest correction record and its other quantitative claims are
not renewed by this ruling.

Primary repository sources at reviewed commit: pathdomain.py;
d1d2_adjudicate_030.py; d0_freeze_030.py; d3_return_030.py; D1 and D1B attempt
ledgers; D1B/INDEPENDENT_DOMAIN_HOLDOUT_030.json and PHYSICAL_MASK_IMPACT_030.json.
The source evidence was read through the GitHub connector. The attached synthetic
check file is independent arithmetic and control-flow illustration, not execution
of those repository sources. External numerical background checked:
https://docs.scipy.org/doc/scipy/reference/generated/scipy.integrate.quad.html
and https://docs.scipy.org/doc/scipy/reference/generated/scipy.integrate.fixed_quad.html .
