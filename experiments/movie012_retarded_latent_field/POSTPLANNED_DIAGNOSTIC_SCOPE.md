# Movie012 postplanned bottleneck readback

The registered Movie012 outcome has already been generated and is not changed or promotable by this diagnostic. The readback uses only the sealed `PREPARED.npz`, validation/test populations, fixed metric, and deterministic noise streams.

It compares three rank-192 latent linear inverses on the same validation and test movies:

1. the registered observation-PCA/q8 latent ridge;
2. a full-whitened-row q8 latent ridge, removing only the rank-256 observation PCA;
3. a q12 full-row same-latent-representation oracle, removing q8/q12 inverse-model mismatch while retaining the rank-192 source decoder.

Each diagnostic ridge exponent is selected only on the frozen validation population with the original exponent grid, then applied to the frozen test population. Report identification, pair-both rate, support error, reliable spans, differential all-frame pass, and q8/q12 fitted discrepancy. Also measure q8/q12 disagreement for the exact rank-192 PCA projection of the analytic test truths.

The diagnostic cannot rescue Movie012, redefine its success gate, or authorize architecture/source changes. Its sole purpose is to attribute the failure among observation compression, latent inverse estimation, source representation, and fitted-field quadrature sensitivity. No new physical call or Paper-I unit is used.
