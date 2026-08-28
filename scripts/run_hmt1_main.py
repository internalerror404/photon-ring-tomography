#!/usr/bin/env python3
"""HMT-1 sealed held-out main, stage B.

Item 10 of REVIEWER_RULING_HMT1_VALIDATION_015. Rebuilds the held-out bank,
verifies every hash committed by stage A, and only then applies an operator.

There is no selection sweep in this file. The hyperparameters come out of the
sealed freeze and a gate counts any reconstruction that used a different one,
so "no retuning" is checked against the emitted table rather than asserted in
a comment.
"""
from __future__ import annotations

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

from hmt1_main_common import (FZ, HASHES, R1, VFZ, build_bank,  # noqa: E402
                              commitment, grids)
from phrt.attestation import attest  # noqa: E402
from phrt.config import load_registry  # noqa: E402
from phrt.geometry.raymap import read  # noqa: E402
from phrt.geometry.sampling import common_count, stratified_subsample  # noqa: E402
from phrt.inverse.background import (axisymmetric_design,  # noqa: E402
                                     background_error, estimate_from_field)
from phrt.io.manifests import (Gate, RunManifest, gate_from_tolerance,  # noqa: E402
                               make_run_id, merge_gate_file)
from phrt.io.tables import write_table  # noqa: E402
from phrt.metrics.features import aggregate, extract, normalized_errors  # noqa: E402
from phrt.operators.physical import PhysicalOperator  # noqa: E402
from phrt.sources.contrast import OFF_MANIFOLD, build  # noqa: E402
from phrt.sources.localized_basis import LocalizedBasis  # noqa: E402
from phrt.sources.physical_basis import PhysicalBasis  # noqa: E402
from run_hmt1_score import (family_param_keys, paired_relative,  # noqa: E402
                            spectral_filter)

LEDGER = ROOT / "artifacts" / "gates" / "hmt1_correctness_gates.json"


def unit_source(b):
    u = np.zeros(b.dimension)
    for a in range(b.n_radial):
        u[(a * b.n_azimuthal + 0) * b.n_temporal + 0] = 1.0
    return u


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--regimes", default="")
    ap.add_argument("--families", default="")
    ap.add_argument("--scratch-seed", type=int, default=0,
                    help="draw a throwaway bank under this seed instead of "
                         "the sealed one. Writes nothing canonical. Exists so "
                         "the runner can be exercised without evaluating a "
                         "held-out truth, which is a peek however small")
    args = ap.parse_args()
    t0 = time.time()
    numerics = require_single_threaded()
    started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    g = grids()
    fz, vfz, r1 = g["fz"], g["vfz"], g["r1"]
    reg = load_registry()
    des = fz["design"]
    seeds = dict(fz["seeds"])
    scratch = bool(args.scratch_seed)
    if scratch:
        seeds["bank_seed"] = int(args.scratch_seed)
        print(f"SCRATCH MODE: bank seed {seeds['bank_seed']}, nothing "
              f"canonical will be written. G2 and G16 are expected to FAIL, "
              f"because this is not the committed bank")
    snr_p, snr_s = float(des["snr_primary"]), float(des["snr_secondary"])
    n_noisy = int(des["noise_draws_per_truth"])
    arms_wanted = list(des["arms"])
    fams = [x for x in args.families.split(",") if x] or list(des["families"])
    regimes = [x for x in args.regimes.split(",") if x] or list(des["regimes"])
    sealed = fz["sealed_hyperparameters"]["values"]
    span = fz["endpoints"]["primary"]["stable_feature_interval"]
    boot = fz["endpoints"]["primary"]["old_band_feature_error"]["bootstrap"]
    old_b = float(fz["endpoints"]["primary"]["old_band_feature_error"]
                  ["old_band_boundary_M"])
    M = fz["pass_criteria"]["material_benefit_under_both_classical_estimators"]
    lim = fz["resource_limits"]
    ages, half = g["ages"], g["half"]
    old_mask = ages >= old_b
    r_axis, phi_axis, gt = g["r_axis"], g["phi_axis"], g["gt"]
    r_in, r_out = g["r_in"], g["r_out"]
    t_lo, t_hi = float(g["t_axis"][0]), float(g["t_axis"][-1])
    t_obs = np.asarray(r1["observation"]["observer_times_M"], float)

    # ---- stage A's bank, and its hashes ------------------------------------
    committed = json.loads(HASHES.read_text())
    # every declared family, not only the subset being run: the commitments
    # are a property of the freeze, and a partial run must not be able to
    # satisfy this gate by checking fewer of them
    commit_ok = ({f: commitment(f, int(des["truths_per_family"]),
                                int(seeds["bank_seed"]))
                  for f in des["families"]}
                 == fz["commitments"] == committed["seed_commitments"])
    if scratch:
        g = dict(g)
        g["fz"] = dict(fz, seeds=seeds)
    bank = build_bank(g, families=fams)
    mismatched = [k for k in sorted(bank)
                  if bank[k]["hashes"] != committed["hashes"][f"{k[0]}|{k[1]}"]]
    print(f"bank rebuilt, {len(bank)} truths, {len(mismatched)} hash "
          f"mismatches, {time.time() - t0:.0f}s")

    vseeds = set()
    for f in vfz["counts"]["families"]:
        for s in vfz["counts"]["splits"]:
            for rg in vfz["counts"]["regimes"]:
                for i in range(8):
                    p = json.dumps({"family": f, "split": s, "regime": rg,
                                    "n": 8, "seed": vfz["seeds"]["bank_seed"],
                                    "model": "contrast"}, sort_keys=True).encode()
                    vseeds.add(int(hashlib.sha256(
                        p + f"|{i}".encode()).hexdigest()[:16], 16) % (2 ** 63))
    overlap = sum(1 for k in bank if bank[k]["truth_seed"] in vseeds)

    # ---- operators ---------------------------------------------------------
    basis = LocalizedBasis(r_in, r_out, t_lo, t_hi, 4, 7, 16)
    keep = np.array([lab["azimuthal_mode"] != 0 for lab in basis.labels()])
    D = basis.design(g["gr"], g["gp"], gt)[:, keep]
    bdes = axisymmetric_design(g["gr"], gt, r_in, r_out, t_min=t_lo, t_max=t_hi)

    rng = np.random.default_rng(seeds["subsample_seed"])
    base = common_count([stratified_subsample(
        read(ROOT / "artifacts" / "raymaps" / f"a050_i050_n{n}_core.h5"),
        int(r1["observation"]["rays_per_order"]), rng)
        for n in r1["physical_model"]["orders"]], rng)
    n_orders, n_rays = len(base), base[0].n_rays

    ones = np.ones((1, n_orders))
    cfg = {"DIRECT_PHYSICAL": dict(orders=[base[0]]),
           "RESOLVED_PHYSICAL": dict(orders=base),
           "UNRESOLVED_IMAGE": dict(orders=base, mixer=ones),
           "TOTAL_FLUX": dict(orders=base, mixer=ones, collapse="total_flux")}
    ops = {n: PhysicalOperator(design=lambda r, p, t: basis.design(r, p, t)[:, keep],
                               dimension=int(keep.sum()), observer_times=t_obs,
                               **c) for n, c in cfg.items() if n in arms_wanted}
    ref_basis = PhysicalBasis(r_in, r_out, t_lo, t_hi, 4, 7, 8)
    s_ref = float(np.sqrt(np.mean(PhysicalOperator(
        orders=[base[0]], observer_times=t_obs, design=ref_basis.design,
        dimension=ref_basis.dimension).matvec(unit_source(ref_basis)) ** 2)))

    worst = {"adjoint": 0.0, "identity": 0.0, "determinism": 0.0}
    svd = {}
    for aname, op in ops.items():
        U, s, Vt = np.linalg.svd(op.to_dense(), full_matrices=False)
        svd[aname] = (U, s, Vt)
        x = np.random.default_rng(5).normal(size=op.shape[1])
        y = np.random.default_rng(6).normal(size=op.shape[0])
        f1 = float(y @ op.matvec(x))
        worst["adjoint"] = max(worst["adjoint"],
                               abs(f1 - float(x @ op.rmatvec(y)))
                               / max(abs(f1), 1e-300))
        got = op.forward_analytic(
            lambda r, p, t, _x=x: basis.design(r, p, t)[:, keep] @ _x)
        want = op.matvec(x)
        worst["identity"] = max(worst["identity"],
                                float(np.abs(got - want).max())
                                / max(float(np.abs(want).max()), 1e-300))
    print(f"operators ready, contrast class {int(keep.sum())}, "
          f"{time.time() - t0:.0f}s")

    for k in sorted(bank):
        f1 = extract(bank[k]["dj"], gt, ages, r_axis, phi_axis, half)
        f2 = extract(bank[k]["dj"], gt, ages, r_axis, phi_axis, half)
        worst["determinism"] = max(worst["determinism"], max(
            float(np.abs(np.asarray(f1[c]) - np.asarray(f2[c])).max())
            for c in ("r_h", "phi_h", "A_h", "a_m1", "a_m2")))

    bw = committed["worst_bank_residuals"]

    # ---- noise, shared across regimes so the regimes are paired ------------
    nrng = np.random.default_rng(seeds["noise_seed"])
    Z = {k: [nrng.normal(size=(n_orders, n_rays, t_obs.size))
             for _ in range(n_noisy)] for k in sorted(bank)}

    cache = {}
    for aname, op in ops.items():
        U, s, Vt = svd[aname]
        cache[aname] = (
            {k: U.T @ op.forward_analytic(bank[k]["fluct"]) for k in bank},
            {k: np.column_stack([U.T @ op.noise_from_standard(z) for z in Z[k]])
             for k in bank},
            {k: U.T @ op.forward_analytic(
                lambda r, p, t, _b=bank[k]["b"]: _b(r, t)) for k in bank})
    print(f"  projections done, {time.time() - t0:.0f}s")

    # ---- backgrounds, per regime -------------------------------------------
    bgerr_rows = []
    b_hat = {}
    for regime in regimes:
        for k in sorted(bank):
            rec = bank[k]
            if regime == "oracle_known":
                b_hat[(regime, k)] = rec["bg"]
                info = {"regime": regime, **background_error(rec["bg"], rec["bg"])}
            else:
                total = rec["bg"] + rec["dj"]
                bh, inf = estimate_from_field(total, bdes)
                if regime == "joint_inversion":
                    q, _ = np.linalg.qr(D)
                    for _ in range(6):
                        resid = total - q @ (q.T @ (total - bh))
                        bh, inf = estimate_from_field(resid, bdes)
                b_hat[(regime, k)] = bh
                info = {"regime": regime, **background_error(bh, rec["bg"]),
                        **{x: v for x, v in inf.items() if x != "min_before_clip"}}
            bgerr_rows.append({"family": k[0], "index": k[1], **info})
    print(f"  backgrounds estimated, {time.time() - t0:.0f}s")

    proj = {a: {} for a in ops}
    for aname, op in ops.items():
        U, s, Vt = svd[aname]
        for regime in regimes:
            for k in sorted(bank):
                if regime == "oracle_known":
                    proj[aname][(regime, k)] = cache[aname][2][k]
                    continue
                coef, *_ = np.linalg.lstsq(bdes, b_hat[(regime, k)], rcond=None)
                proj[aname][(regime, k)] = U.T @ op.forward_analytic(
                    lambda r, p, t, _c=coef: axisymmetric_design(
                        r, t, r_in, r_out, t_min=float(gt.min()),
                        t_max=float(gt.max())) @ _c)
    print(f"  background projections done, {time.time() - t0:.0f}s")

    fkeys = {f: family_param_keys(vfz, f) for f in fams}

    def reconstruct(aname, k, regime, est, hyper, snr, draw):
        U, s, Vt = svd[aname]
        sig, noi, bkg = cache[aname]
        scale = snr / s_ref
        c = scale * (sig[k] + bkg[k] - proj[aname][(regime, k)])
        if draw < n_noisy:
            c = c + noi[k][:, draw]
        return Vt.T @ (spectral_filter(est, s, scale, hyper) * c)

    def feature_error(k, xhat):
        recon = extract(D @ xhat, gt, ages, r_axis, phi_axis, half)
        errs = normalized_errors(bank[k]["features"], recon, g["r_span"],
                                 g["obs_span"])
        return aggregate(errs, fkeys[k[0]]), errs

    # ---- the main, at sealed hyperparameters only --------------------------
    score_rows, joint_rows, unsealed = [], [], 0
    for regime in regimes:
        for aname in ops:
            for est in ("TSVD", "RIDGE_IDENTITY"):
                sk = f"{regime}|{aname}|{est}"
                hyper = float(sealed[sk]["hyperparameter"])
                for snr in (snr_p, snr_s):
                    for k in sorted(bank):
                        oe, comp = [], []
                        for d in range(n_noisy + 1):
                            xh = reconstruct(aname, k, regime, est, hyper, snr, d)
                            e, errs = feature_error(k, xh)
                            if d < n_noisy:
                                oe.append(float(e[old_mask].mean()))
                                # component errors are averaged over the noisy
                                # draws. Reading them off whichever draw the
                                # loop happened to end on would report the
                                # noiseless control's components under a noisy
                                # row, since the noiseless draw runs last
                                comp.append((
                                    float(errs["radial"][old_mask].mean()),
                                    float(errs["angular"][old_mask].mean()),
                                    float(errs.get("t_birth_age_M", np.nan)),
                                    float(errs.get("tau_decay_M", np.nan))))
                                if est == "TSVD" and snr == snr_p:
                                    joint_rows.append({
                                        "regime": regime, "arm": aname,
                                        "family": k[0], "index": k[1],
                                        "draw": d, "snr0": snr,
                                        "pass_to_age_M": float(
                                            ages[np.maximum.accumulate(e)
                                                 <= span["epsilon"]].max()
                                            if e[0] <= span["epsilon"] else 0.0)})
                            else:
                                noiseless = float(e[old_mask].mean())
                                noiseless_x = xh
                        if hyper != float(sealed[sk]["hyperparameter"]):
                            unsealed += 1
                        cm = np.nanmean(np.asarray(comp, float), axis=0)
                        # how far the noisy reconstructions sit from the
                        # noiseless one, in the reconstruction itself rather
                        # than in the endpoint. This is what "the noise path
                        # is live" means and it does not assume a direction
                        # for the error
                        nx = float(np.linalg.norm(noiseless_x))
                        noise_disp = float(np.median([
                            np.linalg.norm(
                                reconstruct(aname, k, regime, est, hyper, snr, d)
                                - noiseless_x) / max(nx, 1e-300)
                            for d in range(n_noisy)]))
                        score_rows.append({
                            "regime": regime, "arm": aname, "estimator": est,
                            "snr0": snr, "family": k[0], "index": k[1],
                            "hyperparameter": hyper,
                            "old_band_feature_error": float(np.mean(oe)),
                            "noiseless_old_band_feature_error": noiseless,
                            "noise_displacement_relative": noise_disp,
                            "radial_error_old": float(cm[0]),
                            "angular_error_old_rad": float(cm[1] * np.pi),
                            "t_birth_error": float(cm[2]),
                            "tau_decay_error": float(cm[3])})
        print(f"  {regime}: scored, {time.time() - t0:.0f}s")
        if time.time() - t0 > lim["wall_clock_seconds"]:
            raise SystemExit("HMT1_MAIN_IMPLEMENTATION_DEFECT: wall-clock limit")

    # ---- off-manifold controls, built and excluded -------------------------
    off_rows = []
    for family in OFF_MANIFOLD:
        for i in range(4):
            # not hash((family, i)): str hashing is salted per interpreter
            # unless PYTHONHASHSEED is set before the process starts, and
            # pinning it from inside the process is too late. A salted seed
            # would draw a different control bank on every run
            oseed = int(hashlib.sha256(
                f"hmt1_main_off_manifold|{family}|{i}".encode()
            ).hexdigest()[:16], 16) % (2 ** 63)
            orng = np.random.default_rng(oseed)
            _, _, _, odj, obg, odiag = build(
                orng, family, g["spin"], r_in, r_out, g["gr"], g["gp"], gt,
                g["t_index"], g["NT"])
            off_rows.append({"family": family, "index": i,
                             "in_endpoint": False,
                             "min_total": odiag["min_total"],
                             "azimuthal_mean_max_abs":
                                 odiag["azimuthal_mean_max_abs"]})

    # ---- null-pair controls -------------------------------------------------
    null_rows = []
    prng = np.random.default_rng(seeds["null_pair_seed"])
    for aname in ops:
        U, s, Vt = svd[aname]
        nz = np.flatnonzero(s > 1e-12 * s.max())
        small = nz[np.argsort(s[nz])][:max(1, len(nz) // 8)]
        for target in (0.25, 1.0, 4.0):
            for _ in range(8):
                w = prng.normal(size=small.size)
                w /= max(np.linalg.norm(w), 1e-300)
                delta = Vt[small].T @ w
                pred = float(np.linalg.norm((snr_p / s_ref) * s[small] * w))
                real = float(np.linalg.norm(
                    (snr_p / s_ref) * (s * (Vt @ ((target / pred) * delta)))))
                null_rows.append({"arm": aname,
                                  "target_separation_sigma": target,
                                  "realized_separation_sigma": real,
                                  "relative_error": abs(real - target) / target})
    print(f"  controls done, {time.time() - t0:.0f}s")

    state = dict(
        fz=fz, vfz=vfz, reg=reg, t0=t0, started=started, numerics=numerics,
        regimes=regimes, fams=fams, arms=arms_wanted, sealed=sealed,
        snr_p=snr_p, snr_s=snr_s, n_noisy=n_noisy, span=span, boot=boot,
        M=M, lim=lim, ages=ages, old_mask=old_mask, keep=keep,
        score_rows=score_rows, joint_rows=joint_rows, bgerr_rows=bgerr_rows,
        off_rows=off_rows, null_rows=null_rows, bank=bank,
        commit_ok=commit_ok, mismatched=mismatched, overlap=overlap,
        unsealed=unsealed, worst=worst, bank_worst=bw,
        committed_sha=committed.get("freeze_sha256"), scratch=scratch)
    from run_hmt1_main_score import finish
    return finish(state)


if __name__ == "__main__":
    raise SystemExit(main())
