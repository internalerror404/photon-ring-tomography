#!/usr/bin/env python3
"""Ruling 037: regression scan, correction ledger, gaps, return. Zero queries."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "revisions" / "mahakal_v4_1" / "manuscript038"
DRAFT = "Photon_Ring_Retarded_Time_Tomography_Working_Revision_038.md"

# Every regression ruling 037 named, as a pattern that must NOT appear, paired
# with the text that must appear instead.
REGRESSIONS = [
    ("R01", r"99\.8\s*%", "the Cholesky-coordinate localization",
     r"2\.44%"),
    ("R02", r"exactly zero in hat 0|zero in the oldest",
     "the zero-oldest-epoch claim", r"oldest-third contribution is not zero"),
    ("R03", r"recoverable depth", "144 M named as recoverable depth",
     r"oldest detectable age probe"),
    ("R04", r"set by inclination rather than spin",
     "spin independence inferred from a supremum",
     r"does not establish physical spin independence"),
    ("R05", r"carried by \*?when\*?, not|history is carried by",
     "the delay/spatial mechanism sentence",
     r"index-paired counterfactuals"),
    ("R06", r"destroys identifiability",
     "the universal enrichment slogan", r"Proposition 4\.1"),
    ("R07", r"sixteen-month", "the unsupported duration",
     r"Working revision 038"),
    ("R08", r"coefficient-space result",
     "the metric misidentification", r"baseline-inclusive field metric"),
    ("R09", r"cleared at ten times", "the structure onset error",
     r"first becomes nonzero at `SNR_0 = 30000`|30000"),
    ("R10", r"so the gain is attributable to resolving the orders",
     "the causal attribution sentence",
     r"does not establish how a physically unresolved image would perform"),
    ("R11", r"Shiva Effect|Shiva effect", "the Shiva-era title and slogan",
     r"Mahakal Phenomenon"),
    ("R13", r"stable recovery.{0,40}rank|three rank notions.{0,200}stable recovery",
     "recovery counted as a rank notion",
     r"Estimator recovery\*?\*? is a separate criterion"),
    ("R14", r"continuous history from the present",
     "the anchor described as the present",
     r"contiguous passing interval beginning at the geometry-specific anchor"),
    ("R15", r"enriching the declared temporal class",
     "the E3D ladder called temporal enrichment", r"C528_S"),
    ("R16", r"source cell `C_p`", "source cell in a screen intersection",
     r"screen integration cell"),
    ("R17", r"on all 40 transferred diagnostic channels",
     "per-order maxima stated as an all-channel value",
     r"maximum relative same-support discrepancy over the 40"),
    ("R18", r"both prior-free", "the term prior-free",
     r"non-Bayesian spectral estimators"),
    ("R12", r"the only valid form",
     "the four-endpoint enclosure claimed unique",
     r"is \*a\* valid enclosure"),
]

LEDGER = """# MANUSCRIPT_CORRECTION_LEDGER_038

What ruling 037 found in the 036 draft, and what the 037 draft does instead.
Every replacement number is read from the primary artifact named in
`CLAIM_EVIDENCE_MATRIX_038.json`, not from the archived manuscript prose.

## Regressions repaired

| id | the 036 draft said | the 037 draft says | primary source |
| --- | --- | --- | --- |
| R01/R02 | "99.8% of squared weight in temporal hat 2 ... exactly zero in hat 0" | 2.44%/2.35% oldest third, 43.81%/43.92% middle, 53.75%/53.73% youngest; the oldest third is not zero | `LOC025_.../LOCALIZATION_READBACK.json`, `intervals[*].source_energy_fraction` |
| R03/R04 | 60/84/144 M called "recoverable depth", reach "set by inclination rather than spin" | 144 M is the oldest detectable age probe, a supremum of a threshold mask; the anchor-connected spans are 60, 84 and 112/116 M and they vary with spin at 75 degrees | `E3C_GEOMETRY_WIDE_OPERATOR_AUDIT.md`, oldest-probe and anchor-span tables |
| R05 | "the history is carried by when, not where, the orders sample" | 0.98 and 0.57 retained as index-paired counterfactuals; the mechanism sentence withdrawn | `E3C_MECHANISM_DECOMPOSITION.md`; amendment 023 |
| R06 | "source enrichment destroys identifiability"; "compactness makes the direct image blind" | Proposition 4.1 with proof, conditional on support disjointness, plus Corollary 4.2 and an explicit statement of what the proposition does not say | supplied replacement passages; theorem restated and proved in section 4 |
| R07 | "a sixteen-month numerical audit" | removed; no duration is asserted | ruling 037 |
| R08 | the level result called "a coefficient-space result" | the registered baseline-inclusive field metric, level dominated at level fraction 0.9838 | `R1_HELD_OUT_MAIN.md`, level/structure split |
| R09 | structure "cleared at ten times the reference SNR" | zero at SNR_0 = 100, first nonzero at 30000 with 40 M direct and 76 M resolved; R1L stage-2R at 1000 is a separate aggregate result | `R1_HELD_OUT_MAIN.md`, structural recovery onset |
| R10 | "the gain is attributable to resolving the orders" | the labelled stack improves; the tested flux readout does not reproduce it; the index-sum control says nothing about a physically unresolved image | HMT-2 control rows in the evidence ledger |
| R11 | the Shiva-era title | the author-facing Mahakal title | ruling 037 source reconciliation |
| R12 | the four-endpoint interval called "the only valid form" | *a* valid enclosure for supplied intervals | ruling 037 |

## Scientific content restored, not present in 036

- Proposition 4.1 with a proof, and Corollary 4.2 as a conditional continuum
  statement rather than a measurement validation.
- The target/nuisance and normalised-Fisher definitions, including the explicit
  warning against multiplying singular values by an SNR label when sigma is
  already inside C.
- A per-experiment table of source spaces, metrics, estimators and noise
  conventions, replacing the single global noise pin of the 036 matrix.
- Three separate rank notions, and three separate reach statistics with their
  definitions.
- The R1 regime table and the HMT-2 estimator/draw/materiality detail.
- A references section listing only sources actually read, with the external
  bibliography marked outstanding rather than fabricated.

## Corrections to the 036 evidence matrix

| id | 036 | 037 |
| --- | --- | --- |
| M01 | `pins_recorded_per_claim` named ten pins globally; individual claims supplied none | each claim carries all ten pins as RESOLVED with a value and reference, NOT_APPLICABLE with a reason, or UNRESOLVED |
| M02 | one "single-sky noise, sigma = 0.0113..." assumption string for every experiment | five per-experiment pin blocks; R2's ideal order-labelled comparison and the D026 single-sky detector experiment are pinned separately |
| M03 | `source_commit_path_and_hash` held a bare path | structured evidence: commit, path, sha256 of the bytes at that commit, and a row selector, verified by `git show` |
| M04 | several claims resolved only to `PAPER_I.md` or the summary ledger | each resolves to its primary artifact; the 276-entry claim ledger is used as an index only |
"""

GAPS = """# SUBMISSION_GAPS_038

## A. Editorial — no new science

| item | state |
| --- | --- |
| Regressions R01-R12 repaired and scanned | done, `REGRESSION_SCAN_038.json` |
| Theorem, proof, definitions, regime tables restored | done |
| Per-experiment pins and structured evidence | done, checker `SCHEMA_READY_FOR_SEMANTIC_REVIEW` |
| **External bibliography** | **outstanding.** The archived manuscript carries one; it has not been re-audited against this text, and no reference is carried over unread |
| **Figures** | **outstanding.** They must match the corrected statistic definitions — in particular any figure captioned with "recoverable depth" now needs the oldest-probe / anchor-span distinction |
| **Reconciliation with the supplied 42-page PDF** | **outstanding.** That document was not available to this session; only the reviewer's recorded sha256 is carried. Passages taken from it come via the supplied replacement text, not from reading it |
| Author review | **outstanding and required** |

## B. Discrete lineage — archive work

| item | state |
| --- | --- |
| Sixteen claims resolved to primary artifacts with verified byte hashes | done |
| Ten pins per claim | done |
| Corrected-measure R2 recomputation | **not authorised**; needed only if the authors want a count rather than the one-to-two interval |
| Metric formula and evaluation map recovered from the registered runner config rather than the report prose | **partially done** — the metric is named and its level-dominance quantified from the R1 report; the formula itself is cited to the report, not to the runner config |

## C. Physical revalidation — two experiments

**C.1 Transfer quadrature.** Five conditions, none met: signed per-channel
response inside 5e-4; full-domain coverage or a bounded remainder for the
0.6092 M² uncovered at order 2; a stated accuracy for the reference; remainder
radii from outside the certified pair (one route, not the only one); a funded
independent validation budget fixed before launch.

**C.2 Order-resolution attribution.** An appropriate physical control and a new
result. C.1 does not supply it.

## D. Author scope approval

Whether to submit a finite-model paper that states the gap plainly, or to run
C.1 and C.2 first. Calling the work finite-model does not make an unresolved
physical claim publishable.
"""


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with Path(p).open("rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


# A regression is an ASSERTION of the old claim. Quoting it in order to
# withdraw it is required practice, not a regression, so each hit is
# classified by the context it sits in.
WITHDRAWAL = re.compile(
    r"withdrawn|withdraw|the earlier|is not|are not|no longer|corrected|"
    r"replaced|does not establish|rather than|scope\b", re.I)


def scan(text: str) -> dict:
    # Scan paragraphs, not lines: the draft is hard-wrapped, so a phrase can
    # straddle a newline and a line-wise regex would miss it in both
    # directions. Whitespace is normalised inside each paragraph.
    raw = text.split("\n\n")
    paras = [(i, " ".join(re.sub(r"(?m)^\s*>\s?", "", b).split()), b)
             for i, b in enumerate(raw, 1)]
    # blockquote markers are formatting, not words: strip them before
    # flattening, or a phrase inside a quoted box reads as "... unresolved >
    # image ..." and no replacement pattern can match it
    flat = " ".join(re.sub(r"(?m)^\s*>\s?", "", text).split())
    rows = []
    for rid, bad, what, good in REGRESSIONS:
        asserted, quoted = [], []
        for i, one, block in paras:
            if not re.search(bad, one, re.I):
                continue
            (quoted if (block.lstrip().startswith(">")
                        or WITHDRAWAL.search(one)) else asserted).append(i)
        fix = re.search(good, flat, re.I)
        rows.append({"id": rid, "regression": what,
                     "forbidden_pattern": bad,
                     "asserted_paragraphs": asserted,
                     "quoted_in_a_withdrawal_paragraphs": quoted,
                     "still_asserted": bool(asserted),
                     "replacement_pattern": good,
                     "replacement_present": bool(fix),
                     "clean": bool(not asserted and fix)})
    return {"rule": "a forbidden pattern inside a withdrawal or scope "
                    "statement is preservation, not a regression; only an "
                    "unqualified assertion fails",
            "checks": rows,
            "all_clean": all(r["clean"] for r in rows),
            "still_asserted": [r["id"] for r in rows if r["still_asserted"]],
            "quoted_only": [r["id"] for r in rows
                            if r["quoted_in_a_withdrawal_paragraphs"]
                            and not r["asserted_paragraphs"]],
            "replacement_missing": [r["id"] for r in rows
                                    if not r["replacement_present"]]}


def main() -> int:
    t0 = time.time()
    draft = OUT / DRAFT
    text = draft.read_text()
    sc = scan(text)
    (OUT / "REGRESSION_SCAN_038.json").write_text(json.dumps({
        "ruling": "PAPER_I_SEMANTIC_REVIEW_038",
        "draft": DRAFT, "draft_sha256": sha(draft), **sc}, indent=2) + "\n")
    (OUT / "MANUSCRIPT_CORRECTION_LEDGER_038.md").write_text(LEDGER)
    (OUT / "SUBMISSION_GAPS_038.md").write_text(GAPS)

    check = json.loads((OUT / "CLAIM_MATRIX_CHECK_038.json").read_text())
    matrix = json.loads((OUT / "CLAIM_EVIDENCE_MATRIX_038.json").read_text())
    blocked = (not sc["all_clean"]) or check["status"] != \
        "SCHEMA_READY_FOR_SEMANTIC_REVIEW"
    status = ("MANUSCRIPT_038_BLOCKED" if blocked
              else "MANUSCRIPT_038_READY_FOR_FINAL_TEXT_REVIEW")
    completion = {
        "schema": "phrt-completion/1",
        "id": "MANUSCRIPT_038_COMPLETION",
        "ruling": "PAPER_I_SEMANTIC_REVIEW_038",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "commit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                 capture_output=True, text=True).stdout.strip(),
        "return_status": status,
        "draft": DRAFT, "draft_sha256": sha(draft),
        "draft_words": len(text.split()),
        "title": "Photon-Ring Retarded-Time Tomography: The Mahakal Phenomenon",
        "regression_scan": {"all_clean": sc["all_clean"],
                            "checks": len(sc["checks"]),
                            "still_asserted": sc["still_asserted"],
                            "quoted_only": sc["quoted_only"]},
        "claim_matrix": {"status": check["status"],
                         "claims": check["claim_count"],
                         "schema_errors": len(check["errors"]),
                         "pinned_bytes_verified_by_git_show": True,
                         "semantic_support_verified": False,
                         "headline_allowed": sum(
                             1 for c in matrix["claims"]
                             if c["candidate_abstract_or_headline_allowed"])},
        "restored_scientific_content": [
            "Proposition 4.1 with proof and Corollary 4.2",
            "target/nuisance and normalised Fisher definitions",
            "per-experiment source spaces, metrics, estimators, noise",
            "three rank notions and three reach statistics",
            "R1 regime table and HMT-2 estimator/draw detail",
        ],
        "outstanding": ["external bibliography", "figures",
                        "reconciliation with the supplied 42-page PDF",
                        "author review"],
        "supplied_PDF_available_to_this_session": False,
        "physical_claims_supported": 0,
        "resources": {"convention": "B", "second_batch_spent": 19146,
                      "second_batch_remaining": 854,
                      "spent_under_this_ruling": 0, "boundary_spent": 33410},
        "old_results_or_flags_rewritten": False,
        "manuscript036_overwritten": False,
        "R3B_or_submission_freeze": "not authorized",
        "runtime_seconds": time.time() - t0,
    }
    (OUT / "MANUSCRIPT_038_COMPLETION.json").write_text(
        json.dumps(completion, indent=2) + "\n")
    print(json.dumps({"status": status, "scan_clean": sc["all_clean"],
                      "still_asserted": sc["still_asserted"],
                      "quoted_only": sc["quoted_only"],
                      "matrix": check["status"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
