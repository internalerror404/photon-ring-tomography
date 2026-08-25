"""Source bases on the physical equatorial plane, in (r, phi, t).

Two representations, as ruled, and they answer different questions.

``PhysicalBasis`` -- the registered global class
    4 radial cubic B-splines x 7 real azimuthal Fourier modes x 8 temporal DCT
    modes = 224. Every temporal factor spans the whole history, so this measures
    whether a low-dimensional global model can be fitted. It cannot be indexed
    by epoch.

``age_probe`` -- the localized class
    the same radial and azimuthal factors crossed with one compact temporal bump
    at a declared retarded age. Sweeping the age converts "is the class
    identifiable" into "is this epoch identifiable", which is the question a
    historical claim is actually about.

Both evaluate at arbitrary scattered (r, phi, t), because the physical operator
samples the source wherever the rays happen to land -- there is no grid.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.interpolate import BSpline

DEFAULT_N_RADIAL = 4
DEFAULT_N_AZIMUTHAL = 7      # m = 0, plus cos/sin for m = 1, 2, 3
DEFAULT_N_TEMPORAL = 8
SPLINE_DEGREE = 3


def radial_design(r: np.ndarray, r_inner: float, r_outer: float,
                  n_radial: int = DEFAULT_N_RADIAL) -> np.ndarray:
    """Cubic B-spline design matrix, shape (len(r), n_radial).

    Knots are uniform in log r: the emission region spans a factor of ~25 in
    radius, and uniform-in-r knots would put almost all resolution outside the
    strong-field region where the orders actually differ.
    """
    x = np.log(np.clip(np.asarray(r, dtype=float), r_inner, r_outer))
    lo, hi = np.log(r_inner), np.log(r_outer)
    n_interior = max(n_radial - SPLINE_DEGREE - 1, 0)
    interior = np.linspace(lo, hi, n_interior + 2)[1:-1]
    knots = np.concatenate([[lo] * (SPLINE_DEGREE + 1), interior,
                            [hi] * (SPLINE_DEGREE + 1)])
    out = np.empty((x.size, n_radial))
    for k in range(n_radial):
        c = np.zeros(n_radial)
        c[k] = 1.0
        out[:, k] = BSpline(knots, c, SPLINE_DEGREE, extrapolate=False)(x)
    return np.nan_to_num(out, nan=0.0)


def azimuthal_design(phi: np.ndarray,
                     n_azimuthal: int = DEFAULT_N_AZIMUTHAL) -> np.ndarray:
    """Real Fourier design: [1, cos phi, sin phi, cos 2phi, ...]."""
    p = np.asarray(phi, dtype=float)
    cols = [np.ones_like(p)]
    m = 1
    while len(cols) < n_azimuthal:
        cols.append(np.cos(m * p))
        if len(cols) < n_azimuthal:
            cols.append(np.sin(m * p))
        m += 1
    return np.column_stack(cols[:n_azimuthal])


def temporal_design(t: np.ndarray, t_min: float, t_max: float,
                    n_temporal: int = DEFAULT_N_TEMPORAL) -> np.ndarray:
    """DCT-II style global cosine modes on [t_min, t_max]."""
    span = max(t_max - t_min, 1e-30)
    u = (np.asarray(t, dtype=float) - t_min) / span
    inside = (u >= 0.0) & (u <= 1.0)
    out = np.column_stack([np.cos(np.pi * k * np.clip(u, 0.0, 1.0))
                           for k in range(n_temporal)])
    return out * inside[:, None]


def temporal_bump(t: np.ndarray, centre: float, width: float) -> np.ndarray:
    g = np.exp(-0.5 * ((np.asarray(t, dtype=float) - centre) / width) ** 2)
    return g[:, None]


@dataclass(frozen=True)
class PhysicalBasis:
    """The registered global class, evaluated at scattered source coordinates."""

    r_inner: float
    r_outer: float
    t_min: float
    t_max: float
    n_radial: int = DEFAULT_N_RADIAL
    n_azimuthal: int = DEFAULT_N_AZIMUTHAL
    n_temporal: int = DEFAULT_N_TEMPORAL

    @property
    def dimension(self) -> int:
        return self.n_radial * self.n_azimuthal * self.n_temporal

    def design(self, r: np.ndarray, phi: np.ndarray, t: np.ndarray) -> np.ndarray:
        """Shape (len(r), dimension). Column order is radial-major."""
        R = radial_design(r, self.r_inner, self.r_outer, self.n_radial)
        P = azimuthal_design(phi, self.n_azimuthal)
        T = temporal_design(t, self.t_min, self.t_max, self.n_temporal)
        # outer product per row, flattened as (radial, azimuthal, temporal)
        return (R[:, :, None, None] * P[:, None, :, None]
                * T[:, None, None, :]).reshape(r.size, -1)

    def labels(self) -> list[dict]:
        out = []
        for a in range(self.n_radial):
            for b in range(self.n_azimuthal):
                m = (b + 1) // 2
                for c in range(self.n_temporal):
                    out.append({"radial_mode": a, "azimuthal_mode": b,
                                "azimuthal_m": m, "temporal_mode": c})
        return out


@dataclass(frozen=True)
class AgeProbeBasis:
    """The localized class at one retarded age: radial x azimuthal x one bump."""

    r_inner: float
    r_outer: float
    centre: float
    width: float
    n_radial: int = DEFAULT_N_RADIAL
    n_azimuthal: int = DEFAULT_N_AZIMUTHAL

    @property
    def dimension(self) -> int:
        return self.n_radial * self.n_azimuthal

    def design(self, r: np.ndarray, phi: np.ndarray, t: np.ndarray) -> np.ndarray:
        R = radial_design(r, self.r_inner, self.r_outer, self.n_radial)
        P = azimuthal_design(phi, self.n_azimuthal)
        B = temporal_bump(t, self.centre, self.width)
        return (R[:, :, None] * P[:, None, :]).reshape(r.size, -1) * B


def orthonormalise_design(D: np.ndarray, tol: float = 1e-10) -> tuple[np.ndarray, np.ndarray]:
    """Return (Q, keep) with Q an orthonormal column basis of D's column space.

    Rank-deficient columns are dropped rather than silently retained: a design
    matrix whose columns are not independent on the sampled points makes every
    restricted rank ambiguous.
    """
    Q, R = np.linalg.qr(D)
    d = np.abs(np.diag(R))
    keep = d > tol * max(d.max(), 1e-300)
    return np.ascontiguousarray(Q[:, keep]), keep
