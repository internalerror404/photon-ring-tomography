#!/usr/bin/env python3
"""Which image orders carry the two surviving historical combinations.

Order-attribution triage. Zero new rays, zero new truths, zero new estimators:
the cached reference-geometry maps are read, the archived R2 operator is
rebuilt under its own frozen measure and source Gram, and the question asked
of it is a decomposition, not a new experiment.

The whitened operator's rows are grouped by order and each order's whitening
uses only its own quadrature, so the operator for an order subset is exactly a
row-block of the full one. Every subset therefore shares one noise level, one
target/nuisance split and one source metric; nothing is recalibrated per
subset, because recalibration would confound the comparison being made.

The nuisance projector is rebuilt for each subset. The direct order has
identically zero target response, but it can still constrain nuisance
coefficients, so leaving it out is not the same as ignoring it.
"""
from __future__ import annotations

import csv
import json
import sys
import time
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from phrt.numerics import pin

pin()

import numpy as np  # noqa: E402
from scipy.linalg import subspace_angles  # noqa: E402

from phrt.geometry.raymap import read  # noqa: E402
from phrt.geometry.sampling import common_count, stratified_subsample  # noqa: E402
from phrt.operators.physical import PhysicalOperator  # noqa: E402
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

# The archived endpoints this rebuild must reproduce before any subset result
# is reported. Source: artifacts/.../R0_20260906T070540Z_38e1f8a/.
ARCHIVED = {
    "RESOLVED_PHYSICAL": {
        "s_conditional_top3": [1.4371649, 1.3458733, 0.8062804],
        "information_conditional": 7.198318,
        "information_known": 11.053660,
        "n_operational_known": 3,
        "n_operational_conditional": 2,
        "nuisance_rank": 152,
    },
    "DIRECT_PHYSICAL": {
        "information_known": 0.0,
        "information_conditional": 0.0,
        "n_operational_known": 0,
        "n_operational_conditional": 0,
        "nuisance_rank": 140,
    },
}
GATE_RTOL = 1e-6


def unit_source(basis: PhysicalBasis) -> np.ndarray:
    u = np.zeros(basis.dimension)
    for a in range(basis.n_radial):
        u[(a * basis.n_azimuthal + 0) * basis.n_temporal + 0] = 1.0
    return u


def tensor_gram(basis: LocalizedBasis, n: int) -> np.ndarray:
    """H = H_r (x) H_phi (x) H_t under r dr dphi dt, as the archive built it."""
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


def angles_deg(P: np.ndarray, Q: np.ndarray) -> list[float]:
    """Principal angles in degrees; [] when either subspace is trivial."""
    if P.shape[1] == 0 or Q.shape[1] == 0:
        return []
    return [float(np.degrees(a)) for a in subspace_angles(P, Q)]


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
    assert L.dimension == 224, L.dimension

    # target/nuisance: the archived rule, from support geometry alone
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

    # one noise level, from the direct arm, shared by every subset
    gb = PhysicalBasis(r_in, r_out, t_lo, t_hi, 4, 7, 8)
    ref_direct = PhysicalOperator(orders=[base[0]], observer_times=t_obs,
                                  design=gb.design, dimension=gb.dimension)
    cal = calibrate(ref_direct.matvec(unit_source(gb)), SNR_LABEL,
                    mode=COMMON_REFERENCE_COUNT, m_reference=m_star,
                    grid_identity=GEOMETRY,
                    noise_label="R1L design count 1536 x 8")

    # the full stack once; every subset is a row-block of it
    full = PhysicalOperator(orders=base, observer_times=t_obs,
                            design=L.design, dimension=L.dimension)
    A = full.to_dense() / cal.sigma
    rpc = full._rows_per_channel
    assert A.shape[0] == len(orders) * rpc, (A.shape, rpc)
    blocks = {n: slice(i * rpc, (i + 1) * rpc) for i, n in enumerate(orders)}

    def spectrum(subset):
        """Conditional spectrum and conditional operator for one order subset.

        The projector is rebuilt from this subset's own nuisance rows: the
        direct order carries no target response but can still constrain the
        nuisance, and dropping it must be allowed to show that.
        """
        rows = np.concatenate([np.arange(rpc * i, rpc * (i + 1))
                               for i, n in enumerate(orders) if n in subset])
        As = A[rows]
        B_o = metric.to_physical(As[:, target])
        sp = conditioning.conditional_spectrum(B_o, As[:, nuisance],
                                               rtol=PRIMARY_RTOL, rho=RHO)
        U_n, _ = conditioning.nuisance_basis(As[:, nuisance], PRIMARY_RTOL)
        return sp, conditioning.residualize(B_o, U_n)

    # ---- gate: reproduce the archived endpoints --------------------------
    gate = {}
    for arm, subset in (("DIRECT_PHYSICAL", (0,)),
                        ("RESOLVED_PHYSICAL", tuple(orders))):
        sp, _ = spectrum(subset)
        want = ARCHIVED[arm]
        checks = {
            "information_known": (sp.information_known,
                                  want["information_known"]),
            "information_conditional": (sp.information_conditional,
                                        want["information_conditional"]),
        }
        ok = {k: (abs(g - w) <= GATE_RTOL * max(abs(w), 1.0))
              for k, (g, w) in checks.items()}
        ok["n_operational_known"] = (sp.n_operational_known
                                     == want["n_operational_known"])
        ok["n_operational_conditional"] = (sp.n_operational_conditional
                                           == want["n_operational_conditional"])
        ok["nuisance_rank"] = sp.nuisance_rank == want["nuisance_rank"]
        if "s_conditional_top3" in want:
            top3 = np.sort(sp.s_conditional)[::-1][:3]
            ok["s_conditional_top3"] = bool(np.all(
                np.abs(top3 - np.array(want["s_conditional_top3"])) <= 1e-6))
            gate[f"{arm}_s_top3_rebuilt"] = [float(v) for v in top3]
        gate[arm] = {k: bool(v) for k, v in ok.items()}
        gate[f"{arm}_rebuilt"] = {
            "information_known": sp.information_known,
            "information_conditional": sp.information_conditional,
            "n_operational_known": sp.n_operational_known,
            "n_operational_conditional": sp.n_operational_conditional,
            "nuisance_rank": sp.nuisance_rank,
        }
    gate["all_pass"] = all(all(v.values()) for k, v in gate.items()
                           if isinstance(v, dict) and k in ARCHIVED)
    (run_dir / "REPRODUCTION_GATE_041.json").write_text(
        json.dumps(gate, indent=2) + "\n")
    print(f"reproduction gate: {'PASS' if gate['all_pass'] else 'FAIL'}")
    for arm in ARCHIVED:
        print(f"  {arm:18s} {gate[arm]}")
    if not gate["all_pass"]:
        print("gate failed: subset results are not reported")
        return 1

    # ---- full-stack reference subspace and order energies ----------------
    sp_full, B_full = spectrum(tuple(orders))
    U, s, Vt = np.linalg.svd(B_full, full_matrices=False)
    keep = s >= RHO
    V_ref = Vt[keep].T                       # the two-mode target subspace
    energy = []
    for j in range(min(5, s.size)):
        row = {"mode": j + 1, "singular_value": float(s[j])}
        tot = 0.0
        for i, n in enumerate(orders):
            f = float(np.sum(U[blocks[n], j] ** 2))
            row[f"f_order{n}"] = f
            tot += f
        row["sum"] = tot
        energy.append(row)

    # ---- the seven subsets ------------------------------------------------
    subsets = [c for k in (1, 2, 3) for c in combinations(orders, k)]
    rows = []
    for subset in subsets:
        sp, B_cond = spectrum(subset)
        _, ss, Vts = np.linalg.svd(B_cond, full_matrices=False)
        V_sub = Vts[ss >= RHO].T
        ang = angles_deg(V_sub, V_ref)
        top = np.sort(sp.s_conditional)[::-1][:5]
        rows.append({
            "subset": "".join(str(n) for n in subset),
            "n_orders": len(subset),
            **{f"s{i + 1}": float(top[i]) if i < top.size else None
               for i in range(5)},
            "n_operational_conditional": sp.n_operational_conditional,
            "n_operational_known": sp.n_operational_known,
            "information_conditional": sp.information_conditional,
            "information_known": sp.information_known,
            "nuisance_rank": sp.nuisance_rank,
            "operational_subspace_dim": int(V_sub.shape[1]),
            "principal_angles_deg_vs_full_two_mode":
                ";".join(f"{a:.4f}" for a in ang) if ang else "",
            "max_principal_angle_deg": max(ang) if ang else None,
        })
        print(f"  {rows[-1]['subset']:>3s}  ops {sp.n_operational_conditional} "
              f" trFcond {sp.information_conditional:.6f}  "
              f"s {['%.4f' % v for v in top[:3]]}  "
              f"nrank {sp.nuisance_rank}  "
              f"angles {rows[-1]['principal_angles_deg_vs_full_two_mode'] or '-'}")

    with (run_dir / "ORDER_ATTRIBUTION_041.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    (run_dir / "ORDER_ENERGY_FRACTIONS_041.json").write_text(json.dumps({
        "schema": "phrt-order-attribution/1",
        "definition": "f[j,n] = ||P_n B_cond v_j||^2 / s_j^2 for the full-stack "
                      "conditional modes; P_n selects the whitened row block of "
                      "order n. Sums to one across orders by construction.",
        "geometry": GEOMETRY, "snr_label": SNR_LABEL, "rho": RHO,
        "sigma": cal.sigma, "rtol": PRIMARY_RTOL,
        "target_columns": 72, "nuisance_columns": 152,
        "modes": energy,
    }, indent=2) + "\n")
    print(f"  runtime {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main((ROOT / sys.argv[1]).resolve()))
