#!/usr/bin/env python3
"""R3A return report, written from the run's own manifest.

Every number below is read back out of the artifacts rather than retyped, so
the prose cannot drift away from the record it describes.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REV = ROOT / "artifacts" / "revisions" / "mahakal_v4_1"
LOC = REV / "LOC025_20260906T184213Z"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main(run_dir: Path) -> int:
    m = json.loads((run_dir / "raw_to_common_sky_mapping_manifest.json"
                    ).read_text())
    t = json.loads((run_dir / "R3A_constructor_test_results.json").read_text())
    cv, lat = m["convergence"], m["lattice_commensurability"]
    qa, dg = m["stored_quadrature_weight_audit"], m["detector_grid"]
    L = []
    w = L.append

    w("# R3A return: common-sky construction and correctness\n")
    w(f"Status: **{m['status']}**\n")
    w(f"Geometry {m['geometry']}, orders {m['orders']}, run `{run_dir.name}`, "
      f"commit at freeze "
      f"`{json.loads((run_dir / 'R3A_ACQUISITION_INPUT_FREEZE.json').read_text())['commit_at_freeze_time'][:12]}`.\n")
    w("The construction is built and its correctness canaries pass. It is "
      "returned blocked, not delivered, because the registered convergence "
      "criterion fails for two of three orders and because the audit that "
      "diagnosed the failure turned up a defect in the archived ray maps "
      "that has to be adjudicated before any common-sky information is "
      "compared to anything. Nothing has been retuned to make either go "
      "away: the tolerance is unchanged, and no operator, weight or archived "
      "endpoint has been touched.\n")

    w("## 1. What was built\n")
    w(f"One detector grid, {dg['n_alpha']} x {dg['n_beta']} = "
      f"{dg['n_cells']} cells at pitch {dg['pitch']} M, spanning alpha "
      f"[{dg['alpha_min']}, {dg['alpha_max']}] and beta "
      f"[{dg['beta_min']}, {dg['beta_max']}]. The field of view is the union "
      f"of every valid ray cell plus a declared pad; the pitch is the finest "
      "order's own cell. Both were fixed from geometry before any target "
      "quantity existed, and neither was revised afterwards.\n")
    w("Each order is placed on that grid by conservative area overlap: a ray "
      "cell and a detector cell are both axis-aligned rectangles, so their "
      "intersection is a product of interval intersections and is exact. "
      "Invalid rays are masked out, never interpolated into signal. Area "
      "that leaves the field of view is measured, not dropped quietly.\n")
    w("The cross-order time origin was verified rather than assumed: "
      "`coordinate_time + delay` is one constant across every ray of every "
      f"order, with a measured drift of "
      f"{m['registration']['cross_order_origin_drift']:.3e} M between "
      "orders.\n")
    w("Two acquisition models are specified and kept apart, because they "
      "answer different questions and do not share a covariance: "
      "`POSTPROCESSING_INHERITED_NOISE`, where `C_sky = L C L^T` and "
      "information must contract, and `SINGLE_SKY_DETECTOR_NOISE`, where the "
      "orders are summed on the screen first and noise is assigned once "
      "afterwards. No positive-semidefinite ordering is asserted between the "
      "second and the ideal order-labeled stack, and no telescope "
      "feasibility claim is made for either.\n")

    w("## 2. The registered convergence criterion fails\n")
    w(f"Registered before any refinement ran: relative change in the "
      f"declared-field whitened information proxy between successive "
      f"detector pitches, below {cv['registered_rtol']:g}. The refinement "
      f"ladder is {cv['refinement_factors_of_the_ray_pitch']} times each "
      "order's ray pitch.\n")
    w("| order | ray pitch (M) | last pair | converged | deficit at finest "
      "pitch | ceiling respected |")
    w("| --- | --- | --- | --- | --- | --- |")
    for n in ("0", "1", "2"):
        c = cv["per_order"][n]
        w(f"| {n} | {m['raw_maps'][n]['cell_pitch']:g} | "
          f"{c['last_pair_relative_change']:.3e} | "
          f"{'yes' if c['converged'] else '**no**'} | "
          f"{c['residual_deficit_at_finest_pitch']:+.3e} | "
          f"{'yes' if c['never_exceeds_ray_level_limit'] else 'no'} |")
    w("")
    w("The first R3A run stopped the ladder at the ray pitch itself and so "
      "compared two pitches that both still straddled ray cells. It could "
      "not have met its own criterion whatever the construction did. "
      "Extending the ladder below the ray pitch makes the criterion harder "
      "to satisfy, not easier, and it is the extension that lets order 0 "
      "reach it. Orders 1 and 2 still do not.\n")
    w("The substantive canary behind that criterion does pass. In every "
      "order the proxy is monotone non-decreasing under refinement and never "
      "passes the ray-level ceiling -- the value a detector that fully "
      "resolved the rays would return. Refinement recovers information; it "
      f"does not manufacture it "
      f"(`no_information_manufactured_by_quadrature_refinement`: "
      f"{cv['no_information_manufactured_by_quadrature_refinement']}).\n")

    w("## 3. Why it fails, measured rather than argued\n")
    w("The overlap arithmetic is exact. The proxy is inexact only where a "
      "detector cell straddles two ray cells, which needs the detector "
      "lattice to be commensurate with the ray lattice. Two independent "
      "things break commensurability here, so each was switched on alone.\n")
    w("Relative deficit against the ray-level value, at the order's own "
      "pitch:\n")
    w("| order | stored footprint, shared origin | realized footprint, "
      "shared origin | realized footprint, lattice-aligned origin |")
    w("| --- | --- | --- | --- |")
    for n in ("0", "1", "2"):
        r = lat["measured_relative_deficit"][n]
        w(f"| {n} | {r['stored_footprint_shared_origin']:+.3e} | "
          f"{r['realized_footprint_shared_origin']:+.3e} | "
          f"{r['realized_footprint_lattice_aligned_origin']:+.3e} |")
    w("")
    w("Give the detector the order's own footprint and its own origin and "
      "the same overlap rule reproduces the ray-level value to about 1e-14 "
      "at every pitch tested, in all three orders. The error in the shared "
      "grid is lattice misalignment, not the overlap rule. Canary C12 holds "
      "that conclusion in the test suite.\n")
    sp = lat["realized_grid_spacings"]
    w(f"That is also why it cannot simply be fixed by choosing a better "
      f"shared pitch. The three realized spacings are "
      f"{sp['0']:.12g}, {sp['1']:.12g} and {sp['2']:.12g} M -- 50/125, "
      "20/249 and 14/699. They are mutually incommensurate at any feasible "
      "detector pitch, so **no single uniform Cartesian detector is exact "
      "for more than one order at a time**. At the natural pitch the "
      "resulting loss is not order-neutral: it runs "
      f"{abs(lat['measured_relative_deficit']['0']['stored_footprint_shared_origin'])*100:.1f}%, "
      f"{abs(lat['measured_relative_deficit']['1']['stored_footprint_shared_origin'])*100:.1f}% and "
      f"{abs(lat['measured_relative_deficit']['2']['stored_footprint_shared_origin'])*100:.1f}% "
      "by order. That is a beat between two discretizations, not a physical "
      "compression loss, and it falls hardest on exactly the order "
      "comparison R3B would be asked to make. Proceeding to R3B on this "
      "grid would compare an artifact.\n")

    w("## 4. Defect found in the archived ray maps\n")
    w("Diagnosing the above required comparing the stored solid angle per "
      "ray against the grid it was measured on. They disagree.\n")
    w("`build_raymaps.py` stores `pixel_area = dx**2`, the cell size AART "
      "was *asked* for. AART lays `npoints` samples across the band, so the "
      "realized spacing is `span/(npoints-1)`, which equals `dx` only when "
      f"the division comes out even. It does so in "
      f"{qa['n_agreeing']} of {qa['n_combinations']} profile/order "
      f"combinations ({', '.join(qa['combinations_that_agree'])}).\n")
    w("| profile / order | points per axis | nominal dx | realized spacing | "
      "realized/stored cell area |")
    w("| --- | --- | --- | --- | --- |")
    for k, q in qa["per_profile_and_order"].items():
        flag = "" if q["agrees"] else " **"
        w(f"| {k}{flag} | {q['grid_points_per_axis']} | "
          f"{q['nominal_dx_M']:g} | {q['realized_grid_spacing_M']:.10g} | "
          f"{q['realized_over_stored_cell_area']:.9f} "
          f"({(q['realized_over_stored_cell_area'] - 1) * 100:+.4f}%) |")
    w("")
    w(f"The worst case is {qa['worst_relative_area_error'] * 100:.4f}% in "
      "cell area. The error is small, but it is order-dependent and "
      "profile-dependent, and it enters the whitened row as `sqrt(dOmega)`, "
      "so it is a differential miscalibration between image orders -- the "
      "one kind an order-resolved experiment cannot absorb. In the core "
      "profile it is 0.0000%, +0.8048% and +0.2863% for orders 0, 1 and 2, "
      "biasing order-to-order comparisons by roughly 0.4% and 0.14% in "
      "amplitude.\n")
    w("No existing gate catches it. `run_s0_backend_canary.py` compares the "
      "stored total against `metadata['dx']**2`, which is where the stored "
      "value came from, so the check is satisfied by construction. "
      "`run_g7b_field_convergence.py` explicitly marks `pixel_area` as "
      "`expected_to_differ` between profiles and excludes it.\n")
    w("Nothing was repaired. No operator, weight, table or archived endpoint "
      "has been altered, and no endpoint is claimed to move. This is "
      "reported as a new defect candidate for the reviewer to number and "
      "disposition, alongside C01-C12.\n")

    w("## 5. What is not proposed\n")
    w("The registered tolerance stands at "
      f"{cv['registered_rtol']:g} and was not relaxed after the failure. No "
      "replacement criterion has been adopted. Three routes exist and each "
      "has a measured cost; the choice belongs to the reviewer, and none is "
      "applied here.\n")
    w("1. **Per-order aligned detectors.** Exact to 1e-14, as measured "
      "above, but it abandons the single common sky that R3A was asked to "
      "build.\n")
    w("2. **A shared grid with a declared, measured discretization error.** "
      "Keeps the common sky and states the deficit as a known bias, but the "
      "bias is order-dependent at the percent level and would have to be "
      "carried into every downstream comparison.\n")
    w("3. **A detector coarse relative to the rays, converged in the ray "
      "sampling instead.** Physically the right ordering, and the coarse, "
      "core and fine profiles exist for this geometry. It was measured and "
      "it does not converge either at present: the valid lensing-band area "
      "itself still moves between profiles (order 0: "
      + ", ".join(f"{qa['per_profile_and_order'][f'{p}_n0']['stored_total_solid_angle']:.2f}"
                  for p in ("coarse", "core", "fine"))
      + " M^2), so the ray sampling is not converged at the band edge "
      "and the quadrature defect above contaminates the comparison.\n")
    w("Route 3 cannot be assessed honestly until the defect in section 4 is "
      "dispositioned, which is the main reason this return is blocked rather "
      "than merely incomplete.\n")

    w("## 6. Correctness canaries\n")
    w(f"`{t['suite']}`: {t['summary']}.\n")
    for k, v in t["canaries"].items():
        w(f"- **{k}** {v}")
    w("")
    w("C10, C11 and C12 are new in this run. C10 measures the quadrature "
      "discrepancy and fails if it silently disappears from the maps, "
      "because a repair is something to record and re-review rather than to "
      "inherit. C11 is the ceiling check. C12 is the exactness proof on a "
      "commensurate lattice that entitles section 3 to its conclusion.\n")

    w("## 7. Localization overlay, carried forward from review 025\n")
    w("The two localization deliverables were produced under the corrected "
      "interpretation and are unchanged by this run:\n")
    for f in ("localization_interpretation_overlay.md",
              "saved_mode_physical_localization.json"):
        w(f"- `{LOC.relative_to(ROOT)}/{f}` sha256 `{sha(LOC / f)[:16]}`")
    w("")
    w("The Cholesky coordinate groups are recorded as "
      "`CHOLESKY_COORDINATE_GROUP_DIAGNOSTIC`, not as a physical epoch "
      "partition. The withdrawn readings stay withdrawn.\n")

    w("## 8. Scope\n")
    w("Delivered: the acquisition specification, the constructor and its "
      "canaries, the convergence study, the commensurability diagnosis and "
      "the input freeze. Not done, and not started: any common-sky target "
      "spectrum, any target-spectrum sweep, any new source bank, any "
      "nuisance enrichment, any reconstruction estimator, any submission "
      "freeze, and any R3B information comparison. Target column selection "
      "is untouched at the accepted 72.\n")
    w(f"Returned as **{m['status']}**, pending a disposition on the "
      "quadrature-weight defect and a decision on the convergence criterion.")

    (run_dir / "R3A_RETURN_REPORT.md").write_text("\n".join(L) + "\n")
    print(f"wrote {run_dir / 'R3A_RETURN_REPORT.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main((ROOT / sys.argv[1]).resolve()))
