from __future__ import annotations
import base64, hashlib, runpy, tarfile, tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
ENC=HERE/"Movie009_R3_Source.tar.xz.b64"
EXPECTED="8861e1bb80991237b0cf32cfc96e4d490d55eb4d3cbf4c282ec09d3bbd3d4916"
with tempfile.TemporaryDirectory(prefix="movie009_r3_") as tmp:
    tmp=Path(tmp); arc=tmp/"source.tar.xz"; arc.write_bytes(base64.b64decode(ENC.read_text()))
    with tarfile.open(arc,"r:xz") as tf: tf.extractall(tmp,filter="data")
    src=tmp/"run_movie009_r3.py"
    got=hashlib.sha256(src.read_bytes()).hexdigest()
    if got!=EXPECTED: raise RuntimeError(f"source hash mismatch {got} != {EXPECTED}")
    runpy.run_path(str(src),run_name="__main__")
