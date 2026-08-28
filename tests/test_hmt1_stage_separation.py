"""Stage A owns the source gates, and stage B cannot jump the queue.

Items 10 and 11 of ruling 017.
"""
import ast
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "scripts" / "run_hmt1_main.py"
BANK = ROOT / "scripts" / "run_hmt1_main_bank.py"
FZ = ROOT / "artifacts" / "configs" / "HMT1_SEALED_HELD_OUT_MAIN_FREEZE_V2.json"

OPERATOR_MODULES = {
    "phrt.operators.physical", "phrt.geometry.raymap", "phrt.geometry.sampling",
    "phrt.sources.localized_basis", "phrt.sources.physical_basis",
    "phrt.inverse.background",
}


def _module_level_imports(path):
    tree = ast.parse(path.read_text())
    out = set()
    for node in tree.body:                       # module level only
        if isinstance(node, ast.Import):
            out.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            out.add(node.module)
    return out


def test_stage_b_does_not_import_an_operator_at_module_level():
    """The ordering must be a property of the file, not a habit.

    If these imports sit at module level, importing the runner touches an
    operator before any source gate has been read, and the guarantee is only
    as good as whoever remembers to check first.
    """
    leaked = _module_level_imports(MAIN) & OPERATOR_MODULES
    assert not leaked, leaked


def test_stage_a_never_imports_an_operator_at_all():
    """Stage A must be unable to evaluate one even by accident."""
    tree = ast.parse(BANK.read_text())
    seen = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            seen.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            seen.add(node.module)
    assert not seen & OPERATOR_MODULES, seen & OPERATOR_MODULES


def test_stage_b_refuses_without_a_clean_stage_a(tmp_path):
    """A failed source gate must stop the run before the operator loads."""
    gates = ROOT / "artifacts" / "gates" / "hmt1_main_stage_a_gates.json"
    if not gates.exists():
        pytest.skip("stage A has not been run in this tree")
    saved = gates.read_text()
    doc = json.loads(saved)
    doc["failed_gates"] = ["HMT1M_G5_total_emissivity_nonnegative"]
    doc["stage_b_may_proceed"] = False
    try:
        gates.write_text(json.dumps(doc))
        p = subprocess.run([sys.executable, str(MAIN)], capture_output=True,
                           text=True, cwd=str(ROOT), timeout=300)
        assert p.returncode != 0
        assert "stage A source gates failed" in p.stderr
    finally:
        gates.write_text(saved)


def test_the_freeze_declares_which_gates_belong_to_stage_a():
    fz = json.loads(FZ.read_text())
    stage_a = set(fz["gate_stages"]["stage_a"])
    declared = set(fz["gates"])
    assert stage_a <= declared, stage_a - declared
    # the source-side checks that must not wait for an operator
    for g in ("HMT1M_G4_contrast_zero_spatial_mean",
              "HMT1M_G5_total_emissivity_nonnegative",
              "HMT1M_G10c_truth_extraction_matches_independent_windowed_reference"):
        assert g in stage_a, g


def test_the_retired_gate_is_not_declared_for_execution():
    fz = json.loads(FZ.read_text())
    assert "HMT1M_G10b_truth_extraction_recovers_generative_parameters" \
        not in fz["gates"]
    assert "HMT1M_G10b_truth_extraction_recovers_generative_parameters" \
        in fz["retired_gate"]


def test_retired_bank_seeds_are_recorded_so_they_cannot_be_redrawn():
    fz = json.loads(FZ.read_text())
    assert set(fz["retired_bank_seeds"]) == {20260915, 20260917}
    assert fz["seeds"]["bank_seed"] not in fz["retired_bank_seeds"]


def test_estimator_scope_is_recorded():
    fz = json.loads(FZ.read_text())
    d = fz["design"]
    assert d["estimators_authorized"] == ["TSVD", "RIDGE_IDENTITY"]
    assert d["estimators_withdrawn"]["NONNEGATIVE_CONSTRAINED"] == \
        "WITHDRAWN_UNSELECTED"
    assert d["estimators_not_authorized"]["ML"] == "NOT_AUTHORIZED"
    assert "HMT1M_G19_estimator_scope" in fz["gates"]
