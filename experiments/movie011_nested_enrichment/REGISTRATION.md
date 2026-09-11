# Mahakal II Movie011 — nested source-space enrichment

**Lineage:** successor to the negative Movie010 background-controlled classical result. Base commit `84ef7b60a9e179487796aaa9ad6c22f94ee90992`.  
**Scientific question:** when the shared/current movie is exactly in the original 595-dimensional class and only the old twin difference is natural and off that class, can a source space that *strictly contains* all 595 old directions recover a reliable historical movie?  
**Status at registration:** no Movie011 source parameter, source bank, noise draw, regularization choice, reconstruction, or endpoint has been generated. This is a prospectively registered development successor, not an externally sealed journal main.

No new Kerr ray, path integral, hull/critical root, or Paper-I unit is authorized. Paper I remains unchanged with 854 convention-B units.

## 1. Why this successor is separate

Movie009 mixed two mismatches: the shared/current background and the historical twin difference were both outside the inverse class. Movie010 removed the first mismatch by placing every shared background in the old 595-dimensional class, but its 1617-dimensional comparison basis did not contain the old class because it changed radial and temporal knots. It therefore reconstructed the direct/current anchor worse than the old 595-dimensional model and returned a valid negative result.

Movie011 changes exactly that source-space relation. Its reconstruction space contains every old 595-dimensional movie exactly and adds higher spatial resolution. Movie009 and Movie010 outputs remain untouched; their failures are not reinterpreted.

## 2. Frozen acquisition and authenticated inputs

Reuse the Movie007 physical q8 inverse and q12 reference acquisition:

- Kerr spin `a=0.5`, inclination `50 deg`, static observer at `100M`;
- ideal order labels, direct `n=0` and first indirect `n=1`;
- 8x8 pixels per order and 13 observer times `0,2,...,24M`;
- one direct-reference noise density shared across orders at `SNR0=300`; `SNR0=100` is secondary;
- pixel-integrated rows and variance `sigma_Omega^2 dOmega`;
- registered Movie007 union measurement-support weights at `tau=0,-2,...,-28M`.

Required hashes:

- `PHYSICAL_AND_OPERATOR_ARRAYS.npz`: `54204f14b8c834fb3c54dc012c9827e711f339fc6c30251802fea71ac6d8274e`;
- `SUPPORT_WEIGHTS.npz`: `72080e09e722b01a821d2989d706f21eccfc9ce7671d1fa2f18f66bcd56a7952`;
- `REGULARIZATION_SELECTION.json`: `f3739497a08973bec6ed0b5c174188ad1b2321b469efa06750de2b43bcddf090`;
- Movie007 `movie007_run.py`: `8b80d533cd48400570e505423053a6557e4a2ea6f3d82367adfd5c88b34e5cf1`.

Input authentication and replay of Movie007 operator orientation, source Gram, regularization exponents, and primary 0M/28M endpoint are required before generating Movie011 sources.

## 3. Strictly nested reconstruction space

The old class is 5 clamped cubic radial B-splines, real azimuthal Fourier factors through `m=3` (7 factors), and 17 compact linear temporal B-splines: `5 x 7 x 17 = 595`.

Movie011 uses:

- **9 clamped cubic radial B-splines** on `[6,13]M`, formed by inserting four knots so the old radial spline space is an exact subspace;
- real azimuthal Fourier factors through **`m=8`** (17 factors), whose first seven columns are the old angular class;
- the **same 17 temporal B-splines and knots** as Movie007;
- total dimension `9 x 17 x 17 = 2601`.

The nested containment gate projects every old basis function into the new source-normalized class and requires maximum relative residual <=`1e-11` on both an independent tensor grid and the q8/q12 ray coordinates. Failure blocks the experiment.

The numerical inverse operates in source-orthonormal coordinates for the declared source metric `integral |j-1|^2 r dr dphi dtau`. One-dimensional Gram factors are Cholesky-normalized before assembling the operator. The primary penalty is identity in these source-normalized coordinates, so the comparison does not import a nonnested smoothness penalty. Candidate regularization strengths are `10^k` times the mean nonzero squared singular value, with `k=-8,-7,...,2`.

## 4. Source populations

Shared/current backgrounds are generated exactly in the old 595-dimensional class, with broad orbiting hotspot, broad double-hotspot, and flare/drift families. Their old coefficients are unknown to every estimator. Fresh seeds:

- validation backgrounds/features: `110061`;
- test backgrounds/features: `110062`;
- validation noise: `110063`;
- test noise: `110064`;
- bootstrap: `110065`.

The old twin differences are analytic and evaluated directly on the physical q12 rays and movie grid. They use the Movie010 compact C2 plateau: zero for `tau>=-6M` and `tau<=-31M`, one on `[-29,-10]M`, with smooth transitions. Therefore every clean direct twin difference must be numerical zero by temporal support.

Four natural feature families are retained:

1. narrow orbiting hotspot with angular concentration above the old `m<=3` bandwidth;
2. radially shearing spiral/arc;
3. split/merge topology-changing movie;
4. deforming radial plume.

No feature is projected before physical rendering or scoring, and no source is admitted using order-1 response or reconstruction performance. Positivity, finite values, old-frame activity, and a fixed minimum support-weighted feature RMS are the only source-admission rules. The radial-plume family is excluded from validation and remains the held-out family.

Population:

- validation: 8 twin pairs from each of the first three families;
- test: 16 twin pairs from each of all four families;
- four paired Gaussian noise draws per sibling and SNR;
- primary half-amplitude `0.30`; secondary amplitude factors `0.3` and `0.1` are diagnostic only.

Direct and labelled arms receive identical direct observations and identical direct noise.

## 5. Methods and selection

Primary method: Movie011 nested source-normalized ridge. Select one exponent separately for direct and labelled arms using only validation twins at SNR300 and the median support-weighted total-movie frame error. Freeze both before test evaluation.

Controls:

- frozen Movie007 old595 ridge with its original exponents (`+1` direct, `-2` labelled);
- source-normalized TSVD of the nested operator using the fixed relative cutoff grid `{1e-5,3e-5,1e-4,3e-4,1e-3,3e-3,1e-2}`, selected on the same validation population and frozen before test.

No family-specific or test-dependent tuning. A neural/Retarded-NeRF stage is authorized only if the nested classical primary gate passes; its source and checkpoint rule must be separately frozen after Stage A without changing Stage-A data or endpoints.

## 6. Endpoints and success gate

Primary comparison: SNR300, 64 held-out twin pairs, four paired noise draws, primary feature amplitude.

Report for every arm/method:

- individual sibling identification and pair-both-correct rate, with balanced direct ties;
- total-movie and differential-movie support-weighted frame error and structural correlation;
- 95% and 90% reliable contiguous movie spans under the unchanged Movie007 rule (`error<=0.35`, `correlation>=0.75`);
- family-level paired integrated old-frame error reduction;
- q8/q12 clean and fitted detector discrepancies;
- decomposition into the old 595-dimensional source subspace and the newly added nested directions.

All Stage-A conditions must hold:

1. authentication, Movie007 replay, and exact old595 containment pass;
2. direct clean twin differences are <=`1e-10` whitened at q8 and q12;
3. every source is nonnegative and family populations fill without response-based admission;
4. nested labelled individual identification >=`0.90` and pair-both-correct >=`0.80`;
5. nested labelled 95%-reliable span >=`12M` and exceeds direct by >=`8M`;
6. at least three of four families, including held-out radial plume, have positive median paired old-frame error reduction;
7. q8/q12 clean and fitted discrepancies are <=`5e-4` relatively and <=`0.1` whitened.

A Stage-A pass supports a nested finite-model off-old-basis recovery claim and authorizes separately frozen neural evaluation. Failure preserves the result and does not authorize changing the source class, thresholds, families, or endpoint.

## 7. Limits

- New physical calls: exactly zero.
- Nested basis dimension: exactly 2601.
- CPU float64, one BLAS thread; <=8GiB working memory.
- Maximum execution time: 45 minutes.
- No Paper-I maps, units, source banks, or manuscript files changed.
- Preserve source-candidate ledgers, selection scores, eigensystems/SVDs, reconstructions, frame metrics, numerical gates, failures, and compact review artifacts.
