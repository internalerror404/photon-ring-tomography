from __future__ import annotations
import base64,hashlib,runpy,tarfile,tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
ENC=HERE/"Movie009_R3_Source_V2.tar.xz.b64"
EXPECTED="5e64828af3767a371ee859cf95299d90820970b5fe667408a9c3b3957ed7dac9"
with tempfile.TemporaryDirectory(prefix="movie009_r3_v2_") as tmp:
    tmp=Path(tmp); a=tmp/"source.tar.xz"; a.write_bytes(base64.b64decode(ENC.read_text()))
    with tarfile.open(a,"r:xz") as tf: tf.extractall(tmp,filter="data")
    s=tmp/"run_movie009_r3.py"; got=hashlib.sha256(s.read_bytes()).hexdigest()
    if got!=EXPECTED: raise RuntimeError(f"source hash mismatch {got} != {EXPECTED}")
    runpy.run_path(str(s),run_name="__main__")
