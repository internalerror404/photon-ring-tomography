# E3B — TRANSFER-WEIGHT SEMANTICS AUDIT (G9w)

## Identity
- branch `claude/experiment-review-mac-rthiz1`, commit `0ef341dae3b21bc2bdd0e54a18971cff208af783`
- registry sha256 `2ba66f0209fe1cdec97b8cf5862494c22fb94704318f9601a7a1f9eb4b783796`
- geometry a* = 0.5, i = 50 deg, orders n = 0, 1, 2 (the single authorized pilot geometry)
- kgeo commit `dc347060c5fb24e2c360c8aaffbfe25482a83805`

## Declared semantics

| item | value |
|---|---|
| accretion-flow prescription | Keplerian outside the ISCO, AART's plunging solution inside |
| flow parameters | `betaphi = 1.0`, `betar = 1.0`, `sub_kep = 1.0` |
| zeta_n | 1 for every order; no extra geometric factor is applied |
| observable | monochromatic specific intensity; `g^3` per ray |
| pixel area | enters the likelihood, not the forward row, under the primary model |
| redshift units and sign | dimensionless `g = nu_obs / nu_emit`, taken positive; AART sets `g = 0` at and inside the horizon |
| source radial support | horizon (1.866 M at a* = 0.5) to a declared 50 M outer edge |
| quadrature | `dOmega = dx_n^2`, different for every band |

Three measurement models are implemented and have different null spaces:
specific intensity (`c = g^3`, the primary oracle), photon count
(`c = dOmega·g^3`), and total flux (spatial collapse, the deliberately
information-poor control).

## Unit-source test

A source `j(r, phi, t) = 1` is pushed through the operator and compared against
`sum(dOmega · g^3)` computed outside it.

| order | operator unit-source throughput | independent sum dOmega·g^3 | relative |
|---:|---:|---:|---:|
| 0 | 2069.153391 | 2069.153391 | 0.000e+00 |
| 1 | 28.87133011 | 28.87133011 | 1.231e-16 |
| 2 | 0.656109304 | 0.656109304 | 1.692e-16 |

Exact agreement, per order. The operator's weighting is what the audit says it
is.

## Why the total-flux arm carries sqrt(N) noise

A total-flux row sums N pixels with independent per-pixel noise, so it carries
`sigma·sqrt(N)`. An earlier revision gave it the per-pixel sigma while giving it
the summed signal, which made the information-poor control look competitive at
low SNR. Corrected, it behaves as intended: at SNR 10 it reaches age 40 M
against the resolved arm's 84 M.

## Gates
| gate | status | measured | threshold |
|---|---|---:|---:|
| `G9w_weight_semantics` | **PASS** | 1.692e-16 | 1e-10 |
| `G9c_per_order_ray_count` | **PASS** | 4179 | 1536 |

`G9c` answers the reviewer's challenge directly: n0 = 15597, n1 = 8531,
n2 = 4179, minimum per order = 4179, total = 28307. The reported 4179 was the
per-order minimum, not the combined total, and every order independently
exceeds the registered 1536.
