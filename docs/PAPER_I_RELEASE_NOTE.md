# Paper I — submission release note

**Photon-Ring Retarded-Time Tomography I: The Shiva Effect — Null Spaces, Multi-Geometry Observability, and Bounded Inference of Historical Emissivity Level and Morphology**

Hina Dixit and Abhinav Chauhan

- generated 2026-08-28T15:27:23Z
- manuscript build commit `82e106eee85c871ab6ec9685d823bce8a3c6de59`
- canonical artifact freeze v2: 591 artifacts,
  pinned at `8345068676b15ce8f96a76da9d92b159db215f1d`
- claim ledger: 276 numbers over
  33 artifacts
- gates: 208 total, 189 passing,
  0 active blocking failures,
  8 preserved literal failures

## What this release contains

A preprint draft reporting theory and controlled synthetic computation only.
No telescope detection, no laboratory result, and no recovery from a resolved
real photon ring is claimed.

Two held-out historical inverse results, each judged against a materiality
floor fixed before its bank was drawn:

| result | what it establishes |
|---|---|
| `STABLE_BASELINE_INCLUSIVE_EMISSIVITY_LEVEL_RECONSTRUCTION` | stacking orders extends the anchored stable span of age-local emissivity **level** reconstruction, on a sealed bank hashed before an operator existed for it |
| `AGGREGATE_RESOLUTION_AWARE_MORPHOLOGY_ERROR_REDUCTION` | on a second sealed bank, an aggregate reduction in a morphology error whose per-state measure is selected by what the evaluation grid can resolve, with no state excluded |

Four qualifications are part of the second result and are printed beside it,
never after it: `MULTI_FEATURE_RECOVERY_NEGATIVE`,
`STABLE_MORPHOLOGY_INTERVAL_NEGATIVE`, `FAMILY_HETEROGENEITY`,
`DIRECT_BASELINE_SATURATION_QUALIFICATION`.

Neither result is recovery of a historical movie. Age-local *structure* under
the preregistered standard is a bar not cleared at the reference SNR, reported
as such rather than as an effect shown to be zero.

## The organising claim

The paper's structural finding is named the **Shiva effect**: the enrichment of
the source model that creates recoverable history destroys identifiability, and
the compactness that makes an epoch well posed makes the direct image exactly
blind to it — an exact null space, not an ill-conditioning. It is measured in
three independent places rather than argued once.

## What changed in this release

- Title, author line, running header and PDF metadata set for submission.
- Result vocabulary standardized on the two labels above, replacing the earlier
  informal "two held-out reconstruction claims".
- Section numbering derived from a single ordered list rather than typed into
  each heading, with a test that every in-text cross-reference resolves.
- Abstract compressed and reorganised around the two labelled results.
- Contribution list and conclusion added.
- Source bundle renamed to `PHOTON_RING_TOMOGRAPHY_I_SHIVA_EFFECT_SOURCE_BUNDLE.tar.gz` and repaired: it now ships the v2
  freeze the manuscript is actually built and verified against, together with
  the evidence-ledger and checklist builders.

No endpoint, table, threshold or artifact was altered, and no experiment was
run, for this release.

## Rebuilding

```
python scripts/build_canonical_freeze.py --v2
python scripts/build_evidence_ledger.py
python scripts/build_manuscript.py
python scripts/compile_manuscript.py
python scripts/verify_manuscript.py
python scripts/build_submission_checklist.py
```

The bundle carries 145 files and excludes only the ray maps,
whose digests are pinned in the operator grid freeze that travels with it.

## Digests

| file | sha256 |
|---|---|
| `artifacts/manuscript/PAPER_I.pdf` | `b2af07620ecebabd...` |
| `artifacts/manuscript/PAPER_I.md` | `e04d3dc14f41dc00...` |
| `artifacts/manuscript/PAPER_I.html` | `950f771b059c9df8...` |
| `artifacts/manuscript/CLAIM_LEDGER.json` | `8d195ce597ad8892...` |
| `artifacts/manuscript/PHOTON_RING_TOMOGRAPHY_I_SHIVA_EFFECT_SOURCE_BUNDLE.tar.gz` | `9e86c66ef676c6f4...` |
| `artifacts/CANONICAL_ARTIFACT_FREEZE_V2.json` | `471a0da7a06e5f89...` |
| `docs/Paper_I_v1_Current_Evidence_Ledger.md` | `2189c43718eae0e4...` |
| `docs/PAPER_I_SUBMISSION_CHECKLIST.md` | `5c6b5f06beab08c5...` |
