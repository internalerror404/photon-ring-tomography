"""Splitting the reconstruction error into data-supported and weak subspaces.

    P_data = sum_{i : SNR_0 sigma_i >= rho} v_i v_i^T,   P_weak = I - P_data

The split exists to keep one specific claim honest: an estimator with a prior
can reduce the error inside ``P_weak`` without any information having been
measured there. That is a prior effect, and describing it as recovery would be
wrong. The two errors are therefore always reported separately and never summed
into a single headline number.
"""
from __future__ import annotations

import numpy as np

from phrt.inverse.reduced import ReducedOperator


def subspace_errors(op: ReducedOperator, truth: np.ndarray,
                    recon: np.ndarray, snr0: float, rho: float = 1.0) -> dict:
    """Coefficient-space error split by the data-supported projector."""
    keep, weak = op.project_data_weak(snr0, rho)
    diff = np.atleast_2d(recon - truth)
    c = diff @ op.V                       # components along singular directions
    # the part of the difference outside span(V) is unobservable by any arm and
    # is attributed to the weak subspace, which is where it belongs
    outside = diff - c @ op.V.T
    e_data = np.sqrt(np.sum(c[:, keep] ** 2, axis=1))
    e_weak = np.sqrt(np.sum(c[:, weak] ** 2, axis=1)
                     + np.sum(outside ** 2, axis=1))
    tot = np.sqrt(np.sum(diff ** 2, axis=1))
    return {"error_data_supported": e_data, "error_weak": e_weak,
            "error_total": tot,
            "n_data_directions": int(keep.sum()),
            "n_weak_directions": int(op.dimension - keep.sum())}
