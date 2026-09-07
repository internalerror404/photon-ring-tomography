#!/usr/bin/env python3
"""N0 of ruling 033: the input freeze, written before any physical query.

Everything the diagnostic is allowed to depend on is pinned here: the
comparator sources and their hashes, the backend, the numerical policy, the
reference hierarchy, the caps, the stopping rules, and -- by explicit index --
the two cohorts. The confirmation IDs are chosen from geometry and from
archived labels alone, and every point/order ID used by rulings 029, 030 or
031 is excluded. Selecting them after seeing this stage's outcomes would make
them a tuning panel; that is what freezing them beforehand is for.

Zero physical queries are made by this script.
"""
from __future__ import annotations

import glob
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

import h5py
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from phrt.geometry.raymap import horizon_radius, read            # noqa: E402
from phrt.revision_v4_1 import domain as D                       # noqa: E402
from phrt.revision_v4_1 import pathdomain3 as P3                 # noqa: E402
from phrt.revision_v4_1 import rootcheck as RC                   # noqa: E402

MAPS = ROOT / "artifacts" / "raymaps"
AART = ROOT / "artifacts" / "e3_pilot" / "aart_out"
BANDS = {"core": AART / ("core/LensingBands_a_0.5_i_50.0_dx0_0.4_dx1_0.08"
                         "_dx2_0.02.h5"),
         "fine": AART / ("fine/LensingBands_a_0.5_i_50.0_dx0_0.2_dx1_0.04"
                         "_dx2_0.01.h5")}
GEOMETRY, SPIN, INC, D_OBS, R_OUTER = "a050_i050", 0.5, 50.0, 1000.0, 50.0
SIGMA, T_REF = 0.011341986814407566, -978.6055123201214
T_OBS = [0.0, 2.857142857142857, 5.714285714285714, 8.571428571428571,
         11.428571428571429, 14.285714285714286, 17.142857142857142, 20.0]
PROFILE = "fine"                       # the profile ruling 031 sampled
STRATA = ("near_turn", "healthy", "absent_requested_event",
          "finite_outside_annulus")
PER_STRATUM = 48                       # 4 x 48 = 192, the confirmation cap

SRC = ["src/phrt/revision_v4_1/pathdomain.py",
       "src/phrt/revision_v4_1/pathdomain2.py",
       "src/phrt/revision_v4_1/pathdomain3.py",
       "src/phrt/revision_v4_1/rootcheck.py",
       "src/phrt/revision_v4_1/leaf.py",
       "src/phrt/revision_v4_1/leaf2.py",
       "src/phrt/revision_v4_1/domain.py",
       "src/phrt/revision_v4_1/query.py",
       "scripts/revision_v4_1/t1_first_invalid_primitive.py",
       "scripts/revision_v4_1/n0_freeze_033.py",
       "scripts/revision_v4_1/n2_comparator_closeout_033.py"]


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def used_ids() -> dict:
    """Every (profile, order, index) any previous ruling has evaluated."""
    used: set[tuple] = set()
    prov: dict[str, int] = {}

    p = sorted(glob.glob(str(ROOT / "artifacts/revisions/mahakal_v4_1/I1_*/"
                             "FRESH_COMPARATOR_CONFIRMATION_031.json")))[-1]
    rec = json.loads(Path(p).read_text())
    for r in rec["rows"]:
        used.add(("fine", int(r["order"]), int(r["index"])))
    prov["I1_031_fine"] = len(rec["rows"])

    for f in sorted(glob.glob(str(ROOT / "artifacts/revisions/mahakal_v4_1/"
                                  "D1*/PER_POINT_PATH_DOMAIN_ADJUDICATION_"
                                  "030.npz"))):
        with np.load(f, allow_pickle=False) as z:
            for key, profile in (("dev", "core"), ("holdout", "fine")):
                if key not in z.files:
                    continue
                n = 0
                for s in z[key]:
                    d = json.loads(str(s))
                    used.add((profile, int(d["order"]), int(d["index"])))
                    n += 1
                prov[f"{Path(f).parent.name}:{key}:{profile}"] = n

    # 029 stored screen coordinates rather than indices; they are matched back
    # to a node index on each profile, so a coordinate reused there is excluded
    nodes = {}
    for profile in ("core", "fine"):
        for n in (0, 1, 2):
            rm = read(MAPS / f"{GEOMETRY}_n{n}_{profile}.h5")
            nodes[(profile, n)] = {(round(float(a), 9), round(float(b), 9)): i
                                   for i, (a, b) in
                                   enumerate(zip(rm.alpha, rm.beta))}
    for f in sorted(glob.glob(str(ROOT / "artifacts/revisions/mahakal_v4_1/"
                                  "T1_*/FIRST_INVALID_PRIMITIVE_029.json"))):
        d = json.loads(Path(f).read_text())
        n_hit = 0
        for tag, arr in d.get("arrays", {}).items():
            order = int(tag[1])
            for a, b in zip(arr["alpha"], arr["beta"]):
                key = (round(float(a), 9), round(float(b), 9))
                for profile in ("core", "fine"):
                    i = nodes[(profile, order)].get(key)
                    if i is not None:
                        used.add((profile, order, i))
                        n_hit += 1
        prov[f"{Path(f).parent.name}:029"] = n_hit
    return {"set": used, "provenance": prov}


def development_ids() -> list[dict]:
    """The 66 records ruling 031 left unresolved, as point/order IDs."""
    p = sorted(glob.glob(str(ROOT / "artifacts/revisions/mahakal_v4_1/I1_*/"
                             "FRESH_COMPARATOR_CONFIRMATION_031.json")))[-1]
    rec = json.loads(Path(p).read_text())
    out = []
    for r in rec["rows"]:
        if not r["agree"]:
            out.append({"profile": "fine", "order": int(r["order"]),
                        "index": int(r["index"]),
                        "prior_primary": r["primary"],
                        "prior_reference": r["reference"],
                        "prior_margin": r["margin"],
                        "prior_error_estimate": r["error_estimate"],
                        "strata": r["strata"]})
    return out


def confirmation_ids(used: set) -> tuple[list[dict], dict]:
    """192 previously unused IDs, four declared scopes, chosen without targets.

    The near-turn stratum is selected by an algebraic property of the screen
    coordinate -- how close the outermost accessible turning root is to its
    neighbour -- which needs no ray and no path integral. Nothing here looks
    at a singular value, a spectrum, or any quantity the campaign is trying
    to estimate.
    """
    rh = horizon_radius(SPIN)
    th = np.deg2rad(INC)
    rng = np.random.default_rng(20260907)
    picked: list[dict] = []
    audit: dict = {}
    with h5py.File(BANDS[PROFILE], "r") as h:
        band = {n: h[f"mask{n}"][:] for n in (0, 1, 2)}
    pool: dict[str, list[tuple]] = {s: [] for s in STRATA}
    sep_by_point: dict[tuple, float] = {}

    for n in (0, 1, 2):
        rm = read(MAPS / f"{GEOMETRY}_n{n}_{PROFILE}.h5")
        st, _ = D.classify_points(band[n], rm.source_r, rm.source_phi,
                                  rm.coordinate_time, rm.redshift, rh, R_OUTER)
        inband = band[n].reshape(-1).astype(bool)
        finite = np.isfinite(rm.source_r)
        emitting = st == D.CERTIFIED_EMITTING
        absent = inband & ~finite
        outside = inband & finite & ((rm.source_r > R_OUTER)
                                     | (rm.source_r <= rh))
        cand = np.flatnonzero(inband)
        cand = np.array([i for i in cand if (PROFILE, n, int(i)) not in used])
        if cand.size == 0:
            continue
        # algebraic turn separation, on a bounded random subsample of the
        # eligible points so the freeze is cheap and reproducible
        sub = cand if cand.size <= 20000 else rng.choice(cand, 20000, False)
        lam, eta = RC.conserved_quantities(rm.alpha[sub], rm.beta[sub], th, SPIN)
        seps = np.full(sub.size, np.inf)
        for j in range(sub.size):
            c = RC.quartic_coefficients(SPIN, lam[j], eta[j]).ravel()
            r = np.roots(c)
            k = RC.turning_index(r, rh, D_OBS)
            if k is None:
                continue
            seps[j] = float(np.min(np.abs(np.delete(r, k) - r[k])))
        for j, i in enumerate(sub):
            sep_by_point[(n, int(i))] = float(seps[j])
        ok = np.isfinite(seps)
        if ok.any():
            cut = float(np.quantile(seps[ok], 0.10))
            for j, i in enumerate(sub):
                if ok[j] and emitting[i] and seps[j] <= cut:
                    pool["near_turn"].append((n, int(i)))
                elif ok[j] and emitting[i] and seps[j] >= float(
                        np.quantile(seps[ok], 0.60)):
                    pool["healthy"].append((n, int(i)))
        for i in cand:
            if absent[i]:
                pool["absent_requested_event"].append((n, int(i)))
            elif outside[i]:
                pool["finite_outside_annulus"].append((n, int(i)))
        audit[f"order{n}"] = {
            "eligible_in_band_and_unused": int(cand.size),
            "turn_separation_subsample": int(sub.size),
            "with_an_accessible_turn": int(ok.sum())}

    for s in STRATA:
        c = sorted(set(pool[s]))
        audit.setdefault("pool_sizes", {})[s] = len(c)
        if not c:
            continue
        take = rng.choice(len(c), min(PER_STRATUM, len(c)), replace=False)
        for t in sorted(take):
            n, i = c[int(t)]
            picked.append({"profile": PROFILE, "order": n, "index": int(i),
                           "stratum": s,
                           "turn_separation": sep_by_point.get((n, i))})
    audit["selected"] = len(picked)
    audit["selection_used_target_information"] = False
    return picked, audit


def main(out: Path) -> int:
    t0 = time.time()
    out.mkdir(parents=True, exist_ok=False)
    u = used_ids()
    dev = development_ids()
    conf, audit = confirmation_ids(u["set"])
    overlap = [c for c in conf
               if (c["profile"], c["order"], c["index"]) in u["set"]]
    if overlap:
        raise SystemExit(f"{len(overlap)} confirmation IDs were used before")
    dev_keys = {(d["profile"], d["order"], d["index"]) for d in dev}
    if any((c["profile"], c["order"], c["index"]) in dev_keys for c in conf):
        raise SystemExit("a confirmation ID collides with a development ID")

    backend = sorted(glob.glob("/tmp/aartvenv/lib/python3.11/site-packages/"
                               "aart/*.py"))
    files = {f: sha(ROOT / f) for f in SRC}
    files.update({b: sha(Path(b)) for b in backend})
    for profile in ("fine",):
        for n in (0, 1, 2):
            f = f"artifacts/raymaps/{GEOMETRY}_n{n}_{profile}.h5"
            files[f] = sha(ROOT / f)

    charged_dev = 3 * len(dev)
    charged_conf = 3 * len(conf)
    fz = {
        "schema": "phrt-input-freeze/1",
        "id": "FEASIBILITY_CLOSEOUT_033_INPUT_FREEZE",
        "ruling": "PAPER_I_FEASIBILITY_AND_CLOSEOUT_RULING_033",
        "written_before_any_new_physical_query": True,
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "commit_at_freeze_time": subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True,
            text=True).stdout.strip(),
        "detector": {"name": "D026", "unchanged": True,
                     "alpha_M": [-25.0, 25.0], "beta_M": [-25.0, 25.0],
                     "pitch_M": 0.4, "sigma": SIGMA,
                     "observer_times": T_OBS},
        "clock": {"absolute_reference_coordinate_time_M": T_REF},
        "solver_policy": {
            "entry_point": "aart.raytracing_f.calculate_observables, "
                           "reproduced expression for expression",
            "spin": SPIN, "inclination_deg": INC, "d_obs": D_OBS,
            "source_annulus": "horizon exclusive to 50 inclusive",
            "predicate": "path-domain, Mino parameter, backward from the "
                         "observer",
            "transfer_formula_repair": "none; no evidence justifies one",
            "missing_node_or_failed_quadrature_as_zero": False,
            "comparator_primary": "pathdomain2.adjudicate (frozen 031)",
            "reference_A": "pathdomain2.adjudicate(reference=True), graded "
                           "panels; run to recover the ACTUAL 031 failure "
                           "reason, which I1 discarded",
            "reference_B": f"pathdomain3.adjudicate ({P3.VERSION})",
            "reference_hierarchy": ["primary", "reference_A", "reference_B"],
            "numerical_policy": P3.POLICY,
            "ambiguity_rule": "a case inside the decision margin is returned "
                              "unresolved; it is never resolved toward the "
                              "archived mask",
        },
        "selection_rule": {
            "development": "the 66 records ruling 031 left unresolved; these "
                           "are development inputs, not a holdout",
            "confirmation": f"{len(conf)} previously unused point/order IDs "
                            f"on the {PROFILE} profile, {PER_STRATUM} per "
                            "declared scope, frozen before any outcome",
            "strata": list(STRATA),
            "target_information_used": False,
            "excluded_prior_ids": len(u["set"]),
            "excluded_provenance": u["provenance"],
            "audit": audit,
        },
        "ledger": {
            "convention": "B: native evaluations plus independent end-to-end "
                          "reference evaluations",
            "transfer_remaining": 1628,
            "boundary_remaining": 0,
            "diagnostic_total_max": 1024,
            "development_charged_max": 384,
            "confirmation_points_max": 192,
            "confirmation_charged_reserved_min": 576,
            "point_order_ids_max": 258,
            "planned_development_charged": charged_dev,
            "planned_confirmation_charged": charged_conf,
            "planned_total_charged": charged_dev + charged_conf,
            "primary_path_within_the_native_bundle": "component record, not a "
                                                     "second charge",
            "standalone_primary_path_reevaluation": "charged one unit",
            "each_independent_end_to_end_reference": "separately charged",
            "per_quadrature_abscissa_is_a_new_ray": False,
            "second_batch_cap": 20000,
            "second_batch_spent_before_033": 18372,
            "suspended_full_response_reserve_4000":
                "suspended for the unlaunched integration design; any future "
                "integration campaign must fund its own validation",
            "new_allowance": "none",
        },
        "development_gate": {
            "declared_before_any_query": True,
            "continue_to_confirmation_requires_all_of": [
                "reference_B resolves every one of the 66 development cases",
                "reference_B agrees with the primary label on every one",
                "reference_A's failures concentrate at 90% or more in one "
                "identified cause",
            ],
            "otherwise": "report exactly which cases remain unresolved and "
                         "stop; the confirmation reserve is not spent",
        },
        "stopping_rules": {
            "development_unresolved_after_reference_B":
                "report exactly which cases remain and stop; do not continue "
                "to confirmation and do not launch any integration",
            "confirmation_unresolved":
                "return blocked with all evidence; no forced labels",
            "comparator_pass_means":
                "COMPARATOR_NUMERICALLY_VALIDATED_ON_TESTED_COHORTS",
            "comparator_pass_authorizes_integration": False,
            "no_tuning_after_the_confirmation_outcome": True,
            "retries": "must fit the committed cap; no refreeze resets a "
                       "counter",
        },
        "payload_requirements": {
            "write_order": "chunk payload and hash before the summary",
            "fields": ["evaluation_ids", "coordinates", "roots",
                       "lam_eta", "G_theta", "integral_values",
                       "error_estimates", "decision_margins",
                       "endpoint_limits", "root_residuals_and_conditioning",
                       "failure_reasons", "codes"],
            "cache_identity": ["screen_alpha", "screen_beta", "order",
                               "geometry", "observer_convention", "backend",
                               "numerical_policy", "precision"],
        },
        "development_ids": dev,
        "confirmation_ids": conf,
        "files": files,
    }
    (out / "FEASIBILITY_CLOSEOUT_033_INPUT_FREEZE.json").write_text(
        json.dumps(fz, indent=2) + "\n")
    print(json.dumps({"stage": "N0", "out": str(out.relative_to(ROOT)),
                      "development": len(dev), "confirmation": len(conf),
                      "pools": audit.get("pool_sizes"),
                      "planned_charged": charged_dev + charged_conf,
                      "excluded_prior_ids": len(u["set"]),
                      "seconds": round(time.time() - t0, 1)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main((ROOT / sys.argv[1]).resolve()))
