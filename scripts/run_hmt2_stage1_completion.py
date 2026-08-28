#!/usr/bin/env python3
"""HMT-2 stage 1 endpoint completion.

REVIEWER_RULING_HMT2_STAGE1_020 items 7 to 10. The same bank, operators,
hyperparameters, SNRs and noise draws. No new truth and no selection: the
hyperparameters are read out of the stage 1 selection table.

Every existing primary endpoint cell must reproduce bitwise. If one moves this
is not a completion, it is a different run, and the difference has to be
explained before anything is added to it.
"""
from __future__ import annotations

import argparse
import hashlib
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

from phrt.attestation import attest  # noqa: E402
from phrt.config import load_registry, sha256_file  # noqa: E402
from phrt.geometry.raymap import read  # noqa: E402
from phrt.geometry.sampling import common_count, stratified_subsample  # noqa: E402
from phrt.io.manifests import Gate, RunManifest, make_run_id, merge_gate_file  # noqa: E402
from phrt.io.tables import write_table  # noqa: E402
from phrt.metrics.feature_sets import assignment, cell_metric, peaks_to_features  # noqa: E402
from phrt.metrics.morphology import aggregate_all_states, state_error  # noqa: E402
from phrt.metrics.topography import classify, reconcile  # noqa: E402
from phrt.metrics.windowed_reference import window_stack  # noqa: E402
from phrt.operators.physical import PhysicalOperator  # noqa: E402
from phrt.sources.contrast import build  # noqa: E402
from phrt.sources.localized_basis import LocalizedBasis  # noqa: E402
from phrt.sources.physical_basis import PhysicalBasis  # noqa: E402
from phrt.sources.separable_projection import factors, project  # noqa: E402
from run_hmt1_score import paired_relative, spectral_filter  # noqa: E402

# Inlined rather than imported from run_hmt2_stage1: that module calls pin() at
# import time, and importing it here would pin after numpy is already loaded.
# Same lesson as the source-only guard -- a helper that lives inside a pinning
# script cannot be reused by another pinning script.


def axes_for(level, r_in, r_out, t_lo, t_hi):
    nr, npz, nt = level
    return (np.exp(np.linspace(np.log(r_in), np.log(r_out), nr)),
            np.linspace(0.0, 2 * np.pi, npz, endpoint=False),
            np.linspace(t_lo, t_hi, nt))


def truth_seed(family, split, i, n, seed):
    p = json.dumps({"family": family, "split": f"hmt2_stage1_{split}", "n": n,
                    "seed": seed, "model": "contrast"}, sort_keys=True).encode()
    return int(hashlib.sha256(p + f"|{i}".encode()).hexdigest()[:16], 16) % (2 ** 63)


def unit_source(b):
    u = np.zeros(b.dimension)
    for a in range(b.n_radial):
        u[(a * b.n_azimuthal + 0) * b.n_temporal + 0] = 1.0
    return u

FZ = ROOT / "artifacts" / "configs" / "HMT2_STAGE1_RESOLUTION_AWARE_MORPHOLOGY_VALIDATION_V0.json"
AMD = ROOT / "artifacts" / "configs" / "HMT2_STAGE1_ENDPOINT_COMPLETION_AMENDMENT_020.json"
S0 = ROOT / "artifacts" / "configs" / "HMT2_STAGE0_SOURCE_OBJECT_AND_RESOLUTION_AUDIT_V0.json"
R1 = ROOT / "artifacts" / "configs" / "R1_MAIN_FREEZE.json"
TAB = ROOT / "artifacts" / "tables"
OUT = ROOT / "artifacts" / "gates" / "hmt2_stage1_completion_gates.json"
LEDGER = ROOT / "artifacts" / "gates" / "hmt2_correctness_gates.json"
T_PHYS, T_CC = "PHYSICAL_END_TO_END", "CLASS_CONDITIONAL"
BLENDED_STATES = ("BLENDED", "AMBIGUOUS")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()
    t0 = time.time()
    numerics = require_single_threaded()
    started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    fz = json.loads(FZ.read_text())
    s0 = json.loads(S0.read_text())
    r1 = json.loads(R1.read_text())
    reg = load_registry()
    scratch = bool(args.limit)

    sel_tab = pd.read_parquet(TAB / "hmt2_stage1_selection.parquet")
    hyper = {(r["class"], r.arm, r.estimator): float(r.selected_hyperparameter)
             for _, r in sel_tab.iterrows()}
    prev_end = pd.read_parquet(TAB / "hmt2_stage1_endpoint.parquet")

    r_in = float(r1["physical_model"]["r_inner_M"])
    r_out = float(r1["physical_model"]["r_outer_M"])
    t_lo = float(r1["observation"]["basis_t_min"])
    t_hi = float(r1["observation"]["basis_t_max"])
    t_obs = np.asarray(r1["observation"]["observer_times_M"], float)
    inh = s0["inherited"]
    spin, half = float(inh["spin"]), float(inh["probe_half_width_M"])
    ages = np.arange(0.0, float(inh["age_grid_max_M"]) + 1e-9,
                     float(inh["age_grid_step_M"]))
    frac = float(fz["classification"]["prominence_fraction"])
    mult = fz["source_model"]["expected_windowed_multiplicity"]
    lab_levels = [tuple(x) for x in fz["classification"]["levels"]]
    comp = tuple(fz["evaluation"]["comparison_grid"])
    fams = list(fz["source_model"]["families"])
    bc = fz["bank"]
    n_per = int(bc["truths_per_family_per_split"])
    n_draws = int(bc["noise_draws_per_truth"])
    seed = int(bc["bank_seed"])
    snr_p, snr_s = float(fz["snr"]["primary"]), float(fz["snr"]["secondary"])
    arms = list(fz["arms"])
    classes = {fz["classes"]["primary"]["id"]: fz["classes"]["primary"],
               fz["classes"]["control"]["id"]: fz["classes"]["control"]}
    # the stable-interval reading, reused from the campaign's declared block
    span = json.loads((ROOT / "artifacts" / "configs"
                       / "HMT1_VALIDATION_FREEZE_V0.json").read_text()
                      )["primary_endpoints"]["stable_feature_interval"]
    eps, quant = float(span["epsilon"]), float(span["quantile"])

    if args.limit:
        fams = fams[:2]
        n_per = min(n_per, args.limit)

    rc, pc, tc = axes_for(comp, r_in, r_out, t_lo, t_hi)
    met = cell_metric(rc, pc)
    Rc, Pc, Tc = np.meshgrid(rc, pc, tc, indexing="ij")
    Wc = window_stack(tc, ages, half)

    basis_ref = PhysicalBasis(r_in, r_out, t_lo, t_hi, 4, 7, 8)
    rng0 = np.random.default_rng(int(r1["observation"]["subsample_seed"]))
    base = common_count([stratified_subsample(
        read(ROOT / "artifacts" / "raymaps" / f"a050_i050_n{n}_core.h5"),
        int(r1["observation"]["rays_per_order"]), rng0)
        for n in r1["physical_model"]["orders"]], rng0)
    n_orders, n_rays = len(base), base[0].n_rays
    ones = np.ones((1, n_orders))
    cfg = {"DIRECT_PHYSICAL": dict(orders=[base[0]]),
           "RESOLVED_PHYSICAL": dict(orders=base),
           "UNRESOLVED_IMAGE": dict(orders=base, mixer=ones),
           "TOTAL_FLUX": dict(orders=base, mixer=ones, collapse="total_flux")}
    bases, ops, svd, keeps = {}, {}, {}, {}
    for cname, cdef in classes.items():
        b = LocalizedBasis(r_in, r_out, t_lo, t_hi, cdef["radial"],
                           cdef["azimuthal"], cdef["temporal"])
        keep = np.array([lab["azimuthal_mode"] != 0 for lab in b.labels()])
        bases[cname], keeps[cname] = b, keep
        for aname, c in cfg.items():
            if aname not in arms:
                continue
            op = PhysicalOperator(
                design=lambda r, p, t, _b=b, _k=keep: _b.design(r, p, t)[:, _k],
                dimension=int(keep.sum()), observer_times=t_obs, **c)
            ops[(cname, aname)] = op
            svd[(cname, aname)] = np.linalg.svd(op.to_dense(), full_matrices=False)
    s_ref = float(np.sqrt(np.mean(PhysicalOperator(
        orders=[base[0]], observer_times=t_obs, design=basis_ref.design,
        dimension=basis_ref.dimension).matvec(unit_source(basis_ref)) ** 2)))
    Dc = {c: bases[c].design(Rc.ravel(), Pc.ravel(), Tc.ravel())[:, keeps[c]]
          for c in classes}
    facs = {c: factors(rc, pc, tc, classes[c]["radial"], classes[c]["azimuthal"],
                       classes[c]["temporal"]) for c in classes}
    print(f"operators ready, {time.time() - t0:.0f}s", flush=True)

    # ---- noise: the same stream over the same full key list ----------------
    keys = [(f, sp, i) for f in fams for sp in bc["splits"]
            for i in range(n_per)]
    nrng = np.random.default_rng(seed + 2)
    Z = {}
    for k in keys:
        draws = [nrng.normal(size=(n_orders, n_rays, t_obs.size))
                 for _ in range(n_draws)]
        if k[1] == "pilot":
            Z[k] = draws          # selection draws are advanced and discarded

    pil = [k for k in keys if k[1] == "pilot"]
    truths = {}
    for (family, split, i) in pil:
        ts = truth_seed(family, split, i, n_per, seed)
        _, fluct, _, dj, _, _ = build(
            np.random.default_rng(ts), family, spin, r_in, r_out, Rc.ravel(),
            Pc.ravel(), Tc.ravel(),
            np.tile(np.arange(comp[2]), comp[0] * comp[1]), comp[2])
        lab = {}
        for lv in lab_levels:
            r, p, t = axes_for(lv, r_in, r_out, t_lo, t_hi)
            R, P, T = np.meshgrid(r, p, t, indexing="ij")
            v = np.asarray(fluct(R.ravel(), P.ravel(), T.ravel()),
                           float).reshape(r.size * p.size, t.size)
            m = (v @ window_stack(t, ages, half)).reshape(r.size, p.size, ages.size)
            tmax = float(np.abs(m).max())
            lab[lv] = [classify(m[:, :, k2], int(mult[family]),
                                float(m[:, :, k2].max()), tmax, frac)["state"]
                       for k2 in range(ages.size)]
        labels = [reconcile(lab[lab_levels[-1]][k2], lab[lab_levels[-2]][k2])
                  for k2 in range(ages.size)]
        raw = dj.reshape(comp[0], comp[1], comp[2])
        mph = (raw.reshape(comp[0] * comp[1], comp[2]) @ Wc).reshape(
            comp[0], comp[1], ages.size)
        tmp = float(np.abs(mph).max())
        fp = [peaks_to_features(*[classify(mph[:, :, k2], int(mult[family]),
                                           float(mph[:, :, k2].max()), tmp,
                                           frac)[x]
                                  for x in ("peaks", "prominences")],
                                mph[:, :, k2], rc, pc) for k2 in range(ages.size)]
        inclass = {}
        for cname in classes:
            pr = project(raw, facs[cname])
            mp = (pr.reshape(comp[0] * comp[1], comp[2]) @ Wc).reshape(
                comp[0], comp[1], ages.size)
            tm = float(np.abs(mp).max())
            ff, plab = [], []
            for k2 in range(ages.size):
                c = classify(mp[:, :, k2], int(mult[family]),
                             float(mp[:, :, k2].max()), tm, frac)
                ff.append(peaks_to_features(c["peaks"], c["prominences"],
                                            mp[:, :, k2], rc, pc))
                plab.append(c["state"])
            inclass[cname] = {"maps": mp, "feats": ff, "labels": plab}
        truths[(family, split, i)] = {
            "fluct": fluct, "labels": labels, "maps_phys": mph,
            "feats_phys": fp, "inclass": inclass, "truth_seed": ts}
    print(f"pilot bank built, {len(truths)} truths, {time.time() - t0:.0f}s",
          flush=True)

    cache = {}
    for (cname, aname), op in ops.items():
        U, s, Vt = svd[(cname, aname)]
        cache[(cname, aname)] = (
            {k: U.T @ op.forward_analytic(truths[k]["fluct"]) for k in pil},
            {k: np.column_stack([U.T @ op.noise_from_standard(z) for z in Z[k]])
             for k in pil})
    print(f"  projections done, {time.time() - t0:.0f}s", flush=True)

    def reconstruct(cname, aname, k, est, hy, snr, draw):
        U, s, Vt = svd[(cname, aname)]
        sig, noi = cache[(cname, aname)]
        scale = snr / s_ref
        return Vt.T @ (spectral_filter(est, s, scale, hy)
                       * (scale * sig[k] + noi[k][:, draw]))

    score_rows, state_rows, stable_rows, span_rows = [], [], [], []
    for cname in classes:
        for aname in arms:
            for est in ("TSVD", "RIDGE_IDENTITY"):
                hy = hyper[(cname, aname, est)]
                for snr in (snr_p, snr_s):
                    for k in pil:
                        rec = truths[k]
                        acc = {t: [] for t in (T_PHYS, T_CC, "CC_PROJLAB")}
                        nd = {t: [] for t in (T_PHYS, T_CC)}
                        sat = {t: [] for t in (T_PHYS, T_CC)}
                        stab, reach = [], []
                        for d in range(n_draws):
                            xh = reconstruct(cname, aname, k, est, hy, snr, d)
                            fld = (Dc[cname] @ xh).reshape(comp)
                            mp = (fld.reshape(comp[0] * comp[1], comp[2]) @ Wc
                                  ).reshape(comp[0], comp[1], ages.size)
                            tm = float(np.abs(mp).max())
                            rf = [peaks_to_features(
                                *[classify(mp[:, :, k2], 1,
                                           float(mp[:, :, k2].max()), tm,
                                           frac)[x]
                                  for x in ("peaks", "prominences")],
                                mp[:, :, k2], rc, pc) for k2 in range(ages.size)]
                            variants = (
                                (T_PHYS, rec["labels"], rec["maps_phys"],
                                 rec["feats_phys"]),
                                (T_CC, rec["labels"],
                                 rec["inclass"][cname]["maps"],
                                 rec["inclass"][cname]["feats"]),
                                ("CC_PROJLAB", rec["inclass"][cname]["labels"],
                                 rec["inclass"][cname]["maps"],
                                 rec["inclass"][cname]["feats"]),
                            )
                            for tname, labs, refm, reff in variants:
                                rows = [state_error(labs[k2], refm[:, :, k2],
                                                    mp[:, :, k2], reff[k2],
                                                    rf[k2], rc, pc, met)
                                        for k2 in range(ages.size)]
                                acc[tname].append(
                                    aggregate_all_states(rows)["all_state_error"])
                                if tname in nd:
                                    live = [r for r in rows
                                            if r["state"] != "DEAD"]
                                    nd[tname].append(
                                        aggregate_all_states(live)["all_state_error"])
                                    sat[tname].append(
                                        float(np.mean([r["error"] >= 1.0 - 1e-12
                                                       for r in rows])))
                                    # every draw, not only the first
                                    for k2, rr in enumerate(rows):
                                        state_rows.append({
                                            "class": cname, "arm": aname,
                                            "estimator": est, "snr0": snr,
                                            "family": k[0], "index": k[2],
                                            "target": tname, "draw": d,
                                            "age_M": float(ages[k2]),
                                            "state": rr["state"],
                                            "measure": rr["measure"],
                                            "error": rr["error"]})
                                if tname == T_PHYS:
                                    e = np.array([r["error"] for r in rows])
                                    reach.append(float(
                                        ages[np.maximum.accumulate(e) <= eps].max()
                                        if e[0] <= eps else 0.0))
                            # both estimators and both SNRs now
                            for k2 in range(ages.size):
                                if rec["labels"][k2] != "MULTI_RESOLVED":
                                    continue
                                a = assignment(rec["feats_phys"][k2], rf[k2], met)
                                stab.append(a["unbalanced_cost"]
                                            / met["unmatched_cost"])
                        row = {"class": cname, "arm": aname, "estimator": est,
                               "snr0": snr, "family": k[0], "index": k[2],
                               "hyperparameter": hy}
                        for t in acc:
                            row[f"{t}_all_state_error"] = float(np.mean(acc[t]))
                        for t in nd:
                            row[f"{t}_non_dead_error"] = float(np.mean(nd[t]))
                            row[f"{t}_saturation_fraction"] = float(np.mean(sat[t]))
                        row["stable_multi_cost_normalized"] = (
                            float(np.mean(stab)) if stab else float("nan"))
                        row["n_stable_multi_states"] = len(stab)
                        score_rows.append(row)
                        for rr in reach:
                            span_rows.append({"class": cname, "arm": aname,
                                              "estimator": est, "snr0": snr,
                                              "family": k[0], "index": k[2],
                                              "pass_to_age_M": rr})
        print(f"  {cname}: scored, {time.time() - t0:.0f}s", flush=True)

    from run_hmt2_stage1_completion_score import finish
    return finish(dict(
        fz=fz, reg=reg, t0=t0, started=started, numerics=numerics,
        scratch=scratch, classes=list(classes), arms=arms, fams=fams,
        snr_p=snr_p, snr_s=snr_s, score_rows=score_rows,
        state_rows=state_rows, span_rows=span_rows, prev_end=prev_end,
        eps=eps, quant=quant, ages=ages))


if __name__ == "__main__":
    raise SystemExit(main())
