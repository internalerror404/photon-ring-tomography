# Mahakal reviewer-response EPC1 and LBR1: actual pre-outcome registration

Date: 2026-09-21. No EPC1 or LBR1 outcomes exist at this commit. Original source/configuration, independent checker, registration and environment are in the source capsule below. The complete input manifest and source snapshot were published in the current conversation before execution as Mahakal_Reviewer_Tests_PREOUTCOME_20260921.tar.gz. This record does not claim that large inherited data are deposited remotely.

## Exact source reconstruction

Read source_transport/SOURCE.b64.00 (Git blob d4039b0629bff18085a3a52f43c8d610b36b7dc3) and SOURCE.b64.01 (Git blob c363fe872eb18446538632900b3ce537fac36ef1) as ASCII. The first transport chunk contains one known transcription error, detected before any experiment: replace the exact substring `2fsp542i9wRSSm` by `2fsp542i9wR6m` once, requiring one occurrence. This restores the first chunk to 9404 bytes with Git blob 5f9cfc1fbca817c739a776e2eed23dc9afde07e4. The second chunk is 9404 bytes and requires no correction. This is an explicit transport repair, not a scientific source change or an outcome-dependent amendment.

Concatenate the corrected first and exact second chunks and base64-decode. The gzip-tar capsule must be 14106 bytes with SHA-256 af27657ff650c20dc26032b8993a90a026d3905db90137bf7516de4adea9032c. Extract only safe relative paths. Read REGISTRATION.md and config.json completely. FREEZE.json has SHA-256 f6380c3feeff75cec97f57a7ed6ed793cdff2ce402be14d279d1240684d0e0b3 and binds every executable/configuration file plus INPUT_MANIFEST.json (116093 bytes; SHA-256 f9515b917c5be9b32aeb1f8c264684f4211fda4c170af2124004a7a97c0ace05). The full manifest is in the pre-outcome conversation package, not this compact capsule. Actual source was locally committed at bc61baa4f28f318e44e71e32c6b2432ea41fdc6e before outcomes.

Execution remains blocked until immutable commit readback verifies the transport identities and reconstructed source/archive/member identities. Write the resulting REGISTRATION_READBACK.json only after those checks. The runner authenticates every registered input and refuses an already-used output directory.

## Scope

EPC1: all 256 existing C1 datasets, two new exact-posterior-bank replicates, 512 particles per family, six region-construction arms, 32768 independent evaluation samples per family and 5000 dataset-bootstrap resamples. This is a diagnostic on previously examined C1 cases, not new population confirmation and not a new candidate sampler run. It separates finite-bank region construction from discrepancy of saved candidate posterior banks.

LBR1: 60 fresh in-class histories, no response/activity admission filter, the authenticated KNOT 595D finite operator, ten fixed ridge/TSVD/acquisition/SNR settings, 32 paired noise draws per history. The actual q12-mean/q8-inverse bias and noise-variance predictions are sealed before observation noise is generated. No estimator is selected by outcomes. Secondary frame/pass statistics do not release the inherited physical movie claim. This is NOT a Movie007 replay: original Movie007 per-history arrays remain unavailable.

Both experiments retain exact sources, seeds, thresholds, errors, partial outputs and failures. No reseeding, widened thresholds, silent retry, new ray tracing, continuum integration, or Paper-I units. Paper I stays at 084fb45fedae99f203393dbc1e9cdda9ab250c2d. Historical records remain unchanged. C2 calibrated physical-posterior release and evidence-only FAMILY_EVIDENCE_BRIDGE_007 remain HOLD. Failed 006R adequacy is not revived. The missing original Movie009-R2 records remain missing.
