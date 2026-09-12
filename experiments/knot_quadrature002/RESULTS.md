# KNOT_QUADRATURE_002 - numerical integration gate passed

Status: `KNOT_QUADRATURE_002_PASS`. Registration and all five actual source files were committed before physical outcomes at `c0ac7e314bc10b2624cf6ff9f54856405ad9a951` on `research/mahakal_II_knot_quadrature002_20260912`. This is a new same-pixel integration experiment, not the missing R2 execution and not a movie-recovery result.

## Primary comparison

| Method | Basis checks | Failed checks | Maximum relative q8/q12 difference | Maximum whitened q8/q12 difference |
|---|---:|---:|---:|---:|
| Original unsplit CACHE001 | 1785 | 142 | 0.134129143807 | 0.173855776113 |
| Uniform 2x2 subdivision control | 1785 | 34 | 0.022405788625 | 0.0184267377857 |
| Knot-aware composite q8/q12 | 1785 | 0 | 1.59813073478e-11 | 5.62463703352e-11 |

Every column-arm check uses BOTH unchanged thresholds: relative L2 <=5e-4 and whitened L2 <=0.1. The 595 basis columns are checked in direct, first-indirect and stacked data separately. No difficult columns were removed, no amplitudes rescaled, and no thresholds relaxed. The original 142 failures remain in their original experiment; the uniform control's 34 relative-criterion failures are preserved here.

## What changed

The new quadrature splits at source-basis breakpoint contours before integrating each subpanel: the union of temporal-hat delay levels for every observer time, plus the internal radial knot. All split decisions are independent of source coefficients and historical labels. The detector still has 64 pixels per order and 13 times. Noise calibration, source basis and support weights remain frozen. q8 and q12 here mean local composite rules, not the old unsplit tensor rules. Additional numerical ray evaluations do not create additional observed pixels or photons.

Uniform refinement also improves the absolute discrepancy and clears its whitened criterion, but it does not clear the full registered panel. The breakpoint-aware method clears both criteria for all columns. This supports a practical numerical integration remedy on this new finite basis. It does not isolate temporal knots from the included radial-knot partition, demonstrate equal-compute superiority, identify the sole cause of original R2's failure, or establish continuum accuracy.

## Analytic fields and direct-null preservation

178 analytic numerical probes are tested: the original 89 plus 89 freshly generated from frozen seed 2026091204. There is no response-based admission. For each method, all 534 field-arm comparisons pass. Knot-aware maxima are 1.06488441111e-06 relative and 1.03328826232e-05 whitened. Uniform2 maxima are 2.35031626913e-07 relative and 2.06076658964e-05 whitened. Thus knot-aware is not claimed best on every analytic metric; both are qualified on this panel.

All 128 compact historical-feature probes have exact-zero direct responses under both rules and both new methods. Pixel-area checks against the same frozen reference pass for every pixel. Saved operator readback is exact.

## Resource accounting

The complete run used 404087 new separated ray calls (cap 600000), with 51911 memoized hits and 808174 BEGIN/END events. The core run took 312.568581 seconds; peak resident memory 448664 KiB. It used one BLAS thread, float64, and no new ODE calls; the identical solver's earlier 64-point ODE validation is reused only as prior finite evidence. Paper-I units: 0. Movie fits: 0. Posterior fits: 0.

Knot quadrature nodes: direct q8=20480, direct q12=46080, order1 q8=41472, order1 q12=93312. Uniform2 has 16384 nodes per q8/order and 36864 per q12/order. These are not equal-work comparisons; contour searches also consume logged ray calls.

The finite source-norm operator discrepancy diagnostic is 1.83236584837e-11 for the knot-aware rule versus 0.0100738257947 for uniform2. This is the spectral norm of the difference between two discrete operators on the declared source-norm unit ball, not an error certificate relative to the true continuum operator.

## Release and scientific boundary

The numerical primary gate passed. A separately source-frozen inference successor must still check its actual clean and fitted fields, marginalize the joint unknown background/history distribution, calibrate coverage, and meet the unchanged 12M/95%, identification and differential-movie gates on fresh histories/noise. A different PCA/interpolated decoder has different knot surfaces and is not automatically qualified by this basis test. Original R2 provenance remains unrepaired and no prior movie claim is revised.

The complete binary package contains all frozen inputs, source, nodes/weights, operators, partitions, numerical panels, ledger and logs needed to reproduce this new stage. GitHub contains readable source, registrations, compact result/audit records and artifact hashes. Binary presence in GitHub is not implied. See CACHE_INTERFACE.md for the variable-node-count consumer contract and NEXT_STAGE_DRAFT.md for unregistered scientific-stage constraints.

## Independent postplanned readback

The no-new-physics audit returned `POSTPLANNED_KNOT002_READBACK_PASS`. It verified all 808174 ledger events and 404087 completed calls, matched all 307840 saved numerical nodes to their recorded physical tuples, replayed 3570 basis and 1068 analytic comparisons, and found zero changed gate decisions. Maximum analytic metric difference was 1.08570397948e-11; basis metrics reproduced exactly. Thirty-two random complete-field contractions agreed within 6.28837260042e-18. Source/input hashes remained unchanged. This validates recorded computation and independent accumulation, not independent source physics or a continuum-error theorem.
