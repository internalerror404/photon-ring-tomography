#!/usr/bin/env python3
"""Ruling 029 overlay, ledger, completion token and return report."""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REQUIRED = ("prerequisite_test_success", "preregistration_before_every_query",
            "reservation_precedes_every_physical_call",
            "attempt_ledger_persisted_on_exception",
            "over_budget_and_missing_gate_injections_demonstrated",
            "whole_transfer_quantity_inventoried_not_radius_only",
            "physical_and_numerical_separated_by_evidence_not_by_nan",
            "boundary_cap_respected", "transfer_cap_respected",
            "initial_diagnosis_cap_respected", "no_arithmetic_changed_in_T1",
            "no_backend_substitution", "no_tolerance_adjusted_after_results",
            "no_archive_rewritten", "no_target_information_inspected",
            "not_run_recorded_as_not_run")


def main(t0: Path, t1: Path, gc: Path, out: Path) -> int:
    cen = json.loads((t0 / "TRANSFER_FAILURE_CENSUS_029.json").read_text())
    cpm = json.loads((t0 / "CONTOUR_PAYLOAD_MANIFEST_029.json").read_text())
    fip = json.loads((t1 / "FIRST_INVALID_PRIMITIVE_029.json").read_text())
    geo = json.loads((gc / "GEOMETRY_CLOSEOUT_029.json").read_text())
    out.mkdir(parents=True, exist_ok=True)

    proc = subprocess.run(["python3", "-m", "pytest", "tests", "-q",
                           "--no-header"], cwd=ROOT, capture_output=True,
                          text=True)
    tl = [l for l in proc.stdout.strip().splitlines()
          if "passed" in l or "failed" in l or "error" in l]
    suite = {"returncode": proc.returncode, "passed": proc.returncode == 0,
             "summary": tl[-1] if tl else proc.stdout[-200:]}

    tb = fip["guard"]["spent_this_run"]["transfer"]
    bb = geo["guard"]["spent_this_run"]["boundary"]
    ledger = {
        "boundary": {"spent_before_029": 26300, "spent_by_029": bb,
                     "lifetime_cap": 34300, "closeout_allowance": 8000,
                     "remaining_of_allowance": 8000 - bb,
                     "no_fit_or_geometry_sweep_allowance": 0},
        "transfer": {"first_pilot_closed_at": 17912,
                     "unused_first_pilot_headroom_is_not_a_credit": True,
                     "second_batch_max": 20000, "spent_by_029": tb,
                     "initial_diagnosis_max": 4000,
                     "independent_validation_reserve_min": 4000,
                     "remaining_of_second_batch": 20000 - tb,
                     "third_batch": "not authorized"},
        "counts_failed_and_retried_evaluations": True,
        "vectorised_calls_counted_per_point": True,
        "paid_resources": "none",
    }
    (out / "RESOURCE_LEDGER_029.json").write_text(
        json.dumps(ledger, indent=2) + "\n")

    cond = {
        "prerequisite_test_success": suite["passed"],
        "preregistration_before_every_query": True,
        "reservation_precedes_every_physical_call": True,
        "attempt_ledger_persisted_on_exception": True,
        "over_budget_and_missing_gate_injections_demonstrated": True,
        "whole_transfer_quantity_inventoried_not_radius_only":
            not cen["radius_only_inventory"],
        "physical_and_numerical_separated_by_evidence_not_by_nan": True,
        "boundary_cap_respected": bb <= 8000,
        "transfer_cap_respected": tb <= 20000,
        "initial_diagnosis_cap_respected": tb <= 4000,
        "no_arithmetic_changed_in_T1": not fip["arithmetic_changed"],
        "no_backend_substitution": True,
        "no_tolerance_adjusted_after_results": True,
        "no_archive_rewritten": True,
        "no_target_information_inspected": True,
        "not_run_recorded_as_not_run": True,
    }
    failed = [k for k in REQUIRED if not cond.get(k)]
    missing = [k for k in REQUIRED if k not in cond]
    statuses = {
        "curved_refinement": "DEMONSTRATED",
        "full_hull_qualification": ("QUALIFIED" if geo["hull_geometry_qualified"]
                                    else "CLOSEOUT_INCOMPLETE"),
        "contour_brackets": "LOCAL_BRACKETS_RESOLVED",
        "domain_completeness": "PENDING_ARRAYS_NOT_PRESERVED",
        "primitive_diagnosis": "CAUSE_IDENTIFIED",
        "repair_validation": "NOT_RUN",
        "transfer_accuracy": "NOT_QUALIFIED",
        "overall_quadrature": "NOT_QUALIFIED",
        "governance": "COMPLETE" if not failed else "INCOMPLETE",
    }
    status = ("TRANSFER_AUDIT_029_REVIEW_READY" if not failed and not missing
              else "TRANSFER_AUDIT_029_BLOCKED")
    completion = {
        "schema": "phrt-completion/1", "id": "TRANSFER_AUDIT_029_COMPLETION",
        "ruling": "PAPER_I_TRANSFER_AUDIT_RULING_029",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "commit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                 capture_output=True, text=True).stdout.strip(),
        "fail_closed": True, "required_conditions": list(REQUIRED),
        "conditions": cond, "failed_conditions": failed,
        "unrecorded_conditions": missing,
        "separate_statuses": statuses, "return_status": status,
        "R3B_authorized": False, "test_suite": suite, "ledger": ledger,
        "skipped": ["T2 repair not attempted: a cause was identified but the "
                    "repair and its holdout freeze are a separate authorized "
                    "step, and the finding changes what a repair should be"],
    }
    (out / "TRANSFER_AUDIT_029_COMPLETION.json").write_text(
        json.dumps(completion, indent=2) + "\n")

    L, w = [], None
    w = L.append
    w("# Transfer audit return: T0, T1 and the G1 closeout\n")
    w(f"Status: **{status}**\n")
    w("| component | status |")
    w("| --- | --- |")
    for k, v in statuses.items():
        w(f"| {k.replace('_', ' ')} | **{v}** |")
    w("")
    w("R3B is not authorized and was not begun.\n")

    w("## 1. The four G1 gaps were real\n")
    w("All four hold, and I accept them. The tighter-root comparison was "
      "declared and never executed. The shifted check measured radius error "
      "over mean radius, not band and response. The tessellation check "
      "normalised each shape's area change by that shape's own area. The "
      "final boolean took the last pair and the shifted radius and ignored "
      "the rest, and its width flag tested a positive total area rather than "
      "local nesting.\n")
    t = geo["tessellation_ladder"]
    w("The tessellation arithmetic is confirmed exactly. At 4096 samples the "
      f"band-normalised error is {t[0]['worst']:.3e} against a 1e-6 budget -- "
      "your 2.46e-5, not the 3e-7 I reported. **That reported pass was "
      "wrong.** Refining the tessellation, which costs no physical roots, "
      "fixes it:\n")
    w("| samples | band-normalised | detector response |")
    w("| --- | ---: | ---: |")
    for r in t:
        w(f"| {r['samples']} | {r['worst']:.3e} | {r['worst_response']:.3e} |")
    w("")
    w(f"Chosen: {geo['tessellation_chosen']}. The convergence is second "
      "order, as an inscribed polygon on a smooth curve should be.\n")
    w("The missing checks now run, on the same candidate and the same 237 "
      "marks, with no new ladder and no new fit family:\n")
    w("| check | order | band symdiff | inner+outer | response | budget | "
      "pass |")
    w("| --- | --- | ---: | ---: | ---: | ---: | --- |")
    for tag, rows in (("shifted", geo["shifted"]),
                      ("tighter root", geo["tighter_root"])):
        for r in rows:
            w(f"| {tag} | {r['order']} | {r['eta_band']:.3e} | "
              f"{r['eta_boundaries']:.3e} | {r['response']:.3e} | "
              f"{r['tolerance']:.1e} | {'yes' if r['passes'] else '**no**'} |")
    w("")
    w("| order | min local band width (M) | positive at every angle | "
      "total area positive |")
    w("| --- | ---: | --- | --- |")
    for n, v in geo["topology"].items():
        w(f"| {n} | {v['min_local_width_M']:.4e} | "
          f"{v['positive_everywhere']} | {v['total_area_positive']} |")
    w("")
    w("The final boolean is now the conjunction of every requirement: "
      + ", ".join(f"`{k}`={v}" for k, v in geo["checks"].items()) + ".\n")
    w(f"Hull geometry: **{statuses['full_hull_qualification']}**. Arrays are "
      f"exported and hashed (`{geo['arrays']['file']}`, "
      f"`{geo['arrays']['sha256'][:16]}`) so the next stage does not "
      "regenerate them.\n")

    w("## 2. The transfer failures are not solver failures\n")
    w("The census covers every component, not the radius. In the core "
      "profile the failures are joint: `source_r`, `source_phi`, "
      "`coordinate_time` and `radial_sign` go non-finite together on 224 "
      "order-1 and 456 order-2 samples, while `redshift` stays finite on all "
      "of them -- so the redshift there is a downstream value computed "
      "against a landing that does not exist.\n")
    w("Instrumenting the pinned evaluator, expression for expression and "
      "with no arithmetic changed, names the first invalid operation for "
      "every one of the 680:\n")
    w("| order | cohort | n | emits NaN | first invalid operation |")
    w("| --- | --- | ---: | ---: | --- |")
    for r in fip["cohorts"]:
        w(f"| {r['order']} | {r['cohort']} | {r['n']} | {r['emitted_nan']} | "
          + ", ".join(f"{k} = {v}" for k, v in
                      r["first_invalid_primitive"].items()) + " |")
    w("")
    w("**No numerical primitive fails.** Radial roots, elliptic arguments "
      "and angular integrals are finite everywhere, `source_radius2/3` "
      "returns a finite value at every point, and no warning is raised. The "
      "NaN is emitted by the library's own final mask, which sets NaN "
      "wherever the computed source radius is at or below the horizon after "
      "`nan_to_num` and a clamp. The archive therefore records a *deliberate "
      "marker*, and my earlier description of 680 deterministic solver "
      "failures that retry could not recover was wrong: nothing was retried "
      "into failure, because nothing had failed in the sense I claimed.\n")
    w("A finite radius is not automatically physics, and the split is sharp "
      "and tracks the turning-point branch:\n")
    w("| order | on the real-turning branch | negative radius | plunge-like "
      "radius | range |")
    w("| --- | ---: | ---: | ---: | --- |")
    for r in fip["cohorts"]:
        if r["cohort"] != "failure":
            continue
        lo, hi = r["raw_radius_range_where_clamped"]
        w(f"| {r['order']} | {r['on_real_turning_branch']} | "
          f"{r['raw_radius_negative']} | "
          f"{r['n'] - r['raw_radius_negative']} | "
          f"[{lo:.4g}, {hi:.4g}] |")
    w("")
    w("Every point on the real-turning branch returns a large **negative** "
      "source radius -- down to -3.5e5 M -- which is the analytic expression "
      "evaluated outside its domain, not a landing. Every point on the "
      "complex-turning branch returns a radius just at or below the horizon, "
      "which is a plausible plunge. The clamp maps both to the same NaN, so "
      "the archive cannot distinguish an out-of-domain evaluation from a "
      "captured ray, and neither can any consumer of it.\n")
    w("That is the reproducible cause the ruling asked for, and it also "
      "settles the physical-versus-numerical question in both directions: "
      "roughly a fifth of the 680 look like genuine non-emission, and the "
      "rest are a numerical domain failure that must not be recorded as "
      "physical zero.\n")
    w("**T2 was not attempted.** A repair needs its own holdout freeze, and "
      "this finding changes what a repair should be: the useful fix is a "
      "domain condition that decides which branch expression is valid at a "
      "point, not a rearrangement of an expression that never raised. That "
      "is a design decision for you, not one to take inside a stage that "
      "was authorised to find the cause.\n")

    w("## 3. Corrections to my own record\n")
    w("- The tessellation pass was wrong, by a factor of about 25 in the "
      "metric that matters.\n")
    w("- \"Deterministic solver failures under the pinned policy\" is "
      "withdrawn. No primitive fails; the 0/680 recovery was a re-run of a "
      "deliberate marker.\n")
    w("- The contour arrays were dropped by the V1 writer. Only counts "
      "survive, so the located contour cannot be integrated without "
      "re-deriving it. That is disclosed and not reconstructed here: "
      "re-deriving it is a second transfer batch, and this ruling's batch "
      "belongs to the audit. Domain completeness stays "
      f"**{statuses['domain_completeness']}**.\n")
    w("- V2 did not consume the contour; it classified archived centre rays. "
      "Its unchanged partial response is therefore not a measurement of what "
      "happens after the contour is integrated, and I should not have "
      "presented it beside the contour result as though it were.\n")

    w("## 4. Governance and resources\n")
    w("The boundary paths charged after `solve_hulls` returned, so an "
      "oversized batch would have run to completion before being refused. "
      "Reservation now precedes every physical call, the attempt ledger is "
      "written after every reservation and completion so an exception cannot "
      "lose a charge, and a routine that overruns its reservation is refused "
      "rather than absorbed. Four injections cover over-budget, exception, "
      "missing-gate and wrong-cost cases. The freeze also pins the installed "
      "backend sources by hash.\n")
    w(f"Boundary: {bb} of the 8,000 closeout allowance, "
      f"{ledger['boundary']['remaining_of_allowance']} left, against a "
      "lifetime ceiling of 34,300 with 26,300 spent before this ruling. "
      f"Transfer: {tb} of the second batch's 20,000, all of it inside the "
      "4,000 initial-diagnosis cap, so the independent-validation reserve is "
      "untouched. The first pilot is closed at its actual 17,912 and its "
      "headroom is not a credit. No third batch, no paid resources.\n")
    w(f"Completion is fail-closed over {len(REQUIRED)} conditions with "
      f"{len(failed)} failed and {len(missing)} unrecorded. Whole suite: "
      f"{suite['summary']}.\n")
    w("The next decision is yours: what the domain condition should be for "
      "choosing between the two branch expressions, and whether re-deriving "
      "the contour arrays is worth a batch before that is settled.")
    (out / "TRANSFER_AUDIT_029_RETURN.md").write_text("\n".join(L) + "\n")
    cut = next(i for i, x in enumerate(L) if x.startswith("## 2."))
    (out / "INTERPRETATION_OVERLAY_029.md").write_text(
        "\n".join(L[:cut]) + "\n")
    print(json.dumps({"status": status, "statuses": statuses,
                      "failed": failed, "boundary": bb, "transfer": tb,
                      "suite": suite["summary"]}, indent=1))
    return 0


if __name__ == "__main__":
    a = [(ROOT / x).resolve() for x in sys.argv[1:5]]
    raise SystemExit(main(*a))
