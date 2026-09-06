#!/usr/bin/env python3
"""Q0 second output: where the stored weight goes, and what depends on it.

Written from the inventory and from the source tree, so the dependency list
is the one the code actually has rather than the one the campaign remembers.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# Roles are assigned per file, from reading each site. The distinction that
# matters is narrow: exactly one path turns the stored weight into an operator
# row, and everything physical depends on C13 through that path alone.
ROLES = {
    "scripts/build_raymaps.py": (
        "GENERATOR", "writes pixel_area = dx**2 from the requested pitch, "
        "beside coordinates AART returned on a different pitch"),
    "scripts/build_raymaps_schwarzschild.py": (
        "GENERATOR", "same, for the kgeo cross-tracer maps"),
    "src/phrt/geometry/raymap.py": (
        "SCHEMA", "declares the field and reports total_quadrature_area; "
        "documents it as dx_n^2, which is the claim C13 disputes"),
    "src/phrt/geometry/sampling.py": (
        "OPERATOR_QUADRATURE", "the only path from the stored weight to an "
        "operator row. stratified_subsample gives each retained ray "
        "stratum_area/n_taken and then rescales so the order's TOTAL solid "
        "angle is preserved, so what reaches the operator is the per-order "
        "total, not the per-ray footprint"),
    "scripts/run_s0_backend_canary.py": (
        "GATE", "checks the stored total against metadata['dx']**2, the "
        "value it was built from, so it cannot detect C13"),
    "scripts/run_g7b_field_convergence.py": (
        "GATE", "field convergence across profiles; excludes pixel_area by "
        "name as expected_to_differ, so it is not an area audit"),
    "scripts/run_g10q_quadrature_invariance.py": (
        "GATE", "quadrature invariance under resampling at fixed measure"),
    "scripts/run_g5ab_instrumentation.py": (
        "GATE", "instrumentation totals"),
    "scripts/run_e3_validation.py": ("DIAGNOSTIC", "pilot cross-profile table"),
    "scripts/run_delay_quantiles.py": ("DIAGNOSTIC", "area-weighted delay quantiles"),
    "scripts/run_production_grid.py": ("DIAGNOSTIC", "per-geometry reported totals"),
    "scripts/build_e3c_freeze.py": ("FREEZE", "records the operator grid"),
    "tests/test_e3_pilot_products.py": (
        "TEST", "asserts pixel_area == dx**2, which pins the archive to the "
        "nominal value and will fail on a corrected map by design"),
    "tests/test_raymap_schema.py": ("TEST", "schema fixtures only"),
    "tests/revision_v4_1/test_r3a_construction.py": (
        "TEST", "R3A canaries, including C10 which measures the discrepancy"),
    "scripts/revision_v4_1/r3a_build.py": ("REVIEW_TOOLING", "R3A construction"),
    "scripts/revision_v4_1/r3a_return_report.py": ("REVIEW_TOOLING", "R3A report"),
    "scripts/revision_v4_1/q0_measure_inventory.py": ("REVIEW_TOOLING", "this audit"),
    "src/phrt/revision_v4_1/measure.py": ("REVIEW_TOOLING", "the corrected measure"),
}

# Claim families reached through the operator path, with the artifact that
# carries each. Every one of them inherits the per-order total solid angle.
CLAIMS = [
    ("E3B", "order-resolved reach and depth curves", "artifacts/reports"),
    ("E3C", "twelve-geometry operator audit and stored spectra", "artifacts/tables"),
    ("E3D", "nested source-class stress", "artifacts/tables"),
    ("R0/R0C", "rank, null space and calibration split", "artifacts/reports"),
    ("R1", "level and structure reconstruction endpoints", "artifacts/tables"),
    ("R1L", "localized temporal bases, stages 1 and 2R", "artifacts/tables"),
    ("HMT-1/HMT-2", "held-out historical inverse results", "artifacts/tables"),
    ("R2", "nuisance-adjusted conditional information", "artifacts/revisions"),
]


def main(out_dir: Path) -> int:
    inv = json.loads((out_dir / "C13_MAP_MEASURE_INVENTORY.json").read_text())
    maps = inv["maps"]
    ref = {m["file"]: m for m in maps}
    by_file: dict[str, int] = {}
    for r in inv["stored_weight_consumers"]:
        by_file[r["file"]] = by_file.get(r["file"], 0) + 1

    L = []
    w = L.append
    w("# C13 claim dependency overlay\n")
    w("Ruling 026, phase Q0. An audit of what is already in the tree. No map, "
      "operator, weight, table or endpoint is altered by this document, and "
      "no archived number is recomputed or declared changed.\n")

    w("## The two descriptions that disagree\n")
    w("`build_raymaps.py` stores `pixel_area = dx**2` from the pitch the "
      "generator was asked for. Both generators lay endpoint-inclusive nodes "
      "across a declared finite square domain and derive their own count, so "
      "the realized spacing is `2*lims/(N-1)`:\n")
    w("- `aart.lensingbands.grid_mask`: `linspace(-lims, lims, "
      "round_up_to_even(2*lims/dx))`")
    w("- `build_raymaps_schwarzschild.band_grid`: `linspace(-lim, lim, "
      "ceil(2*lim/dx))`\n")
    w(f"Both rules reproduce every observed node count in the archive "
      f"({inv['summary']['generator_rule_reproduces_every_node_count']}), so "
      "the sampling semantics are settled from the generators rather than "
      "inferred from the numbers. The samples are nodes, not cell centres. "
      "Every axis is uniform and, in every archived map, alpha and beta share "
      "a spacing -- checked separately, because a rectangular grid would make "
      "a single `delta` silently wrong in one direction.\n")
    w(f"The stored weight matches the realized geometry in "
      f"{inv['summary']['maps_where_stored_weight_matches_realized_geometry']}"
      f" of {inv['n_maps']} maps and disagrees in "
      f"{inv['summary']['maps_where_it_does_not']}, worst case "
      f"{inv['summary']['worst_relative_area_error']:.4%} in cell area.\n")

    w("## Where the weight is read\n")
    w("| file | sites | role | what it does with the weight |")
    w("| --- | ---: | --- | --- |")
    for f in sorted(by_file):
        role, note = ROLES.get(f, ("UNCLASSIFIED", "not yet classified"))
        w(f"| `{f}` | {by_file[f]} | {role} | {note} |")
    w("")
    w("Only `src/phrt/geometry/sampling.py` carries the weight into an "
      "operator. It preserves each order's **total** solid angle and "
      "distributes it over retained rays as `stratum_area / n_taken`, so a "
      "retained ray's operator weight is already not its geometric footprint. "
      "That is the distinction the corrected records must keep: nominal "
      "request pitch, realized nodes, cell edges, geometric area, validity "
      "mask, and effective quadrature weight after subsampling are six "
      "different things.\n")

    w("## What the reference geometry's totals actually do\n")
    w("Per-order valid solid angle at a050_i050, split into the three causes "
      "the ruling asks be kept apart. `interior weight` is the realized "
      "spacing replacing the nominal pitch; `domain boundary` is dual-cell "
      "clipping at the declared screen edge; the mask is unchanged "
      "throughout.\n")
    w("| map | legacy total | interior weight | domain boundary | corrected "
      "total | net | band-edge area share |")
    w("| --- | ---: | ---: | ---: | ---: | ---: | ---: |")
    for n in (0, 1, 2):
        for prof in ("coarse", "core", "fine"):
            m = ref.get(f"a050_i050_n{n}_{prof}.h5")
            if m is None:
                continue
            d = m["valid_area_decomposition"]
            k = m["mask_geometry"]
            w(f"| n{n} {prof} | {d['legacy_stored']:.4f} | "
              f"{d['delta_from_interior_weight']:+.4f} | "
              f"{d['delta_from_domain_boundary_clipping']:+.4f} | "
              f"{d['nodal_dual_clipped']:.4f} | "
              f"{d['relative_total_change']:+.4%} | "
              f"{k['valid_band_edge_area_fraction']:.2%} |")
    w("")
    w("Two things in that table were not visible before this audit. Order 0's "
      "correction is dominated by **boundary clipping**, not by the interior "
      "pitch: its core map has an exact 0.4 M spacing, so the interior term "
      "is identically zero, and the whole -1.20% comes from the valid band "
      "reaching the declared screen edge where dual cells are half-width. And "
      "the share of each order's area sitting in cells on the lensing-band "
      "edge -- where a binary node mask cannot represent a boundary that cuts "
      "through a cell -- is 1.5% for order 0 but 57.8% for order 2 at the core "
      "profile. The n=2 band is two to three cells thick. That is a property "
      "of the sampling, and it is the quantity a fixed-detector refinement "
      "study has to resolve.\n")

    w("## Claims that inherit the per-order total\n")
    w("Every result built through the operator path inherits each order's "
      "total solid angle, and therefore inherits C13. Listing them is a "
      "dependency statement, not a claim that any number moves:\n")
    for tag, what, where in CLAIMS:
        w(f"- **{tag}** -- {what} (`{where}`)")
    w("")
    w("The direction of the effect is order-dependent, which is why it "
      "cannot be absorbed into a common normalization: at the core profile "
      "the corrected per-order totals move by "
      + ", ".join(
          f"{ref[f'a050_i050_n{n}_core.h5']['valid_area_decomposition']['relative_total_change']:+.4%}"
          f" (n={n})" for n in (0, 1, 2))
      + ". Half of each in amplitude, since the whitened row carries "
        "`sqrt(dOmega)`.\n")

    w("## Gates that cannot see this\n")
    w("- `run_s0_backend_canary.py` compares the stored total against "
      "`metadata['dx']**2`. That is the quantity the stored value was "
      "constructed from, so the check passes by construction and is not "
      "independent evidence of the geometry.\n")
    w("- `run_g7b_field_convergence.py` lists `pixel_area` as "
      "`expected_to_differ` between profiles and excludes it. A field "
      "convergence test that excludes area is not an area audit.\n")
    w("- `tests/test_e3_pilot_products.py` asserts `pixel_area == dx**2`. It "
      "is correct about the archive as built and will fail against any "
      "corrected map, by design. It is kept, under its own name, as a record "
      "of the legacy measure rather than as a check on the corrected one.\n")
    w("These remain part of the historical record and keep their results. "
      "None of them is retitled or repurposed into evidence for the "
      "corrected measure.\n")

    w("## Status\n")
    w("C13 is a confirmed geometry/weight inconsistency. Q0 establishes its "
      "extent and its dependency graph. It does not establish that any "
      "archived endpoint changes, and no such claim is made here. Physical "
      "revalidation under the corrected measure is the later task; the "
      "narrow analytical bound on R2 is recorded in Q1.\n")
    w(f"Generated from `C13_MAP_MEASURE_INVENTORY.json` at commit "
      f"`{inv['commit'][:12]}`.")

    (out_dir / "C13_CLAIM_DEPENDENCY_OVERLAY.md").write_text("\n".join(L) + "\n")
    unclassified = [f for f in by_file if f not in ROLES]
    if unclassified:
        raise SystemExit(f"unclassified consumer files: {unclassified}")
    print(f"wrote {out_dir / 'C13_CLAIM_DEPENDENCY_OVERLAY.md'} "
          f"({len(by_file)} consumer files, all classified)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main((ROOT / sys.argv[1]).resolve()))
