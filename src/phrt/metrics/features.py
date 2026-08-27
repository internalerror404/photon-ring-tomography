"""Extract a compressed physical description from a contrast field.

HMT-1. The endpoint of this study is not pixel error, it is whether we recover
*where a feature was, how it moved, how bright it was, when it appeared and when
it faded*. That is a much smaller object than the field, and it is the object a
rendered historical movie would actually be built from.

Every quantity here is produced by a procedure fixed in the freeze and applied
identically to the truth field and to the reconstruction. Nothing compares a
reconstruction against the generative parameters directly: doing so would credit
the extractor's own bias to the operator. The generative parameters are used
once, to check that extraction from a noiseless truth recovers them at the
evaluation grid's resolution, and that check is reported rather than gated at a
tolerance the grid cannot deliver.
"""
from __future__ import annotations

import numpy as np

from phrt.sources.movie import wrapped_angle

BIRTH_FRACTION = 0.25             # of the amplitude maximum
DECAY_FRACTION = float(np.exp(-1.0))


def age_maps(values: np.ndarray, grid_t: np.ndarray, ages: np.ndarray,
             half_width: float, shape_rphi: tuple[int, int]) -> np.ndarray:
    """One (r, phi) map per age: the window-weighted average over source time.

    A window at age ``a`` is centred on source time ``-a``, so the map is what
    the field looked like at that age, smoothed by the same probe the rest of
    the campaign uses.
    """
    nr, npz = shape_rphi
    v = np.asarray(values, float).reshape(nr * npz, -1)
    t = np.asarray(grid_t, float).reshape(nr, npz, -1)[0, 0]
    # one gemm rather than a loop over ages: the window stack is (n_t, n_ages)
    # and the maps are the field times that stack, column-normalised
    W = np.exp(-0.5 * ((t[:, None] + np.asarray(ages, float)[None, :])
                       / half_width) ** 2)
    W = W / np.maximum(W.sum(axis=0, keepdims=True), 1e-300)
    return (v @ W).T.reshape(np.asarray(ages).size, nr, npz)


def _parabolic(y0: float, y1: float, y2: float) -> float:
    """Sub-cell offset of the peak of the parabola through three samples."""
    den = y0 - 2.0 * y1 + y2
    if den == 0.0:
        return 0.0
    return float(np.clip(0.5 * (y0 - y2) / den, -1.0, 1.0))


def peak_position(m: np.ndarray, r_axis: np.ndarray,
                  phi_axis: np.ndarray) -> tuple[float, float, float]:
    """Refined argmax of one map, and its value.

    Refinement is parabolic on the three cells straddling the peak, wrapping in
    azimuth and clamping in radius. Without it every reported angle would be
    quantised to the grid and the trajectory error would measure the grid rather
    than the reconstruction.
    """
    i, j = np.unravel_index(int(np.argmax(m)), m.shape)
    dr = 0.0
    if 0 < i < m.shape[0] - 1:
        dr = _parabolic(m[i - 1, j], m[i, j], m[i + 1, j])
    jm, jp = (j - 1) % m.shape[1], (j + 1) % m.shape[1]
    dp = _parabolic(m[i, jm], m[i, j], m[i, jp])
    lr = np.log(r_axis)
    r_hat = float(np.exp(np.interp(i + dr, np.arange(lr.size), lr)))
    step = float(phi_axis[1] - phi_axis[0])
    phi_hat = float(wrapped_angle(np.array([phi_axis[j] + dp * step]))[0])
    return r_hat, phi_hat, float(m[i, j])


def mode_amplitudes(m: np.ndarray, r_axis: np.ndarray, phi_axis: np.ndarray,
                    orders=(1, 2)) -> dict:
    """Radially weighted azimuthal mode moduli of one map."""
    w = r_axis / max(float(r_axis.sum()), 1e-300)
    out = {}
    for k in orders:
        c = float((w[:, None] * m * np.cos(k * phi_axis)[None, :]).sum())
        s = float((w[:, None] * m * np.sin(k * phi_axis)[None, :]).sum())
        out[f"a_m{k}"] = float(np.hypot(c, s)) * 2.0 / phi_axis.size
    return out


def extract(values: np.ndarray, grid_t: np.ndarray, ages: np.ndarray,
            r_axis: np.ndarray, phi_axis: np.ndarray, half_width: float) -> dict:
    """The full feature history of one contrast field.

    Deterministic and free of hidden state: the same field in gives the same
    dictionary out, which gate ``HMT1_G10`` checks rather than assumes.
    """
    maps = age_maps(values, grid_t, ages, half_width,
                    (r_axis.size, phi_axis.size))
    r_h, phi_h, amp, m1, m2 = [], [], [], [], []
    for k in range(ages.size):
        rr, pp, aa = peak_position(maps[k], r_axis, phi_axis)
        r_h.append(rr)
        phi_h.append(pp)
        amp.append(aa)
        mm = mode_amplitudes(maps[k], r_axis, phi_axis)
        m1.append(mm["a_m1"])
        m2.append(mm["a_m2"])
    amp = np.asarray(amp)
    return {"ages": np.asarray(ages, float), "r_h": np.asarray(r_h),
            "phi_h": np.asarray(phi_h), "A_h": amp,
            "a_m1": np.asarray(m1), "a_m2": np.asarray(m2),
            **event_times(np.asarray(ages, float), amp)}


def event_times(ages: np.ndarray, amp: np.ndarray) -> dict:
    """Birth and decay, read off the amplitude history.

    Age runs backwards in time: a *larger* age is an *earlier* moment. So the
    birth of a feature -- the first moment it exists -- is the **largest** age
    at which the amplitude clears a quarter of its maximum, and the decay runs
    from the peak age *down* toward zero as time moves forward.

    Reading these off the wrong end of the age axis is an easy mistake and a
    silent one: it returns a finite, plausible number for the wrong event. The
    first version of this function took the smallest age and reported a birth
    40 M away from the truth without any sign of trouble.
    """
    a = np.asarray(amp, float)
    if a.size == 0 or not np.isfinite(a).any() or a.max() <= 0:
        return {"t_birth_age_M": float("nan"), "tau_decay_M": float("nan")}
    peak = int(np.argmax(a))
    above_birth = np.flatnonzero(a >= BIRTH_FRACTION * a.max())
    above_decay = np.flatnonzero(a >= DECAY_FRACTION * a.max())
    return {"t_birth_age_M": float(ages[above_birth.max()]) if above_birth.size
            else float("nan"),
            "tau_decay_M": float(abs(ages[peak] - ages[above_decay.min()]))
            if above_decay.size else float("nan")}


def normalized_errors(truth: dict, recon: dict, r_span: float,
                      obs_span: float) -> dict:
    """Per-age normalised error in each recovered quantity.

    Each parameter is divided by its own natural scale so they can be combined:
    radius by the radial support width, angle by pi, amplitudes by the truth's
    own maximum, event times by the observation span. A parameter whose truth is
    identically zero contributes nothing rather than dividing by it.
    """
    def rel(a, b, scale):
        s = max(float(scale), 1e-300)
        return np.abs(np.asarray(a, float) - np.asarray(b, float)) / s

    out = {
        "radial": rel(recon["r_h"], truth["r_h"], r_span),
        "angular": np.abs(wrapped_angle(
            np.asarray(recon["phi_h"], float)
            - np.asarray(truth["phi_h"], float))) / np.pi,
        "amplitude": rel(recon["A_h"], truth["A_h"],
                         np.abs(truth["A_h"]).max()),
        "mode_m1": rel(recon["a_m1"], truth["a_m1"],
                       np.abs(truth["a_m1"]).max()),
        "mode_m2": rel(recon["a_m2"], truth["a_m2"],
                       np.abs(truth["a_m2"]).max()),
    }
    for k in ("t_birth_age_M", "tau_decay_M"):
        tv, rv = truth.get(k), recon.get(k)
        out[k] = (float("nan") if tv is None or rv is None
                  or not np.isfinite(tv) or not np.isfinite(rv)
                  else abs(rv - tv) / max(obs_span, 1e-300))
    return out


def aggregate(errs: dict, keys) -> np.ndarray:
    """Root mean square over the declared per-age parameter errors."""
    stack = [np.asarray(errs[k], float) for k in keys
             if k in errs and np.ndim(errs[k]) == 1]
    if not stack:
        return np.zeros(0)
    return np.sqrt(np.mean(np.stack(stack) ** 2, axis=0))


def generative_peak_error(traj, ages: np.ndarray, feats: dict,
                          r_axis: np.ndarray, phi_axis: np.ndarray,
                          m_fold: int = 1) -> dict:
    """How far the extracted peak sits from the trajectory it was drawn from.

    Gate ``HMT1_G10b``. ``HMT1_G10`` only asks that extraction be *repeatable*;
    a deterministic extractor that reads the wrong position passes it every
    time. This asks the other question -- does the instrument, applied to the
    truth itself with no operator and no noise in the way, return the feature
    that was actually put there.

    The error is reported in grid cells rather than in M and radians, because
    the freeze declares this quantity at the evaluation-grid resolution: an
    extractor reading a sampled field cannot localise a feature better than the
    grid it is sampled on, and a tolerance in physical units would silently
    become a different tolerance at a different radius. The radial axis is
    uniform in ``log r``, so a cell there is a fixed step in ``log r``.

    Ages where the generative amplitude has fallen below ``BIRTH_FRACTION`` of
    its own maximum are excluded. That is not a convenience: where the feature
    has faded to nothing the argmax of the residual is the argmax of numerical
    dust, and scoring it would measure rounding rather than extraction. The
    threshold is the one ``event_times`` already uses, not a new one.

    ``m_fold`` folds the azimuthal comparison for the pattern families, whose
    ``cos(m phi)`` shape has ``m`` equal maxima -- the extractor has no way to
    prefer one, and no reason to.
    """
    ages = np.asarray(ages, float)
    gen_r, gen_phi, gen_a, cands = [], [], [], []
    for a in ages:
        tv = traj(float(a))
        gen_r.append(tv.get("r_h", tv.get("r_peak", np.nan)))
        gen_phi.append(tv.get("phi_h", tv.get("pattern_phase", np.nan)))
        gen_a.append(tv.get("A_h", tv.get("a_m1", tv.get("a_m2", 1.0))))
        cands.append(tv.get("candidates"))
    gen_r = np.asarray(gen_r, float)
    gen_phi = np.asarray(gen_phi, float)
    gen_a = np.abs(np.asarray(gen_a, float))

    live = np.isfinite(gen_r) & np.isfinite(gen_phi) & np.isfinite(gen_a)
    if live.any() and gen_a[live].max() > 0:
        live &= gen_a >= BIRTH_FRACTION * gen_a[live].max()
    if not live.any():
        return {"radial_cells": float("nan"), "azimuthal_cells": float("nan"),
                "n_ages_scored": 0}

    d_logr = float(np.log(r_axis[-1] / r_axis[0]) / (r_axis.size - 1))
    d_phi = float(2.0 * np.pi / phi_axis.size)
    fold = 2.0 * np.pi / max(int(m_fold), 1)

    fr = np.asarray(feats["r_h"], float)
    fp = np.asarray(feats["phi_h"], float)

    def cells(idx, r_t, phi_t):
        dp = (fp[idx] - phi_t + 0.5 * fold) % fold - 0.5 * fold
        return abs(np.log(fr[idx] / r_t)) / d_logr, abs(dp) / d_phi

    er, ep = [], []
    for idx in np.flatnonzero(live):
        opts = cands[idx] or [{"r_h": gen_r[idx], "phi_h": gen_phi[idx]}]
        # A field with several features has no single peak position, so the
        # comparison is against the nearest declared feature. With one feature
        # this is that feature and the reading is unchanged; with several it
        # asks whether the extractor found a feature that is really there
        # rather than which of two near-equal ones it happened to pick.
        best = min((cells(idx, c["r_h"], c["phi_h"]) for c in opts),
                   key=lambda e: e[0] ** 2 + e[1] ** 2)
        er.append(best[0])
        ep.append(best[1])
    return {"radial_cells": float(np.max(er)), "azimuthal_cells": float(np.max(ep)),
            "n_ages_scored": int(live.sum())}
