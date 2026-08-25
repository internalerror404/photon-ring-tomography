"""Governance invariants for the v1 manuscript record and the v2 E3C contract.

The v1 manuscript was built against the v1 canonical freeze. E3C is being
re-executed under PAPER_I_V2_PRE_E3C_AMENDMENT_001, which changes the E3C tables
in place, so v1 is verified against its own snapshot in artifacts/v1_line rather
than against the live tree. Checking it against live paths would either fail for
the wrong reason or, worse, silently start passing against v2 numbers.
"""
from __future__ import annotations

import hashlib
import json

import pandas as pd
import pytest

from phrt.audits.e3c_contract import DISPOSITIONS, RESERVED_FOR_E3D
from phrt.config import repo_root

ROOT = repo_root()
V1 = ROOT / "artifacts" / "v1_line"
V1_SNAP = V1 / "V1_LINE_SNAPSHOT.json"
V1_LEDGER = V1 / "manuscript_v1" / "CLAIM_LEDGER.json"
V1_MAN = V1 / "manuscript_v1" / "PAPER_I.md"
SUPS = ROOT / "artifacts" / "SUPERSEDED_PRE_G10Q.json"
TABLES = ROOT / "artifacts" / "tables"

v1_only = pytest.mark.skipif(not V1_LEDGER.exists(),
                             reason="the v1 snapshot is not present")


def _ledger() -> dict:
    return json.loads(V1_LEDGER.read_text())


# ---------------------------------------------------------------- v1 record
@v1_only
def test_v1_snapshot_is_self_consistent():
    """The v1 line stays verifiable after the live E3C tables move."""
    doc = json.loads(V1_SNAP.read_text())
    for rel, want in doc["files"].items():
        p = ROOT / rel
        assert p.exists(), f"{rel} is missing from the v1 snapshot"
        assert hashlib.sha256(p.read_bytes()).hexdigest() == want, \
            f"{rel} has changed since the v1 snapshot was taken"


@v1_only
def test_v1_claims_appear_in_the_v1_manuscript():
    text = V1_MAN.read_text()
    for cl in _ledger()["claims"]:
        assert cl["rendered"] in text, f"{cl['id']} is registered but unused"


@v1_only
def test_v1_claim_ids_are_unique():
    ids = [c["id"] for c in _ledger()["claims"]]
    assert len(ids) == len(set(ids))


@v1_only
def test_v1_every_claim_names_its_provenance():
    for cl in _ledger()["claims"]:
        src = cl["source"]
        assert src.get("kind")
        if src["kind"] in ("parquet", "parquet_count", "json"):
            assert src.get("path") and src.get("sha256")
        elif src["kind"] == "derived":
            assert src.get("inputs") and src.get("expression")
        elif src["kind"] == "literal":
            assert src.get("source")


@v1_only
def test_v1_derived_claims_reference_registered_inputs():
    doc = _ledger()
    ids = {c["id"] for c in doc["claims"]}
    for cl in doc["claims"]:
        if cl["source"]["kind"] == "derived":
            for i in cl["source"]["inputs"]:
                assert i in ids, f"{cl['id']} derives from unregistered {i}"


def test_supersession_record_covers_every_listed_artifact():
    doc = json.loads(SUPS.read_text())
    allowed = {"SUPERSEDED_MEASUREMENT_MODEL_DEFECT",
               "PRESERVED_MEASUREMENT_MODEL_INDEPENDENT"}
    for a in doc["artifacts"]:
        assert a["disposition"] in allowed
    assert doc["counts"]["superseded"] + doc["counts"]["preserved_model_independent"] \
        == len(doc["artifacts"])


def test_readme_superseded_count_matches_the_record():
    import re
    n = json.loads(SUPS.read_text())["counts"]["superseded"]
    m = re.search(r"(\d+) pre-correction artifacts are",
                  (ROOT / "README.md").read_text())
    assert m, "the README no longer states the superseded count"
    assert int(m.group(1)) == n


# ------------------------------------------------- v2 E3C contract (amendment)
# The amendment requires its own record and the final freeze to be committed
# before any non-canary geometry is evaluated, so there is a window in which the
# contract is registered but the tables are still v1. These tests skip in that
# window, named by the artifact whose appearance ends it, rather than failing
# for a reason that is not the contract's fault.
V2_MARKER = TABLES / "e3c_incremental_indirect_gram.parquet"
v2_only = pytest.mark.skipif(
    not V2_MARKER.exists(),
    reason="E3C has not been re-executed under the v2 contract yet "
           "(e3c_incremental_indirect_gram.parquet absent)")


def _e3c_tables() -> list:
    return sorted(TABLES.glob("e3c_*.parquet"))


@v2_only
def test_v2_no_e3c_table_carries_a_reserved_e3d_name():
    """Item 6. D_hist and d_eff belong to E3D; effective_rank is d_eff."""
    for p in _e3c_tables():
        cols = set(pd.read_parquet(p).columns)
        assert not (cols & set(RESERVED_FOR_E3D)), \
            f"{p.name} carries {sorted(cols & set(RESERVED_FOR_E3D))}"


@v2_only
def test_v2_rank_reporting_tables_declare_exact_rank_not_applicable():
    """Item 5. A float64 physical operator has no exact rank to report."""
    for p in _e3c_tables():
        df = pd.read_parquet(p)
        if "numerical_rank" not in df.columns:
            continue
        assert "exact_rank" in df.columns, f"{p.name} reports a rank without exact_rank"
        assert set(df["exact_rank"].dropna().unique()) <= {"NOT_APPLICABLE"}


@v2_only
def test_v2_dispositions_are_registered_values():
    """Item 8."""
    for p in _e3c_tables():
        df = pd.read_parquet(p)
        if "disposition" not in df.columns:
            continue
        assert set(df["disposition"].dropna().unique()) <= set(DISPOSITIONS)


@v2_only
def test_v2_depth_table_carries_the_full_depth_contract():
    """Item 4, as amended by AGE_INTERVAL_SEMANTICS_AMENDMENT_003."""
    p = TABLES / "e3c_depth_curves.parquet"
    if not p.exists():
        pytest.skip("E3C depth table not built")
    cols = set(pd.read_parquet(p).columns)
    for c in ("oldest_detectable_age_probe", "a_anchor_M",
              "longest_detectable_run_span_M",
              "longest_detectable_run_start_M",
              "longest_detectable_run_end_M",
              "contiguous_detectable_end_from_anchor_M",
              "contiguous_detectable_span_from_anchor_M",
              "age_threshold_mask", "censor_boundary_M",
              "detectable_set_is_contiguous"):
        assert c in cols, f"the depth table is missing {c}"
    assert "T_rec" not in cols, "T_rec was renamed by amendment item 4"
    for retired in ("largest_contiguous_detectable_depth",
                    "largest_contiguous_start_M", "largest_contiguous_end_M"):
        assert retired not in cols, (
            f"{retired} was retired by AGE_INTERVAL_SEMANTICS_AMENDMENT_003 "
            "because a span length is not a depth from the present")


def test_v2_freeze_records_the_amendment_and_notation():
    """Items 3 and 9."""
    fz = json.loads((ROOT / "artifacts" / "configs"
                     / "E3C_OPERATOR_GRID_FREEZE.json").read_text())
    assert fz["amendment"] == "PAPER_I_V2_PRE_E3C_AMENDMENT_001"
    assert fz["operator_notation"]["restricted_coefficient_matrix"] == \
        "A_C = mathcal A Q_C"
    assert set(fz["reserved_for_e3d"]) >= {"D_hist", "d_eff"}
    assert fz["accepted_base_commit"].startswith("0ef341d")


def test_v2_amendment_record_exists_and_flags_its_interpretations():
    doc = json.loads((ROOT / "artifacts" / "configs"
                      / "PAPER_I_V2_PRE_E3C_AMENDMENT_001.json").read_text())
    assert doc["item_1_base_commit"]["action"] == "PRESERVED"
    # the reading of item 1 as preserve-not-revert is a judgement call and must
    # stay visible as one
    assert doc["item_1_base_commit"]["flagged_for_reviewer"] is True
