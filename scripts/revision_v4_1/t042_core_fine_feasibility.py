#!/usr/bin/env python3
"""Can the cached records answer the order-0/1 question without new rays.

Feasibility pass. The triage showed the two surviving historical combinations
are carried by orders 0 and 1, so the validation question narrowed to those
two. This asks whether the archive can already answer it, and how far the
answer moves when the screen sampling is refined.

Three constructions of the same {0,1} operator, all under the frozen sigma,
the frozen 72/152 split and the frozen source Gram:

    ARCHIVED   1536 stratified rays per order from the core maps -- the
               construction the R2 result was computed on
    CORE_ALL   every valid core ray, quadrature untouched
    FINE_ALL   every valid fine ray, quadrature untouched

Nothing is interpolated between grids: each construction evaluates the
declared basis at its own landing coordinates, so no support is zero-filled
and none is dropped. The difference between ARCHIVED and CORE_ALL is the
subsample; between CORE_ALL and FINE_ALL is the refinement.

The operators have different row counts, so their difference is not an
operator with a norm. The comparable object is the 72x72 conditional Gram in
source-normalized target coordinates, which is what the singular values come
from, and Weyl on its eigenvalues bounds every singular-value change.

Memory: the fine stack is 767k rows, so the operator is never materialized.
A streaming QR carries a 224x224 factor with the same column geometry, which
determines the projector, the spectrum and the Gram exactly.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from phrt.numerics import pin

pin()

import numpy as np  # noqa: E402
from scipy.linalg import qr, solve_triangular, subspace_angles  # noqa: E402

from phrt.geometry.raymap import read  # noqa: E402
from phrt.geometry.sampling import common_count, stratified_subsample  # noqa: E402
from phrt.operators.physical import OrderRays, PhysicalOperator  # noqa: E402
from phrt.revision_v4_1 import conditioning, source_metric  # noqa: E402
from phrt.revision_v4_1.calibration import (COMMON_REFERENCE_COUNT,  # noqa: E402
                                            calibrate)
from phrt.sources.localized_basis import (LocalizedBasis,  # noqa: E402
                                          azimuthal_design, radial_design,
                                          temporal_design)
from phrt.sources.physical_basis import PhysicalBasis  # noqa: E402

R1FZ = ROOT / "artifacts" / "configs" / "R1_MAIN_FREEZE.json"
MAPS = ROOT / "artifacts" / "raymaps"
GEOMETRY = "a050_i050"
SNR_LABEL = 100.0
PRIMARY_RTOL = 1e-12
RHO = 1.0
GRAM_NODES = 12800
STACK = (0, 1)
CHUNK = 20000


def unit_source(basis: PhysicalBasis) -> np.ndarray:
    u = np.zeros(basis.dimension)
    for a in range(basis.n_radial):
        u[(a * basis.n_azimuthal + 0) * basis.n_temporal + 0] = 1.0
    return u


def tensor_gram(basis: LocalizedBasis, n: int) -> np.ndarray:
    r = basis.r_inner + (np.arange(n) + 0.5) * (basis.r_outer
                                                - basis.r_inner) / n
    wr = (basis.r_outer - basis.r_inner) / n * r
    Hr = source_metric.gram(radial_design(r, basis.r_inner, basis.r_outer,
                                          basis.n_radial), wr)
    p = (np.arange(n) + 0.5) * 2 * np.pi / n
    Hp = source_metric.gram(azimuthal_design(p, basis.n_azimuthal),
                            np.full(n, 2 * np.pi / n))
    t = basis.t_min + (np.arange(n) + 0.5) * (basis.t_max - basis.t_min) / n
    Ht = source_metric.gram(temporal_design(t, basis.t_min, basis.t_max,
                                            basis.n_temporal),
                            np.full(n, (basis.t_max - basis.t_min) / n))
    return np.kron(np.kron(Hr, Hp), Ht)


def all_valid(path: Path) -> OrderRays:
    """Every valid ray of a map, with its own pixel areas as the quadrature."""
    rm = read(path)
    v = np.flatnonzero(rm.valid)
    return OrderRays(order=rm.order, source_r=rm.source_r[v].copy(),
                     source_phi=rm.source_phi[v].copy(),
                     delay=rm.delay[v].copy(), redshift=rm.redshift[v].copy(),
                     quadrature=rm.pixel_area[v].copy())


def streaming_r(rays, t_obs, design, dim, sigma) -> np.ndarray:
    """Upper-triangular factor of the whitened stack, without forming it.

    Column geometry is all that matters downstream: for A = Q R with Q
    orthonormal, every singular value, projector and Gram of a column block of
    A equals that of the same column block of R.
    """
    R = np.zeros((0, dim))
    for o in rays:
        w = o.whitened_coefficient(1.0) / sigma      # sqrt(dOmega) g^3 / sigma
        for t in t_obs:
            arg = float(t) - o.delay
            for a in range(0, o.source_r.size, CHUNK):
                b = slice(a, a + CHUNK)
                D = design(o.source_r[b], o.source_phi[b], arg[b])
                R = qr(np.vstack([R, w[b, None] * D]), mode="r")[0][:dim]
    return R


def conditional(Rfac, target, nuisance, Rsrc):
    """Conditional spectrum and 72x72 Gram from the 224x224 column factor."""
    B_o = solve_triangular(Rsrc, Rfac[:, target].T, lower=False, trans="T").T
    B_n = Rfac[:, nuisance]
    U_n, rank = conditioning.nuisance_basis(B_n, PRIMARY_RTOL)
    B_cond = conditioning.residualize(B_o, U_n)
    _, s, Vt = np.linalg.svd(B_cond, full_matrices=False)
    return {
        "s": s, "V": Vt.T, "rank": rank,
        "gram": B_cond.T @ B_cond,
        "n_operational": int(np.sum(s >= RHO)),
        "information_conditional": float(np.sum(s ** 2)),
    }


def main(run_dir: Path) -> int:
    t0 = time.time()
    run_dir.mkdir(parents=True, exist_ok=True)
    r1 = json.loads(R1FZ.read_text())
    obs, pm = r1["observation"], r1["physical_model"]
    t_obs = np.asarray(obs["observer_times_M"], float)
    n_rays, orders = int(obs["rays_per_order"]), list(pm["orders"])
    m_star = n_rays * len(t_obs)

    rng = np.random.default_rng(int(obs["subsample_seed"]))
    base = common_count([stratified_subsample(read(
        MAPS / f"{GEOMETRY}_n{n}_core.h5"), n_rays, rng) for n in orders], rng)

    r_in, r_out = float(pm["r_inner_M"]), float(pm["r_outer_M"])
    t_lo, t_hi = float(obs["basis_t_min"]), float(obs["basis_t_max"])
    L = LocalizedBasis(r_in, r_out, t_lo, t_hi, 4, 7, 8)

    direct_times = (t_obs[:, None] - base[0].delay[None, :]).ravel()
    covered = L.temporal_columns_covering(direct_times)
    labels = L.labels()
    target = np.array([(lb["azimuthal_m"] >= 1)
                       and (not covered[lb["temporal_mode"]]) for lb in labels])
    nuisance = ~target
    assert int(target.sum()) == 72 and int(nuisance.sum()) == 152

    H = tensor_gram(L, GRAM_NODES)
    metric = source_metric.factor(H[np.ix_(target, target)],
                                  domain="r dr dphi dt on the registered "
                                         "annulus and source-time interval",
                                  n_quadrature=GRAM_NODES)

    gb = PhysicalBasis(r_in, r_out, t_lo, t_hi, 4, 7, 8)
    ref = PhysicalOperator(orders=[base[0]], observer_times=t_obs,
                           design=gb.design, dimension=gb.dimension)
    sigma = calibrate(ref.matvec(unit_source(gb)), SNR_LABEL,
                      mode=COMMON_REFERENCE_COUNT, m_reference=m_star,
                      grid_identity=GEOMETRY,
                      noise_label="R1L design count 1536 x 8").sigma

    variants = {
        "ARCHIVED": [base[n] for n in STACK],
        "COARSE_ALL": [all_valid(MAPS / f"{GEOMETRY}_n{n}_coarse.h5")
                       for n in STACK],
        "CORE_ALL": [all_valid(MAPS / f"{GEOMETRY}_n{n}_core.h5") for n in STACK],
        "FINE_ALL": [all_valid(MAPS / f"{GEOMETRY}_n{n}_fine.h5") for n in STACK],
    }

    support = {}
    for name, rays in variants.items():
        support[name] = {f"order_{o.order}": {
            "rays": int(o.source_r.size),
            "rows": int(o.source_r.size * t_obs.size),
            "quadrature_sum": float(o.quadrature.sum()),
            "response_mass_dOmega_g6": float(np.sum(
                o.quadrature * np.abs(o.redshift) ** 6)),
            "source_r_min": float(o.source_r.min()),
            "source_r_max": float(o.source_r.max()),
            "rays_outside_declared_annulus": int(np.sum(
                (o.source_r < r_in) | (o.source_r > r_out))),
        } for o in rays}

    out = {}
    for name, rays in variants.items():
        Rfac = streaming_r(rays, t_obs, L.design, L.dimension, sigma)
        out[name] = conditional(Rfac, target, nuisance, metric.R)
        s = out[name]["s"]
        print(f"{name:9s} ops {out[name]['n_operational']}  "
              f"trFcond {out[name]['information_conditional']:.6f}  "
              f"s {['%.4f' % v for v in s[:3]]}  nrank {out[name]['rank']}  "
              f"[{time.time() - t0:.0f}s]")

    # ---- gate: ARCHIVED must be the triage's {0,1} row --------------------
    a = out["ARCHIVED"]
    gate = {
        "s1": (float(a["s"][0]), 1.4098), "s2": (float(a["s"][1]), 1.2954),
        "s3": (float(a["s"][2]), 0.7606),
        "trF": (a["information_conditional"], 6.276810),
    }
    gate_pass = all(abs(g - w) <= 1e-4 * max(abs(w), 1.0)
                    for g, w in gate.values()) \
        and a["n_operational"] == 2 and a["rank"] == 148

    def compare(lo, hi, label):
        A, B = out[lo], out[hi]
        dM = B["gram"] - A["gram"]
        k = min(A["s"].size, B["s"].size)
        ds = B["s"][:k] - A["s"][:k]
        Va = A["V"][:, A["s"] >= RHO]
        Vb = B["V"][:, B["s"] >= RHO]
        ang = ([float(np.degrees(x)) for x in subspace_angles(Va, Vb)]
               if Va.shape[1] and Vb.shape[1] else [])
        return {
            "label": label, "from": lo, "to": hi,
            "gram_difference_operator_norm": float(np.linalg.norm(dM, 2)),
            "gram_difference_frobenius": float(np.linalg.norm(dM, "fro")),
            "max_abs_singular_value_change": float(np.abs(ds).max()),
            "singular_value_changes_top3": [float(v) for v in ds[:3]],
            "operational_count": [A["n_operational"], B["n_operational"]],
            "information_conditional": [A["information_conditional"],
                                        B["information_conditional"]],
            "nuisance_rank": [A["rank"], B["rank"]],
            "principal_angles_deg_operational_subspaces": ang,
            "max_principal_angle_deg": max(ang) if ang else None,
        }

    comparisons = [compare("ARCHIVED", "CORE_ALL", "subsample effect"),
                   compare("COARSE_ALL", "CORE_ALL", "refinement coarse->core"),
                   compare("CORE_ALL", "FINE_ALL", "refinement core->fine"),
                   compare("ARCHIVED", "FINE_ALL", "archived to refined")]

    # Is the refinement change shrinking? One ratio over a 4x ray ladder is a
    # trend, not an order of convergence, and it is reported as such.
    c1 = next(c for c in comparisons if c["label"] == "refinement coarse->core")
    c2 = next(c for c in comparisons if c["label"] == "refinement core->fine")
    convergence = {
        "ladder": "coarse -> core -> fine, roughly 4x valid rays per step",
        "gram_norm_first_step": c1["gram_difference_operator_norm"],
        "gram_norm_second_step": c2["gram_difference_operator_norm"],
        "ratio_second_over_first": (c2["gram_difference_operator_norm"]
                                    / max(c1["gram_difference_operator_norm"],
                                          1e-300)),
        "shrinking": (c2["gram_difference_operator_norm"]
                      < c1["gram_difference_operator_norm"]),
        "caveat": "two steps give a trend, not a measured order of convergence, "
                  "and neither step is a distance from the continuum",
    }

    # What the measured refinement difference alone permits, via Weyl on the
    # eigenvalues of the conditional Gram: this is a bound, not a point change.
    dM = c2["gram_difference_operator_norm"]
    sF = out["FINE_ALL"]["s"]
    bounded = []
    for k in range(min(5, sF.size)):
        lo2, hi2 = max(sF[k] ** 2 - dM, 0.0), sF[k] ** 2 + dM
        bounded.append({"mode": k + 1, "s_fine": float(sF[k]),
                        "s_lower_bound": float(np.sqrt(lo2)),
                        "s_upper_bound": float(np.sqrt(hi2))})
    weyl = {
        "perturbation_used": dM,
        "source": "operator norm of the measured core->fine conditional Gram "
                  "difference, applied as if it bounded a further step of the "
                  "same size; it is not a bound on the distance to the "
                  "continuum operator",
        "per_mode": bounded,
        "guaranteed_operational_count_lower": int(sum(
            b["s_lower_bound"] >= RHO for b in bounded)),
        "possible_operational_count_upper": int(sum(
            b["s_upper_bound"] >= RHO for b in bounded)),
    }

    margins = {
        "s2_minus_rho_core_all": float(out["CORE_ALL"]["s"][1] - RHO),
        "rho_minus_s3_core_all": float(RHO - out["CORE_ALL"]["s"][2]),
        "s2_minus_rho_fine_all": float(out["FINE_ALL"]["s"][1] - RHO),
        "rho_minus_s3_fine_all": float(RHO - out["FINE_ALL"]["s"][2]),
    }

    (run_dir / "CORE_FINE_FEASIBILITY_042.json").write_text(json.dumps({
        "schema": "phrt-core-fine-feasibility/1",
        "geometry": GEOMETRY, "stack": list(STACK), "snr_label": SNR_LABEL,
        "sigma": sigma, "rho": RHO, "rtol": PRIMARY_RTOL,
        "target_columns": 72, "nuisance_columns": 152,
        "gram_nodes": GRAM_NODES,
        "interpolation_between_grids": "none; each construction evaluates the "
                                       "declared basis at its own landing "
                                       "coordinates, so no support is "
                                       "zero-filled and none is dropped",
        "archived_gate_pass": bool(gate_pass),
        "archived_gate": {k: {"rebuilt": g, "expected": w}
                          for k, (g, w) in gate.items()},
        "support": support,
        "spectra": {k: {"s_top5": [float(x) for x in v["s"][:5]],
                        "n_operational": v["n_operational"],
                        "information_conditional": v["information_conditional"],
                        "nuisance_rank": v["rank"]} for k, v in out.items()},
        "comparisons": comparisons,
        "threshold_margins": margins,
        "convergence_trend": convergence,
        "weyl_bound_from_measured_refinement": weyl,
        "superseded_run": "an earlier two-level execution of this script "
                          "(ARCHIVED/CORE_ALL/FINE_ALL, no coarse level) was "
                          "left in place under its own F042 directory; this "
                          "three-level run supersedes it and reproduces its "
                          "numbers",
        "operator_norm_note": "The three constructions have different row "
                              "counts, so B_fine - B_core is not an operator "
                              "and has no norm. The reported quantity is the "
                              "operator norm of the difference of the 72x72 "
                              "conditional Grams in source-normalized target "
                              "coordinates; by Weyl it bounds every change in "
                              "a squared singular value.",
    }, indent=2) + "\n")

    print(f"archived gate: {'PASS' if gate_pass else 'FAIL'}")
    print(f"  convergence: {convergence['gram_norm_first_step']:.4e} -> "
          f"{convergence['gram_norm_second_step']:.4e}  "
          f"ratio {convergence['ratio_second_over_first']:.3f}  "
          f"shrinking {convergence['shrinking']}")
    print(f"  Weyl at the measured step: count in "
          f"[{weyl['guaranteed_operational_count_lower']}, "
          f"{weyl['possible_operational_count_upper']}]")
    for c in comparisons:
        print(f"  {c['label']:24s} ||dGram||2 {c['gram_difference_operator_norm']:.4e}  "
              f"max|ds| {c['max_abs_singular_value_change']:.4e}  "
              f"ops {c['operational_count']}  "
              f"angle {c['max_principal_angle_deg']}")
    print(f"  runtime {time.time() - t0:.0f}s")
    return 0 if gate_pass else 1


if __name__ == "__main__":
    raise SystemExit(main((ROOT / sys.argv[1]).resolve()))
