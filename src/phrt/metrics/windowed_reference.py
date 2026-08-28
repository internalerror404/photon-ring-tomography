"""An independent reference for where a feature is at a given age.

Gate ``HMT1M_G10c``. This exists because the first reference was wrong.

``G10b`` compared the extracted peak against the *generative trajectory* --
the declared centre of the blob that was drawn. That is a raw-trajectory proxy,
and it is not what the extractor measures. The extractor reports the argmax of
the field after the declared temporal window has been applied, and a feature
that moves appreciably inside that window has its windowed peak somewhere other
than the instantaneous centre the window is centred on. On the retired bank one
hotspot swept about 2.5 azimuthal cells inside the 3 M window, and the proxy
reported a 1.2 cell error that was entirely the proxy's own.

The reference here windows the field first and then asks where the peak is,
which is the same question the extractor answers. It stays independent of
``extract`` in every way that matters:

* it evaluates the **analytic** source, never the sampled array the extractor
  reads, so a defect in the sampling is visible rather than shared;
* it samples on a grid refined several times per evaluation cell and takes a
  plain argmax, where the extractor takes a coarse argmax and refines it by
  parabolic interpolation. Neither inherits the other's discretisation error;
* it shares no code path with ``extract`` beyond numpy itself.

What it deliberately *does* share is the window: same Gaussian, same half
width, same centring on source time ``-a``, same normalisation, evaluated on
the same source-time axis. A reference that windowed differently would measure
the difference between two windows rather than the accuracy of the extractor.

Nothing here is used by any endpoint. It is a check on the instrument.
"""
from __future__ import annotations

import numpy as np

DEFAULT_REFINE = 4


def window_stack(t_axis: np.ndarray, ages: np.ndarray,
                 half_width: float) -> np.ndarray:
    """The declared probe window, as an ``(n_t, n_ages)`` column-normalised stack.

    Written out rather than imported from ``features`` so that a change to the
    extractor's internals cannot silently move the reference with it. The two
    are required to agree, and a test asserts they do.
    """
    t = np.asarray(t_axis, float)
    a = np.asarray(ages, float)
    W = np.exp(-0.5 * ((t[:, None] + a[None, :]) / half_width) ** 2)
    return W / np.maximum(W.sum(axis=0, keepdims=True), 1e-300)


def windowed_peak(source_fn, t_axis, ages, r_lo: float, r_hi: float,
                  n_r: int, n_phi: int, half_width: float,
                  refine: int = DEFAULT_REFINE) -> dict:
    """Where the windowed analytic field peaks, at each age.

    ``source_fn(r, phi, t)`` is the analytic fluctuation. The returned radii and
    angles are in physical units; the caller converts to evaluation-grid cells.
    """
    t = np.asarray(t_axis, float)
    ages = np.asarray(ages, float)
    rf = np.exp(np.linspace(np.log(r_lo), np.log(r_hi), n_r * refine))
    pf = np.linspace(0.0, 2 * np.pi, n_phi * refine, endpoint=False)
    R, P, T = np.meshgrid(rf, pf, t, indexing="ij")
    vals = np.asarray(source_fn(R.ravel(), P.ravel(), T.ravel()),
                      dtype=float).reshape(rf.size * pf.size, t.size)
    maps = vals @ window_stack(t, ages, half_width)      # (n_cells, n_ages)
    cube = maps.reshape(rf.size, pf.size, ages.size)
    flat = np.argmax(maps, axis=0)
    ri, pi = np.divmod(flat, pf.size)
    return {"r": rf[ri], "phi": pf[pi],
            "amplitude": maps[flat, np.arange(ages.size)],
            "maxima": local_maxima(cube, rf, pf), "r_fine": rf,
            "phi_fine": pf, "refine": int(refine)}


def local_maxima(cube: np.ndarray, rf: np.ndarray, pf: np.ndarray) -> list:
    """Every local maximum of the windowed field, per age.

    The windowed field can have more than one maximum, and when it does, ranking
    them is not something a grid-sampled extractor can be asked to do. A
    ``cos(2 phi)`` pattern has two maxima that are equal *by symmetry* -- there
    is no fact of the matter about which is "the" peak, and the retired proxy
    reported exactly pi, half the azimuthal grid, for that. Two hotspots of
    nearly equal windowed height are the same situation by accident rather than
    by symmetry: sample them coarsely and the ranking can flip.

    So the reference offers all the maxima and the agreement test asks whether
    the extractor landed on one of them. That is still falsifiable -- a peak
    from a sampling artefact, a seam-handling bug or a mis-indexed axis is not
    at a local maximum of the true windowed field -- and it needs no tolerance
    beyond the frozen one cell. Which maximum the extractor chose is reported
    separately and is not gated.
    """
    nr, npz, na = cube.shape
    out = []
    for k in range(na):
        m = cube[:, :, k]
        best = m
        for dr in (-1, 0, 1):
            for dp in (-1, 0, 1):
                if dr == 0 and dp == 0:
                    continue
                sh = np.roll(m, dp, axis=1)          # phi is periodic
                if dr:                                # r is not
                    sh = np.roll(sh, dr, axis=0)
                    if dr > 0:
                        sh[0, :] = -np.inf
                    else:
                        sh[-1, :] = -np.inf
                best = np.maximum(best, sh)
        ii, jj = np.nonzero(m >= best)
        out.append((rf[ii], pf[jj], m[ii, jj]))
    return out


def peak_agreement(feats: dict, ref: dict, r_axis: np.ndarray,
                   phi_axis: np.ndarray, live: np.ndarray | None = None) -> dict:
    """Extractor against reference, in evaluation-grid cells.

    Cells, not physical units, because the freeze reads this at the evaluation
    grid's resolution: an extractor reading a sampled field cannot localise
    better than the grid it is sampled on. The radial axis is uniform in
    ``log r``, so a cell there is a fixed step in ``log r`` and the tolerance
    does not quietly change meaning with radius.

    No candidate list and no per-family special case. The windowed field has one
    global peak whatever drew it, so a two-hotspot draw needs no tie-breaking
    rule and none is applied.
    """
    d_logr = float(np.log(r_axis[-1] / r_axis[0]) / (r_axis.size - 1))
    d_phi = float(2.0 * np.pi / phi_axis.size)
    fr = np.asarray(feats["r_h"], float)
    fp = np.asarray(feats["phi_h"], float)
    rr = np.asarray(ref["r"], float)
    rp = np.asarray(ref["phi"], float)
    m = np.ones(fr.shape, bool) if live is None else np.asarray(live, bool)
    if not m.any():
        return {"radial_cells": float("nan"), "azimuthal_cells": float("nan"),
                "n_ages_scored": 0, "chose_global_maximum_fraction": float("nan")}
    er, ep, glob = [], [], []
    for k in np.flatnonzero(m):
        cr, cp, ca = ref["maxima"][k]
        dr = np.abs(np.log(fr[k] / cr)) / d_logr
        dp = np.abs((fp[k] - cp + np.pi) % (2.0 * np.pi) - np.pi) / d_phi
        j = int(np.argmin(dr ** 2 + dp ** 2))
        er.append(float(dr[j]))
        ep.append(float(dp[j]))
        glob.append(bool(ca[j] >= ca.max() - 1e-12))
    return {"radial_cells": float(np.max(er)),
            "azimuthal_cells": float(np.max(ep)),
            "n_ages_scored": int(m.sum()),
            "chose_global_maximum_fraction": float(np.mean(glob))}
