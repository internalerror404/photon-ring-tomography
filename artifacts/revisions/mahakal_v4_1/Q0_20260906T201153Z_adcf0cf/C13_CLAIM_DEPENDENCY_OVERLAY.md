# C13 claim dependency overlay

Ruling 026, phase Q0. An audit of what is already in the tree. No map, operator, weight, table or endpoint is altered by this document, and no archived number is recomputed or declared changed.

## The two descriptions that disagree

`build_raymaps.py` stores `pixel_area = dx**2` from the pitch the generator was asked for. Both generators lay endpoint-inclusive nodes across a declared finite square domain and derive their own count, so the realized spacing is `2*lims/(N-1)`:

- `aart.lensingbands.grid_mask`: `linspace(-lims, lims, round_up_to_even(2*lims/dx))`
- `build_raymaps_schwarzschild.band_grid`: `linspace(-lim, lim, ceil(2*lim/dx))`

Both rules reproduce every observed node count in the archive (True), so the sampling semantics are settled from the generators rather than inferred from the numbers. The samples are nodes, not cell centres. Every axis is uniform and, in every archived map, alpha and beta share a spacing -- checked separately, because a rectangular grid would make a single `delta` silently wrong in one direction.

The stored weight matches the realized geometry in 16 of 63 maps and disagrees in 47, worst case 2.0304% in cell area.

## Where the weight is read

| file | sites | role | what it does with the weight |
| --- | ---: | --- | --- |
| `scripts/build_e3c_freeze.py` | 1 | FREEZE | records the operator grid |
| `scripts/build_raymaps.py` | 1 | GENERATOR | writes pixel_area = dx**2 from the requested pitch, beside coordinates AART returned on a different pitch |
| `scripts/build_raymaps_schwarzschild.py` | 1 | GENERATOR | same, for the kgeo cross-tracer maps |
| `scripts/revision_v4_1/q0_measure_inventory.py` | 5 | REVIEW_TOOLING | this audit |
| `scripts/revision_v4_1/r3a_build.py` | 5 | REVIEW_TOOLING | R3A construction |
| `scripts/revision_v4_1/r3a_return_report.py` | 2 | REVIEW_TOOLING | R3A report |
| `scripts/run_delay_quantiles.py` | 1 | DIAGNOSTIC | area-weighted delay quantiles |
| `scripts/run_e3_validation.py` | 2 | DIAGNOSTIC | pilot cross-profile table |
| `scripts/run_g10q_quadrature_invariance.py` | 2 | GATE | quadrature invariance under resampling at fixed measure |
| `scripts/run_g5ab_instrumentation.py` | 2 | GATE | instrumentation totals |
| `scripts/run_g7b_field_convergence.py` | 5 | GATE | field convergence across profiles; excludes pixel_area by name as expected_to_differ, so it is not an area audit |
| `scripts/run_production_grid.py` | 2 | DIAGNOSTIC | per-geometry reported totals |
| `scripts/run_s0_backend_canary.py` | 7 | GATE | checks the stored total against metadata['dx']**2, the value it was built from, so it cannot detect C13 |
| `src/phrt/geometry/raymap.py` | 7 | SCHEMA | declares the field and reports total_quadrature_area; documents it as dx_n^2, which is the claim C13 disputes |
| `src/phrt/geometry/sampling.py` | 2 | OPERATOR_QUADRATURE | the only path from the stored weight to an operator row. stratified_subsample gives each retained ray stratum_area/n_taken and then rescales so the order's TOTAL solid angle is preserved, so what reaches the operator is the per-order total, not the per-ray footprint |
| `src/phrt/revision_v4_1/measure.py` | 2 | REVIEW_TOOLING | the corrected measure |
| `tests/revision_v4_1/test_r3a_construction.py` | 6 | TEST | R3A canaries, including C10 which measures the discrepancy |
| `tests/test_e3_pilot_products.py` | 3 | TEST | asserts pixel_area == dx**2, which pins the archive to the nominal value and will fail on a corrected map by design |
| `tests/test_raymap_schema.py` | 2 | TEST | schema fixtures only |

Only `src/phrt/geometry/sampling.py` carries the weight into an operator. It preserves each order's **total** solid angle and distributes it over retained rays as `stratum_area / n_taken`, so a retained ray's operator weight is already not its geometric footprint. That is the distinction the corrected records must keep: nominal request pitch, realized nodes, cell edges, geometric area, validity mask, and effective quadrature weight after subsampling are six different things.

## What the reference geometry's totals actually do

Per-order valid solid angle at a050_i050, split into the three causes the ruling asks be kept apart. `interior weight` is the realized spacing replacing the nominal pitch; `domain boundary` is dual-cell clipping at the declared screen edge; the mask is unchanged throughout.

| map | legacy total | interior weight | domain boundary | corrected total | net | band-edge area share |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| n0 coarse | 2554.8800 | -40.3927 | -59.5238 | 2454.9635 | -3.9108% | 2.99% |
| n0 core | 2495.5200 | +0.0000 | -30.0000 | 2465.5200 | -1.2022% | 1.49% |
| n0 fine | 2465.4000 | +19.8422 | -15.0602 | 2470.1819 | +0.1940% | 0.75% |
| n1 coarse | 55.1936 | +0.0000 | +0.0000 | 55.1936 | +0.0000% | 18.65% |
| n1 core | 54.5984 | +0.4394 | -0.0000 | 55.0378 | +0.8048% | 9.40% |
| n1 fine | 54.8448 | +0.2200 | +0.0000 | 55.0648 | +0.4012% | 4.69% |
| n2 coarse | 1.6592 | +0.0095 | -0.0000 | 1.6687 | +0.5739% | 86.11% |
| n2 core | 1.6716 | +0.0048 | +0.0000 | 1.6764 | +0.2863% | 57.84% |
| n2 fine | 1.6672 | +0.0028 | -0.0000 | 1.6700 | +0.1669% | 34.76% |

Two things in that table were not visible before this audit. Order 0's correction is dominated by **boundary clipping**, not by the interior pitch: its core map has an exact 0.4 M spacing, so the interior term is identically zero, and the whole -1.20% comes from the valid band reaching the declared screen edge where dual cells are half-width. And the share of each order's area sitting in cells on the lensing-band edge -- where a binary node mask cannot represent a boundary that cuts through a cell -- is 1.5% for order 0 but 57.8% for order 2 at the core profile. The n=2 band is two to three cells thick. That is a property of the sampling, and it is the quantity a fixed-detector refinement study has to resolve.

## Claims that inherit the per-order total

Every result built through the operator path inherits each order's total solid angle, and therefore inherits C13. Listing them is a dependency statement, not a claim that any number moves:

- **E3B** -- order-resolved reach and depth curves (`artifacts/reports`)
- **E3C** -- twelve-geometry operator audit and stored spectra (`artifacts/tables`)
- **E3D** -- nested source-class stress (`artifacts/tables`)
- **R0/R0C** -- rank, null space and calibration split (`artifacts/reports`)
- **R1** -- level and structure reconstruction endpoints (`artifacts/tables`)
- **R1L** -- localized temporal bases, stages 1 and 2R (`artifacts/tables`)
- **HMT-1/HMT-2** -- held-out historical inverse results (`artifacts/tables`)
- **R2** -- nuisance-adjusted conditional information (`artifacts/revisions`)

The direction of the effect is order-dependent, which is why it cannot be absorbed into a common normalization: at the core profile the corrected per-order totals move by -1.2022% (n=0), +0.8048% (n=1), +0.2863% (n=2). Half of each in amplitude, since the whitened row carries `sqrt(dOmega)`.

## Gates that cannot see this

- `run_s0_backend_canary.py` compares the stored total against `metadata['dx']**2`. That is the quantity the stored value was constructed from, so the check passes by construction and is not independent evidence of the geometry.

- `run_g7b_field_convergence.py` lists `pixel_area` as `expected_to_differ` between profiles and excludes it. A field convergence test that excludes area is not an area audit.

- `tests/test_e3_pilot_products.py` asserts `pixel_area == dx**2`. It is correct about the archive as built and will fail against any corrected map, by design. It is kept, under its own name, as a record of the legacy measure rather than as a check on the corrected one.

These remain part of the historical record and keep their results. None of them is retitled or repurposed into evidence for the corrected measure.

## Status

C13 is a confirmed geometry/weight inconsistency. Q0 establishes its extent and its dependency graph. It does not establish that any archived endpoint changes, and no such claim is made here. Physical revalidation under the corrected measure is the later task; the narrow analytical bound on R2 is recorded in Q1.

Generated from `C13_MAP_MEASURE_INVENTORY.json` at commit `adcf0cf1f4a0`.
