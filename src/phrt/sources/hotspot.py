"""Orbiting hotspot families, one and two spots."""
from __future__ import annotations

import numpy as np

from phrt.sources.movie import Movie, keplerian_omega, wrapped_angle


def _spot(r, phi, t, r0, sr, phi0, sphi, amp, omega):
    dr = (r - r0) / sr
    dphi = wrapped_angle(phi - (phi0 + omega * t)) / sphi
    return amp * np.exp(-0.5 * (dr ** 2 + dphi ** 2))


def single_orbiting_hotspot(rng, ranges: dict, baseline: float,
                            off_grid: bool = False) -> Movie:
    refine = ranges.get("off_grid_refinement", 1.0) if off_grid else 1.0
    p = {
        "r0": float(rng.uniform(*ranges["r_centre_M"])),
        "sigma_r": float(rng.uniform(*ranges["sigma_r_M"]) / refine),
        "phi0": float(rng.uniform(0.0, 2 * np.pi)),
        "sigma_phi": float(rng.uniform(*ranges["sigma_phi_rad"]) / refine),
        "amplitude": float(rng.uniform(0.5, 1.5)),
        "baseline": float(baseline),
    }
    p["omega"] = float(keplerian_omega(p["r0"]))

    def render(r, phi, t):
        return p["baseline"] + _spot(r, phi, t, p["r0"], p["sigma_r"],
                                     p["phi0"], p["sigma_phi"],
                                     p["amplitude"], p["omega"])

    return Movie("single_orbiting_hotspot", p, render, off_grid=off_grid)


def two_independent_hotspots(rng, ranges: dict, baseline: float,
                             off_grid: bool = False) -> Movie:
    refine = ranges.get("off_grid_refinement", 1.0) if off_grid else 1.0
    spots = []
    for _ in range(2):
        r0 = float(rng.uniform(*ranges["r_centre_M"]))
        spots.append({
            "r0": r0, "sigma_r": float(rng.uniform(*ranges["sigma_r_M"]) / refine),
            "phi0": float(rng.uniform(0.0, 2 * np.pi)),
            "sigma_phi": float(rng.uniform(*ranges["sigma_phi_rad"]) / refine),
            "amplitude": float(rng.uniform(0.5, 1.5)),
            "omega": float(keplerian_omega(r0))})
    p = {"spots": spots, "baseline": float(baseline)}

    def render(r, phi, t):
        out = np.full(np.shape(r), p["baseline"], dtype=float)
        for s in p["spots"]:
            out = out + _spot(r, phi, t, s["r0"], s["sigma_r"], s["phi0"],
                              s["sigma_phi"], s["amplitude"], s["omega"])
        return out

    return Movie("two_independent_hotspots", p, render, off_grid=off_grid)
