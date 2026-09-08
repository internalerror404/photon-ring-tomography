# PAPER_I_SEMANTIC_REVIEW_038

Repository: internalerror404/photon-ring-tomography  
Branch: research/mahakal_v4_1  
Reviewed commit: 2dd9ea1ad950001f8350faf9ec8fb957d532065e  
Disposition: MAIN_INTERPRETIVE_REPAIRS_ACCEPTED_TARGETED_METHOD_AND_PIN_CLOSEOUT_REQUIRED

Author-directed project review, not a journal decision. The main 037 corrections
are accepted: the Mahakal title, support-disjointness proposition and conditional
continuum statement, source-function localization, three reach statistics, R1
regime split, distinct R1/R1L structure results, and the removal of physical
causation from the index-sum control. These are real improvements over 036.
They should not be reopened or regenerated merely to complete the manuscript.

The draft is not yet semantically complete or submission-ready. Remaining issues
are specific definitions, mismatched evidence pins and missing result context.
No new physical experiment is requested by this review. The already deferred
continuous-acquisition work remains separate from this source-based closeout.

## 1. Scope of this review

The full 037 manuscript and all 16 claim records were read through the GitHub
connector, together with the gap report and selected primary configuration,
implementation and report files. This review did NOT run the user's matrix
checker, rehash every referenced repository blob locally, regenerate results,
or execute a repository test suite. The reported schema/hash pass is accepted as
such, not upgraded to semantic validation.

The locally available supplied PDF was rehashed: 42 pages, SHA256
152b099fc09994e917f629bda90de19bfd388ee19e96f754a0dfc4b763e61148. Selected pages
were rendered for inspection. Its bibliography is provided as an explicitly
UNVERIFIED source extract so it is no longer inaccessible text for the next
editorial pass. No external paper has been independently read or verified in
this review, and this is not a new literature or novelty assessment.

## 2. A field metric is now correctly named, but must actually be defined

Section 7.1 correctly calls the R1 loss a baseline-inclusive field metric. The
gap report acknowledges that its formula/evaluation-map recovery is incomplete.
Naming the loss cannot complete that task. The required definitions already
exist; there is no need to simulate anything.

src/phrt/metrics/scoring.py explicitly evaluates the reconstructed field on a
fixed source evaluation grid, with normalized Gaussian age-window weights. It
uses equal grid weights, and says this is a scoring device, not a quadrature of
physical emission. Its Git blob is identical at the archived R1 execution commit
5f557fb606b76a95093cbf8e98d89d6f1dab9664 and the reviewed head:
0b04245c73ac80d63e3a6b8c2d2e67c2fef17dbc.

The accompanying METHODS_AND_PIN_CLOSEOUT_038.md spells out the actual quadratic
form, normalization, declared epsilon=0.25, q=0.95, 3-M window, 4-M age grid,
8-M materiality criterion, eight noisy draws, and truth-cluster bootstrap from
the R1 freeze and scorer. Preserve the difference between this finite-grid field
loss and R2's source-function Gram normalization. Do not replace either by a new
physical-volume norm, or infer a continuum error from the word 'field'. Resolve
the archived scalar eta and grid identity through their real execution payloads
before marking those pins complete; do not insert a default value.

The morphology loss likewise needs a compact definition: resolved states use
assignment error, blended/ambiguous states use descriptors, and dead states use
amplitude. Name the analytic-source and class-conditional targets, the aggregation
unit and bootstrap unit. Four paired noise draws are experimental replication;
they are not a covariance matrix. The existing morphology implementation and
sealed freeze supply these definitions without new computation.

## 3. Correct evidence pins that are structurally present but semantically wrong

The 037 matrix is a genuine structural improvement: explicit source commit,
path, hash and selectors have replaced path-only records. It still needs the
following targeted corrections. Do not discard the structure or invent a new
schema just to repeat the same work.

- C04/C05: the quadrature pin calls Gauss radial and piecewise-quadratic temporal
  integration a 'corrected measure'. Those are the SOURCE-function localization
  integrals. They are not the legacy SCREEN/ray quadrature used to compute the
  R2 spectrum. Keep both identities and do not imply the accepted two-mode count
  was recomputed with the C13 measure. For C04, the evaluated quantity is an
  interval source-energy fraction, not the Fisher trace currently inherited in
  its evaluation_metric field.
- C09-C11: 'four paired noise draws per truth' does not specify covariance, and
  'family source norms' does not identify a Gram matrix. Resolve the actual
  observation/noise definition and any relevant projection/evaluation metric,
  or mark that field not applicable with the right reason. Do not fill a pin
  with a neighboring fact merely because the schema requires a string.
- C13: the claimed hull tessellation metric currently inherits detector-response
  norm(W(yhat-yref))/norm(Wyref). The geometry closeout provides its actual
  band-normalized geometric comparison. Cite that metric, its compared levels
  and its 1e-6 component budget. The accepted total hull closeout stays closed.
- C14: the event-existence comparator does not have a D026 observation covariance
  or a six-screen/five-transfer-channel source basis. Those copied pins belong
  to the response audit. Describe the tested path-domain predicate, cohorts,
  numerical policies and shared inputs; mark acquisition-only fields inapplicable.
- C05: headline_allowed=false conflicts with the abstract, which includes the
  two-direction result. The scoped LEGACY result is eligible once its evidence
  resolves; only a stronger corrected-measure/existing-instrument claim needs
  additional evidence. Split the claims rather than require an unnecessary R2
  rerun or remove a sound scoped result merely to satisfy a flag.

A nonempty evidence_ref path is not automatically a resolved pin: it must resolve
to the same authenticated source set and actually support the pin's value.
Several current pin references are not among the claim's hashed evidence entries.
Manifest indirection is allowed; requiring duplicated hashes is unnecessary.
The existing checker verifies evidence bytes but does not follow every pin
reference or prove that its selector means what the prose says. Retain that
limitation in the completion record.

The 16 records are not yet an exhaustive inventory of the draft's numbers.
Section 6.4's 16.8-percentage-point/five-order/class-ladder result and section
1.2's 12-geometry/16-seed conditioning claim have no matching entries in this
matrix. Map them to their primary sources, or remove them from the candidate
text. C09-C11 still cite the summary evidence ledger; follow its references to
endpoint, family and config records rather than label the summary itself the
completed primary numerical lineage. Existing source reports remain useful
interpretive evidence, not a substitute for a missing selector.

## 4. Four local wording/interpretation repairs

First, section 3's 'three rank notions' includes stable recovery. Recovery is not
a rank notion. Distinguish algebraic rank (only where exact justification exists),
numerical rank and operational rank; then define estimator recovery as a separate
quantity. Not every operational count in E3C/E3D was nuisance-profiled: that step
belongs specifically to the stated R2 calculation.

Second, an anchor-connected span is not necessarily history 'from the present'.
The same section gives positive anchors of 28 or 32 M at high inclination. Say
'continuous over the passing interval beginning at the geometry-specific anchor';
only identify that anchor with age zero when it is actually zero.

Third, section 6.4 describes 224 -> 1056 as temporal enrichment and calls the
endpoint an oldest detectable probe. E3D includes temporal AND spatial enrichment:
(4,7,8) -> (4,7,16) -> (6,11,16), with (6,11,8) as a spatial branch. Its report
and source tables distinguish numerical-rank counts, operational fractions and
localized-directional reach. The exact 16.8-point aggregate and five-order
statement need their own selectors; do not equate the localized directional
endpoint with the scalar E3C probe. At the reference anchor the reported numerical
ranks of the resolved ladder are 224, 448, 528 and 1045. This is compatible with a
falling FRACTION, not an absolute loss of all supported dimensions. No new spectrum
is requested to recover these distinctions.

Fourth, section 7.4 puts a weaker L448-class result under FAMILY_HETEROGENEITY.
Changing the representation class is not changing the source family. Restore
actual family-level evidence on the same primary class, alongside the genuine
class-size comparison. The supplied paper's page 31 and the existing family table
identify the nonuniform effects; the simpler circular-hotspot family is not made
a positive result by the aggregate. Keep calibration withdrawal assigned to the
R1 posterior program, rather than suggesting TSVD/ridge generated calibrated
posterior intervals. Preserve the other negative endpoints in their tested scope.

Minor but important consistency edits: the three audit discrepancies are per-order
MAXIMA, not one identical error shared by every channel. The 40 transferred
columns are not 40 independent trials. In section 2, the integration cells that
intersect detector pixels are SCREEN cells, not source-plane cells. For inherited
noise, define parent areas in the same experiment as the overlap; keep that
covariance separate from full-detector-area single-sky noise. Restrict the quoted
absolute clock reference to the reference-geometry audit where it was imposed;
do not suggest all legacy geometry/recovery results were retrospectively recentered.
Section 9 should not restore mandatory group-remainder radii after section 8
correctly calls them only one possible certificate.

## 5. Complete the method, rather than substitute internal names for it

Preserve the restored theorem and information definitions. Add the remaining
minimal methods needed to interpret the results: source synthesis factors and
actual dimensions, declared observer/time/age grids, localized probe and its
normalization, per-geometry SNR definition, explicit recovery loss and success
statistic, estimator regularization/selection rule, target definition and
uncertainty aggregation. Existing code/configs determine these, not general
inverse-problem convention. Ridge/TSVD should be described as non-Bayesian
spectral estimators with fixed representation and validation-selected tuning,
not as inference without assumptions.

The HMT2 freeze records 896 and 448 as representation names BEFORE removal of
axisymmetric columns, with active coefficient counts 768 and 384 after m=0
removal. Keep those conventions explicit instead of silently reading a class
identifier as the number actually estimated. That is a source-based dimensional
clarification, not authorization to alter the source class.

The next matrix should differentiate a source coefficient Gram, the evaluation
quadratic form and the physical detector quadrature. They may all be matrices
or integration weights, but are not interchangeable pins. A concise methods
appendix plus a main-text summary is sufficient; every implementation detail
need not dominate the scientific narrative.

## 6. Source access, references and publication scope

The supplied PDF is available in this review and has the same recorded hash.
SOURCE_PDF_BIBLIOGRAPHY_038.txt makes its 26 listed references available directly
on the research branch as source text. It is NOT a verified external bibliography.
Verify relevant publications and their support for each sentence before citing
them as read. This review did not perform outside-literature verification; it
neither silently imports the PDF's disputed physical claims nor claims novelty.
Use the original 'Relation to Existing Work' as an organization guide while
retaining the current corrected scope. Add real in-text citations and a related-
work account before calling the manuscript a submission draft.

There is no need to keep every historical error quoted in the main paper.
Preserve withdrawn wording in the immutable drafts and correction ledger. Use
positive, accurate statements in the new main text, with short scope notes where
needed. A withdrawal box is not a substitute for an unambiguous final statement,
and a regex recognizing boxes is not semantic verification.

Submission remains pending method/lineage closeout, bibliography/figures, author
scope approval and the appropriately limited scientific claims. The two deferred
physical workstreams remain identified, but their completion is not a universal
prerequisite to a clearly finite-model paper. Nor are they an exhaustive promise
of every experiment that a broader physical claim might eventually need.
No new physical work is authorized to settle the drafting issues listed here.

## 7. Bounded next delivery and preservation

Authorize one source-based manuscript038 revision addressing these enumerated
findings, with the actual edited draft, typed pin corrections, per-number evidence
links and a reader-facing methods appendix. Keep the already corrected 037
interpretations fixed. Do not merely return a stronger regex or a renamed status.
Use source facts and already generated artifacts, not new estimates. If a required
pin is genuinely unavailable, mark the precise dependency and restrict its claim.

Convention B remains 19146 units spent, 854 unspent; boundary spend 33410.
Zero new rays, physical path integrals, hull roots, target matrices, spectra,
estimators or truths. No new interpolation candidates, R3B or submission freeze.
Old manuscripts, numerical data and accepted closeouts remain unchanged. No full
numerical-suite replay is required for this document task. New document-source
extraction and elementary algebra checks are permitted and are not evidence of
physical convergence. Return MANUSCRIPT_038_READY_FOR_FINAL_TEXT_REVIEW or
MANUSCRIPT_038_BLOCKED, with the complete draft and exact remaining dependencies.

## Sources read

All repository sources at the reviewed commit unless specified:
- manuscript037 draft, matrix, source-check/gap records and directory metadata.
- artifacts/configs/R1_MAIN_FREEZE.json and HMT2_SEALED_MAIN_V1.json.
- src/phrt/metrics/{scoring,age_error,morphology}.py and src/phrt/main_r1.py.
- artifacts/reports/E3D_SOURCE_CLASS_STRESS.md.
- the supplied 42-page Mahakal PDF, inspected separately from repository sources.
R1 scoring.py was additionally read at its archived execution commit to compare
its Git blob identity. No primary endpoint parquet or full matrix was numerically
recomputed, and no new physics result is asserted by this review.
