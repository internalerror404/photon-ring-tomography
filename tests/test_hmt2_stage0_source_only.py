"""Item 8: stage 0 imports no ray map and constructs no operator.

Checked by reading the file and by running the guard, not by trusting that
nobody adds an import later.
"""
import ast
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "scripts" / "run_hmt2_stage0_audit.py"
FZ = ROOT / "artifacts" / "configs" / "HMT2_STAGE0_SOURCE_OBJECT_AND_RESOLUTION_AUDIT_V0.json"

FORBIDDEN = {
    "phrt.operators.physical", "phrt.operators",
    "phrt.geometry.raymap", "phrt.geometry.sampling",
}


def _all_imports(path):
    seen = set()
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.Import):
            seen.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            seen.add(node.module)
    return seen


def test_the_audit_imports_no_operator_anywhere():
    """Not at module level and not inside a function either."""
    bad = _all_imports(AUDIT) & FORBIDDEN
    assert not bad, bad


def test_the_audit_carries_its_own_runtime_guard():
    """A source file can be edited; the guard fires at run time."""
    src = AUDIT.read_text()
    assert "_assert_source_only" in src
    assert "FORBIDDEN" in src


def test_the_guard_actually_detects_an_operator_import():
    import importlib
    import sys
    spec = importlib.util.spec_from_file_location("_hmt2_audit_guard", AUDIT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod._assert_source_only() is True
    importlib.import_module("phrt.operators.physical")
    with pytest.raises(SystemExit):
        mod._assert_source_only()
    sys.modules.pop("phrt.operators.physical", None)
    sys.modules.pop("phrt.operators", None)


def test_the_freeze_declares_the_prohibition():
    fz = json.loads(FZ.read_text())
    p = fz["prohibitions"]
    assert "not imported" in p["ray_map"]
    assert "not constructed" in p["observation_operator"]
    assert "not imposed" in p["separation_cut"]


def test_the_freeze_declares_the_three_nested_grids():
    fz = json.loads(FZ.read_text())
    got = [(g["n_radial"], g["n_azimuthal"], g["n_temporal"])
           for g in fz["grids"]["nested"]]
    assert got == [(16, 32, 40), (32, 64, 80), (64, 128, 160)]


def test_the_freeze_declares_both_source_classes_with_the_right_dimensions():
    fz = json.loads(FZ.read_text())
    a = fz["source_classes"]["L448_contrast"]
    b = fz["source_classes"]["L896_radial_enriched"]
    assert (a["dimension_before_m0_removal"], a["dimension_after"]) == (448, 384)
    assert (b["dimension_before_m0_removal"], b["dimension_after"]) == (896, 768)
    assert b["radial"] == 2 * a["radial"]
    assert (b["azimuthal"], b["temporal"]) == (a["azimuthal"], a["temporal"])


def test_the_freeze_introduces_no_new_tuned_constant():
    """Both thresholds reuse the campaign's declared birth fraction."""
    from phrt.metrics.features import BIRTH_FRACTION
    fz = json.loads(FZ.read_text())
    c = fz["classification"]
    assert c["prominence_fraction"] == BIRTH_FRACTION
    assert c["dead_fraction"] == BIRTH_FRACTION


def test_the_canary_is_declared_excluded_from_aggregates():
    fz = json.loads(FZ.read_text())
    assert "aggregate" in fz["canary"]["excluded_from"]
    assert fz["canary"]["role"].startswith("named regression")
