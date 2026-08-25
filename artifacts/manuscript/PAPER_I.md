# Photon-Ring Retarded-Time Tomography I: Class-Dependent Identifiability and the Separation of Historical Reach from Algebraic Rank in Near-Critical Null Geodesics

**Preprint draft — theory and controlled synthetic computation only.**
No telescope detection, no laboratory result, and no recovery from a resolved
real photon ring is claimed anywhere in this manuscript.

- campaign tag `paper-I-campaign-final`, commit `03b0d1c9c63131aa553904df0c09849d641dee8f`
- registry sha256 `2ba66f0209fe1cdec97b8cf5862494c22fb94704318f9601a7a1f9eb4b783796`
- canonical artifact freeze: 265 artifacts, `artifacts/CANONICAL_ARTIFACT_FREEZE.json`
- every number below is registered in `artifacts/manuscript/CLAIM_LEDGER.json`
  with the artifact, row filter and column it was read from

---

## Abstract

Light that passes near the photon shell of a Kerr black hole reaches a distant
observer along a family of increasingly delayed null geodesics, so a single
image contains a superposition of source epochs. We ask what of that history is
actually recoverable, and we separate three questions that are routinely
conflated: whether a declared source model is identifiable, how far back in
retarded time an observation can see, and how strongly higher-order images are
suppressed.

We build a matrix-free whitened forward operator directly from per-ray Kerr
transfer maps on 12 registered spin–inclination geometries, retaining
orders n = 0, 1, 2. The measurement model is pixel-integrated with white noise
of fixed density per unit solid angle, so the whitened row carries
`sqrt(dOmega) g^3`; an earlier convention using `g^3` with a flat per-row noise
made Fisher information scale with pixel count and is retired, with the
correction and everything it moved recorded rather than absorbed.

Three results. First, **historical extension is real but modest and set by
inclination, not spin**: the resolved stack sees deeper than the direct image at
12 of 12 geometries, with median recoverable depth
60, 84 and 144 M at i = 20, 50 and 75 degrees, and the four
spins give a single value at every inclination. Second, **retarded-time
diversity supplies more of that reach than spatial remapping, but not all of
it**: measured against the direct image as the zero point, flattening the delays
costs a median 0.98 of the higher orders' entire contribution while
transplanting the spatial map costs 0.57. Third, and most consequential for
how such claims should be stated, **identifiability and historical reach are
different quantities that move independently**. Enriching the declared source
class from 224 to 1056 dimensions drives the resolved
operational-rank fraction down by 16.8 percentage points and the smallest
determined singular value down by five orders of magnitude, while the deepest
recoverable epoch moves by at most 1 grid step of 4 M. Full column
rank on the registered class is therefore a statement about that class and not
about the continuum: temporal enrichment alone exposes a direct-channel null
space of up to 100 dimensions.

We report a negative control throughout. Permuting each order's delays,
positions and weights independently — preserving all three marginals and
destroying only their pairing — yields a better-conditioned operator than the
physical one at 12 of 12 geometries across 16 frozen seeds.
Conditioning is not evidence of physical content, and no conclusion here rests
on it.

---

## 1. Introduction

A photon emitted from the equatorial plane near a Kerr black hole can reach a
distant observer directly, or after one or more near-critical windings around
the photon shell. Each additional half-orbit adds delay, so the n-th image of a
time-varying source shows that source as it was further in the past. This is the
observation behind every proposal to read accretion history out of a resolved
photon ring.

Whether that history can be *recovered* is a different question from whether it
is *present*, and the difference is where most of the difficulty lives. Three
quantities are easy to conflate:

1. **Algebraic identifiability** — does the forward operator have a trivial null
   space on the declared source model? This is a property of the pair (operator,
   model class), and a small enough class is identifiable under almost any
   operator.
2. **Historical reach** — how far into the past can a localized change in the
   source be detected at a given signal-to-noise ratio? This is a property of
   where the operator's *sensitivity* lives in retarded time.
3. **Throughput suppression** — how much fainter is each successive image? This
   is a property of the transfer coefficients alone and says nothing directly
   about either of the first two.

This paper measures all three on validated Kerr and Schwarzschild ray maps and
shows that they separate. It also documents a measurement-convention defect we
found and corrected mid-campaign, because several of the conclusions we would
otherwise have reported were artefacts of it.

### 1.1 What is deliberately not claimed

No statement here concerns a real observation. The source model is a declared
finite-dimensional class, and no result is extrapolated from full rank on such a
class to injectivity on a continuum of source functions — that inference is
exactly what section 7 shows to be invalid. No machine-learned reconstruction is
performed. No geometry-mismatch or order-leakage study is included. The
recoverable depth reported everywhere is a detection statement about a localized
unit-norm historical mode, never the largest delay any ray happens to carry.

---

## 2. Forward model and measurement convention

### 2.1 The operator

Each retained ray p of image order n lands at an equatorial source point
`(r, phi)` and carries a delay `Delta t` and a redshift factor `g`. The
observation at observer time `t_o` is built row by row rather than from an
order-wide delay:

```
z_{n,p}(t_o) = dOmega_{n,p} g_{n,p}^3 j(r_{n,p}, phi_{n,p}, t_o - Delta t_{n,p}) + eta
Var(eta)      = sigma_Omega^2 dOmega_{n,p}
```

The distinction from a delay ladder matters. The pilot geometry's orders span
*overlapping* retarded windows, so an image order does not correspond to one
source epoch, and `a_n j(t_o - n tau)` is only an asymptotic summary. A
distributed delay kernel and a delay ladder have different null spaces.

Whitening under the declared noise gives the row that every audit consumes:

```
Atilde = sqrt(dOmega) / sigma_Omega * g^3 * B(r, phi, t)
```

### 2.2 The square root is load-bearing

An earlier revision of this work used `c = g^3` with a flat per-row noise. That
convention makes the Fisher information scale with the *number of rows*:
splitting one pixel into k equal-area children carrying the same transfer value
multiplies the Gram matrix by k. Adaptive ray counts differ by an order of
magnitude across geometry and order, and the lensing bands differ in solid angle
by roughly three orders of magnitude, so the convention silently reweighted the
bands against one another — handing the thin, deep, high-order bands a far
quieter detector per unit sky than the direct image.

The corrected convention is invariant under the same split-and-merge test to
5.4e-15, against 7 for the retired one, and the check is a registered
gate. Every result in this manuscript is computed under the corrected
convention; section 9 lists what the correction moved.

Derived arms are linear maps of the same resolved data with their covariance
propagated, never separate models with their own noise level:

```
unresolved image   y_U = L y_R,  C_U = L C_R L^T
total flux         y_F = S y_R,  C_F = S C_R S^T
```

with `C_R = sigma_Omega^2 diag(dOmega)`. One noise density is fixed once from
the direct arm's clean response to the declared reference source and shared by
every arm. No arm may choose its own sigma; an arm that did would be measuring
its own row count.

### 2.3 Source classes and the localized historical probe

The registered primary class **C224** is 4 radial cubic B-splines (uniform knots
in log r) x 7 real azimuthal Fourier modes x 8 global temporal DCT modes =
224 dimensions. Every temporal factor spans the whole history, so C224
answers "can a low-dimensional global model be fitted" and cannot be indexed by
epoch.

Epoch-resolved questions use the **localized class**: the same radial and
azimuthal factors crossed with one compact Gaussian bump in retarded age of half
width 3 M. Its m = 0, partition-of-unity contraction is a spatially flat
scalar probe, and both are used — the scalar probe for the registered depth and
innovation statistics, the full 28-dimensional class where a spatially flat
probe would be blind (section 5.2).

---

## 3. Geometries, ray maps, and the common age grid

Twelve registered geometries span spin a* in (0, 0.5, 0.9, 0.98) and inclination
in (20, 50, 75) degrees, with orders n = 0, 1, 2 and 1536 rays retained per
order, stratified in screen azimuth, source radius and delay with each band's
total solid angle preserved. Observations are 8 times over 20 M.

At exactly zero spin the pinned tracer packages are unusable — one package's
critical-curve parameterization is singular there and the other's default
Keplerian branch sets the orbital angular velocity to zero — so an explicitly
validated Schwarzschild backend is used, and the orbital orientation at a* = 0
is the a -> 0+ disk-rotation branch. A Schwarzschild black hole has no preferred
spin direction, but the disk still has an orbital orientation, and matching the
positive-spin limit keeps the grid continuous.

### 3.1 Delay summaries that converge

The sampled maximum ray delay is an extreme-value statistic set by whichever
single ray sits closest to a band edge. It does not converge under refinement
and is not used as a historical depth anywhere in this work. The converging
summaries are weighted quantiles under three weightings: solid angle
(`dOmega`), throughput (`dOmega g^3`), and Fisher (`dOmega g^6`, the squared
whitened row weight). Only the first two are properties of the spacetime and the
transfer alone; the third depends on the declared measurement model and is
labelled as such.

The common age ceiling is fixed from those source-independent summaries over the
*whole* grid before any operator is evaluated:

```
A_max = T_obs + 1.25 max_(g,n) {Q_0.999^Omega, Q_0.999^I} + 2h
      = 249.6 M  ->  252 M after rounding up to the age step
```

with the maximum, 178.9 M, occurring at `a098_i075`. Because the ceiling sits
above the deepest ray any geometry carries, 0 of 1152 depth entries in
the whole campaign are right-censored: the depths reported below are
measurements, not grid ceilings. For contrast, the largest sampled maximum delay
anywhere on the grid is 191.5 M — the statistic we do not use.

---

## 4. Correctness

Every mechanical gate is the worst case over all 12 geometries (E3C) or all
class–anchor combinations (E3D).

| gate | status | measured | threshold |
|---|---|---:|---:|
| `E3C_G2_physical_dense_matrix_free` | **PASS** | 0 | 1e-10 |
| `E3C_G3_physical_adjoint` | **PASS** | 2.67e-13 | 1e-08 |
| `E3C_G4_physical_resolved_unresolved_mixing` | **PASS** | 0 | 1e-10 |
| `E3C_G4b_linear_collapse_covariance_propagation` | **PASS** | 0 | 1e-12 |
| `E3C_G6_physical_Gram_monotonicity` | **PASS** | 1.86e-16 | 1e-10 |
| `E3C_G6b_resolved_dominates_direct` | **PASS** | 1.57e-16 | 1e-10 |
| `E3C_G9w_weight_semantics` | **PASS** | 4.38e-16 | 1e-10 |
| `E3C_freeze_raymap_hashes` | **PASS** | 0 | 0 |
| `E3C_frozen_grid_invariance` | **PASS** | dims=[224] n_ages=[64] | dims=[224] n_ages=[64] |
| `E3C_H2_registered_statistic_is_an_identity` | **PASS** | 12 | 12 |
| `E3D_adjoint` | **PASS** | 4.89e-13 | 1e-08 |
| `E3D_dense_smoke_comparison` | **PASS** | 0 | 1e-10 |
| `E3D_Gram_monotonicity` | **PASS** | 1.14e-16 | 1e-10 |
| `E3D_class_nesting` | **PASS** | 2.73e-14 | 1e-10 |
| `E3D_enrichment_does_not_lose_rank` | **PASS** | 0 | 0 |
| `G10q_continuum_noise_quadrature_invariance` | **PASS** | 5.4e-15 | 1e-10 |

`E3C_freeze_raymap_hashes` re-checks every ray map against the digest pinned
before evaluation; `E3C_frozen_grid_invariance` checks that the class dimension
and age grid were identical at every geometry. `E3D_class_nesting` is discussed
in section 7.

---

## 5. Results

### 5.1 Historical extension is real, modest, and set by inclination

At the reference SNR the resolved stack sees deeper than the direct image at
12 of 12 geometries, and carries strictly positive historical
innovation beyond the direct channel's own 99.9% throughput-weighted age
boundary at 12 of 12.

**Recoverable depth, resolved stack (M):**

| a\* \ i | 20° | 50° | 75° | trend in inclination |
|---|---:|---:|---:|---|
| 0.00 | 60 | 84 | 144 | nondecreasing |
| 0.50 | 60 | 84 | 144 | nondecreasing |
| 0.90 | 60 | 84 | 144 | nondecreasing |
| 0.98 | 60 | 84 | 144 | nondecreasing |
| **trend in spin** | constant | constant | constant | |

**Recoverable depth, direct image alone (M):**

| a\* \ i | 20° | 50° | 75° | trend in inclination |
|---|---:|---:|---:|---|
| 0.00 | 20 | 60 | 140 | nondecreasing |
| 0.50 | 20 | 60 | 140 | nondecreasing |
| 0.90 | 20 | 60 | 140 | nondecreasing |
| 0.98 | 20 | 60 | 140 | nondecreasing |
| **trend in spin** | constant | constant | constant | |

The surface is flat in spin and steep in inclination. At each of the three
inclinations the four spins give a single value of the resolved depth
(1, 1 and 1 distinct values respectively); the medians
are 60, 84 and 144 M for the resolved stack against 20,
60 and 140 M for the direct image. Whatever
sets historical reach in this operator, it is the geometry of the retarded
windows as seen from a given viewing angle, not the spin parameter.

Depth is a threshold statement, so we report alongside it the
threshold-independent **historical innovation**

```
J_old = integral over a > A_0,0.999 of log(1 + I(a)) da
```

which integrates information about the localized epoch over exactly the region
where the direct channel is essentially absent.

**Historical innovation, resolved stack:**

| a\* \ i | 20° | 50° | 75° | trend in inclination |
|---|---:|---:|---:|---|
| 0.00 | 67.86 | 40.93 | 12.36 | nonincreasing |
| 0.50 | 69.94 | 41.21 | 15.88 | nonincreasing |
| 0.90 | 70.81 | 40.44 | 16.07 | nonincreasing |
| 0.98 | 71.53 | 40.51 | 16.22 | nonincreasing |
| **trend in spin** | nondecreasing | nonmonotone | nondecreasing | |

**Historical innovation, direct image alone:**

| a\* \ i | 20° | 50° | 75° | trend in inclination |
|---|---:|---:|---:|---|
| 0.00 | 15.02 | 8.34 | 5.07 | nonincreasing |
| 0.50 | 15.28 | 8.78 | 4.92 | nonincreasing |
| 0.90 | 15.37 | 8.24 | 5.09 | nonincreasing |
| 0.98 | 15.40 | 7.99 | 5.24 | nonincreasing |
| **trend in spin** | nondecreasing | nonmonotone | nonmonotone | |

`J_old` falls with inclination while depth rises with it. The two are not in
tension: at high inclination the direct channel already reaches far back, so the
*additional* history the higher orders supply is a smaller increment even though
the absolute reach is larger.

The incremental Gram operator `delta_G = G_resolved - G_direct` separates
information reweighted inside the direct channel's support from genuinely new
historical information beyond it. Its rank runs from 195 to
224 of 224:

| a\* \ i | 20° | 50° | 75° | trend in inclination |
|---|---:|---:|---:|---|
| 0.00 | 224 | 224 | 195 | nonincreasing |
| 0.50 | 224 | 224 | 196 | nonincreasing |
| 0.90 | 224 | 224 | 196 | nonincreasing |
| 0.98 | 224 | 224 | 197 | nonincreasing |
| **trend in spin** | constant | constant | nondecreasing | |

### 5.2 A registered statistic that could not answer its own question

The registered mechanism test compares the full and substituted age-information
curves through a relative discrepancy `D`. Applied to the delay-only
substitution it is **identically zero at every geometry**, with a maximum over
the whole grid of 0.0e+00.

This is an algebraic identity, not a finding. The registered probe is spatially
flat, and the delay-only substitution replaces only `source_r` and `source_phi`;
the scalar curve therefore *cannot* depend on the substitution. We verified the
curves are bitwise identical at all 12 geometries and locked that fact
behind a gate, so the zero can never be re-read as support for the delay
mechanism. Reporting it as such would have been circular.

The literal values are preserved on the record. Amendment 002 adds the
comparison that can discriminate: the age-resolved information matrix on the
registered 28-dimensional localized class, each probe normalised to unit L2 norm
over the emission region, compared through the log information volume
`sum_k log(1 + SNR^2 lambda_k(a))`.

### 5.3 Delay diversity supplies more of the reach than spatial remapping

Two substitution arms isolate the candidate mechanisms while holding the
measurement model, the noise, the source class and the ray weights fixed.
`DELAY_ONLY` keeps each order's physical delays and takes the direct order's
spatial map; `SPATIAL_ONLY` keeps each order's spatial map and flattens every
delay onto the direct order's.

| geometry | D_delay (registered) | D_delay | D_spatial | D_direct | D_delay / D_direct | D_spatial / D_direct |
|---|---:|---:|---:|---:|---:|---:|
| `a000_i020` | 0.0e+00 | 0.1691 | 0.3108 | 0.3147 | 0.537 | 0.988 |
| `a000_i050` | 0.0e+00 | 0.1512 | 0.2060 | 0.2307 | 0.655 | 0.893 |
| `a000_i075` | 0.0e+00 | 0.1651 | 0.3036 | 0.2294 | 0.720 | 1.324 |
| `a050_i020` | 0.0e+00 | 0.1469 | 0.3229 | 0.3276 | 0.448 | 0.986 |
| `a050_i050` | 0.0e+00 | 0.1685 | 0.2041 | 0.2475 | 0.681 | 0.825 |
| `a050_i075` | 0.0e+00 | 0.2747 | 0.3418 | 0.2663 | 1.032 | 1.283 |
| `a090_i020` | 0.0e+00 | 0.1749 | 0.3344 | 0.3400 | 0.514 | 0.983 |
| `a090_i050` | 0.0e+00 | 0.1613 | 0.2183 | 0.2688 | 0.600 | 0.812 |
| `a090_i075` | 0.0e+00 | 0.2147 | 0.3099 | 0.3074 | 0.699 | 1.008 |
| `a098_i020` | 0.0e+00 | 0.1653 | 0.3386 | 0.3457 | 0.478 | 0.979 |
| `a098_i050` | 0.0e+00 | 0.1187 | 0.2416 | 0.2984 | 0.398 | 0.810 |
| `a098_i075` | 0.0e+00 | 0.1288 | 0.3734 | 0.3379 | 0.381 | 1.105 |

The direct arm's discrepancy is the natural zero point: it is what remains when
the higher orders are removed altogether. Normalised by it, flattening the
delays costs a median 0.98 of everything the higher orders contribute —
essentially all of it — while transplanting the spatial map costs 0.57.
Delay-only is the closer of the two substitutions at 12 of 12
geometries.

**This is weaker than a single-geometry canary suggested.** Under the scalar
statistic the delay-only arm looked like an exact reproduction of the full
operator. On the localized class it is a median 0.165 relative departure
against the direct arm's 0.303. Retarded-time diversity carries the larger
share of the historical reach; it does not carry all of it, and spatial
remapping is not negligible.

Conditioning is reported beside the discrepancy deliberately: spatial remapping
can improve `kappa+` without moving the oldest detectable epoch, so reading the
mechanism off a depth endpoint alone would credit delay with work that spatial
diversity does.

### 5.4 What the order labels are worth

`UNRESOLVED_IMAGE` sums the orders into a single image plane and pays the summed
noise through `C_U = L C_R L^T`.

| geometry | T(unresolved) / T(resolved) | J_old(unresolved) / J_old(resolved) |
|---|---:|---:|
| `a000_i020` | 0.333 | 0.243 |
| `a000_i050` | 0.714 | 0.235 |
| `a000_i075` | 0.972 | 0.439 |
| `a050_i020` | 0.333 | 0.241 |
| `a050_i050` | 0.714 | 0.245 |
| `a050_i075` | 0.972 | 0.381 |
| `a090_i020` | 0.333 | 0.244 |
| `a090_i050` | 0.714 | 0.240 |
| `a090_i075` | 0.972 | 0.382 |
| `a098_i020` | 0.333 | 0.243 |
| `a098_i050` | 0.714 | 0.233 |
| `a098_i075` | 0.972 | 0.393 |

Depth degrades gracefully — the ratio runs from 0.33 to 0.97, reaching
0.97 at high inclination where the direct channel already dominates the
reach. Historical innovation does not: the ratio runs 0.23 to 0.44.
Explicit order labels are close to dispensable for *how far back* one can see
and load-bearing for *how much* is learned about that history.

### 5.5 Throughput suppression and sensitivity suppression are different exponents

Comparing orders requires matched support. Each order is sampled at the same
fractional position within its own retarded window, giving

```
Gamma_sensitivity_matched = -0.5 log( I_{n+1}^matched / I_n^matched )
```

against the throughput exponent `Gamma_amp = -log(A_g ratio)`. All 19 window
fractions are retained at every geometry.

| geometry | pair | defined / 19 | median | IQR | Gamma_amp | difference | window overlap | disposition |
|---|---|---:|---:|---:|---:|---:|---:|---|
| `a000_i020` | 0->1 | 19 | 2.614 | 0.397 | 4.714 | 2.100 | 0.000 | **undefined** |
| `a000_i020` | 1->2 | 19 | 1.831 | 0.124 | 3.602 | 1.771 | 0.534 | supported |
| `a000_i050` | 0->1 | 19 | 2.441 | 0.583 | 4.274 | 1.833 | 0.115 | supported |
| `a000_i050` | 1->2 | 19 | 2.187 | 0.263 | 3.887 | 1.700 | 0.493 | supported |
| `a000_i075` | 0->1 | 19 | 1.979 | 0.909 | 3.248 | 1.269 | 0.308 | supported |
| `a000_i075` | 1->2 | 19 | 2.059 | 0.131 | 4.057 | 1.998 | 0.578 | supported |
| `a050_i020` | 0->1 | 19 | 2.723 | 0.126 | 4.681 | 1.958 | 0.000 | **undefined** |
| `a050_i020` | 1->2 | 19 | 1.794 | 0.018 | 3.501 | 1.706 | 0.545 | supported |
| `a050_i050` | 0->1 | 19 | 2.486 | 0.561 | 4.272 | 1.786 | 0.114 | supported |
| `a050_i050` | 1->2 | 19 | 2.120 | 0.157 | 3.784 | 1.664 | 0.521 | supported |
| `a050_i075` | 0->1 | 19 | 1.530 | 0.815 | 2.870 | 1.340 | 0.309 | supported |
| `a050_i075` | 1->2 | 19 | 2.569 | 0.343 | 4.388 | 1.819 | 0.519 | supported |
| `a090_i020` | 0->1 | 19 | 2.609 | 0.259 | 4.620 | 2.010 | 0.000 | **undefined** |
| `a090_i020` | 1->2 | 19 | 1.704 | 0.112 | 3.203 | 1.499 | 0.545 | supported |
| `a090_i050` | 0->1 | 19 | 2.492 | 0.568 | 4.249 | 1.758 | 0.117 | supported |
| `a090_i050` | 1->2 | 19 | 1.950 | 0.211 | 3.548 | 1.599 | 0.557 | supported |
| `a090_i075` | 0->1 | 19 | 1.560 | 0.884 | 2.875 | 1.315 | 0.309 | supported |
| `a090_i075` | 1->2 | 19 | 2.310 | 0.403 | 4.251 | 1.941 | 0.571 | supported |
| `a098_i020` | 0->1 | 10 | 1.909 | 3.409 | 4.592 | 2.683 | 0.435 | **undefined** |
| `a098_i020` | 1->2 | 19 | 1.682 | 0.042 | 3.075 | 1.394 | 0.536 | supported |
| `a098_i050` | 0->1 | 19 | 2.679 | 1.197 | 4.230 | 1.551 | 0.139 | supported |
| `a098_i050` | 1->2 | 19 | 1.684 | 0.627 | 3.356 | 1.672 | 0.724 | **undefined** |
| `a098_i075` | 0->1 | 19 | 1.611 | 1.013 | 2.872 | 1.262 | 0.304 | supported |
| `a098_i075` | 1->2 | 19 | 2.230 | 0.261 | 4.120 | 1.889 | 0.559 | supported |

**5 of 24 cells are marked
`UNDEFINED_NO_COMMON_MATCHED_SUPPORT` and are named rather than dropped:**

| geometry | pair | reasons |
|---|---|---|
| `a000_i020` | 0->1 | windows_disjoint |
| `a050_i020` | 0->1 | windows_disjoint |
| `a090_i020` | 0->1 | windows_disjoint |
| `a098_i020` | 0->1 | fractions_without_information, negative_exponent_fractions |
| `a098_i050` | 1->2 | negative_exponent_fractions |

The zero-overlap cells are the substantive caveat. At i = 20 degrees the n = 0
and n = 1 retarded windows are disjoint, so sampling both at the same fractional
position compares two epochs that share no support at all; the statistic is
still computed and reported, but "matched support" is not what it means there.
These cells remain in every denominator: the interpretable set is
19 of 24, not 19 of 19.

On the 19 interpretable cells the sensitivity exponent is below the
throughput exponent in all 19, with median difference
1.700 and range 1.262 to 1.998. A single scalar attenuation
exponent describes the flux and misdescribes the information.

At the canary geometry, the corrected medians are 2.486 (0 to 1) and
2.120 (1 to 2) against throughput exponents 4.27 and 3.78. The same
quantities computed independently in the single-geometry canary tables give
2.486 and 2.120. The corrected gap is close to a convention-level identity:
whitened rows carry `sqrt(dOmega)` where flux carries `dOmega`, so information
scales linearly in solid angle where throughput scales quadratically, and the
exponent difference is approximately half the log solid-angle demagnification.
**No asymptotic law is fitted**: n = 0, 1, 2 does not determine one.

### 5.6 The geometry surface

These are twelve deterministic registered geometries, not a sample from a
population. No p-value, confidence interval or significance claim appears
anywhere in this paper; the surface is reported cell by cell.

**Operational rank, resolved stack, of 224:**

| a\* \ i | 20° | 50° | 75° | trend in inclination |
|---|---:|---:|---:|---|
| 0.00 | 203 | 201 | 185 | nonincreasing |
| 0.50 | 203 | 201 | 184 | nonincreasing |
| 0.90 | 203 | 203 | 189 | nonincreasing |
| 0.98 | 203 | 205 | 193 | nonmonotone |
| **trend in spin** | constant | nondecreasing | nonmonotone | |

**Operational rank, direct image, of 224:**

| a\* \ i | 20° | 50° | 75° | trend in inclination |
|---|---:|---:|---:|---|
| 0.00 | 133 | 153 | 159 | nondecreasing |
| 0.50 | 134 | 153 | 157 | nondecreasing |
| 0.90 | 135 | 154 | 157 | nondecreasing |
| 0.98 | 133 | 153 | 156 | nondecreasing |
| **trend in spin** | nonmonotone | nonmonotone | nonincreasing | |

**Conditioning `kappa+`, resolved stack:**

| a\* \ i | 20° | 50° | 75° | trend in inclination |
|---|---:|---:|---:|---|
| 0.00 | 7.04e+05 | 7.03e+05 | 2.88e+07 | nonmonotone |
| 0.50 | 7.12e+05 | 7.04e+05 | 1.73e+07 | nonmonotone |
| 0.90 | 8.56e+05 | 6.98e+05 | 1.36e+07 | nonmonotone |
| 0.98 | 1.19e+06 | 2.00e+05 | 7.53e+06 | nonmonotone |
| **trend in spin** | nondecreasing | nonmonotone | nonincreasing | |

Read off the cells rather than summarised: the resolved operational rank is
constant at i = 20, nondecreasing at i = 50, nonmonotone at i = 75; nonincreasing at a* = 0.00, nonincreasing at a* = 0.50, nonincreasing at a* = 0.90, nonmonotone at a* = 0.98. There is no clean monotone spin trend, and section 6.2 shows
that what trend there is in rank is partly confounded with the source domain and
must not be read as a pure spacetime effect. The inclination dependence is the
robust one, and it runs opposite to depth: higher inclination buys reach and
costs identifiable directions.

### 5.7 Arms at a glance

| arm | operational rank (median) | range | kappa+ (median) | J_old (median) | T_rec (median) |
|---|---:|---|---:|---:|---:|
| `DIRECT_PHYSICAL` | 153 | 133–159 | 9.00e+08 | 8.29 | 60 |
| `RESOLVED_PHYSICAL` | 202 | 184–205 | 7.84e+05 | 40.72 | 84 |
| `UNRESOLVED_IMAGE` | 178 | 173–183 | 9.52e+06 | 9.66 | 60 |
| `TOTAL_FLUX` | 13 | 12–14 | 9.86e+08 | 6.90 | 56 |
| `DELAY_ONLY` | 212 | 193–216 | 9.50e+04 | 40.72 | 84 |
| `SPATIAL_ONLY` | 178 | 140–209 | 9.76e+06 | 8.33 | 60 |
| `EQUALIZED_ORDER_SENSITIVITY` | 216 | 196–222 | 5.04e+04 | 306.70 | 120 |
| `PAIRING_DESTROYED` | 221 | 217–224 | 1.80e+04 | 28.72 | 72 |

Two rows in that table are not measurement architectures and must not be read
as ones. `EQUALIZED_ORDER_SENSITIVITY` removes the physical attenuation between
orders by fiat; its large `J_old` and depth are an oracle bound on what
attenuation costs, not an achievable configuration. `PAIRING_DESTROYED` is the
nonphysical negative control of section 6.1. `TOTAL_FLUX` is a genuine but
deliberately impoverished readout: it collapses all spatial information and
reaches a median operational rank of 13 against the resolved
stack's 202, and is included as a floor.

---

## 6. Controls

### 6.1 A physically meaningless operator is better conditioned than the real one

`PAIRING_DESTROYED` permutes delay, spatial position and quadrature weight
independently within each order. All three marginals survive; only their pairing
is destroyed. Over 16 frozen seeds per geometry it reaches a median
operational rank of 220 and a worst-case conditioning of
5.81e+04, against the physical resolved operator's median
7.84e+05. At 12 of 12 geometries the *worst* seed is still
better conditioned than the physical operator.

This is a nonphysical control and is never ranked as an alternative measurement
architecture. Its purpose is to refute a specific inference: any argument that
reads good conditioning, high operational rank or a large stable rank as
evidence that an operator is capturing physical structure is refuted by these
rows.

### 6.2 The source domain moves with spin, and we measured how much

The registered radial support is geometry-dependent — the knots follow the rays,
and a higher-spin geometry's rays reach closer to the horizon. A spin trend in
any rank statistic is therefore partly a statement about the source domain.
Rather than assume the confound away, we repeated three anchor geometries on one
fixed radial interval in r/M with identical knot locations.

Operational rank moves under the common support in 12 of 24
anchor–arm combinations, by at most 5 of 224. Recoverable depth is
unchanged in 23 of 24. Read strictly: the spin trends in
operational rank are partly confounded with the source domain; the depth and
innovation results are not.

Separately, near-horizon *ray* coverage does not imply that the emissivity model
physically emits to the horizon. Ray-map support and assumed source emission are
different objects and are kept apart throughout.

---

## 7. Full rank on a declared class is a statement about that class

The registered class C224 reaches full column rank under
21 of 21 arm–anchor combinations. That fact is often where such
analyses stop. It should not be, because it is a joint property of the operator
and a 224-dimensional model, and the way to find out how much of it is the
model's poverty is to enrich the model.

We do so along a nested ladder on three anchor geometries. The azimuthal and
temporal factors are literal prefixes, so their columns are preserved; the
radial cubic B-spline factor is refined, so its columns move while its span is
contained in the enriched span, to 2.7e-14. Rank statements depend on the
span, and that is what the nesting gate checks. Exact adjoint, Gram monotonicity
and a dense smoke comparison were run at every class including the
1056-dimensional one; the worst dense-versus-matrix-free discrepancy
is 0.0e+00.

| class | radial | azimuthal | temporal | dimension | resolved operational rank | as a fraction | sigma_min+ |
|---|---:|---:|---:|---:|---:|---:|---:|
| `C224` | 4 | 7 | 8 | 224 | 201 | 0.897 | 1.63e-02 |
| `C448_T` | 4 | 7 | 16 | 448 | 365 | 0.815 | 7.16e-05 |
| `C528_S` | 6 | 11 | 8 | 528 | 441 | 0.835 | 2.87e-04 |
| `C1056_ST` | 6 | 11 | 16 | 1056 | 770 | 0.729 | 1.33e-07 |

Rank deficiency by arm and class. Each cell gives how many of the three anchor
geometries are rank-deficient and the range of nullities among those that are;
`full` means every anchor reaches full column rank. Aggregating to a single
worst nullity would report a deficiency for an arm that is clean at two anchors
out of three, which is a different finding:

| arm | `C224` (224) | `C448_T` (448) | `C528_S` (528) | `C1056_ST` (1056) |
|---|---:|---:|---:|---:|
| `DIRECT_PHYSICAL` | full | **3/3, −4 to −100** | **1/3, −6** | **3/3, −109 to −265** |
| `RESOLVED_PHYSICAL` | full | **1/3, −1** | full | **3/3, −11 to −35** |
| `UNRESOLVED_IMAGE` | full | **1/3, −1** | full | **3/3, −14 to −35** |
| `DELAY_ONLY` | full | **1/3, −1** | full | **1/3, −36** |
| `SPATIAL_ONLY` | full | **2/3, −23 to −91** | full | **2/3, −60 to −228** |
| `EQUALIZED_ORDER_SENSITIVITY` | full | **1/3, −1** | full | **3/3, −4 to −25** |
| `PAIRING_DESTROYED` | full | full | full | full |

Four findings.

**Temporal enrichment alone breaks it.** Doubling the temporal resolution while
holding the spatial factors fixed leaves 9 of the 21
arm–anchor combinations rank-deficient, with the direct channel deficient at
every anchor and losing up to 100 dimensions of 448. Nothing about the geometry changed; only the question being asked
of it.

**Spatial enrichment is far gentler.** At C528_S only 1 of the
21 combinations are deficient — the direct channel at a single anchor,
by 6 dimensions of 528. The operator
resolves the declared spatial class much better than the declared temporal one —
the same asymmetry the mechanism decomposition found from the other side.

**At the richest class the full physical operator has a null space.**
15 of the 21 combinations are deficient at C1056_ST,
including the resolved stack itself (up to 35 dimensions of
1056) and the direct channel (up to 265).

**The negative control never loses rank.** `PAIRING_DESTROYED` reaches full
column rank at every class and every anchor, including the
1056-dimensional one, where the physical resolved operator does not.
An operator with no physical content is the only one on the table that stays
identifiable under enrichment. This is the same lesson as section 6.1 arriving
from the rank side: identifiability is not a measure of physical fidelity.

**The delay-only equivalence does not survive enrichment.** Indistinguishable
from the resolved operator by rank on C224, the two separate once the model is
rich enough — and not always in the direction one would guess, because
substituting the direct order's well-sampled spatial map onto every order is not
a strict impoverishment. `DELAY_ONLY` is a mechanism probe, not a measurement
architecture.

### 7.1 Identifiability and reach move independently

Over the same ladder the resolved *operational*-rank fraction falls by
16.8 percentage points and the smallest determined singular value falls
from 1.63e-02 to 1.33e-07 — five orders of magnitude. Recoverable
depth moves in 7 of 18 physical anchor–arm rows and never by more
than 1 grid step of 4 M.

This is the cleanest statement the campaign supports. **A rank statement is not
a depth statement, in either direction, and neither is evidence for the other.**
Enriching a source model exposes directions the operator cannot determine; it
barely changes how far back in retarded time the operator can see. Papers that
report identifiability and papers that report historical reach are reporting
different physics, and a result in one does not transfer to the other.

---

## 8. Discussion

The picture that survives all of the above is narrower than the one a
single-geometry study would support, and we think it is the useful one.

Near-critical null geodesics do create a long, distributed, overlapping
retarded-time transfer structure. That structure is not a delay ladder: orders
share retarded windows, each ray carries its own delay, and treating the n-th
image as a snapshot of one past epoch is an asymptotic convenience that the
operator's null structure does not respect.

Higher-order images are drastically suppressed in integrated brightness and
retain disproportionate — though not, as we first reported, dramatically
disproportionate — Fisher sensitivity to historical source modes. The gap
between the throughput and sensitivity exponents is real, roughly a factor of
two in the exponent on the interpretable cells, and is largely accounted for by
the solid-angle scaling that whitening imposes rather than by anything
distinctive about near-critical geodesics.

Recoverable history is controlled by an information-weighted temporal kernel. It
is not controlled by the oldest ray, which is an extreme-value statistic that
does not converge; not by total photon-ring flux, which the equalized-sensitivity
arm shows to be a poor proxy; and not by algebraic rank, which section 7 shows
can move by hundreds of dimensions while depth moves by one grid step.

The most transferable methodological point is negative. Three of the quantities
one would naturally reach for — total information, algebraic rank, conditioning —
each fail as proxies for recoverable history in a specific, demonstrable way:
total information is dominated by the bright direct image and barely moves when
the informative deep orders are added; rank is a property of the declared class;
and conditioning is optimised by a permutation with no physical content at all.

---

## 9. What the measurement-model correction changed

The defect and its consequences are recorded in the invalidation ledger as
`D-H_flat_sigma_measurement_convention`, and 33 artifacts produced under the
retired convention are marked `SUPERSEDED_MEASUREMENT_MODEL_DEFECT`. No table in
this manuscript is built from any of them; the builder reads its inputs through
the canonical freeze and raises on a superseded path.

What moved, at the canary geometry. The retired-convention values in the middle
column are quoted from the defect record and from the pre-correction commit's
tables; they are deliberately *not* in the claim ledger, because the ledger may
only cite canonical artifacts and those bytes are superseded:

| quantity | retired convention | corrected convention |
|---|---:|---:|
| `Gamma_sensitivity_matched`, 0 to 1 | 0.576 | 2.486 |
| `Gamma_sensitivity_matched`, 1 to 2 | 0.387 | 2.120 |
| resolved trace information | — | 8.944e+08 |
| direct trace information | — | 8.845e+08 |
| resolved-over-direct trace information gain | 82% | 1.12% |
| equalized-arm depth advantage | one grid step | tens of M |

The first row is the one that mattered scientifically. Under the retired
convention the sensitivity exponent was roughly seven to ten times smaller than
the throughput exponent, which reads as "information decays far more slowly than
flux". Corrected, it is about half — a real effect, but an ordinary one. The
82% trace-information gain becomes 1.12%: the resolved stack collects
almost no additional photons, and its value is that its operational rank still
rises from 153 to 201 of 224. Structure, not signal.

What did not move under the correction: the ordering of the mechanism
decomposition, the negative control's superior conditioning, and full algebraic
rank on C224.

The mechanism conclusion was nonetheless weakened, by a separate finding rather
than by this correction. Amendment 002 (section 5.2) established that the
registered mechanism statistic could not see the delay-only substitution at all.
On the diagnostic that can, delay diversity is still the larger contribution but
no longer the whole of it. Two distinct problems, corrected independently, both
in the direction of a smaller claim.

---

## 10. Limitations

1. **Declared classes, not the continuum.** Every rank and nullity is relative
   to a finite-dimensional class. Section 7 is a demonstration that this
   qualification is load-bearing, not a formality.
2. **Three image orders.** Orders above n = 2 are not computed. No asymptotic
   exponent in n is fitted, and none should be read off the three points here.
3. **One emissivity and flow prescription.** The throughput exponent is a
   property of the frozen specific-intensity and Keplerian-flow prescription. It
   is not the geometric Kerr critical exponent and is not identified with it
   anywhere.
4. **A source domain that moves with spin.** The primary radial support follows
   the rays. Section 6.2 measures the confound on three anchors; it does not
   remove it from the primary surface.
5. **5 matched-support cells are undefined.** At low inclination the
   n = 0 and n = 1 retarded windows are disjoint. Those cells are reported and
   retained in every denominator, but they carry no exponent.
6. **No real data, no reconstruction, no learning.** The operator is analysed;
   nothing is inverted against an observation, and no estimator is trained.
7. **Single-instrument idealisation.** One monochromatic, spatially resolved
   intensity observation with white noise of fixed density per unit solid angle.
   No interferometric sampling, calibration, or polarisation.

---

## 11. Reproducibility and governance

The campaign is gate-driven. Gates carry a mechanical status that is never
edited to match a later adjudication, so a defect that was real stays visible:

```
    gates passing:              121
    active blocking failures:   0
    preserved literal failures: 7
    future-phase not run:       11
```

A preserved literal failure is a FAIL that has been ruled on and kept on the
record rather than reinterpreted. There are 7:

| preserved failure | adjudicated disposition |
|---|---|
| `EDGE1_a000_i020_raymap_generation` | `RESOLVED_BY_S0_BACKEND` |
| `G10q_retired_flat_sigma_convention` | `RETIRED_PIXELIZATION_DEPENDENT` |
| `G1_v01_reproduction_relative` | `FAIL_AS_WRITTEN` |
| `G7_grid_convergence_a098_i075` | `RETIRED_NONCONVERGENT_EXTREME_STATISTIC` |
| `G7_grid_convergence_raw_max` | `RETIRED_NONCONVERGENT_EXTREME_STATISTIC` |
| `G7b_weighted_operator_discrepancy` | `WITHDRAWN_INVALID_CONVERGENCE_METRIC` |
| `GRID_AUTHORIZATION` | `SUPERSEDED_GRID_COMPLETE` |

Reproduction path: the registry digest is `2ba66f0209fe1cdec97b8cf5862494c22fb94704318f9601a7a1f9eb4b783796`; the operator grid freeze
pins the ray-map hashes, source class, probe, observer sampling, age grid, noise
convention, SNR grid, arms, rank conventions, thresholds, censoring rule and
permutation seeds before the first geometry was evaluated; the canonical freeze
lists the 265 artifacts the manuscript may cite; and the claim ledger maps
every number above to the artifact, row filter and column it came from.
`scripts/verify_manuscript.py` re-derives all of them from the frozen bytes and
checks that each rendered value appears in this text.

---

## Data and code availability

All code, ray maps, tables, gate records, freezes, amendments and the
invalidation ledger are in the campaign repository at tag `paper-I-campaign-final`,
commit `03b0d1c9c63131aa553904df0c09849d641dee8f`. Ray tracing uses two independent tracers, pinned by version
and commit, with an explicitly validated Schwarzschild backend at zero spin.
