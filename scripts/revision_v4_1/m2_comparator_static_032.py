#!/usr/bin/env python3
"""M2 of ruling 032: static diagnostics for the comparator. Zero queries.

Everything here is closed-form algebra on archived screen coordinates or on
synthetic fixtures. No ray is traced, no path integral is recomputed, and no
label from 030 or 031 is overwritten. Where a question cannot be answered
without recomputation, that is said rather than approximated.
"""
from __future__ import annotations

import glob
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from phrt.geometry.raymap import horizon_radius, read           # noqa: E402
from phrt.revision_v4_1 import pathdomain as PD                 # noqa: E402
from phrt.revision_v4_1 import pathdomain2 as P2                # noqa: E402
from phrt.revision_v4_1 import rootcheck as RC                  # noqa: E402

SPIN, INC_DEG, D_OBS, R_OUTER = 0.5, 50.0, 1000.0, 50.0
MAPS = ROOT / "artifacts" / "raymaps"


def tautology_demonstration() -> dict:
    """The 031 residual is zero for any list of four numbers whatsoever."""
    rng = np.random.default_rng(20260907)
    worst = 0.0
    for _ in range(2000):
        z = rng.normal(size=4) + 1j * rng.normal(size=4)
        worst = max(worst, float(np.max(np.abs(
            np.prod(z[:, None] - z[None, :], axis=0)))))
    c = RC.quartic_coefficients(SPIN, 3.0, 4.0).ravel()
    r = np.roots(c)
    bad = r.copy()
    bad[0] += 0.05
    return {
        "what_031_reported": "max_i |prod_j (z_i - z_j)| = 0",
        "max_over_2000_random_quadruples": worst,
        "conclusion": "zero for an arbitrary wrong root list; it is not a check",
        "original_quartic_at_the_returned_roots":
            float(np.max(RC.backward_residual(c, r))),
        "original_quartic_at_a_root_perturbed_by_0.05":
            float(np.max(RC.backward_residual(c, bad))),
        "coefficients_from_conserved_quantities": c.tolist(),
        "backward_residual_is_a_root_location_bound": False,
    }


def endpoint_limit_fixture() -> dict:
    """R(r)/(r - r_t) at the turn: identity exclusion gives 0, index gives the limit."""
    roots = np.array([-3.0 + 0j, 0.2 + 0j, 1.1 + 0j, 4.7 + 0j])
    idx = RC.turning_index(roots, 0.5, 1000.0)
    turn = float(roots[idx].real)
    want = RC.reduced_limit(roots, idx)
    approach = []
    for eps in (1e-2, 1e-4, 1e-6, 1e-8):
        r = turn + eps
        approach.append({
            "epsilon": eps,
            "R_over_r_minus_turn": float(
                np.real(PD.radial_potential(r, roots) / (r - turn))),
            "error_against_analytic_limit": float(abs(
                complex(PD.radial_potential(r, roots) / (r - turn)) - want))})
    return {
        "roots": [str(q) for q in roots], "turning_index": idx, "turn": turn,
        "analytic_limit": float(want.real),
        "031_identity_excluded_product_at_the_turn":
            float(np.real(RC.identity_excluded_product(roots, turn, turn))),
        "index_excluded_product_at_the_turn": float(want.real),
        "approach": approach,
        "why_it_matters": (
            "classify_path returns max(ext) as a plain float, so `q is not "
            "turn` is true for every element and the factor (r - turn) is "
            "kept. The reduced potential then vanishes at u = 0, the guard "
            "substitutes a zero integrand, and the quadrature samples a hole "
            "at the endpoint where the integrand is largest."),
        "multiplicity_guard_tested": True,
    }


def multiplicity_guard() -> dict:
    clustered = np.array([1.0 + 0j, 2.0 + 0j, 2.0 + 1e-12j, 9.0 + 0j])
    try:
        RC.reduced_product(clustered, 1, 2.0)
        refused = False
        why = None
    except RC.RootCheckError as exc:
        refused, why = True, str(exc)
    return {"clustered_turning_root_refused": refused, "message": why,
            "branch_checked_by_index_not_object_identity": True}


def perturbed_root_battery() -> dict:
    rng = np.random.default_rng(4242)
    rows = []
    for _ in range(200):
        lam = rng.uniform(-8.0, 8.0)
        eta = rng.uniform(0.0, 60.0)
        c = RC.quartic_coefficients(SPIN, lam, eta).ravel()
        r = np.roots(c)
        base = float(np.max(RC.backward_residual(c, r)))
        for d in (1e-8, 1e-6, 1e-4, 1e-2):
            p = r.copy()
            p[int(rng.integers(4))] += d
            rows.append({"delta": d, "base": base,
                         "perturbed": float(np.max(RC.backward_residual(c, p)))})
    out = {}
    for d in (1e-8, 1e-6, 1e-4, 1e-2):
        sub = [x for x in rows if x["delta"] == d]
        out[f"delta_{d:g}"] = {
            "cases": len(sub),
            "median_backward_residual": float(np.median(
                [x["perturbed"] for x in sub])),
            "detected_above_unperturbed":
                int(sum(x["perturbed"] > 100 * max(x["base"], 1e-16)
                        for x in sub))}
    return out


def conditioning_of_the_unresolved_cases() -> dict:
    """Root conditioning at the 66 unresolved references, and at a control set.

    lam and eta are a closed form of the archived screen coordinates, so this
    reaches the same quartic the campaign solved without recomputing anything.
    It measures conditioning; it does not diagnose the 66, because the
    reference's own integral values and reason codes were never written and
    cannot be recovered without a recomputation this ruling does not authorize.
    """
    p = sorted(glob.glob(str(ROOT / "artifacts/revisions/mahakal_v4_1/I1_*/"
                             "FRESH_COMPARATOR_CONFIRMATION_031.json")))
    if not p:
        return {"status": "I1_RECORD_NOT_FOUND"}
    rec = json.loads(Path(p[-1]).read_text())
    th = np.deg2rad(INC_DEG)
    rh = horizon_radius(SPIN)
    maps = {}
    groups = {"unresolved_reference": [r for r in rec["rows"] if not r["agree"]],
              "agreeing_control": [r for r in rec["rows"] if r["agree"]]}
    out = {"reference_reason_codes_available": False,
           "reference_integral_values_available": False,
           "why": ("I1 wrote only the label, the margin and the error "
                   "estimate; the reference's reason code and integral value "
                   "were discarded at write time"),
           "lam_eta_source": "closed form of the archived alpha, beta",
           "profile_sampled_by_I1": "fine",
           "groups": {}}
    for name, rows in groups.items():
        stats = {"n": len(rows), "by_order": {}, "kind": {}, "no_turning_root": 0,
                 "min_separation_quantiles": None, "max_backward_residual": 0.0}
        seps = []
        for r in rows:
            n = int(r["order"])
            if n not in maps:
                maps[n] = read(MAPS / f"a050_i050_n{n}_fine.h5")
            rm = maps[n]
            i = int(r["index"])
            lam, eta = RC.conserved_quantities(rm.alpha[i], rm.beta[i], th, SPIN)
            c = RC.quartic_coefficients(SPIN, lam, eta).ravel()
            roots = np.roots(c)
            cond = RC.conditioning(c, roots)
            seps.append(cond["min_separation"])
            stats["max_backward_residual"] = max(
                stats["max_backward_residual"],
                float(np.max(RC.backward_residual(c, roots))))
            for k in cond["kind"]:
                stats["kind"][k] = stats["kind"].get(k, 0) + 1
            stats["by_order"][str(n)] = stats["by_order"].get(str(n), 0) + 1
            idx = RC.turning_index(roots, rh, D_OBS)
            if idx is None:
                stats["no_turning_root"] += 1
            else:
                d = np.abs(np.delete(roots, idx) - roots[idx])
                stats.setdefault("turn_separation", []).append(float(d.min()))
        if seps:
            q = np.quantile(seps, [0.0, 0.05, 0.5, 0.95, 1.0])
            stats["min_separation_quantiles"] = dict(
                zip(("min", "p05", "median", "p95", "max"),
                    [float(x) for x in q]))
        if "turn_separation" in stats:
            t = np.array(stats.pop("turn_separation"))
            stats["turn_separation_quantiles"] = {
                "min": float(t.min()), "median": float(np.median(t)),
                "max": float(t.max())}
        out["groups"][name] = stats
    return out


def frozen_031_reduction_named() -> dict:
    import inspect
    src = inspect.getsource(P2.integral)
    return {
        "file": "src/phrt/revision_v4_1/pathdomain2.py",
        "expression_present": "q is not turn" in src,
        "disposition": "NAMED_NOT_REPAIRED_IN_PLACE",
        "why": ("version 2 is the frozen 031 record; the corrected reduction "
                "lives in rootcheck.reduced_product and is validated on "
                "analytic fixtures here, ready for a next ruling to adopt"),
        "tuned_on_the_494_panel": False,
        "physical_cause_of_the_66_established": False,
    }


def main(out: Path) -> int:
    t0 = time.time()
    rep = {
        "stage": "M2", "ruling": "PAPER_I_MATCHED_INTEGRATION_RULING_032",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "commit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                 capture_output=True, text=True).stdout.strip(),
        "physical_queries": 0, "path_integrals_recomputed": 0,
        "rays_traced": 0,
        "tautological_residual": tautology_demonstration(),
        "perturbed_roots": perturbed_root_battery(),
        "endpoint_limit": endpoint_limit_fixture(),
        "multiplicity_guard": multiplicity_guard(),
        "frozen_031_reduction": frozen_031_reduction_named(),
        "unresolved_reference_conditioning":
            conditioning_of_the_unresolved_cases(),
        "runtime_seconds": time.time() - t0,
    }
    (out / "COMPARATOR_STATIC_DIAGNOSTICS_032.json").write_text(
        json.dumps(rep, indent=2) + "\n")
    g = rep["unresolved_reference_conditioning"].get("groups", {})
    print(json.dumps({
        "stage": "M2",
        "identity_form_at_the_turn":
            rep["endpoint_limit"]["031_identity_excluded_product_at_the_turn"],
        "analytic_limit": rep["endpoint_limit"]["analytic_limit"],
        "unresolved": g.get("unresolved_reference", {}).get("n"),
        "control": g.get("agreeing_control", {}).get("n")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main((ROOT / sys.argv[1]).resolve()))
