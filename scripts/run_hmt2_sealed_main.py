#!/usr/bin/env python3
"""HMT-2 sealed main, stage B. Item 12: execute and stop.

No operator is imported until stage A's gate file is read and found clean, and
the imports live inside a function so the ordering is a property of the file.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from phrt.numerics import pin, record as numerics_record, require_single_threaded

pin()

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from hmt2_sealed_common import (FZ, HASHES, STAGE_A, axes_for,  # noqa: E402
                                build_bank)
from phrt.attestation import attest  # noqa: E402
from phrt.config import load_registry, sha256_file  # noqa: E402
from phrt.io.endpoint_lineage import screen  # noqa: E402
from phrt.io.manifests import Gate, RunManifest, make_run_id, merge_gate_file  # noqa: E402
from phrt.io.tables import write_table  # noqa: E402
from phrt.metrics.feature_sets import assignment, cell_metric, peaks_to_features  # noqa: E402
from phrt.metrics.morphology import aggregate_all_states, state_error  # noqa: E402
from phrt.metrics.topography import classify  # noqa: E402
from phrt.metrics.windowed_reference import window_stack  # noqa: E402
from run_hmt1_score import paired_relative, spectral_filter  # noqa: E402

R1 = ROOT / "artifacts" / "configs" / "R1_MAIN_FREEZE.json"
S0 = ROOT / "artifacts" / "configs" / "HMT2_STAGE0_SOURCE_OBJECT_AND_RESOLUTION_AUDIT_V0.json"
OUT = ROOT / "artifacts" / "gates" / "hmt2_sealed_main_gates.json"
LEDGER = ROOT / "artifacts" / "gates" / "hmt2_correctness_gates.json"
PH, CC, CCP = "PHYSICAL_END_TO_END", "CLASS_CONDITIONAL", "CC_PROJLAB"
BOOT = {"n_resamples": 10000, "seed": 20260953, "level": 0.95}


def _operator_modules():
    from phrt.geometry.raymap import read
    from phrt.geometry.sampling import common_count, stratified_subsample
    from phrt.operators.physical import PhysicalOperator
    from phrt.sources.localized_basis import LocalizedBasis
    from phrt.sources.physical_basis import PhysicalBasis
    return dict(read=read, common_count=common_count,
                stratified_subsample=stratified_subsample,
                PhysicalOperator=PhysicalOperator,
                LocalizedBasis=LocalizedBasis, PhysicalBasis=PhysicalBasis)


def main() -> int:
    t0 = time.time()
    numerics = require_single_threaded()
    started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    if not STAGE_A.exists():
        print("stage A gate file missing", file=sys.stderr)
        return 1
    sa = json.loads(STAGE_A.read_text())
    if sa.get("failed_gates") or not sa.get("stage_b_may_proceed"):
        print(f"stage A source gates failed: {sa.get('failed_gates')}. No "
              f"operator will be imported.", file=sys.stderr)
        return 1
    print(f"stage A clean: {len(sa['gates'])} source gates passed")
    OPS = _operator_modules()

    fz = json.loads(FZ.read_text())
    r1 = json.loads(R1.read_text())
    s0 = json.loads(S0.read_text())
    reg = load_registry()
    inh = s0["inherited"]
    iv = fz["inherits_verbatim"]
    comp = tuple(iv["evaluation"]["comparison_grid"])
    r_in = float(r1["physical_model"]["r_inner_M"])
    r_out = float(r1["physical_model"]["r_outer_M"])
    t_lo = float(r1["observation"]["basis_t_min"])
    t_hi = float(r1["observation"]["basis_t_max"])
    t_obs = np.asarray(r1["observation"]["observer_times_M"], float)
    ages = np.arange(0.0, float(inh["age_grid_max_M"]) + 1e-9,
                     float(inh["age_grid_step_M"]))
    half = float(inh["probe_half_width_M"])
    frac = float(iv["prominence_fraction"])
    rc, pc, tc = axes_for(comp, r_in, r_out, t_lo, t_hi)
    met = cell_metric(rc, pc)
    Rc, Pc, Tc = np.meshgrid(rc, pc, tc, indexing="ij")
    Wc = window_stack(tc, ages, half)
    span = json.loads((ROOT / "artifacts" / "configs"
                       / "HMT1_VALIDATION_FREEZE_V0.json").read_text()
                      )["primary_endpoints"]["stable_feature_interval"]
    eps, quant = float(span["epsilon"]), float(span["quantile"])
    M = fz["pass_criteria"]["materiality"]
    prim = fz["pass_criteria"]["claim_bearing_class"]
    arms = list(iv["arms"])
    classes = {iv["classes"]["primary"]["id"]: iv["classes"]["primary"],
               iv["classes"]["control"]["id"]: iv["classes"]["control"]}
    sealed = fz["sealed_hyperparameters"]["values"]
    n_draws = int(fz["bank"]["noise_draws_per_truth"])
    seed = int(fz["bank"]["bank_seed"])
    snr_p, snr_s = 100.0, 1000.0

    cfg = {"fz": fz, "comp": comp, "rc": rc, "pc": pc, "tc": tc, "ages": ages,
           "half": half, "spin": float(inh["spin"]), "r_in": r_in,
           "r_out": r_out, "t_lo": t_lo, "t_hi": t_hi}
    bank = build_bank(cfg)
    mismatch = [k for k in sorted(bank)
                if bank[k]["hashes"] != sa["hashes"][f"{k[0]}|{k[1]}"]]
    print(f"bank rebuilt, {len(bank)} truths, {len(mismatch)} hash mismatches, "
          f"{time.time() - t0:.0f}s", flush=True)

    basis_ref = OPS["PhysicalBasis"](r_in, r_out, t_lo, t_hi, 4, 7, 8)
    rng0 = np.random.default_rng(int(r1["observation"]["subsample_seed"]))
    base = OPS["common_count"]([OPS["stratified_subsample"](
        OPS["read"](ROOT / "artifacts" / "raymaps" / f"a050_i050_n{n}_core.h5"),
        int(r1["observation"]["rays_per_order"]), rng0)
        for n in r1["physical_model"]["orders"]], rng0)
    n_orders, n_rays = len(base), base[0].n_rays
    ones = np.ones((1, n_orders))
    ocfg = {"DIRECT_PHYSICAL": dict(orders=[base[0]]),
            "RESOLVED_PHYSICAL": dict(orders=base),
            "UNRESOLVED_IMAGE": dict(orders=base, mixer=ones),
            "TOTAL_FLUX": dict(orders=base, mixer=ones, collapse="total_flux")}
    bases, ops, svd, keeps, worst = {}, {}, {}, {}, {"adjoint": 0.0, "identity": 0.0}
    for cname, cdef in classes.items():
        b = OPS["LocalizedBasis"](r_in, r_out, t_lo, t_hi, cdef["radial"],
                                  cdef["azimuthal"], cdef["temporal"])
        keep = np.array([lab["azimuthal_mode"] != 0 for lab in b.labels()])
        bases[cname], keeps[cname] = b, keep
        for aname, c in ocfg.items():
            if aname not in arms:
                continue
            op = OPS["PhysicalOperator"](
                design=lambda r, p, t, _b=b, _k=keep: _b.design(r, p, t)[:, _k],
                dimension=int(keep.sum()), observer_times=t_obs, **c)
            ops[(cname, aname)] = op
            svd[(cname, aname)] = np.linalg.svd(op.to_dense(), full_matrices=False)
            x = np.random.default_rng(5).normal(size=op.shape[1])
            y = np.random.default_rng(6).normal(size=op.shape[0])
            f1 = float(y @ op.matvec(x))
            worst["adjoint"] = max(worst["adjoint"],
                                   abs(f1 - float(x @ op.rmatvec(y)))
                                   / max(abs(f1), 1e-300))
            got = op.forward_analytic(
                lambda r, p, t, _x=x, _b=b, _k=keep: _b.design(r, p, t)[:, _k] @ _x)
            want = op.matvec(x)
            worst["identity"] = max(worst["identity"],
                                    float(np.abs(got - want).max())
                                    / max(float(np.abs(want).max()), 1e-300))
    s_ref = float(np.sqrt(np.mean(OPS["PhysicalOperator"](
        orders=[base[0]], observer_times=t_obs, design=basis_ref.design,
        dimension=basis_ref.dimension).matvec(
            np.array([1.0 if (j % (basis_ref.n_azimuthal * basis_ref.n_temporal)) == 0
                      else 0.0 for j in range(basis_ref.dimension)])) ** 2)))
    Dc = {c: bases[c].design(Rc.ravel(), Pc.ravel(), Tc.ravel())[:, keeps[c]]
          for c in classes}
    print(f"operators ready, {time.time() - t0:.0f}s", flush=True)

    keys = sorted(bank)
    nrng = np.random.default_rng(seed + 2)
    Z = {k: [nrng.normal(size=(n_orders, n_rays, t_obs.size))
             for _ in range(n_draws)] for k in keys}
    cache = {}
    for (cname, aname), op in ops.items():
        U, s, Vt = svd[(cname, aname)]
        cache[(cname, aname)] = (
            {k: U.T @ op.forward_analytic(bank[k]["fluct"]) for k in keys},
            {k: np.column_stack([U.T @ op.noise_from_standard(z) for z in Z[k]])
             for k in keys})
    print(f"  projections done, {time.time() - t0:.0f}s", flush=True)

    unsealed = 0
    score_rows, state_rows, span_rows = [], [], []
    for cname in classes:
        for aname in arms:
            for est in ("TSVD", "RIDGE_IDENTITY"):
                sk = f"{cname}|{aname}|{est}"
                hy = float(sealed[sk]["hyperparameter"])
                U, s, Vt = svd[(cname, aname)]
                sig, noi = cache[(cname, aname)]
                for snr in (snr_p, snr_s):
                    scale = snr / s_ref
                    filt = spectral_filter(est, s, scale, hy)
                    for k in keys:
                        rec = bank[k]
                        acc = {t: [] for t in (PH, CC, CCP)}
                        nd = {t: [] for t in (PH, CC)}
                        sat = {t: [] for t in (PH, CC)}
                        stab, reach = [], []
                        for d in range(n_draws):
                            if hy != float(sealed[sk]["hyperparameter"]):
                                unsealed += 1
                            xh = Vt.T @ (filt * (scale * sig[k] + noi[k][:, d]))
                            fld = (Dc[cname] @ xh).reshape(comp)
                            mp = (fld.reshape(comp[0] * comp[1], comp[2]) @ Wc
                                  ).reshape(comp[0], comp[1], ages.size)
                            tm = float(np.abs(mp).max())
                            rf = []
                            for k2 in range(ages.size):
                                c = classify(mp[:, :, k2], 1,
                                             float(mp[:, :, k2].max()), tm, frac)
                                rf.append(peaks_to_features(
                                    c["peaks"], c["prominences"],
                                    mp[:, :, k2], rc, pc))
                            for tn, labs, refm, reff in (
                                    (PH, rec["labels"], rec["maps_phys"],
                                     rec["feats_phys"]),
                                    (CC, rec["labels"],
                                     rec["inclass"][cname]["maps"],
                                     rec["inclass"][cname]["feats"]),
                                    (CCP, rec["inclass"][cname]["labels"],
                                     rec["inclass"][cname]["maps"],
                                     rec["inclass"][cname]["feats"])):
                                rows = [state_error(labs[k2], refm[:, :, k2],
                                                    mp[:, :, k2], reff[k2],
                                                    rf[k2], rc, pc, met)
                                        for k2 in range(ages.size)]
                                acc[tn].append(
                                    aggregate_all_states(rows)["all_state_error"])
                                if tn in nd:
                                    live = [r for r in rows if r["state"] != "DEAD"]
                                    nd[tn].append(
                                        aggregate_all_states(live)["all_state_error"])
                                    sat[tn].append(float(np.mean(
                                        [r["error"] >= 1.0 - 1e-12 for r in rows])))
                                    for k2, rr in enumerate(rows):
                                        state_rows.append({
                                            "class": cname, "arm": aname,
                                            "estimator": est, "snr0": snr,
                                            "family": k[0], "index": k[1],
                                            "target": tn, "draw": d,
                                            "age_M": float(ages[k2]),
                                            "state": rr["state"],
                                            "measure": rr["measure"],
                                            "error": rr["error"]})
                                if tn == PH:
                                    e = np.array([r["error"] for r in rows])
                                    reach.append(float(
                                        ages[np.maximum.accumulate(e) <= eps].max()
                                        if e[0] <= eps else 0.0))
                            for k2 in range(ages.size):
                                if rec["labels"][k2] != "MULTI_RESOLVED":
                                    continue
                                a = assignment(rec["feats_phys"][k2], rf[k2], met)
                                stab.append(a["unbalanced_cost"]
                                            / met["unmatched_cost"])
                        row = {"class": cname, "arm": aname, "estimator": est,
                               "snr0": snr, "family": k[0], "index": k[1],
                               "hyperparameter": hy}
                        for t in acc:
                            row[f"{t}_all_state_error"] = float(np.mean(acc[t]))
                        for t in nd:
                            row[f"{t}_non_dead_error"] = float(np.mean(nd[t]))
                            row[f"{t}_saturation_fraction"] = float(np.mean(sat[t]))
                        row["stable_multi_cost_normalized"] = (
                            float(np.mean(stab)) if stab else float("nan"))
                        score_rows.append(row)
                        for rr in reach:
                            span_rows.append({"class": cname, "arm": aname,
                                              "estimator": est, "snr0": snr,
                                              "family": k[0], "index": k[1],
                                              "pass_to_age_M": rr})
        print(f"  {cname}: scored, {time.time() - t0:.0f}s", flush=True)

    from run_hmt2_sealed_main_score import finish
    return finish(dict(
        fz=fz, reg=reg, t0=t0, started=started, numerics=numerics, sa=sa,
        classes=list(classes), arms=arms, snr_p=snr_p, snr_s=snr_s, M=M,
        prim=prim, score_rows=score_rows, state_rows=state_rows,
        span_rows=span_rows, mismatch=mismatch, unsealed=unsealed,
        worst=worst, eps=eps, quant=quant, boot=BOOT))


if __name__ == "__main__":
    raise SystemExit(main())
