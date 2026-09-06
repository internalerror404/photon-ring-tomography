"""Exact area of a simple polygon inside every cell of a tensor grid.

Ruling 027 authorizes fractional coverage, and fractional coverage is only
worth having if the fraction is exact. This computes

    coverage[i, j] = | P  intersect  [X_i, X_i+1] x [Y_j, Y_j+1] |

for a simple closed polygon P, with no rasterization, no sampling and no
tolerance -- the only error is floating point.

The method integrates the vertical slice length across each column. Along a
vertical line x = t the polygon cuts an even number of crossings, which pair
into inside intervals by the even-odd rule; the length of those intervals
inside a row is a *linear* function of t as long as three things do not
happen: no vertex is passed, no grid line in x is passed, and no crossing
passes a grid line in y. Making all three into breakpoints therefore makes
midpoint times width exact on every sub-interval, and exact for a vertical
edge and a repeated vertex too, which a vertex-value quadrature would not be.

Nothing here snaps, simplifies, convexifies or repairs a polygon. A band with
a hole is expressed as the difference of two coverages, so its hole survives.
"""
from __future__ import annotations

import numpy as np


class PolygonError(RuntimeError):
    pass


def signed_area(poly: np.ndarray) -> float:
    x, y = poly[:, 0], poly[:, 1]
    return 0.5 * float(np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y))


def is_simple(poly: np.ndarray) -> bool:
    """Do any two non-adjacent edges of the polygon cross?

    O(n^2) and deliberately so: it runs on hulls of a few thousand vertices,
    once, and a self-intersecting boundary would silently corrupt every area
    downstream.
    """
    n = poly.shape[0]
    p = poly
    q = np.roll(poly, -1, axis=0)
    r = q - p
    for i in range(n):
        j = np.arange(n)
        skip = (j == i) | (j == (i + 1) % n) | (j == (i - 1) % n)
        d = r[i, 0] * r[:, 1] - r[i, 1] * r[:, 0]
        pq = p - p[i]
        with np.errstate(divide="ignore", invalid="ignore"):
            t = (pq[:, 0] * r[:, 1] - pq[:, 1] * r[:, 0]) / d
            u = (pq[:, 0] * r[i, 1] - pq[:, 1] * r[i, 0]) / d
        hit = (~skip) & np.isfinite(t) & (t > 1e-12) & (t < 1 - 1e-12) \
            & (u > 1e-12) & (u < 1 - 1e-12)
        if hit.any():
            return False
    return True


def _crossings(px, py, qx, qy, t):
    """y of every edge crossing of the vertical line x = t.

    Half-open in x so a vertex shared by two edges is counted once and a
    vertical edge is counted zero times, which is what the even-odd rule
    needs to stay consistent.
    """
    lo = np.minimum(px, qx)
    hi = np.maximum(px, qx)
    m = (lo <= t) & (t < hi)
    if not m.any():
        return np.empty(0)
    a, b, c, d = px[m], py[m], qx[m], qy[m]
    return b + (t - a) * (d - b) / (c - a)


def grid_coverage(poly: np.ndarray, X: np.ndarray, Y: np.ndarray,
                  chunk: int = 4096) -> np.ndarray:
    """Exact |P intersect cell| for every cell of the grid X x Y."""
    if poly.ndim != 2 or poly.shape[1] != 2 or poly.shape[0] < 3:
        raise PolygonError("a polygon needs at least three (x, y) vertices")
    X = np.asarray(X, float)
    Y = np.asarray(Y, float)
    if np.any(np.diff(X) <= 0) or np.any(np.diff(Y) <= 0):
        raise PolygonError("grid edges must be strictly increasing")
    out = np.zeros((X.size - 1, Y.size - 1))

    px, py = poly[:, 0], poly[:, 1]
    qx, qy = np.roll(px, -1), np.roll(py, -1)

    # Breakpoints: vertices, grid lines in x, and every place the boundary
    # crosses a grid line in y.
    bp = [px, X]
    ylo, yhi = np.minimum(py, qy), np.maximum(py, qy)
    j0 = np.searchsorted(Y, ylo, "right")
    j1 = np.searchsorted(Y, yhi, "left")
    for k in np.flatnonzero((j1 > j0) & (qy != py)):
        yy = Y[j0[k]:j1[k]]
        bp.append(px[k] + (yy - py[k]) * (qx[k] - px[k]) / (qy[k] - py[k]))
    b = np.unique(np.concatenate(bp))
    b = b[(b >= X[0]) & (b <= X[-1])]
    if b.size < 2:
        return out
    mid = 0.5 * (b[:-1] + b[1:])
    wid = np.diff(b)
    keep = wid > 0
    mid, wid = mid[keep], wid[keep]
    col = np.clip(np.searchsorted(X, mid) - 1, 0, X.size - 2)

    for s in range(0, mid.size, chunk):
        for t, w, c in zip(mid[s:s + chunk], wid[s:s + chunk],
                           col[s:s + chunk]):
            ys = _crossings(px, py, qx, qy, t)
            if ys.size < 2:
                continue
            if ys.size % 2:
                raise PolygonError(
                    f"odd crossing count at x={t!r}; the polygon is not a "
                    "closed simple curve")
            ys.sort()
            lo, hi = ys[0::2], ys[1::2]
            m = (np.clip(Y[:, None] - lo[None, :], 0.0, None)
                 - np.clip(Y[:, None] - hi[None, :], 0.0, None)).sum(1)
            out[c] += w * np.diff(m)
    return out


def polygon_rect_area(poly: np.ndarray, x0: float, x1: float, y0: float,
                      y1: float) -> float:
    """|P intersect one rectangle|, the single-cell case of the above."""
    return float(grid_coverage(poly, np.array([x0, x1]),
                               np.array([y0, y1]))[0, 0])


def band_coverage(outer: np.ndarray, inner: np.ndarray | None,
                  X: np.ndarray, Y: np.ndarray) -> np.ndarray:
    """Coverage of ``outer`` minus ``inner``, the lensing band of one order.

    The hole is subtracted rather than sampled away, so a cell that straddles
    the inner boundary keeps the part of itself that is genuinely in the band.
    """
    cov = grid_coverage(outer, X, Y)
    if inner is not None:
        cov = cov - grid_coverage(inner, X, Y)
    return cov
