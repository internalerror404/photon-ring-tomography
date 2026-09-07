# PAPER_I_MATCHED_INTEGRATION_RULING_032

Repository: internalerror404/photon-ring-tomography  
Branch: research/mahakal_v4_1  
Reviewed commit: e9924705285d04fd282758de640a916044e987c7  
Disposition: BLOCK_ACCEPTED_LEAF_GEOMETRY_AND_COMPARISON_PREFLIGHT_REQUIRED

Author-directed project review, not a journal referee decision. This review read
connected source and records and ran 20 local synthetic arithmetic, geometry,
control-flow and plan-validation checks. It did not run campaign rays, download
unreported sample arrays, or rerun the reported 607-test suite.

## 1. Decision and scope

Accept the blocked return and the withdrawal of the mixed core/fine comparison as
convergence evidence. Preserve G1 numerical qualification, the audited 680-point
absence interpretation, legacy R2 scope, and every previous numerical record.
Do not attempt a new transfer-formula repair. C13 and physical quadrature remain
open. No larger compute allocation, third batch, R3B, new target spectrum,
estimator or submission freeze is authorized.

Allocation was a real failure, but is not the only remaining problem. The I2
runner repeats the parent-fraction overlap approximation rejected in ruling 027,
measures a constant-field occupancy proxy rather than the full transferred
response, and does not bound between-sample domain error. A balanced rerun of
that same code would still not answer the physical convergence question.

Authorize a ZERO-NEW-PHYSICAL-QUERY repair and planning stage: correct the leaf
assembly using fixtures, audit I1 prerequisites and counts, inventory reusable
payloads, and produce one costed matched-comparison manifest. Return that plan
before spending any more of the remaining second batch. This pause is not a
requirement to repeat the old hull, R2, or absence campaigns; it prevents a second
expensive incomplete comparison. The next physical run must complete its declared
comparison bundles or refuse to start, rather than silently report baseline-only
arms as evaluated. Narrow local diagnostics are permitted as plans but may not be
presented as full-domain quadrature qualification.

## 2. I2 implements a parent fraction, not spatially resolved leaf integration

Source: scripts/revision_v4_1/i2_domain_integration_031.py.
It computes four point labels per selected parent, assigns

    chi[parent] = mean(subpoint_labels),
    y[detector] += old_overlap[detector,parent] * chi[parent].

This is precisely the whole-parent fraction times unclipped-with-respect-to-the-
emitting-subregion overlap approximation. The old overlap already includes the
sampling hull, but not the within-parent emission domain. Four new point values
cannot be averaged and redistributed uniformly across that geometry without a
new approximation error. This can be wrong even if the emitting fraction were
known exactly; unequal band clipping of the child cells introduces another error.

For a unit parent emitting only on its leftmost 20%, with two half-width detector
pixels, exact contributions are (0.2,0). A parent fraction of 0.2 gives (0.1,0.1).
Total flux agrees while the detector image does not. Ruling 027's kernel canary
caught this example, but I2 bypasses the geometry that made the canary correct.
A helper test is not a production-path integration test.

For an implicit child-cell approximation, use

    y_d = sum_parent sum_leaf |D_d intersect C_leaf intersect B_n|
                              * chi(xi_leaf) * f(xi_leaf).

Each genuine child keeps its own detector and hull overlap; do not collapse it
back to its parent. This is still a quadrature approximation to the physical
indicator and field, not an exact emission contour. Refine the indicator and
field, compare their effects, and record unresolved fragments or empirical
convergence limits. Alternatively integrate explicitly certified emitting
fragments with the triple intersection already specified by ruling 027.

Retain known point absence as a point fact. Neighbor-label disagreement is a useful
candidate selector, but same-label neighbors do not certify that no small component
or tangent boundary crosses a cell. Four finite labels and zero failed evaluations
do not establish zero uncertain boundary area. The current unresolved_area sum
only describes point-evaluator uncertainty in sampled subcells. Rename it
SAMPLED_EVALUATOR_UNRESOLVED_AREA_PROXY, not a complete geometric-error bound.
If unknown labels are omitted from a response, call that a partial response and
carry its possible contribution; an 'unresolved_not_zero' Boolean is insufficient.

## 3. What the measured changes do and do not show

The reported 3.853e-3 and 1.854e-3 are changes in total estimated emitting area
between two approximations, with the proxy applied to selected transition cells.
They show sensitivity of that numerical representation, not a validated error
of the center rule against the physical integral. Do not infer that one rule is
correct just because they differ, or call the discrepancy a proven transfer error.
The 5e-4 criterion is for the whitened transfer/emission response component; the
registered total area/mask budget is 1e-3. Keep these metrics distinct.

I2 builds only a one-column response for f=1. It does not validate g^3, source
azimuth, source time, or the inherited temporal test fields. Its profile metric is

    abs(norm(y_fine)-norm(y_core)) / norm(y_fine),

rather than norm(y_fine-y_core)/norm(y_fine). Equal-norm images can disagree in
all their spatial content. Save and compare matched detector vectors and compute
per-order, per-field and per-time residuals, not a difference of their norms.
No physical operator spectrum or reconstruction claim is supported by this pilot.

The selected cells are not all the discovered transition cells: tc is truncated
and the truncated count is emitted as transition_cells_found. Preserve separate
found, eligible, selected, evaluated, cached, omitted and unresolved counts and
areas. Zero selected cells in core order 2 or a fine arm means NOT_EVALUATED for
that refinement, not zero error, zero unresolved support, or no transition cells.
Baseline center-rule values can remain as explicitly named controls.

The committed I2 output directory and runner contain summaries and ledgers but
no saved subpoint labels/transfer arrays or detector vectors. Check for an actual
external cache before declaring those 6000 evaluations reusable. Coordinates can
be reconstructed from a frozen rule, but missing values cannot. Any genuine
re-evaluation must be charged. Future batches must write recoverable chunk payloads
and hashes as they finish, before generating a summary.

## 4. I1 has useful agreement but did not clear the launch gate

Keep the 428 agreeing cases and 66 unresolved references. They are not 66 label
conflicts, but they are also not successful independent confirmations. Without a
validated bound or a prospectively justified scope exclusion, unresolved primary-
reference comparisons cannot silently pass the launch condition for a full-domain
integration campaign. This is particularly material to the untested order 2.
No comparator tuning on this panel should be called a fresh holdout success.

The old reused-panel label belongs to the 880-point 030 panel. The 031 runner says
it did not tune the comparator on the new panel and excluded prior 030 indices.
Preserve that narrower freshness statement for the 494 records; do not assign the
old reuse label to them without a corresponding edit/run history. Different kinds
of reuse should have distinct provenance, not one blanket label.

The protocol capped I1 at 192 points AND 1024 charged evaluations. The source applies
38 samples per stratum repeatedly across orders, producing 494 points. Its output
still records points_cap=192, but no cap check stops execution. Meeting a separate
call cap does not satisfy the point cap. Record the 302-point overrun; do not rerun
or discard the already observed data. The user's 1024 is the evaluation ceiling,
not the reported native charge, which is 494.

The purported shared-input polynomial residual is tautological:

    product_j (returned_root_i - returned_root_j) = 0

because one factor is the root subtracted from itself. It is zero even for an
arbitrary wrong root list. Evaluate the original radial polynomial from the
conserved quantities, not a polynomial manufactured from the returned roots.
For the project's M=1 convention, expansion of its radial potential gives

    R(r) = r^4 + (a^2-lambda^2-eta) r^2
           + 2*((lambda-a)^2+eta)*r - a^2*eta.

Use complex Horner evaluation and a scale-aware backward residual; a small residual
alone is not a root-location bound near a multiple root. Test deliberately perturbed
roots. The reported max_residual=0 does not check the shared input as claimed.

One source-level issue deserves a fixture before new comparator queries:
pathdomain2's reduced product selects roots with `q is not turn`, an object-identity
comparison rather than exclusion of the verified turning-root index. For u != 0
it still divides R(r) by r-turn, allowing cancellation near the turn. The reference
uses the same division. This is a potential numerical weakness, not a diagnosis
of the 66 cases without their intermediate data. Exclude the identified simple
root by index with multiplicity/branch checks and validate the endpoint limit on
analytic fixtures. Export actual reason codes, integral values and convergence
estimates when a reference is unresolved; I1 currently discards that detail.
Do not mask an invalid potential or a physically uncertain case to gain agreement.

## 5. Why the budget must belong to comparisons, not traversal order

A sequential cap across (core n0, core n1, core n2, fine n0, fine n1, fine n2)
protects the wallet but not the experiment. Each comparison needs both profiles,
the same physical detector region and integrand, and its own quadrature levels.
An extra 12000 evaluations is only a planning estimate until those dependencies
and the numerical reference costs have been enumerated. Six equal quotas alone
do not guarantee sufficient coverage or correctness.

Build the allocation before running. The minimum planned matrix has six
profile/order endpoints and three declared integration levels, enough to form two
successive refinement pairs. Use one leaf rule family and one intended emitting
domain; parameters may refine but the quantity must not change. Choose physical
regions from geometry, boundary coverage and accuracy, not target singular values.
Make matched per-order/profile/level work an atomic budget bundle, with a stop rule
that never changes an omitted endpoint into a baseline observation. Schedule
coverage across all orders before deep refinement of one order. A local diagnostic
must state its actual domain and omitted fraction; it cannot qualify D026 globally.

The delivered checks_and_preflight_032.py rejects missing matrix endpoints,
inconsistent domain/representation/field/detector/clock/noise IDs, absent evaluation
dependencies, missing payload plans, and a declared budget that invades the 4000
validation reserve. It is a schema/cost preflight, not a physical certificate or
execution authorization. Runtime guards must verify actual cached bytes and all
scientific prerequisites; a Boolean in a plan does not do that work.

Return one plan, either a feasible complete local diagnostic plus a measured path
to global qualification, or a costed full-domain comparison. Show full costs,
shared/cache reuse and error coverage. Do not choose a smaller physical claim
silently. If the whole comparison cannot fit, state that before the first query.
There is no requirement to exhaust the remaining allowance to demonstrate a block.

## 6. Resources and governance

Accept the newly recovered 120-attempt aborted execution; my earlier summary-based
count missed it. The matched native-tracer ledger now reports 7072 before 031 and
6494 during 031, totalling 13566 in the second batch and leaving 6434 on that
native-only convention. Those arithmetic corrections are accepted.

The ledger inventories primary/reference quadratures but declines to meter them
as separate end-to-end evaluations. That is not the counting convention required
by 030/031. Reconcile evaluation IDs and distinguish native ray calls, primary
path integrations, independent reference integrations, cached algebra and retries.
Do not count quadrature abscissae as new rays, but do not silently redefine the
previous quota either. Treat 6434 as the reported native balance, not an automatic
spending authorization. Preserve the 4000 response-validation reserve pending that
reconciliation. No new allowance is granted in this ruling.

Governance disposition: AUDIT_COMPLETE_WITH_PROTOCOL_DEVIATIONS, not COMPLETE
without qualification. In addition to the admitted allocation error, preserve the
point-cap overrun, unmet reference-confirmation gate and partial/mismatched
comparison. Hardcoded completion conditions did not detect them. Add fault-injection
tests in the actual launch/report path: 193 points, unresolved reference, missing
fine/order2 arm, one-column occupancy offered as full transfer, equal-norm different
vectors, parent-fraction assembly, absent payload, and an infeasible complete bundle.
The old 607-test result remains a reported test result, not proof of those missing
properties. The old blocked token and all bytes remain unchanged.

## 7. Authorized next return and manuscript consequence

Only zero-new-physical-query work is authorized now: fixtures, versioned leaf
assembly, plan generation from existing geometry/cache metadata, evidence overlays,
correct counters and query guards, and static/analytic reference checks. Recomputing
physical path integrals or original rays is not zero-query simply because the screen
coordinates are cached. No new hull roots, physical samples, target operators or
independent response-validation calls may start under this ruling.

Return MATCHED_INTEGRATION_032_PLAN_READY_FOR_REVIEW or
MATCHED_INTEGRATION_032_PLAN_BLOCKED. Include the exact missing physical prerequisite
and full-cost budget; neither token launches a run. The next ruling can authorize
a verified matched bundle, rather than another open-ended greedy pass.

For the manuscript, preserve the distinction already made by equation (2), page 6
of the supplied draft: chi multiplies the full transferred source response. A
constant occupancy proxy cannot validate the entire transfer operator. Its older
section-5 'Validated Computational Operator' statement and physical order-summed
claims are not restored by the present test count or by these area changes.
No manuscript rebuild or submission-ready claim is made by this delivery.

## Evidence and local-check scope

Primary repository sources at reviewed commit: i2_domain_integration_031.py;
i1_confirmation_031.py; pathdomain2.py; I0 RESOURCE_LEDGER_031.json; I2
DOMAIN_INTEGRATION_031_RETURN.md and COMPLETION.json; and the I2 output tree.
The supplied manuscript is an older claim record, not the new numerical evidence.
The attached independent script tests simple exact intervals, a radial-polynomial
expansion and synthetic planning records. It does not execute the campaign's
production code, identify the cause of all 66 reference cases, or certify any real
emitting area. Its executable preflight can be used on a newly prepared JSON plan.
