# MANUSCRIPT_CORRECTION_LEDGER_037

What ruling 037 found in the 036 draft, and what the 037 draft does instead.
Every replacement number is read from the primary artifact named in
`CLAIM_EVIDENCE_MATRIX_037.json`, not from the archived manuscript prose.

## Regressions repaired

| id | the 036 draft said | the 037 draft says | primary source |
| --- | --- | --- | --- |
| R01/R02 | "99.8% of squared weight in temporal hat 2 ... exactly zero in hat 0" | 2.44%/2.35% oldest third, 43.81%/43.92% middle, 53.75%/53.73% youngest; the oldest third is not zero | `LOC025_.../LOCALIZATION_READBACK.json`, `intervals[*].source_energy_fraction` |
| R03/R04 | 60/84/144 M called "recoverable depth", reach "set by inclination rather than spin" | 144 M is the oldest detectable age probe, a supremum of a threshold mask; the anchor-connected spans are 60, 84 and 112/116 M and they vary with spin at 75 degrees | `E3C_GEOMETRY_WIDE_OPERATOR_AUDIT.md`, oldest-probe and anchor-span tables |
| R05 | "the history is carried by when, not where, the orders sample" | 0.98 and 0.57 retained as index-paired counterfactuals; the mechanism sentence withdrawn | `E3C_MECHANISM_DECOMPOSITION.md`; amendment 023 |
| R06 | "source enrichment destroys identifiability"; "compactness makes the direct image blind" | Proposition 4.1 with proof, conditional on support disjointness, plus Corollary 4.2 and an explicit statement of what the proposition does not say | supplied replacement passages; theorem restated and proved in section 4 |
| R07 | "a sixteen-month numerical audit" | removed; no duration is asserted | ruling 037 |
| R08 | the level result called "a coefficient-space result" | the registered baseline-inclusive field metric, level dominated at level fraction 0.9838 | `R1_HELD_OUT_MAIN.md`, level/structure split |
| R09 | structure "cleared at ten times the reference SNR" | zero at SNR_0 = 100, first nonzero at 30000 with 40 M direct and 76 M resolved; R1L stage-2R at 1000 is a separate aggregate result | `R1_HELD_OUT_MAIN.md`, structural recovery onset |
| R10 | "the gain is attributable to resolving the orders" | the labelled stack improves; the tested flux readout does not reproduce it; the index-sum control says nothing about a physically unresolved image | HMT-2 control rows in the evidence ledger |
| R11 | the Shiva-era title | the author-facing Mahakal title | ruling 037 source reconciliation |
| R12 | the four-endpoint interval called "the only valid form" | *a* valid enclosure for supplied intervals | ruling 037 |

## Scientific content restored, not present in 036

- Proposition 4.1 with a proof, and Corollary 4.2 as a conditional continuum
  statement rather than a measurement validation.
- The target/nuisance and normalised-Fisher definitions, including the explicit
  warning against multiplying singular values by an SNR label when sigma is
  already inside C.
- A per-experiment table of source spaces, metrics, estimators and noise
  conventions, replacing the single global noise pin of the 036 matrix.
- Three separate rank notions, and three separate reach statistics with their
  definitions.
- The R1 regime table and the HMT-2 estimator/draw/materiality detail.
- A references section listing only sources actually read, with the external
  bibliography marked outstanding rather than fabricated.

## Corrections to the 036 evidence matrix

| id | 036 | 037 |
| --- | --- | --- |
| M01 | `pins_recorded_per_claim` named ten pins globally; individual claims supplied none | each claim carries all ten pins as RESOLVED with a value and reference, NOT_APPLICABLE with a reason, or UNRESOLVED |
| M02 | one "single-sky noise, sigma = 0.0113..." assumption string for every experiment | five per-experiment pin blocks; R2's ideal order-labelled comparison and the D026 single-sky detector experiment are pinned separately |
| M03 | `source_commit_path_and_hash` held a bare path | structured evidence: commit, path, sha256 of the bytes at that commit, and a row selector, verified by `git show` |
| M04 | several claims resolved only to `PAPER_I.md` or the summary ledger | each resolves to its primary artifact; the 276-entry claim ledger is used as an index only |
