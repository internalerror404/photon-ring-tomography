"""The corrected common-sky acquisition, with its units written down.

Ruling 026. This is a new constructor beside `common_sky`, not a rewrite of
it: the R3A construction and its canaries stay exactly as they were recorded.
Two things are different here.

Cells are rectangles given by four edges. Under C13 a ray's footprint is the
dual cell of its node clipped to the declared screen, so an order's cells have
three different areas -- full in the interior, half along an edge, a quarter at
a corner -- and no single ``sqrt(area)`` square can express that.

Units are explicit. With

    O[d, p] = |D_d intersect P_p|,      a[p] = |P_p|,

``O`` carries *brightness* to integrated detector flux. A parent whose signal
is already integrated flux ``z = a * f`` is therefore mapped by

    L = O diag(a)^-1,        C_inherited = L (sigma^2 diag(a)) L^T
                                         = sigma^2 O diag(1/a) O^T,

and using ``O`` itself where ``L`` belongs is an ``a``-fold error per ray. The
single-sky detector is a different experiment and keeps its own covariance:
one variance ``sigma^2 |D_d|`` per detector cell per observer time, assigned
once after the orders are summed on the screen, never per order and never
interchanged with the inherited form to obtain a preferred ordering.
"""
from __future__ import annotations

import numpy as np
from scipy import sparse

from phrt.revision_v4_1.common_sky import DetectorGrid, _overlap_1d
from phrt.revision_v4_1.measure import RayCells

BRIGHTNESS_PARENT = "BRIGHTNESS_PARENT"
INTEGRATED_FLUX_PARENT = "INTEGRATED_FLUX_PARENT"


class AcquisitionError(RuntimeError):
    pass


def overlap_triplets(cells: RayCells, grid: DetectorGrid, valid: np.ndarray
                     ) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict]:
    """Exact area overlap of rectangular ray cells with detector cells.

    Returns ``(rows, cols, areas, accounting)``. Row indices address the whole
    detector but nothing of that length is allocated, so a refinement study can
    run below the ray pitch without a row space it never uses.
    """
    ea, eb = grid.edges()
    j = np.flatnonzero(valid)
    oa = _overlap_1d(cells.alpha_lo[j], cells.alpha_hi[j], ea)
    ob = _overlap_1d(cells.beta_lo[j], cells.beta_hi[j], eb)
    rows, cols, vals = [], [], []
    inside = np.zeros(valid.size)
    for k in range(j.size):
        ia, wa = oa[k]
        ib, wb = ob[k]
        if wa.sum() <= 0 or wb.sum() <= 0:
            continue
        w = np.outer(wb, wa).ravel()
        r = (ib[:, None].astype(np.int64) * grid.n_alpha
             + ia[None, :].astype(np.int64)).ravel()
        keep = w > 0
        rows.append(r[keep])
        cols.append(np.full(int(keep.sum()), j[k], dtype=np.int64))
        vals.append(w[keep])
        inside[j[k]] = w.sum()
    if rows:
        r_, c_, v_ = (np.concatenate(rows), np.concatenate(cols),
                      np.concatenate(vals))
    else:
        r_ = np.zeros(0, np.int64)
        c_ = np.zeros(0, np.int64)
        v_ = np.zeros(0, float)
    area = cells.area
    total = float(area[valid].sum())
    captured = float(inside[valid].sum())
    return r_, c_, v_, {
        "n_valid": int(valid.sum()),
        "total_valid_cell_area": total,
        "area_captured_in_field_of_view": captured,
        "area_outside_field_of_view": total - captured,
        "captured_fraction": captured / total if total > 0 else None,
        "n_rays_partly_outside": int(
            np.count_nonzero(valid & (inside < area * (1 - 1e-12)))),
        "n_rays_wholly_outside": int(
            np.count_nonzero(valid & (inside <= 0))),
    }


def overlap_operator(cells: RayCells, grid: DetectorGrid, valid: np.ndarray
                     ) -> tuple[sparse.csr_matrix, dict]:
    """``O``: brightness on the ray cells to integrated flux on the detector."""
    r, c, v, acc = overlap_triplets(cells, grid, valid)
    return sparse.csr_matrix((v, (r, c)),
                             shape=(grid.n_cells, cells.area.size)), acc


def postprocessing_matrix(O: sparse.csr_matrix, a: np.ndarray
                          ) -> sparse.csr_matrix:
    """``L = O diag(a)^-1``, for a parent already expressed as integrated flux.

    Zero-area cells would be a division by zero rather than a small number, so
    they are refused: a ray with no footprint has no flux to redistribute and
    must be excluded by the validity mask instead.
    """
    if np.any(a <= 0):
        raise AcquisitionError(
            "a parent cell of zero area cannot carry integrated flux; mask "
            "the ray out rather than inverting its area")
    return O @ sparse.diags(1.0 / a)


def inherited_covariance(O: sparse.csr_matrix, a: np.ndarray, sigma: float
                         ) -> np.ndarray:
    """``sigma^2 O diag(1/a) O^T``: the parent's noise, pushed through ``L``.

    Dense by construction, so this is for fixtures and small detectors. At full
    detector size the whitened response is formed directly instead.
    """
    L = postprocessing_matrix(O, a)
    C_parent = sparse.diags(sigma ** 2 * a)
    return np.asarray((L @ C_parent @ L.T).todense())


def detector_covariance(grid: DetectorGrid, sigma: float, n_times: int
                        ) -> np.ndarray:
    """``sigma^2 |D_d|`` per detector cell per observer time, assigned once.

    One variance per cell, after the orders have been summed on the screen.
    Summing three orders onto a cell does not triple its noise, and this is
    not the inherited covariance above under another name.
    """
    return np.full(grid.n_cells * n_times, sigma ** 2 * grid.cell_area)


def detector_response(cells: RayCells, grid: DetectorGrid, valid: np.ndarray,
                      brightness: np.ndarray, parent: str = BRIGHTNESS_PARENT
                      ) -> np.ndarray:
    """Integrated flux per detector cell, for one or more fields.

    ``brightness`` has one row per ray and one column per field. With
    ``parent=INTEGRATED_FLUX_PARENT`` the same columns are read as already
    integrated over their parent cell, and ``L`` is used in place of ``O`` --
    the two must agree once the caller converts, which is what the unit canary
    checks.
    """
    b = np.atleast_2d(brightness.T).T
    r, c, v, _ = overlap_triplets(cells, grid, valid)
    if parent == INTEGRATED_FLUX_PARENT:
        a = cells.area
        if np.any(a[valid] <= 0):
            raise AcquisitionError("zero-area parent cell in a flux parent")
        v = v / a[c]
    elif parent != BRIGHTNESS_PARENT:
        raise AcquisitionError(f"unknown parent convention {parent!r}")
    y = np.zeros((grid.n_cells, b.shape[1]))
    np.add.at(y, r, v[:, None] * b[c])
    return y
