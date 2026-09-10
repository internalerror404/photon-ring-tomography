# Movie006 execution amendment 001 — timeout recovery before movie outcomes

The first execution was terminated by the local tool timeout while constructing the registered physical q8/q12 ray arrays. It logged **24,918 separated ray attempts**, produced no `PHYSICAL_ARRAYS`, no source bank, no observations, no regularization choice, and no inverse or movie metric. The in-memory ray values are unrecoverable and are not reconstructed from the attempt ledger.

The original cap is retained rather than reset: 28,000 separated evaluations total. Only 3,082 remain. Repeating the original 26,624-node construction would violate the registration and is not authorized.

Before any movie outcome, the physical construction is changed as follows:

1. Trace one fixed 33×33 tensor chart for each of n=0 and n=1: 2,178 separated evaluations.
2. Freeze an explicit tensor-cubic representation of `(r_source, phi_source, delay)` for each order; derive redshift from the same registered circular-emitter formula.
3. Evaluate the registered q8/q12 detector rules from that frozen representation. These evaluations are no longer described as direct physical rays.
4. Use 32 fixed grid nodes per order for independent compactified-ODE comparison: 64 ODE evaluations, no additional separated reference calls.
5. Use a matched 8×8-pixel q2 detector rule—256 direct physical nodes per order, 512 separated evaluations—to compare frozen-chart and direct-physics responses at identical nodes and weights. This tests the chart approximation without conflating it with pixel-integration refinement.

Total planned separated attempts after the failed process: 2,690. Cumulative planned attempts: 27,608, below 28,000. The remaining 392 are held as an exception reserve and are not automatically usable.

The physical gate is amended to require:

- the independent ODE limits from the original registration at all 64 points;
- maximum frozen-versus-direct tuple discrepancies on the matched q2 nodes below `2e-4 M` in radius, `2e-4 rad` in wrapped phase, `2e-4 M` in delay, and `2e-5` in redshift;
- maximum per-channel frozen-versus-direct q2 detector discrepancy below `5e-4` for the declared basis diagnostics;
- q8-versus-q12 integration discrepancies below the original relative and whitened limits for every fixed validation/test source.

This is a protocol deviation prompted by an execution failure, not by favorable or unfavorable movie results. The forward model is now explicitly a **validated local frozen chart**, not a direct q8/q12 ray integration. All original attempts and this amendment remain in the record. The source, movie families, noise, inverse methods, selection, endpoints, and success gates are unchanged.