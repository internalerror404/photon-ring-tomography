#!/usr/bin/env python3
"""Assemble the manuscript source bundle: everything needed to rebuild the paper.

A reviewer should be able to take this one archive and regenerate the manuscript
byte-for-byte, or find any number in it back to the artifact it came from. The
bundle therefore carries the manuscript, the claim ledger, the freezes, the gate
ledger, the amendment and defect records, the canonical tables the ledger cites,
and the scripts that build and verify all of it -- and a MANIFEST listing the
sha256 of every entry.

Ray maps are deliberately excluded: they are large binary HDF5 and their digests
are pinned in the operator grid freeze, which is in the bundle.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import sys
import tarfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from phrt import provenance

OUT = ROOT / "artifacts" / "manuscript"
BUNDLE = OUT / "PAPER_I_SOURCE_BUNDLE.tar.gz"
MANIFEST = OUT / "PAPER_I_SOURCE_BUNDLE_MANIFEST.json"

EXPLICIT = [
    "artifacts/manuscript/PAPER_I.md",
    "artifacts/manuscript/PAPER_I.html",
    "artifacts/manuscript/PAPER_I.pdf",
    "artifacts/manuscript/CLAIM_LEDGER.json",
    "artifacts/CANONICAL_ARTIFACT_FREEZE.json",
    "artifacts/SUPERSEDED_PRE_G10Q.json",
    "artifacts/GATE_DASHBOARD.json",
    "artifacts/PREFIX_INVALIDATION_LEDGER.json",
    "artifacts/gates/correctness_gates.json",
    "artifacts/gates/e3c_correctness_gates.json",
    "artifacts/gates/e3d_correctness_gates.json",
    "artifacts/gates/s0_correctness_gates.json",
    "artifacts/configs/E3C_OPERATOR_GRID_FREEZE.json",
    "artifacts/configs/AMENDMENT_002_LOCALIZED_CLASS_MECHANISM_DIAGNOSTIC.json",
    "artifacts/configs/E3B_FREEZE.json",
    "configs/paper1_experiment_registry_v0.2.yaml",
    "scripts/build_manuscript.py",
    "scripts/verify_manuscript.py",
    "scripts/compile_manuscript.py",
    "scripts/build_canonical_freeze.py",
    "scripts/build_supersession_record.py",
    "scripts/build_gate_dashboard.py",
    "scripts/build_e3c_tables.py",
    "scripts/build_e3c_reports.py",
    "scripts/build_e3d_reports.py",
    "scripts/run_e3c_operator_grid.py",
    "scripts/run_e3d_source_class_stress.py",
    "scripts/build_e3c_freeze.py",
    "src/phrt/manuscript/ledger.py",
    "src/phrt/manuscript/render.py",
    "src/phrt/manuscript/sections.py",
    "src/phrt/io/dashboard.py",
]
GLOBS = ["artifacts/reports/*.md", "environments/*.yml"]


def cited_tables() -> list[str]:
    doc = json.loads((OUT / "CLAIM_LEDGER.json").read_text())
    out = set()
    for p in doc["artifacts_cited"]:
        out.add(p)
        if p.endswith(".parquet"):
            csv = p[:-len(".parquet")] + ".csv"
            if (ROOT / csv).exists():
                out.add(csv)
    return sorted(out)


def main() -> int:
    paths: list[str] = []
    for p in EXPLICIT + cited_tables():
        if (ROOT / p).exists():
            paths.append(p)
        else:
            print(f"  missing, skipped: {p}")
    for g in GLOBS:
        paths.extend(str(q.relative_to(ROOT)) for q in sorted(ROOT.glob(g)))
    paths = sorted(set(paths))

    entries = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in paths}
    prov = provenance.collect()
    fz = json.loads((ROOT / "artifacts" / "CANONICAL_ARTIFACT_FREEZE.json").read_text())
    doc = {
        "schema": "phrt-source-bundle/1",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "git_commit": prov.git_commit,
        "campaign_tag": fz["campaign_tag"],
        "campaign_commit": fz["campaign_commit"],
        "rebuild": ["python scripts/build_canonical_freeze.py",
                    "python scripts/build_manuscript.py",
                    "python scripts/compile_manuscript.py",
                    "python scripts/verify_manuscript.py"],
        "excluded": "artifacts/raymaps/*.h5 -- large binaries whose sha256 are "
                    "pinned in artifacts/configs/E3C_OPERATOR_GRID_FREEZE.json, "
                    "which is included",
        "n_entries": len(entries),
        "entries": entries,
    }
    MANIFEST.write_text(json.dumps(doc, indent=2) + "\n")

    # Deterministic archive: fixed member metadata and a gzip header with no
    # timestamp, so rebuilding an unchanged bundle produces identical bytes and
    # the repository does not churn a 500 KB binary on every regeneration.
    def _norm(ti: tarfile.TarInfo) -> tarfile.TarInfo:
        ti.mtime, ti.uid, ti.gid = 0, 0, 0
        ti.uname = ti.gname = ""
        ti.mode = 0o644 if ti.isfile() else 0o755
        return ti

    if BUNDLE.exists():
        BUNDLE.unlink()
    with open(BUNDLE, "wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as gz:
            with tarfile.open(fileobj=gz, mode="w", format=tarfile.GNU_FORMAT) as tf:
                for p in paths:
                    tf.add(ROOT / p, arcname=f"paper_I_source/{p}", filter=_norm)
                tf.add(MANIFEST, arcname="paper_I_source/MANIFEST.json",
                       filter=_norm)

    print(f"wrote {BUNDLE.relative_to(ROOT)} "
          f"({BUNDLE.stat().st_size // 1024} KB, {len(paths)} files)")
    print(f"wrote {MANIFEST.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
