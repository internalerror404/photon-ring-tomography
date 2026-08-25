# E3C — MECHANISM DECOMPOSITION

## Identity
- branch `claude/experiment-review-mac-rthiz1`, commit `e766cfcd9c9340c40e969f90c322e04de01c8ba3`
- registry sha256 `2ba66f0209fe1cdec97b8cf5862494c22fb94704318f9601a7a1f9eb4b783796`
- freeze `artifacts/configs/E3C_OPERATOR_GRID_FREEZE.json` sha256 `818199a7ac4f3f90cf592f568d2a550dfd575aba1d539b0966a3a5c6521473d2`
- 12 registered geometries, orders n = 0, 1, 2, profile `core`
- source class `C224` (224 dimensions), unmodified
- common age grid 0 to 252 M in steps of 4 M

## The question

The canary established, on one geometry, that the historical reach of the
resolved operator comes from retarded-time diversity rather than from spatial
remapping. One geometry cannot distinguish a mechanism from a coincidence of
that geometry's lensing bands. This report tests the decomposition on all
12 registered geometries.

Two substitution arms isolate the two candidate mechanisms while holding
everything else fixed:

* `DELAY_ONLY` keeps each order's physical per-ray delays and replaces its
  spatial mapping with the direct order's.
* `SPATIAL_ONLY` keeps each order's physical spatial mapping and flattens every
  delay onto the direct order's delay field.

Neither arm changes the measurement model, the noise, the source class or the
ray weights. The comparison is against the full resolved operator's
age-information curve on the common grid.

## Result

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

**First, the registered statistic does not answer the question.** The
registered localized probe is spatially flat. `DELAY_ONLY` changes only where
the rays land on the source plane, so the scalar curve `I(a)` is
bitwise identical between the
full and delay-only arms at every geometry, and `D_delay = 0` is an algebraic
identity. Reporting that zero as evidence for the delay mechanism would have
been circular. Amendment 002 records the degeneracy, preserves the literal
values, and adds the comparison on the registered 28-dimensional localized
class, where the substitution does act.

**On that class the mechanisms separate, but far less sharply than the canary
suggested.** Median relative discrepancy: delay-only 0.165,
spatial-only 0.310, with the direct arm at 0.303 as the
scale. Delay-only is the closer of the two substitutions in
**12 of 12** cells.

The ordering holds in every cell, so the direction of the canary's conclusion survives the grid — but its magnitude does not. Delay diversity is the larger of the two contributions to historical reach, not the whole of it.

## Why the endpoint alone would have been the wrong test

Spatial remapping can improve conditioning without moving the oldest detectable
probe centre. Reading the mechanism off a depth endpoint would therefore credit
delay with everything spatial diversity does to `kappa+`. The `kappa+` columns
above are reported next to `D` for exactly that reason, and the two are not the
same statement.

## What this does and does not license

Licensed: the statement that, on the registered geometries and class, the
distributed retarded-time structure of near-critical null geodesics — not the
spatial remapping of the higher-order images — is what extends recoverable
history.

Not licensed: any claim about a continuum source, any claim about geometries
outside the registered grid, any asymptotic exponent from n = 0, 1, 2, and any
reading of `PAIRING_DESTROYED` as a measurement architecture.
