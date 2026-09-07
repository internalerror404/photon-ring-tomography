"""Fault injections in the launch and report path. Ruling 032.

Each test drives the gate the production runner will call, not a helper: the
031 failures were all failures of that path, so a check that lives beside it
would not have caught them. No physical query is made here.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from phrt.revision_v4_1 import leaf as LF                       # noqa: E402
from phrt.revision_v4_1 import plan032 as PL                    # noqa: E402


def good_plan(charge: int = 100, remaining: int = 12928) -> dict:
    tasks, evals = [], []
    for p, n, lev in PL.ENDPOINTS:
        eid = f"{p}:{n}:{lev}"
        evals.append({"id": eid, "charge": charge})
        tasks.append({"profile": p, "order": n, "level": lev,
                      "physical_domain_id": f"region_order{n}",
                      "representation_id": LF.LEAF_RULE,
                      "field_set_id": "transfer_fields_v1",
                      "detector_id": "D026", "clock_id": "T_REF_absolute",
                      "sigma_id": "sigma_D026", "payload_export": True,
                      "evaluation_ids": [eid]})
    return {"scope": "local_feasibility", "tasks": tasks, "evaluations": evals,
            "reconciled_remaining": remaining, "validation_reserve": 4000,
            "accounting_scope_resolved": True,
            "prerequisite_status": "SUPPORTED_FOR_DECLARED_SCOPE"}


def caps(remaining: int = 12928, points: int = 192, evals: int = 20000):
    return PL.Caps(points_max=points, evaluations_max=evals,
                   reconciled_remaining=remaining, validation_reserve=4000)


PREREQ = {"comparator_reference_resolved_or_scoped": True,
          "leaf_kernel_conservation_verified": True,
          "payload_export_implemented": True}


def test_baseline_complete_plan_is_authorized():
    PL.LaunchGate(good_plan(), caps()).authorize(192, PREREQ)


# ---- F1: 193 points under a 192-point cap ----
def test_F1_point_cap_is_enforced_not_merely_recorded():
    """031 recorded points_cap=192 and ran 494 points."""
    g = PL.LaunchGate(good_plan(), caps())
    with pytest.raises(PL.LaunchRefused, match="does not satisfy the point cap"):
        g.authorize(193, PREREQ)


def test_F1b_meeting_the_evaluation_cap_does_not_excuse_the_point_cap():
    g = PL.LaunchGate(good_plan(), caps(points=192, evals=20000))
    with pytest.raises(PL.LaunchRefused):
        g.authorize(494, PREREQ)          # 494 < 1024 evaluations, still refused


# ---- F2: an unresolved reference prerequisite blocks the launch ----
def test_F2_unresolved_reference_prerequisite_blocks_launch():
    p = good_plan()
    p["prerequisite_status"] = "REFERENCE_UNRESOLVED"
    with pytest.raises(PL.LaunchRefused, match="PREREQUISITE_NOT_READY"):
        PL.LaunchGate(p, caps()).authorize(192, PREREQ)


def test_F2b_a_prerequisite_recorded_false_blocks_launch():
    bad = dict(PREREQ, comparator_reference_resolved_or_scoped=False)
    with pytest.raises(PL.LaunchRefused, match="not a pass"):
        PL.LaunchGate(good_plan(), caps()).authorize(192, bad)


# ---- F3: a missing fine or order-2 endpoint ----
@pytest.mark.parametrize("drop", [("fine", 0, "L0"), ("core", 2, "L1"),
                                  ("fine", 2, "L2")])
def test_F3_missing_endpoint_is_refused_before_any_query(drop):
    p = good_plan()
    p["tasks"] = [t for t in p["tasks"]
                  if (t["profile"], t["order"], t["level"]) != drop]
    with pytest.raises(PL.LaunchRefused,
                       match="INCOMPLETE_OR_DUPLICATED_COMPARISON_MATRIX"):
        PL.LaunchGate(p, caps()).authorize(192, PREREQ)


def test_F3b_an_unreached_endpoint_reports_NOT_EVALUATED_not_zero():
    g = PL.LaunchGate(good_plan(), caps())
    res = {k: dict(counts=dict.fromkeys(LF.COUNT_FIELDS, 0), areas={},
                   representation_id=LF.LEAF_RULE,
                   field_set_id="transfer_fields_v1", payload="chunk.npz")
           for k in PL.ENDPOINTS if not (k[0] == "fine" and k[1] == 2)}
    out = g.report(res)
    assert out["comparison_status"] == "BUNDLE_INCOMPLETE_NO_CONVERGENCE_CLAIM"
    assert out["fine/2/L0"]["status"] == PL.NOT_EVALUATED
    assert "counts" not in out["fine/2/L0"]


# ---- F4: a constant occupancy column offered as full transfer ----
def test_F4_occupancy_only_field_set_is_refused_in_the_plan():
    p = good_plan()
    for t in p["tasks"]:
        t["field_set_id"] = PL.OCCUPANCY_ONLY
    with pytest.raises(PL.LaunchRefused,
                       match="OCCUPANCY_ONLY_FIELD_SET_CANNOT_QUALIFY_TRANSFER"):
        PL.LaunchGate(p, caps()).authorize(192, PREREQ)


def test_F4b_occupancy_only_result_may_not_claim_full_transfer():
    g = PL.LaunchGate(good_plan(), caps())
    res = {k: dict(counts=dict.fromkeys(LF.COUNT_FIELDS, 0), areas={},
                   representation_id=LF.LEAF_RULE,
                   field_set_id=PL.OCCUPANCY_ONLY, claims_full_transfer=True,
                   payload="chunk.npz") for k in PL.ENDPOINTS}
    with pytest.raises(PL.ReportRefused, match="validated transfer response"):
        g.report(res)


# ---- F5: equal norms, different detector vectors ----
def test_F5_norm_difference_hides_a_completely_different_image():
    y1 = np.array([[1.0], [0.0]])
    y2 = np.array([[0.0], [1.0]])
    assert PL.norm_difference(y1, y2) == pytest.approx(0.0)
    assert PL.vector_residual(y1, y2) == pytest.approx(np.sqrt(2.0))


def test_F5b_mismatched_detectors_cannot_be_compared():
    with pytest.raises(PL.ReportRefused, match="matched comparisons"):
        PL.vector_residual(np.zeros((4, 1)), np.zeros((5, 1)))


# ---- F6: parent-fraction assembly reaching the actual consumer ----
def test_F6_parent_fraction_representation_is_refused_in_the_plan():
    p = good_plan()
    p["tasks"][7]["representation_id"] = LF.PARENT_FRACTION
    with pytest.raises(PL.LaunchRefused, match="PARENT_FRACTION|NON_LEAF"):
        PL.LaunchGate(p, caps()).authorize(192, PREREQ)


def test_F6b_parent_fraction_result_is_refused_in_the_report():
    g = PL.LaunchGate(good_plan(), caps())
    res = {k: dict(counts=dict.fromkeys(LF.COUNT_FIELDS, 0), areas={},
                   representation_id=LF.PARENT_FRACTION, payload="chunk.npz")
           for k in PL.ENDPOINTS}
    with pytest.raises(PL.ReportRefused, match="occupancy proxy is not a consumer"):
        g.report(res)


# ---- F7: a missing numerical payload ----
def test_F7_missing_payload_export_is_refused_in_the_plan():
    p = good_plan()
    p["tasks"][0]["payload_export"] = False
    with pytest.raises(PL.LaunchRefused, match="PAYLOAD_NOT_PLANNED"):
        PL.LaunchGate(p, caps()).authorize(192, PREREQ)


def test_F7b_a_summary_without_values_is_refused_in_the_report():
    g = PL.LaunchGate(good_plan(), caps())
    res = {k: dict(counts=dict.fromkeys(LF.COUNT_FIELDS, 0), areas={},
                   representation_id=LF.LEAF_RULE, payload=None)
           for k in PL.ENDPOINTS}
    with pytest.raises(PL.ReportRefused, match="not a reusable result"):
        g.report(res)


def test_F7c_a_missing_count_field_is_refused():
    g = PL.LaunchGate(good_plan(), caps())
    counts = dict.fromkeys(LF.COUNT_FIELDS, 0)
    counts.pop("omitted")
    res = {k: dict(counts=counts, areas={}, representation_id=LF.LEAF_RULE,
                   payload="chunk.npz") for k in PL.ENDPOINTS}
    with pytest.raises(PL.ReportRefused, match="seven different numbers"):
        g.report(res)


# ---- F8: an infeasible bundle, and invasion of the validation reserve ----
def test_F8_infeasible_complete_bundle_refuses_to_start():
    p = good_plan(charge=600, remaining=6434)      # 18 * 600 + 4000 > 6434
    with pytest.raises(PL.LaunchRefused,
                       match="PLAN_PLUS_VALIDATION_EXCEEDS_RECONCILED_BUDGET"):
        PL.LaunchGate(p, caps(remaining=6434)).authorize(192, PREREQ)


def test_F8b_reserving_bundles_stops_before_the_validation_reserve():
    g = PL.LaunchGate(good_plan(charge=100), caps(remaining=6434))
    g.authorize(192, PREREQ)
    for key in PL.ENDPOINTS:
        g.reserve_bundle(*key, charge=100)
    with pytest.raises(PL.LaunchRefused, match="rather than dropping an endpoint"):
        g.reserve_bundle("core", 0, "L0", charge=2500)


def test_F8c_the_031_greedy_traversal_cannot_reproduce_itself():
    """Spending the whole cap on core n0 and n1 leaves the bundle unfunded."""
    g = PL.LaunchGate(good_plan(charge=100), caps(remaining=10000))
    g.authorize(192, PREREQ)
    g.reserve_bundle("core", 0, "L0", charge=1324)
    g.reserve_bundle("core", 1, "L0", charge=4676)
    with pytest.raises(PL.LaunchRefused):
        g.reserve_bundle("core", 2, "L0", charge=4000)


# ---- F9: a missing prerequisite record, and unauthenticated cache bytes ----
def test_F9_accounting_scope_must_be_resolved():
    p = good_plan()
    p["accounting_scope_resolved"] = False
    with pytest.raises(PL.LaunchRefused, match="ACCOUNTING_SCOPE_UNRESOLVED"):
        PL.LaunchGate(p, caps()).authorize(192, PREREQ)


def test_F9b_a_declared_cache_must_exist_and_hash(tmp_path):
    p = good_plan()
    blob = tmp_path / "chunk.npz"
    blob.write_bytes(b"values")
    h = hashlib.sha256(blob.read_bytes()).hexdigest()
    p["evaluations"][0] = {"id": p["evaluations"][0]["id"], "charge": 0,
                           "cache_sha256": h, "cache_path": "chunk.npz"}
    PL.LaunchGate(p, caps(), cache_root=tmp_path).authorize(192, PREREQ)

    p["evaluations"][0]["cache_sha256"] = "0" * 64
    with pytest.raises(PL.LaunchRefused, match="reuse is refused"):
        PL.LaunchGate(p, caps(), cache_root=tmp_path).authorize(192, PREREQ)


def test_F9c_a_cache_that_does_not_exist_is_refused(tmp_path):
    p = good_plan()
    p["evaluations"][0] = {"id": p["evaluations"][0]["id"], "charge": 0,
                           "cache_sha256": "a" * 64, "cache_path": "absent.npz"}
    with pytest.raises(PL.LaunchRefused, match="values\\s+cannot|does not exist"):
        PL.LaunchGate(p, caps(), cache_root=tmp_path).authorize(192, PREREQ)


def test_F9d_a_task_without_its_evaluation_is_refused():
    p = good_plan()
    p["tasks"][3]["evaluation_ids"] = ["not-an-evaluation"]
    with pytest.raises(PL.LaunchRefused,
                       match="TASK_MISSING_EVALUATION_DEPENDENCY"):
        PL.LaunchGate(p, caps()).authorize(192, PREREQ)


def test_F9e_unmatched_identifiers_within_an_order_are_refused():
    p = good_plan()
    p["tasks"][0]["clock_id"] = "recentred_per_profile"
    with pytest.raises(PL.LaunchRefused, match="UNMATCHED_CLOCK_ID"):
        PL.LaunchGate(p, caps()).authorize(192, PREREQ)


def test_F9g_an_empty_refinement_endpoint_is_not_a_free_endpoint():
    """A region with no transition parents refines nothing; zero is not a saving."""
    p = good_plan()
    p["evaluations"][4] = {"id": p["evaluations"][4]["id"], "charge": 0,
                           "leaf_factor": 2, "transition_parents": 0,
                           "cache_sha256": "b" * 64, "cache_path": "x.h5"}
    assert "DEGENERATE_ENDPOINT_NOTHING_TO_REFINE" in PL.validate_plan(p)


def test_F9f_a_complete_funded_bundle_reports_complete():
    g = PL.LaunchGate(good_plan(charge=100), caps())
    g.authorize(192, PREREQ)
    res = {k: dict(counts=dict.fromkeys(LF.COUNT_FIELDS, 1), areas={},
                   representation_id=LF.LEAF_RULE,
                   field_set_id="transfer_fields_v1", payload="chunk.npz")
           for k in PL.ENDPOINTS}
    assert g.report(res)["comparison_status"] == "BUNDLE_COMPLETE"
