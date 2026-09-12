# Movie014 preexecution amendment 001 — deterministic feature-library shortlist

Before generating any validation/test source, posterior beam, reconstruction, or endpoint, replace the computationally prohibitive instruction to score all 4,096 historical templates separately under every one of 16 background hypotheses by the following deterministic two-stage calculation:

1. score all 4,096 templates exactly under the direct-MAP background residual;
2. retain the best 32 templates from each of the four families (128 total), with stable index tie-breaking;
3. score all 16 x 128 background/template combinations exactly under the full direct-plus-order-1 objective;
4. retain and average the registered top eight joint hypotheses.

The full library, all families, parameter priors, amplitude optimization, posterior beam, source populations, metrics, thresholds, and success gate remain unchanged. The shortlist is fixed before outcomes and is reported as an approximation: a template outside the MAP-background family shortlists cannot enter the joint posterior. Validation/test truth, family labels, or reconstruction performance do not alter the shortlist rule.
