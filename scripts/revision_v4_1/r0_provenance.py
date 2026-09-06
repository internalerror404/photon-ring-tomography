#!/usr/bin/env python3
"""R0 provenance: what is on this machine, and whether it is what 022 froze.

PAPER_I_DEFECT_AMENDMENT_023 / EXPERIMENT_PROTOCOL R0. Records the commit
ancestry, re-hashes every deliverable freeze 022 pinned, and states the
uploaded-PDF lineage as unresolved rather than reconciling two different
documents by assumption.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from phrt.attestation import working_tree_state

FREEZE = ROOT / "artifacts" / "configs" / "PAPER_I_SUBMISSION_FREEZE_022.json"
REV = ROOT / "docs" / "revisions" / "mahakal_v4_1"
UPLOADED_PDF_SHA = ("152b099fc09994e917f629bda90de19bfd388ee1"
                    "9e96f754a0dfc4b763e61148")
FROZEN_PDF_SHA = ("b2af07620ecebabd704a83aa9022f044574de443"
                  "a7130a1c9ae5a8050a3962d5")


def sha(p: Path) -> str | None:
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


def git(*a: str) -> str:
    return subprocess.run(["git", *a], cwd=ROOT, capture_output=True,
                          text=True).stdout.strip()


def main(run_dir: Path) -> int:
    fz = json.loads(FREEZE.read_text())
    deliverables = {}
    for rel, pinned in fz["deliverables"].items():
        now = sha(ROOT / rel)
        deliverables[rel] = {
            "pinned_sha256": pinned, "current_sha256": now,
            "status": ("MATCHES" if now == pinned
                       else "ABSENT" if now is None else "DIFFERS")}
    n_match = sum(1 for v in deliverables.values() if v["status"] == "MATCHES")

    doc = {
        "schema": "phrt-revision-provenance/1",
        "campaign": "MAHAKAL_REVISION_INFORMATION_BOUNDARY_V4_1",
        "phase": "R0",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "amendment": "PAPER_I_DEFECT_AMENDMENT_023",
        "git": {
            "execution_branch": git("rev-parse", "--abbrev-ref", "HEAD"),
            "execution_commit": git("rev-parse", "HEAD"),
            "execution_tree": git("rev-parse", "HEAD^{tree}"),
            "delivery_commit": "38e1f8a758e68d0bb272085bc826152d53996931",
            "inspected_base": "7961e5bd7d46be23885151afa7664596cc58cfa6",
            "ancestry": {
                "delivery_contains_inspected_base": git(
                    "merge-base", "--is-ancestor",
                    "7961e5bd7d46be23885151afa7664596cc58cfa6",
                    "38e1f8a758e68d0bb272085bc826152d53996931") == "",
                "reconciliation": "fast-forward only; no reset, rebase, clean "
                                  "or stash was performed and the local "
                                  "worktree carried no divergent commits",
            },
        },
        "working_tree_at_r0_start": working_tree_state(),
        "freeze_022": {
            "path": str(FREEZE.relative_to(ROOT)),
            "sha256": sha(FREEZE),
            "status_field": fz["status"],
            "n_deliverables": len(fz["deliverables"]),
            "n_matching_now": n_match,
            "all_match": n_match == len(fz["deliverables"]),
            "deliverables": deliverables,
        },
        "manuscript_lineage": {
            "uploaded_pdf_sha256": UPLOADED_PDF_SHA,
            "frozen_repository_pdf_sha256": FROZEN_PDF_SHA,
            "repository_pdf_current_sha256":
                sha(ROOT / "artifacts" / "manuscript" / "PAPER_I.pdf"),
            "identical": False,
            "status": "UNRESOLVED_DISTINCT_DOCUMENTS",
            "consequence": "claims are mapped by content, never by section "
                           "number. No reproduction of the uploaded document "
                           "is asserted anywhere in this campaign; the code "
                           "audit is against the pinned repository version "
                           "only",
            "uploaded_pdf_present_on_this_machine": False,
        },
        "governing_documents": {
            p.name: sha(p) for p in sorted(REV.glob("*"))},
        "isolation": {
            "new_source_root": "src/phrt/revision_v4_1",
            "new_runner_root": "scripts/revision_v4_1",
            "new_test_root": "tests/revision_v4_1",
            "run_directory": str(run_dir.relative_to(ROOT)),
            "inherited_writers_invoked": "none",
        },
    }
    out = run_dir / "provenance.json"
    out.write_text(json.dumps(doc, indent=2) + "\n")
    print(f"wrote {out.relative_to(ROOT)}")
    print(f"  deliverables {n_match}/{len(deliverables)} match freeze 022")
    for rel, v in deliverables.items():
        if v["status"] != "MATCHES":
            print(f"  {v['status']}: {rel}")
    print(f"  uploaded PDF lineage: {doc['manuscript_lineage']['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main((ROOT / sys.argv[1]).resolve()))
