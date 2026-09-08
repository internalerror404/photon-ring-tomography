#!/usr/bin/env python3
"""Ruling 037: the claim-level evidence chain. Zero physical queries.

Every claim carries structured evidence -- commit, repository path, the sha256
of the bytes at that commit, and a row selector -- and the ten pins resolved
per experiment. A pin is RESOLVED with a value and a reference, NOT_APPLICABLE
with a reason, or UNRESOLVED; an UNRESOLVED pin bars the claim from a headline.

The single global "single-sky sigma" pin of the 036 matrix is gone. R2's ideal
order-labelled comparison and the later D026 single-sky detector experiment are
different experiments and are pinned separately.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "revisions" / "mahakal_v4_1" / "manuscript037"
PINS = ("operator", "source_basis", "source_Gram", "sampled_rays",
        "quadrature", "covariance", "noise_normalisation",
        "target_nuisance_partition", "estimator", "evaluation_metric")

E3C = "artifacts/reports/E3C_GEOMETRY_WIDE_OPERATOR_AUDIT.md"
E3CM = "artifacts/reports/E3C_MECHANISM_DECOMPOSITION.md"
E3CF = "artifacts/configs/E3C_OPERATOR_GRID_FREEZE.json"
R1 = "artifacts/reports/R1_HELD_OUT_MAIN.md"
EVID = "docs/Paper_I_v1_Current_Evidence_Ledger.md"
R2CSV = ("artifacts/revisions/mahakal_v4_1/R2REPLAY_20260906T144528Z_b873908/"
         "reference_geometry_information.csv")
R2MD = ("artifacts/revisions/mahakal_v4_1/R2REPLAY_20260906T144528Z_b873908/"
        "R2_CLOSEOUT_REPORT.md")
LOC = ("artifacts/revisions/mahakal_v4_1/LOC025_20260906T184213Z/"
       "LOCALIZATION_READBACK.json")
G1C = ("artifacts/revisions/mahakal_v4_1/G1C_20260907T075203Z_d252697/"
       "GEOMETRY_CLOSEOUT_029.json")
Q035 = ("artifacts/revisions/mahakal_v4_1/Q035_20260908T004247Z_c1bf640/"
        "PER_CHANNEL_RESPONSE_AND_SUPPORT_035.json")
N033 = ("artifacts/revisions/mahakal_v4_1/N033B_20260907T211922Z_45bd28e/"
        "COMPARATOR_CAUSE_AND_CONFIRMATION_033.json")
HMT2 = "artifacts/configs/HMT2_SEALED_MAIN_V1.json"


def head() -> str:
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                          capture_output=True, text=True).stdout.strip()


def blob_sha(commit: str, path: str) -> str | None:
    r = subprocess.run(["git", "-C", str(ROOT), "show", f"{commit}:{path}"],
                       capture_output=True)
    if r.returncode:
        return None
    return hashlib.sha256(r.stdout).hexdigest()


def ev(commit, path, selector):
    d = blob_sha(commit, path)
    return {"commit": commit, "path": path, "sha256": d,
            "selector": selector} if d else {
        "commit": commit, "path": path, "sha256": None, "selector": selector,
        "unreadable": True}


def R(value, ref):
    return {"status": "RESOLVED", "value": value, "evidence_ref": ref}


def NA(reason):
    return {"status": "NOT_APPLICABLE", "reason": reason}


def U(note):
    return {"status": "UNRESOLVED", "note": note}


def build(c: str) -> list[dict]:
    # --- per-experiment pin blocks, written once and reused -------------
    e3c_pins = {
        "operator": R("order-labelled ideal stack, n = 0,1,2, matrix-free "
                      "whitened, 12 registered geometries", E3CF),
        "source_basis": R("declared temporal/spatial product class on the "
                          "common age grid", E3CF),
        "source_Gram": NA("detectability masks are computed per probe age; no "
                          "source-norm Gram enters the threshold statistic"),
        "sampled_rays": R("frozen E3C ray set per geometry", E3CF),
        "quadrature": R("pixel-integrated, sqrt(dOmega) g^3 whitened row", E3CF),
        "covariance": R("diagonal whitened, per-geometry SNR sweep", E3CF),
        "noise_normalisation": R("reference SNR_0 with the corrected "
                                 "sqrt(dOmega) g^3 row convention", E3CF),
        "target_nuisance_partition": NA("no nuisance profiling in the "
                                        "detectability audit"),
        "estimator": NA("threshold detectability, not an estimator"),
        "evaluation_metric": R("age_threshold_mask; oldest probe, longest run "
                               "and anchor-connected span reported separately",
                               E3C),
    }
    r2_pins = {
        "operator": R("sampled order-labelled operator at a050_i050; ideal "
                      "order-labelled observations, NOT the later D026 "
                      "single-sky detector experiment", R2MD),
        "source_basis": R("full L224; 72-dim old-contrast target, 152-dim "
                          "nuisance", R2CSV),
        "source_Gram": R("target Gram condition 1.786e+03; Gram relative "
                         "change 3.009e-07 across refinements", R2MD),
        "sampled_rays": R("frozen R2 replay input set, 36 hashed files", R2MD),
        "quadrature": R("corrected measure; Gauss radial plus exact piecewise "
                        "quadratic temporal for the localization readback",
                        LOC),
        "covariance": R("declared positive-definite noise model C with "
                        "sigma = 0.011341986814407566 inside C", R2CSV),
        "noise_normalisation": R("sigma inside C; singular values are NOT "
                                 "multiplied by an SNR label a second time",
                                 R2MD),
        "target_nuisance_partition": R("orthogonal projector onto range(B_N), "
                                       "nuisance rank 152", R2CSV),
        "estimator": NA("an information calculation, not a reconstruction "
                        "estimator"),
        "evaluation_metric": R("traces of the normalised Fisher matrices; "
                               "operational count at rho = 1; frozen legacy "
                               "measure", R2CSV),
    }
    r1_pins = {
        "operator": R("order-labelled arms DIRECT_PHYSICAL, "
                      "RESOLVED_PHYSICAL, UNRESOLVED_IMAGE, TOTAL_FLUX", R1),
        "source_basis": R("C224", R1),
        "source_Gram": R("C224 source norm as registered in the R1 freeze", R1),
        "sampled_rays": R("frozen R1 ray set at a050_i050", R1),
        "quadrature": R("pixel-integrated, corrected row convention", R1),
        "covariance": R("whitened diagonal at SNR_0 = 100 reference", R1),
        "noise_normalisation": R("SNR_0 = 100 reference; onset sweep to 30000",
                                 R1),
        "target_nuisance_partition": NA("no nuisance profiling; the level and "
                                        "structure projectors are a "
                                        "deterministic diagnostic split"),
        "estimator": R("prior-free TSVD and ridge", R1),
        "evaluation_metric": R("registered baseline-inclusive field metric; "
                               "anchored stable span; NOT a coefficient-space "
                               "metric", R1),
    }
    hmt2_pins = {
        "operator": R("order-labelled arms with UNRESOLVED_IMAGE and "
                      "TOTAL_FLUX controls", HMT2),
        "source_basis": R("L448_contrast and L896_radial_enriched", EVID),
        "source_Gram": R("family source norms as registered in the sealed "
                         "main freeze", HMT2),
        "sampled_rays": R("frozen HMT-2 ray set", HMT2),
        "quadrature": R("pixel-integrated, corrected row convention", HMT2),
        "covariance": R("four paired noise draws per truth", EVID),
        "noise_normalisation": R("as registered in HMT2_SEALED_MAIN_V1", HMT2),
        "target_nuisance_partition": NA("no nuisance profiling in the "
                                        "morphology benchmark"),
        "estimator": R("prior-free TSVD and ridge, reported separately", EVID),
        "evaluation_metric": R("registered morphology error-reduction against "
                               "the analytic source target; materiality median "
                               ">= 0.10 and bootstrap lower bound >= 0.05",
                               EVID),
    }
    d026_pins = {
        "operator": R("D026 detector, alpha,beta in [-25,25] M, pitch 0.4 M",
                      Q035),
        "source_basis": R("six screen channels and five transferred channels "
                          "at each of eight observer times", Q035),
        "source_Gram": NA("a response comparison on identical support; no "
                          "source norm enters"),
        "sampled_rays": R("archived core and fine ray maps at a050_i050", Q035),
        "quadrature": R("nodal dual clipped cell measure; qualified hull "
                        "tessellation", Q035),
        "covariance": R("single-sky sigma^2 over the full pixel area once per "
                        "observer time", Q035),
        "noise_normalisation": R("sigma = 0.011341986814407566; whitening "
                                 "1/(sigma sqrt(cell area))", Q035),
        "target_nuisance_partition": NA("no target/nuisance split in a "
                                        "response comparison"),
        "estimator": NA("no estimator; a representation comparison"),
        "evaluation_metric": R("per-channel norm(W(y_hat - y_ref)) / "
                               "norm(W y_ref)", Q035),
    }

    def cl(cid, orig, rev, disp, level, evs, pins, dep, headline, note=None):
        d = {"claim_id": cid,
             "original_document_identity": "artifacts/manuscript/PAPER_I.md "
                                           "(archived Shiva-era source) and "
                                           "docs/revisions/mahakal_v4_1/"
                                           "manuscript036 working revision",
             "original_exact_text_and_location": orig,
             "revised_text_and_location": rev, "disposition": disp,
             "evidence_level": level, "evidence": evs,
             "pins": {k: dict(pins[k]) for k in PINS},
             "unresolved_scientific_dependency": dep,
             "candidate_abstract_or_headline_allowed": headline}
        if note:
            d["note"] = note
        return d

    S, D = "STRUCTURAL_MATHEMATICS", "REPRODUCED_DISCRETE_BENCHMARK"
    return [
        cl("C01",
           "036 abstract: 'median recoverable depth 60, 84 and 144 M ... a "
           "single value across four spins', read as recoverable depth",
           "section 5.2: 60, 84, 144 M is the oldest detectable age probe, a "
           "supremum of a threshold mask; the anchor-connected spans are 60, "
           "84 and 112/116 M",
           "CORRECTED_STATISTIC_AND_INTERPRETATION", D,
           [ev(c, E3C, "Oldest detectable age probe, resolved stack (M) table; "
                       "Contiguous detectable span from the anchor, resolved "
                       "stack (M) table")],
           e3c_pins,
           None, True,
           "the 036 draft used the supremum under the name 'recoverable "
           "depth' and inferred spin independence from it"),
        cl("C02",
           "036 abstract: 'retarded-time diversity supplies more of that reach "
           "than spatial remapping ... the history is carried by when, not "
           "where, the orders sample'",
           "section 5.3: retained as index-paired counterfactuals; the "
           "mechanism sentence is withdrawn",
           "RETAINED_AS_COUNTERFACTUAL_MECHANISM_CLAIM_WITHDRAWN", D,
           [ev(c, E3CM, "delay and spatial substitution rows, 0.98 and 0.57")],
           e3c_pins,
           "an experiment that co-registers delay and spatial remapping rather "
           "than transplanting arrays by index",
           False),
        cl("C03",
           "036 section 5.1: 'source enrichment destroys identifiability' and "
           "'compact support makes the direct image blind'",
           "section 4, Proposition 4.1 with proof and Corollary 4.2, both "
           "conditional on support disjointness",
           "REPLACED_BY_THE_CONDITIONAL_THEOREM", S,
           [ev(c, "docs/revisions/mahakal_v4_1/review037/"
                  "REPLACEMENT_PASSAGES_037.md",
               "Proposition (sampled support-nullity) and its proof")],
           {**e3c_pins,
            "evaluation_metric": NA("a theorem, not a measured quantity"),
            "covariance": NA("a statement about the transfer map, independent "
                             "of the noise model"),
            "noise_normalisation": NA("as above")},
           None, True,
           "the slogan is universal; the theorem is conditional"),
        cl("C04",
           "036 section 5.3: 'the surviving directions have 99.8% of squared "
           "weight in temporal hat 2 ... exactly zero in hat 0'",
           "section 6.3: 2.44%/2.35% oldest third, 43.81%/43.92% middle, "
           "53.75%/53.73% youngest; the oldest-third contribution is not zero",
           "WITHDRAWN_AND_REPLACED_FROM_THE_PRIMARY_RECORD", D,
           [ev(c, LOC, "intervals[*].source_energy_fraction for oldest_third, "
                       "middle_third, youngest_third")],
           r2_pins,
           None, True,
           "the 99.8% figure grouped Cholesky-normalised coordinates and is "
           "not an energy fraction in a physical time interval"),
        cl("C05",
           "036 section 5.3: two operational directions",
           "section 6.2: two under the frozen legacy measure, with the "
           "one-to-two reweighting interval stated",
           "RETAINED_LEGACY_MEASURE_WITH_INTERVAL", D,
           [ev(c, R2CSV, "RESOLVED_PHYSICAL rows, n_operational_conditional, "
                         "all three rtol values"),
            ev(c, R2MD, "singular values and margins against rho = 1")],
           r2_pins,
           "a corrected-measure recomputation, not authorised", False),
        cl("C06",
           "036 abstract: 'on 640 truths ... stacking orders extends the "
           "anchored stable span from 48 to 80 M'",
           "section 7.1: 48 to 80 M in IN_CLASS_ID, IN_CLASS_OOD and the mild "
           "OFF_GRID_OOD diagnostic; OFF_GRID_ID remains 0 to 0 M",
           "CORRECTED_REGIMES_RESTORED", D,
           [ev(c, R1, "regime table rows IN_CLASS_ID, IN_CLASS_OOD, "
                      "OFF_GRID_ID, OFF_GRID_OOD")],
           r1_pins, None, True,
           "'640 truths' describes the bank, not uniform success"),
        cl("C07",
           "036 section 6.1: 'a coefficient-space result under the declared "
           "source norm'",
           "section 7.1: the registered baseline-inclusive field metric, level "
           "dominated with level fraction 0.9838",
           "CORRECTED_METRIC_IDENTITY", D,
           [ev(c, R1, "level/structure split table, level fraction of truth; "
                      "registered baseline-inclusive field metric")],
           r1_pins, None, True,
           "an estimator operating on coefficients does not determine what its "
           "evaluation loss measures"),
        cl("C08",
           "036 section 6.2: 'cleared at ten times the reference SNR'",
           "section 7.2: the structure-only stable span is zero at SNR_0 = 100 "
           "and first nonzero at 30000, with 40 M direct and 76 M resolved; "
           "R1L stage-2R at 1000 is a separate aggregate result",
           "CORRECTED_ONSET_AND_EXPERIMENT_SEPARATION", D,
           [ev(c, R1, "Structural recovery onset table, onset SNR_0 column"),
            ev(c, EVID, "R1L stage 2R section")],
           r1_pins, None, True),
        cl("C09",
           "036 abstract: 'reduces morphology error ... by 0.164 and 0.133, "
           "lower bounds 0.116 and 0.101'",
           "section 7.3, with estimators named, four paired draws, and the "
           "materiality criteria stated",
           "RETAINED_WITH_ESTIMATORS_AND_DRAWS_NAMED", D,
           [ev(c, EVID, "HMT-2 sealed main table, L896_radial_enriched / "
                        "RESOLVED_PHYSICAL / Ridge and TSVD rows")],
           hmt2_pins, None, True),
        cl("C10",
           "036 section 6.3: 'neither an unresolved second image nor total flux "
           "reaches materiality, so the gain is attributable to resolving the "
           "orders'",
           "section 7.3: the labelled-stack estimates improve; the tested flux "
           "readout does not reproduce the gain; the index-sum control does "
           "not establish how a physically unresolved image would perform",
           "CAUSAL_FRAMING_REMOVED", D,
           [ev(c, EVID, "HMT-2 sealed main table, UNRESOLVED_IMAGE and "
                        "TOTAL_FLUX control rows")],
           hmt2_pins,
           "a comparison against an appropriate physical control", False),
        cl("C11",
           "036 section 6.4 qualifications",
           "section 7.4, with the L448_contrast TSVD non-material row named "
           "and the posterior calibration failure preserved",
           "RETAINED_AND_EXPANDED", D,
           [ev(c, EVID, "HMT-2 sealed main table, L448_contrast rows; "
                        "Preserved literal failures section")],
           hmt2_pins, None, True),
        cl("C12",
           "036 section 8.2 detector-response error",
           "section 8: 9.594e-03, 4.274e-02, 5.116e-01, described as a "
           "discrepancy between two discretisations rather than a continuum "
           "error",
           "RETAINED_WITH_SCOPE_CORRECTED", D,
           [ev(c, Q035, "per_order.nX.baseline.max_relative_E and "
                        "node_coverage, area_coverage, omitted_area")],
           d026_pins, None, True),
        cl("C13",
           "036 section 7: hull qualified at 9.592e-08",
           "section 8: the tessellation component at 9.592e-08, not the entire "
           "hull error",
           "SCOPE_NARROWED", D,
           [ev(c, G1C, "closeout tessellation metric")],
           {**d026_pins,
            "covariance": NA("a geometric qualification; no noise model"),
            "noise_normalisation": NA("as above"),
            "source_basis": NA("a hull boundary, not a source representation")},
           None, True),
        cl("C14",
           "036 section 7: comparator validated",
           "section 8: validated on 66 development and 192 confirmation IDs "
           "with bounded independence",
           "RETAINED_COHORT_SCOPE", D,
           [ev(c, N033, "development.tally and confirmation.tally")],
           {**d026_pins,
            "evaluation_metric": R("label agreement between the primary and "
                                   "two references, with zero forced labels",
                                   N033)},
           None, False),
        cl("C15",
           "036 abstract: 'a sixteen-month numerical audit'",
           "removed; no duration is asserted anywhere",
           "REMOVED_UNSUPPORTED", D,
           [ev(c, "docs/revisions/mahakal_v4_1/PAPER_I_MANUSCRIPT_REVIEW_037.md",
               "unsupported_sixteen_month_duration disposition")],
           {k: NA("an editorial removal; no experiment is cited") for k in PINS},
           None, False),
        cl("C16",
           "036 title: the long Shiva-effect title",
           "the author-facing title 'Photon-Ring Retarded-Time Tomography: The "
           "Mahakal Phenomenon'",
           "TITLE_RECONCILED", D,
           [ev(c, "docs/revisions/mahakal_v4_1/NEXT_STAGE_037.yaml",
               "source_reconciliation.author_facing_title")],
           {k: NA("an editorial reconciliation; no experiment is cited")
            for k in PINS},
           "the supplied 42-page PDF was not available to this session, so "
           "repository and uploaded document identities are recorded "
           "separately and only the reviewer's recorded hash is carried",
           False),
    ]


def main() -> int:
    t0 = time.time()
    OUT.mkdir(parents=True, exist_ok=True)
    c = head()
    claims = build(c)
    unreadable = [(cl["claim_id"], e["path"]) for cl in claims
                  for e in cl["evidence"] if e.get("unreadable")]
    matrix = {
        "ruling": "PAPER_I_MANUSCRIPT_REVIEW_037",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "commit": c, "pins": list(PINS),
        "per_experiment_pins": True,
        "global_single_sky_pin_for_all_experiments": False,
        "hash_pass_is_semantic_validation": False,
        "claims": claims, "n_claims": len(claims),
        "unreadable_evidence": unreadable,
        "seed_index": "artifacts/manuscript/CLAIM_LEDGER.json (276 entries) "
                      "used as an index; every claim here is resolved to its "
                      "own primary artifact and later amendments applied",
    }
    (OUT / "CLAIM_EVIDENCE_MATRIX_037.json").write_text(
        json.dumps(matrix, indent=2) + "\n")
    print(json.dumps({"claims": len(claims), "unreadable": unreadable,
                      "headline": sum(
                          1 for x in claims
                          if x["candidate_abstract_or_headline_allowed"]),
                      "seconds": round(time.time() - t0, 1)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
