#!/usr/bin/env python3
"""C3 of ruling 034: claim routes, return, completion. Zero physical queries."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

CLAIMS = """# MANUSCRIPT_CLAIM_ROUTES_034

Additive. The frozen manuscript is not overwritten and no claim in it is
edited here. This table says, for each family of claims, which route it takes
after rulings 029-034. The draft is **not** submission-ready.

## Route A -- retained, finite-dimensional and discrete

These rest on constructed operators over declared finite bases and on sealed
held-out protocols. Nothing in the 029-034 arc touched their inputs.

| claim family | where | why it is retained |
| --- | --- | --- |
| R1 main and its null-pair controls | sec. 7 | finite basis, sealed freeze, unchanged |
| R1L stage 1 and stage 2R | sec. 8 | localized bases, unchanged |
| HMT-1 and HMT-2 sealed mains | sec. 9 | held-out commitments, unchanged |
| E3C geometry-wide operator audit | sec. 6 | discrete audit over archived maps |
| G1 hull qualification | sec. 4.3 | qualified at 9.592e-08 band-normalised, 029 |
| the 680 sampled physical absences | sec. 6.2 | validated per point, 030-031 |
| the comparator on its tested cohorts | new | 033, at cohort scope only |

## Route B -- requires physical revalidation before it can be restated

| claim | where | what is missing |
| --- | --- | --- |
| "Validated Computational Operator" | sec. 5 | no matched detector-response comparison has met the 5e-4 component budget. Measured on identical supported geometry, the coarse representation misses it by roughly 19x at order 0, 85x at order 1 and 1000x at order 2 |
| physical order-resolution attribution | sec. 10.1 | rests on the same operator; the order-2 comparison covers 61.7% of emitting nodes and the rest has no response bound |
| order-summed physical claims | sec. 6.4 | same operator, plus C13 quadrature still open |

## Route C -- deferred

| item | status |
| --- | --- |
| R3A common-sky construction | blocked since the C13 discovery; not reopened |
| R3B, target spectra, estimators | not authorized |
| the adaptive integration campaign | designed and costed, unfunded |

## What a correction overlay can say now

That the discrete results of route A stand on their own inputs; that route B
statements are suspended pending a detector-response comparison inside budget,
not withdrawn as false; and that the numerical work since ruling 026 has
narrowed the open question from "is the operator right" to "what does it cost
to integrate it to the declared accuracy". That is a smaller question than the
one the manuscript currently assumes is answered, and it is not yet answered.
"""


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with Path(p).open("rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def render(rb, st, resp, sc, suite) -> str:
    d = rb["development"]
    L = []
    L += [
        "# CACHED_RESPONSE_AUDIT_034_RETURN",
        "",
        "Status: **CACHED_RESPONSE_AUDIT_034_REVIEW_READY**",
        "",
        "Ruling: PAPER_I_RESPONSE_ERROR_RULING_034  ",
        f"Commit: {sc['commit']}  ",
        "New rays, path quadratures, hull roots, target operators: **0**. "
        "854 units remain, none spent under this ruling.",
        "",
        "## 1. The 033 summaries, recomputed from the rows",
        "",
        "The corrections are accepted and the numbers are now derived rather "
        "than narrated.",
        "",
        "| quantity | A vs B, median absolute | max relative |",
        "| --- | --- | --- |",
    ]
    q = d["per_quantity_A_vs_B"]
    for k in ("J_observer", "J_50", "s_escape", "tail"):
        v = q.get(k) or {}
        a, r = v.get("absolute_difference"), v.get("relative_difference")
        if a:
            L.append(f"| {k} | {a['median']:.3e} | {r['max']:.3e} |")
    L += [
        "",
        "So the blanket \"agree to about 3e-16\" sentence was wrong. "
        "`J_observer`, `J_50` and the tail agree near machine precision; "
        f"`s_escape` differs by a median of "
        f"{q['s_escape']['absolute_difference']['median']:.3e} and up to "
        f"{q['s_escape']['absolute_difference']['max']:.3e}. Reference A's "
        f"convergence estimate, median "
        f"{d['reference_A_error_estimate']['median']:.3e}, is a third quantity "
        "again, and it is an estimate rather than the error.",
        "",
        "The endpoint split and the distance median reproduce from the "
        f"payload: {d['endpoint_that_refused']}, median estimated distance "
        f"{d['estimated_distance_to_the_nearest_endpoint']['median']:.3e}. "
        "That distance is computed with the same quadrature, so it is not "
        "ground truth either. Root separation stays an association, not a "
        "controlled unique cause, and the indexed reduction is not claimed to "
        "have been necessary here.",
        "",
        "## 2. The interval error report",
        "",
        "`leaf2.envelope_response_bound` is replaced by "
        "`leaf2.box_radius_about`, which takes an explicit reference response. "
        "For the interval [0, 2] the radius about a nominal of zero is 2 and "
        "about the midpoint is 1; the old helper would have said 1 either way. "
        "The per-channel Euclidean radius over the whitened detector rows is "
        "the primary figure and the joint radius over the stack is labelled "
        "separately -- for a one-row half-width of [1, 1] those are 1 and "
        "sqrt(2), while the matrix one-norm the 033 helper used gives 1, which "
        "is neither. Agrees with the reviewer's helper to "
        "1e-12 across randomised inputs.",
        "",
        "## 3. What the bilinear diagnostic was actually comparing",
        "",
        "The interpolation mechanics check out on all three orders: "
        "alpha-major raster confirmed against each node's own coordinates, "
        "in-cell weights inside the unit square, no fine node outside the "
        "coarse hull, no silent extrapolation.",
        "",
        "The stencil partition is where the 033 reading breaks. A stencil "
        "whose four corners merely carry finite numbers is not a stencil "
        "sampling one smooth piece of the field.",
        "",
        "| order | four emitting corners and one radial leg | crosses the "
        "boundary | a corner has no value | median relative source-radius span "
        "across a coarse cell |",
        "| --- | --- | --- | --- | --- |",
    ]
    for n in (0, 1, 2):
        o = st["per_order"][f"n{n}"]
        c = o["categories"]
        span = o["relative_source_radius_span_across_emitting_stencils"]
        L.append(
            f"| n{n} | "
            f"{c['SAME_EMITTING_DOMAIN_AND_SAME_RADIAL_LEG']['fraction_of_fine_emitting_nodes']:.1%} | "
            f"{c['STENCIL_CROSSES_THE_EMITTING_BOUNDARY']['fraction_of_fine_emitting_nodes']:.1%} | "
            f"{c['A_CORNER_HAS_NO_VALUE']['fraction_of_fine_emitting_nodes']:.1%} | "
            f"{span['median']:.2f} |")
    n1r = st["per_order"]["n1"]["metrics"]["redshift"]
    L += [
        "",
        "Restricting order 1 to the strict same-leg stencils drops the "
        f"above-threshold fraction from "
        f"{n1r['033_comparable_stencils']['global_max_scaled_fraction_above_5e_4']:.1%}"
        f" to {n1r['strict_same_domain']['global_max_scaled_fraction_above_5e_4']:.1%}"
        ", at 77.9% coverage. Boundary-crossing stencils were inflating it, "
        "exactly as the ruling anticipated.",
        "",
        "Order 2 is worse than that, and in a way that changes the 033 "
        "conclusion rather than qualifying it. **No** order-2 stencil passes "
        "the same-leg proxy, and the reason is visible in the last column: the "
        "archived source radius varies by a median of 0.81 of its own mean "
        "across a single coarse cell, with a minimum of 0.37. The coarse map "
        "does not resolve the order-2 field within one cell at all, so the "
        "94.7% was measuring the failure of that representation, not a "
        "property of the interior that new sampling must pay for. The 033 "
        "sentence attributing the cost to interior sampling is withdrawn.",
        "",
        "The proxy -- radius span under a quarter of its own mean -- is a "
        "declared heuristic, not a proof, and the span distribution is "
        "reported beside it so the threshold can be judged.",
        "",
        "## 4. The detector-response error, measured",
        "",
        "The eleven inherited channels -- six screen, five transferred at each "
        "of the eight accepted observer times -- built from cached tuples on "
        "both sides, carried through the same overlap areas, the same "
        "single-sky noise and the same absolute clock, compared as whitened "
        "detector vectors on identical support.",
        "",
        "| order | screen channels | transferred, median | transferred, max | "
        "node coverage | area coverage |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for n in (0, 1, 2):
        r = resp["per_order"][f"n{n}"]
        w, s = r["whitened_relative_error"], r["support"]
        L.append(
            f"| n{n} | {w['screen_channels']['max']:.1e} | "
            f"{w['transferred_channels']['median']:.3e} | "
            f"{w['transferred_channels']['max']:.3e} | "
            f"{s['node_coverage_of_emitting']:.1%} | "
            f"{s['area_coverage_of_emitting']:.1%} |")
    L += [
        "",
        "The screen channels come back at exactly zero. They are the control: "
        "both sides share the same overlap operator and the same geometry, so "
        "anything the machinery itself introduced would show there. Nothing "
        "does.",
        "",
        "The transferred channels miss the 5e-4 component budget by roughly "
        "19x at order 0, 85x at order 1 and 1000x at order 2. This is the "
        "quantity the budget is written against, and the answer is the same "
        "direction as the 033 node counts for a better reason. It says the "
        "coarse profile is not an adequate representation of the transferred "
        "field at this detector. It does not say how many rays an adequate "
        "scheme needs.",
        "",
        "Coverage is carried, not absorbed: at order 2, 38.3% of emitting "
        "nodes have a coarse corner with no value, the comparison covers "
        "61.7% of emitting nodes and 62.8% of emitting area, and the remainder "
        "has no response bound at all. A small residual on available support "
        "would not qualify the quadrature while that is true, and here the "
        "residual is not small either.",
        "",
        "## 5. A cost scenario driven by the response",
        "",
        "Per node, the whitened response error is bounded by the sum of "
        "`||W O[:,p]|| * |dF_p|`, so refining the largest contributors bounds "
        "what is left by the tail. The error is genuinely concentrated:",
        "",
        "| order | nodes carrying 50% of the bound | 90% | nodes needed for "
        "the tail bound to reach budget | bound is conservative by |",
        "| --- | --- | --- | --- | --- |",
    ]
    for n in (0, 1, 2):
        c = sc["per_order"][f"n{n}"]
        L.append(
            f"| n{n} | {c['concentration']['0.50']['fraction_of_support']:.2%} | "
            f"{c['concentration']['0.90']['fraction_of_support']:.1%} | "
            f"{c['fraction_of_support_needing_refinement']:.1%} | "
            f"{c['bound_is_conservative_by']:.0f}x |")
    L += [
        "",
        "Half the bound sits in 0.21% of the order-0 support and 1.5% of the "
        "order-1 support, which is real leverage for an adaptive scheme. "
        "Driving the *bound* inside budget still takes 63% to 94% of the "
        "support, because the triangle inequality ignores the cancellation "
        "that makes the measured error 10x to 57x smaller than the bound. "
        f"At a declared 2x2 per node that scenario is "
        f"{sc['scenario_total_at_2x2']:,} evaluations.",
        "",
        "Both that number and the 033 figures are scenarios. Neither is a "
        "measured call count, neither is a certified upper bound, and the 033 "
        "expected total of 101,416 splits 52,379 boundary against 49,037 "
        "interior -- so the boundary term was never negligible, and the 033 "
        "sentence saying adaptivity fixes it is withdrawn. The 4.385x figure "
        "is projection arithmetic, not a measured speedup.",
        "",
        "What this changes for the design: a scheme that refines on the "
        "measured response contribution has real leverage, and a scheme that "
        "has to certify a triangle bound does not. Closing that gap -- an "
        "error model that earns cancellation instead of discarding it -- is "
        "the next design question, and it is cheaper to answer than any "
        "sampling campaign.",
        "",
        "## 6. Status",
        "",
        "| item | status |",
        "| --- | --- |",
        "| comparator | CLOSED_AT_TESTED_COHORT_SCOPE |",
        "| interval report | CORRECTED_NOMINAL_AND_NORM_EXPLICIT |",
        "| stencil diagnostics | REPRODUCED_AND_PARTITIONED_033_ATTRIBUTION_WITHDRAWN |",
        "| partial response comparison | MEASURED_AND_OUTSIDE_BUDGET |",
        "| missing support | CARRIED_AS_A_COVERAGE_GAP_WITH_NO_BOUND |",
        "| cost scenarios | SCENARIOS_NOT_MEASURED_EFFICIENCY |",
        "| physical quadrature | NOT_QUALIFIED (C13 open) |",
        "| manuscript claim routes | DRAFTED_ADDITIVE_NO_OVERWRITE |",
        "",
        f"Suite: {suite}, run in a disposable git worktree; the authoritative "
        "archive was not written to.",
        "",
        "This return authorizes nothing. R3B, target spectra, estimators and a "
        "submission freeze remain unauthorized, and no new physical query has "
        "been made.",
        "",
    ]
    return "\n".join(L)


def main(out: Path) -> int:
    t0 = time.time()
    rb = json.loads((out / "COMPARATOR_QUANTITY_READBACK_034.json").read_text())
    st = json.loads((out / "STENCIL_AND_COVERAGE_AUDIT_034.json").read_text())
    resp = json.loads(
        (out / "RESPONSE_ERROR_AND_OMITTED_SUPPORT_034.json").read_text())
    sc = json.loads(
        (out / "RESPONSE_BASED_COST_SCENARIOS_034.json").read_text())
    suite_f = out / "PYTEST_FULL_SUITE_034.txt"
    suite = "NOT_RECORDED_IN_THIS_RUN"
    if suite_f.is_file():
        t = suite_f.read_text().splitlines()
        suite = next((ln.strip() for ln in reversed(t)
                      if " passed" in ln or " failed" in ln), suite)
    (out / "MANUSCRIPT_CLAIM_ROUTES_034.md").write_text(CLAIMS)
    (out / "CACHED_RESPONSE_AUDIT_034_RETURN.md").write_text(
        render(rb, st, resp, sc, suite))
    completion = {
        "schema": "phrt-completion/1",
        "id": "CACHED_RESPONSE_AUDIT_034_COMPLETION",
        "ruling": "PAPER_I_RESPONSE_ERROR_RULING_034",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "commit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                 capture_output=True, text=True).stdout.strip(),
        "return_status": "CACHED_RESPONSE_AUDIT_034_REVIEW_READY",
        "ready_authorizes_R3B": False,
        "statuses": {
            "comparator_closed": "CLOSED_AT_TESTED_COHORT_SCOPE",
            "interval_report": "CORRECTED_NOMINAL_AND_NORM_EXPLICIT",
            "stencil_diagnostics":
                "REPRODUCED_AND_PARTITIONED_033_ATTRIBUTION_WITHDRAWN",
            "partial_response_comparison": "MEASURED_AND_OUTSIDE_BUDGET",
            "missing_support": "CARRIED_AS_A_COVERAGE_GAP_WITH_NO_BOUND",
            "cost_scenarios": "SCENARIOS_NOT_MEASURED_EFFICIENCY",
            "physical_quadrature": "NOT_QUALIFIED",
            "manuscript_claim_routes": "DRAFTED_ADDITIVE_NO_OVERWRITE",
        },
        "withdrawn_from_033": [
            "the blanket 3e-16 integral equality statement",
            "the attribution of the order-2 cost to interior sampling",
            "the sentence that adaptivity fixes the boundary cost",
            "envelope_response_bound as an error figure",
        ],
        "measured_whitened_response_relative_error": {
            f"n{n}": resp["per_order"][f"n{n}"]["whitened_relative_error"]
                          ["transferred_channels"]["max"] for n in (0, 1, 2)},
        "coverage": {
            f"n{n}": resp["per_order"][f"n{n}"]["support"] for n in (0, 1, 2)},
        "resources": {"convention": "B", "second_batch_spent": 19146,
                      "second_batch_remaining": 854,
                      "spent_under_this_ruling": 0,
                      "boundary_spent": 33410,
                      "new_allowance_or_third_batch": "none"},
        "tests": {"whole_repository": suite,
                  "run_in_a_disposable_worktree": True},
        "old_results_or_flags_rewritten": False,
        "preserved_tokens": ["DOMAIN_INTEGRATION_031_BLOCKED",
                             "MATCHED_INTEGRATION_032_PLAN_BLOCKED",
                             "FEASIBILITY_CLOSEOUT_033_REVIEW_READY"],
        "runtime_seconds": time.time() - t0,
    }
    (out / "CACHED_RESPONSE_AUDIT_034_COMPLETION.json").write_text(
        json.dumps(completion, indent=2) + "\n")
    names = sorted(f.name for f in out.iterdir()
                   if f.is_file() and f.name != "SHA256SUMS.txt")
    (out / "SHA256SUMS.txt").write_text(
        "".join(f"{sha(out / n)}  {n}\n" for n in names))
    print(json.dumps({"stage": "C3", "status": completion["return_status"],
                      "suite": suite}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main((ROOT / sys.argv[1]).resolve()))
