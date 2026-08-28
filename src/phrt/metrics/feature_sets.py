"""A set-valued feature measure, and an error that compares sets.

HMT-2 stage 0, item 13. HMT-1 compared one position against one position, which
forces an answer even when the field holds two features or none. A field holds a
*set* of features, possibly empty, and comparing two of those needs a distance
between sets rather than between points.

The assignment is exact rather than greedy: with the prominence filter in place
the sets are small, and an exact optimum removes a source of disagreement that
would otherwise have to be explained every time a number looked odd. Unmatched
features are not dropped and not free -- creating or destroying one costs the
largest distance the grid admits, which is derived from the grid rather than
chosen, so a method cannot improve its score by reporting fewer features.
"""
from __future__ import annotations

from itertools import permutations

import numpy as np

MAX_EXACT = 7          # beyond this the exact assignment is truncated, and said


def cell_metric(r_axis: np.ndarray, phi_axis: np.ndarray) -> dict:
    """Cell sizes and the largest distance the grid admits, in cells."""
    d_logr = float(np.log(r_axis[-1] / r_axis[0]) / (r_axis.size - 1))
    d_phi = float(2.0 * np.pi / phi_axis.size)
    diameter = float(np.hypot(r_axis.size - 1, phi_axis.size / 2.0))
    return {"d_logr": d_logr, "d_phi": d_phi, "unmatched_cost": diameter,
            "n_radial": int(r_axis.size), "n_azimuthal": int(phi_axis.size)}


def distance(a: dict, b: dict, met: dict) -> float:
    """Between two features, in level-0 grid cells."""
    dr = abs(np.log(max(a["r"], 1e-300) / max(b["r"], 1e-300))) / met["d_logr"]
    dp = abs((a["phi"] - b["phi"] + np.pi) % (2.0 * np.pi) - np.pi) / met["d_phi"]
    return float(np.hypot(dr, dp))


def assignment(A: list, B: list, met: dict) -> dict:
    """Optimal injective assignment between two feature sets.

    Returns the matched pairs, the mean matched distance, the cardinality
    difference, and the total unbalanced cost. All three are reported because
    they fail differently: a method can be accurate on what it finds and find
    the wrong number of things, and one number would hide that.
    """
    lam = met["unmatched_cost"]
    na, nb = len(A), len(B)
    if na == 0 and nb == 0:
        return {"mean_matched_cells": float("nan"), "cardinality_error": 0,
                "unbalanced_cost": 0.0, "n_matched": 0, "pairs": [],
                "exact": True}
    if na == 0 or nb == 0:
        return {"mean_matched_cells": float("nan"),
                "cardinality_error": abs(na - nb),
                "unbalanced_cost": float(lam * max(na, nb)), "n_matched": 0,
                "pairs": [], "exact": True}

    D = np.array([[distance(a, b, met) for b in B] for a in A], float)
    small, big = (D, False) if na <= nb else (D.T, True)
    ns, nl = small.shape
    exact = nl <= MAX_EXACT
    best, best_perm = None, None
    if exact:
        for perm in permutations(range(nl), ns):
            c = small[np.arange(ns), perm].sum()
            if best is None or c < best:
                best, best_perm = c, perm
    else:                                   # greedy fallback, recorded as such
        used, perm, c = set(), [], 0.0
        for i in range(ns):
            j = int(np.argmin([small[i, k] if k not in used else np.inf
                               for k in range(nl)]))
            used.add(j)
            perm.append(j)
            c += small[i, j]
        best, best_perm = c, tuple(perm)
    pairs = ([(int(p), int(i)) for i, p in enumerate(best_perm)] if big
             else [(int(i), int(p)) for i, p in enumerate(best_perm)])
    return {"mean_matched_cells": float(best / max(ns, 1)),
            "cardinality_error": int(abs(na - nb)),
            "unbalanced_cost": float(best + lam * abs(na - nb)),
            "n_matched": int(ns), "pairs": pairs, "exact": bool(exact)}


def peaks_to_features(peaks: np.ndarray, prom: np.ndarray, field: np.ndarray,
                      r_axis: np.ndarray, phi_axis: np.ndarray) -> list:
    """Flat peak indices to the set-valued feature representation."""
    npz = phi_axis.size
    out = []
    for k, pr in zip(np.atleast_1d(peaks), np.atleast_1d(prom)):
        i, j = divmod(int(k), npz)
        out.append({"r": float(r_axis[i]), "phi": float(phi_axis[j]),
                    "amplitude": float(field[i, j]), "prominence": float(pr)})
    return out


def blended_descriptors(field: np.ndarray, r_axis: np.ndarray,
                        phi_axis: np.ndarray) -> dict:
    """What a one-peak field can actually support. Item 14.

    A centroid, a size and a mode content -- not two trajectories pushed
    through a field that only ever had one peak. Weights are the positive part
    of the fluctuation: the negative part is the other side of a zero-mean
    field and is not a feature.
    """
    w = np.maximum(np.asarray(field, float), 0.0)
    tot = float(w.sum())
    if tot <= 0:
        nan = float("nan")
        return {"centroid_r": nan, "centroid_phi": nan, "total_contrast": 0.0,
                "second_moment_rr": nan, "second_moment_pp": nan,
                "second_moment_rp": nan, "a_m1": 0.0, "a_m2": 0.0}
    lr = np.log(r_axis)[:, None]
    ph = phi_axis[None, :]
    cx = float((w * np.cos(ph)).sum() / tot)
    cy = float((w * np.sin(ph)).sum() / tot)
    cphi = float(np.arctan2(cy, cx) % (2.0 * np.pi))
    clr = float((w * lr).sum() / tot)
    dlr = lr - clr
    dph = (ph - cphi + np.pi) % (2.0 * np.pi) - np.pi
    radial = w.sum(axis=1)
    m1 = float(np.abs((w * np.exp(-1j * ph)).sum()) / tot)
    m2 = float(np.abs((w * np.exp(-2j * ph)).sum()) / tot)
    return {"centroid_r": float(np.exp(clr)), "centroid_phi": cphi,
            "total_contrast": tot,
            "second_moment_rr": float((w * dlr ** 2).sum() / tot),
            "second_moment_pp": float((w * dph ** 2).sum() / tot),
            "second_moment_rp": float((w * dlr * dph).sum() / tot),
            "a_m1": m1, "a_m2": m2,
            "radial_mass_fraction_peak": float(radial.max() / max(tot, 1e-300))}


def associate_tracks(per_age: list, met: dict) -> list:
    """Follow features from one age to the next. Item 15.

    Association is the same assignment used everywhere else, so a track break
    and a position error are measured on one scale rather than two. A feature
    that cannot be matched starts a new track rather than being attached to the
    nearest survivor, because an unmatched feature is information.
    """
    tracks, next_id = [], 0
    prev_ids: list[int] = []
    for k, feats in enumerate(per_age):
        ids = [-1] * len(feats)
        if k and prev_ids:
            res = assignment(per_age[k - 1], feats, met)
            for i, j in res["pairs"]:
                if distance(per_age[k - 1][i], feats[j], met) <= met["unmatched_cost"]:
                    ids[j] = prev_ids[i]
        for j in range(len(feats)):
            if ids[j] < 0:
                ids[j] = next_id
                next_id += 1
        tracks.append(ids)
        prev_ids = ids
    return tracks
