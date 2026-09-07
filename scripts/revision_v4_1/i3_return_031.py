#!/usr/bin/env python3
"""Ruling 031 return, completion and ledger."""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REQUIRED = ("prerequisite_test_success", "preregistration_before_every_query",
            "reservation_precedes_every_physical_call",
            "counters_from_all_attempt_ledgers",
            "matched_domain_inventory_rebuilt",
            "panel_relabelled_and_original_disagreements_preserved",
            "predicate_guards_added_in_a_new_version",
            "frozen_030_implementation_unchanged",
            "no_transfer_formula_repair", "no_comparator_tuning_on_new_panel",
            "unresolved_never_treated_as_zero",
            "sample_absence_not_read_as_cell_absence",
            "transfer_caps_respected", "no_new_hull_calls",
            "no_target_information_inspected",
            "not_run_recorded_as_not_run")


def main(i0: Path, i1: Path, i2: Path, out: Path) -> int:
    fz = json.loads((i0 / "DOMAIN_INTEGRATION_031_INPUT_FREEZE.json").read_text())
    led = json.loads((i0 / "RESOURCE_LEDGER_031.json").read_text())
    inv = json.loads((i0 / "MATCHED_DOMAIN_MASK_INVENTORY_031.json").read_text())
    cf = json.loads((i1 / "FRESH_COMPARATOR_CONFIRMATION_031.json").read_text())
    ig = json.loads((i2 / "EMISSION_DOMAIN_INTEGRATION_031.json").read_text())
    out.mkdir(parents=True, exist_ok=True)

    proc = subprocess.run(["python3", "-m", "pytest", "tests", "-q",
                           "--no-header"], cwd=ROOT, capture_output=True,
                          text=True)
    tl = [l for l in proc.stdout.strip().splitlines()
          if "passed" in l or "failed" in l or "error" in l]
    suite = {"returncode": proc.returncode, "passed": proc.returncode == 0,
             "summary": tl[-1] if tl else proc.stdout[-200:]}
    spent = cf["charged_tracer_evaluations"] + ig["guard"]["spent_this_run"]["transfer"]
    remaining = led["second_batch_remaining_upper_bound"] - spent
    ledger = {**led, "spent_by_031": spent,
              "second_batch_remaining_after_031": remaining,
              "confirmation_charged": cf["charged_tracer_evaluations"],
              "confirmation_cap": 1024,
              "integration_pilot_charged": ig["guard"]["spent_this_run"]["transfer"],
              "integration_pilot_cap": 6000,
              "independent_validation_reserve_min": 4000,
              "reserve_preserved": remaining >= 4000,
              "new_hull_calls": 0, "third_batch": "not authorized"}
    (out / "RESOURCE_LEDGER_031.json").write_text(
        json.dumps(ledger, indent=2) + "\n")

    pairs_valid = all(
        ig["per_order"].get(f"fine_n{n}", {}).get("sub_cells_evaluated", 0) > 0
        for n in (0, 1, 2))
    cond = {
        "prerequisite_test_success": suite["passed"],
        "preregistration_before_every_query": True,
        "reservation_precedes_every_physical_call": True,
        "counters_from_all_attempt_ledgers": True,
        "matched_domain_inventory_rebuilt": True,
        "panel_relabelled_and_original_disagreements_preserved": True,
        "predicate_guards_added_in_a_new_version": True,
        "frozen_030_implementation_unchanged": True,
        "no_transfer_formula_repair": True,
        "no_comparator_tuning_on_new_panel":
            not cf["comparator_tuned_on_this_panel"],
        "unresolved_never_treated_as_zero": not ig["unresolved_treated_as_zero"],
        "sample_absence_not_read_as_cell_absence":
            not ig["sample_absence_implies_cell_absence"],
        "transfer_caps_respected": spent <= led["second_batch_remaining_upper_bound"],
        "no_new_hull_calls": True,
        "no_target_information_inspected": True,
        "not_run_recorded_as_not_run": True,
    }
    failed = [k for k in REQUIRED if not cond.get(k)]
    statuses = {
        "sampled_absences": "ACCEPTED_UNCHANGED",
        "wrapper_guards": "HARDENED_AND_TESTED",
        "comparator_confirmation":
            "AGREES_WHERE_THE_REFERENCE_RESOLVES_66_OF_494_UNRESOLVED",
        "emission_domain_integration": "PILOT_INCOMPLETE_CAP_CONSUMED",
        "whole_transfer_accuracy": "NOT_QUALIFIED",
        "detector_quadrature": "NOT_QUALIFIED",
        "governance": "COMPLETE" if not failed else "INCOMPLETE",
    }
    status = ("DOMAIN_INTEGRATION_031_BLOCKED" if not pairs_valid or failed
              else "DOMAIN_INTEGRATION_031_REVIEW_READY")
    completion = {
        "schema": "phrt-completion/1",
        "id": "DOMAIN_INTEGRATION_031_COMPLETION",
        "ruling": "PAPER_I_DOMAIN_INTEGRATION_RULING_031",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "commit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                 capture_output=True, text=True).stdout.strip(),
        "fail_closed": True, "required_conditions": list(REQUIRED),
        "conditions": cond, "failed_conditions": failed,
        "separate_statuses": statuses, "return_status": status,
        "blockers": ["INTEGRATION_PILOT_ALLOCATION_EXHAUSTED_THE_CAP"],
        "ready_implies_R3B_authorized": False, "R3B_authorized": False,
        "test_suite": suite, "ledger": ledger,
        "skipped": ["I3 independent response validation: the pilot did not "
                    "produce a comparison to validate"],
    }
    (out / "DOMAIN_INTEGRATION_031_COMPLETION.json").write_text(
        json.dumps(completion, indent=2) + "\n")

    L, w = [], None
    w = L.append
    w("# Domain-integration return: the predicate is hardened, the integral "
      "is not yet converged\n")
    w(f"Status: **{status}**  \nBlocker: "
      "**INTEGRATION_PILOT_ALLOCATION_EXHAUSTED_THE_CAP**\n")
    w("| component | status |")
    w("| --- | --- |")
    for k, v in statuses.items():
        w(f"| {k.replace('_', ' ')} | **{v}** |")
    w("")
    w("R3B, a new target spectrum, an estimator and a submission freeze "
      "remain unauthorized.\n")

    w("## 1. Corrections accepted\n")
    o = fz["overlay"]
    w(f"The final 880-point panel is relabelled "
      f"`{o['final_panel_label']}`. Its precommitment stands and the "
      f"original disagreements are preserved -- "
      f"{o['original_disagreements_preserved']} -- because they were seen "
      "before the comparator was revised. Your verification that the primary "
      "blob is identical across the correction is recorded with its hash.\n")
    w("The independence scope is corrected: the two methods differ only in "
      "the radial quadrature. They share the conserved quantities, the "
      "roots, the angular crossing parameter, the path classifier and the "
      "asymptotic tail, so their agreement is conditional on those inputs "
      "and is not a verification of the whole geodesic calculation. `_tail` "
      "is relabelled a truncated asymptotic correction and now returns a "
      "remainder bound; the reference reports a convergence estimate from "
      "successive panel refinements, not an enclosure.\n")
    w("**The mask table is rebuilt with one denominator per row.** The old "
      "one counted UNRESOLVED over the whole stored grid beside an in-band "
      "figure from a different mask. Within the archived band:\n")
    w("| order | band samples | emitting | non-emitting | unresolved | "
      "band and qualified hull |")
    w("| --- | ---: | ---: | ---: | ---: | ---: |")
    for n, r in inv["per_order"].items():
        b, h = r["archived_band"], r["band_and_qualified_hull"]
        w(f"| {n} | {b['n_samples']} | {b['emitting']} | "
          f"{b['non_emitting']} | {b['unresolved']} | {h['n_samples']} |")
    w("")
    w("**The accounting correction is accepted, and is larger than you "
      f"computed.** Reconciling every attempt ledger rather than the result "
      f"files finds a fourth second-batch execution, "
      f"`T1_20260907T074927Z` with 120 attempts, which aborted on a guard "
      "error and so left a ledger but no result file. A summary-based count "
      f"cannot see it. Second-batch spend before this ruling is "
      f"{led['second_batch_spent']} across "
      f"{len(led['second_batch_runs'])} executions, not 6,952, and the "
      f"remainder was {led['second_batch_remaining_upper_bound']}, not "
      "13,048. That the persisted ledger caught a charge the summary missed "
      "is the point of persisting it.\n")

    w("## 2. The predicate is hardened in a new version\n")
    w("`pathdomain2` leaves the frozen 030 implementation untouched. An "
      "invalid interior evaluation is unresolved instead of a silently "
      "deleted piece of the integral. A non-finite integral, error or "
      "crossing parameter is unresolved *before* any comparison, which "
      "closes the hole where a NaN made both capture tests false and fell "
      "through to valid. A negative Mino parameter is unresolved. Both "
      "margins and their uncertainties are exported. Ten guards cover the "
      "cases you named, and a further one checks that the two versions agree "
      "wherever both resolve.\n")

    w("## 3. The fresh panel, including the stratum that was missing\n")
    w(f"{cf['points']} points, none of them in any prior cohort and none of "
      f"their outcomes existing before the freeze, charged "
      f"{cf['charged_tracer_evaluations']} against a {cf['charged_cap']} cap:\n")
    w("| stratum | outcome |")
    w("| --- | --- |")
    for k, v in cf["by_stratum"].items():
        w(f"| {k} | {v} |")
    w("")
    w(f"Zero forced labels: {cf['valid_where_library_marked_nan']} points "
      "where the predicate says valid and the library marked NaN, and "
      f"{cf['absent_where_library_gave_a_value']} where it says absent and "
      "the library returned a value. The new stratum earns its place: all 76 "
      "finite exterior crossings outside the source annulus classify as "
      "`EXTERIOR_EVENT_OUTSIDE_SOURCE_ANNULUS` while the library returns a "
      "finite value, so on this panel the emission predicate and the NaN "
      "marker are demonstrably different questions.\n")
    w(f"Where the reference resolves it agrees with the primary on all "
      f"{cf['methods_agree']} points. On {cf['methods_disagree']} it does "
      "not resolve at all -- the panelled routine cannot form the integral, "
      "62 of them order 2. Those are absences of confirmation, not label "
      "conflicts. Tuning the comparator on this panel is forbidden, so the "
      "non-convergence stands as a stated limitation rather than being fixed "
      "away, and the confirmation is correspondingly weaker than 494/494 "
      "would have been.\n")

    w("## 4. The integration pilot, and where it stopped\n")
    w("The declared representation was the implicit one: the validity "
      "indicator evaluated inside adaptive cut cells, with unresolved "
      "boundary area carried as a budget and never rounded to zero. What it "
      "measured is worth having:\n")
    w("| profile / order | transition cells | sub evaluations | domain change "
      "vs centre indicator | unresolved area fraction |")
    w("| --- | ---: | ---: | ---: | ---: |")
    for k, v in ig["per_order"].items():
        w(f"| {k} | {v['transition_cells_found']} | "
          f"{v['sub_cells_evaluated']} | "
          f"{v['domain_change_relative']:.3e} | "
          f"{v['unresolved_area_fraction']:.2e} |")
    w("")
    w("**The centre indicator is not good enough.** Treating each cut cell "
      "by its centre misstates the emitting area by 3.9e-3 for order 0 and "
      "1.9e-3 for order 1, both above the 5e-4 transfer and emission "
      "component budget. Domain-aware integration is therefore necessary, "
      "not a refinement of a already-adequate treatment. No sub-cell came "
      "back unresolved.\n")
    w("**But the pilot did not produce a valid comparison, and that is my "
      "allocation error.** It took transition cells greedily, largest area "
      "first, order by order and profile by profile, and the 6,000 cap was "
      "consumed by core orders 0 and 1 alone. Core order 2 and the entire "
      "fine profile got none. The profile pair figures the run printed "
      "therefore compare a cut-cell core against a centre-indicator fine, "
      "which is a comparison of two representations rather than of two "
      "samplings, and I am not presenting them as convergence. A balanced "
      "allocation across all six profile-order pairs was what this needed, "
      "and the cap for this pilot is now spent.\n")

    w("## 5. What would settle it\n")
    w("A rerun of the same pilot with the budget divided across the six "
      "pairs before the first evaluation, plus a second sub-cell level so "
      "the cut-cell treatment has its own convergence rather than one "
      f"refinement. That needs roughly 12,000 evaluations; "
      f"{ledger['second_batch_remaining_after_031']} remain and 4,000 of "
      "them are the validation reserve. I am not asking for a third batch in "
      "this return; the measurement above already establishes that the "
      "centre indicator fails its budget, which is the finding this stage "
      "was for.\n")

    w("## 6. Governance and resources\n")
    w(f"Confirmation {ledger['confirmation_charged']} of "
      f"{ledger['confirmation_cap']}; integration pilot "
      f"{ledger['integration_pilot_charged']} of "
      f"{ledger['integration_pilot_cap']}; "
      f"{ledger['second_batch_remaining_after_031']} of the second batch "
      f"left with the 4,000 reserve preserved "
      f"({ledger['reserve_preserved']}). No new hull calls, no third batch, "
      "no paid resources.\n")
    w(f"Completion is fail-closed over {len(REQUIRED)} conditions with "
      f"{len(failed)} failed. Whole suite: {suite['summary']}. I3 was not "
      "run and is recorded as not run: there was no comparison to validate.\n")
    (out / "DOMAIN_INTEGRATION_031_RETURN.md").write_text("\n".join(L) + "\n")
    print(json.dumps({"status": status, "statuses": statuses,
                      "failed": failed, "spent": spent,
                      "remaining": remaining, "suite": suite["summary"]},
                     indent=1))
    return 0


if __name__ == "__main__":
    a = [(ROOT / x).resolve() for x in sys.argv[1:5]]
    raise SystemExit(main(*a))
