# Movie006 execution amendment 002 — batched inverse resume

The amended physical construction completed and produced the frozen chart, independent ODE comparison, source bank, q8/q12 operators, and integration gates. The process was then terminated by the local 900-second command limit while evaluating the predeclared regularization candidates. It produced **no regularization selection, no test reconstruction, no movie span, and no success/failure endpoint**.

The completed physical/source/operator bytes are retained and will be read rather than recomputed. No further ray or ODE call is authorized or needed.

The inverse implementation is changed only algebraically and operationally:

- apply each candidate inverse to the complete validation observation matrix in one matrix multiplication rather than one history at a time;
- evaluate movie frames through one precomputed coefficient-to-frame matrix rather than repeated tensor contractions;
- use an eigendecomposition of the 595×595 source-normalized normal matrix for TSVD instead of a full rectangular SVD;
- checkpoint the frozen regularization selection before test evaluation;
- batch the fixed test histories/draws by arm, SNR, and method.

The source basis, physical rows, source movies, standardized noise draws, candidate grids, validation metric, thresholds, and test endpoint are unchanged. Batched and scalar formulations are required to agree on a fixed synthetic fixture before the resumed run. The initial timeout and all completed pre-outcome artifacts remain in the package.