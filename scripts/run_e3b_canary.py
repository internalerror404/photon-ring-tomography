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
from phrt.geometry.sampling import common_count, stratified_subsample
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
def build_arms(base: list[OrderRays]) -> dict:
    """Every arm is the same measurement model; only the linear map differs."""
    ones = np.ones((1, len(base)))
    return {
        "DIRECT_PHYSICAL": dict(orders=[base[0]]),
        "RESOLVED_PHYSICAL": dict(orders=base),
        "RESOLVED_EQUALIZED": dict(orders=equalize(base)),
        "DELAY_ONLY_PHYSICAL": dict(orders=substitute_spatial(base, base[0])),
        "SPATIAL_ONLY_PHYSICAL": dict(orders=substitute_delay(base, base[0])),
        "PAIRING_DESTROYED": dict(orders=destroy_pairing(base, SEED)),
        "UNRESOLVED_PHYSICAL": dict(orders=base, mixer=ones),
        "TOTAL_FLUX": dict(orders=base, collapse="total_flux"),
    }


def snr_scale(direct_op: PhysicalOperator, reference: np.ndarray) -> float:
    """The one noise density, fixed from the direct arm and shared by all arms.

    Operators are built at sigma_Omega = 1, so their rows are
    sqrt(dOmega) * g^3 * B. Choosing a physical noise density sigma_Omega
    rescales every whitened row by 1/sigma_Omega. This returns the RMS
    whitened response of order 0 alone to the declared reference source; a
    sweep point at SNR0 is then obtained by multiplying any sigma=1 whitened
    quantity by ``snr0 / s_ref``, i.e. sigma_Omega = s_ref / snr0.

    The registered definition is a *leading-order* effective SNR, so the noise
    is fixed by order 0 and then held constant across every arm. Letting each
    arm set its own sigma from its own data would give an arm with more rows a
    quieter detector, and the arm comparison -- the entire point of the canary
    -- would be measuring row counts rather than physics. The derived arms
    (mixed image, total flux) do not get a sigma at all: their covariance is
    propagated by the operator as C_U = L C_R L^T, so summation costs them the
    noise that summation implies.
    """
    clean = direct_op.matvec(reference)
    return max(float(np.sqrt(np.mean(clean ** 2))), 1e-300)


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
        c = o.coefficient()                       # unwhitened dOmega * g^3
        for t in op.observer_times:
            ts = float(t) - o.delay
            bump = np.exp(-0.5 * ((ts + age) / BUMP_WIDTH) ** 2)
            row = c * bump
            blocks.append(np.array([row.sum()]) if op.collapse == "total_flux" else row)
    per_order = np.split(np.concatenate(blocks), len(op.orders))
    out = [sum(op.L[ch, k] * per_order[k] for k in range(len(op.orders)))
           for ch in range(op.n_channels)]
    # whiten with the arm's own propagated covariance, exactly as the operator does
    return np.concatenate(out) / np.sqrt(op.channel_variance()) / norm


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="pixel_integrated")
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

    arms = build_arms(base)
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
    mixed = ops["UNRESOLVED_PHYSICAL"].unwhitened_dense()
    man.add_gate(gate_from_tolerance(
        "G4_physical_resolved_unresolved_mixing",
        float(np.abs(direct_sum - mixed).max()) / max(float(np.abs(direct_sum).max()), 1e-300),
        reg.data["correctness_gates"]["G4_order_collapse_relative"]))

    # G4b: the covariance the derived arms carry is the propagated one,
    # C_U = L C_R L^T with C_R = sigma^2 diag(dOmega). Checking the collapse
    # identity on unwhitened rows alone would let a wrong noise propagation
    # through, which is exactly how a summed arm can be made to look free.
    worst_cov = 0.0
    cov_rows = []
    for name in ("UNRESOLVED_PHYSICAL", "TOTAL_FLUX"):
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
        rel = float(np.abs(got - expect).max()) / max(float(np.abs(expect).max()), 1e-300)
        worst_cov = max(worst_cov, rel)
        cov_rows.append({"arm": name, "relative_difference": rel,
                         "min_row_variance": float(got.min()),
                         "max_row_variance": float(got.max())})
    man.add_gate(gate_from_tolerance(
        "G4b_linear_collapse_covariance_propagation", worst_cov, 1e-12,
        note="channel variance against an independently formed L C_R L^T"))

    # G6: information monotonicity in retained order, resolved readout
    cum = []
    for k in range(1, len(base) + 1):
        sub = PhysicalOperator(orders=base[:k], observer_times=t_obs,
                               design=basis.design, dimension=basis.dimension)
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
                                   collapse="total_flux")
        through = float(flux_op.matvec(unit)[0]
                        * np.sqrt(flux_op.channel_variance()[0]))
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
    s_ref = snr_scale(ops["DIRECT_PHYSICAL"], unit)
    for name, op in ops.items():
        Aq = {float(a): age_direction(op, float(a), qnorm) for a in ages}
        for snr in SNR_GRID:
            gain = snr / s_ref
            detectable = []
            for a in ages:
                fisher = float(np.sum((Aq[float(a)] * gain) ** 2))
                sd = np.sqrt(fisher)
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
        B = op.to_dense() * (100.0 / s_ref)
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
                                      design=basis.design, dimension=basis.dimension)
                     for o in base]
    for a in ages:
        vals = []
        for op in per_order_ops:
            vals.append(float(np.sum((age_direction(op, float(a), qnorm)
                                      * (100.0 / s_ref)) ** 2)))
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
            vals.append(float(np.sum((age_direction(op, a_u, qnorm)
                                      * (100.0 / s_ref)) ** 2)))
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
                       ("e3b_weight_semantics", g9w_rows),
                       ("e3b_covariance_propagation", cov_rows)):
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
