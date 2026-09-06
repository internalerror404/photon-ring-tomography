#!/usr/bin/env python3
"""Q2 of ruling 026: converge the rays into one fixed detector.

The question this stage asks is not whether a changing detector reproduces an
ideal ray-level norm. It is whether the piecewise ray representation is an
accurate enough description of one fixed observation. So D026 is held fixed --
aperture, pitch, observer times and sigma -- and the ray sampling is refined
across the three archived profiles.

Refuses to start unless the preexecution freeze matches the tree. No target
spectrum, operational count or estimator is computed anywhere here.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from phrt.geometry.raymap import read                       # noqa: E402
from phrt.revision_v4_1 import acquisition as ACQ           # noqa: E402
from phrt.revision_v4_1 import measure as M                 # noqa: E402
from phrt.revision_v4_1.common_sky import DetectorGrid      # noqa: E402

MAPS = ROOT / "artifacts" / "raymaps"
PAIRS = (("coarse", "core"), ("core", "fine"))


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def check_freeze(fz: dict) -> dict:
    """Fail closed: every frozen file must still hash to its frozen value."""
    bad = {f: {"frozen": h, "now": sha(ROOT / f) if (ROOT / f).exists()
               else None}
           for f, h in fz["files"].items()
           if not (ROOT / f).exists() or sha(ROOT / f) != h}
    if bad:
        raise SystemExit("freeze does not match the tree:\n"
                         + json.dumps(bad, indent=2))
    if not fz.get("frozen_files_clean_in_git"):
        raise SystemExit("the freeze was written over uncommitted files; "
                         "commit them and re-freeze before running Q2")
    return {"verified_input_hashes": True, "n_files": len(fz["files"]),
            "commit_at_freeze_time": fz["commit_at_freeze_time"]}


def fields(a, b, g, delay, t_obs, names_s, names_t):
    """The declared suite, evaluated on valid rays only.

    Columns are the screen fields first, then each transferred field at each
    observer time. Nothing here depends on a target mode.
    """
    cols, labels = [], []
    s = {"1": np.ones(a.size), "alpha/25": a / 25.0, "beta/25": b / 25.0,
         "(alpha/25)^2": (a / 25.0) ** 2, "(beta/25)^2": (b / 25.0) ** 2,
         "alpha*beta/625": a * b / 625.0}
    for n in names_s:
        cols.append(s[n])
        labels.append(("screen", n, None))
    g3 = np.abs(g) ** 3
    for it, t in enumerate(t_obs):
        ph = t - delay
        t_ = {"g^3": g3,
              "g^3*cos(2*pi*(t_obs-delay)/20)": g3 * np.cos(2 * np.pi * ph / 20.0),
              "g^3*sin(2*pi*(t_obs-delay)/20)": g3 * np.sin(2 * np.pi * ph / 20.0),
              "g^3*cos(2*pi*(t_obs-delay)/40)": g3 * np.cos(2 * np.pi * ph / 40.0),
              "g^3*sin(2*pi*(t_obs-delay)/40)": g3 * np.sin(2 * np.pi * ph / 40.0)}
        for n in names_t:
            cols.append(t_[n])
            labels.append(("transferred", n, it))
    return np.stack(cols, axis=1), labels


def build(profile: str, order: int, fz: dict, grid: DetectorGrid) -> dict:
    rm = read(MAPS / f"{fz['geometry']['id']}_n{order}_{profile}.h5")
    a, b, v = rm.alpha, rm.beta, rm.valid
    cells = M.build_ray_cells(a, b, M.NODAL_DUAL_CLIPPED)

    # One absolute clock. The stored delay was measured from this profile's
    # own latest arrival, so it is re-expressed against the frozen origin and
    # the resulting offset is kept signed.
    t_ref = fz["clock"]["absolute_reference_coordinate_time_M"]
    delay = t_ref - rm.coordinate_time
    shift = t_ref - float(rm.metadata["t_reference"])

    rows, cols, w, acc = ACQ.overlap_triplets(cells, grid, v)
    idx = np.flatnonzero(v)
    pos = np.full(a.size, -1, np.int64)
    pos[idx] = np.arange(idx.size)
    F, labels = fields(a[idx], b[idx], rm.redshift[idx], delay[idx],
                       fz["detector_D026"]["observer_times_M"],
                       fz["field_suite"]["screen_fields"],
                       fz["field_suite"]["transferred_fields"])
    y = np.zeros((grid.n_cells, F.shape[1]))
    np.add.at(y, rows, w[:, None] * F[pos[cols]])
    y /= fz["detector_D026"]["sigma"] * np.sqrt(grid.cell_area)   # whitened

    V = M.valid_matrix(a, b, cells, v)
    on_edge = int((v & ((np.searchsorted(cells.axis_alpha.nodes, a) == 0)
                        | (np.searchsorted(cells.axis_alpha.nodes, a)
                           == cells.axis_alpha.nodes.size - 1)
                        | (np.searchsorted(cells.axis_beta.nodes, b) == 0)
                        | (np.searchsorted(cells.axis_beta.nodes, b)
                           == cells.axis_beta.nodes.size - 1))).sum())
    return {
        "profile": profile, "order": order, "cells": cells, "V": V,
        "response": y, "labels": labels,
        "n_valid": int(v.sum()),
        "corrected_valid_area": float(cells.area[v].sum()),
        "declared_domain_M": [cells.axis_alpha.domain_lo,
                              cells.axis_alpha.domain_hi],
        "clock_shift_from_stored_delay_M": shift,
        "delay_min_under_common_clock": float(delay[idx].min()),
        "delay_max_under_common_clock": float(delay[idx].max()),
        "negative_delay_present": bool(delay[idx].min() < 0),
        "field_of_view": acc,
        "valid_nodes_on_declared_domain_boundary": on_edge,
        "outside_declared_domain":
            "MISSING_DATA_NOT_CERTIFIED_ZERO" if on_edge else
            "CERTIFIED_ZERO_BY_THE_LENSING_BAND_HULL",
    }


def compare(fine: dict, coarse: dict, tol: dict) -> dict:
    yf, yc = fine["response"], coarse["response"]
    labels = fine["labels"]
    n_t = len({l[2] for l in labels if l[0] == "transferred"})
    # per declared field, the whitened response stacked over observer times
    per_field: dict[str, np.ndarray] = {}
    for j, (kind, name, it) in enumerate(labels):
        per_field.setdefault(f"{kind}:{name}", []).append(j)
    const = np.tile(yf[:, 0], max(n_t, 1))
    floor = tol["exact_fixture_relative"] * float(np.linalg.norm(const))

    rows = {}
    for name, js in per_field.items():
        vf = np.concatenate([yf[:, j] for j in js])
        vc = np.concatenate([yc[:, j] for j in js])
        if len(js) == 1:                       # a screen field: same each time
            vf, vc = np.tile(vf, n_t), np.tile(vc, n_t)
        nf = float(np.linalg.norm(vf))
        err = float(np.linalg.norm(vf - vc))
        empty = nf <= floor
        rows[name] = {
            "fine_response_norm": nf, "absolute_difference": err,
            "relative_error": err / max(nf, floor),
            "denominator_is_floor": bool(empty),
            "empty_or_zero_signal": bool(empty),
            "passes": bool(not empty
                           and err / max(nf, floor)
                           < tol["fixed_detector_response_relative"])}

    Af = fine["corrected_valid_area"]
    Ac = coarse["corrected_valid_area"]
    inter = M.region_intersection_area(fine["cells"], fine["V"],
                                       coarse["cells"], coarse["V"])
    union = Af + Ac - inter
    symd = Af + Ac - 2 * inter
    return {
        "pair": f"{coarse['profile']}->{fine['profile']}",
        "order": fine["order"],
        "response": rows,
        "worst_relative_response_error": max(r["relative_error"]
                                             for r in rows.values()),
        "worst_field": max(rows, key=lambda k: rows[k]["relative_error"]),
        "all_fields_pass": all(r["passes"] for r in rows.values()),
        "area": {"coarser": Ac, "finer": Af,
                 "relative_error": abs(Af - Ac) / max(Af, Ac),
                 "passes": bool(abs(Af - Ac) / max(Af, Ac)
                                < tol["corrected_area_relative"])},
        "mask": {"intersection": inter, "union": union,
                 "symmetric_difference": symd,
                 "relative_error": symd / union if union else None,
                 "passes": bool(union and symd / union
                                < tol["mask_symmetric_difference_relative"])},
        "declared_domains_agree":
            fine["declared_domain_M"] == coarse["declared_domain_M"],
        "declared_domains": {coarse["profile"]: coarse["declared_domain_M"],
                             fine["profile"]: fine["declared_domain_M"]},
    }


def main(out_dir: Path, freeze_path: Path) -> int:
    t0 = time.time()
    fz = json.loads(freeze_path.read_text())
    guard = check_freeze(fz)
    out_dir.mkdir(parents=True, exist_ok=False)     # fresh directory guard

    d = fz["detector_D026"]
    grid = DetectorGrid(d["alpha_bounds_M"][0], d["alpha_bounds_M"][1],
                        d["beta_bounds_M"][0], d["beta_bounds_M"][1],
                        d["pitch_M"])
    if [grid.n_alpha, grid.n_beta] != d["cells"]:
        raise SystemExit(f"detector is {[grid.n_alpha, grid.n_beta]}, frozen "
                         f"as {d['cells']}")

    built = {(p, n): build(p, n, fz, grid)
             for p in fz["profiles_compared"] for n in fz["geometry"]["orders"]}
    comps = [compare(built[(f, n)], built[(c, n)], fz["tolerances"])
             for c, f in PAIRS for n in fz["geometry"]["orders"]]

    late = [c for c in comps if c["pair"] == "core->fine"]
    early = [c for c in comps if c["pair"] == "coarse->core"]
    def ok(cs):
        return all(c["all_fields_pass"] and c["area"]["passes"]
                   and c["mask"]["passes"] for c in cs)
    qualified = ok(late) and ok(early)

    conv = {
        "stage": "Q2", "ruling": "PAPER_I_R3A_RULING_026",
        "question": "is the piecewise ray representation accurate enough for "
                    "ONE fixed observation, not whether a changing detector "
                    "reproduces an ideal ray-level norm",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "commit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                 capture_output=True, text=True).stdout.strip(),
        "freeze": {"path": str(freeze_path.relative_to(ROOT)), **guard},
        "detector": grid.to_dict(), "sigma": d["sigma"],
        "observer_times_M": d["observer_times_M"],
        "clock": fz["clock"],
        "tolerances": fz["tolerances"],
        "successive_pairs_required":
            fz["tolerances"]["successive_late_refinement_pairs_required"],
        "pairs_evaluated": [f"{c}->{f}" for c, f in PAIRS],
        "comparisons": [{k: v for k, v in c.items()} for c in comps],
        "both_successive_pairs_qualify": qualified,
        "status": fz["outcome_labels"]["pass"] if qualified
                  else fz["outcome_labels"]["fail"],
        "three_levels_are_not_proof_of_divergence": True,
        "target_modes_inspected": False,
    }
    (out_dir / "FIXED_DETECTOR_PROFILE_CONVERGENCE.json").write_text(
        json.dumps(conv, indent=2) + "\n")

    ledger = {
        "stage": "Q2", "purpose": "boundary, domain and mask accounting kept "
                                  "separate from the response comparison",
        "per_profile_and_order": [
            {k: v for k, v in b.items()
             if k not in ("cells", "V", "response", "labels")}
            for b in built.values()],
        "cropped_flux_against_the_archived_padded_screen": {
            "older_R3A_screen": "alpha [-25.4, 25.4], beta [-25.0, 25.4], "
                                "pitch 0.02",
            "D026": "alpha [-25, 25], beta [-25, 25], pitch 0.4",
            "captured_fraction_by_profile_and_order": {
                f"{b['profile']}_n{b['order']}":
                    b["field_of_view"]["captured_fraction"]
                for b in built.values()},
            "note": "under the corrected measure an order's cells stop at its "
                    "declared domain, so D026 crops nothing the archive "
                    "holds; the padding in the older screen covered ground "
                    "the maps never sampled"},
        "coverage_certification": {
            f"{b['profile']}_n{b['order']}": b["outside_declared_domain"]
            for b in built.values()},
        "mask_and_area_by_pair": [
            {"pair": c["pair"], "order": c["order"], "area": c["area"],
             "mask": c["mask"],
             "declared_domains": c["declared_domains"],
             "declared_domains_agree": c["declared_domains_agree"]}
            for c in comps],
    }
    (out_dir / "BOUNDARY_AND_MASK_ERROR_LEDGER.json").write_text(
        json.dumps(ledger, indent=2) + "\n")

    print(f"D026 {grid.n_alpha}x{grid.n_beta} at {grid.pitch} M, sigma {d['sigma']}")
    for c in comps:
        print(f"  {c['pair']:<14} n{c['order']}  response {c['worst_relative_response_error']:.3e} "
              f"({'pass' if c['all_fields_pass'] else 'FAIL'}, worst {c['worst_field']})"
              f"  area {c['area']['relative_error']:.3e}"
              f" ({'pass' if c['area']['passes'] else 'FAIL'})"
              f"  mask {c['mask']['relative_error']:.3e}"
              f" ({'pass' if c['mask']['passes'] else 'FAIL'})")
    for b in built.values():
        if b["negative_delay_present"]:
            print(f"  {b['profile']} n{b['order']}: delay reaches "
                  f"{b['delay_min_under_common_clock']:+.4f} M under the "
                  f"common clock (shift {b['clock_shift_from_stored_delay_M']:+.4f})")
    print(f"  status {conv['status']}")
    print(f"  runtime {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main((ROOT / sys.argv[1]).resolve(),
                          (ROOT / sys.argv[2]).resolve()))
