# Mahakal II Movie009 — natural off-basis direct-null movie recovery

**Lineage:** successor to Movie007 measured-support recovery and Movie008 exact direct-null in-basis twins. Base commit `bdaf9fc2c4fabfe10b4b2d055f7e73c4a46f2f14` on the separate Paper-II line.  
**Status at registration:** repository/operator audit completed; no Movie009 source parameter, source bank, observation, regularization choice, learned weight, reconstruction, or endpoint has been generated. This is a prospectively registered development experiment, not an externally sealed journal main.

No new Kerr ray, path integral, hull/critical root, or Paper-I unit is authorized. Paper I remains unchanged with 854 convention-B units.

## 1. Scientific question

Can the first indirect Kerr image identify and reconstruct which of two physically natural historical movies occurred when:

1. the two movies have exactly the same direct-image mean because their difference is supported strictly before the direct retarded-time footprint;
2. the movie difference is defined analytically rather than selected from an order-1 singular vector;
3. the truth is evaluated directly at physical ray landing points and is not projected into the 595-dimensional Movie007/008 reconstruction class; and
4. one source family is excluded entirely from neural training and validation?

## 2. Frozen physical acquisition and repository conventions

Reuse authenticated Movie007 q8 inverse and q12 reference arrays:

- Kerr spin `a=0.5`, inclination `50 deg`, static observer at `100M`;
- ideal order labels, direct `n=0` and first indirect `n=1`;
- 8x8 detector pixels per order, 13 observer times `0,2,...,24M`;
- one direct-reference noise density shared across orders at `SNR0=300`; `SNR0=100` is secondary;
- pixel-integrated rows and variance `sigma_Omega^2 dOmega`, equivalent to the repository convention `sqrt(dOmega) g^3 / sigma_Omega` after whitening;
- per-ray source radius, phase, delay, redshift, pixel identity, and q8/q12 area weights retained;
- Movie007 union measurement-support weights on the fixed 32x64 source-plane grid and frames `tau=0,-2,...,-28M`.

Required Movie007 input hashes:

- `PHYSICAL_AND_OPERATOR_ARRAYS.npz`: `54204f14b8c834fb3c54dc012c9827e711f339fc6c30251802fea71ac6d8274e`;
- `SUPPORT_WEIGHTS.npz`: `72080e09e722b01a821d2989d706f21eccfc9ce7671d1fa2f18f66bcd56a7952`;
- `REGULARIZATION_SELECTION.json`: `f3739497a08973bec6ed0b5c174188ad1b2321b469efa06750de2b43bcddf090`;
- Movie007 source `movie007_run.py`: `8b80d533cd48400570e505423053a6557e4a2ea6f3d82367adfd5c88b34e5cf1`.

Every hash and the Movie007 metric/operator replay must pass before Movie009 source generation. Direct and labelled arms use the same direct samples and direct-noise realizations. No row is zero-filled or assigned a per-arm noise recalibration.

## 3. Natural analytic twin families

Every sibling is an everywhere-positive analytic source evaluated directly on q12 physical rays for clean data and on the fixed source grid for movie scoring. Let `w(tau)` be the compact polynomial window

`w=(1-u^2)^4 for |u|<1 and 0 otherwise`, with `u=(tau+18)/12`.

Hence every sibling difference vanishes identically for `tau >= -6M`. The q12 direct rays begin no earlier than approximately `-2.533454M`; direct twin means must therefore agree to numerical roundoff without a numerical nullspace search.

Four families are fixed:

1. **narrow orbiting hotspot:** two alternatives differ by an azimuthal phase displacement; radial width 0.30–0.55M and concentration 9–15, intentionally above the old `m<=3` bandwidth;
2. **shearing spiral/arc:** two alternatives have opposite radial phase shear, with a continuously radius-dependent phase;
3. **split/merge movie:** two alternatives split and merge along different time-dependent axes, changing source topology;
4. **radial plume:** two alternatives move radially in opposite directions while remaining azimuthally localized and deforming in time.

Each sibling equals `1 + shared_background + old_feature_A/B`. Shared backgrounds are broad, positive, rotating analytic scenes. No feature is projected before rendering. Family parameters are drawn from fixed ranges by recorded seeds; there is no admission based on order-1 response or reconstruction performance. Sources are accepted only if finite, nonnegative on the evaluation grid, active on at least 9 of the 12 old frames `tau=-6,...,-28M`, and have support-weighted old-feature RMS at least 0.03. Every rejection and reason is retained.

Population:

- training for the neural estimator: 300 histories from each of the first three families, seed `90050`; one randomly chosen sibling per history and random SNR in `{100,300}`;
- validation: 8 twin pairs from each of the first three families, seed `90061`;
- held-out test: 16 twin pairs from each of all four families, seed `90062`;
- **radial plume is excluded from neural training and validation**;
- test noise: four paired draws per sibling and SNR, seed `90063`;
- bootstrap: 2,000 resamples clustered by midpoint pair, seed `90064`.

Primary old-feature scale is fixed by the analytic family amplitude range 0.35–0.55. Secondary families use a multiplicative ladder `1.0, 0.3, 0.1`; the ladder cannot change the primary gate.

## 4. Reconstruction methods

### A. Frozen 595-dimensional ridge baseline

Reuse Movie007's source class, source norm, penalty, and independently validation-selected arm-specific ridge exponents: direct `+1`, labelled `-2`. The analytic truth is not projected before observation or scoring.

### B. Rich classical source model

Use a separately declared finite movie basis:

- 7 clamped cubic radial B-splines on 6–13M;
- real Fourier factors through `m=5` (11 angular factors);
- 21 compact linear temporal B-splines on -32–28M;
- dimension `7 x 11 x 21 = 1617`.

Construct q8 and q12 source-linear operators directly from the cached physical ray tuples. Use the source norm `integral |j-1|^2 r dr dphi dtau` and a fixed positive quadratic penalty combining source norm, radial curvature, angular harmonic weight, and temporal curvature. Select one ridge exponent separately for direct and labelled arms from `10^k`, `k=-7,...,3`, using only the first-three-family validation twins at SNR300 and the median support-weighted movie error. Freeze before test reconstruction. No family-specific or test-dependent tuning.

### C. Retarded Neural Field

Train separate direct and labelled amortized inverse models. Each model contains:

- an observation encoder: standardized whitened residual data -> 256 -> 96 latent units with GELU;
- a continuous decoder queried at `(r,phi,tau)`, using normalized radius/time, raw azimuthal Fourier features through `m=8`, co-rotating features `phi-Omega(r)tau` through `m=4`, four temporal Fourier frequencies, and six fixed radial RBFs;
- two hidden layers of width 128 with GELU and a sigmoid-bounded nonnegative contrast output.

Training uses the 900 registered histories, noisy q8 observations, and support-weighted source-value supervision at 384 sampled source-grid coordinates per example, mixed 75% from the registered union-support distribution and 25% uniformly. The decoder is a source representation only; the Kerr renderer is fixed and never learned. No test family or test source enters normalization, training, early stopping, or model choice.

Use seeds `11,22,33`, AdamW for 1,200 updates, batch size 24, learning rate 2e-3 with cosine decay, weight decay 1e-5, gradient clipping 1.0. Save checkpoints at updates 600, 900, and 1200. For each arm/seed, choose the checkpoint with lowest median validation support error pooled across the first three families; freeze it before evaluating test data. No architecture or loss sweep.

## 5. Endpoints

Primary comparison is at SNR300 on all 64 held-out twin pairs, four paired noise draws, and the primary family amplitudes.

For each arm and method report:

- individual sibling identification accuracy using nearest reconstructed movie under the registered support metric;
- pair-both-correct rate;
- differential movie `(recon_A-recon_B)/2` versus the true analytic differential movie;
- total-movie support-weighted frame error and structural correlation;
- 95% and 90% reliable contiguous spans under the unchanged Movie007 frame rule: active error <=0.35 and correlation >=0.75; inactive predicted RMS <=0.05;
- paired integrated old-frame error reduction by family;
- separately, error in the old 595-dimensional source subspace and residual error outside it, so prior/basis completion is not silently called measured recovery;
- q8/q12 clean-truth and fitted-field detector discrepancies.

Direct identification must be scored with balanced tie handling: identical direct means cannot be turned into a deterministic success by label ordering. A secondary independent-sibling-noise classification is reported separately.

## 6. Success gates

### Stage A — rich classical feasibility

All must hold:

1. input authentication and Movie007 replay pass;
2. direct clean twin difference <=1e-10 whitened for every source at q8 and q12;
3. every source remains nonnegative and every family fills without response-based admission;
4. rich labelled individual identification >=0.90 and pair-both-correct >=0.80;
5. rich labelled 95%-reliable span >=12M and exceeds direct by >=8M;
6. at least three of four families, including radial plume, show positive median paired error reduction;
7. q8/q12 clean and fitted response differences <=5e-4 relatively and <=0.1 whitened.

Stage A pass authorizes Stage B evaluation; Stage B architecture and training are already frozen above and cannot be altered after Stage-A outcomes.

### Stage B — neural generalization

All must hold for the median over the three registered neural seeds:

1. labelled individual identification >=0.90 and pair-both-correct >=0.80;
2. labelled 95%-reliable span >=10M and gain over direct >=8M;
3. at least three of four families improve, including the completely held-out radial-plume family;
4. direct sign/nearest-twin accuracy remains in [0.45,0.55] under matched direct data;
5. q8/q12 fitted-field detector gates pass;
6. any completion outside the measurement-supported or old 595-dimensional subspace is reported separately.

A Stage-A pass with Stage-B failure remains a physical/inverse result but not a neural generalization claim. A Stage-B pass supports a continuous learned reconstruction claim. Neither stage licenses full-annulus, visibility-domain, telescope, or observational recovery.

## 7. Resource and stopping rules

- New physical calls: exactly zero.
- Rich basis dimension: exactly 1617; no post-outcome expansion.
- Neural fits: six maximum, three seeds for each arm.
- CPU float64 for classical operators/solves; neural training may use float32 CPU. One BLAS thread for scientific NumPy/SciPy calculations.
- Maximum 8GiB working memory and 45 minutes total local execution.
- Preserve every failed source candidate, training trace, checkpoint decision, and numerical gate.
- Any implementation defect before outcomes is recorded and source re-frozen; no threshold, family, basis, or architecture changes after test results exist.
