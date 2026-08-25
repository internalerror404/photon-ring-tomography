# E3B — RETARDED-TIME AND AZIMUTH VALIDATION (G8t, G7b)

## Identity
- branch `claude/experiment-review-mac-rthiz1`, commit `e766cfcd9c9340c40e969f90c322e04de01c8ba3`
- registry sha256 `2ba66f0209fe1cdec97b8cf5862494c22fb94704318f9601a7a1f9eb4b783796`
- geometry a* = 0.5, i = 50 deg, orders n = 0, 1, 2 (the single authorized pilot geometry)
- kgeo commit `dc347060c5fb24e2c360c8aaffbfe25482a83805`

## Why this gate exists

G8 certified the source-radius map to 1.1e-12. Paper I is about historical
inversion, so the emission time is the field the claim rests on, and it had not
been independently checked.

## Independent route

kgeo's analytic elliptic-integral solution, evaluated at the Mino time its own
`r_equatorial` returns, gives `t_s` and `phi_s` by a path sharing no code with
AART. The coordinate slotting is verified against the trusted radius and against
`theta = pi/2` rather than assumed — a mis-slotted `t` would have produced a
number while meaning nothing.

## Time

Compared as **pairwise differences** over 25,200 pairs from
225 stratified rays, 16,875 of them
spanning different orders, so a common origin cancels.

| quantity | value |
|---|---:|
| worst pairwise difference | 4.781e-06 M |
| fitted common offset | -2.274e-13 |
| radius control, max relative | 6.521e-13 |

The fitted offset is zero: the two codes already share a time origin.

## Azimuth — a real convention difference

`phi_kgeo = phi_aart + pi/2`, exactly, to
4.419e-14. Residual after
removing one global constant:
2.971e-11 rad. Spread of that constant
across orders: 1.315e-13 rad.

A reflection was tested and rejected (residual 3.14). This is a rigid rotation
of the equatorial azimuth origin, a convention in the same sense a common time
origin is. The gate that matters is the second one: a global rotation only
relabels the azimuth axis, whereas an order-dependent or screen-dependent
rotation would corrupt every non-axisymmetric source model. Nothing was altered
to make anything agree; the repository adopts AART's origin and records the
transformation.

## G7b — what the first version of this gate got wrong

The first construction compared transfer-field *values* between the core and
fine profiles at matched screen points and failed at 0.366 against 5e-2.

That failure was not physics. AART's ray tracing is analytic: landing
coordinates are closed-form in `(alpha, beta)`. Verified here against the
grid-free kgeo at **both** resolutions, agreeing to 2.6e-15 (n=0), 1.1e-13
(n=1) and 2.2e-12 (n=2). The per-ray fields carry no discretisation error at
all.

`dx` controls only which screen points are sampled — the quadrature. Two
profiles never evaluate the same point, so comparing field values measures the
field gradient across the grid offset. In the n=2 band the source radius sweeps
from the horizon to 50 M across a band a few hundredths of an M wide, so that
gradient dominates everything. The test was measuring band steepness.

The corrected gate is on the quantity the inverse problem actually consumes:

    G = sum_p dOmega_p (g_p^3)^2 D_p D_p^T

accumulated over every valid ray with its own quadrature weight — no matching,
no subsampling. Weighting rows equally would make G grow without bound under
refinement and could never converge, which was the second defect.

| step | relative change in G |
|---|---:|
| coarse → core | 4.408e-02 |
| core → fine | 2.192e-02 |

Refinement halves the change, which is convergence.

The field-level statistics are retained in
`artifacts/tables/e3b_field_convergence.parquet`, relabelled as a
band-steepness diagnostic rather than a convergence test.

## Gates
| gate | status | measured | threshold |
|---|---|---:|---:|
| `G8t_retarded_time_validation` | **PASS** | 2.763e-06 | 0.001 |
| `G8t_azimuth_after_rigid_offset` | **PASS** | 6.329e-12 | 1e-08 |
| `G8t_azimuth_offset_is_order_independent` | **PASS** | 1.303e-13 | 1e-09 |
| `G8t_radius_control` | **PASS** | 8.963e-13 | 1e-09 |
| `G7b_transfer_field_convergence` | **PASS** | 0.02192 | 0.05 |
| `G7b_fields_are_analytic_not_discretised` | **PASS** | 2.2e-12 | 1e-09 |
