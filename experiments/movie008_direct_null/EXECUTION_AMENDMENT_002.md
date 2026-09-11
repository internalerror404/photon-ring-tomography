# Movie008 execution amendment 002 — batched algebraic resume

The first post-mode-bank process reached the local 600-second command limit before writing any fresh source, noise, estimate, table, summary, or movie endpoint. The separately frozen mode bank remains the only Movie008 scientific output on disk.

The source/noise generation, q8/q12 inputs, four-mode bank, 210/385 target–nuisance split, amplitudes, SNRs, paired-noise construction, estimators, thresholds, bootstrap population, and success gate remain unchanged. The execution path is replaced only as follows:

- construct all 480 pair/sign/draw cases in fixed deterministic arrays;
- apply the already factorized conditional GLS, ridge, and TSVD maps to complete case matrices instead of one vector at a time;
- evaluate the four frozen mode movies in batches rather than repeating the 595-to-frame contraction per case;
- reuse the SNR300 ridge/TSVD factorizations under the exact global SNR scaling;
- store estimates as dense arrays with explicit pair/sign/draw metadata rather than thousands of separate NPZ members;
- require scalar/batch equality on one fixed SNR300, alpha=0.08 case for conditional GLS, ridge, TSVD, and movie metrics before any completion record is written.

The corrected executable source is committed before rerun. No physical calls or Paper-I units are authorized. The timeout and its empty scientific output remain recorded rather than hidden.
