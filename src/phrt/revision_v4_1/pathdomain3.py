"""Comparator version 3: indexed reduction and retained evidence. Ruling 033.

Versions 1 and 2 stay frozen; this is a separate implementation, and where all
three resolve a case they must agree.

Two source-level changes, both named in ruling 032 and authorised in 033.

*The turning root is excluded by index, not by object identity.* Version 2
formed the reduced potential as

    red = prod(r - q for q in roots if q is not turn)      # keeps every factor
    red = R(r) / (r - turn) if u != 0 else red

``classify_path`` returns ``max(ext)``, a plain float built from ``q.real``, so
``q is not turn`` is true for every element of the array and the first line
keeps the factor it meant to drop. The second line then divides it out again,
which is why the defect is latent rather than loud in the adaptive path: the
quadrature never samples ``u = 0``. Here the reduced potential is the product
over the other roots, chosen by the verified index -- defined at the turning
point, with no division anywhere.

*The division is removed, not merely guarded.* Forming ``r = turn + u*u`` loses
``r - turn`` to cancellation once ``u*u`` falls below ``eps * turn``: for
``turn ~ 34`` that is ``u < 2.4e-8``, where ``r - turn`` evaluates to exactly
zero and ``R(r)/(r - turn)`` becomes 0/0. Version 2 substitutes a zero
integrand there and the graded reference raises. The product form has no such
point.

Everything the decision rests on is returned, not summarised: the integral
values, their error estimates, the endpoint limit at the turn, the backward
residual and conditioning of every root against the ORIGINAL quartic built
from the conserved quantities, the decision margins, and -- when the answer is
withheld -- the reason it was withheld. An ambiguous case is refused. It is
never resolved in the direction that happens to match the archived mask.
"""
from __future__ import annotations

import numpy as np
from scipy.integrate import quad

from phrt.revision_v4_1 import rootcheck as RC
from phrt.revision_v4_1.pathdomain import (CAPTURE, INSIDE_OBSERVER,  # noqa
                                           NO_ANNULUS_ON_PATH,
                                           NO_CROSSING_CAPTURE,
                                           NO_CROSSING_ESCAPE, OUTSIDE_ANNULUS,
                                           SCATTER, UNRESOLVED, VALID,
                                           radial_potential)
from phrt.revision_v4_1.pathdomain2 import DomainUnresolved, tail

VERSION = "PATHDOMAIN_V3_INDEXED_REDUCTION"

# Numerical policy. Frozen before any query; changing any of it is a new
# comparator, not a tuning of this one.
POLICY = {
    "version": VERSION,
    "imag_tol_for_a_real_root": 1e-13,
    "cluster_rel_tol_for_the_turning_root": 1e-6,
    "max_backward_residual_of_the_original_quartic": 1e-10,
    "adaptive_quad_limit": 200,
    "adaptive_quad_epsabs": 1e-12,
    "adaptive_quad_epsrel": 1e-12,
    "far_radius_for_the_escape_tail": 1e7,
    "margin_factor": 10.0,
    "reduced_potential": "index_excluded_product_no_division",
    "ambiguous_cases": "refused_not_resolved_toward_the_archived_mask",
}


def root_report(roots, lam: float, eta: float, spin: float) -> dict:
    """The original quartic, evaluated at the roots the tracer returned.

    The coefficients come from the conserved quantities, so this is a check on
    the roots rather than a polynomial manufactured from them. A small
    backward residual is reported as a backward residual; it bounds where the
    root is only when the conditioning below says the root is well separated.
    """
    coeff = RC.quartic_coefficients(spin, lam, eta).ravel()
    res = RC.backward_residual(coeff, roots)
    cond = RC.conditioning(coeff, roots,
                           POLICY["cluster_rel_tol_for_the_turning_root"])
    return {"coefficients": [float(c) for c in coeff],
            "lam": float(lam), "eta": float(eta),
            "backward_residual": [float(x) for x in np.atleast_1d(res)],
            "max_backward_residual": float(np.max(res)),
            "min_separation": cond["min_separation"],
            "max_newton_step": cond["max_newton_step"],
            "kind": cond["kind"],
            "residual_is_a_root_location_bound": False}


def turning_index(roots, r_horizon: float, r_obs: float) -> int | None:
    return RC.turning_index(roots, r_horizon, r_obs,
                            POLICY["imag_tol_for_a_real_root"])


def classify(roots, r_horizon: float, r_obs: float):
    """As version 1, but returning the turning root's INDEX as well."""
    idx = turning_index(roots, r_horizon, r_obs)
    if idx is not None:
        return SCATTER, idx
    real = [q.real for q in roots
            if abs(q.imag) <= POLICY["imag_tol_for_a_real_root"]]
    if any(x >= r_obs for x in real):
        return INSIDE_OBSERVER, None
    return CAPTURE, None


def _reduced(r, roots, index: int):
    """R(r) / (r - r_index) as a product over the other roots."""
    return np.real(RC.reduced_product(
        roots, index, r, POLICY["cluster_rel_tol_for_the_turning_root"]))


def integral(a: float, b: float, roots, index: int | None = None) -> tuple:
    """dr/sqrt(R) from a to b, refusing to drop an invalid piece silently."""
    if not (np.isfinite(a) and np.isfinite(b)):
        raise DomainUnresolved("non-finite integration endpoint")
    if b < a:
        raise DomainUnresolved(f"misordered endpoints {a!r} > {b!r}")
    if b == a:
        return 0.0, 0.0
    bad = {"n": 0, "why": ""}
    lim = POLICY["adaptive_quad_limit"]
    kw = dict(limit=lim, epsabs=POLICY["adaptive_quad_epsabs"],
              epsrel=POLICY["adaptive_quad_epsrel"])
    if index is not None:
        turn = float(np.real(roots[index]))
        if abs(a - turn) > 1e-12:
            raise DomainUnresolved(
                "the reduced form is only valid from the turning point")

        def f(u):
            red = _reduced(turn + u * u, roots, index)
            if not np.isfinite(red) or red <= 0:
                bad["n"] += 1
                bad["why"] = "the reduced potential is not positive"
                return 0.0
            return 2.0 / np.sqrt(red)

        v, e = quad(f, 0.0, np.sqrt(max(b - turn, 0.0)), **kw)
    else:
        def g(r):
            q = radial_potential(r, roots)
            if not np.isfinite(q) or q <= 0:
                bad["n"] += 1
                bad["why"] = "the radial potential is not positive"
                return 0.0
            return 1.0 / np.sqrt(q)

        v, e = quad(g, a, b, **kw)
    if bad["n"]:
        raise DomainUnresolved(
            f"{bad['why']} at {bad['n']} interior evaluations; the integral "
            "is not defined on this interval")
    if not (np.isfinite(v) and np.isfinite(e)):
        raise DomainUnresolved("the quadrature returned a non-finite value")
    return float(v), float(e)


def endpoint_limit(roots, index: int) -> float:
    """The analytic value of R(r)/(r - r_t) at the turn, by index exclusion."""
    return float(np.real(RC.reduced_limit(
        roots, index, POLICY["cluster_rel_tol_for_the_turning_root"])))


def adjudicate(roots, s_n: float, r_horizon: float, r_obs: float,
               r_outer: float = 50.0, *, lam: float | None = None,
               eta: float | None = None, spin: float = 0.5) -> dict:
    """Where the requested crossing falls, with all of its evidence."""
    roots = np.asarray(roots, dtype=complex)
    out: dict = {"comparator": VERSION, "s_n": float(s_n),
                 "policy_margin_factor": POLICY["margin_factor"]}
    if lam is not None and eta is not None:
        rep = root_report(roots, lam, eta, spin)
        out["roots"] = rep
        if rep["max_backward_residual"] > \
                POLICY["max_backward_residual_of_the_original_quartic"]:
            return {**out, "code": UNRESOLVED,
                    "why": ("the returned roots do not solve the original "
                            f"quartic: backward residual "
                            f"{rep['max_backward_residual']:.3e}")}
    kind, index = classify(roots, r_horizon, r_obs)
    out["path"] = kind
    out["turning_index"] = index
    out["turn"] = None if index is None else float(np.real(roots[index]))
    if not np.isfinite(s_n):
        return {**out, "code": UNRESOLVED, "why": "s_n is not finite"}
    if s_n < 0:
        return {**out, "code": UNRESOLVED,
                "why": "a negative Mino parameter is not physical"}
    if kind == INSIDE_OBSERVER:
        return {**out, "code": UNRESOLVED,
                "why": "a real root lies at or beyond the observer radius"}
    try:
        if kind == CAPTURE:
            sH, eH = integral(r_horizon, r_obs, roots)
            s50, e50 = integral(r_outer, r_obs, roots)
            err = max(eH, e50)
            m = POLICY["margin_factor"] * max(err, 1e-15)
            out.update({"s_horizon": sH, "s_50": s50, "error_estimate": err,
                        "margin": m, "margin_s_n_minus_s50": s_n - s50,
                        "margin_sH_minus_s_n": sH - s_n})
            if abs(s_n - sH) <= m or abs(s_n - s50) <= m:
                return {**out, "code": UNRESOLVED,
                        "why": "within the margin of a capture endpoint"}
            if s_n >= sH:
                return {**out, "code": NO_CROSSING_CAPTURE}
            if s_n < s50:
                return {**out, "code": OUTSIDE_ANNULUS}
            return {**out, "code": VALID}

        turn = float(np.real(roots[index]))
        out["endpoint_limit_at_the_turn"] = endpoint_limit(roots, index)
        Jo, eo = integral(turn, r_obs, roots, index)
        if turn >= r_outer:
            return {**out, "code": NO_ANNULUS_ON_PATH, "J_observer": Jo,
                    "error_estimate": eo}
        J50, e50 = integral(turn, r_outer, roots, index)
        Ji, ei = integral(turn, POLICY["far_radius_for_the_escape_tail"],
                          roots, index)
        tv, trem = tail(POLICY["far_radius_for_the_escape_tail"], roots)
        esc = Jo + Ji + tv
        err = max(eo, e50, ei)
        m = POLICY["margin_factor"] * max(err, trem, 1e-15)
        out.update({"J_observer": Jo, "J_50": J50, "s_escape": esc,
                    "tail": tv, "tail_remainder": trem,
                    "error_estimate": err, "margin": m,
                    "margin_s_n_minus_lower": s_n - (Jo - J50),
                    "margin_upper_minus_s_n": (Jo + J50) - s_n,
                    "margin_escape_minus_s_n": esc - s_n})
        if not np.isfinite(esc):
            raise DomainUnresolved("non-finite escape parameter")
        if abs(s_n - (Jo - J50)) <= m or abs(s_n - (Jo + J50)) <= m \
                or abs(s_n - esc) <= m:
            return {**out, "code": UNRESOLVED,
                    "why": "within the margin of an annulus or escape endpoint"}
        if s_n > esc:
            return {**out, "code": NO_CROSSING_ESCAPE}
        if Jo - J50 < s_n < Jo + J50:
            return {**out, "code": VALID}
        return {**out, "code": OUTSIDE_ANNULUS}
    except (DomainUnresolved, RC.RootCheckError) as exc:
        return {**out, "code": UNRESOLVED, "why": str(exc),
                "reason_class": type(exc).__name__}
