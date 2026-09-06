# Correction ledger - Mahakal revision v4.1

Controlling amendment: PAPER_I_DEFECT_AMENDMENT_023.md. This replaces the v4.0 execution ledger prospectively; it does not replace archived evidence. Twelve IDs are preserved; C05 has two subitems. Status below concerns the stated scope, not a global verdict on the paper.

## Inputs and identity

Repository branch: research/hmt2_resolution_aware_feature_measure_v0. Inspected remote base: 7961e5bd7d46be23885151afa7664596cc58cfa6, freeze 022. The uploaded Mahakal PDF SHA-256 is 152b099fc09994e917f629bda90de19bfd388ee19e96f754a0dfc4b763e61148. Freeze 022 records repository PAPER_I.pdf as b2af07620ecebabd704a83aa9022f044574de443a7130a1c9ae5a8050a3962d5. They are different documents; the repository title at that freeze also differs. Do not assert byte identity or transfer section numbers without mapping them.

R0 must link each uploaded-paper claim to a verified source artifact, or mark its provenance unresolved. An unresolved uploaded-PDF lineage does not prevent algebra tests or an explicitly repository-based new analysis, but blocks a claim of reproducing that uploaded version.

## C01 - SNR notation versus actual scaling

Status: NOTATION_REPAIR; no double scaling found in the inspected E3C/HMT2 paths.
Evidence: scripts/run_e3c_operator_grid.py (snr_scale/evaluate), scripts/run_hmt2_sealed_main.py, scripts/run_hmt1_score.py (spectral_filter).

E3C forms unit-reference ihat then applies SNR squared once. HMT2 scales signal and singular values consistently. Trace every other consumer before generalizing. Use either B_s=C_s^(-1/2) A with the actual covariance and no extra multiplier, or an explicitly unit-reference B_1 with s B_1. Fix the printed equations/box in an overlay. Do not divide existing results by SNR again.
Acceptance: source-to-output scale trace; doubling amplitude or halving noise standard deviation gives Fisher times four. A code pass does not excuse ambiguous manuscript notation.

## C02 - Production reference scale and row-count dependence

Status: CORRECT_REPAIR_TARGET_AND_LIMIT_SCOPE; production migration and count-only mask audit pending.
Evidence: scripts/run_e3c_operator_grid.py::snr_scale; inline s_ref in scripts/run_hmt2_sealed_main.py. Agent additionally identifies run_hmt2_stage1.py, run_hmt1_validation.py, run_r1l_stage2r_b.py, run_e3d_source_class_stress.py and further sites. These names are search seeds, not an exhaustive count.

NoiseModel.from_snr in src/phrt/operators/whitening.py is the toy normalization path; the agent reports its only call in scripts/reproduce_v01.py. Its reference_rows argument is a row-selection slice, NOT an immutable reference count. R0 must verify the call graph. A patch confined to that helper cannot close this item.

Legacy physical formula: E_g=||A_g,unit j_ref||^2; s_ref,legacy=sqrt(E_g/m_g); sigma=s_ref/SNR0. E3C computes this once per geometry from the direct arm and shares sigma across all arms. Within-geometry noise comparability is therefore protected.

Three modes must be distinct:
1. LEGACY_REPLAY: exact archived construction/count, to reproduce old results.
2. LOCKED_LEGACY_NOISE: hold the archived per-geometry sigma fixed for refinement of the same physical observation.
3. COMMON_REFERENCE_COUNT: s_ref=sqrt(E_g/m_star), with one frozen design count across a fixed-schedule geometry campaign. E3C m_star=1536*8=12288. Other campaigns require their own predeclared count, verified from their design rather than inferred from held-out truths.

Only mode 3 removes the cross-geometry count artifact. Merely freezing each geometry's own original m_g prevents future drift but retains the 1483-versus-1536 distinction. Preserve geometry-dependent brightness normalization; matched direct reference response is not one absolute instrument sigma across different geometries.

Count-only factor for a000_i020: F_new/F_old=1536/1483=1.035738368172623 at fixed E_g and label. Do not extrapolate this small current-grid effect to a claim that all past results are materially wrong. The k-fold artificial split example concerns recalibration under future mesh refinement. Conversely, 4M quantization does not prove masks cannot change: enumerate crossings from stored curves, including all archived SNR/threshold settings. Recompute nonlinear log integrals from their curves.
Acceptance: exhaustive normalization-site inventory, opt-in revised physical-path integration tests, legacy replay, fixed-noise split tests, common-count split tests, per-geometry noise dictionary and endpoint-delta table. Helper-only tests are insufficient.

## C03 - Coefficient spectra versus source-function metric

Status: SOURCE_CONFIRMED_COORDINATE_SPECTRA; new physical-metric spectra pending.
Evidence: E3C uses PhysicalBasis.design directly and normalizes the 28 local factors separately before P.T@P. Individual normalization is not orthogonalization.

Retain old spectra as coefficient-coordinate diagnostics. Declare the model norm r dr dphi dt on a common nondimensional domain, compute H_ij=<q_i,q_j>, factor H=R.T R and analyze C^(-1/2) A R^(-1). Prefer weighted QR/SVD and triangular solves; do not hide ill conditioning with a ridge. The coordinate-area norm is not automatically a covariant proper-volume norm. Fix nuisance/target labels before normalizing; a global transformation must not silently mix their meanings.
Acceptance: converged source quadrature, generalized spectra under basis rescaling, separately reported ordinary rank/fraction/conditioning. A physical-norm regularizer is a new estimator, not a retroactive replacement.

## C04 - General mixing covariance

Status: EXTENSION_GUARD; inspected archived identity and one-output-sum cases survive.
Evidence: PhysicalOperator.channel_variance computes only marginal variances. General overlapping output channels require full L C L.T and matching forward, adjoint and noise sampling.

Do not invent a historical continuous leakage sweep. Identity and all-ones single-output mixing have no omitted cross-output covariance. For redundant outputs, whiten the stochastic support and separately test whether null-covariance directions contain signal; never discard informative noiseless constraints or add undocumented noise.
Acceptance: exact information invariance for invertible re-expression, contraction for rank-reducing postprocessing, covariance/adjoint/noise consistency; legacy restricted cases unchanged. Optical acquisition with new detector noise is a different model.

## C05 - Lost sky registration, with two affected control families

Status: PHYSICAL_INTERPRETATION_WITHDRAWN_PENDING_NEW_MODEL.
Evidence: src/phrt/geometry/sampling.py::stratified_subsample/common_count; src/phrt/operators/physical.py::OrderRays/substitute_spatial/substitute_delay; E3C/HMT2 constructors.

C05a: independent draws and independent trimming equalize cardinality, not screen coordinates. OrderRays lacks alpha/beta. UNRESOLVED_IMAGE sums array indices. New interpretation alias: INDEX_SUM_CONTROL. Preserve the archived 23.7%, rank and morphology values as results for this compression map. Withdraw the physical unresolved-image attribution in all manuscript and ledger occurrences.

C05b: the same missing correspondence affects DELAY_ONLY and SPATIAL_ONLY. Aliases: INDEX_PAIRED_DELAY_SUBSTITUTION and INDEX_PAIRED_SPATIAL_SUBSTITUTION. Preserve 0.98/0.57 and related numerical differences with their exact claim mappings; qualify them as pairing-dependent synthetic ablations. A flat scalar probe's invariance under spatial substitution remains algebraically valid but does not prove a physical mechanism split. Co-registration alone will not make a delay/spatial counterfactual a realizable spacetime; any successor must declare its intervention and common domain.

PAIRING_DESTROYED intentionally permutes and is not newly defective for doing so. Preserve its limitations and randomization convention.
Acceptance now: alias/claim overlay plus tests exposing cardinality versus registration and sensitivity of index ablations to reindexing. Do not require or fabricate a common-sky construction before R2. Physical common-sky and mechanism replacements remain R3 or later, separately authorized.

## C06 - Runner-specific flux

Status: SEMANTIC_SPLIT_CONFIRMED; numerical evidence retained.
E3C: collapse='total_flux', no mixer -> one light curve per order -> 24 rows for 3 orders/8 times; alias ORDER_RESOLVED_FLUX_CONTROL. Rank 13 is consistent.
HMT2: mixer=ones and collapse='total_flux' -> all orders and pixels -> 8 rows; alias ALL_ORDER_FLUX_CONTROL. Summation of integrated pixels does not require inter-order pixel correspondence. Its tested nonmaterial/negative result survives under the declared inherited noise and contrast model.
Acceptance: every claim keyed by runner plus arm, not arm string alone; row counts and rank ceilings checked. Preserve the distinction between failure of the tested total-flux estimator and a universal impossibility claim.

## C07 - Absolute dimension, fraction and extra observations

Status: INTERPRETATION_REPAIR.
Uploaded Table 5 resolved numerical ranks 224,448,528,1045 do not demonstrate falling absolute rank. Richer models add weak/blind directions and can lower the well-constrained fraction. For fixed unknowns, source metric and observation noise, adding independent channels adds PSD information. Enlarging unknown/nuisance spaces is a different operation.
Acceptance: separate absolute rank, dimension, rank fraction, operational rank and norm-dependent conditioning. No slogan about photons destroying information.

## C08 - Known-remainder sensitivity versus nuisance-adjusted information

Status: NEW_R2_ANALYSIS_REQUIRED.
||B q_a||^2 holds other components fixed. It need not survive an unknown baseline or unknown remaining emission. Retain J_old as old-age sensitivity volume; it is not mutual information or a nuisance-profiled capacity.
For a fixed target and all other unknown source coefficients, residualize against the nuisance response, with numerical rank tolerance but no SNR cutoff or regularizer. State unconstrained-linear/local assumptions. Zero profiled information must be reported. Geometry uncertainty is not authorized in the initial R2.
Acceptance: same physical target and actual noise across arms; conditional/unconditional spectra; projector rank and tolerance sensitivity; all baseline and boundary-overlap nuisances included. See handoff for the exact construction.

## C09 - Support theorem and impossibility boundary

Status: RETAIN_WITH_PRECISE_SCOPE.
A nonzero new column need not be independent of other columns. A count of zero columns yields that subspace nullity only for independent source functions. Use finite regular source bases; arbitrary L2 point evaluation needs extra assumptions. Preserve structural support-null results separately from numerical small values.
Acceptance: no claim that one sampled response proves stable inversion. Zero stable morphology interval is a failure of the declared estimators/ensemble, not every possible method. Stronger admissible-pair impossibility work is deferred, not presumed complete.

## C10 - Attribution, endpoints and uncertainty

Status: CLAIM_QUALIFICATION; old scores, thresholds and banks immutable.
Apply amendment 023's approved paragraph in a new overlay. The HMT2 all-order flux result supports failure of that tested scalar readout to reproduce the gain. The index-sum result does not establish failure of a physical unresolved spatial image. Neither implies that order labels alone cause the entire gain.
Preserve level dominance, family heterogeneity, baseline saturation, failed multi-feature recovery, zero stable morphology span, and withdrawn posterior calibration. Preserve negative families. Existing tuned banks are not fresh confirmation. Neither bootstrap error bars nor numerical gates restore posterior calibration.
Acceptance: complete claim-occurrence map and retained negative statements. No new main bank or retuning in R0-R2.

## C11 - Contrast-only background assumption

Status: SCOPE_CONFIRMED; unknown-background companion pending.
Evidence: run_hmt2_sealed_main.py forwards bank[k]['fluct'] and masks m=0; the agent also traces drop_m0=True in separable_projection. Distinguish the reconstruction mask from the projection helper when building the dependency graph.
The primary physical end-to-end score is fidelity to the analytic contrast object under absent/perfectly removed background. It is not unrestricted recovery with an unknown data-estimated baseline. Retain the score. Restore all relevant baseline columns to the nuisance block for R2; do not use truth fields to estimate that background.
Acceptance: complete signal/background dependency trace and R2 nuisance manifest. No retrospective claim that the archived main solved this problem.

## C12 - Delivery, provenance and export

Status: DELIVERY_REPAIRED_BY_REPOSITORY_FILES; full reproduction/export review pending.
These four files are the operative R0-R2 package; no missing v4 helper or PDF is required. The prior local algebra report is not a physical gate and is not required to trust this protocol. New tests must report actual local execution.
Preserve freeze 022 and map the different uploaded PDF explicitly. A later revised PDF needs its own hash, source, claim ledger, accurate metadata and visual QA. Do not claim author review, test execution or artifact availability unless performed. Locate legacy reconstruction arrays without using them for new tuning in this phase.
Acceptance: append-only delivery, checked identities, actual test output and no dependence on sandbox paths.

## R0 output schema

For each C01-C12 emit: status, observed_ref, file_paths, blob_SHA_or_SHA256, runner_family, old_claim_IDs, observed_behavior, affected_claims, surviving_claims, new_alias, required_test, test_status, numerical_rerun_needed, prose_overlay_needed, blocker. Use UNRESOLVED where evidence is missing. A prose issue, code-extension guard, new scientific question and demonstrated numerical error are different statuses.
