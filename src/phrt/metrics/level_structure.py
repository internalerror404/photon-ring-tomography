"""The level/structure split, as an explicit orthogonal projector.

REVIEWER_RULING_R0C_005. R0C showed a 32 M anchored-span gain at the reference
SNR under the registered metric and no structure recovery at all under the
companion until three orders of magnitude higher. Those are different results
and the paper's language has to be exact about which one it is claiming, so the
split stops being a normalisation convention and becomes a projector:

    x = P_level x + P_structure x,      P_structure = I - P_level

``P_level`` is the orthogonal projection onto fields that are constant in space
at each source time. It is spanned by the class's own temporal modes rendered
as spatially uniform fields, so it is a subspace of the class rather than an
approximation to one, and it carries the positive baseline every family sits on
together with whatever time dependence that baseline has.

The evaluation grid declares equal weights -- it is a scoring device, not a
quadrature of the emission -- so the inner product here is the plain Euclidean
one on grid points, which is the same inner product the age-window norms use.

This is a diagnostic, not an endpoint. It has no threshold, no tolerance and
nothing to select on; it splits an error that is already being reported.
"""
from __future__ import annotations

import numpy as np

from phrt.sources.physical_basis import temporal_design


def level_subspace(t: np.ndarray, t_min: float, t_max: float,
                   n_temporal: int) -> np.ndarray:
    """Orthonormal field values spanning the spatially constant modes.

    Columns are the class's temporal modes evaluated at every grid point and
    made uniform in radius and azimuth, then orthonormalised. Returned as an
    (n_points, k) matrix with orthonormal columns.
    """
    T = temporal_design(np.asarray(t, float), t_min, t_max, n_temporal)
    q, r = np.linalg.qr(T)
    keep = np.abs(np.diag(r)) > 1e-12 * max(abs(np.diag(r)).max(), 1e-300)
    return np.ascontiguousarray(q[:, keep])


def split(values: np.ndarray, level: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """``(P_level v, P_structure v)`` for one field or a stack of them."""
    v = np.atleast_2d(np.asarray(values, float))
    lev = (v @ level) @ level.T
    return lev, v - lev


def component_errors(truth: np.ndarray, recon: np.ndarray, level: np.ndarray,
                     weights: np.ndarray, eta: float = 1e-12) -> dict:
    """Age-resolved error in each component, absolute and normalised.

    ``weights`` is the (n_ages, n_points) age-window matrix the registered
    metric already uses, so the only thing that changes between the two
    components is which part of the field is being compared.
    """
    tl, ts = split(truth, level)
    rl, rs = split(recon, level)

    def norms(a):
        return np.sqrt(np.einsum("ap,np->na", weights ** 2, a ** 2))

    el, es = norms(rl - tl), norms(rs - ts)
    nl, ns = norms(tl), norms(ts)
    return {"error_level_absolute": el,
            "error_structure_absolute": es,
            "error_level_normalized": el / np.maximum(nl, eta),
            "error_structure_normalized": es / np.maximum(ns, eta),
            "truth_level_norm": nl,
            "truth_structure_norm": ns,
            "level_fraction_of_truth":
                nl / np.maximum(np.sqrt(nl ** 2 + ns ** 2), eta),
            "n_level_modes": int(level.shape[1])}
