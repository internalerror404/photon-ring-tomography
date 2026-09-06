#!/usr/bin/env python3
"""Q1 of ruling 026: specify the corrected measure and prove its units.

Corrected geometry is recorded as a sidecar. No HDF5 archive is rewritten, no
operator is rebuilt, no endpoint is recomputed and no archived number is
rescaled or restated. The only target-related operation performed anywhere in
this stage is the analytical uniform-order-weight bound the ruling allows.
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
from phrt.revision_v4_1 import measure as M                 # noqa: E402

MAPS = ROOT / "artifacts" / "raymaps"
REV = ROOT / "artifacts" / "revisions" / "mahakal_v4_1"
R2_REPLAY = REV / "R2REPLAY_20260906T144528Z_b873908"
R2_MODES = R2_REPLAY / "mode_export.json"
R2_INFO = R2_REPLAY / "reference_geometry_information.csv"
RHO = 1.0
TESTS = ("tests/revision_v4_1/test_c13_measure.py",)


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def arr_sha(a: np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(a, dtype=np.float64)
                          .tobytes()).hexdigest()


def specification() -> dict:
    return {
        "defect": "C13", "ruling": "PAPER_I_R3A_RULING_026", "stage": "Q1",
        "six_quantities_kept_distinct": {
            "nominal_request_pitch": "the dx a generator was asked for; what "
                                     "pixel_area was built from",
            "realized_nodes": "the coordinates the generator returned, "
                              "spacing 2*lims/(N-1) per axis, audited "
                              "separately on alpha and on beta",
            "cell_edges": "four edges per ray; rectangular and of unequal "
                          "area, not one scalar",
            "geometric_area": "the product of the two edge widths",
            "validity_mask": "a binary per-node flag, which cannot represent "
                             "a band boundary that cuts through a cell",
            "effective_quadrature_weight": "what a runner gives a retained "
                                           "ray after subsampling; "
                                           "stratified_subsample assigns "
                                           "stratum_area/n_taken and rescales "
                                           "to the order total, so it is not "
                                           "the ray's footprint",
        },
        "conventions": {
            M.LEGACY_NOMINAL_SQUARE: {
                "definition": "square of side sqrt(pixel_area) on each node",
                "tiles": False,
                "status": "the archive's own claim; preserved for replay, "
                          "never used as the corrected measure"},
            M.NODAL_DUAL_CLIPPED: {
                "definition": "dual cell of each node clipped to the declared "
                              "domain; half-width edges, quarter corners",
                "tiles": True,
                "total_equals": "the declared domain area exactly",
                "status": "ADOPTED for the corrected records",
                "justification": "both generators lay endpoint-inclusive "
                                 "nodes across a declared finite square "
                                 "domain, so the domain, not the node count, "
                                 "is the fixed thing. Clipped dual cells "
                                 "partition exactly that domain and keep it "
                                 "fixed as the pitch changes, which is what "
                                 "lets two profiles be compared on one "
                                 "footing"},
            M.CENTER_CELL_EXTENDED: {
                "definition": "a full cell for every node",
                "tiles": True,
                "total_equals": "an enlarged domain (2*lims + delta)^2",
                "status": "available and measured, NOT adopted",
                "why_not": "it integrates a domain that grows as the pitch "
                           "shrinks, so a profile comparison would change the "
                           "region as well as the resolution. Legitimate only "
                           "with that extended domain declared as the "
                           "intended one, which it is not here"},
        },
        "generator_rules": {
            "aart.lensingbands.grid_mask":
                "np.linspace(-lims, lims, round_up_to_even(2*lims/dx)); "
                "lims = ceil(hull extent + 5*dx), capped at limits",
            "build_raymaps_schwarzschild.band_grid":
                "np.linspace(-lim, lim, int(ceil(2*lim/dx)))",
            "samples_are": "endpoint-inclusive nodes, not cell centres",
            "verified_by": "both rules reproduce every observed node count "
                           "in all 63 archived maps",
        },
        "acquisition_units": {
            "O[d,p]": "|D_d intersect P_p|, brightness to integrated flux",
            "a[p]": "|P_p|, the geometric parent cell area",
            "integrated_parent_signal": "z = a * f",
            "integrated_parent_covariance": "sigma^2 diag(a)",
            "postprocessing_L": "O diag(a)^-1, not O",
            "inherited_covariance": "sigma^2 O diag(1/a) O^T",
            "detector_covariance": "sigma^2 |D_d| per cell per observer time, "
                                   "assigned once after the order sum",
            "two_models_share_a_covariance": False,
            "monotonicity_claimed_only_for": "the matched inherited-noise "
                                             "experiment",
        },
        "integration_device": {
            "chosen": "direct exact overlap of rectangular cells",
            "why": "a ray cell and a detector cell are both axis-aligned "
                   "rectangles, so the intersection is a product of interval "
                   "intersections and is already exact. A nonuniform common "
                   "refinement mesh is permitted but buys nothing here, so "
                   "none is built",
            "is_a_detector": False,
        },
        "not_done_here": [
            "no HDF5 archive rewritten",
            "no operator rebuilt and no runner re-executed",
            "no archived endpoint recomputed, rescaled or restated",
            "no target spectrum, operational count or estimator touched",
        ],
    }


def sidecars() -> tuple[list[dict], dict]:
    rows = []
    for p in sorted(MAPS.glob("*.h5")):
        rm = read(p)
        stored = float(np.unique(rm.pixel_area)[0])
        dual = M.build_ray_cells(rm.alpha, rm.beta, M.NODAL_DUAL_CLIPPED)
        legacy = M.build_ray_cells(rm.alpha, rm.beta, M.LEGACY_NOMINAL_SQUARE,
                                   nominal_side=float(np.sqrt(stored)))
        v = rm.valid
        rows.append({
            "file": p.name, "source_sha256": sha(p),
            "geometry_id": rm.geometry_id, "order": int(rm.order),
            "profile": rm.profile,
            "convention": M.NODAL_DUAL_CLIPPED,
            "derivable_from_source": True,
            "recipe": "measure.build_ray_cells(alpha, beta, "
                      "NODAL_DUAL_CLIPPED) on the archived node arrays",
            "corrected_area_sha256": arr_sha(dual.area),
            "legacy_area_sha256": arr_sha(legacy.area),
            "distinct_corrected_cell_areas":
                int(np.unique(np.round(dual.area, 12)).size),
            "declared_domain_area": dual.domain_area,
            "tiles_declared_domain": dual.tiles_exactly(),
            "total_all_nodes_corrected": float(dual.area.sum()),
            "total_valid_legacy": float(legacy.area[v].sum()),
            "total_valid_corrected": float(dual.area[v].sum()),
            "valid_total_ratio_corrected_over_legacy":
                float(dual.area[v].sum() / legacy.area[v].sum()),
        })
    return rows, {
        "sidecar_form": "a recipe plus a checksum of the derived areas, not a "
                        "copy of them. The cells are a deterministic function "
                        "of node arrays already in the archive, so recording "
                        "the rule and the hash makes any recomputation "
                        "verifiable without duplicating tens of millions of "
                        "edges",
        "archives_rewritten": False,
        "n_maps": len(rows),
    }


def r2_bound(order_ratios: dict[str, float], label: str, certified: bool,
             scope: str) -> dict:
    modes = json.loads(R2_MODES.read_text())["RESOLVED_PHYSICAL"]
    sv = np.array(modes["singular_values"], float)
    r = np.array(list(order_ratios.values()), float)
    lo, hi = float(r.min()), float(r.max())
    iv = [[float(s * np.sqrt(lo)), float(s * np.sqrt(hi))] for s in sv]
    above = [i for i, (a, b) in enumerate(iv) if a > RHO]
    straddle = [i for i, (a, b) in enumerate(iv) if a <= RHO <= b]
    # The full conditional Fisher trace from the accepted replay, not the sum
    # over the three exported modes: those are the leading directions only.
    rows = [r.split(",") for r in R2_INFO.read_text().strip().splitlines()[1:]]
    tr = {float(r[5]) for r in rows if r[0] == "RESOLVED_PHYSICAL"}
    if len(tr) != 1:
        raise SystemExit(f"the archived conditional trace is not unique: {tr}")
    trace = tr.pop()
    return {
        "label": label, "certified": certified, "scope": scope,
        "per_order_weight_ratio": order_ratios,
        "r_min": lo, "r_max": hi,
        "bound": "r_min * F_cond <= F_cond_new <= r_max * F_cond, valid after "
                 "profiling; the nuisance projection is allowed to change",
        "archived_conditional_singular_values": sv.tolist(),
        "singular_value_intervals": iv,
        "directions_certainly_above_rho": above,
        "n_directions_certainly_above_rho": len(above),
        "directions_straddling_rho": straddle,
        "conditional_trace_archived": trace,
        "conditional_trace_source": str(R2_INFO.relative_to(ROOT)),
        "conditional_trace_interval": [trace * lo, trace * hi],
        "rho": RHO,
    }


def main(out_dir: Path) -> int:
    t0 = time.time()
    out_dir.mkdir(parents=True, exist_ok=False)
    spec = specification()
    spec["generated_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    spec["commit"] = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                    capture_output=True,
                                    text=True).stdout.strip()

    rows, meta = sidecars()
    ref = {f"{r['order']}": r for r in rows
           if r["geometry_id"] == "a050_i050" and r["profile"] == "core"}

    # The isolated interior-pitch diagnostic the ruling scopes, and the wider
    # ratio the adopted measure actually implies. They answer different
    # questions and only the first is certified.
    interior = {"0": 1.0, "1": (250 / 249) ** 2, "2": (700 / 699) ** 2}
    adopted = {k: ref[k]["valid_total_ratio_corrected_over_legacy"]
               for k in ("0", "1", "2")}
    spec["scalar_spacing_only_diagnostic"] = r2_bound(
        interior, "INTERIOR_PITCH_ONLY", True,
        "the isolated uniform interior-cell correction. Excludes boundary "
        "clipping, changed masks, new rays, a different detector and any "
        "estimator error. This is the bound the ruling certifies")
    spec["adopted_measure_indicative_bound"] = r2_bound(
        adopted, "NODAL_DUAL_CLIPPED_TOTALS", False,
        "the same inequality applied to the ratio of each order's TOTAL "
        "corrected solid angle. NOT certified: clipped dual cells are not "
        "uniform within an order, so the per-order reweighting they induce "
        "through stratified_subsample is only approximately uniform. Recorded "
        "because it is the direction the adopted measure points, and because "
        "it widens rather than narrows the interval")

    (out_dir / "C13_MEASURE_SPECIFICATION.json").write_text(
        json.dumps(spec, indent=2) + "\n")
    (out_dir / "GEOMETRIC_CELL_SIDECAR_MANIFEST.json").write_text(
        json.dumps({**meta, "maps": rows}, indent=2) + "\n")

    # pytest lives at the system interpreter in this environment, not in the
    # numerics venv, so the suite is run there and the interpreter recorded.
    py = "python3"
    proc = subprocess.run([py, "-m", "pytest", *TESTS, "-q", "--no-header"],
                          cwd=ROOT, capture_output=True, text=True)
    tail = [ln for ln in proc.stdout.strip().splitlines() if "passed" in ln
            or "failed" in ln]
    names = subprocess.run([py, "-m", "pytest", *TESTS, "--collect-only",
                            "-q", "--no-header"], cwd=ROOT,
                           capture_output=True, text=True).stdout
    (out_dir / "C13_UNIT_AND_GEOMETRY_TESTS.json").write_text(json.dumps({
        "suite": list(TESTS),
        "interpreter": py,
        "returncode": proc.returncode,
        "stderr_tail": proc.stderr.strip().splitlines()[-3:],
        "passed": proc.returncode == 0,
        "summary": tail[0] if tail else "not run",
        "collected": [ln.split("::")[-1] for ln in names.splitlines()
                      if "::" in ln],
        "covers": {
            "partition": "P1 clipped dual cells tile the declared domain",
            "endpoint_semantics": "P2 half-width edges and quarter corners; "
                                  "full centre cells enlarge the domain",
            "beta_axis_and_rectangular_cells":
                "P3 unequal alpha and beta spacing are carried separately",
            "non_uniform_refusal": "P4 a non-uniform axis raises, never averages",
            "invalid_mask": "P5 masking removes area and adds none",
            "representation_invariance":
                "P6/P6b subdividing cells that carry the same field moves the "
                "fixed-detector response by less than 1e-12, on a fixture and "
                "on an archived order",
            "acquisition_units":
                "P7 brightness and integrated-flux parents agree on "
                "unequal-area cells, and O in place of L is detectable",
            "inherited_covariance": "P8 equals sigma^2 O diag(1/a) O^T, is "
                                    "symmetric PSD, and differs from the "
                                    "single-sky detector covariance",
            "noise_assigned_once": "P9 per cell per time, after the order sum",
            "zero_area": "P10 refused, not inverted",
            "legacy_vs_corrected": "P11/P12 both measures available, "
                                   "different, and the corrected one "
                                   "partitions the real screens",
        },
    }, indent=2) + "\n")

    b1 = spec["scalar_spacing_only_diagnostic"]
    b2 = spec["adopted_measure_indicative_bound"]
    print(f"{meta['n_maps']} sidecar records, no archive rewritten")
    print(f"  adopted convention {M.NODAL_DUAL_CLIPPED}")
    print(f"  reference core totals corrected/legacy: "
          + ", ".join(f"n{k}={v:.9f}" for k, v in adopted.items()))
    print(f"  R2 certified interior-only bound: r in "
          f"[{b1['r_min']:.9f}, {b1['r_max']:.9f}], directions above rho "
          f"{b1['n_directions_certainly_above_rho']}, trace in "
          f"[{b1['conditional_trace_interval'][0]:.6f}, "
          f"{b1['conditional_trace_interval'][1]:.6f}]")
    print(f"  indicative adopted-measure bound: r in "
          f"[{b2['r_min']:.9f}, {b2['r_max']:.9f}], directions above rho "
          f"{b2['n_directions_certainly_above_rho']}, straddling "
          f"{b2['directions_straddling_rho']}")
    print(f"  unit and geometry tests: {tail[0] if tail else 'not run'}")
    print(f"  runtime {time.time() - t0:.0f}s")
    return 0 if proc.returncode == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main((ROOT / sys.argv[1]).resolve()))
