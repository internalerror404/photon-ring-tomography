#!/usr/bin/env python3
"""Ruling 036: input manifest, claim matrix, correction ledger, gaps, return.

Zero physical queries. Every row below points at a file that is hashed in the
manifest; a claim whose source cannot be resolved is recorded UNRESOLVED rather
than given a number.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT_ROOT = ROOT / "docs" / "revisions" / "mahakal_v4_1" / "manuscript036"
DRAFT = ("Photon_Ring_Retarded_Time_Tomography_Working_Revision_036.md")

PINNED = "artifacts/manuscript/PAPER_I.md"
LEDGER = "artifacts/manuscript/CLAIM_LEDGER.json"
FREEZE = "artifacts/CANONICAL_ARTIFACT_FREEZE_V2.json"
EVID = "docs/Paper_I_v1_Current_Evidence_Ledger.md"
R2 = ("artifacts/revisions/mahakal_v4_1/R2REPLAY_20260906T144528Z_b873908/"
      "R2_CLOSEOUT_REPORT.md")
R2CSV = ("artifacts/revisions/mahakal_v4_1/R2REPLAY_20260906T144528Z_b873908/"
         "reference_geometry_information.csv")
G1C = ("artifacts/revisions/mahakal_v4_1/G1C_20260907T075203Z_d252697/"
       "GEOMETRY_CLOSEOUT_029.json")
N033 = ("artifacts/revisions/mahakal_v4_1/N033B_20260907T211922Z_45bd28e/"
        "COMPARATOR_CAUSE_AND_CONFIRMATION_033.json")
P034 = ("artifacts/revisions/mahakal_v4_1/P034_20260907T231135Z_ff6250d/"
        "RESPONSE_ERROR_AND_OMITTED_SUPPORT_034.json")
Q035 = ("artifacts/revisions/mahakal_v4_1/Q035_20260908T004247Z_c1bf640/"
        "PER_CHANNEL_RESPONSE_AND_SUPPORT_035.json")
Q035I = ("artifacts/revisions/mahakal_v4_1/Q035_20260908T004247Z_c1bf640/"
         "HARMONIC_TEMPLATE_IDENTITY_035.json")

PINS = ["operator", "source_basis", "source_Gram", "sampled_rays",
        "quadrature", "covariance", "noise_normalisation",
        "target_nuisance_partition", "estimator", "evaluation_metric"]

S, D, P = ("STRUCTURAL_MATHEMATICS", "REPRODUCED_DISCRETE_BENCHMARK",
           "PHYSICAL_ACQUISITION_OR_CONTINUUM")


def claim(cid, orig, rev, disp, level, src, row, assume, dep, headline):
    return {"claim_id": cid, "original_document_identity": PINNED,
            "original_exact_text_and_location": orig,
            "revised_text_and_location": rev, "disposition": disp,
            "evidence_level": level, "source_commit_path_and_hash": src,
            "supporting_row_theorem_or_array_key": row,
            "source_operator_metric_and_noise_assumptions": assume,
            "unresolved_scientific_dependency": dep,
            "candidate_abstract_or_headline_allowed": headline}


def matrix() -> list[dict]:
    legacy = ("whitened sqrt(dOmega) g^3 row convention; declared source norm; "
              "sigma = 0.011341986814407566; single-sky noise")
    return [
        claim("C01",
              "abstract: 'the resolved stack sees deeper than the direct image "
              "at 12 of 12 geometries, with median recoverable depth 60, 84 "
              "and 144 M'",
              "section 4.1, unchanged numbers, evidence tag [D] added",
              "RETAINED_WITH_SCOPE_TAG", D, PINNED,
              "recoverable-depth tables, resolved and direct rows",
              legacy + "; threshold statement at the reference SNR on the "
              "declared class", None, True),
        claim("C02",
              "abstract: 'flattening the delays costs 0.98 ... against 0.57 "
              "for transplanting the spatial map'",
              "section 4.2, unchanged", "RETAINED_WITH_SCOPE_TAG", D, PINNED,
              "retarded-time diversity ablation rows", legacy, None, True),
        claim("C03",
              "section 5.4 'What the order labels are worth', read as evidence "
              "about physical order resolution",
              "section 4.3, retained as a comparison between two declared "
              "constructions, with an explicit CORRECTED SCOPE box",
              "CORRECTED_SCOPE_NOT_MERELY_PENDING", D, PINNED,
              "UNRESOLVED_IMAGE ratio table",
              legacy + "; UNRESOLVED_IMAGE is an index-sum construction, not a "
              "physically unresolved image",
              "a new comparison against an appropriate physical control and a "
              "new result; a future quadrature pass does not restore it",
              False),
        claim("C04",
              "abstract: 'compact temporal support turns the direct image's "
              "old-epoch blindness into 84 identically zero columns'",
              "section 5.1, unchanged, with the sampled-vs-continuum "
              "distinction stated",
              "RETAINED_WITH_ASSUMPTIONS_STATED", S, PINNED,
              "support/null-direction statement",
              "declared class and sampled ray set; a sampled support null is "
              "not a checked continuum null; a nonzero added column is not "
              "automatically an independent operational direction", None, True),
        claim("C05",
              "abstract: 'enriching the declared class from 224 to 1056 "
              "dimensions drives the resolved operational-rank fraction down "
              "16.8 percentage points'",
              "section 5.2, unchanged", "RETAINED_WITH_SCOPE_TAG", D, PINNED,
              "class-ladder table", legacy, None, True),
        claim("C06",
              "R2: two operational directions at the reference geometry",
              "section 5.3, retained and pinned to the frozen legacy measure, "
              "with the corrected-measure interval 1 <= N <= 2 stated",
              "RETAINED_LEGACY_MEASURE_ONLY", D, R2CSV,
              "RESOLVED_PHYSICAL rows, n_operational_conditional = 2 at all "
              "three rank tolerances",
              legacy + "; frozen legacy measure; nuisance rank 152; target "
              "dimension 72",
              "a corrected-measure recomputation, not authorised in this "
              "revision; the reweighting bound leaves 1 <= N <= 2 because the "
              "order-0 row ratios span [0.500081, 1.000162]",
              False),
        claim("C07",
              "abstract: 'stacking orders extends the anchored stable span "
              "from 48 to 80 M at SNR_0 = 100, a gain of 32 M against a "
              "threshold of 8 M'",
              "section 6.1, unchanged", "RETAINED_WITH_SCOPE_TAG", D, EVID,
              "R1 held-out main reconstruction section",
              legacy + "; 640 hash-committed truths; two prior-free "
              "estimators; coefficient-space metric under the declared source "
              "norm, not a source-function metric", None, True),
        claim("C08",
              "abstract: 'the resolved stack reduces morphology error against "
              "the analytic source by 0.164 and 0.133, lower bounds 0.116 and "
              "0.101'",
              "section 6.3, unchanged, with the four qualifications moved "
              "beside it in section 6.4",
              "RETAINED_WITH_QUALIFICATIONS_ATTACHED", D, EVID,
              "HMT-2 sealed main section",
              legacy + "; 60 held-out truths; resolution-aware measure "
              "selected by the state's own resolved label; no state excluded",
              None, True),
        claim("C09",
              "MULTI_FEATURE_RECOVERY_NEGATIVE, "
              "STABLE_MORPHOLOGY_INTERVAL_NEGATIVE, FAMILY_HETEROGENEITY, "
              "DIRECT_BASELINE_SATURATION_QUALIFICATION",
              "section 6.4, promoted from trailing caveats to part of the "
              "result", "RETAINED_AND_PROMOTED", D, EVID,
              "preserved literal failures section", legacy, None, True),
        claim("C10",
              "section 5 heading 'Validated Computational Operator'",
              "removed; section 7 states which parts of the discrete pipeline "
              "are qualified and section 8.2 states that the physical "
              "quadrature is not",
              "WITHDRAWN", P, P034,
              "per_order.n0/n1/n2.whitened_relative_error.transferred_channels",
              "measured on identical supported geometry with the same overlap "
              "operator, noise and absolute clock",
              "a signed per-channel response comparison inside 5e-4 with "
              "bounded coverage; see section 9.1", False),
        claim("C11",
              "no equivalent in the pinned document",
              "section 8.2, measured detector-response error 9.594e-03, "
              "4.274e-02, 5.116e-01 at orders 0, 1, 2 against a 5e-4 budget",
              "NEW_NEGATIVE_FINDING", D, Q035,
              "per_order.nX.baseline.max_relative_E", legacy,
              None, True),
        claim("C12",
              "no equivalent in the pinned document",
              "section 8.2, order-2 coverage 61.7% of emitting nodes and "
              "62.8% of emitting area; 0.6092 M^2 with no response bound",
              "NEW_NEGATIVE_FINDING", D, Q035,
              "per_order.n2.node_coverage, area_coverage, omitted_area",
              legacy + "; missing support is not zero", None, True),
        claim("C13",
              "no equivalent in the pinned document",
              "section 8.2, bound decomposition A/E = 1.10, 4.57, 4.71 and "
              "T/A = 20.02, 9.02, 6.73",
              "NEW_METHODOLOGICAL_FINDING", D, Q035,
              "per_order.nX.baseline.max_A_over_E and max_T_over_A",
              "separate channelwise maxima; the product of maxima is not the "
              "maximum of the product, and these do not identify the dominant "
              "factor for any single channel", None, False),
        claim("C14",
              "no equivalent in the pinned document",
              "section 8.2, five real templates reproduce all 40 declared "
              "transferred columns to 6.68e-15 pointwise and 1.12e-13 after "
              "the detector map",
              "NEW_STRUCTURAL_RESULT", S, Q035I,
              "per_order.nX.max_pointwise and max_after_the_detector",
              "the declared harmonic diagnostic fields only; not a ray "
              "speedup, not an L224 reduction, not arbitrary source movies",
              None, False),
        claim("C15",
              "no equivalent in the pinned document",
              "section 8.2, the composite-first representation is worse at all "
              "three orders on the registered maximum-error criterion",
              "NEW_NEGATIVE_RESULT_TEST_CLOSED", D, Q035,
              "per_order.nX.candidate.max_relative_E against baseline",
              legacy + "; identical support both sides; the order-2 median "
              "improvement is a secondary result and not the criterion",
              None, False),
        claim("C16",
              "hull geometry qualification",
              "section 7, 9.592e-08 band-normalised against 2.5e-4",
              "RETAINED", D, G1C, "closeout metrics", legacy, None, True),
        claim("C17",
              "no equivalent in the pinned document",
              "section 7, path-domain comparator validated on 66 development "
              "and 192 confirmation IDs with zero forced labels",
              "NEW_POSITIVE_RESULT_COHORT_SCOPE", D, N033,
              "development.tally and confirmation.tally",
              "tested cohorts only; bounded independence -- primary and "
              "reference share roots, angular crossing and path "
              "classification", None, False),
        claim("C18",
              "negative control: permuted pairing beats the physical operator "
              "on conditioning at 12 of 12 geometries",
              "section 6.5, unchanged, retained under its declared synthetic "
              "meaning", "RETAINED", D, PINNED,
              "pairing control rows", legacy, None, True),
    ]


LEDGER_MD = """# MANUSCRIPT_CORRECTION_LEDGER_036

Every correction applied in the working revision, and where it came from. The
pinned manuscript and the canonical freeze are unchanged; this is an additive
record.

## Corrections carried into the draft

| id | what the pinned version said | what the revision says | source ruling |
| --- | --- | --- | --- |
| L01 | section 5 headed "Validated Computational Operator" | heading removed; section 7 lists what is qualified, section 8.2 states the quadrature is not | 032, 034 |
| L02 | order-resolution attributed using `UNRESOLVED_IMAGE` | retained as a comparison of two declared constructions, with a CORRECTED SCOPE box; restoring the physical attribution needs a new physical control and a new result | 035, 036 |
| L03 | R2's two operational directions read without a measure pin | pinned to the frozen legacy measure; corrected-measure interval 1 <= N <= 2 stated beside it | 026, 036 |
| L04 | flat-per-row measurement convention | retired; results recomputed or labelled legacy in place | 026 |
| L05 | four morphology qualifications trailing the result | moved beside it as part of the result | 036 |
| L06 | coefficient and source-function metrics not consistently separated | separated throughout; actual noise and SNR labels not interchanged | 036 |
| L07 | no statement of continuum accuracy | section 8.2 gives the measured detector-response error and the coverage gap | 034, 035 |

## Corrections to my own earlier reporting

| id | what I reported | what the record says |
| --- | --- | --- |
| L08 | "the integrals agree to about 3e-16" (033 return) | true of `J_observer`, `J_50` and the tail; false for `s_escape`, which differs by a median 2.94e-05 | 035 |
| L09 | "the 10x-to-57x gap was conservatism from sign cancellation" (034) | it is mostly loss of detector-vector structure; cancellation is 1.10 to 4.71 and is not absent | 035 |
| L10 | "the order-2 interior is where the cost lives" (033) | withdrawn; no order-2 stencil passes the smoothness proxy, so the figure measured that representation failing | 034 |
| L11 | "adaptivity fixes the boundary cost" (033) | withdrawn; the same model splits 52,379 boundary against 49,037 interior | 034 |
| L12 | "identity ... 6.4e-15 after the detector map" (035 commit message and chat summary) | the global post-detector maximum is 1.1191048088221578e-13; 6.4e-15 is the order-2 *pointwise* value. The 035 RETURN.md reported the detector maximum correctly; the commit message and my summary did not. Record-only correction; no replay required | 036 |
| L13 | "308,656 evaluations" presented as a cost scenario | relabelled ORACLE_ZERO_HEAD_CACHED_DEFECT: it assumes a refined node's discrepancy goes to exactly zero and everything else stays put | 035 |
| L14 | "no order-2 stencil passes the same-leg test" | relabelled a small-radius-span heuristic; physical branch membership is unverified | 035 |

## What was deliberately not changed

- The pinned manuscript bytes, the canonical artifact freeze, and every
  historical run directory.
- Every preserved literal failure and every governance deviation record.
- The original title, the author list, and the three organizing questions.
"""

GAPS_MD = """# SUBMISSION_GAPS_036

Four categories, deliberately separated. Only the third requires an experiment.

## A. Editorial completion — no new science needed

| item | state |
| --- | --- |
| Abstract, contributions, captions, tables, conclusion and limitations made consistent with the corrections | done in the working revision |
| Evidence tags [S] / [D] / [P] applied to every headline claim | done |
| Coefficient vs source-function metrics separated; noise vs SNR labels separated | done |
| Figures regenerated against the revised section numbering | **outstanding** — figures are referenced by the pinned build and have not been re-rendered for this revision |
| Bibliography and cross-reference audit against the new structure | **outstanding** |
| Author review of scope and of every proposed disposition | **outstanding and required** |

## B. Discrete result lineage — archive work, no new computation

| item | state |
| --- | --- |
| Every retained number pinned to commit, artifact, hash and row | done in CLAIM_EVIDENCE_MATRIX_036.json |
| The ten pins recorded per claim | done |
| R2 pinned to the legacy measure | done |
| Corrected-measure R2 recomputation | **not authorised in this ruling**; required only if the authors wish to state a corrected-measure operational count rather than the interval |

## C. Physical claim revalidation — this needs an experiment

Only two claims in the draft would need it, and both are currently marked
rather than asserted.

**C.1 The transfer quadrature (blocks any [P] reading of any [D] number).**
Required: a response comparison whose signed per-channel relative error is
inside 5e-4 on the declared channels; full-domain coverage or an explicit
bounded remainder for the 0.6092 M² currently uncovered at order 2; a stated
accuracy for the reference itself; group remainder radii from something other
than the pair being certified; and a funded independent validation budget fixed
before launch. Costed scenarios exist (expected 101,416 new native evaluations,
worst case 382,580, at a 4.4x reduction on the retired uniform layout) but they
are scenarios, not measured call counts, and 854 units remain.

**C.2 The order-resolution attribution.** Required: a comparison against an
appropriate physical control — not the `UNRESOLVED_IMAGE` index-sum
construction — and a new result. A quadrature pass under C.1 would not supply
this; it is a separate experiment.

## D. Author scope approval

The authors decide whether to submit a finite-model paper that states the
physical gap plainly, or to run C.1 and C.2 first. This revision does not make
that choice, and calling the work finite-model does not by itself make an
unresolved physical claim publishable.

## What is explicitly *not* required

- An expensive common-sky campaign for every finite-model statement in the
  paper. The [S] and [D] results stand on their own inputs.
- A monolithic repack of the split 035 payload.
- Any replay of the accepted comparator, hull or sampled-absence closeouts.
"""


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with Path(p).open("rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def main() -> int:
    t0 = time.time()
    out = OUT_ROOT
    out.mkdir(parents=True, exist_ok=True)
    cited = [PINNED, LEDGER, FREEZE, EVID, R2, R2CSV, G1C, N033, P034, Q035,
             Q035I]
    present = {f: sha(ROOT / f) for f in cited if (ROOT / f).is_file()}
    missing = [f for f in cited if not (ROOT / f).is_file()]
    rows = matrix()
    unresolved = [r["claim_id"] for r in rows
                  if r["source_commit_path_and_hash"] not in present]
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                            capture_output=True, text=True).stdout.strip()
    (out / "MANUSCRIPT_036_INPUT_MANIFEST.json").write_text(json.dumps({
        "ruling": "PAPER_I_TEMPLATE_CLOSEOUT_AND_REVISION_036",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "commit": commit,
        "new_rays": 0, "new_path_integrals": 0, "new_hull_roots": 0,
        "new_target_operators_or_spectra": 0,
        "cited_artifacts": present, "missing_artifacts": missing,
        "claims_with_unresolvable_source": unresolved,
        "repository_document_identity": present.get(PINNED),
        "uploaded_document_identity": "NOT_VERIFIED_BY_THIS_STAGE: the "
                                      "reviewer's attached PDF was not "
                                      "supplied to this session, so repository "
                                      "and uploaded identities are recorded "
                                      "separately and only the repository copy "
                                      "is hashed here",
        "pinned_manuscript_overwritten": False,
        "canonical_tables_overwritten": False,
    }, indent=2) + "\n")
    (out / "CLAIM_EVIDENCE_MATRIX_036.json").write_text(json.dumps({
        "ruling": "PAPER_I_TEMPLATE_CLOSEOUT_AND_REVISION_036",
        "commit": commit, "pins_recorded_per_claim": PINS,
        "evidence_levels": [S, D, P],
        "claims": rows, "n_claims": len(rows),
        "claims_with_unresolvable_source": unresolved,
        "missing_source_policy": "recorded UNRESOLVED or removed from the "
                                 "candidate headline; never invented",
    }, indent=2) + "\n")
    (out / "MANUSCRIPT_CORRECTION_LEDGER_036.md").write_text(LEDGER_MD)
    (out / "SUBMISSION_GAPS_036.md").write_text(GAPS_MD)

    draft = out / DRAFT
    headline = [r["claim_id"] for r in rows
                if r["candidate_abstract_or_headline_allowed"]]
    completion = {
        "schema": "phrt-completion/1",
        "id": "MANUSCRIPT_REVISION_036_COMPLETION",
        "ruling": "PAPER_I_TEMPLATE_CLOSEOUT_AND_REVISION_036",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "commit": commit,
        "return_status": "MANUSCRIPT_REVISION_036_READY_FOR_AUTHOR_REVIEW",
        "ready_is_submission_or_R3B_authorization": False,
        "draft": DRAFT,
        "draft_sha256": sha(draft) if draft.is_file() else None,
        "draft_lines": len(draft.read_text().splitlines())
        if draft.is_file() else 0,
        "organisation": ["historical_reach", "historical_dimension",
                         "historical_recovery"],
        "claims": {"total": len(rows),
                   "headline_allowed": headline,
                   "withdrawn": [r["claim_id"] for r in rows
                                 if r["disposition"] == "WITHDRAWN"],
                   "corrected_scope": [r["claim_id"] for r in rows
                                       if "CORRECTED" in r["disposition"]],
                   "legacy_measure_only": [r["claim_id"] for r in rows
                                           if "LEGACY" in r["disposition"]],
                   "unresolvable_source": unresolved},
        "physical_claims_supported": 0,
        "author_review_required_before_scope_and_submission": True,
        "author_verification_claimed": False,
        "resources": {"convention": "B", "second_batch_spent": 19146,
                      "second_batch_remaining": 854,
                      "spent_under_this_ruling": 0,
                      "boundary_spent": 33410},
        "old_results_or_flags_rewritten": False,
        "preserved_tokens": ["DOMAIN_INTEGRATION_031_BLOCKED",
                             "MATCHED_INTEGRATION_032_PLAN_BLOCKED",
                             "FEASIBILITY_CLOSEOUT_033_REVIEW_READY",
                             "CACHED_RESPONSE_AUDIT_034_REVIEW_READY",
                             "DETECTOR_TEMPLATE_035_REVIEW_READY"],
        "R3B_or_submission_freeze": "not authorized",
        "runtime_seconds": time.time() - t0,
    }
    (out / "MANUSCRIPT_REVISION_036_COMPLETION.json").write_text(
        json.dumps(completion, indent=2) + "\n")
    print(json.dumps({"stage": "036", "claims": len(rows),
                      "headline": len(headline), "unresolved": unresolved,
                      "missing": missing,
                      "draft_lines": completion["draft_lines"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
