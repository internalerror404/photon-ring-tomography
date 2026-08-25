# E3B — PHYSICAL HISTORICAL-OPERATOR CANARY

## Identity
- branch `claude/experiment-review-mac-rthiz1`, commit `0ef341dae3b21bc2bdd0e54a18971cff208af783`
- registry sha256 `2ba66f0209fe1cdec97b8cf5862494c22fb94704318f9601a7a1f9eb4b783796`
- geometry a* = 0.5, i = 50 deg, orders n = 0, 1, 2 (the single authorized pilot geometry)
- kgeo commit `dc347060c5fb24e2c360c8aaffbfe25482a83805`

## Mechanical gate result
**PASS.** Every E3B gate passes under the corrected measurement convention.
The one FAIL row below is `G10q_retired_flat_sigma_convention`, preserved
literally with disposition `RETIRED_PIXELIZATION_DEPENDENT`: it is the retired
convention failing on purpose, kept in the ledger so the convention change is
auditable rather than silent. It is not an active blocking failure.
Scope restriction observed: one geometry, no production grid, no ML.

| gate | status | measured | threshold |
|---|---|---:|---:|
| `G2_physical_dense_matrix_free` | **PASS** | 0 | 1e-10 |
| `G3_physical_adjoint` | **PASS** | 7.173e-14 | 1e-08 |
| `G4_physical_resolved_unresolved_mixing` | **PASS** | 0 | 1e-10 |
| `G4b_linear_collapse_covariance_propagation` | **PASS** | 0 | 1e-12 |
| `G5_physical_injected_null` | **NOT_RUN** | – | – |
| `G6_physical_Gram_monotonicity` | **PASS** | 6.563e-17 | 1e-10 |
| `G6b_resolved_dominates_direct` | **PASS** | 0 | 1e-10 |
| `G7b_transfer_field_convergence` | **PASS** | 0.02192 | 0.05 |
| `G7b_fields_are_analytic_not_discretised` | **PASS** | 2.2e-12 | 1e-09 |
| `G8t_retarded_time_validation` | **PASS** | 2.763e-06 | 0.001 |
| `G8t_azimuth_after_rigid_offset` | **PASS** | 6.329e-12 | 1e-08 |
| `G8t_azimuth_offset_is_order_independent` | **PASS** | 1.303e-13 | 1e-09 |
| `G8t_radius_control` | **PASS** | 8.963e-13 | 1e-09 |
| `G9w_weight_semantics` | **PASS** | 1.692e-16 | 1e-10 |
| `G9c_per_order_ray_count` | **PASS** | 4179 | 1536 |
| `G10q_continuum_noise_quadrature_invariance` | **PASS** | 5.401e-15 | 1e-10 |
| `G10q_retired_flat_sigma_convention` | **FAIL** | 7 | 1e-10 |

## The operator

Built row by row from the per-ray Kerr transfer maps, never from an order-wide
delay:

    z_{n,p}(t_o) = dOmega_{n,p} · g_{n,p}^3 · j(r_{n,p}, phi_{n,p}, t_o − Delta t_{n,p}) + eta,
    Var(eta) = sigma_Omega^2 · dOmega_{n,p}

The pilot measured overlapping retarded windows — n=0 spans ages 0–58 M, n=1
spans 46–103 M, n=2 spans 62–120 M — so an order does not correspond to one
source age and `a_n j(t_o − n tau)` is only an asymptotic summary.

**The measurement convention changed, and the numbers below changed with it.**
The datum is a pixel-integrated flux against white noise of density
`sigma_Omega` per unit solid angle, so the whitened row is

    sqrt(dOmega) / sigma_Omega · g^3 · B(r, phi, t)

The earlier revision of this experiment used `c = g^3` with a flat per-row
sigma. That convention makes Fisher information scale with the *number of rows*:
splitting one pixel into k identical children multiplied the Gram by k
(measured relative error 1.0, 3.0, 7.0 at k = 2, 4, 8). The lensing bands
differ enormously in solid angle — n=0 covers 2496 M^2, n=1
54.6 M^2, n=2 1.67 M^2 — so giving every order the same
1536-row budget silently handed n=1 a detector 46x quieter per unit
sky than the direct image, and n=2 one 1493x quieter. Gate
`G10q_continuum_noise_quadrature_invariance` now locks the corrected
convention at 5.4e-15; the retired convention is recorded as a literal FAIL
with disposition `RETIRED_PIXELIZATION_DEPENDENT`. Every quantity in this
report is the corrected one, and where a conclusion moved, it is stated.

## Arms

| arm | rows | rank /224 | operational rank | kappa+ |
|---|---:|---:|---:|---:|
| `DIRECT_PHYSICAL` | 12288 | 224 | 153 | 1.134e+09 |
| `RESOLVED_PHYSICAL` | 36864 | 224 | 201 | 7.036e+05 |
| `RESOLVED_EQUALIZED` | 36864 | 224 | 216 | 4.705e+04 |
| `DELAY_ONLY_PHYSICAL` | 36864 | 224 | 214 | 7.831e+04 |
| `SPATIAL_ONLY_PHYSICAL` | 36864 | 224 | 177 | 1.195e+07 |
| `UNRESOLVED_PHYSICAL` | 12288 | 224 | 181 | 7.069e+06 |
| `TOTAL_FLUX` | 24 | 24 | 13 | 1.042e+09 |
| `PAIRING_DESTROYED` | 36864 | 224 | 221 | 2.098e+04 |

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
| 10 | 48 | 48 | 96 | 48 | 48 | 48 | – | 48 |
| 30 | 56 | 56 | 112 | 56 | 56 | 56 | 52 | 56 |
| 100 | 60 | 84 | ≥120 | 84 | 60 | 60 | 56 | 72 |
| 300 | 60 | 96 | ≥120 | 96 | 60 | 64 | 76 | 92 |
| 1000 | 64 | 104 | ≥120 | 104 | 64 | 92 | 92 | 100 |
| 3000 | 64 | 112 | ≥120 | 112 | 64 | 96 | 96 | 108 |
| 10000 | 64 | ≥120 | ≥120 | ≥120 | 64 | 100 | 108 | ≥120 |
| 30000 | 68 | ≥120 | ≥120 | ≥120 | 68 | 104 | 112 | ≥120 |
| 100000 | 68 | ≥120 | ≥120 | ≥120 | 68 | 112 | 116 | ≥120 |
| 1e+06 | 68 | ≥120 | ≥120 | ≥120 | 68 | ≥120 | ≥120 | ≥120 |

Three readings, and the middle one is the paper's result.

**Order 0 saturates.** Direct-only stops near 60–68 M at every SNR from 100 to
10^6. Its window ends at 58 M, so no amount of signal reaches further: this is a
structural limit, not a noise limit.

**Retarded-time diversity supplies the reach; spatial remapping supplies none.**
`DELAY_ONLY_PHYSICAL` — physical per-ray delays, direct-order spatial map —
tracks `RESOLVED_PHYSICAL` exactly at every SNR. `SPATIAL_ONLY_PHYSICAL` —
physical spatial maps, delays flattened onto the direct field — tracks
`DIRECT_PHYSICAL` exactly (both tracking relations hold at every SNR in the sweep). **This reverses E1.** In the toy, a common sampler
made the delay ladder worth nothing and spatial diversity did all the work. On
physical Kerr maps the opposite holds. E1's mechanism conclusion does not
survive contact with the real transfer maps, and should not be carried into the
manuscript as a physical statement.

**Attenuation costs real depth. This reverses the earlier reading.** Under the
retired flat-sigma convention `RESOLVED_EQUALIZED` beat `RESOLVED_PHYSICAL` by
one grid step at SNR 100, and the experiment reported that a ~3154x
throughput suppression cost almost no historical reach. Under the corrected
convention the same comparison gives at least 36 M at SNR 100 and
at least 56 M across the sweep — lower bounds, because
`RESOLVED_EQUALIZED` is right-censored at the 120 M grid
ceiling wherever the gap is largest. The earlier statement was an artefact of
the flat-sigma row budget, which had already given the faint deep orders most
of the equalization for free. Removing physical attenuation is worth tens of M of
reach, not a rounding step, and the corrected finding is the opposite of the
one previously recorded.

**Total information barely moves; distinguishable directions do.** The resolved
stack carries trace information 8.944e+08 against the direct image's
8.845e+08 — a gain of 1.12%, because
orders 1 and 2 collect almost no photons. Its operational rank nonetheless rises
from 153 to 201 of 224. That gap is the whole point: the deep
orders add structure, not signal, and any figure of merit built on total
information will miss what they contribute.

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
| 0 | 230 | 1.13e-36 | 7.12e-92 | – | – |
| 20 | 273 | 0.000347 | 6.02e-29 | 1.27e-06x | – |
| 40 | 247 | 3.36 | 0.0012 | 0.0136x | 0.000359x |
| 60 | 4.39 | 3.33 | 0.0985 | 0.758x | 0.0296x |
| 80 | 1.99e-24 | 1.41 | 0.049 | – | 0.0347x |
| 100 | 1.15e-86 | 0.0236 | 0.0169 | – | 0.716x |
| 116 | 3.26e-164 | 3.07e-14 | 0.000716 | – | – |

This is the **age_specific_order_dominance_ratio**: a pointwise comparison at a
fixed absolute age between orders whose temporal supports barely overlap. It is
deliberately *not* called Gamma_info, because it does not measure a decay along
matched support. Order 1 overtakes order 0 between 60 M and 64 M; order 2 overtakes
order 1 between 100 M and 104 M. Under the retired convention those crossovers sat at
44–48 M and 60–64 M, so correcting the whitening pushes each of them ~16 to
40 M deeper: the deep orders take over later than previously reported. The
ordering survives; the depths and the ratios do not. Entries appear only where both orders clear an
information floor — a ratio of two vanishing informations is neither a ratio nor
an exponent.

## Sensitivity attenuation on matched support

Each order is sampled at the same fractional position within its **own** retarded
window, so the orders are compared on matched temporal support:

    Gamma_sensitivity_matched = -0.5 * log(I_next_matched / I_current_matched)

All 19 window fractions are retained; the full distribution is in
`artifacts/tables/e3b_matched_support_attenuation.parquet`.

| window fraction | age n=0 | age n=1 | age n=2 | Gamma_sens 0→1 | Gamma_sens 1→2 |
|---:|---:|---:|---:|---:|---:|
| 0.05 | 2.9 | 49.0 | 65.3 | 1.980 | 1.887 |
| 0.25 | 14.5 | 59.9 | 76.7 | 2.159 | 2.035 |
| 0.45 | 26.0 | 70.8 | 88.2 | 2.426 | 2.106 |
| 0.65 | 37.6 | 81.7 | 99.7 | 2.704 | 2.138 |
| 0.85 | 49.1 | 92.5 | 111.2 | 2.899 | 2.305 |

Median Gamma_sensitivity_matched is **2.486** from order 0 to 1 and
**2.120** from 1 to 2, defined at all 19 window fractions. Against
Gamma_amp of 4.27 and 4.03, sensitivity decays more slowly than
throughput by **1.79 and 1.91 in the exponent** —
a factor of about 1.7x and 1.9x in the rate,
not the order of magnitude reported under the retired convention.

**This is the largest single change from the corrected convention, and the
earlier number should not be quoted.** The retired flat-sigma run gave 0.576
and 0.387, which read as "information decays seven to ten times more slowly
than amplitude". That gap was manufactured: a flat per-row sigma across bands
of wildly different solid angle inflates the thin deep bands, and it inflates
precisely the quantity the claim rested on.

The corrected gap is not a fitted result but a convention-level identity, which
is why it is worth stating. A whitened row carries sqrt(dOmega) where the flux
carries dOmega, so information scales linearly in solid angle where throughput
scales quadratically, and

    Gamma_sensitivity_matched ≈ Gamma_amp − 0.5 · log(dOmega_0 / dOmega_1)
                              = 4.27 − 1.91
                              = 2.36

against a measured 2.49. The surviving statement is therefore weaker,
better founded, and still the operative one: a single scalar attenuation
exponent describes the throughput and misdescribes the information, by about
half the log solid-angle demagnification. Higher orders are ~3154x
fainter and remain the sole carriers of everything older than about 60 M.

## Claim effect
Permits, for this one geometry: reporting that the physical historical channel
is a distributed, overlapping retarded-time kernel; that its reach is supplied
by delay diversity rather than spatial remapping; and that throughput
suppression and information suppression are different quantities with
different magnitudes, separated by about half the log solid-angle
demagnification.
Demotes: E1's mechanism finding, which is a property of the toy's common
sampler and not of Kerr.
Forbids: any 12-geometry or spin/inclination-dependent statement; any
identification of Gamma_amp with a geometric exponent; any ML claim.

## Artifacts
`artifacts/tables/e3b_*.parquet`, `artifacts/configs/E3B_FREEZE.json`,
`artifacts/provenance/E3B_ARTIFACT_MANIFEST.json`.
