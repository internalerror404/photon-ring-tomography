#!/usr/bin/env python3
"""Does the row-count convention move any archived endpoint?

Ledger C02 / protocol G20. The count-only change multiplies whitened
information by m*/m at fixed reference energy, so every stored age-information
curve can be rescaled analytically and every threshold decision rebuilt. No
geodesics are recomputed and no frozen file is written.

A small multiplier and a 4 M age grid do not prove an endpoint is unchanged,
so nothing is inferred: each mask is rebuilt bit by bit, at every archived SNR
and for every arm, and every crossing is counted. The eleven geometries whose
factor is exactly one double as the self-check -- if the rebuild does not
reproduce their archived endpoints bit for bit, the rebuild is wrong and the
one geometry that does change cannot be trusted either.

J_old is nonlinear in the multiplier and is recomputed from the rescaled
curve, never scaled.
"""
from __future__ import annotations

import csv
import json
import math
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from phrt.numerics import pin

pin()

import numpy as np  # noqa: E402

from phrt.revision_v4_1.calibration import E3C_REFERENCE_ROWS  # noqa: E402

E3C = ROOT / "artifacts" / "e3c"
RHO2 = 1.0                      # detection threshold on whitened information


def endpoints(ages: np.ndarray, mask: np.ndarray, anchor: float) -> dict:
    """Every archived depth statistic, rebuilt from a boolean mask."""
    idx = np.flatnonzero(mask)
    if idx.size == 0:
        return {"oldest": -1.0, "shallowest": -1.0, "n_detectable": 0,
                "n_runs": 0, "longest_run_M": 0.0, "anchor_span_M": 0.0,
                "contiguous": False,
                "mask": "".join("1" if m else "0" for m in mask)}
    runs, start = [], idx[0]
    for a, b in zip(idx[:-1], idx[1:]):
        if b != a + 1:
            runs.append((start, a))
            start = b
    runs.append((start, idx[-1]))
    step = float(ages[1] - ages[0]) if ages.size > 1 else 0.0
    longest = max((ages[j] - ages[i] + step) for i, j in runs)
    anchor_i = int(np.argmin(np.abs(ages - anchor)))
    span = 0.0
    for i, j in runs:
        if i <= anchor_i <= j:
            span = float(ages[j] - ages[anchor_i] + step)
    return {"oldest": float(ages[idx[-1]]), "shallowest": float(ages[idx[0]]),
            "n_detectable": int(idx.size), "n_runs": len(runs),
            "longest_run_M": float(longest), "anchor_span_M": float(span),
            "contiguous": len(runs) == 1,
            "mask": "".join("1" if m else "0" for m in mask)}


def j_old(ages: np.ndarray, info: np.ndarray, a_lo: float) -> float:
    """Integral of log(1 + I(a)) over the old band, recomputed not scaled."""
    sel = ages > a_lo
    if sel.sum() < 2:
        return 0.0
    return float(np.trapz(np.log1p(info[sel]), ages[sel]))


def main(run_dir: Path) -> int:
    files = sorted(E3C.glob("*.json"))
    noise_rows, delta_rows, crossings = [], [], []
    selfcheck_fail, changed = [], []

    for f in files:
        d = json.loads(f.read_text())
        g = d["geometry"]
        m_current = int(d["rays_per_order"]) * len(d["observation_times"]) \
            if "observation_times" in d else int(d["rays_per_order"]) * 8
        F = E3C_REFERENCE_ROWS / m_current
        ages = np.asarray(d["ages"], float)
        anchor = float(d["a0_999_M"])
        noise_rows.append({
            "geometry": g, "rays_per_order": d["rays_per_order"],
            "direct_rows_m": m_current, "m_reference": E3C_REFERENCE_ROWS,
            "s_ref_legacy": d["s_ref"],
            "s_ref_common": d["s_ref"] * math.sqrt(m_current
                                                   / E3C_REFERENCE_ROWS),
            "sigma_factor_common_over_legacy": math.sqrt(
                m_current / E3C_REFERENCE_ROWS),
            "information_factor": F,
            "is_exceptional": F != 1.0,
        })

        per_arm = {}
        for r in d["age_rows"]:
            per_arm.setdefault(r["arm"], []).append(
                (r["retarded_age"], r["information_per_snr2"]))
        for arm, pairs in per_arm.items():
            pairs.sort()
            a = np.array([p[0] for p in pairs])
            i_per = np.array([p[1] for p in pairs])
            for row in d["depth_rows"]:
                if row["arm"] != arm:
                    continue
                snr = float(row["snr0"])
                old_mask = np.array([c == "1" for c in
                                     row["age_threshold_mask"]])
                reb_legacy = endpoints(a, i_per * snr ** 2 >= RHO2, anchor)
                reb_common = endpoints(a, F * i_per * snr ** 2 >= RHO2, anchor)
                if reb_legacy["mask"] != row["age_threshold_mask"]:
                    selfcheck_fail.append(
                        {"geometry": g, "arm": arm, "snr0": snr,
                         "archived": row["age_threshold_mask"],
                         "rebuilt": reb_legacy["mask"]})
                n_flip = int(np.sum(
                    np.array([c == "1" for c in reb_legacy["mask"]])
                    != np.array([c == "1" for c in reb_common["mask"]])))
                moved = (reb_legacy["oldest"] != reb_common["oldest"]
                         or reb_legacy["longest_run_M"]
                         != reb_common["longest_run_M"]
                         or reb_legacy["anchor_span_M"]
                         != reb_common["anchor_span_M"]
                         or n_flip > 0)
                # the smallest information margin, in units of the threshold
                margin = float(np.min(np.abs(i_per * snr ** 2 - RHO2))
                               / RHO2) if i_per.size else float("nan")
                delta_rows.append({
                    "geometry": g, "arm": arm, "snr0": snr,
                    "information_factor": F,
                    "oldest_legacy": reb_legacy["oldest"],
                    "oldest_common": reb_common["oldest"],
                    "longest_run_legacy": reb_legacy["longest_run_M"],
                    "longest_run_common": reb_common["longest_run_M"],
                    "anchor_span_legacy": reb_legacy["anchor_span_M"],
                    "anchor_span_common": reb_common["anchor_span_M"],
                    "n_detectable_legacy": reb_legacy["n_detectable"],
                    "n_detectable_common": reb_common["n_detectable"],
                    "n_mask_bits_flipped": n_flip,
                    "smallest_threshold_margin_relative": margin,
                    "j_old_legacy": j_old(a, i_per * snr ** 2, anchor),
                    "j_old_common": j_old(a, F * i_per * snr ** 2, anchor),
                    "endpoint_moved": moved,
                    "selfcheck_mask_reproduced":
                        reb_legacy["mask"] == row["age_threshold_mask"],
                })
                if n_flip:
                    crossings.append({
                        "geometry": g, "arm": arm, "snr0": snr,
                        "n_bits": n_flip,
                        "ages_crossed": [float(x) for x in a[
                            np.array([c == "1" for c in reb_legacy["mask"]])
                            != np.array([c == "1" for c in
                                         reb_common["mask"]])]],
                    })
                if moved:
                    changed.append((g, arm, snr))

    for name, rows in (("noise_dictionary.csv", noise_rows),
                       ("normalization_endpoint_deltas.csv", delta_rows),
                       ("threshold_crossings.csv", crossings)):
        p = run_dir / name
        if rows:
            with p.open("w", newline="") as fh:
                w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
                w.writeheader()
                w.writerows(rows)
        else:
            p.write_text("no rows\n")
        print(f"wrote {p.relative_to(ROOT)}  ({len(rows)} rows)")

    n_self = sum(1 for r in delta_rows if r["selfcheck_mask_reproduced"])
    print(f"  self-check: {n_self}/{len(delta_rows)} archived masks "
          f"reproduced bit for bit from the stored curves")
    if selfcheck_fail:
        print(f"  SELF-CHECK FAILURES: {len(selfcheck_fail)} "
              f"(first: {selfcheck_fail[0]})")
    print(f"  endpoints moved under the common count: {len(changed)}")
    for c in changed[:10]:
        print(f"    {c}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main((ROOT / sys.argv[1]).resolve()))
