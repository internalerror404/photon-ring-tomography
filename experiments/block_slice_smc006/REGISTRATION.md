# BLOCK_SLICE_SMC_006 — prospective within-family exploration benchmark

**Date:** 2026-09-13.  
**Status at freeze:** nine model-free software fixtures pass; no 006 dataset, optimizer, posterior particle, evidence estimate, coverage result, or benchmark endpoint exists.  
**Authorization:** the user explicitly instructed the Mahakal Paper-II master thread to continue with the next experiment.  
**Canonical numerical parent:** `KNOT_QUADRATURE_002_PASS`, completion commit `c783d46d0567a6300ce99c2fdedfe55051b91ffd`.  
**Immediate algorithmic parent:** local provisional `FAMILY_STRATIFIED_SMC_005_COMPLETE_DIAGNOSTIC_FAIL`; its compact completion, adjudication, source freeze, local Git receipt, and full-package SHA-256 are frozen under `provenance/`. The parent remains a failure and is not rewritten or promoted.

## 1. Purpose and scope

005 showed that explicit family populations repaired the simple 2D benchmark but did not meet the 8D posterior-mean and family-probability limits. A postplanned exact-family-weight diagnostic left the 8D posterior-mean error above threshold, implicating inadequate **within-family exploration** rather than family allocation alone.

006 tests one bounded remedy: a reversible, coefficient-independent, two-dimensional blocked slice mutation inside each conditional family SMC. It compares that kernel with the preserved 005 random-walk/independence kernel under a matched two-run, matched-particle design. This is **algorithm calibration only**. It imports no Kerr arrays, generates no physical history or photon observation, and cannot create a movie-span, identification, differential-recovery, or physical-coverage claim.

## 2. Fresh known target

Use the unchanged 005 target and priors so the kernel change is isolated:

- two family labels with prior probabilities `(0.4, 0.6)`;
- eight unit-cube continuous parameters arranged as four 2D blocks;
- only block zero carries family offset `(0.0, 0.6)`;
- each block predicts `(b, b+h)` with Gaussian standard deviations `(0.18, 0.22)`;
- optimizer/proposal surrogate adds fixed block bias `(+0.025, -0.035)`;
- terminal native likelihood has no surrogate bias;
- all eight coordinates and the family are inferred.

Generate **64 fresh 8D datasets** from root seed `2026091321`, with per-case seeds drawn before simulation. A dataset is generated once and shared by all six method readouts. No case may be rejected, replaced, rescaled, or admitted based on reconstruction or sampler performance.

The reference posterior is calculated independently by tensor Gauss-128 integration of each 2D block and exact factor recombination. The sampler receives no true parameters, family labels, reference moments, reference family masses, or reference evidence.

## 3. Matched methods

Every conditional family run starts from the same proposal construction used in 005: one bounded least-squares fit at the all-0.5 point, a normalized Student-t/logit mixture with defensive uniform component, two adaptive SMC bridges, CESS 0.8, and at most 80 stages per bridge. Each run uses 128 particles per family.

### RWM control

`RWM128_A` and `RWM128_B` are independent executions of the preserved 005 conditional random-walk/independence mutation kernel. `RWM_POOLED` combines the two independent runs by averaging evidence in **linear evidence space** and pooling each conditional posterior in proportion to its run-level evidence estimate. This gives 256 terminal particles per family in the pooled control.

### Block-slice primary

`SLICE128_A` and `SLICE128_B` are independent conditional-family SMC runs. At every SMC stage, each particle receives two complete sweeps over fixed parameter blocks `[0:2]`, `[2:4]`, `[4:6]`, and `[6:8]`.

For each block:

1. transform the current particle to unit-cube coordinates;
2. draw a direction preconditioned by the frozen optimizer covariance transformed to unit-cube coordinates;
3. calculate the full line segment that remains inside `(10^-9, 1-10^-9)^2`;
4. draw the slice height from the exact current bridge target;
5. sample uniformly from the current line interval and shrink around zero until accepted, with a fixed cap of 80 shrink evaluations;
6. keep the original particle if the cap is reached and record the failure.

The first-bridge density is evaluated with respect to unit-cube measure as

`(1-t)(log q_y - log|du/dy|) + t log L_surrogate`,

up to the conditional-family prior constant. The native bridge uses

`log L_surrogate + t(log L_native - log L_surrogate)`.

Thus the mutation leaves the declared bridge target invariant; the surrogate does not replace the terminal native target. No step size, block layout, sweep count, or shrink cap is selected from outcomes.

`SLICE_POOLED` uses the same linear-evidence pooling rule as the RWM control, yielding 256 particles per family. The two pooled methods therefore have matched nominal terminal particle counts and matched numbers of independent runs, although their likelihood evaluation counts and wall times may differ and must be reported.

## 4. Registered diagnostics and gates

For each individual run and pooled method, report:

- average and worst largest-coordinate posterior-mean error;
- average maximum family-mass error;
- average log-evidence error;
- ten-bin rank chi-square for all eight parameters and joint native log likelihood;
- exact-count empirical 90% and 95% marginal coverage;
- terminal weight ESS, maximum weight, unique states, stage counts, likelihood calls, slice attempts/evaluations/failures, and wall time.

The unchanged per-method reference gates are:

- mean largest-coordinate posterior-mean error `< 0.04`;
- worst posterior-mean error `< 0.15`;
- mean maximum family-mass error `< 0.04`;
- every rank chi-square below `chi2_9(0.999)`;
- for every coordinate, `|coverage90 - 0.90| < 0.10` and `|coverage95 - 0.95| < 0.075`, evaluated with exact rational counts so equality at a strict boundary fails.

Independent-run agreement is evaluated separately for RWM and block-slice:

- mean across datasets of the maximum coordinate difference between A/B posterior means `< 0.03`;
- mean maximum A/B family-mass difference `< 0.03`;
- median absolute A/B log-evidence difference `< 0.15`;
- 90th percentile absolute A/B log-evidence difference `< 0.50`.

The primary 006 gate requires **both**:

1. `SLICE_POOLED` passes every reference gate; and
2. the block-slice A/B agreement panel passes every agreement gate.

The RWM control may pass or fail and never determines the primary disposition; all its results remain reported. A completed primary pass returns `BLOCK_SLICE_SMC_006_BENCHMARK_PASS`. A fully completed but failing primary returns `BLOCK_SLICE_SMC_006_COMPLETE_DIAGNOSTIC_FAIL`. Any exception, missing dataset, incomplete method, source mismatch, or timeout returns `BLOCK_SLICE_SMC_006_INCOMPLETE`; no subset is promoted.

A 006 pass qualifies this algorithm only on the declared 8D reference benchmark. It does **not** qualify the physical posterior or release a new movie experiment. A physical successor still requires a distinct source freeze, fresh paired histories across all background families, native direct/order-1 likelihood counted once, multiple retained background histories, calibrated 90/95% movie uncertainty, and the original 12M/95%, identification, differential, family, and fitted q8/q12 gates.

## 5. Provenance, resources, and preservation

- actual source, this registration, parent records, and software-test record are hash-frozen before the first 006 dataset;
- pre-outcome source is deposited on a new GitHub branch before execution;
- four CPU workers, one BLAS thread each, 1800-second supervisor cap;
- zero new Kerr calls, zero Paper-I units, and no external writes from experiment code;
- save every generated dataset, optimizer, individual and pooled particle bank, conditional evidence, SMC-stage record, slice diagnostics, completion/failure, audit, and hashes;
- no post-outcome source repair is allowed inside 006; implementation defects are preserved and require a separately registered successor;
- Paper I remains frozen at `084fb45fedae99f203393dbc1e9cdda9ab250c2d`;
- original Movie009-R2 provenance remains unrepaired;
- the 003 physical eight-observation point-reconstruction canary remains provisional and is not reclassified by this algorithm benchmark.
