"""Source banks whose primary signal is structure, not total level.

REVIEWER_RULING_R1L_REPRODUCIBILITY_009 item 7, implementing section B of the
R1L freeze.

The R1 primary was baseline-inclusive, and the level component carried 98.4% of
the truth norm. A metric dominated by one scalar per age slice can report a deep
reconstruction while recovering no morphology at all, so "how deep can the
history be recovered" and "how deep can the *shape* of the history be recovered"
were not separated. These banks separate them by construction rather than by
reweighting after the fact.

Two primary constructions:

``constant_flux``
    every age slice renormalized to a fixed spatial mean. The level component is
    then constant in time, carries no information, and cannot inflate the
    endpoint. Morphology still moves.

``structure_balanced``
    ``j = b(t) + s(r, phi, t)`` with the structure fraction fixed *before*
    sampling. The baseline is the smallest one that keeps the movie non-negative
    at the target fraction, so positivity is bought at the minimum cost in level
    dominance rather than by letting the baseline grow until the arithmetic is
    comfortable.

Both are measured against the declared evaluation grid and the level projector
of REVIEWER_RULING_R0C_005, so "structure fraction" means the same thing here as
in every error the campaign already reports.
"""
from __future__ import annotations

import numpy as np

from phrt.sources.movie import Movie, wrapped_angle
from phrt.sources.orbits import isco_radius, kerr_omega, plunge_omega

FAMILIES = ("circular_single_hotspot", "circular_two_hotspots",
            "circular_crescent", "plunging_hotspot")


def _blob(r, phi, t, r0, sr, phi0, sphi, amp, omega):
    dr = (r - r0) / sr
    dphi = wrapped_angle(phi - (phi0 + omega * t)) / sphi
    return amp * np.exp(-0.5 * (dr ** 2 + dphi ** 2))


def _circular_radius(rng, spin, r_outer):
    """A centre strictly outside the ISCO, where a circular orbit exists."""
    return float(rng.uniform(isco_radius(spin) * 1.02, r_outer))


def circular_single_hotspot(rng, spin: float, r_outer: float) -> Movie:
    r0 = _circular_radius(rng, spin, r_outer)
    p = {"r0": r0, "sigma_r": float(rng.uniform(2.38, 12.50)),
         "phi0": float(rng.uniform(0.0, 2 * np.pi)),
         "sigma_phi": float(rng.uniform(0.524, 1.571)),
         "amplitude": float(rng.uniform(0.5, 1.5)),
         "omega": float(kerr_omega(r0, spin)), "spin": float(spin),
         "orbit": "kerr_prograde_circular"}

    def render(r, phi, t):
        return _blob(r, phi, t, p["r0"], p["sigma_r"], p["phi0"],
                     p["sigma_phi"], p["amplitude"], p["omega"])

    return Movie("circular_single_hotspot", p, render)


def circular_two_hotspots(rng, spin: float, r_outer: float) -> Movie:
    spots = []
    for _ in range(2):
        r0 = _circular_radius(rng, spin, r_outer)
        spots.append({"r0": r0, "sigma_r": float(rng.uniform(2.38, 12.50)),
                      "phi0": float(rng.uniform(0.0, 2 * np.pi)),
                      "sigma_phi": float(rng.uniform(0.524, 1.571)),
                      "amplitude": float(rng.uniform(0.5, 1.5)),
                      "omega": float(kerr_omega(r0, spin))})
    p = {"spots": spots, "spin": float(spin), "orbit": "kerr_prograde_circular"}

    def render(r, phi, t):
        out = np.zeros(np.shape(r), dtype=float)
        for s in p["spots"]:
            out = out + _blob(r, phi, t, s["r0"], s["sigma_r"], s["phi0"],
                              s["sigma_phi"], s["amplitude"], s["omega"])
        return out

    return Movie("circular_two_hotspots", p, render)


def circular_crescent(rng, spin: float, r_outer: float) -> Movie:
    r0 = _circular_radius(rng, spin, r_outer)
    p = {"r_peak": r0, "width": float(rng.uniform(4.76, 14.99)),
         "phi0": float(rng.uniform(0.0, 2 * np.pi)),
         "m": int(rng.integers(1, 4)),
         "contrast": float(rng.uniform(0.3, 0.9)),
         "pattern_speed": float(kerr_omega(r0, spin)), "spin": float(spin),
         "orbit": "kerr_prograde_rigid_pattern"}

    def render(r, phi, t):
        radial = np.exp(-0.5 * ((r - p["r_peak"]) / p["width"]) ** 2)
        ang = 1.0 + p["contrast"] * np.cos(
            p["m"] * (phi - p["phi0"] - p["pattern_speed"] * t))
        return radial * ang

    return Movie("circular_crescent", p, render)


def plunging_hotspot(rng, spin: float, r_outer: float) -> Movie:
    """Inside the ISCO, on the plunge law. A separate family, never averaged
    with circular material: frame dragging locks the rate to a/(2 r_+) at the
    horizon, so the pattern turns over rather than spinning up."""
    r_h = 1.0 + np.sqrt(1.0 - float(spin) ** 2)
    r_i = isco_radius(spin)
    r0 = float(rng.uniform(r_h * 1.02, r_i * 0.98))
    p = {"r0": r0, "sigma_r": float(rng.uniform(0.3, 1.0)),
         "phi0": float(rng.uniform(0.0, 2 * np.pi)),
         "sigma_phi": float(rng.uniform(0.524, 1.571)),
         "amplitude": float(rng.uniform(0.5, 1.5)),
         "omega": float(plunge_omega(r0, spin)), "spin": float(spin),
         "orbit": "kerr_plunge_on_isco_constants"}

    def render(r, phi, t):
        return _blob(r, phi, t, p["r0"], p["sigma_r"], p["phi0"],
                     p["sigma_phi"], p["amplitude"], p["omega"])

    return Movie("plunging_hotspot", p, render)


BUILDERS = {"circular_single_hotspot": circular_single_hotspot,
            "circular_two_hotspots": circular_two_hotspots,
            "circular_crescent": circular_crescent,
            "plunging_hotspot": plunging_hotspot}


# --------------------------------------------------------------------------
# bank shaping on the declared evaluation grid


def structure_fraction(values: np.ndarray, level: np.ndarray) -> float:
    """``||P_structure j|| / ||j||`` on the evaluation grid."""
    v = np.asarray(values, float).ravel()
    lev = level @ (level.T @ v)
    n = np.linalg.norm(v)
    return float(np.linalg.norm(v - lev) / max(n, 1e-300))


def slice_means(values: np.ndarray, t_index: np.ndarray, n_t: int) -> np.ndarray:
    """Spatial mean of each age slice."""
    out = np.zeros(n_t)
    for k in range(n_t):
        out[k] = values[t_index == k].mean()
    return out


def constant_flux(values: np.ndarray, t_index: np.ndarray, n_t: int,
                  target_mean: float = 1.0,
                  floor: float = 1e-9) -> tuple[np.ndarray, dict]:
    """Renormalize each age slice to a fixed spatial mean.

    A slice whose mean is at the floor is left alone rather than divided by
    almost zero: scaling it up would manufacture morphology out of numerical
    dust and then report recovering it.
    """
    v = np.asarray(values, float).copy()
    m = slice_means(v, t_index, n_t)
    scaled = 0
    for k in range(n_t):
        if m[k] > floor:
            v[t_index == k] *= target_mean / m[k]
            scaled += 1
    return v, {"n_slices": int(n_t), "n_slices_rescaled": int(scaled),
               "slice_mean_before_min": float(m.min()),
               "slice_mean_before_max": float(m.max()),
               "slice_mean_after_max_relative_deviation":
                   float(np.abs(slice_means(v, t_index, n_t) / target_mean
                                - 1.0).max())}


def max_structure_fraction(values: np.ndarray, level: np.ndarray) -> dict:
    """The largest structure fraction a *non-negative* field of this shape allows.

    Writing ``j = s + c`` with ``s`` the structure part and ``c`` a constant,
    positivity forces ``c >= -min(s)``, and the fraction ``||s|| / ||s + c||``
    falls monotonically in ``c``. So the ceiling is reached exactly at the
    positivity boundary and equals ``||s|| / ||s - min(s)||``.

    Scaling does not evade it: at the boundary ``j = a (s - min(s))`` for any
    ``a > 0`` and the fraction is unchanged. The ceiling is a property of how
    peaked the family renders, not of how the bank is built -- which is the
    thing R1L_STOP_4 exists to detect.
    """
    v = np.asarray(values, float).ravel()
    s = v - level @ (level.T @ v)
    ns = float(np.linalg.norm(s))
    if ns <= 0.0:
        return {"max_structure_fraction": 0.0, "c_min": 0.0,
                "reason": "the family rendered no structure at all"}
    c_min = float(max(0.0, -s.min()))
    return {"max_structure_fraction":
                ns / max(float(np.linalg.norm(s + c_min)), 1e-300),
            "c_min": c_min, "structure_norm": ns}


def structure_balanced(values: np.ndarray, level: np.ndarray,
                       target: float,
                       tol: float = 1e-12) -> tuple[np.ndarray, dict]:
    """The non-negative field of this shape whose structure fraction is ``target``.

    Bisects the constant offset ``c`` on ``[c_min, inf)`` where ``c_min`` is the
    positivity boundary, so positivity holds at every step rather than being
    patched afterwards. An earlier version bisected from zero and then lifted
    the result to make it positive, which moved the fraction off target by up
    to 0.2 -- the lift is baseline, and baseline is exactly what the fraction
    measures.

    When ``target`` exceeds the ceiling of ``max_structure_fraction`` it is not
    achievable by any non-negative field of this shape. The function then
    returns the most structural positive field available and marks
    ``achievable`` false. It does not quietly return something near the target,
    because a bank that cannot reach its declared fraction is a finding.
    """
    v = np.asarray(values, float).ravel()
    lev0 = level @ (level.T @ v)
    s = v - lev0
    ns = float(np.linalg.norm(s))
    if ns <= 0.0:
        return v, {"achieved": 0.0, "baseline": 0.0, "achievable": False,
                   "max_structure_fraction": 0.0,
                   "reason": "the family rendered no structure at all"}

    ceil = max_structure_fraction(v, level)
    c_min = ceil["c_min"]

    def frac(c):
        return ns / max(float(np.linalg.norm(s + c)), 1e-300)

    if target > ceil["max_structure_fraction"]:
        j = s + c_min
        return j, {"achieved": frac(c_min), "baseline": c_min,
                   "achievable": False,
                   "max_structure_fraction": ceil["max_structure_fraction"],
                   "shortfall": float(target - ceil["max_structure_fraction"]),
                   "min_value": float(j.min()),
                   "reason": "the target exceeds what a non-negative field of "
                             "this shape allows; positivity itself is the "
                             "binding constraint"}

    lo, hi = c_min, max(c_min + ns, 1.0)
    while frac(hi) > target:
        hi *= 2.0
        if hi > 1e12:
            break
    for _ in range(300):
        mid = 0.5 * (lo + hi)
        if frac(mid) > target:
            lo = mid
        else:
            hi = mid
        if hi - lo < tol * max(hi, 1.0):
            break
    c = 0.5 * (lo + hi)
    j = s + c
    return j, {"achieved": frac(c), "baseline": float(c), "achievable": True,
               "max_structure_fraction": ceil["max_structure_fraction"],
               "positivity_boundary": c_min, "min_value": float(j.min())}


# --------------------------------------------------------------------------
# analytic shaping, so the truth the operator sees is the truth being scored


def temporal_level_function(values: np.ndarray, grid_t: np.ndarray,
                            t_min: float, t_max: float, n_temporal: int = 8):
    """``ell(t)``, the spatially uniform part, as a function evaluable anywhere.

    ``P_level v`` is uniform in space, so it is a pure function of source time,
    and it lies exactly in the span of the class's temporal modes. Fitting its
    grid values back onto those modes therefore recovers it exactly rather than
    approximately, and the returned callable can be evaluated at the scattered
    source times the rays land on.

    This matters because the bank shaping is defined on the evaluation grid
    while the operator samples wherever the rays go. Without an analytic form
    the data and the truth would be different objects, and every error reported
    would be measuring that difference as well as the reconstruction.
    """
    from phrt.sources.physical_basis import temporal_design
    T = temporal_design(np.asarray(grid_t, float), t_min, t_max, n_temporal)
    b, *_ = np.linalg.lstsq(T, np.asarray(values, float).ravel(), rcond=None)
    resid = float(np.abs(T @ b - np.asarray(values, float).ravel()).max())

    def ell(t):
        return temporal_design(np.asarray(t, float), t_min, t_max, n_temporal) @ b

    return ell, resid


def spatial_mean_function(movie, grid_r: np.ndarray, grid_phi: np.ndarray,
                          t_min: float, t_max: float, n_dense: int = 4096):
    """``m(t)``, the spatial mean of the render, tabulated densely and interpolated.

    Evaluating the exact mean at every ray time would mean rendering the movie
    on the whole spatial grid tens of thousands of times per truth. The source
    families vary on tens of M and the tabulation spacing here is under 0.04 M,
    so interpolation is far below every tolerance in play -- but the runner
    measures the interpolation error against exact evaluation at sampled times
    rather than taking that on faith.
    """
    ts = np.linspace(t_min, t_max, n_dense)
    R = np.asarray(grid_r, float)
    P = np.asarray(grid_phi, float)
    m = np.array([float(np.mean(movie(R, P, np.full(R.size, t)))) for t in ts])

    def mean_at(t):
        return np.interp(np.asarray(t, float), ts, m)

    return mean_at, ts, m


def shaped_renderer(bank: str, movie, level_values: np.ndarray,
                    grid_r, grid_phi, grid_t, t_min, t_max,
                    offset: float = 0.0, target_mean: float = 1.0,
                    floor: float = 1e-9):
    """The bank's truth as a callable on scattered (r, phi, t).

    ``constant_flux`` divides by the spatial mean at that source time;
    ``structure_balanced`` removes the uniform part and adds the frozen offset;
    ``baseline_one`` adds one. All three are the same operations the grid-based
    shaping performs, expressed so that the rays can be sampled.
    """
    if bank == "constant_flux_structural":
        mean_at, _, _ = spatial_mean_function(movie, grid_r, grid_phi, t_min, t_max)

        def render(r, phi, t):
            m = mean_at(t)
            v = movie(r, phi, t)
            return np.where(m > floor, v * target_mean / np.maximum(m, floor), v)

        return render, {"kind": "constant_flux"}

    if bank == "baseline_one_positive":
        return (lambda r, phi, t: movie(r, phi, t) + 1.0), {"kind": "baseline_one"}

    ell, resid = temporal_level_function(level_values, grid_t, t_min, t_max)

    def render(r, phi, t):
        return movie(r, phi, t) - ell(t).ravel() + offset

    return render, {"kind": "structure_balanced", "level_fit_residual": resid}


# --------------------------------------------------------------------------
# exact-in-class construction


def project_to_class(values: np.ndarray, design: np.ndarray) -> tuple:
    """Least-squares coefficients and the synthesised in-class field.

    The synthesis is the truth. Returning the coefficients as well matters
    because the operator must be given *the same object* the scorer holds, and
    with the coefficients in hand the data can be formed by the class-restricted
    matvec rather than by sampling an analytic function -- which is what makes
    the representation floor exactly zero instead of merely small.
    """
    D = np.asarray(design, float)
    v = np.asarray(values, float).ravel()
    coef, *_ = np.linalg.lstsq(D, v, rcond=None)
    return coef, D @ coef


def in_class_bank(bank: str, raw: np.ndarray, design: np.ndarray,
                  level: np.ndarray, t_index: np.ndarray, n_t: int,
                  target: float | None) -> tuple[np.ndarray, np.ndarray, dict]:
    """Build one exact-in-class truth: project, shape, re-project.

    Shaping a projected field can push it back out of the class -- dividing by a
    per-slice mean is not a linear operation on the coefficients -- so the
    result is projected once more and the residual of that second projection is
    reported. If it is not at machine precision the truth is not in class and
    the gate says so rather than the report claiming a floor of zero.
    """
    _, v0 = project_to_class(raw, design)
    if bank == "constant_flux_structural":
        shaped, diag = constant_flux(v0, t_index, n_t, target_mean=1.0)
        diag["bank_kind"] = "constant_flux"
    else:
        shaped, diag = structure_balanced(v0, level, float(target))
        diag["bank_kind"] = "structure_balanced"
        diag["target"] = float(target)
    coef, v = project_to_class(shaped, design)
    resid = float(np.linalg.norm(v - shaped)
                  / max(np.linalg.norm(shaped), 1e-300))
    diag["reprojection_residual_relative"] = resid
    diag["achieved_structure_fraction"] = structure_fraction(v, level)
    diag["min_value"] = float(v.min())
    diag["negative_mass_relative"] = float(
        np.linalg.norm(np.minimum(v, 0.0)) / max(np.linalg.norm(v), 1e-300))
    return coef, v, diag
