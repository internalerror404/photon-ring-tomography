#!/usr/bin/env python3
"""E3B -- physical historical-operator canary, single geometry a*=0.5, i=50 deg.

Answers, on real Kerr transfer maps, the question the toy could only pose:
which age-localized source directions enter the operator's range, and which
remain null or near-null once physical attenuation, redshift and order mixing
are applied.

Two exponents are kept apart throughout, because conflating them is the error
this experiment exists to avoid:

    Gamma_amp   = -log( order amplitude ratio )        a throughput statement
    Gamma_info  = -0.5 * log( Fisher information ratio )  an information statement

A thin higher-order band can carry negligible flux and still supply a
distinguishable mode; a band with flux can carry almost no information about
the age direction of interest. Only Gamma_info bears on recoverable history.
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

from phrt.audits.rank import spectrum_of
from phrt.config import load_registry
from phrt.geometry.raymap import read
from phrt.io.manifests import Gate, RunManifest, gate_from_tolerance, make_run_id, merge_gate_file
from phrt.io.tables import write_table
from phrt.operators.physical import (OrderRays, PhysicalOperator, destroy_pairing,
                                     equalize, substitute_delay, substitute_spatial)
from phrt.sources.physical_basis import AgeProbeBasis, PhysicalBasis

GEOMETRY = "a050_i050"
PROFILE = "core"
ORDERS = (0, 1, 2)
RAYS_PER_ORDER = 1536          # the registered core profile
N_OBSERVER_TIMES = 8
OBSERVER_SPAN = 20.0           # M
BUMP_WIDTH = 3.0               # M
AGE_STEP = 4.0                 # M
OPERATIONAL_THRESHOLD = 1.0
SNR_GRID = (1.0, 3.0, 10.0, 30.0, 100.0, 300.0, 1e3, 3e3, 1e4, 3e4, 1e5, 1e6)
SEED = 20260825


# ---------------------------------------------------------------------------
def stratified_subsample(rm, n_target: int, rng) -> OrderRays:
    """Sample n_target rays, stratified, with quadrature rescaled so the band's
    total solid angle is preserved. Sampling without rescaling would silently
    shrink every order by its own sampling fraction."""
    v = np.where(rm.valid)[0]
    keys = (np.arctan2(rm.beta[v], rm.alpha[v]), rm.source_r[v], rm.delay[v])
    n_strata = max(int(round(n_target ** (1 / 3))), 2)
    edges = [np.quantile(k, np.linspace(0, 1, n_strata + 1)) for k in keys]
    cell = np.zeros(v.size, dtype=int)
    for k, e in zip(keys, edges):
        cell = cell * n_strata + np.clip(np.searchsorted(e, k, side="right") - 1,
                                         0, n_strata - 1)
    chosen, weights = [], []
    total_area = float(np.sum(rm.pixel_area[v]))
    for c in np.unique(cell):
        members = v[cell == c]
        take = max(1, int(round(n_target * members.size / v.size)))
        take = min(take, members.size)
        pick = rng.choice(members, size=take, replace=False)
        area = float(np.sum(rm.pixel_area[members]))
        chosen.append(np.atleast_1d(pick))
        weights.append(np.full(np.atleast_1d(pick).size, area / take))
    idx = np.concatenate(chosen)
    w = np.concatenate(weights)
    # trim or pad to exactly n_target while preserving the total area
    if idx.size > n_target:
        keep = rng.choice(idx.size, size=n_target, replace=False)
        idx, w = idx[keep], w[keep]
    w = w * (total_area / max(float(w.sum()), 1e-300))
    return OrderRays(order=rm.order, source_r=rm.source_r[idx].copy(),
                     source_phi=rm.source_phi[idx].copy(),
                     delay=rm.delay[idx].copy(), redshift=rm.redshift[idx].copy(),
                     quadrature=w)


def common_count(order_rays: list[OrderRays], rng) -> list[OrderRays]:
    """Trim every order to the same ray count, which the substitution arms need."""
    n = min(o.n_rays for o in order_rays)
    out = []
    for o in order_rays:
        pick = np.sort(rng.choice(o.n_rays, size=n, replace=False)) if o.n_rays > n \
            else np.arange(n)
        scale = float(o.quadrature.sum()) / max(float(o.quadrature[pick].sum()), 1e-300)
        out.append(OrderRays(o.order, o.source_r[pick], o.source_phi[pick],
                             o.delay[pick], o.redshift[pick],
                             o.quadrature[pick] * scale, o.amplitude))
    return out


def build_arms(base: list[OrderRays], model: str) -> dict:
    n = len(base)
    ones = np.ones((1, n))
    return {
        "DIRECT_PHYSICAL": dict(orders=[base[0]], mixer=None, model=model),
        "RESOLVED_PHYSICAL": dict(orders=base, mixer=None, model=model),
        "RESOLVED_EQUALIZED": dict(orders=equalize(base, model), mixer=None, model=model),
        "DELAY_ONLY_PHYSICAL": dict(orders=substitute_spatial(base, base[0]),
                                    mixer=None, model=model),
        "SPATIAL_ONLY_PHYSICAL": dict(orders=substitute_delay(base, base[0]),
                                      mixer=None, model=model),
        "PAIRING_DESTROYED": dict(orders=destroy_pairing(base, SEED),
                                  mixer=None, model=model),
        "UNRESOLVED_PHYSICAL": dict(orders=base, mixer=ones, model=model),
        "TOTAL_FLUX": dict(orders=base, mixer=None, model="total_flux"),
    }


def detector_sigma(direct_op: PhysicalOperator, snr0: float,
                   reference: np.ndarray) -> float:
    """One physical per-pixel detector noise, defined once from the direct arm.

    The registered definition is a *leading-order* effective SNR, so the noise
    is fixed by order 0's clean response to the declared reference source and
    then held constant across every arm. Letting each arm set its own sigma
    from its own data would give an arm with more rows a quieter detector, and
    the arm comparison -- the entire point of the canary -- would be measuring
    row counts rather than physics.
    """
    clean = direct_op.matvec(reference)
    return max(float(np.sqrt(np.mean(clean ** 2))), 1e-300) / snr0


def row_sigma(op: PhysicalOperator, sigma: float) -> np.ndarray:
    """Per-row noise for one arm.

    Two independent propagations, both forced by the model rather than chosen:
    a mixed channel sums orders, so C_U = L C_R L^T gives channel c a noise
    sigma * ||L[c,:]||_2; and a total-flux row sums N pixels with independent
    per-pixel noise, so it carries sigma * sqrt(N). Omitting the second would
    hand the spatially collapsed control the per-pixel noise of a single pixel
    while giving it the summed signal of all of them, making the deliberately
    information-poor arm look competitive.
    """
    per_channel = sigma * np.linalg.norm(op.L, axis=1)
    if op.model == "total_flux":
        per_channel = per_channel * np.sqrt(float(op.orders[0].n_rays))
    rows = op.shape[0] // op.n_channels
    return np.repeat(per_channel, rows)


def age_grid(base: list[OrderRays]) -> np.ndarray:
    lo = min(float(o.delay.min()) for o in base)
    hi = max(float(o.delay.max()) for o in base)
    return np.arange(lo, hi + AGE_STEP, AGE_STEP)


def age_norm(r_in: float, r_out: float, width: float = BUMP_WIDTH) -> float:
    """L2 norm of the unnormalised age probe over the emission region.

    The probe is spatially flat and temporally a Gaussian of the given width,
    so ||q||^2 = (spatial area) * (width * sqrt(pi)). Without this the reported
    Fisher information is in units of an arbitrary peak amplitude and the depth
    curve means nothing.
    """
    area = np.pi * (r_out ** 2 - r_in ** 2)
    return float(np.sqrt(area * width * np.sqrt(np.pi)))


def age_direction(op: PhysicalOperator, age: float, norm: float) -> np.ndarray:
    """A q_a for the unit-L2-norm source localized at one retarded age."""
    blocks = []
    for o in op.orders:
        c = o.coefficient(op.model)
        for t in op.observer_times:
            ts = float(t) - o.delay
            bump = np.exp(-0.5 * ((ts + age) / BUMP_WIDTH) ** 2)
            row = c * bump
            blocks.append(np.array([row.sum()]) if op.model == "total_flux" else row)
    per_order = np.split(np.concatenate(blocks), len(op.orders))
    out = [sum(op.L[ch, k] * per_order[k] for k in range(len(op.orders)))
           for ch in range(op.n_channels)]
    return np.concatenate(out) / norm


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="specific_intensity")
    ap.add_argument("--rays", type=int, default=RAYS_PER_ORDER)
    args = ap.parse_args()

    t0 = time.time()
    reg = load_registry()
    rng = np.random.default_rng(SEED)
    maps = ROOT / "artifacts" / "raymaps"

    raw = [read(maps / f"{GEOMETRY}_n{n}_{PROFILE}.h5") for n in ORDERS]
    base = common_count([stratified_subsample(rm, args.rays, rng) for rm in raw], rng)
    print(f"rays per order after common-count trim: {[o.n_rays for o in base]}")

    ages = age_grid(base)
    t_obs = np.linspace(0.0, OBSERVER_SPAN, N_OBSERVER_TIMES)
    r_in = min(float(o.source_r.min()) for o in base)
    r_out = max(float(o.source_r.max()) for o in base)
    t_lo = float(t_obs.min() - max(o.delay.max() for o in base)) - 3 * BUMP_WIDTH
    t_hi = float(t_obs.max()) + 3 * BUMP_WIDTH
    basis = PhysicalBasis(r_in, r_out, t_lo, t_hi)
    print(f"registered global class dimension {basis.dimension}; "
          f"ages {ages[0]:.1f}..{ages[-1]:.1f} M in {ages.size} steps")

    arms = build_arms(base, args.model)
    ops = {name: PhysicalOperator(design=basis.design, dimension=basis.dimension,
                                  observer_times=t_obs, **cfg)
           for name, cfg in arms.items()}

    run_id = make_run_id("E3B", reg.sha256)
    man = RunManifest(run_id=run_id, experiment_id="E3B",
                      seeds={"seed": SEED, "rays_per_order": args.rays,
                             "observer_times": N_OBSERVER_TIMES},
                      extra={"geometry": GEOMETRY, "measurement_model": args.model,
                             "bump_width_M": BUMP_WIDTH,
                             "operational_threshold": OPERATIONAL_THRESHOLD})
    man.add_input(reg.path)

    unit = np.zeros(basis.dimension)
    unit[:] = 0.0
    # a unit source j = 1 in the registered basis: the radial B-splines form a
    # partition of unity and the m=0 azimuthal and k=0 temporal modes are both
    # constant, so the constant source is the sum of those columns.
    for a in range(basis.n_radial):
        unit[(a * basis.n_azimuthal + 0) * basis.n_temporal + 0] = 1.0

    # ---- gates ------------------------------------------------------------
    ref = ops["RESOLVED_PHYSICAL"]
    A = ref.to_dense()
    worst_parity = float(np.abs(np.column_stack([ref.matvec(e) for e in np.eye(basis.dimension)])
                                - A).max()) / max(float(np.abs(A).max()), 1e-300)
    man.add_gate(gate_from_tolerance("G2_physical_dense_matrix_free", worst_parity,
                                     reg.data["correctness_gates"]["G2_dense_operator_relative"]))
    worst_adj = 0.0
    for _ in range(20):
        x = rng.normal(size=ref.shape[1]); y = rng.normal(size=ref.shape[0])
        a_, b_ = float(y @ ref.matvec(x)), float(x @ ref.rmatvec(y))
        worst_adj = max(worst_adj, abs(a_ - b_) / max(abs(a_), abs(b_), 1e-300))
    man.add_gate(gate_from_tolerance("G3_physical_adjoint", worst_adj,
                                     reg.data["correctness_gates"]["G3_adjoint_relative"]))

    # G4: mixing the resolved stack down reproduces the unresolved operator
    blocks = [ref.order_block(i) for i in range(len(ref.orders))]
    direct_sum = sum(blocks)
    mixed = ops["UNRESOLVED_PHYSICAL"].to_dense()
    man.add_gate(gate_from_tolerance(
        "G4_physical_resolved_unresolved_mixing",
        float(np.abs(direct_sum - mixed).max()) / max(float(np.abs(direct_sum).max()), 1e-300),
        reg.data["correctness_gates"]["G4_order_collapse_relative"]))

    # G6: information monotonicity in retained order, resolved readout
    grams, cum = [], []
    for k in range(1, len(base) + 1):
        sub = PhysicalOperator(orders=base[:k], observer_times=t_obs,
                               design=basis.design, dimension=basis.dimension,
                               model=args.model)
        cum.append(sub.gram())
    worst_mono = 0.0
    for i in range(1, len(cum)):
        d = 0.5 * (cum[i] - cum[i - 1] + (cum[i] - cum[i - 1]).T)
        lam = float(np.min(np.linalg.eigvalsh(d)))
        worst_mono = max(worst_mono, max(0.0, -lam) / max(1.0, float(np.linalg.norm(cum[i], 2))))
    man.add_gate(gate_from_tolerance(
        "G6_physical_Gram_monotonicity", worst_mono,
        reg.data["correctness_gates"]["G6_monotonicity_relative_negative_eigenvalue"]))

    # resolved must dominate direct under the same observation model
    g_dir = ops["DIRECT_PHYSICAL"].gram()
    g_res = cum[-1]
    lam = float(np.min(np.linalg.eigvalsh(0.5 * (g_res - g_dir + (g_res - g_dir).T))))
    man.add_gate(gate_from_tolerance(
        "G6b_resolved_dominates_direct", max(0.0, -lam) / max(1.0, float(np.linalg.norm(g_res, 2))),
        reg.data["correctness_gates"]["G6_monotonicity_relative_negative_eigenvalue"],
        note="G_resolved - G_direct must be positive semidefinite"))

    # G5: inject a numerical null direction of the restricted operator
    from phrt.audits.rank import numerical_null_basis
    V = numerical_null_basis(A)
    if V.shape[1]:
        v = V[:, 0]
        man.add_gate(gate_from_tolerance(
            "G5_physical_injected_null",
            float(np.linalg.norm(A @ v)) / max(float(np.linalg.norm(A @ unit)), 1e-300),
            reg.data["correctness_gates"]["G5_kernel_normalized_residual"],
            note=f"null dimension {V.shape[1]} in the registered global class"))
    else:
        man.add_gate(Gate("G5_physical_injected_null", "NOT_RUN",
                          note="the registered global class has trivial numerical "
                               "null space under this arm"))

    # G9w: unit source throughput must match the independent integrated value
    g9w_rows, worst_g9w = [], 0.0
    for i, o in enumerate(base):
        independent = float(np.sum(o.quadrature * np.power(np.abs(o.redshift), 3.0)))
        flux_op = PhysicalOperator(orders=[o], observer_times=np.array([0.0]),
                                   design=basis.design, dimension=basis.dimension,
                                   model="total_flux")
        through = float(flux_op.matvec(unit)[0])
        rel = abs(through - independent) / max(abs(independent), 1e-300)
        worst_g9w = max(worst_g9w, rel)
        g9w_rows.append({"order": o.order, "operator_unit_source_throughput": through,
                         "independent_sum_dOmega_g3": independent,
                         "relative_difference": rel})
    man.add_gate(gate_from_tolerance(
        "G9w_weight_semantics", worst_g9w, 1e-10,
        note="operator output for a unit source j=1, against sum(dOmega * g^3) "
             "computed outside the operator, per order"))

    # ---- attenuation decomposition ----------------------------------------
    decomp = []
    for o in base:
        g3 = np.power(np.abs(o.redshift), 3.0)
        decomp.append({"order": o.order,
                       "A_area": float(np.sum(o.quadrature)),
                       "A_g": float(np.sum(o.quadrature * g3)),
                       "mean_redshift": float(o.redshift.mean()),
                       "n_rays": o.n_rays})
    a0 = decomp[0]["A_g"]
    for d in decomp:
        d["A_g_ratio_to_direct"] = d["A_g"] / a0
        d["Gamma_amp_from_direct"] = (-np.log(max(d["A_g"] / a0, 1e-300)) / d["order"]
                                      if d["order"] else 0.0)

    # ---- age information, per arm -----------------------------------------
    info_rows, depth_rows, spec_rows = [], [], []
    qnorm = age_norm(r_in, r_out)
    for name, op in ops.items():
        Aq = {float(a): age_direction(op, float(a), qnorm) for a in ages}
        for snr in SNR_GRID:
            sigma = row_sigma(op, detector_sigma(ops["DIRECT_PHYSICAL"], snr, unit))
            detectable = []
            for a in ages:
                fisher = float(np.sum((Aq[float(a)] / sigma) ** 2))
                sd = np.sqrt(fisher)
                if snr == SNR_GRID[-1]:
                    pass
                if sd >= OPERATIONAL_THRESHOLD:
                    detectable.append(float(a))
                if snr in (1.0, 100.0, 1e4, 1e6):
                    info_rows.append({"arm": name, "snr0": snr, "retarded_age": float(a),
                                      "fisher_information": fisher,
                                      "sqrt_fisher": sd,
                                      "crlb": 1.0 / fisher if fisher > 0 else np.inf,
                                      "detectable": bool(sd >= OPERATIONAL_THRESHOLD)})
            deepest = max(detectable) if detectable else -1.0
            # A depth equal to the deepest age the grid contains is a lower
            # bound, not a measurement: the sweep ran out of grid before the
            # arm ran out of reach.
            censored = bool(detectable and np.isclose(deepest, float(ages[-1])))
            depth_rows.append({
                "arm": name, "snr0": snr,
                "n_detectable_ages": len(detectable),
                "deepest_detectable_age": deepest,
                "shallowest_detectable_age": min(detectable) if detectable else -1.0,
                "total_ages": int(ages.size),
                "right_censored": censored,
                "age_grid_max": float(ages[-1]),
                "depth_report": ("none" if not detectable else
                                 (f">={deepest:.1f}" if censored else f"{deepest:.1f}"))})
        # restricted spectra on the registered global class
        B = op.to_dense() / row_sigma(
            op, detector_sigma(ops["DIRECT_PHYSICAL"], 100.0, unit))[:, None]
        sp = spectrum_of(B, basis.dimension, operational_threshold=OPERATIONAL_THRESHOLD)
        s = sp.summary()
        spec_rows.append({"arm": name, "snr0_reference": 100.0,
                          "source_dimension": basis.dimension,
                          "data_dimension": int(op.shape[0]),
                          **{k: s[k] for k in ("numerical_rank", "operational_rank",
                                               "nullity", "sigma_max",
                                               "sigma_min_positive", "kappa_positive",
                                               "stable_rank", "effective_rank",
                                               "trace_information")}})
        print(f"  {name:24s} rows {op.shape[0]:7d}  rank {s['numerical_rank']:4d}"
              f"/{basis.dimension}  oprank {s['operational_rank']:4d}"
              f"  kappa+ {s['kappa_positive']:.3e}")

    # Gamma_info between consecutive orders, resolved arm, per age
    ginfo = []
    per_order_ops = [PhysicalOperator(orders=[o], observer_times=t_obs,
                                      design=basis.design, dimension=basis.dimension,
                                      model=args.model) for o in base]
    for a in ages:
        vals = []
        for op in per_order_ops:
            sg = row_sigma(op, detector_sigma(ops["DIRECT_PHYSICAL"], 100.0, unit))
            vals.append(float(np.sum((age_direction(op, float(a), qnorm) / sg) ** 2)))
        row = {"retarded_age": float(a)}
        for k, v in enumerate(vals):
            row[f"I_order{k}"] = v
        # This is a pointwise comparison at a FIXED absolute age, between orders
        # whose temporal supports barely overlap. It is a dominance ratio, not
        # an attenuation exponent, and is named accordingly: calling it
        # Gamma_info would imply a decay along matched support that this
        # quantity does not measure. The matched-support exponent is computed
        # separately below, in delay-aligned coordinates.
        floor = 1e-9 * max(max(vals), 1e-300)
        for k in range(1, len(vals)):
            lo, hi = vals[k - 1], vals[k]
            if lo <= floor or hi <= floor:
                row[f"age_specific_order_dominance_ratio_{k-1}_to_{k}"] = float("nan")
                row[f"age_specific_order_dominance_ratio_{k-1}_to_{k}_status"] = (
                    "undefined: at least one order carries no information at this age")
            else:
                row[f"age_specific_order_dominance_ratio_{k-1}_to_{k}"] = float(hi / lo)
                row[f"age_specific_order_dominance_ratio_{k-1}_to_{k}_status"] = "ok"
        ginfo.append(row)

    # Matched-order sensitivity attenuation, in delay-aligned coordinates.
    # Each order is sampled at the same FRACTIONAL position u within its own
    # retarded window, so the orders are compared on matched temporal support:
    #
    #     Gamma_sensitivity_matched = -0.5 * log(I_next / I_current)
    #
    # Named for sensitivity rather than information because the quantity being
    # compared is the Fisher sensitivity to a localized amplitude at matched
    # window position, not a decay of total information content.
    matched = []
    windows = [(float(o.delay.min()), float(o.delay.max())) for o in base]
    for u in np.linspace(0.05, 0.95, 19):
        vals, agesu = [], []
        for op, (lo, hi) in zip(per_order_ops, windows):
            a_u = lo + u * (hi - lo)
            agesu.append(a_u)
            sg = row_sigma(op, detector_sigma(ops["DIRECT_PHYSICAL"], 100.0, unit))
            vals.append(float(np.sum((age_direction(op, a_u, qnorm) / sg) ** 2)))
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

    # Age-support bookkeeping, exact.
    support = [{
        "observer_time_min": float(t_obs.min()), "observer_time_max": float(t_obs.max()),
        "observer_time_span": float(t_obs.max() - t_obs.min()),
        "n_observer_times": int(t_obs.size),
        "localized_probe_width_M": BUMP_WIDTH,
        "localized_probe_support_pm3sigma_M": 3.0 * BUMP_WIDTH,
        "age_grid_min": float(ages[0]), "age_grid_max": float(ages[-1]),
        "age_grid_step": AGE_STEP, "n_ages": int(ages.size),
        "global_class_t_min": basis.t_min, "global_class_t_max": basis.t_max,
    }]
    for k, (lo, hi) in enumerate(windows):
        support.append({"order": k, "delay_window_min_M": lo, "delay_window_max_M": hi,
                        "delay_window_span_M": hi - lo,
                        "reachable_source_time_min": float(t_obs.min() - hi),
                        "reachable_source_time_max": float(t_obs.max() - lo)})

    for name, rows in (("e3b_age_information", info_rows),
                       ("e3b_matched_support_attenuation", matched),
                       ("e3b_age_support_bookkeeping", support),
                       ("e3b_temporal_depth_curve", depth_rows),
                       ("e3b_singular_spectra", spec_rows),
                       ("e3b_attenuation_decomposition", decomp),
                       ("e3b_gamma_info", ginfo),
                       ("e3b_weight_semantics", g9w_rows)):
        man.add_output(write_table(rows, name))

    mp = man.write(reg.path, reg.sha256, runtime_seconds=time.time() - t0)
    merge_gate_file(man.gates, run_id)
    print("\ngates")
    for g in man.gates:
        m = g.measured
        ms = f"{m:.3e}" if isinstance(m, float) else str(m)
        print(f"  {g.name:38s} {g.status:8s} {ms}")
    print(f"\nmanifest {mp}\ntotal {time.time()-t0:.0f}s")
    return 1 if man.failed_gates else 0


if __name__ == "__main__":
    raise SystemExit(main())
