#!/usr/bin/env python3
"""E3D -- nested source-class stress on the three anchor geometries.

Conditionally authorized after E3C's correctness gates pass. Asks what the
registered class C224 was hiding: full column rank on a 224-dimensional model is
a statement about that model, never about the continuum, and the way to find out
how much of it was the model's poverty is to enrich the model and look again.

    class      radial  azimuthal  temporal  dimension
    C224            4          7         8        224
    C448_T          4          7        16        448
    C528_S          6         11         8        528
    C1056_ST        6         11        16       1056

The ladder must be nested, and 'nested' is asserted exactly rather than assumed:
the azimuthal and temporal factors are literal prefixes, so their columns are
preserved, while the radial cubic B-spline factor is refined -- its columns move
but its span is contained in the enriched span. Rank and monotonicity statements
depend on the span, which is what gate ``E3D_class_nesting`` checks.

Exact adjoint, Gram monotonicity and a dense smoke comparison remain mandatory
at every class, including C1056_ST.
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
from phrt.operators.physical import (PhysicalOperator, destroy_pairing, equalize,
                                     substitute_delay, substitute_spatial)
from phrt.sources.physical_basis import (PhysicalBasis, age_probe_norms,
                                         age_probe_spatial, radial_design)

FREEZE = ROOT / "artifacts" / "configs" / "E3C_OPERATOR_GRID_FREEZE.json"
E3C_GATES = ROOT / "artifacts" / "gates" / "e3c_correctness_gates.json"
REFERENCE_SNR = 100.0

CLASSES = {
    "C224":     dict(n_radial=4, n_azimuthal=7,  n_temporal=8),
    "C448_T":   dict(n_radial=4, n_azimuthal=7,  n_temporal=16),
    "C528_S":   dict(n_radial=6, n_azimuthal=11, n_temporal=8),
    "C1056_ST": dict(n_radial=6, n_azimuthal=11, n_temporal=16),
}
# which class each one must contain, as a function space
PARENT = {"C448_T": "C224", "C528_S": "C224", "C1056_ST": "C448_T"}

ARMS = ("DIRECT_PHYSICAL", "RESOLVED_PHYSICAL", "DELAY_ONLY", "SPATIAL_ONLY",
        "UNRESOLVED_IMAGE", "EQUALIZED_ORDER_SENSITIVITY", "PAIRING_DESTROYED")


def require_e3c_pass() -> dict:
    if not E3C_GATES.exists():
        raise SystemExit("E3D is conditional on E3C correctness; "
                         "artifacts/gates/e3c_correctness_gates.json is missing")
    doc = json.loads(E3C_GATES.read_text())
    failed = [k for k, v in doc["gates"].items() if v["status"] == "FAIL"]
    if failed:
        raise SystemExit(f"E3D is conditional on E3C correctness; failing: {failed}")
    return doc


def build_arms(base, seed: int) -> dict:
    ones = np.ones((1, len(base)))
    return {
        "DIRECT_PHYSICAL": dict(orders=[base[0]]),
        "RESOLVED_PHYSICAL": dict(orders=base),
        "DELAY_ONLY": dict(orders=substitute_spatial(base, base[0])),
        "SPATIAL_ONLY": dict(orders=substitute_delay(base, base[0])),
        "UNRESOLVED_IMAGE": dict(orders=base, mixer=ones),
        "EQUALIZED_ORDER_SENSITIVITY": dict(orders=equalize(base)),
        "PAIRING_DESTROYED": dict(orders=destroy_pairing(base, seed)),
    }


def unit_source(basis: PhysicalBasis) -> np.ndarray:
    u = np.zeros(basis.dimension)
    for a in range(basis.n_radial):
        u[(a * basis.n_azimuthal + 0) * basis.n_temporal + 0] = 1.0
    return u


def nesting_residual(small: PhysicalBasis, large: PhysicalBasis,
                     r: np.ndarray, phi: np.ndarray, t: np.ndarray) -> float:
    """Max residual of projecting the smaller design onto the larger's span."""
    A, B = small.design(r, phi, t), large.design(r, phi, t)
    Q, _ = np.linalg.qr(B)
    scale = max(float(np.abs(A).max()), 1e-300)
    return float(np.abs(A - Q @ (Q.T @ A)).max()) / scale


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--geometry", default=None)
    args = ap.parse_args()

    t0 = time.time()
    require_e3c_pass()
    fz = json.loads(FREEZE.read_text())
    reg = load_registry()
    maps = ROOT / "artifacts" / "raymaps"
    anchors = [args.geometry] if args.geometry else list(fz["anchor_geometries"])
    h = float(fz["localized_probe"]["half_width_h_M"])
    t_obs = np.asarray(fz["observation"]["observer_times_M"], dtype=float)
    ages = np.arange(0.0, fz["common_age_grid"]["A_max_M"] + 1e-9,
                     fz["common_age_grid"]["step_M"])
    a_max = float(fz["common_age_grid"]["A_max_M"])
    rho = float(fz["rank_conventions"]["operational_threshold_rho"])
    snr_grid = [float(s) for s in fz["snr_grid"]]
    seed0 = int(fz["permutation_seeds"][0])

    run_id = make_run_id("E3D", reg.sha256)
    man = RunManifest(run_id=run_id, experiment_id="E3D",
                      seeds={"subsample_seed": fz["observation"]["subsample_seed"],
                             "permutation_seed": seed0},
                      extra={"anchor_geometries": anchors,
                             "classes": {k: v | {"dimension":
                                                 v["n_radial"] * v["n_azimuthal"]
                                                 * v["n_temporal"]}
                                         for k, v in CLASSES.items()},
                             "reference_snr": REFERENCE_SNR})
    man.add_input(reg.path)
    man.add_input(FREEZE)

    spec_rows, depth_rows, nest_rows, smoke_rows, age_rows = [], [], [], [], []
    worst = {"adjoint": 0.0, "smoke": 0.0, "monotonicity": 0.0, "nesting": 0.0,
             "parent_rank": 0.0}

    for g in anchors:
        rng = np.random.default_rng(int(fz["observation"]["subsample_seed"]))
        raw = [read(maps / f"{g}_n{n}_{fz['profile']}.h5") for n in fz["orders"]]
        base = common_count(
            [stratified_subsample(rm, int(fz["observation"]["rays_per_order"]), rng)
             for rm in raw], rng)
        r_in = min(float(o.source_r.min()) for o in base)
        r_out = max(float(o.source_r.max()) for o in base)
        t_lo = float(t_obs.min() - max(o.delay.max() for o in base)) - 3.0 * h
        t_hi = float(t_obs.max()) + 3.0 * h
        bases = {k: PhysicalBasis(r_in, r_out, t_lo, t_hi, **v)
                 for k, v in CLASSES.items()}

        # nesting, on the actual sampled source coordinates
        sr = np.concatenate([o.source_r for o in base])
        sp = np.concatenate([o.source_phi for o in base])
        st = np.concatenate([float(t_obs[0]) - o.delay for o in base])
        for child, parent in PARENT.items():
            res = nesting_residual(bases[parent], bases[child], sr, sp, st)
            worst["nesting"] = max(worst["nesting"], res)
            nest_rows.append({"geometry": g, "parent": parent, "child": child,
                              "parent_dimension": bases[parent].dimension,
                              "child_dimension": bases[child].dimension,
                              "projection_residual": res,
                              "columns_preserved":
                                  CLASSES[parent]["n_radial"] == CLASSES[child]["n_radial"]})

        # the reference noise density is fixed once per geometry, on C224,
        # exactly as in E3C -- enriching the model must not quietly requantify
        # the detector.
        b224 = bases["C224"]
        ref_direct = PhysicalOperator(orders=[base[0]], observer_times=t_obs,
                                      design=b224.design, dimension=b224.dimension)
        s_ref = max(float(np.sqrt(np.mean(ref_direct.matvec(unit_source(b224)) ** 2))),
                    1e-300)

        for cname, basis in bases.items():
            probe_norms = age_probe_norms(r_in, r_out, h, basis.n_radial,
                                          basis.n_azimuthal)
            arms = build_arms(base, seed0)
            ops = {n: PhysicalOperator(design=basis.design, dimension=basis.dimension,
                                       observer_times=t_obs, **cfg)
                   for n, cfg in arms.items()}
            ref = ops["RESOLVED_PHYSICAL"]

            # mandatory at every class, C1056_ST included
            wadj = 0.0
            for _ in range(20):
                x = rng.normal(size=ref.shape[1]); y = rng.normal(size=ref.shape[0])
                a_, b_ = float(y @ ref.matvec(x)), float(x @ ref.rmatvec(y))
                wadj = max(wadj, abs(a_ - b_) / max(abs(a_), abs(b_), 1e-300))
            worst["adjoint"] = max(worst["adjoint"], wadj)

            # dense smoke comparison on a random column subset, so the check is
            # real at 1056 dimensions rather than skipped for cost
            cols = rng.choice(basis.dimension, size=min(48, basis.dimension),
                              replace=False)
            E = np.zeros((basis.dimension, cols.size))
            E[cols, np.arange(cols.size)] = 1.0
            dense = ref.to_dense()[:, cols]
            free = np.column_stack([ref.matvec(E[:, k]) for k in range(cols.size)])
            smoke = float(np.abs(dense - free).max()) / max(float(np.abs(dense).max()), 1e-300)
            worst["smoke"] = max(worst["smoke"], smoke)
            smoke_rows.append({"geometry": g, "source_class": cname,
                               "n_columns_checked": int(cols.size),
                               "relative_difference": smoke, "adjoint_relative": wadj})

            cum = [PhysicalOperator(orders=base[:k], observer_times=t_obs,
                                    design=basis.design,
                                    dimension=basis.dimension).gram()
                   for k in range(1, len(base) + 1)]
            for i in range(1, len(cum)):
                dd = 0.5 * (cum[i] - cum[i - 1] + (cum[i] - cum[i - 1]).T)
                lam = float(np.min(np.linalg.eigvalsh(dd)))
                worst["monotonicity"] = max(
                    worst["monotonicity"],
                    max(0.0, -lam) / max(1.0, float(np.linalg.norm(cum[i], 2))))

            for aname, op in ops.items():
                B = op.to_dense() * (REFERENCE_SNR / s_ref)
                s = spectrum_of(B, basis.dimension, operational_threshold=rho).summary()
                spec_rows.append({
                    "geometry": g, "source_class": cname,
                    "source_dimension": basis.dimension,
                    "n_radial": basis.n_radial, "n_azimuthal": basis.n_azimuthal,
                    "n_temporal": basis.n_temporal, "arm": aname,
                    "data_dimension": int(op.shape[0]),
                    "full_column_rank": bool(s["numerical_rank"] == basis.dimension),
                    **{k: s[k] for k in ("numerical_rank", "operational_rank",
                                         "nullity", "sigma_max", "sigma_min_positive",
                                         "kappa_positive", "stable_rank",
                                         "effective_rank", "trace_information")}})

                rp = [age_probe_spatial(o.source_r, o.source_phi, r_in, r_out,
                                        basis.n_radial, basis.n_azimuthal)
                      for o in op.orders]
                lam_max, lam_min, logvol = [], [], []
                for a in ages:
                    blocks = []
                    for i, o in enumerate(op.orders):
                        c = o.coefficient()
                        for t in op.observer_times:
                            w = c * np.exp(-0.5 * ((float(t) - o.delay + a) / h) ** 2)
                            Bm = rp[i] * w[:, None]
                            blocks.append(Bm.sum(axis=0, keepdims=True)
                                          if op.collapse == "total_flux" else Bm)
                    po = np.split(np.vstack(blocks), len(op.orders))
                    P = np.vstack([sum(op.L[ch, k] * po[k] for k in range(len(op.orders)))
                                   for ch in range(op.n_channels)])
                    P = P / np.sqrt(op.channel_variance())[:, None] \
                        / (probe_norms * s_ref)[None, :]
                    M = P.T @ P
                    lv = np.linalg.eigvalsh(0.5 * (M + M.T))
                    lam_max.append(float(lv[-1]))
                    lam_min.append(float(max(lv[0], 0.0)))
                    logvol.append(float(np.sum(np.log1p(REFERENCE_SNR ** 2
                                                        * np.clip(lv, 0.0, None)))))
                lam_max = np.asarray(lam_max)
                for a, lx, ln, lv in zip(ages, lam_max, lam_min, logvol):
                    age_rows.append({"geometry": g, "source_class": cname, "arm": aname,
                                     "retarded_age": float(a),
                                     "lambda_max_per_snr2": float(lx),
                                     "lambda_min_per_snr2": float(ln),
                                     "log_information_volume_at_reference_snr": float(lv)})
                for snr in snr_grid:
                    ok = (snr ** 2) * lam_max >= rho ** 2
                    deepest = float(ages[ok].max()) if ok.any() else -1.0
                    cens = bool(ok.any() and np.isclose(deepest, a_max))
                    depth_rows.append({
                        "geometry": g, "source_class": cname, "arm": aname,
                        "snr0": snr, "T_rec_best_mode": deepest,
                        "right_censored": cens, "age_grid_max": a_max,
                        "depth_report": ("none" if deepest < 0 else
                                         (f">={deepest:.1f}" if cens else f"{deepest:.1f}"))})

        # the enriched class must not lose rank the parent had
        for child, parent in PARENT.items():
            for aname in ARMS:
                pk = [r for r in spec_rows if r["geometry"] == g
                      and r["source_class"] == parent and r["arm"] == aname][0]
                ck = [r for r in spec_rows if r["geometry"] == g
                      and r["source_class"] == child and r["arm"] == aname][0]
                deficit = max(0, pk["numerical_rank"] - ck["numerical_rank"])
                worst["parent_rank"] = max(worst["parent_rank"], deficit)
        print(f"{g} done, {time.time() - t0:.0f}s elapsed")

    man.add_gate(gate_from_tolerance("E3D_adjoint", worst["adjoint"], 1e-8,
                                     note="exact adjoint at every class including C1056_ST"))
    man.add_gate(gate_from_tolerance("E3D_dense_smoke_comparison", worst["smoke"], 1e-10,
                                     note="matrix-free columns against the dense operator"))
    man.add_gate(gate_from_tolerance("E3D_Gram_monotonicity", worst["monotonicity"], 1e-10))
    man.add_gate(gate_from_tolerance(
        "E3D_class_nesting", worst["nesting"], 1e-10,
        note="the parent class design projected onto the child's span; the radial "
             "columns are refined rather than preserved, so nesting is asserted "
             "on the function space"))
    man.add_gate(Gate("E3D_enrichment_does_not_lose_rank",
                      "PASS" if worst["parent_rank"] == 0 else "FAIL",
                      measured=worst["parent_rank"], threshold=0,
                      note="numerical rank of the enriched class is at least the "
                           "parent's, for every arm and anchor"))

    for name, rows in (("e3d_class_spectra", spec_rows),
                       ("e3d_depth_by_class", depth_rows),
                       ("e3d_class_nesting", nest_rows),
                       ("e3d_operator_smoke", smoke_rows),
                       ("e3d_age_information", age_rows)):
        man.add_output(write_table(rows, name))

    mp = man.write(reg.path, reg.sha256, runtime_seconds=time.time() - t0)
    merge_gate_file(man.gates, run_id)
    sub = {g.name: g.to_dict() for g in man.gates}
    (ROOT / "artifacts" / "gates" / "e3d_correctness_gates.json").write_text(
        json.dumps({"experiment": "E3D", "run_id": run_id, "gates": sub,
                    "summary": {s: sum(1 for v in sub.values() if v["status"] == s)
                                for s in ("PASS", "FAIL", "NOT_RUN")}}, indent=2) + "\n")
    print("\ngates")
    for gt in man.gates:
        m = gt.measured
        ms = f"{m:.3e}" if isinstance(m, float) else str(m)
        print(f"  {gt.name:38s} {gt.status:8s} {ms}")
    print(f"\nmanifest {mp}\ntotal {time.time() - t0:.0f}s")
    return 1 if man.failed_gates else 0


if __name__ == "__main__":
    raise SystemExit(main())
