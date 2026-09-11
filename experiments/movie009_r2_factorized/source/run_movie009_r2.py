from __future__ import annotations

"""Launcher for the pre-outcome Movie009-R2 V3 source freeze.

Decode the V2 implementation, apply the registered deterministic population-
builder patch, verify the resulting executable SHA256, and run those exact bytes.
"""

import base64
import hashlib
import runpy
import subprocess
import tarfile
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENCODED = HERE / "Movie009_R2_Source_V2.tar.xz.b64"
PATCH = HERE / "population_builder_v3.patch"
EXPECTED_SOURCE_SHA256 = "4e4f3a54bb24dc9d6aab8db1ca270063b6a550643d6966c69f6913e33355b50f"
if not ENCODED.exists():
    raise FileNotFoundError(ENCODED)
if not PATCH.exists():
    raise FileNotFoundError(PATCH)
with tempfile.TemporaryDirectory(prefix="movie009_r2_v3_") as tmp:
    tmp_path = Path(tmp)
    archive = tmp_path / "Movie009_R2_Source_V2.tar.xz"
    archive.write_bytes(base64.b64decode(ENCODED.read_text()))
    with tarfile.open(archive, "r:xz") as tf:
        tf.extractall(tmp_path, filter="data")
    subprocess.run(
        ["patch", "-p1", "--batch", "--forward", "-i", str(PATCH)],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )
    source = tmp_path / "run_movie009_r2.py"
    observed = hashlib.sha256(source.read_bytes()).hexdigest()
    if observed != EXPECTED_SOURCE_SHA256:
        raise RuntimeError(f"patched source hash mismatch: {observed} != {EXPECTED_SOURCE_SHA256}")
    runpy.run_path(str(source), run_name="__main__")
