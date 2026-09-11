# Mahakal II Movie011 — Retarded Neural Field on natural direct-null twins

**Lineage:** Movie009 and Movie010 showed that rich finite-basis ridge can identify every natural direct-null twin but does not achieve the registered 95%-reliable contiguous movie endpoint because off-basis historical structure leaks across the global tensor representation. Movie011 tests the Retarded Neural Field architecture already frozen in Movie010, using entirely fresh training, validation, and test populations. Base commit `8681d7baf2c04eed9ced9afdda74abcef19c8e29`.

No Movie010 test source is reused. No Movie011 source, observation, neural weight, checkpoint choice, or endpoint exists at registration. No new Kerr call or Paper-I unit is authorized.

## Fixed physical input and causal construction

Reuse the authenticated Movie007 q8 inverse and q12 reference Kerr arrays, the union measurement-support metric, ideal labels, shared direct-reference noise calibration, 8x8 pixels per order, 13 observer times, and per-ray distributed delays. The direct and labelled arms share the exact same direct samples and direct-noise draw.

Use Movie010's source construction without modification:

- shared low-order background in the intersection of the old 595- and rich 1617-dimensional source spaces;
- four analytic old-feature alternatives: narrow hotspot, opposite-shear spiral, split/merge topology, and radial plume;
- compact C2 old-time window that is zero outside `(-30,-6)M` and one on `[-26,-10]M`;
- no projection before clean physical rendering or movie scoring;
- radial plume completely excluded from training and validation.

Fresh population seeds:

- neural training: 300 single movies from each of narrow-hotspot, shearing-spiral, and split/merge, seed `110050`;
- validation: 8 twin pairs per those three families, seed `110061`;
- test: 16 twin pairs per all four families, seed `110062`;
- training noise seed `110063`; validation noise `110064`; test noise `110065`; bootstrap `110066`.

Training examples randomly choose one of the two historical alternatives and an old-feature multiplier uniformly in `[0.5,1.0]`. SNR is sampled uniformly from `{100,300}`. Test uses the primary multiplier 1.0 and four paired draws at SNR300; SNR100 is secondary.

## Frozen architecture

Train separate direct and direct-plus-order-1 models for seeds 11, 22, and 33.

### Observation encoder

- input: whitened, base-subtracted q8 observations, standardized per row from the training set only;
- `Linear(d,256) -> GELU -> Linear(256,96) -> GELU`;
- no order mixing before concatenation in the labelled input.

### Continuous decoder

For every query `(r,phi,tau)`, concatenate the 96-dimensional observation latent with fixed coordinate features:

- normalized radius and time plus their squares;
- `sin/cos(m phi)` for `m=1,...,8`;
- `sin/cos(m [phi-Omega(r)tau])` for `m=1,...,4`, with `Omega(r)=1/(r^1.5+0.5)`;
- four temporal Fourier frequencies over `[-32,28]M`;
- six Gaussian radial RBFs on `[6,13]M`.

Decoder: `Linear -> 128 GELU -> 128 GELU -> 1`, output contrast `0.85*tanh(raw)`. The network represents the source only; it does not learn or change the Kerr renderer, screen weights, noise, or order labels.

## Training and checkpoint selection

- AdamW, 1,200 updates, batch size 24, initial learning rate 2e-3 with cosine decay, weight decay 1e-5, gradient clipping 1.0;
- 384 source-grid coordinates per update, sampled 75% from the registered union-support distribution and 25% uniformly;
- weighted source-value MSE normalized per history by support-weighted contrast energy plus 1e-4;
- checkpoints at updates 600, 900, and 1,200;
- select one checkpoint per arm/seed by lowest median validation support-movie error pooled across the first three families; no test source or radial plume enters selection;
- no architecture, feature, width, learning-rate, loss, or training-length sweep.

## Evaluation

For every test twin and four paired noise draws:

- reconstruct the full 15-frame, 32x64 source movie;
- individual twin identification by nearest registered support-movie distance;
- pair-both-correct rate;
- differential movie and total movie frame errors/correlations;
- 95% and 90% reliable contiguous spans under the unchanged Movie007 rule;
- paired integrated movie-error reduction by family;
- direct matched-data accuracy must be scored with balanced tie handling;
- q8/q12 fitted-field response check on the first noise draw of every test twin for every arm/seed;
- source completion error inside and outside the old 595-dimensional evaluation-grid column space is reported separately.

Primary aggregate is the median metric over the three registered seeds, with history-cluster bootstrap over the 64 test pairs. No seed is selected from test performance.

## Success gate

All are required at SNR300:

1. all input/source hashes and Movie007 metric/operator replays pass;
2. every test direct twin mean differs by <=1e-10 whitened at q8 and q12;
3. median labelled individual identification across seeds >=0.90;
4. median labelled pair-both-correct >=0.80;
5. median labelled 95%-reliable span >=10M and exceeds the direct median by >=8M;
6. at least three of four families, including unseen radial plume, have positive median paired error reduction;
7. median direct individual identification lies in `[0.45,0.55]` under matched direct data;
8. every registered fitted-field q8/q12 check is <=5e-4 relatively and <=0.1 whitened;
9. no outside-subspace completion is called measured recovery without separate support.

A failure remains evidence about amortized neural inversion and does not authorize retuning. A pass supports continuous source reconstruction on one measured Kerr chart with ideal labels; it does not establish full-annulus, visibility-domain, telescope, or observational movie recovery.
