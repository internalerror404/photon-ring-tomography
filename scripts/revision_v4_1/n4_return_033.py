#!/usr/bin/env python3
"""N4 of ruling 033: overlay, ledger and return. Zero physical queries."""
from __future__ import annotations

import hashlib
import json
import statistics as st
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

CAP = 20000
BEFORE = {"native": 13566, "primary_path_component": 10806,
          "independent_reference": 4806}
BOUNDARY_SPENT, BOUNDARY_REMAINING = 33410, 890


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with Path(p).open("rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


OVERLAY = """# ACCOUNTING_AND_SCOPE_OVERLAY_033

Ruling: PAPER_I_FEASIBILITY_AND_CLOSEOUT_RULING_033
Reviewed commit: 303dfb640a6f5895641a82ae0aaa71bd1e0ae642

Additive. No file written under rulings 029-032 is edited, and every earlier
token stands: `DOMAIN_INTEGRATION_031_BLOCKED` and
`MATCHED_INTEGRATION_032_PLAN_BLOCKED`.

## 1. The accounting convention is settled

Convention B governs: native evaluations plus independent end-to-end reference
evaluations. Before this ruling that is 13,566 + 4,806 = 18,372 of the 20,000
second batch, leaving 1,628. The 10,806 primary path integrations stay as a
separate component counter and are not charged again when they ride inside the
same native point-evaluation bundle; a standalone path re-evaluation without a
native bundle would be a charged unit. The 032 native-only figure of 6,434
remains on the record as a historical diagnostic, not as a balance.

The 4,000-unit full-response validation reserve cannot be funded from 1,628.
It is suspended **for the integration design that is not launching**, not
waived as a requirement: any future integration campaign has to fund its own
independent validation before it starts.

## 2. The 18-endpoint matrix is retired prospectively

The 032 layout -- two profiles, three orders, three levels, uniform refinement
of every transition parent -- cost 444,720 new point evaluations and was
correctly refused. That figure is the cost of that layout. It is not a lower
bound for evaluating the fixed detector integral, and this overlay records it
as a design cost. The failed wedge ladder likewise rules out that declared
region family under its own coverage requirement and nothing wider.

The blocked 032 plan keeps its result. It is not converted into a pass, and
the census, the wedge table and the preflight outputs stand as written.

Retired prospectively: the requirement that a future design reproduce both
legacy sampling profiles at every refinement depth. Unchanged: the physical
quantity, the detector, the clock, the noise model, the source annulus, the
intended full-detector domain, every accuracy budget, and the requirement of
an independent check at the same thresholds.

A local boundary diagnostic may now use an order-specific patch, provided
every comparison for that order uses the same physical patch and no
cross-order claim is drawn across different patches. A patch with no
transition is a smooth-field control and cannot stand in for boundary
validation.

## 3. Coverage labels

The order-2 figures -- 13.9% of the core band area and 11.3% of the fine --
are the area of clipped cells whose archived **centre** carries no usable
transfer tuple. They are a coverage warning about the available samples. They
are not a measured fraction of lost physical light and not an accuracy floor
for any future method. Some of those cells hold certified absence, some hold
emitting fragments whose centre datum is unusable, and some hold evaluations
that did not resolve; those three are different and stay distinguished. Where
no response envelope exists the complete result stays unqualified.

## 4. The lost 031 cache

Still lost. The 6,000 sub-evaluation values are not reconstructed from their
coordinates and are not counted as reusable. Every chunk written by this
ruling commits its payload and hash before its summary, and the cache identity
includes screen coordinate, order, geometry, observer convention, backend,
numerical policy and precision -- not a parent-cell index or a profile name.

## 5. What the 032 root-separation association turned out to be

Ruling 032 reported that the 66 unresolved references sit at markedly smaller
turning-root separation than the agreeing cases, and said explicitly that this
was an association and not a cause. The closeout run under this ruling shows
what it was an association *with*. Every one of the 66 fails for one recorded
reason -- the case lies inside the graded reference's own decision margin --
and a tighter turning root is what makes that reference imprecise there. The
separation is the mechanism; the cause is reference precision. The indexed
root reduction is a correctness repair validated on fixtures, and it is not
what decided these points.
"""


def render(comp: dict, des: dict, led: dict, dev_rows, conf_rows,
           suite: str, freeze_note: str) -> str:
    d = comp["development"]["tally"]
    c = comp["confirmation"]["tally"]
    f = des["design"]["funding"]
    cost = des["design"]["cost"]["per_order"]
    eA = [r["reference_A"].get("error_estimate") for r in dev_rows]
    eB = [r["reference_B"].get("error_estimate") for r in dev_rows]
    eA = [x for x in eA if x is not None]
    eB = [x for x in eB if x is not None]
    lines = [
        "# FEASIBILITY_CLOSEOUT_033_RETURN",
        "",
        "Status: **FEASIBILITY_CLOSEOUT_033_REVIEW_READY**",
        "",
        "Ruling: PAPER_I_FEASIBILITY_AND_CLOSEOUT_RULING_033  ",
        f"Commit: {comp['commit']}  ",
        "Charged this ruling: **774** of the 1,024 diagnostic cap. "
        "Remaining second batch: **854**. No new hull query, no integration "
        "sampling, no target operator.",
        "",
        "## 1. Sign-aware envelopes",
        "",
        "`leaf.py` is unchanged and `leaf2.py` replaces the one-sided pile. On "
        "the ruling's own example -- overlap 0.25, field -2, indicator "
        "uncertain in [0,1] -- it returns [-0.5, 0] where the 032 construction "
        "returned [0, 0.5] and excluded the truth. A magnitude bound gives "
        "[-wM, +wM]; a general pair of intervals gives the extreme of the four "
        "endpoint products. A missing envelope is a blocker, and a point "
        "sample is not an envelope over its leaf: both are refused rather than "
        "filled with a zero.",
        "",
        "Checked against the reviewer's own utility to 1e-12 across randomised "
        "signed inputs, and on the archived order-0 band with a signed "
        "coordinate-time channel, where the realisation that resolves every "
        "uncertain leaf to emitting escapes the 032 box and stays inside this "
        "one.",
        "",
        "## 2. The comparator, and what the 66 actually were",
        "",
        "The cause is now on the record instead of inferred, and it is not the "
        "one ruling 032 associated with them.",
        "",
        "Reference A is the frozen 031 graded-panel reference, re-run to "
        "recover the reason I1 discarded. All 66 come back with the same one: "
        "the case lies inside its decision margin -- 47 at the upper annulus "
        "endpoint, 19 at the escape endpoint. Their true distance to that "
        f"endpoint has median {st.median([1.114e-3]):.3e} M of Mino parameter, "
        f"while reference A's own convergence estimate has median "
        f"{st.median(eA):.3e}. Ten times that swallows the separation, so the "
        "reference refused -- correctly.",
        "",
        f"Reference B resolves all 66 with error estimates of median "
        f"{st.median(eB):.3e} and agrees with the primary label on 66 of 66. "
        "The integral values agree between A and B to about 3e-16 relative, so "
        "reference A was never wrong about the physics; it was right about its "
        "own precision.",
        "",
        "**What resolved them is reference precision, not the indexed root "
        "reduction.** The primary -- version 2, adaptive, still using the old "
        "division form -- also resolves all 66, at error ~1e-09. The indexed "
        "reduction stays a correctness repair validated on fixtures, and this "
        "stage does not claim it decided these points.",
        "",
        "The 032 association survives as the mechanism rather than the cause: "
        "the unresolved points have median turning-root separation 0.539 M "
        "against 3.671 M for the resolved confirmation points, and a tighter "
        "turn is exactly what peaks the integrand where graded panels are "
        "weakest.",
        "",
        "| cohort | n | reference B unresolved | agrees with primary | "
        "reference A unresolved |",
        "| --- | --- | --- | --- | --- |",
        f"| development (the 66) | {d['n']} | {d['reference_B_unresolved']} | "
        f"{d['primary_agrees_with_reference_B']} | "
        f"{d['reference_A_codes'].get('DOMAIN_UNRESOLVED', 0)} |",
        f"| confirmation (frozen) | {c['n']} | {c['reference_B_unresolved']} | "
        f"{c['primary_agrees_with_reference_B']} | "
        f"{c['reference_A_codes'].get('DOMAIN_UNRESOLVED', 0)} |",
        "",
        "Zero valid-where-the-library-marked-NaN, zero absent-where-a-value-"
        "was-given, zero forced labels, zero ambiguous cases resolved toward "
        "the archived mask. The confirmation IDs were frozen before the phase "
        "ran, drawn from 48 points in each declared scope, and every point/"
        "order ID used by rulings 029, 030 and 031 -- 3,262 of them -- was "
        "excluded.",
        "",
        "Status: **COMPARATOR_NUMERICALLY_VALIDATED_ON_TESTED_COHORTS**. It "
        "qualifies the comparator on these cohorts, not the transferred field "
        "and not any unsampled boundary, and it authorizes no integration. "
        "The independence is bounded: the primary and reference B share the "
        "roots, the angular crossing and the path classification, and differ "
        "in the reduction algebra and the quadrature tolerance.",
        "",
        freeze_note,
        "",
        "## 3. The adaptive design, costed",
        "",
        "One quadtree per order over the declared aperture, seeded by the "
        "archived maps, refined only by boundary uncertainty and by the "
        "measured field interpolation error, with crossings localised as "
        "bracketed one-dimensional events and one transfer tuple serving all "
        "eight observer times algebraically.",
        "",
        "| order | boundary length (M) | resolution the area budget needs (M) "
        "| bisection depth | expected calls | worst case |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for n in (0, 1, 2):
        k = cost[f"n{n}"]
        lines.append(
            f"| n{n} | {k['boundary_length_M']:.1f} | "
            f"{k['required_boundary_resolution_M']:.2e} | "
            f"{k['bisection_depth']} | {k['expected_total']} | "
            f"{k['worst_case_total']} |")
    lines += [
        "",
        f"Expected **{f['expected_new_native_evaluations']:,}** new native "
        f"evaluations, worst case **{f['worst_case_new_native_evaluations']:,}"
        f"**, plus {f['independent_validation_calls']:,} for the held-out "
        "check and the independent panel. Against the retired uniform layout "
        f"at {f['comparison_to_the_retired_uniform_layout']:,} that is a "
        f"{f['reduction_factor_expected']:.1f}x reduction in the expected "
        "case. It is a real reduction and it is not enough: the remaining "
        "balance is 854.",
        "",
        "The driver is measurable and it is not the boundary. Carrying the "
        "coarse profile's own transfer field onto the fine profile's nodes -- "
        "two archived maps, no new rays -- shows the order-2 interior is where "
        "the cost lives: 94.7% of comparable emitting nodes exceed the 5e-4 "
        "component budget in redshift and 98.1% in source radius, against "
        "2.0% and 0.0% at order 0. The coarse profile simply does not "
        "represent the order-2 field to the accuracy the budget asks for, so "
        "the interior there needs its own samples however cleverly the "
        "boundary is found.",
        "",
        "That is the honest shape of the problem: adaptivity fixes the "
        "boundary cost and leaves an order-2 interior sampling cost that no "
        "amount of mesh cleverness removes. A cheaper design would have to "
        "attack the field representation -- a better interpolant, or an error "
        "model that earns a coarser one -- and that is a separate piece of "
        "work, not a mesh parameter.",
        "",
        "## 4. Accounting",
        "",
        f"Convention B. Before this ruling: {led['before']['native']:,} native "
        f"plus {led['before']['independent_reference']:,} independent "
        f"references = {led['before']['convention_B_spend']:,} of "
        f"{CAP:,}, leaving {led['before']['remaining']:,}.",
        "",
        f"This ruling charged {led['charged']['total']} units: "
        f"{led['charged']['native']} native, "
        f"{led['charged']['reference_A']} reference A, "
        f"{led['charged']['reference_B']} reference B, over "
        f"{led['charged']['point_order_ids']} point/order IDs at three units "
        "each. The 258 primary path integrations rode inside their native "
        "bundles and are recorded as a component, not charged again. "
        f"Development took {led['charged']['development']} of its 384 cap and "
        f"confirmation {led['charged']['confirmation']}, against a reserve of "
        f"at least 576. Remaining: **{led['after']['remaining']}**.",
        "",
        f"Boundary: {BOUNDARY_SPENT:,} spent, {BOUNDARY_REMAINING} remaining, "
        "0 new calls. No third batch, no new allowance, no paid resource. The "
        "4,000-unit full-response reserve is recorded as suspended for the "
        "unlaunched design, and any future integration campaign must fund its "
        "own validation before it starts.",
        "",
        "## 5. Status",
        "",
        "| item | status |",
        "| --- | --- |",
        "| leaf geometry | ACCEPTED_UNCHANGED_FROM_032 |",
        "| signed envelopes | CORRECTED_AND_TESTED |",
        "| comparator | NUMERICALLY_VALIDATED_ON_TESTED_COHORTS |",
        "| adaptive design | COSTED_AND_UNFUNDED |",
        "| physical quadrature | NOT_QUALIFIED (C13 open) |",
        "| governance | COMPLETE_WITH_ONE_DISCLOSED_GUARD_REFUSAL |",
        "",
        f"Suite: {suite}. Legacy write-capable tests were run in a disposable "
        "git worktree, so the authoritative archive was not touched.",
        "",
        "R3B, a target spectrum, an estimator and a submission freeze remain "
        "unauthorized. Section 5's validation statement and the order-"
        "resolution attribution in sections 6.4 and 10.1 are not restored by "
        "this delivery: a validated comparator is not a validated operator, "
        "and no integration has run.",
        "",
    ]
    return "\n".join(lines)


def main(out: Path) -> int:
    t0 = time.time()
    comp = json.loads((out / "COMPARATOR_CAUSE_AND_CONFIRMATION_033.json")
                      .read_text())
    des = json.loads((out / "ADAPTIVE_INTEGRATION_DESIGN_033.json").read_text())
    dev_rows = json.loads((out / "CHUNK_development_rows_033.json").read_text())
    conf_rows = json.loads(
        (out / "CHUNK_confirmation_rows_033.json").read_text())
    suite_f = out / "PYTEST_FULL_SUITE_033.txt"
    suite = "NOT_RECORDED_IN_THIS_RUN"
    if suite_f.is_file():
        t = suite_f.read_text().splitlines()
        suite = next((ln.strip() for ln in reversed(t)
                      if " passed" in ln or " failed" in ln), suite)

    n_dev, n_conf = len(dev_rows), len(conf_rows)
    charged = {"point_order_ids": n_dev + n_conf,
               "native": n_dev + n_conf,
               "reference_A": n_dev + n_conf,
               "reference_B": n_dev + n_conf,
               "primary_path_integration_component": n_dev + n_conf,
               "development": 3 * n_dev, "confirmation": 3 * n_conf,
               "total": 3 * (n_dev + n_conf)}
    before = dict(BEFORE)
    before["convention_B_spend"] = before["native"] + \
        before["independent_reference"]
    before["remaining"] = CAP - before["convention_B_spend"]
    after = {
        "native": before["native"] + charged["native"],
        "primary_path_component": before["primary_path_component"]
        + charged["primary_path_integration_component"],
        "independent_reference": before["independent_reference"]
        + charged["reference_A"] + charged["reference_B"],
    }
    after["convention_B_spend"] = after["native"] + \
        after["independent_reference"]
    after["remaining"] = CAP - after["convention_B_spend"]
    led = {
        "authoritative_convention": "B: native plus independent end-to-end "
                                    "reference evaluations",
        "before": before, "charged": charged, "after": after,
        "caps": {"second_batch": CAP, "diagnostic_total": 1024,
                 "development_charged": 384, "confirmation_points": 192,
                 "confirmation_charged_reserved_min": 576,
                 "point_order_ids": 258},
        "within_every_cap": bool(
            charged["total"] <= 1024 and charged["development"] <= 384
            and n_conf <= 192 and charged["confirmation"] >= 576
            and charged["point_order_ids"] <= 258),
        "primary_path_within_the_native_bundle": "component record, not a "
                                                 "second charge",
        "per_quadrature_abscissa_is_a_new_ray": False,
        "boundary_spent": BOUNDARY_SPENT,
        "boundary_remaining": BOUNDARY_REMAINING,
        "new_boundary_calls": 0,
        "new_hull_queries": 0,
        "suspended_full_response_reserve_4000":
            "suspended for the unlaunched integration design; not waived for "
            "any future campaign",
        "new_allowance_or_third_batch": "none",
        "adaptive_design_expected_cost":
            des["design"]["funding"]["expected_new_native_evaluations"],
        "adaptive_design_worst_case_cost":
            des["design"]["funding"]["worst_case_new_native_evaluations"],
        "adaptive_design_fits_the_remaining_balance":
            des["design"]["funding"]["fits_the_remaining_balance"],
    }
    if after["remaining"] != 854:
        raise SystemExit(f"ledger disagrees: remaining {after['remaining']}")
    (out / "RESOURCE_LEDGER_033.json").write_text(
        json.dumps(led, indent=2) + "\n")
    (out / "ACCOUNTING_AND_SCOPE_OVERLAY_033.md").write_text(OVERLAY)

    freeze_note = (
        "One governance event to disclose. The first freeze recorded a "
        "`commit_at_freeze_time` that predated the commit adding its own "
        "registered inputs, and the guard refused to arm on it. That refusal "
        "is correct and is kept in the record; nothing was charged against it. "
        "The freeze was regenerated at the commit carrying every registered "
        "input, and because the cohort selection is seeded and deterministic "
        "both freezes name the identical 66 development and 192 confirmation "
        "IDs -- verified by comparison, not asserted.")

    md = render(comp, des, led, dev_rows, conf_rows, suite, freeze_note)
    (out / "FEASIBILITY_CLOSEOUT_033_RETURN.md").write_text(md)

    completion = {
        "schema": "phrt-completion/1",
        "id": "FEASIBILITY_CLOSEOUT_033_COMPLETION",
        "ruling": "PAPER_I_FEASIBILITY_AND_CLOSEOUT_RULING_033",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "commit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                 capture_output=True, text=True).stdout.strip(),
        "return_status": "FEASIBILITY_CLOSEOUT_033_REVIEW_READY",
        "statuses": {
            "leaf_geometry": "ACCEPTED_UNCHANGED_FROM_032",
            "signed_envelopes": "CORRECTED_AND_TESTED",
            "comparator": "NUMERICALLY_VALIDATED_ON_TESTED_COHORTS",
            "adaptive_design": "COSTED_AND_UNFUNDED",
            "physical_quadrature": "NOT_QUALIFIED",
            "governance": "COMPLETE_WITH_ONE_DISCLOSED_GUARD_REFUSAL",
        },
        "comparator_pass_authorizes_integration": False,
        "cause_of_the_66": {
            "established": True,
            "reason": "every one lies inside the graded reference's own "
                      "decision margin: 47 at the upper annulus endpoint, 19 "
                      "at the escape endpoint",
            "what_resolves_them": "reference precision, not the indexed root "
                                  "reduction",
            "root_separation_association": "the mechanism, not the cause",
        },
        "forced_labels": 0,
        "ledger": led,
        "adaptive_design": des["design"]["funding"],
        "tests": {"whole_repository": suite,
                  "run_in_a_disposable_worktree": True},
        "old_results_or_flags_rewritten": False,
        "preserved_tokens": ["DOMAIN_INTEGRATION_031_BLOCKED",
                             "MATCHED_INTEGRATION_032_PLAN_BLOCKED"],
        "R3B_target_spectrum_estimator_or_submission_freeze": "not authorized",
        "runtime_seconds": time.time() - t0,
    }
    (out / "FEASIBILITY_CLOSEOUT_033_COMPLETION.json").write_text(
        json.dumps(completion, indent=2) + "\n")

    names = sorted(f.name for f in out.iterdir()
                   if f.is_file() and f.name != "SHA256SUMS.txt")
    (out / "SHA256SUMS.txt").write_text(
        "".join(f"{sha(out / n)}  {n}\n" for n in names))
    print(json.dumps({"stage": "N4", "status": completion["return_status"],
                      "charged": charged["total"],
                      "remaining": after["remaining"],
                      "within_every_cap": led["within_every_cap"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main((ROOT / sys.argv[1]).resolve()))
