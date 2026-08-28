#!/usr/bin/env python3
"""HMT1_VALIDATION_RECORD_AMENDMENT_015. Record only; recomputes nothing.

Items 3, 4 and 5 of REVIEWER_RULING_HMT1_VALIDATION_015: record the five
validation findings separately, preserve the two superseded runs under the
three names the ruling gives them, and name runs 3 and 4 the canonical
deterministic pair.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from phrt.numerics import pin

pin()

from phrt.attestation import attest  # noqa: E402
from phrt.config import sha256_file  # noqa: E402

OUT = ROOT / "artifacts" / "configs" / "HMT1_VALIDATION_RECORD_AMENDMENT_015.json"
FZ = ROOT / "artifacts" / "configs" / "HMT1_VALIDATION_FREEZE_V0.json"
G = ROOT / "artifacts" / "gates" / "hmt1_gates.json"

RUNS = {
    "smoke_1": "HMT1_20260827T212947Z_2ba66f02",
    "smoke_2": "HMT1_20260827T213738Z_2ba66f02",
    "run_1": "HMT1_20260827T214203Z_2ba66f02",
    "run_2": "HMT1_20260827T220408Z_2ba66f02",
    "run_3": "HMT1_20260827T222531Z_2ba66f02",
    "run_4": "HMT1_20260827T224512Z_2ba66f02",
}


def main() -> int:
    g = json.loads(G.read_text())
    doc = {
        "schema": "phrt-record-amendment/1",
        "id": "HMT1_VALIDATION_RECORD_AMENDMENT_015",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "ruling": "REVIEWER_RULING_HMT1_VALIDATION_015",
        "kind": "RECORD_ONLY",
        "recomputation": "none",
        "accepted_commit": "814f78ab03ec4a3e6b1360ae3cb73819543ceceb",
        "accepted_disposition": "HMT1_MATERIAL_ERROR_REDUCTION_NO_STABLE_INTERVAL",
        "reported_run": RUNS["run_4"],

        "dispositions": {
            "HMT1_VALIDATION_FEATURE_ERROR_MATERIAL_PASS": {
                "finding": "the resolved arm reduces old-band feature error "
                           "against the direct image by a median 0.156 to "
                           "0.251 depending on regime and estimator, with "
                           "paired truth-cluster bootstrap intervals "
                           "excluding zero, on both classical estimators, in "
                           "all three background regimes",
                "family_agreement": "met under the primary fraction reading "
                                    "of 5 of 6 in every regime: 6 of 6 under "
                                    "oracle_known and joint_inversion, 5 of 6 "
                                    "under estimated_from_data",
                "reading": "materiality is met. It is one half of the "
                           "registered pass criterion and does not on its own "
                           "constitute a pass",
            },
            "HMT1_VALIDATION_ESTIMATED_BACKGROUND_PASS": {
                "finding": "materiality survives estimated_from_data, where "
                           "the axisymmetric background is fit through the "
                           "arm's own operator against the arm's own data "
                           "rather than supplied",
                "measured": "median relative background error 0.0154, worst "
                            "0.0565 over the bank",
                "reading": "the result is not background-assisted. This is "
                           "the regime the freeze names as the one a "
                           "paper-grade result must survive, and it is why "
                           "the disposition is not "
                           "HMT1_BACKGROUND_ASSISTED_ONLY",
            },
            "HMT1_VALIDATION_UNRESOLVED_NOT_MATERIAL": {
                "finding": "the unresolved-image arm improves on the direct "
                           "image but does not reach the registered "
                           "materiality bar in any regime",
                "reading": "the benefit is attributable to resolving the "
                           "photon-ring orders and not to the extra photons "
                           "an unresolved second image also carries",
            },
            "HMT1_VALIDATION_TOTAL_FLUX_NEGATIVE_CONTROL": {
                "finding": "the total-flux arm is negative in every regime "
                           "and on both estimators, meaning worse than the "
                           "direct image",
                "reading": "the control behaves as a control. A single flux "
                           "number carries no azimuthal information, so an "
                           "endpoint that rewarded it would have been "
                           "measuring something other than feature recovery",
            },
            "HMT1_VALIDATION_STABLE_INTERVAL_NEGATIVE_RESULT": {
                "finding": "L_stable_features = 0 M for every arm in every "
                           "regime at epsilon 0.25 and the 0.95 quantile",
                "direction": "the recovered history is not leaving the "
                             "tolerance early, it is never inside it. Median "
                             "old-band feature error is 0.545 resolved "
                             "against 0.675 direct, both above the 0.25 "
                             "tolerance. Only 7.8% of resolved-arm "
                             "realizations are inside the tolerance even at "
                             "age zero and the furthest any reaches is 4 M",
                "reading": "a reportable negative result on the co-primary "
                           "endpoint. A material reduction in a time-averaged "
                           "error is not the same claim as a history that "
                           "holds together over a stretch of the past, and "
                           "this validation separates them",
            },
        },

        "superseded": {
            "HMT1_SUPERSEDED_GATE_COVERAGE_DEFECT": {
                "run_id": RUNS["smoke_1"],
                "provenance_note": "caught on the first end-to-end execution, "
                                   "which was a single-family single-regime "
                                   "smoke run rather than a full run. "
                                   "Recorded here under the ruling's name for "
                                   "it, with the actual provenance stated "
                                   "rather than assimilated to full run 1",
                "failed_gates": ["HMT1_G13_declared_gate_coverage"],
                "defect": "HMT1_G10b was registered with its reading written "
                          "into the threshold field as prose and was "
                          "therefore declared but never emitted, and "
                          "HMT1_G4b was emitted without being declared, "
                          "behind a hard-coded exemption in the coverage "
                          "computation",
                "repair": "G10b implemented rather than withdrawn, because "
                          "G10 asks only that extraction be repeatable and an "
                          "extractor reading the wrong position reads it "
                          "repeatably. G4b declared, and the exemption "
                          "removed so the coverage gate compares the declared "
                          "and emitted sets with no allowance on either side",
                "status": "superseded and not scored",
            },
            "HMT1_SUPERSEDED_FAMILY_METRIC_DIVIDE_BY_NEAR_ZERO": {
                "run_ids": [RUNS["run_1"], RUNS["run_2"]],
                "failed_gates": {
                    RUNS["run_1"]: ["HMT1_G12_no_maximal_regularization_collapse",
                                    "HMT1_G10b_truth_extraction_recovers_generative_parameters"],
                    RUNS["run_2"]: ["HMT1_G12_no_maximal_regularization_collapse"],
                },
                "defect": "the freeze defines the aggregate over 'the "
                          "family's declared normalised parameter errors' and "
                          "declares a different parameter list per family. "
                          "The scorer used one global five-component list for "
                          "all six families, so m2_structural_mode was scored "
                          "on an m = 1 mode amplitude that is zero by "
                          "construction, measured at 1.6e-17. Dividing by "
                          "'max over ages of |a_m1|' divided by round-off and "
                          "that single term reached 1e16",
                "consequence": "an estimator can only shrink such a term by "
                               "driving its reconstruction to zero, so 22 of "
                               "24 arm-estimator cells pinned their selection "
                               "at the most-regularized end of the grid and "
                               "every arm collapsed onto the same near-null "
                               "estimator. The selection rule was not "
                               "degenerate; it was correctly minimising an "
                               "error dominated by a division by zero",
                "how_it_was_found": "recording the whole selection sweep "
                                    "rather than only its argmin. A selection "
                                    "pinned at a grid endpoint and one with a "
                                    "genuine interior optimum produce the "
                                    "same single number, and the sweep showed "
                                    "errors of order 1e12 to 1e17 where a "
                                    "normalised error cannot exceed order one",
                "second_defect_same_runs": "the stop token was selected from "
                                           "the science before any gate had "
                                           "been emitted, so run 1 failed two "
                                           "gates and still reported "
                                           "HMT1_NO_MATERIAL_EFFECT. A null "
                                           "result is exactly what a broken "
                                           "run looks like from the outside, "
                                           "and that one would have reported "
                                           "a null produced by a "
                                           "divide-by-zero. A failed gate now "
                                           "forces HMT1_IMPLEMENTATION_DEFECT",
                "third_defect_run_1": "HMT1_G10b's two-hotspot label ordered "
                                      "the two spots by drawn amplitude. Two "
                                      "spots 0.08 radial cells apart at "
                                      "opposite azimuths with peak heights "
                                      "differing by 1.5% are not ordered "
                                      "reliably by any scalar once the field "
                                      "is sampled onto the evaluation grid, "
                                      "because the broader spot survives "
                                      "sampling better. The label now carries "
                                      "both centres and the gate asks whether "
                                      "the extracted peak is at a feature "
                                      "that is really there",
                "status": "superseded and not scored",
            },
            "HMT1_SUPERSEDED_FALSE_ORACLE_BACKGROUND": {
                "run_ids": [RUNS["run_1"], RUNS["run_2"]],
                "defect": "the freeze says oracle_known supplies b exactly, "
                          "but every regime was routed through the same "
                          "least-squares axisymmetric design fit, which "
                          "cannot represent the background exactly. That left "
                          "a residual of 0.69 against a signal of 7.58",
                "consequence": "a 9% background error inside the regime whose "
                               "entire purpose is to have none, which would "
                               "have been read as the operator's limit rather "
                               "than the fit's",
                "repair": "the oracle regime now removes the operator image "
                          "of the true background and nothing else. Its "
                          "measured background error is exactly zero in the "
                          "canonical runs",
                "status": "superseded and not scored",
            },
        },

        "canonical_deterministic_pair": {
            "runs": [RUNS["run_3"], RUNS["run_4"]],
            "reported": RUNS["run_4"],
            "reproduction": "endpoint tables bitwise identical; gate sets "
                            "differ only in HMT1_G14_resource_limits, which "
                            "measures wall-clock seconds and therefore cannot "
                            "be identical (882 s against 890 s)",
            "environment": "the pinned single-threaded numerical environment "
                           "established by R1L_DETERMINISTIC_NUMERICS_"
                           "AMENDMENT_009",
            "gates": g["summary"],
        },

        "scope_unchanged": {
            "geometry": "one geometry, one spin, one inclination",
            "banks": "six declared analytic families, in the reconstruction "
                     "class by construction up to the m = 0 projection",
            "bound": "an upper bound on what this operator can do for this "
                     "class, not a statement about real source histories",
            "r1l": "the R1L stop stands and its sealed commitments remain "
                   "unscored",
        },
        "sealed_held_out_main_authorized": True,
        "authorized_by": "REVIEWER_RULING_HMT1_VALIDATION_015 items 6 to 10",
        "not_authorized": ["order leakage", "geometry mismatch", "VLBI",
                           "machine learning",
                           "a new pixel-movie reconstruction campaign"],
        "validation_freeze_sha256": sha256_file(FZ),
        "attestation": attest([FZ, G]),
    }
    OUT.write_text(json.dumps(doc, indent=2, default=str) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}\n  sha256 {sha256_file(OUT)}")
    print(f"  {len(doc['dispositions'])} dispositions, "
          f"{len(doc['superseded'])} superseded records")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
