#!/usr/bin/env python3
"""Freeze Paper I for submission.

PAPER_I_EDITORIAL_RULING_022 item 10. The editorial pass is complete, so the
deliverable set is pinned: this records the sha256 of every file a reviewer or
an editor would receive, together with the checks that were green when it was
pinned. Re-running the builders after this point and getting different digests
means the paper moved after it was frozen, which is exactly what this file
exists to make visible.

Freezing is a record, not a lock. It alters no endpoint, table, threshold or
artifact, and it runs no experiment.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from phrt.attestation import working_tree_state
from phrt.config import sha256_file
from phrt.io.dashboard import gate_counts

MAN = ROOT / "artifacts" / "manuscript"
BUNDLE = "PHOTON_RING_TOMOGRAPHY_I_SHIVA_EFFECT_SOURCE_BUNDLE"
OUT = ROOT / "artifacts" / "configs" / "PAPER_I_SUBMISSION_FREEZE_022.json"

DELIVERABLES = [
    "artifacts/manuscript/PAPER_I.pdf",
    "artifacts/manuscript/PAPER_I.md",
    "artifacts/manuscript/PAPER_I.html",
    "artifacts/manuscript/CLAIM_LEDGER.json",
    "artifacts/manuscript/PDF_METADATA.json",
    f"artifacts/manuscript/{BUNDLE}.tar.gz",
    f"artifacts/manuscript/{BUNDLE}_MANIFEST.json",
    "artifacts/manuscript/figures/FIGURES.json",
    "artifacts/CANONICAL_ARTIFACT_FREEZE_V2.json",
    "docs/Paper_I_v1_Current_Evidence_Ledger.md",
    "docs/PAPER_I_SUBMISSION_CHECKLIST.md",
    "docs/PAPER_I_RELEASE_NOTE.md",
    "docs/PAPER_I_PROOF_AUDIT.md",
]


def main() -> int:
    meta = json.loads((MAN / "PDF_METADATA.json").read_text())
    ledger = json.loads((MAN / "CLAIM_LEDGER.json").read_text())
    figs = json.loads((MAN / "figures" / "FIGURES.json").read_text())
    counts = gate_counts()

    verify = subprocess.run([sys.executable, str(ROOT / "scripts"
                                                 / "verify_manuscript.py")],
                            cwd=ROOT, capture_output=True, text=True)
    tests = subprocess.run(["python3", "-m", "pytest", "tests/", "-q",
                            "--no-header", "-x"],
                           cwd=ROOT, capture_output=True, text=True)
    tail = [ln for ln in tests.stdout.strip().splitlines() if ln.strip()][-1:]

    doc = {
        "schema": "phrt-submission-freeze/1",
        "id": "PAPER_I_SUBMISSION_FREEZE_022",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "ruling": "PAPER_I_EDITORIAL_RULING_022",
        "status": "FROZEN_FOR_SUBMISSION",
        "title": meta["title"],
        "authors": meta["author"],
        "results": {
            "held_out": ["STABLE_BASELINE_INCLUSIVE_EMISSIVITY_LEVEL_"
                         "RECONSTRUCTION",
                         "AGGREGATE_RESOLUTION_AWARE_MORPHOLOGY_ERROR_"
                         "REDUCTION"],
            "qualifications_travelling_with_the_second": [
                "MULTI_FEATURE_RECOVERY_NEGATIVE",
                "STABLE_MORPHOLOGY_INTERVAL_NEGATIVE",
                "FAMILY_HETEROGENEITY",
                "DIRECT_BASELINE_SATURATION_QUALIFICATION"],
            "not_established": "recovery of a historical movie, at any point "
                               "in the campaign",
        },
        "editorial_pass": {
            "compression": "abstract rewritten from 900 to about 500 words "
                           "around the two labelled results; the twelve-row "
                           "per-family table replaced by figure 4 with the "
                           "exact values left in the evidence ledger; one "
                           "duplicated sentence removed",
            "figure_hierarchy": {
                "n_figures": len(figs["figures"]),
                "hierarchy": figs["hierarchy"],
                "figures": [f["name"] for f in figs["figures"]]},
            "bibliography": "10 entries; literature checked against the "
                            "publisher or arXiv record, software pinned to "
                            "the version or commit actually run",
            "proof_audit": "docs/PAPER_I_PROOF_AUDIT.md, 20 assertions, 3 "
                           "defects of statement found and repaired",
            "preflight": "no element overflows its container at the print "
                         "width; running header and page numbers present; "
                         "PDF metadata stamped and dated from the canonical "
                         "freeze so a rebuild does not churn the bundle",
        },
        "checks_at_freeze": {
            "manuscript_verification": ("PASS" if verify.returncode == 0
                                        else "FAIL"),
            "verification_summary": [ln.strip() for ln in
                                     verify.stdout.strip().splitlines()[-7:]],
            "tests": tail[0] if tail else "not run",
            "tests_returncode": tests.returncode,
            "n_claims": ledger["n_claims"],
            "n_artifacts_cited": len(ledger["artifacts_cited"]),
            "gates": {k: counts[k] for k in
                      ("total_gates", "passing", "active_blocking_failures",
                       "preserved_literal_failures")},
        },
        "deliverables": {p: sha256_file(ROOT / p) for p in DELIVERABLES
                         if (ROOT / p).exists()},
        "not_authorized": ["order leakage", "geometry mismatch", "VLBI",
                           "machine learning", "a new pixel-movie campaign",
                           "any further experiment for Paper I"],
        "working_tree_at_freeze": working_tree_state(),
    }
    OUT.write_text(json.dumps(doc, indent=2, default=str) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}")
    print(f"  {len(doc['deliverables'])} deliverables pinned")
    print(f"  verification {doc['checks_at_freeze']['manuscript_verification']}"
          f", tests: {doc['checks_at_freeze']['tests']}")
    return 0 if (verify.returncode == 0 and tests.returncode == 0) else 1


if __name__ == "__main__":
    raise SystemExit(main())
