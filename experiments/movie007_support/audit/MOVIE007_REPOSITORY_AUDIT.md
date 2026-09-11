# Paper II repository audit before Movie008

Reviewed branch head `60caf340c90d8ea5c64d792cc1f2e1d7e23af2a1` and the complete delivered Movie007 artifact.

## Result

Movie007's reported arrays and summary are internally reproducible. The full package manifest has 49 entries and zero hash/size mismatches. Independent algebraic replay recovered the frozen regularization choices, all eight reconstruction matrices, and the per-history/per-frame metrics to the numerical differences recorded in `MOVIE007_REPOSITORY_AUDIT.json`.

Sixty-four independently regenerated Kerr tuple/weight checks match the stored q8/q12 arrays bitwise. The recorded ODE, clean-response, and fitted-response gates pass.

## Critical design finding

The 595-dimensional movie basis contains a 210-dimensional old, non-axisymmetric subspace on which both q8 and q12 direct operators are exactly zero. The first-indirect q8 operator has numerical rank 183 on that subspace; its top six source-normalized singular values at SNR0=300 are:

`269.101541, 268.371770, 267.033200, 264.482169, 235.464221, 232.086586`.

This supports a zero-new-ray direct-null twin experiment.

## Repository gaps and limits

- Movie006 has no committed final movie endpoint.
- Movie007 has registration, amendments, freezes, compact results, and artifact hashes in GitHub, but its exact executed source bytes were only hash-frozen and shipped in the full artifact; they were not deposited in the repository before this audit.
- There is no CI/check-run record for the Movie007 head.
- Movie007's primary union-support metric combines historical-time extension with new source-plane coverage.
- The positive result is in-basis at SNR0=300; SNR0=100 and off-basis movie spans are weak/zero.
- The actual family source streams used deterministic per-family seed offsets; this should be recorded explicitly.

## Movie008 consequence

Movie008 should not repeat the union-support comparison. It should freeze exact direct-null old movie modes from q8, validate direct nullness and order1 response at q12, generate balanced positive twin histories only afterward, and test whether the frozen estimator recovers the correct twin/movie from labelled data while direct data remain identical.
