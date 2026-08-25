"""The reviewer-ruled mixed reproduction criterion."""
import numpy as np
import pytest

from phrt.audits import tolerance as tol


def test_criterion_constants_are_as_ruled():
    assert tol.ATOL == 1e-14 and tol.RTOL == 1e-8
    assert tol.SPECIFICATION == "RELATIVE_ONLY_NEAR_ZERO_DEFECT"


def test_zero_limit_cell_passes_on_the_absolute_floor():
    """The disputed G1 cell: two round-off residuals of a quantity whose limit
    is zero. It fails a pure relative test and passes the mixed one."""
    a, b = 5.57692292754989478e-10, 5.57692300078700935e-10
    assert abs(a - b) / max(abs(a), abs(b)) > 1e-8      # pure relative fails
    assert bool(tol.passes(b, a))                        # mixed criterion passes
    assert tol.utilisation(b, a) < 1e-3                  # with large margin


def test_large_values_are_governed_by_the_relative_term():
    """At unit scale the 1e-14 floor is negligible and 1e-8 relative governs."""
    a = 1.0
    assert bool(tol.passes(a * (1 + 9e-9), a))
    assert not bool(tol.passes(a * (1 + 2e-8), a))


def test_tiny_values_are_governed_by_the_absolute_floor():
    a = 1e-20
    assert bool(tol.passes(a + 5e-15, a))
    assert not bool(tol.passes(a + 5e-14, a))


def test_exact_agreement_uses_no_allowance():
    assert tol.utilisation(3.25, 3.25) == 0.0


def test_criterion_is_symmetric_in_its_arguments():
    a, b = 1.0, 1.0 + 5e-9
    assert bool(tol.passes(a, b)) == bool(tol.passes(b, a))
    assert np.isclose(tol.utilisation(a, b), tol.utilisation(b, a))


def test_machine_epsilon_unit_is_unit_scale_not_ulp():
    """The reported unit is unit-scale binary64 machine epsilon. A ULP is
    relative to each number's own magnitude, which would mean something
    different in every row of a table spanning ten orders of magnitude."""
    assert np.isclose(tol.MACHINE_EPS, 2.220446049250313e-16)
    assert np.isclose(tol.in_machine_eps(7.324e-18), 0.03298, atol=1e-4)


def test_nan_never_passes():
    assert not bool(tol.passes(float("nan"), 1.0))


@pytest.mark.parametrize("scale", [1e-18, 1e-9, 1.0, 1e6])
def test_vectorised_and_scalar_agree(scale):
    a = np.array([scale, scale * 2, scale * 3])
    b = a * (1 + 1e-9)
    assert bool(tol.passes(b, a).all())
    for i in range(3):
        assert bool(tol.passes(b[i], a[i]))
