"""The only door to a physical evaluation, and the ledger it charges.

Ruling 028 requires a committed input snapshot before any uncached physical
query, and requires the query entry point itself to check it -- not the report
written afterwards. So the guard lives here, beside the call, and every path
to the pinned tracer or the pinned boundary equations goes through it.

Nothing is cached silently. A call that the guard refuses raises; it does not
fall back, substitute a backend, or return a filled value.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
TRANSFER = "transfer"
BOUNDARY = "boundary"


class GuardFailure(RuntimeError):
    """Raised instead of performing an unregistered or over-budget query."""


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


class Guard:
    """Verifies the freeze, then meters every physical call against it."""

    def __init__(self, freeze_path: Path, allow_dirty: bool = False):
        self.path = Path(freeze_path)
        if not self.path.exists():
            raise GuardFailure(f"no committed freeze at {self.path}")
        self.fz = json.loads(self.path.read_text())
        self.spent = {TRANSFER: 0, BOUNDARY: 0}
        self._verify(allow_dirty)
        self.armed = True

    def _verify(self, allow_dirty: bool) -> None:
        bad = {f: {"frozen": h,
                   "now": sha(ROOT / f) if (ROOT / f).exists() else None}
               for f, h in self.fz["files"].items()
               if not (ROOT / f).exists() or sha(ROOT / f) != h}
        if bad:
            raise GuardFailure(f"frozen inputs changed: {json.dumps(bad)}")
        if not allow_dirty:
            dirty = subprocess.run(
                ["git", "status", "--porcelain", "--", *self.fz["files"]],
                cwd=ROOT, capture_output=True, text=True).stdout.strip()
            if dirty:
                raise GuardFailure(
                    "the registered tree is not clean; commit before "
                    f"querying:\n{dirty}")
        for k in ("detector", "clock", "solver_policy", "selection_rule",
                  "ledger"):
            if k not in self.fz:
                raise GuardFailure(f"the freeze does not pin {k!r}")
        # HEAD must not have moved *under the frozen files*. Requiring HEAD
        # to equal the freeze commit would be self-defeating: committing the
        # freeze itself advances HEAD without changing a single input.
        base = self.fz.get("commit_at_freeze_time")
        if base:
            moved = subprocess.run(
                ["git", "diff", "--name-only", base, "HEAD", "--",
                 *self.fz["files"]], cwd=ROOT, capture_output=True,
                text=True)
            if moved.returncode != 0:
                raise GuardFailure(
                    f"cannot compare against the freeze commit {base[:12]}: "
                    f"{moved.stderr.strip()}")
            if moved.stdout.strip():
                raise GuardFailure(
                    "frozen inputs changed between the freeze commit "
                    f"{base[:12]} and HEAD:\n{moved.stdout.strip()}")

    def remaining(self, kind: str) -> int:
        led = self.fz["ledger"]
        return int(led[f"{kind}_remaining"]) - self.spent[kind]

    def charge(self, kind: str, n: int, why: str) -> None:
        """Count every evaluation, including failures and retries."""
        if not self.armed:
            raise GuardFailure("the guard is closed")
        if kind not in self.spent:
            raise GuardFailure(f"unknown ledger {kind!r}")
        if n < 0:
            raise GuardFailure("a query count cannot be negative")
        if n > self.remaining(kind):
            raise GuardFailure(
                f"{kind} cap reached: {why} needs {n}, "
                f"{self.remaining(kind)} left of "
                f"{self.fz['ledger'][f'{kind}_remaining']}")
        self.spent[kind] += n

    def snapshot(self) -> dict:
        led = self.fz["ledger"]
        try:
            where = str(self.path.relative_to(ROOT))
        except ValueError:
            where = str(self.path)
        return {"freeze": where,
                "commit_at_freeze_time": self.fz["commit_at_freeze_time"],
                "verified_input_hashes": True,
                "registered_tree_clean": True,
                "spent_this_run": dict(self.spent),
                "remaining_after_run": {k: self.remaining(k)
                                        for k in self.spent},
                "lifetime": {k: led[k] for k in sorted(led)}}


def trace_points(alpha: np.ndarray, beta: np.ndarray, order: int,
                 guard: Guard, why: str) -> dict:
    """The pinned tracer, on arbitrary screen points. Charged, never cached.

    Calls ``aart.raytracing_f.calculate_observables``, which is the same
    primitive ``raytrace`` uses on the archived grids; only the point set
    differs. No backend is substituted and no failed value is filled.
    """
    from aart.raytracing_f import calculate_observables
    a = np.atleast_1d(np.asarray(alpha, float))
    b = np.atleast_1d(np.asarray(beta, float))
    if a.shape != b.shape:
        raise GuardFailure("alpha and beta must match")
    d = guard.fz["solver_policy"]
    guard.charge(TRANSFER, int(a.size), why)
    grid = np.stack([a, b], axis=1)
    mask = np.ones(a.size, bool)
    thetao = float(d["inclination_deg"]) * np.pi / 180.0
    rs, sign, t, phi = calculate_observables(
        grid, mask, thetao, float(d["spin"]), int(order),
        distance=float(d["d_obs"]))
    rs = np.asarray(rs, float).ravel()
    return {"alpha": a, "beta": b, "order": int(order),
            "source_r": rs, "radial_sign": np.asarray(sign, float).ravel(),
            "coordinate_time": np.asarray(t, float).ravel(),
            "source_phi": np.asarray(phi, float).ravel(),
            "n_evaluations": int(a.size), "why": why}
