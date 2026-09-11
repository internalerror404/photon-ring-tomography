# Mahakal II Movie009-R4 — historical representation ladder

**Base:** completed Movie009-R3 closeout `122f8b9123bd619d0742ff9a808bc67471ad5828`.  
**Status:** registered before fitting any R4 source representation, selecting regularization, or evaluating any R4 endpoint.  
**Purpose:** isolate whether Movie009-R2/R3 fail because the rank-96 unweighted PCA historical decoder is too restrictive or numerically unstable, independently of background uncertainty.

Movie009-R2 and R3 remain failures. This is a postplanned mechanism experiment on their examined population, not a fresh confirmatory main. No new Kerr ray, path integral, ODE trajectory, or Paper-I unit is authorized.

## Frozen population and acquisition

Use the exact authenticated Movie009-R2 training, validation, and test source specifications; the exact q8 inverse/q12 reference Kerr arrays; the same four paired SNR0=300 test-noise draws; the same union-support and full-annulus movie metrics; and the same frame rule (`error<=0.35`, `correlation>=0.75`). The **true shared background is supplied** in every arm so that only historical representation and inversion are tested.

## Representations

Fit all representations using the 1,080 training historical-feature movies only on the fixed 15 radial x 48 periodic-azimuth x 25 time grid.

1. `UNWEIGHTED_PCA_R96`: exact Movie009-R2 rank-96 source-PCA construction and seed; must replay the R3 true-background latent result.
2. `UNWEIGHTED_PCA_R192`.
3. `UNWEIGHTED_PCA_R384`.
4. `MEASUREMENT_WEIGHTED_PCA_R96`.
5. `MEASUREMENT_WEIGHTED_PCA_R192`.
6. `MEASUREMENT_WEIGHTED_PCA_R384`.

For ranks 192/384 use randomized SVD with three power iterations and seed 290090. For weighted PCA, define the fixed latent-grid weight by the column sum of the absolute q8 order-1 grid-to-data operator, normalize its positive mean to one, and floor every cell at 1% of that mean. Fit PCA in the corresponding weighted Euclidean metric, then decode back to physical source values.

No rank or weighting is selected using test outcomes. Each representation receives the same latent-ridge exponent grid `-8,...,2`, selected on validation total-movie support error at SNR0=300 with the true background supplied.

## Endpoints

For each representation report: validation-selected exponent; validation/test representation floor; labelled twin identification and pair-both rate; median total and innovation movie error; 95%/90% contiguous span; differential all-active-frame pass; family results including radial plume; q8/q12 clean and fitted-field discrepancies; explained training variance; wall time and memory.

## Gates

Mechanics gates:

- all hashes and source populations replay;
- rank-96 unweighted result reproduces R3 true-background latent values to 1e-8;
- PCA components are orthonormal in their declared metric to 1e-10;
- clean and fitted q8/q12 comparisons satisfy relative <=5e-4 and whitened <=0.1;
- zero new physical calls and zero Paper-I units.

A representation is a practical mechanism winner only if it has labelled identity >=0.95, pair-both >=0.90, span95 >=12M, differential all-active pass >=0.90, positive median improvement in all four families, and all numerical gates pass. A positive result must be combined with non-oracle background inference and then confirmed on fresh sources before supporting a headline claim.

If every representation fails, linear PCA rank/weighting is closed as the missing ingredient and the next experiment must use a nonlinear dynamics-aware continuous historical model rather than another global linear decoder.