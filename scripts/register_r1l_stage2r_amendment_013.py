#!/usr/bin/env python3
"""R1L_STAGE2R_GATE_COMPLETION_AMENDMENT_013 -- record and reclassify.

Reviewer ruling on stage 2R-B, items 1 to 6 and 8. The scientific disposition
stands; what is repaired is gate coverage and the description of two source
banks. Nothing is rescored by this amendment.
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

FZ = ROOT / "artifacts" / "configs" / "R1L_STAGE2R_VALIDATION_FREEZE_012.json"
GATES = ROOT / "artifacts" / "gates" / "r1l_2rb_gates.json"
TAB = ROOT / "artifacts" / "tables"
OUT = (ROOT / "artifacts" / "configs"
       / "R1L_STAGE2R_GATE_COMPLETION_AMENDMENT_013.json")

PRIMARY_CLASS = "L1056"
ROLES = {
    "constant_flux_structural": {
        "role_id": "SIGNED_CONSTANT_FLUX_STRUCTURAL_DIAGNOSTIC",
        "physical_primary_eligible": False,
        "why": "renormalising each age slice to a fixed spatial mean, then "
               "projecting onto the class, leaves a field that is not "
               "everywhere non-negative. It is a legitimate linear "
               "inverse-problem stress control and is not a physical "
               "emissivity history",
    },
    "structure_balanced_050": {
        "role_id": "STRUCTURE_BALANCED_050",
        "physical_primary_eligible": True,
        "why": "non-negative to numerical tolerance and realized close to its "
               "nominal structure fraction",
    },
    "structure_balanced_080": {
        "role_id": "HIGH_STRUCTURE_NOMINAL_080_REALIZED_066",
        "physical_primary_eligible": True,
        "why": "non-negative to numerical tolerance. The nominal 0.80 target is "
               "set before projection onto the class and projection removes "
               "structure, so the realized fraction is what the operator and "
               "the estimator saw and is what the name now carries",
    },
}


def main() -> int:
    fz = json.loads(FZ.read_text())
    g = json.loads(GATES.read_text())
    banks = pd.read_parquet(TAB / "r1l_2rb_source_banks.parquet")
    end = pd.read_parquet(TAB / "r1l_2rb_endpoint.parquet")

    declared = list(fz["gates"])
    emitted = list(g["gates"])
    missing = [k for k in declared if k not in emitted]

    b = banks[banks.source_class == PRIMARY_CLASS]
    measured = {}
    for name, grp in b.groupby("bank"):
        measured[name] = {
            "n": int(len(grp)),
            "achieved_structure_fraction_median":
                float(grp.achieved_structure_fraction.median()),
            "achieved_structure_fraction_min":
                float(grp.achieved_structure_fraction.min()),
            "nominal_structure_fraction":
                fz["source_banks"]["target_structure_fraction"][name],
            "negative_mass_relative_median":
                float(grp.negative_mass_relative.median()),
            "negative_mass_relative_max":
                float(grp.negative_mass_relative.max()),
            "n_records_above_0_1_negative_mass":
                int((grp.negative_mass_relative > 0.1).sum()),
            "reprojection_residual_relative_median":
                float(grp.reprojection_residual_relative.median()),
            "representation_floor_max": float(grp.representation_floor.max()),
        }

    res = end[(end.source_class == PRIMARY_CLASS) & (end.snr0 == 100.0)
              & (end.arm == "RESOLVED_PHYSICAL")]
    estimands = {r.estimator: {
        "per_truth_median": float(r.median_relative_reduction),
        "cell_balanced_mean": float(r.relative_reduction),
        "ci_low_on_cell_balanced_mean": float(r.ci_low),
        "ci_high_on_cell_balanced_mean": float(r.ci_high),
    } for r in res.itertuples()}

    doc = {
        "schema": "phrt-record-amendment/1",
        "id": "R1L_STAGE2R_GATE_COMPLETION_AMENDMENT_013",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "ruling": "Reviewer ruling on R1L stage 2R-B",
        "kind": "RECORD_AND_RECLASSIFY",
        "recomputation": "none by this amendment. The gate implementations and "
                         "the deterministic rerun follow it",

        "preserved_commits": [
            "2f7af9a6019cfb75b3642cac1cf87b3e58bd5081",
            "b83cdf4706eed942bcef2c7a057f1a0d34f2e807",
            "151229d45c08012e8aa5197f389cce49784b6080",
        ],
        "preserved_disposition": "R1L_STAGE2R_B_MATERIAL_RESOLVED_ONLY",

        "R1L_2RB_DECLARED_GATE_COVERAGE_DEFECT": {
            "defect": "the freeze declared 11 gates and the runner emitted 9",
            "declared": declared,
            "emitted": emitted,
            "missing": missing,
            "accurate_statement_before_repair":
                f"all {len(emitted)} emitted gates passed",
            "inaccurate_statement_avoided":
                f"all {len(declared)} frozen gates passed",
            "why_it_matters": "the two omitted gates correspond exactly to the "
                              "source-construction caveats the experiment then "
                              "found by hand. A declared gate that is never "
                              "emitted is indistinguishable from a gate that "
                              "was emitted and passed, unless someone counts",
            "detected_by": "the reviewer, by counting declared against emitted. "
                           "Nothing in the harness compared the two",
            "structural_remedy": "the runner now asserts that the set of emitted "
                                 "gate names equals the set the freeze declares, "
                                 "and fails if it does not. Counting is not left "
                                 "to a reader",
            "is_a_scientific_defect": False,
            "is_a_governance_defect": True,
        },

        "source_bank_reclassification": {
            "rule": "the realized property, not the pre-projection intent, is "
                    "what the operator and the estimator saw, so it is what the "
                    "name carries",
            "banks": {k: {**v, "measured": measured.get(k, {})}
                      for k, v in ROLES.items()},
            "physical_primary_banks": [k for k, v in ROLES.items()
                                       if v["physical_primary_eligible"]],
            "signed_diagnostic_banks": [k for k, v in ROLES.items()
                                        if not v["physical_primary_eligible"]],
            "consequence": "the physical-source claim must survive on the two "
                           "non-negative structure-balanced banks alone. The "
                           "signed bank is reported and may not carry it",
            "note_on_the_earlier_summary": "the stage 2R-B report gave the "
                                           "constant-flux negative mass as "
                                           "about 3.6 percent, which is the "
                                           "median. The maximum over records is "
                                           "19.7 percent and 18 of 64 records "
                                           "exceed 10 percent. Quoting the "
                                           "median alone understated it",
        },

        "estimand_correction": {
            "defect": "the report attached a bootstrap interval computed for the "
                      "equal-weight bank-family mean to a per-truth median, as "
                      "though they were one number",
            "two_estimands": "per-truth median, and cell-balanced mean over "
                             "bank-family cells. They are different statistics "
                             "of the same paired sample",
            "primary_class": PRIMARY_CLASS,
            "reference_snr": 100.0,
            "resolved_arm": estimands,
            "both_support_a_material_effect": True,
            "remedy": "a separate truth-cluster bootstrap interval for the "
                      "median is added, and every reported interval names the "
                      "statistic it belongs to",
        },

        "stable_span_noise_semantics": {
            "implemented_in_2rb": "the four noise-draw error curves are averaged "
                                  "per truth before the q = 0.95 criterion is "
                                  "applied",
            "canonical_definition": "Pr over truth and noise jointly that "
                                    "sup_a E(a) <= epsilon",
            "difference": "averaging over noise first is a weaker condition than "
                          "requiring every truth-noise realization to hold",
            "does_it_change_the_result": "no. The averaged curves already give "
                                         "zero span, and the joint criterion is "
                                         "stricter, so it cannot produce a "
                                         "positive span that averaging hid",
            "remedy": "both are emitted, and the joint (x, eta) statistic "
                      "controls the scientific claim",
        },

        "exact_in_class_scope_correction": {
            "was": "an upper bound on what this operator can do for this class",
            "defect": "over-strong. Exact-in-class truths are not a formal upper "
                      "bound over all histories: an off-class history that "
                      "happens to align with well-observed operator directions "
                      "could be easier than some in-class ones, while many "
                      "others are much harder",
            "now": "a representation-matched, zero-floor best-case benchmark. It "
                   "isolates inversion error from representation error and "
                   "measures the operator under an exactly matched localized "
                   "model class. It does not establish performance for "
                   "arbitrary or realistic accretion-flow histories",
        },

        "instructions_discharged": [
            "1 preserve the three commits",
            "2 preserve R1L_STAGE2R_B_MATERIAL_RESOLVED_ONLY",
            "3 record R1L_2RB_DECLARED_GATE_COVERAGE_DEFECT",
            "6 reclassify the constant-flux and nominal-080 banks",
            "8 commit the amendment with the code",
        ],
        "provenance": {"freeze_sha256": sha256_file(FZ),
                       "gates_sha256": sha256_file(GATES)},
    }
    doc["attestation"] = attest([FZ])
    OUT.write_text(json.dumps(doc, indent=2) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}")
    print(f"  declared {len(declared)}, emitted {len(emitted)}, missing {missing}")
    for k, v in measured.items():
        print(f"  {k:26s} f_struct {v['achieved_structure_fraction_median']:.3f}  "
              f"neg mass med {v['negative_mass_relative_median']:.4f} "
              f"max {v['negative_mass_relative_max']:.4f} "
              f"(> 0.1 in {v['n_records_above_0_1_negative_mass']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
