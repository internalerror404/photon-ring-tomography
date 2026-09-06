"""Preconditions that must hold before an outcome-bearing run may start.

Review 024. Three of the seven injected failures are not conditions a report
can evaluate after the fact -- they are reasons a run must not begin: inputs
that no longer hash to their freeze, a target column set that has drifted from
the committed manifest, and an output directory that already exists. Each
raises here rather than being recorded as a caveat later.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np


class GuardFailure(RuntimeError):
    """A precondition failed. The run does not start."""


def sha256(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def require_fresh_output_dir(path: Path) -> Path:
    """Never overwrite an emitted run."""
    path = Path(path)
    if path.exists() and any(path.iterdir()):
        raise GuardFailure(
            f"output directory {path} already exists and is not empty; a run "
            "directory is written once and never replaced")
    path.mkdir(parents=True, exist_ok=True)
    return path


def verify_inputs(freeze_path: Path, root: Path) -> dict:
    """Every frozen input must still hash to what the freeze recorded."""
    freeze = json.loads(Path(freeze_path).read_text())
    files = freeze["files"] if "files" in freeze else freeze["inputs"]
    bad, missing = {}, []
    for rel, want in files.items():
        p = Path(root) / rel
        if not p.exists():
            missing.append(rel)
            continue
        got = sha256(p)
        if got != want:
            bad[rel] = {"frozen": want, "current": got}
    if missing or bad:
        raise GuardFailure(
            f"input freeze violated: {len(missing)} missing, {len(bad)} "
            f"modified. missing={missing[:5]} modified={list(bad)[:5]}")
    return {"n_inputs": len(files), "all_match": True,
            "freeze_sha256": sha256(freeze_path)}


def verify_target_columns(manifest_path: Path, target: np.ndarray,
                          nuisance: np.ndarray) -> dict:
    """The recomputed selection must equal the committed one, exactly.

    The replay reuses the original support rule; if that rule now yields a
    different column set, the replay is not a replay and must stop rather than
    quietly measuring something else.
    """
    man = json.loads(Path(manifest_path).read_text())
    want_t, want_n = int(man["n_target_columns"]), int(man["n_nuisance_columns"])
    got_t, got_n = int(target.sum()), int(nuisance.sum())
    if (got_t, got_n) != (want_t, want_n):
        raise GuardFailure(
            f"target selection drifted: manifest has {want_t} target and "
            f"{want_n} nuisance columns, the rule now gives {got_t} and "
            f"{got_n}. This is not a replay")
    if "target_column_indices" in man:
        want_idx = list(man["target_column_indices"])
        got_idx = [int(i) for i in np.flatnonzero(target)]
        if want_idx != got_idx:
            raise GuardFailure(
                "target column indices differ from the committed manifest "
                "even though the counts agree")
    modes = man.get("temporal_modes_outside_direct_footprint")
    return {"n_target": got_t, "n_nuisance": got_n,
            "indices_checked": "target_column_indices" in man,
            "temporal_modes_outside_direct_footprint": modes}
