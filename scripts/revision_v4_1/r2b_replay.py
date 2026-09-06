#!/usr/bin/env python3
"""Phase B: the clean reference-geometry replay, with modes exported.

Guarded before it starts: the input freeze must verify, the target column set
must equal the committed one index for index, and the output directory must
not already exist. The completion token is computed from the seven declared
conditions, so this runner cannot report success while a prerequisite failed.

Same target, nuisance model, noise convention, geometry and tolerances as the
candidate. Nothing is tuned toward the expected values; a difference is
reported and investigated.
"""
from __future__ import annotations

import csv
import json
import platform
import resource
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from phrt.numerics import pin

pin()

import numpy as np  # noqa: E402
import scipy  # noqa: E402

from phrt.geometry.raymap import read  # noqa: E402
from phrt.geometry.sampling import common_count, stratified_subsample  # noqa: E402
from phrt.operators.physical import PhysicalOperator  # noqa: E402
from phrt.revision_v4_1 import conditioning, guards, source_metric  # noqa: E402
from phrt.revision_v4_1.calibration import (COMMON_REFERENCE_COUNT,  # noqa: E402
                                            calibrate)
from phrt.revision_v4_1.completion import Completion  # noqa: E402
from phrt.sources.localized_basis import (LocalizedBasis,  # noqa: E402
                                          azimuthal_design, radial_design,
                                          temporal_design)
from phrt.sources.physical_basis import PhysicalBasis  # noqa: E402

REV = ROOT / "artifacts" / "revisions" / "mahakal_v4_1"
CANDIDATE = REV / "R0_20260906T070540Z_38e1f8a"
MANIFEST = REV / "R2_REPLAY_TARGET_MANIFEST.json"
FREEZE = REV / "R2_REPLAY_INPUT_FREEZE.json"
R1FZ = ROOT / "artifacts" / "configs" / "R1_MAIN_FREEZE.json"
MAPS = ROOT / "artifacts" / "raymaps"
GEOMETRY, SNR_LABEL, RHO = "a050_i050", 100.0, 1.0
RTOLS, PRIMARY_RTOL = (1e-13, 1e-12, 1e-11), 1e-12
CMP_RTOL, CMP_ATOL = 1e-10, 1e-12
N_MODES = 3


def unit_source(b: PhysicalBasis) -> np.ndarray:
    u = np.zeros(b.dimension)
    for a in range(b.n_radial):
        u[(a * b.n_azimuthal + 0) * b.n_temporal + 0] = 1.0
    return u


def tensor_gram(L: LocalizedBasis, n: int) -> np.ndarray:
    r = L.r_inner + (np.arange(n) + 0.5) * (L.r_outer - L.r_inner) / n
    Hr = source_metric.gram(radial_design(r, L.r_inner, L.r_outer, L.n_radial),
                            (L.r_outer - L.r_inner) / n * r)
    p = (np.arange(n) + 0.5) * 2 * np.pi / n
    Hp = source_metric.gram(azimuthal_design(p, L.n_azimuthal),
                            np.full(n, 2 * np.pi / n))
    t = L.t_min + (np.arange(n) + 0.5) * (L.t_max - L.t_min) / n
    Ht = source_metric.gram(temporal_design(t, L.t_min, L.t_max, L.n_temporal),
                            np.full(n, (L.t_max - L.t_min) / n))
    return np.kron(np.kron(Hr, Hp), Ht)


def subspace_angles(A: np.ndarray, B: np.ndarray) -> list[float]:
    from scipy.linalg import subspace_angles as sa
    return [float(x) for x in sa(A, B)]


def main(run_dir: Path) -> int:
    t0 = time.time()
    comp = Completion()

    # ---- guards, before anything is computed -----------------------------
    run_dir = guards.require_fresh_output_dir(run_dir)
    tests = subprocess.run(["python3", "-m", "pytest", "tests/revision_v4_1/",
                            "-q", "--no-header"], cwd=ROOT,
                           capture_output=True, text=True)
    tail = [l for l in tests.stdout.strip().splitlines() if l.strip()][-1:]
    comp.record("prerequisite_test_success", tests.returncode == 0,
                tail[0] if tail else "not run")
    inputs = guards.verify_inputs(FREEZE, ROOT)

    r1 = json.loads(R1FZ.read_text())
    obs, pm = r1["observation"], r1["physical_model"]
    t_obs = np.asarray(obs["observer_times_M"], float)
    rng = np.random.default_rng(int(obs["subsample_seed"]))
    base = common_count([stratified_subsample(
        read(MAPS / f"{GEOMETRY}_n{n}_core.h5"), int(obs["rays_per_order"]),
        rng) for n in pm["orders"]], rng)

    L = LocalizedBasis(float(pm["r_inner_M"]), float(pm["r_outer_M"]),
                       float(obs["basis_t_min"]), float(obs["basis_t_max"]),
                       4, 7, 8)
    direct_times = (t_obs[:, None] - base[0].delay[None, :]).ravel()
    covered = L.temporal_columns_covering(direct_times)
    labels = L.labels()
    target = np.array([(lb["azimuthal_m"] >= 1)
                       and (not covered[lb["temporal_mode"]]) for lb in labels])
    nuisance = ~target
    sel = guards.verify_target_columns(MANIFEST, target, nuisance)
    comp.record("verified_input_and_target_hashes", True,
                f"{inputs['n_inputs']} frozen inputs match; target column "
                f"indices identical to the committed manifest")

    # ---- source metric ---------------------------------------------------
    H6400, H12800 = tensor_gram(L, 6400), tensor_gram(L, 12800)
    gram_rel = float(np.abs(H12800 - H6400).max() / np.abs(H12800).max())
    metric = source_metric.factor(H12800[np.ix_(target, target)],
                                  domain="r dr dphi dt", n_quadrature=12800)
    coarse = source_metric.factor(H6400[np.ix_(target, target)],
                                  domain="r dr dphi dt", n_quadrature=6400)

    gb = PhysicalBasis(L.r_inner, L.r_outer, L.t_min, L.t_max, 4, 7, 8)
    ref = PhysicalOperator(orders=[base[0]], observer_times=t_obs,
                           design=gb.design, dimension=gb.dimension)
    cal = calibrate(ref.matvec(unit_source(gb)), SNR_LABEL,
                    mode=COMMON_REFERENCE_COUNT,
                    m_reference=int(obs["rays_per_order"]) * len(t_obs),
                    grid_identity=GEOMETRY)

    rows, spectra, modes, stability = [], {}, {}, {}
    for arm, ords in (("DIRECT_PHYSICAL", [base[0]]),
                      ("RESOLVED_PHYSICAL", base)):
        op = PhysicalOperator(orders=ords, observer_times=t_obs,
                              design=L.design, dimension=L.dimension)
        A = op.to_dense() / cal.sigma
        B_o, B_n = metric.to_physical(A[:, target]), A[:, nuisance]
        per_tol = {}
        for rtol in RTOLS:
            sp = conditioning.conditional_spectrum(B_o, B_n, rtol=rtol, rho=RHO)
            per_tol[rtol] = sp
            rows.append({"arm": arm, "rtol": rtol,
                         "target_dimension": sp.target_dimension,
                         "nuisance_rank": sp.nuisance_rank,
                         "information_known_remainder": sp.information_known,
                         "information_conditional": sp.information_conditional,
                         "n_operational_known": sp.n_operational_known,
                         "n_operational_conditional":
                             sp.n_operational_conditional,
                         "sigma": cal.sigma})
        sp = per_tol[PRIMARY_RTOL]
        spectra[f"{arm}_known"] = sp.s_known
        spectra[f"{arm}_conditional"] = sp.s_conditional

        # endpoint stability across the last two metric refinements
        cs = conditioning.conditional_spectrum(coarse.to_physical(A[:, target]),
                                               B_n, rtol=PRIMARY_RTOL, rho=RHO)
        stability[arm] = {
            "ops_coarse": cs.n_operational_conditional,
            "ops_fine": sp.n_operational_conditional,
            "stable": cs.n_operational_conditional
            == sp.n_operational_conditional}

        # ---- mode export -------------------------------------------------
        U_n, _ = conditioning.nuisance_basis(B_n, PRIMARY_RTOL)
        B_cond = conditioning.residualize(B_o, U_n)
        Uc, sc, Vt = np.linalg.svd(B_cond, full_matrices=False)
        k = min(N_MODES, Vt.shape[0])
        V = Vt[:k].copy()
        # coefficients in the source basis: R^{-1} v, since B_phys = B R^{-1}
        from scipy.linalg import solve_triangular
        coeff = solve_triangular(metric.R, V.T, lower=False).T
        for j in range(k):
            big = int(np.argmax(np.abs(coeff[j])))
            if coeff[j, big] < 0:
                V[j], coeff[j] = -V[j], -coeff[j]
        known_on_mode = [float(np.sum((B_o @ V[j]) ** 2)) for j in range(k)]
        cond_on_mode = [float(np.sum((B_cond @ V[j]) ** 2)) for j in range(k)]
        tgt_idx = np.flatnonzero(target)
        modes[arm] = {
            "singular_values": [float(x) for x in sc[:k]],
            "threshold_margins_against_rho": [float(x - RHO) for x in sc[:k]],
            "right_singular_vectors": V.tolist(),
            "source_coefficient_vectors": coeff.tolist(),
            "source_physical_norms": [
                float(np.sqrt(coeff[j] @ metric.H @ coeff[j]))
                for j in range(k)],
            "known_information_on_this_direction": known_on_mode,
            "conditional_information_on_this_direction": cond_on_mode,
            "column_labels": [labels[i] for i in tgt_idx],
            "target_column_indices": [int(i) for i in tgt_idx],
            "sign_rule": "largest absolute source coefficient made positive",
            "subspace_angles_across_rank_tolerances": {
                f"{a:g}_vs_{b:g}": subspace_angles(
                    np.linalg.svd(conditioning.residualize(
                        B_o, conditioning.nuisance_basis(B_n, a)[0]),
                        full_matrices=False)[2][:k].T,
                    np.linalg.svd(conditioning.residualize(
                        B_o, conditioning.nuisance_basis(B_n, b)[0]),
                        full_matrices=False)[2][:k].T)
                for a, b in ((1e-13, 1e-12), (1e-12, 1e-11))} if sc.size else {},
            "subspace_angles_across_last_two_metric_refinements":
                subspace_angles(
                    V.T, np.linalg.svd(conditioning.residualize(
                        coarse.to_physical(A[:, target]), U_n),
                        full_matrices=False)[2][:k].T) if sc.size else [],
            "interpretation": "signed source perturbations, not reconstructed "
                              "histories",
        }

    # ---- completion conditions ------------------------------------------
    finite = all(np.all(np.isfinite(v)) for v in spectra.values())
    comp.record("finite_numeric_outputs", finite, "all spectra finite")
    promoted = gram_rel < 1e-6 and all(v["stable"] for v in stability.values())
    comp.record("source_metric_promotion", promoted,
                f"Gram relative change {gram_rel:.3e}; endpoints stable "
                f"{ {k: v['stable'] for k, v in stability.items()} }")
    stable = True
    for arm in ("DIRECT_PHYSICAL", "RESOLVED_PHYSICAL"):
        rs = [r for r in rows if r["arm"] == arm]
        if len({r["nuisance_rank"] for r in rs}) > 1 or \
                len({r["n_operational_conditional"] for r in rs}) > 1:
            stable = False
    comp.record("stable_nuisance_rank_and_operational_counts_across_registered_"
                "tolerances", stable,
                "nuisance rank and operational counts agree across "
                f"{list(RTOLS)}" if stable else "a decision moved with rtol")
    comp.record("explicit_source_rank_and_nuisance_rank_decisions", True,
                f"target Gram condition {metric.condition:.3e}; nuisance "
                f"ranks {sorted({r['nuisance_rank'] for r in rows})}")

    # ---- comparison with the archived candidate --------------------------
    cand = np.load(CANDIDATE / "nuisance_adjusted_spectra.npz",
                   allow_pickle=False)
    cmp_rows, worst_abs, worst_rel = [], 0.0, 0.0
    for key in sorted(spectra):
        a, b = np.asarray(cand[key], float), np.asarray(spectra[key], float)
        n = min(a.size, b.size)
        da = float(np.abs(a[:n] - b[:n]).max()) if n else 0.0
        # relative error only where the candidate is not near zero
        big = np.abs(a[:n]) > CMP_ATOL
        dr = float(np.abs(a[:n][big] / b[:n][big] - 1).max()) if big.any() else 0.0
        worst_abs, worst_rel = max(worst_abs, da), max(worst_rel, dr)
        cmp_rows.append({"quantity": key, "n": n, "max_abs_difference": da,
                         "max_relative_difference_above_atol": dr,
                         "n_near_zero_compared_absolutely":
                             int((~big).sum()),
                         "within_tolerance": da <= CMP_ATOL or dr <= CMP_RTOL})
    reproduced = all(r["within_tolerance"] for r in cmp_rows)
    comp.record("no_unresolved_blocker", reproduced,
                f"worst absolute difference {worst_abs:.3e}, worst relative "
                f"{worst_rel:.3e} against atol {CMP_ATOL:g} / rtol {CMP_RTOL:g}")

    # ---- outputs ---------------------------------------------------------
    for name, data in (("reference_geometry_information.csv", rows),
                       ("nuisance_rank_sensitivity.csv",
                        [{k: r[k] for k in ("arm", "rtol", "nuisance_rank",
                                            "n_operational_conditional",
                                            "information_conditional")}
                         for r in rows]),
                       ("candidate_vs_replay.csv", cmp_rows)):
        with (run_dir / name).open("w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(data[0].keys()))
            w.writeheader()
            w.writerows(data)
    np.savez(run_dir / "nuisance_adjusted_spectra.npz", **spectra)
    (run_dir / "mode_export.json").write_text(json.dumps(modes, indent=2) + "\n")
    (run_dir / "completion.json").write_text(
        json.dumps(comp.to_dict(), indent=2) + "\n")
    (run_dir / "execution_provenance.json").write_text(json.dumps({
        "schema": "phrt-phase-provenance/1", "phase": "R2_REPLAY",
        "execution_commit": subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True,
            text=True).stdout.strip(),
        "execution_branch": subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=ROOT,
            capture_output=True, text=True).stdout.strip(),
        "tree_clean_at_start": subprocess.run(
            ["git", "status", "--porcelain", ":/src", ":/scripts", ":/tests",
             ":/artifacts/configs"], cwd=ROOT, capture_output=True,
            text=True).stdout.strip() == "",
        "command": " ".join([sys.executable, *sys.argv]),
        "input_freeze": {"path": str(FREEZE.relative_to(ROOT)),
                         "sha256": guards.sha256(FREEZE), **inputs},
        "target_manifest_sha256": guards.sha256(MANIFEST),
        "target_selection_check": sel,
        "python": platform.python_version(), "numpy": np.__version__,
        "scipy": scipy.__version__, "platform": platform.platform(),
        "runtime_seconds": round(time.time() - t0, 1),
        "max_rss_mib": round(
            resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 1),
        "sigma": cal.sigma, "calibration_mode": cal.mode,
    }, indent=2) + "\n")

    print(f"  token: {comp.token}")
    print(f"  reproduction: worst abs {worst_abs:.3e}, worst rel {worst_rel:.3e}")
    for arm in ("DIRECT_PHYSICAL", "RESOLVED_PHYSICAL"):
        r = next(x for x in rows if x["arm"] == arm and x["rtol"] == PRIMARY_RTOL)
        print(f"  {arm:18s} known {r['information_known_remainder']:.6f} -> "
              f"conditional {r['information_conditional']:.6f}, ops "
              f"{r['n_operational_known']} -> {r['n_operational_conditional']}")
    print(f"  modes exported: "
          f"{ {k: len(v['singular_values']) for k, v in modes.items()} }")
    return 0 if comp.ok else 1


if __name__ == "__main__":
    raise SystemExit(main((ROOT / sys.argv[1]).resolve()))
