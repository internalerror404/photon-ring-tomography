# Mahakal II Movie008 — direct-null twin result

**Return:** `MOVIE008_DIRECT_NULL_TWIN_IDENTIFICATION_PASS_MOVIE_FIDELITY_FAIL`  
**Registered gate:** `MOVIE008_DIRECT_NULL_TWIN_MOVIE_FAIL`

At SNR0=300 and registered target norm alpha=0.08, direct observations are byte-identical between both positive twins and yield the balanced 50% identity limit. Direct plus order 1 identifies the correct twin in 100% of 480 held-out sign/draw cases. The nuisance-profiled four-mode estimate has median relative coefficient error 0.2700 and 90th-percentile error 0.4034, clearing both registered coefficient gates.

The strict frame-by-frame movie endpoint fails: only 12.92% of labelled cases pass every active historical frame, against the registered 95% requirement. Movie008 therefore establishes causal twin identification and low-dimensional historical-target recovery, not a 95%-reliable reconstructed movie at alpha=0.08.

All three two-/three-/four-mode complexity groups have 100% labelled twin identity. Their movie-pass rates are 13.75%, 11.25%, and 13.75%. Direct-only target outputs are identical and zero by construction.

Numerical and construction gates pass: q8/q12 direct response is exactly zero, paired noisy direct observations are identical, the minimum labelled q12 twin separation is 14.372 whitened units, maximum q8/q12 twin discrepancy is 1.402e-4 relative and 2.021e-3 whitened, the analytic minimum emissivity bound is 0.7215, and scalar/batched replay agrees to floating-point precision. No physical call or Paper-I unit was used.

The postplanned same-test signal diagnostic is retained separately and cannot upgrade this result. It suggests the strict all-frame criterion is signal-limited and motivates a fresh, separately registered successor—not reinterpretation of Movie008.
