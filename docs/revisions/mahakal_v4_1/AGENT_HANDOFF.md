# Agent handoff - Mahakal v4.1 / R0-R2

Read PAPER_I_DEFECT_AMENDMENT_023.md first. It is the author-directed permission to conduct this NEW correction campaign without changing freeze 022. Then read CORRECTION_LEDGER.md and EXPERIMENT_PROTOCOL.yaml. These are sufficient inputs; the earlier client-local package, working PDF and helper code are not prerequisites.

## 1. Repository state and output isolation

Repository: internalerror404/photon-ring-tomography.
Delivery branch: research/hmt2_resolution_aware_feature_measure_v0.
Inspected remote base: 7961e5bd7d46be23885151afa7664596cc58cfa6.
Submission record: artifacts/configs/PAPER_I_SUBMISSION_FREEZE_022.json.

Fetch the delivery commit. Record local HEAD, remote HEAD, branch and tracked/untracked state. If the local worktree has additional commits or changes, do not reset, rebase, clean, stash or overwrite them automatically. Reconcile ancestry and use a separate worktree if necessary. Stop on conflicting local governance records, not merely on additional unrelated files.

Create a revision work branch from the reconciled state for code execution. The document delivery branch need not be the compute branch. New source, runners and tests go in src/phrt/revision_v4_1/, scripts/revision_v4_1/ and tests/revision_v4_1/. New results go in artifacts/revisions/mahakal_v4_1/<unique_run_id>/. Never replace a previously emitted run directory. Freeze 022, its thirteen named deliverables, the 591-artifact historical freeze and original tables/banks/gates remain unchanged. Reproduction against old code can use a read-only worktree at the old commit.

Before running any inherited script, audit its outputs: many legacy scripts write canonical paths or merge old gate ledgers. Do not invoke such a writer directly in the authoritative worktree. Use a versioned runner or a disposable isolated replay worktree with output redirection verified.

The initial authorization ends after R2 at spin 0.5/inclination 50 degrees. Do not start a fresh reconstruction bank, common-sky acquisition campaign, geometry mismatch or larger grid on the strength of the old v4 planning budget.

## 2. R0: trace all twelve items and write the correction overlay

Verify hashes of the thirteen submission deliverables and map claims to canonical artifacts. The uploaded PDF hash differs from the repository PDF in freeze 022: do not silently reconcile them. Code audits may proceed against the explicitly pinned repository version; unsupported claims of uploaded-PDF reproduction may not.

Write a twelve-item disposition JSON, a claim dependency CSV, and an additive manuscript/evidence overlay. Include all text occurrences of unresolved-image attribution and index-paired mechanism claims, including captions and derivative releases. Copy amendment 023's replacement meaning; do not rename keys inside old numerical tables.

Trace production reference calibration by AST/call graph and textual search of src/ and scripts/. Search snr_scale, s_ref, sigma_omega, from_snr, sqrt/mean and norm-based variants. Inventory every definition AND consumer. The six named physical runners in C02 are seeds; discovering the remaining sites is required. Classify the NoiseModel.from_snr call separately as toy/reproduction if the code confirms that classification. Its reference_rows is a slice, not the proposed count parameter.

For every physical result family record: runner path and blob, ray-map hashes, selected ray indices or reproducible selection seed, quadrature, observation times, direct row count, unit-reference response norm, s_ref, actual sigma, source design and dimension, mixer, collapse rule, covariance treatment, estimator filter scaling, output paths and claim IDs. HMT2's all-order flux and E3C's order-resolved flux must have separate rows.

Primary source paths include src/phrt/operators/physical.py, src/phrt/geometry/sampling.py, scripts/run_e3c_operator_grid.py, scripts/run_hmt2_sealed_main.py, scripts/run_hmt1_score.py, scripts/build_e3c_tables.py, the normalization sites found by discovery, and their registered configurations.

Missing map/bank lineage blocks reproduction of that result. It does not justify synthesizing a substitute with the same label. No new truth draw is required for R0.

## 3. R1: implementation must reach the physical paths

### 3.1 One shared reference-calibration object

Implement a versioned reference calibration taking clean direct-reference response, fixed reference count, reference-grid identity and noise label. It returns and serializes E=||clean||^2, m_current, m_reference, s_ref and sigma. Require positive finite inputs; zero response cannot define this SNR and must raise, not silently become 1e-300.

Use three explicitly named modes from C02. For common-count E3C, m_reference=12288 (1536 rays times eight fixed observer times) for every geometry. For HMT/R1-like campaigns, recover the declared nominal design count before the run; do not assume it equals E3C's. Freeze values before inspecting new information outcomes. Hold one sigma across all arms within a geometry.

A versioned runner must route the SAME physical constructor/signal path through this object. Emit a migration table from every discovered legacy calibration site to its revised entry point and integration test. A utility test, toy from_snr edit, or unused helper cannot mark the campaign repaired. Keep legacy entry points available for exact replay, preferably unchanged.

Tests must separate: legacy-grid replay; spatial subdivision at fixed sigma; subdivision with common-count recalibration; and the deliberately failing old recalibration formula. Changing observation times or exposure is not a quadrature-only subdivision.

### 3.2 Cheap archived-grid impact audit

Without recomputing geodesics, rescale the E3C stored information curves by m_reference/m_current and singular values by its square root. Confirm the reference norm, source space and noise convention are otherwise unchanged before using this identity. Rebuild masks at EVERY archived threshold/SNR, plus anchors, oldest passing age, longest run and anchor-connected span. Also rebuild log sensitivity integrals and information volumes from the rescaled curves/eigenvalues; J_old is nonlinear in that multiplier.

Record old/new values, signed threshold margins and crossing counts, especially a000_i020. Report unchanged endpoints only after this check. Save new tables; do not replace the frozen E3C JSON. The normalization factor alone does not change relative-threshold numerical rank in exact arithmetic, but can change an absolute operational threshold.

### 3.3 Full covariance and source metric

Support both raw A,C and an explicitly documented already-whitened operator. Never whiten or apply SNR twice. General mixing requires C_L=L C L.T, not its diagonal. Use small channel blocks or matrix-free operations where possible. Handle redundant stochastic support without adding a ridge or deleting informative noiseless constraints.

For source columns q_i on the declared annulus/time domain, use H_ij=integral(q_i*q_j r dr dphi dt). This is a chosen model norm. Factor by weighted QR/SVD or Cholesky when justified. For H=R.T R compute A R^(-1) with solves, not explicit inverses. Keep full Gram cross terms; separately normalized columns need not be orthogonal. Record quadrature rules, refinement, conditioning and any dependency removal. Proven zero functions/dependencies can be removed with a certificate; weak directions cannot be discarded because they hurt recovery.

Do not change old TSVD/ridge objectives while calling the result a replay. New metric-normalized estimators belong to a later campaign.

### 3.4 Registration and control guards

Add regression tests showing that equal lengths do not establish a common screen and that row reorderings can change index-paired substitutions. Preserve the original compression controls for replay; require explicit INDEX_* aliases in new reporting. A genuine physical-acquisition API must reject missing screen metadata. Do not invent alpha/beta values from array order.

Flux tests: E3C = 24 order-resolved rows; HMT2 = 8 all-order rows at the archived schedule. Independent within-order pixel permutation preserves their integrated flux. A single scalar at each of eight times has rank at most eight. The new general-covariance tests must not mislabel the old single-sum case a failure.

## 4. R2: one reference-geometry likelihood audit

This is an operator calculation, not a reconstruction or a new main experiment. Reuse authenticated maps at a*=0.5, i=50 degrees and orders 0,1,2. Keep geometry known and fixed. Primary noise label is 100 under the declared COMMON_REFERENCE_COUNT dictionary; emit a same-sigma legacy companion where needed to isolate normalization effects.

### 4.1 Define the target before looking at spectra

Primary source class: the existing localized L224 representation, including ALL baseline/m=0 columns in the full model. Use its registered annulus, temporal interval, source regularity and observation schedule. Freeze a source-function target/selection manifest before computing R2 spectra.

Primary target: coefficients of the non-axisymmetric compact temporal factors whose support is outside the direct retarded-time footprint, as determined by the registered support convention, not by a small measured singular value. Nuisance: EVERY other coefficient of that same full model, including old m=0 terms, recent emission and boundary-overlap factors. An exact support mask may depend on known geometry/maps, but never on a recovery score. Record the selection and number of target directions. An empty target is an outcome, not permission to choose another after inspection.

Use the same physical target, functions, observation times, noise dictionary and normalization across DIRECT_PHYSICAL and ideal RESOLVED_PHYSICAL. Include HMT2-style all-order integrated flux and E3C-style order-resolved flux as separately named diagnostic controls if their definitions are fully reconciled. INDEX_SUM_CONTROL is optional diagnostic only; neither index-paired substitution is a physical primary arm.

The h=3M Gaussian/28-function scalar-sensitivity replay is a separate known-remainder diagnostic, NOT silently the same target as compact old coefficients. Wider h and refined-age sweeps are deferred. A general old-window functional T may be implemented later: use TV=I, TN=0 and col(N)=ker(T), with a FIXED target metric; residualized information must be unchanged by V -> V+NK. Do not add overlapping Gaussian atoms plus a complete parent basis and ignore the resulting target ambiguity.

### 4.2 Compute known- and unknown-remainder spectra

Write y=A_o c_o+A_n c_n+noise, with actual covariance C. Let W whiten C, B_o=W A_o and B_n=W A_n. Set H_o=<q_o,q_o>, H_o=R_o.T R_o, and B_o,phys=B_o R_o^(-1).

Compute U_n, an orthonormal basis of col(B_n) using a rank-revealing factorization. An invertible nuisance-coordinate preconditioner (preferably from its source Gram) is allowed and must be recorded. Define:

    B_cond = B_o,phys - U_n (U_n.T B_o,phys)
    F_cond = B_cond.T B_cond
    F_known = B_o,phys.T B_o,phys

Use thin factors/block application rather than allocating I-U_n U_n.T. Zero nuisance columns are legal. With no nuisance, B_cond=B_o,phys. Use numerical rank tolerances 1e-13,1e-12,1e-11 and record all decisions; the primary is 1e-12 on the declared normalized factorization. Do not use an SNR cutoff or a ridge in the nuisance projector. The assumptions are unconstrained linear nuisance amplitudes at fixed geometry: no positivity-based global impossibility follows.

Report singular spectra of B_cond and B_o,phys, full target dimensions, kernel/near-kernel diagnostics, source Gram, projector rank, and operational counts at effect amplitude one and rho=1. Include absolute values, not only ratios. Align direction-by-direction comparisons before taking ratios; separately sorted spectra do not pair the same target vectors. For every physical result include the actual sigma and source norm units.

If tolerance choices change an operational conclusion or the projector's identified subspace is unstable, report NUMERICALLY_UNRESOLVED and stop that conclusion. Do not pick the favorable tolerance. Additional source-nuisance enrichment or geometry derivatives require a subsequent registered step.

## 5. Correctness gates and freeze discipline

Use CPU float64 and the repository's single-threaded numerical setup. Dense matrices are allowed for small algebra fixtures only. The physical audit should use blocked/matrix-free source and nuisance factors; any materialization requires an explicit memory/dimension audit, not a default full data covariance.

Freeze new source/runner/config/test bytes before outcome-bearing R2 computation. Algebra/debugging tests may precede that freeze. The protocol lists numerical tolerances and outputs; do not weaken them after a failure. Numerical gates verify an implementation, not novelty or favorable physics. No prior 18/18 local report counts as physical validation on this machine.

Required canaries include: SNR-squared scaling; both pixel-refinement conventions; full-covariance invariance; redundant/noiseless modes; source-basis reparameterization; old/recent identical responses giving zero conditional information; an independent recent measurement restoring distinguishability; invariance to nuisance-coordinate changes; conditional information no greater than known-remainder information; and preservation of old flux semantics.

## 6. Return contract and stop

Return: exact parent/delivery/execution commits and tree state; thirteen-deliverable verification and PDF lineage; all twelve dispositions; exhaustive calibration migration table; alias and text overlays; legacy/new sigma dictionary; all archived mask crossings; actual R1 results; source-metric convergence and dependencies; the R2 target/nuisance manifest and conditional/known spectra at the reference geometry; runtime/memory; hash manifest; and everything NOT RUN or blocked.

Do not call a textual correction a numerical rerun. Do not call a preserved result newly confirmed. Preserve zero/negative outcomes. Finish with one of R0_BLOCKED, R1_BLOCKED, R2_NUMERICALLY_UNRESOLVED, or R0_R2_COMPLETE_REFERENCE_GEOMETRY, plus scientific findings without a required sign. Then STOP for review.
