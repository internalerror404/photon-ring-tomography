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


def reference_subspace_errors(op_ref: ReducedOperator, truth: np.ndarray,
                              recon: np.ndarray, snr0: float,
                              rho: float = 1.0) -> dict:
    """The same split, but on one arm's subspace for every arm.

    ``subspace_errors`` uses each arm's own ``P_data``, and those are different
    subspaces of different sizes: on this canary the direct channel supports 154
    directions and the resolved stack 202. Reading the two error norms against
    each other then compares a norm over 202 components with a norm over 154,
    and the extra 48 are exactly the weakly determined ones, so the arm that
    sees more is penalised for seeing more.

    Here the projector comes from a single reference arm -- the direct channel --
    and is applied to every arm's error. Two questions, kept apart:

    ``error_in_reference_data_subspace``
        is the resolved stack better *where the direct channel can already
        see*? Like for like, and the one that answers whether the gain is a
        prior effect.

    ``error_outside_reference_data_subspace``
        does it also recover what the direct channel cannot see? A reduction
        here is only measured recovery for an arm whose own ``P_data`` covers
        those directions; for the direct channel itself it is a prior effect.
    """
    keep, _ = op_ref.project_data_weak(snr0, rho)
    Vk = op_ref.V[:, keep]
    diff = np.atleast_2d(recon - truth)
    c = diff @ Vk
    inside = np.sqrt(np.sum(c ** 2, axis=1))
    total = np.sqrt(np.sum(diff ** 2, axis=1))
    outside = np.sqrt(np.maximum(total ** 2 - inside ** 2, 0.0))
    return {"error_in_reference_data_subspace": inside,
            "error_outside_reference_data_subspace": outside,
            "n_reference_data_directions": int(keep.sum()),
            "reference_arm": op_ref.arm}
