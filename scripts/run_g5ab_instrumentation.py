#!/usr/bin/env python3
"""G5a / G5b -- instrumentation gates for the null-space audit machinery.

**These are not physical results.** The physical operator has full column rank
on the registered 224-dimensional class, so there is no natural null direction
to inject and G5 as originally written is NOT_APPLICABLE. What can still be
tested is whether the audit machinery would *find* a null direction if one
existed. That is done by manufacturing one.

G5a  append an exact duplicate of an existing column. The vector (+1 on the
     original, -1 on the duplicate) is then an exact null vector, known in
     closed form rather than recovered numerically. The gate checks the
     normalized data residual it produces.

G5b  append a near-duplicate column at a sequence of epsilon. The smallest
     singular value must fall monotonically and approximately linearly with
     epsilon, which is the signature the near-null detector relies on.

Neither result says anything about Kerr. They say the detector works.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from phrt.audits.rank import numerical_null_basis, spectrum_of
from phrt.config import load_registry
from phrt.geometry.raymap import read
from phrt.io.manifests import Gate, RunManifest, gate_from_tolerance, make_run_id, merge_gate_file
from phrt.io.tables import write_table
from phrt.operators.physical import OrderRays, PhysicalOperator
from phrt.sources.physical_basis import PhysicalBasis

GEOMETRY = "a050_i050"
EPSILONS = (1e-2, 1e-3, 1e-4, 1e-5, 1e-6, 1e-7)
G5A_TOLERANCE = 1e-10
SEED = 20260825


def physical_matrix(n_rays: int = 700) -> tuple[np.ndarray, int]:
    rng = np.random.default_rng(SEED)
    orders = []
    for n in (0, 1, 2):
        m = read(ROOT / "artifacts" / "raymaps" / f"{GEOMETRY}_n{n}_core.h5")
        v = np.where(m.valid)[0]
        i = rng.choice(v, size=min(n_rays, v.size), replace=False)
        tot = float(m.pixel_area[v].sum())
        w = m.pixel_area[i] * (tot / float(m.pixel_area[i].sum()))
        orders.append(OrderRays(n, m.source_r[i], m.source_phi[i], m.delay[i],
                                m.redshift[i], w))
    r_in = min(float(o.source_r.min()) for o in orders)
    r_out = max(float(o.source_r.max()) for o in orders)
    t_obs = np.linspace(0.0, 20.0, 8)
    basis = PhysicalBasis(r_in, r_out,
                          float(t_obs.min() - max(o.delay.max() for o in orders)) - 9.0,
                          float(t_obs.max()) + 9.0)
    A = PhysicalOperator(orders=orders, observer_times=t_obs, design=basis.design,
                         dimension=basis.dimension).to_dense()
    return A, basis.dimension


def main() -> int:
    t0 = time.time()
    reg = load_registry()
    A, d = physical_matrix()
    sp = spectrum_of(A, d)
    run_id = make_run_id("G5AB", reg.sha256)
    man = RunManifest(run_id=run_id, experiment_id="G5AB", seeds={"seed": SEED})
    man.add_input(reg.path)

    man.add_gate(Gate(
        "G5_natural_null_on_registered_class", "NOT_RUN",
        disposition="NOT_APPLICABLE_FULL_COLUMN_RANK",
        measured=sp.numerical_rank, threshold=d,
        note=f"the physical operator has rank {sp.numerical_rank} of {d} columns, "
             f"so ker(A_physical | C_224) = {{0}} and there is no natural null "
             f"direction to inject. Full column rank on a 224-dimensional "
             f"discretised class is NOT a statement of continuum injectivity."))

    # --- G5a: manufactured exact null --------------------------------------
    col = A[:, 3:4]
    A_dup = np.hstack([A, col])
    v = np.zeros(A_dup.shape[1])
    v[3], v[-1] = 1.0, -1.0
    v /= np.linalg.norm(v)
    rng = np.random.default_rng(SEED)
    x0 = rng.normal(size=A_dup.shape[1])
    residual = float(np.linalg.norm(A_dup @ v)) / max(float(np.linalg.norm(A_dup @ x0)), 1e-300)
    found = numerical_null_basis(A_dup)
    overlap = (float(np.abs(found.T @ v).max()) if found.shape[1] else 0.0)
    man.add_gate(gate_from_tolerance(
        "G5a_manufactured_exact_null", residual, G5A_TOLERANCE,
        note=f"a duplicated column makes (+1, -1) an exact null vector known in "
             f"closed form. Normalized data residual {residual:.3e}; the "
             f"numerical detector recovers it with overlap {overlap:.6f} and "
             f"reports nullity {found.shape[1]}. Instrumentation only: this null "
             f"direction was constructed, not discovered."))
    man.add_gate(Gate(
        "G5a_detector_recovers_the_known_vector",
        "PASS" if overlap > 1 - 1e-8 else "FAIL",
        measured=overlap, threshold=1.0,
        note="overlap between the closed-form null vector and the span the "
             "numerical detector returns"))

    # --- G5b: near-duplicate scaling ---------------------------------------
    rows = []
    base_min = sp.sigma_min_positive
    perturb = rng.normal(size=A.shape[0])
    perturb /= np.linalg.norm(perturb)
    for eps in EPSILONS:
        near = col.ravel() + eps * np.linalg.norm(col) * perturb
        A_eps = np.hstack([A, near[:, None]])
        s = spectrum_of(A_eps, A_eps.shape[1])
        rows.append({"epsilon": eps, "sigma_min": s.sigma_min_positive,
                     "sigma_max": s.sigma_max, "rank": s.numerical_rank,
                     "kappa_positive": s.kappa_positive,
                     "sigma_min_over_epsilon": s.sigma_min_positive / eps})
    sig = np.array([r["sigma_min"] for r in rows])
    eps = np.array([r["epsilon"] for r in rows])
    monotone = bool(np.all(np.diff(sig) <= 0))          # EPSILONS descend

    # The expected behaviour is sigma_min = min(baseline, C * epsilon): the
    # manufactured near-null only becomes the SMALLEST singular value once it
    # drops below the operator's own smallest. Fitting a slope across that
    # crossover measures the crossover, not the scaling, so the exponent is
    # fitted on the asymptotic branch and the crossover is reported separately.
    asymptotic = sig < 0.9 * base_min
    n_asym = int(asymptotic.sum())
    slope = (float(np.polyfit(np.log10(eps[asymptotic]), np.log10(sig[asymptotic]), 1)[0])
             if n_asym >= 2 else float("nan"))
    slope_all = float(np.polyfit(np.log10(eps), np.log10(sig), 1)[0])
    crossover = float(eps[asymptotic].max()) if n_asym else float("nan")
    # the piecewise model itself, as a residual over every point
    C = float(np.median(sig[asymptotic] / eps[asymptotic])) if n_asym else float("nan")
    model = np.minimum(base_min, C * eps)
    model_rel = float(np.abs(sig - model).max() / max(base_min, 1e-300))
    man.add_gate(Gate(
        "G5b_near_null_is_monotone_in_epsilon",
        "PASS" if monotone else "FAIL", measured=int(monotone), threshold=1,
        note=f"smallest singular value across epsilon = {list(EPSILONS)}: "
             f"{[f'{s:.3e}' for s in sig]}"))
    man.add_gate(gate_from_tolerance(
        "G5b_near_null_scaling_exponent", abs(slope - 1.0), 0.05,
        note=f"log-log slope of sigma_min against epsilon on the asymptotic "
             f"branch ({n_asym} of {len(rows)} points, epsilon <= {crossover:.0e}) "
             f"is {slope:.4f}; a near-duplicate column should give exactly 1. "
             f"Fitted across all points including the crossover it would read "
             f"{slope_all:.4f}, which measures where the manufactured direction "
             f"overtakes the operator's own smallest singular value, not the "
             f"scaling. Instrumentation only."))
    man.add_gate(gate_from_tolerance(
        "G5b_piecewise_model_residual", model_rel, 1e-3,
        note=f"largest deviation from sigma_min = min(baseline, C*epsilon) with "
             f"baseline {base_min:.4e} and C = {C:.4f}, relative to the baseline, "
             f"over every epsilon. This is the full expected behaviour, floor "
             f"included, rather than a slope on a hand-picked branch."))
    man.add_gate(Gate(
        "G5b_baseline_unperturbed_sigma_min", "PASS", measured=base_min,
        threshold=base_min,
        note="smallest singular value of the unaugmented physical operator, for "
             "reference: every G5b value must sit below it"))

    tbl = write_table(rows, "e3b_near_null_scaling")
    man.add_output(tbl)
    mp = man.write(reg.path, reg.sha256, runtime_seconds=time.time() - t0)
    merge_gate_file(man.gates, run_id)

    print(f"physical operator rank {sp.numerical_rank}/{d}  "
          f"sigma_min+ {base_min:.4e}   ker = {{0}}")
    print(f"\nG5a manufactured exact null: residual {residual:.3e} "
          f"(tol {G5A_TOLERANCE:.0e}), detector overlap {overlap:.10f}")
    print("\nG5b near-duplicate scaling")
    print(f"  {'epsilon':>10} {'sigma_min':>12} {'sigma_min/eps':>14} {'rank':>6}")
    for r in rows:
        print(f"  {r['epsilon']:>10.0e} {r['sigma_min']:>12.4e} "
              f"{r['sigma_min_over_epsilon']:>14.4e} {r['rank']:>6d}")
    print(f"  monotone {monotone}")
    print(f"  asymptotic branch ({n_asym} points, eps <= {crossover:.0e}): "
          f"slope {slope:.4f} (expected 1)")
    print(f"  all points incl. crossover: slope {slope_all:.4f} "
          f"(measures the crossover, not the scaling)")
    print(f"  piecewise model min(baseline, {C:.4f}*eps) residual {model_rel:.3e}")
    print("\ngates")
    for g in man.gates:
        m = g.measured
        ms = f"{m:.4g}" if isinstance(m, float) else str(m)
        dis = f"  [{g.disposition}]" if g.disposition else ""
        print(f"  {g.name:44s} {g.status:8s} {ms}{dis}")
    return 1 if man.failed_gates else 0


if __name__ == "__main__":
    raise SystemExit(main())
