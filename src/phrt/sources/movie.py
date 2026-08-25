"""The common interface for a source movie and its content hash.

A movie is a callable ``j(r, phi, t) -> intensity`` evaluated at scattered
coordinates, because the operator samples the source wherever the rays land and
there is no grid to interpolate on. Every family renders a strictly positive
intensity: a positive baseline plus non-negative components.

The content hash is over the family name and the rounded parameter dictionary,
not over the rendered values. Two truths with the same physics therefore hash
identically no matter which split drew them, which is what makes the split
disjointness check in ``R0_G11`` meaningful rather than a tautology about seeds.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Callable

import numpy as np

HASH_DECIMALS = 9


@dataclass
class Movie:
    family: str
    params: dict
    render: Callable[[np.ndarray, np.ndarray, np.ndarray], np.ndarray]
    split: str = ""
    off_grid: bool = False
    extra: dict = field(default_factory=dict)

    @property
    def content_hash(self) -> str:
        def norm(v):
            if isinstance(v, (list, tuple, np.ndarray)):
                return [norm(x) for x in np.asarray(v).tolist()]
            if isinstance(v, (float, np.floating)):
                return round(float(v), HASH_DECIMALS)
            if isinstance(v, (int, np.integer)):
                return int(v)
            if isinstance(v, dict):
                return {k: norm(x) for k, x in sorted(v.items())}
            return v
        payload = json.dumps({"family": self.family,
                              "params": norm(self.params),
                              "off_grid": self.off_grid},
                             sort_keys=True).encode()
        return hashlib.sha256(payload).hexdigest()

    def __call__(self, r, phi, t):
        out = self.render(np.asarray(r, float), np.asarray(phi, float),
                          np.asarray(t, float))
        return out


def keplerian_omega(r: np.ndarray | float) -> np.ndarray | float:
    """Newtonian-Keplerian angular rate in M units, the declared orbit law."""
    return np.power(np.asarray(r, float), -1.5)


def wrapped_angle(d: np.ndarray) -> np.ndarray:
    """Shortest signed angular difference, so an azimuthal blob does not tear
    at the phi = 0 seam."""
    return (d + np.pi) % (2.0 * np.pi) - np.pi
