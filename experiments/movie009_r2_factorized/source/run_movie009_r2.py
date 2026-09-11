from __future__ import annotations

"""Launcher for the pre-outcome Movie009-R2 V4 source freeze.

Decode the V2 implementation, apply the registered V3 population-builder patch
and V4 joint/resume patch, verify the final executable SHA256, and run those
exact bytes.
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
PATCHES = [HERE / "population_builder_v3.patch", HERE / "joint_resume_v4.patch"]
EXPECTED_SOURCE_SHA256 = "39cfbcf12c1918eb86a1ef842714fa900bb3204ed0078e692d243740ce4cadff"
if not ENCODED.exists():
    raise FileNotFoundError(ENCODED)
for patch_path in PATCHES:
    if not patch_path.exists():
        raise FileNotFoundError(patch_path)
with tempfile.TemporaryDirectory(prefix="movie009_r2_v4_") as tmp:
    tmp_path = Path(tmp)
    archive = tmp_path / "Movie009_R2_Source_V2.tar.xz"
    archive.write_bytes(base64.b64decode(ENCODED.read_text()))
    with tarfile.open(archive, "r:xz") as tf:
        tf.extractall(tmp_path, filter="data")
    for patch_path in PATCHES:
        subprocess.run(
            ["patch", "-p1", "--batch", "--forward", "-i", str(patch_path)],
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
