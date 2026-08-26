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

import argparse
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

# R0_REPAIR_AMENDMENT_004 adds a v2 line. The v1 freeze is the record of the
# E3C v1 manuscript line and is never rewritten; v2 covers the accepted
# post-E3C-v2 set, which the v1 file could not, because it predates the
# re-execution and mismatches 42 of its own entries against the accepted
# artifact commit.
V2_CAMPAIGN_COMMIT = "8345068676b15ce8f96a76da9d92b159db215f1d"
V2_LINE = {
    "accepted_base_commit": "0ef341dae3b21bc2bdd0e54a18971cff208af783",
    "measurement_correction_commit": "d6869f8d1c08889fee34e91d392c2bbc1bc9a62f",
    "e3c_execution_code_commit": "546763ed29e2be3fb129ec707cb07ee37a4f7db8",
    "e3c_artifact_commit": "7d610121adc95fb641ab5692d37d2b761b082039",
    "e3c_age_interval_amendment_commit":
        "f034f19829623efa1f29bdcf27f95e10bd2de62e",
    "r0_pilot_artifact_commit": V2_CAMPAIGN_COMMIT,
}
# Artifacts the reviewer accepted as evidence but not as a final result. They
# are canonical -- reproducible, hashed, citable in methods and preregistration
# -- and they are not a reconstruction claim.
V2_NOT_CITABLE_AS_RESULT_PREFIXES = (
    "artifacts/tables/r0_pilot_",
    "artifacts/reports/R0_CANARY_RECONSTRUCTION_PILOT.md",
    "artifacts/configs/R0_PROPOSED_R1_MAIN_FREEZE.json",
)

TAG = "paper-I-campaign-final"
# The commit the tag names, pinned literally. A fresh clone that does not
# carry the tag must still reproduce this freeze, and the paper must keep
# citing the commit that produced its numbers rather than whatever is
# checked out. When the tag is present the two are cross-checked.
CAMPAIGN_COMMIT = "03b0d1c9c63131aa553904df0c09849d641dee8f"

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
    ap = argparse.ArgumentParser()
    ap.add_argument("--v2", action="store_true",
                    help="emit CANONICAL_ARTIFACT_FREEZE_V2.json over the "
                         "accepted post-E3C-v2 set; leaves v1 untouched")
    args = ap.parse_args()
    reg = load_registry()
    prov = provenance.collect()
    r = subprocess.run(["git", "rev-list", "-n", "1", TAG], cwd=ROOT,
                       capture_output=True, text=True)
    tag_resolved = r.returncode == 0 and bool(r.stdout.strip())
    if tag_resolved and r.stdout.strip() != CAMPAIGN_COMMIT:
        raise SystemExit(f"tag {TAG} points at {r.stdout.strip()}, but the "
                         f"freeze pins {CAMPAIGN_COMMIT}")
    head = V2_CAMPAIGN_COMMIT if args.v2 else CAMPAIGN_COMMIT
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
        "schema": "phrt-canonical-freeze/2" if args.v2
                  else "phrt-canonical-freeze/1",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "campaign_tag": TAG,
        "campaign_commit": head,
        "campaign_commit_source": "pinned; " + ("cross-checked against local "
                                  "git tag " + TAG if tag_resolved else
                                  "tag not present in this clone"),
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
    if args.v2:
        doc["campaign_commit_source"] = (
            "pinned to the accepted R0 pilot artifact commit")
        doc["supersedes"] = {
            "path": "artifacts/CANONICAL_ARTIFACT_FREEZE.json",
            "reason": "the v1 freeze was built at the E3C v1 amendment commit "
                      "and mismatches 42 of its own entries against the accepted "
                      "E3C v2 artifact commit. It is preserved verbatim as the "
                      "record of the v1 manuscript line, together with its "
                      "snapshot under artifacts/v1_line/, and is not rewritten",
            "preserved_snapshot": "artifacts/v1_line/",
        }
        doc["accepted_line"] = V2_LINE
        doc["amendment"] = "R0_REPAIR_AMENDMENT_004"
        doc["citation_policy"] = {
            "rule": "an artifact listed here is reproducible and hashed. That "
                    "is not the same as being citable as a final result",
            "not_citable_as_a_reconstruction_result": sorted(
                rel for rel in canonical
                if rel.startswith(V2_NOT_CITABLE_AS_RESULT_PREFIXES)),
            "disposition": "PILOT_USABLE_MAIN_TEST_NOT_AUTHORIZED",
            "reason": "the R0B pilot is accepted as positive validation "
                      "evidence and may inform methods and preregistration. The "
                      "public reconstruction section needs the repaired, "
                      "independently held-out result",
        }
        doc["pilot_governance_deviations"] = [
            {"id": "R0B_FREEZE_COMMIT_ATTESTATION_INCONSISTENCY",
             "disposition": "PILOT_USABLE_MAIN_TEST_NOT_AUTHORIZED",
             "finding": "the R0B manifest reports git_commit e1619fa with "
                        "dirty_tree false and a 610 s run, but the freeze it "
                        "names was committed later, in 8345068. The freeze "
                        "existed uncommitted during execution",
             "root_cause": "provenance.git_dirty used pathspecs from an earlier "
                           "layout (:/photon-ring/src and siblings). git status "
                           "returns nothing for a pathspec matching nothing, so "
                           "the check was vacuous and every manifest in the "
                           "campaign reported a clean tree whatever its state",
             "scope": "systematic, not one run",
             "repair": "pathspecs corrected and artifacts/configs added; "
                       "phrt.attestation records the porcelain text, its digest, "
                       "the committed and working blob SHAs, the head tree SHA "
                       "and the tracked/untracked counts; gate "
                       "R0_G13_freeze_commit_attestation fails a run whose "
                       "freeze is not committed at the reported commit"},
            {"id": "R0_G6_GATE_SEMANTICS_MISMATCH",
             "disposition": "CORRECTED_NO_RERUN_REQUIRED",
             "finding": "the record named R0_G6_age_probe_normalization carried "
                        "the freeze's 1e-12 threshold while measuring a "
                        "4001-point quadrature cross-check at 5e-3, reporting "
                        "5.551e-5. The canonical table therefore read as though "
                        "5.551e-5 < 1e-12",
             "root_cause": "two different checks recorded under one gate name",
             "repair": "split into R0_G6a_declared_probe_unit_norm at 1e-12, "
                       "measuring 0 by construction, and "
                       "R0_G6b_independent_quadrature_crosscheck with its own "
                       "threshold frozen before R0C. The probe itself was "
                       "correct, so no physical rerun follows from this"},
        ]
    out = (ROOT / "artifacts" / ("CANONICAL_ARTIFACT_FREEZE_V2.json" if args.v2
                                 else "CANONICAL_ARTIFACT_FREEZE.json"))
    out.write_text(json.dumps(doc, indent=2) + "\n")
    print(f"wrote {out.relative_to(ROOT)}")
    print(f"  {len(canonical)} canonical artifacts, "
          f"{len(set(excluded))} superseded run manifests excluded")
    print(f"  commit {head}, tag {TAG}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
