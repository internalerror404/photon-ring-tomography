"""Held-out bank construction shared by both stages of the HMT-2 sealed main.

Stage A draws it and commits the hashes; stage B rebuilds it and checks them
before touching an operator. Both import this, so "the same bank" is a property
of the code rather than a claim about it. Nothing here can reach an operator.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

from phrt.metrics.feature_sets import peaks_to_features
from phrt.metrics.topography import classify, reconcile
from phrt.metrics.windowed_reference import window_stack
from phrt.sources.contrast import build
from phrt.sources.separable_projection import factors, project

ROOT = Path(__file__).resolve().parents[1]
FZ = ROOT / "artifacts" / "configs" / "HMT2_SEALED_MAIN_V1.json"
HASHES = ROOT / "artifacts" / "provenance" / "HMT2_SEALED_MAIN_BANK_HASHES.json"
STAGE_A = ROOT / "artifacts" / "gates" / "hmt2_sealed_main_stage_a_gates.json"


def _payload(family: str, n: int, seed: int) -> bytes:
    return json.dumps({"family": family, "split": "hmt2_sealed_main_heldout",
                       "n": n, "seed": seed, "model": "contrast"},
                      sort_keys=True).encode()


def commitment(family: str, n: int, seed: int) -> str:
    return hashlib.sha256(_payload(family, n, seed)).hexdigest()


def truth_seed(family: str, i: int, n: int, seed: int) -> int:
    h = hashlib.sha256(_payload(family, n, seed) + f"|{i}".encode())
    return int(h.hexdigest()[:16], 16) % (2 ** 63)


def _h(a) -> str:
    return hashlib.sha256(np.ascontiguousarray(np.asarray(a, float),
                                               dtype="<f8").tobytes()).hexdigest()


def axes_for(level, r_in, r_out, t_lo, t_hi):
    nr, npz, nt = level
    return (np.exp(np.linspace(np.log(r_in), np.log(r_out), nr)),
            np.linspace(0.0, 2 * np.pi, npz, endpoint=False),
            np.linspace(t_lo, t_hi, nt))


def build_bank(cfg: dict) -> dict:
    """Every held-out truth, its labels, its in-class references, its hashes."""
    fz = cfg["fz"]
    comp = cfg["comp"]
    rc, pc, tc = cfg["rc"], cfg["pc"], cfg["tc"]
    Rc, Pc, Tc = np.meshgrid(rc, pc, tc, indexing="ij")
    Wc = window_stack(tc, cfg["ages"], cfg["half"])
    ti = np.tile(np.arange(comp[2]), comp[0] * comp[1])
    n = int(fz["bank"]["truths_per_family"])
    seed = int(fz["bank"]["bank_seed"])
    mult = fz["inherits_verbatim"]["expected_windowed_multiplicity"]
    frac = float(fz["inherits_verbatim"]["prominence_fraction"])
    lab_levels = [tuple(x) for x in fz["inherits_verbatim"]["classification"]["levels"]]
    classes = {k: v for k, v in
               (("primary", fz["inherits_verbatim"]["classes"]["primary"]),
                ("control", fz["inherits_verbatim"]["classes"]["control"]))}
    out = {}
    for family in fz["inherits_verbatim"]["source_families"]:
        for i in range(n):
            ts = truth_seed(family, i, n, seed)
            _, fluct, _, dj, _, diag = build(
                np.random.default_rng(ts), family, cfg["spin"], cfg["r_in"],
                cfg["r_out"], Rc.ravel(), Pc.ravel(), Tc.ravel(), ti, comp[2])
            lab = {}
            for lv in lab_levels:
                r, p, t = axes_for(lv, cfg["r_in"], cfg["r_out"], cfg["t_lo"],
                                   cfg["t_hi"])
                R, P, T = np.meshgrid(r, p, t, indexing="ij")
                v = np.asarray(fluct(R.ravel(), P.ravel(), T.ravel()),
                               float).reshape(r.size * p.size, t.size)
                m = (v @ window_stack(t, cfg["ages"], cfg["half"])).reshape(
                    r.size, p.size, cfg["ages"].size)
                tmax = float(np.abs(m).max())
                lab[lv] = [classify(m[:, :, k], int(mult[family]),
                                    float(m[:, :, k].max()), tmax, frac)["state"]
                           for k in range(cfg["ages"].size)]
            labels = [reconcile(lab[lab_levels[-1]][k], lab[lab_levels[-2]][k])
                      for k in range(cfg["ages"].size)]
            unstable = sum(1 for s in labels if s == "AMBIGUOUS")
            raw = dj.reshape(comp[0], comp[1], comp[2])
            mph = (raw.reshape(comp[0] * comp[1], comp[2]) @ Wc).reshape(
                comp[0], comp[1], cfg["ages"].size)
            tmp = float(np.abs(mph).max())
            fp = []
            for k in range(cfg["ages"].size):
                c = classify(mph[:, :, k], int(mult[family]),
                             float(mph[:, :, k].max()), tmp, frac)
                fp.append(peaks_to_features(c["peaks"], c["prominences"],
                                            mph[:, :, k], rc, pc))
            inclass = {}
            for _, cdef in classes.items():
                cn = cdef["id"]
                fac = factors(rc, pc, tc, cdef["radial"], cdef["azimuthal"],
                              cdef["temporal"])
                pr = project(raw, fac)
                mp = (pr.reshape(comp[0] * comp[1], comp[2]) @ Wc).reshape(
                    comp[0], comp[1], cfg["ages"].size)
                tm = float(np.abs(mp).max())
                ff, plab = [], []
                for k in range(cfg["ages"].size):
                    c = classify(mp[:, :, k], int(mult[family]),
                                 float(mp[:, :, k].max()), tm, frac)
                    ff.append(peaks_to_features(c["peaks"], c["prominences"],
                                                mp[:, :, k], rc, pc))
                    plab.append(c["state"])
                inclass[cn] = {"maps": mp, "feats": ff, "labels": plab}
            out[(family, i)] = {
                "fluct": fluct, "labels": labels, "maps_phys": mph,
                "feats_phys": fp, "inclass": inclass, "truth_seed": ts,
                "diag": diag, "n_ambiguous": unstable,
                "hashes": {"dj": _h(dj), "labels": _h(
                    [hash(s) % 1000 for s in labels])}}
    return out
