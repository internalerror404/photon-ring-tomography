# Movie013 execution amendment 003 — exact-sample replay and DCT closeout

The first completed `SUMMARY.json` is invalidated before scientific interpretation. Its in-basis O0/O2/O3 calculations are deterministic, but three closeout issues prevent the registered tournament gate from being evaluated as written:

1. the baseline aggregate comparator merged the new ridge rows against both archived ridge and TSVD rows, creating a false 0.0589 replay discrepancy;
2. the off-basis source parameters were exact, but the Gaussian stream was consumed as all order-0 histories followed by all order-1 histories, whereas the executed Movie007 source consumes order 0 then order 1 inside each history. The resulting off-basis tournament observations were not the registered archived samples and are superseded;
3. the orthogonal DCT Gram agrees with baseline at approximately 1e-15, but redundantly refactorizing two roundoff-different normal matrices amplified a validation coefficient difference to 5.9e-10. The corrected equivalence control transforms rows, verifies Gram and right-hand-side invariance, then uses the mathematically identical invariant normal equations rather than treating solver roundoff as an operator effect.

Superseded local hashes: `SUMMARY.json` 99078b3cc8220751db2e6237becc671b5ffc6e806a63f62ace3b93f39f75047e; `AGGREGATE.csv` 5f9386d7393fbd90944c21d70aa0c06efae15d1ddc8d8e62d4648fbba547fff9; `FAMILY.csv` 7ffb58bf48b8d81c5a96fd037fc11a75f63416672764aa5805e3a84ca117c0da.

No source history, source parameter, physical operator, regularization grid, selected in-basis hyperparameter, metric, threshold, or winner rule changes. All variants are rerun with the exact archived off-basis noise ordering; the superseded files remain preserved in the delivery record.
