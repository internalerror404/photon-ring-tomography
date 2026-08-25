"""Rotating asymmetric crescent: a radial ring with an azimuthal asymmetry
rotating rigidly at the Keplerian rate of the ring peak."""
from __future__ import annotations

import numpy as np

from phrt.sources.movie import Movie, keplerian_omega


def rotating_asymmetric_crescent(rng, ranges: dict, baseline: float,
                                 off_grid: bool = False) -> Movie:
    refine = ranges.get("off_grid_refinement", 1.0) if off_grid else 1.0
    m_lo, m_hi = ranges["asymmetry_modes"]
    p = {
        "r_peak": float(rng.uniform(*ranges["r_peak_M"])),
        "width": float(rng.uniform(*ranges["width_M"]) / refine),
        "m": int(rng.integers(int(m_lo), int(m_hi) + 1)),
        "asymmetry": float(rng.uniform(0.2, 0.9)),
        "phase": float(rng.uniform(0.0, 2 * np.pi)),
        "amplitude": float(rng.uniform(0.5, 1.5)),
        "baseline": float(baseline),
    }
    p["pattern_speed"] = float(keplerian_omega(p["r_peak"]))

    def render(r, phi, t):
        ring = np.exp(-0.5 * ((r - p["r_peak"]) / p["width"]) ** 2)
        # 1 + a cos(...) with a < 1 keeps the azimuthal factor strictly positive,
        # so the crescent never renders a negative intensity
        ang = 1.0 + p["asymmetry"] * np.cos(
            p["m"] * (phi - p["phase"] - p["pattern_speed"] * t))
        return p["baseline"] + p["amplitude"] * ring * ang

    return Movie("rotating_asymmetric_crescent", p, render, off_grid=off_grid)
