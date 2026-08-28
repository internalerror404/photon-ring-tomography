"""Topographic prominence, and what a windowed field actually contains.

HMT-2 stage 0, item 12. The question HMT-1 answered badly was "where is the
feature", asked of fields that sometimes had two features and sometimes had one
that the grid could not split. Asking it as a single argmax gave an answer every
time, including the times there was no such thing to answer.

Prominence is the standard way to tell a real second peak from a bump on the
first one's shoulder. Every local maximum is assigned the height it stands above
the highest saddle that connects it to any higher maximum: a genuinely separate
feature stands high above its saddle, a shoulder barely stands above it at all.
The computation is the usual descending-threshold union-find, which is exact
rather than a heuristic and needs no smoothing parameter.

The azimuthal axis wraps and the radial axis does not, which is handled in the
neighbour list rather than by padding, because padding a periodic axis creates
maxima that are not there.
"""
from __future__ import annotations

from functools import lru_cache

import numpy as np

STATES = ("SINGLE_RESOLVED", "MULTI_RESOLVED", "BLENDED", "DEAD", "AMBIGUOUS")


@lru_cache(maxsize=16)
def _adjacency(nr: int, npz: int):
    """8-connected neighbours as a flat CSR pair, phi periodic and r not.

    Cached by shape. Rebuilding this per map cost more than the union-find it
    feeds: the audit classifies a few hundred maps per truth and they all share
    a handful of shapes.
    """
    idx = np.arange(nr * npz).reshape(nr, npz)
    a_all, b_all = [], []
    for dr in (-1, 0, 1):
        for dp in (-1, 0, 1):
            if dr == 0 and dp == 0:
                continue
            b = np.roll(idx, (-dr, -dp), axis=(0, 1))
            a = idx
            if dr > 0:
                a, b = a[:-1], b[:-1]
            elif dr < 0:
                a, b = a[1:], b[1:]
            a_all.append(a.ravel())
            b_all.append(b.ravel())
    a = np.concatenate(a_all)
    b = np.concatenate(b_all)
    o = np.argsort(a, kind="stable")
    a, b = a[o], b[o]
    start = np.searchsorted(a, np.arange(nr * npz))
    end = np.searchsorted(a, np.arange(nr * npz), side="right")
    return b, start, end


class _DSU:
    __slots__ = ("p", "peak")

    def __init__(self, n):
        self.p = np.full(n, -1, dtype=np.int64)
        self.peak = {}

    def find(self, a):
        r = a
        while self.p[r] >= 0:
            r = self.p[r]
        while self.p[a] >= 0:
            self.p[a], a = r, self.p[a]
        return r


def prominences(field: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Local maxima of a 2-d (r, phi) map and their topographic prominence.

    Returns the flat indices of the maxima and their prominences. The global
    maximum's prominence is its height above the field's floor, which is the
    usual convention and makes it always the most prominent thing present.
    """
    m = np.asarray(field, float)
    nr, npz = m.shape
    flat = np.ascontiguousarray(m.ravel())
    order = np.argsort(-flat, kind="stable")
    nbr, start, end = _adjacency(nr, npz)

    dsu = _DSU(nr * npz)
    seen = np.zeros(nr * npz, bool)
    prom = {}
    for c in order:
        c = int(c)
        roots = set()
        for n_ in nbr[start[c]:end[c]]:
            if seen[n_]:
                roots.add(dsu.find(int(n_)))
        seen[c] = True
        if not roots:
            dsu.peak[c] = flat[c]
            prom[c] = None                      # still open
            continue
        roots = sorted(roots, key=lambda r: -dsu.peak[r])
        keep = roots[0]
        dsu.p[c] = keep
        for r in roots[1:]:
            # r dies here: this cell is the saddle joining it to something taller
            prom[r] = dsu.peak[r] - flat[c]
            dsu.p[r] = keep
    floor = float(flat.min())
    peaks, vals = [], []
    for c, p in prom.items():
        peaks.append(int(c))
        vals.append(float(dsu.peak[c] - floor if p is None else p))
    if not peaks:                               # a perfectly flat field
        peaks, vals = [int(order[0])], [0.0]
    o = np.argsort(-np.asarray(vals))
    return np.asarray(peaks)[o], np.asarray(vals)[o]


def classify(field: np.ndarray, expected_multiplicity: int,
             age_max: float, truth_max: float, fraction: float) -> dict:
    """One age of one truth: what is present, and is it separable.

    ``fraction`` is the frozen prominence and dead threshold, reused from the
    campaign's declared birth fraction rather than invented here.
    """
    if truth_max <= 0 or age_max < fraction * truth_max:
        return {"state": "DEAD", "n_prominent": 0, "peaks": np.zeros(0, int),
                "prominences": np.zeros(0), "n_local_maxima": 0}
    idx, prom = prominences(field)
    keep = prom >= fraction * max(age_max, 1e-300)
    n = int(keep.sum())
    if n >= 2:
        state = "MULTI_RESOLVED"
    elif expected_multiplicity >= 2:
        state = "BLENDED"
    else:
        state = "SINGLE_RESOLVED"
    return {"state": state, "n_prominent": n, "peaks": idx[keep],
            "prominences": prom[keep], "n_local_maxima": int(idx.size)}


def reconcile(label_fine: str, label_coarser: str) -> str:
    """AMBIGUOUS is disagreement between the two finest levels, and nothing else.

    Item 12 asks that the classification be stable under the final two
    refinement levels. Making instability the definition of AMBIGUOUS, rather
    than adding a tolerance band and then checking stability separately, means
    the requirement cannot be satisfied by widening a band.
    """
    return label_fine if label_fine == label_coarser else "AMBIGUOUS"
