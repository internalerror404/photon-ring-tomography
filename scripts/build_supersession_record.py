#!/usr/bin/env python3
"""Mark every pre-G10q physical-operator artifact SUPERSEDED_MEASUREMENT_MODEL_DEFECT.

The corrected measurement convention landed in d6869f8. Everything the physical
operator produced before it was computed with c = g^3 and a flat per-row sigma,
which makes Fisher information scale with the number of rows. Those artifacts are
not deleted -- the whole point of the ledger is that a wrong result stays on the
record -- but they must be unmistakably marked so no manuscript table can be
built from them by accident.

Two classes are distinguished, because conflating them would overstate the
damage:

  SUPERSEDED_MEASUREMENT_MODEL_DEFECT
      produced by the physical operator under the retired convention. Its
      numbers are wrong or unverifiable and it must not be cited.

  PRESERVED_MEASUREMENT_MODEL_INDEPENDENT
      produced in the same phase but by ray-map or instrumentation code that
      never instantiates the operator, so the convention change cannot have
      touched it. Verified byte-identical across the correction.

The record stores the pre-correction sha256 read out of git, the post-correction
sha256 on disk, and whether the bytes moved.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from phrt import provenance

PRE = "0ef341dae3b21bc2bdd0e54a18971cff208af783"     # last commit before the correction
FIX = "d6869f8d1c08889fee34e91d392c2bbc1bc9a62f"     # the correction itself

# Artifacts whose values pass through PhysicalOperator, and therefore through the
# measurement model. Everything else in the same phase is listed separately.
OPERATOR_DEPENDENT = (
    "artifacts/tables/e3b_age_information",
    "artifacts/tables/e3b_attenuation_decomposition",
    "artifacts/tables/e3b_gamma_info",
    "artifacts/tables/e3b_matched_support_attenuation",
    "artifacts/tables/e3b_near_null_scaling",
    "artifacts/tables/e3b_singular_spectra",
    "artifacts/tables/e3b_temporal_depth_curve",
    "artifacts/tables/e3b_weight_semantics",
    "artifacts/tables/s0_operator_comparison",
    "artifacts/gates/e3b_correctness_gates.json",
    "artifacts/provenance/E3B_ARTIFACT_MANIFEST.json",
    "artifacts/reports/E3B_PHYSICAL_OPERATOR_CANARY.md",
    "artifacts/reports/E3B_TRANSFER_WEIGHT_AUDIT.md",
    "artifacts/reports/S0_BACKEND_CANARY.md",
)
# Same phase, but produced by ray-map or instrumentation code that never builds
# an operator.
MODEL_INDEPENDENT = (
    "artifacts/tables/e3b_field_convergence",
    "artifacts/tables/e3b_field_convergence_a098_i075",
    "artifacts/tables/e3b_per_order_ray_count",
    "artifacts/tables/e3b_age_support_bookkeeping",
    "artifacts/configs/E3B_FREEZE.json",
    "artifacts/reports/E3B_RETARDED_TIME_VALIDATION.md",
)
SUFFIXES = (".csv", ".parquet")


def expand(stems: tuple[str, ...]) -> list[str]:
    out = []
    for s in stems:
        if Path(s).suffix:
            out.append(s)
        else:
            out.extend(f"{s}{x}" for x in SUFFIXES)
    return out


def git_blob_sha256(commit: str, path: str) -> str | None:
    r = subprocess.run(["git", "show", f"{commit}:{path}"], cwd=ROOT,
                       capture_output=True)
    if r.returncode != 0:
        return None
    return hashlib.sha256(r.stdout).hexdigest()


def disk_sha256(path: str) -> str | None:
    p = ROOT / path
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


def _strip_identity(blob: bytes) -> bytes:
    """Drop the generated provenance identity line from a markdown report.

    Every report stamps the commit it was generated at, so a report regenerated
    at a later commit differs in bytes even when nothing scientific moved. The
    supersession record needs to distinguish those two cases, or a re-run would
    look like a corrected result.
    """
    keep = [ln for ln in blob.split(b"\n")
            if not (ln.startswith(b"- branch ") and b", commit `" in ln)]
    return b"\n".join(keep)


def content_changed(commit: str, path: str) -> bool | None:
    """Did anything but the provenance stamp move?"""
    r = subprocess.run(["git", "show", f"{commit}:{path}"], cwd=ROOT,
                       capture_output=True)
    p = ROOT / path
    if r.returncode != 0 or not p.exists():
        return None
    a, b = r.stdout, p.read_bytes()
    if path.endswith(".md"):
        a, b = _strip_identity(a), _strip_identity(b)
    return a != b


def run_manifests(commit: str) -> list[str]:
    r = subprocess.run(["git", "ls-tree", "-r", "--name-only", commit,
                        "artifacts/manifests/"], cwd=ROOT,
                       capture_output=True, text=True)
    return [p for p in r.stdout.split()
            if any(k in p for k in ("E3B", "E3BPRE", "G5AB", "S0"))]


def main() -> int:
    rows, unexpected, still_stale = [], [], []
    for path in expand(OPERATOR_DEPENDENT):
        pre, post = git_blob_sha256(PRE, path), disk_sha256(path)
        changed = (pre != post) if (pre and post) else None
        # Supersession attaches to the pre-correction *bytes*, not to the path.
        # The file on disk is the regenerated one and is citable; what must never
        # be cited is the version at PRE, which lives in git history. A file that
        # did not move is the case to worry about: either it is genuinely
        # insensitive to the convention, or it was never regenerated.
        rows.append({"path": path, "class": "operator_output",
                     "disposition": "SUPERSEDED_MEASUREMENT_MODEL_DEFECT",
                     "applies_to": "the bytes at " + PRE[:12],
                     "current_disk_state": ("REGENERATED_POST_CORRECTION" if changed
                                            else "UNCHANGED_ACROSS_THE_CORRECTION"),
                     "sha256_pre_correction": pre, "sha256_post_correction": post,
                     "bytes_changed": changed,
                     "superseded_by_commit": FIX})
        if changed is False:
            still_stale.append(path)
    for path in expand(MODEL_INDEPENDENT):
        pre, post = git_blob_sha256(PRE, path), disk_sha256(path)
        changed = (pre != post) if (pre and post) else None
        real = content_changed(PRE, path)
        rows.append({"path": path, "class": "measurement_model_independent",
                     "disposition": ("PRESERVED_MEASUREMENT_MODEL_INDEPENDENT"
                                     if real is False else
                                     "SUPERSEDED_MEASUREMENT_MODEL_DEFECT"),
                     "sha256_pre_correction": pre, "sha256_post_correction": post,
                     "bytes_changed": changed,
                     "content_changed_excluding_provenance_stamp": real,
                     "note": ("regenerated at a later commit; only the provenance "
                              "identity line differs" if changed and real is False
                              else None),
                     "superseded_by_commit": FIX})
        if real:
            # a file classified as model-independent that moved is a
            # classification error, not a rounding difference: say so loudly
            unexpected.append(path)
    for path in run_manifests(PRE):
        rows.append({"path": path, "class": "run_manifest_pre_correction",
                     "disposition": "SUPERSEDED_MEASUREMENT_MODEL_DEFECT",
                     "sha256_pre_correction": git_blob_sha256(PRE, path),
                     "sha256_post_correction": disk_sha256(path),
                     "bytes_changed": False, "superseded_by_commit": FIX})

    prov = provenance.collect()
    doc = {
        "schema": "phrt-supersession/1",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "git_commit": prov.git_commit,
        "defect": "D-H_flat_sigma_measurement_convention",
        "pre_correction_commit": PRE,
        "correcting_commit": FIX,
        "rule": "no manuscript-facing table may be built from any artifact "
                "marked SUPERSEDED_MEASUREMENT_MODEL_DEFECT",
        "counts": {
            "superseded": sum(1 for r in rows
                              if r["disposition"] == "SUPERSEDED_MEASUREMENT_MODEL_DEFECT"),
            "preserved_model_independent":
                sum(1 for r in rows
                    if r["disposition"] == "PRESERVED_MEASUREMENT_MODEL_INDEPENDENT"),
        },
        "misclassified_model_independent": unexpected,
        "operator_outputs_unchanged_across_the_correction": still_stale,
        "supersession_scope": "the disposition marks the pre-correction bytes of "
                              "each path. The regenerated file now on disk is "
                              "canonical and citable; the version at the "
                              "pre-correction commit is not.",
        "byte_vs_content": "a markdown report regenerated at a later commit "
                           "differs in bytes because it stamps its own commit; "
                           "the classification uses the content comparison with "
                           "that line removed",
        "artifacts": rows,
    }
    out = ROOT / "artifacts" / "SUPERSEDED_PRE_G10Q.json"
    out.write_text(json.dumps(doc, indent=2) + "\n")
    print(f"wrote {out.relative_to(ROOT)}")
    print(f"  superseded {doc['counts']['superseded']}, "
          f"preserved model-independent {doc['counts']['preserved_model_independent']}")
    if unexpected:
        print(f"  WARNING: classified model-independent but the content moved: {unexpected}")
    if still_stale:
        print(f"  operator outputs whose bytes did not move across the correction "
              f"({len(still_stale)}): {still_stale}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
