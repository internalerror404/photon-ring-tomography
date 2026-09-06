"""Reference calibration, with the row-count convention made explicit.

Ledger C02. The archived runners each compute

    s_ref = sqrt(mean(clean**2)) = sqrt(E / m_current),   sigma = s_ref / SNR

where ``clean`` is the direct arm's whitened response to the declared
reference source. Pinning the *mean* row to the SNR label makes the label a
statement about a row rather than about the observation: split every pixel
into k equal-area children and the total response ``E`` is preserved while
``m`` multiplies by k, so ``sigma`` falls by sqrt(k) and the whitened Fisher
information rises by k. Refining the quadrature manufactures information.

Three modes, named because they answer different questions:

``LEGACY_REPLAY``
    the archived formula and the archived count, so an old number reproduces.
``LOCKED_LEGACY_NOISE``
    an archived sigma held fixed while the representation of the *same*
    observation is refined. The right mode for a convergence study.
``COMMON_REFERENCE_COUNT``
    ``s_ref = sqrt(E / m_reference)`` against one design count frozen for the
    campaign, which is the only mode that removes the cross-geometry count
    artefact -- E3C carries 1483 rays at a000_i020 against 1536 elsewhere.

The reference count is a campaign design constant. It is frozen before any
information outcome is inspected, and it is recorded in the serialization so
a reader can tell which question a number answers.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass, asdict

import numpy as np

LEGACY_REPLAY = "LEGACY_REPLAY"
LOCKED_LEGACY_NOISE = "LOCKED_LEGACY_NOISE"
COMMON_REFERENCE_COUNT = "COMMON_REFERENCE_COUNT"
MODES = (LEGACY_REPLAY, LOCKED_LEGACY_NOISE, COMMON_REFERENCE_COUNT)

# E3C: 1536 rays per order by design, eight observer times. Frozen here before
# any R2 spectrum is computed. Other campaigns must declare their own.
E3C_RAYS_PER_ORDER = 1536
E3C_OBSERVER_TIMES = 8
E3C_REFERENCE_ROWS = E3C_RAYS_PER_ORDER * E3C_OBSERVER_TIMES      # 12288


@dataclass(frozen=True)
class ReferenceCalibration:
    """What noise level a named SNR means, and under which convention."""

    mode: str
    snr_label: float
    energy: float                 # E = ||clean||^2, the total squared response
    m_current: int                # rows the operator actually has
    m_reference: int              # rows the label is defined against
    s_ref: float
    sigma: float
    grid_identity: str
    noise_label: str

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, sort_keys=True)

    @property
    def information_factor_against(self):
        """How this calibration's Fisher information compares with another."""
        def f(other: "ReferenceCalibration") -> float:
            return (other.sigma / self.sigma) ** 2
        return f


def _check(clean: np.ndarray, snr_label: float) -> tuple[float, int]:
    a = np.asarray(clean, dtype=float).ravel()
    if a.size == 0:
        raise ValueError("empty reference response: nothing to calibrate")
    if not np.all(np.isfinite(a)):
        raise ValueError("reference response contains non-finite entries")
    energy = float(a @ a)
    if not (energy > 0.0) or not math.isfinite(energy):
        raise ValueError(
            "zero or non-finite reference response cannot define an SNR. The "
            "archived floor of 1e-300 silently turned this into a calibration "
            "of noise against nothing")
    if not (snr_label > 0.0) or not math.isfinite(snr_label):
        raise ValueError(f"SNR label must be positive and finite: {snr_label}")
    return energy, a.size


def calibrate(clean: np.ndarray, snr_label: float, *, mode: str,
              grid_identity: str, m_reference: int | None = None,
              locked_sigma: float | None = None,
              noise_label: str = "declared") -> ReferenceCalibration:
    """The noise level a named SNR stands for, under one explicit convention."""
    if mode not in MODES:
        raise ValueError(f"unknown calibration mode {mode!r}; expected {MODES}")
    energy, m_current = _check(clean, snr_label)

    if mode == LEGACY_REPLAY:
        m_ref = m_current
        s_ref = math.sqrt(energy / m_current)
        sigma = s_ref / snr_label
    elif mode == COMMON_REFERENCE_COUNT:
        if m_reference is None:
            raise ValueError(
                "COMMON_REFERENCE_COUNT needs the campaign design count, "
                "frozen before outcomes are inspected")
        if m_reference <= 0:
            raise ValueError("reference row count must be positive")
        m_ref = int(m_reference)
        s_ref = math.sqrt(energy / m_ref)
        sigma = s_ref / snr_label
    else:                                     # LOCKED_LEGACY_NOISE
        if locked_sigma is None or not (locked_sigma > 0.0):
            raise ValueError(
                "LOCKED_LEGACY_NOISE needs the archived positive sigma it is "
                "holding fixed")
        m_ref = m_current
        sigma = float(locked_sigma)
        s_ref = sigma * snr_label
    return ReferenceCalibration(
        mode=mode, snr_label=float(snr_label), energy=energy,
        m_current=int(m_current), m_reference=int(m_ref), s_ref=float(s_ref),
        sigma=float(sigma), grid_identity=str(grid_identity),
        noise_label=str(noise_label))


def legacy_s_ref(clean: np.ndarray) -> float:
    """The archived formula verbatim, for replay comparisons only."""
    a = np.asarray(clean, dtype=float).ravel()
    return max(float(np.sqrt(np.mean(a ** 2))), 1e-300)


def fisher_information(operator: np.ndarray, cal: ReferenceCalibration,
                       q: np.ndarray | None = None) -> float:
    """||B q||^2 with B = A / sigma, or ||B||_F^2 when no direction is given."""
    B = np.asarray(operator, dtype=float) / cal.sigma
    return float(np.sum(B ** 2)) if q is None else float(
        np.sum((B @ np.asarray(q, dtype=float)) ** 2))
