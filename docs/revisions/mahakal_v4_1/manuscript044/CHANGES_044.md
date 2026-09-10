# Changes in manuscript revision 044

Revision 044 makes two accepted cached-data results part of Paper I without changing any earlier numerical artifact.

## Added scientific results

1. **Order attribution.** The first indirect image is the load-bearing historical channel. Omitting order $n=2$ leaves two nuisance-adjusted singular values above threshold, whereas omitting $n=1$ removes all above-threshold historical directions. In the full-stack passing modes, 96.90% and 95.64% of the residualized response energy lie in order $n=1$.

2. **Direct-image nuisance control.** The direct block has zero raw target response, yet improves the conditional Fisher trace by constraining nuisance explanations of the order-1 signal.

3. **Cached sampling robustness.** Re-evaluating the $n=0,1$ operator with all available rays at coarse, core, and fine screen samplings leaves the operational count at two at every level. The conditional-Gram difference and subspace rotation decrease from the coarse-to-core step to the core-to-fine step.

4. **Count versus identity.** The exact two-mode subspace is less stable than the operational count. The archived-to-fine subspace rotation is 16.90 degrees, so the paper claims greater robustness for the number of supported combinations than for their precise identities.

## Manuscript locations

- Abstract: concise order-attribution and cached-sampling statements.
- Introduction: interpretation of the first indirect image, the direct nuisance-control role, and count-versus-mode-identity distinction.
- Nuisance-adjusted results: compact subset table, direct-order explanation, and coarse/core/fine sampling table.
- Discussion and conclusion: revised strongest claim and narrowed next physical-validation target.
- Appendix: all seven order subsets, order-energy fractions, sampling comparisons, and support caveats.
- Numerical-source index: explicit order-attribution and cached-sampling records.

## Preserved limitations

The results remain finite-model statements at one reference geometry and noise label. The full transfer quadrature remains unqualified; the cached sampling ladder does not bound distance to the continuum; support changes across grids are not absorbed into a convergence certificate; the unrecovered R1 normalization scalar remains disclosed; and the index-sum control is not presented as a physical unresolved image.

No Paper II result is imported as validation of Paper I. No new ray, truth, estimator, physical integral, source bank, or production numerical experiment was run while preparing this revision.
