"""A runtime guard that a stage touched no operator.

HMT-2 stage 0, item 8. The audit is a statement about sources, and it is only
worth anything if nothing observational leaked into it. Reading the file proves
no import is written there; this proves none arrived by any other route before
the work began.

It reads ``sys.modules``, so it means what it says in a process whose only
imports are the stage's own -- which is how the audit runs. Inside a shared
interpreter it would fire on somebody else's import, correctly but uselessly,
so the test that exercises it controls ``sys.modules`` explicitly.

It lives here rather than inside the audit script so it can be imported and
tested without executing a script that pins the numerical environment.
"""
from __future__ import annotations

import sys

FORBIDDEN = ("phrt.operators", "phrt.geometry.raymap", "phrt.geometry.sampling")


def loaded_forbidden(prefixes: tuple[str, ...] = FORBIDDEN) -> list[str]:
    return sorted(m for m in sys.modules if m.startswith(prefixes))


def assert_source_only(prefixes: tuple[str, ...] = FORBIDDEN) -> bool:
    bad = loaded_forbidden(prefixes)
    if bad:
        raise SystemExit(
            f"source-only stage must import no operator or ray map: {bad}")
    return True
