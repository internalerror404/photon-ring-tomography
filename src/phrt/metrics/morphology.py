"""A morphology error that scores every state by what that state supports.

HMT-2 stage 1, items 15 and 16. The endpoint HMT-1 used asked every state for a
peak position. Where the field held two features it answered about one of them;
where it held a blend it answered about a maximum that no feature occupied. Both
answers were numbers, and neither was a measurement.

Here the state's reconciled label decides the measure:

* resolved states, single or multiple, are scored by the set-valued unbalanced
  assignment cost, so a feature gained or lost is an error rather than a
  silently different question;
* blended states are scored on centroid, size and mode content -- the things a
  one-peak field determines -- and are never asked for two trajectories;
* ambiguous states, where the analysis grid cannot settle the multiplicity, get
  the blended measure, because scoring them as though the count were known
  would be reporting the classifier's coin flip as a result;
* dead states are scored on amplitude alone, having no position to get right.

Every measure is normalised by its own worst case, so states of different kinds
combine into one number without one kind dominating through a larger natural
scale. Nothing is excluded: an endpoint that drops the states a method finds
hard is an endpoint that measures the easy ones.
"""
from __future__ import annotations

import numpy as np

from phrt.metrics.feature_sets import assignment, blended_descriptors

EPS = 1e-300
ASSIGNMENT_STATES = ("SINGLE_RESOLVED", "MULTI_RESOLVED")
BLENDED_STATES = ("BLENDED", "AMBIGUOUS")


def _rel(a: float, b: float) -> float:
    """Symmetric relative discrepancy in [0, 1]."""
    a, b = float(a), float(b)
    d = abs(a) + abs(b)
    return abs(a - b) / d if d > EPS else 0.0


def assignment_error(truth_feats: list, recon_feats: list, met: dict) -> dict:
    """Unbalanced assignment cost, normalised by its own worst case.

    The worst case is every feature on both sides unmatched, which is what a
    reconstruction that finds nothing where the truth has features, or features
    where the truth has nothing, actually costs.
    """
    res = assignment(truth_feats, recon_feats, met)
    worst = met["unmatched_cost"] * max(len(truth_feats), len(recon_feats), 1)
    return {"error": float(min(res["unbalanced_cost"] / worst, 1.0)),
            "matched_cells": res["mean_matched_cells"],
            "cardinality_error": res["cardinality_error"],
            "n_truth": len(truth_feats), "n_recon": len(recon_feats)}


def blended_error(truth_map: np.ndarray, recon_map: np.ndarray,
                  r_axis: np.ndarray, phi_axis: np.ndarray,
                  met: dict) -> dict:
    """Centroid, size and mode content: what a one-peak field determines."""
    a = blended_descriptors(truth_map, r_axis, phi_axis)
    b = blended_descriptors(recon_map, r_axis, phi_axis)
    if not np.isfinite(a["centroid_r"]) or not np.isfinite(b["centroid_r"]):
        return {"error": 1.0, "centroid_cells": float("nan"),
                "size_error": 1.0, "mode_error": 1.0, "contrast_error": 1.0}
    dr = abs(np.log(max(a["centroid_r"], EPS) / max(b["centroid_r"], EPS))) \
        / met["d_logr"]
    dp = abs((a["centroid_phi"] - b["centroid_phi"] + np.pi) % (2 * np.pi)
             - np.pi) / met["d_phi"]
    centroid = float(np.hypot(dr, dp))
    e_pos = min(centroid / met["unmatched_cost"], 1.0)
    e_size = float(np.mean([_rel(np.sqrt(max(a[k], 0.0)),
                                 np.sqrt(max(b[k], 0.0)))
                            for k in ("second_moment_rr", "second_moment_pp")]))
    e_mode = float(np.mean([_rel(a["a_m1"], b["a_m1"]),
                            _rel(a["a_m2"], b["a_m2"])]))
    e_con = _rel(a["total_contrast"], b["total_contrast"])
    return {"error": float(np.mean([e_pos, e_size, e_mode, e_con])),
            "centroid_cells": centroid, "size_error": e_size,
            "mode_error": e_mode, "contrast_error": e_con}


def dead_error(truth_map: np.ndarray, recon_map: np.ndarray) -> dict:
    """No position is defined; amplitude is the whole of it."""
    e = _rel(float(np.abs(truth_map).max()), float(np.abs(recon_map).max()))
    return {"error": float(e), "amplitude_error": float(e)}


def state_error(label: str, truth_map: np.ndarray, recon_map: np.ndarray,
                truth_feats: list, recon_feats: list, r_axis: np.ndarray,
                phi_axis: np.ndarray, met: dict) -> dict:
    """One error for one (truth, age), by the measure that state supports."""
    if label == "DEAD":
        out = dead_error(truth_map, recon_map)
        kind = "amplitude"
    elif label in BLENDED_STATES:
        out = blended_error(truth_map, recon_map, r_axis, phi_axis, met)
        kind = "blended"
    else:
        out = assignment_error(truth_feats, recon_feats, met)
        kind = "assignment"
    return {"state": label, "measure": kind, **out}


def aggregate_all_states(rows: list) -> dict:
    """The primary endpoint: every state, none dropped.

    Reported as the mean over states and also per measure kind, because a
    single mean can improve while the states a method actually struggles with
    get worse, and the split makes that visible instead of hiding it.
    """
    if not rows:
        return {"all_state_error": float("nan"), "n_states": 0}
    e = np.array([r["error"] for r in rows], float)
    out = {"all_state_error": float(np.mean(e)), "n_states": int(e.size)}
    for kind in ("assignment", "blended", "amplitude"):
        sub = np.array([r["error"] for r in rows if r["measure"] == kind], float)
        out[f"{kind}_error"] = float(np.mean(sub)) if sub.size else float("nan")
        out[f"n_{kind}"] = int(sub.size)
    return out
