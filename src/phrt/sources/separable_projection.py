"""Least-squares projection onto a tensor-product class, mode by mode.

HMT-2 stage 0, item 11. The finest audit grid holds 64 x 128 x 160 cells and
the enriched class has 896 functions; a dense design matrix would be about
eight gigabytes and is unnecessary. The basis is a tensor product of radial,
azimuthal and temporal factors and the grid is a tensor product of its axes, so
the normal equations factorise and the projection is three small solves applied
along one axis each.

This is exact, not an approximation of the dense projection: for a tensor
product basis on a tensor product grid with uniform weights the two coincide.
A test asserts they agree on a grid small enough to build densely.

The m = 0 removal is applied in the azimuthal factor, where it is one column,
rather than by masking columns of an assembled design.
"""
from __future__ import annotations

import numpy as np

from phrt.sources.localized_basis import (azimuthal_design, radial_design,
                                          temporal_design)


def factors(r_axis, phi_axis, t_axis, n_radial, n_azimuthal, n_temporal,
            drop_m0: bool = True) -> dict:
    """The three factor matrices, with the axisymmetric column removed."""
    B_r = radial_design(np.asarray(r_axis, float), float(r_axis[0]),
                        float(r_axis[-1]), n_radial)
    B_p = azimuthal_design(np.asarray(phi_axis, float), n_azimuthal)
    B_t = temporal_design(np.asarray(t_axis, float), float(t_axis[0]),
                          float(t_axis[-1]), n_temporal)
    if drop_m0:
        B_p = B_p[:, 1:]                # column 0 is the m = 0 constant
    return {"r": B_r, "phi": B_p, "t": B_t,
            "dimension": B_r.shape[1] * B_p.shape[1] * B_t.shape[1]}


def _apply(mat: np.ndarray, x: np.ndarray, axis: int) -> np.ndarray:
    """Hat matrix of ``mat`` applied along one axis of a 3-d array."""
    G = mat.T @ mat
    y = np.moveaxis(x, axis, 0)
    shape = y.shape
    y = y.reshape(shape[0], -1)
    y = mat @ np.linalg.solve(G, mat.T @ y)
    return np.moveaxis(y.reshape(shape), 0, axis)


def project(field: np.ndarray, fac: dict) -> np.ndarray:
    """Orthogonal projection of an ``(n_r, n_phi, n_t)`` field onto the class."""
    y = _apply(fac["r"], np.asarray(field, float), 0)
    y = _apply(fac["phi"], y, 1)
    return _apply(fac["t"], y, 2)


def minimum_representable_width(fac: dict, r_axis, phi_axis, t_axis,
                                widths_M, r_centre: float,
                                broadening: float = 2.0) -> dict:
    """The narrowest feature the class keeps narrow. Item 16.

    A Gaussian of decreasing width is projected onto the class and the width of
    what comes back is measured. Below some input width the output stops
    following it: the class has no functions narrow enough and returns
    something broader. The reported minimum is the input width at which the
    output has broadened by the declared factor, which is stated rather than
    fitted.
    """
    r = np.asarray(r_axis, float)
    p = np.asarray(phi_axis, float)
    t = np.asarray(t_axis, float)
    rows = []
    for w in widths_M:
        f = (np.exp(-0.5 * ((r[:, None] - r_centre) / w) ** 2)[:, :, None]
             * np.cos(p)[None, :, None] * np.ones(t.size)[None, None, :])
        g = project(f, fac)
        prof = np.maximum(g[:, :, t.size // 2].max(axis=1), 0.0)
        tot = prof.sum()
        if tot <= 0:
            rows.append({"input_width_M": float(w), "output_width_M": np.inf,
                         "ratio": np.inf})
            continue
        c = float((prof * r).sum() / tot)
        var = float((prof * (r - c) ** 2).sum() / tot)
        out = float(np.sqrt(max(var, 0.0)))
        rows.append({"input_width_M": float(w), "output_width_M": out,
                     "ratio": float(out / w)})
    over = [x for x in rows if x["ratio"] >= broadening]
    return {"curve": rows, "broadening_factor": broadening,
            "minimum_representable_width_M":
                float(max(x["input_width_M"] for x in over)) if over
                else float("nan")}
