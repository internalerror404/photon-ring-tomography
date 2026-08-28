#!/usr/bin/env python3
"""HMT1_SEALED_MAIN_BANK_V1_RETIREMENT_016. Deviation record.

Written before the replacement bank is drawn, so the record cannot have been
shaped by what the replacement produces.
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

FZ = ROOT / "artifacts" / "configs" / "HMT1_SEALED_HELD_OUT_MAIN_FREEZE_V1.json"
OUT = ROOT / "artifacts" / "configs" / "HMT1_SEALED_MAIN_BANK_V1_RETIREMENT_016.json"


def main() -> int:
    doc = {
        "schema": "phrt-deviation-record/1",
        "id": "HMT1_SEALED_MAIN_BANK_V1_RETIREMENT_016",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "ruling": "REVIEWER_RULING_HMT1_VALIDATION_015",
        "kind": "DEVIATION_AND_REMEDY",
        "written_before_replacement_bank_drawn": True,

        "what_happened": {
            "event": "stage B of the sealed main was smoke tested on the "
                     "sealed held-out bank, restricted to one family and one "
                     "regime, to check that the runner executed at all",
            "why_it_matters": "that is an operator evaluation on held-out "
                              "truths. The ruling's ordering exists so that "
                              "no held-out truth is scored before the run "
                              "that reports it, and a smoke test is a run",
            "what_was_seen": "the gate list, and one verdict line for "
                             "oracle_known restricted to "
                             "circular_hotspot_trajectory: materiality False, "
                             "families_improved 0 of a single-family subset. "
                             "No endpoint table, no per-family reduction, no "
                             "interval, and nothing from the claim-bearing "
                             "regime",
            "my_error": "the smoke test should have run against a scratch "
                        "bank drawn under a throwaway seed. Nothing about "
                        "checking that a runner starts requires the sealed "
                        "truths",
        },

        "remedy": {
            "action": "the v1 held-out bank, drawn under bank_seed 20260915, "
                      "is retired and will not be evaluated again. The freeze "
                      "is revised to bank_seed 20260917 and stage A is re-run "
                      "to draw and commit a replacement",
            "rationale": "redrawing costs five seconds. Arguing that the peek "
                         "was too small to matter costs the seal, and the "
                         "seal is the only thing that makes a held-out result "
                         "worth more than the validation it follows",
            "retired_bank_hashes": "artifacts/provenance/"
                                   "HMT1_MAIN_BANK_HASHES.json at commit "
                                   "1734dab, preserved in history and "
                                   "superseded in the working tree",
            "residual_exposure": "the peek informed no sealed quantity. The "
                                 "hyperparameters, estimators, feature lists, "
                                 "denominators, tolerances and family set are "
                                 "fixed by the freeze and item 8 forbids "
                                 "changing them, so there was nothing the "
                                 "peek could have been used to tune even if "
                                 "it had shown more",
        },

        "second_defect_found_by_the_smoke_run": {
            "gate": "HMT1M_G15",
            "as_registered": "required the noiseless control to score a lower "
                             "endpoint error than the noisy draws",
            "falsified_by": "with the sealed hyperparameters the feature "
                            "error is bias dominated rather than noise "
                            "dominated. The noise norm exceeds the signal "
                            "norm, 19.0 against 7.58 in the projected "
                            "coefficients, but the regularization removes "
                            "most of it, so removing the noise entirely "
                            "changes the median endpoint by a few percent and "
                            "in some cells raises it -- a bounded "
                            "argmax-based metric can be helped slightly by "
                            "dither",
            "correction": "the gate's purpose was to confirm the noise path "
                          "is live. It now measures that directly, as the "
                          "relative displacement between the noisy and "
                          "noiseless reconstructions, which does not assume a "
                          "direction for the endpoint. The endpoint direction "
                          "is still reported and is not gated, because no "
                          "correct direction for it was established in "
                          "advance",
            "timing": "the correction is made before the replacement bank "
                      "exists, so it is applied to no held-out data",
            "honest_reading": "this is a gate I designed wrongly, caught by "
                              "the run it was meant to guard. Leaving it "
                              "would have reported "
                              "HMT1_MAIN_IMPLEMENTATION_DEFECT for a physical "
                              "fact rather than a defect, which is the same "
                              "failure in the opposite direction",
        },

        "third_defect": {
            "gate": "HMT1M_G2_held_out_commitment_reproduces",
            "defect": "compared only the commitments of the families being "
                      "run, so a family-restricted run could satisfy it by "
                      "checking fewer of them",
            "correction": "always compares all six declared commitments",
        },

        "known_gap_not_repaired": {
            "item": "NONNEGATIVE_CONSTRAINED estimator",
            "status": "declared in the validation freeze as a required "
                      "control, scoped to the primary SNR and the estimated "
                      "background regime, and never implemented in the "
                      "validation",
            "why_not_now": "it has no sealed hyperparameter, because it was "
                           "never selected. Running it in the sealed main "
                           "would require choosing one, and item 8 of the "
                           "ruling forbids selection and retuning. It is "
                           "therefore left unimplemented and reported as an "
                           "open gap rather than smuggled in behind a "
                           "selection the ruling prohibits",
            "needs": "a reviewer ruling",
        },

        "freeze_sha256_after_revision": sha256_file(FZ),
        "attestation": attest([FZ]),
    }
    OUT.write_text(json.dumps(doc, indent=2, default=str) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}\n  sha256 {sha256_file(OUT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
