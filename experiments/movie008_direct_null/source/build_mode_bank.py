"""Build and freeze the q8 conditional direct-null mode bank before fresh sources."""
from __future__ import annotations

import time
import numpy as np
from scipy import linalg

from common import ROOT, RESULTS, dump, load_inputs, load_movie007_module, noise_calibration, residual_projector, sha256


def coefficient_index(i: int, j: int, k: int, na: int = 7, nt: int = 17) -> int:
    return (i * na + j) * nt + k


def index_sets() -> tuple[np.ndarray, np.ndarray]:
    target = np.array(
        [coefficient_index(i, j, k) for i in range(5) for j in range(1, 7) for k in range(7)],
        dtype=np.int64,
    )
    nuisance = []
    for i in range(5):
        for j in range(7):
            for k in range(7, 17):
                nuisance.append(coefficient_index(i, j, k))
        for k in range(7):
            nuisance.append(coefficient_index(i, 0, k))
    return target, np.array(sorted(set(nuisance)), dtype=np.int64)


def conditional_parent(A0, A1, std0, std1, parent_map, nuisance_coeff):
    A = np.vstack([A0, A1])
    std = np.concatenate([std0, std1])
    bt = (A @ parent_map) / std[:, None]
    bn = (A @ nuisance_coeff) / std[:, None]
    qn, rank, nuisance_s = residual_projector(bn, 1e-12)
    e = bt - qn @ (qn.T @ bt)
    return e, qn, rank, nuisance_s


def main() -> None:
    if (RESULTS / "MODE_BANK.npz").exists():
        raise RuntimeError("Mode bank already exists; use a fresh directory")
    start = time.perf_counter()
    arrays, _support, _selection, input_hashes = load_inputs()
    m = load_movie007_module()
    H = arrays["H"]
    sigma300, shape0, shape1 = noise_calibration(arrays)
    std0, std1 = sigma300 * shape0, sigma300 * shape1
    target, nuisance = index_sets()
    if len(target) != 210 or len(nuisance) != 385 or np.intersect1d(target, nuisance).size:
        raise AssertionError("Target/nuisance index construction failed")

    Ht = H[np.ix_(target, target)]
    Lt = np.linalg.cholesky(Ht)
    parent_map = np.zeros((595, len(target)))
    parent_map[target] = linalg.solve_triangular(Lt.T, np.eye(len(target)), lower=False, check_finite=False)
    parent_orth = float(np.linalg.norm(parent_map.T @ H @ parent_map - np.eye(len(target)), ord=2))

    nuisance_coeff = np.eye(595)[:, nuisance]
    e8, qn8, nuisance_rank8, nuisance_s8 = conditional_parent(
        arrays["A_q8_n0"], arrays["A_q8_n1"], std0, std1, parent_map, nuisance_coeff
    )
    u8, s8, vt8 = linalg.svd(e8, full_matrices=False, lapack_driver="gesdd", check_finite=False)
    sub_modes = vt8[:4].T.copy()
    mode_coeff = parent_map @ sub_modes
    for j in range(4):
        pivot = int(np.argmax(np.abs(mode_coeff[:, j])))
        if mode_coeff[pivot, j] < 0:
            mode_coeff[:, j] *= -1
            sub_modes[:, j] *= -1
            u8[:, j] *= -1
    mode_orth = float(np.linalg.norm(mode_coeff.T @ H @ mode_coeff - np.eye(4), ord=2))

    e12, qn12, nuisance_rank12, nuisance_s12 = conditional_parent(
        arrays["A_q12_n0"], arrays["A_q12_n1"], std0, std1, parent_map, nuisance_coeff
    )
    response8 = e8 @ sub_modes
    response12 = e12 @ sub_modes
    corr = np.array([
        response8[:, j] @ response12[:, j]
        / (np.linalg.norm(response8[:, j]) * np.linalg.norm(response12[:, j]))
        for j in range(4)
    ])
    conditional_s12 = linalg.svdvals(response12)

    direct8 = arrays["A_q8_n0"] @ mode_coeff
    direct12 = arrays["A_q12_n0"] @ mode_coeff
    bank_path = RESULTS / "MODE_BANK.npz"
    np.savez_compressed(
        bank_path,
        target_indices=target,
        nuisance_indices=nuisance,
        parent_map=parent_map,
        subspace_modes=sub_modes,
        mode_coefficients=mode_coeff,
        q8_conditional_responses=response8,
        q12_conditional_responses=response12,
        q8_singular_values=s8,
        q12_modebank_singular_values=conditional_s12,
        sigma300=np.array(sigma300),
        std_shape0=shape0,
        std_shape1=shape1,
        nuisance_rank_q8=np.array(nuisance_rank8),
        nuisance_rank_q12=np.array(nuisance_rank12),
    )
    checks = {
        "authenticated_inputs": True,
        "target_dimension_210": len(target) == 210,
        "nuisance_dimension_385": len(nuisance) == 385,
        "disjoint_target_nuisance": np.intersect1d(target, nuisance).size == 0,
        "parent_source_orthonormal": parent_orth <= 1e-10,
        "four_modes_source_orthonormal": mode_orth <= 1e-10,
        "direct_q8_exact_zero": float(np.max(np.abs(direct8))) == 0.0,
        "direct_q12_exact_zero": float(np.max(np.abs(direct12))) == 0.0,
        "q8_q12_conditional_response_correlation": bool(np.all(corr >= 0.99999)),
        "q8_nuisance_rank_stable": nuisance_rank8 == 322,
        "q12_nuisance_rank_stable": nuisance_rank12 == 322,
    }
    if not all(checks.values()):
        raise AssertionError(checks)
    summary = {
        "experiment": "Movie008 q8-frozen direct-null mode bank",
        "input_hashes": input_hashes,
        "target_dimension": len(target),
        "nuisance_dimension": len(nuisance),
        "nuisance_rank_q8": nuisance_rank8,
        "nuisance_rank_q12": nuisance_rank12,
        "parent_source_orthonormality_error": parent_orth,
        "mode_source_orthonormality_error": mode_orth,
        "direct_q8_max_abs": float(np.max(np.abs(direct8))),
        "direct_q12_max_abs": float(np.max(np.abs(direct12))),
        "q8_conditional_singular_values_top10": s8[:10],
        "q12_frozen_mode_bank_singular_values": conditional_s12,
        "q8_q12_mode_response_correlations": corr,
        "mode_bank_sha256": sha256(bank_path),
        "checks": checks,
        "seconds": time.perf_counter() - start,
        "q12_status": "q12 behavior was inspected in the pre-registration audit; it is a numerical cross-rule record, not a fresh held-out mode-selection gate",
    }
    dump(RESULTS / "MODE_BANK.json", summary)
    print(summary)


if __name__ == "__main__":
    main()
