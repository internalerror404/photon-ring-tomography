#!/usr/bin/env python3
"""R1L_STAGE2R_SCIENTIFIC_DISPOSITION_AMENDMENT_014.

REVIEWER_RULING_R1L_GATE_COMPLETION_014 items 1 to 7. Six dispositions recorded
separately, because they are six different findings and collapsing them into one
token is what made the earlier reports misleading. Nothing is recomputed.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd

from phrt.attestation import attest
from phrt.config import sha256_file

TAB = ROOT / "artifacts" / "tables"
G = ROOT / "artifacts" / "gates" / "r1l_2rb_gates.json"
REPRO = ROOT / "artifacts" / "provenance" / "R1L_2RB_GATE_COMPLETION_REPRODUCTION.json"
CFG = ROOT / "artifacts" / "configs"
OUT = CFG / "R1L_STAGE2R_SCIENTIFIC_DISPOSITION_AMENDMENT_014.json"
PC = "L1056"


def rows(e, scope, snr, arm):
    q = e[(e.source_class == PC) & (e.scope == scope) & (e.snr0 == snr)
          & (e.arm == arm)]
    return {r.estimator: {
        "median_relative_reduction": float(r.median_relative_reduction),
        "median_ci_low": float(r.median_ci_low),
        "cell_balanced_mean": float(r.relative_reduction),
        "mean_ci_low": float(r.ci_low),
        "n_families_improved": int(r.n_families_improved),
        "meets_materiality": bool(r.meets_materiality)} for r in q.itertuples()}


def main() -> int:
    e = pd.read_parquet(TAB / "r1l_2rb_endpoint.parquet")
    d = pd.read_parquet(TAB / "r1l_2rb_delta_spans.parquet")
    g = json.loads(G.read_text())
    rep = json.loads(REPRO.read_text())

    doc = {
        "schema": "phrt-record-amendment/1",
        "id": "R1L_STAGE2R_SCIENTIFIC_DISPOSITION_AMENDMENT_014",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "ruling": "REVIEWER_RULING_R1L_GATE_COMPLETION_014",
        "kind": "RECORD_ONLY",
        "recomputation": "none",
        "accepted_commit": "4cb9895a14cc5e870a77fd3a98a79ee82055c2ef",
        "machine_token_preserved": "R1L_STAGE2R_B_NO_MATERIAL_EFFECT",
        "machine_token_prose": "PREREGISTERED_PHYSICAL_SOURCE_MATERIALITY_NOT_MET",
        "machine_token_is_not": "proof of an exactly zero effect. The physical "
                                "banks show a positive central estimate at the "
                                "reference SNR; what fails is the preregistered "
                                "materiality bar, and the bar is what the token "
                                "reports",
        "sealed_main_authorized": False,

        "dispositions": {
            "R1L_STAGE2R_GATE_COMPLETION_REPRODUCTION_PASS": {
                "finding": "the gate-completed rerun reproduced every "
                           "pre-existing scientific cell bitwise against "
                           "151229d",
                "gates": f"{g['summary']['PASS']} of {len(g['gates'])} PASS, "
                         f"coverage complete",
                "verdict": rep["verdict"],
                "explicitly_not_an_implementation_defect": True,
                "why": "the tables did not move. What moved was which bank "
                       "scope the disposition reads, and that was directed by "
                       "the ruling that required the physical claim to survive "
                       "on the non-negative banks alone",
            },
            "R1L_STAGE2R_PHYSICAL_SOURCE_MATERIALITY_NOT_MET": {
                "class": PC, "snr0": 100.0, "arm": "RESOLVED_PHYSICAL",
                "scope": "physical_banks_only",
                "measured": rows(e, "physical_banks_only", 100.0,
                                 "RESOLVED_PHYSICAL"),
                "why_not_met": "both cell-balanced-mean lower bounds fall below "
                               "the 5 percent floor and both drop to three of "
                               "four families. The per-truth medians, 16.8 and "
                               "17.8 percent, clear the 10 percent bar and "
                               "their own lower bounds clear 5 percent, so the "
                               "failure is on the mean estimand rather than on "
                               "the median",
                "not_a_null_result": "the central estimates are positive on "
                                     "both estimators. This is a bar not "
                                     "cleared, not an effect shown to be zero",
            },
            "R1L_STAGE2R_SIGNED_DIAGNOSTIC_MATERIAL_EFFECT": {
                "bank": "constant_flux_structural",
                "role": "SIGNED_CONSTANT_FLUX_STRUCTURAL_DIAGNOSTIC",
                "measured": rows(e[e.bank == "constant_flux_structural"],
                                 "single_bank", 100.0, "RESOLVED_PHYSICAL"),
                "finding": "the signed diagnostic bank alone shows the largest "
                           "effect of the three, and it was carrying the pooled "
                           "all-banks result that earlier read as material",
                "status": "a linear inverse-problem result. It may not be "
                          "reported as a physical-source claim, because the "
                          "bank is not everywhere a non-negative emissivity "
                          "field",
            },
            "R1L_STAGE2R_HIGH_SNR_PHYSICAL_VALIDATION_PASS": {
                "class": PC, "snr0": 1000.0, "scope": "physical_banks_only",
                "resolved": rows(e, "physical_banks_only", 1000.0,
                                 "RESOLVED_PHYSICAL"),
                "unresolved": rows(e, "physical_banks_only", 1000.0,
                                   "UNRESOLVED_IMAGE"),
                "finding": "on the non-negative physical banks at the secondary "
                           "SNR, the resolved arm meets every materiality "
                           "criterion on both estimators and all four families",
                "unresolved_status": "material on ridge and not on TSVD, so it "
                                     "fails the both-estimators requirement",
                "status": "secondary. The registered point is SNR0 = 100 and a "
                          "result at tenfold higher normalized SNR does not "
                          "substitute for it",
            },
            "R1L_STAGE2R_STABLE_SPAN_NEGATIVE_RESULT": {
                "measured": [{k: (float(v) if isinstance(v, float) else v)
                              for k, v in r._asdict().items()
                              if k in ("arm", "snr0", "noise_semantics",
                                       "L_direct_M", "L_arm_M",
                                       "delta_L_stable_structure_M",
                                       "meets_threshold")}
                             for r in d[d.source_class == PC].itertuples()],
                "finding": "every stable structural span is zero under both "
                           "noise semantics at both SNRs, so delta L is 0 M "
                           "against the 8 M threshold",
                "robustness": "the joint truth-and-noise statistic is the "
                              "stricter of the two and agrees with the averaged "
                              "one, so the negative cannot be an artefact of "
                              "averaging over noise first",
                "is_a_real_negative": "yes. The representation floor is zero, so "
                                      "nothing blocked the criterion except the "
                                      "reconstruction itself",
            },
            "R1L_STAGE2R_SCIENTIFIC_STOP": {
                "finding": "the reconstruction campaign stops here",
                "sealed_main_authorized": False,
                "not_authorized": ["sealed main", "order leakage",
                                   "geometry mismatch", "VLBI", "ML"],
                "no_redesign_within_paper_i": ["source bank", "endpoint",
                                               "estimator", "SNR",
                                               "materiality threshold"],
                "next": "manuscript reframing, shortening and submission "
                        "preparation from the canonical stage-1 and stage-2R "
                        "records",
            },
        },

        "sealed_commitments_preserved_unscored": [
            {"id": "R1L_SEALED_ANALYTIC_STRESS_COMMITMENT_UNSCORED",
             "path": "artifacts/configs/"
                     "R1L_SEALED_ANALYTIC_STRESS_COMMITMENT_UNSCORED.json",
             "sha256": sha256_file(
                 CFG / "R1L_SEALED_ANALYTIC_STRESS_COMMITMENT_UNSCORED.json"),
             "scored": False},
            {"id": "R1L_SEALED_MAIN_COMMITMENT",
             "path": "artifacts/configs/R1L_SEALED_MAIN_COMMITMENT.json",
             "sha256": sha256_file(CFG / "R1L_SEALED_MAIN_COMMITMENT.json"),
             "scored": False,
             "note": "the original document, preserved byte for byte"},
        ],

        "report_correction_required": {
            "file": "artifacts/reports/R1L_STAGE2R_B_GATE_COMPLETED.md",
            "section": 7,
            "defect": "section 7 was written before the physical-bank scope "
                      "carried the disposition and still claimed a material "
                      "reduction at the reference SNR",
            "corrected_to": "materiality is not met on the physical banks at "
                            "SNR0 = 100; it is met at SNR0 = 1000 as a "
                            "secondary result; the all-banks effect is carried "
                            "by the signed diagnostic bank",
        },

        "instructions_discharged": [
            "1 accept 4cb9895",
            "2 record the six dispositions separately",
            "3 the clean reproduction is not an implementation defect",
            "4 correct section 7 of the gate-completed report",
            "5 preserve the machine token and explain it in prose",
            "6 sealed_main_authorized = false",
            "7 preserve every sealed commitment unscored",
        ],
    }
    doc["attestation"] = attest([])
    OUT.write_text(json.dumps(doc, indent=2, default=str) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}")
    print(f"  sealed_main_authorized: {doc['sealed_main_authorized']}")
    for k in doc["dispositions"]:
        print(f"  recorded {k}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
