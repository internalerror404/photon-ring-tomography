from __future__ import annotations

"""Launcher for the hash-frozen Movie009-R2 implementation.

The complete executable source is deposited beside this file as
Movie009_R2_Source.tar.xz.  This launcher extracts that archive into a temporary
directory and executes the exact run_movie009_r2.py contained in it.
"""

import runpy
import tarfile
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ARCHIVE = HERE / "Movie009_R2_Source.tar.xz"
if not ARCHIVE.exists():
    raise FileNotFoundError(ARCHIVE)
with tempfile.TemporaryDirectory(prefix="movie009_r2_") as tmp:
    with tarfile.open(ARCHIVE, "r:xz") as tf:
        tf.extractall(tmp, filter="data")
    runpy.run_path(str(Path(tmp) / "run_movie009_r2.py"), run_name="__main__")
