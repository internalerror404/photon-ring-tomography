# Mahakal II Movie012 — Retarded Latent Neural Field

**Lineage:** Movie009–011 establish that natural analytic direct-null twins are distinguishable with the first indirect image but are not reliably reconstructed by the frozen 595-dimensional ridge or two richer separable classical classes. Movie012 is a new learned-prior experiment; those negative endpoints remain unchanged.

**Status at registration:** no Movie012 training, validation, or test source; latent basis; network weight; regularization decision; reconstruction; or endpoint exists. No Kerr ray, path integral, hull/critical root, or Paper-I unit is authorized.

## Scientific question

Can an amortized, source-only neural inverse reconstruct the correct natural historical movie from direct-plus-first-indirect Kerr data when the competing movie has exactly the same direct observation, without altering or learning the Kerr renderer?

## Frozen physical acquisition

Reuse the authenticated Movie007 q8 inverse/q12 reference arrays at `a=0.5`, inclination `50 deg`, observer radius `100M`, ideal order labels, 8x8 pixels per order, 13 observer times, one direct-reference noise density shared across orders, and the registered union measurement-support metric. q12 produces clean validation/test observations; q8 defines the inverse/training data-consistency operator. Direct and labelled arms share identical direct samples and noise. q8/q12 clean and fitted limits remain `5e-4` relative and `0.1` whitened.

## Source populations

Use background-controlled analytic twins: the shared background is an unknown movie projected into the frozen 595-dimensional class; the old alternatives are analytic narrow hotspots, opposite-shear spirals, split/merge scenes, and opposite radial plumes with compact C2 support ending before the direct footprint. The alternatives are evaluated directly at physical ray coordinates and never projected before rendering or scoring.

Training uses 180 fresh pairs per family from the first three families (`single narrow`, `shear`, `split/merge`), seed family rooted at `120061`; both siblings enter the training population. Radial plume is absent from training and model selection and is a secondary cross-family test. Validation uses 8 fresh pairs per first-three family, seeds `120071`/`120072`. Test uses 16 fresh pairs per all four families, seeds `120081`/`120082`. Four paired noise draws at SNR0=300 are primary; SNR0=100 is secondary. No source is admitted using order-1 response or reconstruction performance.

## Continuous latent movie representation

Sample each training movie on a fixed periodic trilinear grid:

- 15 radial nodes on `[6,13]M`;
- 48 periodic azimuthal nodes;
- 25 source-time nodes on `[-32,28]M`;
- 18,000 field values per movie.

Compute a randomized rank-192 PCA decoder from training movies only, seed `120090`. The decoder is a fixed continuous trilinear source representation: a latent vector generates a movie grid and is interpolated at arbitrary ray coordinates. Report the representation floor on validation/test movies before training the inverse. PCA components, mean field, interpolation convention, and q8/q12 latent response matrices are frozen before neural training.

## Inverse models

For each arm, whiten and standardize observations using training statistics only.

1. **Latent linear ridge:** map observations to the 192 PCA scores; choose one exponent from `10^k`, `k=-8,...,2`, on validation support-weighted movie error only.
2. **Retarded Latent Neural Field:** MLP encoder with two 256-wide SiLU hidden layers and a 192-dimensional output. Three seeds `11,22,33`. The primary prediction is the arithmetic mean of the three decoded latent predictions; each seed is reported separately. AdamW, 80 epochs, batch size 64, learning rate `3e-4`, weight decay `1e-4`; no test-dependent stopping. Training noise is redrawn each epoch, with SNR0 chosen equiprobably from 100 and 300.

The neural loss is standardized latent-score MSE plus `0.1` times q8 whitened data-consistency MSE through the frozen latent response matrix. The network learns only the inverse map; the Kerr transfer, noise, latent decoder, and movie metric are fixed.

## Endpoints

Use the unchanged Movie007 frame error/correlation and 95%/90% reliable-span definitions on analytic truth frames. Report twin identification, pair-both-correct, differential-feature movie fidelity, total-movie span, family results, radial-plume cross-family diagnostics, full-annulus control, PCA representation floor, latent linear baseline, individual neural seeds, ensemble result, and q8/q12 fitted-response checks.

Also report the reconstruction error projected into the frozen 595-dimensional source subspace and its complementary grid residual. A visually plausible complementary completion is not called measured information merely because the network generated it.

## Primary success gate

At SNR0=300 on the first three test families, the neural ensemble must satisfy all of:

- direct individual identification in `[0.45,0.55]` and pair-both at most 5%;
- labelled individual identification at least 95% and pair-both at least 90%;
- labelled 95%-reliable total-movie span at least 12M and at least 8M beyond direct;
- positive median paired error reduction in all three trained families;
- at least 90% of labelled differential movies pass every active frame and at most 5% of direct differential movies do;
- all q8/q12 clean and fitted-response gates pass.

Radial plume is reported as a secondary held-out-family result and cannot make the primary gate pass. Failure is retained; architecture, PCA rank, source populations, thresholds, and training schedule are not changed after test outcomes.

## Scope

A pass would establish learned-prior recovery of natural analytic historical twins on one Kerr chart, with exact direct nullity and a fixed physical renderer. It would not establish full-annulus, visibility-domain, telescope, or observational black-hole movie recovery, and source details outside the measured subspace remain prior-conditioned.