"""Kerr equatorial orbit laws, so the source moves the way the redshift assumes.

The ray maps compute ``g`` from AART's fluid model: circular Keplerian orbits
outside the ISCO, plunging on the ISCO's conserved quantities inside it, in the
Kerr metric at the geometry's spin. The emissivity movies, however, advected
their features at the Newtonian rate ``Omega = r^{-3/2}`` and were allowed to
place circular hotspots anywhere from ``r = 3 M`` outward.

Both of those are inconsistent with the redshift the same rays carry. At
``a* = 0.5`` the prograde ISCO is at ``4.233 M``, so a circular feature drawn at
``3 M`` is orbiting where no circular orbit exists, and the Newtonian rate is
wrong by ~5% at the inner edge -- a pattern-speed error that accumulates into a
whole radian of phase over a 120 M history. Neither breaks a linear-algebra
gate, which is exactly why it survived: the operator is linear in ``j`` and does
not care whether ``j`` is physical.

This module supplies the consistent laws. It does not modify
``phrt.sources.movie.keplerian_omega``: the R1 banks are sealed and reported
under that law, and silently changing it would rewrite a result rather than
supersede it. New source families opt in here; the old ones keep their record.
"""
from __future__ import annotations

import numpy as np

PROGRADE = +1
RETROGRADE = -1


def isco_radius(a: float, sense: int = PROGRADE) -> float:
    """Kerr equatorial ISCO in M, Bardeen-Press-Teukolsky."""
    a = float(a)
    z1 = 1.0 + np.cbrt(1.0 - a ** 2) * (np.cbrt(1.0 + a) + np.cbrt(1.0 - a))
    z2 = np.sqrt(3.0 * a ** 2 + z1 ** 2)
    return float(3.0 + z2 - np.sign(sense) * np.sqrt((3.0 - z1) * (3.0 + z1 + 2.0 * z2)))


def horizon_radius(a: float) -> float:
    return float(1.0 + np.sqrt(1.0 - float(a) ** 2))


def kerr_omega(r: np.ndarray | float, a: float,
               sense: int = PROGRADE) -> np.ndarray | float:
    """Angular velocity of a circular equatorial geodesic, ``1/(r^{3/2} + a)``.

    Prograde takes ``+a``. This is the rate the fluid actually turns at in the
    metric the ray maps were traced in, so a feature advected at this rate keeps
    a fixed position relative to the fluid element that emits it.
    """
    rr = np.asarray(r, dtype=float)
    return np.sign(sense) / (rr ** 1.5 + np.sign(sense) * float(a))


def circular_energy_angular_momentum(r: np.ndarray | float, a: float,
                                     sense: int = PROGRADE) -> tuple:
    """Specific energy and angular momentum of a circular equatorial orbit."""
    rr = np.asarray(r, dtype=float)
    s = np.sign(sense)
    root = np.sqrt(rr)
    denom = rr ** 0.75 * np.sqrt(rr ** 1.5 - 3.0 * root + 2.0 * s * float(a))
    E = (rr ** 1.5 - 2.0 * root + s * float(a)) / denom
    L = s * (rr ** 2 - 2.0 * s * float(a) * root + float(a) ** 2) / denom
    return E, L


def plunge_omega(r: np.ndarray | float, a: float,
                 sense: int = PROGRADE) -> np.ndarray | float:
    """Angular velocity inside the ISCO, on the ISCO's conserved E and L.

    ``Omega = u^phi / u^t`` for an equatorial geodesic carrying the marginally
    stable orbit's constants, which is the same plunge law the ray maps' fluid
    uses. Inside the ISCO the pattern is not free to rotate at ``Omega_K``:
    there is no circular orbit there, so a family that keeps using the circular
    law inside is describing motion that cannot happen.
    """
    rr = np.asarray(r, dtype=float)
    aa = float(a)
    E, L = circular_energy_angular_momentum(isco_radius(aa, sense), aa, sense)
    E, L = float(E), float(L)
    num = (rr - 2.0) * L + 2.0 * aa * E
    den = (rr ** 3 + aa ** 2 * rr + 2.0 * aa ** 2) * E - 2.0 * aa * L
    return num / den


def pattern_omega(r: np.ndarray | float, a: float,
                  sense: int = PROGRADE) -> np.ndarray | float:
    """Circular outside the ISCO, plunging inside it -- the fluid's own law."""
    rr = np.asarray(r, dtype=float)
    r_isco = isco_radius(a, sense)
    out = np.where(rr >= r_isco, kerr_omega(np.maximum(rr, r_isco), a, sense),
                   plunge_omega(np.minimum(rr, r_isco), a, sense))
    return out if np.ndim(r) else float(out)


def velocity_field_record(a: float, sense: int = PROGRADE) -> dict:
    """The declared velocity field, recorded alongside every result that uses it.

    ``g^3`` is not a free parameter of the reconstruction: it is fixed by this
    field and baked into the ray maps. Recording it makes the source families'
    motion and the redshift they are weighted by checkable against each other
    instead of merely assumed to agree.
    """
    r_isco = isco_radius(a, sense)
    return {
        "metric": "Kerr, Boyer-Lindquist, equatorial, M = 1",
        "spin": float(a),
        "sense": "prograde" if np.sign(sense) > 0 else "retrograde",
        "outside_isco": "circular geodesic, Omega = 1 / (r^{3/2} + a)",
        "inside_isco": "radial plunge on the ISCO's conserved E and L, "
                       "Omega = u^phi / u^t",
        "isco_radius_M": r_isco,
        "horizon_radius_M": horizon_radius(a),
        "omega_isco": float(kerr_omega(r_isco, a, sense)),
        "matches_raymap_fluid": True,
        "raymap_fluid_note": "AART gfactorf called with betaphi = betar = sub_kep "
                             "= 1, i.e. fully Keplerian outside the ISCO and "
                             "plunging inside it, which is the same field",
        "superseded_law": "Omega = r^{-3/2}, Newtonian, used by the R0/R1 "
                          "families; retained there because those banks are "
                          "sealed and reported",
    }


def circular_radius_bounds(a: float, r_outer: float,
                           sense: int = PROGRADE) -> tuple[float, float]:
    """Admissible centre radii for a *circular* feature: outside the ISCO."""
    return isco_radius(a, sense), float(r_outer)
