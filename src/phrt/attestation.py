"""What the working tree actually was when a run executed.

A manifest that says ``dirty_tree: false`` is worth exactly as much as the check
behind it. In this repository that check was vacuous: the pathspecs it used were
written for an earlier layout in which the package sat under ``photon-ring/``,
and ``git status`` returns nothing at all for a pathspec that matches nothing,
so every run in the campaign reported a clean tree whatever its state. This
module replaces the claim with a record: the exact porcelain text, its digest,
the counts behind it, and, for each registered configuration, whether the bytes
on disk are the bytes in the commit the run reports.

Capture it at the *start* of a run. A run writes its own outputs, so an
attestation taken at the end would report untracked artifacts the run itself
created and could never distinguish those from a genuinely unclean start.
"""
from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# Repository-root-relative pathspecs for everything that decides a result:
# source, scripts, registry configs, tests, and the registered freezes. The
# freezes belong here even though they live under artifacts/: a freeze is a
# registered configuration, not a generated artifact, and a run against an
# uncommitted freeze is not a preregistered run.
REGISTERED_PATHSPECS = (":/src", ":/scripts", ":/configs", ":/tests",
                        ":/schemas", ":/artifacts/configs")


def _git(*args: str) -> tuple[int, str]:
    p = subprocess.run(["git", *args], capture_output=True, text=True, cwd=ROOT)
    return p.returncode, p.stdout


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def working_tree_state(pathspecs=REGISTERED_PATHSPECS) -> dict:
    """The porcelain record, verbatim, with the counts it implies."""
    rc_all, porcelain = _git("status", "--porcelain=v1", "-uall")
    rc_reg, scoped = _git("status", "--porcelain=v1", "-uall", "--", *pathspecs)
    if rc_all != 0 or rc_reg != 0:
        return {"available": False,
                "reason": "git status failed; treat this run as unattested"}
    lines = [ln for ln in scoped.splitlines() if ln.strip()]
    untracked = [ln for ln in lines if ln.startswith("??")]
    tracked = [ln for ln in lines if not ln.startswith("??")]
    rc_head, head = _git("rev-parse", "HEAD")
    rc_tree, tree = _git("rev-parse", "HEAD^{tree}")
    return {
        "available": True,
        "execution_commit": head.strip() if rc_head == 0 else None,
        "head_tree_sha": tree.strip() if rc_tree == 0 else None,
        "pathspecs": list(pathspecs),
        "porcelain_registered": scoped,
        "porcelain_registered_sha256": _sha256(scoped),
        "porcelain_whole_tree_sha256": _sha256(porcelain),
        "n_tracked_changes": len(tracked),
        "n_untracked": len(untracked),
        "tracked_clean": not tracked,
        "untracked_clean": not untracked,
        "clean": not lines,
        "rule": "scoped to registered paths: source, scripts, configs, tests, "
                "schemas and artifacts/configs. Generated artifacts elsewhere "
                "do not make a run unattested; an uncommitted freeze does",
    }


def file_attestation(path: str | Path) -> dict:
    """Whether the bytes on disk are the bytes in the commit being reported."""
    p = Path(path)
    rel = p.resolve().relative_to(ROOT).as_posix()
    data = p.read_bytes()
    rc_w, working_blob = _git("hash-object", "--", str(p))
    rc_c, committed_blob = _git("rev-parse", f"HEAD:{rel}")
    working_blob = working_blob.strip() if rc_w == 0 else None
    committed_blob = committed_blob.strip() if rc_c == 0 else None
    return {
        "path": rel,
        "sha256": hashlib.sha256(data).hexdigest(),
        "working_blob_sha": working_blob,
        "committed_blob_sha": committed_blob,
        "committed_at_execution_commit": bool(
            committed_blob and working_blob and committed_blob == working_blob),
        "tracked": committed_blob is not None,
    }


def attest(paths, pathspecs=REGISTERED_PATHSPECS) -> dict:
    """The full record: tree state plus one entry per registered file."""
    state = working_tree_state(pathspecs)
    files = [file_attestation(p) for p in paths]
    state["files"] = files
    state["all_registered_files_committed"] = all(
        f["committed_at_execution_commit"] for f in files)
    state["preregistered"] = bool(
        state.get("clean") and state["all_registered_files_committed"])
    return state
