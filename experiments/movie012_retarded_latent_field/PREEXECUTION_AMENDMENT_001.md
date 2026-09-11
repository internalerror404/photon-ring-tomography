# Movie012 preexecution amendment 001 — observation compression

Before generating any source bank, latent source basis, network weight, validation score, or test outcome, add one deterministic training-only preprocessing step for computational tractability: after row-wise standardization, fit a rank-256 randomized PCA of the training observations separately for the direct and labelled arms, seed `120091`. The two 256-dimensional scores, not the raw 832/1664 vectors, enter the registered two-hidden-layer neural encoder.

The physical q8 data-consistency term is evaluated after mapping the predicted latent movie through the full frozen response matrix and then through the same orthonormal observation-PCA projection. This is an explicitly projected q8 residual, not claimed to be the full data residual. Full q8/q12 fitted-response discrepancies remain mandatory at evaluation and are unchanged.

No source count, family, physical row, latent rank, network hidden width, epoch count, threshold, test population, or success gate changes.