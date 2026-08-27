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
    v = np.asarray(values, float).reshape(shape_rphi[0], shape_rphi[1], -1)
    t = np.asarray(grid_t, float).reshape(shape_rphi[0], shape_rphi[1], -1)[0, 0]
    out = np.empty((ages.size, shape_rphi[0], shape_rphi[1]))
    for i, a in enumerate(ages):
        w = np.exp(-0.5 * ((t + float(a)) / half_width) ** 2)
        s = w.sum()
        out[i] = (v * w).sum(axis=2) / (s if s > 0 else 1.0)
    return out


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
