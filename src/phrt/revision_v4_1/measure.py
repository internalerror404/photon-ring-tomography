"""The geometric measure of a ray map, separated from its stored weight.

C13. `build_raymaps.py` stores `pixel_area = dx**2`, the pitch AART was asked
for. AART does not use that pitch. `lensingbands.grid_mask` builds

    x = np.linspace(-lims, lims, round_up_to_even(2 * lims / dx))

so the samples are endpoint-inclusive *nodes* on a declared finite square
domain, and the realized spacing is ``2 * lims / (N - 1)``, which equals ``dx``
only when the division happens to come out even. The two descriptions cannot
both be the same uniform pixel partition, and the archived weight is the one
that does not match the coordinates.

Three conventions are named here and none is silently preferred:

``LEGACY_NOMINAL_SQUARE``
    a square of side ``sqrt(pixel_area)`` centred on each node. What the
    archive asserts and what R3A's first construction used. Its cells do not
    tile: against the realized node spacing they leave gaps, or overlap.

``NODAL_DUAL_CLIPPED``
    the dual cell of each node, clipped to the declared domain. Interior nodes
    get a full cell, edge nodes a half-width one and corners a quarter. These
    tile ``[-lims, lims]^2`` exactly, with no gap and no overlap, and their
    total is the declared domain area by construction. Cells are rectangular
    and of unequal area, which is the point: a single scalar cannot express
    this and ``delta_alpha ** 2`` is not the repair.

``CENTER_CELL_EXTENDED``
    a full cell for every node, which is only legitimate when the enlarged
    domain ``[-lims - d/2, lims + d/2]^2`` is explicitly the intended one. It
    is provided so that choice can be measured rather than assumed.

Nothing here rewrites an archive. A corrected measure is a sidecar; the stored
weight stays exactly as it was recorded, under its own name.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

LEGACY_NOMINAL_SQUARE = "LEGACY_NOMINAL_DX_SQUARED_SQUARE"
NODAL_DUAL_CLIPPED = "NODAL_DUAL_CLIPPED_TO_DECLARED_DOMAIN"
CENTER_CELL_EXTENDED = "FULL_CENTER_CELL_ON_EXTENDED_DOMAIN"
CONVENTIONS = (LEGACY_NOMINAL_SQUARE, NODAL_DUAL_CLIPPED, CENTER_CELL_EXTENDED)

UNIFORMITY_ATOL = 1e-9      # M, on a screen measured in tens of M


class MeasureError(RuntimeError):
    """A map whose geometry does not support any declared convention."""


@dataclass(frozen=True)
class AxisMeasure:
    """One screen axis: its nodes, the domain they declare, and their cells.

    Both axes are described separately and never inferred from each other.
    They agree in every archived map here, but that is a fact to be measured
    on each map rather than a property to assume: a rectangular grid would
    make a single `delta` silently wrong in one direction.
    """

    nodes: np.ndarray
    domain_lo: float
    domain_hi: float
    spacing: float
    max_spacing_deviation: float
    lo: np.ndarray                 # per-node cell lower edge
    hi: np.ndarray                 # per-node cell upper edge
    convention: str

    @property
    def widths(self) -> np.ndarray:
        return self.hi - self.lo

    @property
    def covered(self) -> float:
        return float(self.widths.sum())

    def to_dict(self) -> dict:
        w = self.widths
        return {"convention": self.convention, "n_nodes": int(self.nodes.size),
                "node_min": float(self.nodes[0]),
                "node_max": float(self.nodes[-1]),
                "declared_domain": [self.domain_lo, self.domain_hi],
                "realized_spacing": self.spacing,
                "max_spacing_deviation": self.max_spacing_deviation,
                "cell_width_min": float(w.min()),
                "cell_width_max": float(w.max()),
                "distinct_cell_widths": int(np.unique(np.round(w, 12)).size),
                "total_covered_length": self.covered,
                "covers_declared_domain_exactly":
                    bool(abs(self.covered - (self.domain_hi - self.domain_lo))
                         < 1e-9)}


def axis_nodes(values: np.ndarray) -> tuple[np.ndarray, dict]:
    """The distinct node coordinates of one axis, with its regularity audit."""
    nodes = np.unique(values)
    if nodes.size < 2:
        raise MeasureError("an axis needs at least two nodes to have a pitch")
    d = np.diff(nodes)
    audit = {"n_nodes": int(nodes.size), "n_samples": int(values.size),
             "min_spacing": float(d.min()), "max_spacing": float(d.max()),
             "mean_spacing": float(d.mean()),
             "max_spacing_deviation": float(np.abs(d - d.mean()).max()),
             "uniform": bool(np.abs(d - d.mean()).max() < UNIFORMITY_ATOL),
             "strictly_ascending": bool(np.all(d > 0)),
             "duplicate_nodes": int(values.size - np.unique(values).size
                                    - (values.size - nodes.size))}
    return nodes, audit


def axis_measure(values: np.ndarray, convention: str,
                 nominal_side: float | None = None) -> AxisMeasure:
    """Cell edges for one axis under one named convention."""
    nodes, audit = axis_nodes(values)
    if not audit["uniform"]:
        raise MeasureError(
            f"axis spacing is not uniform to {UNIFORMITY_ATOL}: "
            f"{audit['max_spacing_deviation']:.3e}. No convention here "
            "describes a non-uniform axis, and guessing one would be the "
            "same class of error C13 records.")
    d = float(audit["mean_spacing"])
    lo_d, hi_d = float(nodes[0]), float(nodes[-1])
    if convention == NODAL_DUAL_CLIPPED:
        lo = np.maximum(nodes - d / 2.0, lo_d)
        hi = np.minimum(nodes + d / 2.0, hi_d)
        dom = (lo_d, hi_d)
    elif convention == CENTER_CELL_EXTENDED:
        lo, hi = nodes - d / 2.0, nodes + d / 2.0
        dom = (lo_d - d / 2.0, hi_d + d / 2.0)
    elif convention == LEGACY_NOMINAL_SQUARE:
        if nominal_side is None:
            raise MeasureError("the legacy convention needs its stored side")
        h = 0.5 * nominal_side
        lo, hi = nodes - h, nodes + h
        dom = (lo_d - h, hi_d + h)
    else:
        raise MeasureError(f"unknown convention {convention!r}")
    return AxisMeasure(nodes, dom[0], dom[1], d,
                       float(audit["max_spacing_deviation"]), lo, hi,
                       convention)


@dataclass(frozen=True)
class RayCells:
    """Per-ray rectangular cells: four edges, never one scalar area."""

    alpha_lo: np.ndarray
    alpha_hi: np.ndarray
    beta_lo: np.ndarray
    beta_hi: np.ndarray
    axis_alpha: AxisMeasure
    axis_beta: AxisMeasure
    convention: str

    @property
    def area(self) -> np.ndarray:
        return (self.alpha_hi - self.alpha_lo) * (self.beta_hi - self.beta_lo)

    def tiles_exactly(self, tol: float = 1e-9) -> bool:
        """Do the cells of every node partition the declared domain?"""
        want = ((self.axis_alpha.domain_hi - self.axis_alpha.domain_lo)
                * (self.axis_beta.domain_hi - self.axis_beta.domain_lo))
        return bool(abs(float(self.area.sum()) - want) < tol * max(1.0, want))


def build_ray_cells(alpha: np.ndarray, beta: np.ndarray, convention: str,
                    nominal_side: float | None = None) -> RayCells:
    """Cells for every ray of a tensor-product screen grid.

    The node index of each ray is recovered by exact lookup rather than by
    assuming a raster order, and a ray whose coordinate is not a node is an
    error rather than a nearest match.
    """
    ax = axis_measure(alpha, convention, nominal_side)
    bx = axis_measure(beta, convention, nominal_side)
    ia = np.searchsorted(ax.nodes, alpha)
    ib = np.searchsorted(bx.nodes, beta)
    if (ia >= ax.nodes.size).any() or (ib >= bx.nodes.size).any() or \
            not np.array_equal(ax.nodes[ia], alpha) or \
            not np.array_equal(bx.nodes[ib], beta):
        raise MeasureError("a ray coordinate is not one of the axis nodes; "
                           "this screen is not the tensor product it claims")
    return RayCells(ax.lo[ia], ax.hi[ia], bx.lo[ib], bx.hi[ib], ax, bx,
                    convention)
