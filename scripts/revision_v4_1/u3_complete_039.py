#!/usr/bin/env python3
"""Ruling 039: completion record and checksums, written last.

The checksum file is generated after the document is rendered and inspected, so
what it certifies is the artifact a reader would open, not an intermediate.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs/revisions/mahakal_v4_1/manuscript039"
STEM = "Photon_Ring_Retarded_Time_Tomography_Candidate_039"


def sha(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main() -> int:
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                            capture_output=True, text=True).stdout.strip()
    files = sorted(p for p in DOC.rglob("*")
                   if p.is_file() and p.name != "SHA256SUMS.txt")
    record = {
        "ruling": "PAPER_I_FINAL_TEXT_REVIEW_039",
        "return_token": "PUBLICATION_CANDIDATE_039_READY_FOR_AUTHOR_REVIEW",
        "ready_is_permission_to_submit": False,
        "R3B_started": False,
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "commit": commit,
        "branch": "research/mahakal_v4_1",
        "document_version": f"manuscript039/{STEM}.md",
        "deliverable": {
            "editable_source": f"{STEM}.md",
            "rendered_html": f"{STEM}.html",
            "rendered_pdf": f"{STEM}.pdf",
            "pdf_pages": 23,
            "display_equations": 14,
            "tables": 8,
            "figures": 2,
            "status_only_packet": False,
        },
        "method_dependencies": {
            "R1_EVALUATION_GRID": "SOURCE_RESOLVED",
            "HMT2_PAIRED_REDUCTION_AGGREGATION_ORDER": "SOURCE_RESOLVED",
            "R1_REALIZED_ETA": "REALIZED_ETA_NOT_LOCATED",
        },
        "eta_affected_claims": ["C06", "C07", "C08", "C21"],
        "eta_marked_complete_anywhere": False,
        "eta_value_invented": False,
        "text_consistency_edits": [
            "tuning lineage split R1 <- R0C, HMT2 <- its own stage-1",
            "HMT2 noise cell states the readout law, not the draw count",
            "internal references name this revision, not the 037 matrix",
            "nonzero columns need not be independent or recoverable",
            "posterior-calibration failure scoped to the R1 probabilistic "
            "estimator program",
            "family heterogeneity reports its measured estimates and intervals",
        ],
        "exposition_added": [
            "C224 factorization, support and column order",
            "reference observer schedule, eight samples 0 to 20 M",
            "age probe form and unit-L2 normalisation",
            "detectability rule sup { a : SNR_0^2 I(a) >= rho^2 }, rho = 1",
        ],
        "figures": {
            "regenerated_from_saved_tables_only": True,
            "new_operator_or_reconstruction_inside_builder": False,
            "canonical_assets_overwritten": False,
            "in_figure_titles_and_labels_corrected": True,
        },
        "bibliography": {
            "verified_records": 7,
            "verification_level": "metadata_and_abstract",
            "full_text_audited": False,
            "all_archived_references_audited": False,
            "novelty_or_priority_claim_made": False,
        },
        "rendering_check": {
            "performed_before_hashing": True,
            "figures_numbered_captioned_and_cited_in_text": True,
            "equation_delimiters_leaked": False,
            "stale_037_or_038_record_references": 0,
            "cross_references_resolve": True,
            "tables_within_page_width": True,
        },
        "preservation": {
            "manuscripts_036_037_038_unchanged": True,
            "freeze_022_unchanged": True,
            "canonical_figures_unchanged": True,
            "run_directories_unchanged": True,
            "shared_renderer_modified": False,
            "reset_rebase_or_force_push": False,
        },
        "resources": {
            "new_rays": 0,
            "new_path_integrals": 0,
            "new_hull_roots": 0,
            "new_target_matrices_spectra_estimators_truths_interpolants": 0,
            "convention_B_units_spent_this_stage": 0,
            "convention_B_second_batch_spent": 19146,
            "convention_B_second_batch_remaining": 854,
            "boundary_spent": 33410,
            "paid_resources_used": False,
        },
        "outputs": [
            {"file": str(p.relative_to(DOC)), "sha256": sha(p),
             "bytes": p.stat().st_size} for p in files
        ],
    }
    (DOC / "PUBLICATION_CANDIDATE_039_COMPLETION.json").write_text(
        json.dumps(record, indent=2) + "\n")

    files = sorted(p for p in DOC.rglob("*")
                   if p.is_file() and p.name != "SHA256SUMS.txt")
    (DOC / "SHA256SUMS.txt").write_text(
        "".join(f"{sha(p)}  {p.relative_to(DOC)}\n" for p in files))
    print(json.dumps({"token": record["return_token"],
                      "files": len(files)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
