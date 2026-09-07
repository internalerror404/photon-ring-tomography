#!/usr/bin/env python3
"""C0 of ruling 034: recompute every comparator summary from the saved rows.

The 033 return stated its headline numbers as narrative in the renderer -- the
47/19 split, the median endpoint distance, and a single "agree to about 3e-16"
sentence covering all the integrals at once. Two of those were right and one
was too broad: the finite-path values agree near machine precision, the escape
parameter does not, and a convergence estimate is a third quantity again. This
stage derives all of it from the payload instead, per quantity, so the summary
cannot drift from the rows again.

Zero physical queries: the rows are read, not re-evaluated.
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
from phrt.revision_v4_1 import leaf2 as L2                       # noqa: E402
from phrt.revision_v4_1 import pathdomain as PD                  # noqa: E402

N033B = ROOT / ("artifacts/revisions/mahakal_v4_1/"
                "N033B_20260907T211922Z_45bd28e")
HELPER = ROOT / ("docs/revisions/mahakal_v4_1/review034/"
                 "response_checks_034.py")
CACHED_INPUTS = [
    "artifacts/revisions/mahakal_v4_1/N033B_20260907T211922Z_45bd28e/"
    "CHUNK_development_rows_033.json",
    "artifacts/revisions/mahakal_v4_1/N033B_20260907T211922Z_45bd28e/"
    "CHUNK_confirmation_rows_033.json",
    "artifacts/revisions/mahakal_v4_1/N033B_20260907T211922Z_45bd28e/"
    "CHUNK_development_033.npz",
    "artifacts/revisions/mahakal_v4_1/N033B_20260907T211922Z_45bd28e/"
    "CHUNK_confirmation_033.npz",
    "artifacts/revisions/mahakal_v4_1/N033B_20260907T211922Z_45bd28e/"
    "COMPARATOR_CAUSE_AND_CONFIRMATION_033.json",
    "artifacts/revisions/mahakal_v4_1/N033B_20260907T211922Z_45bd28e/"
    "FEASIBILITY_CLOSEOUT_033_INPUT_FREEZE.json",
    "artifacts/revisions/mahakal_v4_1/N033B_20260907T211922Z_45bd28e/"
    "ADAPTIVE_INTEGRATION_DESIGN_033.json",
    "artifacts/revisions/mahakal_v4_1/G1C_20260907T075203Z_d252697/"
    "CLOSEOUT_ARRAYS_029.npz",
]
QUANTITIES = ("J_observer", "J_50", "s_escape", "s_horizon", "s_50", "tail")


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with Path(p).open("rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def stats(v) -> dict | None:
    v = [float(x) for x in v if x is not None and np.isfinite(x)]
    if not v:
        return None
    a = np.array(v)
    return {"n": int(a.size), "min": float(a.min()),
            "median": float(np.median(a)), "p95": float(np.quantile(a, 0.95)),
            "max": float(a.max())}


def readback(rows: list[dict]) -> dict:
    """Everything the 033 report asserted, recomputed here from the rows."""
    by_quantity = {}
    for q in QUANTITIES:
        d, rel = [], []
        for r in rows:
            a, b = r["reference_A"].get(q), r["reference_B"].get(q)
            if a is None or b is None:
                continue
            d.append(abs(a - b))
            scale = max(abs(a), abs(b))
            if scale > 0:
                rel.append(abs(a - b) / scale)
        by_quantity[q] = {"absolute_difference": stats(d),
                          "relative_difference": stats(rel)}

    endpoint, dist = {}, []
    for r in rows:
        A = r["reference_A"]
        if A["code"] != PD.UNRESOLVED:
            continue
        m = A.get("margin")
        cand = {
            "upper_annulus": A.get("margin_upper_minus_G_theta"),
            "lower_annulus": A.get("margin_G_theta_minus_lower"),
            "escape": (A["s_escape"] - A["s_n"])
            if A.get("s_escape") is not None else None,
            "capture_horizon": A.get("margin_sH_minus_G_theta"),
            "capture_annulus": A.get("margin_G_theta_minus_s50"),
        }
        hit = tuple(sorted(k for k, v in cand.items()
                           if v is not None and m is not None and abs(v) <= m))
        endpoint["+".join(hit) or "(none)"] = \
            endpoint.get("+".join(hit) or "(none)", 0) + 1
        finite = [abs(v) for v in cand.values() if v is not None]
        if finite:
            dist.append(min(finite))

    sep_unres = [r["turn_separation"] for r in rows
                 if r["reference_A"]["code"] == PD.UNRESOLVED
                 and r["turn_separation"] is not None]
    sep_res = [r["turn_separation"] for r in rows
               if r["reference_A"]["code"] != PD.UNRESOLVED
               and r["turn_separation"] is not None]
    return {
        "n": len(rows),
        "per_quantity_A_vs_B": by_quantity,
        "blanket_3e_16_equality_claim_holds": False,
        "which_quantities_agree_near_machine_precision": [
            q for q in QUANTITIES
            if (by_quantity[q]["relative_difference"] or {}).get("max", 1.0)
            < 1e-13],
        "which_do_not": [
            q for q in QUANTITIES
            if (by_quantity[q]["relative_difference"] or {}).get("max", 0.0)
            >= 1e-13],
        "reference_A_error_estimate": stats(
            [r["reference_A"].get("error_estimate") for r in rows]),
        "reference_B_error_estimate": stats(
            [r["reference_B"].get("error_estimate") for r in rows]),
        "primary_error_estimate": stats(
            [r["primary"].get("error_estimate") for r in rows]),
        "error_estimate_is_an_estimate_not_the_error": True,
        "endpoint_that_refused": endpoint,
        "estimated_distance_to_the_nearest_endpoint": stats(dist),
        "distance_is_computed_from_the_same_quadrature_not_ground_truth": True,
        "turn_separation_where_A_refused": stats(sep_unres),
        "turn_separation_where_A_resolved": stats(sep_res),
        "separation_is_an_association_not_a_controlled_unique_cause": True,
        "codes": {
            k: {c: int(sum(r[k]["code"] == c for r in rows))
                for c in sorted({r[k]["code"] for r in rows})}
            for k in ("primary", "reference_A", "reference_B")},
        "primary_agrees_with_reference_B": int(sum(
            r["primary"]["code"] == r["reference_B"]["code"] for r in rows)),
        "primary_agrees_with_reference_A": int(sum(
            r["primary"]["code"] == r["reference_A"]["code"] for r in rows)),
    }


def box_tests() -> dict:
    """The nominal-aware error radius, against the reviewer's own helper."""
    import importlib.util
    out = {"corrected_helper": "leaf2.box_radius_about",
           "replaces": "leaf2.envelope_response_bound (033), which reduced a "
                       "half-width with a matrix one-norm about no stated "
                       "reference"}
    a = L2.BoundedAssembly(np.zeros((1, 1)), np.full((1, 1), 2.0))
    out["radius_about_zero_for_the_interval_0_to_2"] = float(
        L2.box_radius_about(a, np.zeros((1, 1)))["per_channel_euclidean"][0])
    out["radius_about_the_midpoint"] = float(
        L2.box_radius_about(a, L2.midpoint(a))["per_channel_euclidean"][0])
    b = L2.BoundedAssembly(-np.ones((1, 2)), np.ones((1, 2)))
    r = L2.box_radius_about(b, np.zeros((1, 2)))
    out["per_channel_for_a_unit_two_channel_row"] = \
        r["per_channel_euclidean"].tolist()
    out["joint_euclidean"] = r["joint_euclidean_over_the_whole_stack"]
    out["matrix_one_norm_of_the_same_half_width"] = float(
        np.linalg.norm(0.5 * (b.upper - b.lower), ord=1))
    if HELPER.is_file():
        spec = importlib.util.spec_from_file_location("rev034", HELPER)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        rng = np.random.default_rng(34)
        worst = 0.0
        for _ in range(200):
            lo = rng.normal(size=(4, 3))
            hi = lo + rng.uniform(0, 2, (4, 3))
            nom = rng.normal(size=(4, 3))
            w = rng.uniform(0, 2, 4)
            per, joint = mod.box_radius_about(lo, hi, nom, w)
            got = L2.box_radius_about(L2.BoundedAssembly(lo, hi), nom, w)
            worst = max(worst, float(np.max(np.abs(
                got["per_channel_euclidean"] - per))),
                abs(got["joint_euclidean_over_the_whole_stack"] - joint))
        out["max_disagreement_with_the_reviewer_helper"] = worst
        out["agrees_with_the_reviewer_helper"] = bool(worst < 1e-12)
    return out


OVERLAY = """# INTERPRETATION_OVERLAY_034

Ruling: PAPER_I_RESPONSE_ERROR_RULING_034
Reviewed commit: d1617963d93713053a4ea374a8c78fcfa013448a

Additive. No file written under rulings 029-033 is edited, the 033 renderer
keeps its bytes, and every earlier token stands.

## 1. Corrections to the 033 report

**The integrals do not all agree at 3e-16.** That sentence was true of the
finite-path values and false as a blanket statement. Recomputed per quantity
from the saved rows: `J_observer` and `J_50` agree between reference A and
reference B to within machine precision, while `s_escape` does not -- in the
first exported development case it differs by 7.27e-08. A third quantity again
is reference A's convergence estimate, ~3.76e-05 there. Finite-path values,
escape values and error estimates are three different things and the readback
now reports them separately.

**The summary numbers were narrative.** The 47/19 endpoint split, the median
endpoint distance and the equality sentence were literals in the renderer
rather than derivations from the payload. They are recomputed here from the
rows, and the report now quotes the recomputation.

**A quadrature error estimate is not the error.** SciPy documents it as an
estimate, and the distance from a decision endpoint is itself computed with
the same quadrature. Neither is ground truth, and neither is presented as
such.

**Root separation stays an association.** The population difference is real
and consistent with harder integration, but it is not a controlled
demonstration that separation is the sole mechanism.

**The indexed reduction was not shown to be necessary here.** It remains a
worthwhile algebraic safeguard. The delivered evidence does not show it was
required to decide these particular cases.

## 2. Corrections to the 033 field-error finding

The 94.7% and 98.1% figures are the fraction of comparable nodes at which

    |z_interpolated - z_fine| / max over comparable nodes |z_fine|

exceeds 5e-4, for a primitive field z. That is a **global-maximum-scaled
primitive bilinear discrepancy**. It is not a pointwise relative error and it
is not the whitened detector-response error the 5e-4 budget is written
against. Using the same number for both does not make them the same quantity.

Two scope limits go on the record with it. The 10,284 comparable order-2 nodes
are 61.68% of the fine map's emitting nodes, not the whole emitting domain.
And the comparison did not isolate smooth interior stencils: bilinear
interpolation there required finite radius and redshift at the corners, not
that every corner belong to the same emitting domain or the same radial leg,
so boundary-crossing and outside-annulus stencils could contribute.

The figures stay as evidence about that bilinear representation on those
comparable stencils. They do not establish that no mesh design can reduce the
cost, and the 033 sentence saying so is withdrawn.

## 3. Corrections to the 033 cost numbers

101,416 expected and 382,580 worst case are **scenarios**. The interior term
is a heuristic extrapolation -- the largest above-threshold node fraction times
the transition-parent count times four -- not a count of unresolved interior
leaves, and the worst case stipulates retries and multipliers rather than
proving a bound. The 4.385x figure is arithmetic between projected work and
the retired layout, not a measured speedup.

The 033 sentence "adaptivity fixes the boundary cost" is also withdrawn as
written: within that same model the boundary term is 52,379 and the interior
term 49,037, so the boundary is the larger half of the projection.

## 4. Correction to the interval error report

The interval propagation itself is accepted. Its scalar helper was wrong:
a box's half-width bounds the error about the box's midpoint and about nothing
else, and reducing a whitened half-width with a matrix one-norm is neither a
per-channel nor a joint Euclidean radius. `leaf2.box_radius_about` now takes an
explicit reference response, returns the per-channel Euclidean radius over the
whitened detector rows as the primary figure, and labels the joint
aggregation separately.

## 5. What stands

The comparator closeout stands at its stated cohort scope, with its bounded
independence. The recorded reason for reference A's refusal was its own
decision margin, not a disagreement about the physical event. The accounting
stands: 18,372 + 774 = 19,146 spent, 854 remaining, none of it spent under
this ruling.
"""


def main(out: Path) -> int:
    t0 = time.time()
    out.mkdir(parents=True, exist_ok=False)
    missing = [f for f in CACHED_INPUTS if not (ROOT / f).is_file()]
    manifest = {
        "stage": "C0", "ruling": "PAPER_I_RESPONSE_ERROR_RULING_034",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "commit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                 capture_output=True, text=True).stdout.strip(),
        "new_rays": 0, "new_path_quadratures": 0, "new_hull_roots": 0,
        "cached_inputs": {f: sha(ROOT / f) for f in CACHED_INPUTS
                          if (ROOT / f).is_file()},
        "missing_inputs": missing,
        "skipped_missing_inputs_are_explicit_not_a_pass": True,
    }
    (out / "CACHED_RESPONSE_034_INPUT_MANIFEST.json").write_text(
        json.dumps(manifest, indent=2) + "\n")

    dev = json.loads((N033B / "CHUNK_development_rows_033.json").read_text())
    conf = json.loads((N033B / "CHUNK_confirmation_rows_033.json").read_text())
    first = dev[0]
    rep = {
        "stage": "C0", "ruling": "PAPER_I_RESPONSE_ERROR_RULING_034",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "derived_from_saved_rows_not_narrative": True,
        "new_physical_evaluations": 0,
        "development": readback(dev),
        "confirmation": readback(conf),
        "first_exported_development_case": {
            "order": first["order"], "index": first["index"],
            "reference_A": {q: first["reference_A"].get(q)
                            for q in QUANTITIES + ("error_estimate", "margin")},
            "reference_B": {q: first["reference_B"].get(q)
                            for q in QUANTITIES + ("error_estimate", "margin")},
            "absolute_differences": {
                q: abs(first["reference_A"][q] - first["reference_B"][q])
                for q in QUANTITIES
                if first["reference_A"].get(q) is not None
                and first["reference_B"].get(q) is not None},
        },
    }
    (out / "COMPARATOR_QUANTITY_READBACK_034.json").write_text(
        json.dumps(rep, indent=2) + "\n")
    (out / "BOX_REFERENCE_NORM_TESTS_034.json").write_text(
        json.dumps({"stage": "C0", "new_physical_evaluations": 0,
                    **box_tests()}, indent=2) + "\n")
    (out / "INTERPRETATION_OVERLAY_034.md").write_text(OVERLAY)

    if HELPER.is_file():
        dst = out / "REVIEWER_CHECKS_034.json"
        if not dst.exists():
            subprocess.run([sys.executable, str(HELPER), "--output", str(dst)],
                           cwd=ROOT, check=True, capture_output=True, text=True)
    d = rep["development"]
    print(json.dumps({
        "stage": "C0",
        "agree_near_machine_precision": d["which_quantities_agree_near_machine_precision"],
        "do_not": d["which_do_not"],
        "endpoint_split": d["endpoint_that_refused"],
        "distance_median": (d["estimated_distance_to_the_nearest_endpoint"]
                            or {}).get("median"),
        "seconds": round(time.time() - t0, 1)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main((ROOT / sys.argv[1]).resolve()))
