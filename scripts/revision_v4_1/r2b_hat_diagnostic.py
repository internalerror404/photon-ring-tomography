#!/usr/bin/env python3
"""Where the target information sits before and after profiling, by epoch.

An addition beyond the export contents review 024 listed, and named as one.
The mode export shows both surviving directions concentrated in one temporal
hat; this says whether the other hats are empty because the resolved arm never
saw them or because the nuisance absorbs them. Same operator, no estimator.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from phrt.numerics import pin

pin()

import numpy as np  # noqa: E402

from phrt.geometry.raymap import read  # noqa: E402
from phrt.geometry.sampling import common_count, stratified_subsample  # noqa: E402
from phrt.operators.physical import PhysicalOperator  # noqa: E402
from phrt.revision_v4_1 import conditioning, guards, source_metric  # noqa: E402
from phrt.revision_v4_1.calibration import COMMON_REFERENCE_COUNT, calibrate  # noqa: E402
from phrt.sources.localized_basis import (LocalizedBasis,  # noqa: E402
                                          azimuthal_design, radial_design,
                                          temporal_design)
from phrt.sources.physical_basis import PhysicalBasis  # noqa: E402

REV = ROOT / "artifacts" / "revisions" / "mahakal_v4_1"
MANIFEST = REV / "R2_REPLAY_TARGET_MANIFEST.json"
R1FZ = ROOT / "artifacts" / "configs" / "R1_MAIN_FREEZE.json"
MAPS = ROOT / "artifacts" / "raymaps"
GEOMETRY, SNR, RTOL = "a050_i050", 100.0, 1e-12


def main(run_dir: Path) -> int:
    guards.verify_inputs(REV / "R2_REPLAY_INPUT_FREEZE.json", ROOT)
    man = json.loads(MANIFEST.read_text())
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
    idx = np.array(man["target_column_indices"])
    target = np.zeros(L.dimension, bool)
    target[idx] = True
    nuisance = ~target

    n = 12800
    r = L.r_inner + (np.arange(n) + 0.5) * (L.r_outer - L.r_inner) / n
    Hr = source_metric.gram(radial_design(r, L.r_inner, L.r_outer, L.n_radial),
                            (L.r_outer - L.r_inner) / n * r)
    p = (np.arange(n) + 0.5) * 2 * np.pi / n
    Hp = source_metric.gram(azimuthal_design(p, L.n_azimuthal),
                            np.full(n, 2 * np.pi / n))
    t = L.t_min + (np.arange(n) + 0.5) * (L.t_max - L.t_min) / n
    Ht = source_metric.gram(temporal_design(t, L.t_min, L.t_max, L.n_temporal),
                            np.full(n, (L.t_max - L.t_min) / n))
    H = np.kron(np.kron(Hr, Hp), Ht)
    metric = source_metric.factor(H[np.ix_(target, target)],
                                  domain="r dr dphi dt", n_quadrature=n)

    gb = PhysicalBasis(L.r_inner, L.r_outer, L.t_min, L.t_max, 4, 7, 8)
    ref = PhysicalOperator(orders=[base[0]], observer_times=t_obs,
                           design=gb.design, dimension=gb.dimension)
    u = np.zeros(gb.dimension)
    for a in range(gb.n_radial):
        u[(a * gb.n_azimuthal + 0) * gb.n_temporal + 0] = 1.0
    cal = calibrate(ref.matvec(u), SNR, mode=COMMON_REFERENCE_COUNT,
                    m_reference=int(obs["rays_per_order"]) * len(t_obs),
                    grid_identity=GEOMETRY)

    labels = L.labels()
    hats = np.array([labels[i]["temporal_mode"] for i in idx])
    out = {"note": "an addition beyond the listed mode-export contents, "
                   "labelled as one", "by_arm": {}}
    for arm, ords in (("DIRECT_PHYSICAL", [base[0]]),
                      ("RESOLVED_PHYSICAL", base)):
        op = PhysicalOperator(orders=ords, observer_times=t_obs,
                              design=L.design, dimension=L.dimension)
        A = op.to_dense() / cal.sigma
        B_o = metric.to_physical(A[:, target])
        U_n, _ = conditioning.nuisance_basis(A[:, nuisance], RTOL)
        B_c = conditioning.residualize(B_o, U_n)
        per = {}
        for h in sorted(set(hats)):
            sel = hats == h
            lb = next(labels[i] for i in idx[sel])
            per[int(h)] = {
                "support_M": [lb["temporal_support_lo_M"],
                              lb["temporal_support_hi_M"]],
                "n_columns": int(sel.sum()),
                "known_fisher_trace": float(np.sum(B_o[:, sel] ** 2)),
                "conditional_fisher_trace": float(np.sum(B_c[:, sel] ** 2)),
            }
            k, c = per[int(h)]["known_fisher_trace"], \
                per[int(h)]["conditional_fisher_trace"]
            per[int(h)]["retained_fraction"] = (c / k) if k > 0 else None
        out["by_arm"][arm] = per
        print(f"{arm}")
        for h, v in per.items():
            print(f"  hat {h} [{v['support_M'][0]:.1f}, {v['support_M'][1]:.1f}] M"
                  f"  known {v['known_fisher_trace']:.6f}"
                  f"  conditional {v['conditional_fisher_trace']:.6f}"
                  f"  retained {v['retained_fraction']}")
    (run_dir / "epoch_breakdown_addition.json").write_text(
        json.dumps(out, indent=2) + "\n")
    print(f"wrote {(run_dir / 'epoch_breakdown_addition.json').relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main((ROOT / sys.argv[1]).resolve()))
