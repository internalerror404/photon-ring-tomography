# Mahakal II Movie008 — direct-null twin movie recovery

**Return:** `MOVIE008_DIRECT_NULL_TWIN_IDENTIFICATION_PASS_MOVIE_FIDELITY_FAIL`  
**Registered movie gate:** FAIL.

Movie008 tests balanced positive historical twins whose q8 and q12 direct observations are exactly identical. The four target modes are frozen from a 210-dimensional old non-axisymmetric parent after profiling a declared 385-dimensional nuisance movie.

At SNR0=300 and target norm alpha=0.08, direct plus the first indirect image identifies the correct twin in 100% of 480 held-out sign/draw cases. Median and 90th-percentile four-mode coefficient errors are 0.270 and 0.403, clearing their registered gates. Direct-only data remain at the exact balanced 50% identity limit.

The strict frame-by-frame endpoint fails: only 12.92% of labelled cases pass every active old frame, against the registered 95% requirement. The supported result is therefore causal twin identification and low-dimensional coefficient recovery—not a 95%-reliable movie at the registered amplitude.

Start with `RESULTS.md`, `COMPLETION.json`, and `REPORT.md`. Compact numerical tables and the postplanned signal diagnostic are under `results/`. The complete binary inputs, sources, estimates, frame metrics, visualizations, and logs are in the delivered full artifact whose hash is recorded in `SOURCE_AND_ARTIFACT_HASHES.json`.

No new physical ray calculation or Paper-I unit was used. The scalar execution timeout and the pre-outcome batched replacement remain recorded in the lineage.
