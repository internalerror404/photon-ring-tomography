#!/usr/bin/env python3
"""Emit the Paper I submission release note.

PAPER_I_EDITORIAL_RULING_022 item 6. One page a reader gets before the paper:
what this release is, what the two results are called, what travels with them,
what changed in this release, and how to rebuild it. Everything is read from
the freeze, the claim ledger and the bundle manifest, so the note cannot claim
a digest the tree does not have.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from phrt.config import sha256_file
from phrt.io.dashboard import gate_counts

MAN = ROOT / "artifacts" / "manuscript"
OUT = ROOT / "docs" / "PAPER_I_RELEASE_NOTE.md"
BUNDLE = "PHOTON_RING_TOMOGRAPHY_I_SHIVA_EFFECT_SOURCE_BUNDLE"
D = "\n"


def sha(p: Path) -> str:
    return sha256_file(p)[:16] + "..." if p.exists() else "ABSENT"


def main() -> int:
    meta = json.loads((MAN / "PDF_METADATA.json").read_text())
    ledger = json.loads((MAN / "CLAIM_LEDGER.json").read_text())
    fz = json.loads((ROOT / "artifacts"
                     / "CANONICAL_ARTIFACT_FREEZE_V2.json").read_text())
    bundle = json.loads((MAN / f"{BUNDLE}_MANIFEST.json").read_text())
    counts = gate_counts()

    files = [MAN / "PAPER_I.pdf", MAN / "PAPER_I.md", MAN / "PAPER_I.html",
             MAN / "CLAIM_LEDGER.json", MAN / f"{BUNDLE}.tar.gz",
             ROOT / "artifacts" / "CANONICAL_ARTIFACT_FREEZE_V2.json",
             ROOT / "docs" / "Paper_I_v1_Current_Evidence_Ledger.md",
             ROOT / "docs" / "PAPER_I_SUBMISSION_CHECKLIST.md"]

    body = f"""# Paper I — submission release note

**{meta['title']}**

{meta['author']}

- generated {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
- manuscript build commit `{bundle['git_commit']}`
- canonical artifact freeze v2: {fz['n_canonical_artifacts']} artifacts,
  pinned at `{fz['campaign_commit']}`
- claim ledger: {ledger['n_claims']} numbers over
  {len(ledger['artifacts_cited'])} artifacts
- gates: {counts['total_gates']} total, {counts['passing']} passing,
  {counts['active_blocking_failures']} active blocking failures,
  {counts['preserved_literal_failures']} preserved literal failures

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
- Source bundle renamed to `{BUNDLE}.tar.gz` and repaired: it now ships the v2
  freeze the manuscript is actually built and verified against, together with
  the evidence-ledger and checklist builders.

No endpoint, table, threshold or artifact was altered, and no experiment was
run, for this release.

## Rebuilding

```
{D.join(bundle['rebuild'])}
```

The bundle carries {bundle['n_entries']} files and excludes only the ray maps,
whose digests are pinned in the operator grid freeze that travels with it.

## Digests

| file | sha256 |
|---|---|
{D.join(f'| `{p.relative_to(ROOT)}` | `{sha(p)}` |' for p in files)}
"""
    OUT.write_text(body)
    print(f"wrote {OUT.relative_to(ROOT)}")
    print(f"  {ledger['n_claims']} claims, {fz['n_canonical_artifacts']} "
          f"canonical artifacts, {bundle['n_entries']} bundle entries")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
