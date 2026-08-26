#!/usr/bin/env python3
"""R1 held-out main. Scores the sealed bank once, then stops.

Order matters here. The attestation runs before an operator exists, the sealed
records are regenerated and checked against their committed hashes before any
of them is put through one, and the hyperparameters are read from the R0C
selection rather than chosen. If any of that fails the run stops with
R1_IMPLEMENTATION_OR_LEAKAGE_DEFECT and no score is computed at all.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from phrt.attestation import attest
from phrt.config import load_registry
from phrt.geometry.raymap import read
from phrt.geometry.sampling import common_count, stratified_subsample
from phrt.governance import r0_provenance
from phrt.inverse.reduced import reduce_operator
from phrt.inverse.smoothness import temporal_difference_operator
from phrt.inverse.state_space import random_walk_precision
from phrt.inverse.wiener import fit_gaussian_prior
from phrt.io.manifests import Gate
from phrt.main_r1 import run
from phrt.metrics.age_error import freeze_eta
from phrt.metrics.level_structure import level_subspace
from phrt.metrics.scoring import AgeScorer, evaluation_grid
from phrt.operators.physical import PhysicalOperator
from phrt.pilot_r0c import coefficients_for
from phrt.sources.bank import BankContext, build_split, disjointness_report
from phrt.sources.in_span import (IN_SPAN_TOLERANCE, constant_coefficients,
                                  in_span_movie, in_span_residual)
from phrt.sources.physical_basis import PhysicalBasis

FREEZE = ROOT / "artifacts" / "configs" / "R1_MAIN_FREEZE.json"
R0C = ROOT / "artifacts" / "configs" / "R0C_REPAIRED_SOURCE_AND_CALIBRATION_FREEZE.json"
COMMITMENT = ROOT / "artifacts" / "manifests" / "r0c_future_test_hash_commitment.json"
NULL_BANK = ROOT / "artifacts" / "manifests" / "r1_null_pair_control_bank.json"
SELECTION = ROOT / "artifacts" / "tables" / "r0c_estimator_selection.parquet"
DEFECT = "R1_IMPLEMENTATION_OR_LEAKAGE_DEFECT"


def stop(msg: str, code: int = 2) -> int:
    print(f"STOP: {DEFECT}: {msg}")
    return code


def main() -> int:
    t0 = time.time()
    started = time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime())
    att = attest([FREEZE, R0C, COMMITMENT, NULL_BANK])
    if not att.get("preregistered"):
        return stop("the R1 freeze, the R0C freeze, the sealed-bank commitment "
                    "and the null control bank must all be committed in a clean "
                    f"tree before an operator touches a main truth. tracked "
                    f"{att.get('n_tracked_changes')}, untracked "
                    f"{att.get('n_untracked')}")
    print(f"attested at {att['execution_commit']}, clean tree")

    fz = json.loads(FREEZE.read_text())
    fh = hashlib.sha256(FREEZE.read_bytes()).hexdigest()
    r0c = json.loads(R0C.read_text())
    reg = load_registry()
    sc, obs = fz["source_class"], fz["observation"]
    gates = []

    # ---- operators and basis, from the freeze ------------------------------
    rng = np.random.default_rng(int(obs["subsample_seed"]))
    maps = [read(ROOT / "artifacts" / "raymaps" / f"a050_i050_n{n}_core.h5")
            for n in fz["physical_model"]["orders"]]
    base = common_count([stratified_subsample(m, int(obs["rays_per_order"]), rng)
                         for m in maps], rng)
    t_obs = np.asarray(obs["observer_times_M"], float)
    basis = PhysicalBasis(*sc["radial_support_M"], *sc["temporal_support_M"])
    kw = dict(observer_times=t_obs, design=basis.design,
              dimension=basis.dimension)
    ops = {
        "RESOLVED_PHYSICAL": PhysicalOperator(orders=base, **kw),
        "DIRECT_PHYSICAL": PhysicalOperator(orders=[base[0]], **kw),
        "UNRESOLVED_IMAGE": PhysicalOperator(orders=base,
                                             mixer=np.ones((1, len(base))), **kw),
        "TOTAL_FLUX": PhysicalOperator(orders=base, collapse="total_flux", **kw),
    }
    red = {a: reduce_operator(op.to_dense(), a) for a, op in ops.items()}
    rq, pq, tq = evaluation_grid(basis.r_inner, basis.r_outer,
                                 basis.t_min, basis.t_max)
    design = basis.design(rq, pq, tq)
    const_coef, _ = constant_coefficients(design)
    level = level_subspace(tq, basis.t_min, basis.t_max, basis.n_temporal)
    ages = np.arange(0.0, float(fz["metrics"]["age_grid_max_M"]) + 1e-9,
                     float(fz["metrics"]["age_grid_step_M"]))
    h_probe = float(fz["source_families"]["resolution_bounds"]
                    ["probe_half_width_M"])
    scorer = AgeScorer.build(design, tq, ages, h_probe)
    ctxb = BankContext(fz["source_families"]["resolved_ranges"],
                       (basis.r_inner, basis.r_outer),
                       (basis.t_min, basis.t_max))
    print(f"class d={basis.dimension}, evaluation points={rq.size}, "
          f"level modes={level.shape[1]}")

    # ---- the sealed bank, regenerated and checked against its hashes -------
    commit_doc = json.loads(COMMITMENT.read_text())
    if commit_doc["commitment_sha256"] != fz["sealed_bank"]["commitment_sha256"]:
        return stop("the commitment on disk is not the one the freeze names")
    committed = {}
    for r in commit_doc["payload"]["records"]:
        committed.setdefault(r["regime"], []).append(r)
    master = int(r0c["seeds"]["master"])
    streams = r0c["seeds"]["streams"]
    regimes = fz["source_regimes"]

    bank, mismatches, n_checked = {}, [], 0
    for regime, spec in regimes.items():
        movies = []
        for fam in spec["families"]:
            mv = build_split(fam, f"future_main_test:{regime}", 64, master,
                             streams["future_main_test"], ctxb,
                             off_grid=spec["off_grid"])
            if spec["in_span"]:
                mv = [in_span_movie(m, basis, rq, pq, tq, const_coef)
                      for m in mv]
            movies.extend(mv)
        bank[regime] = movies
        want = {r["parameter_hash"]: r for r in committed.get(regime, [])}
        for m in movies:
            n_checked += 1
            rec = want.get(m.content_hash)
            if rec is None:
                mismatches.append(f"{regime}/{m.family}: parameter hash "
                                  f"{m.content_hash[:12]} is not in the "
                                  f"commitment")
                continue
            if spec["in_span"]:
                ch = hashlib.sha256(np.ascontiguousarray(
                    m.extra["coefficients"], dtype="<f8").tobytes()).hexdigest()
                if ch != rec["coefficient_hash"]:
                    mismatches.append(f"{regime}/{m.family}: coefficient hash "
                                      f"differs from the commitment")
    gates.append(Gate("R1_G1_sealed_bank_matches_commitment",
                      "PASS" if not mismatches else "FAIL",
                      measured=len(mismatches), threshold=0,
                      note=f"{n_checked} regenerated records checked against "
                           f"commitment "
                           f"{commit_doc['commitment_sha256'][:16]}..., "
                           f"parameter hashes and, where the regime is "
                           f"in-span, coefficient hashes"
                           + ("" if not mismatches else f"; {mismatches[:3]}")))
    if mismatches:
        return stop(f"{len(mismatches)} sealed records do not match their "
                    f"committed hashes")
    print(f"sealed bank: {n_checked} records match their committed hashes")

    # ---- in-span membership, off the projection grid -----------------------
    r2 = np.linspace(basis.r_inner, basis.r_outer, 257)
    p2 = np.linspace(0.0, 2 * np.pi, 257)
    t2 = np.linspace(basis.t_min, basis.t_max, 257)
    D2 = basis.design(r2, p2, t2)
    devs = [0.0]
    for regime, spec in regimes.items():
        if spec["in_span"]:
            devs += [in_span_residual(m, D2, r2, p2, t2) for m in bank[regime]]
    worst = float(max(devs))
    gates.append(Gate("R1_G2_in_span_membership",
                      "PASS" if worst <= IN_SPAN_TOLERANCE else "FAIL",
                      measured=worst, threshold=IN_SPAN_TOLERANCE,
                      note="measured on coordinates other than the projection "
                           "grid"))
    if worst > IN_SPAN_TOLERANCE:
        return stop(f"in-span residual {worst:.2e}")

    # ---- split isolation: the main bank must not touch any R0C split -------
    groups = {f"future_main_test:{k}": v for k, v in bank.items()}
    for split, offset in (("prior_fit_train", streams["prior_fit_train"]),
                          ("repair_validation", streams["repair_validation"]),
                          ("uncertainty_calibration",
                           streams["uncertainty_calibration"])):
        got = []
        for regime, spec in regimes.items():
            per = (r0c["splits"]["prior_fit_train"]["per_family"]
                   if split == "prior_fit_train"
                   else r0c["splits"]["uncertainty_calibration"]["per_regime"]
                   if split == "uncertainty_calibration"
                   else r0c["splits"]["repair_validation"]
                   ["per_family_by_regime"][regime])
            if split == "prior_fit_train" and regime != "IN_CLASS_ID":
                continue
            for fam in spec["families"]:
                mv = build_split(fam, split, int(per), master, offset, ctxb,
                                 off_grid=spec["off_grid"])
                if spec["in_span"]:
                    mv = [in_span_movie(m, basis, rq, pq, tq, const_coef)
                          for m in mv]
                got.extend(mv)
        groups[split] = got
    disj = disjointness_report(groups)
    gates.append(Gate("R1_G3_split_isolation",
                      "PASS" if disj["disjoint"] else "FAIL",
                      measured=disj["worst_overlap"], threshold=0,
                      note="content-hash overlap between the sealed main bank "
                           "and every R0C split"))
    if not disj["disjoint"]:
        return stop(f"split leakage {disj['pairwise_overlap']}")
    print(f"split isolation: worst overlap {disj['worst_overlap']} across "
          f"{len(groups)} splits")

    # ---- frozen estimator machinery, refitted on the R0C prior-fit bank ----
    pf = np.array([m(rq, pq, tq) for m in groups["prior_fit_train"]])
    pf_coef = coefficients_for(groups["prior_fit_train"], pf, design)
    Wn = scorer.weights
    eta = freeze_eta(np.sqrt(np.einsum("ap,np->na", Wn ** 2, pf ** 2)).ravel())
    _, s_pf, m_pf = scorer.truth_terms(pf)
    tn = np.sqrt(np.maximum(s_pf - m_pf ** 2
                            / np.maximum(scorer.h, 1e-300), 0.0))
    pos = tn[tn > 0]
    eta_struct = float(0.05 * np.median(pos)) if pos.size else 1e-12
    priors = {sh: fit_gaussian_prior(pf_coef, float(sh))
              for sh in fz["hyperparameter_grids"]["WIENER_GAUSSIAN"]["grid"]}
    LtL = temporal_difference_operator(basis.n_radial, basis.n_azimuthal,
                                       basis.n_temporal)
    LtL = LtL.T @ LtL
    ss_prec = {q: random_walk_precision(basis.n_radial, basis.n_azimuthal,
                                        basis.n_temporal, float(q))
               for q in fz["hyperparameter_grids"]["LINEAR_STATE_SPACE"]
               ["process_noise"]}
    print(f"frozen from R0C: eta {eta:.6g}, eta_struct {eta_struct:.6g}")

    # ---- hyperparameters: read from the R0C selection, never chosen --------
    sel = pd.read_parquet(SELECTION)
    selected = {(r.arm, r.estimator, float(r.snr0)): float(
        r.selected_hyperparameter) for r in sel.itertuples()}
    estimators = list(fz["hyperparameter_grids"].keys())
    estimators = [e for e in ("TSVD", "RIDGE_IDENTITY", "TIKHONOV_TEMPORAL",
                              "WIENER_GAUSSIAN", "LINEAR_STATE_SPACE")]
    snr_grid = [float(s) for s in fz["physical_model"]["snr0_grid"]]
    missing = [(a, e, s) for a in
               ("DIRECT_PHYSICAL", "RESOLVED_PHYSICAL", "UNRESOLVED_IMAGE",
                "TOTAL_FLUX")
               for e in estimators for s in snr_grid
               if (a, e, s) not in selected]
    gates.append(Gate("R1_G4_hyperparameters_frozen_from_validation",
                      "PASS" if not missing else "FAIL",
                      measured=len(selected), threshold=len(selected) + len(missing),
                      note="every (arm, estimator, SNR) hyperparameter is read "
                           "from the R0C repair-validation selection; nothing "
                           "is selected on a main-test truth"
                           + ("" if not missing else f"; missing {missing[:3]}")))
    if missing:
        return stop(f"{len(missing)} hyperparameters absent from the R0C "
                    f"selection")

    # ---- render the sealed truths ------------------------------------------
    truth_vals, truth_coef, terms, truth_family = {}, {}, {}, {}
    for regime, movies in bank.items():
        v = np.array([m(rq, pq, tq) for m in movies])
        if v.min() < 0:
            return stop(f"negative intensity in {regime}")
        truth_vals[regime] = v
        truth_coef[regime] = coefficients_for(movies, v, design)
        truth_family[regime] = np.array([m.family for m in movies])
        p_, s_, m_ = scorer.truth_terms(v)
        terms[regime] = (p_, s_, m_, np.sqrt(np.maximum(s_, 0.0)))
    print("sealed truths rendered: "
          + ", ".join(f"{k}={v.shape[0]}" for k, v in truth_vals.items()))

    P = {"t0": t0, "started": started, "attestation": att, "freeze": fz,
         "freeze_hash": fh, "reg": reg, "ages": ages, "scorer": scorer,
         "design": design, "red": red, "rho": float(fz["subspaces"]["rho"]),
         "snr_grid": snr_grid, "eta": eta, "eta_struct": eta_struct,
         "truth_vals": truth_vals, "truth_coef": truth_coef, "terms": terms,
         "truth_family": truth_family, "regimes": list(regimes),
         "master": master, "streams": streams, "dimension": basis.dimension,
         "selected": selected, "estimators": estimators,
         "level_basis": level, "integrity_gates": gates,
         "ctx": {"LtL": LtL, "priors": priors, "ss_prec": ss_prec, "cache": {}},
         "provenance": r0_provenance()}
    return run(P)


if __name__ == "__main__":
    raise SystemExit(main())
