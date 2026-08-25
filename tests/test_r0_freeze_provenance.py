"""The R0 freeze must carry the provenance the activation ruling requires.

Nine fields, named separately rather than folded into one ambiguous "commit",
plus the frozen anchor and the anchored depth definition. These are cheap to
drop by accident during an edit and expensive to notice missing afterwards, so
they are pinned here.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
FREEZE = ROOT / "artifacts" / "configs" / "R0_CANARY_RECONSTRUCTION_PILOT_FREEZE.json"
E3C_FREEZE = ROOT / "artifacts" / "configs" / "E3C_OPERATOR_GRID_FREEZE.json"

REQUIRED = ("accepted_base_commit", "measurement_correction_commit",
            "e3c_execution_code_commit", "e3c_artifact_commit",
            "e3c_age_interval_amendment_commit", "e3c_freeze_sha256",
            "e3c_registry_sha256", "ray_map_manifest_sha256",
            "r0_config_sha256")

PINNED_BY_RULING = {
    "e3c_execution_code_commit": "546763ed29e2be3fb129ec707cb07ee37a4f7db8",
    "e3c_artifact_commit": "7d610121adc95fb641ab5692d37d2b761b082039",
    "e3c_freeze_sha256": ("7ab28bcd14674fb6544b577f19c00301f09e45ffec805cfcc"
                          "29896c53634bf1b"),
    "e3c_registry_sha256": ("2ba66f0209fe1cdec97b8cf5862494c22fb94704318f9601a"
                            "7a1f9eb4b783796"),
}


@pytest.fixture(scope="module")
def freeze() -> dict:
    if not FREEZE.exists():
        pytest.skip("R0 freeze not registered")
    return json.loads(FREEZE.read_text())


def test_all_nine_provenance_fields_are_present(freeze):
    prov = freeze["provenance"]
    for field in REQUIRED:
        assert field in prov, f"the R0 freeze does not record {field}"


def test_the_ruling_pinned_values_are_the_ones_recorded(freeze):
    prov = freeze["provenance"]
    for field, want in PINNED_BY_RULING.items():
        assert prov[field] == want, f"{field} is {prov[field]}, ruling pins {want}"


def test_execution_and_artifact_commits_are_distinguished(freeze):
    """One ambiguous commit field is exactly what the ruling forbids."""
    prov = freeze["provenance"]
    assert prov["e3c_execution_code_commit"] != prov["e3c_artifact_commit"]


def test_the_e3c_freeze_on_disk_is_the_pinned_one(freeze):
    if not E3C_FREEZE.exists():
        pytest.skip("E3C freeze absent")
    got = hashlib.sha256(E3C_FREEZE.read_bytes()).hexdigest()
    assert got == freeze["provenance"]["e3c_freeze_sha256"]


def test_the_ray_map_manifest_digest_is_over_the_recorded_digests(freeze):
    want = hashlib.sha256(json.dumps(
        freeze["physical_model"]["raymap_sha256"], sort_keys=True,
        separators=(",", ":")).encode()).hexdigest()
    assert freeze["provenance"]["ray_map_manifest_sha256"] == want


def test_the_self_digest_is_over_the_document_with_the_field_nulled(freeze):
    doc = json.loads(json.dumps(freeze))
    recorded = doc["provenance"]["r0_config_sha256"]
    doc["provenance"]["r0_config_sha256"] = None
    want = hashlib.sha256(json.dumps(doc, sort_keys=True,
                                     separators=(",", ":")).encode()).hexdigest()
    assert recorded == want


def test_the_anchor_is_frozen_and_the_anchored_depth_is_defined(freeze):
    m = freeze["metrics"]
    assert m["age_interval_amendment"] == "AGE_INTERVAL_SEMANTICS_AMENDMENT_003"
    assert isinstance(m["a_anchor_M"], (int, float))
    assert m["primary_point"] == "T_stable_anchor(epsilon=0.50, q=0.90)"
    assert "inside" in m["T_stable_anchor"], (
        "the definition must say the supremum over the age window is inside the "
        "probability, which is what distinguishes it from thresholding the "
        "per-age passing fraction")
    assert "must not be called depth from the present" in \
        m["secondary_unanchored_interval"]


def test_the_e3d_reserved_names_are_withheld_not_quietly_dropped(freeze):
    w = freeze["metrics"]["withheld_from_the_launch_list"]
    assert set(w["fields"]) == {"D_hist(T)", "d_eff(T)"}
    assert "E3D" in w["reason"]
    blob = json.dumps(freeze["metrics"]["also_reported"])
    for reserved in ("D_hist", "d_eff", "effective_rank"):
        assert reserved not in blob


def test_every_template_leaf_maps_to_a_filled_value(freeze):
    tpl_path = ROOT / freeze["template"]
    if not tpl_path.exists():
        pytest.skip("launch template not vendored")
    tpl = json.loads(tpl_path.read_text())
    mapping = freeze["template_conformance"]

    def leaves(node, prefix=""):
        if isinstance(node, dict) and node:
            for k, v in node.items():
                yield from leaves(v, f"{prefix}.{k}" if prefix else k)
        else:
            yield prefix

    def dig(path):
        cur = freeze
        for part in path.split("."):
            if not isinstance(cur, dict) or part not in cur:
                return None, False
            cur = cur[part]
        return cur, True

    for path in leaves(tpl):
        target = next((mapping[".".join(path.split(".")[:d])]
                       for d in range(path.count(".") + 1, 0, -1)
                       if ".".join(path.split(".")[:d]) in mapping), None)
        assert target is not None, f"{path} is not mapped"
        value, present = dig(target)
        assert present, f"{path} -> {target} is missing"
        assert value is not None, f"{path} -> {target} is still null"
        if isinstance(value, str):
            assert not value.upper().startswith("FILL"), \
                f"{path} -> {target} still carries a FILL marker"
