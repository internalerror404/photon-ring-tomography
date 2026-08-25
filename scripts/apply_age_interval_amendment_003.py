#!/usr/bin/env python3
"""AGE_INTERVAL_SEMANTICS_AMENDMENT_003 -- freeze the anchor and verify it.

The amendment itself is applied inside ``build_e3c_tables.py``, at the single
point where the canonical per-geometry E3C results are read, so that every
derived table speaks one vocabulary. This script is the independent check on
that rename and the record of the anchor:

* it refuses to run unless the E3C freeze and the registry on disk are the
  pinned ones, because reassembling from a different set of masks would
  silently produce a different table under the same name;
* it re-derives every reach and every longest-run span from the stored
  ``age_threshold_mask`` in the canonical per-geometry JSON, which still
  carries the pre-amendment values, and requires exact agreement;
* it freezes ``a_anchor_M`` from the reachable source-time window, never from
  a detectability or error curve;
* it counts the rows where the longest run anywhere is not the stretch that
  reaches the anchor, which is the difference the amendment exists to expose.

No physical operator is recomputed. The only inputs are the frozen
configuration and the canonical result JSON written at the E3C artifact commit.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from phrt.config import load_registry
from phrt.io.manifests import Gate, RunManifest, make_run_id, merge_gate_file
from phrt.metrics.age_intervals import (AMENDMENT, RETIRED_FIELDS,
                                        amend_depth_row, grid_anchor,
                                        interval_statistics, observation_anchor)

E3C_FREEZE = ROOT / "artifacts" / "configs" / "E3C_OPERATOR_GRID_FREEZE.json"
E3C_RESULTS = ROOT / "artifacts" / "e3c"
OUT = ROOT / "artifacts" / "configs" / "AGE_INTERVAL_SEMANTICS_AMENDMENT_003.json"

PINNED_E3C_FREEZE_SHA = ("7ab28bcd14674fb6544b577f19c00301f09e45ffec805cfcc"
                         "29896c53634bf1b")
# every derived artifact the reassembly rewrites. No entry here is a physical
# operator: all of them are aggregations of the canonical per-geometry results.
REASSEMBLED = [
    "artifacts/tables/e3c_depth_curves.parquet",
    "artifacts/tables/e3c_depth_curves.csv",
    "artifacts/tables/e3c_geometry_metrics.parquet",
    "artifacts/tables/e3c_geometry_metrics.csv",
    "artifacts/tables/e3c_geometry_surface.parquet",
    "artifacts/tables/e3c_geometry_surface.csv",
    "artifacts/reports/E3C_GEOMETRY_WIDE_OPERATOR_AUDIT.md",
    "artifacts/reports/E3C_MECHANISM_DECOMPOSITION.md",
    "artifacts/reports/E3C_MEASUREMENT_NOISE_MODEL.md",
    "artifacts/reports/AMENDMENT_002_LOCALIZED_CLASS_MECHANISM_DIAGNOSTIC.md",
    "artifacts/provenance/E3C_ARTIFACT_MANIFEST.json",
]

PINNED = {
    "accepted_base_commit": "0ef341dae3b21bc2bdd0e54a18971cff208af783",
    "measurement_correction_commit": "d6869f8d1c08889fee34e91d392c2bbc1bc9a62f",
    "e3c_execution_code_commit": "546763ed29e2be3fb129ec707cb07ee37a4f7db8",
    "e3c_artifact_commit": "7d610121adc95fb641ab5692d37d2b761b082039",
    "e3c_freeze_sha256": PINNED_E3C_FREEZE_SHA,
    "e3c_registry_sha256": ("2ba66f0209fe1cdec97b8cf5862494c22fb94704318f9601a"
                            "7a1f9eb4b783796"),
}


def main() -> int:
    t0 = time.time()
    got = hashlib.sha256(E3C_FREEZE.read_bytes()).hexdigest()
    if got != PINNED_E3C_FREEZE_SHA:
        print(f"STOP: E3C freeze on disk is {got}, pinned is "
              f"{PINNED_E3C_FREEZE_SHA}")
        return 2
    reg = load_registry()
    if reg.sha256 != PINNED["e3c_registry_sha256"]:
        print(f"STOP: registry sha256 {reg.sha256} is not the pinned one")
        return 2

    fz = json.loads(E3C_FREEZE.read_text())
    geoms = list(fz["geometries"])
    missing = [g for g in geoms if not (E3C_RESULTS / f"{g}.json").exists()]
    if missing:
        print(f"STOP: canonical E3C results missing for {missing}")
        return 2
    R = {g: json.loads((E3C_RESULTS / f"{g}.json").read_text()) for g in geoms}
    ages = np.asarray(R[geoms[0]]["ages"], dtype=float)
    h = float(fz["localized_probe"]["half_width_h_M"])

    t_obs = fz["observation"]["observer_times_M"]
    anchors = {g: observation_anchor(ages, h, t_obs, R[g]["windows"])
               for g in geoms}
    bad = [g for g in geoms if not anchors[g]["admissible"]]
    if bad:
        print(f"STOP: no admissible anchor at {bad}")
        return 3
    a_anchor_of = {g: float(anchors[g]["a_anchor_M"]) for g in geoms}
    anchor = grid_anchor([anchors[g] for g in geoms])

    # independent re-derivation of the reachable window from the same numbers
    # the operator was built from: t_min is t_obs.min() - max delay - 3h, so if
    # the windows the anchor uses were not the operator's windows this fails.
    win_dev = max(abs((min(t_obs) - max(w[1] for w in R[g]["windows"]) - 3.0 * h)
                      - R[g]["t_min"]) for g in geoms)

    for g in geoms:
        print(f"  {g}: a_anchor_M = {a_anchor_of[g]:g} "
              f"(delay in [{anchors[g]['delay_min_M']:.2f}, "
              f"{anchors[g]['delay_max_M']:.2f}] M, reachable source time "
              f"[{anchors[g]['source_time_min_M']:.2f}, "
              f"{anchors[g]['source_time_max_M']:.2f}] M)")
    print(f"grid anchor = {anchor['grid_anchor_M']:g} M ({anchor['rule']})")

    n_rows, n_checked, differs, non_contig, retired_seen = 0, 0, 0, 0, set()
    nothing_detectable = 0
    reach_max_dev, span_max_dev = 0.0, 0.0
    for g in geoms:
        a_anchor = a_anchor_of[g]
        for r in R[g]["depth_rows"]:
            n_rows += 1
            retired_seen |= {k for k in RETIRED_FIELDS if k in r}
            ok = np.array([c == "1" for c in r["age_threshold_mask"]], bool)
            st = interval_statistics(ages, ok, a_anchor)
            if r["oldest_detectable_age_probe"] >= 0:
                reach_max_dev = max(reach_max_dev, abs(
                    st["oldest_detectable_age_probe"]
                    - r["oldest_detectable_age_probe"]))
            span_max_dev = max(span_max_dev, abs(
                st["longest_detectable_run_span_M"]
                - r["largest_contiguous_detectable_depth"]))
            n_checked += 1
            if st["contiguous_detectable_span_from_anchor_M"] != \
                    st["longest_detectable_run_span_M"]:
                differs += 1
            if st["oldest_detectable_age_probe"] < 0:
                nothing_detectable += 1
            elif not st["is_contiguous"]:
                non_contig += 1
            # the amender itself must accept the row; it raises on disagreement
            amend_depth_row(r, ages, a_anchor)

    run_id = make_run_id("E3CAMD", reg.sha256)
    man = RunManifest(run_id=run_id, experiment_id="AGE_INTERVAL_AMENDMENT_003",
                      seeds={},
                      extra={**PINNED, "a_anchor_M_by_geometry": a_anchor_of,
                             "grid_anchor_M": anchor["grid_anchor_M"],
                             "amendment": AMENDMENT,
                             "operators_recomputed": False,
                             "depth_rows_reassembled": n_rows})
    man.add_input(E3C_FREEZE)
    man.add_input(reg.path)

    man.add_gate(Gate("E3C_AMD003_reach_rederived_from_masks",
                      "PASS" if reach_max_dev == 0.0 else "FAIL",
                      measured=reach_max_dev, threshold=0.0,
                      note=f"every one of the {n_checked} canonical depth rows "
                           "had its reach re-derived from its own stored mask "
                           "and compared with the value the row already carried; "
                           "no operator was recomputed"))
    man.add_gate(Gate("E3C_AMD003_longest_run_span_rederived_from_masks",
                      "PASS" if span_max_dev == 0.0 else "FAIL",
                      measured=span_max_dev, threshold=0.0,
                      note="the renamed longest_detectable_run_span_M equals the "
                           "retired largest_contiguous_detectable_depth exactly, "
                           "so the amendment is a rename and two additions, not a "
                           "change of value"))
    man.add_gate(Gate("E3C_AMD003_anchor_frozen_from_support", "PASS",
                      measured=anchor["grid_anchor_M"], threshold=None,
                      note="per-geometry anchors "
                           + ", ".join(f"{g}={a_anchor_of[g]:g}" for g in geoms)
                           + f" M. {anchor['rule']}"))
    man.add_gate(Gate("E3C_AMD003_anchor_windows_are_the_operator_windows",
                      "PASS" if win_dev < 1e-9 else "FAIL",
                      measured=win_dev, threshold=1e-9,
                      note="the reachable source-time window the anchor is "
                           "derived from reproduces the basis lower edge each "
                           "operator was actually built with, so the anchor is "
                           "not computed from a different set of rays"))
    man.add_gate(Gate("E3C_AMD003_rows_where_anchored_span_differs", "PASS",
                      measured=differs, threshold=None,
                      note="rows where the longest detectable run anywhere is not "
                           "the stretch reaching the anchor. Instrumentation: "
                           "this is the difference the amendment exists to "
                           "expose, not a pass/fail criterion"))
    man.add_gate(Gate("E3C_AMD003_noncontiguous_detectable_sets", "PASS",
                      measured=non_contig, threshold=None,
                      note=f"of the {n_checked - nothing_detectable} rows with "
                           "any detectable age, this many have a detectable set "
                           "that is not an interval, so the reach overstates the "
                           f"usable span. {nothing_detectable} further rows have "
                           "no detectable age at all and are excluded from this "
                           "count rather than folded into it"))

    # before/after digests of every derived artifact the reassembly rewrites,
    # taken against the canonical E3C artifact commit, so the change is
    # auditable without having to diff parquet by hand
    import subprocess
    reassembled = []
    for rel in REASSEMBLED:
        after = hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() \
            if (ROOT / rel).exists() else None
        try:
            before = subprocess.run(
                ["git", "-C", str(ROOT), "rev-parse",
                 f"{PINNED['e3c_artifact_commit']}:{rel}"],
                capture_output=True, text=True, check=True).stdout.strip()
            blob = subprocess.run(["git", "-C", str(ROOT), "cat-file", "blob", before],
                                  capture_output=True, check=True).stdout
            before_sha = hashlib.sha256(blob).hexdigest()
        except subprocess.CalledProcessError:
            before_sha = None
        reassembled.append({"path": rel, "sha256_at_e3c_artifact_commit": before_sha,
                            "sha256_after_amendment": after,
                            "changed": before_sha != after})

    OUT.write_text(json.dumps({
        "amendment": AMENDMENT,
        "reassembled_derived_artifacts": reassembled,
        "supersedes": {
            "largest_contiguous_detectable_depth": "longest_detectable_run_span_M",
            "largest_contiguous_start_M": "longest_detectable_run_start_M",
            "largest_contiguous_end_M": "longest_detectable_run_end_M"},
        "adds": ["a_anchor_M", "contiguous_detectable_end_from_anchor_M",
                 "contiguous_detectable_span_from_anchor_M",
                 "anchor_is_detectable"],
        "reach_statistic_retained": "oldest_detectable_age_probe",
        "a_anchor_M_by_geometry": a_anchor_of,
        "grid_anchor_M": anchor["grid_anchor_M"],
        "anchor_rule": anchor["rule"],
        "per_geometry_anchor": {g: anchors[g] for g in geoms},
        "anchor_definition": (
            "a probe centred at age a occupies source time -a within 3 half "
            "widths; the anchor is the youngest age on the common grid whose "
            "whole probe support lies inside the reachable source-time window "
            "[min(t_obs) - max(delay), max(t_obs) - min(delay)]. Where the "
            "minimum delay exceeds the last observer sample the anchor is a "
            "positive age and the present is simply not observed"),
        "anchored_stable_depth": (
            "T_stable_anchor(eps,q) = sup{ T >= a_anchor : "
            "Pr[ sup_{a_anchor <= a <= T} E(a) <= eps ] >= q }; the supremum "
            "over the age window is inside the probability, taken per truth, so "
            "a truth counts only if the whole window from the anchor out to T is "
            "good for that truth"),
        "anchored_stable_span": "L_stable_anchor = T_stable_anchor - a_anchor",
        "prohibition": ("an arbitrary old detectable island is never labelled "
                        "continuous history from the anchor; a secondary "
                        "unanchored longest stable interval may be reported with "
                        "both endpoints but must not be called depth from the "
                        "present"),
        "operators_recomputed": False,
        "depth_rows_reassembled": n_rows,
        "rows_where_anchored_span_differs": differs,
        "noncontiguous_rows": non_contig,
        "rows_with_no_detectable_age": nothing_detectable,
        "retired_names_present_in_preamendment_results": sorted(retired_seen),
        **PINNED}, indent=2) + "\n")
    man.add_output(OUT)
    mp = man.write(reg.path, reg.sha256, runtime_seconds=time.time() - t0)
    merge_gate_file(man.gates, run_id)
    print(f"checked {n_checked} canonical depth rows against their own masks")
    print(f"  max reach deviation {reach_max_dev}, max span deviation {span_max_dev}")
    print(f"  rows where anchored span != longest run span: {differs}")
    print(f"  non-contiguous detectable sets: {non_contig} "
          f"({nothing_detectable} rows have no detectable age at all)")
    print(f"manifest {mp}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
