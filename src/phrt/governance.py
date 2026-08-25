"""Provenance every R0 result manifest must carry.

The activation ruling requires nine fields, recorded separately rather than
folded into one ambiguous ``commit``: in particular the commit whose code ran
E3C and the commit whose tree holds E3C's outputs are different things and are
named differently. They are read from the registered R0 freeze rather than
duplicated in code, so a manifest cannot disagree with the freeze it was run
under, and the freeze's own digest travels with them.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
R0_FREEZE = ROOT / "artifacts" / "configs" / "R0_CANARY_RECONSTRUCTION_PILOT_FREEZE.json"

REQUIRED_FIELDS = ("accepted_base_commit", "measurement_correction_commit",
                   "e3c_execution_code_commit", "e3c_artifact_commit",
                   "e3c_age_interval_amendment_commit", "e3c_freeze_sha256",
                   "e3c_registry_sha256", "ray_map_manifest_sha256",
                   "r0_config_sha256")


def r0_provenance(freeze_path: Path | None = None) -> dict:
    """The nine fields, plus the digest of the freeze file they came from."""
    path = Path(freeze_path or R0_FREEZE)
    fz = json.loads(path.read_text())
    prov = fz["provenance"]
    missing = [f for f in REQUIRED_FIELDS if f not in prov]
    if missing:
        raise ValueError(f"{path.name} does not record {missing}")
    out = {f: prov[f] for f in REQUIRED_FIELDS}
    out["r0_freeze_file_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    out["a_anchor_M"] = fz["metrics"]["a_anchor_M"]
    out["age_interval_amendment"] = fz["metrics"]["age_interval_amendment"]
    return out
