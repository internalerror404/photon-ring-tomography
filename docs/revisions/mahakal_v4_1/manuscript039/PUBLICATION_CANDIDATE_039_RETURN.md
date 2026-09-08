# PUBLICATION_CANDIDATE_039_RETURN

**Return token: `PUBLICATION_CANDIDATE_039_READY_FOR_AUTHOR_REVIEW`**

A ready token is not authorization to submit and not authorization to start
R3B. It says the reader-facing candidate exists, is rendered, and carries an
honest account of what is still missing.

Ruling: `PAPER_I_FINAL_TEXT_REVIEW_039`. Branch `research/mahakal_v4_1`.
No rays, path integrals, hull roots, target matrices, spectra, estimators,
truths or interpolants were computed. Convention-B second-batch spend remains
19,146 with 854 unspent; boundary spend remains 33,410.

## 1. What was delivered

An editable source and a rendered document, not a status packet:

| artifact | what it is |
| --- | --- |
| `Photon_Ring_Retarded_Time_Tomography_Candidate_039.md` | the editable candidate, 12 sections plus a three-part methods appendix |
| `Photon_Ring_Retarded_Time_Tomography_Candidate_039.html` | the rendered document |
| `Photon_Ring_Retarded_Time_Tomography_Candidate_039.pdf` | 23 pages, both figures embedded, 14 display equations set apart from the prose |
| `figures/fig1_reach_two_statistics_039.png` | reach, regenerated with corrected in-figure title, panels and axis labels |
| `figures/fig2_enrichment_three_panels_039.png` | enrichment, likewise |
| `FIGURE_MANIFEST_039.json` | per figure: source tables and their sha256, the exact row selector, the plotted columns, what it replaces, why, and the caption |
| `CLAIM_EVIDENCE_MATRIX_039.json` | 29 claims, ten pins per claim, each resolved to a primary artifact, commit, hash and row selector |
| `METHOD_DEPENDENCY_STATUS_039.json` | the three method inputs, two resolved and one not, each linked to the claims it affects |
| `BIBLIOGRAPHY_VERIFICATION_039.json` | seven external records with the verification level of each |
| `MANUSCRIPT_CORRECTION_LEDGER_039.md` | this revision's twelve corrections, plus the full withdrawal history moved out of the main text |
| `SUBMISSION_GAPS_039.md` | editorial, archival, physical and author-decision gaps, separated |
| `PUBLICATION_039_INPUT_MANIFEST.json` | every artifact read, hashed at this commit |
| `RENDER_039.json` | the render record: source hash, output hashes, equation and figure counts |
| `SHA256SUMS.txt` | hashed after rendering |

The canonical figures, manuscripts 036–038, freeze 022 and every run directory
are untouched.

## 2. The two dependencies the review resolved, now in the paper

**R1 evaluation grid.** Appendix A.1 states the source-resolved grid:
10 x 12 x 40 = **4,800 evaluation points** — ten log-spaced radii over
`[1.8660386527060988, 49.98205255591607] M` with both endpoints, twelve uniform
azimuths over `[0, 2π)` with the repeated endpoint omitted, forty uniform source
times over `[−128.82234649196255, 29.0] M` with both endpoints, flattened
`meshgrid(indexing="ij")` in C order so time varies fastest. Established by the
archived caller `scripts/run_r1_main.py` (blob `291adbf7`) calling
`evaluation_grid` with four support arguments and no size overrides, and its
imported callee `src/phrt/metrics/scoring.py` (blob `0b04245c`) at execution
commit `5f557fb6`. Recorded as a source-resolved definition; no hash of a
persisted grid payload is claimed.

**HMT-2 aggregation order.** Appendix A.2 states the full chain: mean over the
declared ages within a draw, mean over the four draws within a history, a paired
direct-relative reduction per history with denominator
`max(|ē_direct|, 1e−300)`, and the **median across histories** as the reported
point estimate. The 95% interval is the 2.5th and 97.5th percentiles of 10,000
bootstrap resamples of histories at helper seed **20260954** (bank seed 20260953
plus one). The helper's cell-balanced mean is named as a separate estimand and
is not the headline. The reported main pair count of 60 is cited as reported and
was not independently recomputed here, so no missing-pair claim is made in
either direction.

## 3. Eta: the bounded search, and its negative result

**Status: `REALIZED_ETA_NOT_LOCATED`.** The rule is source-resolved and
restated in Appendix A.1 — 0.05 times the median positive windowed truth norm on
the prior-fit split, frozen before scoring. The realized scalar was searched for
in: `R1_MAIN_FREEZE.json` (`metrics.eta_value: null`), the R0C freeze (also
null), the R1 run manifest (no eta field), every stored log, sidecar and output
directory under `artifacts/`, and the saved main tables. It is in none of them.

The runner computes `eta = freeze_eta(sqrt(einsum("ap,np->na", Wn**2, pf**2)).ravel())`,
holds it only in an in-process dictionary, and prints it at `%.6g`; no capture of
that stream is stored. A derived readback from the saved outputs is also not
available: `r1_age_errors.parquet` stores `median_normalized_error` and
`median_absolute_error` as **separate medians** over the truth/draw population,
and the quotient of two independent medians is not the per-row denominator.
Regenerating the prior-fit norms would be truth generation, which this ruling
forbids.

This is the result of a bounded search of the inspected records. It is **not** a
claim that no copy exists anywhere. It is recorded in section 9 item 4 of the
paper, in `METHOD_DEPENDENCY_STATUS_039.json`, and against claims C06, C07, C08
and C21 in the matrix. Nothing marks it complete, and no value was invented. It
limits exact reproducibility of the R1 normalisation; it does not change the
archived benchmark values, which were computed with the frozen scalar, and the
floor binds only where the windowed truth norm falls below it.

## 4. The consistency edits

Each is a prose or identity correction; no estimator, hyperparameter, noise
model or numerical result changed. Detail in
`MANUSCRIPT_CORRECTION_LEDGER_039.md` section 1.

- **Tuning lineage split** (section 3.3). R1 reuses its R0C validation
  selection; HMT-2 reuses its own stage-1 selection through the sealed-main
  freeze, whose runner performs no sweep. The single global R0C sentence is gone.
- **HMT-2 noise cell** (section 3 table). Now the readout law — one
  standard-normal (orders, rays, observer times) tensor per truth and draw,
  mapped to `σ_Ω sqrt(dΩ) z` on each order's pixels and through each arm's
  declared readout, whitened by the channel variance. The four paired draws are
  stated separately as replication.
- **Matrix links** (opening and section 12). Every internal reference names this
  revision's records; the draft, matrix, manifest and completion report identify
  one document version.
- **Support caveat** (section 4). Nonzero columns *need not be* independent or
  operationally recoverable — insufficiency, not impossibility. The theorem and
  its nonvanishing assumptions are unchanged.
- **Posterior calibration** (section 7.4) scoped to the R1 probabilistic
  estimator program, the state-space and Wiener branch at 0.497 against a frozen
  0.5 floor, and explicitly not a posterior from TSVD or ridge.
- **Family heterogeneity** (section 7.4). The measured point estimates and
  intervals are reported as measured; what does not follow is a strong universal
  family claim.

## 5. The exposition the review asked for

Section 3.1 gives `C224` as `4 × 7 × 8 = 224` — four cubic B-splines in `log r`,
seven real Fourier modes with `|m| ≤ 3`, eight DCT modes in source time,
radial-major ordering — on the declared radial and temporal supports, and gives
the reference observer schedule as eight samples uniformly spaced 0 to 20 M with
1536 retained rays per order at `n = 0, 1, 2`. The localized `L`-classes keep
their own temporal definition rather than being folded into `C224`.

Section 3.2 gives the age probe — Gaussian in retarded age, flat in the emission
annulus, half width 3.0 M, **normalised to unit `L²` norm over the emission
region** — and the detectability convention
`sup { a : SNR_0² I(a) ≥ ρ² }` with `ρ = 1`, on the operator scaled to the
reference SNR, with one noise density fixed from the direct arm's clean response
and no arm-specific `σ`.

## 6. Figures: what changed and what did not

Both were regenerated from authenticated saved tables into new filenames. No
operator, reconstruction or new sampling is invoked inside the builder; only
selection and median aggregation of archived columns. Unchanged values are
unchanged.

**Figure 1** now plots *both* reach statistics. The oldest detectable age probe
is flat across the four sampled spins at every inclination; the anchor-connected
span is not — at 75 degrees the resolved span is 112 M at spin 0 and 116 M at
the other three. Its in-figure title says so. The replaced asset asserted
"recoverable depth ... flat across four spins" while plotting a threshold
supremum.

**Figure 2** now has three panels and an axis that names the ladder by
`radial × azimuthal × temporal`, so it is visible that both factors change. The
supported fraction falls 0.897 to 0.729 while the count rises 201 to 770; the
localized-directional depth is flat across the ladder for both physical arms.
The replaced asset said "temporal class" for a ladder that changes both factors
and labelled the localized-directional depth "recoverable depth".

## 7. Rendering check

The PDF was rendered from the editable source through the repository's own
Markdown renderer, imported unmodified, and printed by headless Chromium. The
rendered artifact was inspected before hashing:

- 23 pages; the title block is its own page and the body starts at the abstract.
- Both figures appear, numbered, with their captions attached and cited from the
  running text ("Figure 1 plots the two statistics side by side" in section 5.2;
  "Figure 2 plots the fraction, the count and the localized-directional depth"
  in section 6.4).
- 14 display equations are set apart from the prose; no delimiter leaks into the
  rendered text.
- Every internal cross-reference resolves to a section that exists; no reference
  to a 037 or 038 record survives in the candidate.
- All eight tables render inside the page width.

Hashes in `SHA256SUMS.txt` were taken after this check.

## 8. Scope, stated once

The candidate is a finite-model information and recovery paper with explicit
limitations. It makes no continuum-acquisition claim and no physical
order-resolution claim, so the two deferred physical workstreams are not launch
prerequisites for it; they become prerequisites the moment a stronger claim is
added. That distinction is in `SUBMISSION_GAPS_039.md` section D rather than
described as a universal block.

Author scope approval is required. No journal acceptance is promised, no
submission is authorized by this return, and R3B is not started.
