#!/usr/bin/env python3
"""Phase A: freeze every byte the replay will read, before it runs.

The R1 freeze omitted the R2 runner and the target manifest, which is the gap
review 024 requires closing. This one covers the runner, every module it
imports from the revision namespace, the tests, the registered configuration,
the ray maps and the target manifest, plus the interpreter and library
versions the numbers depend on.
"""
from __future__ import annotations

import json
import platform
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from phrt.revision_v4_1.guards import sha256  # noqa: E402

REV = ROOT / "artifacts" / "revisions" / "mahakal_v4_1"
OUT = REV / "R2_REPLAY_INPUT_FREEZE.json"
GEOMETRY = "a050_i050"


def main() -> int:
    files: list[str] = []
    files += sorted(str(p.relative_to(ROOT)) for p in
                    (ROOT / "src" / "phrt" / "revision_v4_1").glob("*.py"))
    files += sorted(str(p.relative_to(ROOT)) for p in
                    (ROOT / "scripts" / "revision_v4_1").glob("*.py"))
    files += sorted(str(p.relative_to(ROOT)) for p in
                    (ROOT / "tests" / "revision_v4_1").glob("*.py"))
    # the archived modules the replay imports: the operator, the sampler, the
    # bases and the reader are as much an input as the runner is
    files += ["src/phrt/operators/physical.py",
              "src/phrt/geometry/sampling.py",
              "src/phrt/geometry/raymap.py",
              "src/phrt/sources/localized_basis.py",
              "src/phrt/sources/physical_basis.py",
              "src/phrt/numerics.py",
              "artifacts/configs/R1_MAIN_FREEZE.json",
              str((REV / "R2_REPLAY_TARGET_MANIFEST.json").relative_to(ROOT)),
              str((REV / "R2_CLOSEOUT_RECORD_024.json").relative_to(ROOT)),
              "docs/revisions/mahakal_v4_1/R2_CLOSEOUT_024.yaml"]
    files += sorted(str(p.relative_to(ROOT)) for p in
                    (ROOT / "artifacts" / "raymaps").glob(f"{GEOMETRY}_n*_core.h5"))
    files = sorted(set(f for f in files if (ROOT / f).exists()))

    doc = {
        "schema": "phrt-input-freeze/1",
        "id": "R2_REPLAY_INPUT_FREEZE",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "purpose": "the complete pre-execution snapshot the R1 freeze lacked",
        "closes": "review 024 issue A",
        "n_files": len(files),
        "environment": {
            "python": platform.python_version(),
            "numpy": __import__("numpy").__version__,
            "scipy": __import__("scipy").__version__,
            "platform": platform.platform(),
            "threading": "phrt.numerics.pin, single-threaded",
        },
        "commit_at_freeze_time": subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True,
            text=True).stdout.strip(),
        "files": {f: sha256(ROOT / f) for f in files},
    }
    OUT.write_text(json.dumps(doc, indent=2) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}  ({len(files)} inputs)")
    print(f"  includes the R2 runner: "
          f"{any('r2b_replay' in f for f in files)}")
    print(f"  includes the target manifest: "
          f"{any('TARGET_MANIFEST' in f for f in files)}")
    print(f"  includes the ray maps: "
          f"{sum(1 for f in files if f.endswith('.h5'))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
