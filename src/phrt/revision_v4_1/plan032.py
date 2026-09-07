"""The launch and report gate for a matched integration campaign. Ruling 032.

The 031 pilot did not fail because a check reported the wrong answer. It failed
because nothing stood between an incomplete comparison and a run: the point cap
was recorded and never enforced, the traversal order decided the allocation, an
unreached arm was printed beside evaluated ones, and the report metric was a
difference of norms. Every one of those is a property of the launch and report
path, so the guards live here, on that path, and the tests drive them through
it rather than through a helper.

Two refusals are structural. A bundle is atomic: either every endpoint of a
(profile, order, level) comparison is funded and run, or the campaign does not
start. And an endpoint that was not reached is reported as NOT_EVALUATED --
never as a zero error, a zero unresolved area, or a baseline observation.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from phrt.revision_v4_1.leaf import COUNT_FIELDS, LEAF_RULE, PARENT_FRACTION

PROFILES = ("core", "fine")
ORDERS = (0, 1, 2)
LEVELS = ("L0", "L1", "L2")
ENDPOINTS = tuple((p, n, lev) for p in PROFILES for n in ORDERS
                  for lev in LEVELS)
MATCHED_IDS = ("physical_domain_id", "representation_id", "field_set_id",
               "detector_id", "clock_id", "sigma_id")
SCOPES = ("local_feasibility", "full_domain_qualification")
NOT_EVALUATED = "NOT_EVALUATED"
VALIDATION_RESERVE_MIN = 4000

# a response claimed to validate the transfer operator must carry more than a
# constant occupancy column; chi multiplies the full transferred source
OCCUPANCY_ONLY = "constant_occupancy_f_equals_one"


class LaunchRefused(RuntimeError):
    """A campaign that would repeat a 031 failure is not started."""


class ReportRefused(RuntimeError):
    """A result that would overstate what was measured is not written."""


@dataclass
class Caps:
    points_max: int
    evaluations_max: int
    reconciled_remaining: int
    validation_reserve: int = VALIDATION_RESERVE_MIN


def _endpoint(task) -> tuple:
    return (task.get("profile"), task.get("order"), task.get("level"))


def validate_plan(plan: dict) -> list[str]:
    """Schema and cost errors, in the same terms as the reviewer's preflight.

    This duplicates the delivered ``checks_and_preflight_032.py`` deliberately:
    that script validates a manifest offline, this one runs inside the process
    that would spend the budget. A plan that passes the reviewer's schema check
    still has to pass here, with the real caches and the real counters.
    """
    errors: list[str] = []
    tasks = plan.get("tasks", [])
    observed = [_endpoint(t) for t in tasks]
    if set(observed) != set(ENDPOINTS) or len(observed) != len(ENDPOINTS):
        errors.append("INCOMPLETE_OR_DUPLICATED_COMPARISON_MATRIX")
    if plan.get("scope") not in SCOPES:
        errors.append("UNDECLARED_SCIENTIFIC_SCOPE")
    for n in ORDERS:
        subset = [t for t in tasks if t.get("order") == n]
        for key in MATCHED_IDS:
            vals = {t.get(key) for t in subset}
            if not vals or None in vals or len(vals) != 1:
                errors.append(f"ORDER_{n}_UNMATCHED_{key.upper()}")
        if any(t.get("payload_export") is not True for t in subset):
            errors.append(f"ORDER_{n}_PAYLOAD_NOT_PLANNED")
    for t in tasks:
        if t.get("representation_id") not in (LEAF_RULE, None):
            errors.append("NON_LEAF_REPRESENTATION_DECLARED")
        if t.get("representation_id") == PARENT_FRACTION:
            errors.append("PARENT_FRACTION_REPRESENTATION_DECLARED")
        if t.get("field_set_id") == OCCUPANCY_ONLY:
            errors.append("OCCUPANCY_ONLY_FIELD_SET_CANNOT_QUALIFY_TRANSFER")
    by_id, cost = {}, 0
    for ev in plan.get("evaluations", []):
        eid = ev.get("id")
        if not isinstance(eid, str) or eid in by_id:
            errors.append("DUPLICATED_OR_MISSING_EVALUATION_ID")
            continue
        by_id[eid] = ev
        if ev.get("cache_sha256") is not None:
            if not re.fullmatch("[0-9a-f]{64}", str(ev["cache_sha256"])):
                errors.append("INVALID_CACHE_HASH_FORMAT")
            if ev.get("charge") != 0:
                errors.append("CACHE_COST_INCONSISTENT")
        else:
            q = ev.get("charge")
            if not isinstance(q, int) or isinstance(q, bool) or q < 1:
                errors.append("UNDECLARED_NEW_EVALUATION_COST")
            else:
                cost += q
        # A refining level with no transition parents in the declared region
        # measures nothing there. Costing it at zero would turn an empty
        # comparison into a satisfied endpoint, which is the 031 failure in a
        # new place, so it is an error rather than a saving.
        if ev.get("leaf_factor", 1) > 1 and ev.get("transition_parents") == 0:
            errors.append("DEGENERATE_ENDPOINT_NOTHING_TO_REFINE")
    for t in tasks:
        ids = t.get("evaluation_ids", [])
        if not ids or any(eid not in by_id for eid in ids):
            errors.append("TASK_MISSING_EVALUATION_DEPENDENCY")
    rem = plan.get("reconciled_remaining")
    reserve = plan.get("validation_reserve")
    if not isinstance(rem, int) or not isinstance(reserve, int) \
            or reserve < VALIDATION_RESERVE_MIN:
        errors.append("INVALID_REMAINING_OR_VALIDATION_RESERVE")
    elif cost + reserve > rem:
        errors.append("PLAN_PLUS_VALIDATION_EXCEEDS_RECONCILED_BUDGET")
    if plan.get("accounting_scope_resolved") is not True:
        errors.append("ACCOUNTING_SCOPE_UNRESOLVED")
    if plan.get("prerequisite_status") != "SUPPORTED_FOR_DECLARED_SCOPE":
        errors.append("PREREQUISITE_NOT_READY")
    return sorted(set(errors))


def declared_cost(plan: dict) -> int:
    return sum(int(ev.get("charge", 0)) for ev in plan.get("evaluations", [])
               if ev.get("cache_sha256") is None)


class LaunchGate:
    """Everything that must hold before the first new physical call."""

    def __init__(self, plan: dict, caps: Caps,
                 cache_root: Path | None = None) -> None:
        self.plan, self.caps = plan, caps
        self.cache_root = Path(cache_root) if cache_root else None
        self.reserved: dict[tuple, int] = {}

    # -- launch ---------------------------------------------------------
    def authorize(self, points_requested: int,
                  prerequisites: dict) -> None:
        errors = validate_plan(self.plan)
        if errors:
            raise LaunchRefused("plan invalid: " + ", ".join(errors))
        if points_requested > self.caps.points_max:
            raise LaunchRefused(
                f"{points_requested} points requested against a cap of "
                f"{self.caps.points_max}: meeting a separate evaluation cap "
                "does not satisfy the point cap")
        cost = declared_cost(self.plan)
        if cost > self.caps.evaluations_max:
            raise LaunchRefused(
                f"declared charge {cost} exceeds the evaluation cap "
                f"{self.caps.evaluations_max}")
        if cost + self.caps.validation_reserve > self.caps.reconciled_remaining:
            raise LaunchRefused(
                f"declared charge {cost} plus the {self.caps.validation_reserve}"
                " response-validation reserve exceeds the reconciled remaining "
                f"{self.caps.reconciled_remaining}: an infeasible complete "
                "bundle must refuse to start, not run its cheap arms")
        missing = [k for k, v in prerequisites.items() if v is not True]
        if missing:
            raise LaunchRefused(
                "unmet scientific prerequisites " + repr(sorted(missing))
                + ": an unresolved primary-reference comparison is not a pass")
        self._verify_caches()

    def _verify_caches(self) -> None:
        for ev in self.plan.get("evaluations", []):
            h = ev.get("cache_sha256")
            if h is None:
                continue
            path = ev.get("cache_path")
            if not path:
                raise LaunchRefused(
                    f"evaluation {ev.get('id')!r} claims a cache with no path;"
                    " a hash in a plan does not authenticate any bytes")
            if self.cache_root is None:
                raise LaunchRefused("a cached evaluation was declared but no "
                                    "cache root was supplied to the gate")
            f = self.cache_root / path
            if not f.is_file():
                raise LaunchRefused(f"declared cache {path!r} does not exist; "
                                    "coordinates can be regenerated, values "
                                    "cannot")
            got = hashlib.sha256(f.read_bytes()).hexdigest()
            if got != h:
                raise LaunchRefused(
                    f"cache {path!r} hashes {got[:12]}..., plan declares "
                    f"{str(h)[:12]}...: reuse is refused")

    # -- bundles --------------------------------------------------------
    def reserve_bundle(self, profile: str, order: int, level: str,
                       charge: int) -> None:
        """A comparison is funded whole or not at all."""
        key = (profile, order, level)
        if key not in ENDPOINTS:
            raise LaunchRefused(f"{key} is not a declared endpoint")
        spent = sum(self.reserved.values())
        if spent + charge + self.caps.validation_reserve \
                > self.caps.reconciled_remaining:
            raise LaunchRefused(
                f"reserving {charge} for {key} would leave less than the "
                f"{self.caps.validation_reserve} validation reserve; the "
                "campaign stops rather than dropping an endpoint")
        self.reserved[key] = self.reserved.get(key, 0) + charge

    # -- report ---------------------------------------------------------
    def report(self, results: dict) -> dict:
        """Assemble the campaign record, refusing every 031-style overstatement."""
        out, missing = {}, []
        for key in ENDPOINTS:
            r = results.get(key)
            if r is None:
                missing.append(key)
                out["/".join(map(str, key))] = {"status": NOT_EVALUATED}
                continue
            for f in COUNT_FIELDS:
                if f not in r.get("counts", {}):
                    raise ReportRefused(
                        f"{key}: count {f!r} absent; found, eligible, "
                        "selected, evaluated, cached, omitted and unresolved "
                        "are seven different numbers")
            if r.get("representation_id") != LEAF_RULE:
                raise ReportRefused(
                    f"{key}: assembled under {r.get('representation_id')!r}; "
                    "the parent-averaged occupancy proxy is not a consumer")
            if r.get("field_set_id") == OCCUPANCY_ONLY \
                    and r.get("claims_full_transfer"):
                raise ReportRefused(
                    f"{key}: a constant occupancy column is offered as a "
                    "validated transfer response")
            if r.get("payload") is None:
                raise ReportRefused(
                    f"{key}: no numerical payload; a summary without the "
                    "evaluated values is not a reusable result")
            out["/".join(map(str, key))] = {"status": "EVALUATED", **{
                k: r[k] for k in ("counts", "areas") if k in r}}
        if missing:
            out["incomplete"] = ["/".join(map(str, k)) for k in missing]
            out["comparison_status"] = "BUNDLE_INCOMPLETE_NO_CONVERGENCE_CLAIM"
        else:
            out["comparison_status"] = "BUNDLE_COMPLETE"
        return out


def vector_residual(y_fine: np.ndarray, y_core: np.ndarray) -> float:
    """norm(y_fine - y_core) / norm(y_fine), never a difference of norms.

    Two images with the same norm can disagree in every pixel, so the norm
    difference is not a bound on the disagreement and must not be reported as
    a convergence metric.
    """
    y_fine = np.asarray(y_fine, float)
    y_core = np.asarray(y_core, float)
    if y_fine.shape != y_core.shape:
        raise ReportRefused(
            f"cannot compare a {y_fine.shape} response with a {y_core.shape} "
            "one: matched comparisons share the detector, not just its size")
    d = float(np.linalg.norm(y_fine - y_core))
    return d / max(float(np.linalg.norm(y_fine)), 1e-300)


def norm_difference(y_fine: np.ndarray, y_core: np.ndarray) -> float:
    """The 031 metric, kept only so a test can show it hides disagreement."""
    a, b = np.linalg.norm(y_fine), np.linalg.norm(y_core)
    return float(abs(a - b) / max(a, 1e-300))


def load_plan(path: Path) -> dict:
    return json.loads(Path(path).read_text())
