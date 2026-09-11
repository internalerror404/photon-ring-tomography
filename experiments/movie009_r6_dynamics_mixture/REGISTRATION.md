# Mahakal II Movie009-R6 — local nonnegative dynamics mixture

**Base:** Movie009-R5 closeout `94a4406c2382ccc80e24ba47e70c1f39d9e61e27`.  
**Status:** registered before generating the R6 bank, choosing mixture size/penalty, or evaluating any R6 endpoint.  
**Purpose:** remove finite single-template quantization while retaining analytic, q8/q12-stable historical dynamics and no true feature-family label.

Movie009-R5 remains a failure: its family-blind 8,192-template bank reached 99.2% identity, 6M span95, 32.4% differential pass, and passed q8/q12, but a single nearest template could not reproduce continuous parameters. R6 fits a local nonnegative mixture over the same pre-outcome dynamics bank.

This is a postplanned mechanism experiment on the examined Movie009-R2 population with the true shared background supplied. It is not a fresh confirmation. No new Kerr ray, path integral, ODE trajectory, or Paper-I unit is authorized.

## Frozen bank and data

Regenerate the exact R5 bank: seed 490090, 1,024 parameter records per family, both variants, four analytic families, 8,192 unit-amplitude q8 templates, and the same candidate ordering. Use the exact Movie009-R2 validation/test populations, q8 inverse/q12 reference arrays, paired noise, union-support/full-annulus metrics, and frame rules.

## Local mixture

For each observation, rank all 8,192 candidates by the registered single-template amplitude-fitted q8 residual. Retain the first K candidates, then solve a nonnegative ridge problem

`min_w ||T_K w-r||_2^2 + lambda ||w||_2^2`, `w>=0`.

Use an augmented nonnegative least-squares solve. If the fitted total amplitude is above 0.70, rescale weights to sum to 0.70; if it is nonzero but below 0.20, rescale to 0.20. Zero remains zero. The predicted movie and q8/q12 responses are the same weighted combination of exact analytic candidates.

Select one pair `(K, exponent)` using only Movie009-R2 validation sources at SNR0=300:

- `K in {4,8,16,32}`;
- `lambda = 10^exponent * mean(||T_j||_2^2)` with `exponent in {-6,-4,-2,0}`.

The validation objective is median support-weighted total-movie error with the true background supplied. Freeze the selected pair before test evaluation. No family-specific tuning.

## Ablations

Report the selected family-blind mixture, a true-family-restricted mixture using the same K/lambda, and fixed K prefixes at the selected exponent. The R5 single-template full bank is the K=1 control. No continuous parameter refinement is authorized.

## Endpoints and gates

Report identity, pair-both, inferred-family composition, total/innovation movie error, span95/span90, differential all-active-frame pass, family results, number/effective number of nonzero atoms, and q8/q12 clean/fitted checks.

Primary success requires identity >=0.95, pair-both >=0.90, span95 >=12M, differential pass >=0.90, positive median improvement in all four families, and q8/q12 relative <=5e-4 / whitened <=0.1. A pass requires fresh confirmation with non-oracle background inference. If R6 fails, convex interpolation of fixed analytic templates is closed and the next experiment must optimize continuous dynamics parameters or a coordinate neural field directly through the fixed Kerr renderer.