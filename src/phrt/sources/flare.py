"""Moving flare with birth and decay -- the held-out out-of-distribution family.

Held out because its temporal profile is compactly supported: it switches on at
a birth time, rises, and decays. The prior-fit families are all stationary or
smoothly modulated in time, so a prior fitted on them has never seen this
temporal shape. That is the point of the split, and it is why the flare family
must not appear anywhere in the prior fit.
"""
from __future__ import annotations

import numpy as np

from phrt.sources.movie import Movie, keplerian_omega, wrapped_angle


def moving_flare_birth_decay(rng, ranges: dict, baseline: float,
                             t_window: tuple[float, float],
                             off_grid: bool = False) -> Movie:
    refine = ranges.get("off_grid_refinement", 1.0) if off_grid else 1.0
    t_lo, t_hi = t_window
    r0 = float(rng.uniform(*ranges["r_centre_M"]))
    p = {
        "r0": r0,
        "sigma_r": float(rng.uniform(*ranges["sigma_r_M"]) / refine),
        "phi0": float(rng.uniform(0.0, 2 * np.pi)),
        "sigma_phi": float(rng.uniform(*ranges["sigma_phi_rad"]) / refine),
        "amplitude": float(rng.uniform(0.5, 1.5)),
        "t_birth": float(rng.uniform(t_lo + 0.1 * (t_hi - t_lo),
                                     t_hi - 0.1 * (t_hi - t_lo))),
        "rise": float(rng.uniform(*ranges["rise_M"]) / refine),
        "decay": float(rng.uniform(*ranges["decay_M"]) / refine),
        "radial_drift": float(rng.uniform(-0.05, 0.05)),
        "omega": float(keplerian_omega(r0)),
        "baseline": float(baseline),
    }

    def render(r, phi, t):
        dt = t - p["t_birth"]
        # zero before birth, then rise and decay: compactly supported in time
        env = np.where(dt < 0.0, 0.0,
                       (1.0 - np.exp(-dt / max(p["rise"], 1e-9)))
                       * np.exp(-dt / max(p["decay"], 1e-9)))
        rc = p["r0"] + p["radial_drift"] * np.clip(dt, 0.0, None)
        dr = (r - rc) / p["sigma_r"]
        dphi = wrapped_angle(phi - (p["phi0"] + p["omega"] * t)) / p["sigma_phi"]
        return p["baseline"] + p["amplitude"] * env * np.exp(
            -0.5 * (dr ** 2 + dphi ** 2))

    return Movie("moving_flare_birth_decay", p, render, off_grid=off_grid)
