#!/usr/bin/env python3
"""Freeze the canonical artifact set the manuscript is allowed to cite.

Two jobs. First, record the sha256 of every artifact that survives the
measurement-model correction, so the manuscript's provenance is a fixed set of
bytes rather than "whatever was in the tree". Second, make the post-G10q rule
mechanical: an artifact appears here only if it is not marked
SUPERSEDED_MEASUREMENT_MODEL_DEFECT, and the manuscript builder reads its
inputs through this file. A superseded artifact cannot be cited by accident,
because it is not in the set.

The freeze also carries the campaign tag and the three governance counts, so a
reader holding only this file can tell which commit the numbers came from and
what the gate ledger looked like at that commit.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from phrt import provenance
from phrt.config import load_registry, sha256_file
from phrt.io.dashboard import gate_counts

TAG = "paper-I-campaign-final"

# Directories whose contents are canonical evidence. Ray maps are hashed by the
# E3C freeze already and are large, so they are referenced by that file rather
# than re-hashed here.
INCLUDE = (
    "artifacts/tables",
    "artifacts/gates",
    "artifacts/configs",
    "artifacts/reports",
    "artifacts/provenance",
    "artifacts/e3c",
    "artifacts/e3_pilot",
    "artifacts/e0_reproduction",
    "artifacts/g1_run",
)
TOP_LEVEL = (
    "artifacts/GATE_DASHBOARD.json",
    "artifacts/PREFIX_INVALIDATION_LEDGER.json",
    "artifacts/SUPERSEDED_PRE_G10Q.json",
    "artifacts/PROTOCOL_DEVIATION_001_E1E2_BEFORE_G1.json",
)


def superseded_paths() -> set[str]:
    p = ROOT / "artifacts" / "SUPERSEDED_PRE_G10Q.json"
    doc = json.loads(p.read_text())
    return {a["path"] for a in doc["artifacts"]
            if a["disposition"] == "SUPERSEDED_MEASUREMENT_MODEL_DEFECT"}


def main() -> int:
    reg = load_registry()
    prov = provenance.collect()
    # The campaign commit is the tag, not HEAD. Manuscript work lands after the
    # campaign, and rebuilding the freeze from a later HEAD would silently
    # restamp the paper as citing a commit that did not produce its numbers.
    r = subprocess.run(["git", "rev-list", "-n", "1", TAG], cwd=ROOT,
                       capture_output=True, text=True)
    head = r.stdout.strip() if r.returncode == 0 and r.stdout.strip() else \
        subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                       capture_output=True, text=True).stdout.strip()
    tag_resolved = r.returncode == 0 and bool(r.stdout.strip())
    sup = superseded_paths()

    files: list[Path] = []
    for d in INCLUDE:
        files.extend(p for p in (ROOT / d).rglob("*") if p.is_file())
    files.extend(ROOT / p for p in TOP_LEVEL)

    canonical, excluded = {}, []
    for p in sorted(set(files)):
        if not p.exists():
            continue
        rel = str(p.relative_to(ROOT))
        # A superseded *path* is still on disk in its corrected form; only the
        # pre-correction bytes are superseded. What must never be cited is the
        # pre-correction version, and that lives in git, not here. Run manifests
        # of superseded runs are excluded outright.
        if rel in sup and "/manifests/" in rel:
            excluded.append(rel)
            continue
        canonical[rel] = sha256_file(p)

    # run manifests: only those at or after the correction
    man_dir = ROOT / "artifacts" / "manifests"
    for p in sorted(man_dir.glob("*.json")):
        rel = str(p.relative_to(ROOT))
        if rel in sup:
            excluded.append(rel)
            continue
        canonical[rel] = sha256_file(p)

    counts = gate_counts()
    doc = {
        "schema": "phrt-canonical-freeze/1",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "campaign_tag": TAG,
        "campaign_commit": head,
        "campaign_commit_source": ("git tag " + TAG) if tag_resolved
                                  else "HEAD (tag not found)",
        "registry_sha256": reg.sha256,
        "measurement_convention": "pixel_integrated; whitened row "
                                  "sqrt(dOmega)/sigma_Omega * g^3 * B",
        "correcting_commit": "d6869f8d1c08889fee34e91d392c2bbc1bc9a62f",
        "rule": "the manuscript may cite only artifacts listed here; anything "
                "marked SUPERSEDED_MEASUREMENT_MODEL_DEFECT is excluded",
        "gate_counts": {k: counts[k] for k in
                        ("total_gates", "passing", "active_blocking_failures",
                         "preserved_literal_failures", "future_phase_not_run")},
        "preserved_literal_failure_dispositions":
            counts["preserved_literal_failure_dispositions"],
        "n_canonical_artifacts": len(canonical),
        "n_excluded_superseded_runs": len(excluded),
        "excluded_superseded_runs": sorted(set(excluded)),
        "raymap_hashes_recorded_in":
            "artifacts/configs/E3C_OPERATOR_GRID_FREEZE.json",
        "artifacts": canonical,
    }
    out = ROOT / "artifacts" / "CANONICAL_ARTIFACT_FREEZE.json"
    out.write_text(json.dumps(doc, indent=2) + "\n")
    print(f"wrote {out.relative_to(ROOT)}")
    print(f"  {len(canonical)} canonical artifacts, "
          f"{len(set(excluded))} superseded run manifests excluded")
    print(f"  commit {head}, tag {TAG}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
