# Source-grounded methods and pin corrections for manuscript038

These are proposed insertions and evidence pointers, not a new physical result
or a completed manuscript. Read the primary source under the named commit and
preserve its units, loss and experiment. Do not substitute general convention
for a value absent from the execution record.

## 1. R1 field metric: ready-to-insert definition

Let D be the C224 synthesis matrix on the fixed source evaluation grid and let
v_j be the rendered truth on that same grid. The reconstructed coefficients
c_hat give the evaluated field D c_hat. For an age a, define normalized Gaussian
window weights

    w_ap = exp[-(t_p+a)^2/(2 h^2)] /
           sqrt(sum_q exp[-(t_q+a)^2/h^2]),  h = 3 M.

With W_a = diag(w_ap), the registered relative error is

    E_jb(a) = ||W_a (D c_hat_jb - v_j)||_2 /
              max(||W_a v_j||_2, eta),

where b labels the noisy realization. Eta is a common floor fixed from the
prior-fit split, not chosen per truth or from the test set. Its registered rule
is 0.05 times the median positive windowed truth norm on that fit split. The
actual scalar is an execution input and must be read from its recorded payload,
not recomputed or inferred from a default for this manuscript task.

This is a weighted FIELD loss on a finite evaluation grid, even though it is
computed using the algebraically equivalent quadratic form

    ||W_a(D c_hat-v)||^2
      = c_hat^T M_a c_hat - 2 c_hat^T p_a(v) + s_a(v),
    M_a = D^T W_a^2 D,
    p_a(v) = D^T W_a^2 v,
    s_a(v) = v^T W_a^2 v.

The evaluation grid is log-spaced in radius and uniform in azimuth and time,
with equal spatial grid weights in this scorer. It is a declared scoring device,
not an approximation to the continuum r dr dphi dt norm simply by definition.
State the frozen grid shape and domain from the execution record; the function's
default 10/12/40 shape is not proof of the executed configuration.

On the fixed 4-M age grid, the primary endpoint is the largest passing span
connected to the frozen anchor, at epsilon=0.25 and q=0.95. The underlying
criterion is that the running maximum of E_jb over the interval is <=epsilon
on at least q of the empirical joint truth/noise evaluations. There are eight
noisy draws per truth in R1 and a separate noiseless control. The main runner
concatenates the noisy draws for the endpoint and excludes the noiseless control.
Uncertainty uses paired truth-cluster resampling with all draws travelling with
the sampled truth: 10000 resamples, 95% intervals, frozen seed 20260901. The
prespecified improvement floor is 8 M. IN_CLASS_ID is primary; report the other
regimes under their declared roles rather than reclassify the whole 640-bank
as one successful population.

Sources:
- src/phrt/metrics/scoring.py: AgeScorer.build, truth_terms, errors, evaluation_grid.
  Git blob 0b04245c73ac80d63e3a6b8c2d2e67c2fef17dbc at BOTH the reviewed commit
  2dd9ea1ad950001f8350faf9ec8fb957d532065e and R1 execution
  5f557fb606b76a95093cbf8e98d89d6f1dab9664, checked through the connector.
- src/phrt/metrics/age_error.py: age_error_curve and freeze_eta.
- src/phrt/main_r1.py: noisy/noiseless separation and anchored_depth_surface calls.
- artifacts/configs/R1_MAIN_FREEZE.json: /primary, /noise, /bootstrap, /metrics,
  /sealed_bank/n_per_regime and /estimators.
All except the explicitly compared older scorer were read at the reviewed commit.
No scorer, source grid or historical endpoint was executed during this review.

## 2. HMT2: state-dependent morphology, not a generic norm

Each truth-age state receives its reconciled source-side label before arm
comparisons. SINGLE_RESOLVED and MULTI_RESOLVED states use an unbalanced
assignment cost, normalized and clipped to its declared worst-case scale.
BLENDED and AMBIGUOUS states compare normalized centroid, size, azimuthal-mode
and contrast descriptors. DEAD states compare amplitude. Every state contributes;
a favorable subset must not replace the all-state primary endpoint.

The code's all_state_error is a mean over state errors. The final reported
paired-reduction statistic, its order of aggregation over ages and draws, and
the bootstrap unit must be quoted from the actual endpoint runner; do not
silently replace a median of paired reductions by a relative difference of mean
errors. The primary analytic-source comparison reports ridge 0.164 and TSVD
0.133, with lower confidence limits 0.116 and 0.101, respectively, under its
registered 0.10/0.05 floors. These values retain the exact scope of the primary
endpoint table and later interpretation amendments.

The legacy class identifiers include the axisymmetric factor in their names:
L896_radial_enriched has 8 radial x 7 azimuthal x 16 temporal factors, while
L448_contrast has 4 x 7 x 16. The runner removes m=0 before inversion, leaving
768 and 384 fitted contrast coefficients. Preserve the names and state their
active dimension; do not silently reinterpret the history of the experiment.

Sixty independent histories have four paired noise draws each. The draws are
not 240 independent histories, and their count is not the observation covariance.
The observation law, noise scale and linear arm readouts must be documented
separately. The runner generates a common standard-normal order/ray/time tensor
per truth/draw and maps it through each arm's noise_from_standard; it builds the
TOTAL_FLUX control with an all-ones order mixer plus total-flux collapse. This
is not the E3C per-order flux readout by name alone. The archived physical
meaning of PHYSICAL_END_TO_END is fidelity to the analytic source, not a
validation of a real instrument or of continuous transfer quadrature.

Sources at the reviewed commit:
- artifacts/configs/HMT2_SEALED_MAIN_V1.json: /inherits_verbatim/classes,
  /inherits_verbatim/primary_endpoint, /bank, /sealed_hyperparameters,
  /pass_criteria, /inherits_verbatim/evaluation and /inherits_verbatim/classification.
- src/phrt/metrics/morphology.py: state_error, assignment_error, blended_error,
  dead_error and aggregate_all_states.
- scripts/run_hmt2_sealed_main.py: ocfg, keep, Z and noise_from_standard calls.
- scripts/run_hmt1_score.py: imported spectral_filter and paired_relative.
  The latter's body was not inspected in this review; follow it to close the
  paired-reduction formula, not this note as a substitute source.
- artifacts/tables/hmt2_main_endpoint.parquet and hmt2_main_per_family.parquet:
  existing primary result/family sources, identified in the canonical ledger;
  their contents were not recomputed by this review.

## 3. Rank, source metric and nuisance statements

Suggested replacement for 'Three rank notions':

'We distinguish structural algebraic rank when exactly justified, numerical rank
at a stated floating-point tolerance, and operational rank at the declared SNR,
source normalization and decision threshold. Estimator recovery is a separate
criterion: a declared loss and reliability requirement on held-out histories.
Nuisance projection is part of the stated R2 target calculation, not an automatic
step applied to every earlier E3C/E3D count.'

For R2, retain its existing definitions B_known=B_T R^(-1) and
B_cond=(I-Pi_N)B_T R^(-1) with H_T=R^T R. State what H_T actually is: the Gram
matrix of the specified target source functions under the declared source
measure. This must not be confused with D^T W_a^2 D, the R1 scoring matrix above,
or with geometric screen-cell areas. The full nuisance space has 152 columns;
its sampled rank is 140 in the direct arm and 152 in the resolved arm. Label
column count and arm-specific rank separately.

For the legacy result, an abstract may state the sampled direct target null and
two surviving order-labeled combinations after profiling, with the legacy-measure
qualification. Do not require a corrected-measure experiment solely to keep that
scoped archived fact. Split the matrix entry for the legacy result from any
claim to an exact corrected-measure count or a validated physical acquisition.

## 4. Typed corrections to the existing claim matrix

| Claim | Current mismatch | Required evidence value |
|---|---|---|
| C04 | source-localization result tagged with Fisher-trace evaluation | interval source-energy fraction, source Gram and saved coefficient vectors |
| C05 | localization integration called the spectral 'corrected measure' | legacy ray/screen quadrature and noise; source Gram integration listed separately |
| C09-C11 | four draws entered as covariance | covariance/noise-from-standard/readout definition; draw count in replication metadata |
| C13 | tessellation entered as a detector response norm | band/boundary geometry discrepancy between named tessellation levels |
| C14 | domain comparator assigned D026 noise and harmonic fields | path-domain predicate, cohorts, numerical reference policies; detector-noise/source-basis fields N/A |

Pin references may be indirect, but must resolve uniquely to authenticated
source bytes and a relevant selector. A report saying 'as registered' is a
pointer to follow, not the value of an unknown pin. Likewise a summary ledger
can organize primary rows without itself replacing their evidence.

The E3D paragraph and conditioning-control result need matrix entries of their
own. E3D's four classes are C224, C448_T, C528_S and C1056_ST. Spatial and temporal
factors both change over the full ladder. Use the actual table fields for its
operational fraction, positive singular value and localized-directional reach.
Do not describe a scalar E3C detectability supremum and an E3D directional endpoint
as the same quantity just because both are expressed in M.

## 5. Direct wording replacements

- 'Continuous history from the present' -> 'a contiguous passing interval from
  the geometry-specific anchor; this is age zero only where the recorded anchor
  equals zero.'
- 'Source cell C_p' in detector intersections -> 'screen integration cell C_p'.
  The source-plane map appears inside the transfer function, not as a set to
  intersect directly with the observer's pixel without a mapping.
- '9.594e-3 / 4.274e-2 / 5.116e-1 on all 40 channels' -> 'maximum relative
  same-support discrepancy over the 40 transferred diagnostic columns of
  9.594e-3 / 4.274e-2 / 5.116e-1; every such column exceeds the tested threshold.'
  This preserves maxima and the separate all-channel failure statement.
- 'Prior-free' -> 'non-Bayesian spectral estimators with a fixed representation
  and validation-selected regularization.' This does not change any estimator.
- 'Family heterogeneity' backed only by an L448 vs L896 row -> a genuine
  same-class per-family table, with class dependence retained as its own result.
- Group remainder radii -> one possible numerical certificate; any alternative
  still needs justified reference error, full/controlled omitted support and
  independent validation appropriate to its own construction.

## 6. Supplied PDF and references

The supplied 42-page PDF has the unchanged SHA256 recorded in the review. Its
pages 10-13 contain the old Gaussian-probe and SNR definitions, and pages 29-32
contain the morphology state metric, sample sizes and family qualifications.
These are source-document statements, not new revalidation of their numerical
claims. In particular later C02/C13, index-pairing and noise-convention amendments
must take precedence over contradictory older wording.

The separate SOURCE_PDF_BIBLIOGRAPHY_038.txt is a faithful text extraction of its
reference pages, not a claim to have read the external papers. It removes the
source-access obstacle to beginning the literature audit. Verify relevant sources,
then attach each citation to the exact claim it supports; neither an internal
ruling number nor a list of unverified titles replaces scientific related work.
