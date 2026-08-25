# E3C — GEOMETRY-WIDE PHYSICAL-OPERATOR AUDIT

## Identity
- branch `claude/experiment-review-mac-rthiz1`, commit `d6869f8d1c08889fee34e91d392c2bbc1bc9a62f`
- registry sha256 `2ba66f0209fe1cdec97b8cf5862494c22fb94704318f9601a7a1f9eb4b783796`
- freeze `artifacts/configs/E3C_OPERATOR_GRID_FREEZE.json` sha256 `818199a7ac4f3f90cf592f568d2a550dfd575aba1d539b0966a3a5c6521473d2`
- 12 registered geometries, orders n = 0, 1, 2, profile `core`
- source class `C224` (224 dimensions), unmodified
- common age grid 0 to 252 M in steps of 4 M

## Mechanical gate result
**PASS.** Every E3C correctness gate passes on every geometry.
Each mechanical gate below is the worst case over all 12 geometries;
the per-geometry values are in `artifacts/tables/e3c_gate_detail.parquet`.

| gate | status | measured | threshold |
|---|---|---:|---:|
| `E3C_G2_physical_dense_matrix_free` | **PASS** | 0 | 1e-10 |
| `E3C_G3_physical_adjoint` | **PASS** | 2.674e-13 | 1e-08 |
| `E3C_G4_physical_resolved_unresolved_mixing` | **PASS** | 0 | 1e-10 |
| `E3C_G4b_linear_collapse_covariance_propagation` | **PASS** | 0 | 1e-12 |
| `E3C_G6_physical_Gram_monotonicity` | **PASS** | 1.861e-16 | 1e-10 |
| `E3C_G6b_resolved_dominates_direct` | **PASS** | 1.574e-16 | 1e-10 |
| `E3C_G9w_weight_semantics` | **PASS** | 4.378e-16 | 1e-10 |
| `E3C_freeze_raymap_hashes` | **PASS** | 0 | 0 |
| `E3C_frozen_grid_invariance` | **PASS** | dims=[224] n_ages=[64] | dims=[224] n_ages=[64] |
| `G10q_continuum_noise_quadrature_invariance` | **PASS** | 5.401e-15 | 1e-10 |

## What was frozen before the first geometry was evaluated

`E3C_OPERATOR_GRID_FREEZE.json` pins the ray-map hashes, the source class and
its support rule, the localized probe, the observer sampling, the common age
grid, the noise convention, the SNR grid, all eight arms, the rank conventions,
the operational threshold, the censoring rule and the sixteen permutation seeds.
Gate `E3C_freeze_raymap_hashes` re-checks every map against the pinned digest at
assembly time, and `E3C_frozen_grid_invariance` checks that the class dimension
and age grid were the same at every geometry.

The common age ceiling is not chosen from a favorable geometry:

    A_max = T_obs + 1.25 max_(g,n) {Q_0.999^Omega, Q_0.999^I} + 2h
          = 249.6 M
          -> 252 M after rounding up to the age step

with the maximum, 178.9 M, taken
over the whole grid from source-independent map summaries. It sits above the
deepest ray any geometry carries, so 0 of 1152 depth entries are
right-censored: the reported depths are measurements, not grid ceilings.

## Arms across the grid, at the reference SNR_0 = 100

| arm | oprank median | oprank min–max | kappa+ median | J_old median | T_rec median |
|---|---:|---|---:|---:|---:|
| `DIRECT_PHYSICAL` | 153 | 133–159 | 9.00e+08 | 8.29 | 60 |
| `RESOLVED_PHYSICAL` | 202 | 184–205 | 7.84e+05 | 40.72 | 84 |
| `UNRESOLVED_IMAGE` | 178 | 173–183 | 9.52e+06 | 9.66 | 60 |
| `TOTAL_FLUX` | 13 | 12–14 | 9.86e+08 | 6.90 | 56 |
| `DELAY_ONLY` | 212 | 193–216 | 9.50e+04 | 40.72 | 84 |
| `SPATIAL_ONLY` | 178 | 140–209 | 9.76e+06 | 8.33 | 60 |
| `EQUALIZED_ORDER_SENSITIVITY` | 216 | 196–222 | 5.04e+04 | 306.70 | 120 |
| `PAIRING_DESTROYED` | 221 | 217–224 | 1.80e+04 | 28.72 | 72 |

The full cell-by-cell surface is in `artifacts/tables/e3c_geometry_metrics.parquet`.

## H1 — historical extension

At the reference SNR, `T_resolved > T_direct` in **12 of 12**
geometries, and `J_old_resolved > 0` in **12 of 12**. Across the
whole SNR sweep the depth inequality is strict somewhere in
**12 of 12** geometries.

| a\* \ i | 20 deg | 50 deg | 75 deg | monotone in inclination |
|---|---:|---:|---:|---|
| 0.00 | 60 | 84 | 144 | nondecreasing |
| 0.50 | 60 | 84 | 144 | nondecreasing |
| 0.90 | 60 | 84 | 144 | nondecreasing |
| 0.98 | 60 | 84 | 144 | nondecreasing |
| **monotone in spin** | constant | constant | constant | |

against the direct channel:

| a\* \ i | 20 deg | 50 deg | 75 deg | monotone in inclination |
|---|---:|---:|---:|---|
| 0.00 | 20 | 60 | 140 | nondecreasing |
| 0.50 | 20 | 60 | 140 | nondecreasing |
| 0.90 | 20 | 60 | 140 | nondecreasing |
| 0.98 | 20 | 60 | 140 | nondecreasing |
| **monotone in spin** | constant | constant | constant | |

and the threshold-independent innovation:

| a\* \ i | 20 deg | 50 deg | 75 deg | monotone in inclination |
|---|---:|---:|---:|---|
| 0.00 | 67.86 | 40.93 | 12.36 | nonincreasing |
| 0.50 | 69.94 | 41.21 | 15.88 | nonincreasing |
| 0.90 | 70.81 | 40.44 | 16.07 | nonincreasing |
| 0.98 | 71.53 | 40.51 | 16.22 | nonincreasing |
| **monotone in spin** | nondecreasing | nonmonotone | nondecreasing | |

| a\* \ i | 20 deg | 50 deg | 75 deg | monotone in inclination |
|---|---:|---:|---:|---|
| 0.00 | 15.02 | 8.34 | 5.07 | nonincreasing |
| 0.50 | 15.28 | 8.78 | 4.92 | nonincreasing |
| 0.90 | 15.37 | 8.24 | 5.09 | nonincreasing |
| 0.98 | 15.40 | 7.99 | 5.24 | nonincreasing |
| **monotone in spin** | nondecreasing | nonmonotone | nonmonotone | |

`J_old` integrates `log(1 + I(a))` over ages beyond the direct channel's own
99.9% throughput-weighted boundary, so it does not depend on where a detection
contour happens to fall. It is reported because a depth endpoint alone would be
a statement about the threshold as much as about the physics.

## H2 and H3 — which mechanism supplies the reach

| geometry | D_delay (registered) | D_delay (localized class) | D_spatial (localized class) | D_direct (reference) | kappa+ full | kappa+ delay-only | kappa+ spatial-only |
|---|---:|---:|---:|---:|---:|---:|---:|
| `a000_i020` | 0.000e+00 | 0.1691 | 0.3108 | 0.3147 | 7.04e+05 | 8.82e+04 | 8.77e+09 |
| `a000_i050` | 0.000e+00 | 0.1512 | 0.2060 | 0.2307 | 7.03e+05 | 8.79e+04 | 1.75e+07 |
| `a000_i075` | 0.000e+00 | 0.1651 | 0.3036 | 0.2294 | 2.88e+07 | 1.55e+07 | 1.11e+05 |
| `a050_i020` | 0.000e+00 | 0.1469 | 0.3229 | 0.3276 | 7.12e+05 | 7.33e+04 | 6.64e+09 |
| `a050_i050` | 0.000e+00 | 0.1685 | 0.2041 | 0.2475 | 7.04e+05 | 7.83e+04 | 1.20e+07 |
| `a050_i075` | 0.000e+00 | 0.2747 | 0.3418 | 0.2663 | 1.73e+07 | 6.38e+06 | 1.55e+05 |
| `a090_i020` | 0.000e+00 | 0.1749 | 0.3344 | 0.3400 | 8.56e+05 | 9.83e+04 | 5.47e+09 |
| `a090_i050` | 0.000e+00 | 0.1613 | 0.2183 | 0.2688 | 6.98e+05 | 7.71e+04 | 7.37e+06 |
| `a090_i075` | 0.000e+00 | 0.2147 | 0.3099 | 0.3074 | 1.36e+07 | 7.48e+06 | 1.01e+05 |
| `a098_i020` | 0.000e+00 | 0.1653 | 0.3386 | 0.3457 | 1.19e+06 | 1.22e+05 | 4.84e+09 |
| `a098_i050` | 0.000e+00 | 0.1187 | 0.2416 | 0.2984 | 2.00e+05 | 9.16e+04 | 7.57e+06 |
| `a098_i075` | 0.000e+00 | 0.1288 | 0.3734 | 0.3379 | 7.53e+06 | 8.51e+06 | 6.49e+04 |

`D` is the relative L2 discrepancy between `log(1 + I)` curves over the common
age grid — on the log scale so a single loud epoch cannot dominate the norm.

**The registered H2 statistic is degenerate and is reported as an identity.**
The registered localized probe is spatially flat, and the delay-only
substitution changes only `source_r` and `source_phi`. The scalar curve `I(a)`
therefore cannot see that substitution: `D_delay` is
identically zero at every geometry,
by algebra rather than by physics. Gate
`E3C_H2_registered_statistic_is_an_identity` asserts bitwise equality so that
the zero can never be read as support for the delay mechanism. The literal
values stay on the record; Amendment 002 adds the comparison that can actually
discriminate.

**On the registered localized class the two mechanisms separate, but modestly.**
Median `D_delay` is 0.165 against `D_spatial` 0.310, with
the direct arm at 0.303 as the scale for what "far" means. The
delay-only arm is closer to the full operator than the spatial-only arm in
**12 of 12** cells.
The ordering holds everywhere on the grid.

**Normalising by the direct arm makes the decomposition legible.** The direct
arm is the natural zero point: it is what remains when the higher orders are
removed altogether. Measuring each substitution's discrepancy against it:

| geometry | D_delay / D_direct | D_spatial / D_direct |
|---|---:|---:|
| `a000_i020` | 0.537 | 0.988 |
| `a000_i050` | 0.655 | 0.893 |
| `a000_i075` | 0.720 | 1.324 |
| `a050_i020` | 0.448 | 0.986 |
| `a050_i050` | 0.681 | 0.825 |
| `a050_i075` | 1.032 | 1.283 |
| `a090_i020` | 0.514 | 0.983 |
| `a090_i050` | 0.600 | 0.812 |
| `a090_i075` | 0.699 | 1.008 |
| `a098_i020` | 0.478 | 0.979 |
| `a098_i050` | 0.398 | 0.810 |
| `a098_i075` | 0.381 | 1.105 |
| **median** | 0.569 | 0.985 |
| **min–max** | 0.381–1.032 | 0.810–1.324 |

A ratio near 1 means the substitution destroyed essentially everything the
higher orders contributed; a ratio near 0 means it preserved it. Spatial-only
sits at a median 0.98 — flattening the delays leaves the
resolved stack about as far from the truth as not having the higher orders at
all — while delay-only sits at 0.57, recovering roughly half
the gap. Delay-only is closer than the direct arm in
11 of 12 cells, spatial-only in
8 of 12.

This is weaker than the canary reported. Under the scalar probe the delay-only
arm looked like an exact reproduction of the full operator; on the localized
class it is a 17% relative departure, so delay diversity carries
the larger share of the historical reach but not all of it. Spatial remapping is
not the mechanism, but it is not nothing either.

Conditioning is reported alongside the discrepancy because spatial remapping can
improve `kappa+` without moving the oldest detected probe centre, and inferring
the mechanism from a depth endpoint alone would miss that.

| a\* \ i | 20 deg | 50 deg | 75 deg | monotone in inclination |
|---|---:|---:|---:|---|
| 0.00 | 0.1691 | 0.1512 | 0.1651 | nonmonotone |
| 0.50 | 0.1469 | 0.1685 | 0.2747 | nondecreasing |
| 0.90 | 0.1749 | 0.1613 | 0.2147 | nonmonotone |
| 0.98 | 0.1653 | 0.1187 | 0.1288 | nonmonotone |
| **monotone in spin** | nonmonotone | nonmonotone | nonmonotone | |

| a\* \ i | 20 deg | 50 deg | 75 deg | monotone in inclination |
|---|---:|---:|---:|---|
| 0.00 | 0.3108 | 0.2060 | 0.3036 | nonmonotone |
| 0.50 | 0.3229 | 0.2041 | 0.3418 | nonmonotone |
| 0.90 | 0.3344 | 0.2183 | 0.3099 | nonmonotone |
| 0.98 | 0.3386 | 0.2416 | 0.3734 | nonmonotone |
| **monotone in spin** | nondecreasing | nonmonotone | nonmonotone | |

## H4 — how much the order labels are worth

| geometry | T_unresolved / T_resolved | J_old ratio |
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

`UNRESOLVED_IMAGE` sums the orders into one image plane and pays the summed
noise, `C_U = L C_R L^T`. A ratio near 1 means explicit order labels are nearly
dispensable for that quantity; a ratio well below 1 means they are load-bearing.

## H5 — throughput versus sensitivity attenuation

All 19 aligned-window fractions are retained at every geometry.

| geometry | pair | n def / 19 | median | IQR | min | max | Gamma_amp | difference | window overlap |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `a000_i020` | 0->1 | 19 | 2.614 | 0.397 | 0.120 | 2.645 | 4.714 | 2.100 | 0.000 |
| `a000_i020` | 1->2 | 19 | 1.831 | 0.124 | 1.370 | 1.923 | 3.602 | 1.771 | 0.534 |
| `a000_i050` | 0->1 | 19 | 2.441 | 0.583 | 1.967 | 3.109 | 4.274 | 1.833 | 0.115 |
| `a000_i050` | 1->2 | 19 | 2.187 | 0.263 | 1.941 | 2.385 | 3.887 | 1.700 | 0.493 |
| `a000_i075` | 0->1 | 19 | 1.979 | 0.909 | 1.059 | 3.405 | 3.248 | 1.269 | 0.308 |
| `a000_i075` | 1->2 | 19 | 2.059 | 0.131 | 0.950 | 2.124 | 4.057 | 1.998 | 0.578 |
| `a050_i020` | 0->1 | 19 | 2.723 | 0.126 | 2.521 | 2.791 | 4.681 | 1.958 | 0.000 |
| `a050_i020` | 1->2 | 19 | 1.794 | 0.018 | 1.570 | 1.830 | 3.501 | 1.706 | 0.545 |
| `a050_i050` | 0->1 | 19 | 2.486 | 0.561 | 1.980 | 3.422 | 4.272 | 1.786 | 0.114 |
| `a050_i050` | 1->2 | 19 | 2.120 | 0.157 | 1.887 | 2.330 | 3.784 | 1.664 | 0.521 |
| `a050_i075` | 0->1 | 19 | 1.530 | 0.815 | 0.957 | 3.519 | 2.870 | 1.340 | 0.309 |
| `a050_i075` | 1->2 | 19 | 2.569 | 0.343 | 1.703 | 2.687 | 4.388 | 1.819 | 0.519 |
| `a090_i020` | 0->1 | 19 | 2.609 | 0.259 | 0.850 | 2.695 | 4.620 | 2.010 | 0.000 |
| `a090_i020` | 1->2 | 19 | 1.704 | 0.112 | 1.629 | 1.930 | 3.203 | 1.499 | 0.545 |
| `a090_i050` | 0->1 | 19 | 2.492 | 0.568 | 1.996 | 3.427 | 4.249 | 1.758 | 0.117 |
| `a090_i050` | 1->2 | 19 | 1.950 | 0.211 | 1.614 | 2.078 | 3.548 | 1.599 | 0.557 |
| `a090_i075` | 0->1 | 19 | 1.560 | 0.884 | 0.976 | 3.067 | 2.875 | 1.315 | 0.309 |
| `a090_i075` | 1->2 | 19 | 2.310 | 0.403 | 1.794 | 2.560 | 4.251 | 1.941 | 0.571 |
| `a098_i020` | 0->1 | 10 | 1.909 | 3.409 | -8.566 | 2.568 | 4.592 | 2.683 | 0.435 |
| `a098_i020` | 1->2 | 19 | 1.682 | 0.042 | 1.574 | 1.922 | 3.075 | 1.394 | 0.536 |
| `a098_i050` | 0->1 | 19 | 2.679 | 1.197 | 1.997 | 7.629 | 4.230 | 1.551 | 0.139 |
| `a098_i050` | 1->2 | 19 | 1.684 | 0.627 | -3.474 | 1.869 | 3.356 | 1.672 | 0.724 |
| `a098_i075` | 0->1 | 19 | 1.611 | 1.013 | 0.966 | 3.513 | 2.872 | 1.262 | 0.304 |
| `a098_i075` | 1->2 | 19 | 2.230 | 0.261 | 1.472 | 2.520 | 4.120 | 1.889 | 0.559 |

**5 of 24 cells are set aside as not interpretable, and
they are named rather than averaged away.**

| geometry | pair | defined / 19 | negative | windows disjoint | why it is set aside |
|---|---|---:|---:|---|---|
| `a000_i020` | 0->1 | 19 | 0 | yes | the two orders' retarded windows do not overlap at all, so matched *fractional position* is not matched support |
| `a050_i020` | 0->1 | 19 | 0 | yes | the two orders' retarded windows do not overlap at all, so matched *fractional position* is not matched support |
| `a090_i020` | 0->1 | 19 | 0 | yes | the two orders' retarded windows do not overlap at all, so matched *fractional position* is not matched support |
| `a098_i020` | 0->1 | 10 | 3 | no | 9 fractions carry no information in one of the orders; 3 fractions give a negative exponent, i.e. the higher order is locally more sensitive |
| `a098_i050` | 1->2 | 19 | 2 | no | 2 fractions give a negative exponent, i.e. the higher order is locally more sensitive |

The zero-overlap cells are the important caveat. At i = 20 deg the n = 0 and
n = 1 retarded windows are disjoint, so sampling both at the same *fractional*
position inside their own windows compares two epochs that share no support at
all. The statistic is still computed and reported, but "matched support" is not
what it means there, and those cells do not bear on H5.

On the 19 interpretable cells:
the sensitivity exponent is below the throughput exponent in every one, so a single scalar attenuation exponent describes the flux and misdescribes the information.
Median difference 1.700,
range 1.262 to
1.998.

No asymptotic law is fitted: n = 0, 1, 2 does not determine one.

## H6 — the spin and inclination surface

These are twelve deterministic registered geometries, not a sample from a
population. No p-value, confidence interval or significance claim appears
anywhere in this report; the surface is reported cell by cell with its median,
extremes and monotonicity.

| a\* \ i | 20 deg | 50 deg | 75 deg | monotone in inclination |
|---|---:|---:|---:|---|
| 0.00 | 203 | 201 | 185 | nonincreasing |
| 0.50 | 203 | 201 | 184 | nonincreasing |
| 0.90 | 203 | 203 | 189 | nonincreasing |
| 0.98 | 203 | 205 | 193 | nonmonotone |
| **monotone in spin** | constant | nondecreasing | nonmonotone | |

| a\* \ i | 20 deg | 50 deg | 75 deg | monotone in inclination |
|---|---:|---:|---:|---|
| 0.00 | 133 | 153 | 159 | nondecreasing |
| 0.50 | 134 | 153 | 157 | nondecreasing |
| 0.90 | 135 | 154 | 157 | nondecreasing |
| 0.98 | 133 | 153 | 156 | nondecreasing |
| **monotone in spin** | nonmonotone | nonmonotone | nonincreasing | |

| a\* \ i | 20 deg | 50 deg | 75 deg | monotone in inclination |
|---|---:|---:|---:|---|
| 0.00 | 7.04e+05 | 7.03e+05 | 2.88e+07 | nonmonotone |
| 0.50 | 7.12e+05 | 7.04e+05 | 1.73e+07 | nonmonotone |
| 0.90 | 8.56e+05 | 6.98e+05 | 1.36e+07 | nonmonotone |
| 0.98 | 1.19e+06 | 2.00e+05 | 7.53e+06 | nonmonotone |
| **monotone in spin** | nondecreasing | nonmonotone | nonincreasing | |

| a\* \ i | 20 deg | 50 deg | 75 deg | monotone in inclination |
|---|---:|---:|---:|---|
| 0.00 | 224 | 224 | 195 | nonincreasing |
| 0.50 | 224 | 224 | 196 | nonincreasing |
| 0.90 | 224 | 224 | 196 | nonincreasing |
| 0.98 | 224 | 224 | 197 | nonincreasing |
| **monotone in spin** | constant | constant | nondecreasing | |

`delta_G_indirect = G_resolved - G_direct` separates information reweighted
inside the direct channel's support from genuinely new historical information
beyond it. Its rank, trace, stable rank and smallest positive eigenvalue are in
`artifacts/tables/e3c_historical_innovation.parquet`.

## Negative control: PAIRING_DESTROYED over 16 frozen seeds

| geometry | oprank min / med / max | kappa+ min / med / max | resolved kappa+ |
|---|---|---|---:|
| `a000_i020` | 216 / 218.0 / 220 | 1.81e+04 / 2.48e+04 / 3.45e+04 | 7.04e+05 |
| `a000_i050` | 218 / 220.0 / 222 | 1.29e+04 / 1.86e+04 / 2.78e+04 | 7.03e+05 |
| `a000_i075` | 220 / 221.0 / 222 | 1.93e+04 / 2.20e+04 / 3.69e+04 | 2.88e+07 |
| `a050_i020` | 217 / 219.0 / 220 | 1.71e+04 / 2.12e+04 / 3.19e+04 | 7.12e+05 |
| `a050_i050` | 219 / 220.5 / 222 | 1.17e+04 / 1.78e+04 / 2.70e+04 | 7.04e+05 |
| `a050_i075` | 222 / 223.0 / 223 | 1.25e+04 / 1.48e+04 / 2.16e+04 | 1.73e+07 |
| `a090_i020` | 216 / 218.0 / 219 | 2.28e+04 / 3.07e+04 / 3.80e+04 | 8.56e+05 |
| `a090_i050` | 219 / 221.0 / 222 | 1.14e+04 / 1.62e+04 / 2.38e+04 | 6.98e+05 |
| `a090_i075` | 221 / 223.0 / 224 | 1.22e+04 / 1.72e+04 / 2.63e+04 | 1.36e+07 |
| `a098_i020` | 215 / 216.5 / 218 | 2.71e+04 / 3.88e+04 / 5.81e+04 | 1.19e+06 |
| `a098_i050` | 220 / 220.5 / 222 | 1.40e+04 / 1.81e+04 / 2.57e+04 | 2.00e+05 |
| `a098_i075` | 220 / 223.0 / 224 | 1.21e+04 / 1.54e+04 / 2.63e+04 | 7.53e+06 |

Permuting delay, position and weight independently within each order preserves
all three marginals and destroys their pairing. This is a nonphysical control
and is never ranked as an alternative measurement architecture. It is reported
over the full frozen seed set because the canary's unusually good conditioning
could otherwise have been one favorable permutation:
at every geometry the *worst* of the sixteen seeds is still better conditioned than the physical resolved operator, so the effect is systematic and not a lucky draw.

Any argument that reads conditioning as evidence of physical content is refuted
by these rows.

## Scope

Permits: geometry-wide statements about the registered class `C224` on the
twelve registered geometries under the frozen measurement convention.
Forbids: continuum injectivity claims from full rank on `C224`; any geometry
mismatch, order-leakage or ML claim; any raw maximum delay used as a historical
depth; population-style inference across the twelve cells.

## Artifacts
`artifacts/configs/E3C_OPERATOR_GRID_FREEZE.json`,
`artifacts/tables/e3c_*.parquet`,
`artifacts/gates/e3c_correctness_gates.json`,
`artifacts/provenance/E3C_ARTIFACT_MANIFEST.json`.
