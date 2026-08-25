"""Deterministic source bank: families, splits, seeds and content hashes.

Every truth is produced from a labelled seed stream so that a rerun reproduces
it bitwise, and carries a content hash over its physical parameters so that the
disjointness of the splits is a checkable property of the *movies* rather than
an assumption about the seeds.

The split roles are frozen: the flare family is held out and never enters the
prior fit, and the future main-test bank is generated and hashed here but never
rendered or scored.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from phrt.sources.crescent import rotating_asymmetric_crescent
from phrt.sources.flare import moving_flare_birth_decay
from phrt.sources.gaussian_field import correlated_extended_field
from phrt.sources.hotspot import single_orbiting_hotspot, two_independent_hotspots
from phrt.sources.movie import Movie

PHYSICAL_FAMILIES = ("single_orbiting_hotspot", "two_independent_hotspots",
                     "rotating_asymmetric_crescent", "correlated_extended_field",
                     "moving_flare_birth_decay")
BASELINE = 1.0


@dataclass(frozen=True)
class BankContext:
    ranges: dict
    r_support: tuple[float, float]
    t_window: tuple[float, float]


def make_movie(family: str, rng, ctx: BankContext, off_grid: bool = False) -> Movie:
    rg = dict(ctx.ranges[family])
    if off_grid:
        rg["off_grid_refinement"] = float(ctx.ranges["off_grid_refinement"])
    if family == "single_orbiting_hotspot":
        return single_orbiting_hotspot(rng, rg, BASELINE, off_grid)
    if family == "two_independent_hotspots":
        return two_independent_hotspots(rng, rg, BASELINE, off_grid)
    if family == "rotating_asymmetric_crescent":
        return rotating_asymmetric_crescent(rng, rg, BASELINE, off_grid)
    if family == "correlated_extended_field":
        return correlated_extended_field(rng, rg, BASELINE, ctx.r_support,
                                         ctx.t_window, off_grid)
    if family == "moving_flare_birth_decay":
        return moving_flare_birth_decay(rng, rg, BASELINE, ctx.t_window, off_grid)
    raise ValueError(f"unknown family {family!r}")


def stream(master: int, offset: int, index: int) -> np.random.Generator:
    """A generator for one truth, keyed by stream offset and index.

    Keying on (offset, index) rather than advancing a shared generator means a
    truth's parameters do not depend on how many truths were drawn before it,
    so changing one split's count cannot silently move another split's content.
    """
    return np.random.default_rng([master, offset, index])


def build_split(family: str, split: str, n: int, master: int, offset: int,
                ctx: BankContext, off_grid: bool = False) -> list[Movie]:
    out = []
    for i in range(n):
        m = make_movie(family, stream(master, offset, i), ctx, off_grid)
        m.split = split
        out.append(m)
    return out


def hash_set(movies) -> set[str]:
    return {m.content_hash for m in movies}


def disjointness_report(groups: dict[str, list[Movie]]) -> dict:
    """Pairwise content-hash overlap between every pair of splits.

    Reported as a full matrix rather than a single boolean so that a leak shows
    which two splits it is between.
    """
    hashes = {k: hash_set(v) for k, v in groups.items()}
    keys = sorted(hashes)
    overlaps, worst = {}, 0
    for i, a in enumerate(keys):
        for b in keys[i + 1:]:
            n = len(hashes[a] & hashes[b])
            overlaps[f"{a}|{b}"] = n
            worst = max(worst, n)
    return {"sizes": {k: len(v) for k, v in hashes.items()},
            "unique_sizes": {k: len(v) for k, v in hashes.items()},
            "pairwise_overlap": overlaps, "worst_overlap": worst,
            "disjoint": worst == 0}
