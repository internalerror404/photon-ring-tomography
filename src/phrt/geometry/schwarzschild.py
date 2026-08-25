"""Exact Schwarzschild branch for the a* = 0 registered geometry.

Two independent tools are singular at exactly zero spin, for unrelated reasons,
and both were found by measurement rather than assumed:

AART ``lensingbands.CritCurve``
    forms ``lam = a + (r/a)(...)`` and ``eta = (r^3/a^2)(...)`` while sweeping r
    over the photon shell [rM, rP], which collapses to the single radius 3M at
    a = 0. The positivity mask then selects no points and the call raises.

kgeo ``velocities.u_kep``
    computes ``Omega = np.sign(a) * s / (r^1.5 + s|a|)``. The ``np.sign(a)``
    factor is there to set the orbit sense, but it is zero at a = 0, so the
    Keplerian disk is returned non-rotating: u^t is correct and u^phi is
    identically zero. Verified against the exact values at r = 7, 10, 30.

kgeo's *geodesics* are fine at a = 0 -- ``r_equatorial`` reproduces AART to
2e-12 at every spin tested -- so only the fluid velocity needs replacing. This
module supplies it in closed form and leaves the redshift formula itself to
kgeo, so the only new derivation is the part that has to be new.

Neither external package is modified. Both remain pinned validation
dependencies.
"""
from __future__ import annotations

import numpy as np

R_HORIZON = 2.0
R_PHOTON_SPHERE = 3.0
R_ISCO = 6.0
B_CRITICAL = 3.0 * np.sqrt(3.0)

# Conserved quantities of the ISCO circular orbit, used for the plunge inside it.
E_ISCO = np.sqrt(8.0 / 9.0)
L_ISCO = np.sqrt(12.0)


def keplerian_u(r: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Cunningham four-velocity for Schwarzschild: Keplerian outside the ISCO,
    plunging on the ISCO's conserved quantities inside it.

    Returns (u^t, u^r, u^theta, u^phi) in Boyer-Lindquist, with M = 1.
    """
    r = np.asarray(r, dtype=float)
    u0 = np.zeros_like(r)
    u1 = np.zeros_like(r)
    u3 = np.zeros_like(r)

    outside = r >= R_ISCO
    if np.any(outside):
        rr = r[outside]
        omega = rr ** -1.5                       # Keplerian angular velocity
        ut = 1.0 / np.sqrt(1.0 - 3.0 / rr)       # circular-orbit normalisation
        u0[outside] = ut
        u3[outside] = omega * ut

    inside = ~outside
    if np.any(inside):
        rr = np.clip(r[inside], R_HORIZON + 1e-12, None)
        f = 1.0 - 2.0 / rr
        u0[inside] = E_ISCO / f
        u3[inside] = L_ISCO / rr ** 2
        # radial: normalisation u.u = -1, infalling
        rad = E_ISCO ** 2 - f * (1.0 + L_ISCO ** 2 / rr ** 2)
        u1[inside] = -np.sqrt(np.clip(rad, 0.0, None))

    return u0, u1, np.zeros_like(r), u3


def four_velocity_norm(r: np.ndarray) -> np.ndarray:
    """u.u, which must equal -1 everywhere outside the horizon.

    Computed from the metric rather than from the construction, so it is a real
    check on the branch and not a restatement of it.
    """
    r = np.asarray(r, dtype=float)
    u0, u1, _u2, u3 = keplerian_u(r)
    f = 1.0 - 2.0 / r
    return -f * u0 ** 2 + u1 ** 2 / f + r ** 2 * u3 ** 2


def exact_invariants() -> dict[str, float]:
    """Closed-form Schwarzschild values the backend is validated against."""
    return {"horizon_radius": R_HORIZON, "photon_sphere_radius": R_PHOTON_SPHERE,
            "isco_radius": R_ISCO, "critical_impact_parameter": B_CRITICAL,
            "E_isco": float(E_ISCO), "L_isco": float(L_ISCO)}


def kerr_keplerian_u(a: float, r: np.ndarray) -> tuple:
    """The same Cunningham prescription at nonzero spin, for the low-spin limit.

    This is the standard Kerr expression; at a = 0 it reduces to
    ``keplerian_u``. It exists so the Schwarzschild branch can be checked
    against a spin-dependent formula that is *not* the one being tested, and
    against kgeo at spins where kgeo works.
    """
    r = np.asarray(r, dtype=float)
    z1 = 1 + np.cbrt(1 - a ** 2) * (np.cbrt(1 + a) + np.cbrt(1 - a))
    z2 = np.sqrt(3 * a ** 2 + z1 ** 2)
    r_isco = 3 + z2 - np.sqrt((3 - z1) * (3 + z1 + 2 * z2))
    u0 = np.zeros_like(r)
    u3 = np.zeros_like(r)
    out = r >= r_isco
    if np.any(out):
        rr = r[out]
        # Omega = 1 / (r^{3/2} + a); no sign(a) factor, which is the term that
        # makes kgeo's version vanish at a = 0.
        omega = 1.0 / (rr ** 1.5 + a)
        u0[out] = (rr ** 1.5 + a) / np.sqrt(rr ** 3 - 3 * rr ** 2 + 2 * a * rr ** 1.5)
        u3[out] = omega * u0[out]
    return u0, np.zeros_like(r), np.zeros_like(r), u3
