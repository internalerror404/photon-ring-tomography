"""Turning a validated ray map into the rays an operator actually consumes.

Two operations, both of which are easy to get quietly wrong:

``stratified_subsample``
    A band's rays are not exchangeable -- delay, source radius and screen
    azimuth are strongly correlated -- so uniform sampling of a few thousand
    from tens of thousands would under-represent the band edges that carry the
    oldest history. Sampling is stratified in all three, and the quadrature
    weights are rescaled so the band's *total solid angle* is preserved. Without
    that rescaling each order would shrink by its own sampling fraction, and the
    orders are sampled at very different fractions.

``common_count``
    The substitution arms transplant one order's spatial map onto another's
    delays, which is only defined pixel-for-pixel. Trimming to a common count
    again preserves each order's total solid angle.
"""
from __future__ import annotations

import numpy as np

from phrt.operators.physical import OrderRays


def stratified_subsample(rm, n_target: int, rng) -> OrderRays:
    v = np.where(rm.valid)[0]
    keys = (np.arctan2(rm.beta[v], rm.alpha[v]), rm.source_r[v], rm.delay[v])
    n_strata = max(int(round(n_target ** (1 / 3))), 2)
    edges = [np.quantile(k, np.linspace(0, 1, n_strata + 1)) for k in keys]
    cell = np.zeros(v.size, dtype=int)
    for k, e in zip(keys, edges):
        cell = cell * n_strata + np.clip(np.searchsorted(e, k, side="right") - 1,
                                         0, n_strata - 1)
    chosen, weights = [], []
    total_area = float(np.sum(rm.pixel_area[v]))
    for c in np.unique(cell):
        members = v[cell == c]
        take = max(1, int(round(n_target * members.size / v.size)))
        take = min(take, members.size)
        pick = rng.choice(members, size=take, replace=False)
        area = float(np.sum(rm.pixel_area[members]))
        chosen.append(np.atleast_1d(pick))
        weights.append(np.full(np.atleast_1d(pick).size, area / take))
    idx = np.concatenate(chosen)
    w = np.concatenate(weights)
    if idx.size > n_target:
        keep = rng.choice(idx.size, size=n_target, replace=False)
        idx, w = idx[keep], w[keep]
    w = w * (total_area / max(float(w.sum()), 1e-300))
    return OrderRays(order=rm.order, source_r=rm.source_r[idx].copy(),
                     source_phi=rm.source_phi[idx].copy(),
                     delay=rm.delay[idx].copy(), redshift=rm.redshift[idx].copy(),
                     quadrature=w)


def common_count(order_rays: list[OrderRays], rng) -> list[OrderRays]:
    n = min(o.n_rays for o in order_rays)
    out = []
    for o in order_rays:
        pick = np.sort(rng.choice(o.n_rays, size=n, replace=False)) if o.n_rays > n \
            else np.arange(n)
        scale = float(o.quadrature.sum()) / max(float(o.quadrature[pick].sum()), 1e-300)
        out.append(OrderRays(o.order, o.source_r[pick], o.source_phi[pick],
                             o.delay[pick], o.redshift[pick],
                             o.quadrature[pick] * scale, o.amplitude))
    return out
