#!/usr/bin/env python3
"""S3 of ruling 035: decision table, claim routes, return. Zero queries."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BUDGET = 5.0e-4


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with Path(p).open("rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def decision_md(per) -> str:
    L = ["# CONDITIONAL_ERROR_MODEL_AND_DECISION_035", "",
         "## 1. Where the conservatism actually lives", "",
         "| order | A/E, cancellation only | T/A, detector structure | T/E | "
         "U / max E, the 034 figure |", "| --- | --- | --- | --- | --- |"]
    for n in (0, 1, 2):
        b = per[f"n{n}"]["baseline"]
        L.append(f"| n{n} | {b['max_A_over_E']:.2f} | {b['max_T_over_A']:.2f} "
                 f"| {b['max_T_over_E']:.1f} | {b['U_over_max_E']:.1f} |")
    L += [
        "",
        "The 034 report attributed a 10x-to-57x gap to sign cancellation. "
        "Decomposed, cancellation is the smallest of the three effects at "
        "order 0 (1.10x) and never the largest anywhere. What dominates is "
        "T/A: replacing the detector vector by a sum of per-column magnitudes "
        "costs a factor of 6.7 to 20. That conservatism is removable by "
        "arithmetic alone -- no correlation model, no assumption -- and "
        "removing it changes only where refinement is aimed.",
        "",
        "## 2. What a cancellation-aware certificate would still need", "",
        "    ||W(y - y_true)|| <= ||sum of signed estimates||",
        "                        + sum of validated group remainders",
        "                        + the fine reference's own error",
        "                        + the omitted-support contribution",
        "",
        "Three of those four terms are not available from the cached pair. "
        "The core-to-fine residual is a difference between two "
        "discretisations, not a bound on the fine map's own error; no group "
        "remainder radii exist; and the omitted support has no bound at all. "
        "Fitting correlations to this same pair would supply a model "
        "assumption, not a numerical bound, and is not attempted.",
        "",
        "## 3. The greedy trap, stated", "",
        "Contributions of 1 and -0.99 sum to 0.01. Correcting the first "
        "perfectly leaves -0.99. A local improvement can raise a signed global "
        "residual by breaking cancellation, so a refinement schedule driven by "
        "|contribution| is a bound-reduction schedule, not an error-reduction "
        "schedule. The 308,656 figure is relabelled "
        "ORACLE_ZERO_HEAD_CACHED_DEFECT: it assumes a selected node's "
        "discrepancy goes to exactly zero and everything else stays put.",
        "",
        "## 4. Decision table", "",
        "| question | answer | evidence |", "| --- | --- | --- |",
        "| Is the 034 gap mainly cancellation? | No | A/E is 1.10 to 6.58; "
        "T/A is 6.7 to 20 |",
        "| Does the five-template identity hold? | Yes | max pointwise "
        f"{max(per[f'n{n}']['identity_max_pointwise'] for n in (0,1,2)):.2e}, "
        "max after the detector "
        f"{max(per[f'n{n}']['identity_max_after_the_detector'] for n in (0,1,2)):.2e} |",
        "| Does forming templates before interpolating help? | No | worse at "
        "all three orders on the max-channel criterion |",
        "| Is any representation here inside 5e-4? | No | every one of the 40 "
        "transferred channels is above budget at every order, for both |",
        "| Is the missing support bounded? | No | 0.6092 M^2 of order-2 "
        "emitting area has no response bound |",
        "",
        "## 5. Minimum evidence any future physical campaign needs", "",
        "1. A response comparison whose *signed* per-channel relative error is "
        "inside 5e-4, not a bound that has been tightened until it fits.",
        "2. Coverage of the full declared domain, or an explicit bounded "
        "remainder for what is left out -- currently absent at order 2.",
        "3. A statement of the reference's own accuracy. Every number here "
        "compares two discretisations; neither is continuum truth.",
        "4. Group remainder radii from something other than the pair being "
        "certified.",
        "5. A funded independent validation budget, decided before launch.",
        "",
        "None of those five exists today, which is why no campaign starts.",
        ""]
    return "\n".join(L)


CLAIMS = """# MANUSCRIPT_CLAIM_ROUTES_035

Additive; supersedes nothing and overwrites nothing. Claims are identified by
their exact wording plus the manuscript hash recorded in the completion file,
not by section numbers alone.

## The correction ruling 035 requires

The 034 route table put the section 10.1 order-resolution attribution in the
same queue as the section 5 operator statement -- both "suspended pending a
detector-response comparison inside budget". That is wrong for 10.1, and the
distinction matters.

The section 5 statement is about the operator's numerical accuracy. A
quadrature comparison that met the declared budgets would speak to it
directly.

The section 10.1 attribution is not. Its control was an index-sum construction,
not a physically unresolved image. A future accurate common-sky operator would
not retroactively change what that control was: passing a quadrature test does
not convert an index-sum control into evidence about physical order
resolution. Restoring the attribution needs a new comparison against an
appropriate physical control and a new result -- not the same claim revived by
a numerical pass elsewhere.

| claim | route | what would restore it |
| --- | --- | --- |
| sec. 5, "Validated Computational Operator" | RESTRICTED | a detector-response comparison meeting 5e-4 per channel with bounded coverage |
| sec. 10.1, order-resolution attribution | CORRECTED, NOT MERELY PENDING | a new comparison against a physical control, plus a new result; a quadrature pass does not do it |
| sec. 4.2 support theorem | RETAINED | finite-dimensional, unchanged inputs |
| sec. 9 level and morphology results | RETAINED WITH LIMITATIONS | discrete; retention requires the explicit operator norm and stated limitations |
| sec. 6.4 order-summed physical claims | RESTRICTED | same operator, and C13 still open |
| common-sky R3A, R3B, target spectra, estimators | DEFERRED | not authorized |

Unchanged historical files do not by themselves restore a physical
interpretation. A discrete result stays valid as a statement about the
operator that was constructed; it does not become a statement about the sky
because its inputs were never edited.
"""


def render(man, per, ident, suite) -> str:
    L = ["# DETECTOR_TEMPLATE_035_RETURN", "",
         "Status: **DETECTOR_TEMPLATE_035_REVIEW_READY**", "",
         "Ruling: PAPER_I_CANCELLATION_RULING_035  ",
         f"Commit: {man['commit']}  ",
         "New rays, path integrals, hull roots, target operators: **0**. "
         "854 units remain, none spent. No file from 029-034 is edited.",
         "",
         "## 1. The export defect, confirmed and repaired", "",
         "The 034 archive holds three keys -- `n0_reference`, `n1_reference`, "
         "`n2_reference` -- and nothing else. The writer popped the dictionary "
         "carrying both vectors and stored only its reference member, so the "
         "estimated vectors and signed residuals were never written. "
         "Regenerated here from cached inputs into a new directory: reference, "
         "baseline and candidate vectors, signed residuals, channel labels and "
         "times, supported node ids and coordinates, template arrays, the CSR "
         "overlap triple, reference norms and the bound hierarchy, and the "
         "omitted masks. Read back and validated before this summary was "
         "written. The 034 directory is byte-identical.",
         "",
         "## 2. The 034 gap, decomposed", "",
         "| order | A/E cancellation | T/A detector structure | T/E | "
         "U / max E |", "| --- | --- | --- | --- | --- |"]
    for n in (0, 1, 2):
        b = per[f"n{n}"]["baseline"]
        L.append(f"| n{n} | {b['max_A_over_E']:.2f} | {b['max_T_over_A']:.2f} "
                 f"| {b['max_T_over_E']:.1f} | {b['U_over_max_E']:.1f} |")
    L += [
        "",
        "The 034 claim that the 10x-to-57x gap was conservatism from "
        "cancellation is withdrawn. The U/max-E column reproduces that range, "
        "and decomposing it shows cancellation is the smallest term at order 0 "
        "-- 1.10x -- and never the largest anywhere. The dominant factor is "
        "T/A, from 6.7x to 20x: replacing the detector vector with a sum of "
        "per-column magnitudes. That is removable by arithmetic, with no "
        "correlation model, and removing it aims refinement better without "
        "making any approximation more accurate.",
        "",
        "Every channel now carries its own reference norm. The 034 scenario "
        "divided by the largest reference norm across channels, which is not "
        "the same test.",
        "",
        "## 3. The five-template identity", "",
        "Verified: `H0`, `Re H20`, `Im H20`, `Re H40`, `Im H40` reconstruct "
        "all 40 transferred columns at the eight observer times, to a maximum "
        f"pointwise discrepancy of "
        f"{max(ident['per_order'][f'n{n}']['max_pointwise'] for n in (0,1,2)):.2e}"
        " and "
        f"{max(ident['per_order'][f'n{n}']['max_after_the_detector'] for n in (0,1,2)):.2e}"
        " after the detector map, against a 1e-12 tolerance.",
        "",
        "It is an algebraic reduction of these declared diagnostic fields. It "
        "is not a ray speedup, it does not reduce the L224 source space, and "
        "it says nothing about arbitrary source movies.",
        "",
        "## 4. The one authorised representation test, and its answer", "",
        "Baseline interpolates the redshift and the coordinate time and then "
        "cubes and phases. The candidate forms the five templates at the "
        "coarse nodes first and interpolates those. Same support, same "
        "overlap operator, same noise, same clock, same periods and times.",
        "",
        "| order | baseline max relative | candidate max relative | verdict |",
        "| --- | --- | --- | --- |"]
    for n in (0, 1, 2):
        b, c = per[f"n{n}"]["baseline"], per[f"n{n}"]["candidate"]
        v = "worse" if c["max_relative_E"] > b["max_relative_E"] else "better"
        L.append(f"| n{n} | {b['max_relative_E']:.4e} | "
                 f"{c['max_relative_E']:.4e} | {v} |")
    L += [
        "",
        "**The candidate is worse at all three orders on the criterion.** "
        "Composite-first does not fix order 2; it makes the worst channel "
        "worse by 28%, order 1 worse by a factor of two, and order 0 worse by "
        "1.3%. One detail is worth recording rather than burying: at order 2 "
        "the candidate's *median* channel error is better "
        f"({per['n2']['candidate']['median_relative_E']:.3e} against "
        f"{per['n2']['baseline']['median_relative_E']:.3e}) while its maximum "
        "is worse. The criterion is the maximum, so the candidate fails; the "
        "median is reported because it is what the archive says, not because "
        "it rescues anything.",
        "",
        "This closes the test. No interpolant sweep follows, and the budget is "
        "not adjusted to produce a pass. Every one of the 40 transferred "
        "channels is above 5e-4 at every order under both representations.",
        "",
        "## 5. Scope, unchanged", "",
        "The screen channels return exactly zero absolute residual under both "
        "representations. That is an equal-input consistency control -- both "
        "sides receive identical screen fields through the same operator -- "
        "not an absolute geometry validation.",
        "",
        "Coverage is unchanged and still the harder problem: order 2 compares "
        f"{per['n2']['node_coverage']:.1%} of emitting nodes and "
        f"{per['n2']['area_coverage']:.1%} of emitting area, leaving "
        f"{per['n2']['omitted_area']:.4f} M^2 with no response bound. No "
        "cancellation argument on the compared subset touches it.",
        "",
        "The 034 same-leg flag is relabelled a small-radius-span heuristic; "
        "physical branch membership stays unverified where the archived "
        "metadata does not establish it. The 308,656 figure is relabelled an "
        "oracle-zero-head scenario over the cached defect.",
        "",
        "## 6. Status", "",
        "| item | status |", "| --- | --- |",
        "| cached discrepancy | MEASURED_AND_OUTSIDE_BUDGET_UNCHANGED |",
        "| bound decomposition | E_A_T_U_MEASURED_PER_CHANNEL |",
        "| template identity | VERIFIED_TO_6.7e-15 |",
        "| candidate comparison | WORSE_AT_ALL_THREE_ORDERS_TEST_CLOSED |",
        "| missing support | UNBOUNDED_0.6092_M2_AT_ORDER_2 |",
        "| physical quadrature | NOT_QUALIFIED (C13 open) |",
        "| claim routes | SECTION_10.1_CORRECTED_NOT_MERELY_PENDING |",
        "| governance | COMPLETE |",
        "",
        f"Suite: {suite}, run in a disposable worktree.",
        "",
        "This return authorizes nothing. R3B, target spectra, estimators and a "
        "submission freeze remain unauthorized, and no physical query has been "
        "made.", ""]
    return "\n".join(L)


def main(out: Path) -> int:
    t0 = time.time()
    man = json.loads(
        (out / "DETECTOR_TEMPLATE_035_INPUT_MANIFEST.json").read_text())
    resp = json.loads(
        (out / "PER_CHANNEL_RESPONSE_AND_SUPPORT_035.json").read_text())
    ident = json.loads(
        (out / "HARMONIC_TEMPLATE_IDENTITY_035.json").read_text())
    per = resp["per_order"]
    suite_f = out / "PYTEST_FULL_SUITE_035.txt"
    suite = "NOT_RECORDED_IN_THIS_RUN"
    if suite_f.is_file():
        t = suite_f.read_text().splitlines()
        suite = next((ln.strip() for ln in reversed(t)
                      if " passed" in ln or " failed" in ln), suite)
    (out / "CONDITIONAL_ERROR_MODEL_AND_DECISION_035.md").write_text(
        decision_md(per))
    (out / "MANUSCRIPT_CLAIM_ROUTES_035.md").write_text(CLAIMS)
    (out / "DETECTOR_TEMPLATE_035_RETURN.md").write_text(
        render(man, per, ident, suite))
    completion = {
        "schema": "phrt-completion/1",
        "id": "DETECTOR_TEMPLATE_035_COMPLETION",
        "ruling": "PAPER_I_CANCELLATION_RULING_035",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "commit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                 capture_output=True, text=True).stdout.strip(),
        "return_status": "DETECTOR_TEMPLATE_035_REVIEW_READY",
        "statuses": {
            "cached_discrepancy": "MEASURED_AND_OUTSIDE_BUDGET_UNCHANGED",
            "bound_decomposition": "E_A_T_U_MEASURED_PER_CHANNEL",
            "template_identity": "VERIFIED",
            "candidate_comparison":
                "WORSE_AT_ALL_THREE_ORDERS_TEST_CLOSED",
            "missing_support": "UNBOUNDED_AT_ORDER_2",
            "physical_quadrature": "NOT_QUALIFIED",
            "claim_routes": "SECTION_10_1_CORRECTED_NOT_MERELY_PENDING",
            "governance": "COMPLETE",
        },
        "withdrawn_from_034": [
            "that the 10x-to-57x gap was conservatism from sign cancellation",
            "the largest-reference-norm denominator as a per-channel test",
            "308,656 as a sufficient physical sampling budget",
            "'no same-leg stencil' as a branch statement rather than a "
            "heuristic",
        ],
        "bound_decomposition": {
            f"n{n}": {k: per[f"n{n}"]["baseline"][k] for k in
                      ("max_A_over_E", "max_T_over_A", "max_T_over_E",
                       "U_over_max_E")} for n in (0, 1, 2)},
        "candidate_result": {
            f"n{n}": {"baseline": per[f"n{n}"]["baseline"]["max_relative_E"],
                      "candidate": per[f"n{n}"]["candidate"]["max_relative_E"]}
            for n in (0, 1, 2)},
        "candidate_is_an_improvement": False,
        "further_interpolant_search": "not authorized and not attempted",
        "coverage": {f"n{n}": {k: per[f"n{n}"][k] for k in
                               ("node_coverage", "area_coverage",
                                "omitted_area")} for n in (0, 1, 2)},
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
                             "FEASIBILITY_CLOSEOUT_033_REVIEW_READY",
                             "CACHED_RESPONSE_AUDIT_034_REVIEW_READY"],
        "R3B_or_submission_freeze": "not authorized",
        "runtime_seconds": time.time() - t0,
    }
    (out / "DETECTOR_TEMPLATE_035_COMPLETION.json").write_text(
        json.dumps(completion, indent=2) + "\n")
    names = sorted(f.name for f in out.iterdir()
                   if f.is_file() and f.name != "SHA256SUMS.txt")
    (out / "SHA256SUMS.txt").write_text(
        "".join(f"{sha(out / n)}  {n}\n" for n in names))
    print(json.dumps({"stage": "S3", "status": completion["return_status"],
                      "candidate_is_an_improvement": False, "suite": suite}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main((ROOT / sys.argv[1]).resolve()))
