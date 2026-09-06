"""Refining the lensing-band boundary itself, and measuring how much it moves.

Ruling 027. A finer polygon is only a finer boundary if its new vertices come
from solving the defining equations at new parameter locations; inserting
points along an existing straight edge changes the file and not the geometry.
So the ladder here re-runs AART's own root solves -- ``ApparentBH`` for the
direct-order inner boundary and ``nlayers`` for the photon-ring boundaries --
at more arclength marks on the critical curve, through the pinned generator's
own conventions.

Every archived hull in this campaign is star-shaped about the origin, which
their vertex angles are checked for rather than assumed. That makes the areas
this module needs exact from a radial representation: over an angular interval
where the boundary is a single straight segment, the swept area is the
triangle from the origin, so a sample set that contains every vertex angle
integrates the polygon exactly. What remains is the handful of angles where
two radius functions cross, and that residual is measured by refining the
angular sample rather than assumed small.
"""
from __future__ import annotations

import numpy as np
from scipy import optimize

TWO_PI = 2.0 * np.pi
SOLVES_PER_DIRECTION = 5      # 1 apparent horizon + 2 per photon-ring order


def critical_marks(spin: float, inc_deg: float, n_marks: int
                   ) -> tuple[np.ndarray, np.ndarray, dict]:
    """``n_marks`` arclength-equispaced points on the upper critical curve."""
    import aart.lensingbands as lbm
    a, b = lbm.CritCurve(spin, inc_deg)
    ma, mb = lbm.spacedmarks(a, b, n_marks)
    return ma, mb, {"n_marks": int(n_marks), "source": "aart.lensingbands."
                    "CritCurve + spacedmarks", "half_step_shift": False}


def shifted_marks(spin: float, inc_deg: float, n_marks: int
                  ) -> tuple[np.ndarray, np.ndarray, dict]:
    """The same curve sampled half a step along, with the endpoints kept.

    An independent check has to move the sample locations, not relabel them:
    resampling the same polygon would agree with itself perfectly and prove
    nothing about the boundary.
    """
    import aart.lensingbands as lbm
    from scipy.integrate import cumulative_trapezoid as cumtrapz
    x, y = lbm.CritCurve(spin, inc_deg)
    dydx = np.gradient(y, x[0], edge_order=2)
    dxdx = np.gradient(x, x[0], edge_order=2)
    arc = cumtrapz(np.sqrt(dydx ** 2 + dxdx ** 2), initial=0)
    s = np.linspace(0, arc.max(), n_marks)
    h = 0.5 * (s[1] - s[0])
    s = np.concatenate([[s[0]], s[1:-1] + h, [s[-1]]])
    mx = np.interp(s, arc, x)
    return mx, np.interp(mx, x, y), {
        "n_marks": int(n_marks), "half_step_shift": True,
        "endpoints_preserved": True,
        "source": "aart.lensingbands.CritCurve, arclength resampled"}


def solve_hulls(marks_a: np.ndarray, marks_b: np.ndarray, spin: float,
                inc_deg: float, limits: float, thetad: float = np.pi / 2,
                d_obs: float = 1000.0, xtol: float | None = None
                ) -> tuple[dict, dict]:
    """AART's own boundary equations, at whatever directions are handed in.

    A transcription of ``lensingbands.hulls`` with the sample count and the
    root tolerance opened up and every solve counted. The equations, the
    initial brackets, the smin/smax clamps and the limi/lime factors are the
    pinned generator's; nothing physical is substituted.
    """
    import aart.lensingbands as lbm
    thetao = inc_deg * np.pi / 180.0
    da = np.append(marks_a, marks_a[::-1])
    db = np.append(marks_b, -marks_b[::-1])
    n = da.size
    limi0, limi1, lime1, limi2, lime2 = 0.99, 0.999, 1.001, 0.9999, 1.001
    smin, smax = 0.5, 100.0
    opt = {} if xtol is None else {"options": {"xtol": xtol}}
    out = {k: np.zeros((n, 2)) for k in ("0i", "1i", "1e", "2i", "2e")}
    stats = {"solves": 0, "failures": 0, "clamped_smin": 0, "clamped_smax": 0}

    def root(fn, x0, args):
        stats["solves"] += 1
        r = optimize.root(fn, x0, args=args, **opt)
        if not r.success:
            stats["failures"] += 1
        return r

    for i in range(n):
        u = np.array([da[i], db[i]])
        if db[i] >= 0:
            m = root(lbm.ApparentBH, limi0,
                     (spin, thetao, da[i], db[i], 1, 1, d_obs))
        else:
            m = root(lbm.ApparentBH, limi0,
                     (spin, thetao, da[i], db[i], 0, -1, d_obs))
        out["0i"][i] = m.x[0] * u
        for order, (li, le) in ((1, (limi1, lime1)), (2, (limi2, lime2))):
            m1 = root(lbm.nlayers, li, (spin, thetao, thetad, da[i], db[i],
                                        order))
            m2 = root(lbm.nlayers, le, (spin, thetao, thetad, da[i], db[i],
                                        order))
            v1, v2 = m1.x[0], m2.x[0]
            if order == 1:
                if v1 < smin:
                    v1 = smin
                    stats["clamped_smin"] += 1
                if v2 > smax:
                    v2 = smax
                    stats["clamped_smax"] += 1
            out[f"{order}i"][i] = li * v1 * u
            out[f"{order}e"][i] = le * v2 * u
    out["0e"] = np.array([[-limits, -limits], [limits, -limits],
                          [limits, limits], [-limits, limits]], float)
    stats["directions"] = n
    stats["unique_vertices"] = {k: int(np.unique(v, axis=0).shape[0])
                                for k, v in out.items()}
    return out, stats


def star_check(poly: np.ndarray) -> dict:
    """Are the vertex angles monotone, so the polygon is star-shaped here?"""
    th = np.unwrap(np.arctan2(poly[:, 1], poly[:, 0]))
    d = np.diff(th)
    return {"monotone": bool(np.all(d > 0) or np.all(d < 0)),
            "sweep_over_2pi": float(abs(th[-1] - th[0]) / TWO_PI),
            "min_radius": float(np.hypot(poly[:, 0], poly[:, 1]).min())}


def star_radius(poly: np.ndarray, theta: np.ndarray) -> np.ndarray:
    """Boundary radius at each angle, exact on every straight segment."""
    th = np.arctan2(poly[:, 1], poly[:, 0]) % TWO_PI
    o = np.argsort(th)
    th, P = th[o], poly[o]
    # Angles are cyclic. Rebasing on the first vertex keeps the search
    # monotone and sends an angle below it to the wrapping segment rather
    # than to the first one -- which for the order-0 screen square meant a
    # ray at angle zero being tested against the top edge it never meets.
    base = th[0]
    ths = np.concatenate([th - base, [TWO_PI]])
    tt = (np.asarray(theta) - base) % TWO_PI
    n = P.shape[0]
    k = np.clip(np.searchsorted(ths, tt, "right") - 1, 0, n - 1)
    A, B = P[k], P[(k + 1) % n]
    ang = np.asarray(theta)
    ux, uy = np.cos(ang), np.sin(ang)
    d = B - A
    den = d[:, 0] * uy - d[:, 1] * ux
    num = A[:, 0] * d[:, 1] - A[:, 1] * d[:, 0]
    with np.errstate(divide="ignore", invalid="ignore"):
        r = num / np.where(np.abs(den) < 1e-300, np.nan, den)
    return np.abs(r)


def sample_angles(polys: list[np.ndarray], n_uniform: int) -> np.ndarray:
    """Every vertex angle, plus a uniform fill.

    Including the vertex angles is what makes the swept-area quadrature exact
    on the polygons themselves, so the only residual is at radius crossings.
    """
    v = [np.arctan2(p[:, 1], p[:, 0]) % TWO_PI for p in polys]
    v.append(np.linspace(0.0, TWO_PI, n_uniform, endpoint=False))
    t = np.unique(np.concatenate(v))
    return np.concatenate([t, t[:1] + TWO_PI])


def _swept(r0, r1, dth):
    """Area swept by a radius going r0 -> r1 across dth, to second order."""
    return 0.5 * dth * 0.5 * (r0 ** 2 + r1 ** 2)


def region_measures(outer: np.ndarray, inner: np.ndarray,
                    other_outer: np.ndarray, other_inner: np.ndarray,
                    n_uniform: int) -> dict:
    """Band areas, their intersection, and the two boundary disagreements."""
    t = sample_angles([outer, inner, other_outer, other_inner], n_uniform)
    dth = np.diff(t)
    rs = {k: star_radius(p, t) for k, p in
          (("oN", outer), ("iN", inner), ("oM", other_outer),
           ("iM", other_inner))}
    if any(np.isnan(v).any() for v in rs.values()):
        raise RuntimeError("a ray missed a boundary; the polygon is not "
                           "star-shaped about the origin")
    u = {k: v ** 2 for k, v in rs.items()}          # radial measure is r^2/2

    def area(lo, hi):
        g = np.clip(u[hi] - u[lo], 0.0, None)
        return float(np.sum(0.25 * dth * (g[:-1] + g[1:])))

    def sym(a, b):
        g = np.abs(u[a] - u[b])
        return float(np.sum(0.25 * dth * (g[:-1] + g[1:])))

    inter_hi = np.minimum(u["oN"], u["oM"])
    inter_lo = np.maximum(u["iN"], u["iM"])
    g = np.clip(inter_hi - inter_lo, 0.0, None)
    inter = float(np.sum(0.25 * dth * (g[:-1] + g[1:])))
    bN, bM = area("iN", "oN"), area("iM", "oM")
    return {"band_N": bN, "band_M": bM, "band_intersection": inter,
            "band_union": bN + bM - inter,
            "band_symmetric_difference": bN + bM - 2 * inter,
            "outer_symmetric_difference": sym("oN", "oM"),
            "inner_symmetric_difference": sym("iN", "iM"),
            "n_sample_angles": int(t.size)}
