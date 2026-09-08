#!/usr/bin/env python3
"""Ruling 039: emit the publication-candidate record set.

Document work. Every value here is copied from an artifact already on disk or
from the 038 matrix this revision supersedes; nothing is recomputed from a
physical model, and no default is substituted for a missing execution input.
The two method dependencies the review resolved from source are promoted here,
and the one that is still unlocated stays unlocated -- linked to the claims it
affects rather than buried in an appendix.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs/revisions/mahakal_v4_1/manuscript039"
PREV = ROOT / "docs/revisions/mahakal_v4_1/manuscript038"
RULING = "PAPER_I_FINAL_TEXT_REVIEW_039"
STEM = "Photon_Ring_Retarded_Time_Tomography_Candidate_039"

R1_EXEC = "5f557fb606b76a95093cbf8e98d89d6f1dab9664"
HMT2_EXEC = "9713af2caf3f1035622b09c8026ea31f75c0275e"
ETA_STATUS = "REALIZED_ETA_NOT_LOCATED"
ETA_CLAIMS = ["C06", "C07", "C08", "C21"]


def sha(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def head() -> str:
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                          capture_output=True, text=True).stdout.strip()


def utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


# --------------------------------------------------------------- dependencies

def method_dependency_status(commit: str) -> dict:
    return {
        "ruling": RULING,
        "generated_utc": utc(),
        "commit": commit,
        "document": f"docs/revisions/mahakal_v4_1/manuscript039/{STEM}.md",
        "rule": ("a method formula can be source-resolved while one realized "
                 "scalar remains unlocated; a schema pass does not close an "
                 "unresolved execution input, and a count of unresolved pins "
                 "is not an inventory of scientific dependencies"),
        "dependencies": [
            {
                "id": "R1_EVALUATION_GRID",
                "status": "SOURCE_RESOLVED",
                "resolved_in": RULING,
                "what": "shape and axes of the fixed R1 source evaluation grid",
                "value": {"shape": [10, 12, 40], "point_count": 4800,
                          "radial_bounds_M": [1.8660386527060988,
                                              49.98205255591607],
                          "azimuth": "[0, 2pi), endpoint excluded, 12 points",
                          "source_time_bounds_M": [-128.82234649196255, 29.0],
                          "axes": "log radius inclusive; uniform azimuth "
                                  "endpoint-excluded; uniform time inclusive",
                          "flatten": "meshgrid(indexing='ij') then C order"},
                "evidence": {
                    "execution_commit": R1_EXEC,
                    "caller": "scripts/run_r1_main.py",
                    "caller_git_blob":
                        "291adbf720007a300000ea570e6acbfceaacd3e1",
                    "callee": "src/phrt/metrics/scoring.py",
                    "callee_git_blob":
                        "0b04245c73ac80d63e3a6b8c2d2e67c2fef17dbc",
                    "call_size_overrides": "none",
                    "manifest":
                        "artifacts/manifests/R1_20260826T022951Z_2ba66f02.json",
                },
                "provenance_class":
                    "source-resolved definition; no independent hash of a "
                    "persisted evaluation-array payload is claimed",
                "document_location": "Appendix A.1",
                "affected_claims": ["C06", "C07", "C08", "C21"],
            },
            {
                "id": "HMT2_PAIRED_REDUCTION_AGGREGATION_ORDER",
                "status": "SOURCE_RESOLVED",
                "resolved_in": RULING,
                "what": "the order of aggregation in the paired reduction and "
                        "the interval convention of the declared headline",
                "value": {
                    "order": "mean over declared ages within a draw, then mean "
                             "over the four draws within a history, then a "
                             "paired direct-relative reduction per history, "
                             "then the median across histories",
                    "ratio": "(ebar_direct - ebar_arm) / "
                             "max(|ebar_direct|, 1e-300)",
                    "headline_fields": ["median", "median_ci_low"],
                    "separate_estimand_not_used": "cell/family-balanced mean",
                    "bootstrap_unit": "history, with its four draws already "
                                      "inside its score",
                    "median_bootstrap_resamples": 10000,
                    "median_bootstrap_seed": 20260954,
                    "seed_derivation": "HMT2 bank seed 20260953 plus one",
                    "interval_percentiles": [2.5, 97.5],
                },
                "evidence": {
                    "execution_commit": HMT2_EXEC,
                    "blobs": {
                        "scripts/run_hmt2_sealed_main.py":
                            "0e65135fa2f4bfb83e36c7f65b23d4ef8c62704d",
                        "scripts/run_hmt2_sealed_main_score.py":
                            "3b1f5f983a9204b856bbabcbd446dc629c9dc01f",
                        "scripts/run_hmt1_score.py":
                            "03f13ef1a2c1e47807f125feaf4785f871df0fda",
                    },
                    "manifest": "artifacts/manifests/"
                                "HMT2M_20260828T064757Z_2ba66f02.json",
                },
                "not_established_here":
                    "the reported main pair count of 60 was not independently "
                    "recomputed from the stored arrays; no missing-pair claim "
                    "is made in either direction",
                "document_location": "Appendix A.2",
                "affected_claims": ["C09", "C11", "C20", "C22"],
            },
            {
                "id": "R1_REALIZED_ETA",
                "status": ETA_STATUS,
                "rule_status": "SOURCE_RESOLVED",
                "what": "the realized numerical value of the common metric "
                        "floor eta used by the R1 sealed main",
                "rule": "0.05 times the median, over prior-fit truths and ages "
                        "with ||W_a x|| > 0, of ||W_a x||_2; frozen before "
                        "scoring; common to all truths; not taken from the "
                        "test set",
                "searched_and_not_found": [
                    {"where": "artifacts/configs/R1_MAIN_FREEZE.json",
                     "field": "metrics.eta_value", "found": None},
                    {"where": "artifacts/configs/"
                              "R0C_REPAIRED_SOURCE_AND_CALIBRATION_FREEZE.json",
                     "field": "metrics.eta_value", "found": None},
                    {"where": "artifacts/manifests/"
                              "R1_20260826T022951Z_2ba66f02.json",
                     "field": "any eta field", "found": None},
                    {"where": "saved stdout, run sidecars and log files under "
                              "artifacts/",
                     "field": "the runner's printed '%.6g' eta",
                     "found": None,
                     "note": "the runner holds eta only in an in-process dict "
                             "and prints it; no capture of that stream is "
                             "stored in the repository"},
                    {"where": "artifacts/tables/r1_age_errors.parquet",
                     "field": "derived readback from saved errors",
                     "found": None,
                     "note": "the table stores median_normalized_error and "
                             "median_absolute_error as separate medians over "
                             "the truth/draw population; the quotient of two "
                             "independent medians is not the per-row "
                             "denominator, so eta cannot be recovered from it"},
                    {"where": "cached prior-fit windowed norms",
                     "field": "the inputs to the registered rule",
                     "found": None,
                     "note": "not cached; regenerating them would be truth "
                             "generation, which this ruling forbids"},
                ],
                "not_asserted": "that no copy exists anywhere in the archive; "
                                "this is the result of a bounded search of the "
                                "inspected records",
                "consequence": "exact reproducibility of the R1 normalisation "
                               "is limited. The archived benchmark values are "
                               "unchanged: they were computed with the frozen "
                               "scalar, and the floor binds only where the "
                               "windowed truth norm falls below it",
                "document_location": "section 9 item 4 and Appendix A.1",
                "affected_claims": ETA_CLAIMS,
                "closed_by": "a genuine recorded value, or an authorized "
                             "recomputation of the prior-fit norms",
            },
        ],
        "unresolved_count": 1,
        "unresolved_count_is_not_a_full_dependency_inventory": True,
        "deferred_physical_workstreams": [
            {"id": "TRANSFER_QUADRATURE_QUALIFICATION",
             "status": "NOT_QUALIFIED",
             "blocks": "any continuum-acquisition accuracy claim",
             "blocks_this_candidate": False,
             "why": "the candidate makes no qualified continuum claim"},
            {"id": "PHYSICAL_ORDER_RESOLUTION_CONTROL",
             "status": "NOT_PERFORMED",
             "blocks": "any physical order-resolution attribution",
             "blocks_this_candidate": False,
             "why": "the candidate makes no such attribution and labels the "
                    "index-sum arm a compression control"},
        ],
    }


# ---------------------------------------------------------------- bibliography

BIB = [
    ("GL2020", "S. E. Gralla and A. Lupsasca",
     "Lensing by Kerr Black Holes", "arXiv:1910.12873v2",
     "Phys. Rev. D 101, 044031 (2020)", "10.1103/PhysRevD.101.044031",
     "the highly bent Kerr-image hierarchy has demagnification, rotation and "
     "relative-delay structure",
     "METADATA_AND_ABSTRACT_VERIFIED"),
    ("J2020", "M. D. Johnson et al.",
     "Universal Interferometric Signatures of a Black Hole's Photon Ring",
     "arXiv:1907.04329v2", "Science Advances 6, eaaz1310 (2020)",
     "10.1126/sciadv.aaz1310",
     "photon subrings have characteristic long-baseline interferometric "
     "signatures", "METADATA_AND_ABSTRACT_VERIFIED"),
    ("AART2023", "A. Cardenas-Avendano, A. Lupsasca and H. Zhu",
     "Adaptive Analytical Ray Tracing of Black Hole Photon Rings",
     "arXiv:2211.07469v4", "Phys. Rev. D 107, 043030 (2023)",
     "10.1103/PhysRevD.107.043030",
     "the analytic Kerr ray-tracing framework with adaptive image sampling "
     "underlying the archived maps", "METADATA_AND_ABSTRACT_VERIFIED"),
    ("H2021", "S. Hadar, M. D. Johnson, A. Lupsasca and G. N. Wong",
     "Photon Ring Autocorrelations", "arXiv:2010.03683v3",
     "Phys. Rev. D 103, 104038 (2021)", "10.1103/PhysRevD.103.104038",
     "a photon-ring intensity-correlation observable for stochastic equatorial "
     "emission whose structure contains lens and source information",
     "METADATA_AND_ABSTRACT_VERIFIED"),
    ("T2020", "P. Tiede, H.-Y. Pu, A. E. Broderick, R. Gold, M. Karami and "
     "J. A. Preciado-Lopez",
     "Spacetime Tomography Using The Event Horizon Telescope",
     "arXiv:2002.05735v2", None, "10.3847/1538-4357/ab744c",
     "related tomography work using a constrained hotspot model in simulated "
     "recovery and spacetime inference",
     "ARXIV_IDENTITY_ABSTRACT_AND_LINKED_DOI_VERIFIED_JOURNAL_PAGINATION_NOT"),
    ("B2018", "K. L. Bouman, M. D. Johnson, A. V. Dalca, A. A. Chael, "
     "F. Roelofs, S. S. Doeleman and W. T. Freeman",
     "Reconstructing Video from Interferometric Measurements of Time-Varying "
     "Sources", "arXiv:1711.01357v2", None, None,
     "related dynamic VLBI imaging of evolving sources under a Gaussian Markov "
     "model", "ARXIV_IDENTITY_AND_ABSTRACT_VERIFIED_JOURNAL_METADATA_NOT"),
    ("L2024", "A. Levis, A. A. Chael, K. L. Bouman, M. Wielgus and "
     "P. P. Srinivasan",
     "Orbital Polarimetric Tomography of a Flare Near the Sagittarius A* "
     "Supermassive Black Hole", "arXiv:2310.07687v2", None, None,
     "model-dependent 3-D flare-emission reconstruction combining a neural "
     "representation with a gravitational model",
     "ARXIV_IDENTITY_AND_ABSTRACT_VERIFIED_JOURNAL_METADATA_NOT"),
]


def bibliography(commit: str) -> dict:
    return {
        "ruling": RULING,
        "generated_utc": utc(),
        "commit": commit,
        "audit_source":
            "docs/revisions/mahakal_v4_1/review039/CORE_BIBLIOGRAPHY_AUDIT_039.md",
        "audit_scope": "seven primary arXiv records, metadata and "
                       "author-posted abstracts",
        "full_text_read": False,
        "all_archived_references_audited": False,
        "systematic_novelty_survey_performed": False,
        "rule": "a citation may support only what the verified level of that "
                "entry supports; a stronger claim needs the relevant full text",
        "entries": [
            {"key": k, "authors": a, "title": t, "arxiv": x,
             "journal": j, "doi": d, "narrow_supported_use": u,
             "verification_level": v,
             "cited_in": "section 1.2 and section 11"}
            for k, a, t, x, j, d, u, v in BIB
        ],
        "pages_opened": [
            "https://arxiv.org/abs/1910.12873",
            "https://arxiv.org/abs/1907.04329",
            "https://arxiv.org/abs/2211.07469",
            "https://arxiv.org/abs/2010.03683",
            "https://arxiv.org/abs/2002.05735",
            "https://arxiv.org/abs/1711.01357",
            "https://arxiv.org/abs/2310.07687",
        ],
        "claims_resting_on_this_audit": [
            "the background paragraph in section 1.2",
        ],
        "claims_not_resting_on_this_audit": [
            "every numerical result in sections 5 to 8",
            "any novelty or priority statement -- none is made",
        ],
        "outstanding": [
            "the remaining entries of the archived manuscript's older "
            "reference list have not been re-audited against this text",
            "journal volume and pagination for T2020, B2018 and L2024",
            "a full-text reading for any citation used more strongly than the "
            "narrow use recorded above",
        ],
    }


# ----------------------------------------------------------------- claim matrix

def claim_matrix(commit: str) -> dict:
    prev = json.loads((PREV / "CLAIM_EVIDENCE_MATRIX_038.json").read_text())
    claims = prev["claims"]
    by_id = {c["claim_id"]: c for c in claims}

    for c in claims:
        c["document_version"] = f"manuscript039/{STEM}.md"
        c["carried_from"] = "CLAIM_EVIDENCE_MATRIX_038.json"

    # the two method claims the review resolved from archived source
    c21 = by_id["C21"]
    c21["revised_text_and_location"] = (
        "Appendix A.1: the baseline-inclusive field metric, its normalised "
        "Gaussian window (h = 3 M), its quadratic-form implementation, and the "
        "source-resolved 10 x 12 x 40 = 4,800-point evaluation grid with its "
        "declared axes and flattening order")
    c21["disposition"] = "METHOD_DEFINITION_GRID_RESOLVED_ETA_STILL_UNLOCATED"
    c21["unresolved_scientific_dependency"] = (
        "the realized eta scalar; the evaluation-grid shape is now resolved "
        "from the archived caller and callee at execution commit 5f557fb6")
    c21["method_dependency_refs"] = ["R1_EVALUATION_GRID", "R1_REALIZED_ETA"]

    c22 = by_id["C22"]
    c22["revised_text_and_location"] = (
        "Appendix A.2: the state-dependent morphology error and the paired "
        "reduction -- mean over ages within a draw, mean over the four draws "
        "within a history, paired direct-relative reduction per history, "
        "median across histories, with a 10,000-resample history bootstrap at "
        "helper seed 20260954")
    c22["disposition"] = "METHOD_DEFINITION_AGGREGATION_ORDER_RESOLVED"
    c22["unresolved_scientific_dependency"] = None
    c22["method_dependency_refs"] = [
        "HMT2_PAIRED_REDUCTION_AGGREGATION_ORDER"]

    for cid in ETA_CLAIMS:
        by_id[cid]["affected_by_unresolved_method_input"] = {
            "id": "R1_REALIZED_ETA", "status": ETA_STATUS,
            "effect": "limits exact reproducibility of the R1 normalisation; "
                      "does not change the archived benchmark values"}

    # softened per the review: wide intervals do not forbid reporting the
    # measured family-level point estimates
    by_id["C11"]["revised_text_and_location"] = (
        "section 7.4: 5 of 12 family-estimator cells material on the physical "
        "end-to-end target, 4 of 12 on both; circular_hotspot_trajectory "
        "negative under both estimators; the measured point estimates and "
        "intervals are reported as measured, while no strong universal "
        "family claim follows in either direction")

    def ev(path, selector):
        return [{"commit": commit, "path": path, "sha256": sha(ROOT / path),
                 "selector": selector}]

    new = [
        {
            "claim_id": "C23",
            "original_document_identity":
                "manuscript038 section 3 (source-space table only)",
            "original_exact_text_and_location":
                "038 section 3 left C224/L224 as unexplained identifiers and "
                "named a reference SNR without an observation schedule",
            "revised_text_and_location":
                "section 3.1: C224 is 4 x 7 x 8 = 224 -- four cubic B-splines "
                "in log r, seven real Fourier modes (|m| <= 3), eight DCT "
                "modes in source time, radial-major ordering -- on r in "
                "[1.8660386527060988, 49.98205255591607] M and t in "
                "[-128.82234649196255, 29.0] M; the reference observer "
                "schedule is eight samples uniformly spaced 0 to 20 M with "
                "1536 retained rays per order at n = 0, 1, 2; the localized "
                "L-classes keep their own temporal definition",
            "disposition": "EXPOSITION_COMPLETED_FROM_THE_EXECUTED_FREEZE",
            "evidence_level": "SOURCE_RESOLVED_DEFINITION",
            "evidence": ev("artifacts/configs/R1_MAIN_FREEZE.json",
                           "source_class.*, observation.*"),
            "pins": {"source_basis": {"status": "RESOLVED",
                                      "value": "C224 = 4 x 7 x 8",
                                      "evidence_ref":
                                          "artifacts/configs/R1_MAIN_FREEZE.json"}},
            "unresolved_scientific_dependency": None,
            "candidate_abstract_or_headline_allowed": False,
            "note": "a definition, not a new source class",
        },
        {
            "claim_id": "C24",
            "original_document_identity": "manuscript038 sections 3 and 5",
            "original_exact_text_and_location":
                "038 gave the age-threshold detectability masks and a "
                "reference SNR without the probe function, its normalisation "
                "or the threshold rule",
            "revised_text_and_location":
                "section 3.2: the localized probe is Gaussian in retarded age "
                "and flat in the emission annulus with half width h = 3.0 M, "
                "normalised to unit L2 norm over the emission region; "
                "detectability is sup { a : SNR_0^2 I(a) >= rho^2 } with "
                "rho = 1, on the operator scaled to the reference SNR, with "
                "one noise density sigma_Omega fixed from the direct arm's "
                "clean response and no arm-specific sigma",
            "disposition": "EXPOSITION_COMPLETED_FROM_THE_EXECUTED_FREEZE",
            "evidence_level": "SOURCE_RESOLVED_DEFINITION",
            "evidence": ev("artifacts/configs/E3C_OPERATOR_GRID_FREEZE.json",
                           "localized_probe.*, depth_contract.*, "
                           "measurement_model.*, rank_conventions.*"),
            "pins": {"evaluation_metric": {"status": "RESOLVED",
                                           "value": "age_threshold_mask at "
                                                    "rho = 1",
                                           "evidence_ref":
                                               "artifacts/configs/"
                                               "E3C_OPERATOR_GRID_FREEZE.json"}},
            "unresolved_scientific_dependency": None,
            "candidate_abstract_or_headline_allowed": False,
        },
        {
            "claim_id": "C25",
            "original_document_identity": "manuscript038 section 3",
            "original_exact_text_and_location":
                "038 section 3: 'TSVD and ridge ... tuned on the R0C "
                "repair-validation bank and frozen before any main-test "
                "truth', stated once for every recovery program",
            "revised_text_and_location":
                "section 3.3: R1 reuses its R0C validation-selected "
                "hyperparameters; HMT-2 reuses its own stage-1 selection, "
                "inherited unchanged through the sealed-main freeze whose "
                "runner performs no sweep; neither main experiment tunes on "
                "its held-out bank",
            "disposition": "PROVENANCE_OVERGENERALIZATION_CORRECTED",
            "evidence_level": "SOURCE_RESOLVED_DEFINITION",
            "evidence": (ev("artifacts/configs/R1_MAIN_FREEZE.json",
                            "estimators.hyperparameters")
                         + ev("artifacts/configs/HMT2_SEALED_MAIN_V1.json",
                              "sealed_hyperparameters.*, "
                              "gates.HMT2M_G11_sealed_hyperparameters_used_"
                              "unchanged")),
            "pins": {"estimator": {"status": "RESOLVED",
                                   "value": "TSVD and RIDGE_IDENTITY, "
                                            "per-experiment selection lineage",
                                   "evidence_ref":
                                       "artifacts/configs/"
                                       "HMT2_SEALED_MAIN_V1.json"}},
            "unresolved_scientific_dependency": None,
            "candidate_abstract_or_headline_allowed": False,
            "note": "no estimator and no selected hyperparameter changed",
        },
        {
            "claim_id": "C26",
            "original_document_identity": "manuscript038 section 3 table",
            "original_exact_text_and_location":
                "038 section 3, HMT-2 noise-convention cell: 'four paired "
                "noise draws per truth' -- a replication count in a noise "
                "column",
            "revised_text_and_location":
                "section 3: one standard-normal tensor of shape (orders, "
                "rays, observer times) per truth and draw, mapped to "
                "sigma_Omega sqrt(dOmega) z on each order's pixels and then "
                "through each arm's declared readout, whitened by the channel "
                "variance; the four paired draws are stated as replication",
            "disposition": "NOISE_CONVENTION_CELL_CORRECTED",
            "evidence_level": "SOURCE_RESOLVED_DEFINITION",
            "evidence": ev("src/phrt/operators/physical.py",
                           "PhysicalOperator.noise_from_standard"),
            "pins": {"noise_normalisation": {"status": "RESOLVED",
                                             "value": "shared standard-normal "
                                                      "draw through each arm's "
                                                      "linear readout",
                                             "evidence_ref":
                                                 "src/phrt/operators/"
                                                 "physical.py"}},
            "unresolved_scientific_dependency": None,
            "candidate_abstract_or_headline_allowed": False,
            "note": "a consistency edit, not a new noise model",
        },
        {
            "claim_id": "C27",
            "original_document_identity":
                "artifacts/manuscript/figures/fig1_depth_inclination_not_spin.png "
                "and artifacts/manuscript/figures/fig2_shiva_effect.png",
            "original_exact_text_and_location":
                "the canonical assets asserted 'recoverable depth ... flat "
                "across four spins' and 'enriching the declared temporal "
                "class' in their own in-figure titles",
            "revised_text_and_location":
                "figures 1 and 2, regenerated to new filenames under "
                "manuscript039/figures with corrected in-figure titles, axis "
                "labels and panels",
            "disposition": "FIGURE_ASSETS_REGENERATED_CANONICAL_UNTOUCHED",
            "evidence_level": "REPRODUCED_DISCRETE_BENCHMARK",
            "evidence": (ev("artifacts/tables/e3c_depth_curves.parquet",
                            "snr0 == 100, arm in (DIRECT_PHYSICAL, "
                            "RESOLVED_PHYSICAL), median over source_class")
                         + ev("artifacts/tables/e3d_class_spectra.parquet",
                              "arm == RESOLVED_PHYSICAL, median over the 12 "
                              "geometries by source_class")
                         + ev("artifacts/tables/e3d_depth_by_class.parquet",
                              "snr0 == 100, arm in (DIRECT_PHYSICAL, "
                              "RESOLVED_PHYSICAL), median over geometries")),
            "pins": {"evaluation_metric": {"status": "RESOLVED",
                                           "value": "archived table columns, "
                                                    "selected and aggregated "
                                                    "only",
                                           "evidence_ref":
                                               "FIGURE_MANIFEST_039.json"}},
            "unresolved_scientific_dependency": None,
            "candidate_abstract_or_headline_allowed": False,
            "note": "no operator, reconstruction or new sampling is invoked "
                    "inside the figure builder",
        },
        {
            "claim_id": "C28",
            "original_document_identity": "manuscript038 references section",
            "original_exact_text_and_location":
                "038: 'A full external bibliography is outstanding ... no "
                "reference is carried over unread'",
            "revised_text_and_location":
                "section 1.2 and section 11: seven primary arXiv records "
                "verified at metadata and abstract level, each cited only for "
                "the narrow background use its verified level supports, with "
                "the unverified journal fields named",
            "disposition": "EXTERNAL_AUDIT_STARTED_SCOPE_STATED",
            "evidence_level": "EXTERNAL_METADATA_AND_ABSTRACT",
            "evidence": ev("docs/revisions/mahakal_v4_1/review039/"
                           "CORE_BIBLIOGRAPHY_AUDIT_039.md",
                           "the seven-entry verification table"),
            "pins": {},
            "unresolved_scientific_dependency":
                "full-text verification for any stronger use, and the "
                "remaining archived references",
            "candidate_abstract_or_headline_allowed": False,
            "note": "no novelty or priority claim rests on this audit",
        },
    ]
    claims = claims + new
    return {
        "ruling": RULING,
        "generated_utc": utc(),
        "commit": commit,
        "document": f"docs/revisions/mahakal_v4_1/manuscript039/{STEM}.md",
        "supersedes": "CLAIM_EVIDENCE_MATRIX_038.json",
        "pins": prev["pins"],
        "per_experiment_pins": True,
        "global_single_sky_pin_for_all_experiments": False,
        "hash_pass_is_semantic_validation": False,
        "schema_pass_closes_an_unresolved_execution_input": False,
        "claims": claims,
        "n_claims": len(claims),
        "claims_affected_by_unresolved_eta": ETA_CLAIMS,
        "unreadable_evidence": [],
        "seed_index": prev["seed_index"],
    }


# -------------------------------------------------------------- input manifest

CITED = [
    "artifacts/configs/E3C_OPERATOR_GRID_FREEZE.json",
    "artifacts/configs/HMT2_SEALED_MAIN_V1.json",
    "artifacts/configs/R1_MAIN_FREEZE.json",
    "artifacts/reports/E3C_GEOMETRY_WIDE_OPERATOR_AUDIT.md",
    "artifacts/reports/E3C_MECHANISM_DECOMPOSITION.md",
    "artifacts/reports/E3D_SOURCE_CLASS_STRESS.md",
    "artifacts/reports/R1_HELD_OUT_MAIN.md",
    "artifacts/revisions/mahakal_v4_1/LOC025_20260906T184213Z/"
    "LOCALIZATION_READBACK.json",
    "artifacts/revisions/mahakal_v4_1/Q035_20260908T004247Z_c1bf640/"
    "PER_CHANNEL_RESPONSE_AND_SUPPORT_035.json",
    "artifacts/revisions/mahakal_v4_1/R2REPLAY_20260906T144528Z_b873908/"
    "R2_CLOSEOUT_REPORT.md",
    "artifacts/tables/e3c_depth_curves.parquet",
    "artifacts/tables/e3d_class_spectra.parquet",
    "artifacts/tables/e3d_depth_by_class.parquet",
    "docs/Paper_I_v1_Current_Evidence_Ledger.md",
    "docs/revisions/mahakal_v4_1/NEXT_STAGE_039.yaml",
    "docs/revisions/mahakal_v4_1/PAPER_I_FINAL_TEXT_REVIEW_039.md",
    "docs/revisions/mahakal_v4_1/review039/CORE_BIBLIOGRAPHY_AUDIT_039.md",
    "docs/revisions/mahakal_v4_1/review039/METHOD_DEPENDENCY_CLOSEOUT_039.md",
    "docs/revisions/mahakal_v4_1/manuscript038/"
    "Photon_Ring_Retarded_Time_Tomography_Working_Revision_038.md",
    "docs/revisions/mahakal_v4_1/manuscript038/CLAIM_EVIDENCE_MATRIX_038.json",
    "src/phrt/manuscript/render.py",
    "src/phrt/metrics/morphology.py",
    "src/phrt/metrics/scoring.py",
    "src/phrt/operators/physical.py",
]


def input_manifest(commit: str) -> dict:
    return {
        "ruling": RULING,
        "generated_utc": utc(),
        "commit": commit,
        "document": f"docs/revisions/mahakal_v4_1/manuscript039/{STEM}.md",
        "new_rays": 0,
        "new_path_integrals": 0,
        "new_hull_roots": 0,
        "new_operator_spectra_estimators_truths_or_interpolants": 0,
        "convention_B_units_spent_this_stage": 0,
        "convention_B_second_batch_spent": 19146,
        "convention_B_second_batch_remaining": 854,
        "boundary_spent": 33410,
        "cited_artifacts": {p: sha(ROOT / p) for p in CITED},
        "missing_artifacts": [],
        "figure_builder": "scripts/revision_v4_1/u0_figures_039.py",
        "renderer_driver": "scripts/revision_v4_1/u1_render_039.py",
        "record_builder": "scripts/revision_v4_1/u2_package_039.py",
        "shared_renderer_modified": False,
        "canonical_figures_overwritten": False,
        "pinned_manuscripts_overwritten": False,
        "manuscripts_036_037_038_unchanged": True,
        "supplied_PDF": {
            "sha256": "152b099fc09994e917f629bda90de19bfd388ee19e96f754a0dfc4b"
                      "763e61148",
            "pages": 42,
            "available_to_this_session": False,
            "reference_extract": "docs/revisions/mahakal_v4_1/review038/"
                                 "SOURCE_PDF_BIBLIOGRAPHY_038.txt",
            "extract_is_verified_bibliography": False,
        },
    }


def main() -> int:
    commit = head()
    for name, obj in (
            ("METHOD_DEPENDENCY_STATUS_039.json",
             method_dependency_status(commit)),
            ("BIBLIOGRAPHY_VERIFICATION_039.json", bibliography(commit)),
            ("CLAIM_EVIDENCE_MATRIX_039.json", claim_matrix(commit)),
            ("PUBLICATION_039_INPUT_MANIFEST.json", input_manifest(commit))):
        (DOC / name).write_text(json.dumps(obj, indent=2) + "\n")
        print(name, sha(DOC / name)[:16])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
