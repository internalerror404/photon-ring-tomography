#!/usr/bin/env python3
"""HMT-2 stage 0: the source object and resolution audit.

REVIEWER_RULING_HMT1_SOURCE_RESOLUTION_018 items 8 to 18.

Imports no ray map and constructs no observation operator. Nothing here is an
inverse-problem result. The question is what these source families put on these
grids, and what survives projection onto a reconstruction class -- the contract
HMT-1 assumed and never checked.
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

from phrt.attestation import attest  # noqa: E402
from phrt.config import sha256_file  # noqa: E402
from phrt.io.source_only import assert_source_only  # noqa: E402
from phrt.io.tables import write_table  # noqa: E402
from phrt.metrics.feature_sets import (assignment, associate_tracks,  # noqa: E402
                                       blended_descriptors, cell_metric,
                                       peaks_to_features)
from phrt.metrics.topography import classify, reconcile  # noqa: E402
from phrt.metrics.windowed_reference import window_stack  # noqa: E402
from phrt.sources.contrast import build  # noqa: E402
from phrt.sources.separable_projection import (factors,  # noqa: E402
                                               minimum_representable_width,
                                               project)

FZ = ROOT / "artifacts" / "configs" / "HMT2_STAGE0_SOURCE_OBJECT_AND_RESOLUTION_AUDIT_V0.json"
OUT = ROOT / "artifacts" / "gates" / "hmt2_stage0_gates.json"

def truth_seed(family, i, n, seed):
    p = json.dumps({"family": family, "split": "hmt2_stage0_source_audit",
                    "n": n, "seed": seed, "model": "contrast"},
                   sort_keys=True).encode()
    return int(hashlib.sha256(p + f"|{i}".encode()).hexdigest()[:16], 16) % (2 ** 63)


def canary_seed():
    """The HMT-1 failing truth, by its own commitment, as a named regression."""
    p = json.dumps({"family": "two_hotspot_trajectories",
                    "split": "sealed_main_heldout", "n": 16,
                    "seed": 20260921, "model": "contrast"},
                   sort_keys=True).encode()
    return int(hashlib.sha256(p + b"|5").hexdigest()[:16], 16) % (2 ** 63)


def axes_for(level, r_in, r_out, t_lo, t_hi):
    nr, npz, nt = level
    return (np.exp(np.linspace(np.log(r_in), np.log(r_out), nr)),
            np.linspace(0.0, 2 * np.pi, npz, endpoint=False),
            np.linspace(t_lo, t_hi, nt))


def windowed(fluct, r, p, t, ages, half):
    """The analytic fluctuation, windowed to each age, on one analysis grid."""
    R, P, T = np.meshgrid(r, p, t, indexing="ij")
    v = np.asarray(fluct(R.ravel(), P.ravel(), T.ravel()), float)
    v = v.reshape(r.size * p.size, t.size)
    return (v @ window_stack(t, ages, half)).reshape(r.size, p.size, ages.size), \
        v.reshape(r.size, p.size, t.size)


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0,
                    help="smoke run on this many truths per family. Writes "
                         "nothing canonical. Stage 0 has no held-out endpoint "
                         "to protect, but a partial table on disk is still a "
                         "table someone can mistake for the audit")
    args = ap.parse_args()
    t0 = time.time()
    numerics = require_single_threaded()
    fz = json.loads(FZ.read_text())
    assert_source_only()

    inh = fz["inherited"]
    r_in, r_out = 1.8660386527060988, 49.98205255591607
    import json as _j
    r1 = _j.loads((ROOT / "artifacts" / "configs" / "R1_MAIN_FREEZE.json").read_text())
    r_in = float(r1["physical_model"]["r_inner_M"])
    r_out = float(r1["physical_model"]["r_outer_M"])
    t_lo = float(r1["observation"]["basis_t_min"])
    t_hi = float(r1["observation"]["basis_t_max"])
    spin = float(inh["spin"])
    half = float(inh["probe_half_width_M"])
    ages = np.arange(0.0, float(inh["age_grid_max_M"]) + 1e-9,
                     float(inh["age_grid_step_M"]))
    frac = float(fz["classification"]["prominence_fraction"])
    mult = fz["source_families"]["expected_windowed_multiplicity"]
    levels = [(g["n_radial"], g["n_azimuthal"], g["n_temporal"])
              for g in fz["grids"]["nested"]]
    fine = levels[-1]
    classes = {k: v for k, v in fz["source_classes"].items()
               if isinstance(v, dict) and "radial" in v}

    r0a, p0a, _ = axes_for(levels[0], r_in, r_out, t_lo, t_hi)
    met0 = cell_metric(r0a, p0a)

    fams = list(fz["source_families"]["declared"])
    offm = list(fz["source_families"]["off_manifold"])
    n_per = int(fz["bank"]["truths_per_family"])
    n_off = int(fz["bank"]["off_manifold_per_family"])
    seed = int(fz["bank"]["bank_seed"])

    lim_d = args.limit or n_per
    lim_o = min(args.limit, n_off) if args.limit else n_off
    work = [(f, i, truth_seed(f, i, n_per, seed), False, False)
            for f in fams for i in range(lim_d)]
    work += [(f, i, truth_seed(f, i, n_off, seed), True, False)
             for f in offm for i in range(lim_o)]
    work += [("two_hotspot_trajectories", -1, canary_seed(), False, True)]

    state_rows, feat_rows, blend_rows, track_rows = [], [], [], []
    conv_rows, proj_rows = [], []
    fac_cache = {}

    Rf, Pf, Tf = axes_for(fine, r_in, r_out, t_lo, t_hi)
    gR, gP, gT = np.meshgrid(Rf, Pf, Tf, indexing="ij")
    t_index_f = np.tile(np.arange(fine[2]), fine[0] * fine[1])

    for n_done, (family, idx, ts, is_off, is_canary) in enumerate(work):
        rng = np.random.default_rng(ts)
        # the source object is built once, at the finest level, so that only
        # the analysis resolution varies below
        _, fluct, _, _, _, diag = build(rng, family, spin, r_in, r_out,
                                        gR.ravel(), gP.ravel(), gT.ravel(),
                                        t_index_f, fine[2])
        exp_m = int(mult[family])
        per_level_labels, per_level_feats = {}, {}
        raw_fine = maps_fine = None

        for li, lev in enumerate(levels):
            r, p, t = axes_for(lev, r_in, r_out, t_lo, t_hi)
            maps, raw = windowed(fluct, r, p, t, ages, half)
            if li == len(levels) - 1:
                raw_fine, maps_fine = raw, maps
            truth_max = float(np.abs(maps).max())
            labels, feats = [], []
            for k in range(ages.size):
                m = maps[:, :, k]
                c = classify(m, exp_m, float(m.max()), truth_max, frac)
                labels.append(c["state"])
                feats.append(peaks_to_features(c["peaks"], c["prominences"],
                                               m, r, p))
                if li == len(levels) - 1:
                    if c["state"] == "BLENDED":
                        blend_rows.append({
                            "family": family, "index": idx,
                            "off_manifold": is_off, "canary": is_canary,
                            "age_M": float(ages[k]), "level": li,
                            "multiplicity_label": exp_m,
                            **blended_descriptors(m, r, p)})
                    if c["state"] == "MULTI_RESOLVED":
                        for q, ft in enumerate(feats[-1]):
                            feat_rows.append({
                                "family": family, "index": idx,
                                "off_manifold": is_off, "canary": is_canary,
                                "age_M": float(ages[k]), "peak": q,
                                "cardinality": len(feats[-1]),
                                "peak_r": ft["r"], "peak_phi": ft["phi"],
                                "peak_amplitude": ft["amplitude"],
                                "peak_prominence": ft["prominence"]})
            per_level_labels[li] = labels
            per_level_feats[li] = feats

        # grid convergence between the two finest levels, item 16
        conv = [assignment(per_level_feats[len(levels) - 2][k],
                           per_level_feats[len(levels) - 1][k], met0)
                for k in range(ages.size)]
        conv_cells = [c["mean_matched_cells"] for c in conv
                      if np.isfinite(c["mean_matched_cells"])]
        card_err = [c["cardinality_error"] for c in conv]

        final = [reconcile(per_level_labels[len(levels) - 1][k],
                           per_level_labels[len(levels) - 2][k])
                 for k in range(ages.size)]
        tracks = associate_tracks(per_level_feats[len(levels) - 1], met0)
        for k, ids in enumerate(tracks):
            for q, tid in enumerate(ids):
                track_rows.append({"family": family, "index": idx,
                                   "off_manifold": is_off, "canary": is_canary,
                                   "age_M": float(ages[k]), "peak": q,
                                   "track_id": int(tid)})

        counts = {s: 0 for s in ("SINGLE_RESOLVED", "MULTI_RESOLVED",
                                 "BLENDED", "DEAD", "AMBIGUOUS")}
        for s in final:
            counts[s] += 1
        state_rows.append({
            "family": family, "index": idx, "truth_seed": ts,
            "off_manifold": is_off, "canary": is_canary,
            "expected_multiplicity": exp_m, "n_ages": int(ages.size),
            **{f"n_{s.lower()}": counts[s] for s in counts},
            "grid_convergence_cells_median":
                float(np.median(conv_cells)) if conv_cells else float("nan"),
            "grid_convergence_cells_max":
                float(np.max(conv_cells)) if conv_cells else float("nan"),
            "grid_convergence_cardinality_error_max": int(max(card_err)),
            "contrast_fraction": diag["contrast_fraction"],
            "peak_fraction_of_background":
                diag["achieved_peak_fraction_of_background"]})

        # projection onto each class, at the finest analysis level. The field
        # is the one already evaluated above: 1.3 million source evaluations
        # is not a thing to do twice per truth
        r, p, t = Rf, Pf, Tf
        for cname, cdef in classes.items():
            key = (cname, fine)
            if key not in fac_cache:
                fac_cache[key] = factors(r, p, t, cdef["radial"],
                                         cdef["azimuthal"], cdef["temporal"])
            fac = fac_cache[key]
            pr = project(raw_fine, fac)
            pmaps = (pr.reshape(r.size * p.size, t.size)
                     @ window_stack(t, ages, half)).reshape(r.size, p.size, ages.size)
            tmax_p = float(np.abs(pmaps).max())
            merged = kept = floor_costs = 0
            floors = []
            for k in range(ages.size):
                before = per_level_feats[len(levels) - 1][k]
                lab_b = per_level_labels[len(levels) - 1][k]
                m = pmaps[:, :, k]
                c = classify(m, exp_m, float(m.max()), tmax_p, frac)
                after = peaks_to_features(c["peaks"], c["prominences"], m, r, p)
                floors.append(assignment(before, after, met0)["unbalanced_cost"])
                if lab_b == "MULTI_RESOLVED":
                    kept += int(c["state"] == "MULTI_RESOLVED")
                    merged += int(c["state"] != "MULTI_RESOLVED")
            proj_rows.append({
                "family": family, "index": idx, "class": cname,
                "off_manifold": is_off, "canary": is_canary,
                "n_multi_before": int(kept + merged), "n_merged": int(merged),
                "merger_rate": float(merged / max(kept + merged, 1)),
                "representation_floor_median": float(np.median(floors)),
                "representation_floor_max": float(np.max(floors))})

        if (n_done + 1) % 12 == 0:
            print(f"  {n_done + 1}/{len(work)} truths, {time.time() - t0:.0f}s",
                  flush=True)

    # class properties, measured without drawing a source
    widths = [8.0, 6.0, 4.0, 3.0, 2.0, 1.5, 1.0, 0.75, 0.5]
    width_rows = []
    for cname, cdef in classes.items():
        for rc in (6.0, 20.0, 45.0):
            fac = factors(Rf, Pf, Tf, cdef["radial"], cdef["azimuthal"],
                          cdef["temporal"])
            mw = minimum_representable_width(fac, Rf, Pf, Tf, widths, rc)
            for row in mw["curve"]:
                width_rows.append({"class": cname, "r_centre_M": rc, **row})
            width_rows.append({"class": cname, "r_centre_M": rc,
                               "input_width_M": float("nan"),
                               "output_width_M": float("nan"),
                               "ratio": float("nan"),
                               "minimum_representable_width_M":
                                   mw["minimum_representable_width_M"]})

    if args.limit:
        print(f"\nSMOKE (limit {args.limit}): {len(work)} truths, "
              f"nothing written. {time.time() - t0:.0f}s")
        return 0

    for name, rows in (("hmt2_stage0_states", state_rows),
                       ("hmt2_stage0_multi_features", feat_rows),
                       ("hmt2_stage0_blended", blend_rows),
                       ("hmt2_stage0_tracks", track_rows),
                       ("hmt2_stage0_projection", proj_rows),
                       ("hmt2_stage0_class_widths", width_rows)):
        if rows:
            write_table(rows, name)

    doc = {
        "schema": "phrt-hmt2-stage0/1",
        "id": "HMT2_STAGE0_AUDIT",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "ruling": "REVIEWER_RULING_HMT1_SOURCE_RESOLUTION_018",
        "freeze": fz["id"], "freeze_sha256": sha256_file(FZ),
        "ray_map_imported": False, "operator_constructed": False,
        "source_only_verified": True,
        "n_truths": len(work), "n_declared": n_per * len(fams),
        "n_off_manifold": n_off * len(offm), "canary": 1,
        "levels": levels, "classes": sorted(classes),
        "numerical_environment": numerics_record(),
        "attestation": attest([FZ]),
        "runtime_seconds": round(time.time() - t0),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(doc, indent=2, default=str) + "\n")
    print(f"\nwrote {OUT.relative_to(ROOT)}")
    print(f"  {len(work)} truths, {len(levels)} levels, {len(classes)} classes")
    print(f"total {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
