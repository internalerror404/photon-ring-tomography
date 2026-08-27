#!/usr/bin/env python3
"""Stage 2R-A -- recompute the stage-2 endpoint correctly from existing artifacts.

REVIEWER_RULING_R1L_STAGE2_011 item 7. No new source truth is generated. The
committed banks are regenerated from their frozen seeds and checked against the
content hashes already recorded, so the truths here are provably the same
objects stage 2 scored; everything else is read from the stage-2 tables.

Nine corrections, each because the stage-2 endpoint answered a slightly
different question than the freeze asked:

  the secondary bank is excluded -- it was pooled into the primary despite the
  freeze forbidding it;
  every primary bank is reported separately, since pooling hides a bank that
  disagrees;
  aggregation is equal-weight over bank-family cells, so a bank with more
  usable truths cannot dominate;
  TSVD and ridge must confirm on the *same* class, not on any class each;
  effects are normalized paired relative reductions, because an absolute
  difference of 8e-04 on an error of 8.4 is not a result;
  representation floors are age-local and exact, so the span criterion can be
  compared against what is actually reachable at each age;
  stable spans use the canonical anchored quantile endpoint;
  the direct arm gets its own common-subspace row rather than being only the
  reference;
  and the disposition is recomputed under the materiality standard of item 10.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from phrt.numerics import pin, record as numerics_record, require_single_threaded

pin()

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from phrt.attestation import attest  # noqa: E402
from phrt.config import load_registry  # noqa: E402
from phrt.io.manifests import Gate, RunManifest, make_run_id, merge_gate_file  # noqa: E402
from phrt.io.tables import write_table  # noqa: E402
from phrt.metrics.age_error import age_window_weights  # noqa: E402
from phrt.metrics.cluster_bootstrap import _counts  # noqa: E402
from phrt.metrics.level_structure import level_subspace  # noqa: E402
from phrt.metrics.scoring import evaluation_grid  # noqa: E402
from phrt.sources.localized_basis import LocalizedBasis  # noqa: E402
from phrt.sources.structural import (BUILDERS, constant_flux,  # noqa: E402
                                     shaped_renderer, structure_balanced,
                                     structure_fraction)

FZ = ROOT / "artifacts" / "configs" / "R1L_STAGE2_VALIDATION_ACTIVATION_010.json"
R1 = ROOT / "artifacts" / "configs" / "R1_MAIN_FREEZE.json"
TAB = ROOT / "artifacts" / "tables"
SECONDARY = "baseline_one_positive"
CLASSDEF = {"L224": (4, 7, 8), "L448": (4, 7, 16), "L1056": (6, 11, 16)}
N_T = 40
EPS, QUANT = 0.25, 0.95
MATERIALITY = {"median_relative_reduction": 0.10, "ci_low_relative": 0.05,
               "min_families": 3, "all_primary_banks_positive": True}


def truth_seed(bank, family, split, i, base):
    payload = json.dumps({"bank": bank, "family": family, "split": split,
                          "n": 8, "seed": base}, sort_keys=True).encode()
    return int(hashlib.sha256(payload + f"|{i}".encode()).hexdigest()[:16], 16) % (2 ** 63)


def paired_relative(direct: np.ndarray, arm: np.ndarray, cell: np.ndarray,
                    n_resamples: int, seed: int, level: float = 0.95) -> dict:
    """Equal-weight bank-family aggregation of the paired relative reduction.

    Per truth the statistic is ``(E_direct - E_arm) / E_direct``, which is what
    a reader means by "how much better". Truths are averaged within each
    bank-family cell first and the cells are then weighted equally, so a cell
    with more usable truths cannot outvote the others. The bootstrap resamples
    truths, not cells, so the interval still reflects truth-level variability.
    """
    d, a = np.asarray(direct, float), np.asarray(arm, float)
    rel = (d - a) / np.maximum(np.abs(d), 1e-300)
    cells = np.asarray(cell)
    uniq = np.unique(cells)
    onehot = np.stack([(cells == c).astype(float) for c in uniq])
    per_cell = (onehot @ rel) / np.maximum(onehot.sum(axis=1), 1.0)
    w = _counts(rel.size, n_resamples, seed) / rel.size
    boot_cell = (w * rel) @ onehot.T / np.maximum(onehot.sum(axis=1), 1.0)[None, :]
    boot = boot_cell.mean(axis=1) * rel.size
    lo, hi = np.percentile(boot, [100 * (1 - level) / 2, 100 * (1 + level) / 2])
    return {"point_estimate": float(per_cell.mean()),
            "median_per_truth": float(np.median(rel)),
            "ci_low": float(lo), "ci_high": float(hi),
            "excludes_zero": bool(lo > 0.0), "n_truths": int(rel.size),
            "n_cells": int(uniq.size), "level": level}


def main() -> int:
    t0 = time.time()
    numerics = require_single_threaded()
    started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    fz = json.loads(FZ.read_text())
    r1 = json.loads(R1.read_text())
    reg = load_registry()
    seeds = fz["seeds"]
    snr_ref = float(fz["reference_snr"])
    boot = fz["primary_endpoint"]["bootstrap"]
    old_b = float(fz["primary_endpoint"]["old_band_boundary_M"])
    families = fz["counts"]["families"]
    primary_banks = [b for b in fz["counts"]["banks"] if b != SECONDARY]

    pilot = pd.read_parquet(TAB / "r1l_s2_pilot_scores.parquet")
    ages_tab = pd.read_parquet(TAB / "r1l_s2_age_structure_errors.parquet")
    balance = pd.read_parquet(TAB / "r1l_s2_source_balance.parquet")
    sub_old = pd.read_parquet(TAB / "r1l_s2_common_subspace.parquet")
    nulls = pd.read_parquet(TAB / "r1l_s2_null_pairs.parquet")

    run_id = make_run_id("R1LS2RA", reg.sha256)
    run_dir = ROOT / "artifacts" / "runs" / run_id
    (run_dir / "tables").mkdir(parents=True, exist_ok=True)
    (run_dir / "gates").mkdir(parents=True, exist_ok=True)
    man = RunManifest(run_id=run_id, experiment_id="R1L_STAGE_2R_A",
                      seeds=seeds, started_at=started,
                      attestation=attest([FZ]),
                      extra={"stage": "2R-A recomputation from existing artifacts",
                             "generates_new_truths": False,
                             "secondary_bank_excluded": SECONDARY,
                             "run_dir": str(run_dir.relative_to(ROOT)),
                             "numerics": numerics_record()})
    man.add_input(FZ)

    # ---- 7a-7e: the endpoint, recomputed -----------------------------------
    p = pilot[(pilot.bank != SECONDARY) & (pilot.snr0 == snr_ref)].copy()
    p["cell"] = p.bank + "|" + p.family
    end_rows = []
    for cname in sorted(p.source_class.unique()):
        for est in sorted(p.estimator.unique()):
            g = p[(p.source_class == cname) & (p.estimator == est)]
            d = g[g.arm == "DIRECT_PHYSICAL"].set_index(["bank", "family", "index"])
            for arm in sorted(g.arm.unique()):
                if arm == "DIRECT_PHYSICAL":
                    continue
                a = g[g.arm == arm].set_index(["bank", "family", "index"])
                common = d.index.intersection(a.index)
                dv = d.loc[common, "old_band_structure_error"].to_numpy()
                av = a.loc[common, "old_band_structure_error"].to_numpy()
                cells = np.array([f"{b}|{f}" for b, f, _ in common])
                # pooled over the primary banks
                r = paired_relative(dv, av, cells, boot["n_resamples"],
                                    boot["seed"], boot["level"])
                fam_ok = {}
                for fam in families:
                    m = np.array([c.endswith("|" + fam) for c in cells])
                    fam_ok[fam] = bool(m.any() and np.mean(av[m]) < np.mean(dv[m]))
                bank_pos = {}
                for bk in primary_banks:
                    m = np.array([c.startswith(bk + "|") for c in cells])
                    bank_pos[bk] = bool(m.any() and np.mean(av[m]) < np.mean(dv[m]))
                end_rows.append({
                    "source_class": cname, "estimator": est, "arm": arm,
                    "snr0": snr_ref, "scope": "primary_banks_pooled",
                    "bank": "ALL_PRIMARY",
                    "mean_direct": float(dv.mean()), "mean_arm": float(av.mean()),
                    "relative_reduction": r["point_estimate"],
                    "median_relative_reduction": r["median_per_truth"],
                    "ci_low": r["ci_low"], "ci_high": r["ci_high"],
                    "excludes_zero": r["excludes_zero"],
                    "n_truths": r["n_truths"], "n_cells": r["n_cells"],
                    "n_families_improved": int(sum(fam_ok.values())),
                    "n_primary_banks_positive": int(sum(bank_pos.values())),
                    "all_primary_banks_positive": bool(all(bank_pos.values())),
                    **{f"improved_{f}": v for f, v in fam_ok.items()},
                    **{f"positive_{b}": v for b, v in bank_pos.items()}})
                # 7b: every primary bank separately
                for bk in primary_banks:
                    m = np.array([c.startswith(bk + "|") for c in cells])
                    rb = paired_relative(dv[m], av[m], cells[m],
                                         boot["n_resamples"], boot["seed"],
                                         boot["level"])
                    end_rows.append({
                        "source_class": cname, "estimator": est, "arm": arm,
                        "snr0": snr_ref, "scope": "single_bank", "bank": bk,
                        "mean_direct": float(dv[m].mean()),
                        "mean_arm": float(av[m].mean()),
                        "relative_reduction": rb["point_estimate"],
                        "median_relative_reduction": rb["median_per_truth"],
                        "ci_low": rb["ci_low"], "ci_high": rb["ci_high"],
                        "excludes_zero": rb["excludes_zero"],
                        "n_truths": rb["n_truths"], "n_cells": rb["n_cells"],
                        "n_families_improved": int(sum(
                            1 for f in families
                            if np.mean(av[m & np.array([c.endswith('|' + f)
                                                        for c in cells])])
                            < np.mean(dv[m & np.array([c.endswith('|' + f)
                                                       for c in cells])])
                            if (m & np.array([c.endswith('|' + f)
                                              for c in cells])).any())),
                        "n_primary_banks_positive": None,
                        "all_primary_banks_positive": None})
    print(f"endpoint recomputed, {len(end_rows)} rows, {time.time()-t0:.0f}s")

    # ---- 7f: exact age-local oracle representation floors -------------------
    r_in = float(r1["physical_model"]["r_inner_M"])
    r_out = float(r1["physical_model"]["r_outer_M"])
    t_lo = float(r1["observation"]["basis_t_min"])
    t_hi = float(r1["observation"]["basis_t_max"])
    step = float(fz["coprimary_endpoint"]["age_grid_step_M"])
    a_max = float(r1["metrics"]["age_grid_max_M"])
    ages = np.arange(0.0, a_max + 1e-9, step)
    gr, gp, gt = evaluation_grid(r_in, r_out, t_lo, t_hi, n_t=N_T)
    t_axis = np.linspace(t_lo, t_hi, N_T)
    t_index = np.clip(np.searchsorted(t_axis, gt), 0, N_T - 1)
    windows = np.array([age_window_weights(gt, float(a), 3.0) for a in ages])
    level = level_subspace(gt, t_lo, t_hi, 8)
    spin = float(r1["physical_model"]["spin"])
    targets = {"structure_balanced_050": 0.50, "structure_balanced_080": 0.80}

    stored_hash = {(r.bank, r.family, r.split, r.index): r.content_hash
                   for r in balance.itertuples()}
    hash_ok, floor_rows, truth_vals = True, [], {}
    for bank in primary_banks:
        for fam in families:
            for i in range(fz["counts"]["truths_per_bank_family_split"]):
                s = truth_seed(bank, fam, "pilot", i, seeds["bank_seed"])
                mv = BUILDERS[fam](np.random.default_rng(s), spin, 29.989231533549642)
                hash_ok &= (stored_hash.get((bank, fam, "pilot", i))
                            == mv.content_hash)
                raw = mv(gr, gp, gt)
                if bank == "constant_flux_structural":
                    v, _ = constant_flux(raw, t_index, N_T, target_mean=1.0)
                    off = 0.0
                else:
                    v, dg = structure_balanced(raw, level, targets[bank])
                    off = float(dg.get("baseline", 0.0))
                truth_vals[(bank, fam, i)] = v
    for cname, (nr, na, nt) in CLASSDEF.items():
        basis = LocalizedBasis(r_in, r_out, t_lo, t_hi, nr, na, nt)
        Q, _ = np.linalg.qr(basis.design(gr, gp, gt))
        for (bank, fam, i), v in truth_vals.items():
            res = v - Q @ (Q.T @ v)
            sres = res - level @ (level.T @ res)
            sv = v - level @ (level.T @ v)
            num = np.sqrt(np.einsum("ap,p->a", windows ** 2, sres ** 2))
            den = np.sqrt(np.einsum("ap,p->a", windows ** 2, sv ** 2))
            rel = num / np.maximum(den, 1e-300)
            for j, a in enumerate(ages):
                floor_rows.append({
                    "source_class": cname, "bank": bank, "family": fam,
                    "index": i, "retarded_age": float(a),
                    "oracle_floor_absolute": float(num[j]),
                    "oracle_floor_normalized": float(rel[j]),
                    "truth_structure_norm": float(den[j]),
                    "reachable_at_epsilon": bool(rel[j] <= EPS),
                    "in_old_band": bool(a >= old_b)})
        print(f"  {cname}: oracle floors, {time.time()-t0:.0f}s")

    # ---- 7g: canonical ensemble stable spans -------------------------------
    span_rows = []
    at = ages_tab[ages_tab.bank != SECONDARY]
    for (cname, arm), g in at.groupby(["source_class", "arm"]):
        piv = g.pivot_table(index=["bank", "family", "index"],
                            columns="retarded_age",
                            values="structure_error_normalized")
        A = np.asarray(sorted(piv.columns), float)
        E = piv[sorted(piv.columns)].to_numpy()
        run_max = np.maximum.accumulate(E, axis=1)
        frac = (run_max <= EPS).mean(axis=0)
        ok = frac >= QUANT
        T = float(A[ok].max()) if ok.any() and ok[0] else 0.0
        span_rows.append({
            "source_class": cname, "arm": arm, "epsilon": EPS, "quantile": QUANT,
            "definition": "T_stable_anchor: sup{T : Pr[sup_{0<=a<=T} E(a) "
                          "<= epsilon] >= q}, supremum inside the probability",
            "T_stable_anchor_M": T, "a_anchor_M": 0.0,
            "L_stable_anchor_M": T,
            "n_truths": int(E.shape[0]),
            "pass_fraction_at_youngest_age": float(frac[0]),
            "slice": "TSVD, SNR0=100, draw 0 -- the ensemble stored by stage 2"})

    # ---- 7h: the direct arm's own common-subspace row ----------------------
    sub_rows = [r._asdict() for r in sub_old.itertuples(index=False)]
    for cname in sorted(sub_old.source_class.unique()):
        for est in sorted(sub_old.estimator.unique()):
            ref = sub_old[(sub_old.source_class == cname)
                          & (sub_old.estimator == est)]
            if ref.empty:
                continue
            sub_rows.append({
                "source_class": cname, "arm": "DIRECT_PHYSICAL", "estimator": est,
                "snr0": snr_ref,
                "reference_subspace": "DIRECT_PHYSICAL P_data",
                "reference_subspace_dimension":
                    int(ref.reference_subspace_dimension.iloc[0]),
                "arm_subspace_dimension":
                    int(ref.reference_subspace_dimension.iloc[0]),
                "error_in_reference_data_subspace": None,
                "error_outside_reference_data_subspace": None,
                "note": "the direct arm is the reference subspace, so its own "
                        "projection is the identity and the split is not "
                        "informative. The row exists so the table cannot be "
                        "read as if the direct arm had been omitted for a "
                        "reason"})

    return finish(man, run_dir, run_id, reg, t0, end_rows, floor_rows, span_rows,
                  sub_rows, nulls, hash_ok, primary_banks, numerics, fz)


def finish(man, run_dir, run_id, reg, t0, end_rows, floor_rows, span_rows,
           sub_rows, nulls, hash_ok, primary_banks, numerics, fz) -> int:
    end = pd.DataFrame(end_rows)
    floors = pd.DataFrame(floor_rows)
    null_ok = bool((nulls.relative_error < 0.05).all())

    pooled = end[end.scope == "primary_banks_pooled"]

    def material(arm, cname):
        g = pooled[(pooled.arm == arm) & (pooled.source_class == cname)]
        if set(g.estimator) < {"TSVD", "RIDGE_IDENTITY"}:
            return False, {}
        rec = {}
        for est in ("TSVD", "RIDGE_IDENTITY"):
            r = g[g.estimator == est].iloc[0]
            rec[est] = {
                "median_relative_reduction": float(r.median_relative_reduction),
                "ci_low": float(r.ci_low),
                "n_families_improved": int(r.n_families_improved),
                "all_primary_banks_positive": bool(r.all_primary_banks_positive),
                "meets": bool(
                    r.median_relative_reduction >= MATERIALITY["median_relative_reduction"]
                    and r.ci_low >= MATERIALITY["ci_low_relative"]
                    and r.n_families_improved >= MATERIALITY["min_families"]
                    and r.all_primary_banks_positive)}
        return (all(v["meets"] for v in rec.values()) and null_ok), rec

    verdicts = {}
    for arm in ("RESOLVED_PHYSICAL", "UNRESOLVED_IMAGE", "TOTAL_FLUX"):
        for cname in sorted(pooled.source_class.unique()):
            ok, rec = material(arm, cname)
            verdicts[f"{arm}|{cname}"] = {"material": ok, "detail": rec}
    res_any = any(v["material"] for k, v in verdicts.items()
                  if k.startswith("RESOLVED_PHYSICAL"))
    unres_any = any(v["material"] for k, v in verdicts.items()
                    if k.startswith("UNRESOLVED_IMAGE"))
    token = ("R1L_STAGE2R_A_MATERIAL_RESOLVED_AND_UNRESOLVED" if res_any and unres_any
             else "R1L_STAGE2R_A_MATERIAL_RESOLVED_ONLY" if res_any
             else "R1L_STAGE2R_A_NO_MATERIAL_EFFECT")

    reach = float(floors.reachable_at_epsilon.mean())
    man.add_gate(Gate("R1L_2RA_G1_no_new_truths", "PASS", measured=0, threshold=0,
                      note="banks regenerated from frozen seeds only"))
    man.add_gate(Gate("R1L_2RA_G2_truth_content_hashes_match",
                      "PASS" if hash_ok else "FAIL", measured=int(hash_ok),
                      threshold=1,
                      note="every regenerated truth hashes to the value stage 2 "
                           "recorded, so these are the same objects"))
    man.add_gate(Gate("R1L_2RA_G3_secondary_bank_excluded", "PASS",
                      measured=0, threshold=0,
                      note=f"{SECONDARY} contributes no truth to any endpoint row"))
    man.add_gate(Gate("R1L_2RA_G4_pinned_numerical_environment",
                      "PASS" if numerics["all_single_threaded"] else "FAIL",
                      measured=1, threshold=1))
    man.add_gate(Gate("R1L_2RA_G5_null_controls",
                      "PASS" if null_ok else "FAIL",
                      measured=float(nulls.relative_error.max()), threshold=0.05))

    for name, rows in (("r1l_2ra_endpoint", end_rows),
                       ("r1l_2ra_oracle_floor_curves", floor_rows),
                       ("r1l_2ra_stable_spans", span_rows),
                       ("r1l_2ra_common_subspace", sub_rows)):
        man.add_output(write_table(rows, name, out_dir=run_dir / "tables"))
        write_table(rows, name)

    sub = {g.name: g.to_dict() for g in man.gates}
    doc = json.dumps({"experiment": "R1L_STAGE_2R_A", "run_id": run_id,
                      "stop_token": token,
                      "materiality_standard": MATERIALITY,
                      "verdicts": verdicts,
                      "epsilon_reachable_fraction_of_age_cells": reach,
                      "gates": sub,
                      "summary": {s: sum(1 for v in sub.values()
                                         if v["status"] == s)
                                  for s in ("PASS", "FAIL", "NOT_RUN")}},
                     indent=2, default=str) + "\n"
    (run_dir / "gates" / "r1l_2ra_gates.json").write_text(doc)
    (ROOT / "artifacts" / "gates" / "r1l_2ra_gates.json").write_text(doc)
    mp = man.write(reg.path, reg.sha256, runtime_seconds=time.time() - t0)
    merge_gate_file(man.gates, run_id)

    print("\ngates")
    for g in man.gates:
        print(f"  {g.name:44s} {g.status}")
    print(f"\nage cells where epsilon={EPS} is reachable at all: {reach*100:.1f}%")
    print(f"corrected disposition: {token}")
    print(f"manifest {mp}\ntotal {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
