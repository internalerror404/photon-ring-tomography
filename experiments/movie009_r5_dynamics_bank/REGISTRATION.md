# Mahakal II Movie009-R5 — family-blind analytic dynamics bank

**Base:** Movie009-R4 closeout `358223d85668b2af638039154cfe293c7c9dcdd5`.  
**Status:** registered before generating the dynamics bank, inspecting any R5 test score, or selecting any candidate.  
**Purpose:** test whether a nonlinear dynamics-aware historical representation can recover the natural Movie009 twins without the rank-96/192/384 global PCA decoder and without being given the true feature-family label.

Movie009-R2 through R4 remain failures. This is a postplanned mechanism experiment on the examined R2 population, not a fresh confirmatory main. No new Kerr ray, path integral, ODE trajectory, or Paper-I unit is authorized.

## Frozen population and acquisition

Use the exact authenticated Movie009-R2 source specifications, q8 inverse/q12 reference arrays, SNR0=300 four-draw test observations, union-support/full-annulus metrics, and frame gate. Supply the true shared background for the primary representation-isolation panel. The direct arm remains the exact support-null control.

## Candidate bank

Generate exactly 1,024 parameter records per analytic family with seed `490090` from the registered Movie009-R2 parameter ranges. For each record retain both sibling variants, yielding 8,192 unit-amplitude candidate movies across:

- narrow orbiting hotspot;
- shearing spiral/arc;
- split/merge scene;
- radial plume.

The bank is generated without test observations, truth parameters, q8/q12 response strength, reconstruction performance, or family labels. Every candidate is evaluated analytically at q8 and q12 ray coordinates and on the movie grid; no PCA, Fourier/B-spline projection, or trilinear source decoder is used.

For each candidate, set `amp=1` while preserving its other dynamics parameters. Given a background-subtracted q8 order-1 residual, fit one nonnegative amplitude analytically and clip it to `[0.20,0.70]`. Select the candidate with minimum complete q8 residual over the entire family-blind bank. Ties use the lowest pre-frozen candidate index.

## Registered ablations

- `FAMILY_BLIND_BANK_8192`: primary, all four families compete.
- `TRUE_FAMILY_BANK_2048`: only candidates from the true family compete; oracle diagnostic, not primary.
- `TRAIN_FAMILY_BANK_6144`: radial-plume templates excluded, testing whether the first three family models extrapolate to the held-out plume.
- bank prefixes using 128, 256, 512, and 1,024 parameter records per family, preserving generation order.

No local nonlinear refinement is authorized in R5. It may be registered as a successor only after R5 is closed.

## Endpoints

Report individual identity and pair-both accuracy, inferred-family accuracy, fitted amplitude error, total/innovation movie error, 95%/90% contiguous spans, differential all-active-frame pass, family results, q8/q12 clean and fitted discrepancies, candidate-margin statistics, and runtime/memory.

## Gates

Mechanics:

- all input/population hashes and direct-null checks pass;
- bank generation is deterministic and independent of test outcomes;
- q8/q12 clean and fitted discrepancies are <=`5e-4` relatively and <=`0.1` whitened;
- zero new physical calls and zero Paper-I units.

Primary family-blind success at SNR0=300 requires identity >=0.95, pair-both >=0.90, span95 >=12M, differential all-active-frame pass >=0.90, positive median improvement in all four families, and all mechanics gates. A pass shows that a dynamics-aware model class, rather than a larger linear PCA space, supplies the missing representation on this examined population; it still requires a fresh confirmation population and non-oracle background inference.

If the true-family bank passes but the family-blind bank fails, discrete family/model selection is the remaining bottleneck. If both fail, the finite template approximation or amplitude-only fit is insufficient and a continuous nonlinear optimizer/NeRF must be tested.