"""Governance invariants for the manuscript, enforced as tests.

These are cheap and they guard the properties that are easy to break silently:
the manuscript must cite only canonical artifacts, every number must be in the
ledger, and the supersession record must partition what it covers.
"""
from __future__ import annotations

import json

import pytest

from phrt.config import repo_root, sha256_file

ROOT = repo_root()
LEDGER = ROOT / "artifacts" / "manuscript" / "CLAIM_LEDGER.json"
CANON = ROOT / "artifacts" / "CANONICAL_ARTIFACT_FREEZE.json"
SUPS = ROOT / "artifacts" / "SUPERSEDED_PRE_G10Q.json"
MAN = ROOT / "artifacts" / "manuscript" / "PAPER_I.md"

pytestmark = pytest.mark.skipif(not LEDGER.exists(),
                                reason="manuscript has not been built")


def _ledger() -> dict:
    return json.loads(LEDGER.read_text())


def test_every_cited_artifact_is_canonical():
    fz = json.loads(CANON.read_text())["artifacts"]
    for p in _ledger()["artifacts_cited"]:
        assert p in fz, f"{p} is cited but not canonical"


def test_no_claim_cites_pre_correction_bytes():
    """Supersession attaches to bytes, not paths: the check is that no cited
    file currently hashes to its pre-correction digest."""
    fz = json.loads(CANON.read_text())["artifacts"]
    pre = {a["path"]: a["sha256_pre_correction"]
           for a in json.loads(SUPS.read_text())["artifacts"]
           if a["disposition"] == "SUPERSEDED_MEASUREMENT_MODEL_DEFECT"
           and a["sha256_pre_correction"]}
    for p in _ledger()["artifacts_cited"]:
        if p in pre:
            assert fz[p] != pre[p], f"{p} is cited at its superseded bytes"


def test_every_claim_appears_in_the_manuscript():
    text = MAN.read_text()
    for cl in _ledger()["claims"]:
        assert cl["rendered"] in text, f"{cl['id']} is registered but unused"


def test_claim_ids_are_unique():
    ids = [c["id"] for c in _ledger()["claims"]]
    assert len(ids) == len(set(ids))


def test_every_claim_names_its_provenance():
    for cl in _ledger()["claims"]:
        src = cl["source"]
        assert src.get("kind")
        if src["kind"] in ("parquet", "parquet_count", "json"):
            assert src.get("path") and src.get("sha256")
        elif src["kind"] == "derived":
            assert src.get("inputs") and src.get("expression")
        elif src["kind"] == "literal":
            assert src.get("source")


def test_derived_claims_reference_registered_inputs():
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


def test_canonical_freeze_matches_disk():
    fz = json.loads(CANON.read_text())["artifacts"]
    # spot-check the tables the manuscript actually cites rather than all 265,
    # which the verifier does; this keeps the test suite fast
    for p in _ledger()["artifacts_cited"]:
        assert sha256_file(ROOT / p) == fz[p], f"{p} has changed since the freeze"


def test_manuscript_states_the_three_governance_counts():
    text = MAN.read_text()
    for k in ("active blocking failures", "preserved literal failures",
              "future-phase not run"):
        assert k in text


def test_readme_superseded_count_matches_the_record():
    """The README states the count in prose; this catches it drifting."""
    import re
    n = json.loads(SUPS.read_text())["counts"]["superseded"]
    text = (ROOT / "README.md").read_text()
    m = re.search(r"(\d+) pre-correction artifacts are", text)
    assert m, "the README no longer states the superseded count"
    assert int(m.group(1)) == n


def test_freeze_pins_the_campaign_tag_not_head():
    fz = json.loads(CANON.read_text())
    assert fz["campaign_commit_source"].startswith("git tag"), \
        "the freeze fell back to HEAD; the campaign tag is missing"
