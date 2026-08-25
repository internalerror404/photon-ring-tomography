"""The localized age-probe class, and the degeneracy Amendment 002 exists for.

The scalar probe registered for E3B and E3C is spatially flat, which makes the
registered H2 mechanism statistic identically zero for the delay-only
substitution. That is a property of the diagnostic, not of the physics, and it
is easy to reintroduce by accident -- so it is pinned here as a test rather than
left as a comment.
"""
from __future__ import annotations

import numpy as np
import pytest

from phrt.operators.physical import (OrderRays, PhysicalOperator, substitute_delay,
                                     substitute_spatial)
from phrt.sources.physical_basis import (PhysicalBasis, age_probe_norms,
                                         age_probe_spatial, azimuthal_design,
                                         radial_design)

R_IN, R_OUT, WIDTH = 2.0, 50.0, 3.0


def _orders(rng, n_rays=64):
    out = []
    for n in range(3):
        out.append(OrderRays(
            order=n,
            source_r=rng.uniform(R_IN, R_OUT, n_rays),
            source_phi=rng.uniform(0.0, 2 * np.pi, n_rays),
            delay=rng.uniform(0.0, 20.0, n_rays) + 20.0 * n,
            redshift=rng.uniform(0.5, 1.2, n_rays),
            quadrature=rng.uniform(0.01, 1.0, n_rays)))
    return out


def _flat_curve(op, age):
    """The registered spatially flat probe: response depends only on delay."""
    blocks = []
    for o in op.orders:
        c = o.coefficient()
        for t in op.observer_times:
            ts = float(t) - o.delay
            blocks.append(c * np.exp(-0.5 * ((ts + age) / WIDTH) ** 2))
    per_order = np.split(np.concatenate(blocks), len(op.orders))
    out = [sum(op.L[ch, k] * per_order[k] for k in range(len(op.orders)))
           for ch in range(op.n_channels)]
    return np.concatenate(out) / np.sqrt(op.channel_variance())


def test_flat_probe_cannot_see_a_spatial_substitution():
    """The registered H2 statistic is an identity, not evidence."""
    rng = np.random.default_rng(7)
    base = _orders(rng)
    basis = PhysicalBasis(R_IN, R_OUT, -80.0, 30.0)
    t_obs = np.linspace(0.0, 20.0, 4)
    kw = dict(observer_times=t_obs, design=basis.design, dimension=basis.dimension)
    full = PhysicalOperator(orders=base, **kw)
    delay_only = PhysicalOperator(orders=substitute_spatial(base, base[0]), **kw)
    for age in (0.0, 20.0, 55.0):
        assert np.array_equal(_flat_curve(full, age), _flat_curve(delay_only, age))


def test_flat_probe_does_see_a_delay_substitution():
    """H3 is not degenerate, which is why the pair could not be compared."""
    rng = np.random.default_rng(7)
    base = _orders(rng)
    basis = PhysicalBasis(R_IN, R_OUT, -80.0, 30.0)
    t_obs = np.linspace(0.0, 20.0, 4)
    kw = dict(observer_times=t_obs, design=basis.design, dimension=basis.dimension)
    full = PhysicalOperator(orders=base, **kw)
    spatial_only = PhysicalOperator(orders=substitute_delay(base, base[0]), **kw)
    assert not np.allclose(_flat_curve(full, 30.0), _flat_curve(spatial_only, 30.0))


def test_localized_class_does_see_a_spatial_substitution():
    """Amendment 002's diagnostic is non-degenerate for the same substitution."""
    rng = np.random.default_rng(7)
    base = _orders(rng)
    norms = age_probe_norms(R_IN, R_OUT, WIDTH)

    def probe_matrix(orders, age):
        rows = []
        for o in orders:
            rp = age_probe_spatial(o.source_r, o.source_phi, R_IN, R_OUT)
            c = o.coefficient() / np.sqrt(o.row_variance())
            for t in (0.0, 10.0, 20.0):
                w = c * np.exp(-0.5 * ((t - o.delay + age) / WIDTH) ** 2)
                rows.append(rp * w[:, None])
        P = np.vstack(rows) / norms[None, :]
        return P.T @ P

    a = probe_matrix(base, 30.0)
    b = probe_matrix(substitute_spatial(base, base[0]), 30.0)
    assert not np.allclose(a, b)


def test_age_probe_norms_match_direct_quadrature():
    """The analytic normalisation is the L2 norm it claims to be."""
    n = age_probe_norms(R_IN, R_OUT, WIDTH, n_quad=2048)
    r = np.linspace(R_IN, R_OUT, 4001)
    phi = np.linspace(0.0, 2 * np.pi, 4001)[:-1]
    R = radial_design(r, R_IN, R_OUT)
    P = azimuthal_design(phi)
    wr = np.trapezoid(R ** 2 * r[:, None], r, axis=0)
    wp = (2 * np.pi / phi.size) * np.sum(P ** 2, axis=0)
    want = np.sqrt(np.outer(wr, wp).ravel() * WIDTH * np.sqrt(np.pi))
    assert n.shape == (28,)
    assert np.allclose(n, want, rtol=2e-3)


def test_age_probe_spatial_is_the_c224_spatial_factor():
    """The localized class reuses C224's radial and azimuthal factors exactly."""
    rng = np.random.default_rng(3)
    r = rng.uniform(R_IN, R_OUT, 17)
    phi = rng.uniform(0.0, 2 * np.pi, 17)
    got = age_probe_spatial(r, phi, R_IN, R_OUT)
    want = (radial_design(r, R_IN, R_OUT)[:, :, None]
            * azimuthal_design(phi)[:, None, :]).reshape(17, -1)
    assert got.shape == (17, 28)
    assert np.allclose(got, want)


def test_flat_probe_is_the_partition_of_unity_contraction():
    """The scalar probe is the m=0 contraction of the localized class."""
    rng = np.random.default_rng(11)
    r = rng.uniform(R_IN, R_OUT, 25)
    phi = rng.uniform(0.0, 2 * np.pi, 25)
    sp = age_probe_spatial(r, phi, R_IN, R_OUT).reshape(25, 4, 7)
    assert np.allclose(sp[:, :, 0].sum(axis=1), 1.0)
