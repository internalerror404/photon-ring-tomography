# Mahakal II Movie009-R7 — continuous dynamics refinement

**Base:** Movie009-R6 near-pass closeout `6f601b73e9caa337a9a91acb847ead2fa9e36fa1`.  
**Status:** registered before constructing any R7 barycentric parameter estimate, evaluating a refined q8 score, or reading an R7 endpoint.  
**Purpose:** test whether the remaining Movie009 movie-fidelity gap is finite dynamics-template quantization rather than missing higher-order information.

Movie009-R6 remains a registered failure despite 26M span95, 100% twin identification, and valid q8/q12 numerics, because differential all-active-frame pass was 84.375% versus the required 90%. R7 changes only the historical representation after the frozen R6 mixture.

This is a postplanned true-background mechanism experiment on the examined Movie009-R2 population. It is not a fresh confirmatory main. No new Kerr ray, path integral, ODE trajectory, or Paper-I unit is authorized.

## Frozen starting point

Use the exact Movie009-R6 validation-selected K=32, exponent=-6 nonnegative mixture, bank seed 490090, 8,192 candidate ordering, R2 test observations/noise, true shared background, and all frame/numerical gates. Replay the R6 aggregate before interpreting R7.

## Family-blind continuous parameter estimate

For every observation, use the R6 K=32 weights only as a local proposal distribution. Within each of the four analytic dynamics families:

1. convert candidate parameters to a canonical continuous parameterization that absorbs the discrete sibling variant:
   - narrow hotspot: center phase `phase +/- phase_delta`;
   - shearing spiral: signed shear;
   - split/merge: physical axis `phase` or `phase+pi/2`;
   - radial plume: signed radial drift;
2. compute a weight-normalized circular mean for phase and weighted means for all other active parameters;
3. render the resulting unit-amplitude analytic movie directly through the q8 Kerr operator;
4. fit amplitude analytically and clip it to `[0.20,0.70]`;
5. choose the family with minimum q8 residual. No true family label enters selection.

If a family has zero R6 mixture weight, initialize it from that family's best single R5 bank candidate for the same observation.

## Fixed local coordinate refinement

Starting from the selected family-blind barycenter, apply two deterministic coordinate-search stages to the q8 residual:

- stage 1: plus/minus 5% of each registered parameter range;
- stage 2: plus/minus 2% of each range;
- one pass over active parameters per stage in fixed order;
- phase is periodic; all other parameters are clipped to registered bounds;
- amplitude is re-solved analytically after every trial;
- strict improvements only, with the negative direction tested before the positive direction and exact ties retaining the earlier state.

No iteration count, step size, parameter order, or stopping rule is selected on validation/test outcomes.

## Ablations

Report:

- `BARYCENTER_ONLY`;
- `CONTINUOUS_REFINED` primary;
- `TRUE_FAMILY_REFINED` using the true family only, as an oracle diagnostic;
- R6 K=32 replay.

## Endpoints and gate

Use the unchanged identity, pair-both, total/innovation movie error, span95/span90, differential all-active-frame pass, family results, fitted-parameter diagnostics, and q8/q12 clean/fitted checks.

Primary success requires identity >=0.95, pair-both >=0.90, span95 >=12M, differential pass >=0.90, positive median improvement in all four families, and q8/q12 relative <=5e-4 / whitened <=0.1.

A pass establishes that continuous dynamics refinement closes the representation gap on this examined, true-background population. It still requires non-oracle background inference and fresh confirmatory sources before a paper headline. If it fails, the next representation must be a flexible coordinate neural field or richer event model rather than further template-bank refinement.