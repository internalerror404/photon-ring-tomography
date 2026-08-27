#!/usr/bin/env python3
"""R1L stage 2 -- structure-first validation pilot.

REVIEWER_RULING_R1L_REPRODUCIBILITY_009 items 7 to 11, under the frozen
R1L_STAGE2_VALIDATION_ACTIVATION_010.

Validation, not a held-out result: hyperparameters are chosen here, on the
selection split, and the reported endpoint is computed on the pilot split, which
no hyperparameter ever saw. The sealed main bank is proposed and committed and
is not generated through any operator.

The endpoint is structural by construction. Truths enter the operator
analytically -- sampled wherever the rays land, never projected into the class
first -- so the representation floor is a measured quantity rather than zero,
and the level component is removed by the R0C projector before the old-band
error is formed, so a recovered spatial mean cannot be counted as recovered
morphology.
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

from phrt.numerics import pin, record as numerics_record, require_single_threaded

pin()

import numpy as np  # noqa: E402

from phrt.attestation import attest  # noqa: E402
from phrt.config import load_registry  # noqa: E402
from phrt.geometry.raymap import read  # noqa: E402
from phrt.geometry.sampling import common_count, stratified_subsample  # noqa: E402
from phrt.io.manifests import Gate, RunManifest, gate_from_tolerance, make_run_id  # noqa: E402
from phrt.io.tables import write_table  # noqa: E402
from phrt.metrics.age_error import age_window_weights  # noqa: E402
from phrt.metrics.cluster_bootstrap import mean_difference_interval  # noqa: E402
from phrt.metrics.level_structure import level_subspace  # noqa: E402
from phrt.metrics.scoring import evaluation_grid  # noqa: E402
from phrt.operators.physical import PhysicalOperator  # noqa: E402
from phrt.sources.localized_basis import LocalizedBasis  # noqa: E402
from phrt.sources.physical_basis import PhysicalBasis  # noqa: E402
from phrt.sources.structural import (BUILDERS, constant_flux,  # noqa: E402
                                     max_structure_fraction, shaped_renderer,
                                     slice_means, structure_balanced,
                                     structure_fraction)

FZ = ROOT / "artifacts" / "configs" / "R1L_STAGE2_VALIDATION_ACTIVATION_010.json"
R1 = ROOT / "artifacts" / "configs" / "R1_MAIN_FREEZE.json"
CLASSDEF = {"L224": (4, 7, 8), "L448": (4, 7, 16), "L1056": (6, 11, 16)}
N_T = 40


# ---------------------------------------------------------------- banks
def truth_seed(bank: str, family: str, split: str, i: int, base: int) -> int:
    payload = json.dumps({"bank": bank, "family": family, "split": split,
                          "n": 8, "seed": base}, sort_keys=True).encode()
    h = hashlib.sha256(payload + f"|{i}".encode()).hexdigest()
    return int(h[:16], 16) % (2 ** 63)


def commitment(bank: str, family: str, split: str, base: int) -> str:
    return hashlib.sha256(json.dumps(
        {"bank": bank, "family": family, "split": split, "n": 8,
         "seed": base}, sort_keys=True).encode()).hexdigest()


def shape_bank(bank: str, raw: np.ndarray, level: np.ndarray,
               t_index: np.ndarray, targets: dict) -> tuple[np.ndarray, dict]:
    """Turn one family render into the declared bank's truth on the eval grid."""
    if bank == "constant_flux_structural":
        v, d = constant_flux(raw, t_index, N_T, target_mean=1.0)
        d["bank_kind"] = "constant_flux"
        return v, d
    if bank == "baseline_one_positive":
        v = raw + 1.0
        return v, {"bank_kind": "baseline_one", "baseline": 1.0,
                   "achievable": True, "achieved": structure_fraction(v, level),
                   "min_value": float(v.min())}
    tgt = targets[bank]
    v, d = structure_balanced(raw, level, tgt)
    d["bank_kind"] = "structure_balanced"
    d["target"] = tgt
    return v, d


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--classes", default="")
    args = ap.parse_args()
    t0 = time.time()
    numerics = require_single_threaded()
    started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    fz = json.loads(FZ.read_text())
    r1 = json.loads(R1.read_text())
    reg = load_registry()
    lim = fz["resource_limits"]
    seeds = fz["seeds"]
    banks = fz["counts"]["banks"]
    families = fz["counts"]["families"]
    splits = fz["counts"]["splits"]
    per_cell = fz["counts"]["truths_per_bank_family_split"]
    n_draws = fz["noise"]["draws_per_truth"]
    snr_grid = [float(s) for s in fz["snr_grid"]]
    snr_ref = float(fz["reference_snr"])
    old_b = float(fz["primary_endpoint"]["old_band_boundary_M"])
    arms_wanted = fz["scope"]["arms"]
    targets = {"structure_balanced_050": 0.50, "structure_balanced_080": 0.80}
    tol = fz["source_balance_tolerances"]
    grids = {"TSVD": fz["estimators"]["TSVD"]["grid"],
             "RIDGE_IDENTITY": fz["estimators"]["RIDGE_IDENTITY"]["grid"]}

    spin = float(r1["physical_model"]["spin"])
    r_in = float(r1["physical_model"]["r_inner_M"])
    r_out = float(r1["physical_model"]["r_outer_M"])
    t_lo = float(r1["observation"]["basis_t_min"])
    t_hi = float(r1["observation"]["basis_t_max"])
    t_obs = np.asarray(r1["observation"]["observer_times_M"], float)
    step = float(fz["coprimary_endpoint"]["age_grid_step_M"])
    a_max = float(r1["metrics"]["age_grid_max_M"])
    half = 3.0
    ages = np.arange(0.0, a_max + 1e-9, step)

    wanted = set(args.classes.split(",")) if args.classes else set(CLASSDEF)
    classes = {k: v for k, v in CLASSDEF.items() if k in wanted}

    run_id = make_run_id("R1LS2", reg.sha256)
    run_dir = ROOT / "artifacts" / "runs" / run_id
    (run_dir / "tables").mkdir(parents=True, exist_ok=True)
    (run_dir / "gates").mkdir(parents=True, exist_ok=True)
    man = RunManifest(run_id=run_id, experiment_id="R1L_STAGE_2_VALIDATION",
                      seeds=seeds, started_at=started,
                      attestation=attest([FZ, R1]),
                      extra={"stage": "validation_pilot",
                             "classes": list(classes), "arms": arms_wanted,
                             "run_dir": str(run_dir.relative_to(ROOT)),
                             "numerics": numerics_record()})
    man.add_input(reg.path)
    man.add_input(FZ)

    # ---- commitments reproduce before anything is scored -------------------
    committed = fz["split_rule"]["commitments"]
    recomputed = {f"{b}|{f}|{s}": commitment(b, f, s, seeds["bank_seed"])
                  for b in banks for f in families for s in splits}
    commitments_ok = recomputed == committed

    # ---- rays and the shared evaluation grid -------------------------------
    rng = np.random.default_rng(seeds["subsample_seed"])
    raw_maps = [read(ROOT / "artifacts" / "raymaps" / f"a050_i050_n{n}_core.h5")
                for n in r1["physical_model"]["orders"]]
    base = common_count([stratified_subsample(rm, int(r1["observation"]["rays_per_order"]),
                                              rng) for rm in raw_maps], rng)
    gr, gp, gt = evaluation_grid(r_in, r_out, t_lo, t_hi, n_t=N_T)
    t_axis = np.linspace(t_lo, t_hi, N_T)
    t_index = np.clip(np.searchsorted(t_axis, gt), 0, N_T - 1)
    windows = np.array([age_window_weights(gt, float(a), half) for a in ages])
    old_mask = ages >= old_b

    # ---- the banks, built once and shared by every class -------------------
    bank_rows, truths, shaping_error = [], {}, 0.0
    for bank in banks:
        for fam in families:
            for split in splits:
                for i in range(per_cell):
                    s = truth_seed(bank, fam, split, i, seeds["bank_seed"])
                    trng = np.random.default_rng(s)
                    mv = BUILDERS[fam](trng, spin, 29.989231533549642)
                    key = (bank, fam, split, i)
                    truths[key] = {"movie": mv, "seed": s}
    # the level projector is class-independent: it is spanned by spatially
    # uniform fields, which every class contains
    level = level_subspace(gt, t_lo, t_hi, 8)
    for key, rec in truths.items():
        bank, fam, split, i = key
        raw = rec["movie"](gr, gp, gt)
        v, diag = shape_bank(bank, raw, level, t_index, targets)
        ceil = max_structure_fraction(raw, level)
        sm = slice_means(v, t_index, N_T)
        # The operator samples wherever the rays land, so the shaped truth has
        # to exist as a function, not only as grid values. Building it and then
        # checking it reproduces the grid values is what keeps the data and the
        # scored truth the same object -- an earlier draft pushed the *raw*
        # family render through the operator while scoring against the shaped
        # one, which would have measured the shaping as reconstruction error.
        render, _sd = shaped_renderer(
            bank, rec["movie"], level @ (level.T @ raw), gr, gp, gt, t_lo, t_hi,
            offset=float(diag.get("baseline", 0.0)))
        rec["render"] = render
        chk = np.asarray(render(gr, gp, gt), float)
        rel = float(np.abs(chk - v).max() / max(np.abs(v).max(), 1e-300))
        shaping_error = max(shaping_error, rel)
        rec["values"] = v
        frac = structure_fraction(v, level)
        at_ceiling = (bank in targets) and not diag.get("achievable", True)
        rec["at_ceiling"] = bool(at_ceiling)
        bank_rows.append({
            "bank": bank, "family": fam, "split": split, "index": i,
            "truth_seed": rec["seed"], "content_hash": rec["movie"].content_hash,
            "bank_kind": diag.get("bank_kind"),
            "target_structure_fraction": diag.get("target"),
            "achieved_structure_fraction": frac,
            "level_fraction": float(np.sqrt(max(0.0, 1.0 - frac ** 2))),
            "max_structure_fraction_positivity_ceiling":
                ceil["max_structure_fraction"],
            "at_positivity_ceiling": bool(at_ceiling),
            "within_tolerance": bool(
                diag.get("target") is None
                or abs(frac - diag["target"]) <= tol["structure_fraction_absolute"]),
            "min_value": float(v.min()), "positive": bool(v.min() >= -1e-12),
            "slice_mean_max_relative_deviation":
                float(np.abs(sm / max(sm.mean(), 1e-300) - 1.0).max()),
            "baseline": diag.get("baseline"),
            "analytic_shaping_relative_error": rel,
        })

    # bank-level dispositions
    balance = {}
    for bank in banks:
        rows = [r for r in bank_rows if r["bank"] == bank]
        fr = np.array([r["achieved_structure_fraction"] for r in rows])
        reach = np.mean([r["within_tolerance"] for r in rows])
        balance[bank] = {
            "n": len(rows), "median_structure_fraction": float(np.median(fr)),
            "min_structure_fraction": float(fr.min()),
            "fraction_reaching_target": float(reach),
            "n_at_positivity_ceiling":
                int(sum(r["at_positivity_ceiling"] for r in rows)),
            "all_positive": bool(all(r["positive"] for r in rows)),
        }
    primary_banks = [b for b in banks
                     if fz["source_banks"][b]["role"].startswith("primary")]
    bank_failure = any(
        (balance[b]["median_structure_fraction"]
         < tol["baseline_dominance"]["median_structure_fraction_floor"])
        or (b in targets and balance[b]["fraction_reaching_target"]
            < tol["bank_construction_failure"]["min_fraction_of_truths_reaching_target"])
        for b in primary_banks)
    positivity_ok = all(v["all_positive"] for v in balance.values())
    cf = balance["constant_flux_structural"]
    slice_ok = max(r["slice_mean_max_relative_deviation"] for r in bank_rows
                   if r["bank"] == "constant_flux_structural") <= \
        tol["constant_flux_slice_mean_relative"]

    # split disjointness by content hash
    sel_h = {truths[k]["movie"].content_hash for k in truths if k[2] == "selection"}
    pil_h = {truths[k]["movie"].content_hash for k in truths if k[2] == "pilot"}
    disjoint = not (sel_h & pil_h)

    print(f"banks built, {len(truths)} truths, {time.time()-t0:.0f}s")
    print(f"  analytic shaping reproduces the grid truth to "
          f"{shaping_error:.2e} relative")
    for b in banks:
        v = balance[b]
        print(f"  {b:28s} median f_struct {v['median_structure_fraction']:.3f}  "
              f"reach {v['fraction_reaching_target']:.2f}  "
              f"at ceiling {v['n_at_positivity_ceiling']:3d}/{v['n']}")

    state = {"fz": fz, "man": man, "run_dir": run_dir, "run_id": run_id,
             "t0": t0, "base": base, "t_obs": t_obs, "grid": (gr, gp, gt),
             "level": level, "windows": windows, "old_mask": old_mask,
             "ages": ages, "truths": truths, "bank_rows": bank_rows,
             "balance": balance, "gates_pre": {
                 "commitments_ok": commitments_ok, "disjoint": disjoint,
                 "positivity_ok": positivity_ok, "slice_ok": slice_ok,
                 "bank_failure": bank_failure,
                 "shaping_error": shaping_error},
             "classes": classes, "snr_grid": snr_grid, "snr_ref": snr_ref,
             "grids": grids, "seeds": seeds, "n_draws": n_draws,
             "r": (r_in, r_out, t_lo, t_hi), "arms": arms_wanted,
             "numerics": numerics, "lim": lim, "reg": reg}
    np.save(run_dir / "_state_marker.npy", np.array([0]))
    return score(state)


# ------------------------------------------------------------------ scoring
def build_arms(base, names):
    ones = np.ones((1, len(base)))
    cfg = {"DIRECT_PHYSICAL": dict(orders=[base[0]]),
           "RESOLVED_PHYSICAL": dict(orders=base),
           "UNRESOLVED_IMAGE": dict(orders=base, mixer=ones),
           "TOTAL_FLUX": dict(orders=base, mixer=ones, collapse="total_flux")}
    return {k: cfg[k] for k in names}


def score(st) -> int:
    from run_r1l_stage2_score import run_scoring
    return run_scoring(st)


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT / "scripts"))
    raise SystemExit(main())
