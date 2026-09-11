# Mahakal II Movie009-R3 — background-posterior historical movie recovery

**Base:** completed Movie009-R2 lineage at `be7c49ea18c355fe3c13a5ebce0a0d03854fc316`.  
**Status:** registered before constructing any Movie009-R3 posterior hypothesis, evaluating any new reconstruction, or reading any Movie009-R3 endpoint.  
**Purpose:** test whether the main Movie009-R2 failure comes from collapsing direct-image background uncertainty into one plug-in estimate before reconstructing the historical innovation.

Movie009-R2 remains a registered failure. Its post-outcome oracles and diagnostics motivate this successor but cannot make it pass. No new Kerr ray, path integral, ODE trajectory, hull/critical root, visibility sample, or Paper-I unit is authorized.

## 1. Frozen physical and source inputs

Use the exact authenticated Movie009-R2 population, physical arrays, source-PCA decoder, observation-PCA transform, neural weights, noise draws, frame metrics, and test cases. Regenerate only when necessary from the frozen source and seeds, and require all preserved hashes and Movie009-R2 aggregate results to replay before interpreting Movie009-R3.

Primary population: the existing 64 Movie009-R2 test twin pairs, all four paired noise draws, SNR0=300. This is a postplanned mechanism experiment on an already examined population, not a fresh confirmatory main. A method that passes here must be frozen and tested on a new population before supporting a new headline claim.

## 2. Hypothesis

Let `x_b` denote source-normalized old595 background coefficients and `z_h` the rank-96 historical-innovation latent. Direct data constrain `x_b`, but uncertainty directions that are weak in the direct image can produce large first-indirect forecasts. Movie009-R2 used one posterior mean `x_hat_b`, then reconstructed `z_h` from the residual.

Movie009-R3 retains a deterministic beam approximating the direct background posterior, reconstructs an innovation under each hypothesis, evaluates the full direct-plus-order-1 objective, and either selects or averages the surviving hypotheses. The method does not create new measurements and does not use the true background or feature-family label.

## 3. Deterministic background-posterior beam

Use the Movie009-R2 validation-selected direct-background exponent and source-normalized linear model. For each SNR, form the Gaussian posterior covariance

`Sigma_b = (B0^T B0 + lambda_b P)^(-1)`

under the same prior precision `P` used by Movie009-R2. Rank background uncertainty by its effect on order 1 using the eigensystem of

`Sigma_b^(1/2) B1^T B1 Sigma_b^(1/2)`.

Freeze the top 16 forecast-relevant directions. For each direct observation construct exactly 65 background hypotheses:

- the posterior mean;
- plus and minus 1 posterior standard deviation along each of the top 16 directions;
- plus and minus 2 posterior standard deviations along each of the same directions.

No hypothesis is generated from test truth, test family, or order-1 reconstruction performance.

## 4. Historical reconstruction and joint scoring

For every background hypothesis:

1. predict and subtract its q8 order-1 contribution;
2. apply the already frozen Movie009-R2 rank-128 observation PCA and the arithmetic mean of its three registered latent-MLP predictions;
3. apply the frozen Movie009-R2 joint background/innovation refinement with its validation-selected trust exponents;
4. compute the complete q8 negative-log-posterior score: direct residual, order-1 residual, background displacement penalty under the direct posterior, and latent trust penalty.

Report two fixed estimators:

- `POSTERIOR_BEAM_MAP`: lowest complete score;
- `POSTERIOR_BEAM_MEAN`: normalized exp(-Delta score/2) average over hypotheses with Delta score <=25, using log-sum-exp stabilization.

No temperature, beam width, displacement scale, score component, or averaging rule is selected on the test population.

## 5. Registered ablations

The same code must also report:

- `POINT_ESTIMATE_REPLAY`: exact Movie009-R2 latent-MLP reconstruction;
- `TRUE_BACKGROUND_LATENT`: true background supplied, but the same rank-96 latent PCA/MLP and joint mechanics retained; this isolates representation/inverse limitations and is an oracle diagnostic only;
- `POSTERIOR_BEAM_NO_JOINT`: posterior beam with MLP innovation but without final joint refinement;
- beam-size prefixes K={1,9,17,33,65}, where prefixes are fixed by decreasing forecast eigenvalue and sign/scale order.

These ablations cannot replace the registered primary estimator.

## 6. Endpoints

Use the unchanged Movie007/Movie009-R2 scoring definitions:

- individual twin identification and pair-both-correct rate;
- support-weighted total-movie and differential-movie frame errors and correlations;
- 95% and 90% reliable contiguous spans;
- all-active-frame differential pass rate;
- background-only, innovation-only, and total error;
- family-level paired error reduction, including radial plume;
- q8/q12 clean and fitted response discrepancies;
- effective posterior beam size and posterior weight concentration;
- per-case relation between direct-background forecast uncertainty and reconstruction failure.

## 7. Gates

Mechanics gates:

1. every input and source hash passes;
2. the Movie009-R2 point-estimate aggregate replays to 1e-10;
3. K=1 reproduces the point-estimate method to 1e-9 in coefficients and scored movie values;
4. no true background, family label, or test metric enters the beam;
5. all clean and fitted q8/q12 comparisons satisfy relative <=5e-4 and whitened <=0.1;
6. zero new physical calls and zero Paper-I units.

Primary scientific gate at SNR0=300 for `POSTERIOR_BEAM_MAP`:

- labelled individual identification >=0.95 and pair-both >=0.90;
- 95%-reliable total-movie span >=12M and at least 8M beyond direct;
- at least three of four families, including radial plume, have positive median paired error reduction;
- differential all-active-frame pass >=0.90;
- direct identification remains in [0.45,0.55] with pair-both <=0.05;
- all numerical gates pass.

Interpretation ladder:

- if `TRUE_BACKGROUND_LATENT` itself fails the movie/differential gates, background posterior retention is not sufficient and the rank-96 historical representation/inverse remains limiting;
- if the true-background latent diagnostic passes but posterior beam fails, background posterior approximation or joint selection remains limiting;
- if the posterior beam passes, freeze the method unchanged and run a fresh confirmatory population before claiming success.

## 8. Limits

CPU float64 for scientific linear algebra; neural inference float32 as frozen; one BLAS thread; <=8GiB working memory; <=45 minutes. Preserve every hypothesis score, selected index, posterior weight, ablation output, numerical gate, failure, and negative result.