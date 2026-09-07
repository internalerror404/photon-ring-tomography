"""Leaf-correct assembly of the detector response. Ruling 032.

Ruling 027 rejected the substitution

    y_d  +=  |D_d ^ C_p ^ B_n| * chi_bar(C_p),                     FORBIDDEN

in which a parent cell's mean emitting fraction is spread uniformly over the
parent's whole overlap. I2 of ruling 031 reintroduced it: it evaluated four
sub-points inside a transition cell, averaged their labels, and multiplied the
average by the parent's overlap. Total flux survives that substitution and the
image does not -- a unit cell emitting only on its leftmost fifth, straddling
two half-width pixels, owes (0.2, 0) and the substitution pays (0.1, 0.1).

The rule implemented here keeps each child's own geometry:

    y_d  =  sum_p sum_(l in leaves(p)) |D_d ^ C_l ^ B_n| chi(xi_l) f(xi_l).

Three properties are asserted rather than assumed.

*Partition.* The leaves of a parent tile the parent exactly, so summing the
leaf overlaps over the leaves of every parent must reproduce the parent
overlap **per detector cell**, not merely in total. That per-row identity is
the check that distinguishes a refinement of the integration from a change of
the geometry, and it is verified on real band geometry, not only on fixtures.

*Approximation.* A midpoint indicator on a leaf is still a quadrature rule for
the physical indicator. Refining it changes the answer; it does not certify
it. Nothing here reconstructs an emission contour.

*Unresolved is not zero.* A leaf whose label could not be decided contributes
an unknown amount between zero and its full overlap. The response is therefore
returned as a triple (lower, known, upper) with the unresolved mass carried
explicitly. A boolean saying "there were no unresolved samples" is not a
statement about the boundary: four finite point labels inside a cell do not
exclude a small component or a tangency between them.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from phrt.revision_v4_1 import polyclip as PC
from phrt.revision_v4_1.common_sky import DetectorGrid
from phrt.revision_v4_1.measure import AxisMeasure, MeasureError, RayCells

LEAF_RULE = "LEAF_CLIPPED_MIDPOINT_INDICATOR_V1"
PARENT_FRACTION = "PARENT_AVERAGED_OCCUPANCY_PROXY"   # named to be refused

EMITTING, NOT_EMITTING, UNRESOLVED = 1, 0, -1

# every count the ruling requires a stage to keep separate
COUNT_FIELDS = ("found", "eligible", "selected", "evaluated", "cached",
                "omitted", "unresolved")


class LeafError(RuntimeError):
    """An assembly that would misplace flux or lose a count."""


@dataclass(frozen=True)
class LeafCells:
    """The k x k children of every parent cell, with tensor axes retained."""

    cells: RayCells
    parent: np.ndarray            # (n_leaf,) parent index of each leaf
    alpha: np.ndarray             # (n_leaf,) leaf midpoint
    beta: np.ndarray
    k: int

    @property
    def n_leaf(self) -> int:
        return int(self.parent.size)


def _refine_axis(axis: AxisMeasure, k: int) -> AxisMeasure:
    t = np.arange(k + 1) / k
    w = (axis.hi - axis.lo)[:, None]
    e = axis.lo[:, None] + w * t[None, :]
    lo, hi = e[:, :-1].reshape(-1), e[:, 1:].reshape(-1)
    return AxisMeasure(0.5 * (lo + hi), axis.domain_lo, axis.domain_hi,
                       axis.spacing / k, axis.max_spacing_deviation / k,
                       lo, hi, f"{axis.convention}_REFINED_x{k}")


def refine(cells: RayCells, k: int) -> LeafCells:
    """Split every parent into k x k children, keeping the tensor structure.

    The children of a tensor-product grid are again a tensor-product grid, so
    the exact overlap kernel of ruling 027 applies to them unchanged. Refining
    only the interesting parents would destroy that structure and force a
    per-cell clip; the cost of refining all of them is geometry, not physics,
    and geometry is not metered.
    """
    if k < 1:
        raise LeafError("a refinement factor must be at least one")
    if cells.axis_alpha is None or cells.axis_beta is None:
        raise LeafError("leaf refinement needs the parent's tensor axes")
    ax, ay = _refine_axis(cells.axis_alpha, k), _refine_axis(cells.axis_beta, k)
    na, nb = ax.nodes.size, ay.nodes.size
    a_lo = np.repeat(ax.lo, nb)
    a_hi = np.repeat(ax.hi, nb)
    b_lo = np.tile(ay.lo, na)
    b_hi = np.tile(ay.hi, na)
    child = RayCells(a_lo, a_hi, b_lo, b_hi, ax, ay,
                     f"{cells.convention}_REFINED_x{k}")
    # the parent of a leaf is found from its own axis blocks, never assumed
    pa = np.arange(na) // k
    pb = np.arange(nb) // k
    # parent index in the parent's own (alpha-major) raster
    pn_b = cells.axis_beta.nodes.size
    parent = (np.repeat(pa, nb) * pn_b + np.tile(pb, na)).astype(np.int64)
    return LeafCells(child, parent, 0.5 * (a_lo + a_hi), 0.5 * (b_lo + b_hi), k)


def _parent_raster_index(cells: RayCells) -> np.ndarray:
    """Map each stored parent cell onto the alpha-major raster used above."""
    ax, ay = cells.axis_alpha, cells.axis_beta
    ia = np.clip(np.searchsorted(ax.hi, 0.5 * (cells.alpha_lo + cells.alpha_hi)),
                 0, ax.nodes.size - 1)
    ib = np.clip(np.searchsorted(ay.hi, 0.5 * (cells.beta_lo + cells.beta_hi)),
                 0, ay.nodes.size - 1)
    return (ia * ay.nodes.size + ib).astype(np.int64)


@dataclass
class Assembly:
    """A response with its unresolved mass kept outside the number."""

    known: np.ndarray             # (n_detector, n_field)
    lower: np.ndarray             # unresolved leaves counted as non-emitting
    upper: np.ndarray             # unresolved leaves counted as emitting
    counts: dict = field(default_factory=dict)
    areas: dict = field(default_factory=dict)

    @property
    def unresolved_mass(self) -> np.ndarray:
        return self.upper - self.lower

    def partial(self) -> bool:
        return bool(np.any(self.unresolved_mass > 0))


def assemble(rows: np.ndarray, cols: np.ndarray, vals: np.ndarray,
             label: np.ndarray, fields: np.ndarray, n_detector: int,
             *, granularity: str) -> Assembly:
    """y_d = sum_l |D_d ^ C_l ^ B_n| chi(xi_l) f(xi_l), leaf by leaf.

    ``rows``/``cols``/``vals`` are the sparse overlap of the *same* cells that
    ``label`` and ``fields`` describe. Passing parent-level labels against leaf
    overlaps, or the reverse, is the defect of ruling 027 and is refused here
    rather than silently averaged.
    """
    if granularity != LEAF_RULE:
        raise LeafError(
            f"refusing assembly under {granularity!r}: the only supported "
            f"rule is {LEAF_RULE}; a parent-averaged occupancy proxy "
            f"({PARENT_FRACTION}) moves flux between detector cells")
    label = np.asarray(label)
    fields = np.asarray(fields, float)
    if fields.ndim == 1:
        fields = fields[:, None]
    if fields.ndim != 2:
        raise LeafError("fields must be (n_cell,) or (n_cell, n_field)")
    if label.shape[0] != fields.shape[0]:
        raise LeafError("one label per cell and one field row per cell")
    if cols.size and int(cols.max()) >= label.shape[0]:
        raise LeafError(
            f"the overlap indexes {int(cols.max()) + 1} cells but only "
            f"{label.shape[0]} labels were supplied: the label granularity "
            "does not match the overlap granularity")
    if not np.isin(np.unique(label), (EMITTING, NOT_EMITTING, UNRESOLVED)).all():
        raise LeafError("labels must be EMITTING, NOT_EMITTING or UNRESOLVED")

    nf = fields.shape[1]
    known = np.zeros((n_detector, nf))
    extra = np.zeros((n_detector, nf))
    emit = label[cols] == EMITTING
    unres = label[cols] == UNRESOLVED
    if not np.all(np.isfinite(fields[cols][emit | unres])):
        raise LeafError("a non-finite field value entered the response; a "
                        "missing transfer value is not zero emission")
    w = vals[emit][:, None] * fields[cols[emit]]
    np.add.at(known, rows[emit], w)
    if unres.any():
        # the unknown mass is bounded by the leaf's own overlap times the
        # magnitude of its field, never dropped and never rounded to zero
        wu = vals[unres][:, None] * np.abs(fields[cols[unres]])
        np.add.at(extra, rows[unres], wu)
    return Assembly(known, known.copy(), known + extra)


def bind(assembly: Assembly, counts: dict, areas: dict) -> Assembly:
    """Attach the seven separate counts; a missing one is an error."""
    missing = [k for k in COUNT_FIELDS if k not in counts]
    if missing:
        raise LeafError(f"missing required counts {missing}: an unreached "
                        "endpoint is NOT_EVALUATED, not a zero observation")
    assembly.counts = dict(counts)
    assembly.areas = dict(areas)
    return assembly


def conservation_residual(parent_rows, parent_cols, parent_vals,
                          leaf_rows, leaf_cols, leaf_vals,
                          leaf_parent: np.ndarray, n_detector: int,
                          n_parent: int) -> float:
    """Per detector cell and parent, do the leaves sum to the parent overlap?

    A refinement of the integration must not move geometry. The residual is
    taken on the (detector, parent) pair, because a total-only agreement is
    exactly what the forbidden substitution also satisfies.
    """
    P = np.zeros((n_detector, n_parent))
    np.add.at(P, (parent_rows, parent_cols), parent_vals)
    L = np.zeros((n_detector, n_parent))
    np.add.at(L, (leaf_rows, leaf_parent[leaf_cols]), leaf_vals)
    return float(np.max(np.abs(P - L)))


def parent_fraction_response(rows, cols, vals, chi_parent, fields,
                             n_detector: int) -> np.ndarray:
    """The forbidden substitution, implemented once so it can be measured.

    It exists to be compared against :func:`assemble` and to be refused by the
    launch gate. It is never a production path.
    """
    fields = np.asarray(fields, float)
    fields = fields[:, None] if fields.ndim == 1 else fields
    y = np.zeros((n_detector, fields.shape[1]))
    np.add.at(y, rows, (vals * np.asarray(chi_parent, float)[cols])[:, None]
              * fields[cols])
    return y
