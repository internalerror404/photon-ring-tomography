"""Localized-in-time source classes for AMENDMENT_001.

The registered smooth class is a tensor product of *global* temporal DCT modes:
every basis function spans the whole history.  Its restricted spectrum
therefore reports identifiability averaged over all retarded epochs, and no
per-epoch statement can be recovered from it -- a single sigma_min tells you
that some direction is weak, not when it happened.

This module supplies the complementary probe: a compact temporal bump centred
at one retarded age, crossed with the registered RS spatial modes.  Sweeping
the centre over the history turns "how identifiable is the class" into "how
identifiable is *this epoch*", which is the quantity a historical-inversion
claim actually rests on.

It is an addition, not a substitute.  The registered DCT arm is unchanged and
is still the primary reported class.
"""
from __future__ import annotations

import numpy as np
import scipy.fft as sfft

from phrt.sources.toy_classes import REGISTERED_RS, REGISTERED_RT, _dct_modes, _orthonormalise

DEFAULT_WIDTH = 1.5


def temporal_bump(history: int, centre: float, width: float = DEFAULT_WIDTH) -> np.ndarray:
    """Unit-norm Gaussian bump on the retarded-age axis.

    The axis is retarded age (index 0 = most recent), matching
    ``phrt.operators.structured``.
    """
    t = np.arange(history, dtype=float)
    g = np.exp(-0.5 * ((t - centre) / width) ** 2)
    n = np.linalg.norm(g)
    if n <= 0:
        raise ValueError(f"degenerate bump at centre {centre}")
    return g / n


def localized_epoch_class(n_cells: int, history: int, centre: float,
                          n_spatial: int = REGISTERED_RS,
                          width: float = DEFAULT_WIDTH) -> np.ndarray:
    """RS spatial modes crossed with one temporal bump: an RS-dimensional class
    supported almost entirely on a single retarded epoch."""
    S = _dct_modes(n_cells, n_spatial)
    g = temporal_bump(history, centre, width)
    cols = [np.outer(S[:, a], g).reshape(-1) for a in range(n_spatial)]
    return _orthonormalise(np.column_stack(cols))


def epoch_energy_fraction(Q: np.ndarray, n_cells: int, history: int,
                          centre: float, radius: float = 3.0) -> float:
    """Fraction of the class's energy lying within ``radius`` of the centre.

    Reported so that "localized" is a measured property of the basis rather
    than an adjective in the method section.
    """
    t = np.arange(history, dtype=float)
    inside = np.abs(t - centre) <= radius
    E = (Q.reshape(n_cells, history, -1) ** 2).sum(axis=(0, 2))
    return float(E[inside].sum() / max(E.sum(), 1e-300))


def dct_temporal_localization(history: int, n_temporal: int = REGISTERED_RT) -> float:
    """Best-case temporal localization of the registered DCT arm.

    Returns the smallest fraction-within-3-samples achievable by any single
    registered temporal mode -- the number that shows the DCT arm cannot
    resolve an epoch, however it is combined.
    """
    T = _dct_modes(history, n_temporal)
    t = np.arange(history, dtype=float)
    best = 0.0
    for b in range(T.shape[1]):
        e = T[:, b] ** 2
        com = float((e * t).sum() / max(e.sum(), 1e-300))
        inside = np.abs(t - com) <= 3.0
        best = max(best, float(e[inside].sum() / max(e.sum(), 1e-300)))
    return best
