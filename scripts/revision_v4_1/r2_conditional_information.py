#!/usr/bin/env python3
"""What of the old source survives when the rest of it is unknown.

Ledger C08, protocol R2. An operator calculation at the reference geometry:
no reconstruction, no truths, no estimator, no new geodesics.

The question the archive never asked. ``||B q||^2`` holds every other source
coefficient fixed, so a large old-age sensitivity is compatible with the old
component being indistinguishable from a recent one. Here the target response
is residualized against everything the declared nuisance can produce, and what
is left is what the likelihood can separate.

Target and nuisance are fixed from support geometry alone and written to a
manifest before any spectrum is computed. The target is the non-axisymmetric
compact temporal factors whose support no direct-order ray reaches; the
nuisance is every other coefficient of the same full L224 model -- the old
axisymmetric baseline, all recent emission and the boundary-overlap factors.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from phrt.numerics import pin

pin()

import numpy as np  # noqa: E402

from phrt.geometry.raymap import read  # noqa: E402
from phrt.geometry.sampling import common_count, stratified_subsample  # noqa: E402
from phrt.operators.physical import PhysicalOperator  # noqa: E402
from phrt.revision_v4_1 import conditioning, source_metric  # noqa: E402
from phrt.revision_v4_1.calibration import (COMMON_REFERENCE_COUNT,  # noqa: E402
                                            LEGACY_REPLAY, calibrate)
from phrt.sources.localized_basis import (LocalizedBasis,  # noqa: E402
                                          azimuthal_design, radial_design,
                                          temporal_design)
from phrt.sources.physical_basis import PhysicalBasis  # noqa: E402

R1FZ = ROOT / "artifacts" / "configs" / "R1_MAIN_FREEZE.json"
MAPS = ROOT / "artifacts" / "raymaps"
GEOMETRY = "a050_i050"
SNR_LABEL = 100.0
RTOLS = (1e-13, 1e-12, 1e-11)
PRIMARY_RTOL = 1e-12
RHO = 1.0


def unit_source(basis: PhysicalBasis) -> np.ndarray:
    u = np.zeros(basis.dimension)
    for a in range(basis.n_radial):
        u[(a * basis.n_azimuthal + 0) * basis.n_temporal + 0] = 1.0
    return u


def tensor_gram(basis: LocalizedBasis, n: int) -> tuple[np.ndarray, dict]:
    """H = H_r (x) H_phi (x) H_t under the measure r dr dphi dt.

    The basis is separable, so the Gram is a Kronecker product of three
    one-dimensional Grams and is exact rather than sampled in 3-D. Each factor
    is a midpoint rule on the registered domain; refinement is reported.
    """
    r = basis.r_inner + (np.arange(n) + 0.5) * (basis.r_outer
                                                - basis.r_inner) / n
    wr = (basis.r_outer - basis.r_inner) / n * r          # the r dr measure
    Hr = source_metric.gram(radial_design(r, basis.r_inner, basis.r_outer,
                                          basis.n_radial), wr)
    p = (np.arange(n) + 0.5) * 2 * np.pi / n
    Hp = source_metric.gram(azimuthal_design(p, basis.n_azimuthal),
                            np.full(n, 2 * np.pi / n))
    t = basis.t_min + (np.arange(n) + 0.5) * (basis.t_max - basis.t_min) / n
    Ht = source_metric.gram(temporal_design(t, basis.t_min, basis.t_max,
                                            basis.n_temporal),
                            np.full(n, (basis.t_max - basis.t_min) / n))
    H = np.kron(np.kron(Hr, Hp), Ht)                      # radial-major order
    return H, {"n_per_axis": n, "cond_radial": float(np.linalg.cond(Hr)),
               "cond_azimuthal": float(np.linalg.cond(Hp)),
               "cond_temporal": float(np.linalg.cond(Ht))}


def main(run_dir: Path) -> int:
    t0 = time.time()
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

    # ---- target and nuisance, from support geometry only -----------------
    direct_times = (t_obs[:, None] - base[0].delay[None, :]).ravel()
    covered = L.temporal_columns_covering(direct_times)
    labels = L.labels()
    target = np.array([(lb["azimuthal_m"] >= 1)
                       and (not covered[lb["temporal_mode"]]) for lb in labels])
    nuisance = ~target
    sup = L.supports()

    manifest = {
        "schema": "phrt-r2-target-manifest/1",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "frozen_before_any_spectrum": True,
        "geometry": {"id": GEOMETRY, "spin": pm["spin"],
                     "inclination_deg": pm["inclination_deg"]},
        "orders": orders, "observer_times_M": t_obs.tolist(),
        "source_class": {"id": "L224", "dimension": L.dimension,
                         "n_radial": L.n_radial, "n_azimuthal": L.n_azimuthal,
                         "n_temporal": L.n_temporal,
                         "r_inner_M": r_in, "r_outer_M": r_out,
                         "t_min_M": t_lo, "t_max_M": t_hi,
                         "full_model_includes_m0": True},
        "selection_rule": "target = azimuthal_m >= 1 AND the temporal hat's "
                          "support contains no direct-order sample. Decided "
                          "from ray support and basis geometry alone; no "
                          "singular value, error or score enters",
        "direct_footprint_M": [float(direct_times.min()),
                               float(direct_times.max())],
        "temporal_supports_M": sup.tolist(),
        "temporal_modes_covered_by_direct": [int(i) for i in
                                             np.flatnonzero(covered)],
        "temporal_modes_outside_direct_footprint": [
            int(i) for i in np.flatnonzero(~covered)],
        "n_target_columns": int(target.sum()),
        "n_nuisance_columns": int(nuisance.sum()),
        "nuisance_includes": ["old axisymmetric baseline (m=0)",
                              "all recent emission",
                              "boundary-overlap temporal factors"],
        "empty_target": bool(target.sum() == 0),
    }
    (run_dir / "R2_TARGET_AND_NUISANCE_MANIFEST.json").write_text(
        json.dumps(manifest, indent=2) + "\n")
    print(f"target {int(target.sum())} / {L.dimension} columns; "
          f"nuisance {int(nuisance.sum())}")
    print(f"  direct footprint {manifest['direct_footprint_M'][0]:.1f} to "
          f"{manifest['direct_footprint_M'][1]:.1f} M; temporal modes outside "
          f"it: {manifest['temporal_modes_outside_direct_footprint']}")
    if target.sum() == 0:
        print("EMPTY TARGET: reported, not reselected")
        return 0

    # ---- source metric on the target, with refinement --------------------
    # Node counts are multiples of the temporal hat count and the radial knot
    # count, so every kink in the basis lands on a cell boundary rather than
    # inside one; a midpoint rule then converges cleanly instead of stalling
    # on the corners.
    conv, prev, Hs = [], None, {}
    for n in (1600, 3200, 6400, 12800):
        H, info = tensor_gram(L, n)
        Hs[n] = H
        rel = (float(np.abs(H - prev).max() / np.abs(H).max())
               if prev is not None else None)
        conv.append({**info, "relative_change_from_previous": rel})
        prev = H
    H_full = Hs[12800]
    H_target = H_full[np.ix_(target, target)]
    metric = source_metric.factor(H_target, domain="r dr dphi dt on the "
                                  "registered annulus and source-time interval",
                                  n_quadrature=12800)
    print(f"  source Gram: last refinement relative change "
          f"{conv[-1]['relative_change_from_previous']:.2e}, "
          f"target Gram condition {metric.condition:.3e}")

    metric_coarse = source_metric.factor(
        Hs[6400][np.ix_(target, target)],
        domain="coarser refinement, for the endpoint stability check",
        n_quadrature=6400)

    # ---- one noise level, shared by both arms ----------------------------
    gb = PhysicalBasis(r_in, r_out, t_lo, t_hi, 4, 7, 8)
    ref_direct = PhysicalOperator(orders=[base[0]], observer_times=t_obs,
                                  design=gb.design, dimension=gb.dimension)
    clean = ref_direct.matvec(unit_source(gb))
    cal = calibrate(clean, SNR_LABEL, mode=COMMON_REFERENCE_COUNT,
                    m_reference=m_star, grid_identity=GEOMETRY,
                    noise_label="R1L design count 1536 x 8")
    legacy = calibrate(clean, SNR_LABEL, mode=LEGACY_REPLAY,
                       grid_identity=GEOMETRY)
    print(f"  sigma {cal.sigma:.12g} (legacy {legacy.sigma:.12g}; "
          f"ratio {cal.sigma / legacy.sigma:.12f})")

    # ---- the two arms ----------------------------------------------------
    arms = {"DIRECT_PHYSICAL": [base[0]], "RESOLVED_PHYSICAL": base}
    rows, spectra, stability = [], {}, {}
    for arm, ords in arms.items():
        op = PhysicalOperator(orders=ords, observer_times=t_obs,
                              design=L.design, dimension=L.dimension)
        A = op.to_dense() / cal.sigma          # whitened once, then the SNR
        B_o = metric.to_physical(A[:, target])
        B_n = A[:, nuisance]
        # Promotion needs the endpoints stable across the last two Gram
        # refinements, not merely the Gram entries converged.
        coarse = conditioning.conditional_spectrum(
            metric_coarse.to_physical(A[:, target]), B_n, rtol=PRIMARY_RTOL,
            rho=RHO)
        fine = conditioning.conditional_spectrum(B_o, B_n, rtol=PRIMARY_RTOL,
                                                 rho=RHO)
        stability[arm] = {
            "operational_conditional_stable":
                coarse.n_operational_conditional
                == fine.n_operational_conditional,
            "information_relative_change": (
                abs(fine.information_conditional
                    - coarse.information_conditional)
                / max(coarse.information_conditional, 1e-300)),
            "coarse_ops": coarse.n_operational_conditional,
            "fine_ops": fine.n_operational_conditional,
        }
        for rtol in RTOLS:
            sp = conditioning.conditional_spectrum(B_o, B_n, rtol=rtol,
                                                   rho=RHO)
            rows.append({
                "arm": arm, "rtol": rtol,
                "target_dimension": sp.target_dimension,
                "nuisance_rank": sp.nuisance_rank,
                "information_known_remainder": sp.information_known,
                "information_conditional": sp.information_conditional,
                "s_known_max": float(sp.s_known.max()),
                "s_known_min": float(sp.s_known.min()),
                "s_conditional_max": float(sp.s_conditional.max()),
                "s_conditional_min": float(sp.s_conditional.min()),
                "n_operational_known": sp.n_operational_known,
                "n_operational_conditional": sp.n_operational_conditional,
                "sigma": cal.sigma,
            })
            if rtol == PRIMARY_RTOL:
                spectra[f"{arm}_known"] = sp.s_known
                spectra[f"{arm}_conditional"] = sp.s_conditional
                print(f"  {arm:18s} known {sp.information_known:.6e} "
                      f"({sp.n_operational_known}/{sp.target_dimension} ops) -> "
                      f"conditional {sp.information_conditional:.6e} "
                      f"({sp.n_operational_conditional} ops), "
                      f"nuisance rank {sp.nuisance_rank}")

    # ---- did a tolerance choice change a conclusion? ---------------------
    unresolved = []
    for arm in arms:
        rs = [r for r in rows if r["arm"] == arm]
        if len({r["n_operational_conditional"] for r in rs}) > 1 \
                or len({r["nuisance_rank"] for r in rs}) > 1:
            unresolved.append(arm)

    import csv
    with (run_dir / "reference_geometry_information.csv").open(
            "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    with (run_dir / "nuisance_rank_sensitivity.csv").open(
            "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["arm", "rtol", "nuisance_rank",
                                           "n_operational_conditional",
                                           "information_conditional"])
        w.writeheader()
        w.writerows([{k: r[k] for k in w.fieldnames} for r in rows])
    np.savez(run_dir / "nuisance_adjusted_spectra.npz", **spectra)
    (run_dir / "physical_metric_convergence.json").write_text(json.dumps({
        "schema": "phrt-source-metric-convergence/1",
        "measure": "r dr dphi dt, nondimensional, on the registered domain",
        "separable": "H = H_r (x) H_phi (x) H_t, exact for this basis",
        "refinements": conv,
        "target_gram_condition": metric.condition,
        "endpoint_stability_across_last_two_refinements": stability,
        "promoted": (conv[-1]["relative_change_from_previous"] < 1e-6
                     and all(v["operational_conditional_stable"]
                             for v in stability.values())),
    }, indent=2) + "\n")

    print(f"  tolerance-unstable arms: {unresolved or 'none'}")
    for a, v in stability.items():
        print(f"  {a:18s} endpoint stable across refinements: "
              f"{v['operational_conditional_stable']} "
              f"({v['coarse_ops']} -> {v['fine_ops']} ops, "
              f"info rel change {v['information_relative_change']:.2e})")
    print(f"  runtime {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main((ROOT / sys.argv[1]).resolve()))
