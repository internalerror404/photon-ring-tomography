# MANUSCRIPT_CORRECTION_LEDGER_039

What ruling 039 asked for, what the candidate does, and — because the main text
is no longer to read as a transcript of its own editorial history — the record
of every passage withdrawn along the way. Replacement values are read from the
primary artifact named in `CLAIM_EVIDENCE_MATRIX_039.json`, never from an
earlier draft's prose. That was the 037 failure mode and it is not repeated:
the ancestor of this text is manuscript038 plus the primary records, not
`artifacts/manuscript/PAPER_I.md`.

## 1. Corrections made in this revision

| id | ruling 039 found | the 039 candidate does | source |
| --- | --- | --- | --- |
| E01 | Appendix A.1 carried the evaluation-grid shape as an unresolved dependency | states the source-resolved grid: 10 x 12 x 40 = 4,800 points, log-spaced radii over [1.8660386527060988, 49.98205255591607] M inclusive, 12 azimuths over [0, 2pi) endpoint-excluded, 40 uniform source times over [-128.82234649196255, 29.0] M inclusive, `meshgrid(indexing="ij")` then C-order flatten | `scripts/run_r1_main.py` blob `291adbf7` and `src/phrt/metrics/scoring.py` blob `0b04245c` at execution commit `5f557fb6` |
| E02 | Appendix A.2 carried the paired-reduction aggregation order as an untraced function body | states the full chain: mean over ages within a draw, mean over the four draws within a history, paired direct-relative reduction per history, median across histories; 10,000-resample history bootstrap at helper seed 20260954, 2.5/97.5 percentiles; the cell-balanced mean named as a separate estimand | `run_hmt2_sealed_main.py` `0e65135f`, `run_hmt2_sealed_main_score.py` `3b1f5f98`, `run_hmt1_score.py` `03f13ef1` at execution commit `9713af2c` |
| E03 | section 3 attributed the recovery estimators' tuning to R0C globally | section 3.3 splits the lineage: R1 reuses its R0C validation selection; HMT-2 reuses its own stage-1 selection through the sealed-main freeze, whose runner performs no sweep | `R1_MAIN_FREEZE.json` `estimators.hyperparameters`; `HMT2_SEALED_MAIN_V1.json` sealed hyperparameters and gate G11 |
| E04 | the HMT-2 noise-convention cell held a draw count | the cell now states the readout law — one standard-normal (orders, rays, observer times) tensor per truth and draw, mapped to `sigma_Omega sqrt(dOmega) z` on each order's pixels and through each arm's declared readout, whitened by the channel variance — and replication is stated separately | `src/phrt/operators/physical.py`, `noise_from_standard` |
| E05 | the opening and section 11 linked `CLAIM_EVIDENCE_MATRIX_037.json` | every internal reference names this revision's records; the matrix, manifest, draft and completion report identify one document version | this revision |
| E06 | the support caveat asserted that nonzero columns *are not* independent | section 4 says a nonzero column *need not be* an independent output direction and *need not be* operationally recoverable — insufficiency, not impossibility. The theorem and its nonvanishing assumptions are unchanged | ruling 039 section 3 |
| E07 | `C224`/`L224` were unexplained identifiers and a reference SNR stood in for an observation definition | section 3.1 gives the class factorization, support and column order and the eight-sample 0–20 M observer schedule; section 3.2 gives the unit-`L2` age probe and the `sup { a : SNR_0^2 I(a) >= rho^2 }`, `rho = 1` detectability rule with the single fixed noise density | `R1_MAIN_FREEZE.json`; `E3C_OPERATOR_GRID_FREEZE.json` |
| E08 | the family-heterogeneity bullet turned wide intervals into "no family claim is supported in either direction" | the measured point estimates and intervals are reported as measured; what does not follow is a strong universal family claim | ruling 039 section 4 |
| E09 | the posterior-calibration failure was unscoped | scoped in section 7.4 to the R1 probabilistic estimator program — the state-space and Wiener branch at 0.497 against a frozen 0.5 floor — and explicitly not a posterior from TSVD or ridge | `R1_MAIN_FREEZE.json` `uncertainty.*` |
| E10 | the two figure assets asserted corrected claims in their own titles | figures 1 and 2 regenerated to new filenames with corrected in-figure titles, axis labels and panels; the canonical assets are untouched | `FIGURE_MANIFEST_039.json` |
| E11 | the bibliography was "not started" | seven primary arXiv records verified at metadata and abstract level, cited only for the narrow use each supports, with unverified journal fields named as unverified | `review039/CORE_BIBLIOGRAPHY_AUDIT_039.md`; `BIBLIOGRAPHY_VERIFICATION_039.json` |
| E12 | withdrawal boxes and review-token language ran through the main text | the surviving result is stated in the body; the withdrawal history lives in section 2 of this ledger | ruling 039 section 5 |

## 2. Withdrawal history, preserved out of the main text

Each entry is a statement that appeared in an earlier draft and does not appear
in the candidate. None is reinstated, and none is hidden: the record is here
because a paper is not obliged to read as a transcript of its own editing.

| withdrawn statement | first appeared | replaced by | withdrawn under |
| --- | --- | --- | --- |
| "median recoverable depth 60, 84 and 144 M ... a single value across four spins" | Shiva-era / 036 | the oldest detectable age probe, a supremum of a threshold mask, reported beside the anchor-connected span | ruling 037 |
| "reach is set by inclination rather than spin" | Shiva-era / 036 | a common oldest passing grid point across four spins does not establish spin independence; the anchor-connected quantities vary with spin at 75 degrees | ruling 037 |
| "the history is carried by *when*, not *where*, the orders sample" | Shiva-era / 036 | the 0.98 and 0.57 comparisons retained as index-paired counterfactuals with no mechanism claim | ruling 037, amendment 023 |
| "99.8% of squared weight in one temporal epoch, exactly zero in the oldest" | Shiva-era / 036 | 2.44%/2.35%, 43.81%/43.92%, 53.75%/53.73% across the three source-time thirds; the oldest third is not zero | ruling 037 |
| "source enrichment destroys identifiability"; "compactness makes the direct image blind" | Shiva-era / 036 | Proposition 4.1 with proof, conditional on support disjointness, plus Corollary 4.2 | ruling 037 |
| the level result described as "a coefficient-space result" | 036 | the registered baseline-inclusive field metric, level dominated at level fraction 0.9838 | ruling 037 |
| structure "cleared at ten times the reference SNR" | 036 | zero at `SNR_0 = 100`, first nonzero at 30000 with 40 M direct and 76 M resolved | ruling 037 |
| "the gain is attributable to resolving the orders" | Shiva-era / 036 | the labelled stack improves; the tested flux readout does not reproduce it; the index-sum control says nothing about a physically unresolved image | ruling 037 |
| "a sixteen-month numerical audit" | 036 | removed; no duration is asserted | ruling 037 |
| the four-endpoint interval called "the only valid form" | 036 | *a* valid enclosure for supplied intervals | ruling 037 |
| "prior-free estimators" | Shiva-era | non-Bayesian spectral estimators with validation-selected regularization | ruling 038 |
| "640 truths" read as uniform success | 036 | 640 describes the bank; severe off-grid mismatch remains 0 to 0 M | ruling 038 |
| a single global noise pin for every experiment | 036 matrix | a per-experiment table of source spaces, metrics, estimators and noise conventions | ruling 038 |
| "nonzero columns are not independent" | 038 | nonzero columns need not be independent or operationally recoverable | ruling 039 |
| "TSVD and ridge ... tuned on R0C", stated for every recovery program | 038 | per-experiment tuning lineage, R1 and HMT-2 stated separately | ruling 039 |
| the HMT-2 noise cell reading "four paired noise draws per truth" | 038 | the standard-normal readout law, with replication stated separately | ruling 039 |

## 3. What this revision deliberately did not touch

Under the preservation clause of ruling 039, none of the following was reopened
to polish the manuscript: the support statement of section 4, the saved R2
localization readback, the corrected reach semantics, the regime distinctions,
the accepted numerical hull, comparator and sampled-absence scopes, and the
closed negative composite-representation test. C13 remains unqualified for full
physical quadrature. Manuscripts 036, 037 and 038, freeze 022, the canonical
figures and every run directory are byte-identical to their committed state.

## 4. The one input this revision could not supply

The realized value of the R1 metric floor `eta` was searched for and not found.
The rule is source-resolved and restated in Appendix A.1; the scalar is not in
the executed freeze, the run manifest, any stored log or sidecar, or derivable
from the saved main outputs, whose normalised and absolute errors are separate
medians rather than a paired quotient. It is recorded in section 9 item 4, in
`METHOD_DEPENDENCY_STATUS_039.json` and against claims C06, C07, C08 and C21 in
the matrix. It is not marked complete anywhere, and no value was invented for
it. This is a reproducibility limitation on the R1 normalisation, not a change
to the archived benchmark values.
