"""Three domain states, and the difference between a point and a fragment.

Ruling 028. The forward model contains regions that genuinely do not emit, and
it contains regions where the numerics have not yet told us anything. Folding
them together makes a completeness gate demand that physics be small, which is
not a coherent requirement. So a fragment of the screen is in one of three
states, and only the third is a defect:

``CERTIFIED_EMITTING``
    the pinned validity conditions hold over the fragment. Transfer values
    still have to be available and accurate; that is a separate axis.

``CERTIFIED_NON_EMITTING``
    the model supplies zero there. No brightness has to be invented and no
    budget is charged for its area.

``UNRESOLVED``
    the physical classification or the transfer evaluation is still open. It
    may never contribute zero by default.

Point status is not fragment status. Classifying a cut cell by its centre ray
is a diagnostic, not a certificate: a centre outside the emission annulus says
nothing about the part of its cell that lies inside, and a valid centre does
not make the transfer accurate across the whole cell. The certificate needs
the boundary resolved inside the fragment, which is what the contour pilot is
for. Both are recorded, under names that keep them apart.
"""
from __future__ import annotations

import numpy as np

CERTIFIED_EMITTING = "CERTIFIED_EMITTING"
CERTIFIED_NON_EMITTING = "CERTIFIED_NON_EMITTING"
UNRESOLVED = "UNRESOLVED"
STATES = (CERTIFIED_EMITTING, CERTIFIED_NON_EMITTING, UNRESOLVED)

# for a fragment that is emitting, how good is the transfer data behind it
AVAILABLE_ACCURACY_TESTED = "AVAILABLE_ACCURACY_TESTED"
AVAILABLE_UNQUALIFIED = "AVAILABLE_UNQUALIFIED"
MISSING_OR_SOLVER_UNRESOLVED = "MISSING_OR_SOLVER_UNRESOLVED"
TRANSFER_STATES = (AVAILABLE_ACCURACY_TESTED, AVAILABLE_UNQUALIFIED,
                   MISSING_OR_SOLVER_UNRESOLVED)

# which pinned primitive failed, where one did
RADIAL_ROOT = "RADIAL_ROOT_OR_EQUATORIAL_CROSSING"
POLAR_ORDER = "POLAR_INTERSECTION_OR_ORDER"
AZIMUTH_INTEGRAL = "AZIMUTH_INTEGRAL"
TIME_INTEGRAL = "TIME_INTEGRAL"
REDSHIFT = "REDSHIFT"
CONDITIONING = "NUMERICAL_CONDITIONING"
NEVER_EVALUATED = "NO_PRIOR_EVALUATION"
PRIMITIVES = (RADIAL_ROOT, POLAR_ORDER, AZIMUTH_INTEGRAL, TIME_INTEGRAL,
              REDSHIFT, CONDITIONING, NEVER_EVALUATED)


def classify_points(in_band, source_r, source_phi, coordinate_time, redshift,
                    r_horizon: float, r_outer: float):
    """Per-sample state, from cached values only. A diagnostic, not a certificate.

    The name says point: this is the state of one ray, at one screen
    coordinate, and it is attached to a fragment only as a label of that
    fragment's centre.
    """
    fr = np.isfinite(source_r)
    fp = np.isfinite(source_phi)
    ft = np.isfinite(coordinate_time)
    fg = np.isfinite(redshift)
    state = np.full(source_r.size, UNRESOLVED, dtype=object)
    prim = np.full(source_r.size, "", dtype=object)

    solved = in_band & fr & fp & ft
    emitting = solved & (source_r > r_horizon) & (source_r <= r_outer) & fg
    state[emitting] = CERTIFIED_EMITTING
    # outside the declared emission annulus, on a solved ray: the model says
    # zero there, and that is physics rather than a gap
    outside = solved & ~((source_r > r_horizon) & (source_r <= r_outer))
    state[outside] = CERTIFIED_NON_EMITTING
    # a solved landing whose redshift is not finite is not certified either way
    bad_g = solved & ~fg & ~outside
    state[bad_g] = UNRESOLVED
    prim[bad_g] = REDSHIFT

    unres = in_band & ~solved
    state[unres] = UNRESOLVED
    prim[unres & ~fr] = RADIAL_ROOT
    prim[unres & fr & ~fp] = AZIMUTH_INTEGRAL
    prim[unres & fr & fp & ~ft] = TIME_INTEGRAL
    state[~in_band] = UNRESOLVED
    prim[~in_band] = NEVER_EVALUATED
    return state, prim


def tally(state, prim, area):
    """Area and count by state, with the primitive breakdown for the gap."""
    out = {"total_area": float(area.sum()), "by_state": {}}
    for s in STATES:
        m = state == s
        out["by_state"][s] = {"n": int(m.sum()), "area": float(area[m].sum())}
    tot = out["total_area"]
    for s in STATES:
        d = out["by_state"][s]
        d["area_fraction"] = d["area"] / tot if tot else None
    u = state == UNRESOLVED
    out["unresolved_by_primitive"] = {
        p: {"n": int(((prim == p) & u).sum()),
            "area": float(area[(prim == p) & u].sum())}
        for p in PRIMITIVES if ((prim == p) & u).any()}
    out["certified_non_emitting_is_not_a_defect"] = True
    out["point_classified_not_fragment_certified"] = True
    return out


def response_bound(uncertain_area_per_cell: np.ndarray, envelope: np.ndarray,
                   sigma: float, detector_cell_area: float) -> dict:
    """||W dy|| <= [ sum_d M_d^2 |U_d|^2 / (sigma^2 |D_d|) ]^(1/2).

    Valid only if ``envelope`` really bounds the field over the uncertain
    support. A sampled maximum is not such an envelope and the caller has to
    say which it supplied, so the flag is required rather than assumed.
    """
    u = np.asarray(uncertain_area_per_cell, float)
    m = np.asarray(envelope, float)
    if u.shape != m.shape:
        raise ValueError("one envelope per detector cell is required")
    if np.any(u < 0) or np.any(m < 0):
        raise ValueError("areas and envelopes are non-negative")
    v = float(np.sqrt(np.sum(m ** 2 * u ** 2)
                      / (sigma ** 2 * detector_cell_area)))
    return {"whitened_response_bound": v,
            "uncertain_area_total": float(u.sum()),
            "cells_with_uncertain_support": int(np.count_nonzero(u > 0)),
            "bound_is_conditional_on_the_envelope": True}
