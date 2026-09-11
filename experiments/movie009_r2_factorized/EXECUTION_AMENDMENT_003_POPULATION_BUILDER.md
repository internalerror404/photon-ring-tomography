# Movie009-R2 execution amendment 003 — deterministic population-builder optimization

The source-population timeout was diagnosed before any accepted population file, PCA decoder, regularization choice, neural weight, reconstruction, or endpoint existed. A response-free replay of the registered source gate showed that narrow-hotspot and split/merge candidates are rarely active on at least nine measurement-supported old frames. The original implementation also projected the broad background before checking that feature-only activity predicate and stopped after only 50 candidates per required source.

The corrected population builder preserves the scientific population exactly as the first accepted candidates in the same deterministic RNG stream:

1. draw the same background and feature parameters in the same order;
2. evaluate the finite/activity gate, which depends only on the analytic old feature and frozen support weights;
3. project the already-drawn background only for activity-eligible candidates—background projection uses no RNG and enforces nonnegative total background before the positive feature is added;
4. retain the same positivity check for every accepted candidate;
5. increase the search cap from 50 to 5,000 candidates per requested source without changing the accepted-source ordering or conditional admission distribution;
6. stream candidate records to a compressed JSON-lines ledger rather than retaining hundreds of thousands of rejected dictionaries in memory.

The source families, parameter ranges, seeds, background-family schedule, analytic formulas, activity threshold, positivity rule, source counts, latent rank, physical operator, noise, estimators, validation selection, neural architecture, movie metric, and success gate are unchanged. No candidate is selected using order-1 response or reconstruction performance. The optimized source is equivalence-checked on a fixed development stream, syntax-checked, self-tested, and re-frozen before execution.