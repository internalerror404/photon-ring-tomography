"""Numerical comparison criteria for reproduction gates.

A pure relative criterion is not well posed on a cell whose value is dominated
by regularization rather than by signal.  In the zero-limit case both the
reference and the candidate are round-off residuals of a quantity whose limit
is zero, and their ratio measures the round-off, not the agreement.

The reviewer-ruled criterion applies one mixed rule uniformly, so no cell needs
to be classified or excluded:

    |candidate - reference| <= ATOL + RTOL * max(|candidate|, |reference|)

with ATOL = 1e-14 and RTOL = 1e-8.  The absolute floor is roughly two orders of
magnitude above unit-scale binary64 machine epsilon (2.22e-16), which is the
right scale for a value that has been through an SVD and a Tikhonov solve.
"""
from __future__ import annotations

import numpy as np

ATOL = 1e-14
RTOL = 1e-8
MACHINE_EPS = float(np.finfo(np.float64).eps)

SPECIFICATION = "RELATIVE_ONLY_NEAR_ZERO_DEFECT"
CRITERION = "abs(candidate - reference) <= 1e-14 + 1e-8 * max(abs(candidate), abs(reference))"


def allowance(candidate: np.ndarray | float, reference: np.ndarray | float,
              atol: float = ATOL, rtol: float = RTOL) -> np.ndarray:
    """The permitted absolute discrepancy for each cell."""
    c, r = np.asarray(candidate, dtype=float), np.asarray(reference, dtype=float)
    return atol + rtol * np.maximum(np.abs(c), np.abs(r))


def residual(candidate: np.ndarray | float, reference: np.ndarray | float
             ) -> np.ndarray:
    """Absolute discrepancy per cell."""
    c, r = np.asarray(candidate, dtype=float), np.asarray(reference, dtype=float)
    return np.abs(c - r)


def utilisation(candidate: np.ndarray | float, reference: np.ndarray | float,
                atol: float = ATOL, rtol: float = RTOL) -> np.ndarray:
    """Discrepancy as a fraction of what the criterion allows.

    <= 1 passes.  Reporting this rather than a bare relative error keeps every
    cell on one comparable scale, including the zero-limit ones, and makes the
    margin legible: 0.05 means the criterion had twenty times the room it
    needed.
    """
    return residual(candidate, reference) / np.maximum(
        allowance(candidate, reference, atol, rtol), 1e-300)


def passes(candidate: np.ndarray | float, reference: np.ndarray | float,
           atol: float = ATOL, rtol: float = RTOL) -> np.ndarray:
    return residual(candidate, reference) <= allowance(candidate, reference, atol, rtol)


def in_machine_eps(value: float) -> float:
    """Express an absolute discrepancy in unit-scale binary64 machine epsilon.

    Deliberately not called a ULP: a unit in the last place is relative to the
    magnitude of the number in question, and these comparisons span ten orders
    of magnitude, so ULP would mean something different in every row.
    """
    return float(value) / MACHINE_EPS
