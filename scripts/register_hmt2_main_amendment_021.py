#!/usr/bin/env python3
"""HMT2_MAIN_RECORD_AMENDMENT_021.

Items 1 to 8 of REVIEWER_RULING_HMT2_MAIN_021. A record amendment: it adds
dispositions, deviations and qualifications to an accepted run and changes no
endpoint. Item 10 forbids rerunning, appending truths or recomputing, so every
number below is read out of the canonical parquet the accepted run wrote,
never recalculated from the scores.
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

import pandas as pd  # noqa: E402

from phrt.attestation import attest  # noqa: E402
from phrt.config import sha256_file  # noqa: E402

T = ROOT / "artifacts" / "tables"
CFG = ROOT / "artifacts" / "configs"
FZ = CFG / "HMT2_SEALED_MAIN_V1.json"
S1A = CFG / "HMT2_STAGE1_ENDPOINT_COMPLETION_AMENDMENT_020.json"
GATES = ROOT / "artifacts" / "gates" / "hmt2_sealed_main_gates.json"
MANIFEST = ROOT / "artifacts" / "provenance" / "HMT2_SEALED_MAIN_ARTIFACT_MANIFEST.json"
BANK = ROOT / "artifacts" / "provenance" / "HMT2_SEALED_MAIN_BANK_HASHES.json"
OUT = CFG / "HMT2_MAIN_RECORD_AMENDMENT_021.json"

CLAIM = "L896_radial_enriched"
ARM = "RESOLVED_PHYSICAL"
REF = 100.0


def main() -> int:
    fz = json.loads(FZ.read_text())
    man = json.loads(MANIFEST.read_text())
    bank = json.loads(BANK.read_text())

    ep = pd.read_parquet(T / "hmt2_main_endpoint.parquet")
    fam = pd.read_parquet(T / "hmt2_main_per_family.parquet")
    sm = pd.read_parquet(T / "hmt2_main_stable_multi.parquet")
    si = pd.read_parquet(T / "hmt2_main_stable_interval.parquet")

    def cell(df, arm=ARM, cls=CLAIM, snr=REF, est=None):
        q = df[(df["class"] == cls) & (df.arm == arm) & (df.snr0 == snr)]
        if est is not None:
            q = q[q.estimator == est]
        return q

    claim = cell(ep)
    fq = cell(fam)
    n_phys = int(fq.PHYSICAL_END_TO_END_material.sum())
    n_both = int((fq.PHYSICAL_END_TO_END_material
                  & fq.CLASS_CONDITIONAL_material).sum())
    phys_cells = sorted(f"{r.family}|{r.estimator}"
                        for r in fq[fq.PHYSICAL_END_TO_END_material].itertuples())
    both_cells = sorted(f"{r.family}|{r.estimator}"
                        for r in fq[fq.PHYSICAL_END_TO_END_material
                                    & fq.CLASS_CONDITIONAL_material].itertuples())
    robust = sorted({r.family for r in fq[fq.PHYSICAL_END_TO_END_material].itertuples()}
                    & {f for f in fq.family.unique()
                       if fq[(fq.family == f)].PHYSICAL_END_TO_END_material.all()})
    negative = sorted({r.family for r in fq.itertuples()
                       if fq[fq.family == r.family]
                       .PHYSICAL_END_TO_END_median_reduction.max() < 0})

    smq = cell(sm)
    siq = si[(si["class"] == CLAIM) & (si.snr0 == REF)]
    si10 = si[(si["class"] == CLAIM) & (si.snr0 == 1000.0)]

    def two(v):
        return None if pd.isna(v) else float(v)

    doc = {
        "schema": "phrt-record-amendment/1",
        "id": "HMT2_MAIN_RECORD_AMENDMENT_021",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "ruling": "REVIEWER_RULING_HMT2_MAIN_021",
        "kind": "RECORD_ONLY",
        "accepted_commit": "0d1f7510caf76f7b05e87b640d343ca9b9fbcf93",
        "alters_no_endpoint": True,
        "recomputation": "NONE. Item 10 forbids rerunning, appending truths "
                         "or recomputing the endpoint. Every figure here is "
                         "read from the parquet the accepted run wrote",

        "formal_token_preserved": "HMT2_MAIN_PHYSICAL_MORPHOLOGY_RECOVERY_PASS",
        "formal_token_reading": "the preregistered pass criteria were met on "
                                "held-out truths at a materiality floor "
                                "declared before the bank was drawn. That is "
                                "what the token reports. What the run "
                                "establishes, and what it does not, is in the "
                                "dispositions",

        "scientific_dispositions": {
            "HMT2_MAIN_AGGREGATE_PHYSICAL_MORPHOLOGY_ERROR_REDUCTION_CONFIRMED": {
                "finding": "in the claim-bearing class at the reference SNR "
                           "the resolved arm reduces the all-state "
                           "resolution-aware morphology error against the "
                           "direct image by a median "
                           f"{float(cell(ep, est='RIDGE_IDENTITY').PHYSICAL_END_TO_END_median_reduction.iloc[0]):.3f} "
                           "under ridge and "
                           f"{float(cell(ep, est='TSVD').PHYSICAL_END_TO_END_median_reduction.iloc[0]):.3f} "
                           "under TSVD on the physical end-to-end target, with "
                           "paired bootstrap lower bounds "
                           f"{float(cell(ep, est='RIDGE_IDENTITY').PHYSICAL_END_TO_END_ci_low.iloc[0]):.3f} "
                           "and "
                           f"{float(cell(ep, est='TSVD').PHYSICAL_END_TO_END_ci_low.iloc[0]):.3f}",
                "floor": "median 0.10 and lower bound 0.05, declared in the "
                         "sealed freeze before the bank was drawn",
                "scope": "aggregate over the bank. It is an average across a "
                         "heterogeneous set of families and is not a "
                         "per-family or per-source statement",
            },
            "HMT2_MAIN_ORDER_RESOLUTION_ATTRIBUTION_SUPPORTED": {
                "finding": "the unresolved-image control reaches at most "
                           f"{float(cell(ep, arm='UNRESOLVED_IMAGE').PHYSICAL_END_TO_END_median_reduction.max()):.3f} "
                           "in the claim-bearing class and the total-flux "
                           "control reaches "
                           f"{float(cell(ep, arm='TOTAL_FLUX').PHYSICAL_END_TO_END_median_reduction.max()):.3f}, "
                           "neither material",
                "reading": "the benefit is attributable to resolving the "
                           "photon-ring orders and not to the additional "
                           "photons an unresolved second image also carries, "
                           "nor to the extra flux constraint alone",
                "limit": "an attribution within the four declared arms of one "
                         "geometry. It is not a statement about any other "
                         "route to the same information",
            },
            "HMT2_MAIN_MULTI_FEATURE_RECOVERY_NEGATIVE": {
                "finding": "two-feature recovery reaches materiality in no "
                           "cell. In the claim-bearing class the median "
                           "reductions are "
                           f"{float(smq.median_reduction.min()):.3f} to "
                           f"{float(smq.median_reduction.max()):.3f} and the "
                           "absolute assignment cost stays between "
                           f"{float(smq.arm_cost.min()):.3f} and "
                           f"{float(smq.arm_cost.max()):.3f} "
                           "on a scale where 1.0 is one whole feature wrong",
                "reading": "the measure resolves that a state has two features "
                           "and recovers the morphology of one. It does not "
                           "recover the pair. This is a negative result and is "
                           "preserved as one",
                "held_out": "the sealed main reproduces on fresh truths the "
                            "same split the stage 1 completion found",
                "n_truths_carrying_the_endpoint": int(smq.n_truths.iloc[0]),
                "power": "only "
                         f"{int(smq.n_truths.iloc[0])} of "
                         f"{int(fz['bank']['n_truths'])} truths carry a stable "
                         "multi-resolved state at all, so this endpoint is the "
                         "thinnest in the run. It is reported as a "
                         "not-established rather than as a demonstrated "
                         "absence",
            },
            "HMT2_MAIN_STABLE_MORPHOLOGY_INTERVAL_NEGATIVE": {
                "finding": "the stable morphology interval is "
                           f"{float(si.L_stable_morphology_M.max()):.0f} M for "
                           "every arm, estimator, class and SNR",
                "mean_reach_at_the_reference_snr": "the resolved arm reaches "
                    f"{float(siq[siq.arm == ARM].mean_reach_M.mean()):.3f} M "
                    "against the direct image's "
                    f"{float(siq[siq.arm == 'DIRECT_PHYSICAL'].mean_reach_M.mean()):.3f} M, "
                    "lower under both estimators",
                "mean_reach_at_tenfold_snr": "the ordering reverses: "
                    f"{float(si10[si10.arm == ARM].mean_reach_M.mean()):.3f} M "
                    "resolved against "
                    f"{float(si10[si10.arm == 'DIRECT_PHYSICAL'].mean_reach_M.mean()):.3f} M "
                    "direct. Stated explicitly because the reference-SNR "
                    "comparison is the claim-bearing one and reads as a "
                    "general statement if the SNR is left off",
                "reading": "there is no age window over which recovered "
                           "morphology holds steady. At the reference SNR the "
                           "resolved arm does not even extend how far back "
                           "morphology stays in tolerance. A per-age error "
                           "reduction is not a history interval",
            },
            "HMT2_MAIN_FAMILY_HETEROGENEITY_PRESERVED": {
                "finding": f"{n_phys} of {len(fq)} family-estimator cells are "
                           "material on the physical end-to-end target and "
                           f"{n_both} of {len(fq)} on both targets. "
                           f"{', '.join(negative)} is negative under both "
                           "estimators",
                "material_physical": phys_cells,
                "material_both_targets": both_cells,
                "material_under_both_estimators": robust,
                "reading": "the aggregate is not a uniform improvement and "
                           "must not be quoted as one. Ten truths per family "
                           "makes these intervals wide, so no family claim is "
                           "supported in either direction; the heterogeneity "
                           "is what is recorded, not a ranking",
            },
            "HMT2_MAIN_DIRECT_BASELINE_SATURATION_QUALIFICATION": {
                "finding": "in the claim-bearing class "
                           f"{float(claim.PHYSICAL_END_TO_END_saturation_direct.mean()):.1%} "
                           "of direct-image states sit at the measure's "
                           "ceiling, against "
                           f"{float(claim.PHYSICAL_END_TO_END_saturation_arm.mean()):.1%} "
                           "for the resolved arm",
                "reading": "the mean substantially counts how many states "
                           "failed outright rather than how far off the "
                           "recovered morphology was. The direct baseline is "
                           "partly floor-limited, which flatters the "
                           "difference, and the gain must be read with the "
                           "saturation fractions beside it",
                "not_repaired": "changing the measure's ceiling after seeing "
                                "the result would be moving a criterion. The "
                                "fractions are emitted so the reader can "
                                "discount by inspection",
            },
            "HMT2_MAIN_ACCURATE_HISTORICAL_MOVIE_RECOVERY_NOT_ESTABLISHED": {
                "finding": "absolute all-state error for the resolved arm "
                           "remains "
                           f"{float(claim.PHYSICAL_END_TO_END_arm.min()):.3f} to "
                           f"{float(claim.PHYSICAL_END_TO_END_arm.max()):.3f} "
                           "on a scale whose worst case is 1.0, with no stable "
                           "interval and no two-feature recovery",
                "reading": "a material reduction in a morphology error is not "
                           "accurate recovery of a historical movie, and this "
                           "campaign does not establish the latter at any "
                           "point. Nothing here licenses a statement about "
                           "arbitrary or realistic accretion-flow histories",
            },
        },

        "scope_deviation": {
            "disposition": "HMT2_MAIN_REDUCED_SCOPE_EVIDENCE_ACCEPTED",
            "authorized": {"truths": 96, "truths_per_family": 16,
                           "noise_draws": 8},
            "executed": {"truths": int(fz["bank"]["n_truths"]),
                         "truths_per_family": int(fz["bank"]["truths_per_family"]),
                         "noise_draws": int(fz["bank"]["noise_draws_per_truth"])},
            "pre_data": "the reduction was written into "
                        "HMT2_SEALED_MAIN_V1 and committed before any "
                        "held-out truth was drawn, so it cannot have been "
                        "chosen to shape the result",
            "defect": "it was not flagged as a deviation at the time and no "
                      "rationale was recorded in the freeze. A reduced bank "
                      "was simply written down as though it were the "
                      "authorized one",
            "consequence": "every interval in the run is wider than the "
                           "authorized design would have given, and the "
                           "per-family cells at ten truths are wide enough "
                           "that no family claim is supported either way. The "
                           "aggregate endpoint clears its floor at this "
                           "sample size, which is why the evidence stands",
            "accepted_by": "item 4",
        },

        "family_counts_clarified": {
            "physical_end_to_end_material": f"{n_phys}/{len(fq)}",
            "both_targets_material": f"{n_both}/{len(fq)}",
            "corrects": "the sealed main commit message and the return report "
                        "both say '4 of 12 family-estimator cells are "
                        f"material', which is the both-targets count. "
                        f"{n_phys} of {len(fq)} are material on "
                        "PHYSICAL_END_TO_END, the target that carries the "
                        "physical claim. Item 5",
            "narrative_correction": "the two families material under both "
                                    "estimators are "
                                    f"{' and '.join(robust)}; "
                                    "plunging_feature is material under ridge "
                                    "alone, which is the third family in the "
                                    f"{n_phys}-cell count and was omitted from "
                                    "the earlier summary",
        },

        "qualifications_recorded": {
            "HMT2_MAIN_STAGE_A_ATTESTATION_DIRTY": {
                "qualification": "the authoritative stage A run, which drew "
                                 "the sealed bank and committed its hashes, "
                                 "executed against a working tree that was "
                                 "not clean on the registered pathspecs: "
                                 f"{man['stage_a_attestation']['n_tracked_changes']} "
                                 "tracked modification and "
                                 f"{man['stage_a_attestation']['n_untracked']} "
                                 "untracked files",
                "what_was_dirty": man["stage_a_attestation"]["porcelain_registered"],
                "why": "the modification is the deterministic-hash repair "
                       "below. Stage A had to be re-run with the fix in the "
                       "tree before it could be committed alongside the "
                       "hashes it produced",
                "mitigation": "the sealed freeze was tracked and already "
                              "committed when stage A ran, at "
                              f"{man['stage_a_attestation']['execution_commit'][:12]}; "
                              "the exact porcelain diff is recorded and "
                              "hashed in the manifest; the fix and the bank "
                              "hashes stage A produced were then committed "
                              "together as "
                              f"{man['execution_attestation']['execution_commit'][:12]}, "
                              "and stage B executed at that same commit with "
                              "a fully clean tree and reproduced all "
                              f"{int(bank['n_truths'])} commitments",
                "reading": "the bank is verifiable from the committed record. "
                           "The attestation is not clean and is not presented "
                           "as clean",
                "not_repairable_retrospectively": "re-running stage A from a "
                                                  "clean tree would draw the "
                                                  "bank again, which item 10 "
                                                  "forbids and which would "
                                                  "destroy the seal",
            },
            "HMT2_MAIN_SALTED_HASH_DEFECT_CAUGHT_BY_GATE": {
                "defect": "the sealed bank's label-integrity field was built "
                          "with Python's builtin hash(), which salts string "
                          "hashing per process unless PYTHONHASHSEED is set "
                          "before the interpreter starts. pin() sets it far "
                          "too late. Stage A and stage B are separate "
                          "processes, so the field could never match",
                "presented_as": "60 of 60 bank hash mismatches at the start "
                                "of stage B, which reads as a tampered bank",
                "scope": "the integrity field only. Truth content and truth "
                         "seeds were sha256 throughout, so no drawn truth and "
                         "no seed was ever affected. The defect was in the "
                         "check, not in the bank",
                "caught_by": "HMT2M_G2_commitments_reproduce, which refused "
                             "to let stage B proceed. The gate did its job",
                "third_occurrence": "the same bug appeared at the R0 "
                                    "null-pair seed and at HMT-1's "
                                    "off-manifold seeds. Twice it was found "
                                    "by reasoning backwards from a symptom",
                "repair": "labels are hashed with sha256 of the joined label "
                          "string, and three tests now hold the property: one "
                          "scans every script for a bare builtin hash() call, "
                          "one asserts that builtin hash differs across "
                          "processes, one asserts the replacement is stable "
                          "across them",
                "no_endpoint_effect": "the repair changed an integrity field "
                                      "and nothing the endpoint reads",
            },
        },

        "text_corrections": {
            "test_count": {
                "commit_message_says": 488,
                "correct": 489,
                "cause": "the message was written before "
                         "test_the_csv_twin_is_capped was added to the same "
                         "amended commit. The accepted tree at "
                         "0d1f7510 collects 489",
                "resolution": "the commit message is part of the accepted "
                              "commit and is not rewritten. 489 is the count "
                              "of record and is what every later document "
                              "says. Item 7",
            },
        },

        "artifact_management": {
            "change": "CSV_TWIN_MAX_ROWS = 250000 in src/phrt/io/tables.py",
            "reason": "the 936960-row state table produced a 122 MB CSV twin "
                      "against a 1.7 MB parquet, above the remote's file size "
                      "limit",
            "behaviour": "above the cap the writer emits a .csv.skipped stub "
                         "naming the row count and pointing at the parquet",
            "status": "NON_SCIENTIFIC_ARTIFACT_MANAGEMENT_REPAIR. Parquet is "
                      "authoritative for every table and always was; the stub "
                      "is required so a missing twin is never silent. Item 8",
        },

        "not_authorized": ["order leakage", "geometry mismatch", "VLBI",
                           "machine learning", "a new pixel-movie campaign",
                           "rerunning, appending truths or recomputing the "
                           "endpoint"],

        "inputs": {"sealed_main_freeze_sha256": sha256_file(FZ),
                   "stage_1_amendment_sha256": sha256_file(S1A),
                   "sealed_main_gates_sha256": sha256_file(GATES),
                   "artifact_manifest_sha256": sha256_file(MANIFEST),
                   "bank_hashes_sha256": sha256_file(BANK),
                   "endpoint_table_sha256": sha256_file(T / "hmt2_main_endpoint.parquet"),
                   "per_family_table_sha256": sha256_file(T / "hmt2_main_per_family.parquet"),
                   "stable_multi_table_sha256": sha256_file(T / "hmt2_main_stable_multi.parquet"),
                   "stable_interval_table_sha256": sha256_file(T / "hmt2_main_stable_interval.parquet")},
        "attestation": attest([FZ, S1A]),
    }
    OUT.write_text(json.dumps(doc, indent=2, default=str) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}\n  sha256 {sha256_file(OUT)}")
    print(f"  {len(doc['scientific_dispositions'])} dispositions, "
          f"{len(doc['qualifications_recorded'])} qualifications")
    print(f"  families material: {n_phys}/{len(fq)} physical, "
          f"{n_both}/{len(fq)} both targets")
    print(f"  scope: {doc['scope_deviation']['executed']} executed against "
          f"{doc['scope_deviation']['authorized']} authorized")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
