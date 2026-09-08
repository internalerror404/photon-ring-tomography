# PAPER_I_PUBLICATION_READINESS_040

Repository: internalerror404/photon-ring-tomography  
Reviewed commit: 5985fe90f523d7cc3b0b1e11da9fa3897f6708c2  
Branch: research/mahakal_v4_1  
Disposition: CANDIDATE_ACCEPTED_FOR_AUTHOR_REVIEW_TWO_RELEASE_CORRECTIONS_REQUIRED

Author-directed publication review, not a journal decision. The actual editable
039 manuscript, HTML, method-dependency record, gap report, input/figure manifests
and selected source implementations were inspected. The repository tree confirms
that a PDF is delivered. This review did not independently render that PDF or
visually certify its 23 pages: the connector returned the PDF as encoded content,
and a direct binary-to-local retrieval was unsuccessful. The user's page inspection
and rendering report remain reported evidence, not this review's independent check.
No campaign ray, physical integral, hull root, estimator, spectrum, truth bank or
repository test suite was executed.

## 1. Accept the author-review candidate and stop broad redrafting

The 039 delivery is an actual paper, not just a proposed work plan. Accept the
source-resolved R1 grid definition and the HMT2 aggregation description as completed
method exposition. Accept REALIZED_ETA_NOT_LOCATED as the properly scoped result
of the documented archive search. Do not invent a scalar or divide separately
aggregated medians to manufacture one. The disclosed scalar gap does not change
an existing endpoint table, and this review has not measured its influence on those
endpoints. Rule/seed/code reproducibility and recovery of a contemporaneous scalar
are different questions; absence from inspected logs is not proof the algorithm
cannot be reproduced by a separately authorized reconstruction of its fit inputs.

Preserve the accepted support theorem, R2 localization, twelve-cell E3C result,
regime/family distinctions, sample-level physical absences, numerical hull and
comparator closeouts, and the rejected composite-first candidate. No identical
scientific replay is requested. The 854 units remain untouched.

Two source-based release corrections remain: the E3C measurement normalization
must be unambiguous, and Figure 2's aggregation population must not be described
as twelve geometries without support. These do not call for new geodesics or
re-scoring any history. This is a final copy/metadata pass, not a new general
manuscript reconstruction or another numerical-optimization program.

## 2. E3C: one noise density per geometry and SNR, shared across arms

The table in section 3 currently says 'one density for the whole audit'. The
runner's opening comment uses the same loose phrase, but its implementation is
more specific. run_e3c_operator_grid.py::evaluate constructs operators at unit
noise density and computes s_ref from that geometry/support case's direct
reference-source response. The sweep scales each such operator by SNR_0/s_ref.
The density is shared by the arms of that comparison, not held numerically equal
across all twelve geometries or across all sweep values.

For a fixed geometry/support case g, with the frozen legacy screen weights, let
B^(1)_(g,r) denote the arm's whitened operator at sigma_Omega=1. With j_ref=1,

  s_g = ||B^(1)_(g,0) j_ref||_2 / sqrt(m_(g,0)),
  sigma_(Omega,g)(S) = s_g / S,
  B_(g,r)(S) = (S/s_g) B^(1)_(g,r).

Here m_(g,0) is the actual direct row count used by that archived calibration.
Do not silently substitute the later common-count repair when explaining legacy
results. The familiar integrated-pixel law is

  z_p = a_p |g_p|^3 j_p + epsilon_p,
  Var(epsilon_p) = sigma_Omega^2 a_p,
  whitened coefficient = sqrt(a_p) |g_p|^3 / sigma_Omega,

where a_p is the declared screen quadrature weight and the absolute-redshift
convention follows the archived coefficient() implementation. For pixel AVERAGES,
the corresponding variance is sigma_Omega^2/a_p. Name the measured quantity before
writing its variance. This does not certify the geometric accuracy of legacy a_p.

The square-root row in section 2 currently omits the noise factor. Say explicitly
that it is a sigma=1 row or include the division by sigma_Omega. Section 3.2's
threshold can be correct, but its I(a) must be defined as information PER SNR_0^2:

  I_hat_(g,r)(a) = ||B^(1)_(g,r) q_a||_2^2 / s_g^2,
  I_(g,r)(a;S) = S^2 I_hat_(g,r)(a).

Then sup{a : S^2 I_hat(a) >= rho^2} equals sup{a : I(a;S) >= rho^2}.
Do not use an already scaled/whitened I(a;S) and multiply by S^2 again. The source
writes exactly these distinct columns as information_per_snr2 and
information_at_reference_snr. This is a clarification of implemented quantities,
not evidence that any reported numerical endpoint was double-scaled.

The replacement note supplies the full normalized Gaussian probe from age_norm
and age_direction. It fills a reader-facing definition from existing code; it
performs no new probe evaluation or physical integral.

## 3. Figure 2: preserve the plot, repair the population label

FIGURE_MANIFEST_039.json calls the E3D aggregations medians over twelve geometries.
The primary E3D_SOURCE_CLASS_STRESS.md names THREE anchors: a000_i020, a050_i050,
a098_i075. E3C is the twelve-geometry audit; those counts must not be merged.
The figure builder computes medians over the rows present in the two E3D tables;
its textual '12 geometries' description is hardcoded and does not count them.

Read the existing parquet row identifiers, record unique geometry IDs/counts for
each filtered series, and reconcile them with the report. Use the actual table
population. On the currently inspected report this is a three-anchor E3D study;
if a different stored population is found, identify its separate lineage instead
of guessing either number. This requires table readback only, not a new operator.

Also record that the bottom panel is an aggregation over its named anchors, not
a plot at the reconstruction geometry unless explicitly filtered to that geometry.
Preserve localized-directional reach as distinct from Figure 1's scalar-probe
statistics. No plotted value is declared wrong by this metadata finding. Re-render
only if the displayed labels or a verified selector actually need to change.

The old claim 'only one statistic is flat in spin' should remain scoped to the
sampled grid and note that its difference appears at high inclination; it is not
a theorem about spin dependence. The new two-statistic organization is accepted.

## 4. Remaining paper presentation: editorial, not physical experiments

The HTML contains display blocks but uses plain text such as T_n and R^(−1)
inside div.eq rather than rendered mathematical subscripts/superscripts. That is
an honest editable author-review representation. Before submission, use readable
mathematical typesetting for the final artifact and inspect the actual PDF for
clipped formulae, broken glyphs and cross-references. The present review does not
claim it saw a PDF rendering defect; it inspected the HTML implementation only.

Keep the audit trail, but move the opening project-ruling paragraph and long
verification-status prose to a cover note or reproducibility supplement in a
reader-facing release. Retain scientific limitations, especially finite-model
scope, eta status, unresolved physical quadrature and the nonphysical index-sum
control. Do not remove limitations merely to make the language more confident.

The first paragraph should describe distributed ray-dependent delays rather than
suggest each order is a single earlier source snapshot. The physical.py source
already explicitly contrasts distributed footprints with a scalar delay ladder.
One accurate replacement is: 'Different image orders have different, generally
overlapping distributions of ray delays, so the same observer-time data can
sample different source epochs.' No new propagation or novelty claim is added.

The seven arXiv citations may remain for the narrow statements supported at the
reported metadata/abstract level. Do not manufacture journal fields or claim a
full-text/novelty review that was not performed. Papers not cited in the narrowed
manuscript do not all need to be imported from the old 26-entry list. Any stronger
technical or priority statement requires its own appropriate source verification.
No external literature was newly verified by this review.

## 5. Author decision: finite-model submission versus stronger physical study

Recommend reviewing THIS candidate as the explicitly finite-model information and
recovery study it now describes. The stronger common-sky accuracy and physical
order-resolution attribution remain separate research claims. Their absence is
not an automatic reason to require those experiments before every narrower paper;
changing the scope label also cannot turn an unvalidated physical claim into a
validated one. The original submitted PDF's physical validation and attribution
are not restored.

For eta, there are two honest author choices: retain the archived R1 result with
the rule and missing-scalar limitation, or separately authorize a faithful
reconstruction of the fit-only normalization before claiming exact numerical
reproduction. This ruling authorizes neither that computation nor a claim that
eta was harmless. The disclosed issue applies to R1, not automatically to the
R2 nuisance-information result or HMT2's independently specified endpoint.

Do not imply that a median of ratios can be recovered from separately stored
medians. Equally, do not claim deterministic code/configuration can never
reproduce a value merely because no contemporaneous scalar log was found.
Which reproducibility limitation is acceptable in the final paper is an author
and reviewer decision, not a condition resolved by another status token.

## 6. Bounded release action and stop

Authorize an additive final-release copy addressing ONLY the enumerated
normalization and population fixes, mathematical presentation, ordinary
bibliographic formatting and the authors' confirmed scope/eta decisions. Retain
039 and every canonical scientific artifact. No new schema, numerical search,
source enrichment, inference run or general method rewrite is requested.

The release record must identify the amended source/PDF/figure hashes, the exact
normalization definitions, actual Figure-2 geometry population, eta disposition,
source and claim scope, and what visual checks were actually performed. A source
inspection is not a PDF page inspection. File size and a page count alone do not
certify mathematical rendering or semantic consistency.

Convention B: 19146 spent, 854 unspent; boundary count 33410. New authorized
physical spend is zero; no paid resources, new batch, R3B, target spectrum,
estimator or truth generation. Existing table reads, elementary algebra and
document rendering are allowed. The reported 691-suite result is not rerun by
this review and a suite rerun is not required for these editorial changes.

Return RELEASE_COPY_040_READY_FOR_AUTHOR_SIGNOFF or RELEASE_COPY_040_BLOCKED.
Neither token sends a manuscript anywhere or establishes new physical accuracy.
Do not start a new optimization cycle because a copy edit exposes an ambiguity.

## 7. Source identities and review limitations

All repository reads are at the reviewed commit unless stated otherwise:
- manuscript039 Markdown, HTML, method-dependency report, gap report and manifests;
- scripts/run_e3c_operator_grid.py (blob d2720e6812d7e9a47a741d232d2eb0857e8f6156);
- src/phrt/operators/physical.py (blob cb26a08c3fe2f4836b6ca3edc3bdfbe441faa17c);
- scripts/revision_v4_1/u0_figures_039.py (blob 35e13d9fe53d7c88333fb5f7194a4d314a53cd85);
- artifacts/reports/E3D_SOURCE_CLASS_STRESS.md (blob 79b93e938cd6e8846dd38f962122f400345fc8cb).

The reviewer did not independently compute the E3D parquet medians, inspect all
claim pins, re-run the eta archive search, or certify every rendered PDF page.
The attached original 42-page PDF remains a distinct document source. Its page-13
normalization and page-24 three-anchor E3D setup corroborate the distinction,
without replacing the implemented runner or revalidating its physical operator.
The small local checks in REVIEW_PROVENANCE_040.json use synthetic arrays only.
