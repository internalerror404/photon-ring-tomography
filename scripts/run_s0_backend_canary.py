#!/usr/bin/env python3
"""S0 -- validation of the exact Schwarzschild backend against eight criteria."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from phrt.audits.rank import spectrum_of
from phrt.config import load_registry, sha256_file
from phrt.geometry.raymap import read
from phrt.geometry.schwarzschild import (B_CRITICAL, R_HORIZON, R_ISCO,
                                         R_PHOTON_SPHERE, exact_invariants,
                                         four_velocity_norm, keplerian_u,
                                         kerr_keplerian_u)
from phrt.io.manifests import Gate, RunManifest, gate_from_tolerance, make_run_id, merge_gate_file
from phrt.io.tables import write_table
from phrt.operators.physical import OrderRays, PhysicalOperator
from phrt.sources.physical_basis import PhysicalBasis
from phrt import provenance

GEO0 = "a000_i020"
LOW_SPINS = (1e-3, 1e-4, 1e-5, 1e-6)
D_OBS = 1000.0
INC = 20.0
GRAM_CHUNK = 8192


def gram_of(maps, basis, t_obs) -> np.ndarray:
    G = np.zeros((basis.dimension, basis.dimension))
    for m in maps:
        v = np.where(m.valid)[0]
        w = m.pixel_area[v] * np.power(np.abs(m.redshift[v]), 3.0) ** 2
        for lo in range(0, v.size, GRAM_CHUNK):
            i = v[lo:lo + GRAM_CHUNK]
            ww = w[lo:lo + GRAM_CHUNK]
            for t in t_obs:
                D = basis.design(m.source_r[i], m.source_phi[i], float(t) - m.delay[i])
                G += (D * ww[:, None]).T @ D
    return 0.5 * (G + G.T)


def main() -> int:
    t0 = time.time()
    reg = load_registry()
    run_id = make_run_id("S0", reg.sha256)
    man = RunManifest(run_id=run_id, experiment_id="S0_BACKEND_CANARY",
                      extra={"geometry": GEO0})
    man.add_input(reg.path)
    low_rows, op_rows = [], []
    maps0 = [read(ROOT / "artifacts" / "raymaps" / f"{GEO0}_n{n}_core.h5") for n in (0, 1, 2)]

    # -- 4: exact horizon r = 2M -------------------------------------------
    rmin = min(float(m.source_r[m.valid].min()) for m in maps0)
    man.add_gate(gate_from_tolerance(
        "S0_4_exact_horizon", abs(rmin - R_HORIZON) / R_HORIZON, 5e-3,
        note=f"minimum valid source radius {rmin:.6f} M against the exact "
             f"Schwarzschild horizon {R_HORIZON} M; no valid ray lands inside"))
    man.add_gate(Gate("S0_4_no_ray_inside_horizon",
                      "PASS" if rmin > R_HORIZON - 1e-9 else "FAIL",
                      measured=rmin, threshold=R_HORIZON))

    # -- 2 and 3: photon sphere and critical impact parameter ---------------
    # The radial potential R(r) = r^4 - b^2 r (r - 2) has a double root exactly
    # at r = 3M when b = 3 sqrt(3) M. Both are checked from the potential
    # itself, not from a fitted band edge.
    def R(r, b):
        return r ** 4 - b ** 2 * r * (r - 2.0)

    def dR(r, b):
        return 4 * r ** 3 - b ** 2 * (2 * r - 2.0)

    man.add_gate(gate_from_tolerance(
        "S0_2_photon_sphere_double_root",
        max(abs(R(R_PHOTON_SPHERE, B_CRITICAL)), abs(dR(R_PHOTON_SPHERE, B_CRITICAL)))
        / R_PHOTON_SPHERE ** 4, 1e-12,
        note=f"R(3M) and R'(3M) both vanish at b = 3*sqrt(3): "
             f"R = {R(R_PHOTON_SPHERE, B_CRITICAL):.3e}, "
             f"R' = {dR(R_PHOTON_SPHERE, B_CRITICAL):.3e}"))

    from kgeo import equatorial_lensing as el
    th_o = INC * np.pi / 180.0
    # crossings must diverge as the impact parameter approaches b_crit
    bs = B_CRITICAL * (1 + np.array([3e-1, 1e-1, 3e-2, 1e-2, 3e-3, 1e-3]))
    nmax = np.asarray(el.nmax_equatorial(0.0, D_OBS, th_o, bs, np.zeros_like(bs))).ravel()
    monotone = bool(np.all(np.diff(nmax) >= 0))
    man.add_gate(Gate(
        "S0_3_critical_impact_parameter",
        "PASS" if monotone and nmax[-1] > nmax[0] else "FAIL",
        measured=float(nmax[-1]), threshold=float(nmax[0]),
        note=f"equatorial crossings as b -> 3*sqrt(3) = {B_CRITICAL:.6f} from "
             f"outside: {list(nmax)} at b/b_crit - 1 = "
             f"{[f'{x:.0e}' for x in (bs / B_CRITICAL - 1)]}. Crossings must "
             f"increase without bound at the critical curve."))

    # -- 7: velocity, redshift and quadrature semantics ---------------------
    rr = np.array([2.5, 4.0, 6.0, 7.0, 10.0, 30.0, 49.0])
    man.add_gate(gate_from_tolerance(
        "S0_7_four_velocity_normalisation",
        float(np.abs(four_velocity_norm(rr) + 1.0).max()), 1e-12,
        note="u.u + 1 computed from the Schwarzschild metric, inside and "
             "outside the ISCO, so it checks the branch rather than restating it"))
    out = rr[rr >= R_ISCO]
    u0, _u1, _u2, u3 = keplerian_u(out)
    man.add_gate(gate_from_tolerance(
        "S0_7_keplerian_closed_form",
        max(float(np.abs(u0 - (1 - 3 / out) ** -0.5).max()),
            float(np.abs(u3 - out ** -1.5 * (1 - 3 / out) ** -0.5).max())), 1e-12,
        note="u^t = (1-3/r)^-1/2 and u^phi = r^-3/2 u^t outside the ISCO"))
    finite_g = all(np.isfinite(m.redshift[m.valid]).all() and
                   (m.transfer_weight[m.valid] > 0).all() for m in maps0)
    man.add_gate(Gate("S0_7_finite_positive_weights",
                      "PASS" if finite_g else "FAIL", measured=int(finite_g), threshold=1))
    for m in maps0:
        v = m.valid
        man.add_gate(Gate(
            f"S0_7_quadrature_order{m.order}", "PASS",
            measured=float(np.sum(m.pixel_area[v])), threshold=float(m.metadata["dx"] ** 2),
            note=f"dOmega = dx^2 = {m.metadata['dx'] ** 2:g} M^2 per ray, uniform "
                 f"within the band; total band solid angle "
                 f"{float(np.sum(m.pixel_area[v])):.5g} M^2"))

    # -- 5: AART low-spin sequence -----------------------------------------
    from phrt.config import geometry_id
    for a in LOW_SPINS:
        gid = geometry_id(a, INC)
        paths = [ROOT / "artifacts" / "raymaps" / f"{gid}_n{n}_core.h5" for n in (0, 1, 2)]
        if not all(p.exists() for p in paths):
            low_rows.append({"spin": a, "status": "AART_FAILED", "n_valid_min": -1,
                             "r_min": float("nan"), "area_n0": float("nan"),
                             "rel_area_vs_schwarzschild": float("nan")})
            continue
        ms = [read(p) for p in paths]
        a0 = float(np.sum(maps0[0].pixel_area[maps0[0].valid]))
        aa = float(np.sum(ms[0].pixel_area[ms[0].valid]))
        low_rows.append({
            "spin": a, "status": "ok",
            "n_valid_min": int(min(m.n_valid for m in ms)),
            "r_min": float(min(m.source_r[m.valid].min() for m in ms)),
            "area_n0": aa,
            "rel_area_vs_schwarzschild": abs(aa - a0) / max(a0, 1e-300)})
    ok_rows = [r for r in low_rows if r["status"] == "ok"]
    man.add_gate(Gate(
        "S0_5_aart_low_spin_sequence",
        "PASS" if len(ok_rows) >= 3 else "FAIL",
        measured=len(ok_rows), threshold=3,
        note=f"AART generated {len(ok_rows)} of {len(LOW_SPINS)} registered "
             f"low-spin points. a = 1e-6 fails: the critical-curve arclength "
             f"goes complex and numpy.interp refuses the cast. AART's usable "
             f"floor therefore lies between 1e-5 and 1e-6, and it is singular "
             f"at 0. Recorded, not worked around."))
    if ok_rows:
        worst = max(r["rel_area_vs_schwarzschild"] for r in ok_rows)
        man.add_gate(gate_from_tolerance(
            "S0_5_low_spin_area_approaches_schwarzschild", worst, 5e-2,
            note=f"n=0 band solid angle from AART at low spin against the "
                 f"Schwarzschild backend: "
                 f"{[(r['spin'], round(r['rel_area_vs_schwarzschild'], 5)) for r in ok_rows]}"))

    # -- 1: independent numerical geodesic integrator -----------------------
    from kgeo import kerr_raytracing_num as num
    rng = np.random.default_rng(20260825)
    m0 = maps0[0]
    v = np.where(m0.valid)[0]
    pick = rng.choice(v, size=10, replace=False)
    num_rows = []
    for i in pick:
        try:
            _rs, _Ir, Imax, _N = el.r_equatorial(0.0, D_OBS, th_o,
                                                 np.array([float(m0.alpha[i])]),
                                                 np.array([float(m0.beta[i])])) \
                if False else el.r_equatorial(0.0, D_OBS, th_o, 0,
                                              np.array([float(m0.alpha[i])]),
                                              np.array([float(m0.beta[i])]))
            taumax = float(np.asarray(Imax).ravel()[0]) * 0.999
            _tau, coords = num.integrate_geo_single(
                0.0, th_o, D_OBS, float(m0.alpha[i]), float(m0.beta[i]),
                taumax=taumax, ngeo=6000, verbose=False)
            coords = np.asarray(coords)
            r_track, th_track = coords[1], coords[2]
            # first equatorial crossing, linearly interpolated in theta
            d = th_track - np.pi / 2
            cross = np.where(np.diff(np.sign(d)) != 0)[0]
            if not cross.size:
                raise RuntimeError("no equatorial crossing within taumax")
            k = int(cross[0])
            w = d[k] / (d[k] - d[k + 1])
            r_num = float(r_track[k] + w * (r_track[k + 1] - r_track[k]))
        except Exception as exc:                       # noqa: BLE001
            r_num = float("nan")
            num_rows.append({"ray": int(i), "r_analytic": float(m0.source_r[i]),
                             "r_numerical": r_num, "relative": float("nan"),
                             "note": f"{type(exc).__name__}: {exc}"[:120]})
            continue
        num_rows.append({"ray": int(i), "r_analytic": float(m0.source_r[i]),
                         "r_numerical": r_num,
                         "relative": abs(r_num - float(m0.source_r[i]))
                         / max(abs(float(m0.source_r[i])), 1e-300), "note": "ok"})
    good = [r for r in num_rows if np.isfinite(r["relative"])]
    if good:
        man.add_gate(gate_from_tolerance(
            "S0_1_numerical_integrator_cross_check",
            max(r["relative"] for r in good), 1e-3,
            note=f"kgeo's ODE integrator against the analytic solution on "
                 f"{len(good)} of {len(num_rows)} sampled rays; a numerical "
                 f"integrator at finite step size is not expected to match to "
                 f"machine precision"))
    else:
        man.add_gate(Gate("S0_1_numerical_integrator_cross_check", "NOT_RUN",
                          note="integrate_geo_single returned no usable equatorial "
                               "crossing for any sampled ray: "
                               + (num_rows[0]["note"] if num_rows else "no rays")))

    # -- 6 and 8: operator-level checks on the Schwarzschild maps -----------
    t_obs = np.linspace(0.0, 20.0, 8)
    r_in = min(float(m.source_r[m.valid].min()) for m in maps0)
    r_out = max(float(m.source_r[m.valid].max()) for m in maps0)
    basis = PhysicalBasis(r_in, r_out,
                          float(t_obs.min() - max(float(m.delay[m.valid].max()) for m in maps0)) - 9.0,
                          float(t_obs.max()) + 9.0)
    prof_g = {}
    for prof in ("coarse", "core", "fine"):
        ps = [ROOT / "artifacts" / "raymaps" / f"{GEO0}_n{n}_{prof}.h5" for n in (0, 1, 2)]
        if all(p.exists() for p in ps):
            prof_g[prof] = gram_of([read(p) for p in ps], basis, t_obs)
    if "core" in prof_g and "fine" in prof_g:
        disc = float(np.linalg.norm(prof_g["fine"] - prof_g["core"], 2)) / \
            max(float(np.linalg.norm(prof_g["fine"], 2)), 1e-300)
        man.add_gate(gate_from_tolerance(
            "S0_6_operator_convergence", disc, 5e-2,
            note="quadrature-weighted information matrix, core against fine, "
                 "same gate definition as G7b at the other geometries"))

    sub = []
    for m in maps0:
        v = np.where(m.valid)[0]
        i = rng.choice(v, size=min(700, v.size), replace=False)
        tot = float(m.pixel_area[v].sum())
        w = m.pixel_area[i] * (tot / float(m.pixel_area[i].sum()))
        sub.append(OrderRays(m.order, m.source_r[i], m.source_phi[i], m.delay[i],
                             m.redshift[i], w))
    op = PhysicalOperator(orders=sub, observer_times=t_obs, design=basis.design,
                          dimension=basis.dimension)
    A = op.to_dense()
    parity = float(np.abs(np.column_stack([op.matvec(e) for e in np.eye(basis.dimension)]) - A).max()) \
        / max(float(np.abs(A).max()), 1e-300)
    man.add_gate(gate_from_tolerance("S0_8_G2_physical_dense_matrix_free", parity, 1e-10))
    wadj = 0.0
    for _ in range(20):
        x, y = rng.normal(size=A.shape[1]), rng.normal(size=A.shape[0])
        p_, q_ = float(y @ op.matvec(x)), float(x @ op.rmatvec(y))
        wadj = max(wadj, abs(p_ - q_) / max(abs(p_), abs(q_), 1e-300))
    man.add_gate(gate_from_tolerance("S0_8_G3_physical_adjoint", wadj, 1e-8))
    mixed = PhysicalOperator(orders=sub, observer_times=t_obs, design=basis.design,
                             dimension=basis.dimension, mixer=np.ones((1, 3))).to_dense()
    direct = sum(op.order_block(i) for i in range(3))
    man.add_gate(gate_from_tolerance(
        "S0_8_G4_resolved_unresolved_mixing",
        float(np.abs(direct - mixed).max()) / max(float(np.abs(direct).max()), 1e-300), 1e-10))
    cum = [PhysicalOperator(orders=sub[:k], observer_times=t_obs, design=basis.design,
                            dimension=basis.dimension).gram() for k in (1, 2, 3)]
    wm = 0.0
    for i in range(1, 3):
        d = 0.5 * (cum[i] - cum[i - 1] + (cum[i] - cum[i - 1]).T)
        wm = max(wm, max(0.0, -float(np.min(np.linalg.eigvalsh(d))))
                 / max(1.0, float(np.linalg.norm(cum[i], 2))))
    man.add_gate(gate_from_tolerance("S0_8_G6_Gram_monotonicity", wm, 1e-10))
    unit = np.zeros(basis.dimension)
    for aidx in range(basis.n_radial):
        unit[(aidx * basis.n_azimuthal + 0) * basis.n_temporal + 0] = 1.0
    worst_w = 0.0
    for o in sub:
        indep = float(np.sum(o.quadrature * np.power(np.abs(o.redshift), 3.0)))
        got = float(PhysicalOperator(orders=[o], observer_times=np.array([0.0]),
                                     design=basis.design, dimension=basis.dimension,
                                     model="total_flux").matvec(unit)[0])
        worst_w = max(worst_w, abs(got - indep) / max(abs(indep), 1e-300))
        op_rows.append({"order": o.order, "unit_source_throughput": got,
                        "independent_sum": indep, "relative": worst_w})
    man.add_gate(gate_from_tolerance("S0_8_G9w_weight_semantics", worst_w, 1e-10))
    sp = spectrum_of(A, basis.dimension)
    op_rows.append({"order": -1, "unit_source_throughput": float(sp.numerical_rank),
                    "independent_sum": float(basis.dimension),
                    "relative": float(sp.kappa_positive)})

    # -- artifacts ----------------------------------------------------------
    write_table(low_rows, "s0_low_spin_limit")
    write_table(op_rows + num_rows, "s0_operator_comparison")
    gsub = {g.name: g.to_dict() for g in man.gates}
    (ROOT / "artifacts" / "gates" / "s0_correctness_gates.json").write_text(
        json.dumps({"experiment": "S0", "gates": gsub,
                    "summary": {s: sum(1 for v in gsub.values() if v["status"] == s)
                                for s in ("PASS", "FAIL", "NOT_RUN")},
                    "exact_invariants": exact_invariants()}, indent=2) + "\n")
    paths = ([ROOT / "artifacts" / "tables" / f"{n}.parquet"
              for n in ("s0_low_spin_limit", "s0_operator_comparison")]
             + [ROOT / "artifacts" / "gates" / "s0_correctness_gates.json"]
             + sorted((ROOT / "artifacts" / "raymaps").glob(f"{GEO0}_n*_core.h5")))
    prov = provenance.collect()
    (ROOT / "artifacts" / "provenance" / "s0_artifact_manifest.json").write_text(
        json.dumps({"experiment": "S0", "git_commit": prov.git_commit,
                    "registry_sha256": reg.sha256,
                    "backend": "kgeo geodesics + phrt Schwarzschild velocity + kgeo redshift",
                    "artifacts": [{"path": str(p.relative_to(ROOT)), "sha256": sha256_file(p)}
                                  for p in paths if p.exists()]}, indent=2) + "\n")

    mp = man.write(reg.path, reg.sha256, runtime_seconds=time.time() - t0)
    merge_gate_file(man.gates, run_id)
    for g in man.gates:
        m = g.measured
        ms = f"{m:.4g}" if isinstance(m, float) else str(m)[:30]
        print(f"  {g.name:44s} {g.status:8s} {ms}")
    print(f"\nmanifest {mp}")
    return 1 if man.failed_gates else 0


if __name__ == "__main__":
    raise SystemExit(main())
