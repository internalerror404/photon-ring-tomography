from __future__ import annotations

"""Launcher for the pre-outcome Movie009-R2 V2 source freeze.

The complete corrected executable source is stored beside this file as a base64
encoding of an xz-compressed tar archive.  Decoding is deterministic; the source
and decoded archive hashes are recorded in SOURCE_FREEZE_V2.json.
"""

import base64
import runpy
import tarfile
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENCODED = HERE / "Movie009_R2_Source_V2.tar.xz.b64"
if not ENCODED.exists():
    raise FileNotFoundError(ENCODED)
with tempfile.TemporaryDirectory(prefix="movie009_r2_v2_") as tmp:
    tmp_path = Path(tmp)
    archive = tmp_path / "Movie009_R2_Source_V2.tar.xz"
    archive.write_bytes(base64.b64decode(ENCODED.read_text()))
    with tarfile.open(archive, "r:xz") as tf:
        tf.extractall(tmp_path, filter="data")
    runpy.run_path(str(tmp_path / "run_movie009_r2.py"), run_name="__main__")
