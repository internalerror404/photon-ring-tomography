"""Static checks on the radial quartic and its turning-point reduction. 032.

Ruling 032 identified two defects in how 031 checked its own roots.

*The residual was tautological.* I1 reported, per point,

    max_i | prod_j (z_i - z_j) |  ==  0,

which is zero for any list whatsoever, because the factor j = i is the root
subtracted from itself. It says nothing about whether the roots solve anything.
The residual has to be taken against the polynomial built from the conserved
quantities. For this project's M = 1 convention,

    R(r) = r^4 + (a^2 - lam^2 - eta) r^2 + 2((lam - a)^2 + eta) r - a^2 eta,

and lam, eta come from the screen coordinates, not from the returned roots.

*The turning root was excluded by object identity.* ``pathdomain2`` forms the
reduced potential with ``[r - q for q in roots if q is not turn]``. ``turn`` is
a Python float taken out of the array, so ``is not`` is almost always true for
every element and the factor (r - turn) survives; the product then vanishes at
the turn instead of tending to the analytic limit. Exclusion must be by the
verified index, with the multiplicity of that root checked, because the limit
is only a limit when the turning root is simple.

Nothing here recomputes a path integral or a ray. Everything is closed-form
algebra on archived screen coordinates and on synthetic fixtures, so a small
residual is reported as a backward error, never as a bound on where a root is.
"""
from __future__ import annotations

import numpy as np

SIMPLE, MULTIPLE, CLUSTERED = "SIMPLE", "MULTIPLE", "CLUSTERED"


class RootCheckError(RuntimeError):
    """A reduction that is not valid on the branch it was asked for."""


def conserved_quantities(alpha, beta, theta_o: float, a: float):
    """lam and eta from the screen, in the pinned convention (AART eq. 32 ff.).

    Written out here rather than imported so the diagnostic does not inherit
    the very code it is checking.
    """
    alpha = np.asarray(alpha, float)
    beta = np.asarray(beta, float)
    lam = -alpha * np.sin(theta_o)
    eta = (alpha ** 2 - a ** 2) * np.cos(theta_o) ** 2 + beta ** 2
    return lam, eta


def quartic_coefficients(a: float, lam, eta):
    """Descending coefficients of the expanded null radial potential."""
    lam = np.asarray(lam, float)
    eta = np.asarray(eta, float)
    one = np.ones_like(lam)
    return np.stack([one, 0.0 * one, a * a - lam * lam - eta,
                     2.0 * ((lam - a) ** 2 + eta), -a * a * eta])


def horner(coeff, z):
    """Complex Horner evaluation; coefficients descending."""
    coeff = np.asarray(coeff)
    z = np.asarray(z, dtype=complex)
    out = np.zeros_like(z) + coeff[0]
    for c in coeff[1:]:
        out = out * z + c
    return out


def horner_derivative(coeff, z):
    coeff = np.asarray(coeff)
    n = coeff.size - 1
    d = coeff[:-1] * np.arange(n, 0, -1)
    return horner(d, z)


def backward_residual(coeff, z):
    """|p(z)| divided by the Horner-accumulated magnitude at |z|.

    This is the scale-aware quantity: a bare |p(z)| near r ~ 50 is dominated by
    r^4 and looks small for anything. It is a backward error -- the size of the
    perturbation of the coefficients for which z would be exact -- and it is
    NOT a bound on the distance to a true root unless the conditioning below
    says the root is well separated.
    """
    coeff = np.asarray(coeff)
    z = np.asarray(z, dtype=complex)
    scale = np.zeros_like(np.abs(z)) + abs(coeff[0])
    for c in coeff[1:]:
        scale = scale * np.abs(z) + abs(c)
    val = np.abs(horner(coeff, z))
    return np.where(scale > 0, val / np.maximum(scale, 1e-300), val)


def conditioning(coeff, roots, rel_tol: float = 1e-6) -> dict:
    """Separation, derivative magnitude, and a Newton step, per root.

    A near-multiple root makes ``|p(z)|`` small over a whole neighbourhood, so
    the backward residual stops localising it. That is exactly the regime the
    turning-point reduction lives in, so it is measured rather than assumed
    away.
    """
    roots = np.asarray(roots, dtype=complex)
    n = roots.size
    sep = np.full(n, np.inf)
    for i in range(n):
        d = np.abs(roots[i] - np.delete(roots, i))
        sep[i] = float(d.min()) if d.size else np.inf
    scale = float(np.max(np.abs(roots))) if n else 1.0
    dp = np.abs(horner_derivative(coeff, roots))
    p = np.abs(horner(coeff, roots))
    newton = np.where(dp > 0, p / np.maximum(dp, 1e-300), np.inf)
    kind = np.where(sep <= rel_tol * max(scale, 1.0), CLUSTERED, SIMPLE)
    kind = np.where(sep == 0.0, MULTIPLE, kind)
    return {"separation": sep.tolist(),
            "min_separation": float(sep.min()) if n else None,
            "derivative_magnitude": dp.tolist(),
            "newton_step": newton.tolist(),
            "max_newton_step": float(np.max(newton)) if n else None,
            "kind": kind.tolist(),
            "residual_is_a_root_location_bound": False}


def reduced_product(roots, index: int, r, rel_tol: float = 1e-6):
    """R(r) / (r - roots[index]) with the excluded root chosen BY INDEX.

    Raises rather than returning a number when the named root is not simple:
    the limit at the turn is the product over the other roots only when the
    factor being removed appears exactly once.
    """
    roots = np.asarray(roots, dtype=complex)
    if not (0 <= index < roots.size):
        raise RootCheckError(f"root index {index} is outside 0..{roots.size-1}")
    others = np.delete(roots, index)
    scale = float(np.max(np.abs(roots))) if roots.size else 1.0
    d = np.abs(others - roots[index])
    if d.size and float(d.min()) <= rel_tol * max(scale, 1.0):
        raise RootCheckError(
            f"root {index} is within {float(d.min()):.3e} of another root; "
            "the reduced product is not the analytic limit at a multiple or "
            "clustered turning point")
    r = np.asarray(r, dtype=complex)
    out = np.ones(r.shape, dtype=complex)
    for q in others:
        out = out * (r - q)
    return out


def identity_excluded_product(roots, turn: float, r):
    """The 031 form, kept so a test can show it vanishes at the turn."""
    roots = np.asarray(roots, dtype=complex)
    r = np.asarray(r, dtype=complex)
    keep = [q for q in roots if q is not turn]
    out = np.ones_like(r)
    for q in keep:
        out = out * (r - q)
    return out


def turning_index(roots, r_horizon: float, r_obs: float,
                  imag_tol: float = 1e-13) -> int | None:
    """Index of the outermost accessible exterior turning root, or None.

    ``pathdomain.classify_path`` returns the *value* ``max(ext)`` as a plain
    float, which is why an identity test can never match it. The index is
    what the reduction needs.
    """
    roots = np.asarray(roots, dtype=complex)
    ok = [i for i, q in enumerate(roots)
          if abs(q.imag) <= imag_tol and r_horizon < q.real < r_obs]
    if not ok:
        return None
    return int(max(ok, key=lambda i: roots[i].real))


def reduced_limit(roots, index: int, rel_tol: float = 1e-6) -> complex:
    """The analytic value of R(r)/(r - r_t) at r = r_t, by index exclusion.

    At a simple turning root this is the limit the integrand needs; the 031
    form returns zero there and the quadrature then samples a hole at the very
    endpoint where the integrand peaks.
    """
    roots = np.asarray(roots, dtype=complex)
    return complex(reduced_product(roots, index, roots[index], rel_tol))
