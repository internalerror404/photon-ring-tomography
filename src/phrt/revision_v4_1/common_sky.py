"""One screen, one detector, one noise assignment.

R3A. The archived arms sum image orders by array index, which equalizes
cardinality and nothing else. This builds the thing that index sum was standing
in for: order contributions placed on a common screen by their own alpha and
beta, integrated conservatively onto one detector grid, with noise assigned
once to the detector rather than once per order.

Two constructions are kept apart on purpose, because they answer different
questions and do not share a covariance:

``POSTPROCESSING_INHERITED_NOISE``
    ``A_sky = L A_resolved`` and ``C_sky = L C_resolved L^T``. A compression of
    the *same* parent experiment, so information must contract. This is a data
    processing benchmark and not a forecast of any instrument.

``SINGLE_SKY_DETECTOR_NOISE``
    the physical order contributions are summed on the screen first and a
    detector noise is assigned once afterwards. A different experiment. Its
    information is not comparable to the ideal stack's by assumption, and no
    contraction is claimed for it.

Each raw order carries its own uniform Cartesian cell, so the overlap of a ray
cell with a detector cell is a product of interval intersections and is exact.
Nothing is interpolated: an invalid ray is masked, never smoothed into signal.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import sparse

POSTPROCESSING_INHERITED_NOISE = "POSTPROCESSING_INHERITED_NOISE"
SINGLE_SKY_DETECTOR_NOISE = "SINGLE_SKY_DETECTOR_NOISE"


@dataclass(frozen=True)
class DetectorGrid:
    """A uniform Cartesian screen grid, declared before any spectrum is seen."""

    alpha_min: float
    alpha_max: float
    beta_min: float
    beta_max: float
    pitch: float

    @property
    def n_alpha(self) -> int:
        return int(np.ceil((self.alpha_max - self.alpha_min) / self.pitch))

    @property
    def n_beta(self) -> int:
        return int(np.ceil((self.beta_max - self.beta_min) / self.pitch))

    @property
    def n_cells(self) -> int:
        return self.n_alpha * self.n_beta

    @property
    def cell_area(self) -> float:
        return self.pitch ** 2

    def edges(self) -> tuple[np.ndarray, np.ndarray]:
        return (self.alpha_min + self.pitch * np.arange(self.n_alpha + 1),
                self.beta_min + self.pitch * np.arange(self.n_beta + 1))

    def to_dict(self) -> dict:
        return {"alpha_min": self.alpha_min, "alpha_max": self.alpha_max,
                "beta_min": self.beta_min, "beta_max": self.beta_max,
                "pitch": self.pitch, "n_alpha": self.n_alpha,
                "n_beta": self.n_beta, "n_cells": self.n_cells,
                "cell_area": self.cell_area}


def _overlap_1d(lo: np.ndarray, hi: np.ndarray, edges: np.ndarray
                ) -> list[tuple[np.ndarray, np.ndarray]]:
    """For each input interval, the (cell index, overlap length) pairs."""
    out = []
    n = edges.size - 1
    i0 = np.clip(np.searchsorted(edges, lo, "right") - 1, 0, n - 1)
    i1 = np.clip(np.searchsorted(edges, hi, "left") - 1, 0, n - 1)
    for k in range(lo.size):
        idx = np.arange(i0[k], i1[k] + 1)
        a = np.maximum(lo[k], edges[idx])
        b = np.minimum(hi[k], edges[idx + 1])
        w = np.clip(b - a, 0.0, None)
        out.append((idx, w))
    return out


def overlap_triplets(alpha: np.ndarray, beta: np.ndarray, cell: float,
                     grid: DetectorGrid, valid: np.ndarray
                     ) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict]:
    """Conservative area overlap in coordinate form: rows, columns, areas.

    Row indices address the full detector, but nothing of that length is
    allocated here. A refinement study can therefore run far below the ray
    pitch: the occupied rows stay few, and an empty detector cell carries no
    signal, no noise weight and no information, so leaving it unrepresented
    changes no sum that this construction forms.
    """
    h = 0.5 * np.sqrt(cell)
    ea, eb = grid.edges()
    j = np.flatnonzero(valid)
    oa = _overlap_1d(alpha[j] - h, alpha[j] + h, ea)
    ob = _overlap_1d(beta[j] - h, beta[j] + h, eb)
    rows, cols, vals = [], [], []
    inside = np.zeros(alpha.size)
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
    total = float(cell * valid.sum())
    captured = float(inside[valid].sum())
    return r_, c_, v_, {"n_valid": int(valid.sum()),
                        "total_valid_cell_area": total,
                        "area_captured_in_field_of_view": captured,
                        "area_outside_field_of_view": total - captured,
                        "captured_fraction":
                            captured / total if total > 0 else None}


def overlap_matrix(alpha: np.ndarray, beta: np.ndarray, cell: float,
                   grid: DetectorGrid, valid: np.ndarray
                   ) -> tuple[sparse.csr_matrix, dict]:
    """Conservative area-overlap from one order's cells to the detector.

    Row = detector cell, column = ray. The entry is the overlapping area, so
    applying this to a per-ray surface brightness integrates flux; applying it
    to a per-ray flux would double count, and the caller must not.

    Flux whose cell falls partly outside the field of view is not silently
    dropped: the deficit is measured and returned.
    """
    rows, cols, vals, acc = overlap_triplets(alpha, beta, cell, grid, valid)
    return sparse.csr_matrix((vals, (rows, cols)),
                             shape=(grid.n_cells, alpha.size)), acc


def detector_noise_covariance(grid: DetectorGrid, sigma_omega: float,
                              n_times: int) -> np.ndarray:
    """White noise of fixed density per unit solid angle, assigned once.

    One variance per detector cell per observer time -- not one per image
    order. Summing three orders onto a cell does not triple its noise.
    """
    return np.full(grid.n_cells * n_times,
                   sigma_omega ** 2 * grid.cell_area)
