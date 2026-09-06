#!/usr/bin/env python3
"""The localization correction, and the invariant version of what I got wrong.

Review 025. My epoch breakdown grouped the columns of B_o = A_old R^-1 by the
ORIGINAL temporal hat labels. After that right-multiplication a column no
longer belongs to one hat: the hats overlap, so R^-1 mixes them. Verified here
rather than accepted -- the three-hat temporal Gram is exactly proportional to
[[2,1,0],[1,4,1],[0,1,4]] and the third column of R^-1 is exactly
[1/7, -2/7, 1] in the hat basis, so "group 2" contains all three hats.

The arithmetic in that table was right and its physical label was wrong. The
numbers are preserved and relabelled a Cholesky-coordinate-group diagnostic.

Then the thing the table was reaching for, done invariantly:

    L_I = tr(F E_I),   E_I = R^-T H_I R^-1,   F = B_cond^T B_cond

which is nonnegative, sums to tr F over a disjoint time partition, and is
unchanged by a consistent change of source coordinates. It uses the whole
target information matrix, not the leading two modes.
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
from scipy.linalg import solve_triangular  # noqa: E402
from scipy.special import roots_legendre  # noqa: E402

from phrt.geometry.raymap import read  # noqa: E402
from phrt.geometry.sampling import common_count, stratified_subsample  # noqa: E402
from phrt.operators.physical import PhysicalOperator  # noqa: E402
from phrt.revision_v4_1 import conditioning, source_metric  # noqa: E402
from phrt.revision_v4_1.calibration import COMMON_REFERENCE_COUNT, calibrate  # noqa: E402
from phrt.sources.localized_basis import (LocalizedBasis,  # noqa: E402
                                          azimuthal_design, radial_design,
                                          temporal_design)
from phrt.sources.physical_basis import PhysicalBasis  # noqa: E402

REV = ROOT / "artifacts" / "revisions" / "mahakal_v4_1"
DELIVERED = REV / "R2REPLAY_20260906T144528Z_b873908"
MANIFEST = REV / "R2_REPLAY_TARGET_MANIFEST.json"
R1FZ = ROOT / "artifacts" / "configs" / "R1_MAIN_FREEZE.json"
MAPS = ROOT / "artifacts" / "raymaps"
GEOMETRY, SNR, RTOL = "a050_i050", 100.0, 1e-12


def gram_on(L: LocalizedBasis, lo: float, hi: float, n: int = 12800,
            nt: int = 96) -> np.ndarray:
    """Full source Gram with the temporal factor restricted to [lo, hi]."""
    r = L.r_inner + (np.arange(n) + 0.5) * (L.r_outer - L.r_inner) / n
    Hr = source_metric.gram(radial_design(r, L.r_inner, L.r_outer, L.n_radial),
                            (L.r_outer - L.r_inner) / n * r)
    p = (np.arange(n) + 0.5) * 2 * np.pi / n
    Hp = source_metric.gram(azimuthal_design(p, L.n_azimuthal),
                            np.full(n, 2 * np.pi / n))
    # Gauss-Legendre on the interval: the hat products are piecewise quadratic
    x, w = roots_legendre(nt)
    knots = np.unique(np.clip(
        np.concatenate([[lo, hi], L.nodes(),
                        np.asarray(L.supports()).ravel()]), lo, hi))
    tt, ww = [], []
    for a, b in zip(knots[:-1], knots[1:]):
        if b <= a:
            continue
        tt.append(0.5 * (b - a) * x + 0.5 * (a + b))
        ww.append(0.5 * (b - a) * w)
    if not tt:
        return np.zeros((L.dimension, L.dimension))
    t, wt = np.concatenate(tt), np.concatenate(ww)
    Ht = source_metric.gram(temporal_design(t, L.t_min, L.t_max, L.n_temporal),
                            wt)
    return np.kron(np.kron(Hr, Hp), Ht)


def main(run_dir: Path) -> int:
    run_dir.mkdir(parents=True, exist_ok=True)
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
    man = json.loads(MANIFEST.read_text())
    idx = np.array(man["target_column_indices"])
    target = np.zeros(L.dimension, bool)
    target[idx] = True

    # -- the mixing, verified ---------------------------------------------
    nq = 200000
    tt = L.t_min + (np.arange(nq) + 0.5) * (L.t_max - L.t_min) / nq
    Ht3 = source_metric.gram(
        temporal_design(tt, L.t_min, L.t_max, L.n_temporal),
        np.full(nq, (L.t_max - L.t_min) / nq))[:3, :3]
    R3 = np.linalg.cholesky(Ht3).T
    third = np.linalg.inv(R3)[:, 2]
    third = third / third[2]

    # -- the information matrix, same operator, metric and nuisance --------
    H = gram_on(L, L.t_min, L.t_max)
    metric = source_metric.factor(H[np.ix_(target, target)],
                                  domain="r dr dphi dt", n_quadrature=12800)
    gb = PhysicalBasis(L.r_inner, L.r_outer, L.t_min, L.t_max, 4, 7, 8)
    ref = PhysicalOperator(orders=[base[0]], observer_times=t_obs,
                           design=gb.design, dimension=gb.dimension)
    u = np.zeros(gb.dimension)
    for a in range(gb.n_radial):
        u[(a * gb.n_azimuthal + 0) * gb.n_temporal + 0] = 1.0
    cal = calibrate(ref.matvec(u), SNR, mode=COMMON_REFERENCE_COUNT,
                    m_reference=int(obs["rays_per_order"]) * len(t_obs),
                    grid_identity=GEOMETRY)

    out = {"schema": "phrt-localization-overlay/1",
           "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "review": "PAPER_I_R2_ACCEPTANCE_AND_LOCALIZATION_025",
           "disposition_of_epoch_breakdown_addition":
               "CHOLESKY_COORDINATE_GROUP_DIAGNOSTIC",
           "not": "PHYSICAL_EPOCH_PARTITION",
           "numbers_preserved": True,
           "mechanism_verified_here": {
               "three_hat_temporal_gram_over_scale":
                   (Ht3 / (Ht3[0, 0] / 2)).round(9).tolist(),
               "reviewer_claim": [[2, 1, 0], [1, 4, 1], [0, 1, 4]],
               "third_column_of_R_inverse_in_hat_basis":
                   third.round(9).tolist(),
               "reviewer_claim_1_7_minus_2_7_1": [1 / 7, -2 / 7, 1.0],
               "conclusion": "R^-1 mixes the overlapping hats, so a column "
                             "group of B_o is not a time window"},
           "trace_localization": {}}

    knots = [-128.82234649196255, -109.09455318046723,
             -89.36675986897191, -69.63896655747659]
    windows = {"oldest_third": (knots[0], knots[1]),
               "middle_third": (knots[1], knots[2]),
               "youngest_third": (knots[2], knots[3]),
               "original_hat2_support": (knots[1], knots[3]),
               "youngest_fifth_of_union": (-81.47564254437378, knots[3])}
    Rinv_cols = solve_triangular(metric.R, np.eye(int(target.sum())),
                                 lower=False)
    for arm, ords in (("DIRECT_PHYSICAL", [base[0]]),
                      ("RESOLVED_PHYSICAL", base)):
        op = PhysicalOperator(orders=ords, observer_times=t_obs,
                              design=L.design, dimension=L.dimension)
        A = op.to_dense() / cal.sigma
        B_o = metric.to_physical(A[:, target])
        U_n, _ = conditioning.nuisance_basis(A[:, ~target], RTOL)
        B_c = conditioning.residualize(B_o, U_n)
        F = B_c.T @ B_c
        rec = {"total_conditional_trace": float(np.trace(F)), "windows": {}}
        part = 0.0
        for name, (lo, hi) in windows.items():
            HI = gram_on(L, lo, hi)[np.ix_(target, target)]
            E = Rinv_cols.T @ HI @ Rinv_cols
            LI = float(np.trace(F @ E))
            rec["windows"][name] = {
                "interval_M": [lo, hi], "trace_F_E": LI,
                "fraction_of_total": (LI / np.trace(F)
                                      if np.trace(F) > 0 else None),
                "E_min_eigenvalue": float(np.linalg.eigvalsh(E).min())}
            if name in ("oldest_third", "middle_third", "youngest_third"):
                part += LI
        rec["disjoint_partition_sum"] = part
        rec["partition_sum_relative_error"] = (
            abs(part / np.trace(F) - 1.0) if np.trace(F) > 0 else None)
        out["trace_localization"][arm] = rec
        print(f"{arm}: tr F = {np.trace(F):.6f}")
        for name in ("oldest_third", "middle_third", "youngest_third"):
            w = rec["windows"][name]
            print(f"   {name:22s} tr(F E) = {w['trace_F_E']:.6f}"
                  f"  {'' if w['fraction_of_total'] is None else format(w['fraction_of_total'], '.4%')}")
        print(f"   partition sum relative error: "
              f"{rec['partition_sum_relative_error']}")

    (run_dir / "saved_mode_physical_localization.json").write_text(
        json.dumps(out, indent=2) + "\n")
    print(f"wrote {(run_dir / 'saved_mode_physical_localization.json').relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main((ROOT / sys.argv[1]).resolve()))
