# Mahakal II Movie009-R3 — multi-hypothesis background posterior and analysis-by-synthesis

**Base:** Movie009-R2 source line at `be7c49ea18c355fe3c13a5ebce0a0d03854fc316`.  
**Status:** registered before generating any Movie009-R3 source, candidate bank, noise draw, validation choice, reconstruction, or endpoint.  
**Purpose:** test the Movie009-R2 diagnosis that a single direct-derived background point estimate discards the uncertainty required to reconstruct the old movie reliably.

Movie009, Movie009-R2, Movie010, Movie011, and Movie013 remain unchanged. Movie009-R3 is a fresh confirmatory experiment, not a reinterpretation of prior failures.

No new Kerr ray, path integral, ODE trajectory, hull/critical root, visibility sample, or Paper-I unit is authorized.

## 1. Scientific hypothesis

The first indirect image contains enough information to recover the natural historical feature, but the direct image can leave several dynamically distinct backgrounds with similar direct likelihood and materially different order-1 forecasts. A plug-in subtraction `y1 - A1 b_hat(y0)` can therefore contaminate the historical residual in a small but decisive tail of cases.

Movie009-R3 retains a finite posterior beam of background histories, fits the old feature under every surviving background, and lets the combined direct-plus-order-1 likelihood select or average complete hypotheses. The feature family is inferred from the observations; it is not supplied from the truth record.

## 2. Frozen acquisition and source families

Reuse the authenticated Movie007 q8 inverse/q12 reference acquisition:

- Kerr `a=0.5`, inclination `50 deg`, observer radius `100M`;
- ideal direct (`n=0`) and first-indirect (`n=1`) labels;
- 8x8 pixels per order, 13 observer times `0,2,...,24M`;
- one direct-reference noise density shared across arms;
- Movie007 union-support and full-annulus movie metrics on `tau=0,-2,...,-28M`;
- q8 inverse and q12 clean/fitted numerical checks.

Required hashes remain those of Movie007 and Movie009-R2. Every input and metric replay must pass before source generation.

Use the same explicit source formulas and parameter ranges as Movie009-R2:

- backgrounds: broad single hotspot, broad double hotspot, and flare/drift, projected into the frozen 595-dimensional Movie007 class;
- old features: narrow hotspot, shearing spiral, split/merge, and radial plume;
- compact C2 old-time support, zero for `tau>=-6M` and `tau<=-31M`, one on `[-29,-10]M`;
- analytic q12 rendering and source-grid scoring; no projection of old features before observation or scoring;
- source admission only by finite values, positivity, at least nine active old frames, and fixed support-weighted RMS; never by order-1 response or reconstruction success.

Fresh seeds:

- validation sources `191061`;
- test sources `191062`;
- validation noise `191064`;
- test noise `191065`;
- background proposal bank `191090`;
- feature proposal bank `191091`;
- bootstrap `191066`.

Population:

- validation: 8 twin pairs per first-three feature family;
- test: 16 twin pairs per all four families;
- four paired Gaussian draws per sibling at SNR0=300 primary and SNR0=100 secondary;
- radial plume is excluded from validation but remains one of the four candidate feature models at test time; its label is not supplied.

## 3. Frozen candidate banks

### Background bank

Generate 512 deterministic candidates for each of the three background families by a scrambled Sobol sequence over the registered parameter bounds. Project each candidate once into the 595-dimensional source class and cache its q8/q12 direct and order-1 responses and movie frames.

For each direct observation:

1. score every bank candidate by direct whitened chi-square;
2. retain the best four candidates per family;
3. locally refine all twelve candidates by bounded nonlinear least squares against q8 direct data;
4. retain the best eight distinct refined backgrounds after phase-wrapped parameter-distance deduplication.

No candidate is admitted or removed using the order-1 response.

### Historical-feature bank

Generate 512 deterministic parameter vectors per feature family. Render both registered variants, yielding 4,096 q8/q12 order-1 response candidates and movie frames. For each surviving background, score the full feature bank against its order-1 residual, retain the best two candidates per family, locally refine those candidates with bounded nonlinear least squares, and retain the best two joint background-feature hypotheses per feature family.

## 4. Joint hypothesis refinement and posterior rule

For the best 16 combined hypotheses, jointly refine background and feature parameters against the stacked q8 direct-plus-order-1 residual, with fixed weak Gaussian penalties equal to the registered parameter-range widths. The direct rows constrain only the background; the first-indirect rows constrain both.

Validation selects one of two frozen readout rules using median support-movie error pooled over the first three families:

- `MAP`: lowest penalized stacked q8 chi-square;
- `BMA`: posterior movie average over the best eight hypotheses with weights proportional to `exp[-(chi2-chi2_min)/(2T)]`, where `T` is selected from `{0.5,1,2,4}` on validation only.

The selected rule and temperature are frozen before test evaluation. No family-specific threshold or test-dependent choice is allowed.

## 5. Controls

- `POINT_ESTIMATE`: one best direct background followed by one best feature fit, matching the plug-in mechanics diagnosed in Movie009-R2;
- `BACKGROUND_BEAM`: multiple backgrounds, one feature family chosen by likelihood;
- `FULL_POSTERIOR_BEAM`: the registered primary method;
- `TRUE_BACKGROUND_ORACLE`: post hoc upper-bound diagnostic only, never eligible to pass the primary gate.

## 6. Endpoints and primary gate

For every method and arm report individual twin identification, pair-both-correct, total and differential frame error/correlation, 95%/90% reliable spans, family-level paired error reduction, background forecast error, posterior effective hypothesis count, family-label accuracy as a diagnostic, q8/q12 clean/fitted discrepancies, wall time, and peak memory.

At SNR0=300, `FULL_POSTERIOR_BEAM` must satisfy all:

1. input authentication and Movie007/Movie009-R2 metric replay pass;
2. direct clean twin difference <=`1e-10` whitened at q8 and q12;
3. every source remains nonnegative and all populations fill without response-based admission;
4. direct identification in `[0.45,0.55]` and direct pair-both <=5%;
5. labelled identification >=95% and pair-both >=90%;
6. labelled 95%-reliable total-movie span >=12M and at least 8M beyond direct;
7. positive median paired total-movie error reduction in at least three of four families, including radial plume;
8. at least 90% of labelled differential movies pass every active frame and at most 5% of direct differential movies do;
9. q8/q12 clean and fitted discrepancies <=`5e-4` relatively and <=`0.1` whitened.

A pass supports multi-hypothesis background-conditioned recovery on one Kerr chart with ideal order labels. Failure preserves all beams and negative endpoints and does not authorize changing candidate-bank sizes, families, thresholds, or the gate.

## 7. Resource limits

- zero new physical calls and zero Paper-I units;
- CPU float64, one BLAS thread;
- <=8GiB working memory and <=45 minutes;
- all source candidates, validation scores, local optimizer exits, posterior weights, and failed hypotheses retained.
