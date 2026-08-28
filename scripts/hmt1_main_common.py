"""Held-out bank construction shared by both stages of the HMT-1 sealed main.

Stage A draws this bank and commits its hashes. Stage B rebuilds it and checks
the hashes before touching an operator. Both stages import the same function,
so "the same bank" is a property of the code rather than a claim about it.

Nothing here imports an operator or a ray map. Stage A must be unable to apply
an operator even by accident, and the cheapest way to guarantee that is for the
module it runs to have no way to reach one.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

from phrt.metrics.features import extract
from phrt.metrics.windowed_reference import peak_agreement, windowed_peak
from phrt.sources.contrast import build

ROOT = Path(__file__).resolve().parents[1]
FZ = ROOT / "artifacts" / "configs" / "HMT1_SEALED_HELD_OUT_MAIN_FREEZE_V2.json"
VFZ = ROOT / "artifacts" / "configs" / "HMT1_VALIDATION_FREEZE_V0.json"
R1 = ROOT / "artifacts" / "configs" / "R1_MAIN_FREEZE.json"
HASHES = ROOT / "artifacts" / "provenance" / "HMT1_MAIN_BANK_HASHES.json"


def _payload(family: str, n: int, seed: int) -> bytes:
    return json.dumps({"family": family, "split": "sealed_main_heldout",
                       "n": n, "seed": seed, "model": "contrast"},
                      sort_keys=True).encode()


def commitment(family: str, n: int, seed: int) -> str:
    return hashlib.sha256(_payload(family, n, seed)).hexdigest()


def truth_seed(family: str, i: int, n: int, seed: int) -> int:
    h = hashlib.sha256(_payload(family, n, seed) + f"|{i}".encode())
    return int(h.hexdigest()[:16], 16) % (2 ** 63)


def _h(a) -> str:
    return hashlib.sha256(
        np.ascontiguousarray(np.asarray(a, float), dtype="<f8").tobytes()
    ).hexdigest()


def feature_hash(f: dict) -> str:
    h = hashlib.sha256()
    for k in sorted(f):
        h.update(k.encode())
        h.update(np.ascontiguousarray(
            np.atleast_1d(np.asarray(f[k], float)), dtype="<f8").tobytes())
    return h.hexdigest()


def grids():
    """The evaluation grid and age axis, read from the frozen documents."""
    fz = json.loads(FZ.read_text())
    vfz = json.loads(VFZ.read_text())
    r1 = json.loads(R1.read_text())
    eg = vfz["evaluation_grid"]
    span = fz["endpoints"]["primary"]["stable_feature_interval"]
    r_in = float(r1["physical_model"]["r_inner_M"])
    r_out = float(r1["physical_model"]["r_outer_M"])
    t_lo = float(r1["observation"]["basis_t_min"])
    t_hi = float(r1["observation"]["basis_t_max"])
    NR, NP, NT = eg["n_radial"], eg["n_azimuthal"], eg["n_temporal"]
    r_axis = np.exp(np.linspace(np.log(r_in), np.log(r_out), NR))
    phi_axis = np.linspace(0.0, 2 * np.pi, NP, endpoint=False)
    t_axis = np.linspace(t_lo, t_hi, NT)
    Rg, Pg, Tg = np.meshgrid(r_axis, phi_axis, t_axis, indexing="ij")
    ages = np.arange(0.0, float(r1["metrics"]["age_grid_max_M"]) + 1e-9,
                     float(span["age_grid_step_M"]))
    return {
        "fz": fz, "vfz": vfz, "r1": r1,
        "r_axis": r_axis, "phi_axis": phi_axis, "t_axis": t_axis,
        "gr": Rg.ravel(), "gp": Pg.ravel(), "gt": Tg.ravel(),
        "t_index": np.tile(np.arange(NT), NR * NP),
        "NR": NR, "NP": NP, "NT": NT,
        "spin": float(vfz["geometry"]["a_star"]),
        "r_in": r_in, "r_out": r_out,
        "ages": ages, "half": float(span["probe_half_width_M"]),
        "obs_span": float(np.ptp(np.asarray(
            r1["observation"]["observer_times_M"], float))),
        "r_span": r_out - r_in,
    }


def build_bank(g: dict, families=None) -> dict:
    """Every held-out truth, its features, and their hashes.

    Keyed by (family, index) and not by regime: the ruling's 16 fresh truths
    per family are seen by all three background regimes, so the regime
    comparison is paired on one truth rather than confounded with a redraw.
    """
    fz = g["fz"]
    seed = int(fz["seeds"]["bank_seed"])
    n = int(fz["design"]["truths_per_family"])
    fams = list(families or fz["design"]["families"])
    out = {}
    for family in fams:
        for i in range(n):
            ts = truth_seed(family, i, n, seed)
            rng = np.random.default_rng(ts)
            b, fluct, traj, dj, bg, diag = build(
                rng, family, g["spin"], g["r_in"], g["r_out"],
                g["gr"], g["gp"], g["gt"], g["t_index"], g["NT"])
            feats = extract(dj, g["gt"], g["ages"], g["r_axis"],
                            g["phi_axis"], g["half"])
            # G10c: the independent windowed reference. No per-family
            # candidate list and no m-fold folding, because the windowed field
            # has one set of maxima whatever drew it
            ref = windowed_peak(fluct, np.unique(g["gt"]), g["ages"],
                                g["r_in"], g["r_out"], g["NR"], g["NP"],
                                g["half"])
            gerr = peak_agreement(feats, ref, g["r_axis"], g["phi_axis"])
            out[(family, i)] = {
                "b": b, "fluct": fluct, "traj": traj, "dj": dj, "bg": bg,
                "diag": diag, "features": feats, "truth_seed": ts,
                "windowed": gerr,
                "hashes": {"dj": _h(dj), "bg": _h(bg),
                           "total": _h(bg + dj),
                           "features": feature_hash(feats)},
            }
    return out
