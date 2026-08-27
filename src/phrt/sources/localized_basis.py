"""Compactly supported temporal factors, so no coefficient spans the history.

The registered class C224 crosses its spatial factors with global DCT modes.
Every temporal basis function is then supported on the whole source-time
interval, which means a coefficient fitted where the rays actually land also
determines the field where no ray lands. A reconstruction that looks deep can
therefore be global cosine extrapolation rather than measurement, and nothing
in a rank or error table separates the two.

Replacing the temporal factor with compactly supported functions removes the
mechanism. A coefficient whose support contains no ray is unconstrained by
construction: it shows up as an exact null direction of the operator rather
than as a confident extrapolation. That is the property this module exists to
provide, and it is why the temporal functions here are local rather than
smooth.

The temporal family
-------------------
Degree-one B-splines (hat functions) on the dyadic node set

    t_k = t_min + k w,   k = 0 .. n-1,    w = (t_max - t_min) / n,   n = 2^j

Support is ``2w``, except for the function at ``t_min``, which is a half hat of
width ``w``. Equivalently the space is "piecewise linear on the dyadic grid,
vanishing at ``t_max``". That boundary condition costs nothing: ``t_max`` sits
in the unreachable pad above ``max(t_obs) - min(delay)``, so no ray samples the
field there and nothing measurable is being constrained away. It is what keeps
the dimension at exactly ``n``.

Nesting is exact, and the reason is arithmetic rather than numerical: the
coarse node set is the even half of the fine one, and a function that is
piecewise linear on the coarse nodes is piecewise linear on the fine nodes.
So span(n = 8) is a subspace of span(n = 16), and ``nesting_residual`` in the
audit measures zero rather than something small.

Degree one is not an aesthetic choice. On a bounded interval it is the highest
polynomial degree for which the dyadic B-spline family has dimension exactly
``2^j`` *and* nests exactly. Degree two and above need ``2^j + p`` functions to
cover the boundary, which would break the dimension mirror against E3D's
C224 / C448_T / C1056_ST ladder. The mirror is what makes the localized result
comparable to the global one, so the degree gives way to it.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from phrt.sources.physical_basis import azimuthal_design, radial_design

DEFAULT_N_RADIAL = 4
DEFAULT_N_AZIMUTHAL = 7
DEFAULT_N_TEMPORAL = 8
TEMPORAL_DEGREE = 1


def _require_dyadic(n_temporal: int) -> int:
    if n_temporal < 2 or (n_temporal & (n_temporal - 1)) != 0:
        raise ValueError(f"n_temporal must be a power of two, got {n_temporal}; "
                         "exact nesting is a dyadic statement and approximating "
                         "it would make every nesting gate meaningless")
    return int(n_temporal)


def temporal_nodes(t_min: float, t_max: float, n_temporal: int) -> np.ndarray:
    """Peak locations of the compact temporal functions."""
    n = _require_dyadic(n_temporal)
    w = (float(t_max) - float(t_min)) / n
    return float(t_min) + w * np.arange(n, dtype=float)


def temporal_support_widths(t_min: float, t_max: float,
                            n_temporal: int) -> np.ndarray:
    """Declared support width of each temporal function, in M.

    Reported rather than derived at read time, because the whole point of the
    class is that these widths are finite and were fixed before anything was
    evaluated.
    """
    n = _require_dyadic(n_temporal)
    w = (float(t_max) - float(t_min)) / n
    out = np.full(n, 2.0 * w)
    out[0] = w
    return out


def temporal_supports(t_min: float, t_max: float,
                      n_temporal: int) -> np.ndarray:
    """Shape (n_temporal, 2): the closed interval each function lives on."""
    n = _require_dyadic(n_temporal)
    w = (float(t_max) - float(t_min)) / n
    nodes = temporal_nodes(t_min, t_max, n)
    lo = np.maximum(nodes - w, float(t_min))
    hi = np.minimum(nodes + w, float(t_max))
    return np.column_stack([lo, hi])


def temporal_design(t: np.ndarray, t_min: float, t_max: float,
                    n_temporal: int = DEFAULT_N_TEMPORAL) -> np.ndarray:
    """Compact hat design, shape (len(t), n_temporal), zero outside [t_min, t_max]."""
    n = _require_dyadic(n_temporal)
    span = max(float(t_max) - float(t_min), 1e-30)
    w = span / n
    x = np.asarray(t, dtype=float)
    inside = (x >= float(t_min)) & (x <= float(t_max))
    u = (x - float(t_min)) / w                      # node index coordinate
    k = np.arange(n, dtype=float)
    out = np.clip(1.0 - np.abs(u[:, None] - k[None, :]), 0.0, None)
    return out * inside[:, None]


@dataclass(frozen=True)
class LocalizedBasis:
    """Radial B-splines x azimuthal Fourier modes x compact temporal hats.

    Interface-compatible with ``PhysicalBasis`` so the operator, the audits and
    the estimators consume it unchanged; only the temporal factor differs, which
    is the single variable this experiment turns.
    """

    r_inner: float
    r_outer: float
    t_min: float
    t_max: float
    n_radial: int = DEFAULT_N_RADIAL
    n_azimuthal: int = DEFAULT_N_AZIMUTHAL
    n_temporal: int = DEFAULT_N_TEMPORAL

    def __post_init__(self) -> None:
        _require_dyadic(self.n_temporal)

    @property
    def dimension(self) -> int:
        return self.n_radial * self.n_azimuthal * self.n_temporal

    def design(self, r: np.ndarray, phi: np.ndarray, t: np.ndarray) -> np.ndarray:
        """Shape (len(r), dimension). Column order is radial-major, as C224."""
        R = radial_design(r, self.r_inner, self.r_outer, self.n_radial)
        P = azimuthal_design(phi, self.n_azimuthal)
        T = temporal_design(t, self.t_min, self.t_max, self.n_temporal)
        return (R[:, :, None, None] * P[:, None, :, None]
                * T[:, None, None, :]).reshape(np.asarray(r).size, -1)

    def nodes(self) -> np.ndarray:
        return temporal_nodes(self.t_min, self.t_max, self.n_temporal)

    def support_widths(self) -> np.ndarray:
        return temporal_support_widths(self.t_min, self.t_max, self.n_temporal)

    def supports(self) -> np.ndarray:
        return temporal_supports(self.t_min, self.t_max, self.n_temporal)

    def labels(self) -> list[dict]:
        sup = self.supports()
        wid = self.support_widths()
        out = []
        for a in range(self.n_radial):
            for b in range(self.n_azimuthal):
                m = (b + 1) // 2
                for c in range(self.n_temporal):
                    out.append({"radial_mode": a, "azimuthal_mode": b,
                                "azimuthal_m": m, "temporal_mode": c,
                                "temporal_support_lo_M": float(sup[c, 0]),
                                "temporal_support_hi_M": float(sup[c, 1]),
                                "temporal_support_width_M": float(wid[c])})
        return out

    def temporal_columns_covering(self, t: np.ndarray) -> np.ndarray:
        """Boolean mask over temporal modes whose support contains a sample.

        A mode that no ray reaches is not badly determined, it is undetermined:
        the corresponding columns of the operator are exactly zero. Naming that
        set explicitly is what turns "the direct image cannot see old epochs"
        from a conditioning statement into a support statement.
        """
        T = temporal_design(t, self.t_min, self.t_max, self.n_temporal)
        return np.abs(T).max(axis=0) > 0.0

    def columns_for_temporal_modes(self, mask: np.ndarray) -> np.ndarray:
        """Expand a temporal-mode mask to the full coefficient index set."""
        m = np.asarray(mask, dtype=bool)
        return np.tile(m, self.n_radial * self.n_azimuthal)
