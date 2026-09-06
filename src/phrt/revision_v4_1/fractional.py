"""Fractional coverage: the detector-cell-domain triple intersection.

Ruling 027. The overlap that matters is

    O[d, p] = | D_d  intersect  C_p  intersect  Omega_n |

and it is NOT the whole-cell emitting fraction times the uncut overlap. That
substitution spreads a cell's emitting part uniformly over the cell and so
puts flux into the wrong detector pixels: a cell emitting only in its leftmost
fifth, straddling two half-width pixels, contributes (0.2, 0) and the
substitution gives (0.1, 0.1). The total survives and the image does not. The
fraction is computed here as a *diagnostic* and is never used as a weight.

``Omega_n`` here is the geometric part of the effective domain -- the order's
lensing band, outer hull minus inner hull under the pinned AART convention,
intersected with the declared aperture. It is not the whole validity
predicate. Band membership is one of four conditions; finite landing
coordinates and ``r_+ < r_source <= 50`` are the others, and they are
properties of solved rays rather than of any curve. Every fragment with
positive geometric area is therefore classified against the transfer data that
does or does not exist for it, and a fragment without data is recorded as
missing, never as zero emission.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from phrt.revision_v4_1 import polyclip as PC
from phrt.revision_v4_1.common_sky import DetectorGrid
from phrt.revision_v4_1.measure import RayCells

# how a fragment with positive geometric area is supported by transfer data
SUPPORTED = "SUPPORTED_BY_VALID_CENTRE_RAY"
OUTSIDE_ANNULUS = "CENTRE_OUTSIDE_DECLARED_EMISSION_ANNULUS"
SOLVER_UNRESOLVED = "CENTRE_SOLVER_UNRESOLVED"
NO_BAND_DATA = "MISSING_TRANSFER_SUPPORT"


@dataclass(frozen=True)
class FractionalOverlap:
    rows: np.ndarray          # detector cell index
    cols: np.ndarray          # ray cell index
    vals: np.ndarray          # | D_d ^ C_p ^ Omega |, an area
    active_area: np.ndarray   # per ray cell, | C_p ^ Omega |
    cut_fraction: np.ndarray  # per ray cell, active_area / | C_p |; diagnostic
    accounting: dict


def _edges(axis_lo, axis_hi):
    return np.unique(np.concatenate([axis_lo, axis_hi]))


def triple_overlap(cells: RayCells, grid: DetectorGrid,
                   outer: np.ndarray, inner: np.ndarray | None
                   ) -> FractionalOverlap:
    """Exact clipped overlap of detector, corrected cell and band.

    The common refinement of the detector edges and the cell edges is itself a
    tensor grid, so every one of its cells lies in exactly one detector cell
    and exactly one ray cell. Computing the band's coverage once on that grid
    gives every entry of ``O`` with no per-pair clipping and no double count.
    """
    if cells.axis_alpha is None or cells.axis_beta is None:
        raise PC.PolygonError("a tensor-product cell set is required")
    ea, eb = grid.edges()
    X = _edges(cells.axis_alpha.lo, cells.axis_alpha.hi)
    Y = _edges(cells.axis_beta.lo, cells.axis_beta.hi)
    # the aperture clips the domain; a cell outside the detector is not
    # measured, and that loss is reported rather than absorbed
    lo_a, hi_a = max(X[0], ea[0]), min(X[-1], ea[-1])
    lo_b, hi_b = max(Y[0], eb[0]), min(Y[-1], eb[-1])
    if lo_a >= hi_a or lo_b >= hi_b:
        raise PC.PolygonError("the cell domain and the aperture do not meet")
    X = np.unique(np.concatenate([X, ea]))
    Y = np.unique(np.concatenate([Y, eb]))
    X = X[(X >= lo_a) & (X <= hi_a)]
    Y = Y[(Y >= lo_b) & (Y <= hi_b)]

    cov = PC.band_coverage(outer, inner, X, Y)
    if cov.min() < -1e-9:
        raise PC.PolygonError(
            f"negative band coverage {cov.min():.3e}: the inner hull is not "
            "contained in the outer one, or a polygon is not simple")
    cov = np.clip(cov, 0.0, None)

    mx = 0.5 * (X[:-1] + X[1:])
    my = 0.5 * (Y[:-1] + Y[1:])
    # each refinement cell belongs to one detector cell and one ray cell
    da = np.clip(np.searchsorted(ea, mx) - 1, 0, grid.n_alpha - 1)
    db = np.clip(np.searchsorted(eb, my) - 1, 0, grid.n_beta - 1)
    # A cell is [lo_i, hi_i] and the cells abut, so searchsorted on the upper
    # edges maps any interior point to its own node index. The node itself is
    # NOT the midpoint of a clipped boundary cell, so searching the nodes
    # would misplace exactly the half-width cells the correction is about.
    na = cells.axis_alpha.nodes.size
    nb_ = cells.axis_beta.nodes.size
    ca = np.clip(np.searchsorted(cells.axis_alpha.hi, mx), 0, na - 1)
    cb = np.clip(np.searchsorted(cells.axis_beta.hi, my), 0, nb_ - 1)
    ia = np.clip(np.searchsorted(cells.axis_alpha.hi,
                                 0.5 * (cells.alpha_lo + cells.alpha_hi)),
                 0, na - 1)
    ib = np.clip(np.searchsorted(cells.axis_beta.hi,
                                 0.5 * (cells.beta_lo + cells.beta_hi)),
                 0, nb_ - 1)
    lut = np.full((na, nb_), -1, np.int64)
    lut[ia, ib] = np.arange(cells.alpha_lo.size)

    gi, gj = np.nonzero(cov > 0)
    if gi.size == 0:
        z = np.zeros(0)
        return FractionalOverlap(z.astype(np.int64), z.astype(np.int64), z,
                                 np.zeros(cells.alpha_lo.size),
                                 np.zeros(cells.alpha_lo.size),
                                 {"active_fragments": 0})
    rows = db[gj].astype(np.int64) * grid.n_alpha + da[gi]
    cols = lut[ca[gi], cb[gj]]
    vals = cov[gi, gj]
    if (cols < 0).any():
        raise PC.PolygonError("a covered refinement cell has no parent ray")

    active = np.bincount(cols, weights=vals, minlength=cells.alpha_lo.size)
    area = cells.area
    frac = np.divide(active, area, out=np.zeros_like(active), where=area > 0)

    band_total = float(abs(PC.signed_area(outer))
                       - (abs(PC.signed_area(inner)) if inner is not None
                          else 0.0))
    acc = {
        "band_area_from_hulls": band_total,
        "band_area_inside_aperture_and_cell_domain": float(vals.sum()),
        "band_area_outside": band_total - float(vals.sum()),
        "captured_fraction": float(vals.sum()) / band_total
                             if band_total > 0 else None,
        "active_fragments": int(np.count_nonzero(active > 0)),
        "fully_covered_fragments": int(np.count_nonzero(frac > 1 - 1e-12)),
        "partially_covered_fragments":
            int(np.count_nonzero((frac > 1e-12) & (frac <= 1 - 1e-12))),
        "refinement_grid": [int(X.size - 1), int(Y.size - 1)],
        "cut_fraction_is_a_diagnostic_not_a_weight": True,
    }
    return FractionalOverlap(rows, cols, vals, active, frac, acc)


def classify_support(active_area: np.ndarray, band_mask: np.ndarray,
                     valid: np.ndarray, source_r: np.ndarray,
                     finite: np.ndarray, r_horizon: float,
                     r_outer: float) -> tuple[np.ndarray, dict]:
    """Why each fragment with positive geometric area does or does not have data.

    A masked zero, a failed solve and an unsampled exterior are three different
    things and none of them is a physical zero. They are separated here so that
    a later stage cannot quietly treat any of them as no emission.
    """
    n = active_area.size
    label = np.full(n, "", dtype=object)
    act = active_area > 0
    label[act & valid] = SUPPORTED
    rest = act & ~valid
    label[rest & ~band_mask] = NO_BAND_DATA
    inb = rest & band_mask
    label[inb & ~finite] = SOLVER_UNRESOLVED
    ok = inb & finite
    label[ok & ((source_r > r_outer) | (source_r <= r_horizon))] = \
        OUTSIDE_ANNULUS
    unexplained = act & (label == "")
    if unexplained.any():
        raise PC.PolygonError(
            f"{int(unexplained.sum())} active fragments could not be "
            "classified; a category is missing rather than empty")
    tally = {k: {"fragments": int(np.count_nonzero(label == k)),
                 "area": float(active_area[label == k].sum())}
             for k in (SUPPORTED, OUTSIDE_ANNULUS, SOLVER_UNRESOLVED,
                       NO_BAND_DATA)}
    tot = float(active_area[act].sum())
    for k in tally:
        tally[k]["area_fraction"] = tally[k]["area"] / tot if tot else None
    return label, {"total_active_area": tot, "by_category": tally,
                   "zero_emission_assumed_anywhere": False}
