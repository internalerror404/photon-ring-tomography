"""Correlated extended field, positive by construction.

An exponentiated Gaussian field: the log-intensity is a smooth random field
built from a small number of radial, azimuthal and temporal modes with a power-
law temporal spectrum, and exponentiating it makes the rendered intensity
strictly positive without any clipping. Clipping would introduce a hard
non-linearity at the floor and make the "positive by construction" claim false
in exactly the places it matters.
"""
from __future__ import annotations

import numpy as np

from phrt.sources.movie import Movie


def correlated_extended_field(rng, ranges: dict, baseline: float,
                              r_support: tuple[float, float],
                              t_window: tuple[float, float],
                              off_grid: bool = False) -> Movie:
    refine = ranges.get("off_grid_refinement", 1.0) if off_grid else 1.0
    r_in, r_out = r_support
    t_lo, t_hi = t_window
    m_lo, m_hi = ranges["azimuthal_modes"]
    n_modes = 6
    lr = float(rng.uniform(*ranges["radial_correlation_M"]) / refine)
    p = {
        "radial_correlation": lr,
        "temporal_exponent": float(rng.uniform(1.0, 3.0)),
        "log_amplitude": float(rng.uniform(0.2, 0.8)),
        "baseline": float(baseline),
        "r_in": float(r_in), "r_out": float(r_out),
        "t_lo": float(t_lo), "t_hi": float(t_hi),
        "modes": [],
    }
    for k in range(n_modes):
        p["modes"].append({
            "kr": float(rng.uniform(0.5, max(1.0, (r_out - r_in) / lr))),
            "m": int(rng.integers(int(m_lo), int(m_hi) + 1)),
            "kt": int(rng.integers(0, 6)),
            "phase_r": float(rng.uniform(0, 2 * np.pi)),
            "phase_phi": float(rng.uniform(0, 2 * np.pi)),
            "weight": float(rng.normal()),
        })

    def render(r, phi, t):
        span_r = max(p["r_out"] - p["r_in"], 1e-9)
        span_t = max(p["t_hi"] - p["t_lo"], 1e-9)
        u = (r - p["r_in"]) / span_r
        v = (t - p["t_lo"]) / span_t
        g = np.zeros(np.shape(r), dtype=float)
        for md in p["modes"]:
            # power-law temporal spectrum: higher temporal index contributes less
            damp = (1.0 + md["kt"]) ** (-p["temporal_exponent"] / 2.0)
            g = g + md["weight"] * damp * (
                np.cos(2 * np.pi * md["kr"] * u + md["phase_r"])
                * np.cos(md["m"] * phi + md["phase_phi"])
                * np.cos(np.pi * md["kt"] * v))
        g = g / np.sqrt(len(p["modes"]))
        return p["baseline"] * np.exp(p["log_amplitude"] * g)

    return Movie("correlated_extended_field", p, render, off_grid=off_grid)
