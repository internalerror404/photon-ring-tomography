#!/usr/bin/env python3
"""S1 and S2 of ruling 035: bound decomposition, and one representation test.

S1 measures E_c <= A_c <= T_c <= U per channel, so the 034 conservatism can be
split into channel aggregation, loss of detector structure, and sign
cancellation, instead of being attributed to cancellation alone. Every channel
is divided by its own reference norm.

S2 checks the five-template identity -- that H0, Re/Im H20 and Re/Im H40
reconstruct all 40 transferred columns at the eight observer times -- and then
runs the one authorised representation comparison:

  baseline  : interpolate g and coordinate time, then cube and take the phases
  candidate : form the five templates at the coarse nodes, then interpolate

on exactly the same support. Nonlinear transformation and interpolation do not
commute; which order is better is a measurement, not an assumption, and a null
or worse result closes the test.

Zero physical queries: two archived maps and one archived hull per order.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import time
from pathlib import Path

import h5py
import numpy as np
from scipy import sparse

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from phrt.geometry.raymap import horizon_radius, read            # noqa: E402
from phrt.revision_v4_1 import domain as D                       # noqa: E402
from phrt.revision_v4_1 import fractional as FR                  # noqa: E402
from phrt.revision_v4_1 import measure as M                      # noqa: E402
from phrt.revision_v4_1.common_sky import DetectorGrid           # noqa: E402

MAPS = ROOT / "artifacts" / "raymaps"
AART = ROOT / "artifacts" / "e3_pilot" / "aart_out"
BANDS = {"fine": AART / ("fine/LensingBands_a_0.5_i_50.0_dx0_0.2_dx1_0.04"
                         "_dx2_0.01.h5")}
HULL = ROOT / ("artifacts/revisions/mahakal_v4_1/G1C_20260907T075203Z_d252697"
               "/CLOSEOUT_ARRAYS_029.npz")
HELPER = ROOT / ("docs/revisions/mahakal_v4_1/review035/"
                 "cancellation_and_templates_035.py")
GEOMETRY, SPIN, INC, R_OUTER = "a050_i050", 0.5, 50.0, 50.0
SIGMA, T_REF = 0.011341986814407566, -978.6055123201214
T_OBS = [0.0, 2.857142857142857, 5.714285714285714, 8.571428571428571,
         11.428571428571429, 14.285714285714286, 17.142857142857142, 20.0]
SCREEN = ("1", "alpha/25", "beta/25", "(alpha/25)^2", "(beta/25)^2",
          "alpha*beta/625")
TRANSFER = ("g^3", "g^3*cos20", "g^3*sin20", "g^3*cos40", "g^3*sin40")
BUDGET = 5.0e-4
# the inherited convention, retained without change: g is |redshift| and the
# delay is measured against the absolute clock reference
REDSHIFT_CONVENTION = "g = |archived redshift|; delay = T_REF - coordinate_time"


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with Path(p).open("rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def helper():
    spec = importlib.util.spec_from_file_location("rev035", HELPER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def screen_fields(alpha, beta):
    return np.stack([np.ones(alpha.size), alpha / 25, beta / 25,
                     (alpha / 25) ** 2, (beta / 25) ** 2,
                     alpha * beta / 625], axis=1)


def transferred_from_primitives(redshift, coord_time):
    """The inherited construction: cube and phase AFTER any interpolation."""
    g3 = np.abs(redshift) ** 3
    delay = T_REF - coord_time
    cols = []
    for t in T_OBS:
        ph = t - delay
        cols.extend([g3, g3 * np.cos(2 * np.pi * ph / 20),
                     g3 * np.sin(2 * np.pi * ph / 20),
                     g3 * np.cos(2 * np.pi * ph / 40),
                     g3 * np.sin(2 * np.pi * ph / 40)])
    return np.stack(cols, axis=1)


def labels():
    out = [f"screen:{s}" for s in SCREEN]
    for t in T_OBS:
        out += [f"transferred:{nm}@t={t:.6f}" for nm in TRANSFER]
    return out


def build_order(n: int, mod) -> dict:
    rh = horizon_radius(SPIN)
    grid = DetectorGrid(-25.0, 25.0, -25.0, 25.0, 0.4)
    hz = np.load(HULL)
    core = read(MAPS / f"{GEOMETRY}_n{n}_core.h5")
    fine = read(MAPS / f"{GEOMETRY}_n{n}_fine.h5")
    with h5py.File(BANDS["fine"], "r") as h:
        fband = h[f"mask{n}"][:]
    fstate, _ = D.classify_points(fband, fine.source_r, fine.source_phi,
                                  fine.coordinate_time, fine.redshift, rh,
                                  R_OUTER)
    emit = fstate == D.CERTIFIED_EMITTING

    ca, cb = np.unique(core.alpha), np.unique(core.beta)
    ia = np.clip(np.searchsorted(ca, fine.alpha) - 1, 0, ca.size - 2)
    ib = np.clip(np.searchsorted(cb, fine.beta) - 1, 0, cb.size - 2)
    ta = (fine.alpha - ca[ia]) / (ca[ia + 1] - ca[ia])
    tb = (fine.beta - cb[ib]) / (cb[ib + 1] - cb[ib])
    nb = cb.size
    idx = np.stack([ia * nb + ib, (ia + 1) * nb + ib,
                    ia * nb + (ib + 1), (ia + 1) * nb + (ib + 1)])
    ok = np.isfinite(core.redshift) & np.isfinite(core.source_r)
    w4 = np.stack([(1 - ta) * (1 - tb), ta * (1 - tb),
                   (1 - ta) * tb, ta * tb])

    def carry(values):
        g = np.where(ok, values, np.nan)
        return np.einsum("ij,ij->j", w4, g[idx])

    z_hat = carry(core.redshift)
    t_hat = carry(core.coordinate_time)
    support = emit & np.isfinite(z_hat) & np.isfinite(t_hat) \
        & np.isfinite(fine.redshift) & np.isfinite(fine.coordinate_time)

    # candidate: the five templates formed at the coarse nodes, then carried
    valid_core = ok & np.isfinite(core.coordinate_time)
    gc = np.where(valid_core, np.abs(core.redshift), np.nan)
    dc = np.where(valid_core, T_REF - core.coordinate_time, np.nan)
    Hc = np.full((core.alpha.size, 5), np.nan)
    m = valid_core & np.isfinite(gc) & np.isfinite(dc)
    Hc[m] = mod.harmonic_templates(gc[m], dc[m])
    H_hat = np.stack([carry(Hc[:, j]) for j in range(5)], axis=1)

    cells = M.build_ray_cells(fine.alpha, fine.beta, M.NODAL_DUAL_CLIPPED)
    ov = FR.triple_overlap(cells, grid, hz[f"tess_{n}e"], hz[f"tess_{n}i"])
    keep = support[ov.cols]
    uniq, inv = np.unique(ov.cols[keep], return_inverse=True)
    O = sparse.csr_matrix((ov.vals[keep], (ov.rows[keep], inv)),
                          shape=(grid.n_cells, uniq.size)).tocsr()
    whiten = np.full(grid.n_cells, 1.0 / (SIGMA * np.sqrt(grid.cell_area)))

    scr = screen_fields(fine.alpha[uniq], fine.beta[uniq])
    F_ref = np.concatenate([scr, transferred_from_primitives(
        fine.redshift[uniq], fine.coordinate_time[uniq])], axis=1)
    F_base = np.concatenate([scr, transferred_from_primitives(
        z_hat[uniq], t_hat[uniq])], axis=1)
    H_ref = mod.harmonic_templates(np.abs(fine.redshift[uniq]),
                                   T_REF - fine.coordinate_time[uniq])
    F_cand = np.concatenate(
        [scr, mod.expand_templates(H_hat[uniq], np.array(T_OBS))], axis=1)

    # the identity, on the reference side where both constructions are exact
    ident = mod.expand_templates(H_ref, np.array(T_OBS))
    identity_max = float(np.max(np.abs(ident - F_ref[:, len(SCREEN):])))
    K = O.multiply(whiten[:, None]).tocsr()
    identity_detector = float(np.max(np.abs(
        K @ ident - K @ F_ref[:, len(SCREEN):])))

    emit_area = float(ov.active_area[emit].sum())
    kept_area = float(ov.vals[keep].sum())
    out = {
        "order": n, "supported_nodes": int(uniq.size),
        "fine_emitting_nodes": int(emit.sum()),
        "node_coverage": float(uniq.size / max(int(emit.sum()), 1)),
        "compared_area": kept_area, "emitting_area": emit_area,
        "area_coverage": kept_area / max(emit_area, 1e-30),
        "omitted_area": emit_area - kept_area,
        "identity_max_pointwise": identity_max,
        "identity_max_after_the_detector": identity_detector,
        "support_identical_for_both_candidates": True,
    }
    arrays = {
        "uniq": uniq, "alpha": fine.alpha[uniq], "beta": fine.beta[uniq],
        "F_ref": F_ref, "F_base": F_base, "F_cand": F_cand,
        "H_ref": H_ref, "H_hat": H_hat[uniq],
        "O_data": O.data, "O_indices": O.indices, "O_indptr": O.indptr,
        "O_shape": np.array(O.shape), "whiten": whiten,
        "emit_mask": emit, "support_mask": support,
        "active_area": ov.active_area,
    }
    return out, arrays, O, whiten, F_ref, F_base, F_cand


def summarise(mod, O, whiten, F_ref, F_base, F_cand) -> dict:
    lab = labels()
    tr = slice(len(SCREEN), None)
    res = {}
    for name, F in (("baseline", F_base), ("candidate", F_cand)):
        h = mod.residual_hierarchy(O, whiten, F - F_ref, reference=F_ref)
        E, A, T, U = h["E"], h["A"], h["T"], h["U"]
        ref = h["reference_norm"]
        with np.errstate(divide="ignore", invalid="ignore"):
            relE = np.where(ref > 0, E / ref, np.nan)
        t_rel = relE[tr]
        res[name] = {
            "per_channel": [
                {"channel": lab[i], "E": float(E[i]), "A": float(A[i]),
                 "T": float(T[i]), "reference_norm": float(ref[i]),
                 "relative_E": None if not np.isfinite(relE[i])
                 else float(relE[i]),
                 "A_over_E": None if E[i] == 0 else float(A[i] / E[i]),
                 "T_over_A": None if A[i] == 0 else float(T[i] / A[i])}
                for i in range(len(lab))],
            "U_channel_max_aggregate": float(U),
            "transferred": {
                "max_relative_E": float(np.nanmax(t_rel)),
                "median_relative_E": float(np.nanmedian(t_rel)),
                "channels_above_budget": int(np.count_nonzero(
                    t_rel > BUDGET)),
                "of": int(t_rel.size),
                "worst_channel": lab[len(SCREEN) + int(np.nanargmax(t_rel))],
                "max_A_over_E": float(np.nanmax(
                    np.where(E[tr] > 0, A[tr] / E[tr], np.nan))),
                "max_T_over_A": float(np.nanmax(
                    np.where(A[tr] > 0, T[tr] / A[tr], np.nan))),
                "U_over_max_E": float(U / max(np.max(E[tr]), 1e-300)),
                "max_T_over_E": float(np.nanmax(
                    np.where(E[tr] > 0, T[tr] / E[tr], np.nan))),
            },
            "screen": {"max_relative_E": float(np.nanmax(relE[:len(SCREEN)])),
                       "max_absolute_E": float(np.max(E[:len(SCREEN)]))},
            "zero_reference_channels": int(np.count_nonzero(ref == 0)),
        }
    return res


def main(out: Path) -> int:
    t0 = time.time()
    mod = helper()
    per, blobs = {}, []
    for n in (0, 1, 2):
        info, arrays, O, whiten, F_ref, F_base, F_cand = build_order(n, mod)
        s = summarise(mod, O, whiten, F_ref, F_base, F_cand)
        info["baseline"] = s["baseline"]["transferred"]
        info["candidate"] = s["candidate"]["transferred"]
        info["screen_control"] = {
            "baseline": s["baseline"]["screen"],
            "candidate": s["candidate"]["screen"],
            "meaning": "equal-input consistency control, not an absolute "
                       "geometry validation",
        }
        per[f"n{n}"] = {"summary": info, "channels": s}
        K = O.multiply(whiten[:, None])
        arrays["y_ref"] = np.asarray(K @ F_ref)
        arrays["y_base"] = np.asarray(K @ F_base)
        arrays["y_cand"] = np.asarray(K @ F_cand)
        arrays["resid_base"] = arrays["y_base"] - arrays["y_ref"]
        arrays["resid_cand"] = arrays["y_cand"] - arrays["y_ref"]
        arrays["reference_norm"] = np.linalg.norm(arrays["y_ref"], axis=0)
        # one file per order: the whole set exceeds the 100 MB the remote
        # accepts, and splitting keeps every array rather than dropping any
        b = out / f"COMPOSITE_FIRST_COMPARISON_035_n{n}.npz"
        np.savez_compressed(b, **arrays)
        blobs.append(b)
        print(f"  order {n}: baseline {info['baseline']['max_relative_E']:.4e}"
              f", candidate {info['candidate']['max_relative_E']:.4e}"
              f", A/E {info['baseline']['max_A_over_E']:.2f}"
              f", T/A {info['baseline']['max_T_over_A']:.2f}"
              f", identity {info['identity_max_pointwise']:.2e}", flush=True)

    idx = out / "COMPOSITE_FIRST_COMPARISON_035_index.npz"
    np.savez_compressed(
        idx, channel_labels=np.array(labels(), dtype="U64"),
        observer_times=np.array(T_OBS),
        screen_channels=np.array(SCREEN, dtype="U32"),
        transferred_channels=np.array(TRANSFER, dtype="U32"),
        per_order_files=np.array([b.name for b in blobs], dtype="U64"))
    blobs.append(idx)
    files = {}
    ok = True
    for b in blobs:
        with np.load(b, allow_pickle=False) as z:
            files[b.name] = {
                "sha256": sha(b), "bytes": b.stat().st_size,
                "keys": {k: [int(x) for x in z[k].shape] for k in z.files}}
            ok &= all(np.isfinite(z[k]).all() for k in z.files
                      if z[k].dtype.kind == "f")
    (out / "PAIRED_PAYLOAD_MANIFEST_035.json").write_text(json.dumps({
        "stage": "S0/S2", "files": files, "readback_validated": True,
        "all_float_arrays_finite": bool(ok),
        "split_reason": "one file per order; the combined archive is 102.6 MB "
                        "and the remote rejects a blob over 100 MB. Every "
                        "array is kept; none is downcast or dropped.",
        "written_before_the_summary": True,
        "regenerated_from_cached_inputs_not_a_new_physical_run": True,
    }, indent=2) + "\n")

    rep = {
        "stage": "S1/S2", "ruling": "PAPER_I_CANCELLATION_RULING_035",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "commit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                 capture_output=True, text=True).stdout.strip(),
        "new_rays": 0, "physical_path_integrals": 0,
        "bound_definitions": {
            "E": "||K delta_c||, the actual signed detector residual",
            "A": "||K |delta_c| ||, cancellation removed inside each pixel",
            "T": "sum_p ||K[:,p]|| |delta_pc|, detector structure replaced",
            "U": "sum_p ||K[:,p]|| max_c |delta_pc|, the 034 aggregate",
            "order": "E <= A <= T <= U",
            "each_channel_uses_its_own_reference_norm": True,
        },
        "redshift_convention": REDSHIFT_CONVENTION,
        "candidate": "five templates formed at the coarse nodes, then "
                     "bilinearly interpolated, then expanded",
        "baseline": "redshift and coordinate time interpolated, then cubed "
                    "and phased",
        "support_identical_between_baseline_and_candidate": True,
        "favourable_outcome_required": False,
        "per_order": per,
        "runtime_seconds": time.time() - t0,
    }
    (out / "DETERMINISTIC_BOUND_HIERARCHY_035.json").write_text(
        json.dumps({k: v for k, v in rep.items() if k != "per_order"}
                   | {"per_order": {k: v["channels"] for k, v in per.items()}},
                   indent=2) + "\n")
    (out / "PER_CHANNEL_RESPONSE_AND_SUPPORT_035.json").write_text(
        json.dumps({k: v for k, v in rep.items() if k != "per_order"}
                   | {"per_order": {k: v["summary"] for k, v in per.items()}},
                   indent=2) + "\n")
    (out / "HARMONIC_TEMPLATE_IDENTITY_035.json").write_text(json.dumps({
        "stage": "S2",
        "identity": "H0, Re H20, Im H20, Re H40, Im H40 reconstruct all 40 "
                    "transferred columns at the eight observer times",
        "screen_channels_retained_separately": 6,
        "per_order": {f"n{n}": {
            "max_pointwise": per[f"n{n}"]["summary"]["identity_max_pointwise"],
            "max_after_the_detector":
                per[f"n{n}"]["summary"]["identity_max_after_the_detector"]}
            for n in (0, 1, 2)},
        "is_a_ray_speedup": False,
        "reduces_the_L224_source_space": False,
        "applies_to_arbitrary_source_movies": False,
        "applies_only_to_the_declared_diagnostic_fields": True,
    }, indent=2) + "\n")
    print(json.dumps({"stage": "S1/S2", "seconds": round(time.time() - t0)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main((ROOT / sys.argv[1]).resolve()))
