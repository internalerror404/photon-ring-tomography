# S0 — EXACT SCHWARZSCHILD BACKEND CANARY

## Result

**All 19 gates pass.** `PRODUCTION_GRID` is authorized by the
standing ruling.

## Why a new backend was needed

Two independent tools are singular at exactly zero spin, for unrelated reasons.
Both were found by measurement.

**AART `lensingbands.CritCurve`** forms `lam = a + (r/a)(…)` and
`eta = (r^3/a^2)(…)` while sweeping `r` over the photon shell `[rM, rP]`, which
collapses to the single radius 3M at `a = 0`. Both divide by the spin and the
positivity mask then selects nothing. Its usable floor sits between 1e-5 and
1e-6: at 1e-6 the critical-curve arclength goes complex and `numpy.interp`
refuses the cast.

**kgeo `velocities.u_kep`** computes `Omega = np.sign(a) * s / (r^1.5 + s|a|)`.
The `np.sign(a)` factor is there to set the orbit sense, and it is zero at
`a = 0`, so a Keplerian disk is returned **non-rotating**: `u^t` is correct and
`u^phi` is identically zero. Verified against the closed form at r = 7, 10, 30.

kgeo's *geodesics* are fine at `a = 0`, so only the velocity needed replacing.
Neither package was modified; both remain pinned validation dependencies.

## Composition

| piece | source |
|---|---|
| geodesics | kgeo `r_equatorial` / `coords_at_tau` |
| band membership | kgeo `nmax_equatorial` — a ray's equatorial crossing count, which is the definition of a lensing band and needs no critical-curve parameterisation |
| fluid velocity | `phrt.geometry.schwarzschild`, explicit closed form |
| redshift | kgeo `calc_redshift`, fed the corrected velocity |

Only the piece that had to be new is new.

## Exact invariants validated against

| quantity | value |
|---|---|
| horizon | 2.0 M |
| photon sphere | 3.0 M |
| ISCO | 6.0 M |
| critical impact parameter | 3√3 = 5.196152423 M |
| E, L at ISCO | 0.942809042, 3.464101615 |

`R(3M)` and `R'(3M)` both vanish at `b = 3√3` to machine zero, so the photon
sphere and the critical impact parameter are checked from the radial potential
itself rather than from a fitted band edge.

## Low-spin limit

| spin | status | min valid rays | r_min | n=0 band area | rel. to Schwarzschild |
|---|---|---:|---:|---:|---:|
| 0.001 | ok | 3085 | 2.0005 | 2494.7200 | 0.0117 |
| 0.0001 | ok | 3088 | 2.0005 | 2494.7200 | 0.0117 |
| 1e-05 | ok | 2923 | 2.0002 | 2488.3200 | 0.0091 |
| 1e-06 | **AART_FAILED** | – | – | – | – |

AART converges to the Schwarzschild backend as the spin falls, reaching 1.2%
agreement in the n = 0 band solid angle. The a = 1e-6 point is a backend
failure, recorded rather than worked around.

## A geometry-id collision, found and fixed

`geometry_id` encoded spin as `int(round(spin*100))`, which is exact for every
registered grid spin but **not injective below 0.005**: 1e-3, 1e-4, 1e-5 and
1e-6 all render as `a000`. Every low-spin AART probe therefore overwrote the
Schwarzschild maps at `a000_i020`.

The first S0 run reported `S0_6_operator_convergence` = 0.5208 and failed. That
number was core (AART at a = 1e-5) compared against coarse and fine (kgeo at
a = 0) — two backends at two spins, not a convergence measurement. With
distinct ids the same gate reads **0.007364**.

Fixed two ways: probe spins off the registered grid now get a
mantissa-exponent field (`a1p000e-5_i020`), and both builders refuse to
overwrite a map whose stored spin differs from the run's. A silent overwrite of
one geometry by another is not recoverable from the artifacts alone.

## Gates

| gate | status | measured | threshold |
|---|---|---:|---:|
| `S0_4_exact_horizon` | **PASS** | 1.848e-05 | 0.005 |
| `S0_4_no_ray_inside_horizon` | **PASS** | 2 | 2 |
| `S0_2_photon_sphere_double_root` | **PASS** | 0 | 1e-12 |
| `S0_3_critical_impact_parameter` | **PASS** | 2 | 0 |
| `S0_7_four_velocity_normalisation` | **PASS** | 2.22e-16 | 1e-12 |
| `S0_7_keplerian_closed_form` | **PASS** | 2.22e-16 | 1e-12 |
| `S0_7_finite_positive_weights` | **PASS** | 1 | 1 |
| `S0_7_quadrature_order0` | **PASS** | 2466 | 0.16 |
| `S0_7_quadrature_order1` | **PASS** | 36.72 | 0.0064 |
| `S0_7_quadrature_order2` | **PASS** | 1.236 | 0.0004 |
| `S0_5_aart_low_spin_sequence` | **PASS** | 3 | 3 |
| `S0_5_low_spin_area_approaches_schwarzschild` | **PASS** | 0.01174 | 0.05 |
| `S0_1_numerical_integrator_cross_check` | **PASS** | 1.841e-05 | 0.001 |
| `S0_6_operator_convergence` | **PASS** | 0.007364 | 0.05 |
| `S0_8_G2_physical_dense_matrix_free` | **PASS** | 0 | 1e-10 |
| `S0_8_G3_physical_adjoint` | **PASS** | 1.366e-14 | 1e-08 |
| `S0_8_G4_resolved_unresolved_mixing` | **PASS** | 0 | 1e-10 |
| `S0_8_G6_Gram_monotonicity` | **PASS** | 0 | 1e-10 |
| `S0_8_G9w_weight_semantics` | **PASS** | 1.264e-16 | 1e-10 |

## Artifacts
`artifacts/tables/s0_low_spin_limit.parquet`,
`artifacts/tables/s0_operator_comparison.parquet`,
`artifacts/gates/s0_correctness_gates.json`,
`artifacts/provenance/s0_artifact_manifest.json`,
`artifacts/raymaps/a000_i020_n*_{coarse,core,fine}.h5`.
