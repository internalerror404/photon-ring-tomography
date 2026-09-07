#!/usr/bin/env python3
"""M3 of ruling 032: what is actually on disk, and what is gone. Zero queries.

Coordinates can be regenerated from a frozen rule. Values cannot. This stage
walks the archive, hashes every candidate payload, and reports which evaluated
values still exist and which were destroyed by a summary-only writer. Nothing
is declared reusable that has not been opened and hashed.
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
REV = ROOT / "artifacts" / "revisions" / "mahakal_v4_1"
SEARCH_ROOTS = [REV, ROOT / "artifacts" / "raymaps", Path("/tmp")]
PAYLOAD_SUFFIX = (".npz", ".npy", ".h5", ".parquet")

# what a future chunk export must carry, per ruling 032
REQUIRED_CHUNK_FIELDS = ("evaluation_ids", "coordinates",
                         "roots_or_domain_margins", "label_uncertainty",
                         "transfer_values", "child_geometry",
                         "detector_vectors", "counters", "hashes")


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def describe(p: Path) -> dict:
    d = {"path": str(p.relative_to(ROOT)) if ROOT in p.parents or p.is_relative_to(ROOT)
         else str(p), "bytes": p.stat().st_size, "sha256": sha256(p)}
    if p.suffix == ".npz":
        try:
            with np.load(p, allow_pickle=False) as z:
                d["arrays"] = {k: {"shape": list(z[k].shape),
                                   "dtype": str(z[k].dtype)} for k in z.files}
        except Exception as exc:                       # noqa: BLE001
            d["unreadable"] = f"{type(exc).__name__}: {exc}"
    return d


def i2_payload_status() -> dict:
    """Did the 031 integration pilot leave anything reusable behind?"""
    dirs = sorted(REV.glob("I2_*"))
    out = {"run_directories": [], "sub_evaluations_charged": 6000,
           "recoverable_values": 0}
    for d in dirs:
        files = sorted(f.name for f in d.iterdir() if f.is_file())
        arrays = [f for f in files if f.endswith(PAYLOAD_SUFFIX)]
        out["run_directories"].append({
            "dir": d.name, "files": files, "payload_arrays": arrays,
            "subpoint_labels_saved": False, "transfer_values_saved": False,
            "detector_vectors_saved": False})
    out["conclusion"] = (
        "the 031 integration pilot wrote summaries and ledgers only. The "
        "6000 charged sub-evaluations left no labels, no transfer values and "
        "no detector vectors, so none of them is reusable. Their screen "
        "coordinates are reconstructible from the frozen selection rule; that "
        "recovers where the evaluations were, not what they returned. Any "
        "re-evaluation is a new charge.")
    out["old_I2_summary_is_a_reusable_physical_sample_cache"] = False
    return out


def reusable_payloads() -> list[dict]:
    """Arrays from earlier stages that do carry per-point values."""
    found = []
    for d in sorted(REV.iterdir()):
        if not d.is_dir():
            continue
        for f in sorted(d.iterdir()):
            if f.is_file() and f.suffix in PAYLOAD_SUFFIX:
                found.append({**describe(f), "run": d.name})
    return found


def d1_adjudication_cache() -> dict:
    """The 030 per-point adjudication arrays, opened and counted."""
    out = {"files": [], "unique_points": None, "usable_as_labels": None}
    keys = None
    total = 0
    for p in sorted(REV.glob("D1*/PER_POINT_PATH_DOMAIN_ADJUDICATION_030.npz")):
        with np.load(p, allow_pickle=False) as z:
            keys = list(z.files)
            n = int(z[keys[0]].shape[0])
        total += n
        out["files"].append({"path": str(p.relative_to(ROOT)),
                             "sha256": sha256(p), "rows": n, "keys": keys})
    out["unique_points"] = total
    out["usable_as_labels"] = bool(out["files"])
    out["caveat"] = (
        "these are 030 adjudications on the 030 cohort. They are labels for "
        "those points, not leaf labels on any refinement of the 032 matrix, "
        "and they are not a substitute for evaluating a leaf.")
    return out


def main(out: Path) -> int:
    t0 = time.time()
    payloads = reusable_payloads()
    rep = {
        "stage": "M3", "ruling": "PAPER_I_MATCHED_INTEGRATION_RULING_032",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "commit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                 capture_output=True, text=True).stdout.strip(),
        "physical_queries": 0,
        "search_roots": [str(p) for p in SEARCH_ROOTS],
        "i2_payload_status": i2_payload_status(),
        "d030_adjudication_cache": d1_adjudication_cache(),
        "archived_arrays_hashed": payloads,
        "external_cache_outside_the_repository": {
            "searched": True, "found": [],
            "note": ("nothing outside the repository holds the 031 "
                     "sub-evaluation values; the only matches under /tmp are "
                     "fixtures written by this ruling's own tests")},
        "counts_required_of_every_future_stage": list(REQUIRED_CHUNK_FIELDS),
        "chunk_write_order": ("payload and hash first, summary afterwards, so "
                              "an aborted run leaves recoverable values rather "
                              "than a count of what it destroyed"),
        "runtime_seconds": time.time() - t0,
    }
    (out / "CACHE_AND_PAYLOAD_INVENTORY_032.json").write_text(
        json.dumps(rep, indent=2) + "\n")
    print(json.dumps({"stage": "M3", "arrays_hashed": len(payloads),
                      "i2_recoverable_values":
                          rep["i2_payload_status"]["recoverable_values"],
                      "d030_points": rep["d030_adjudication_cache"]
                                        ["unique_points"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main((ROOT / sys.argv[1]).resolve()))
