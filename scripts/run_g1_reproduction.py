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

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from phrt.audits import tolerance as tol
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
    """Compare two canonical tables under the reviewer-ruled criteria.

    Exact equality is required for integer ranks, dimensions, row identities,
    and arm labels.  Floating cells use the mixed criterion uniformly, with no
    cell classified or excluded.
    """
    gates: list[Gate] = []
    detail: list[dict] = []

    # -- row identities and arm labels, exactly -----------------------------
    ref_keys = set(map(tuple, ref[list(key)].values))
    got_keys = set(map(tuple, got[list(key)].values))
    missing, extra = sorted(ref_keys - got_keys), sorted(got_keys - ref_keys)
    gates.append(Gate(
        f"G1_{label}_row_identities", "PASS" if not missing and not extra else "FAIL",
        measured=len(missing) + len(extra), threshold=0,
        note=f"{len(ref_keys)} canonical rows compared exactly on {list(key)}; "
             f"missing {missing}; extra {extra}"))

    # -- table dimensions, exactly ------------------------------------------
    same_shape = (len(ref) == len(got))
    shared_cols = [c for c in ref.columns if c in got.columns]
    gates.append(Gate(
        f"G1_{label}_dimensions", "PASS" if same_shape else "FAIL",
        measured=f"{len(got)} rows x {len(got.columns)} cols",
        threshold=f"{len(ref)} rows x {len(ref.columns)} cols",
        note=f"{len(shared_cols)} shared columns"))

    merged = ref.merge(got, on=list(key), suffixes=("_ref", "_got"))
    if len(merged) != len(ref):
        gates.append(Gate(f"G1_{label}_row_count", "FAIL",
                          measured=len(merged), threshold=len(ref),
                          note="merge lost rows; keys are not unique"))
        return gates, detail, {}

    # -- integer ranks, exactly ---------------------------------------------
    worst_rank_mismatch = 0
    for c in rank_cols:
        d = (merged[f"{c}_ref"].astype(int) - merged[f"{c}_got"].astype(int)).abs()
        worst_rank_mismatch = max(worst_rank_mismatch, int(d.max()))
        for _, row in merged[d > 0].iterrows():
            detail.append({"table": label, "column": c,
                           "key": " | ".join(str(row[k]) for k in key),
                           "reference": float(row[f"{c}_ref"]),
                           "candidate": float(row[f"{c}_got"]),
                           "residual": float("nan"), "allowance": float("nan"),
                           "utilisation": float("nan"), "kind": "integer_rank"})
    gates.append(Gate(f"G1_{label}_ranks_exact",
                      "PASS" if worst_rank_mismatch == 0 else "FAIL",
                      measured=worst_rank_mismatch, threshold=0,
                      note=f"largest absolute integer-rank disagreement across "
                           f"{len(merged)} rows x {len(rank_cols)} rank columns"))

    # -- floating cells, mixed criterion, applied uniformly ------------------
    worst_util, worst_where, worst_resid = 0.0, "", 0.0
    worst_rel = 0.0
    for c in float_cols:
        a = merged[f"{c}_ref"].to_numpy(dtype=float)
        b = merged[f"{c}_got"].to_numpy(dtype=float)
        util = tol.utilisation(b, a)
        resid = tol.residual(b, a)
        allow = tol.allowance(b, a)
        den = np.maximum(np.maximum(np.abs(a), np.abs(b)), 1e-300)
        rel = np.where((a == 0.0) & (b == 0.0), 0.0, resid / den)
        for i in range(len(a)):
            row_key = " | ".join(str(merged.iloc[i][k]) for k in key)
            if util[i] > 1.0:
                detail.append({"table": label, "column": c, "key": row_key,
                               "reference": float(a[i]), "candidate": float(b[i]),
                               "residual": float(resid[i]),
                               "allowance": float(allow[i]),
                               "utilisation": float(util[i]), "kind": "float_cell"})
        if util.max() > worst_util:
            j = int(np.argmax(util))
            worst_util = float(util[j])
            worst_resid = float(resid[j])
            worst_where = f"{c} @ " + " | ".join(str(merged.iloc[j][k]) for k in key)
        worst_rel = max(worst_rel, float(rel.max()))

    gates.append(Gate(
        f"G1_{label}_mixed_tolerance", "PASS" if worst_util <= 1.0 else "FAIL",
        measured=worst_util, threshold=1.0,
        note=f"fraction of the ruled allowance used by the worst cell "
             f"({worst_where}); residual {worst_resid:.3e} = "
             f"{tol.in_machine_eps(worst_resid):.4f} x unit-scale binary64 "
             f"machine epsilon"))

    return gates, detail, {"worst_relative": worst_rel,
                           "worst_utilisation": worst_util,
                           "worst_residual": worst_resid,
                           "worst_rank_mismatch": worst_rank_mismatch}


def load_canonical(directory: Path) -> dict[str, pd.DataFrame]:
    """Read the two standalone canonical CSVs from a reviewer-supplied directory."""
    out = {}
    for name in ("paper1_identifiability", "paper1_reconstruction"):
        hits = sorted(directory.rglob(f"{name}.csv"))
        if not hits:
            raise FileNotFoundError(f"{name}.csv not found under {directory}")
        out[name] = pd.read_csv(hits[0])
        out[f"{name}__path"] = hits[0]
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gate-file", type=Path, default=None,
                    help="write gates here instead of the canonical "
                         "artifacts/gates/correctness_gates.json. Use for "
                         "diagnostic and self-test runs so they cannot leave "
                         "failures in the provenance record.")
    ap.add_argument("--reference-dir", type=Path, default=None,
                    help="directory holding the reviewer's standalone canonical "
                         "CSVs; enables the cross-machine comparison")
    args = ap.parse_args()

    t0 = time.time()
    reg = load_registry()
    root = repo_root()
    run_id = make_run_id("G1", reg.sha256)
    man = RunManifest(run_id=run_id, experiment_id="G1",
                      seeds={"generator_seed": SEED, "reconstruction_seed": 123},
                      extra={"registered_constants": {
                          "W": W, "D": 4, "NMAX": NMAX, "H": H, "K": K, "M": M,
                          "GAMMA": GAMMA, "RT": RT, "RS": RS, "seed": SEED},
                          "tolerance_specification": tol.SPECIFICATION,
                          "tolerance_criterion": tol.CRITERION})

    gen = root / "archive" / "v0.1" / "generate_synthetic_results.py"
    local_dir = root / "artifacts" / "g1_run" / "results"
    man.add_input(gen)
    man.add_input(reg.path)

    measured_sha = sha256_file(gen)
    man.add_gate(Gate("G1_generator_sha256",
                      "PASS" if measured_sha == GENERATOR_SHA256 else "FAIL",
                      measured=measured_sha, threshold=GENERATOR_SHA256,
                      note="archived generator is byte-for-byte the supplied artifact"))
    man.add_gate(Gate("G1_tolerance_specification", "PASS",
                      measured=tol.SPECIFICATION, threshold=tol.SPECIFICATION,
                      note=f"reviewer-ruled adjudication. Criterion applied "
                           f"uniformly to every floating reproduction cell: "
                           f"{tol.CRITERION}. Exact equality required for integer "
                           f"ranks, dimensions, row identities, and arm labels."))

    spec = V01Spec.build()

    # -- operator-level gates on the independent implementation --------------
    worst_parity = worst_adj = 0.0
    rng = np.random.default_rng(0)
    for name in ("identical", "diverse"):
        for resolved in (True, False):
            for N in range(NMAX + 1):
                op = V01Operator(N, spec.projections(name), resolved)
                ref = reference_dense(N, spec.projections(name), resolved)
                dn = max(float(np.abs(ref).max()), 1e-300)
                worst_parity = max(worst_parity,
                                   float(np.abs(op.to_dense() - ref).max()) / dn)
                for _ in range(5):
                    x, y = rng.normal(size=op.shape[1]), rng.normal(size=op.shape[0])
                    a, b = float(y @ op.matvec(x)), float(x @ op.rmatvec(y))
                    worst_adj = max(worst_adj, abs(a - b) / max(abs(a), abs(b), 1e-300))
    man.add_gate(gate_from_tolerance(
        "G1_matrixfree_dense_parity", worst_parity,
        reg.data["correctness_gates"]["G2_dense_operator_relative"],
        note="matrix-free operator vs original-style dense assembly, all 24 arms"))
    man.add_gate(gate_from_tolerance(
        "G1_matrixfree_adjoint", worst_adj,
        reg.data["correctness_gates"]["G3_adjoint_relative"],
        note="hand-written rmatvec, 5 probes per arm"))

    # -- A: independent implementation vs locally generated reference --------
    ident_local = pd.read_csv(local_dir / "paper1_identifiability.csv")
    recon_local = pd.read_csv(local_dir / "paper1_reconstruction.csv")
    ident_got = pd.DataFrame(identifiability_rows(spec))
    noise_levels = np.array(sorted(recon_local.relative_noise.unique()))
    recon_got = pd.DataFrame(oracle_ridge_rows(spec, noise_levels))

    gA1, dA1, sA1 = compare(ident_local, ident_got, KEY, RANK_COLUMNS,
                            FLOAT_COLUMNS, "identifiability")
    gA2, dA2, sA2 = compare(recon_local, recon_got, RECON_KEY, (),
                            RECON_FLOAT_COLUMNS, "reconstruction")
    for g in gA1 + gA2:
        man.add_gate(g)

    worst_rel = max(sA1.get("worst_relative", np.inf), sA2.get("worst_relative", np.inf))
    worst_util = max(sA1.get("worst_utilisation", np.inf), sA2.get("worst_utilisation", np.inf))
    worst_resid = max(sA1.get("worst_residual", 0.0), sA2.get("worst_residual", 0.0))
    worst_rank = max(sA1.get("worst_rank_mismatch", 1), sA2.get("worst_rank_mismatch", 0))

    # The originally ruled gate is preserved exactly as written, including its
    # tolerance and its failure. It is never edited to match the adjudication.
    man.add_gate(Gate(
        "G1_v01_reproduction_relative", "FAIL" if worst_rel > FLOAT_TOL else "PASS",
        measured=worst_rel, threshold=FLOAT_TOL,
        disposition="FAIL_AS_WRITTEN",
        note="pure relative criterion, preserved unaltered on the record. It is "
             "not well posed on a zero-limit, regularization-dominated cell, "
             "where both values are round-off residuals of a quantity whose "
             "limit is zero; superseded for adjudication by "
             "G1_v01_reproduction_mixed_tolerance."))
    man.add_gate(Gate(
        "G1_v01_reproduction_mixed_tolerance",
        "PASS" if (worst_util <= 1.0 and worst_rank == 0) else "FAIL",
        measured=worst_util, threshold=1.0,
        note=f"ruled criterion over every floating cell of both canonical "
             f"tables, no exclusions. Worst cell uses {worst_util:.3e} of its "
             f"allowance; worst residual {worst_resid:.3e} = "
             f"{tol.in_machine_eps(worst_resid):.4f} x unit-scale binary64 "
             f"machine epsilon. Integer ranks disagree in {worst_rank} places."))
    man.add_gate(Gate(
        "G1_scientific_reproduction",
        "PASS" if (worst_util <= 1.0 and worst_rank == 0) else "FAIL",
        measured="PASS_WITH_NUMERICAL_QUALIFICATION" if worst_util <= 1.0 else "FAIL",
        threshold="PASS_WITH_NUMERICAL_QUALIFICATION",
        disposition="PASS_WITH_NUMERICAL_QUALIFICATION",
        note="all integer ranks, dimensions, row identities and arm labels exact; "
             "all floating cells within the ruled mixed criterion. The "
             "qualification is that one cell is zero-limit and "
             "regularization-dominated, so its agreement is established "
             "absolutely rather than relatively."))

    # Two diagnostics improvised before the adjudication are withdrawn. They
    # are emitted as NOT_RUN rather than deleted so the gate file shows the
    # withdrawal instead of silently dropping entries a reader may have seen.
    for name, why in (
        ("G1_reproduction_relative_signal_bearing",
         "withdrawn: required classifying one cell as excluded. The ruled mixed "
         "criterion applies uniformly and needs no exclusion."),
        ("G1_exact_zero_cell_absolute",
         "withdrawn: a bare absolute floor is only meaningful on the zero-limit "
         "cells it was scoped to. The ruled mixed criterion carries the same "
         "absolute floor for every cell."),
    ):
        man.add_gate(Gate(name, "NOT_RUN", disposition="WITHDRAWN",
                          note=why + " Superseded by "
                               "G1_v01_reproduction_mixed_tolerance."))

    # Gates renamed when the adjudicated criterion replaced the pure relative
    # one. Retired by name so the file cannot show a stale entry as current.
    for old, new in (
        ("G1_identifiability_row_keys", "G1_identifiability_row_identities"),
        ("G1_reconstruction_row_keys", "G1_reconstruction_row_identities"),
        ("G1_identifiability_floats_relative", "G1_identifiability_mixed_tolerance"),
        ("G1_reconstruction_floats_relative", "G1_reconstruction_mixed_tolerance"),
    ):
        man.add_gate(Gate(old, "NOT_RUN", disposition="RENAMED",
                          note=f"renamed to {new} when the adjudicated mixed "
                               f"criterion replaced the pure relative one"))

    # -- B: cross-machine, locally generated vs reviewer's canonical CSVs ----
    cross_rows: list[dict] = []
    cross_status = "NOT_RUN"
    if args.reference_dir is not None:
        canon = load_canonical(args.reference_dir)
        man.add_input(canon["paper1_identifiability__path"])
        man.add_input(canon["paper1_reconstruction__path"])
        gB1, dB1, sB1 = compare(canon["paper1_identifiability"], ident_local, KEY,
                                RANK_COLUMNS, FLOAT_COLUMNS, "crossmachine_identifiability")
        gB2, dB2, sB2 = compare(canon["paper1_reconstruction"], recon_local, RECON_KEY,
                                (), RECON_FLOAT_COLUMNS, "crossmachine_reconstruction")
        for g in gB1 + gB2:
            man.add_gate(g)
        x_util = max(sB1.get("worst_utilisation", np.inf), sB2.get("worst_utilisation", np.inf))
        x_rank = max(sB1.get("worst_rank_mismatch", 1), sB2.get("worst_rank_mismatch", 0))
        ok = (x_util <= 1.0 and x_rank == 0)
        cross_status = "PASS" if ok else "FAIL"
        man.add_gate(Gate(
            "G1_cross_machine_reference", cross_status,
            measured=x_util, threshold=1.0,
            note=f"reviewer's canonical CSVs vs this host's execution of the "
                 f"hash-verified generator. Integer ranks disagree in {x_rank} "
                 f"places. Tests whether LAPACK QR and SVD conventions differ "
                 f"between the two builds."))
        cross_rows = dB1 + dB2
        # also compare the independent implementation directly to the canonical CSVs
        gC1, dC1, sC1 = compare(canon["paper1_identifiability"], ident_got, KEY,
                                RANK_COLUMNS, FLOAT_COLUMNS, "canonical_vs_independent")
        for g in gC1:
            man.add_gate(g)
    else:
        man.add_gate(Gate(
            "G1_cross_machine_reference", "NOT_RUN", threshold=1.0,
            note="the two standalone canonical CSVs were not supplied. The "
                 "comparison harness is implemented and runs with "
                 "--reference-dir; until it does, whether the generator emits "
                 "identical values on the reviewer's machine and on this Linux "
                 "host is untested. LAPACK QR and SVD sign and ordering "
                 "conventions can differ between builds, and this generator's "
                 "projections come directly from qr()."))

    # -- verdict -------------------------------------------------------------
    scientific_ok = (worst_util <= 1.0 and worst_rank == 0)
    if not scientific_ok:
        verdict = "IMPLEMENTATION_DEFECT"
    elif cross_status == "FAIL":
        verdict = "CROSS_MACHINE_REPRODUCTION_DEFECT"
    elif cross_status == "PASS":
        verdict = "PASS"
    else:
        verdict = "PASS_PENDING_CROSS_MACHINE_REFERENCE"

    e3 = "AUTHORIZED" if verdict == "PASS" else "NOT_AUTHORIZED"

    # -- artifacts -----------------------------------------------------------
    detail = dA1 + dA2 + cross_rows
    tbl = write_table(ident_got.to_dict("records"), "e0_reproduction_independent")
    rtb = write_table(recon_got.to_dict("records"), "e0_reconstruction_independent")
    dtl = write_table(detail if detail else
                      [{"table": "none", "column": "none", "key": "none",
                        "reference": 0.0, "candidate": 0.0, "residual": 0.0,
                        "allowance": 0.0, "utilisation": 0.0, "kind": "none"}],
                      "g1_disagreements")
    comparison = ident_local.merge(ident_got, on=list(KEY), suffixes=("_ref", "_got"))
    cmp_tbl = write_table(comparison.to_dict("records"), "g1_identifiability_comparison")
    outputs = [tbl, rtb, dtl, cmp_tbl]
    if args.reference_dir is not None:
        xm = canon["paper1_identifiability"].merge(
            ident_local, on=list(KEY), suffixes=("_canonical", "_thishost"))
        outputs.append(write_table(xm.to_dict("records"), "g1_cross_machine_comparison"))
    for p_ in outputs:
        man.add_output(p_)
    for f in sorted(local_dir.glob("*.csv")):
        man.add_output(f)

    verdict_doc = {
        "run_id": run_id, "verdict": verdict,
        "e3_pilot": e3,
        "generator_sha256": measured_sha,
        "tolerance_specification": tol.SPECIFICATION,
        "tolerance_criterion": tol.CRITERION,
        "reference_execution": {
            "interpreter": "pinned venv (numpy 2.2.6, pandas 2.2.3, matplotlib 3.10.9)",
            "note": ("The generator aborts under the session's default pandas 3.0.5 at "
                     "line 124 with 'assignment destination is read-only': "
                     "DataFrame.to_numpy() returns a read-only array under "
                     "copy-on-write. The source was NOT edited. A pinned "
                     "environment matching the generator's expectations was "
                     "provided instead, and the source hash is unchanged."),
        },
        "worst_relative_disagreement": worst_rel,
        "worst_allowance_utilisation": worst_util,
        "worst_absolute_residual": worst_resid,
        "worst_absolute_residual_in_machine_eps": tol.in_machine_eps(worst_resid),
        "integer_rank_disagreements": worst_rank,
        "cross_machine_reference": cross_status,
        "gates": {g.name: g.to_dict() for g in man.gates},
    }
    vp = root / "artifacts" / "g1_run" / "G1_VERDICT.json"
    vp.write_text(json.dumps(verdict_doc, indent=2) + "\n")
    man.add_output(vp)

    mp = man.write(reg.path, reg.sha256, runtime_seconds=time.time() - t0)
    merge_gate_file(man.gates, run_id, path=args.gate_file)

    print(f"run_id {run_id}")
    print(f"tolerance specification: {tol.SPECIFICATION}")
    print(f"criterion: {tol.CRITERION}\n")
    print("gates")
    for g in man.gates:
        m = g.measured
        ms = f"{m:.3e}" if isinstance(m, float) else str(m)
        if len(ms) > 34:
            ms = ms[:31] + "..."
        disp = f"  [{g.disposition}]" if g.disposition else ""
        print(f"  {g.name:44s} {g.status:8s} {ms}{disp}")
    print(f"\nworst allowance utilisation : {worst_util:.3e}   (pass <= 1.0)")
    print(f"worst absolute residual     : {worst_resid:.3e}"
          f"  ({tol.in_machine_eps(worst_resid):.4f} x unit-scale binary64 machine eps)")
    print(f"worst pure relative         : {worst_rel:.3e}   (ruled gate, preserved FAIL_AS_WRITTEN)")
    print(f"integer rank disagreements  : {worst_rank}")
    print(f"cross-machine reference     : {cross_status}")
    print(f"\nVERDICT: {verdict}")
    print(f"E3 PILOT: {e3}")
    print(f"manifest {mp}")
    return 0 if verdict.startswith("PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
