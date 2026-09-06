#!/usr/bin/env python3
"""The ruling 027 return report, written from the stage artifacts."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SUP = "SUPPORTED_BY_VALID_CENTRE_RAY"
ANN = "CENTRE_OUTSIDE_DECLARED_EMISSION_ANNULUS"
UNR = "CENTRE_SOLVER_UNRESOLVED"
MIS = "MISSING_TRANSFER_SUPPORT"


def main(h0: Path, h1: Path, h2: Path, out: Path) -> int:
    man = json.loads((h0 / "HULL_SOURCE_AND_VALIDITY_MANIFEST_027.json").read_text())
    sup = json.loads((h0 / "MISSING_TRANSFER_SUPPORT_027.json").read_text())
    clip = json.loads((h0 / "FRACTIONAL_CLIPPING_TESTS_027.json").read_text())
    hc = json.loads((h1 / "HULL_CONVERGENCE_027.json").read_text())
    vp = h2 / "FRACTIONAL_FIXED_DETECTOR_VALIDATION_027.json"
    val = json.loads(vp.read_text()) if vp.exists() else None
    comp = json.loads((out / "FRACTIONAL_COVERAGE_027_COMPLETION.json").read_text())
    fz = json.loads((out / "FRACTIONAL_COVERAGE_027_INPUT_FREEZE.json").read_text())
    st = comp["separate_statuses"]

    lines = []
    w = lines.append
    w("# Fractional coverage return: H0, H1 and H2\n")
    w(f"Status: **{comp['return_status']}**  \n"
      f"Blockers: **{', '.join(comp['blockers']) or 'none'}**\n")
    w("| component | status |")
    w("| --- | --- |")
    for k, v in st.items():
        w(f"| {k.replace('_', ' ')} | **{v}** |")
    w("")
    w("R3B is not authorized and was not begun. No target spectrum, "
      "operational count or estimator was inspected.\n")

    w("## 1. Corrections accepted\n")
    w("**\"Provably cannot qualify\" is withdrawn.** The 11.7x figure came "
      "from a rate fitted to two comparisons plus a cost model for boundary "
      "refinement. It is a projection under that model, not a lower bound "
      "over all representations, and it is now labelled "
      "`MODEL_BASED_BINARY_RASTER_COST_PROJECTION`. The numbers stand; the "
      "universal wording does not. The qualification matters precisely "
      "because fractional coverage changes the representation the "
      "extrapolation rested on.\n")
    w("**The overlap is the triple intersection, not a scaled fraction.** "
      "`O[d,p] = |D_d ^ C_p ^ Omega_n|` is what is implemented. The "
      "whole-cell emitting fraction is computed as a diagnostic and never "
      "used as a weight. Canary F1 is the reviewer's counterexample as a "
      "standing test: the clipped overlap puts (0.2, 0) across two "
      "half-width pixels and the substitution puts (0.1, 0.1) -- identical "
      "totals, different image. A conservation check alone would have passed "
      "the wrong construction.\n")
    w("**Geometry is not availability is not accuracy.** Those three are "
      "separated throughout, and the finding below is that the second is the "
      "binding one.\n")

    w("## 2. H0: the kernel, the hulls, and what the hulls do not cover\n")
    w(f"`{clip['suite']}` and `{clip['plus']}`: {clip['summary']}. The "
      "clipping kernel integrates the vertical slice length with breakpoints "
      "at vertices, at grid lines in x, and wherever the boundary crosses a "
      "grid line in y, so midpoint times width is exact -- including across "
      "vertical edges and repeated vertices. Canaries cover non-convex "
      "polygons split into two components by one cell, holes that stay "
      "empty, slivers of area 1e-9 that are kept, and invariance under "
      "orientation, vertex rotation and grid refinement.\n")
    w("Hull provenance is verified rather than asserted: regenerating the "
      "level-60 hulls from the pinned equations reproduces the archived "
      f"arrays bitwise for every order "
      f"({hc['level_60_reproduces_archived_hulls_bitwise']}). Topology is "
      "valid in every profile -- simple boundaries, consistent nesting -- and "
      "the AART conventions are preserved: the direct-order outer boundary is "
      "the screen square, its inner boundary is the apparent horizon, and the "
      "photon-ring boundaries are radial scalings of the critical-curve "
      "directions.\n")
    w("**The three archived profiles carry the same hulls.** All were built "
      "at npointsS=60, so the fractional band areas are identical across "
      "them (2475.2788, 71.9615, 2.0029 M^2) and the archive does not "
      "exercise hull refinement at all. H1 had to generate new levels.\n")
    w("Every fragment with positive geometric area is classified against the "
      "transfer data that exists for it. Area shares:\n")
    w("| profile | order | supported | outside annulus | solver unresolved | "
      "no data |")
    w("| --- | --- | ---: | ---: | ---: | ---: |")
    for prof, rows in sup["per_profile"].items():
        for r in rows:
            b = r["by_category"]
            w(f"| {prof} | {r['order']} | {b[SUP]['area_fraction']:.4f} | "
              f"{b[ANN]['area_fraction']:.4f} | {b[UNR]['area_fraction']:.4f} "
              f"| {b[MIS]['area_fraction']:.4f} |")
    w("")
    w("This is the finding that governs everything after it. **Order 0 is "
      "essentially solved by fractional coverage**: its geometric band is "
      "profile-independent and its supported share converges 0.991, 0.996, "
      "0.998. **Orders 1 and 2 are not, and not because of the hull.** "
      "About 21% of order 1's band area lies outside the declared emission "
      "annulus and 1.5% is solver-unresolved; order 2 runs 5-7% and 5-7%. "
      "Those boundaries are properties of solved rays, not of any curve, so "
      "a perfect hull cannot resolve them. Masked zeros, failed solves and "
      "unsampled exteriors are held in three separate categories and none is "
      "treated as zero emission.\n")

    w("## 3. H1: the hull hierarchy\n")
    b = hc["budget"]
    w(f"Levels {hc['levels']}, each re-running the pinned root equations at "
      f"more arclength marks -- {hc['solves_per_direction']} solves per "
      "direction, so new vertices are new boundary solutions and not points "
      f"inserted along old edges. {b['boundary_point_solves']} boundary "
      f"solves of the {b['cap']} authorized; zero transfer rays.\n")
    w("| pair | order | band symdiff | boundaries | hull-only response | "
      "angular quadrature |")
    w("| --- | --- | ---: | ---: | ---: | ---: |")
    for p in hc["pairs"]:
        m = "" if p["all_pass"] else " **"
        w(f"| {p['pair']}{m} | {p['order']} | {p['eta_band']:.3e} | "
          f"{p['eta_boundaries']:.3e} | "
          f"{p['hull_only_response_relative']:.3e} | "
          f"{p['angular_quadrature_self_check']:.2e} |")
    w("")
    w(f"Budgets: band {hc['tolerances']['band']:.1e}, boundaries "
      f"{hc['tolerances']['boundaries']:.1e}, hull-only response "
      f"{hc['tolerances']['hull_only_response']:.1e}, all taken verbatim from "
      "the ruling. The angular-quadrature column is a self-check against the "
      f"{hc['tolerances']['angular_quadrature']:.0e} aggregate budget: the "
      "sample set contains every vertex angle, which makes the swept-area "
      "integration exact on the polygons themselves, so only radius "
      "crossings contribute and doubling the uniform fill measures what they "
      "leave.\n")
    # what the measured rates say the ladder would need, stated as a
    # projection under the observed rate and not as a bound
    proj = []
    for n in (0, 1, 2):
        seq = [p for p in hc["pairs"] if p["order"] == n]
        e = [p["eta_band"] for p in seq]
        if len(e) < 2 or e[-1] <= 0:
            continue
        rate = (e[-2] / e[-1]) if e[-1] > 0 else float("nan")
        err = e[-1]
        steps = 0
        while err >= hc["tolerances"]["band"] and steps < 12:
            err, steps = err / rate, steps + 1
        need = 0
        Lx = hc["levels"][-1]
        for _ in range(steps + 1):        # +1 for the second successive pair
            Lx *= 2
            need += 10 * Lx
        proj.append({"order": n, "observed_ratio_per_doubling": rate,
                     "level_for_two_successive_pairs": Lx,
                     "further_solves": need})
    w(f"Accepted level: **{hc['accepted_level']}**"
      + (" -- no level reached two successive qualifying pairs."
         if hc["accepted_level"] is None else ".") + "\n")
    if hc["accepted_level"] is None:
        w("Order 0 qualifies at every pair. Order 1 qualifies at 240->480 "
          "(band 7.6e-5, response 1.7e-4) but its previous pair misses at "
          "3.1e-4, so it has one qualifying pair and not two. Order 2 misses "
          "at 1.9e-3 on the band criterion.\n")
        w("The band symmetric difference falls by almost exactly a factor of "
          "four per doubling in every order, so the boundary is converging "
          "second order and the ladder is behaving. What it needs is more "
          "levels than the allowance holds, and that is a projection under "
          "the observed rate rather than a bound:\n")
        w("| order | ratio per doubling | level needed for two successive "
          "pairs | further boundary solves |")
        w("| --- | ---: | ---: | ---: |")
        for q in proj:
            w(f"| {q['order']} | {q['observed_ratio_per_doubling']:.2f} | "
              f"{q['level_for_two_successive_pairs']} | "
              f"{q['further_solves']:,} |")
        w("")
        w(f"Against {hc['budget']['cap'] - hc['budget']['boundary_point_solves']:,} "
          "remaining solves, and before the two independent checks that "
          "promotion also requires. Order 2 is the binding one. The band "
          "criterion is severe for a thin annulus by design -- a small radial "
          "shift moves a large share of a band two to three cells thick -- "
          "and it is the criterion the ruling chose precisely so that inner "
          "and outer errors cannot compensate. Its response counterpart is "
          "much closer: order 2's hull-only response change is 3.3e-4 against "
          "a 2.5e-4 budget.\n")
        w("Orders 0 and 1 alone would fit the remaining allowance at level "
          "960, but promotion also needs the shifted-sample and tighter-root "
          "checks at the accepted level, which would not fit, and the "
          "criterion is required of every order in any case. So the "
          "allowance was not spent on a level that could not be promoted. "
          "What would settle it is a larger boundary-solve authorization -- "
          "roughly 220,000 including the checks at level 3840 under the "
          "observed rate -- or a decision that the band criterion should be "
          "read differently for a band only two to three cells thick.\n")
    w("Independent checks:\n")
    if not hc["independent_checks"]:
        w("- not run: no level was accepted, and the checks are defined at "
          "an accepted level. Not run is recorded as not run, not as a pass.")
    for tag, c in hc["independent_checks"].items():
        if not c.get("run"):
            w(f"- `{tag}`: not run -- {c['reason']}")
            continue
        w(f"- `{tag}` at level {c['level']}, budget "
          f"{c['tolerance']:.1e}: "
          + ", ".join(f"n{r['order']} band {r['band_discrepancy']:.2e} "
                      f"resp {r['response_discrepancy']:.2e}"
                      for r in c["rows"])
          + f" -- {'pass' if c['passes'] else '**fail**'}")
    w("")
    w("The shifted check moves the sample locations half a step along the "
      "generator's own arclength parameter with the endpoints preserved, so "
      "it is a different set of boundary solves and not a resampling of the "
      "same polygon.\n")

    if val:
        w("## 4. H2: transfer and emission-boundary accuracy at a fixed hull\n")
        w(f"The hull is held at level {val['hull_held_fixed_at_level']}, so "
          "anything that moves is the ray sampling and the emission-validity "
          "boundary. Detector, observer times, sigma and the common absolute "
          "clock are the ones already pinned in the Q2 freeze. Zero transfer "
          "rays: the finding did not require any.\n")
        w("| pair | order | worst field | relative | active area | supported "
          "area |")
        w("| --- | --- | --- | ---: | ---: | ---: |")
        for r in val["comparisons"]:
            w(f"| {r['pair']} | {r['order']} | {r['worst_field']} | "
              f"{r['worst_relative']:.3e} "
              f"{'' if r['component_passes'] else '**'} | "
              f"{r['active_area']['relative']:.3e} | "
              f"{r['supported_area']['relative']:.3e} |")
        w("")
        w(f"Component budget {val['tolerances']['component']:.0e}, total "
          f"{val['tolerances']['total']:.0e}. Worst unsupported area "
          f"fraction across all profiles and orders: "
          f"{val['worst_unsupported_area_fraction']:.4f}.\n")
        w("The active area -- the geometric band inside the aperture -- is "
          "now profile-independent by construction, because the hull no "
          "longer moves. What still moves is the supported area, and it moves "
          "because the set of rays with valid transfer data changes with the "
          "sampling. That is the residual the fractional representation "
          "cannot remove on its own.\n")
    else:
        w("## 4. H2: not run\n")
        w("H1 accepted no hull level, so there was no fixed geometry to hold "
          "while testing transfer accuracy. Recorded as a skipped "
          "prerequisite, not as a pass.\n")

    w("## 5. What blocks a full qualification\n")
    if "MISSING_TRANSFER_SUPPORT" in comp["blockers"]:
        w("`MISSING_TRANSFER_SUPPORT`. Fractional coverage gives an exact "
          "geometric band, and for order 0 that is nearly the whole answer. "
          "For orders 1 and 2 a fifth to a quarter of the band area has no "
          "valid transfer data behind it, because the emission-annulus "
          "contour and the solver-failure region cut through cells and "
          "neither is a hull. Refining the hull to machine precision would "
          "not move those numbers.\n")
        w("What would: locating the `r_source = 50` contour and the "
          "solver-validity boundary by targeted root solves along screen "
          "rays, using the same pinned equations. Those are transfer-ray "
          "evaluations and would count against the 250,000 carried forward, "
          "which is ample -- a contour needs thousands, not millions. It is "
          "a different construction from the one authorized here, so it is "
          "reported and not attempted.\n")
    if "HULL_ACCURACY_UNQUALIFIED" in comp["blockers"]:
        w("`HULL_ACCURACY_UNQUALIFIED`: the hull ladder did not reach two "
          "successive qualifying pairs within the authorized boundary-solve "
          "allowance. The measured sequence is above; no tolerance was "
          "relaxed to close it.\n")

    w("## 6. R2: the permitted readback, and a claim of mine it withdraws\n")
    rb = h0 / "R2_WEIGHTS_READBACK_027.json"
    if not rb.exists():
        w("The weights readback was not performed in this stage, so the "
          "wider interval stays hypothetical.\n")
    else:
        d = json.loads(rb.read_text())
        w("The readback was run within its permitted scope: an inventory of "
          "the weights the sampler actually produces. No operator was built, "
          "no Fisher matrix formed, no SVD run and no target column touched. "
          "The same seed retains the same rays under both measures, verified "
          "ray by ray, and both draws go through the same rescale and "
          "common-count trimming.\n")
        w("| order | rows | per-order total ratio | row ratios |")
        w("| --- | ---: | ---: | --- |")
        for q in d["per_order"]:
            w(f"| {q['order']} | {q['n_rays']} | {q['total_ratio']:.9f} | "
              f"[{q['row_ratio_min']:.9f}, {q['row_ratio_max']:.9f}] |")
        w("")
        w(f"**The reviewer was right that a per-order total does not bound "
          f"every row, and the gap is not small.** Order 0's total ratio is "
          f"0.987978 while its row ratios span a factor of two: rays whose "
          f"cells sit on the declared screen edge get half-width or quarter "
          f"cells, so their individual weights halve while interior rays are "
          f"unchanged. Over all rows r lies in "
          f"[{d['row_ratio_min_over_all_rows']:.9f}, "
          f"{d['row_ratio_max_over_all_rows']:.9f}], which is wider than any "
          f"per-order total.\n")
        w("| direction | certified interval from the row bound |")
        w("| --- | --- |")
        for i, (a, b) in enumerate(d["certified_singular_value_intervals"], 1):
            mark = ("above rho" if a > 1.0 else "below rho" if b < 1.0
                    else "**straddles rho**")
            w(f"| {i} | [{a:.9f}, {b:.9f}] -- {mark} |")
        w("")
        w(f"So the count certified by this bound is "
          f"{d['n_directions_certainly_above_rho']}, not two: direction "
          f"{', '.join(str(i + 1) for i in d['directions_straddling_rho'])} "
          f"is undetermined. **I withdraw the reading I recorded in Q1** that "
          "the adopted measure's indicative interval still gave exactly two "
          "directions above rho with none straddling: that was computed from "
          "per-order totals, which the row inventory now shows do not bound "
          "the rows. The bound is sufficient rather than tight, so this does "
          "not say the count changes -- it says the count is not certified, "
          f"and the status is `{d['status']}`.\n")
        w("The certified interior-pitch bound from ruling 026 is untouched "
          "and still gives two, under its own stated assumptions. R2 remains "
          "accepted under its frozen legacy measure; nothing here recomputes "
          "or replaces it.\n")

    w("## 7. Governance\n")
    pr = fz["preexecution_registration"]
    w("**Preexecution registration was not satisfied for H0 and H1.** "
      f"{pr['disclosure']}. {pr['remedy_not_taken']}.\n")
    w("The gap does not change this return's outcome: the hull geometry is "
      f"**{st['hull_geometry']}** on its own measurements, so nothing here "
      "rests on treating an unregistered run as a qualification. H2 was run "
      "at the finest measured level under the ruling's explicitly-separated-"
      "diagnostic clause and is labelled as such. If the reviewer wants the "
      "geometry ladder itself registered before it is believed, that has to "
      "come with a boundary-solve allowance large enough to reach a "
      "qualifying level, since the current one does not.\n")
    bud = comp["budget"]
    w(f"Budget: {bud['boundary_point_solves_used']} of "
      f"{bud['boundary_point_solve_cap']} boundary solves; "
      f"{bud['transfer_ray_calls']} transfer rays of the "
      f"{bud['transfer_ray_cap_carried_forward']} carried forward; no paid "
      "resources.\n")
    w(f"Completion is fail-closed over {len(comp['required_conditions'])} "
      f"conditions with {len(comp['failed_conditions'])} failed and "
      f"{len(comp['unrecorded_conditions'])} unrecorded. Whole suite: "
      f"{comp['test_suite']['summary']}, return code "
      f"{comp['test_suite']['returncode']}.\n")
    for s in comp["skipped_prerequisites"]:
        w(f"- Skipped prerequisite: {s}")
    w("")
    w("No archive rewritten, no operator rebuilt, no endpoint recomputed or "
      "rescaled, no tolerance adjusted after a result, no geometry added, no "
      "paid resource acquired. R3B remains unauthorized.")
    (out / "FRACTIONAL_COVERAGE_027_RETURN.md").write_text(
        "\n".join(lines) + "\n")
    print(f"wrote {out / 'FRACTIONAL_COVERAGE_027_RETURN.md'}")
    return 0


if __name__ == "__main__":
    a = [(ROOT / x).resolve() for x in sys.argv[1:5]]
    raise SystemExit(main(*a))
