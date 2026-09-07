# INTERPRETATION_OVERLAY_032

Ruling: PAPER_I_MATCHED_INTEGRATION_RULING_032
Reviewed commit: e9924705285d04fd282758de640a916044e987c7
Disposition accepted: BLOCK_ACCEPTED_LEAF_GEOMETRY_AND_COMPARISON_PREFLIGHT_REQUIRED

This overlay is additive. No file written under rulings 029, 030 or 031 is
edited, and the 031 return keeps its literal token
`DOMAIN_INTEGRATION_031_BLOCKED`. What follows re-labels the meaning of numbers
that are already on the record.

## 1. What I2 actually computed

I2 evaluated four sub-points inside each selected transition cell, averaged
their labels into a per-parent number, and multiplied that number by the
*parent's* overlap:

    chi[parent] = mean(subpoint_labels)
    y[detector] += old_overlap[detector, parent] * chi[parent]

That is the substitution ruling 027 rejected, reintroduced. It conserves the
total and misplaces the image: a unit cell emitting only on its leftmost fifth
and straddling two half-width pixels owes (0.2, 0) and this rule pays
(0.1, 0.1). The kernel canary of 027 was not bypassed by accident -- I2 never
routed through the geometry the canary protects.

| 031 field | corrected reading |
| --- | --- |
| `chi[parent]` | UNQUALIFIED_PARENT_AVERAGED_OCCUPANCY_PROXY |
| the single response column | constant occupancy for f = 1, not the full transferred response |
| `domain_change_relative` (3.853e-03 core n0, 1.854e-03 core n1) | difference between two approximations, not an error against the physical integral |
| `unresolved_area_fraction` = 0.0 | SAMPLED_EVALUATOR_UNRESOLVED_AREA_PROXY: zero failed point evaluations in the sampled sub-cells, not a bound on uncertain boundary area |
| `transition_cells_found` | the count **after** greedy truncation, not the number discovered |
| core n2, fine n0, fine n1, fine n2 rows | NOT_EVALUATED -- not zero error, not zero unresolved support, not "no transition cells" |
| `response_relative` in `profile_pairs` | \|norm(y_fine)\| - \|norm(y_core)\| over norm(y_fine): a difference of norms, which two completely different images can make zero |

The correct statement of what the 3.853e-03 and 1.854e-03 measure: the total
estimated emitting area moves by that much between the centre-indicator
representation and the four-sample occupancy proxy, on the transition cells
that were reached. It is a sensitivity of the numerical representation. It is
not evidence that either rule is right, and it is not a proven transfer error.

The unit is also not the one it was compared against. The 5e-4 criterion is
the whitened transfer/emission **response** component; the registered budget
for total area and mask is 1e-3. Both figures exceed 1e-3 as areas, so
domain-aware integration still looks necessary -- but that conclusion now rests
on an area comparison against the area budget, not on the response budget.

## 2. What I1 established and what it did not

The 428 agreeing cases stand. The 66 disagreements are reference
non-convergence, not label conflicts, and they are equally not successful
independent confirmations. Until they are bounded or prospectively excluded by
scope, they do not clear a launch condition for a full-domain campaign. That
matters most for order 2, where 62 of the 66 sit and where nothing else has
been tested.

| 031 field | corrected reading |
| --- | --- |
| `points_cap` = 192 with `points` = 494 | a 302-point overrun; the cap was recorded and never enforced |
| `charged_cap` = 1024 | the evaluation ceiling; the native charge is 494 |
| `max_polynomial_residual` = 0.0 | tautological: prod_j (z_i - z_j) contains the factor j = i and is zero for any list at all |
| panel provenance | the new 494 records keep their own narrower statement -- comparator not tuned on this panel, prior 030 indices excluded. The label PRECOMMITTED_PANEL_REUSED_AFTER_COMPARATOR_CORRECTION belongs to the 880-point 030 panel and is not transferred to them |
| `methods_agree` = 428 | agreement where the reference resolved; the confirmation is incomplete, not passed |

Only 10 of the 66 disagreement records were exported with their detail, and
none of them carries the reference's reason code, integral value or convergence
estimate. Those were discarded at write time and cannot be recovered without
recomputation, which is not authorized here.

## 3. Governance

The 031 governance line read `COMPLETE`. It is corrected to
AUDIT_COMPLETE_WITH_PROTOCOL_DEVIATIONS, with four deviations preserved on the
record: the admitted allocation error, the 302-point cap overrun, the unmet
reference-confirmation gate, and the partial and mismatched comparison. The
607-test result of 031 remains a reported test result; it did not test any of
these properties, and the fault injections added under this ruling are what
now do.

## 4. Accounting

Accepted as corrected: 7,072 native before 031, 6,494 during 031, 13,566 in the
second batch, 6,434 reported remaining on the native-only convention. That
balance is the *reported* native figure and not an authorization to spend. The
end-to-end convention -- whether an independent reference integration is its
own metered evaluation or cached algebra -- is reconciled in
FULL_COST_RESOURCE_LEDGER_032.json, and the 4,000 response-validation reserve
is preserved untouched pending it.

## 5. Manuscript

Section 5's "Validated Computational Operator" statement and the order-
resolution attribution in section 10.1 are not restored by this delivery.
Equation (2) has chi multiplying the full transferred source response; a
constant occupancy column cannot validate that operator, and no run under 031
or 032 has produced a matched comparison that could. No manuscript rebuild and
no submission-ready claim is made here.
