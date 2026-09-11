# Movie013 execution failure 001 — direct old-target scale is exactly zero

The first execution authenticated every input, reproduced the Movie007 validation choices, passed the baseline/DCT mechanics through validation, built the exact nested q8/q12 operators, and then stopped during O3 validation before any held-out tournament result was produced.

For the direct-only arm, the registered old temporal target has exactly zero response. Its trace-derived target ridge scale is therefore exactly zero. The generic two-block Woodbury routine divided by that zero scale, produced nonfinite candidates, and correctly failed with `no block candidate`.

This is an implementation-domain defect, not a scientific result. The direct O3 estimator is uniquely defined for this case by setting its unobservable old-target estimate to zero and selecting only the nuisance ridge exponent; the labelled arm retains the registered 5x5 old/nuisance grid. No source, noise, operator, threshold, family, metric, or test endpoint changes. The failed local record and source hash are preserved, and corrected source is re-frozen before rerun.
