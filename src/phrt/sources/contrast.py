"""Positive-background contrast movies: j = b(r,t) + dj(r,phi,t).

HMT-1. The object here is not an emissivity field with structure bolted on, it
is a positive axisymmetric background carrying a signed fluctuation. Motion and
morphology live in the fluctuation; the background carries the flux.

The distinction matters because it is what separates this from the signed
constant-flux bank R1L had to disqualify. There the *emissivity* went negative,
which is not a physical source. Here ``dj`` is signed by construction and
``b + dj`` is non-negative by construction, so the physical field is positive
and the modelled fluctuation is free to change sign.

Each family also returns the generative trajectory it was drawn from --
``r_h(t)``, ``phi_h(t)``, amplitudes, birth and decay times -- so the recovered
trajectory can be compared against what actually happened rather than against a
re-extraction of the same estimate.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from phrt.sources.movie import wrapped_angle
from phrt.sources.orbits import isco_radius, kerr_omega, plunge_omega

FAMILIES = ("circular_hotspot_trajectory", "two_hotspot_trajectories",
            "m1_rotating_crescent", "m2_structural_mode",
            "flare_birth_motion_decay", "plunging_feature")
OFF_MANIFOLD = ("three_hotspot_cluster", "counter_rotating_pair",
                "radially_drifting_arc")
POSITIVITY_MARGIN = 0.02          # keep b + dj strictly above zero
BACKGROUND_FLOOR = 1e-6


@dataclass
class ContrastMovie:
    """A background, a fluctuation, and the trajectory that generated it."""

    family: str
    params: dict
    background: "callable"
    fluctuation: "callable"
    trajectory: "callable"        # age -> dict of generative feature values
    off_manifold: bool = False
    extra: dict = field(default_factory=dict)

    def total(self, r, phi, t):
        return self.background(r, t) + self.fluctuation(r, phi, t)


def background_field(rng, r_inner: float, r_outer: float) -> tuple:
    """A positive, axisymmetric, slowly varying background.

    A radial power law with a slow temporal breathing mode. Positive by
    construction rather than by clipping, because a background that has to be
    clipped is one whose positivity the estimator could exploit.
    """
    p = {"amplitude": float(rng.uniform(0.8, 1.4)),
         "slope": float(rng.uniform(0.8, 1.8)),
         "r_scale": float(rng.uniform(6.0, 14.0)),
         "breathe": float(rng.uniform(0.05, 0.20)),
         "breathe_period_M": float(rng.uniform(60.0, 160.0)),
         "floor": 0.15}

    def b(r, t):
        rr = np.maximum(np.asarray(r, float), r_inner)
        radial = (1.0 + (rr / p["r_scale"]) ** 2) ** (-0.5 * p["slope"])
        temporal = 1.0 + p["breathe"] * np.sin(
            2 * np.pi * np.asarray(t, float) / p["breathe_period_M"])
        return p["amplitude"] * radial * temporal + p["floor"]

    return b, p


def _blob(r, phi, t, r0, sr, phi0, sphi, omega):
    dr = (np.asarray(r, float) - r0) / sr
    dphi = wrapped_angle(np.asarray(phi, float) - (phi0 + omega * np.asarray(t, float))) / sphi
    return np.exp(-0.5 * (dr ** 2 + dphi ** 2))


def _circular_radius(rng, spin, r_outer):
    return float(rng.uniform(isco_radius(spin) * 1.05, r_outer))


def _raw_family(rng, family: str, spin: float, r_outer: float):
    """The unnormalised fluctuation shape and its generative trajectory."""
    if family == "circular_hotspot_trajectory":
        r0 = _circular_radius(rng, spin, r_outer)
        p = {"r_h": r0, "phi_h_0": float(rng.uniform(0, 2 * np.pi)),
             "A_h": float(rng.uniform(0.5, 1.5)),
             "sigma_r": float(rng.uniform(1.5, 4.0)),
             "sigma_phi": float(rng.uniform(0.35, 0.9)),
             "omega": float(kerr_omega(r0, spin))}

        def shape(r, phi, t):
            return p["A_h"] * _blob(r, phi, t, p["r_h"], p["sigma_r"],
                                    p["phi_h_0"], p["sigma_phi"], p["omega"])

        def traj(a):
            return {"r_h": p["r_h"],
                    "phi_h": float(wrapped_angle(np.array(
                        [p["phi_h_0"] + p["omega"] * (-a)]))[0]),
                    "A_h": p["A_h"]}
        return shape, traj, p

    if family == "two_hotspot_trajectories":
        spots = []
        for _ in range(2):
            r0 = _circular_radius(rng, spin, r_outer)
            spots.append({"r": r0, "phi0": float(rng.uniform(0, 2 * np.pi)),
                          "A": float(rng.uniform(0.5, 1.5)),
                          "sr": float(rng.uniform(1.5, 4.0)),
                          "sphi": float(rng.uniform(0.35, 0.9)),
                          "omega": float(kerr_omega(r0, spin))})
        p = {"spots": spots, "r_h1": spots[0]["r"], "r_h2": spots[1]["r"]}

        def shape(r, phi, t):
            out = np.zeros(np.shape(r), dtype=float)
            for sp in spots:
                out = out + sp["A"] * _blob(r, phi, t, sp["r"], sp["sr"],
                                            sp["phi0"], sp["sphi"], sp["omega"])
            return out

        def traj(a):
            lead = max(spots, key=lambda s: s["A"])
            return {"r_h": lead["r"],
                    "phi_h": float(wrapped_angle(np.array(
                        [lead["phi0"] + lead["omega"] * (-a)]))[0]),
                    "A_h": lead["A"]}
        return shape, traj, p

    if family in ("m1_rotating_crescent", "m2_structural_mode"):
        m = 1 if family == "m1_rotating_crescent" else 2
        r0 = _circular_radius(rng, spin, r_outer)
        p = {"r_peak": r0, "width": float(rng.uniform(3.0, 9.0)),
             "pattern_phase": float(rng.uniform(0, 2 * np.pi)),
             "a_m": float(rng.uniform(0.5, 1.5)), "m": m,
             "omega": float(kerr_omega(r0, spin))}

        def shape(r, phi, t):
            radial = np.exp(-0.5 * ((np.asarray(r, float) - p["r_peak"])
                                    / p["width"]) ** 2)
            ang = np.cos(m * (np.asarray(phi, float) - p["pattern_phase"]
                              - p["omega"] * np.asarray(t, float)))
            return p["a_m"] * radial * ang

        def traj(a):
            return {f"a_m{m}": p["a_m"], "r_peak": p["r_peak"],
                    "pattern_phase": float(wrapped_angle(np.array(
                        [p["pattern_phase"] + p["omega"] * (-a)]))[0])}
        return shape, traj, p

    if family == "flare_birth_motion_decay":
        r0 = _circular_radius(rng, spin, r_outer)
        p = {"r_h": r0, "phi_h_0": float(rng.uniform(0, 2 * np.pi)),
             "A_peak": float(rng.uniform(0.6, 1.6)),
             "sigma_r": float(rng.uniform(1.5, 4.0)),
             "sigma_phi": float(rng.uniform(0.35, 0.9)),
             "omega": float(kerr_omega(r0, spin)),
             "t_birth": float(rng.uniform(-95.0, -35.0)),
             "tau_decay": float(rng.uniform(12.0, 35.0)),
             "rise_M": 6.0}

        def envelope(t):
            tt = np.asarray(t, float)
            rise = 1.0 / (1.0 + np.exp(-(tt - p["t_birth"]) / p["rise_M"]))
            decay = np.exp(-np.maximum(tt - p["t_birth"], 0.0) / p["tau_decay"])
            return rise * decay

        def shape(r, phi, t):
            return p["A_peak"] * envelope(t) * _blob(
                r, phi, t, p["r_h"], p["sigma_r"], p["phi_h_0"],
                p["sigma_phi"], p["omega"])

        def traj(a):
            return {"r_h": p["r_h"],
                    "phi_h": float(wrapped_angle(np.array(
                        [p["phi_h_0"] + p["omega"] * (-a)]))[0]),
                    "A_h": float(p["A_peak"] * envelope(-a)),
                    "t_birth_age_M": -p["t_birth"],
                    "tau_decay_M": p["tau_decay"]}
        return shape, traj, p

    if family == "plunging_feature":
        r_h = 1.0 + np.sqrt(1.0 - spin ** 2)
        r_i = isco_radius(spin)
        r0 = float(rng.uniform(r_h * 1.08, r_i * 0.95))
        p = {"r_h_start": r0, "phi_h_0": float(rng.uniform(0, 2 * np.pi)),
             "A_h": float(rng.uniform(0.5, 1.5)),
             "sigma_r": float(rng.uniform(0.4, 1.1)),
             "sigma_phi": float(rng.uniform(0.35, 0.9)),
             "omega": float(plunge_omega(r0, spin))}

        def shape(r, phi, t):
            return p["A_h"] * _blob(r, phi, t, p["r_h_start"], p["sigma_r"],
                                    p["phi_h_0"], p["sigma_phi"], p["omega"])

        def traj(a):
            return {"r_h": p["r_h_start"],
                    "phi_h": float(wrapped_angle(np.array(
                        [p["phi_h_0"] + p["omega"] * (-a)]))[0]),
                    "A_h": p["A_h"]}
        return shape, traj, p

    # ---- off-manifold controls, deliberately outside the declared set ----
    if family == "three_hotspot_cluster":
        spots = [{"r": _circular_radius(rng, spin, r_outer),
                  "phi0": float(rng.uniform(0, 2 * np.pi)),
                  "A": float(rng.uniform(0.4, 1.2)),
                  "sr": float(rng.uniform(1.2, 3.0)),
                  "sphi": float(rng.uniform(0.3, 0.7))} for _ in range(3)]
        for sp in spots:
            sp["omega"] = float(kerr_omega(sp["r"], spin))
        p = {"spots": spots}

        def shape(r, phi, t):
            out = np.zeros(np.shape(r), dtype=float)
            for sp in spots:
                out = out + sp["A"] * _blob(r, phi, t, sp["r"], sp["sr"],
                                            sp["phi0"], sp["sphi"], sp["omega"])
            return out
        return shape, (lambda a: {}), p

    if family == "counter_rotating_pair":
        r1 = _circular_radius(rng, spin, r_outer)
        r2 = _circular_radius(rng, spin, r_outer)
        p = {"r1": r1, "r2": r2, "phi1": float(rng.uniform(0, 2 * np.pi)),
             "phi2": float(rng.uniform(0, 2 * np.pi)),
             "w1": float(kerr_omega(r1, spin)),
             "w2": -float(kerr_omega(r2, spin, -1))}

        def shape(r, phi, t):
            return (_blob(r, phi, t, r1, 2.5, p["phi1"], 0.6, p["w1"])
                    - _blob(r, phi, t, r2, 2.5, p["phi2"], 0.6, p["w2"]))
        return shape, (lambda a: {}), p

    if family == "radially_drifting_arc":
        p = {"r0": _circular_radius(rng, spin, r_outer),
             "drift": float(rng.uniform(-0.06, -0.02)),
             "phi0": float(rng.uniform(0, 2 * np.pi)),
             "width": float(rng.uniform(2.0, 5.0))}

        def shape(r, phi, t):
            rc = p["r0"] + p["drift"] * np.asarray(t, float)
            return np.exp(-0.5 * ((np.asarray(r, float) - rc) / p["width"]) ** 2) \
                * np.cos(np.asarray(phi, float) - p["phi0"])
        return shape, (lambda a: {}), p

    raise ValueError(f"unknown family {family!r}")


def build(rng, family: str, spin: float, r_inner: float, r_outer: float,
          grid_r, grid_phi, grid_t, t_index, n_t: int) -> tuple:
    """One contrast movie, with the two constraints enforced by construction.

    Zero spatial mean is imposed per age slice; the fluctuation is then scaled
    by the largest factor keeping ``b + dj`` above zero. Both operations are
    reported: the achieved contrast fraction is what the operator saw, not the
    amplitude the family was drawn with.
    """
    b, bp = background_field(rng, r_inner, r_outer)
    shape, traj, fp = _raw_family(rng, family, spin, r_outer)

    bg = b(grid_r, grid_t)
    raw = np.asarray(shape(grid_r, grid_phi, grid_t), dtype=float)
    # zero spatial mean at every age
    for k in range(n_t):
        m = t_index == k
        if m.any():
            raw[m] -= raw[m].mean()
    neg = np.maximum(-raw / np.maximum(bg, BACKGROUND_FLOOR), 0.0).max()
    alpha = 1.0 if neg <= 0 else min(1.0, (1.0 - POSITIVITY_MARGIN) / neg)
    dj = alpha * raw

    def fluctuation(r, phi, t):
        v = alpha * np.asarray(shape(r, phi, t), dtype=float)
        return v - alpha * _mean_correction(shape, grid_r, grid_phi, grid_t,
                                            t_index, n_t, t)

    diag = {"background_params": bp, "feature_params": fp,
            "positivity_scale": float(alpha),
            "contrast_fraction": float(np.linalg.norm(dj)
                                       / max(np.linalg.norm(bg + dj), 1e-300)),
            "min_total": float((bg + dj).min()),
            "min_background": float(bg.min()),
            "zero_mean_max_abs": float(max(
                abs(dj[t_index == k].mean()) for k in range(n_t)
                if (t_index == k).any())),
            "family": family}
    return b, fluctuation, traj, dj, bg, diag


def _mean_correction(shape, grid_r, grid_phi, grid_t, t_index, n_t, t):
    """The per-age spatial mean of the raw shape, evaluated at arbitrary times.

    The zero-mean constraint is defined on the evaluation grid, so making it
    hold at scattered ray times needs the same per-age mean evaluated there.
    Tabulated on the grid's own age axis and interpolated, which is exact at the
    grid and smooth between it.
    """
    ages = np.array([grid_t[t_index == k][0] for k in range(n_t)
                     if (t_index == k).any()])
    means = np.array([np.asarray(shape(grid_r[t_index == k],
                                       grid_phi[t_index == k],
                                       grid_t[t_index == k]), float).mean()
                      for k in range(n_t) if (t_index == k).any()])
    order = np.argsort(ages)
    return np.interp(np.asarray(t, float), ages[order], means[order])
