"""R0_REPAIR_AMENDMENT_004: in-span membership, and attestation that attests.

The pilot's "in-class" bank was not in class and its clean-tree claim was
produced by a check that could only ever say clean. Both repairs are the kind
that look fine until someone measures them, so both are measured here.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import numpy as np
import pytest

from phrt.attestation import (REGISTERED_PATHSPECS, file_attestation,
                              working_tree_state)
from phrt.sources.in_span import (IN_SPAN_TOLERANCE, constant_coefficients,
                                  in_span_movie, in_span_residual,
                                  project_to_class)
from phrt.sources.movie import Movie

ROOT = Path(__file__).resolve().parents[1]


class _Basis:
    """A tiny separable basis with the property that matters: it holds a constant."""

    def __init__(self, n=6):
        self.n = n

    def design(self, r, phi, t):
        r = np.atleast_1d(np.asarray(r, float))
        cols = [np.ones_like(r)]
        for k in range(1, self.n):
            cols.append(np.cos(k * r))
        return np.stack(cols, axis=1)


@pytest.fixture(scope="module")
def toy():
    b = _Basis()
    grid = np.linspace(0.0, 3.0, 200)
    d = b.design(grid, grid, grid)
    c1, resid = constant_coefficients(d)
    return b, grid, d, c1, resid


def test_the_class_holds_a_constant_or_the_lift_is_invalid(toy):
    _, _, _, _, resid = toy
    assert resid < IN_SPAN_TOLERANCE


def test_a_projected_truth_is_in_span_off_the_projection_grid(toy):
    """The point of defining the truth as Q_C x rather than approximating it."""
    b, grid, d, c1, _ = toy
    parent = Movie("toy", {"seed": 1},
                   lambda r, p, t: 1.0 + np.exp(-((r - 1.5) / 0.05) ** 2))
    m = in_span_movie(parent, b, grid, grid, grid, c1)
    other = np.linspace(0.1, 2.9, 137)          # a different set of coordinates
    assert in_span_residual(m, b.design(other, other, other),
                            other, other, other) < IN_SPAN_TOLERANCE


def test_the_analytic_parent_is_not_in_span_which_is_why_this_matters(toy):
    b, grid, d, c1, _ = toy
    parent = Movie("toy", {"seed": 2},
                   lambda r, p, t: 1.0 + np.exp(-((r - 1.5) / 0.05) ** 2))
    assert in_span_residual(parent, d, grid, grid, grid) > 1e-3


def test_positivity_is_restored_without_leaving_the_span(toy):
    b, grid, d, c1, _ = toy
    values = np.cos(4.0 * grid) - 0.5          # goes well negative
    p = project_to_class(values, d, c1, min_intensity=1e-6)
    assert p["lift_applied"] > 0
    assert p["min_intensity"] >= 1e-6 - 1e-12
    assert np.linalg.norm(d @ p["coefficients"] - p["values"]) < 1e-10


def test_the_truth_records_its_distance_from_the_analytic_parent(toy):
    b, grid, d, c1, _ = toy
    parent = Movie("toy", {"seed": 3},
                   lambda r, p, t: 1.0 + np.exp(-((r - 1.5) / 0.05) ** 2))
    m = in_span_movie(parent, b, grid, grid, grid, c1)
    assert m.extra["distance_from_analytic_parent"] > 0
    assert m.extra["parent_content_hash"] == parent.content_hash
    assert m.content_hash != parent.content_hash, (
        "an in-span truth and its analytic parent are different truths and must "
        "not collide in the split disjointness check")


def test_the_pathspecs_describe_this_repository():
    """The defect behind the pilot's clean-tree claim, pinned.

    git status says nothing about a pathspec that matches nothing, so pathspecs
    from another layout produce a permanently clean answer.
    """
    for spec in REGISTERED_PATHSPECS:
        assert (ROOT / spec[2:]).exists(), (
            f"{spec} does not exist in this repository, so any status scoped to "
            "it is vacuous")


def test_working_tree_state_reports_evidence_not_a_verdict():
    st = working_tree_state()
    if not st.get("available"):
        pytest.skip("git unavailable")
    for key in ("porcelain_registered", "porcelain_registered_sha256",
                "n_tracked_changes", "n_untracked", "tracked_clean",
                "untracked_clean", "clean", "execution_commit",
                "head_tree_sha"):
        assert key in st
    lines = [ln for ln in st["porcelain_registered"].splitlines() if ln.strip()]
    assert len(lines) == st["n_tracked_changes"] + st["n_untracked"]
    assert st["clean"] == (not lines)


def test_a_modified_registered_file_is_visible_to_the_attestation(tmp_path):
    """A tracked file edited in place must stop being 'committed at HEAD'."""
    target = ROOT / "artifacts" / "configs" / "R0C_REPAIRED_SOURCE_AND_CALIBRATION_FREEZE.json"
    if not target.exists():
        pytest.skip("R0C freeze not registered")
    before = file_attestation(target)
    if not before["tracked"]:
        pytest.skip("freeze not committed yet")
    original = target.read_bytes()
    try:
        target.write_bytes(original + b"\n")
        after = file_attestation(target)
        assert after["sha256"] != before["sha256"]
        assert after["committed_at_execution_commit"] is False
    finally:
        target.write_bytes(original)
    assert file_attestation(target)["sha256"] == before["sha256"]
