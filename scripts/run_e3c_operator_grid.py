#!/usr/bin/env python3
"""E3C -- geometry-wide physical historical-operator audit.

Runs the eight registered arms on all twelve validated Kerr/Schwarzschild ray
maps under the frozen measurement convention, and emits the geometry surface
the manuscript's central claim depends on.

Everything that could be tuned after seeing a result is read from
``artifacts/configs/E3C_OPERATOR_GRID_FREEZE.json`` rather than defined here.
The script refuses to run without it.

Three things this file is careful about, because each has already produced a
wrong answer once in this program:

* **One noise density for the whole audit.** ``sigma`` is fixed from the direct
  arm's clean response to the declared reference source and shared by every
  arm. An arm that set its own sigma from its own data would be measuring its
  row count.
* **Derived arms are linear maps, not separate models.** The unresolved image
  and total-flux controls carry ``C_U = L C_R L^T`` and ``C_F = S C_R S^T``,
  propagated inside the operator.
* **Depth is not the oldest ray.** ``T_rec`` is the deepest age whose unit-norm
  localized probe clears the operational threshold, right-censored at the
  frozen common ceiling, and ``J_old`` is reported alongside it precisely
  because a depth endpoint depends on that threshold.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from phrt.audits.e3c_contract import (EXACT_RANK_REASON, EXACT_RANK_VALUE,
                                      check_no_reserved_fields, detectability,
                                      restrict_spectrum)
from phrt.audits.rank import spectrum_of
from phrt.config import load_registry
from phrt.geometry.raymap import read
from phrt.geometry.sampling import common_count, stratified_subsample
from phrt.io.manifests import make_run_id
from phrt.operators.physical import (OrderRays, PhysicalOperator, destroy_pairing,
                                     equalize, substitute_delay, substitute_spatial)
from phrt.sources.physical_basis import (PhysicalBasis, age_probe_norms,
                                         age_probe_spatial)

FREEZE = ROOT / "artifacts" / "configs" / "E3C_OPERATOR_GRID_FREEZE.json"
OUTDIR = ROOT / "artifacts" / "e3c"
REFERENCE_SNR = 100.0     # the scale at which spectra, J_old and H2/H3 are reported
SOURCE_CLASS = "C224"     # the class C whose synthesis map Q_C defines A_C


# ---------------------------------------------------------------------------
def load_freeze() -> dict:
    if not FREEZE.exists():
        raise SystemExit("E3C_OPERATOR_GRID_FREEZE.json is missing: the freeze "
                         "must exist before any geometry is evaluated")
    return json.loads(FREEZE.read_text())


def build_arms(base: list[OrderRays], seed: int) -> dict:
    """The eight registered arms. Every one is the same measurement model."""
    ones = np.ones((1, len(base)))
    return {
        "DIRECT_PHYSICAL": dict(orders=[base[0]]),
        "RESOLVED_PHYSICAL": dict(orders=base),
        "UNRESOLVED_IMAGE": dict(orders=base, mixer=ones),
        "TOTAL_FLUX": dict(orders=base, collapse="total_flux"),
        "DELAY_ONLY": dict(orders=substitute_spatial(base, base[0])),
        "SPATIAL_ONLY": dict(orders=substitute_delay(base, base[0])),
        "EQUALIZED_ORDER_SENSITIVITY": dict(orders=equalize(base)),
        "PAIRING_DESTROYED": dict(orders=destroy_pairing(base, seed)),
    }


def snr_scale(direct_op: PhysicalOperator, reference: np.ndarray) -> float:
    """The one noise density, fixed from the direct arm and shared by all arms.

    Operators are built at sigma_Omega = 1, so a physical noise density rescales
    every whitened row by 1/sigma_Omega. This returns order 0's RMS whitened
    response to the declared reference source; a sweep point at SNR_0 multiplies
    any sigma=1 whitened quantity by ``snr0 / s_ref``.
    """
    clean = direct_op.matvec(reference)
    return max(float(np.sqrt(np.mean(clean ** 2))), 1e-300)


def unit_source(basis: PhysicalBasis) -> np.ndarray:
    """j = 1 in the registered basis: the radial B-splines are a partition of
    unity and the m=0 azimuthal and k=0 temporal modes are both constant."""
    u = np.zeros(basis.dimension)
    for a in range(basis.n_radial):
        u[(a * basis.n_azimuthal + 0) * basis.n_temporal + 0] = 1.0
    return u


def age_norm(r_in: float, r_out: float, width: float) -> float:
    """L2 norm of the unnormalised age probe over the emission region.

    Without this the reported Fisher information is in units of an arbitrary
    peak amplitude and the depth curve is not comparable between geometries.
    """
    area = np.pi * (r_out ** 2 - r_in ** 2)
    return float(np.sqrt(area * width * np.sqrt(np.pi)))


def age_direction(op: PhysicalOperator, age: float, norm: float,
                  width: float) -> np.ndarray:
    """Whitened response to the unit-L2-norm source localized at one age."""
    blocks = []
    for o in op.orders:
        c = o.coefficient()
        for t in op.observer_times:
            ts = float(t) - o.delay
            row = c * np.exp(-0.5 * ((ts + age) / width) ** 2)
            blocks.append(np.array([row.sum()]) if op.collapse == "total_flux" else row)
    per_order = np.split(np.concatenate(blocks), len(op.orders))
    out = [sum(op.L[ch, k] * per_order[k] for k in range(len(op.orders)))
           for ch in range(op.n_channels)]
    return np.concatenate(out) / np.sqrt(op.channel_variance()) / norm


def age_probe_matrix(op: PhysicalOperator, age: float, width: float,
                     rp: list[np.ndarray], norms: np.ndarray) -> np.ndarray:
    """Age-resolved information matrix on the registered localized class.

    AMENDMENT 002. The registered scalar probe is spatially flat, so the
    delay-only substitution -- which changes only source_r and source_phi --
    cannot move the scalar curve at all: ``D_delay`` is then identically zero as
    an algebraic identity, not as evidence. The localized class registered in
    ``physical_basis`` is the radial x azimuthal factors crossed with one
    compact temporal bump, and on that 28-dimensional class the substitution
    does act. This returns

        M(a) = P(a)^T P(a),   P(a) = whitened operator applied to the 28
                                     unit-L2 probes localized at age a

    whose eigenvalues are Fisher informations per unit source amplitude. The
    flat-probe scalar is recovered as the m = 0, partition-of-unity contraction
    of the same object and is retained unchanged alongside it.
    """
    blocks = []
    for i, o in enumerate(op.orders):
        c = o.coefficient()
        for t in op.observer_times:
            ts = float(t) - o.delay
            w = c * np.exp(-0.5 * ((ts + age) / width) ** 2)
            B = rp[i] * w[:, None]
            blocks.append(B.sum(axis=0, keepdims=True) if op.collapse == "total_flux" else B)
    per_order = np.split(np.vstack(blocks), len(op.orders))
    out = [sum(op.L[ch, k] * per_order[k] for k in range(len(op.orders)))
           for ch in range(op.n_channels)]
    P = np.vstack(out) / np.sqrt(op.channel_variance())[:, None] / norms[None, :]
    M = P.T @ P
    return 0.5 * (M + M.T)


def log_information_volume(M: np.ndarray, snr: float) -> float:
    """sum_k log(1 + SNR^2 lambda_k): the log-volume of information about one
    epoch. Reduces to log(1 + SNR^2 I) when the localized class is scalar."""
    lam = np.linalg.eigvalsh(M)
    return float(np.sum(np.log1p((snr ** 2) * np.clip(lam, 0.0, None))))


CENSORING_RULE = ("a depth equal to the common age-grid ceiling is "
                  "right-censored and reported as a lower bound")


def depth_from_curve(ages: np.ndarray, ihat: np.ndarray, snr: float,
                     rho: float, a_max: float) -> dict:
    """The item-4 depth contract for one curve.

    The registered statistic was the supremum of the detectable set alone. A
    supremum cannot distinguish a history detectable all the way back from a
    detectable island beyond an undetectable gap, so it is now reported under a
    name that says it is a supremum, beside the longest contiguous detectable
    span and the complete mask.
    """
    d = detectability(ages, (snr ** 2) * ihat >= rho ** 2)
    oldest = d["oldest_detectable_age_probe"]
    censored = bool(oldest >= 0 and np.isclose(oldest, a_max))
    d.update({
        "right_censored": censored,
        "age_grid_max_M": float(a_max),
        "censor_boundary_M": float(a_max),
        "censoring_rule": CENSORING_RULE,
        "depth_report": ("none" if oldest < 0 else
                         (f">={oldest:.1f}" if censored else f"{oldest:.1f}")),
    })
    return d


def j_old(ages: np.ndarray, ihat: np.ndarray, snr: float, a0: float) -> float:
    """Historical innovation beyond the direct channel's 99.9% age boundary.

    Threshold-independent by construction: it integrates log(1 + I) over the
    region where the direct channel is essentially absent, instead of reporting
    where one contour happens to cross.
    """
    y = np.log1p((snr ** 2) * ihat)
    if a0 >= ages[-1]:
        return 0.0
    m = ages > a0
    aa = np.concatenate([[a0], ages[m]])
    yy = np.concatenate([[float(np.interp(a0, ages, y))], y[m]])
    return float(np.trapezoid(yy, aa)) if hasattr(np, "trapezoid") \
        else float(np.trapz(yy, aa))


def j_old_direct(ages: np.ndarray, y: np.ndarray, a0: float) -> float:
    """Integral of an already-formed non-negative curve beyond a0."""
    if a0 >= ages[-1]:
        return 0.0
    m = ages > a0
    aa = np.concatenate([[a0], ages[m]])
    yy = np.concatenate([[float(np.interp(a0, ages, y))], y[m]])
    return float(np.trapezoid(yy, aa)) if hasattr(np, "trapezoid") \
        else float(np.trapz(yy, aa))


def psd_summary(D: np.ndarray) -> dict:
    """Rank, trace, stable rank and smallest positive eigenvalue of a symmetric
    matrix, on its image."""
    D = 0.5 * (D + D.T)
    lam = np.linalg.eigvalsh(D)
    tol = max(D.shape) * np.finfo(float).eps * max(float(np.abs(lam).max()), 1e-300)
    pos = lam[lam > tol]
    fro2 = float(np.sum(lam ** 2))
    top = float(np.abs(lam).max())
    return {"rank": int(pos.size), "trace": float(lam.sum()),
            "stable_rank": fro2 / max(top ** 2, 1e-300),
            "min_positive_eigenvalue": float(pos.min()) if pos.size else float("nan"),
            "max_eigenvalue": float(lam.max()),
            "min_eigenvalue": float(lam.min()),
            "numerical_tolerance": float(tol)}


# ---------------------------------------------------------------------------
def evaluate(base: list[OrderRays], fz: dict, r_in: float, r_out: float,
             support_tag: str, rng, want_seeds: bool, a0_999: float) -> dict:
    """All E3C measurements for one set of rays under one radial support."""
    h = fz["localized_probe"]["half_width_h_M"]
    t_obs = np.asarray(fz["observation"]["observer_times_M"], dtype=float)
    ages = np.arange(0.0, fz["common_age_grid"]["A_max_M"] + 1e-9,
                     fz["common_age_grid"]["step_M"])
    a_max = float(fz["common_age_grid"]["A_max_M"])
    rho = float(fz["rank_conventions"]["operational_threshold_rho"])
    snr_grid = [float(s) for s in fz["snr_grid"]]

    t_lo = float(t_obs.min() - max(o.delay.max() for o in base)) - 3.0 * h
    t_hi = float(t_obs.max()) + 3.0 * h
    basis = PhysicalBasis(r_in, r_out, t_lo, t_hi)
    unit = unit_source(basis)
    qnorm = age_norm(r_in, r_out, h)

    probe_norms = age_probe_norms(r_in, r_out, h)
    seeds = [int(s) for s in fz["permutation_seeds"]]
    arms = build_arms(base, seeds[0])
    ops = {name: PhysicalOperator(design=basis.design, dimension=basis.dimension,
                                  observer_times=t_obs, **cfg)
           for name, cfg in arms.items()}
    s_ref = snr_scale(ops["DIRECT_PHYSICAL"], unit)

    out = {"support": support_tag, "source_dimension": basis.dimension,
           "r_inner": r_in, "r_outer": r_out, "t_min": t_lo, "t_max": t_hi,
           "rays_per_order": base[0].n_rays, "s_ref": s_ref,
           "reference_snr": REFERENCE_SNR}

    # -- correctness gates on this geometry ---------------------------------
    ref = ops["RESOLVED_PHYSICAL"]
    A = ref.to_dense()
    gates = {}
    gates["G2_physical_dense_matrix_free"] = float(np.abs(
        np.column_stack([ref.matvec(e) for e in np.eye(basis.dimension)]) - A
    ).max()) / max(float(np.abs(A).max()), 1e-300)
    worst = 0.0
    for _ in range(20):
        x = rng.normal(size=ref.shape[1]); y = rng.normal(size=ref.shape[0])
        a_, b_ = float(y @ ref.matvec(x)), float(x @ ref.rmatvec(y))
        worst = max(worst, abs(a_ - b_) / max(abs(a_), abs(b_), 1e-300))
    gates["G3_physical_adjoint"] = worst

    blocks = [ref.order_block(i) for i in range(len(ref.orders))]
    direct_sum = sum(blocks)
    mixed = ops["UNRESOLVED_IMAGE"].unwhitened_dense()
    gates["G4_physical_resolved_unresolved_mixing"] = float(
        np.abs(direct_sum - mixed).max()) / max(float(np.abs(direct_sum).max()), 1e-300)

    worst_cov = 0.0
    for name in ("UNRESOLVED_IMAGE", "TOTAL_FLUX"):
        op = ops[name]
        s2 = op.sigma_omega ** 2
        if op.collapse == "total_flux":
            cr = np.array([s2 * float(o.quadrature.sum()) for o in op.orders])
            expect = np.concatenate([np.full(t_obs.size, float(op.L[c] ** 2 @ cr))
                                     for c in range(op.n_channels)])
        else:
            expect = np.concatenate([
                np.tile(s2 * sum((op.L[c, n] ** 2) * op.orders[n].quadrature
                                 for n in range(len(op.orders))), t_obs.size)
                for c in range(op.n_channels)])
        got = op.channel_variance()
        worst_cov = max(worst_cov, float(np.abs(got - expect).max())
                        / max(float(np.abs(expect).max()), 1e-300))
    gates["G4b_linear_collapse_covariance_propagation"] = worst_cov

    cum = [PhysicalOperator(orders=base[:k], observer_times=t_obs,
                            design=basis.design, dimension=basis.dimension).gram()
           for k in range(1, len(base) + 1)]
    worst_mono = 0.0
    for i in range(1, len(cum)):
        d = 0.5 * (cum[i] - cum[i - 1] + (cum[i] - cum[i - 1]).T)
        lam = float(np.min(np.linalg.eigvalsh(d)))
        worst_mono = max(worst_mono, max(0.0, -lam)
                         / max(1.0, float(np.linalg.norm(cum[i], 2))))
    gates["G6_physical_Gram_monotonicity"] = worst_mono

    g_dir, g_res = ops["DIRECT_PHYSICAL"].gram(), cum[-1]
    dG = 0.5 * (g_res - g_dir + (g_res - g_dir).T)
    lam = float(np.min(np.linalg.eigvalsh(dG)))
    gates["G6b_resolved_dominates_direct"] = max(0.0, -lam) / max(
        1.0, float(np.linalg.norm(g_res, 2)))

    worst_w, w_rows = 0.0, []
    for o in base:
        indep = float(np.sum(o.quadrature * np.power(np.abs(o.redshift), 3.0)))
        fop = PhysicalOperator(orders=[o], observer_times=np.array([0.0]),
                               design=basis.design, dimension=basis.dimension,
                               collapse="total_flux")
        got = float(fop.matvec(unit)[0] * np.sqrt(fop.channel_variance()[0]))
        worst_w = max(worst_w, abs(got - indep) / max(abs(indep), 1e-300))
        w_rows.append({"order": o.order, "operator_unit_source_throughput": got,
                       "independent_sum_dOmega_g3": indep})
    gates["G9w_transfer_weight_semantics"] = worst_w
    out["gates"] = gates
    out["weight_semantics"] = w_rows

    # -- delta G indirect ----------------------------------------------------
    scale2 = (REFERENCE_SNR / s_ref) ** 2
    # Item 7: promoted to a canonical record of its own rather than a field
    # tucked inside the historical-innovation table.
    out["delta_G_indirect"] = {**psd_summary(dG * scale2),
                               "source_class": SOURCE_CLASS,
                               "operator_notation": "A_C = mathcal A Q_C",
                               "definition": "G_resolved - G_direct, both Gram "
                                             "matrices of A_C at the reference SNR"}
    out["G_resolved"] = psd_summary(g_res * scale2)
    out["G_direct"] = psd_summary(g_dir * scale2)

    # -- spectra, age curves, depth, J_old, per arm --------------------------
    per_arm, age_rows, depth_rows, jold_rows = {}, [], [], []
    for name, op in ops.items():
        B = op.to_dense() * (REFERENCE_SNR / s_ref)
        s = restrict_spectrum(
            spectrum_of(B, basis.dimension, operational_threshold=rho).summary(),
            SOURCE_CLASS)
        ihat = np.array([float(np.sum((age_direction(op, float(a), qnorm, h)
                                       / s_ref) ** 2)) for a in ages])
        # AMENDMENT 002: the same epochs on the registered 28-dim localized
        # class, which the delay-only substitution can actually move.
        rp = [age_probe_spatial(o.source_r, o.source_phi, r_in, r_out)
              for o in op.orders]
        mats = [age_probe_matrix(op, float(a), h, rp, probe_norms * s_ref)
                for a in ages]
        lam_max = np.array([float(np.linalg.eigvalsh(M)[-1]) for M in mats])
        lam_min = np.array([float(np.clip(np.linalg.eigvalsh(M)[0], 0.0, None))
                            for M in mats])
        logvol = np.array([log_information_volume(M, REFERENCE_SNR) for M in mats])
        per_arm[name] = {
            "spectrum": s,
            "data_dimension": int(op.shape[0]),
            "ihat": ihat.tolist(),
            "lambda_max": lam_max.tolist(),
            "lambda_min": lam_min.tolist(),
            "log_information_volume_at_reference_snr": logvol.tolist(),
        }
        for snr in snr_grid + [REFERENCE_SNR]:
            jold_rows.append({
                "arm": name, "snr0": snr, "a0_999_lower_limit_M": a0_999,
                "J_old": j_old(ages, ihat, snr, a0_999),
                "J_old_best_mode": j_old(ages, lam_max, snr, a0_999),
                "J_old_log_volume": j_old_direct(
                    ages, np.array([log_information_volume(M, snr) for M in mats]),
                    a0_999)})
        for a, v, lx, ln, lv in zip(ages, ihat, lam_max, lam_min, logvol):
            age_rows.append({"arm": name, "retarded_age": float(a),
                             "information_per_snr2": float(v),
                             "information_at_reference_snr": float(v * REFERENCE_SNR ** 2),
                             "lambda_max_per_snr2": float(lx),
                             "lambda_min_per_snr2": float(ln),
                             "log_information_volume_at_reference_snr": float(lv)})
        for snr in snr_grid:
            d = depth_from_curve(ages, ihat, snr, rho, a_max)
            d.update({"arm": name, "snr0": snr, "total_ages": int(ages.size),
                      "age_grid_max": a_max})
            # the same contract on the best-determined localized mode
            best = depth_from_curve(ages, lam_max, snr, rho, a_max)
            d.update({
                "best_mode_oldest_detectable_age_probe":
                    best["oldest_detectable_age_probe"],
                "best_mode_largest_contiguous_detectable_depth":
                    best["largest_contiguous_detectable_depth"],
                "best_mode_age_threshold_mask": best["age_threshold_mask"],
                "best_mode_detectable_set_is_contiguous":
                    best["detectable_set_is_contiguous"],
                "best_mode_n_detectable_runs": best["n_detectable_runs"],
                "best_mode_right_censored": best["right_censored"],
                "best_mode_depth_report": best["depth_report"]})
            depth_rows.append(d)
    out["arms"] = per_arm
    out["jold_rows"] = jold_rows
    out["age_rows"] = age_rows
    out["depth_rows"] = depth_rows
    out["ages"] = ages.tolist()

    # -- matched-support sensitivity attenuation (H5) ------------------------
    per_order_ops = [PhysicalOperator(orders=[o], observer_times=t_obs,
                                      design=basis.design, dimension=basis.dimension)
                     for o in base]
    windows = [(float(o.delay.min()), float(o.delay.max())) for o in base]
    matched = []
    for u in np.linspace(0.05, 0.95, 19):
        vals, agesu = [], []
        for op, (lo, hi) in zip(per_order_ops, windows):
            a_u = lo + u * (hi - lo)
            agesu.append(a_u)
            vals.append(float(np.sum((age_direction(op, a_u, qnorm, h)
                                      * (REFERENCE_SNR / s_ref)) ** 2)))
        row = {"window_fraction": float(u)}
        for k, (v, a_u) in enumerate(zip(vals, agesu)):
            row[f"age_order{k}"] = float(a_u)
            row[f"I_order{k}"] = v
        floor = 1e-9 * max(max(vals), 1e-300)
        for k in range(1, len(vals)):
            lo_, hi_ = vals[k - 1], vals[k]
            ok = lo_ > floor and hi_ > floor
            row[f"Gamma_sensitivity_matched_{k-1}_to_{k}"] = (
                float(-0.5 * np.log(hi_ / lo_)) if ok else float("nan"))
            row[f"Gamma_sensitivity_matched_{k-1}_to_{k}_status"] = "ok" if ok else "undefined"
        matched.append(row)
    out["matched"] = matched
    out["windows"] = windows

    # -- attenuation decomposition ------------------------------------------
    decomp = []
    for o in base:
        g3 = np.power(np.abs(o.redshift), 3.0)
        decomp.append({"order": o.order, "A_area": float(np.sum(o.quadrature)),
                       "A_g": float(np.sum(o.quadrature * g3)),
                       "mean_redshift": float(o.redshift.mean()),
                       "n_rays": o.n_rays})
    a0 = decomp[0]["A_g"]
    for d_ in decomp:
        d_["A_g_ratio_to_direct"] = d_["A_g"] / a0
        d_["Gamma_amp_from_direct"] = (-np.log(max(d_["A_g"] / a0, 1e-300)) / d_["order"]
                                       if d_["order"] else 0.0)
    out["attenuation"] = decomp

    # -- PAIRING_DESTROYED across the frozen seed set ------------------------
    if want_seeds:
        dist = []
        for sd in seeds:
            op = PhysicalOperator(orders=destroy_pairing(base, sd),
                                  observer_times=t_obs, design=basis.design,
                                  dimension=basis.dimension)
            s = restrict_spectrum(
                spectrum_of(op.to_dense() * (REFERENCE_SNR / s_ref),
                            basis.dimension,
                            operational_threshold=rho).summary(), SOURCE_CLASS)
            dist.append({"seed": sd, **s})
        out["pairing_destroyed_seeds"] = dist
    return out


# ---------------------------------------------------------------------------
def run_geometry(g: str, fz: dict, control_interval=None) -> dict:
    t0 = time.time()
    maps = ROOT / "artifacts" / "raymaps"
    rng = np.random.default_rng(int(fz["observation"]["subsample_seed"]))
    n_rays = int(fz["observation"]["rays_per_order"])
    raw = [read(maps / f"{g}_n{n}_{fz['profile']}.h5") for n in fz["orders"]]
    base = common_count([stratified_subsample(rm, n_rays, rng) for rm in raw], rng)

    r_in = min(float(o.source_r.min()) for o in base)
    r_out = max(float(o.source_r.max()) for o in base)
    a0_999 = float(
        fz["common_age_grid"]["direct_order_A_0_999_by_geometry_M"][g])
    res = evaluate(base, fz, r_in, r_out, "PRIMARY_GEOMETRY_DEPENDENT", rng,
                   want_seeds=True, a0_999=a0_999)
    res["geometry"] = g
    res["a0_999_M"] = a0_999

    if control_interval is not None:
        lo, hi = control_interval
        filt = []
        for o in base:
            m = (o.source_r >= lo) & (o.source_r <= hi)
            if m.sum() < 64:
                raise SystemExit(f"{g}: common-support control retains only "
                                 f"{int(m.sum())} rays at order {o.order}")
            filt.append(OrderRays(o.order, o.source_r[m], o.source_phi[m],
                                  o.delay[m], o.redshift[m], o.quadrature[m],
                                  o.amplitude))
        filt = common_count(filt, np.random.default_rng(
            int(fz["observation"]["subsample_seed"])))
        ctrl = evaluate(filt, fz, lo, hi, "COMMON_RADIAL_SUPPORT", rng,
                        want_seeds=False, a0_999=a0_999)
        ctrl["geometry"] = g
        ctrl["a0_999_M"] = a0_999
        res["control"] = ctrl
    res["runtime_seconds"] = time.time() - t0
    return res


def control_interval(fz: dict) -> tuple[float, float]:
    """One fixed radial interval in r/M contained in every anchor's valid domain.

    Taken as the intersection of the anchors' sampled radial ranges, so the
    control changes the source domain in exactly one way -- it stops moving with
    spin -- and changes nothing else.
    """
    maps = ROOT / "artifacts" / "raymaps"
    los, his = [], []
    for g in fz["anchor_geometries"]:
        rr = []
        for n in fz["orders"]:
            rm = read(maps / f"{g}_n{n}_{fz['profile']}.h5")
            rr.append(rm.source_r[rm.valid])
        allr = np.concatenate(rr)
        los.append(float(allr.min())); his.append(float(allr.max()))
    return float(max(los)), float(min(his))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--geometry", default=None,
                    help="one geometry id; default runs the whole frozen grid")
    args = ap.parse_args()

    fz = load_freeze()
    reg = load_registry()
    OUTDIR.mkdir(parents=True, exist_ok=True)
    todo = [args.geometry] if args.geometry else list(fz["geometries"])
    anchors = set(fz["anchor_geometries"])
    ci = control_interval(fz)
    print(f"common radial support control interval r/M = "
          f"[{ci[0]:.4f}, {ci[1]:.4f}]")

    t0 = time.time()
    for g in todo:
        res = run_geometry(g, fz, ci if g in anchors else None)
        res["registry_sha256"] = reg.sha256
        res["run_id"] = make_run_id("E3C", reg.sha256)
        (OUTDIR / f"{g}.json").write_text(json.dumps(res) + "\n")
        sp = res["arms"]
        print(f"{g}  {res['runtime_seconds']:6.0f}s  "
              f"dir oprank {sp['DIRECT_PHYSICAL']['spectrum']['operational_rank']:3d}  "
              f"res oprank {sp['RESOLVED_PHYSICAL']['spectrum']['operational_rank']:3d}  "
              f"dG rank {res['delta_G_indirect']['rank']:3d}  "
              f"{'+control' if 'control' in res else ''}")
    print(f"total {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
