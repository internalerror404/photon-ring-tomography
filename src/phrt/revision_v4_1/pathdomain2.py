"""Hardened path-domain predicate. Version 2; version 1 stays frozen.

Ruling 031. The delivered finite results did not exercise every numerical
path, and two of the untested ones are unsafe:

* ``_J`` in version 1 substitutes a zero integrand wherever the radial
  potential or the reduced turning factor is not positive. At a genuinely
  invalid interior evaluation that silently deletes part of the integral
  instead of saying so. Here it raises an unresolved status.
* the version 1 comparator has no finiteness check, so on a capture path a
  NaN makes both comparisons false and falls through to a valid label. That
  is a control-flow hole, not an observed error in the delivered outcomes,
  and it is closed by testing finiteness before any comparison.

Two further labels are corrected. ``_tail`` is a truncated asymptotic
correction with a remainder, not an exact closed form. And fixed-order
Gaussian quadrature carries no a posteriori error estimate, so a panelled
value reports a convergence estimate from successive refinements rather than
an enclosure.

Nothing here changes the physics, the requested order, or the decision rule
of version 1. Where both versions resolve a case they must agree, and a
guard that fires on an archived case reports the point and its margin rather
than overwriting the old label.
"""
from __future__ import annotations

import numpy as np
from scipy.integrate import quad

from phrt.revision_v4_1.pathdomain import (CAPTURE, INSIDE_OBSERVER,  # noqa
                                           NO_ANNULUS_ON_PATH,
                                           NO_CROSSING_CAPTURE,
                                           NO_CROSSING_ESCAPE, OUTSIDE_ANNULUS,
                                           SCATTER, UNRESOLVED, VALID,
                                           classify_path, radial_potential)


class DomainUnresolved(RuntimeError):
    """An integral could not be formed; the caller must not substitute zero."""


def integral(a: float, b: float, roots, turn=None, limit: int = 200):
    """dr/sqrt(R) from a to b, refusing to silently drop an invalid piece."""
    if not (np.isfinite(a) and np.isfinite(b)):
        raise DomainUnresolved("non-finite integration endpoint")
    if b < a:
        raise DomainUnresolved(f"misordered endpoints {a!r} > {b!r}")
    if b == a:
        return 0.0, 0.0
    bad = {"n": 0}

    if turn is not None and abs(a - turn) < 1e-12:
        def f(u):
            r = turn + u * u
            # the reduced product is the analytic limit of R/(r - turn) at a
            # simple turn, so u = 0 is a value rather than a 0/0 floor
            red = np.prod([r - q for q in roots if q is not turn])
            red = radial_potential(r, roots) / (r - turn) if u != 0 else red
            red = np.real(red)
            if not np.isfinite(red) or red <= 0:
                bad["n"] += 1
                return 0.0
            return 2.0 / np.sqrt(red)
        v, e = quad(f, 0.0, np.sqrt(b - turn), limit=limit)
    else:
        def g(r):
            q = radial_potential(r, roots)
            if not np.isfinite(q) or q <= 0:
                bad["n"] += 1
                return 0.0
            return 1.0 / np.sqrt(q)
        v, e = quad(g, a, b, limit=limit)
    if bad["n"]:
        raise DomainUnresolved(
            f"the radial potential was not positive at {bad['n']} interior "
            "evaluations; the integral is not defined on this interval")
    if not (np.isfinite(v) and np.isfinite(e)):
        raise DomainUnresolved("the quadrature returned a non-finite value")
    if v < 0:
        raise DomainUnresolved("a negative Mino parameter is not physical")
    return float(v), float(e)


def tail(L: float, roots) -> tuple[float, float]:
    """Truncated asymptotic Mino parameter from L to infinity, with remainder.

    R = r^4 - S1 r^3 + S2 r^2 - ..., so 1/sqrt(R) = r^-2 (1 + S1/(2r) + ...)
    and the two retained terms are 1/L and S1/(4 L^2). The next term is
    O(L^-3); its coefficient is bounded here by the symmetric functions, and
    the value is returned with that bound rather than as a closed form.
    """
    S1 = float(np.real(np.sum(roots)))
    S2 = float(np.real(sum(roots[i] * roots[j] for i in range(len(roots))
                           for j in range(i + 1, len(roots)))))
    v = 1.0 / L + S1 / (4.0 * L * L)
    rem = abs(3.0 * S1 * S1 / 8.0 - S2 / 2.0) / (3.0 * L ** 3) + 1.0 / L ** 4
    return v, rem


def panelled(a: float, b: float, roots, turn=None, n: int = 64,
             panels: int = 64) -> tuple[float, float]:
    """The reference integral, with a convergence estimate, not an enclosure.

    Fixed-order Gauss-Legendre gives no a posteriori error, so the value is
    computed at ``panels`` and ``2*panels`` and their difference reported as
    a convergence estimate. A synthetic endpoint-peaked integral shows why
    this matters: 64 graded panels are exact to 2.5e-10 at delta = 1e-8 and
    still wrong by 2.4e-5 at delta = 1e-12.
    """
    def once(p):
        if b < a:
            raise DomainUnresolved("misordered endpoints")
        if b == a:
            return 0.0
        x, w = np.polynomial.legendre.leggauss(n)
        if turn is not None and abs(a - turn) < 1e-12:
            edges = np.sqrt(np.linspace(0.0, b - turn, p + 1))
            tot = 0.0
            for lo, hi in zip(edges[:-1], edges[1:]):
                u = 0.5 * (hi - lo) * (x + 1) + lo
                r = turn + u * u
                q = radial_potential(r, roots) / (r - turn)
                if np.any(~np.isfinite(q)) or np.any(q <= 0):
                    raise DomainUnresolved("reduced potential not positive")
                tot += float(np.sum(0.5 * (hi - lo) * w * 2.0 / np.sqrt(q)))
            return tot
        edges = a + (b - a) * np.linspace(0.0, 1.0, p + 1) ** 3
        tot = 0.0
        for lo, hi in zip(edges[:-1], edges[1:]):
            if hi <= lo:
                continue
            u = 0.5 * (hi - lo) * (x + 1) + lo
            q = radial_potential(u, roots)
            if np.any(~np.isfinite(q)) or np.any(q <= 0):
                raise DomainUnresolved("radial potential not positive")
            tot += float(np.sum(0.5 * (hi - lo) * w / np.sqrt(q)))
        return tot
    v1, v2 = once(panels), once(2 * panels)
    if not (np.isfinite(v1) and np.isfinite(v2)):
        raise DomainUnresolved("the reference quadrature is not finite")
    return v2, abs(v2 - v1)


def adjudicate(roots, s_n: float, r_horizon: float, r_obs: float,
               r_outer: float = 50.0, margin_factor: float = 10.0,
               reference: bool = False) -> dict:
    """Where the requested crossing falls, with every margin made explicit."""
    kind, turn = classify_path(roots, r_horizon, r_obs)
    out = {"path": kind, "turn": turn, "s_n": float(s_n),
           "method": "panelled_reference" if reference else "adaptive_primary"}
    if not np.isfinite(s_n):
        return {**out, "code": UNRESOLVED, "why": "s_n is not finite"}
    if s_n < 0:
        return {**out, "code": UNRESOLVED,
                "why": "a negative Mino parameter is not physical"}
    if kind == INSIDE_OBSERVER:
        return {**out, "code": UNRESOLVED,
                "why": "a real root lies at or beyond the observer radius"}
    f = (lambda *a, **k: panelled(*a, **k)) if reference else integral
    try:
        if kind == CAPTURE:
            sH, eH = f(r_horizon, r_obs, roots)
            s50, e50 = f(r_outer, r_obs, roots)
            if not all(np.isfinite(x) for x in (sH, s50, eH, e50)):
                raise DomainUnresolved("non-finite capture endpoints")
            m = margin_factor * max(eH, e50, 1e-15)
            out.update({"s_horizon": sH, "s_50": s50,
                        "error_estimate": max(eH, e50), "margin": m,
                        "margin_G_theta_minus_s50": s_n - s50,
                        "margin_sH_minus_G_theta": sH - s_n})
            if abs(s_n - sH) <= m or abs(s_n - s50) <= m:
                return {**out, "code": UNRESOLVED,
                        "why": "within the margin of a capture endpoint"}
            if s_n >= sH:
                return {**out, "code": NO_CROSSING_CAPTURE}
            if s_n < s50:
                return {**out, "code": OUTSIDE_ANNULUS}
            return {**out, "code": VALID}
        Jo, eo = f(turn, r_obs, roots, turn=turn)
        if turn >= r_outer:
            return {**out, "code": NO_ANNULUS_ON_PATH, "J_observer": Jo,
                    "error_estimate": eo}
        J50, e50 = f(turn, r_outer, roots, turn=turn)
        Ji, ei = f(turn, 1e7, roots, turn=turn)
        tv, trem = tail(1e7, roots)
        esc = Jo + Ji + tv
        m = margin_factor * max(eo, e50, ei, trem, 1e-15)
        out.update({"J_observer": Jo, "J_50": J50, "s_escape": esc,
                    "tail": tv, "tail_remainder": trem,
                    "error_estimate": max(eo, e50, ei), "margin": m,
                    "margin_G_theta_minus_lower": s_n - (Jo - J50),
                    "margin_upper_minus_G_theta": (Jo + J50) - s_n})
        if not np.isfinite(esc):
            raise DomainUnresolved("non-finite escape parameter")
        if abs(s_n - (Jo - J50)) <= m or abs(s_n - (Jo + J50)) <= m \
                or abs(s_n - esc) <= m:
            return {**out, "code": UNRESOLVED,
                    "why": "within the margin of an annulus or escape "
                           "endpoint"}
        if s_n > esc:
            return {**out, "code": NO_CROSSING_ESCAPE}
        if Jo - J50 < s_n < Jo + J50:
            return {**out, "code": VALID}
        return {**out, "code": OUTSIDE_ANNULUS}
    except DomainUnresolved as exc:
        return {**out, "code": UNRESOLVED, "why": str(exc)}
