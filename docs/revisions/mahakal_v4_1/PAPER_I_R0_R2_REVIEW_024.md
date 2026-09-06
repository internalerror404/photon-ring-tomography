# PAPER_I_R0_R2_REVIEW_024

Reviewed repository: internalerror404/photon-ring-tomography  
Reviewed branch: research/mahakal_v4_1  
Reviewed commit: d15debbeefcaab31d56e2977805168d2782bd28b  
Delivery commit: 38e1f8a758e68d0bb272085bc826152d53996931  
Disposition: SCIENTIFIC_CANDIDATE_SUPPORTED_CLOSEOUT_REPLAY_REQUIRED

This is an author-directed project review, not a journal referee decision.
No repository files were changed in this review. The review inspected connected
repository records and code, decoded the committed spectrum file, verified its Git
blob identity, and recomputed its trace totals and operational counts. It did not
rerun Kerr operators or the reported 513-test suite.

## 1. Scientific finding

The saved results support the narrow positive finding under the declared finite
model. For the 72 target coefficients and the 152 remaining nuisance coefficients
of full L224 at spin 0.5, inclination 50 degrees and normalized SNR 100:

- DIRECT_PHYSICAL: normalized Fisher trace 0, before and after nuisance profiling.
- RESOLVED_PHYSICAL: known-remainder trace 11.0536601416515; profiled trace
  7.198318097661488.
- Profiled-to-known trace ratio: 0.651215796886804.
- Operational counts at unit target amplitude and rho=1: direct 0 to 0;
  resolved 3 to 2.
- Leading resolved profiled singular values:
  1.4371649013558634, 1.3458732686433825, 0.8062804378838909.

These numbers are sums of squared singular values, i.e. Fisher traces under
the declared source metric. They are not bits, mutual information, reconstruction
accuracy, a recovered fraction of the past, or proof of a movie. Two operational
directions means two source-function combinations at the stated threshold, not
two resolved events, frames, or hotspots.

The direct support-null statement concerns the specified sampled operator and
source functions. The target is disjoint from its direct retarded-time footprint.
The positive profiled spectrum concerns only the specified finite nuisance family
and ideal order-labeled acquisition at known geometry.

Proposed manuscript sentence after clean replay:
"At the reference Kerr geometry, a 72-dimensional compact old-contrast target is
exactly absent from the sampled direct image. Ideal order-labeled data retain two
operational target combinations at normalized SNR 100 after profiling the other
152 coefficients of the same full L224 source model. Profiling reduces the
normalized target Fisher trace from 11.0537 to 7.1983. This is a likelihood-level
information result, not a reconstruction result."

## 2. Accepted records and qualifications

The work branch is the appropriate branch; no merge or rewrite of the delivery
branch is required. The delivery-to-result Git comparison contains additions only
and no modifications of existing files. The submitted preservation manifest
reports all thirteen frozen deliverables matching their pinned digests.

Accept the ten physical normalization-site inventory and the correction of
absolute numerical rank versus operational fraction. The original six paths were
search seeds; the final operational record must use the completed inventory.

The count-only E3C audit reports exactly one crossing: a000_i020,
PAIRING_DESTROYED, SNR 100, age 48 M. No physical-arm endpoint changes in that
reported audit. Preserve both the crossing and the corrected nonlinear J_old
values in the new diagnostic record. PAIRING_DESTROYED is a nonphysical control,
not a claim-free artifact: the paper makes quantitative statements about it.

The exact Kronecker factorization of the source Gram does not make its midpoint
quadrature entries exact. Retain the reported refinement error and model-norm
qualification. Background amplitudes are included in this L224 nuisance analysis;
an unknown-background reconstruction companion remains unperformed.

## 3. Why blanket completion is not yet accepted

### 3.1 Execution and preexecution freeze

The report uses the R0 starting commit as the entire campaign execution commit.
The inspected provenance file is explicitly phase R0. The R1 code freeze does not
list scripts/revision_v4_1/r2_conditional_information.py or its R2 target manifest.
The R1-to-R2 Git comparison first adds the runner, target manifest and results
together in the result commit.

Writing the target manifest inside the runner before its SVD is a useful sequencing
property, but is not the committed preexecution snapshot required by amendment 023.
There is no inference of fabrication here and no mathematical refutation. Record
the deviation honestly and do not backdate or relabel the original execution as
fully prospective. Perform one clean numerical replay from a complete committed
snapshot. This is numerical reproducibility, not a fresh independent experiment.

### 3.2 Inventory versus migration evidence

The migration map says 10/10 sites covered, but several entries say "migration
recorded", "not separately replayed", or similar. G06 checks that site names occur
in the map. G02 uses a random algebra fixture rather than ten runner-specific
physical paths. Therefore 10/10 is inventory coverage, not evidence of ten
integration-tested migrations.

Keep the E3C physical replay result. Classify other sites by evidence level:
INVENTORIED, ALGEBRA_EQUIVALENT, PHYSICAL_REFERENCE_REPLAYED,
PRODUCTION_INTEGRATION_TESTED, DEFERRED, or RETIRED_NOT_REPLAYED.
A scoped exemption is not a test pass. Closed historical main experiments need
not be rerun. Any active path called repaired needs a constructor-level integration
test; no new truths or estimator tuning are authorized.

### 3.3 Completion status and tests

r2_conditional_information.py detects an unresolved condition but returns success.
r2_report.py selects the completion token from operational-count agreement, without
requiring all relevant prerequisite outcomes, metric promotion, nuisance-rank
agreement, and input-freeze validation.

The saved data appear to meet the reported numerical conditions, but the status
generator would not reject every required failure. Repair it and add fault
injection tests. G11 and G14 also use 1e-9 assertion thresholds where the protocol
declares 1e-10 for the relevant well-conditioned fixtures: restore the declared
criterion and report actual residuals instead of retroactively relaxing it.

Trace contraction alone is weaker than positive-semidefinite matrix contraction.
Use full Fisher-matrix checks in small fixtures for the relevant invariance and
profiling tests. Numerical issues must lead to an explicit unresolved/blocked
status, not an unconditional favorable result paragraph.

## 4. Authorized next action

R2 closeout repair and ONE clean reference-geometry numerical replay are authorized.
Use R2_CLOSEOUT_024.yaml. Preserve all original artifacts. Commit a complete
input snapshot, target manifest and gate tests before replay. Keep the same target,
source/nuisance model, noise, quadrature sequence and tolerances. Compare all
saved spectra and traces, using absolute rather than relative errors near zero.
Do not tune a changed result back to the previous answer.

Export the three leading right singular vectors and their source-coefficient
representations from that same operator. Include same-direction known/profiling
information, threshold margins, and subspace comparisons. Label them signed
source perturbations, never recovered histories. This completes the missing
direction-level interpretation without creating a new reconstruction campaign.

A metadata-only R3 readiness inventory is also authorized: the reduced OrderRays
lacks alpha/beta, but the raw RayMap schema and HDF5 reader retain alpha, beta,
pixel_area, valid, coordinate_time and delay. Verify the actual archived HDF5
fields, grid geometry and retained-index lineage before deciding new geodesics
are necessary. Metadata availability does not itself validate sky interpolation,
order summation, or detector covariance.

No new geometry, nuisance enrichment, physical common-sky spectrum, reconstruction
bank, learned estimator, VLBI experiment, or submission freeze is authorized by
this review. Stop after the closeout report.

## 5. Primary evidence inspected

All paths below are at reviewed commit d15debbeefcaab31d56e2977805168d2782bd28b.

Artifact prefix:
artifacts/revisions/mahakal_v4_1/R0_20260906T070540Z_38e1f8a/

- R0_R2_REPORT.md
- provenance.json
- R1_CODE_CONFIG_TEST_FREEZE.json
- R2_TARGET_AND_NUISANCE_MANIFEST.json
- calibration_migration_map.json
- reference_geometry_information.csv
- nuisance_adjusted_spectra.npz
- threshold_crossings.csv

Source and test paths:
- src/phrt/revision_v4_1/conditioning.py
- src/phrt/revision_v4_1/source_metric.py
- scripts/revision_v4_1/r2_conditional_information.py
- scripts/revision_v4_1/r2_report.py
- scripts/revision_v4_1/r1_migration_and_freeze.py
- tests/revision_v4_1/test_r1_gates.py
- src/phrt/geometry/raymap.py

The copied spectrum bytes match Git blob
c15d4b0725d00efa508420db05b9f7fc16e676dc.
The separate arithmetic-check JSON records the recomputed values.
