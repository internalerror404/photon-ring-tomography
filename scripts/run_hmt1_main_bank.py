#!/usr/bin/env python3
"""HMT-1 sealed main, stage A: the held-out bank and every source-side gate.

Items 9, 10 and 13 of REVIEWER_RULING_HMT1_MAIN_017.

Every gate that can be decided from the source alone is decided here, and all
of them must pass before stage B is allowed to import an operator. That
ordering is the point: a source defect found after the operator has run is a
defect found too late, because by then the held-out bank has been spent.

This stage imports no operator and nothing that could reach one.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from phrt.numerics import pin, require_single_threaded

pin()

import numpy as np  # noqa: E402

from hmt1_main_common import (FZ, HASHES, VFZ, build_bank, commitment,  # noqa: E402
                              grids)
from phrt.attestation import attest  # noqa: E402
from phrt.config import sha256_file  # noqa: E402
from phrt.io.endpoint_lineage import screen  # noqa: E402
from phrt.io.manifests import Gate, merge_gate_file  # noqa: E402
from phrt.io.tables import write_table  # noqa: E402
from phrt.metrics.features import extract  # noqa: E402
from phrt.sources.contrast import OFF_MANIFOLD, build  # noqa: E402

STAGE_A_GATES = ROOT / "artifacts" / "gates" / "hmt1_main_stage_a_gates.json"


def _validation_seeds(vfz):
    out = set()
    for f in vfz["counts"]["families"]:
        for s in vfz["counts"]["splits"]:
            for rg in vfz["counts"]["regimes"]:
                for i in range(vfz["counts"]["truths_per_family_split_regime"]):
                    p = json.dumps({"family": f, "split": s, "regime": rg,
                                    "n": 8, "seed": vfz["seeds"]["bank_seed"],
                                    "model": "contrast"}, sort_keys=True).encode()
                    out.add(int(hashlib.sha256(
                        p + f"|{i}".encode()).hexdigest()[:16], 16) % (2 ** 63))
    return out


def _retired_seeds(fz, n):
    """Seeds of every bank this freeze has retired, so none can be redrawn."""
    out = set()
    for seed in fz.get("retired_bank_seeds", []):
        for family in fz["design"]["families"]:
            for i in range(n):
                p = json.dumps({"family": family, "split": "sealed_main_heldout",
                                "n": n, "seed": int(seed), "model": "contrast"},
                               sort_keys=True).encode()
                out.add(int(hashlib.sha256(
                    p + f"|{i}".encode()).hexdigest()[:16], 16) % (2 ** 63))
    return out


def gate(name, ok, measured, threshold, note=None):
    d = {"status": "PASS" if ok else "FAIL", "measured": measured,
         "threshold": threshold}
    if note:
        d["note"] = note
    return name, d


def main() -> int:
    t0 = time.time()
    numerics = require_single_threaded()
    g = grids()
    fz, vfz = g["fz"], g["vfz"]
    seed = int(fz["seeds"]["bank_seed"])
    n = int(fz["design"]["truths_per_family"])
    fams = list(fz["design"]["families"])

    recomputed = {f: commitment(f, n, seed) for f in fams}
    commit_ok = recomputed == fz["commitments"]
    print(f"commitments reproduce: {commit_ok}")

    bank = build_bank(g)
    print(f"bank built, {len(bank)} held-out truths, {time.time() - t0:.0f}s")

    vseeds = _validation_seeds(vfz)
    rseeds = _retired_seeds(fz, n)
    overlap = sum(1 for k in bank if bank[k]["truth_seed"] in vseeds | rseeds)

    worst = {"zero_mean": 0.0, "azimuthal": 0.0, "positivity": 0.0,
             "background_floor": 0.0, "determinism": 0.0,
             "g10c_radial_cells": 0.0, "g10c_azimuthal_cells": 0.0}
    rows = []
    for (family, i), rec in sorted(bank.items()):
        d, ge = rec["diag"], rec["windowed"]
        worst["zero_mean"] = max(worst["zero_mean"], d["zero_mean_max_abs"])
        worst["azimuthal"] = max(worst["azimuthal"], d["azimuthal_mean_max_abs"])
        worst["positivity"] = max(worst["positivity"], max(0.0, -d["min_total"]))
        worst["background_floor"] = max(worst["background_floor"],
                                        max(0.0, 1e-6 - d["min_background"]))
        f2 = extract(rec["dj"], g["gt"], g["ages"], g["r_axis"], g["phi_axis"],
                     g["half"])
        worst["determinism"] = max(worst["determinism"], max(
            float(np.abs(np.asarray(rec["features"][c])
                         - np.asarray(f2[c])).max())
            for c in ("r_h", "phi_h", "A_h", "a_m1", "a_m2")))
        for a, b in (("g10c_radial_cells", "radial_cells"),
                     ("g10c_azimuthal_cells", "azimuthal_cells")):
            if np.isfinite(ge[b]):
                worst[a] = max(worst[a], ge[b])
        rows.append({
            "family": family, "index": i, "truth_seed": rec["truth_seed"],
            "contrast_fraction": d["contrast_fraction"],
            "peak_fraction_of_background":
                d["achieved_peak_fraction_of_background"],
            "min_total": d["min_total"], "min_background": d["min_background"],
            "zero_mean_max_abs": d["zero_mean_max_abs"],
            "azimuthal_mean_max_abs": d["azimuthal_mean_max_abs"],
            "positivity_scale": d["positivity_scale"],
            "g10c_radial_cells": ge["radial_cells"],
            "g10c_azimuthal_cells": ge["azimuthal_cells"],
            "g10c_ages_scored": ge["n_ages_scored"],
            "chose_global_maximum_fraction": ge["chose_global_maximum_fraction"],
            **{f"hash_{k}": v for k, v in rec["hashes"].items()}})

    off_rows = []
    for family in OFF_MANIFOLD:
        for i in range(4):
            os_ = int(hashlib.sha256(
                f"hmt1_main_off_manifold|{family}|{i}".encode()
            ).hexdigest()[:16], 16) % (2 ** 63)
            _, _, _, odj, _, od = build(np.random.default_rng(os_), family,
                                        g["spin"], g["r_in"], g["r_out"],
                                        g["gr"], g["gp"], g["gt"],
                                        g["t_index"], g["NT"])
            off_rows.append({"family": family, "index": i, "scored": False,
                             "truth_seed": os_, "min_total": od["min_total"],
                             "azimuthal_mean_max_abs":
                                 od["azimuthal_mean_max_abs"]})

    g10c = max(worst["g10c_radial_cells"], worst["g10c_azimuthal_cells"])
    gates = dict([
        gate("HMT1M_G1_pinned_numerical_environment",
             numerics["all_single_threaded"], 1, 1),
        gate("HMT1M_G2_held_out_commitment_reproduces", commit_ok,
             1 if commit_ok else 0, 1,
             "all six declared commitments, not only the families run"),
        gate("HMT1M_G3_disjoint_from_validation_and_retired_truths",
             overlap == 0, overlap, 0,
             "held-out seeds also appearing in the validation bank or in any "
             "bank this freeze has retired"),
        gate("HMT1M_G4_contrast_zero_spatial_mean",
             worst["zero_mean"] <= 1e-10, worst["zero_mean"], 1e-10),
        gate("HMT1M_G4b_azimuthal_zero_mean",
             worst["azimuthal"] <= 1e-10, worst["azimuthal"], 1e-10),
        gate("HMT1M_G5_total_emissivity_nonnegative",
             worst["positivity"] <= 0.0, worst["positivity"], 0.0),
        gate("HMT1M_G6_background_strictly_positive",
             worst["background_floor"] <= 0.0, worst["background_floor"], 0.0),
        gate("HMT1M_G10_feature_extraction_deterministic",
             worst["determinism"] <= 1e-9, worst["determinism"], 1e-9),
        gate("HMT1M_G10c_truth_extraction_matches_independent_windowed_reference",
             g10c <= 1.0, g10c, 1.0,
             f"worst displacement from the independent windowed reference, in "
             f"evaluation-grid cells: radial {worst['g10c_radial_cells']:.3f}, "
             f"azimuthal {worst['g10c_azimuthal_cells']:.3f}"),
        gate("HMT1M_G17_off_manifold_bank_built", len(off_rows) > 0,
             len(off_rows), len(OFF_MANIFOLD) * 4,
             "built here and marked unscored. Stage B checks that none "
             "reaches an endpoint"),
    ])
    failed = sorted(k for k, v in gates.items() if v["status"] != "PASS")

    for name, rr in (("hmt1_main_source_banks", rows),
                     ("hmt1_main_off_manifold", off_rows)):
        ok, bad = screen(name, rr, withheld=bool(failed))
        if not ok:
            print(f"firewall blocked {name}: {bad}", file=sys.stderr)
            continue
        write_table(rr, name)

    doc = {
        "schema": "phrt-hmt1-main-stage-a/1",
        "id": "HMT1_MAIN_STAGE_A",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "ruling": "REVIEWER_RULING_HMT1_MAIN_017",
        "freeze": fz["id"], "freeze_sha256": sha256_file(FZ),
        "stage": "A", "operator_imported": False,
        "gates": gates, "failed_gates": failed,
        "stage_b_may_proceed": not failed,
        "rule": "stage B must find this file, with no failed gate, before it "
                "imports an operator. A source defect discovered after the "
                "operator has run is discovered too late",
        "n_truths": len(bank), "truths_per_family": n, "families": fams,
        "seed_commitments": recomputed,
        "worst_bank_residuals": worst,
        "hashes": {f"{f}|{i}": bank[(f, i)]["hashes"] for (f, i) in sorted(bank)},
        "truth_seeds": {f"{f}|{i}": bank[(f, i)]["truth_seed"]
                        for (f, i) in sorted(bank)},
        "off_manifold_seeds": {f"{r['family']}|{r['index']}": r["truth_seed"]
                               for r in off_rows},
        "numerical_environment": numerics,
        "attestation": attest([FZ]),
    }
    STAGE_A_GATES.parent.mkdir(parents=True, exist_ok=True)
    STAGE_A_GATES.write_text(json.dumps(doc, indent=2, default=str) + "\n")
    HASHES.parent.mkdir(parents=True, exist_ok=True)
    HASHES.write_text(json.dumps(doc, indent=2, default=str) + "\n")

    # the HMT-1 ledger must reflect the current run, not the retired one it
    # last saw. Stage A's gates are real gates and belong in it.
    merge_gate_file(
        [Gate(k, v["status"], measured=v.get("measured"),
              threshold=v.get("threshold"), note=v.get("note"))
         for k, v in gates.items()],
        "HMT1M_STAGE_A",
        path=ROOT / "artifacts" / "gates" / "hmt1_correctness_gates.json")

    print("\nstage A gates")
    for k, v in gates.items():
        print(f"  {k:62s} {v['status']}")
    print(f"\nwrote {STAGE_A_GATES.relative_to(ROOT)}")
    print(f"  worst G10c {g10c:.3f} cells, azimuthal mean "
          f"{worst['azimuthal']:.2e}, most negative total "
          f"{-worst['positivity']:.3f}")
    print(f"  stage B may proceed: {not failed}")
    print(f"total {time.time() - t0:.0f}s")
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
