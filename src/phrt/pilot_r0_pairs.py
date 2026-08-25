"""Null pairs, incremental-history pairs, paired bootstrap, and artifact writing."""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

import numpy as np
from scipy import stats

from phrt.inverse.ridge import ridge_from_statistic
from phrt.governance import r0_provenance
from phrt.io.manifests import RunManifest, make_run_id
from phrt.io.tables import write_table
from phrt.sources.near_null import (amplitude_for_target,
                                    direction_for_separation,
                                    realized_separation)

ROOT = Path(__file__).resolve().parents[2]
ARMS = ("DIRECT_PHYSICAL", "RESOLVED_PHYSICAL", "UNRESOLVED_IMAGE", "TOTAL_FLUX")


def bayes_bound(delta: float) -> float:
    """Equal-prior Bayes accuracy for two Gaussians separated by delta."""
    return float(stats.norm.cdf(delta / 2.0))


def pair_experiment(op, u, alpha, rng, n_trials: int) -> dict:
    """Label a coupled pair from one noisy observation each, by the likelihood
    ratio in the whitened data space.

    The optimal rule for a known pair is the projection of the data onto
    A(x_+ - x_-); implementing anything else here would understate the bound and
    make a reconstructor look better than it is by comparison.
    """
    dx = 2.0 * alpha * u
    delta = realized_separation(op, dx)
    if delta <= 0:
        return {"realized_delta": 0.0, "accuracy": 0.5, "n_trials": n_trials}
    # sufficient statistic for the two-point problem, in reduced coordinates
    g_dx = op.forward_statistic(dx)
    correct = 0
    for _ in range(n_trials):
        for sign in (+1.0, -1.0):
            xi = op.noise_statistic(rng, 1)[0]
            b = sign * op.forward_statistic(alpha * u) + xi
            # decide by the sign of <b, dx> in the metric induced by G^-1 on the
            # row space; equivalently the whitened projection
            stat = float(b @ dx)
            correct += int(np.sign(stat) == np.sign(sign))
    return {"realized_delta": float(delta),
            "accuracy": correct / (2.0 * n_trials), "n_trials": n_trials}


def pairs_and_artifacts(P: dict) -> int:
    t0 = P["t0"]
    fz, reg = P["freeze"], P["reg"]
    red, master, streams = P["red"], P["master"], P["streams"]
    fh = P["freeze_hash"]
    out = P["out"]
    targets = fz["null_pairs"]["targets"]
    n_pairs = max(4, int(round(P["counts"]["null_pairs_per_target"] * P["scale"])))

    # ---- null pairs --------------------------------------------------------
    null_rows = []
    for arm in ARMS:
        op = red[arm]
        # ARMS.index, not hash(arm): Python salts string hashes per process,
        # so hash() here would silently break the bitwise replay R0_G9 requires.
        rng = np.random.default_rng([master, streams["null_pairs"],
                                     ARMS.index(arm)])
        for target in targets:
            for j in range(n_pairs):
                u = direction_for_separation(op, rng, "generic")
                alpha = amplitude_for_target(op, u, float(target))
                if not np.isfinite(alpha):
                    null_rows.append({
                        "arm": arm, "target_delta": float(target), "pair": j,
                        "disposition": "NOT_APPLICABLE",
                        "reason": "direction is in the operator's null space; "
                                  "no amplitude realises the target",
                        "realized_delta": 0.0, "bayes_accuracy": 0.5,
                        "observed_accuracy": float("nan"),
                        "exceeds_bayes": False, "freeze_sha256": fh})
                    continue
                res = pair_experiment(op, u, alpha, rng, 256)
                pb = bayes_bound(res["realized_delta"])
                # Monte-Carlo tolerance at 2 sigma for a binomial of this size
                n = 2 * res["n_trials"]
                mc = 2.0 * np.sqrt(max(pb * (1 - pb), 1e-12) / n)
                null_rows.append({
                    "arm": arm, "target_delta": float(target), "pair": j,
                    "realized_delta": res["realized_delta"],
                    "relative_delta_error": abs(res["realized_delta"] - target)
                                            / max(target, 1e-12),
                    "bayes_accuracy": pb,
                    "observed_accuracy": res["accuracy"],
                    "monte_carlo_tolerance": float(mc),
                    "exceeds_bayes": bool(res["accuracy"] > pb + mc),
                    "disposition": "SUPPORTED", "reason": "",
                    "admissible_amplitude_note":
                        "signed perturbation about a positive baseline; the "
                        "amplitude that keeps the rendered movie non-negative is "
                        "recorded in the source bank manifest",
                    "freeze_sha256": fh})
    # Multiplicity matters: with several hundred pairs each tested at a two-sigma
    # one-sided tolerance, a couple of exceedances are expected under a perfectly
    # calibrated null. Declaring a defect on a single excursion would be a false
    # alarm, so the count is compared against its binomial expectation.
    tested = [r for r in null_rows if r["disposition"] == "SUPPORTED"]
    leak = [r for r in tested if r.get("exceeds_bayes")]
    p_one_sided = float(stats.norm.sf(2.0))
    n_tested = len(tested)
    expected = n_tested * p_one_sided
    p_excess = float(stats.binom.sf(len(leak) - 1, n_tested, p_one_sided)) \
        if len(leak) else 1.0
    defect = bool(p_excess < 0.01)
    print(f"null pairs: {n_tested} tested, {len(leak)} above the Bayes bound "
          f"(expected {expected:.1f} under a calibrated null, "
          f"binomial p = {p_excess:.3f})")
    if defect:
        print("STOP: NULL_PAIR_CALIBRATION_DEFECT")
    null_summary = {"n_tested": n_tested, "n_exceeding": len(leak),
                    "expected_exceedances": expected,
                    "binomial_p_excess": p_excess,
                    "defect": defect,
                    "rule": "a defect requires an excess beyond binomial "
                            "multiplicity, not a single two-sigma excursion"}

    # ---- incremental-history pairs -----------------------------------------
    # Directions chosen weak under the direct arm; the question is whether the
    # resolved arm makes them discriminable.
    inc_rows = []
    rng = np.random.default_rng([master, streams["null_pairs"], 31337])
    direct, resolved = red["DIRECT_PHYSICAL"], red["RESOLVED_PHYSICAL"]
    for j in range(max(8, n_pairs)):
        u = direction_for_separation(resolved, rng, "incremental_history",
                                     weak_op=direct)
        d_dir = realized_separation(direct, u)
        d_res = realized_separation(resolved, u)
        inc_rows.append({
            "pair": j,
            "separation_per_unit_direct": float(d_dir),
            "separation_per_unit_resolved": float(d_res),
            "resolved_over_direct": float(d_res / max(d_dir, 1e-300)),
            "bayes_direct_at_unit": bayes_bound(d_dir),
            "bayes_resolved_at_unit": bayes_bound(d_res),
            "construction": "direction inside the direct arm's least-determined "
                            "half-spectrum, maximising the resolved arm's response",
            "freeze_sha256": fh})
    ratios = [r["resolved_over_direct"] for r in inc_rows]
    print(f"incremental-history pairs: median resolved/direct separation ratio "
          f"{np.median(ratios):.3f}")

    # ---- paired arm bootstrap ---------------------------------------------
    import pandas as pd
    depth = pd.DataFrame(out["depth_rows"])
    prim = depth[(depth.primary) & (depth.regime == "validation_in_class")]
    boot_rows = []
    bs = fz["paired_comparison"]["bootstrap"]
    for est in sorted(prim.estimator.unique()):
        for snr in sorted(prim.snr0.unique()):
            sub = prim[(prim.estimator == est) & (prim.snr0 == snr)]
            got = {r.arm: (r.L_stable_anchor, r.L_stable_anchor_structure)
                   for r in sub.itertuples()}
            if "DIRECT_PHYSICAL" not in got:
                continue
            for other in ("RESOLVED_PHYSICAL", "UNRESOLVED_IMAGE", "TOTAL_FLUX"):
                if other not in got:
                    continue
                boot_rows.append({
                    "estimator": est, "snr0": float(snr),
                    "contrast": f"{other} - DIRECT_PHYSICAL",
                    "delta_L_stable_anchor": float(got[other][0]
                                                   - got["DIRECT_PHYSICAL"][0]),
                    "L_stable_anchor_reference": float(got["DIRECT_PHYSICAL"][0]),
                    "L_stable_anchor_arm": float(got[other][0]),
                    "delta_L_stable_anchor_structure":
                        float(got[other][1] - got["DIRECT_PHYSICAL"][1]),
                    "L_stable_anchor_structure_reference":
                        float(got["DIRECT_PHYSICAL"][1]),
                    "L_stable_anchor_structure_arm": float(got[other][1]),
                    "bootstrap_unit": bs["unit"],
                    "bootstrap_n": int(bs["n_resamples"]),
                    "note": "L_stable_anchor is a population quantile over "
                            "truths, so a per-truth bootstrap interval is "
                            "reported on the age-error surface rather than on "
                            "this scalar",
                    "freeze_sha256": fh})

    # ---- artifacts ---------------------------------------------------------
    run_id = make_run_id("R0B", reg.sha256)
    man = RunManifest(run_id=run_id, experiment_id="R0B_CANARY_RECONSTRUCTION_PILOT",
                      seeds={"master": master, "streams": streams},
                      extra={"freeze_sha256": fh, "scale": P["scale"],
                             "n_eval_points": P["n_eval"],
                             **r0_provenance()})
    man.add_input(ROOT / "artifacts" / "configs"
                  / "R0_CANARY_RECONSTRUCTION_PILOT_FREEZE.json")
    for name, rows in (("r0_pilot_age_errors", out["age_rows"]),
                       ("r0_pilot_stable_depth", out["depth_rows"]),
                       ("r0_pilot_estimator_selection", out["sel_rows"]),
                       ("r0_pilot_data_weak_errors", out["dw_rows"]),
                       ("r0_pilot_coverage", out["cov_rows"]),
                       ("r0_pilot_null_pairs", null_rows),
                       ("r0_pilot_incremental_pairs", inc_rows),
                       ("r0_pilot_runtime", out["rt_rows"]),
                       ("r0_pilot_arm_contrasts", boot_rows),
                       ("r0_pilot_representation_floor", out["floor_rows"]),
                       ("r0_pilot_representation_floor_depth",
                        out["floor_depth"])):
        man.add_output(write_table(rows, name))

    # source bank and split manifests
    mans = ROOT / "artifacts" / "manifests"
    mans.mkdir(parents=True, exist_ok=True)
    bank_doc = {"schema": "phrt-r0-source-bank/1", "freeze_sha256": fh,
                "baseline_intensity": 1.0,
                "positivity": "every physical family renders a strictly positive "
                              "intensity; signed null perturbations sit on the "
                              "positive baseline",
                "off_grid": P["og_rows"],
                "families": {}}
    for (split, fam), movies in P["bank"].items():
        bank_doc["families"].setdefault(fam, {})[split] = {
            "n": len(movies),
            "content_hash_sample": [m.content_hash for m in movies[:3]],
            "off_grid": movies[0].off_grid if movies else None}
    (mans / "r0_source_bank_manifest.json").write_text(
        json.dumps(bank_doc, indent=2) + "\n")

    (mans / "r0_null_pair_summary.json").write_text(
        json.dumps({"schema": "phrt-r0-null-summary/1", "freeze_sha256": fh,
                    **null_summary}, indent=2) + "\n")

    (mans / "r0_split_hash_manifest.json").write_text(json.dumps(
        {"schema": "phrt-r0-splits/1", "freeze_sha256": fh, **P["disj"]},
        indent=2) + "\n")

    fut = {fam: sorted(m.content_hash for m in mv)
           for fam, mv in P["future"].items()}
    commit_hash = hashlib.sha256(
        json.dumps(fut, sort_keys=True).encode()).hexdigest()
    (mans / "r0_future_test_hash_commitment.json").write_text(json.dumps(
        {"schema": "phrt-r0-future-test-commitment/1", "freeze_sha256": fh,
         "status": "GENERATED_AND_HASHED_NOT_RENDERED_NOT_SCORED",
         "commitment_sha256": commit_hash,
         "n_per_family": {k: len(v) for k, v in fut.items()},
         "content_hashes": fut}, indent=2) + "\n")

    mp = man.write(reg.path, reg.sha256, runtime_seconds=time.time() - t0)
    print(f"\nmanifest {mp}")
    print(f"total {time.time() - t0:.0f}s")
    return 5 if defect else 0
