# MANUSCRIPT_038_RETURN

Status: **MANUSCRIPT_038_READY_FOR_FINAL_TEXT_REVIEW**

Ruling: PAPER_I_SEMANTIC_REVIEW_038
New rays, path integrals, hull roots, operator spectra, estimators, truths or
interpolants: **0**. The 854 units are untouched. `manuscript036`,
`manuscript037` and every archived record are unchanged.

## 1. The methods are now defined, from the code that produced the results

**The R1 field metric** (Appendix A.1). `src/phrt/metrics/scoring.py` has the
same git blob `0b04245c` at the reviewed commit and at the R1 execution commit
`5f557fb6` — I verified both with `git rev-parse`, so this is the scorer that
ran, not a reconstruction. The loss is

    E_jb(a) = || W_a (D c_hat_jb − v_j) || / max(|| W_a v_j ||, eta)

with normalised Gaussian window weights at h = 3 M. The implementation computes
it through the equivalent quadratic form `M_a = D^T W_a^2 D`; the appendix says
so and says that this does not make it a coefficient-space loss. The evaluation
grid uses **equal spatial weights** and is a declared scoring device, not a
continuum `r dr dphi dt` norm. `M_a` is distinguished from `H_T`, the R2 source
Gram, and from screen-cell areas.

Endpoint parameters read from `R1_MAIN_FREEZE.json`: epsilon 0.25, q 0.95,
floor 8 M, age step 4 M, half width 3.0 M, grid max 120 M, eight noisy draws
plus one excluded noiseless control, paired truth-cluster bootstrap of 10000
resamples at 95% with frozen seed 20260901, bank 640 split 256/64/256/64.

**The HMT-2 morphology metric** (Appendix A.2) is state dependent, not a norm:
assignment cost for `SINGLE_RESOLVED`/`MULTI_RESOLVED`, descriptor
discrepancies for `BLENDED`/`AMBIGUOUS`, amplitude for `DEAD`, with
`all_state_error` their mean. The `TOTAL_FLUX` control uses an all-ones order
mixer plus a total-flux collapse and is not the E3C per-order flux readout.

**Two dependencies are named rather than filled.** The executed `eta` scalar and
the frozen evaluation-grid shape are execution inputs I did not resolve to their
recorded payload, and the function default is not evidence of what ran. The
order of aggregation in the final paired reduction lives in `paired_relative`,
which I did not trace. Both are in the gap report; neither is invented.

## 2. Pins corrected, and one claim split

| claim | was | now |
| --- | --- | --- |
| C04 | localization tagged with the spectral quadrature and a Fisher-trace metric | its own source-norm integration, its own Gram with refinement steps 1.83e-14 / 4.33e-15, metric = interval source-energy fraction; covariance and rays NOT_APPLICABLE |
| C05 | headline barred pending a corrected-measure run | **legacy-measure headline allowed** at its scoped level |
| C05b | — | **new**: the corrected-measure count, `evaluation_metric` UNRESOLVED, therefore barred from a headline |
| C09–C11 | "four paired noise draws" entered as covariance | covariance is the common standard-normal tensor mapped through each arm's `noise_from_standard`; four draws are replication metadata; source Gram NOT_APPLICABLE with a reason |
| C13 | the detector-response norm copied in | band-normalised tessellation discrepancy between named refinement levels against the **1e-6** component budget |
| C14 | D026 noise and harmonic source channels inherited | the path-domain predicate, its cohorts and numerical policy; detector noise and source basis NOT_APPLICABLE with reasons |

Six claims added: C05b, plus C17 (E3D ladder and exact fields), C18 (the
localized-directional depth, separated from the E3C probe), C19 (the pairing
control's 12 geometries and 16 seeds), C20 (family heterogeneity from the real
per-family table), C21 and C22 (the two method definitions).

**23 claims, 230 pins: 152 RESOLVED, 77 NOT_APPLICABLE with reasons, 1
UNRESOLVED** — C05b's evaluation metric, which is exactly the unperformed
calculation. Your checker with `--repo`: `SCHEMA_READY_FOR_SEMANTIC_REVIEW`,
23 claims, 0 errors, every pinned blob read and hashed.

## 3. The four interpretation corrections

**Recovery is not a rank.** Section 3 now lists structural algebraic rank where
exactly justified, numerical rank at a stated tolerance, and operational rank at
the declared threshold — with estimator recovery as a separate criterion. It
also says nuisance projection belongs to the R2 calculation and is not applied
to the E3C/E3D counts.

**The anchor is not the present.** "A contiguous passing interval beginning at
the geometry-specific anchor; age zero only where the recorded anchor is zero" —
8 of 12 geometries, with 32/28/28/28 M at the four 75-degree ones.

**The E3D ladder changes both factors.** The four classes are now in a table:
C224 (4x7x8), C448_T (4x7x16), C528_S (6x11x8), C1056_ST (6x11x16). The 16.8
percentage points is the median operational-rank **fraction** falling 0.897 to
0.729 while the rank itself **rises** 201 to 770 — a falling supported fraction
is compatible with rising absolute rank, and the draft says so. The numerical
rank fraction (up to 3.3%, largest arm fall 25.1%) is a third quantity. And the
localized-directional depth is separated from the E3C scalar probe, with the
asymmetry recorded: every move appears at a spatial enrichment step and none at
the temporal one.

**Class dependence is not family heterogeneity.** `FAMILY_HETEROGENEITY` now
carries the real result — 5 of 12 family-estimator cells material on the
physical target, 4 of 12 on both, `circular_hotspot_trajectory` negative under
both estimators (−0.022, −0.051), and intervals too wide at ten truths per
family to support any family claim in either direction. The L448-vs-L896
comparison is kept as `CLASS_DEPENDENCE`, its own result.

## 4. Smaller edits

Screen integration cells, not source cells, in the detector intersection. The
three discrepancies stated as per-order maxima over 40 correlated columns, with
the all-column failure as a separate sentence. The absolute clock reference
scoped to the audit that imposed it, with no retrospective recentring implied.
Section 9 no longer reinstates group remainder radii as mandatory. "Prior-free"
replaced by "non-Bayesian spectral estimators with a fixed representation and
validation-selected regularization" — no estimator changed. R2's 152 nuisance
**columns** distinguished from the 140 direct-arm and 152 stacked-arm ranks.
HMT-2's nominal 896/448 given with their 768/384 active contrast coefficients.

## 5. Bibliography and figures

The reference extract is on the branch and the audit has **not** started. No
citation from it appears in the draft, and the draft cites only repository
sources actually read. Two archived figures carry captions the corrections
contradict — `fig1` asserts the withdrawn spin conclusion in its own title, and
`fig2` implies temporal-only enrichment. Neither is re-rendered; both are
identified with what their captions must say.

## 6. What still blocks submission

Bibliography audit; figure regeneration; the two named method dependencies
(`eta` and the grid shape; the paired-reduction aggregation); author scope
approval. And the two deferred experiments, unchanged: transfer quadrature and
the order-resolution physical control.

## 7. Status

| item | status |
| --- | --- |
| draft | 5092_WORDS_WITH_METHODS_APPENDIX |
| regression scan | 18_CHECKS_CLEAN_0_STILL_ASSERTED |
| claim matrix | 23_CLAIMS_0_ERRORS_152_RESOLVED_77_NA_1_UNRESOLVED |
| methods | DEFINED_TWO_DEPENDENCIES_NAMED |
| bibliography | SOURCE_AVAILABLE_AUDIT_NOT_STARTED |
| figures | NOT_REGENERATED_TWO_CAPTIONS_IDENTIFIED |
| physical claims supported | 0 |
| author review | REQUIRED |

Not a submission authorization.
