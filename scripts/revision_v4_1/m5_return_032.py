#!/usr/bin/env python3
"""M5 of ruling 032: the resource ledger and the return. Zero physical queries.

The ledger reconciles the second-batch spend under both counting conventions
rather than picking the flattering one. The return states the exact missing
physical prerequisite and the full cost of the comparison, and it launches
nothing.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REV = ROOT / "artifacts" / "revisions" / "mahakal_v4_1"

SECOND_BATCH_CAP = 20000
LIFETIME_TRANSFER_CAP = 250000
VALIDATION_RESERVE = 4000
BOUNDARY_SPENT = 33410
BOUNDARY_REMAINING = 890

# Every second-batch execution, from its own attempt ledger, with the
# component counters the ruling requires kept apart.
EXECUTIONS = [
    {"run": "T1_20260907T074927Z_3b1e6b9", "ruling": "029", "native_trace": 120,
     "primary_path": 0, "independent_reference": 0,
     "outcome": "aborted on a guard error; ledger written, no result file"},
    {"run": "T1_20260907T074951Z_3d42022", "ruling": "029", "native_trace": 480,
     "primary_path": 0, "independent_reference": 0,
     "outcome": "completed"},
    {"run": "T1_20260907T075031Z_c35cb34", "ruling": "029", "native_trace": 1080,
     "primary_path": 0, "independent_reference": 0,
     "outcome": "completed; revisited the cohort of the previous execution"},
    {"run": "T1_20260907T075138Z_1113f3e", "ruling": "029", "native_trace": 1080,
     "primary_path": 0, "independent_reference": 0,
     "outcome": "completed; revisited the cohort of the previous execution"},
    {"run": "D1_20260907T101654Z_57fae0f", "ruling": "030", "native_trace": 2156,
     "primary_path": 2156, "independent_reference": 2156,
     "outcome": "completed; 1276 development and 880 holdout points"},
    {"run": "D1B_20260907T102020Z_5c1cb6a", "ruling": "030", "native_trace": 2156,
     "primary_path": 2156, "independent_reference": 2156,
     "outcome": "completed; re-executed the same cohort after the comparator "
                "correction"},
    {"run": "I1_20260907T170719Z_a9d3f1d", "ruling": "031", "native_trace": 494,
     "primary_path": 494, "independent_reference": 494,
     "outcome": "completed; 988 reference quadrature calls inventoried"},
    {"run": "I2_20260907T170816Z_4968a3d", "ruling": "031", "native_trace": 6000,
     "primary_path": 6000, "independent_reference": 0,
     "outcome": "completed; cap exhausted on core orders 0 and 1"},
]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def ledger() -> dict:
    native = sum(e["native_trace"] for e in EXECUTIONS)
    primary = sum(e["primary_path"] for e in EXECUTIONS)
    reference = sum(e["independent_reference"] for e in EXECUTIONS)
    a_rem = SECOND_BATCH_CAP - native
    b_spent = native + reference
    b_rem = SECOND_BATCH_CAP - b_spent
    return {
        "executions": EXECUTIONS,
        "component_counters": {
            "native_trace": native,
            "primary_path_integration": primary,
            "independent_reference_integration": reference,
            "re_executions_over_an_already_evaluated_cohort": [
                "T1_20260907T075031Z_c35cb34", "T1_20260907T075138Z_1113f3e",
                "D1B_20260907T102020Z_5c1cb6a"],
            "cached_algebra_this_ruling": {
                "quartic_root_solves_on_archived_screen_coordinates": 494,
                "synthetic_fixture_solves": 1000,
                "note": "algebra on archived coordinates; no ray, no path "
                        "integral, not charged against the transfer batch"},
            "quadrature_abscissa_counted_as_a_new_ray": False,
            "independent_end_to_end_evaluation_counted_as_cached_algebra":
                False,
        },
        "convention_A_native_only": {
            "definition": ("one metered evaluation = one screen/order "
                           "evaluation of the pinned tracer; the primary path "
                           "integration and any reference quadrature ride "
                           "inside it"),
            "second_batch_spent": native,
            "second_batch_remaining": a_rem,
            "spendable_after_the_reserve": a_rem - VALIDATION_RESERVE,
            "status": "the convention in force through 029-031",
        },
        "convention_B_independent_reference_metered": {
            "definition": ("an independent end-to-end reference evaluation is "
                           "its own metered evaluation, per ruling 032's "
                           "'independent_end_to_end_evaluation_is_cached_"
                           "algebra: false'"),
            "second_batch_spent": b_spent,
            "second_batch_remaining": b_rem,
            "spendable_after_the_reserve": b_rem - VALIDATION_RESERVE,
            "consequence": ("under this convention the second batch has "
                            f"{b_rem} left, which is less than the "
                            f"{VALIDATION_RESERVE} response-validation "
                            "reserve: nothing is spendable at all"),
        },
        "authoritative_balance": "UNRESOLVED_PENDING_REVIEWER_CHOICE_OF_CONVENTION",
        "reported_native_balance_is_not_a_spending_authorization": True,
        "validation_reserve_preserved": VALIDATION_RESERVE,
        "validation_reserve_touched_this_ruling": False,
        "second_batch_cap": SECOND_BATCH_CAP,
        "transfer_lifetime_cap": LIFETIME_TRANSFER_CAP,
        "boundary_spent": BOUNDARY_SPENT,
        "boundary_remaining": BOUNDARY_REMAINING,
        "new_boundary_calls": 0,
        "new_physical_queries_this_ruling": 0,
        "new_path_integral_recomputations_this_ruling": 0,
        "new_hull_roots_this_ruling": 0,
        "third_batch": "not authorized",
        "new_allowance_granted_by_032": "none",
        "accounting_definition_changed_silently": False,
        "peak_GiB_envelope": 8,
        "elapsed_time_envelope": "inherited cumulative; not reset by this ruling",
    }


def full_suite(path: Path | None) -> dict:
    """The whole repository suite, recorded from its own separate execution.

    The run is not launched from inside this stage: the suite loads several
    large archived maps and the report writer should not be sharing a process
    footprint with it. Its transcript is passed in and quoted verbatim.
    """
    if path is None or not Path(path).is_file():
        return {"command": "python3 -m pytest tests -q",
                "summary": "NOT_RECORDED_IN_THIS_RUN", "passed": None,
                "tests_this_ruling_added_are_included": True}
    text = Path(path).read_text()
    tail = next((ln.strip() for ln in reversed(text.splitlines())
                 if " passed" in ln or " failed" in ln or " error" in ln), "")
    return {"command": "python3 -m pytest tests -q", "summary": tail,
            "passed": (" failed" not in tail and " error" not in tail
                       and " passed" in tail),
            "transcript": str(Path(path).name),
            "tests_this_ruling_added_are_included": True}


def main(out: Path, suite: Path | None = None) -> int:
    t0 = time.time()
    plan = json.loads((out / "MATCHED_COMPARISON_PLAN_032.json").read_text())
    pre = json.loads((out / "PLAN_PREFLIGHT_032.json").read_text())
    leafrec = json.loads((out / "LEAF_ASSEMBLY_CONSUMER_TESTS_032.json").read_text())
    comp = json.loads((out / "COMPARATOR_STATIC_DIAGNOSTICS_032.json").read_text())
    cache = json.loads((out / "CACHE_AND_PAYLOAD_INVENTORY_032.json").read_text())
    led = ledger()
    (out / "FULL_COST_RESOURCE_LEDGER_032.json").write_text(
        json.dumps(led, indent=2) + "\n")

    cen = plan["metadata"]["census"]
    full_cost = plan["metadata"]["full_domain_cost"]
    local_cost = plan["metadata"]["local_cost"]
    spendable_A = led["convention_A_native_only"]["spendable_after_the_reserve"]
    spendable_B = led["convention_B_independent_reference_metered"][
        "spendable_after_the_reserve"]

    blocked = True
    completion = {
        "schema": "phrt-completion/1",
        "id": "MATCHED_INTEGRATION_032_COMPLETION",
        "ruling": "PAPER_I_MATCHED_INTEGRATION_RULING_032",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "commit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                 capture_output=True, text=True).stdout.strip(),
        "return_status": "MATCHED_INTEGRATION_032_PLAN_BLOCKED",
        "token_is_query_authorization": False,
        "statuses": {
            "leaf_kernel_tests": "IMPLEMENTED_AND_VERIFIED_ON_ARCHIVED_GEOMETRY",
            "comparator_static_checks":
                "TAUTOLOGY_REPLACED_REDUCTION_CORRECTED_CAUSE_NOT_ESTABLISHED",
            "payload_availability":
                "031_SUB_EVALUATION_VALUES_ARE_UNRECOVERABLE",
            "complete_comparison_plan":
                "COSTED_BOTH_SCOPES_NEITHER_LAUNCHABLE",
            "resource_accounting":
                "RECONCILED_UNDER_TWO_CONVENTIONS_BALANCE_UNRESOLVED",
            "governance": "AUDIT_COMPLETE_WITH_PROTOCOL_DEVIATIONS",
        },
        "blockers": [
            {"id": "REFERENCE_CONFIRMATION_INCOMPLETE",
             "what": ("66 of 494 primary-reference comparisons did not "
                      "resolve, 62 of them at order 2, and no validated bound "
                      "or prospectively justified scope exclusion exists"),
             "why_it_blocks": ("order 2 is a required endpoint of the matrix; "
                              "the launch condition cannot be met for any "
                              "compliant plan"),
             "cost_to_clear": {"re_adjudication_of_the_66": 66,
                               "fresh_holdout_within_the_192_point_cap": 192,
                               "total_new_evaluations": 258},
             "authorization_needed": "new physical queries; forbidden by 032"},
            {"id": "ORDER2_MISSING_TRANSFER_SUPPORT",
             "what": ("cells whose dual overlaps the order-2 band but whose "
                      "archived centre ray has no usable transfer datum carry "
                      f"{cen['core_n2']['unresolved_support_area_fraction']:.1%}"
                      " of the core band area and "
                      f"{cen['fine_n2']['unresolved_support_area_fraction']:.1%}"
                      " of the fine band area"),
             "why_it_blocks": ("an unresolved support fraction of that size is "
                               "orders of magnitude above the 1e-3 area budget "
                               "and the 5e-4 response budget, so no order-2 "
                               "comparison could be qualified even if it ran"),
             "cost_to_clear": "not costable without new sampling of those cells",
             "authorization_needed": "new physical queries; forbidden by 032"},
            {"id": "ACCOUNTING_CONVENTION_UNRESOLVED",
             "what": ("the second batch has "
                      f"{led['convention_A_native_only']['second_batch_remaining']}"
                      " left under the native-only convention and "
                      f"{led['convention_B_independent_reference_metered']['second_batch_remaining']}"
                      " under the convention 032 states for independent "
                      "end-to-end reference evaluations"),
             "why_it_blocks": ("under the second convention the remaining "
                               "balance is already below the 4000 validation "
                               "reserve, so nothing is spendable; which "
                               "convention governs is the reviewer's call"),
             "cost_to_clear": 0,
             "authorization_needed": "a ruling on the convention"},
            {"id": "NO_AFFORDABLE_NON_DEGENERATE_LOCAL_REGION",
             "what": ("on the declared wedge ladder, every region that fits "
                      f"the {spendable_A} spendable evaluations contains zero "
                      "transition parents at order 0, and the smallest region "
                      "that has something to measure at all six endpoints "
                      f"(half-width "
                      f"{plan['metadata']['smallest_non_degenerate_wedge_deg']}"
                      f" deg) costs {local_cost}"),
             "why_it_blocks": ("a local diagnostic that measures nothing at an "
                               "endpoint is not a cheaper comparison, it is an "
                               "empty one; the fallback scope is therefore not "
                               "available either"),
             "cost_to_clear": local_cost,
             "authorization_needed": "an allowance 032 does not grant"},
            {"id": "FULL_DOMAIN_MATRIX_EXCEEDS_EVERY_ALLOWANCE",
             "what": (f"the 18-endpoint full-domain matrix costs {full_cost} "
                      "new evaluations"),
             "why_it_blocks": (
                 f"that is {full_cost / max(spendable_A, 1):.0f} times the "
                 f"{spendable_A} spendable under the more generous convention, "
                 f"and {full_cost / LIFETIME_TRANSFER_CAP:.2f} times the entire "
                 f"{LIFETIME_TRANSFER_CAP} lifetime transfer cap"),
             "cost_to_clear": full_cost,
             "authorization_needed": "an allowance 032 explicitly does not grant"},
        ],
        "costs": {
            "full_domain_matrix": full_cost,
            "local_feasibility_matrix": local_cost,
            "local_matrix_fits_spendable":
                plan["metadata"]["local_plan_fits_spendable"],
            "smallest_non_degenerate_wedge_deg":
                plan["metadata"]["smallest_non_degenerate_wedge_deg"],
            "spendable_convention_A": spendable_A,
            "spendable_convention_B": spendable_B,
            "lifetime_transfer_cap": LIFETIME_TRANSFER_CAP,
        },
        "preflight": {
            "as_returned": pre["results"]["as_returned"]["status"],
            "as_returned_errors": pre["results"]["as_returned"]["errors"],
            "prerequisite_stipulated_met":
                pre["results"]["prerequisite_stipulated_met"]["status"],
            "full_domain_matrix": pre["results"]["full_domain_matrix"]["errors"],
            "schema_pass_authorizes_execution": False,
        },
        "tests": {"new_032_files": leafrec["tests"],
                  "whole_repository": full_suite(suite)},
        "new_physical_queries": 0,
        "old_results_or_flags_rewritten": False,
        "old_blocked_token_preserved": "DOMAIN_INTEGRATION_031_BLOCKED",
        "stop_for_review_before_any_new_physical_query": True,
        "runtime_seconds": time.time() - t0,
    }
    (out / "MATCHED_INTEGRATION_032_COMPLETION.json").write_text(
        json.dumps(completion, indent=2) + "\n")

    md = render(completion, plan, led, leafrec, comp, cache, cen)
    (out / "MATCHED_INTEGRATION_032_RETURN.md").write_text(md)

    names = sorted(f.name for f in out.iterdir()
                   if f.is_file() and f.name != "SHA256SUMS.txt")
    (out / "SHA256SUMS.txt").write_text(
        "".join(f"{sha256(out / n)}  {n}\n" for n in names))
    print(json.dumps({"stage": "M5",
                      "status": completion["return_status"],
                      "full_cost": full_cost, "local_cost": local_cost,
                      "spendable_A": spendable_A, "spendable_B": spendable_B}))
    return 0


def render(c, plan, led, leafrec, comp, cache, cen) -> str:
    g = leafrec["archived_geometry"]["leaf_vs_parent_fraction"]
    u = comp["unresolved_reference_conditioning"]["groups"]
    reg = plan["metadata"]["region"]
    rows = []
    for n in (0, 1, 2):
        for prof in ("core", "fine"):
            r = cen[f"{prof}_n{n}"]
            rows.append(
                f"| {prof} n{n} | {r['cells_total']} | {r['transition_found']} "
                f"| {r['unresolved_support_area_fraction']:.2%} | "
                f"{r['transition_found'] * 4} | {r['transition_found'] * 16} |")
    lines = [
        "# MATCHED_INTEGRATION_032_RETURN",
        "",
        f"Status: **{c['return_status']}**",
        "",
        "Ruling: PAPER_I_MATCHED_INTEGRATION_RULING_032  ",
        f"Commit: {c['commit']}  ",
        "New physical queries: **0**. No ray traced, no path integral "
        "recomputed, no hull root solved, no target operator touched.",
        "",
        "## 1. Leaf assembly",
        "",
        "The response is now assembled leaf by leaf,",
        "",
        "    y_d = sum_p sum_(l in leaves(p)) |D_d ^ C_l ^ B_n| chi(xi_l) f(xi_l),",
        "",
        "with each child keeping its own detector and hull overlap. The "
        "parent-averaged occupancy proxy is implemented once, named "
        f"`{leafrec['forbidden_representation_id']}`, and refused by both the "
        "plan validator and the report writer.",
        "",
        "On the ruling's own counterexample the leaf rule pays "
        f"{leafrec['counterexample']['leaf_rule']} where the proxy pays "
        f"{leafrec['counterexample']['parent_fraction']}; the totals agree and "
        "the images do not.",
        "",
        "On archived order-0 core geometry -- real band, real hull, real cell "
        "measure -- refining every parent into four children leaves the "
        "overlap unchanged per (detector cell, parent) to "
        f"{leafrec['archived_geometry']['per_detector_cell_and_parent_max_residual']:.3e}. "
        "That is the check that separates a refinement of the integration from "
        "a change of the geometry, and a total-only check would not have made "
        "it: on a declared test domain the two rules differ by "
        f"{g['whitened_vector_residual']:.3e} in whitened vector residual while "
        f"the 031 metric -- the difference of norms -- reports "
        f"{g['norm_difference_metric_used_by_031']:.3e}, "
        f"{g['whitened_vector_residual'] / max(g['norm_difference_metric_used_by_031'], 1e-30):.1f} "
        "times smaller.",
        "",
        "Unresolved leaves are carried as an explicit (lower, known, upper) "
        "response rather than a boolean. A finite leaf label is not a domain "
        "certificate and zero unresolved samples is not zero boundary error; "
        "both are asserted in tests rather than in prose.",
        "",
        f"Nine fault injections run in the launch and report path: "
        + ", ".join(leafrec["fault_injections_implemented"]) + ". ",
        f"Suite, the three new files: {leafrec['tests']['summary']}. "
        f"Whole repository: {c['tests']['whole_repository']['summary']}.",
        "",
        "## 2. Comparator",
        "",
        "The 031 shared-input check was tautological. Over 2000 random "
        "quadruples the quantity it reported is exactly "
        f"{comp['tautological_residual']['max_over_2000_random_quadruples']:.1e}: "
        "it is zero for any list at all. Replaced by the original quartic built "
        "from the conserved quantities,",
        "",
        "    R(r) = r^4 + (a^2 - lam^2 - eta) r^2 + 2((lam - a)^2 + eta) r "
        "- a^2 eta,",
        "",
        "evaluated by complex Horner with a scale-aware backward residual. It "
        "detects a root perturbed by 1e-8 in 200 of 200 synthetic cases, where "
        "the old check reported zero.",
        "",
        "The turning-point reduction excluded its root by Python object "
        "identity. `classify_path` returns `max(ext)` as a plain float, so "
        "`q is not turn` is true for every element, the factor (r - turn) "
        "survives, and the reduced potential vanishes at the endpoint where "
        "the integrand peaks: on the analytic fixture the 031 form returns "
        f"{comp['endpoint_limit']['031_identity_excluded_product_at_the_turn']:.1f} "
        f"and the correct limit is {comp['endpoint_limit']['analytic_limit']:.2f}. "
        "The corrected reduction excludes by verified index and refuses a "
        "clustered or multiple turning root instead of returning a number. "
        "Frozen 031 code is unchanged; the correction is a separate candidate.",
        "",
        "A static association, offered as an association and not a diagnosis: "
        f"all {u['unresolved_reference']['n']} unresolved-reference points have "
        "an accessible turning root, and their turning root sits close to its "
        "neighbours -- median separation "
        f"{u['unresolved_reference']['turn_separation_quantiles']['median']:.3f} M, "
        f"maximum {u['unresolved_reference']['turn_separation_quantiles']['max']:.3f} M. "
        f"In the {u['agreeing_control']['n']} agreeing cases the median is "
        f"{u['agreeing_control']['turn_separation_quantiles']['median']:.3f} M "
        f"and {u['agreeing_control']['no_turning_root']} have no turning root "
        "at all. Every root in both groups is simple and solves the quartic to "
        f"{u['unresolved_reference']['max_backward_residual']:.1e}, so this is "
        "not a root-finding failure. It is consistent with the endpoint defect "
        "above and it does not establish the cause: I1 discarded the "
        "reference's reason codes and integral values at write time, and "
        "recovering them needs a recomputation this ruling does not authorize.",
        "",
        "## 3. Payloads",
        "",
        "The 031 integration pilot left summaries and ledgers only. Of its "
        "6000 charged sub-evaluations, **0** labels, transfer values or "
        "detector vectors survive anywhere -- inside the repository or outside "
        "it. Their screen coordinates can be reconstructed from the frozen "
        "selection rule, which recovers where the evaluations were and not "
        "what they returned. Any re-evaluation is a new charge. The 030 "
        "per-point adjudication arrays do survive "
        f"({cache['d030_adjudication_cache']['unique_points']} rows across two "
        "files, hashed here) but they are labels for the 030 cohort, not leaf "
        "labels on any refinement of this matrix.",
        "",
        "## 4. The comparison, costed",
        "",
        "Census of the archived geometry. Transition parents are cells whose "
        "emitting status differs from a neighbour and whose dual meets the "
        "band; the last two columns are the new evaluations an L1 and an L2 "
        "bundle would need.",
        "",
        "| endpoint | ray cells | transition parents | unresolved support "
        "(area) | L1 cost | L2 cost |",
        "| --- | --- | --- | --- | --- | --- |",
        *rows,
        "",
        f"Full 18-endpoint matrix: **{c['costs']['full_domain_matrix']} new "
        "evaluations**. The spendable balance is "
        f"{c['costs']['spendable_convention_A']} under the native-only "
        f"convention and {c['costs']['spendable_convention_B']} under the "
        "other -- a negative number, because that convention leaves less than "
        "the reserve itself -- and the entire lifetime transfer cap is "
        f"{c['costs']['lifetime_transfer_cap']}. The full-domain comparison "
        "does not fit in the remaining allowance, and it does not fit in the "
        "lifetime cap either. I am saying so before the first query, as the "
        "ruling requires, rather than discovering it in a partial run.",
        "",
        "The fallback the ruling allows -- a complete local diagnostic with "
        "an explicit scope -- does not rescue it. The region family was fixed "
        "in the source before the census was read: a wedge of screen position "
        f"angle about {reg.get('centre_deg')} deg, the same region for both "
        "profiles, half-width taken from a fixed ladder.",
        "",
        "| half-width (deg) | cost | min transition parents | non-degenerate | "
        "fits spendable |",
        "| --- | --- | --- | --- | --- |",
        *[f"| {r['half_width_deg']:g} | {r['cost']} | "
          f"{r['min_transition_parents']} | {r['non_degenerate']} | "
          f"{r['fits_spendable']} |" for r in plan["metadata"]["wedge_ladder"]],
        "",
        "Every wedge that fits the spendable balance contains **zero** "
        "transition parents at order 0, in both profiles: it would refine a "
        "region where the emission boundary does not pass, and report an "
        "endpoint that measured nothing as an endpoint that agreed. The "
        "smallest wedge with something to measure at all six endpoints has "
        f"half-width {plan['metadata']['smallest_non_degenerate_wedge_deg']} "
        f"deg and costs {c['costs']['local_feasibility_matrix']}, which is "
        f"{c['costs']['local_feasibility_matrix'] / max(c['costs']['spendable_convention_A'], 1):.1f} "
        "times the spendable balance and more than the whole reported "
        "remainder. A degenerate endpoint is refused by the plan validator "
        "rather than costed at zero, so no affordable member of this family "
        "can be returned as a plan.",
        "",
        "Even the affordable end of that ladder would cover under half a "
        "percent of any band. A local patch of that size cannot qualify D026 "
        "globally and its omitted regions are not bounded by anything measured "
        "here; both facts are recorded in the plan rather than left implicit.",
        "",
        "## 5. Why the plan is blocked anyway",
        "",
    ]
    def cap(t: str) -> str:
        return t[:1].upper() + t[1:] if t else t

    for b in c["blockers"]:
        cost = b["cost_to_clear"]
        if isinstance(cost, dict):
            cost = ("; ".join(f"{k.replace('_', ' ')} {v}"
                              for k, v in cost.items()))
        lines += [f"**{b['id']}.** {cap(b['what'])}. {cap(b['why_it_blocks'])}."
                  f"", f"*Cost to clear:* {cost}. "
                  f"*Needs:* {b['authorization_needed']}.", ""]
    lines += [
        "The preflight agrees. On the plan as returned it reports "
        f"`{c['preflight']['as_returned']}` with "
        f"{c['preflight']['as_returned_errors']}; with the prerequisite "
        "stipulated met purely to separate schema from science it reports "
        f"`{c['preflight']['prerequisite_stipulated_met']}`, which authorizes "
        "nothing. On the full-domain matrix it reports "
        f"{c['preflight']['full_domain_matrix']}.",
        "",
        "## 6. Accounting",
        "",
        "The component counters are kept apart: "
        f"{led['component_counters']['native_trace']} native tracer "
        f"evaluations, {led['component_counters']['primary_path_integration']} "
        "primary path integrations, "
        f"{led['component_counters']['independent_reference_integration']} "
        "independent end-to-end reference integrations, across eight "
        "executions including the aborted 120-attempt run. A quadrature "
        "abscissa is not counted as a new ray; an independent end-to-end "
        "evaluation is not written off as cached algebra.",
        "",
        "Under the native-only convention in force through 029-031 the second "
        f"batch has spent {led['convention_A_native_only']['second_batch_spent']}"
        f" of {led['second_batch_cap']} and has "
        f"{led['convention_A_native_only']['second_batch_remaining']} left. "
        "Under the convention this ruling states for independent end-to-end "
        "reference evaluations it has spent "
        f"{led['convention_B_independent_reference_metered']['second_batch_spent']}"
        " and has "
        f"{led['convention_B_independent_reference_metered']['second_batch_remaining']}"
        f" left -- below the {led['validation_reserve_preserved']} "
        "response-validation reserve, so nothing at all is spendable. I am not "
        "choosing between them: the balance is recorded as unresolved and the "
        "reserve is untouched.",
        "",
        f"Boundary: {led['boundary_spent']} spent, "
        f"{led['boundary_remaining']} remaining, {led['new_boundary_calls']} "
        "new calls. No third batch, no new allowance.",
        "",
        "## 7. Governance and manuscript",
        "",
        "Governance is AUDIT_COMPLETE_WITH_PROTOCOL_DEVIATIONS. The four 031 "
        "deviations stay on the record: the allocation error, the 302-point "
        "cap overrun, the unmet reference-confirmation gate, and the partial "
        "and mismatched comparison. Nothing written under 029, 030 or 031 has "
        "been edited and the 031 token remains "
        f"`{c['old_blocked_token_preserved']}`.",
        "",
        "Section 5's 'Validated Computational Operator' statement and the "
        "order-resolution attribution in section 10.1 are not restored. This "
        "delivery produced no matched comparison, and a plan is not evidence. "
        "No manuscript rebuild and no submission-ready claim is made.",
        "",
        "This return authorizes nothing. No new physical query has been made "
        "and none should be made before the next ruling.",
        "",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    args = [(ROOT / a).resolve() for a in sys.argv[1:3]]
    raise SystemExit(main(*args))
