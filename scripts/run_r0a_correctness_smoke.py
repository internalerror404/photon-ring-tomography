#!/usr/bin/env python3
"""R0A -- reconstruction correctness smoke.

Runs on a deliberately small, uniquely labelled profile so that a correctness
failure is cheap to find and impossible to confuse with a pilot result: every
output is written under the ``r0_smoke_`` prefix.

Any failure here stops the task. Reconstruction quality is not interpreted at
this stage and no quality number is emitted.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from phrt.audits.e3c_contract import detectability
from phrt.config import load_registry, sha256_file
from phrt.geometry.raymap import read
from phrt.geometry.sampling import common_count, stratified_subsample
from phrt.inverse.reduced import reduce_operator
from phrt.inverse.ridge import ridge_dense, ridge_from_statistic
from phrt.inverse.smoothness import (temporal_difference_operator,
                                     tikhonov_dense, tikhonov_from_statistic)
from phrt.inverse.state_space import (random_walk_precision, state_space_dense,
                                      state_space_from_statistic)
from phrt.inverse.tsvd import tsvd_dense, tsvd_from_statistic
from phrt.inverse.wiener import fit_gaussian_prior, wiener_dense, wiener_from_statistic
from phrt.attestation import attest
from phrt.governance import r0_provenance
from phrt.io.manifests import Gate, RunManifest, gate_from_tolerance, make_run_id
from phrt.io.tables import write_table
from phrt.operators.physical import OrderRays, PhysicalOperator
from phrt.sources.bank import (BankContext, build_split, disjointness_report,
                               stream)
from phrt.sources.movie import Movie
from phrt.sources.near_null import (amplitude_for_target,
                                    direction_for_separation,
                                    realized_separation)
from phrt.sources.physical_basis import PhysicalBasis, age_probe_norms

FREEZE = ROOT / "artifacts" / "configs" / "R0_CANARY_RECONSTRUCTION_PILOT_FREEZE.json"
GATES_OUT = ROOT / "artifacts" / "gates" / "r0_correctness_gates.json"


def rel(a, b) -> float:
    """Relative discrepancy with the launch's max(1, .) denominator."""
    num = float(np.linalg.norm(np.asarray(a) - np.asarray(b)))
    den = max(1.0, float(np.linalg.norm(np.asarray(a))))
    return num / den


def smoke_operators(fz: dict):
    """A small resolved operator plus its declared linear readouts."""
    sp = fz["smoke_profile"]
    n_rays, n_times = int(sp["rays_per_order"]), int(sp["observer_times"])
    rng = np.random.default_rng(int(fz["observation"]["subsample_seed"]))
    maps = [read(ROOT / "artifacts" / "raymaps" / f"a050_i050_n{n}_core.h5")
            for n in (0, 1, 2)]
    base = common_count([stratified_subsample(m, n_rays, rng) for m in maps], rng)
    t_obs = np.linspace(0.0, float(fz["observation"]["observer_span_M"]), n_times)
    r_in = min(float(o.source_r.min()) for o in base)
    r_out = max(float(o.source_r.max()) for o in base)
    t_lo = float(t_obs.min() - max(o.delay.max() for o in base)) - 9.0
    t_hi = float(t_obs.max()) + 9.0
    # C48 = 4 radial x 3 azimuthal x 4 temporal, the labelled smoke class. The
    # radial factor is a cubic B-spline basis, so n_radial >= 4; the freeze
    # records the factorization for exactly this reason.
    f = fz["smoke_profile"]["source_class_factorization"]
    basis = PhysicalBasis(r_in, r_out, t_lo, t_hi,
                          n_radial=int(f["n_radial"]),
                          n_azimuthal=int(f["n_azimuthal"]),
                          n_temporal=int(f["n_temporal"]))
    kw = dict(observer_times=t_obs, design=basis.design,
              dimension=basis.dimension)
    ops = {
        "RESOLVED_PHYSICAL": PhysicalOperator(orders=base, **kw),
        "DIRECT_PHYSICAL": PhysicalOperator(orders=[base[0]], **kw),
        "UNRESOLVED_IMAGE": PhysicalOperator(orders=base,
                                             mixer=np.ones((1, len(base))), **kw),
        "TOTAL_FLUX": PhysicalOperator(orders=base, collapse="total_flux", **kw),
    }
    return base, basis, t_obs, ops


def main() -> int:
    t0 = time.time()
    started = time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime())
    # Captured before anything is written. A run creates its own outputs, so an
    # attestation taken at the end cannot tell a dirty start from its own work.
    att = attest([FREEZE])
    fz = json.loads(FREEZE.read_text())
    freeze_hash = hashlib.sha256(FREEZE.read_bytes()).hexdigest()
    reg = load_registry()
    tol = fz["gates"]
    rng = np.random.default_rng(4242)

    run_id = make_run_id("R0A", reg.sha256)
    man = RunManifest(run_id=run_id, experiment_id="R0A_CORRECTNESS_SMOKE",
                      seeds={"smoke": 4242}, started_at=started,
                      attestation=att,
                      extra={"profile": "R0_SMOKE", "freeze_sha256": freeze_hash,
                             **r0_provenance()})
    man.add_input(FREEZE)
    rows = []

    # ---- R0_G13 freeze commit attestation ----------------------------------
    # R0_REPAIR_AMENDMENT_004. The pilot's manifest asserted a clean tree while
    # the freeze it ran against was uncommitted; the check behind that assertion
    # matched no path in this layout and so could only ever say clean. This gate
    # states the evidence instead of the conclusion.
    f0 = att["files"][0]
    man.add_gate(Gate("R0_G13_freeze_commit_attestation",
                      "PASS" if att.get("preregistered") else "FAIL",
                      measured=int(bool(att.get("preregistered"))), threshold=1,
                      note=f"execution commit {att.get('execution_commit')}, "
                           f"head tree {att.get('head_tree_sha')}, freeze blob "
                           f"{f0['committed_blob_sha']} committed="
                           f"{f0['committed_at_execution_commit']}, freeze "
                           f"sha256 {f0['sha256'][:16]}..., tracked changes "
                           f"{att.get('n_tracked_changes')}, untracked "
                           f"{att.get('n_untracked')}, porcelain sha256 "
                           f"{att.get('porcelain_registered_sha256', '')[:16]}..."))
    rows.append({"gate": "R0_G13_freeze_commit_attestation",
                 "measured": int(bool(att.get("preregistered")))})

    base, basis, t_obs, ops = smoke_operators(fz)
    d = basis.dimension
    A = {k: op.to_dense() for k, op in ops.items()}
    print(f"smoke class d={d}, resolved rows={A['RESOLVED_PHYSICAL'].shape[0]}")

    # ---- R0_G1 dense / matrix-free parity, forward, adjoint and Gram --------
    worst = 0.0
    for name, op in ops.items():
        M = A[name]
        for _ in range(3):
            x = rng.standard_normal(d)
            y = rng.standard_normal(M.shape[0])
            worst = max(worst, rel(M @ x, op.matvec(x)))
            worst = max(worst, rel(M.T @ y, op.rmatvec(y)))
            worst = max(worst, rel(M.T @ (M @ x), op.rmatvec(op.matvec(x))))
    man.add_gate(gate_from_tolerance("R0_G1_dense_matrix_free_parity", worst,
                                     tol["R0_G1_dense_matrix_free_parity"],
                                     note="forward, adjoint and Gram action, "
                                          "every arm"))
    rows.append({"gate": "R0_G1_dense_matrix_free_parity", "measured": worst})

    # ---- R0_G2 adjoint identity --------------------------------------------
    worst = 0.0
    for name, op in ops.items():
        for _ in range(10):
            x = rng.standard_normal(d)
            y = rng.standard_normal(op.shape[0])
            a_, b_ = float(y @ op.matvec(x)), float(x @ op.rmatvec(y))
            worst = max(worst, abs(a_ - b_) / max(1.0, abs(a_), abs(b_)))
    man.add_gate(gate_from_tolerance("R0_G2_physical_adjoint", worst,
                                     tol["R0_G2_physical_adjoint"]))
    rows.append({"gate": "R0_G2_physical_adjoint", "measured": worst})

    # ---- R0_G3 quadrature / noise invariance (G10q) -------------------------
    def split_orders(orders, k):
        out = []
        for o in orders:
            out.append(OrderRays(o.order, np.repeat(o.source_r, k),
                                 np.repeat(o.source_phi, k),
                                 np.repeat(o.delay, k),
                                 np.repeat(o.redshift, k),
                                 np.repeat(o.quadrature, k) / k, o.amplitude))
        return out

    kw = dict(observer_times=t_obs, design=basis.design, dimension=d)
    G0 = PhysicalOperator(orders=base, **kw).gram()
    worst_q = 0.0
    for k in (2, 4, 8):
        Gk = PhysicalOperator(orders=split_orders(base, k), **kw).gram()
        worst_q = max(worst_q, float(np.linalg.norm(Gk - G0, 2))
                      / max(1.0, float(np.linalg.norm(G0, 2))))
    g3 = gate_from_tolerance("R0_G3_G10q_quadrature_noise_invariance", worst_q,
                             tol["R0_G3_G10q_quadrature_noise_invariance"],
                             note="pixel split into k equal-area children "
                                  "carrying the same transfer value")
    man.add_gate(g3)
    rows.append({"gate": "R0_G3_G10q_quadrature_noise_invariance",
                 "measured": worst_q})
    if g3.status != "PASS":
        print("STOP: QUADRATURE_NOISE_DEFECT")
        GATES_OUT.write_text(json.dumps(
            {"experiment": "R0A", "stop": "QUADRATURE_NOISE_DEFECT",
             "gates": {g.name: g.to_dict() for g in man.gates}}, indent=2) + "\n")
        return 2

    # ---- R0_G4 mixing covariance -------------------------------------------
    # The unresolved and total-flux arms must equal L applied to the resolved
    # UNWHITENED rows, with the covariance propagated as L C_R L^T. Comparing
    # whitened maps directly would hide a wrong covariance behind a wrong row.
    worst_mix = 0.0
    res = ops["RESOLVED_PHYSICAL"]
    blocks = [res.order_block(i) for i in range(len(res.orders))]
    unres_expect = sum(blocks)
    worst_mix = max(worst_mix, rel(unres_expect,
                                   ops["UNRESOLVED_IMAGE"].unwhitened_dense()))
    s2 = res.sigma_omega ** 2
    cov_expect = np.tile(
        s2 * sum(o.quadrature for o in res.orders), t_obs.size)
    worst_mix = max(worst_mix, rel(cov_expect,
                                   ops["UNRESOLVED_IMAGE"].channel_variance()))
    # TOTAL_FLUX under the frozen E3B/E3C semantics collapses all spatial
    # information but keeps the orders as separate channels, so the expected
    # variance is per order, tiled over observer times -- not one summed light
    # curve. Asserting the single-channel form here would fail against a
    # correct operator.
    flux_cov = np.concatenate([np.full(t_obs.size, s2 * float(o.quadrature.sum()))
                               for o in res.orders])
    worst_mix = max(worst_mix, rel(flux_cov,
                                   ops["TOTAL_FLUX"].channel_variance()))
    for name in ("UNRESOLVED_IMAGE", "TOTAL_FLUX"):
        x = rng.standard_normal(d)
        worst_mix = max(worst_mix, rel(A[name] @ x, ops[name].matvec(x)))
    man.add_gate(gate_from_tolerance("R0_G4_mixing_covariance", worst_mix,
                                     tol["R0_G4_mixing_covariance"],
                                     note="A_L = L A_R and C_L = L C_R L^T, "
                                          "dense and matrix-free"))
    rows.append({"gate": "R0_G4_mixing_covariance", "measured": worst_mix})

    # ---- R0_G5 basis round trip --------------------------------------------
    # Synthesise a movie from an in-class coefficient vector, evaluate it at the
    # queried coordinates, and compare against direct basis evaluation.
    o0 = base[0]
    r_q, phi_q = o0.source_r, o0.source_phi
    t_q = float(t_obs[0]) - o0.delay
    D = basis.design(r_q, phi_q, t_q)
    x_in = rng.standard_normal(d)
    synth = Movie("in_class", {"coefficients": "random"},
                  lambda r, p, t: basis.design(r, p, t) @ x_in)
    worst_rt = rel(D @ x_in, synth(r_q, phi_q, t_q))
    man.add_gate(gate_from_tolerance("R0_G5_basis_round_trip", worst_rt,
                                     tol["R0_G5_basis_round_trip"]))
    rows.append({"gate": "R0_G5_basis_round_trip", "measured": worst_rt})

    # ---- R0_G6 age probe normalisation -------------------------------------
    norms = age_probe_norms(basis.r_inner, basis.r_outer, 3.0,
                            basis.n_radial, basis.n_azimuthal)
    unit_dev = float(np.abs(norms / norms - 1.0).max())     # exact by construction
    # the substantive check: an independently quadratured norm agrees
    rq = np.linspace(basis.r_inner, basis.r_outer, 4001)
    pq = np.linspace(0.0, 2 * np.pi, 4001)[:-1]
    from phrt.sources.physical_basis import azimuthal_design, radial_design
    R = radial_design(rq, basis.r_inner, basis.r_outer, basis.n_radial)
    P = azimuthal_design(pq, basis.n_azimuthal)
    _trapz = getattr(np, "trapezoid", None) or np.trapz
    wr = _trapz(R ** 2 * rq[:, None], rq, axis=0)
    wp = (2 * np.pi / pq.size) * np.sum(P ** 2, axis=0)
    want = np.sqrt(np.outer(wr, wp).ravel() * 3.0 * np.sqrt(np.pi))
    probe_dev = float(np.abs(norms / want - 1.0).max())
    # R0_REPAIR_AMENDMENT_004 splits this. One gate previously carried the
    # declared-normalisation name and the freeze's 1e-12 threshold while
    # actually reporting a 4001-point quadrature cross-check at 5e-3, so the
    # canonical table read as though 5.55e-5 < 1e-12. Two checks, two records.
    g6a = tol.get("R0_G6a_declared_probe_unit_norm",
                  tol.get("R0_G6_age_probe_normalization", 1e-12))
    man.add_gate(gate_from_tolerance("R0_G6a_declared_probe_unit_norm",
                                     unit_dev, g6a))
    rows.append({"gate": "R0_G6a_declared_probe_unit_norm", "measured": unit_dev})
    g6b = tol.get("R0_G6b_independent_quadrature_crosscheck", 5e-3)
    man.add_gate(Gate("R0_G6b_independent_quadrature_crosscheck",
                      "PASS" if probe_dev < g6b else "FAIL",
                      measured=probe_dev, threshold=g6b,
                      note="analytic probe norm against an independent "
                           "4001-point quadrature. This is a discretisation "
                           "agreement, not the declared normalisation, and it "
                           "carries its own threshold frozen before R0C"))
    rows.append({"gate": "R0_G6b_independent_quadrature_crosscheck",
                 "measured": probe_dev})

    # ---- R0_G7 right censoring and anchored interval semantics -------------
    # Synthetic masks on a synthetic grid: this gate tests the reporting logic,
    # not a geometry, so the anchor is the grid origin by construction.
    ages = np.arange(0.0, 40.0, 4.0)
    R0A_ANCHOR_M = 0.0
    cases = {
        "contiguous_interior": [1, 1, 1, 1, 0, 0, 0, 0, 0, 0],
        "island_beyond_gap": [1, 1, 1, 0, 0, 0, 0, 0, 1, 1],
        "long_run_not_touching_anchor": [1, 1, 0, 0, 1, 1, 1, 1, 0, 0],
        "runs_to_boundary": [1] * 10,
    }
    ok7, notes7 = True, []
    for label, m in cases.items():
        dd = detectability(ages, m, R0A_ANCHOR_M)
        censored = bool(dd["oldest_detectable_age_probe"] >= 0
                        and np.isclose(dd["oldest_detectable_age_probe"],
                                       ages[-1]))
        if label == "contiguous_interior":
            ok7 &= (dd["oldest_detectable_age_probe"] == 12.0
                    and dd["longest_detectable_run_span_M"] == 12.0
                    and dd["contiguous_detectable_span_from_anchor_M"] == 12.0
                    and not censored)
        if label == "island_beyond_gap":
            ok7 &= (dd["oldest_detectable_age_probe"] == 36.0
                    and dd["longest_detectable_run_span_M"] == 8.0
                    and dd["contiguous_detectable_span_from_anchor_M"] == 8.0
                    and dd["n_detectable_runs"] == 2)
        if label == "long_run_not_touching_anchor":
            # AGE_INTERVAL_SEMANTICS_AMENDMENT_003: the longest run is 16-28 M
            # and does not reach the anchor. Reporting 12 M as depth from the
            # present would be exactly the error the amendment forbids.
            ok7 &= (dd["oldest_detectable_age_probe"] == 28.0
                    and dd["longest_detectable_run_span_M"] == 12.0
                    and dd["longest_detectable_run_start_M"] == 16.0
                    and dd["contiguous_detectable_span_from_anchor_M"] == 4.0
                    and dd["anchor_is_detectable"])
        if label == "runs_to_boundary":
            ok7 &= censored
        notes7.append(f"{label}: oldest={dd['oldest_detectable_age_probe']:.0f} "
                      f"longest_run={dd['longest_detectable_run_span_M']:.0f} "
                      f"from_anchor={dd['contiguous_detectable_span_from_anchor_M']:.0f} "
                      f"censored={censored}")
    man.add_gate(Gate("R0_G7_right_censoring", "PASS" if ok7 else "FAIL",
                      measured=len(cases), threshold=len(cases),
                      note="; ".join(notes7)
                           + ". A boundary endpoint is emitted as a lower bound, "
                             "never as exact"))
    rows.append({"gate": "R0_G7_right_censoring", "measured": int(ok7)})

    # ---- R0_G8 estimator closed forms --------------------------------------
    # Small dense problem, well inside float64's comfort zone, so the tolerance
    # tests the formula rather than the conditioning.
    m_small, d_small = 60, 12
    As = rng.standard_normal((m_small, d_small))
    ys = rng.standard_normal(m_small)
    red = reduce_operator(As, "smoke")
    bs = As.T @ ys
    g8 = {}
    g8["TSVD"] = rel(tsvd_dense(As, ys, 1e-3),
                     tsvd_from_statistic(red, bs, 1e-3))
    g8["RIDGE_IDENTITY"] = rel(ridge_dense(As, ys, 1e-3),
                               ridge_from_statistic(red, bs, 1e-3))
    Ls = temporal_difference_operator(2, 2, 3)   # 12 = 2*2*3, matches d_small
    g8["TIKHONOV_TEMPORAL"] = rel(tikhonov_dense(As, ys, 1e-3, Ls),
                                  tikhonov_from_statistic(red, bs, 1e-3,
                                                          Ls.T @ Ls))
    Xp = rng.standard_normal((200, d_small))
    prior = fit_gaussian_prior(Xp, 0.1)
    md, cd = wiener_dense(As, ys, prior)
    mr, cr = wiener_from_statistic(red, bs, prior)
    g8["WIENER_GAUSSIAN"] = max(rel(md, mr), rel(cd, cr))
    Pss = random_walk_precision(2, 2, 3, 1e-2)
    sd, scd = state_space_dense(As, ys, Pss)
    sr, scr = state_space_from_statistic(red, bs, Pss)
    g8["LINEAR_STATE_SPACE"] = max(rel(sd, sr), rel(scd, scr))
    # the sequential construction of the random-walk precision must equal a
    # directly formed tridiagonal, or "state space" is only a label
    direct = np.zeros_like(Pss)
    q = 1.0 / 1e-2
    for spm in range(4):
        b0 = spm * 3
        direct[b0, b0] += 1e-6
        for kk in range(2):
            i, j = b0 + kk, b0 + kk + 1
            direct[i, i] += q; direct[j, j] += q
            direct[i, j] -= q; direct[j, i] -= q
    g8["STATE_SPACE_PRECISION_CONSTRUCTION"] = rel(direct, Pss)
    worst8 = max(g8.values())
    man.add_gate(gate_from_tolerance("R0_G8_estimator_closed_form", worst8,
                                     tol["R0_G8_estimator_closed_form"],
                                     note="; ".join(f"{k}={v:.2e}"
                                                    for k, v in g8.items())))
    for k, v in g8.items():
        rows.append({"gate": f"R0_G8_estimator_closed_form::{k}", "measured": v})

    # ---- R0_G12 reduced-coordinate equivalence (added) ---------------------
    # The pilot simulates in b = A^T y rather than in y. That is exact only if
    # xi = A^T eta has covariance G, so it is checked rather than asserted.
    nrep = 20000
    small = reduce_operator(As, "smoke")
    eta = rng.standard_normal((nrep, m_small))
    xi_full = eta @ As
    xi_red = small.noise_statistic(rng, nrep)
    c_full = np.cov(xi_full, rowvar=False)
    c_red = np.cov(xi_red, rowvar=False)
    g_true = As.T @ As
    err_full = float(np.linalg.norm(c_full - g_true, 2)
                     / np.linalg.norm(g_true, 2))
    err_red = float(np.linalg.norm(c_red - g_true, 2)
                    / np.linalg.norm(g_true, 2))
    man.add_gate(Gate("R0_G12_reduced_statistic_equivalence",
                      "PASS" if err_red < 0.08 and err_full < 0.08 else "FAIL",
                      measured=max(err_full, err_red), threshold=0.08,
                      note=f"Monte-Carlo covariance of A^T eta ({err_full:.3f}) "
                           f"and of the reduced sampler ({err_red:.3f}) against "
                           f"G, {nrep} draws. Added beyond the launch list "
                           "because the pilot's reduced simulation would "
                           "otherwise be an unchecked assumption"))
    rows.append({"gate": "R0_G12_reduced_statistic_equivalence",
                 "measured": max(err_full, err_red)})

    # ---- R0_G9 noise replay -------------------------------------------------
    # Identical seeds and hashes must reproduce truth, noise and results
    # bitwise. Anything weaker than array_equal would let a drifting RNG through.
    ctx = BankContext(fz["source_families"]["resolved_ranges"],
                      (basis.r_inner, basis.r_outer),
                      (basis.t_min, basis.t_max))
    master = int(fz["seeds"]["master"])
    rq2, pq2 = base[0].source_r, base[0].source_phi
    tq2 = float(t_obs[0]) - base[0].delay

    def replay():
        mv = build_split("single_orbiting_hotspot", "smoke", 3, master, 1000, ctx)
        vals = [m(rq2, pq2, tq2) for m in mv]
        n_rng = np.random.default_rng([master, 6000, 0])
        noise = n_rng.standard_normal(64)
        red_ = reduce_operator(A["DIRECT_PHYSICAL"], "DIRECT_PHYSICAL")
        bb = red_.forward_statistic(np.ones(d))
        est = tsvd_from_statistic(red_, bb, 1e-3)
        return [m.content_hash for m in mv], vals, noise, est

    h1, v1, n1, e1 = replay()
    h2, v2, n2, e2 = replay()
    replay_ok = (h1 == h2 and all(np.array_equal(a_, b_) for a_, b_ in zip(v1, v2))
                 and np.array_equal(n1, n2) and np.array_equal(e1, e2))
    man.add_gate(Gate("R0_G9_noise_replay", "PASS" if replay_ok else "FAIL",
                      measured=int(replay_ok), threshold=1,
                      note="content hashes, rendered truths, noise draws and a "
                           "reconstruction all compared with array_equal, not "
                           "allclose"))
    rows.append({"gate": "R0_G9_noise_replay", "measured": int(replay_ok)})

    # ---- R0_G10 null-pair calibration ---------------------------------------
    # The realized whitened Mahalanobis separation must hit its target. This is
    # the gate that makes the Bayes bound meaningful later: a mis-scaled pair
    # would make a reconstructor look better or worse than the bound for a
    # purely bookkeeping reason.
    red_res = reduce_operator(A["RESOLVED_PHYSICAL"], "RESOLVED_PHYSICAL")
    npr = np.random.default_rng([master, 5000, 0])
    worst_delta, delta_rows = 0.0, []
    for target in fz["null_pairs"]["targets"]:
        for j in range(int(fz["smoke_profile"]["null_pairs_per_delta"])):
            u = direction_for_separation(red_res, npr, "generic")
            alpha = amplitude_for_target(red_res, u, float(target))
            realized = realized_separation(red_res, 2.0 * alpha * u)
            err = abs(realized - target) / max(target, 1e-12)
            worst_delta = max(worst_delta, err)
            delta_rows.append({"target": float(target), "realized": realized,
                               "relative_error": err})
    man.add_gate(gate_from_tolerance("R0_G10_null_pair_calibration", worst_delta,
                                     tol["R0_G10_null_pair_calibration"],
                                     note="realized whitened Mahalanobis "
                                          "separation against target, all deltas"))
    rows.append({"gate": "R0_G10_null_pair_calibration", "measured": worst_delta})

    # ---- R0_G11 split hash disjointness -------------------------------------
    groups = {}
    for fam_, off in (("single_orbiting_hotspot", 1000),
                      ("two_independent_hotspots", 1000),
                      ("rotating_asymmetric_crescent", 1000),
                      ("correlated_extended_field", 1000)):
        groups.setdefault("prior_fit_train", []).extend(
            build_split(fam_, "prior_fit_train", 4, master, off, ctx))
        groups.setdefault("validation_in_class", []).extend(
            build_split(fam_, "validation_in_class", 4, master, 2000, ctx))
    for fam_ in ("single_orbiting_hotspot", "moving_flare_birth_decay"):
        groups.setdefault("validation_off_grid", []).extend(
            build_split(fam_, "validation_off_grid", 4, master, 3000, ctx,
                        off_grid=True))
    groups["validation_ood"] = build_split("moving_flare_birth_decay",
                                           "validation_ood", 4, master, 4000, ctx)
    groups["future_main_test"] = build_split("single_orbiting_hotspot",
                                             "future_main_test", 4, master,
                                             9000, ctx)
    rep = disjointness_report(groups)
    man.add_gate(Gate("R0_G11_split_hash_disjointness",
                      "PASS" if rep["disjoint"] else "FAIL",
                      measured=rep["worst_overlap"], threshold=0,
                      note="pairwise content-hash overlap across prior-fit, "
                           "validation, off-grid, OOD and future-test splits: "
                           + json.dumps(rep["pairwise_overlap"])))
    rows.append({"gate": "R0_G11_split_hash_disjointness",
                 "measured": rep["worst_overlap"]})
    man.add_output(write_table(delta_rows, "r0_smoke_null_pair_calibration"))

    man.add_output(write_table(rows, "r0_smoke_gate_values"))
    mp = man.write(reg.path, reg.sha256, runtime_seconds=time.time() - t0)
    sub = {g.name: g.to_dict() for g in man.gates}
    GATES_OUT.parent.mkdir(parents=True, exist_ok=True)
    GATES_OUT.write_text(json.dumps(
        {"experiment": "R0A_CORRECTNESS_SMOKE", "run_id": run_id,
         "freeze_sha256": freeze_hash, "profile": "R0_SMOKE", "gates": sub,
         "summary": {s: sum(1 for v in sub.values() if v["status"] == s)
                     for s in ("PASS", "FAIL", "NOT_RUN")}}, indent=2) + "\n")
    print("\ngates")
    for g in man.gates:
        m = g.measured
        ms = f"{m:.3e}" if isinstance(m, float) else str(m)
        print(f"  {g.name:44s} {g.status:8s} {ms}")
    print(f"\nmanifest {mp}\ntotal {time.time() - t0:.0f}s")
    return 1 if man.failed_gates else 0


if __name__ == "__main__":
    raise SystemExit(main())
