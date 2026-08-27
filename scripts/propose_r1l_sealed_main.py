#!/usr/bin/env python3
"""Propose and commit the R1L sealed-main bank without scoring it.

REVIEWER_RULING_R1L_REPRODUCIBILITY_009 item 10, last clause. The commitment
fixes which truths the sealed main will contain, by hashing the seeds that
generate them. Nothing here renders a movie through an operator, forms a datum,
or computes an error -- the bank's identity is committed, its content is not
inspected.

The point of committing before the pilot is reported is that the sealed set
cannot then be chosen to flatter whatever the pilot showed.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from phrt.attestation import attest
from phrt.config import sha256_file

S2 = ROOT / "artifacts" / "configs" / "R1L_STAGE2_VALIDATION_ACTIVATION_010.json"
OUT = ROOT / "artifacts" / "configs" / "R1L_SEALED_MAIN_COMMITMENT.json"
SEED = 20260905
PER_CELL = 24


def main() -> int:
    fz = json.loads(S2.read_text())
    banks = fz["counts"]["banks"]
    families = fz["counts"]["families"]

    cells, seeds = {}, {}
    for b in banks:
        for f in families:
            payload = json.dumps({"bank": b, "family": f, "split": "sealed_main",
                                  "n": PER_CELL, "seed": SEED},
                                 sort_keys=True).encode()
            key = f"{b}|{f}"
            cells[key] = hashlib.sha256(payload).hexdigest()
            seeds[key] = [int(hashlib.sha256(payload + f"|{i}".encode()
                                             ).hexdigest()[:16], 16) % (2 ** 63)
                          for i in range(PER_CELL)]

    validation = fz["split_rule"]["commitments"]
    overlap = set(cells.values()) & set(validation.values())

    doc = {
        "schema": "phrt-sealed-commitment/1",
        "id": "R1L_SEALED_MAIN_COMMITMENT",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "ruling": "REVIEWER_RULING_R1L_REPRODUCIBILITY_009 item 10",
        "status": "COMMITTED_NOT_GENERATED_NOT_SCORED",
        "scored": False,
        "generated_through_an_operator": False,
        "inspected": False,
        "rule": "the commitment fixes which truths the sealed main will "
                "contain. No movie is rendered through an operator, no datum is "
                "formed and no error is computed here. Committing before the "
                "pilot is reported is what stops the sealed set from being "
                "chosen to flatter the pilot",
        "seed": SEED,
        "truths_per_bank_family": PER_CELL,
        "banks": banks, "families": families,
        "n_cells": len(cells), "n_truths": len(cells) * PER_CELL,
        "cell_commitments": cells,
        "truth_seeds_sha256": hashlib.sha256(
            json.dumps(seeds, sort_keys=True).encode()).hexdigest(),
        "disjoint_from_validation": {
            "checked": True,
            "n_overlapping_cell_commitments": len(overlap),
            "why_disjoint": "the sealed cells use split 'sealed_main' and seed "
                            f"{SEED}, both different from the validation "
                            "commitments, so no truth seed can coincide",
        },
        "authorization": "the sealed main may not be executed under the present "
                         "ruling. This document exists so that when it is "
                         "authorized, the bank is already fixed",
        "provenance": {"stage2_freeze_sha256": sha256_file(S2)},
    }
    doc["attestation"] = attest([S2])
    OUT.write_text(json.dumps(doc, indent=2) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}")
    print(f"  sha256 {sha256_file(OUT)}")
    print(f"  {len(cells)} cells, {len(cells) * PER_CELL} truths, "
          f"overlap with validation: {len(overlap)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
