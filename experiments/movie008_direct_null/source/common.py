"""Shared authenticated Movie008 utilities. No physical ray call is made here."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path
from typing import Any

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")

import numpy as np
from scipy import linalg
from scipy.ndimage import gaussian_filter

ROOT = Path(__file__).resolve().parents[1]
INPUTS = ROOT / "inputs"
RESULTS = ROOT / "results"
FIGURES = ROOT / "figures"
LOGS = ROOT / "logs"
for directory in (RESULTS, FIGURES, LOGS):
    directory.mkdir(parents=True, exist_ok=True)

EXPECTED_INPUT_HASHES = {
    "PHYSICAL_AND_OPERATOR_ARRAYS.npz": "54204f14b8c834fb3c54dc012c9827e711f339fc6c30251802fea71ac6d8274e",
    "SUPPORT_WEIGHTS.npz": "72080e09e722b01a821d2989d706f21eccfc9ce7671d1fa2f18f66bcd56a7952",
    "REGULARIZATION_SELECTION.json": "f3739497a08973bec6ed0b5c174188ad1b2321b469efa06750de2b43bcddf090",
    "movie007_run.py": "8b80d533cd48400570e505423053a6557e4a2ea6f3d82367adfd5c88b34e5cf1",
    "kerr.py": "12abafb39f6d5a6ebf4626e0a05c021d3bd0c5c5ca6ae0abd22632656c8f28cf",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path: Path, value: Any) -> None:
    def default(obj: Any) -> Any:
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, np.generic):
            return obj.item()
        raise TypeError(type(obj).__name__)

    path.write_text(json.dumps(value, indent=2, allow_nan=False, default=default) + "\n")


def authenticate_inputs() -> dict[str, str]:
    actual: dict[str, str] = {}
    for name, expected in EXPECTED_INPUT_HASHES.items():
        path = INPUTS / name
        if not path.is_file():
            raise FileNotFoundError(f"Missing authenticated input: {path}")
        digest = sha256(path)
        if digest != expected:
            raise RuntimeError(f"Input hash mismatch for {name}: {digest} != {expected}")
        actual[name] = digest
    return actual


def load_movie007_module():
    authenticate_inputs()
    # movie007_run imports `kerr`; put authenticated inputs first.
    sys.path.insert(0, str(INPUTS))
    spec = importlib.util.spec_from_file_location("movie007_frozen", INPUTS / "movie007_run.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load frozen Movie007 source")
    module = importlib.util.module_from_spec(spec)
    sys.modules["movie007_frozen"] = module
    spec.loader.exec_module(module)
    return module


def load_inputs():
    hashes = authenticate_inputs()
    arrays = np.load(INPUTS / "PHYSICAL_AND_OPERATOR_ARRAYS.npz", allow_pickle=False)
    support = np.load(INPUTS / "SUPPORT_WEIGHTS.npz", allow_pickle=False)
    selection = json.loads((INPUTS / "REGULARIZATION_SELECTION.json").read_text())
    return arrays, support, selection, hashes


def pixel_areas(arrays, q: int, order: int) -> np.ndarray:
    return np.bincount(
        arrays[f"pixel_q{q}_n{order}"],
        arrays[f"weights_q{q}_n{order}"],
        minlength=64,
    )


def noise_calibration(arrays) -> tuple[float, np.ndarray, np.ndarray]:
    area0 = pixel_areas(arrays, 12, 0)
    area1 = pixel_areas(arrays, 12, 1)
    shape0 = np.tile(np.sqrt(area0), 13)
    shape1 = np.tile(np.sqrt(area1), 13)
    sigma300 = float(np.sqrt(np.mean((arrays["base_q12_n0"] / shape0) ** 2)) / 300.0)
    return sigma300, shape0, shape1


def coefficient_envelope(coeff: np.ndarray, nr: int = 5, na: int = 7, nt: int = 17) -> float:
    """Uniform bound from nonnegative radial/time B-spline partitions and |trig|<=1."""
    c = np.asarray(coeff).reshape(nr, na, nt)
    return float(np.max(np.abs(c[:, 0, :]) + np.sum(np.abs(c[:, 1:, :]), axis=1)))


def make_nuisance_background(rng: np.random.Generator, nuisance_indices: np.ndarray) -> tuple[np.ndarray, dict[str, float]]:
    """Smooth random nuisance contrast with a certified 0.25 coefficient envelope."""
    nr, na, nt = 5, 7, 17
    c = np.zeros((nr, na, nt), dtype=np.float64)

    old_axis = gaussian_filter(rng.normal(size=(nr, 7)), sigma=(0.9, 1.0), mode="nearest")
    c[:, 0, :7] = old_axis

    recent = rng.normal(size=(nr, na, 10))
    recent = gaussian_filter(recent, sigma=(0.9, 0.0, 1.15), mode="nearest")
    harmonic_weight = np.array([1.0, 1.0, 1.0, 4.0, 4.0, 9.0, 9.0])
    recent /= harmonic_weight[None, :, None]
    c[:, :, 7:] = recent

    flat = c.reshape(-1)
    mask = np.zeros_like(flat, dtype=bool)
    mask[nuisance_indices] = True
    if np.any(np.abs(flat[~mask]) > 0):
        raise AssertionError("Background escaped nuisance space")
    before = coefficient_envelope(flat)
    scale = min(1.0, 0.25 / max(before, 1e-15))
    flat *= scale
    after = coefficient_envelope(flat)
    return flat, {"raw_envelope": before, "scale": scale, "certified_envelope": after}


def weighted_target_metrics(
    true_frames: np.ndarray,
    pred_frames: np.ndarray,
    weights: np.ndarray,
    relative_activity: float = 0.20,
) -> dict[str, Any]:
    """Metrics for one old target movie. Arrays have shape (time,r,phi)."""
    old = np.arange(3, 15)  # tau=-6,...,-28
    w = weights[old]
    truth = true_frames[old]
    pred = pred_frames[old]
    truth_rms = np.sqrt(np.sum(w * truth**2, axis=(1, 2)))
    pred_rms = np.sqrt(np.sum(w * pred**2, axis=(1, 2)))
    peak = float(np.max(truth_rms))
    active = truth_rms >= relative_activity * max(peak, 1e-15)

    mx = np.sum(w * truth, axis=(1, 2))
    my = np.sum(w * pred, axis=(1, 2))
    xc = truth - mx[:, None, None]
    yc = pred - my[:, None, None]
    err = np.sqrt(np.sum(w * (pred - truth) ** 2, axis=(1, 2))) / np.maximum(truth_rms, 1e-15)
    cov = np.sum(w * xc * yc, axis=(1, 2))
    den = np.sqrt(np.sum(w * xc**2, axis=(1, 2)) * np.sum(w * yc**2, axis=(1, 2)))
    corr = np.where(den > 1e-15, cov / den, 0.0)
    passed = active & (err <= 0.35) & (corr >= 0.75)
    history_pass = bool(np.sum(active) >= 8 and np.all(passed[active]))
    return {
        "old_frame_indices": old,
        "truth_rms": truth_rms,
        "predicted_rms": pred_rms,
        "active": active,
        "error": err,
        "correlation": corr,
        "passed": passed,
        "active_frames": int(np.sum(active)),
        "history_pass": history_pass,
        "mean_active_error": float(np.mean(err[active])) if np.any(active) else float("inf"),
        "minimum_active_correlation": float(np.min(corr[active])) if np.any(active) else 0.0,
    }


def source_norm(coeff: np.ndarray, H: np.ndarray) -> float:
    return float(np.sqrt(np.asarray(coeff) @ H @ np.asarray(coeff)))


def project_modes(coeff: np.ndarray, mode_coeff: np.ndarray, H: np.ndarray) -> np.ndarray:
    """H-inner-product coordinates; mode columns are H-orthonormal."""
    return mode_coeff.T @ H @ coeff


def residual_projector(matrix: np.ndarray, rtol: float = 1e-12) -> tuple[np.ndarray, int, np.ndarray]:
    u, s, _ = linalg.svd(matrix, full_matrices=False, lapack_driver="gesdd", check_finite=False)
    rank = int(np.sum(s > rtol * s[0])) if len(s) and s[0] > 0 else 0
    return u[:, :rank], rank, s
