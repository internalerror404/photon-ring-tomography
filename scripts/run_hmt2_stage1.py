#!/usr/bin/env python3
"""HMT-2 stage 1: resolution-aware morphology validation.

REVIEWER_RULING_HMT2_STAGE0_019 items 12 to 18. The first HMT-2 stage that
constructs an operator.

Two targets are carried through every row. CLASS_CONDITIONAL compares the
reconstruction against the best in-class approximation of the source, and says
how much of what the class can represent the estimator recovers.
PHYSICAL_END_TO_END compares it against the analytic source, and says how much
of what is actually there it recovers. Reporting the first alone is how a
class-conditional result gets read as a physical claim, so a gate counts any
row that carries only one.
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
from phrt.metrics.feature_sets import (assignment, cell_metric,  # noqa: E402
                                       peaks_to_features)
from phrt.metrics.morphology import aggregate_all_states, state_error  # noqa: E402
from phrt.metrics.topography import classify, reconcile  # noqa: E402
from phrt.metrics.windowed_reference import window_stack  # noqa: E402
from phrt.operators.physical import PhysicalOperator  # noqa: E402
from phrt.sources.contrast import build  # noqa: E402
from phrt.sources.localized_basis import LocalizedBasis  # noqa: E402
from phrt.sources.physical_basis import PhysicalBasis  # noqa: E402
from phrt.sources.separable_projection import factors, project  # noqa: E402
from run_hmt1_score import spectral_filter  # noqa: E402

FZ = ROOT / "artifacts" / "configs" / "HMT2_STAGE1_RESOLUTION_AWARE_MORPHOLOGY_VALIDATION_V0.json"
S0 = ROOT / "artifacts" / "configs" / "HMT2_STAGE0_SOURCE_OBJECT_AND_RESOLUTION_AUDIT_V0.json"
R1 = ROOT / "artifacts" / "configs" / "R1_MAIN_FREEZE.json"
OUT = ROOT / "artifacts" / "gates" / "hmt2_stage1_gates.json"
LEDGER = ROOT / "artifacts" / "gates" / "hmt2_correctness_gates.json"


def commitment(family, split, n, seed):
    return hashlib.sha256(json.dumps(
        {"family": family, "split": f"hmt2_stage1_{split}", "n": n,
         "seed": seed, "model": "contrast"}, sort_keys=True).encode()).hexdigest()


def truth_seed(family, split, i, n, seed):
    p = json.dumps({"family": family, "split": f"hmt2_stage1_{split}", "n": n,
                    "seed": seed, "model": "contrast"}, sort_keys=True).encode()
    return int(hashlib.sha256(p + f"|{i}".encode()).hexdigest()[:16], 16) % (2 ** 63)


def axes_for(level, r_in, r_out, t_lo, t_hi):
    nr, npz, nt = level
    return (np.exp(np.linspace(np.log(r_in), np.log(r_out), nr)),
            np.linspace(0.0, 2 * np.pi, npz, endpoint=False),
            np.linspace(t_lo, t_hi, nt))


def unit_source(b):
    u = np.zeros(b.dimension)
    for a in range(b.n_radial):
        u[(a * b.n_azimuthal + 0) * b.n_temporal + 0] = 1.0
    return u


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0,
                    help="smoke run; writes nothing canonical")
    args = ap.parse_args()
    t0 = time.time()
    numerics = require_single_threaded()
    started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    fz = json.loads(FZ.read_text())
    s0 = json.loads(S0.read_text())
    r1 = json.loads(R1.read_text())
    reg = load_registry()
    scratch = bool(args.limit)

    r_in = float(r1["physical_model"]["r_inner_M"])
    r_out = float(r1["physical_model"]["r_outer_M"])
    t_lo = float(r1["observation"]["basis_t_min"])
    t_hi = float(r1["observation"]["basis_t_max"])
    t_obs = np.asarray(r1["observation"]["observer_times_M"], float)
    inh = s0["inherited"]
    spin = float(inh["spin"])
    half = float(inh["probe_half_width_M"])
    ages = np.arange(0.0, float(inh["age_grid_max_M"]) + 1e-9,
                     float(inh["age_grid_step_M"]))
    frac = float(fz["classification"]["prominence_fraction"])
    mult = fz["source_model"]["expected_windowed_multiplicity"]
    lab_levels = [tuple(x) for x in fz["classification"]["levels"]]
    comp = tuple(fz["evaluation"]["comparison_grid"])
    fams = list(fz["source_model"]["families"])
    bank_cfg = fz["bank"]
    n_per = int(bank_cfg["truths_per_family_per_split"])
    n_draws = int(bank_cfg["noise_draws_per_truth"])
    n_sel_draws = int(bank_cfg["selection_draws_per_truth"])
    seed = int(bank_cfg["bank_seed"])
    snr_p = float(fz["snr"]["primary"])
    snr_s = float(fz["snr"]["secondary"])
    arms_wanted = list(fz["arms"])
    classes = {fz["classes"]["primary"]["id"]: fz["classes"]["primary"],
               fz["classes"]["control"]["id"]: fz["classes"]["control"]}
    lim = fz["resource_limits"]

    if args.limit:
        fams = fams[:2]
        n_per = min(n_per, args.limit)

    recomputed = {f"{f}|{sp}": commitment(f, sp, n_per, seed)
                  for f in fams for sp in bank_cfg["splits"]}
    commitments_ok = all(
        recomputed[k] == bank_cfg["commitments"][k] for k in recomputed) \
        if not args.limit else True

    rc, pc, tc = axes_for(comp, r_in, r_out, t_lo, t_hi)
    met = cell_metric(rc, pc)
    Rc, Pc, Tc = np.meshgrid(rc, pc, tc, indexing="ij")
    Wc = window_stack(tc, ages, half)

    # ---- operators ---------------------------------------------------------
    basis = LocalizedBasis(r_in, r_out, t_lo, t_hi, 4, 7, 16)
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
    worst = {"adjoint": 0.0, "identity": 0.0}
    for cname, cdef in classes.items():
        b = LocalizedBasis(r_in, r_out, t_lo, t_hi, cdef["radial"],
                           cdef["azimuthal"], cdef["temporal"])
        keep = np.array([lab["azimuthal_mode"] != 0 for lab in b.labels()])
        bases[cname], keeps[cname] = b, keep
        for aname, c in cfg.items():
            if aname not in arms_wanted:
                continue
            op = PhysicalOperator(
                design=lambda r, p, t, _b=b, _k=keep: _b.design(r, p, t)[:, _k],
                dimension=int(keep.sum()), observer_times=t_obs, **c)
            ops[(cname, aname)] = op
            U, s, Vt = np.linalg.svd(op.to_dense(), full_matrices=False)
            svd[(cname, aname)] = (U, s, Vt)
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
    ref_basis = PhysicalBasis(r_in, r_out, t_lo, t_hi, 4, 7, 8)
    s_ref = float(np.sqrt(np.mean(PhysicalOperator(
        orders=[base[0]], observer_times=t_obs, design=ref_basis.design,
        dimension=ref_basis.dimension).matvec(unit_source(ref_basis)) ** 2)))
    print(f"operators ready, {len(ops)} (class, arm) pairs, "
          f"{time.time() - t0:.0f}s", flush=True)

    # design of each class on the comparison grid, for reconstructing fields
    Dc = {c: bases[c].design(Rc.ravel(), Pc.ravel(), Tc.ravel())[:, keeps[c]]
          for c in classes}
    facs = {c: factors(rc, pc, tc, classes[c]["radial"], classes[c]["azimuthal"],
                       classes[c]["temporal"]) for c in classes}

    # ---- bank ---------------------------------------------------------------
    keys = [(f, sp, i) for f in fams for sp in bank_cfg["splits"]
            for i in range(n_per)]
    truths, bank_rows = {}, []
    wbad = {"zero_mean": 0.0, "positivity": 0.0}
    for (family, split, i) in keys:
        ts = truth_seed(family, split, i, n_per, seed)
        rng = np.random.default_rng(ts)
        # built on the comparison grid: this is where every comparison happens
        _, fluct, _, dj, _, diag = build(rng, family, spin, r_in, r_out,
                                         Rc.ravel(), Pc.ravel(), Tc.ravel(),
                                         np.tile(np.arange(comp[2]),
                                                 comp[0] * comp[1]), comp[2])
        wbad["zero_mean"] = max(wbad["zero_mean"], diag["zero_mean_max_abs"])
        wbad["positivity"] = max(wbad["positivity"], max(0.0, -diag["min_total"]))

        # labels from the two finest refinement levels, as stage 0R
        lab = {}
        for lv in lab_levels:
            r, p, t = axes_for(lv, r_in, r_out, t_lo, t_hi)
            R, P, T = np.meshgrid(r, p, t, indexing="ij")
            v = np.asarray(fluct(R.ravel(), P.ravel(), T.ravel()),
                           float).reshape(r.size * p.size, t.size)
            m = (v @ window_stack(t, ages, half)).reshape(r.size, p.size, ages.size)
            tmax = float(np.abs(m).max())
            lab[lv] = [classify(m[:, :, k], int(mult[family]),
                                float(m[:, :, k].max()), tmax, frac)["state"]
                       for k in range(ages.size)]
        labels = [reconcile(lab[lab_levels[-1]][k], lab[lab_levels[-2]][k])
                  for k in range(ages.size)]

        raw = dj.reshape(comp[0], comp[1], comp[2])
        maps_phys = (raw.reshape(comp[0] * comp[1], comp[2]) @ Wc).reshape(
            comp[0], comp[1], ages.size)
        feats_phys, inclass = {}, {}
        tmax_p = float(np.abs(maps_phys).max())
        fp = []
        for k in range(ages.size):
            m = maps_phys[:, :, k]
            c = classify(m, int(mult[family]), float(m.max()), tmax_p, frac)
            fp.append(peaks_to_features(c["peaks"], c["prominences"], m, rc, pc))
        for cname in classes:
            pr = project(raw, facs[cname])
            mp = (pr.reshape(comp[0] * comp[1], comp[2]) @ Wc).reshape(
                comp[0], comp[1], ages.size)
            tm = float(np.abs(mp).max())
            ff = []
            for k in range(ages.size):
                m = mp[:, :, k]
                c = classify(m, int(mult[family]), float(m.max()), tm, frac)
                ff.append(peaks_to_features(c["peaks"], c["prominences"], m, rc, pc))
            inclass[cname] = {"maps": mp, "feats": ff}
        truths[(family, split, i)] = {
            "fluct": fluct, "raw": raw, "labels": labels,
            "maps_phys": maps_phys, "feats_phys": fp, "inclass": inclass,
            "truth_seed": ts}
        bank_rows.append({"family": family, "split": split, "index": i,
                          "truth_seed": ts,
                          "zero_mean_max_abs": diag["zero_mean_max_abs"],
                          "min_total": diag["min_total"],
                          **{f"n_{s.lower()}": labels.count(s) for s in
                             ("SINGLE_RESOLVED", "MULTI_RESOLVED", "BLENDED",
                              "DEAD", "AMBIGUOUS")}})
    print(f"bank built, {len(truths)} truths, {time.time() - t0:.0f}s", flush=True)

    # ---- projections through each operator ---------------------------------
    cache = {}
    nrng = np.random.default_rng(seed + 2)
    Z = {k: [nrng.normal(size=(n_orders, n_rays, t_obs.size))
             for _ in range(n_draws)] for k in keys}
    for (cname, aname), op in ops.items():
        U, s, Vt = svd[(cname, aname)]
        cache[(cname, aname)] = (
            {k: U.T @ op.forward_analytic(truths[k]["fluct"]) for k in keys},
            {k: np.column_stack([U.T @ op.noise_from_standard(z) for z in Z[k]])
             for k in keys})
    print(f"  projections done, {time.time() - t0:.0f}s", flush=True)

    def reconstruct(cname, aname, k, est, hyper, snr, draw):
        U, s, Vt = svd[(cname, aname)]
        sig, noi = cache[(cname, aname)]
        scale = snr / s_ref
        c = scale * sig[k] + noi[k][:, draw]
        return Vt.T @ (spectral_filter(est, s, scale, hyper) * c)

    def morphology(k, cname, xhat):
        """Both targets from one reconstruction. Item 14."""
        rec = truths[k]
        fld = (Dc[cname] @ xhat).reshape(comp[0], comp[1], comp[2])
        mp = (fld.reshape(comp[0] * comp[1], comp[2]) @ Wc).reshape(
            comp[0], comp[1], ages.size)
        tm = float(np.abs(mp).max())
        out = {}
        rf = []
        for kk in range(ages.size):
            m = mp[:, :, kk]
            # the reconstruction's own state label is not used: only its peak
            # set is. The state comes from the source, which is the point --
            # the truth decides what question is asked, not the estimate
            c = classify(m, 1, float(m.max()), tm, frac)
            rf.append(peaks_to_features(c["peaks"], c["prominences"], m, rc, pc))
        for target, ref in (("PHYSICAL_END_TO_END",
                             (rec["maps_phys"], rec["feats_phys"])),
                            ("CLASS_CONDITIONAL",
                             (rec["inclass"][cname]["maps"],
                              rec["inclass"][cname]["feats"]))):
            rows = [state_error(rec["labels"][kk], ref[0][:, :, kk],
                                mp[:, :, kk], ref[1][kk], rf[kk], rc, pc, met)
                    for kk in range(ages.size)]
            out[target] = {"rows": rows, **aggregate_all_states(rows)}
        return out, rf

    grids = {"TSVD": [10 ** (-j / 2) for j in range(15)],
             "RIDGE_IDENTITY": [10 ** (-j / 2) for j in range(21)]}
    sel_keys = [k for k in keys if k[1] == "selection"]
    pil_keys = [k for k in keys if k[1] == "pilot"]

    selected, sel_rows = {}, []
    for cname in classes:
        for aname in arms_wanted:
            for est, grid in grids.items():
                best = None
                for hyper in grid:
                    tot = []
                    for k in sel_keys:
                        for d in range(n_sel_draws):
                            xh = reconstruct(cname, aname, k, est, hyper,
                                             snr_p, d)
                            m, _ = morphology(k, cname, xh)
                            tot.append(m["PHYSICAL_END_TO_END"]["all_state_error"])
                    v = float(np.mean(tot))
                    if best is None or v < best[1] - 1e-15:
                        best = (hyper, v)
                selected[(cname, aname, est)] = best[0]
                sel_rows.append({"class": cname, "arm": aname, "estimator": est,
                                 "selected_hyperparameter": best[0],
                                 "selection_error": best[1],
                                 "n_grid": len(grid),
                                 "at_max_regularization_end":
                                     bool(abs(best[0] - max(grid)) < 1e-12)})
        print(f"  {cname}: selection done, {time.time() - t0:.0f}s", flush=True)

    score_rows, state_rows = [], []
    for cname in classes:
        for aname in arms_wanted:
            for est in grids:
                hyper = selected[(cname, aname, est)]
                for snr in (snr_p, snr_s):
                    for k in pil_keys:
                        agg = {t: [] for t in ("PHYSICAL_END_TO_END",
                                               "CLASS_CONDITIONAL")}
                        stable = []
                        first = None
                        for d in range(n_draws):
                            xh = reconstruct(cname, aname, k, est, hyper, snr, d)
                            m, rf = morphology(k, cname, xh)
                            if first is None:
                                first = m          # kept for the state rows
                            for t in agg:
                                agg[t].append(m[t]["all_state_error"])
                            if est == "TSVD" and snr == snr_p:
                                for kk in range(ages.size):
                                    if truths[k]["labels"][kk] != "MULTI_RESOLVED":
                                        continue
                                    a = assignment(truths[k]["feats_phys"][kk],
                                                   rf[kk], met)
                                    stable.append(a["unbalanced_cost"]
                                                  / met["unmatched_cost"])
                        row = {"class": cname, "arm": aname, "estimator": est,
                               "snr0": snr, "family": k[0], "index": k[2],
                               "hyperparameter": hyper}
                        for t in agg:
                            row[f"{t}_all_state_error"] = float(np.mean(agg[t]))
                        row["stable_multi_cost_normalized"] = (
                            float(np.mean(stable)) if stable else float("nan"))
                        row["n_stable_multi_states"] = len(stable)
                        score_rows.append(row)
                        # per-state rows from the draw already computed. A
                        # second morphology pass here would triple the cost of
                        # the pilot to recompute numbers already in hand
                        for t in agg:
                            for kk, rr in enumerate(first[t]["rows"]):
                                state_rows.append({
                                    "class": cname, "arm": aname,
                                    "estimator": est, "snr0": snr,
                                    "family": k[0], "index": k[2],
                                    "target": t, "age_M": float(ages[kk]),
                                    "state": rr["state"],
                                    "measure": rr["measure"],
                                    "error": rr["error"]})
        print(f"  {cname}: pilot scored, {time.time() - t0:.0f}s", flush=True)
        if time.time() - t0 > lim["wall_clock_seconds"]:
            raise SystemExit("HMT2_S1_IMPLEMENTATION_DEFECT: wall-clock limit")

    from run_hmt2_stage1_score import finish
    return finish(dict(
        fz=fz, reg=reg, t0=t0, started=started, numerics=numerics,
        scratch=scratch, ages=ages, classes=list(classes),
        arms=arms_wanted, fams=fams, snr_p=snr_p, snr_s=snr_s,
        commitments_ok=commitments_ok, worst=worst, wbad=wbad,
        bank_rows=bank_rows, sel_rows=sel_rows, score_rows=score_rows,
        state_rows=state_rows, truths=truths, lim=lim,
        n_label_states=sum(len(t["labels"]) for t in truths.values())))


if __name__ == "__main__":
    raise SystemExit(main())
