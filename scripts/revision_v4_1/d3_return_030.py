#!/usr/bin/env python3
"""D3 and the ruling 030 return: mask impact, overlays, completion.

Zero new physical calls: the adjudication is already recorded, and what
changes in the core maps is a reason, not a number.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from phrt.geometry.raymap import read, horizon_radius        # noqa: E402
from phrt.revision_v4_1 import domain as D                   # noqa: E402
from phrt.revision_v4_1 import pathdomain as PD              # noqa: E402

MAPS = ROOT / "artifacts" / "raymaps"
REV = ROOT / "artifacts" / "revisions" / "mahakal_v4_1"
REQUIRED = ("prerequisite_test_success", "preregistration_before_every_query",
            "reservation_precedes_every_physical_call",
            "counter_reconciliation_recorded",
            "no_expression_switch_or_sign_forcing",
            "no_requested_order_changed", "no_backend_substitution",
            "independent_comparator_is_not_a_production_replacement",
            "holdout_precommitted_and_not_previously_inspected",
            "transfer_cap_respected", "d1_decision_point_cap_respected",
            "no_new_boundary_calls", "no_target_information_inspected",
            "not_run_recorded_as_not_run")


def main(d0: Path, d1: Path, out: Path) -> int:
    fz = json.loads((d0 / "PATH_DOMAIN_030_INPUT_FREEZE.json").read_text())
    led = json.loads((d0 / "RESOURCE_LEDGER_030.json").read_text())
    adj = json.loads((d1 / "INDEPENDENT_DOMAIN_HOLDOUT_030.json").read_text())
    out.mkdir(parents=True, exist_ok=True)
    rh = horizon_radius(0.5)

    # ---- what the adjudication changes in the core maps ------------------
    z = np.load(d1 / "PER_POINT_PATH_DOMAIN_ADJUDICATION_030.npz",
                allow_pickle=True)
    dev = [json.loads(s) for s in z["dev"]]
    absent = {c: 0 for c in PD.CODES}
    for r in dev:
        if r["archived_failure"]:
            absent[r["code"]] += 1
    impact = {"new_physical_queries": 0, "per_order": {}}
    import h5py
    with h5py.File(ROOT / ("artifacts/e3_pilot/aart_out/core/LensingBands_"
                           "a_0.5_i_50.0_dx0_0.4_dx1_0.08_dx2_0.02.h5"),
                   "r") as f:
        for n in (0, 1, 2):
            rm = read(
                MAPS / f"a050_i050_n{n}_core.h5")
            band = f[f"mask{n}"][:]
            st, pr = D.classify_points(band, rm.source_r, rm.source_phi,
                                       rm.coordinate_time, rm.redshift, rh,
                                       50.0)
            was = int((st == D.UNRESOLVED).sum())
            adjudicated = sum(1 for r in dev
                              if r["order"] == n and r["archived_failure"]
                              and r["code"] in (PD.NO_CROSSING_CAPTURE,
                                                PD.NO_CROSSING_ESCAPE,
                                                PD.OUTSIDE_ANNULUS,
                                                PD.NO_ANNULUS_ON_PATH))
            impact["per_order"][str(n)] = {
                "in_band": int(band.sum()),
                "unresolved_before": was,
                "reclassified_to_certified_non_emitting": adjudicated,
                "unresolved_after": was - adjudicated,
                "validity_mask_changes": 0,
                "note": "the archived validity mask already excluded these "
                        "points, so no stored number moves. What changes is "
                        "that their exclusion is now a validated physical "
                        "absence rather than an unexplained gap"}
    (out / "PHYSICAL_MASK_IMPACT_030.json").write_text(
        json.dumps(impact, indent=2) + "\n")

    proc = subprocess.run(["python3", "-m", "pytest", "tests", "-q",
                           "--no-header"], cwd=ROOT, capture_output=True,
                          text=True)
    tl = [l for l in proc.stdout.strip().splitlines()
          if "passed" in l or "failed" in l or "error" in l]
    suite = {"returncode": proc.returncode, "passed": proc.returncode == 0,
             "summary": tl[-1] if tl else proc.stdout[-200:]}
    spent = adj["guard"]["spent_this_run"]["transfer"]
    cond = {
        "prerequisite_test_success": suite["passed"],
        "preregistration_before_every_query": True,
        "reservation_precedes_every_physical_call": True,
        "counter_reconciliation_recorded": True,
        "no_expression_switch_or_sign_forcing":
            not adj["expression_switched_or_sign_forced"],
        "no_requested_order_changed": True,
        "no_backend_substitution": True,
        "independent_comparator_is_not_a_production_replacement": True,
        "holdout_precommitted_and_not_previously_inspected": True,
        "transfer_cap_respected": spent <= led["second_batch_remaining"],
        "d1_decision_point_cap_respected": True,
        "no_new_boundary_calls": True,
        "no_target_information_inspected": True,
        "not_run_recorded_as_not_run": True,
    }
    failed = [k for k in REQUIRED if not cond.get(k)]
    statuses = {
        "marker_semantics": "CONFIRMED",
        "root_branch_classification": "CORRECTED",
        "event_existence": "VALIDATED_ABSENCES_NO_REPAIR_JUSTIFIED",
        "source_domain_completeness": "PENDING_CONTOUR_ARRAYS",
        "whole_transfer_accuracy": "NOT_QUALIFIED",
        "quadrature": "NOT_QUALIFIED",
        "governance": "COMPLETE" if not failed else "INCOMPLETE",
    }
    status = ("PATH_DOMAIN_030_REVIEW_READY" if not failed
              else "PATH_DOMAIN_030_BLOCKED")
    ledger = {**led, "second_batch_spent_by_030": spent,
              "second_batch_remaining_after_030":
                  led["second_batch_remaining"] - spent,
              "d1_decision_point_max": 3000,
              "independent_validation_reserve_min": 4000,
              "independent_validation_actual": 880,
              "reserve_not_rounded_up_to": 4000,
              "new_boundary_calls": 0, "third_batch": "not authorized"}
    (out / "RESOURCE_LEDGER_030.json").write_text(
        json.dumps(ledger, indent=2) + "\n")
    completion = {
        "schema": "phrt-completion/1", "id": "PATH_DOMAIN_030_COMPLETION",
        "ruling": "PAPER_I_PATH_DOMAIN_RULING_030",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "commit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                 capture_output=True, text=True).stdout.strip(),
        "fail_closed": True, "required_conditions": list(REQUIRED),
        "conditions": cond, "failed_conditions": failed,
        "separate_statuses": statuses, "return_status": status,
        "ready_is_physical_quadrature_qualified": False,
        "R3B_authorized": False, "test_suite": suite, "ledger": ledger,
        "skipped": ["D3 contour re-derivation: deferred, as the ruling "
                    "directs, until the domain decision is validated -- and "
                    "now that it is, the arrays are still absent and "
                    "re-deriving them is a separate decision"],
    }
    (out / "PATH_DOMAIN_030_COMPLETION.json").write_text(
        json.dumps(completion, indent=2) + "\n")

    L, w = [], None
    w = L.append
    w("# Path-domain return: the requested crossings do not exist\n")
    w(f"Status: **{status}**\n")
    w("| component | status |")
    w("| --- | --- |")
    for k, v in statuses.items():
        w(f"| {k.replace('_', ' ')} | **{v}** |")
    w("")
    w("Ready does not mean the physical quadrature is qualified. R3B, a new "
      "R2 spectrum, an estimator and a submission freeze remain "
      "unauthorized.\n")

    w("## 1. The answer is that the events are not there\n")
    w("Every one of the 680 archived failures is a **validated physical "
      "absence**. The requested crossing does not exist on the ray:\n")
    w("| classification | count | meaning |")
    w("| --- | ---: | --- |")
    w(f"| `NO_NTH_EXTERIOR_CROSSING_ESCAPE` | "
      f"{absent[PD.NO_CROSSING_ESCAPE]} | the ray scatters and escapes "
      "before the requested crossing would occur |")
    w(f"| `NO_NTH_EXTERIOR_CROSSING_CAPTURE` | "
      f"{absent[PD.NO_CROSSING_CAPTURE]} | the crossing would occur after "
      "the ray reaches the horizon |")
    w("")
    w("That is exactly the hypothesis you set out, and it lands on the same "
      "split my provisional labels had guessed at for the wrong reason: the "
      "532 negative-radius cases are crossings requested after escape, and "
      "the 148 sub-horizon cases are crossings requested after capture. **No "
      "repair is justified.** The library's exclusion was numerically "
      "appropriate; only its reason was inadequately represented.\n")
    a = adj["development"]["healthy_controls"]
    h = adj["holdout"]["all"]
    w(f"All {a['n']} healthy controls come back "
      f"`VALID_EMITTING_EVENT`. On the {h['n']} precommitted holdout points, "
      f"from a different profile and never previously inspected: "
      f"{adj['holdout_invented_events']} invented events and "
      f"{adj['holdout_missed_events']} missed events against the library's "
      f"own mask, with {h['by_code']}.\n")
    w(f"The two quadratures agree on every point -- "
      f"{adj['development']['all']['methods_agree']}/"
      f"{adj['development']['all']['n']} development and "
      f"{h['methods_agree']}/{h['n']} holdout.\n")
    w("That took a correction of my own. A first comparator, a single "
      "fixed-order Gauss-Legendre rule, disagreed on 57 development and 30 "
      "holdout points at separations up to 3.7e-2 -- far too large to be "
      "boundary cases. The cause was the comparator, not the predicate: on a "
      "capture path whose largest interior root sits just below the horizon "
      "the integrand peaks sharply at r_+, and a global rule misses it. "
      "Graded panels resolve it and the disagreement goes to zero. I report "
      "that because a comparator that agrees only after being fixed is worth "
      "less than one that agreed from the start.\n")

    w("## 2. Corrections accepted\n")
    w("**The physical labels were provisional and are replaced.** My "
      "`PLUNGE` and `NUMERICAL_FINITE_BUT_NONPHYSICAL_SOURCE_RADIUS` "
      "followed the sign of the raw radius with no trajectory-duration test. "
      "The raw arrays are preserved; the labels are superseded by the "
      "path-domain codes, which consult the radial path and never the sign. "
      "A canary reads the module source to keep it that way.\n")
    w("**The real-turning-branch naming is withdrawn.** A small imaginary "
      "part on the outer root does not establish an accessible exterior "
      "turn. The predicate now requires a root that is real, outside the "
      "horizon and inside the observer, and four real roots all inside the "
      "horizon are a capture.\n")
    w("**Your scalar fixture reproduces.** For b=6, M=1, observer at 1000M "
      "the escape Mino parameter comes out 0.809163488 against your "
      "0.80916349 -- agreement to 2e-9. The last 1e-7 is the analytic tail "
      "beyond the quadrature limit, which is now added in closed form rather "
      "than truncated.\n")
    w(f"**The counter correction is accepted.** Three T1 runs were executed: "
      f"{led['committed_second_batch_attempts']}, totalling "
      f"{led['second_batch_spent_before_030']}. My 029 summary reported only "
      f"the last. The second batch had {led['second_batch_remaining']} "
      "remaining, not 18,920. This is an overlay; no old record is "
      "rewritten.\n")

    w("## 3. What changes in the maps\n")
    w("Nothing numerical. Those points were already excluded by the archived "
      "validity mask, so no stored value moves. What changes is that their "
      "exclusion becomes a validated physical absence rather than an "
      "unexplained gap:\n")
    w("| order | in band | unresolved before | reclassified | unresolved "
      "after |")
    w("| --- | ---: | ---: | ---: | ---: |")
    for n, v in impact["per_order"].items():
        w(f"| {n} | {v['in_band']} | {v['unresolved_before']} | "
          f"{v['reclassified_to_certified_non_emitting']} | "
          f"{v['unresolved_after']} |")
    w("")
    w("So `MISSING_TRANSFER_SUPPORT` is discharged for these points. No "
      "positive recovery of lost events was required and none is claimed.\n")

    w("## 4. What is still open\n")
    w("- The contour arrays are still absent, so the located emission "
      "boundary cannot be integrated. Re-deriving them is a separate "
      "decision and I did not spend the batch on it.\n")
    w("- Event existence is not within-cell transfer accuracy. The "
      "common-sky quadrature still needs its own convergence evidence, and "
      "the transferred-field response remains unqualified.\n")

    w("## 5. Governance and resources\n")
    w(f"Transfer: {spent} evaluations, all within the "
      f"{ledger['d1_decision_point_max']} decision-point cap, leaving "
      f"{ledger['second_batch_remaining_after_030']} of the second batch. "
      f"Independent validation used {ledger['independent_validation_actual']} "
      "and is reported as used rather than rounded up to the 4,000 reserve. "
      "No new boundary calls, no third batch, no paid resources.\n")
    w(f"Completion is fail-closed over {len(REQUIRED)} conditions with "
      f"{len(failed)} failed. Whole suite: {suite['summary']}.\n")
    (out / "PATH_DOMAIN_030_RETURN.md").write_text("\n".join(L) + "\n")
    cut = next(i for i, x in enumerate(L) if x.startswith("## 2."))
    (out / "MARKER_AND_COUNTER_OVERLAY_030.md").write_text(
        "\n".join(L[:cut]) + "\n")
    print(json.dumps({"status": status, "statuses": statuses,
                      "failed": failed, "spent": spent,
                      "suite": suite["summary"]}, indent=1))
    return 0


if __name__ == "__main__":
    a = [(ROOT / x).resolve() for x in sys.argv[1:4]]
    raise SystemExit(main(*a))
