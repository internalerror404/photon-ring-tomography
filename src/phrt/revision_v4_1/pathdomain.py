"""Does the requested exterior equatorial crossing exist on this ray at all?

Ruling 030. The archived NaN says only that the library's final mask fired.
It does not say whether the analytic transfer expression failed to represent
an event that exists, or was evaluated for an event the physical ray never
reaches -- AART's own equation (32) restricts each crossing to the ray's
Mino-time interval, and its section II.4 says the expression can return a
radius, of either sign, for a crossing that does not happen.

So the question is asked in order, and only the third part uses the source
model:

    identify the observer-connected radial path
      -> verify the requested crossing exists on it
        -> test whether it lies in the emitting annulus

``s`` increases backward along the ray from ``s = 0`` at the observer. It is
a Mino parameter: not coordinate time and not retarded age. The requested
crossing sits at ``s_n = G_theta`` for the order, the same angular quantity
the pinned evaluator already forms, so the two normalisations match by
construction rather than by assertion.

Nothing here switches expressions, forces a sign, or changes the requested
order. A case whose endpoints cannot be separated to better than the
integration error is returned unresolved rather than rounded into a boolean.
"""
from __future__ import annotations

import numpy as np
from scipy.integrate import quad

VALID = "VALID_EMITTING_EVENT"
OUTSIDE_ANNULUS = "EXTERIOR_EVENT_OUTSIDE_SOURCE_ANNULUS"
NO_CROSSING_CAPTURE = "NO_NTH_EXTERIOR_CROSSING_CAPTURE"
NO_CROSSING_ESCAPE = "NO_NTH_EXTERIOR_CROSSING_ESCAPE"
NO_ANNULUS_ON_PATH = "NO_ANNULUS_INTERSECTION_ON_PATH"
UNRESOLVED = "DOMAIN_UNRESOLVED"
VALID_BUT_UNRESOLVED = "VALID_EVENT_NUMERICALLY_UNRESOLVED"
CODES = (VALID, OUTSIDE_ANNULUS, NO_CROSSING_CAPTURE, NO_CROSSING_ESCAPE,
         NO_ANNULUS_ON_PATH, UNRESOLVED, VALID_BUT_UNRESOLVED)

CAPTURE = "CAPTURE_NO_ACCESSIBLE_EXTERIOR_TURN"
SCATTER = "SCATTER_WITH_EXTERIOR_TURN"
INSIDE_OBSERVER = "TURN_OUTSIDE_OBSERVER_RADIUS"


def radial_potential(r, roots):
    """R(r) as the product over the quartic's roots, real part taken last."""
    r = np.asarray(r, float)
    out = np.ones_like(r, dtype=complex)
    for q in roots:
        out = out * (r - q)
    return out.real


def classify_path(roots, r_horizon: float, r_obs: float, imag_tol=1e-13):
    """Is there an accessible exterior turning point on the observer's branch?

    A nearly real outer root is not enough. It has to be real, outside the
    horizon and inside the observer, or the ray reaches the horizon without
    turning -- the four-real-root case with every root inside the horizon is
    a capture, not a scattering.
    """
    real = [q.real for q in roots if abs(q.imag) <= imag_tol]
    ext = [x for x in real if r_horizon < x < r_obs]
    if not ext:
        if any(x >= r_obs for x in real):
            return INSIDE_OBSERVER, None
        return CAPTURE, None
    return SCATTER, max(ext)


def _tail(L: float, roots) -> float:
    """The Mino parameter from L out to infinity, in closed form.

    R(r) = r^4 - S1 r^3 + ..., so 1/sqrt(R) -> r^-2 (1 + S1/(2r)) and the
    remaining integral is 1/L + S1/(4 L^2). Truncating the quadrature at a
    large radius instead leaves exactly this much out, which is 1e-7 at
    L = 1e7 and is the whole discrepancy against an escape time quoted to
    eight figures.
    """
    S1 = float(np.real(np.sum(roots)))
    return 1.0 / L + S1 / (4.0 * L * L)


def escape_mino(turn, roots, r_far: float = 1e7) -> tuple[float, float]:
    """Mino parameter from the turning point out to infinity."""
    v, e = _J(turn, r_far, roots, turn=turn)
    return v + _tail(r_far, roots), e


def _J(a, b, roots, turn=None, limit=200):
    """Integral of dr/sqrt(R) from a to b, regularised at a simple turn.

    Near an accessible turning point the integrand has an inverse square-root
    singularity, so the substitution r = turn + u^2 removes it exactly rather
    than asking the quadrature to survive it.
    """
    if b <= a:
        return 0.0, 0.0
    if turn is not None and abs(a - turn) < 1e-12:
        def f(u):
            r = turn + u * u
            q = radial_potential(r, roots)
            other = q / (r - turn) if r != turn else np.nan
            return 2.0 / np.sqrt(other) if other > 0 else 0.0
        v, e = quad(f, 0.0, np.sqrt(b - turn), limit=limit)
        return float(v), float(e)

    def g(r):
        q = radial_potential(r, roots)
        return 1.0 / np.sqrt(q) if q > 0 else 0.0
    v, e = quad(g, a, b, limit=limit)
    return float(v), float(e)


def adjudicate(roots, s_n: float, r_horizon: float, r_obs: float,
               r_outer: float = 50.0, margin_factor: float = 10.0) -> dict:
    """Where the requested crossing falls on this ray's own radial path."""
    kind, turn = classify_path(roots, r_horizon, r_obs)
    out = {"path": kind, "turn": turn, "s_n": float(s_n)}
    if not np.isfinite(s_n):
        return {**out, "code": UNRESOLVED, "why": "the angular crossing "
                "parameter is not finite"}
    if kind == INSIDE_OBSERVER:
        return {**out, "code": UNRESOLVED,
                "why": "a real root lies at or beyond the observer radius; "
                       "the observer-connected branch is not established"}
    if kind == CAPTURE:
        sH, eH = _J(r_horizon, r_obs, roots)
        s50, e50 = _J(r_outer, r_obs, roots)
        m = margin_factor * max(eH, e50, 1e-15)
        out.update({"s_horizon": sH, "s_50": s50, "quad_error": max(eH, e50),
                    "margin": m})
        if abs(s_n - sH) <= m or abs(s_n - s50) <= m:
            return {**out, "code": UNRESOLVED,
                    "why": "the crossing sits within the integration margin "
                           "of an endpoint"}
        if s_n >= sH:
            return {**out, "code": NO_CROSSING_CAPTURE,
                    "why": "the requested crossing would occur after the ray "
                           "reaches the horizon"}
        if s_n < s50:
            return {**out, "code": OUTSIDE_ANNULUS,
                    "why": "the crossing happens outside the emitting "
                           "annulus"}
        return {**out, "code": VALID}
    # scattering
    Jo, eo = _J(turn, r_obs, roots, turn=turn)
    out.update({"J_observer": Jo})
    if turn >= r_outer:
        return {**out, "code": NO_ANNULUS_ON_PATH, "quad_error": eo,
                "margin": margin_factor * eo,
                "why": "the turning point lies outside the emitting annulus, "
                       "so the path never enters it"}
    J50, e50 = _J(turn, r_outer, roots, turn=turn)
    lo, hi = Jo - J50, Jo + J50
    Jinf, einf = escape_mino(turn, roots)
    m = margin_factor * max(eo, e50, einf, 1e-15)
    out.update({"J_50": J50, "s_in": lo, "s_out": hi, "s_escape": Jo + Jinf,
                "quad_error": max(eo, e50, einf), "margin": m})
    if abs(s_n - lo) <= m or abs(s_n - hi) <= m:
        return {**out, "code": UNRESOLVED,
                "why": "the crossing sits within the integration margin of "
                       "an annulus endpoint"}
    if s_n > Jo + Jinf + m:
        return {**out, "code": NO_CROSSING_ESCAPE,
                "why": "the requested crossing would occur after the ray has "
                       "escaped"}
    if lo < s_n < hi:
        return {**out, "code": VALID}
    return {**out, "code": OUTSIDE_ANNULUS,
            "why": "the crossing happens on the path but outside the "
                   "emitting annulus"}
