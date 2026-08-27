"""The localized class must be compact, nested and dimension-matched to E3D."""
import numpy as np
import pytest

from phrt.sources.localized_basis import (LocalizedBasis, temporal_design,
                                          temporal_nodes, temporal_support_widths,
                                          temporal_supports)
from phrt.sources.physical_basis import temporal_design as dct_design

TLO, THI = -128.82234649196255, 29.0
SPAN = THI - TLO


def test_dimension_mirrors_the_e3d_ladder():
    for nr, na, nt, dim in ((4, 7, 8, 224), (4, 7, 16, 448), (6, 11, 16, 1056)):
        assert LocalizedBasis(2.0, 45.0, TLO, THI, nr, na, nt).dimension == dim


def test_non_dyadic_temporal_dimension_is_refused():
    # exact nesting is a dyadic statement; a nearly-nested ladder would make
    # every nesting gate report a small number instead of zero and hide a real
    # violation among rounding.
    with pytest.raises(ValueError):
        LocalizedBasis(2.0, 45.0, TLO, THI, 4, 7, 12)


def test_support_is_compact_unlike_the_dct():
    t = np.linspace(TLO, THI, 2001)
    hat = temporal_design(t, TLO, THI, 8)
    dct = dct_design(t, TLO, THI, 8)
    assert (hat > 0).mean(axis=0).max() <= 0.26
    assert (np.abs(dct) > 0).mean(axis=0).min() > 0.99


def test_declared_support_widths_are_what_the_functions_occupy():
    w = SPAN / 8
    widths = temporal_support_widths(TLO, THI, 8)
    assert widths[0] == pytest.approx(w)
    assert np.allclose(widths[1:], 2 * w)
    t = np.linspace(TLO, THI, 20001)
    hat = temporal_design(t, TLO, THI, 8)
    sup = temporal_supports(TLO, THI, 8)
    for k in range(8):
        nz = t[hat[:, k] > 0]
        assert nz.min() >= sup[k, 0] - 1e-9
        assert nz.max() <= sup[k, 1] + 1e-9


def test_nodes_are_dyadic_and_the_coarse_set_is_the_even_fine_set():
    assert np.allclose(temporal_nodes(TLO, THI, 8), temporal_nodes(TLO, THI, 16)[::2])


def test_temporal_nesting_is_exact():
    t = np.linspace(TLO, THI, 4001)
    T8, T16 = temporal_design(t, TLO, THI, 8), temporal_design(t, TLO, THI, 16)
    Q, _ = np.linalg.qr(T16)
    assert np.abs(T8 - Q @ (Q.T @ T8)).max() < 1e-12


def test_full_class_ladder_is_exactly_nested():
    rng = np.random.default_rng(11)
    r = rng.uniform(2.0, 45.0, 2000)
    p = rng.uniform(0.0, 2 * np.pi, 2000)
    t = rng.uniform(TLO, THI, 2000)
    b = {"L224": LocalizedBasis(1.9, 49.9, TLO, THI, 4, 7, 8),
         "L448": LocalizedBasis(1.9, 49.9, TLO, THI, 4, 7, 16),
         "L1056": LocalizedBasis(1.9, 49.9, TLO, THI, 6, 11, 16)}
    for small, large in (("L224", "L448"), ("L448", "L1056")):
        A, B = b[small].design(r, p, t), b[large].design(r, p, t)
        Q, _ = np.linalg.qr(B)
        assert np.abs(A - Q @ (Q.T @ A)).max() / np.abs(A).max() < 1e-12


def test_partition_of_unity_away_from_the_vanishing_boundary():
    t = np.linspace(TLO, THI - SPAN / 8, 3001)
    assert np.abs(temporal_design(t, TLO, THI, 8).sum(axis=1) - 1.0).max() < 1e-12


def test_unreached_temporal_modes_are_named_not_merely_ill_conditioned():
    # a coefficient whose support holds no sample must give an exactly zero
    # column, which is the property the whole experiment turns on
    b = LocalizedBasis(1.9, 49.9, TLO, THI, 4, 7, 8)
    rng = np.random.default_rng(3)
    t = rng.uniform(-40.0, 20.0, 500)          # young ages only
    r = rng.uniform(2.0, 45.0, 500)
    p = rng.uniform(0.0, 2 * np.pi, 500)
    mask = b.temporal_columns_covering(t)
    assert not mask.all()
    cols = b.columns_for_temporal_modes(mask)
    D = b.design(r, p, t)
    assert np.abs(D[:, ~cols]).max() == 0.0
    assert np.abs(D[:, cols]).max() > 0.0
