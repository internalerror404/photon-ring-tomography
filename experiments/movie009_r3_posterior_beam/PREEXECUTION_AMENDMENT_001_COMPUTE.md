# Movie009-R3 preexecution amendment 001 — bounded beam implementation

Before generating any R3 source, candidate bank, validation score, or test outcome, reduce the preregistered search to a computationally bounded but still multi-hypothesis implementation:

- background bank: 256 Sobol candidates per family; refine the best two per family and retain the best four distinct backgrounds;
- feature bank: 256 parameter vectors per feature family, both registered variants; for each background score the full bank and retain its best two combined hypotheses;
- pool the resulting eight background-feature hypotheses, locally refine all eight feature fits, then jointly refine the best four complete hypotheses;
- MAP versus BMA and the temperature grid remain selected on validation exactly as registered;
- primary SNR0=300 is run first; SNR0=100 is evaluated only after the primary source bank, readout rule, and all optimizer settings are frozen, and cannot affect the primary decision.

No source formula, parameter range, family, seed, metric, threshold, q8/q12 gate, success gate, or physical input changes. No order-1 response is used to admit sources or backgrounds into the direct-derived beam.