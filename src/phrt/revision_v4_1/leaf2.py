"""Sign-aware response envelopes. Version 2; version 1 stays frozen.

Ruling 033. The 032 consumer placed an unresolved leaf's contribution in

    [known, known + sum w |f|],                                    WRONG

which is a bound only when the field is known to be nonnegative. The declared
suite is not: source coordinate time is measured against an absolute reference
and the inherited temporal test fields change sign. With overlap w = 0.25 and
field f = -2 under an uncertain indicator chi in [0, 1], the true contribution
lies in [-0.5, 0] and the old box gives [0, 0.5] -- disjoint from the truth.

For a fixed signed field value the contribution interval is

    [ w min(0, f),  w max(0, f) ],

for a magnitude envelope |f| <= M it is [-wM, +wM], and in general it is the
extreme of the four products of the endpoints of chi and of f. That last form
is what is implemented; the first two are its special cases, and they are
tested as such rather than short-circuited.

Two things this module refuses to do. It will not invent an envelope: a
non-finite bound is a blocker, never a zero, because "no bound" and "no
contribution" are different statements. And it will not treat a midpoint
sample as an envelope -- the value at one point of a leaf bounds the field over
that leaf only if something else says so, and that something else has to be
supplied.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from phrt.revision_v4_1.leaf import (COUNT_FIELDS, EMITTING,  # noqa: F401
                                     LEAF_RULE, NOT_EMITTING, PARENT_FRACTION,
                                     UNRESOLVED, LeafError)

BOUND_RULE = "SIGN_AWARE_ENDPOINT_PRODUCT_ENVELOPE_V2"

# how a leaf's field envelope was obtained; a sample is not an envelope
EXACT_VALUE = "EXACT_POINT_VALUE_ON_A_CONSTANT_FIELD"
VALIDATED_ENVELOPE = "VALIDATED_ENVELOPE_OVER_THE_LEAF"
MAGNITUDE_ENVELOPE = "VALIDATED_MAGNITUDE_BOUND_OVER_THE_LEAF"
SAMPLE_ONLY = "POINT_SAMPLE_WITH_NO_ENVELOPE"


class EnvelopeMissing(LeafError):
    """A contribution has no bound; it is not therefore zero."""


@dataclass
class Envelope:
    """Per-overlap intervals for the indicator and for each field channel."""

    chi_lo: np.ndarray            # (m,)
    chi_hi: np.ndarray            # (m,)
    field_lo: np.ndarray          # (m, n_field)
    field_hi: np.ndarray          # (m, n_field)
    provenance: str = SAMPLE_ONLY

    def validate(self) -> None:
        a = (self.chi_lo, self.chi_hi, self.field_lo, self.field_hi)
        if not all(np.isfinite(x).all() for x in a):
            raise EnvelopeMissing(
                "a non-finite bound entered the envelope: an unbounded "
                "contribution is a blocker, not a zero")
        if np.any(self.chi_lo < 0) or np.any(self.chi_hi > 1):
            raise LeafError("the indicator interval must lie in [0, 1]")
        if np.any(self.chi_lo > self.chi_hi) or np.any(
                self.field_lo > self.field_hi):
            raise LeafError("a reversed interval is not an interval")
        if self.provenance == SAMPLE_ONLY:
            raise EnvelopeMissing(
                "a point sample is not an envelope over its leaf; supply a "
                f"{VALIDATED_ENVELOPE} or {MAGNITUDE_ENVELOPE}, or declare "
                f"{EXACT_VALUE} for a field that is constant on the leaf")


def point_envelope(field: np.ndarray, label: np.ndarray,
                   provenance: str = EXACT_VALUE) -> Envelope:
    """Envelope for exactly known field values under a three-state label.

    ``EMITTING`` pins chi to 1, ``NOT_EMITTING`` to 0, and ``UNRESOLVED``
    leaves it in [0, 1] -- which, once the field is signed, is where the old
    construction went wrong.
    """
    field = np.asarray(field, float)
    if field.ndim == 1:
        field = field[:, None]
    label = np.asarray(label)
    lo = np.where(label == EMITTING, 1.0, 0.0)
    hi = np.where(label == NOT_EMITTING, 0.0, 1.0)
    return Envelope(lo, hi, field, field.copy(), provenance)


def magnitude_envelope(bound: np.ndarray, label: np.ndarray) -> Envelope:
    """Envelope when only |f| <= M is known over the leaf."""
    bound = np.asarray(bound, float)
    if bound.ndim == 1:
        bound = bound[:, None]
    if np.any(bound < 0):
        raise LeafError("a magnitude bound cannot be negative")
    label = np.asarray(label)
    lo = np.where(label == EMITTING, 1.0, 0.0)
    hi = np.where(label == NOT_EMITTING, 0.0, 1.0)
    return Envelope(lo, hi, -bound, bound, MAGNITUDE_ENVELOPE)


@dataclass
class BoundedAssembly:
    """A response with a genuine enclosure, not a one-sided pile."""

    lower: np.ndarray
    upper: np.ndarray
    nominal: np.ndarray | None = None
    counts: dict = field(default_factory=dict)
    provenance: str = ""
    rule: str = BOUND_RULE

    @property
    def width(self) -> np.ndarray:
        return self.upper - self.lower

    def encloses(self, y: np.ndarray, atol: float = 1e-12) -> bool:
        y = np.asarray(y, float)
        return bool(np.all(y >= self.lower - atol)
                    and np.all(y <= self.upper + atol))


def assemble_bounds(rows: np.ndarray, cols: np.ndarray, vals: np.ndarray,
                    env: Envelope, n_detector: int, *,
                    granularity: str) -> BoundedAssembly:
    """Enclose y_d = sum_l w_l chi_l f_l over the supplied intervals.

    The weights are areas and so are nonnegative; the extremes of a product
    of two intervals are attained at endpoint pairs, so the componentwise box
    is the min and max over the four products, accumulated per detector cell.
    It is a box, not a joint set: it does not encode the correlation between
    leaves that share a parent, and it is conservative in that direction.
    """
    if granularity != LEAF_RULE:
        raise LeafError(
            f"refusing assembly under {granularity!r}: the only supported "
            f"rule is {LEAF_RULE}; {PARENT_FRACTION} moves flux between "
            "detector cells")
    rows = np.asarray(rows, np.int64)
    cols = np.asarray(cols, np.int64)
    vals = np.asarray(vals, float)
    env.validate()
    if np.any(vals < 0):
        raise LeafError("an overlap area cannot be negative")
    m = rows.size
    if not (cols.size == m and vals.size == m):
        raise LeafError("rows, cols and vals must agree in length")
    if env.chi_lo.size != env.chi_hi.size:
        raise LeafError("the indicator interval is ragged")
    if env.field_lo.shape[0] != env.chi_lo.size:
        raise LeafError("one field row per cell is required")
    if m and int(cols.max()) >= env.chi_lo.size:
        raise LeafError(
            f"the overlap indexes {int(cols.max()) + 1} cells but only "
            f"{env.chi_lo.size} envelopes were supplied: the label "
            "granularity does not match the overlap granularity")

    cl = env.chi_lo[cols][:, None]
    ch = env.chi_hi[cols][:, None]
    fl = env.field_lo[cols]
    fh = env.field_hi[cols]
    prod = np.stack([cl * fl, cl * fh, ch * fl, ch * fh])
    w = vals[:, None]
    lo_terms = w * prod.min(axis=0)
    hi_terms = w * prod.max(axis=0)
    shape = (n_detector, env.field_lo.shape[1])
    lower = np.zeros(shape)
    upper = np.zeros(shape)
    np.add.at(lower, rows, lo_terms)
    np.add.at(upper, rows, hi_terms)
    return BoundedAssembly(lower, upper, provenance=env.provenance)


def bind(a: BoundedAssembly, counts: dict) -> BoundedAssembly:
    missing = [k for k in COUNT_FIELDS if k not in counts]
    if missing:
        raise LeafError(f"missing required counts {missing}: an unreached "
                        "endpoint is NOT_EVALUATED, not a zero observation")
    a.counts = dict(counts)
    return a


def envelope_response_bound(a: BoundedAssembly, whiten: float = 1.0) -> float:
    """The triangle-inequality bound ||W (y - y_hat)|| <= sum_l e_l.

    Reported as the half-width of the enclosure, which is what the local
    envelopes actually supply. It holds on the domain the envelopes cover and
    says nothing about anything outside it.
    """
    return float(np.linalg.norm(0.5 * a.width * whiten, ord=1))
