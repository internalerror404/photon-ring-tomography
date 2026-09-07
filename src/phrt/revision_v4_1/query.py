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

    def __init__(self, freeze_path: Path, allow_dirty: bool = False,
                 ledger_path: Path | None = None):
        self.path = Path(freeze_path)
        if not self.path.exists():
            raise GuardFailure(f"no committed freeze at {self.path}")
        self.fz = json.loads(self.path.read_text())
        self.spent = {TRANSFER: 0, BOUNDARY: 0}
        self.attempted = {TRANSFER: 0, BOUNDARY: 0}
        self.failed = {TRANSFER: 0, BOUNDARY: 0}
        self.events: list[dict] = []
        self.ledger_path = Path(ledger_path) if ledger_path else None
        self._verify(allow_dirty)
        self.armed = True
        self._persist()

    def _persist(self) -> None:
        """Write the attempt ledger now, so a crash cannot erase a charge."""
        if self.ledger_path is None:
            return
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        self.ledger_path.write_text(json.dumps({
            "freeze": str(self.path), "attempted": self.attempted,
            "completed": self.spent, "failed": self.failed,
            "events": self.events,
            "note": "written after every reservation and completion, so an "
                    "exception in the solver or the report cannot lose a "
                    "charge"}, indent=2) + "\n")

    def reserve(self, kind: str, n: int, why: str) -> int:
        """Take the allowance BEFORE the physical call, not after it.

        Charging after the solver returns lets an oversized batch run to
        completion and only then be refused, which is not a budget.
        """
        if not self.armed:
            raise GuardFailure("the guard is closed")
        if kind not in self.spent:
            raise GuardFailure(f"unknown ledger {kind!r}")
        if n < 0:
            raise GuardFailure("a query count cannot be negative")
        if n > self.remaining(kind):
            raise GuardFailure(
                f"{kind} cap reached before the call: {why} needs {n}, "
                f"{self.remaining(kind)} left of "
                f"{self.fz['ledger'][f'{kind}_remaining']}")
        self.attempted[kind] += n
        self.spent[kind] += n            # reserved, hence already charged
        tok = len(self.events)
        self.events.append({"token": tok, "kind": kind, "reserved": n,
                            "why": why, "outcome": "reserved"})
        self._persist()
        return tok

    def complete(self, token: int, completed: int, failed: int = 0) -> None:
        """``completed`` and ``failed`` partition the reservation."""
        e = self.events[token]
        if completed + failed > e["reserved"]:
            raise GuardFailure("more evaluations reported than reserved")
        self.failed[e["kind"]] += failed
        e.update({"outcome": "completed", "completed": completed,
                  "failed": failed})
        self._persist()

    def abort(self, token: int, reason: str) -> None:
        """The reservation stays charged; a failed attempt is still an attempt."""
        e = self.events[token]
        self.failed[e["kind"]] += e["reserved"]
        e.update({"outcome": "aborted", "reason": reason})
        self._persist()

    def _verify(self, allow_dirty: bool) -> None:
        bad = {f: {"frozen": h,
                   "now": sha(ROOT / f) if (ROOT / f).exists() else None}
               for f, h in self.fz["files"].items()
               if not (ROOT / f).exists() or sha(ROOT / f) != h}
        if bad:
            raise GuardFailure(f"frozen inputs changed: {json.dumps(bad)}")
        # Installed backend sources are pinned by hash but live outside the
        # repository, so only the tracked files can be asked about git state.
        tracked = [f for f in self.fz["files"] if not Path(f).is_absolute()]
        if not allow_dirty:
            dirty = subprocess.run(
                ["git", "status", "--porcelain", "--", *tracked],
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
                ["git", "diff", "--name-only", base, "HEAD", "--", *tracked],
                cwd=ROOT, capture_output=True, text=True)
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
        """Reserve and immediately close, for a call already made atomically."""
        self.complete(self.reserve(kind, n, why), n)

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
                "attempted_this_run": dict(self.attempted),
                "failed_this_run": dict(self.failed),
                "reserved_before_every_physical_call": True,
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
    tok = guard.reserve(TRANSFER, int(a.size), why)
    grid = np.stack([a, b], axis=1)
    mask = np.ones(a.size, bool)
    thetao = float(d["inclination_deg"]) * np.pi / 180.0
    try:
        rs, sign, t, phi = calculate_observables(
            grid, mask, thetao, float(d["spin"]), int(order),
            distance=float(d["d_obs"]))
    except BaseException as exc:
        guard.abort(tok, f"{type(exc).__name__}: {exc}")
        raise
    rs = np.asarray(rs, float).ravel()
    nf = int((~np.isfinite(rs)).sum())
    guard.complete(tok, int(a.size) - nf, nf)
    return {"alpha": a, "beta": b, "order": int(order),
            "source_r": rs, "radial_sign": np.asarray(sign, float).ravel(),
            "coordinate_time": np.asarray(t, float).ravel(),
            "source_phi": np.asarray(phi, float).ravel(),
            "n_evaluations": int(a.size), "why": why}


def solve_boundary(marks_a, marks_b, order_count: int, guard: Guard, why: str,
                   **kw) -> dict:
    """The pinned boundary equations, reserved before they are solved.

    ``solve_hulls`` performs ``5`` root solves per direction and ``2 *
    len(marks)`` directions, so the cost is known before the call and the
    allowance is taken first. Charging afterwards would let an oversized batch
    finish and only then be refused.
    """
    from phrt.revision_v4_1.hulls import solve_hulls, SOLVES_PER_DIRECTION
    n = int(2 * np.asarray(marks_a).size * order_count)
    del SOLVES_PER_DIRECTION
    tok = guard.reserve(BOUNDARY, n, why)
    try:
        hs, st = solve_hulls(marks_a, marks_b, **kw)
    except BaseException as exc:
        guard.abort(tok, f"{type(exc).__name__}: {exc}")
        raise
    if st["solves"] != n:
        guard.abort(tok, f"expected {n} solves, the routine made "
                         f"{st['solves']}")
        raise GuardFailure(
            f"boundary cost model is wrong: reserved {n}, performed "
            f"{st['solves']}. The reservation must bound the call.")
    guard.complete(tok, st["solves"], st["failures"])
    return hs, st
