# E3C — MEASUREMENT AND NOISE MODEL

## Identity
- branch `research/paper1_r0_canary_reconstruction_v0`, commit `c59d0987ad7f70e5ef9dc91d51b9336a782fb52e`
- registry sha256 `2ba66f0209fe1cdec97b8cf5862494c22fb94704318f9601a7a1f9eb4b783796`
- freeze `artifacts/configs/E3C_OPERATOR_GRID_FREEZE.json` sha256 `7ab28bcd14674fb6544b577f19c00301f09e45ffec805cfcc29896c53634bf1b`
- 12 registered geometries, orders n = 0, 1, 2, profile `core`
- source class `C224` (224 dimensions), unmodified
- common age grid 0 to 252 M in steps of 4 M

## The declared model

    z_p = dOmega_p * g_p^3 * j(r_p, phi_p, t_p) + eta_p
    Var(eta_p) = sigma_Omega^2 * dOmega_p, i.e. white noise of density sigma_Omega per unit solid angle

whitened row:

    sqrt(dOmega_p) / sigma_Omega * g_p^3 * B(r_p, phi_p, t_p)

The pixel-average form y_p = g_p^3 j_p + eps_p with Var(eps_p) = sigma_Omega^2 / dOmega_p
produces the same whitened row, so the two statements of the model are the same
model.

**The square root is load-bearing.** Under a flat per-row sigma with `c = g^3`
the Fisher information scales with the *number of rows*: splitting one pixel
into k equal-area children carrying the same transfer value multiplies the Gram
by k. Adaptive ray counts differ by an order of magnitude across geometry and
order in this grid, so that convention would let the grid manufacture
information — and it would do so unevenly across the lensing bands, which differ
in solid angle by roughly three orders of magnitude.

| gate | status | measured | threshold |
|---|---|---:|---:|
| `G10q_continuum_noise_quadrature_invariance` | **PASS** | 5.401e-15 | 1e-10 |
| `G10q_retired_flat_sigma_convention` | **FAIL** | 7 | 1e-10 |

The retired convention is kept in the ledger as a literal FAIL with disposition
`RETIRED_PIXELIZATION_DEPENDENT` rather than deleted, so the convention change
is auditable. Defect `D-H_flat_sigma_measurement_convention` in
`artifacts/PREFIX_INVALIDATION_LEDGER.json` records exactly which E3B
conclusions moved and which did not.

## One sigma for the whole audit

one noise density for the whole audit, fixed from the direct arm's clean response to the declared reference source. No arm may choose its own sigma.

Derived arms are linear maps of the same resolved data with their covariance
propagated, never separate models:

    y_U = L y_R with C_U = L C_R L^T; y_F = S y_R with C_F = S C_R S^T; C_R = sigma_Omega^2 diag(dOmega)

Gate `E3C_G4b_linear_collapse_covariance_propagation` checks the channel
variance the operator actually applies against an independently formed
`L C_R L^T`. Without it the collapse identity alone would pass while a wrong
noise propagation made a summed arm look free.

## Weighted delay quantiles

The sampled maximum ray delay is an extreme-value statistic set by whichever
single ray sits closest to a band edge; it does not converge under refinement
and is not used as a historical depth anywhere in this program. The converging
summaries are weighted quantiles under three weightings:

| weighting | symbol | weight | source-independent |
|---|---|---|---|
| solid angle | Q_q^Omega | dOmega | yes |
| throughput | Q_q^I | dOmega g^3 | yes |
| Fisher | Q_q^F | dOmega g^6 | **no** — this is the squared whitened row weight and depends on the declared measurement model and source class |

The deepest 99.9% throughput-weighted boundary on the grid is
178.9 M at `a098_i075` order 2, against a
sampled maximum of 191.5 M for the same band. Only the
former sets the common age grid.

Full table: `artifacts/tables/e3c_weighted_delay_quantiles.parquet`.

## Source-domain integrity

Radial support convention: **GEOMETRY_DEPENDENT**.
r_inner = min over retained rays of source_r, r_outer = max, taken across the three orders of that geometry after subsampling.

If the primary radial knots move with spin, a source-domain change is confounded with a spacetime change. The primary class is preserved as registered and the confound is measured, not assumed away, by the common-support control below.

Control on the three anchor geometries, one fixed interval in r/M with identical
knot locations:

| geometry | arm | support | r range | oprank | kappa+ | J_old | oldest probe |
|---|---|---|---|---:|---:|---:|---:|
| `a000_i020` | DIRECT_PHYSICAL | primary geometry dependent | 2.000–49.94 | 133 | 3.38e+10 | 15.02 | 20 |
| `a000_i020` | DIRECT_PHYSICAL | common radial support | 2.000–49.94 | 133 | 3.38e+10 | 15.02 | 20 |
| `a000_i020` | RESOLVED_PHYSICAL | primary geometry dependent | 2.000–49.94 | 203 | 7.04e+05 | 67.86 | 60 |
| `a000_i020` | RESOLVED_PHYSICAL | common radial support | 2.000–49.94 | 203 | 7.04e+05 | 67.86 | 60 |
| `a000_i020` | DELAY_ONLY | primary geometry dependent | 2.000–49.94 | 215 | 8.82e+04 | 67.86 | 60 |
| `a000_i020` | DELAY_ONLY | common radial support | 2.000–49.94 | 215 | 8.82e+04 | 67.86 | 60 |
| `a000_i020` | SPATIAL_ONLY | primary geometry dependent | 2.000–49.94 | 140 | 8.77e+09 | 15.06 | 20 |
| `a000_i020` | SPATIAL_ONLY | common radial support | 2.000–49.94 | 140 | 8.77e+09 | 15.06 | 20 |
| `a050_i050` | DIRECT_PHYSICAL | primary geometry dependent | 1.866–49.98 | 153 | 1.13e+09 | 8.78 | 60 |
| `a050_i050` | DIRECT_PHYSICAL | common radial support | 2.000–49.94 | 157 | 6.11e+08 | 8.75 | 60 |
| `a050_i050` | RESOLVED_PHYSICAL | primary geometry dependent | 1.866–49.98 | 201 | 7.04e+05 | 41.21 | 84 |
| `a050_i050` | RESOLVED_PHYSICAL | common radial support | 2.000–49.94 | 202 | 3.83e+05 | 40.11 | 84 |
| `a050_i050` | DELAY_ONLY | primary geometry dependent | 1.866–49.98 | 214 | 7.83e+04 | 41.21 | 84 |
| `a050_i050` | DELAY_ONLY | common radial support | 2.000–49.94 | 216 | 5.33e+04 | 40.11 | 84 |
| `a050_i050` | SPATIAL_ONLY | primary geometry dependent | 1.866–49.98 | 177 | 1.20e+07 | 8.83 | 60 |
| `a050_i050` | SPATIAL_ONLY | common radial support | 2.000–49.94 | 182 | 7.60e+06 | 8.78 | 60 |
| `a098_i075` | DIRECT_PHYSICAL | primary geometry dependent | 1.200–49.98 | 156 | 7.23e+07 | 5.24 | 140 |
| `a098_i075` | DIRECT_PHYSICAL | common radial support | 2.000–49.94 | 156 | 5.07e+07 | 4.88 | 140 |
| `a098_i075` | RESOLVED_PHYSICAL | primary geometry dependent | 1.200–49.98 | 193 | 7.53e+06 | 16.22 | 144 |
| `a098_i075` | RESOLVED_PHYSICAL | common radial support | 2.000–49.94 | 188 | 8.34e+06 | 13.34 | 144 |
| `a098_i075` | DELAY_ONLY | primary geometry dependent | 1.200–49.98 | 193 | 8.51e+06 | 16.22 | 144 |
| `a098_i075` | DELAY_ONLY | common radial support | 2.000–49.94 | 193 | 4.59e+06 | 13.34 | 144 |
| `a098_i075` | SPATIAL_ONLY | primary geometry dependent | 1.200–49.98 | 207 | 6.49e+04 | 5.39 | 140 |
| `a098_i075` | SPATIAL_ONLY | common radial support | 2.000–49.94 | 205 | 8.93e+04 | 5.02 | 140 |

**The confound is real but small, and it does not reach the historical
conclusions.** Operational rank moves under the common support in
12 of 24 anchor–arm combinations, by at most
5 of 224 (median move 2.5).
The oldest detectable age probe is unchanged in 23 of 24 combinations, and
`J_old` moves by at most 18.7% (median
2.3%). The largest shifts are at `a098_i075`, whose
primary radial support reaches to r/M = 1.20 against the common interval's 2.00
— the anchor whose source domain the control changes most.

Read strictly: the spin trends in operational rank are partly confounded with
the source domain, because a higher-spin geometry's rays reach closer to the
horizon and the primary knots follow them. The depth and innovation results are
not: they survive the domain change at every anchor and arm.

Near-horizon ray coverage does not imply the emissivity model physically emits to the horizon. Ray-map support and assumed source emission are separate objects.
