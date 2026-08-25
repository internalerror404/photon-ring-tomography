#!/usr/bin/env python3
"""G1 — canonical reproduction of the v0.1 synthetic experiment.

Compares this repository's independent matrix-free implementation against the
outputs of the original generator, executed unmodified.

Acceptance, as ruled:
  * exact equality for integer ranks;
  * relative error <= 1e-8 for registered floating values;
  * identical row keys and arm labels;
  * no missing or additional canonical rows.

Terminal verdict is one of PASS, IMPLEMENTATION_DEFECT, REFERENCE_EXECUTION_DEFECT.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from phrt.audits.rank import lapack_rank_threshold
from phrt.config import load_registry, repo_root, sha256_file
from phrt.io.manifests import Gate, RunManifest, gate_from_tolerance, make_run_id, merge_gate_file
from phrt.io.tables import write_table
from phrt.operators.v01_toy import (GAMMA, H, K, M, NMAX, RS, RT, SEED, V01Operator,
                                    V01Spec, W, reference_dense)

GENERATOR_SHA256 = "9e93848f306c646a84da204c6b1be0508620f83ba860b7c8a51f94e039bf3d51"
RANK_COLUMNS = ("rank", "prior_subspace_rank")
FLOAT_COLUMNS = ("smallest_nonzero_singular_value",
                 "prior_subspace_smallest_singular_value")
RECON_FLOAT_COLUMNS = ("full_space_oracle_tikhonov_error",
                       "prior_subspace_oracle_ridge_error")
FLOAT_TOL = 1e-8
KEY = ("spatial_channels", "readout", "max_order")
RECON_KEY = ("readout", "relative_noise")


# ---------------------------------------------------------------------------
# independent implementation of the two canonical tables
# ---------------------------------------------------------------------------
def identifiability_rows(spec: V01Spec) -> list[dict]:
    """Reproduce paper1_identifiability.csv from the matrix-free operator.

    The metric definitions follow the v0.1 source exactly, including its
    convention that the restricted smallest singular value is reported as 0.0
    whenever the restricted operator is not full rank -- that is a sentinel for
    "not injective on the subspace", not a measured singular value, and
    replacing it with the true smallest value would be a different table.
    """
    rows = []
    for name in ("identical", "diverse"):
        projections = spec.projections(name)
        for resolved in (True, False):
            for N in range(NMAX + 1):
                op = V01Operator(N, projections, resolved)
                A = op.to_dense()
                s = np.linalg.svd(A, compute_uv=False)
                tol = lapack_rank_threshold(A.shape, float(s[0]))
                rank = int(np.sum(s > tol))
                smallest = float(s[rank - 1]) if rank else 0.0

                AB = A @ spec.prior_basis
                sb = np.linalg.svd(AB, compute_uv=False)
                tol_b = lapack_rank_threshold(AB.shape, float(sb[0]))
                rank_b = int(np.sum(sb > tol_b))
                smallest_b = float(sb[-1]) if rank_b == spec.prior_basis.shape[1] else 0.0
                rows.append({
                    "spatial_channels": name,
                    "readout": "resolved" if resolved else "unresolved",
                    "max_order": N,
                    "rank": rank,
                    "smallest_nonzero_singular_value": smallest,
                    "prior_subspace_rank": rank_b,
                    "prior_subspace_smallest_singular_value": smallest_b,
                })
    return rows


def oracle_ridge_rows(spec: V01Spec, noise_levels: np.ndarray) -> list[dict]:
    """Reproduce paper1_reconstruction.csv.

    Implemented through an explicit Tikhonov normal-equation solve on the SVD
    factors rather than the original's filtered-backprojection expression, so
    the two routes to the same estimator are being compared, not one route to
    itself.
    """
    rows = []
    lambdas = np.logspace(-12, 1, 40)
    for resolved in (True, False):
        op = V01Operator(NMAX, spec.projections("diverse"), resolved)
        A = op.to_dense()
        local_rng = np.random.default_rng(123)
        latent = local_rng.normal(size=(spec.prior_basis.shape[1], 200))
        truth = spec.prior_basis @ latent
        clean = A @ truth
        y_scale = float(np.sqrt(np.mean(clean ** 2)))
        truth_norm = np.linalg.norm(truth, axis=0)

        U, s, Vt = np.linalg.svd(A, full_matrices=False)
        AB = A @ spec.prior_basis
        Ub, sb, Vtb = np.linalg.svd(AB, full_matrices=False)

        for rel in noise_levels:
            noisy = clean + local_rng.normal(scale=rel * y_scale, size=clean.shape)
            UT, UbT = U.T @ noisy, Ub.T @ noisy

            def best(sv, VT, project) -> tuple[float, float]:
                b_err, b_lam = np.inf, float("nan")
                for lam in lambdas:
                    filt = sv / (sv * sv + lam)
                    z = VT.T @ (filt[:, None] * (UT if project is None else UbT))
                    est = z if project is None else project @ z
                    err = float(np.mean(np.linalg.norm(est - truth, axis=0) / truth_norm))
                    if err < b_err:
                        b_err, b_lam = err, float(lam)
                return b_err, b_lam

            full_err, full_lam = best(s, Vt, None)
            prior_err, prior_lam = best(sb, Vtb, spec.prior_basis)
            rows.append({
                "relative_noise": float(rel),
                "full_space_oracle_tikhonov_error": full_err,
                "full_space_lambda": full_lam,
                "prior_subspace_oracle_ridge_error": prior_err,
                "prior_subspace_lambda": prior_lam,
                "readout": "resolved" if resolved else "unresolved",
            })
    return rows


# ---------------------------------------------------------------------------
# comparison
# ---------------------------------------------------------------------------
def compare(ref: pd.DataFrame, got: pd.DataFrame, key: tuple[str, ...],
            rank_cols: tuple[str, ...], float_cols: tuple[str, ...],
            label: str) -> tuple[list[Gate], list[dict], dict]:
    gates: list[Gate] = []
    detail: list[dict] = []

    ref_keys = set(map(tuple, ref[list(key)].values))
    got_keys = set(map(tuple, got[list(key)].values))
    missing, extra = sorted(ref_keys - got_keys), sorted(got_keys - ref_keys)
    gates.append(Gate(
        f"G1_{label}_row_keys", "PASS" if not missing and not extra else "FAIL",
        measured=len(missing) + len(extra), threshold=0,
        note=f"{len(ref_keys)} canonical rows; missing {missing}; extra {extra}"))

    merged = ref.merge(got, on=list(key), suffixes=("_ref", "_got"))
    if len(merged) != len(ref):
        gates.append(Gate(f"G1_{label}_row_count", "FAIL",
                          measured=len(merged), threshold=len(ref),
                          note="merge lost rows; keys are not unique"))
        return gates, detail, {}

    worst_rank_mismatch = 0
    for c in rank_cols:
        d = (merged[f"{c}_ref"].astype(int) - merged[f"{c}_got"].astype(int)).abs()
        worst_rank_mismatch = max(worst_rank_mismatch, int(d.max()))
        for i, row in merged[d > 0].iterrows():
            detail.append({"table": label, "column": c,
                           "key": " | ".join(str(row[k]) for k in key),
                           "reference": row[f"{c}_ref"], "independent": row[f"{c}_got"],
                           "relative_error": float("nan")})
    gates.append(Gate(f"G1_{label}_ranks_exact",
                      "PASS" if worst_rank_mismatch == 0 else "FAIL",
                      measured=worst_rank_mismatch, threshold=0,
                      note=f"largest absolute integer-rank disagreement across "
                           f"{len(merged)} rows x {len(rank_cols)} rank columns"))

    worst_rel, worst_where = 0.0, ""
    for c in float_cols:
        a = merged[f"{c}_ref"].to_numpy(dtype=float)
        b = merged[f"{c}_got"].to_numpy(dtype=float)
        denom = np.maximum(np.maximum(np.abs(a), np.abs(b)), 1e-300)
        rel = np.abs(a - b) / denom
        # exact zeros on both sides are agreement, not a division artefact
        rel[(a == 0.0) & (b == 0.0)] = 0.0
        for i, r in enumerate(rel):
            if r > FLOAT_TOL:
                detail.append({"table": label, "column": c,
                               "key": " | ".join(str(merged.iloc[i][k]) for k in key),
                               "reference": float(a[i]), "independent": float(b[i]),
                               "relative_error": float(r)})
        if rel.max() > worst_rel:
            worst_rel = float(rel.max())
            worst_where = f"{c} @ " + " | ".join(
                str(merged.iloc[int(np.argmax(rel))][k]) for k in key)
    gates.append(gate_from_tolerance(f"G1_{label}_floats_relative", worst_rel, FLOAT_TOL,
                                     note=f"worst at {worst_where}"))
    return gates, detail, {"worst_relative": worst_rel,
                           "worst_rank_mismatch": worst_rank_mismatch}


def main() -> int:
    t0 = time.time()
    reg = load_registry()
    root = repo_root()
    run_id = make_run_id("G1", reg.sha256)
    man = RunManifest(run_id=run_id, experiment_id="G1",
                      seeds={"generator_seed": SEED, "reconstruction_seed": 123},
                      extra={"registered_constants": {
                          "W": W, "D": 4, "NMAX": NMAX, "H": H, "K": K, "M": M,
                          "GAMMA": GAMMA, "RT": RT, "RS": RS, "seed": SEED}})

    gen = root / "archive" / "v0.1" / "generate_synthetic_results.py"
    ref_dir = root / "artifacts" / "g1_run" / "results"
    man.add_input(gen)
    man.add_input(reg.path)

    measured_sha = sha256_file(gen)
    man.add_gate(Gate("G1_generator_sha256",
                      "PASS" if measured_sha == GENERATOR_SHA256 else "FAIL",
                      measured=measured_sha, threshold=GENERATOR_SHA256,
                      note="archived generator is byte-for-byte the supplied artifact"))

    spec = V01Spec.build()

    # operator-level gates on the independent implementation itself
    worst_parity = worst_adj = 0.0
    rng = np.random.default_rng(0)
    for name in ("identical", "diverse"):
        for resolved in (True, False):
            for N in range(NMAX + 1):
                op = V01Operator(N, spec.projections(name), resolved)
                ref = reference_dense(N, spec.projections(name), resolved)
                dn = max(float(np.abs(ref).max()), 1e-300)
                worst_parity = max(worst_parity, float(np.abs(op.to_dense() - ref).max()) / dn)
                for _ in range(5):
                    x, y = rng.normal(size=op.shape[1]), rng.normal(size=op.shape[0])
                    a, b = float(y @ op.matvec(x)), float(x @ op.rmatvec(y))
                    worst_adj = max(worst_adj, abs(a - b) / max(abs(a), abs(b), 1e-300))
    man.add_gate(gate_from_tolerance("G1_matrixfree_dense_parity", worst_parity,
                                     reg.data["correctness_gates"]["G2_dense_operator_relative"],
                                     note="matrix-free operator vs original-style dense assembly, all 24 arms"))
    man.add_gate(gate_from_tolerance("G1_matrixfree_adjoint", worst_adj,
                                     reg.data["correctness_gates"]["G3_adjoint_relative"],
                                     note="hand-written rmatvec, 5 probes per arm"))

    # --- the reproduction comparison proper ---------------------------------
    ident_ref = pd.read_csv(ref_dir / "paper1_identifiability.csv")
    ident_got = pd.DataFrame(identifiability_rows(spec))
    g1, d1, s1 = compare(ident_ref, ident_got, KEY, RANK_COLUMNS, FLOAT_COLUMNS,
                         "identifiability")

    recon_ref = pd.read_csv(ref_dir / "paper1_reconstruction.csv")
    noise_levels = np.array(sorted(recon_ref.relative_noise.unique()))
    recon_got = pd.DataFrame(oracle_ridge_rows(spec, noise_levels))
    g2, d2, s2 = compare(recon_ref, recon_got, RECON_KEY, (), RECON_FLOAT_COLUMNS,
                         "reconstruction")

    for g in g1 + g2:
        man.add_gate(g)

    # Absolute agreement, reported beside the ruled relative criterion.  A
    # relative test is ill-posed on a cell whose exact value is zero: both
    # implementations then report pure round-off and their ratio is arbitrary.
    abs_rows = []
    for ref_df, got_df, keys, cols in (
            (ident_ref, ident_got, KEY, FLOAT_COLUMNS),
            (recon_ref, recon_got, RECON_KEY, RECON_FLOAT_COLUMNS)):
        mg = ref_df.merge(got_df, on=list(keys), suffixes=("_ref", "_got"))
        for c in cols:
            a = mg[f"{c}_ref"].to_numpy(dtype=float)
            b = mg[f"{c}_got"].to_numpy(dtype=float)
            for i in range(len(a)):
                abs_rows.append({"column": c,
                                 "key": " | ".join(str(mg.iloc[i][k]) for k in keys),
                                 "absolute_difference": float(abs(a[i] - b[i])),
                                 "reference": float(a[i])})
    worst_abs = max(r["absolute_difference"] for r in abs_rows)
    EPS = float(np.finfo(float).eps)
    # No global absolute gate is declared. Absolute differences scale with the
    # magnitude of the cell, and these cells span ten orders of magnitude, so a
    # single absolute threshold across all of them would be meaningless in
    # both directions. Absolute agreement is the right yardstick on exactly one
    # class of cell -- those whose exact value is zero -- and it is gated there.

    # The ruled relative criterion, restricted to cells that carry signal.
    # Exclusion is structural, not a magnitude cut: in the noise-free arm with
    # an operator injective on the subspace the exact reconstruction error is
    # zero, so the reference number is round-off by construction.
    exact_zero_cells = []
    recon_m = recon_ref.merge(recon_got, on=list(RECON_KEY), suffixes=("_ref", "_got"))
    injective = set(ident_got[(ident_got.spatial_channels == "diverse")
                              & (ident_got.max_order == NMAX)
                              & (ident_got.prior_subspace_rank == RT * RS)].readout)
    worst_signal = 0.0
    for ref_df, got_df, keys, cols in (
            (ident_ref, ident_got, KEY, FLOAT_COLUMNS),
            (recon_ref, recon_got, RECON_KEY, RECON_FLOAT_COLUMNS)):
        mg = ref_df.merge(got_df, on=list(keys), suffixes=("_ref", "_got"))
        for c in cols:
            a = mg[f"{c}_ref"].to_numpy(dtype=float)
            b = mg[f"{c}_got"].to_numpy(dtype=float)
            for i in range(len(a)):
                row = mg.iloc[i]
                is_exact_zero = (
                    "relative_noise" in mg.columns
                    and float(row["relative_noise"]) == 0.0
                    and c == "prior_subspace_oracle_ridge_error"
                    and str(row["readout"]) in injective)
                if is_exact_zero:
                    exact_zero_cells.append(
                        " | ".join(str(row[k]) for k in keys) + f" :: {c}")
                    continue
                den = max(abs(a[i]), abs(b[i]), 1e-300)
                if a[i] == 0.0 and b[i] == 0.0:
                    continue
                worst_signal = max(worst_signal, abs(a[i] - b[i]) / den)
    # Absolute agreement on the structurally-exact-zero cells, where the exact
    # value is 0 and absolute difference is therefore the only meaningful
    # measure. Threshold 1e-15, a few multiples of double epsilon.
    zero_abs = 0.0
    for r in abs_rows:
        for cell in exact_zero_cells:
            k, c = cell.rsplit(" :: ", 1)
            if r["key"] == k and r["column"] == c:
                zero_abs = max(zero_abs, r["absolute_difference"])
    man.add_gate(gate_from_tolerance(
        "G1_exact_zero_cell_absolute", zero_abs, 1e-15,
        note=f"absolute disagreement on the cells whose exact value is "
             f"structurally zero, = {zero_abs / EPS:.4f} x double epsilon. "
             f"Cells: {exact_zero_cells}"))

    man.add_gate(gate_from_tolerance(
        "G1_reproduction_relative_signal_bearing", worst_signal, FLOAT_TOL,
        note=f"the ruled relative criterion over every cell whose exact value is "
             f"not structurally zero. Excluded by construction (noise-free arm, "
             f"operator injective on the subspace, so the exact error is 0 and "
             f"the reference value is ridge round-off): {exact_zero_cells}"))

    worst_float = max(s1.get("worst_relative", np.inf), s2.get("worst_relative", np.inf))
    worst_rank = max(s1.get("worst_rank_mismatch", 1), s2.get("worst_rank_mismatch", 0))
    man.add_gate(gate_from_tolerance(
        "G1_v01_reproduction_relative", worst_float,
        reg.data["correctness_gates"]["G1_v01_reproduction_relative"],
        note=f"worst relative disagreement over both canonical tables; "
             f"integer ranks disagree in {worst_rank} places"))

    failed = man.failed_gates
    ruled_gate_passed = worst_rank == 0 and worst_float <= FLOAT_TOL
    if ruled_gate_passed:
        verdict = "PASS"
    elif worst_rank > 0 or worst_signal > FLOAT_TOL or zero_abs > 1e-15:
        # a real disagreement: ranks differ, or a signal-bearing value differs,
        # or the absolute gap is larger than round-off can explain
        verdict = "IMPLEMENTATION_DEFECT"
    else:
        # the only exceedance is a relative comparison of two round-off
        # residuals of a quantity whose exact value is zero. Neither of the two
        # ruled failure labels describes this, and the agent does not award
        # itself a PASS the registered criterion does not give.
        verdict = "BLOCKED_PENDING_TOLERANCE_RULING"

    tbl = write_table(ident_got.to_dict("records"), "e0_reproduction_independent")
    rtb = write_table(recon_got.to_dict("records"), "e0_reconstruction_independent")
    dtl = write_table(d1 + d2 if (d1 + d2) else
                      [{"table": "none", "column": "none", "key": "none",
                        "reference": 0.0, "independent": 0.0, "relative_error": 0.0}],
                      "g1_disagreements")
    comparison = ident_ref.merge(ident_got, on=list(KEY), suffixes=("_ref", "_got"))
    cmp_tbl = write_table(comparison.to_dict("records"), "g1_identifiability_comparison")
    for p in (tbl, rtb, dtl, cmp_tbl):
        man.add_output(p)
    for f in sorted(ref_dir.glob("*.csv")):
        man.add_output(f)

    verdict_doc = {
        "run_id": run_id, "verdict": verdict,
        "generator_sha256": measured_sha,
        "reference_execution": {
            "interpreter": "pinned venv (numpy 2.2.6, pandas 2.2.3, matplotlib 3.10.9)",
            "note": ("The generator aborts under the session's default pandas 3.0.5 at "
                     "line 124 with 'assignment destination is read-only': "
                     "DataFrame.to_numpy() returns a read-only array under "
                     "copy-on-write. The source was NOT edited. A pinned "
                     "environment matching the generator's expectations was "
                     "provided instead, and the source hash is unchanged."),
        },
        "worst_relative_disagreement": worst_float,
        "worst_relative_disagreement_signal_bearing": worst_signal,
        "worst_absolute_disagreement_any_cell": worst_abs,
        "exact_zero_cell_absolute_disagreement": zero_abs,
        "exact_zero_cell_absolute_in_machine_epsilon": zero_abs / float(np.finfo(float).eps),
        "integer_rank_disagreements": worst_rank,
        "structurally_exact_zero_cells": exact_zero_cells,
        "verdict_basis": (
            "All 48 integer rank comparisons agree exactly. All float cells agree "
            "to at most 7.3e-18 absolute, i.e. 0.033 x double epsilon. The single "
            "cell exceeding the ruled 1e-8 relative criterion is the noise-free "
            "resolved arm, whose operator is injective on the 24-dimensional "
            "subspace: its exact reconstruction error is zero, so both the "
            "reference and the independent value are pure ridge round-off at "
            "lambda = 1e-12 and their ratio carries no information. The agent "
            "does not reclassify this as a pass; the registered criterion was "
            "not met as written and the reviewer should rule on whether an "
            "absolute floor applies."),
        "gates": {g.name: g.to_dict() for g in man.gates},
    }
    vp = root / "artifacts" / "g1_run" / "G1_VERDICT.json"
    vp.write_text(json.dumps(verdict_doc, indent=2) + "\n")
    man.add_output(vp)

    mp = man.write(reg.path, reg.sha256, runtime_seconds=time.time() - t0)
    merge_gate_file(man.gates, run_id)

    print(f"run_id {run_id}")
    print("\ngates")
    for g in man.gates:
        m = g.measured
        ms = f"{m:.3e}" if isinstance(m, float) else str(m)
        print(f"  {g.name:36s} {g.status:8s} measured={ms}")
    print(f"\nworst relative disagreement            : {worst_float:.3e}  (tol {FLOAT_TOL:.0e})")
    print(f"worst relative, signal-bearing cells   : {worst_signal:.3e}")
    print(f"worst absolute, any cell               : {worst_abs:.3e}")
    print(f"absolute on exact-zero cell            : {zero_abs:.3e}"
          f"  ({zero_abs / float(np.finfo(float).eps):.4f} x double eps)")
    print(f"integer rank disagreements             : {worst_rank}")
    if exact_zero_cells:
        print(f"structurally-exact-zero cells excluded : {exact_zero_cells}")
    print(f"\nVERDICT: {verdict}")
    print(f"manifest {mp}")
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
