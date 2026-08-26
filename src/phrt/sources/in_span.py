"""Truths that are exactly in the declared class, and the check that they are.

R0_REPAIR_AMENDMENT_004. The pilot's "in-class" bank was not in class. Every
family was rendered analytically at roughly the class's resolvable scale, so the
exact least-squares projection onto C224 still left a structure-normalized
residual of 0.41 to 0.43 and the structure-normalized stable span of the class
itself was zero. An experiment run on that bank measures basis mismatch and
reconstruction quality together and cannot separate them.

The repair is to make membership a property of the truth rather than a hope
about its parameters. An in-span truth is *defined* as ``Q_C x``: sample an
analytic family, project it into the class, keep the coefficient vector, and
treat the synthesised movie as the truth. It is then in span at every
coordinate, not merely on the grid it was projected on, because the basis
evaluates everywhere.

Positivity survives the projection because a constant is itself in the class:
the projection of the unit function has a relative residual of order 1e-15 on
this basis, so a negative excursion can be lifted by adding a multiple of that
coefficient vector without leaving the span. The lift is recorded, and both the
positivity and the structure companion are still checked afterwards.
"""
from __future__ import annotations

import numpy as np

from phrt.sources.movie import Movie

# The residual the amendment requires of an in-span truth.
IN_SPAN_TOLERANCE = 1e-10


def constant_coefficients(design: np.ndarray) -> tuple[np.ndarray, float]:
    """Coefficients of the unit function, and how well the class holds it."""
    ones = np.ones(design.shape[0])
    c, *_ = np.linalg.lstsq(design, ones, rcond=None)
    resid = float(np.linalg.norm(design @ c - ones)
                  / max(1.0, float(np.linalg.norm(ones))))
    return c, resid


def project_to_class(values: np.ndarray, design: np.ndarray,
                     const_coef: np.ndarray,
                     min_intensity: float = 1e-6) -> dict:
    """Project one rendered movie into the class and restore positivity.

    Returns the coefficient vector, the synthesised values, the lift applied and
    the relative distance from the analytic parent -- which is not an error but
    a measurement of how much of that family the class can hold.
    """
    values = np.asarray(values, float)
    coef, *_ = np.linalg.lstsq(design, values, rcond=None)
    projected = design @ coef
    denom = max(1.0, float(np.linalg.norm(values)))
    distance = float(np.linalg.norm(values - projected) / denom)
    fluct = max(float(np.linalg.norm(values - values.mean())), 1e-300)
    distance_structure = float(np.linalg.norm(values - projected) / fluct)
    lo = float(projected.min())
    lift = 0.0
    if lo < min_intensity:
        lift = float(min_intensity - lo)
        coef = coef + lift * const_coef
        projected = design @ coef
    return {"coefficients": coef, "values": projected, "lift_applied": lift,
            "distance_from_analytic_parent": distance,
            "distance_from_analytic_parent_structure": distance_structure,
            "min_intensity": float(projected.min())}


def in_span_movie(parent: Movie, basis, rq, pq, tq, const_coef: np.ndarray,
                  min_intensity: float = 1e-6) -> Movie:
    """An exactly-in-class truth derived from an analytic parent.

    The parent's family and parameters are carried through so the regime axis
    and the family axis stay independent: the same physical family appears in
    both the in-span and the off-grid regime, which is the whole point of
    separating representation mismatch from family shift.
    """
    p = project_to_class(parent(rq, pq, tq), basis.design(rq, pq, tq),
                         const_coef, min_intensity)
    coef = p["coefficients"]

    def render(r, phi, t, _c=coef, _b=basis):
        return _b.design(np.asarray(r, float), np.asarray(phi, float),
                         np.asarray(t, float)) @ _c

    return Movie(
        family=parent.family,
        params={**parent.params, "in_span": True,
                "lift_applied": p["lift_applied"]},
        render=render, split=parent.split, off_grid=False,
        extra={"coefficients": coef,
               "in_span": True,
               "parent_content_hash": parent.content_hash,
               "distance_from_analytic_parent":
                   p["distance_from_analytic_parent"],
               "distance_from_analytic_parent_structure":
                   p["distance_from_analytic_parent_structure"],
               "lift_applied": p["lift_applied"],
               "min_intensity": p["min_intensity"]})


def in_span_residual(movie: Movie, design: np.ndarray, rq, pq, tq) -> float:
    """The amendment's gate quantity, measured rather than assumed.

    ``|| j_truth - Q_C x_truth || / max(1, || j_truth ||)`` where ``x_truth`` is
    the coefficient vector the truth carries. For a truth built by projection
    this is zero to rounding; it is measured anyway, because the alternative is
    trusting a construction that a later edit could quietly break.
    """
    j = movie(rq, pq, tq)
    coef = movie.extra.get("coefficients")
    if coef is None:
        coef, *_ = np.linalg.lstsq(design, j, rcond=None)
    return float(np.linalg.norm(j - design @ coef)
                 / max(1.0, float(np.linalg.norm(j))))
