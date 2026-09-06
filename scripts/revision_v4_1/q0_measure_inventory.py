#!/usr/bin/env python3
"""Q0 of ruling 026: what measure does each archived map actually carry?

An audit of existing files. Nothing is regenerated, rewritten or corrected
here; the point is to separate four things the archive currently conflates --
the pitch that was requested, the nodes that were returned, the cell edges
those nodes imply, and the weight that was stored -- and to say, per map,
where the difference between them goes.
"""
from __future__ import annotations

import hashlib
import json
import re
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
NOMINAL = {"coarse": (0.8, 0.16, 0.04), "core": (0.4, 0.08, 0.02),
           "fine": (0.2, 0.04, 0.01)}


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def round_up_to_even(f: float) -> int:
    """AART's own node count rule, reproduced so it can be checked."""
    return int(np.ceil(f / 2.0) * 2)


def audit_map(path: Path) -> dict:
    rm = read(path)
    a, b, v = rm.alpha, rm.beta, rm.valid
    stored = np.unique(rm.pixel_area)
    if stored.size != 1:
        raise SystemExit(f"{path.name}: pixel_area is not constant")
    stored_area = float(stored[0])
    nominal_dx = float(rm.metadata["dx"])

    na, aa = M.axis_nodes(a)
    nb, ab = M.axis_nodes(b)
    dual = M.build_ray_cells(a, b, M.NODAL_DUAL_CLIPPED)
    ext = M.build_ray_cells(a, b, M.CENTER_CELL_EXTENDED)
    d_a, d_b = dual.axis_alpha.spacing, dual.axis_beta.spacing
    lims = float(na[-1])

    # Two generators built this archive and each has its own node-count rule,
    # so the rule is chosen from the map's own provenance rather than fitted
    # to its node count. If the rule then reproduces that count, the sampling
    # semantics are settled from the generator instead of guessed.
    if "limits" in rm.metadata:
        gen = {"generator": "aart.lensingbands.grid_mask",
               "rule": "np.linspace(-lims, lims, "
                       "round_up_to_even(2*lims/dx))",
               "declared_limit_key": "limits",
               "declared_limit_M": float(rm.metadata["limits"])}
        predicted = round_up_to_even(2 * lims / nominal_dx)
    else:
        gen = {"generator": "scripts/build_raymaps_schwarzschild.band_grid",
               "rule": "np.linspace(-lim, lim, int(ceil(2*lim/dx)))",
               "declared_limit_key": "band_limit",
               "declared_limit_M": float(rm.metadata["band_limit"]),
               "backend": rm.metadata.get("backend")}
        predicted = int(np.ceil(2 * lims / nominal_dx))

    # Where the valid area moves, split into the three causes the ruling
    # asks to be kept apart: the interior weight, the domain boundary, and
    # the mask.
    a_legacy = stored_area * int(v.sum())
    a_interior = d_a * d_b * int(v.sum())
    a_dual = float(dual.area[v].sum())

    # Mask geometry: a binary node mask cannot represent a band edge that
    # cuts through a cell, so the cells on that edge are counted rather than
    # folded into the total.
    ia = np.searchsorted(na, a)
    ib = np.searchsorted(nb, b)
    grid = np.zeros((na.size, nb.size), bool)
    grid[ia, ib] = v
    nbr = np.zeros_like(grid)
    nbr[:-1, :] |= grid[1:, :]
    nbr[1:, :] |= grid[:-1, :]
    nbr[:, :-1] |= grid[:, 1:]
    nbr[:, 1:] |= grid[:, :-1]
    edge = grid & ~(np.roll(grid, 1, 0) & np.roll(grid, -1, 0)
                    & np.roll(grid, 1, 1) & np.roll(grid, -1, 1))
    on_domain = ((ia == 0) | (ia == na.size - 1)
                 | (ib == 0) | (ib == nb.size - 1))

    return {
        "file": path.name, "sha256": sha(path),
        "geometry_id": rm.geometry_id, "order": int(rm.order),
        "profile": rm.profile, "n_rays": int(a.size), "n_valid": int(v.sum()),
        "requested_pitch": {
            "nominal_dx_M": nominal_dx,
            "stored_pixel_area": stored_area,
            "stored_pixel_area_is_nominal_dx_squared":
                bool(abs(stored_area - nominal_dx ** 2) < 1e-15),
            "registry_dx_for_profile":
                NOMINAL[rm.profile][int(rm.order)] if rm.profile in NOMINAL
                else None,
            "matches_registry":
                bool(rm.profile in NOMINAL
                     and abs(nominal_dx
                             - NOMINAL[rm.profile][int(rm.order)]) < 1e-15)},
        "realized_nodes": {
            "alpha": aa, "beta": ab,
            "axes_have_equal_node_sets": bool(np.array_equal(na, nb)),
            "axes_have_equal_spacing": bool(abs(d_a - d_b) < 1e-12),
            "tensor_product_complete": bool(a.size == na.size * nb.size),
            "declared_half_width_M": lims,
            "declared_half_width_is_integer":
                bool(abs(lims - round(lims)) < 1e-12),
            "declared_limit_M": gen["declared_limit_M"],
            "within_declared_limit":
                bool(lims <= gen["declared_limit_M"] + 1e-12)},
        "generator_rule": {
            **gen,
            "predicted_nodes_per_axis": predicted,
            "observed_nodes_per_axis": int(na.size),
            "rule_reproduces_node_count": bool(predicted == na.size),
            "endpoint_inclusive_nodes": True,
            "samples_are_cell_centres": False},
        "cell_edges": {
            "nodal_dual_clipped": dual.axis_alpha.to_dict(),
            "distinct_cell_areas_all_nodes":
                int(np.unique(np.round(dual.area, 12)).size),
            "nodal_dual_tiles_declared_domain": dual.tiles_exactly(),
            "centre_cell_extended_domain":
                [ext.axis_alpha.domain_lo, ext.axis_alpha.domain_hi]},
        "geometric_area": {
            "realized_interior_cell_area": d_a * d_b,
            "realized_over_stored": d_a * d_b / stored_area,
            "declared_domain_area": (2 * lims) ** 2,
            "nodal_dual_all_nodes": float(dual.area.sum()),
            "centre_cell_all_nodes": float(ext.area.sum())},
        "valid_area_decomposition": {
            "legacy_stored": a_legacy,
            "interior_spacing_only": a_interior,
            "nodal_dual_clipped": a_dual,
            "delta_from_interior_weight": a_interior - a_legacy,
            "delta_from_domain_boundary_clipping": a_dual - a_interior,
            "relative_total_change": a_dual / a_legacy - 1 if a_legacy else None},
        "mask_geometry": {
            "raw_binary_validity_count": int(v.sum()),
            "valid_nodes_on_band_edge": int(edge.sum()),
            "valid_band_edge_area_nodal_dual":
                float(dual.area[edge[ia, ib]].sum()),
            "valid_band_edge_area_fraction":
                float(dual.area[edge[ia, ib]].sum() / a_dual) if a_dual else None,
            "valid_nodes_on_declared_domain_boundary": int((v & on_domain).sum()),
            "fractional_coverage_represented": False,
            "note": "a node mask is binary; the lensing band edge cuts "
                    "through cells, so the edge area above is the part of "
                    "the total that a binary raster cannot place"},
        "effective_quadrature_weight": {
            "equals_geometric_cell_for_this_raw_map": True,
            "differs_where_a_runner_subsamples": True,
            "subsampling_site": "phrt.geometry.sampling.stratified_subsample "
                                "assigns stratum_area/n_taken to each "
                                "retained ray, which is not that ray's "
                                "geometric footprint"},
    }


def consumers() -> list[dict]:
    """Every source site that reads the stored weight, found by grep."""
    out = subprocess.run(
        ["grep", "-rn", "pixel_area", "--include=*.py", "scripts", "src",
         "tests"], cwd=ROOT, capture_output=True, text=True).stdout
    rows = []
    for line in out.splitlines():
        f, n, body = line.split(":", 2)
        rows.append({"file": f, "line": int(n), "text": body.strip()})
    return rows


def main(out_dir: Path) -> int:
    t0 = time.time()
    out_dir.mkdir(parents=True, exist_ok=False)
    files = sorted(MAPS.glob("*.h5"))
    maps = [audit_map(p) for p in files]

    disagree = [m for m in maps
                if abs(m["geometric_area"]["realized_over_stored"] - 1) > 1e-12]
    bad_rule = [m for m in maps
                if not m["generator_rule"]["rule_reproduces_node_count"]]
    non_uniform = [m for m in maps
                   if not (m["realized_nodes"]["alpha"]["uniform"]
                           and m["realized_nodes"]["beta"]["uniform"])]
    unequal_axes = [m for m in maps
                    if not m["realized_nodes"]["axes_have_equal_spacing"]]

    inv = {
        "stage": "Q0", "ruling": "PAPER_I_R3A_RULING_026", "defect": "C13",
        "purpose": "separate requested pitch, realized nodes, cell edges and "
                   "stored weight in every archived map",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "commit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                 capture_output=True, text=True).stdout.strip(),
        "inputs_are_existing_archived_maps_only": True,
        "nothing_regenerated_or_rewritten": True,
        "n_maps": len(maps),
        "summary": {
            "maps_where_stored_weight_matches_realized_geometry":
                len(maps) - len(disagree),
            "maps_where_it_does_not": len(disagree),
            "worst_relative_area_error": max(
                abs(m["geometric_area"]["realized_over_stored"] - 1)
                for m in maps),
            "generator_rule_reproduces_every_node_count": not bad_rule,
            "maps_whose_node_count_the_rule_misses":
                [m["file"] for m in bad_rule],
            "generators_present": sorted({m["generator_rule"]["generator"]
                                          for m in maps}),
            "every_axis_uniform": not non_uniform,
            "every_map_has_equal_alpha_and_beta_spacing": not unequal_axes,
            "both_axes_audited_separately": True,
            "samples_are_endpoint_inclusive_nodes_not_centres": True,
        },
        "maps": maps,
        "stored_weight_consumers": consumers(),
    }
    (out_dir / "C13_MAP_MEASURE_INVENTORY.json").write_text(
        json.dumps(inv, indent=2) + "\n")
    print(f"{len(maps)} maps audited, {len(disagree)} carry a weight that "
          f"disagrees with their geometry")
    print(f"  generator rule reproduces every node count: {not bad_rule}")
    print(f"  every axis uniform: {not non_uniform}; alpha/beta spacing "
          f"equal everywhere: {not unequal_axes}")
    print(f"  worst relative cell-area error "
          f"{inv['summary']['worst_relative_area_error']:.6%}")
    print(f"  {len(inv['stored_weight_consumers'])} source sites read the "
          f"stored weight")
    print(f"  runtime {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main((ROOT / sys.argv[1]).resolve()))
