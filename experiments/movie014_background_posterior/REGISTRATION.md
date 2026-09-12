# Mahakal II Movie014 — background-posterior analysis-by-synthesis

**Base:** completed Movie009-R2 lineage at `be7c49ea18c355fe3c13a5ebce0a0d03854fc316`.  
**Status:** registered before generating any Movie014 source population, candidate library, posterior beam, validation choice, reconstruction, or endpoint.  
**Purpose:** test whether retaining multiple direct-compatible background histories, rather than subtracting one background point estimate, permits reliable recovery of natural direct-null historical movies.

Movie009-R2 remains a registered failure. Its postplanned oracle and Fisher diagnostics motivate this successor but do not count as Movie014 evidence. No new Kerr ray, path integral, ODE trajectory, hull/critical root, visibility sample, or Paper-I unit is authorized.

## 1. Scientific hypothesis

For a direct-null old feature `h`, the first-indirect observation is

`y1 = A1 b + A1 h + noise`.

Movie009-R2 used one direct-derived estimate `b_hat` and reconstructed from `y1-A1 b_hat`. Its diagnostics showed that a minority of direct-compatible background errors propagate strongly into order 1 and destroy the 95%-reliable movie endpoint. Movie014 retains a finite approximation to the background posterior and selects or averages background/feature hypotheses jointly against both direct and first-indirect data.

The hypothesis is:

> Reliable natural historical movie recovery requires posterior uncertainty over the shared background, not a single plug-in subtraction.

## 2. Frozen physical acquisition and metrics

Reuse the authenticated Movie007 acquisition:

- Kerr spin `a=0.5`, inclination `50 deg`, observer radius `100M`;
- ideal order labels, direct `n=0` and first indirect `n=1`;
- 8x8 pixels/order and 13 observer times `0,2,...,24M`;
- q8 inverse and q12 clean/reference integrations;
- one direct-reference noise density shared across orders;
- registered Movie007 union-support and full-annulus movie metrics at `tau=0,-2,...,-28M`;
- unchanged frame gate: active-frame error `<=0.35`, correlation `>=0.75`, inactive predicted RMS `<=0.05`.

Required input hashes:

- `PHYSICAL_AND_OPERATOR_ARRAYS.npz`: `54204f14b8c834fb3c54dc012c9827e711f339fc6c30251802fea71ac6d8274e`;
- `SUPPORT_WEIGHTS.npz`: `72080e09e722b01a821d2989d706f21eccfc9ce7671d1fa2f18f66bcd56a7952`;
- `REGULARIZATION_SELECTION.json`: `f3739497a08973bec6ed0b5c174188ad1b2321b469efa06750de2b43bcddf090`;
- executed Movie007 source: `8b80d533cd48400570e505423053a6557e4a2ea6f3d82367adfd5c88b34e5cf1`;
- executed Kerr source: `12abafb39f6d5a6ebf4626e0a05c021d3bd0c5c5ca6ae0abd22632656c8f28cf`.

Every hash and the Movie007 operator/metric replay must pass before source generation. Direct and labelled arms reuse identical direct samples and direct-noise realizations.

## 3. Fresh confirmatory population

Use the explicit Movie009-R2 source formulas with fresh seeds; no source from Movie009-R2 test data is reused.

- shared background: broad single-hotspot, double-hotspot, or flare/drift scene projected exactly into the frozen 595-dimensional class;
- old alternatives: analytic narrow hotspot, shearing spiral, split/merge scene, and radial plume;
- compact C2 historical window: zero for `tau>=-6M` and `tau<=-31M`, one on `[-29,-10]M`;
- no response-based source admission;
- source admission uses finite values, nonnegative emissivity, at least nine active old frames, and the fixed support-weighted feature floor.

Fresh seeds:

- validation sources: `140061`;
- test sources: `140062`;
- validation noise: `140064`;
- test noise: `140065`;
- candidate libraries and posterior sigma points: `140090`;
- bootstrap: `140066`.

Population:

- validation: 8 twin pairs per first-three family;
- test: 16 twin pairs per all four families;
- four paired noise draws per sibling at SNR0=300 primary and SNR0=100 secondary;
- radial plume is excluded from validation but remains in the test population.

## 4. Background posterior beam

Work in source-orthonormal coordinates for the old 595-dimensional background class.

1. Fit the direct MAP background with the validation-selected ridge exponent.
2. Form the direct posterior precision `H0 = B0^T B0 + lambda P`.
3. Rank background-uncertainty directions by their order-1 forecast impact using the generalized eigenproblem

   `B1^T B1 v = mu H0 v`.

4. Retain the top 12 forecast-relevant directions.
5. Build a deterministic 25-member sigma-point beam: MAP plus positive and negative 1.5-posterior-standard-deviation displacements along each retained direction.
6. Keep the 16 hypotheses with highest direct posterior density. No test truth or order-1 response is used to construct the beam.

The posterior approximation and beam size are frozen; no adaptive increase after outcomes.

## 5. Historical dynamics library and family inference

Generate an independent analytic library before validation/test evaluation:

- 512 parameter draws per family;
- both sibling variants for each draw;
- all four families included as hypotheses;
- q8/q12 order-1 responses and source-grid movies cached;
- no library element is admitted or ranked using validation/test outcomes.

For each observation and each retained background hypothesis:

1. subtract its q8 order-1 prediction;
2. score every historical library element with its optimal nonnegative amplitude in `[0.5,1.5]`;
3. retain the eight best joint background/feature hypotheses across all families;
4. compute posterior weights from the full direct-plus-order-1 whitened residual and fixed source priors;
5. use the posterior-weighted movie as the primary reconstruction and the MAP hypothesis as a secondary diagnostic.

The true family label is never supplied. No local continuous refinement is allowed in Stage A; this isolates posterior retention from optimizer-basin effects.

## 6. Controls and ablations

Evaluate on the same observations:

- `POINT_MAP`: single direct-MAP background plus best historical library element;
- `POSTERIOR_BEAM`: full registered background beam and posterior model averaging;
- `SHUFFLED_BACKGROUND`: beam hypotheses permuted across test cases;
- `NO_ORDER1`: direct data only with balanced twin ties;
- `TRUE_BACKGROUND_ORACLE`: postplanned-style upper bound, reported as oracle and unable to pass the registered method.

## 7. Endpoints and gates

Report individual identification, pair-both-correct rate, total- and differential-movie frame metrics, 95%/90% reliable spans, family-level paired error reduction, posterior entropy/effective hypothesis count, coverage of the true background forecast by the beam, q8/q12 clean and fitted discrepancies, wall time, and peak memory.

Primary Stage-A success at SNR0=300 requires all:

1. authentication, replay, direct-nullness, positivity, and population-fill gates pass;
2. `POSTERIOR_BEAM` labelled identification `>=0.95` and pair-both `>=0.90`;
3. labelled 95%-reliable span `>=12M` and at least `8M` beyond direct;
4. at least three of four families, including radial plume, have positive median paired total-movie error reduction;
5. at least 90% of labelled differential movies pass every active frame, while direct is at most 5%;
6. q8/q12 clean and fitted discrepancies are `<=5e-4` relatively and `<=0.1` whitened;
7. `POSTERIOR_BEAM` improves the strict movie-pass rate over `POINT_MAP` by at least 10 percentage points.

A Stage-A pass authorizes a separately registered continuous local-refinement successor. Failure preserves the beam, library, posterior diagnostics, and all negative endpoints; no beam size, source family, threshold, or gate may change after outcomes.

## 8. Scope and resources

A pass supports finite posterior-aware recovery of natural direct-null historical movies on one Kerr chart with ideal labels. It does not establish full-annulus, visibility-domain, telescope, or observational recovery.

- zero new physical calls;
- zero Paper-I units;
- CPU float64, one BLAS thread;
- <=8GiB memory;
- <=45 minutes;
- preserve every source ledger, candidate-library record, beam hypothesis, posterior weight, and failed numerical gate.
