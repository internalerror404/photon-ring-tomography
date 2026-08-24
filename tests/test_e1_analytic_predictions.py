"""Analytic predictions the factorial must satisfy.

These are not regression fixtures: each one is a closed-form consequence of the
construction, so a mismatch means the operator is wrong rather than that a
number drifted.
"""
import numpy as np
import pytest

from phrt.audits.rank import spectrum_of
from phrt.operators import mixing
from phrt.operators.structured import (ToySpec, _low_rank_sampler, build_order_blocks)
from phrt.sources.toy_classes import (REGISTERED_RS, REGISTERED_RT,
                                      smooth_separable)

N_CELLS, N_SCREEN, HISTORY = 6, 2, 44
N_TEMPORAL, N_SPATIAL = REGISTERED_RT, REGISTERED_RS   # pinned: 8 x 3 = 24


def _restricted_rank(spatial, delay, seed=9000):
    spec = ToySpec(history_length=HISTORY, window=24, n_screen=N_SCREEN,
                   n_cells=N_CELLS, max_order=5, delay_step=4, gamma=0.6,
                   delay=delay, spatial=spatial, attenuation="exponential")
    blocks = build_order_blocks(spec, seed)
    Q = smooth_separable(N_CELLS, HISTORY, N_SPATIAL, N_TEMPORAL)
    B = mixing.resolved(len(blocks)).whiten(blocks) @ Q
    return spectrum_of(B, Q.shape[1]).numerical_rank


@pytest.mark.parametrize("delay", ["none", "constant", "perturbed"])
def test_common_sampler_caps_restricted_rank_at_rank_P_times_n_temporal(delay):
    """With one sampler shared by every order, the visible source-plane
    subspace is the fixed image of P however many delayed copies are stacked.

    The class is separable, so the restricted rank is exactly
    rank(P) * RT = 2 * 8 = 16, independent of the delay ladder.  This is the
    closed form behind E1's central negative result: a pure delay ladder
    recovers no source-plane direction that the sampler annihilates.
    """
    P = _low_rank_sampler(N_SCREEN, N_CELLS)
    predicted = np.linalg.matrix_rank(P) * N_TEMPORAL
    assert predicted == 16
    assert _restricted_rank("identical", delay) == predicted


def test_registered_class_dimension_is_rs_times_rt():
    """RS = 3, RT = 8 are pinned; their product is the registered 24."""
    assert REGISTERED_RS * REGISTERED_RT == 24
    assert smooth_separable(N_CELLS, HISTORY).shape[1] == 24


def test_rs_three_is_impossible_with_two_source_cells():
    """The pin settles the (K, M) reading without the generator: a separable
    class with three spatial modes cannot exist over two source-plane cells."""
    from phrt.sources.toy_classes import ClassNotConstructible

    with pytest.raises(ClassNotConstructible):
        smooth_separable(2, HISTORY, REGISTERED_RS, REGISTERED_RT)


def test_cell_dependent_delay_breaks_the_cap():
    """A delay that varies across source cells is no longer a pure delay: it
    couples the spatial and temporal axes and lifts the cap."""
    assert _restricted_rank("identical", "cell_dependent") > 16


@pytest.mark.parametrize("spatial", ["rotation", "rotation_shear", "independent"])
def test_order_dependent_sampling_reaches_full_restricted_rank(spatial):
    assert _restricted_rank(spatial, "constant") == N_SPATIAL * N_TEMPORAL


def test_delay_alone_matches_no_delay_at_all():
    """The sharpest statement of the negative result: under a common sampler,
    stacking six delayed orders is worth exactly as much as stacking none."""
    assert _restricted_rank("identical", "constant") == _restricted_rank("identical", "none")
