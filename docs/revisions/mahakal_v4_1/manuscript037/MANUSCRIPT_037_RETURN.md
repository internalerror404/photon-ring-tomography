# MANUSCRIPT_037_RETURN

Status: **MANUSCRIPT_037_READY_FOR_SEMANTIC_REVIEW**

Ruling: PAPER_I_MANUSCRIPT_REVIEW_037
New rays, path integrals, hull roots, operator spectra, estimators or truths:
**0**. The 854 units are untouched. `manuscript036` and every archived record
are unchanged; all outputs are additive under `manuscript037`.

## 1. The findings are accepted, and they were mine

Every regression ruling 037 names is real, and each came from the same
mistake: I wrote the 036 draft out of `artifacts/manuscript/PAPER_I.md`, the
older repository prose, instead of resolving each number to its primary record
and then applying the later amendments. The archived manuscript genuinely
contains that prose; using it as the ancestor is what reintroduced corrections
we had already made.

Twelve regressions are repaired and scanned. Five of them still appear in the
draft **as quotations inside withdrawal statements**, which is the point: the
old claim is preserved and marked, not deleted. The scanner distinguishes the
two, and `still_asserted` is empty.

## 2. What the primary records actually say

| what 036 asserted | what the record says | source |
| --- | --- | --- |
| "99.8% of squared weight in temporal hat 2, exactly zero in hat 0" | 2.44% / 2.35% oldest third, 43.81% / 43.92% middle, 53.75% / 53.73% youngest — broad, younger-weighted, and **not zero in the oldest** | `LOCALIZATION_READBACK.json`, `intervals[*].source_energy_fraction` |
| 60/84/144 M as "recoverable depth", reach "set by inclination rather than spin" | 144 M is the **oldest detectable age probe**, a supremum of a threshold mask; the **anchor-connected** spans are 60, 84 and 112 M at spin 0 / 116 M at the other three, against direct 20, 60, 108/112 | `E3C_GEOMETRY_WIDE_OPERATOR_AUDIT.md` |
| level result "a coefficient-space result" | the registered **baseline-inclusive field metric**, level dominated at level fraction 0.9838 | `R1_HELD_OUT_MAIN.md` |
| structure "cleared at ten times the reference SNR" | zero at `SNR_0 = 100`, **first nonzero at 30000** with 40 M direct and 76 M resolved; R1L stage-2R at 1000 is a separate aggregate result | `R1_HELD_OUT_MAIN.md` |
| "640 truths ... 48 to 80 M" | 48 → 80 M in `IN_CLASS_ID`, `IN_CLASS_OOD` and mild `OFF_GRID_OOD`; **`OFF_GRID_ID` remains 0 → 0 M** | `R1_HELD_OUT_MAIN.md` regime table |

I checked each against the primary artifact rather than taking the replacement
passages on trust. All five agree with the ruling.

## 3. The theorem is restored

Section 4 now carries Proposition 4.1 with a proof — support disjointness from
the direct footprint implies exact zero columns — and Corollary 4.2 as a
conditional continuum statement about the assumed transfer map, explicitly not
a validation of its discretisation. The proposition is followed by what it does
*not* say: nonzero columns are neither independent nor recoverable directions.
The universal slogans ("enrichment destroys identifiability", "compactness
makes the direct image blind") are gone.

Also restored: the target/nuisance and normalised-Fisher definitions with the
warning against double-counting `sigma`; a per-experiment table of source
spaces, metrics, estimators and noise conventions; three rank notions and three
reach statistics with their definitions; the R1 regime table; and the HMT-2
estimator, draw-count and materiality detail.

## 4. The evidence chain is now real

Sixteen claims, each with structured evidence — commit, repository path, the
sha256 of the bytes **at that commit**, and a row selector — and all ten pins
resolved per experiment, or NOT_APPLICABLE with a reason, or UNRESOLVED. An
unresolved pin bars the claim from a headline.

The single global "single-sky noise, sigma = 0.0113..." string of the 036
matrix is gone. There are five per-experiment pin blocks, and R2's ideal
order-labelled comparison is pinned separately from the later D026 single-sky
detector experiment.

The reviewer's checker, run with `--repo`, reads every pinned blob with
`git show` and compares hashes: **`SCHEMA_READY_FOR_SEMANTIC_REVIEW`, 16
claims, 0 errors.** That verifies bytes and structure. It does not verify that
the prose describes the experiment, and the matrix records that distinction.

## 5. What I did not do

- I did not read the supplied 42-page PDF; it was not available to this
  session. Passages attributed to it come through the reviewer's replacement
  text, and only the reviewer's recorded sha256 is carried. Repository and
  uploaded document identities are recorded separately.
- I did not fabricate a bibliography. The references section lists only sources
  actually read, and marks the external bibliography outstanding.
- I did not recompute R2 under the corrected measure, or run anything.

## 6. What is outstanding

Editorial: external bibliography, figures (any caption reading "recoverable
depth" now needs the oldest-probe / anchor-span distinction), reconciliation
with the supplied PDF, author review.

Archive: the metric *formula* is cited to the R1 report rather than recovered
from the registered runner config — partially done, not complete.

Experiments: two, unchanged. The transfer quadrature, five conditions none met;
and the order-resolution physical control.

## 7. Status

| item | status |
| --- | --- |
| draft | COMPLETE_3538_WORDS_MAHAKAL_TITLE |
| regression scan | 12_CHECKS_CLEAN_0_STILL_ASSERTED |
| claim matrix | SCHEMA_READY_16_CLAIMS_0_ERRORS_BYTES_VERIFIED |
| theorem and definitions | RESTORED |
| bibliography | OUTSTANDING |
| supplied PDF reconciliation | OUTSTANDING_NOT_AVAILABLE_TO_THIS_SESSION |
| physical claims supported | 0 |
| author review | REQUIRED |

Not a submission freeze, not an R3B authorization, not an author verification.
