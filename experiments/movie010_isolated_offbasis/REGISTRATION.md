# Mahakal II Movie010 — isolated off-basis historical movie recovery

**Lineage:** successor to Movie009 Stage A, which correctly identified every natural analytic twin but failed its contiguous movie endpoint because the shared present-time background was also outside the reconstruction classes. Base commit `3fe4c7d1d67d08eef4c0cfb2907651b024573d4c`.  
**Status:** no Movie010 source, observation, regularization selection, neural weight, reconstruction, or endpoint exists. The Movie009 failure is preserved and is not reinterpreted as a pass.

No new Kerr ray, physical path integral, hull/critical root, or Paper-I unit is authorized.

## 1. Isolated scientific question

Can the first indirect Kerr image recover a physically natural, analytically defined historical feature that is:

- exactly absent from the direct-image retarded-time footprint;
- outside the old 595-dimensional movie representation;
- not selected from an order-1 singular vector;
- embedded in a shared low-order background that both reconstruction classes can represent?

This changes one experimental factor relative to Movie009: the shared background is placed in the intersection of the old and rich finite source spaces, so failure or success of the historical endpoint is not confounded by an unrelated off-basis present-time scene. The old feature alternatives remain analytic and unprojected.

## 2. Physical acquisition, metric, and source difference

Reuse the authenticated Movie007 q8 inverse and q12 reference Kerr arrays, union support weights, shared direct-reference noise calibration, ideal order labels, 8x8 pixels per order, and 13 observer times. The operator/noise conventions and hashes are unchanged from Movie009.

The twin-feature families and parameter ranges are unchanged from Movie009:

1. narrow orbiting hotspot with angular bandwidth beyond `m<=3`;
2. opposite-shear spiral/arc;
3. split/merge topology with alternative axes;
4. inward-versus-outward radial plume.

All old features use the compact C2 plateau window registered in Movie009 amendment 001: zero outside `(-30,-6)M`, unity on `[-26,-10]M`, smooth transitions on the four-M boundaries. Hence every sibling difference is structurally zero on the q8/q12 direct rays.

## 3. Shared background in the model-space intersection

For normalized radius `R=(r-9.5)/3.5` and normalized time `T=tau/32`, the shared contrast background is

`b = a0 + a1 R + a2 R^2 + (u0+u1 T)(1+0.25R) cos(phi-p1) + (v0+v1 T)(1-0.20R) cos(2phi-p2)`.

Coefficient ranges are fixed before generation:

- `a0 in [0.05,0.10]`, `a1 in [-0.025,0.025]`, `a2 in [-0.015,0.025]`;
- `u0 in [0.05,0.11]`, `u1 in [-0.025,0.025]`;
- `v0 in [0.025,0.065]`, `v1 in [-0.015,0.015]`;
- phases uniform on `[-pi,pi)`.

This is a product of global radial polynomials of degree at most two, angular harmonics through m=2, and a global linear temporal function. It lies in both tensor-product source spaces up to floating-point projection accuracy. Every twin must remain at emissivity at least 0.35 on the fixed evaluation grid.

## 4. Populations and noise

Fresh seeds:

- validation pairs: 8 per first-three family, seed `100061`;
- held-out test pairs: 16 per all four families, seed `100062`;
- test noise: four paired draws per sibling and SNR, seed `100063`;
- bootstrap: 2,000 midpoint-pair resamples, seed `100064`.

Radial plume remains completely excluded from neural training and validation. Sources are admitted only by finiteness, positivity, exact direct-support separation, and activity on at least nine old frames. No order-1 response or reconstruction metric enters admission.

## 5. Classical methods

Use the frozen old 595-dimensional Movie007 ridge as a baseline and the frozen Movie009 rich source class:

- 7 cubic radial B-splines;
- real Fourier factors through m=5;
- 21 linear temporal B-splines;
- dimension 1617.

The source-independent rich q8/q12 operators and source Gram from Movie009 are rehashed and reused. Select rich ridge exponents separately by arm from `-7,...,3` using only the fresh first-three-family validation pairs at SNR300 and median support-weighted total-movie error. No test or family-specific tuning.

Classical Stage-A gates:

1. direct sibling means are <=1e-10 whitened at q8/q12;
2. clean and fitted q8/q12 discrepancies are <=5e-4 relative and <=0.1 whitened;
3. rich labelled individual identification >=0.90 and pair-both-correct >=0.80;
4. rich labelled 95%-reliable movie span >=12M and exceeds direct by >=8M;
5. at least three of four families, including radial plume, improve in paired integrated movie error.

## 6. Retarded Neural Field, conditional Stage B

The Stage-B architecture is frozen before Stage-A outcomes and runs only if Stage A passes.

Training population: 300 single-source histories from each of the first three feature families, seed `100050`; each uses the same intersection-background formula, one randomly selected feature alternative, random amplitude multiplier in `[0.5,1.0]`, and noisy q8 observations at a random SNR in `{100,300}`. No radial plume is used.

Separate direct and labelled networks are trained for seeds 11, 22, and 33. Each network has:

- an encoder from standardized whitened residual data through 256 and 96 GELU units;
- a continuous source decoder using normalized radius/time, raw azimuth harmonics through m=8, co-rotating phase harmonics through m=4, four temporal Fourier frequencies, and six fixed radial RBFs;
- two decoder layers of width 128 with GELU;
- bounded contrast output `0.85*tanh(raw)`.

Training uses AdamW, 1,200 updates, batch 24, learning rate 2e-3 with cosine decay, weight decay 1e-5, gradient clipping 1.0. At each update, 384 source-grid coordinates are sampled, 75% from the registered union-support distribution and 25% uniformly. Checkpoints at 600, 900, and 1,200 updates are selected by median validation support error across the first three families only.

Neural Stage-B gates, evaluated as the median over three seeds:

- labelled identification >=0.90 and pair-both-correct >=0.80;
- labelled 95%-reliable span >=10M and gain over direct >=8M;
- positive paired error reduction in at least three families, including held-out radial plume;
- direct identification in [0.45,0.55] under matched direct data;
- q8/q12 fitted-field checks pass on the preregistered first noise draw of every test twin.

A classical pass with neural failure remains a physical/inverse result and not a neural generalization claim.

## 7. Endpoints and scope

Use the unchanged Movie007 frame rule on `tau=0,-2,...,-28M`: active weighted relative error <=0.35 and weighted structural correlation >=0.75; inactive predicted RMS <=0.05. Report total-movie and differential-movie spans, twin identification, family reductions, q8/q12 checks, full-annulus control, and error projected into versus outside the old 595-dimensional movie subspace.

Success is a partial measurement-supported historical movie on one Kerr chart with ideal order labels. It is not full-annulus, visibility-domain, telescope, polarization, scattering, or observational recovery.
