#!/usr/bin/env python3
"""HMT-1 sealed main, stage A: draw the held-out bank and commit its hashes.

Item 9 of REVIEWER_RULING_HMT1_VALIDATION_015. This stage applies no operator
and imports nothing that could. It draws the 96 held-out truths, extracts each
one's feature history, and writes the hashes that stage B must reproduce before
it is allowed to evaluate anything.

The point of the ordering is that the bank is fixed in the repository's history
before anyone has seen how it scores. A hash committed afterwards attests
nothing.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from phrt.numerics import pin, record as numerics_record, require_single_threaded

pin()

import numpy as np  # noqa: E402

from hmt1_main_common import (FZ, HASHES, build_bank, commitment,  # noqa: E402
                              grids)
from phrt.attestation import attest  # noqa: E402
from phrt.config import sha256_file  # noqa: E402
from phrt.io.tables import write_table  # noqa: E402


def main() -> int:
    t0 = time.time()
    numerics = require_single_threaded()
    g = grids()
    fz = g["fz"]
    seed = int(fz["seeds"]["bank_seed"])
    n = int(fz["design"]["truths_per_family"])
    fams = list(fz["design"]["families"])

    recomputed = {f: commitment(f, n, seed) for f in fams}
    if recomputed != fz["commitments"]:
        print("seed commitments do not reproduce the sealed freeze", file=sys.stderr)
        return 1
    print(f"commitments reproduce, {len(fams)} families")

    bank = build_bank(g)
    print(f"bank built, {len(bank)} held-out truths, {time.time() - t0:.0f}s")

    rows, worst = [], {"zero_mean": 0.0, "azimuthal": 0.0, "positivity": 0.0,
                       "background_floor": 0.0, "generative_radial_cells": 0.0,
                       "generative_azimuthal_cells": 0.0}
    for (family, i), rec in sorted(bank.items()):
        d, ge = rec["diag"], rec["generative"]
        worst["zero_mean"] = max(worst["zero_mean"], d["zero_mean_max_abs"])
        worst["azimuthal"] = max(worst["azimuthal"], d["azimuthal_mean_max_abs"])
        worst["positivity"] = max(worst["positivity"], max(0.0, -d["min_total"]))
        worst["background_floor"] = max(worst["background_floor"],
                                        max(0.0, 1e-6 - d["min_background"]))
        for a, b in (("generative_radial_cells", "radial_cells"),
                     ("generative_azimuthal_cells", "azimuthal_cells")):
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
            "generative_radial_cells": ge["radial_cells"],
            "generative_azimuthal_cells": ge["azimuthal_cells"],
            "generative_ages_scored": ge["n_ages_scored"],
            **{f"hash_{k}": v for k, v in rec["hashes"].items()},
        })
    write_table(rows, "hmt1_main_source_banks")

    doc = {
        "schema": "phrt-hmt1-main-bank-hashes/1",
        "id": "HMT1_MAIN_BANK_HASHES",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "ruling": "REVIEWER_RULING_HMT1_VALIDATION_015",
        "freeze": fz["id"],
        "freeze_sha256": sha256_file(FZ),
        "stage": "A",
        "operator_applied": False,
        "rule": "stage B must reproduce every hash below before it applies an "
                "operator to any of these truths. A mismatch is "
                "HMT1_MAIN_IMPLEMENTATION_DEFECT, not a warning",
        "n_truths": len(bank),
        "truths_per_family": n,
        "families": fams,
        "seed_commitments": recomputed,
        "worst_bank_residuals": worst,
        "hashes": {f"{family}|{i}": bank[(family, i)]["hashes"]
                   for (family, i) in sorted(bank)},
        "truth_seeds": {f"{family}|{i}": bank[(family, i)]["truth_seed"]
                        for (family, i) in sorted(bank)},
        "numerical_environment": numerics,
        "attestation": attest([FZ]),
    }
    HASHES.parent.mkdir(parents=True, exist_ok=True)
    HASHES.write_text(json.dumps(doc, indent=2, default=str) + "\n")
    print(f"wrote {HASHES.relative_to(ROOT)}\n  sha256 {sha256_file(HASHES)}")
    print(f"  worst azimuthal mean {worst['azimuthal']:.2e}, "
          f"most negative total {-worst['positivity']:.3f}")
    print(f"  worst generative displacement "
          f"{max(worst['generative_radial_cells'], worst['generative_azimuthal_cells']):.3f} cells")
    print(f"total {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
