# Movie009-R4 preexecution amendment 001 — common joint-refinement convention

Before fitting any R4 PCA representation or evaluating any endpoint, apply the Movie009-R3 validation-selected joint-refinement exponents `(-2,-2)` to every representation after its validation-selected latent-ridge estimate. The supplied true background is the joint-refinement centre, not a hidden test-dependent fit.

This common convention is necessary for `UNWEIGHTED_PCA_R96` to reproduce the R3 `true_background_latent` diagnostic exactly. It also prevents each representation from receiving a separate 5x5 trust-parameter search, so the tournament changes only PCA weighting/rank and the representation-specific latent-ridge exponent.

Also report a frozen-background latent-only diagnostic for every representation. It is secondary and cannot replace the registered joint-refined primary result. No source, noise, PCA rank, weighting rule, metric, numerical gate, or success threshold changes.