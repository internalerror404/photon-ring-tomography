#!/usr/bin/env python3
"""Every occurrence of a claim amendment 023 qualifies, and where it lives.

The agent's first pass named four positions. The amendment requires all of
them, including captions, scope statements, evidence rows and derivative
releases, so this is a scan rather than a list: declared patterns over the
manuscript sources, the built manuscript, the reports, the docs and the
governance JSON, each hit classified and pointed at its replacement text.

Nothing here edits a frozen file. The output is an additive overlay plus a
dependency CSV; the old bytes stay exactly as freeze 022 pinned them.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REV = "docs/revisions/mahakal_v4_1"

# class -> (compiled pattern, ledger id, disposition, replacement key)
PATTERNS = {
    "ATTRIBUTION_UNRESOLVED_IMAGE": (
        re.compile(r"attributable to resolving|unresolved second image|"
                   r"unresolved-image (arm|control)", re.I),
        "C05a/C10", "PHYSICAL_INTERPRETATION_WITHDRAWN", "attribution"),
    "INDEX_SUM_ARM_LABEL": (
        re.compile(r"\bUNRESOLVED_IMAGE\b"),
        "C05a", "ALIAS_INDEX_SUM_CONTROL", "alias_index_sum"),
    "MECHANISM_SUBSTITUTION_LABEL": (
        re.compile(r"\bDELAY_ONLY\b|\bSPATIAL_ONLY\b"),
        "C05b", "ALIAS_INDEX_PAIRED_SUBSTITUTION", "alias_substitution"),
    "MECHANISM_SPLIT_NUMBERS": (
        re.compile(r"flattening the delays|transplanting the spatial map|"
                   r"delay diversity supplies"),
        "C05b", "PAIRING_DEPENDENT_COUNTERFACTUAL", "mechanism"),
    "INDEX_SUM_RETENTION_FIGURE": (
        re.compile(r"23\.7"),
        "C05a", "INDEX_CONTROL_QUALIFICATION", "retention"),
    "ABSOLUTE_RANK_VERSUS_FRACTION": (
        re.compile(r"destroys identifiability|identifiability falls|"
                   r"destroy identifiability"),
        "C07", "FRACTION_NOT_ABSOLUTE_RANK", "rank_fraction"),
    "FLUX_RUNNER_SEMANTICS": (
        re.compile(r"\bTOTAL_FLUX\b"),
        "C06", "RUNNER_SPECIFIC_ALIAS", "flux"),
}

REPLACEMENT = {
    "attribution":
        "At the declared operating point, ideal order-labeled data reduce "
        "aggregate contrast-morphology error relative to the direct arm. The "
        "tested all-order total-flux readout does not reproduce that material "
        "improvement. The cardinality-matched index-sum control is also "
        "nonmaterial, but it is not a co-registered unresolved image. The "
        "experiment therefore does not establish that a physical unresolved "
        "spatial image would fail, or that order labels rather than retained "
        "spatial information alone explain the gain.",
    "retention":
        "The archived index-sum control retains 23.7% of the resolved old-age "
        "sensitivity volume under its declared indexing and noise convention. "
        "This is not a measured retention fraction for a physical unresolved "
        "detector.",
    "mechanism":
        "The delay and spatial substitution comparisons are index-paired "
        "counterfactual ablations. Their numerical contrast is conditional on "
        "that pairing and does not establish a co-registered physical "
        "delay-versus-spatial decomposition.",
    "alias_index_sum":
        "Archived identifier UNRESOLVED_IMAGE reads as INDEX_SUM_CONTROL. The "
        "numbers stand for that linear map; the physical common-sky reading "
        "is withdrawn.",
    "alias_substitution":
        "Archived identifiers DELAY_ONLY and SPATIAL_ONLY read as "
        "INDEX_PAIRED_DELAY_SUBSTITUTION and "
        "INDEX_PAIRED_SPATIAL_SUBSTITUTION.",
    "rank_fraction":
        "Enrichment lowers the operational rank FRACTION and raises the "
        "absolute numerical rank: 224, 448, 528, 1045 at dimensions 224, 448, "
        "528, 1056, against fractions 0.897, 0.815, 0.835, 0.729. Read "
        "'destroys identifiability' as 'lowers the constrained share of a "
        "larger model'. Adding independent channels at fixed unknowns, source "
        "metric and noise cannot remove information; enlarging the unknown "
        "space is a different operation.",
    "flux":
        "TOTAL_FLUX is runner-specific: in E3C it is "
        "ORDER_RESOLVED_FLUX_CONTROL (24 rows, order labels retained); in "
        "HMT2 it is ALL_ORDER_FLUX_CONTROL (8 rows). Key every claim by "
        "runner and arm, never by arm alone.",
}

SCAN = [
    "src/phrt/manuscript/sections.py", "artifacts/manuscript/PAPER_I.md",
    "docs/Paper_I_v1_Current_Evidence_Ledger.md",
    "docs/PAPER_I_SUBMISSION_CHECKLIST.md", "docs/PAPER_I_RELEASE_NOTE.md",
    "docs/PAPER_I_PROOF_AUDIT.md",
    "artifacts/manuscript/figures/FIGURES.json",
    "artifacts/configs/PAPER_I_SUBMISSION_FREEZE_022.json",
    "artifacts/configs/HMT2_MAIN_RECORD_AMENDMENT_021.json",
    "artifacts/configs/HMT2_STAGE1_ENDPOINT_COMPLETION_AMENDMENT_020.json",
    "artifacts/configs/HMT1_CLOSURE_RECORD_018.json",
]
SCAN_GLOBS = ["artifacts/reports/*.md", "scripts/build_*report*.py",
              "scripts/build_evidence_ledger.py", "scripts/build_manuscript.py"]


def blob(rel: str) -> str:
    return subprocess.run(["git", "hash-object", rel], cwd=ROOT,
                          capture_output=True, text=True).stdout.strip()


def main(run_dir: Path) -> int:
    paths = [ROOT / p for p in SCAN if (ROOT / p).exists()]
    for g in SCAN_GLOBS:
        paths.extend(sorted(ROOT.glob(g)))
    paths = sorted(set(paths))

    rows, blobs = [], {}
    for p in paths:
        rel = str(p.relative_to(ROOT))
        if rel.startswith(REV):
            continue
        blobs.setdefault(rel, blob(rel))
        for n, line in enumerate(p.read_text(errors="replace").splitlines(), 1):
            for cls, (pat, ledger, disp, key) in PATTERNS.items():
                if pat.search(line):
                    rows.append({
                        "occurrence_class": cls, "ledger_id": ledger,
                        "path": rel, "line": n, "blob": blobs[rel],
                        "old_text": " ".join(line.split())[:200],
                        "disposition": disp,
                        "replacement_key": key,
                        "frozen_by_022": rel in json.loads(
                            (ROOT / "artifacts" / "configs"
                             / "PAPER_I_SUBMISSION_FREEZE_022.json"
                             ).read_text())["deliverables"],
                        "edit_in_place": "NO_OVERLAY_ONLY",
                    })

    csv_path = run_dir / "claim_dependency_map.csv"
    with csv_path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    by_cls: dict[str, int] = {}
    by_file: dict[str, int] = {}
    for r in rows:
        by_cls[r["occurrence_class"]] = by_cls.get(r["occurrence_class"], 0) + 1
        by_file[r["path"]] = by_file.get(r["path"], 0) + 1

    lines = [
        "# Manuscript and evidence correction overlay - Mahakal v4.1",
        "",
        "Additive. No frozen file is edited: freeze 022's thirteen "
        "deliverables and every canonical table keep the bytes it pinned. "
        "This overlay states what the affected text is to be read as, and "
        "`claim_dependency_map.csv` lists every occurrence it applies to.",
        "",
        f"- generated {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}",
        f"- {len(rows)} occurrences across {len(by_file)} files",
        "- controlling record: PAPER_I_DEFECT_AMENDMENT_023",
        "",
        "## Replacement meanings",
        "",
    ]
    for key, text in REPLACEMENT.items():
        n = sum(1 for r in rows if r["replacement_key"] == key)
        lines += [f"### `{key}` — {n} occurrences", "", f"> {text}", ""]
    lines += ["## Occurrences by class", "",
              "| class | ledger | count |", "|---|---|---:|"]
    for cls, n in sorted(by_cls.items(), key=lambda kv: -kv[1]):
        lines.append(f"| `{cls}` | {PATTERNS[cls][1]} | {n} |")
    lines += ["", "## Occurrences by file", "",
              "| file | count | frozen by 022 |", "|---|---:|---|"]
    frozen = json.loads((ROOT / "artifacts" / "configs"
                         / "PAPER_I_SUBMISSION_FREEZE_022.json"
                         ).read_text())["deliverables"]
    for f, n in sorted(by_file.items(), key=lambda kv: -kv[1]):
        lines.append(f"| `{f}` | {n} | {'yes' if f in frozen else 'no'} |")
    lines += [
        "", "## What is not changed", "",
        "The archived numbers are correct for the maps they describe and are "
        "not restated: 23.7%, the 0.98/0.57 mechanism contrast, every rank "
        "and every morphology score stand. What is withdrawn is the physical "
        "reading of two control families, and what is added is the runner "
        "keying of the flux control. `PAIRING_DESTROYED` is untouched; it "
        "permutes by design.", ""]
    (run_dir / "manuscript_claim_overlay.md").write_text("\n".join(lines))

    print(f"wrote {csv_path.relative_to(ROOT)}  ({len(rows)} occurrences)")
    print(f"wrote {(run_dir / 'manuscript_claim_overlay.md').relative_to(ROOT)}")
    for cls, n in sorted(by_cls.items(), key=lambda kv: -kv[1]):
        print(f"  {n:3d}  {cls}")
    print(f"  files touched: {len(by_file)}; frozen-by-022 among them: "
          f"{sum(1 for f in by_file if f in frozen)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main((ROOT / sys.argv[1]).resolve()))
