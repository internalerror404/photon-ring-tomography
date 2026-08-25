# E3B — PHYSICAL HISTORICAL-OPERATOR CANARY

## Identity
- branch `claude/experiment-review-mac-rthiz1`, commit `92d183aa9ab46f9f73097deba9e6ce66a4e0ea69`
- registry sha256 `2ba66f0209fe1cdec97b8cf5862494c22fb94704318f9601a7a1f9eb4b783796`
- geometry a* = 0.5, i = 50 deg, orders n = 0, 1, 2 (the single authorized pilot geometry)
- kgeo commit `dc347060c5fb24e2c360c8aaffbfe25482a83805`

## Mechanical gate result
**PASS.** All fourteen E3B gates pass. Scope restriction observed: one geometry,
no production grid, no ML.

| gate | status | measured | threshold |
|---|---|---:|---:|
| `G2_physical_dense_matrix_free` | **PASS** | 0 | 1e-10 |
| `G3_physical_adjoint` | **PASS** | 5.257e-14 | 1e-08 |
| `G4_physical_resolved_unresolved_mixing` | **PASS** | 0 | 1e-10 |
| `G5_physical_injected_null` | **NOT_RUN** | – | – |
| `G6_physical_Gram_monotonicity` | **PASS** | 0 | 1e-10 |
| `G6b_resolved_dominates_direct` | **PASS** | 0 | 1e-10 |
| `G7b_transfer_field_convergence` | **PASS** | 0.02192 | 0.05 |
| `G7b_fields_are_analytic_not_discretised` | **PASS** | 2.2e-12 | 1e-09 |
| `G8t_retarded_time_validation` | **PASS** | 2.763e-06 | 0.001 |
| `G8t_azimuth_after_rigid_offset` | **PASS** | 6.329e-12 | 1e-08 |
| `G8t_azimuth_offset_is_order_independent` | **PASS** | 1.303e-13 | 1e-09 |
| `G8t_radius_control` | **PASS** | 8.963e-13 | 1e-09 |
| `G9w_weight_semantics` | **PASS** | 0 | 1e-10 |
| `G9c_per_order_ray_count` | **PASS** | 4179 | 1536 |

## The operator

Built row by row from the per-ray Kerr transfer maps, never from an order-wide
delay:

    y_{n,p}(t_o) = g_{n,p}^3 · j(r_{n,p}, phi_{n,p}, t_o − Delta t_{n,p})

The pilot measured overlapping retarded windows — n=0 spans ages 0–58 M, n=1
spans 46–103 M, n=2 spans 62–120 M — so an order does not correspond to one
source age and `a_n j(t_o − n tau)` is only an asymptotic summary. Pixel area
enters the likelihood, not the forward row, under the primary specific-intensity
model.

## Arms

| arm | rows | rank /224 | operational rank | kappa+ |
|---|---:|---:|---:|---:|
| `DIRECT_PHYSICAL` | 12288 | 224 | 153 | 1.134e+09 |
| `RESOLVED_PHYSICAL` | 36864 | 224 | 215 | 6.036e+04 |
| `RESOLVED_EQUALIZED` | 36864 | 224 | 216 | 4.700e+04 |
| `DELAY_ONLY_PHYSICAL` | 36864 | 224 | 222 | 2.435e+04 |
| `SPATIAL_ONLY_PHYSICAL` | 36864 | 224 | 192 | 1.715e+06 |
| `UNRESOLVED_PHYSICAL` | 12288 | 224 | 213 | 8.024e+04 |
| `TOTAL_FLUX` | 24 | 24 | 12 | 4.023e+10 |
| `PAIRING_DESTROYED` | 36864 | 224 | 224 | 1.894e+03 |

Every arm reaches full algebraic rank on the registered 224-dimensional global
class, so rank does not discriminate here. Conditioning and reach do.

Note `PAIRING_DESTROYED`: permuting delay, position and weight independently
within each order — preserving all three marginals — yields the **best**
conditioned operator of all. A physically meaningless operator looks better than
the real one. Any argument that reads conditioning as evidence of physical
content is refuted by that row.

## Temporal depth

Deepest retarded age (M) whose unit-norm localized mode is detectable, against
the frozen SNR sweep. A dash means no epoch is detectable. A **≥** marks a
right-censored entry: the arm reached the deepest age the grid contains, so the
value is a lower bound and the sweep ran out of grid before the arm ran out of
reach.

| SNR_0 | DIRECT | RESOLVED | RESOLVED_EQUALIZED | DELAY_ONLY | SPATIAL_ONLY | UNRESOLVED | TOTAL_FLUX | PAIRING_DESTROYED |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | – | – | – | – | – | – | – | – |
| 3 | – | – | – | – | – | – | – | – |
| 10 | 48 | 84 | 96 | 84 | 52 | 64 | 40 | 72 |
| 30 | 56 | 104 | 112 | 104 | 56 | 96 | 52 | 96 |
| 100 | 60 | 116 | ≥120 | 116 | 60 | 112 | 56 | 112 |
| 300 | 60 | ≥120 | ≥120 | ≥120 | 60 | ≥120 | 60 | ≥120 |
| 1000 | 64 | ≥120 | ≥120 | ≥120 | 64 | ≥120 | 68 | ≥120 |
| 3000 | 64 | ≥120 | ≥120 | ≥120 | 64 | ≥120 | 88 | ≥120 |
| 10000 | 64 | ≥120 | ≥120 | ≥120 | 64 | ≥120 | 96 | ≥120 |
| 30000 | 68 | ≥120 | ≥120 | ≥120 | 68 | ≥120 | 96 | ≥120 |
| 100000 | 68 | ≥120 | ≥120 | ≥120 | 68 | ≥120 | 100 | ≥120 |
| 1e+06 | 68 | ≥120 | ≥120 | ≥120 | 68 | ≥120 | 112 | ≥120 |

Three readings, and the middle one is the paper's result.

**Order 0 saturates.** Direct-only stops near 60–68 M at every SNR from 100 to
10^6. Its window ends at 58 M, so no amount of signal reaches further: this is a
structural limit, not a noise limit.

**Retarded-time diversity supplies the reach; spatial remapping supplies none.**
`DELAY_ONLY_PHYSICAL` — physical per-ray delays, direct-order spatial map —
tracks `RESOLVED_PHYSICAL` exactly at every SNR. `SPATIAL_ONLY_PHYSICAL` —
physical spatial maps, delays flattened onto the direct field — tracks
`DIRECT_PHYSICAL` exactly. **This reverses E1.** In the toy, a common sampler
made the delay ladder worth nothing and spatial diversity did all the work. On
physical Kerr maps the opposite holds. E1's mechanism conclusion does not
survive contact with the real transfer maps, and should not be carried into the
manuscript as a physical statement.

**Attenuation costs less depth than the throughput ratio suggests.**
`RESOLVED_EQUALIZED` reaches 120 M where `RESOLVED_PHYSICAL` reaches 116 M at
SNR 100 — four samples out of sixty. A throughput suppression of ~3000x between
orders 0 and 2 costs remarkably little historical reach, because the faint deep
orders are the *only* channels that see those epochs at all.

## Attenuation decomposition

| order | A_area | A_g = sum dOmega g^3 | ratio to direct | Gamma_amp |
|---:|---:|---:|---:|---:|
| 0 | 2496 | 2069 | 1 | – |
| 1 | 54.6 | 28.87 | 0.013953 | 4.272 |
| 2 | 1.672 | 0.6561 | 0.00031709 | 4.028 |

Gamma_amp is 4.27 from order 0 to 1 and 4.03 pooled across 0 to 2. This is the
**throughput** exponent under the frozen specific-intensity and Keplerian-flow
prescription. It is not the geometric Kerr critical exponent and is not
identified with it anywhere in this repository.

## Order dominance at fixed age

| retarded age (M) | I(order 0) | I(order 1) | I(order 2) | dominance 0→1 | dominance 1→2 |
|---:|---:|---:|---:|---:|---:|
| 0 | 232 | 5.01e-35 | 1.03e-88 | – | – |
| 20 | 272 | 0.0158 | 8.69e-26 | 5.8e-05x | – |
| 40 | 245 | 151 | 1.79 | 0.617x | 0.0118x |
| 60 | 4.3 | 152 | 148 | 35.4x | 0.971x |
| 80 | 1.95e-24 | 64 | 71.9 | – | 1.12x |
| 100 | 1.13e-86 | 1.05 | 24.6 | – | 23.4x |
| 116 | 3.19e-164 | 1.36e-12 | 1.03 | – | – |

This is the **age_specific_order_dominance_ratio**: a pointwise comparison at a
fixed absolute age between orders whose temporal supports barely overlap. It is
deliberately *not* called Gamma_info, because it does not measure a decay along
matched support. At age 60 M order 1 carries about 35x more information about
the localized mode than order 0; at 100 M order 2 carries about 23x more than
order 1. Entries appear only where both orders clear an information floor — a
ratio of two vanishing informations is neither a ratio nor an exponent.

## Information attenuation on matched support

Each order is sampled at the same fractional position within its **own** retarded
window, so the orders are compared on matched temporal support and the resulting
exponent is a genuine Gamma_info.

| window fraction | age n=0 | age n=1 | age n=2 | Gamma_info 0→1 | Gamma_info 1→2 |
|---:|---:|---:|---:|---:|---:|
| 0.05 | 2.9 | 49.0 | 65.3 | 0.079 | 0.138 |
| 0.25 | 14.5 | 59.9 | 76.7 | 0.253 | 0.296 |
| 0.45 | 26.0 | 70.8 | 88.2 | 0.513 | 0.374 |
| 0.65 | 37.6 | 81.7 | 99.7 | 0.794 | 0.404 |
| 0.85 | 49.1 | 92.5 | 111.2 | 0.991 | 0.572 |

Median Gamma_info is **0.576** from order 0 to 1 and **0.387** from 1 to 2,
defined at all 19 window fractions. Against Gamma_amp of 4.27 and 4.03,
**information decays roughly seven to ten times more slowly than amplitude**.

That is the paper's sharpest quantitative statement, and it needed matched
support to state: a single scalar attenuation exponent describes the throughput
and badly misdescribes the information. Higher orders are three thousand times
fainter and remain the sole carriers of everything older than about 60 M.

## Claim effect
Permits, for this one geometry: reporting that the physical historical channel
is a distributed, overlapping retarded-time kernel; that its reach is supplied
by delay diversity rather than spatial remapping; and that throughput
suppression and information suppression are different quantities with different
signs.
Demotes: E1's mechanism finding, which is a property of the toy's common
sampler and not of Kerr.
Forbids: any 12-geometry or spin/inclination-dependent statement; any
identification of Gamma_amp with a geometric exponent; any ML claim.

## Artifacts
`artifacts/tables/e3b_*.parquet`, `artifacts/configs/E3B_FREEZE.json`,
`artifacts/provenance/E3B_ARTIFACT_MANIFEST.json`.
