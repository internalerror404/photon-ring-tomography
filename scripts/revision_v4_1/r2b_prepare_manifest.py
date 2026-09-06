#!/usr/bin/env python3
"""Phase A: the identical target manifest, prepared without seeing a spectrum.

The selection rule is re-executed from the frozen maps and the registered
basis, the result is checked against the counts the original run committed,
and the explicit column indices are written down this time so the replay's
guard can compare index sets rather than cardinalities.

No operator is whitened here and no singular value is computed.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from phrt.numerics import pin

pin()

import numpy as np  # noqa: E402

from phrt.geometry.raymap import read  # noqa: E402
from phrt.geometry.sampling import common_count, stratified_subsample  # noqa: E402
from phrt.revision_v4_1.guards import sha256  # noqa: E402
from phrt.sources.localized_basis import LocalizedBasis  # noqa: E402

R1FZ = ROOT / "artifacts" / "configs" / "R1_MAIN_FREEZE.json"
MAPS = ROOT / "artifacts" / "raymaps"
GEOMETRY = "a050_i050"
ORIGINAL = (ROOT / "artifacts" / "revisions" / "mahakal_v4_1"
            / "R0_20260906T070540Z_38e1f8a"
            / "R2_TARGET_AND_NUISANCE_MANIFEST.json")
OUT = (ROOT / "artifacts" / "revisions" / "mahakal_v4_1"
       / "R2_REPLAY_TARGET_MANIFEST.json")


def main() -> int:
    r1 = json.loads(R1FZ.read_text())
    obs, pm = r1["observation"], r1["physical_model"]
    t_obs = np.asarray(obs["observer_times_M"], float)
    rng = np.random.default_rng(int(obs["subsample_seed"]))
    map_paths = [MAPS / f"{GEOMETRY}_n{n}_core.h5" for n in pm["orders"]]
    base = common_count([stratified_subsample(read(p),
                                              int(obs["rays_per_order"]), rng)
                         for p in map_paths], rng)

    L = LocalizedBasis(float(pm["r_inner_M"]), float(pm["r_outer_M"]),
                       float(obs["basis_t_min"]), float(obs["basis_t_max"]),
                       4, 7, 8)
    direct_times = (t_obs[:, None] - base[0].delay[None, :]).ravel()
    covered = L.temporal_columns_covering(direct_times)
    labels = L.labels()
    target = np.array([(lb["azimuthal_m"] >= 1)
                       and (not covered[lb["temporal_mode"]]) for lb in labels])

    orig = json.loads(ORIGINAL.read_text())
    same = (int(target.sum()) == int(orig["n_target_columns"])
            and int((~target).sum()) == int(orig["n_nuisance_columns"]))
    if not same:
        raise SystemExit(
            f"selection drifted from the committed run: "
            f"{int(target.sum())}/{int((~target).sum())} against "
            f"{orig['n_target_columns']}/{orig['n_nuisance_columns']}. "
            "Investigate; do not proceed")

    doc = {
        "schema": "phrt-r2-target-manifest/2",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "phase": "A",
        "prepared_without_inspecting_spectra": True,
        "reuses": "the original support rule and the exact column set",
        "original_manifest": {
            "path": str(ORIGINAL.relative_to(ROOT)),
            "sha256": sha256(ORIGINAL),
            "n_target_columns": orig["n_target_columns"],
            "n_nuisance_columns": orig["n_nuisance_columns"],
        },
        "selection_rule": orig["selection_rule"],
        "geometry": orig["geometry"], "orders": orig["orders"],
        "observer_times_M": orig["observer_times_M"],
        "source_class": orig["source_class"],
        "ray_maps": {str(p.relative_to(ROOT)): sha256(p) for p in map_paths},
        "subsample_seed": int(obs["subsample_seed"]),
        "direct_footprint_M": [float(direct_times.min()),
                               float(direct_times.max())],
        "temporal_modes_outside_direct_footprint": [
            int(i) for i in np.flatnonzero(~covered)],
        "n_target_columns": int(target.sum()),
        "n_nuisance_columns": int((~target).sum()),
        "target_column_indices": [int(i) for i in np.flatnonzero(target)],
        "target_column_labels": [labels[i] for i in np.flatnonzero(target)],
        "matches_original_selection": True,
        "empty_target": bool(target.sum() == 0),
    }
    OUT.write_text(json.dumps(doc, indent=2) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}")
    print(f"  {doc['n_target_columns']} target / "
          f"{doc['n_nuisance_columns']} nuisance, identical to the original")
    print(f"  indices recorded: {len(doc['target_column_indices'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
