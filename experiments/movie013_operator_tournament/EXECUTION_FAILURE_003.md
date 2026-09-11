# Movie013 execution failure 003 — DCT gate included a boolean as the value 1

The exact-replay rerun reproduces the archived in-basis and off-basis baselines to floating-point precision and writes deterministic scientific tables. Its DCT records show Gram and right-hand-side disagreements of approximately `5e-16` to `1.1e-15`, with zero coefficient and movie disagreement under invariant normal equations.

The summary reducer nevertheless reports `dct_max_disagreement=1.0` because Python booleans are numeric subclasses and the reducer included the metadata field `invariant_normal_equations: true` in a numeric maximum. This is a summary-only type-filter defect. The corrected reducer excludes booleans and evaluates only discrepancy fields; no operator, source, noise, selected hyperparameter, reconstruction, metric, or winner outcome changes.
