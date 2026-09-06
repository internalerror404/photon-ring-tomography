"""A completion token that has to be earned.

Review 024 issue C. The first R2 runner detected tolerance instability and
returned success anyway, and the report generator picked its token from
operational-count agreement alone. A reporting path that can emit the same
favourable token for a condition the protocol says must stop execution is not
a reporting path, it is a rubber stamp.

So the token is computed from the conditions rather than asserted beside them.
Every condition in ``REQUIRED`` must be explicitly satisfied; an absent
condition is a failure, not a default, because the failure mode being guarded
against is exactly a check that was never wired up.
"""
from __future__ import annotations

from dataclasses import dataclass, field

# The protocol's completion_requires list, verbatim in intent.
REQUIRED = (
    "prerequisite_test_success",
    "verified_input_and_target_hashes",
    "explicit_source_rank_and_nuisance_rank_decisions",
    "finite_numeric_outputs",
    "source_metric_promotion",
    "stable_nuisance_rank_and_operational_counts_across_registered_tolerances",
    "no_unresolved_blocker",
)

SUCCESS = "R2_REFERENCE_GEOMETRY_REPLAY_ACCEPTANCE_READY"
UNRESOLVED = "R2_NUMERICALLY_UNRESOLVED"
BLOCKED = "R1_BLOCKED"
EMPTY_TARGET = "R2_EMPTY_TARGET_NO_SUCCESS"

# Which failure maps to which non-success token. Anything unlisted is
# NUMERICALLY_UNRESOLVED rather than a pass.
_TOKEN_FOR = {
    "prerequisite_test_success": BLOCKED,
    "verified_input_and_target_hashes": BLOCKED,
    "no_unresolved_blocker": BLOCKED,
}


@dataclass
class Completion:
    """The conditions, their evidence, and the token they add up to."""

    conditions: dict[str, bool] = field(default_factory=dict)
    evidence: dict[str, str] = field(default_factory=dict)
    empty_target: bool = False

    def record(self, name: str, ok: bool, evidence: str) -> None:
        if name not in REQUIRED:
            raise KeyError(f"{name!r} is not a declared completion condition; "
                           f"expected one of {REQUIRED}")
        self.conditions[name] = bool(ok)
        self.evidence[name] = evidence

    def never_recorded_names(self) -> list[str]:
        return self.missing

    @property
    def missing(self) -> list[str]:
        """Conditions never recorded. Silence is a failure, not a pass."""
        return [c for c in REQUIRED if c not in self.conditions]

    @property
    def failed(self) -> list[str]:
        return [c for c in REQUIRED if self.conditions.get(c) is False]

    @property
    def token(self) -> str:
        if self.empty_target:
            return EMPTY_TARGET
        blocking = self.failed + self.missing
        if not blocking:
            return SUCCESS
        for c in blocking:
            if c in _TOKEN_FOR:
                return _TOKEN_FOR[c]
        return UNRESOLVED

    @property
    def ok(self) -> bool:
        return self.token == SUCCESS

    def to_dict(self) -> dict:
        return {
            "token": self.token,
            "success": self.ok,
            "conditions": {c: self.conditions.get(c) for c in REQUIRED},
            "evidence": dict(self.evidence),
            "failed": self.failed,
            "never_recorded": self.missing,
            "empty_target": self.empty_target,
            "rule": "every declared condition must be recorded true; an "
                    "unrecorded condition fails closed",
        }
