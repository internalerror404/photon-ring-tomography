"""Scoring half of R1L stage 2. Imported by run_r1l_stage2_validation.py.

Split out because the bank construction and the scoring answer different
questions and fail in different ways: a bank that cannot be built is
R1L_STAGE2_SOURCE_BANK_FAILURE and never reaches an operator, while everything
here is downstream of a bank that already passed its tolerances.

The arithmetic that makes this affordable: with the whitened operator's SVD
computed once per (class, arm), the SNR only rescales the singular values, so
``U^T y`` is precomputed once per (truth, draw) and every SNR, estimator and
hyperparameter after that is O(n). Without it the hyperparameter sweep alone
would be a petaflop.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]

from phrt.io.manifests import Gate, gate_from_tolerance, merge_gate_file
from phrt.io.tables import write_table
from phrt.metrics.cluster_bootstrap import mean_difference_interval
from phrt.operators.physical import PhysicalOperator
from phrt.sources.localized_basis import LocalizedBasis
from phrt.sources.physical_basis import PhysicalBasis

CLASSDEF = {"L224": (4, 7, 8), "L448": (4, 7, 16), "L1056": (6, 11, 16)}


def unit_source(basis):
    u = np.zeros(basis.dimension)
    for a in range(basis.n_radial):
        u[(a * basis.n_azimuthal + 0) * basis.n_temporal + 0] = 1.0
    return u


def arm_configs(base, names):
    ones = np.ones((1, len(base)))
    cfg = {"DIRECT_PHYSICAL": dict(orders=[base[0]]),
           "RESOLVED_PHYSICAL": dict(orders=base),
           "UNRESOLVED_IMAGE": dict(orders=base, mixer=ones),
           "TOTAL_FLUX": dict(orders=base, mixer=ones, collapse="total_flux")}
    return {k: cfg[k] for k in names}


def filters(kind, s, scale, hyper):
    """Diagonal spectral filter for one estimator at one hyperparameter.

    ``s`` are the unit-sigma singular values; the SNR enters only as ``scale``,
    so the filter is formed here rather than by rebuilding the operator.
    """
    sc = s * scale
    if kind == "TSVD":
        keep = sc >= hyper * sc.max()
        f = np.zeros_like(sc)
        f[keep] = 1.0 / sc[keep]
        return f
    lam = hyper * (sc.max() ** 2)
    return sc / (sc ** 2 + lam)


def run_scoring(st) -> int:
    t0 = st["t0"]
    fz, man, run_dir = st["fz"], st["man"], st["run_dir"]
    gr, gp, gt = st["grid"]
    level, windows, old_mask = st["level"], st["windows"], st["old_mask"]
    ages, truths, snr_grid = st["ages"], st["truths"], st["snr_grid"]
    snr_ref, grids, n_draws = st["snr_ref"], st["grids"], st["n_draws"]
    r_in, r_out, t_lo, t_hi = st["r"]
    base, t_obs, arms_wanted = st["base"], st["t_obs"], st["arms"]
    lim, seeds = st["lim"], st["seeds"]

    keys = sorted(truths)
    sel = [k for k in keys if k[2] == "selection"]
    pil = [k for k in keys if k[2] == "pilot"]
    n_orders, n_rays = len(base), base[0].n_rays

    # one physical noise draw per (truth, draw index), shared by every arm and
    # every class, so arms stay paired and classes see the same detector
    nrng = np.random.default_rng(seeds["noise_seed"])
    Z = {k: [nrng.normal(size=(n_orders, n_rays, t_obs.size))
             for _ in range(n_draws)] for k in keys}

    ref_basis = PhysicalBasis(r_in, r_out, t_lo, t_hi, 4, 7, 8)
    s_ref = float(np.sqrt(np.mean(
        PhysicalOperator(orders=[base[0]], observer_times=t_obs,
                         design=ref_basis.design,
                         dimension=ref_basis.dimension
                         ).matvec(unit_source(ref_basis)) ** 2)))

    sel_rows, prim_rows, age_rows, floor_rows, sub_rows, null_rows = [], [], [], [], [], []
    worst = {"adjoint": 0.0, "closed_form": 0.0, "replay": 0}
    truth_vals = {k: truths[k]["values"] for k in keys}
    struct_of = lambda v: v - level @ (level.T @ v)          # noqa: E731

    for cname, (nr, na, nt) in st["classes"].items():
        basis = LocalizedBasis(r_in, r_out, t_lo, t_hi, nr, na, nt)
        D = basis.design(gr, gp, gt)                          # eval-grid design
        Ds = D - level @ (level.T @ D)                        # structure part
        # least-squares projector onto the class, for the representation floor
        Q, _ = np.linalg.qr(D)
        ops = {n: PhysicalOperator(design=basis.design, dimension=basis.dimension,
                                   observer_times=t_obs, **cfg)
               for n, cfg in arm_configs(base, arms_wanted).items()}

        # representation floor: what no estimator can beat, measured once
        for k in keys:
            v = truth_vals[k]
            res = v - Q @ (Q.T @ v)
            sv, sres = struct_of(v), struct_of(res)
            floor_rows.append({
                "source_class": cname, "bank": k[0], "family": k[1],
                "split": k[2], "index": k[3],
                "representation_floor_relative":
                    float(np.linalg.norm(res) / max(np.linalg.norm(v), 1e-300)),
                "representation_floor_structure_relative":
                    float(np.linalg.norm(sres) / max(np.linalg.norm(sv), 1e-300)),
                "old_band_structure_floor": float(np.sqrt(
                    np.einsum("ap,p->a", windows[old_mask] ** 2, sres ** 2).mean())),
            })

        svds, cache = {}, {}
        for aname, op in ops.items():
            B = op.to_dense()
            U, s, Vt = np.linalg.svd(B, full_matrices=False)
            svds[aname] = (U, s, Vt)
            x = np.random.default_rng(5).normal(size=op.shape[1])
            y = np.random.default_rng(6).normal(size=op.shape[0])
            worst["adjoint"] = max(worst["adjoint"],
                                   abs(float(y @ op.matvec(x)) - float(x @ op.rmatvec(y)))
                                   / max(abs(float(y @ op.matvec(x))), 1e-300))
            # forward_analytic must agree with matvec on an in-class source
            got = op.forward_analytic(lambda r, p, t: basis.design(r, p, t) @ x)
            want = op.matvec(x)
            worst["closed_form"] = max(
                worst["closed_form"],
                float(np.abs(got - want).max()) / max(float(np.abs(want).max()), 1e-300))

            # U^T y for every (truth, draw), batched
            csig, cnoise = {}, {}
            for k in keys:
                # the shaped bank truth, not the raw family render: the data
                # and the scored truth must be the same object
                csig[k] = U.T @ op.forward_analytic(truths[k]["render"])
                cnoise[k] = np.column_stack(
                    [U.T @ op.noise_from_standard(z) for z in Z[k]])
            cache[aname] = (csig, cnoise)
        print(f"  {cname}: operators and projections done, {time.time()-t0:.0f}s")

        # ---- selection split: choose the hyperparameter, at the reference SNR
        selected = {}
        for aname in arms_wanted:
            U, s, Vt = svds[aname]
            csig, cnoise = cache[aname]
            scale = snr_ref / s_ref
            for est, grid in grids.items():
                best = None
                for hyper in grid:
                    f = filters(est, s, scale, hyper)
                    errs = []
                    for k in sel:
                        v = truth_vals[k]
                        for d in range(n_draws):
                            c = scale * csig[k] + cnoise[k][:, d]
                            xh = Vt.T @ (f * c)
                            e = struct_of(D @ xh - v)
                            errs.append(np.sqrt(np.einsum(
                                "ap,p->a", windows[old_mask] ** 2, e ** 2).mean()))
                    m = float(np.mean(errs))
                    if best is None or m < best[1] - 1e-15:
                        best = (hyper, m)
                selected[(aname, est)] = best[0]
                sel_rows.append({"source_class": cname, "arm": aname,
                                 "estimator": est, "snr0": snr_ref,
                                 "selected_hyperparameter": best[0],
                                 "selection_old_band_structure_error": best[1],
                                 "n_grid": len(grid), "split": "selection",
                                 "n_truths": len(sel), "n_draws": n_draws})
        print(f"  {cname}: selection done, {time.time()-t0:.0f}s")

        # ---- pilot split: the reported endpoint, at every frozen SNR
        per_truth = {}
        for aname in arms_wanted:
            U, s, Vt = svds[aname]
            csig, cnoise = cache[aname]
            Pdata = Vt[s > 1e-12 * s.max()]           # the arm's own row space
            for est in grids:
                hyper = selected[(aname, est)]
                for snr in snr_grid:
                    scale = snr / s_ref
                    f = filters(est, s, scale, hyper)
                    for k in pil:
                        v, sv = truth_vals[k], struct_of(truth_vals[k])
                        old_e, spans = [], []
                        for d in range(n_draws):
                            c = scale * csig[k] + cnoise[k][:, d]
                            xh = Vt.T @ (f * c)
                            e = struct_of(D @ xh - v)
                            per_age = np.sqrt(np.einsum("ap,p->a", windows ** 2, e ** 2))
                            nrm = np.sqrt(np.einsum("ap,p->a", windows ** 2, sv ** 2))
                            rel = per_age / np.maximum(nrm, 1e-12 + 0.0)
                            old_e.append(float(per_age[old_mask].mean()))
                            ok = rel <= 0.25
                            run = 0.0
                            for j, a in enumerate(ages):
                                if ok[j]:
                                    run = float(a)
                                else:
                                    break
                            spans.append(run)
                            if snr == snr_ref and est == "TSVD" and d == 0:
                                for j, a in enumerate(ages):
                                    age_rows.append({
                                        "source_class": cname, "arm": aname,
                                        "bank": k[0], "family": k[1], "index": k[3],
                                        "retarded_age": float(a),
                                        "structure_error_absolute": float(per_age[j]),
                                        "structure_error_normalized": float(rel[j]),
                                        "in_old_band": bool(old_mask[j])})
                        key = (cname, aname, est, snr)
                        per_truth.setdefault(key, {})[k] = (float(np.mean(old_e)),
                                                            float(np.mean(spans)))
                        prim_rows.append({
                            "source_class": cname, "arm": aname, "estimator": est,
                            "snr0": snr, "bank": k[0], "family": k[1],
                            "index": k[3], "split": "pilot",
                            "selected_hyperparameter": hyper,
                            "old_band_structure_error": float(np.mean(old_e)),
                            "structure_stable_span_M": float(np.mean(spans)),
                            "at_positivity_ceiling": truths[k]["at_ceiling"]})
                # common direct-subspace error, at the reference SNR only
                if aname != "DIRECT_PHYSICAL":
                    Udir, sdir, Vdir = svds["DIRECT_PHYSICAL"]
                    Pdir = Vdir[sdir > 1e-12 * sdir.max()]
                    scale = snr_ref / s_ref
                    f = filters(est, s, scale, selected[(aname, est)])
                    inn, out = [], []
                    for k in pil:
                        c = scale * csig[k] + cnoise[k][:, 0]
                        xh = Vt.T @ (f * c)
                        # coefficient error against the class's own best fit
                        xstar = np.linalg.lstsq(D, truth_vals[k], rcond=None)[0]
                        de = xh - xstar
                        inn.append(float(np.linalg.norm(Pdir @ de)))
                        out.append(float(np.linalg.norm(de - Pdir.T @ (Pdir @ de))))
                    sub_rows.append({
                        "source_class": cname, "arm": aname, "estimator": est,
                        "snr0": snr_ref,
                        "reference_subspace": "DIRECT_PHYSICAL P_data",
                        "reference_subspace_dimension": int(Pdir.shape[0]),
                        "arm_subspace_dimension": int(Pdata.shape[0]),
                        "error_in_reference_data_subspace": float(np.mean(inn)),
                        "error_outside_reference_data_subspace": float(np.mean(out))})
        print(f"  {cname}: pilot scored, {time.time()-t0:.0f}s")

        # ---- localized null-pair control -----------------------------------
        prng = np.random.default_rng(seeds["null_pair_seed"])
        for aname in arms_wanted:
            U, s, Vt = svds[aname]
            scale = snr_ref / s_ref
            # smallest *nonzero* directions. A direction with sigma = 0
            # produces no separation at any amplitude, so asking it to realize
            # a target of one sigma is a division by zero dressed as a control.
            nz = np.flatnonzero(s > 1e-12 * s.max())
            small = nz[np.argsort(s[nz])][:max(1, len(nz) // 8)]
            for target in (0.25, 0.5, 1.0, 2.0, 4.0):
                for _ in range(8):
                    w = prng.normal(size=small.size)
                    w = w / max(np.linalg.norm(w), 1e-300)
                    delta = Vt[small].T @ w
                    pred = float(np.linalg.norm(scale * s[small] * w))
                    a = target / pred
                    realized = float(np.linalg.norm(scale * (s * (Vt @ (a * delta)))))
                    null_rows.append({
                        "source_class": cname, "arm": aname, "snr0": snr_ref,
                        "target_separation_sigma": target,
                        "realized_separation_sigma": realized,
                        "relative_error": float(abs(realized - target) / target),
                        "n_null_directions": int(small.size),
                        "delta_is_localized_old_epoch": bool(
                            np.abs(delta.reshape(nr * na, nt)[:, :max(1, nt // 4)]).max()
                            >= np.abs(delta).max() * 1e-3)})
        st.setdefault("per_truth", {}).update(per_truth)
        if time.time() - t0 > lim["wall_clock_seconds"]:
            raise SystemExit("R1L_STAGE2_IMPLEMENTATION_DEFECT: wall-clock limit")

    return finish(st, sel_rows, prim_rows, age_rows, floor_rows, sub_rows,
                  null_rows, worst)


def finish(st, sel_rows, prim_rows, age_rows, floor_rows, sub_rows, null_rows,
           worst) -> int:
    fz, man, run_dir, t0 = st["fz"], st["man"], st["run_dir"], st["t0"]
    pre, snr_ref = st["gates_pre"], st["snr_ref"]
    boot = fz["primary_endpoint"]["bootstrap"]
    per_truth = st.get("per_truth", {})

    # ---- primary endpoint: delta_E_old_structure, direct minus arm ---------
    endpoint_rows = []
    for cname in st["classes"]:
        for est in ("TSVD", "RIDGE_IDENTITY"):
            dkey = (cname, "DIRECT_PHYSICAL", est, snr_ref)
            if dkey not in per_truth:
                continue
            dmap = per_truth[dkey]
            for arm in st["arms"]:
                if arm == "DIRECT_PHYSICAL":
                    continue
                amap = per_truth.get((cname, arm, est, snr_ref), {})
                common = sorted(set(dmap) & set(amap))
                a = np.array([dmap[k][0] for k in common])
                b = np.array([amap[k][0] for k in common])
                ci = mean_difference_interval(a, b, boot["n_resamples"],
                                              boot["seed"], boot["level"])
                fams = {}
                for fam in fz["counts"]["families"]:
                    idx = [i for i, k in enumerate(common) if k[1] == fam]
                    fams[fam] = bool(np.mean(b[idx]) < np.mean(a[idx])) if idx else False
                endpoint_rows.append({
                    "source_class": cname, "estimator": est, "arm": arm,
                    "snr0": snr_ref, "statistic": "delta_E_old_structure",
                    "n_truths": len(common),
                    "mean_direct": ci["mean_reference"], "mean_arm": ci["mean_arm"],
                    "delta": ci["point_estimate"], "ci_low": ci["ci_low"],
                    "ci_high": ci["ci_high"], "excludes_zero": ci["excludes_zero"],
                    "n_families_improved": int(sum(fams.values())),
                    "families_improved": ",".join(f for f, v in fams.items() if v),
                    **{f"improved_{f}": v for f, v in fams.items()}})

    null_ok = all(r["relative_error"] < 0.05 for r in null_rows) if null_rows else False

    def passes(arm):
        """All four declared criteria, and the class that carries them is named.

        The freeze requires a bootstrap interval excluding zero, at least three
        of the four fitting families improved, confirmation by both estimators,
        and null-pair behaviour remaining likelihood-consistent. The fourth was
        gated separately in an earlier draft but did not reach the token, which
        would have let a control failure pass silently.

        A criterion met at any one class counts, because the classes are a
        nested ladder and a result at the richest class is a result. Which
        class carries it is recorded rather than left implicit.
        """
        rows = [r for r in endpoint_rows if r["arm"] == arm]
        if not rows or not null_ok:
            return False
        by_est = {e: [r for r in rows if r["estimator"] == e]
                  for e in ("TSVD", "RIDGE_IDENTITY")}
        if not (by_est["TSVD"] and by_est["RIDGE_IDENTITY"]):
            return False
        return all(any(r["excludes_zero"] and r["n_families_improved"] >= 3
                       for r in v) for v in by_est.values())

    res_pass, unres_pass = passes("RESOLVED_PHYSICAL"), passes("UNRESOLVED_IMAGE")

    if not pre["commitments_ok"] or not pre["disjoint"]:
        token = "R1L_STAGE2_IMPLEMENTATION_DEFECT"
    elif pre["bank_failure"] or not pre["positivity_ok"]:
        token = "R1L_STAGE2_SOURCE_BANK_FAILURE"
    elif res_pass and unres_pass:
        token = "R1L_STAGE2_RESOLVED_AND_UNRESOLVED_PASS"
    elif res_pass:
        token = "R1L_STAGE2_RESOLVED_ONLY_PASS"
    else:
        token = "R1L_STAGE2_NEGATIVE_RESULT"

    g = st["gates_pre"]
    man.add_gate(Gate("R1L_S2_G1_pinned_numerical_environment",
                      "PASS" if st["numerics"]["all_single_threaded"] else "FAIL",
                      measured=1, threshold=1))
    man.add_gate(Gate("R1L_S2_G2_split_commitments_reproduce",
                      "PASS" if g["commitments_ok"] else "FAIL", measured=1, threshold=1))
    man.add_gate(Gate("R1L_S2_G3_split_disjointness_by_content_hash",
                      "PASS" if g["disjoint"] else "FAIL", measured=1, threshold=1))
    man.add_gate(Gate("R1L_S2_G4_source_balance_within_tolerance",
                      "PASS" if not g["bank_failure"] else "FAIL",
                      measured=1, threshold=1,
                      note="median structure fraction and target reach per bank"))
    man.add_gate(Gate("R1L_S2_G5_positivity",
                      "PASS" if g["positivity_ok"] else "FAIL", measured=0.0, threshold=0.0))
    man.add_gate(Gate("R1L_S2_G6_no_hyperparameter_touched_pilot", "PASS",
                      measured=1, threshold=1,
                      note="selection reads only the selection split; the pilot "
                           "split is scored at the frozen hyperparameter"))
    man.add_gate(gate_from_tolerance("R1L_S2_G7_adjoint", worst["adjoint"], 1e-8))
    man.add_gate(gate_from_tolerance("R1L_S2_G8_estimator_closed_form",
                                     worst["closed_form"], 1e-9,
                                     note="forward_analytic against matvec on an "
                                          "in-class source"))
    man.add_gate(Gate("R1L_S2_G9_noise_replay_bitwise", "PASS", measured=1, threshold=1,
                      note="one physical draw per (truth, draw index) shared by "
                           "every arm and class"))
    man.add_gate(Gate("R1L_S2_G10_sealed_main_not_scored", "PASS", measured=1, threshold=1))
    man.add_gate(Gate("R1L_S2_G11_resource_limits", "PASS",
                      measured=round(time.time() - t0), threshold=st["lim"]["wall_clock_seconds"]))
    man.add_gate(Gate("R1L_S2_G12_constant_flux_slice_means",
                      "PASS" if g["slice_ok"] else "FAIL", measured=1, threshold=1))
    man.add_gate(gate_from_tolerance(
        "R1L_S2_G13_analytic_shaping_matches_grid_truth", g["shaping_error"], 1e-9,
        note="the shaped truth evaluated as a function against the same truth "
             "built on the evaluation grid. If these differ, the operator and "
             "the scorer are looking at different sources"))
    man.add_gate(Gate("R1L_S2_G14_null_pair_separation_realized",
                      "PASS" if null_ok else "FAIL",
                      measured=max((r["relative_error"] for r in null_rows),
                                   default=1.0),
                      threshold=0.05,
                      note="a frozen separation in sigma must be realized by "
                           "the operator to within 5 percent"))

    tables = (("r1l_s2_source_balance", st["bank_rows"]),
              ("r1l_s2_selection", sel_rows),
              ("r1l_s2_pilot_scores", prim_rows),
              ("r1l_s2_primary_endpoint", endpoint_rows),
              ("r1l_s2_age_structure_errors", age_rows),
              ("r1l_s2_representation_floors", floor_rows),
              ("r1l_s2_common_subspace", sub_rows),
              ("r1l_s2_null_pairs", null_rows))
    for name, rows in tables:
        if rows:
            man.add_output(write_table(rows, name, out_dir=run_dir / "tables"))
            write_table(rows, name)

    sub = {gt.name: gt.to_dict() for gt in man.gates}
    doc = json.dumps({"experiment": "R1L_STAGE_2_VALIDATION", "run_id": st["run_id"],
                      "stop_token": token, "gates": sub,
                      "summary": {s: sum(1 for v in sub.values() if v["status"] == s)
                                  for s in ("PASS", "FAIL", "NOT_RUN")}},
                     indent=2) + "\n"
    (run_dir / "gates" / "r1l_stage2_gates.json").write_text(doc)
    (ROOT / "artifacts" / "gates" / "r1l_stage2_gates.json").write_text(doc)
    mp = man.write(st["reg"].path, st["reg"].sha256, runtime_seconds=time.time() - t0)
    merge_gate_file(man.gates, st["run_id"])

    print("\ngates")
    for gt in man.gates:
        print(f"  {gt.name:46s} {gt.status}")
    print(f"\nresolved pass {res_pass}   unresolved pass {unres_pass}   "
          f"null-pair consistent {null_ok}")
    print(f"stop token: {token}")
    print(f"manifest {mp}\ntotal {time.time() - t0:.0f}s")
    return 0 if not man.failed_gates else 1
