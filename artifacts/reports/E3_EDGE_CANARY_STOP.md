# EDGE CANARIES — STOPPED BEFORE THE PRODUCTION GRID

## Ruling executed

The grid was conditioned on both edge canaries passing, with an immediate stop
on any registered gate failure. **Neither condition is met.** The ten remaining
geometries were not started.

| item | result |
|---|---|
| Edge canary 1, a\* = 0, i = 20° | **cannot be generated** — backend limitation |
| Edge canary 2, a\* = 0.98, i = 75° | generated; **G7 fails**, every other registered gate passes |
| Production grid | **not started** |

## Edge canary 1 — AART cannot do Schwarzschild

`lensingbands.CritCurve` returns an empty root set at exactly `a = 0`. The cause
is structural, not a bug in this repository:

```text
lam = a + (r/a) * (r - 2(r^2 - 2r + a^2)/(r - 1))
eta = (r^3/a^2) * (4(r^2 - 2r + a^2)/(r - 1)^2 - r)
```

Both divide by the spin, and the photon shell `[rM, rP]` that `r` sweeps
collapses to the single radius 3M when `a = 0`. The positivity mask then selects
no points.

The singularity is only at the endpoint. Measured:

| a\* | CritCurve | α range |
|---|---|---|
| 0 | **fails** | – |
| 1e-6 | ok | ±5.1969 |
| 1e-4 | ok | ±5.1961 |
| 0.5 | ok | −4.7675, +5.4720 |
| 0.98 | ok | −4.0105, +5.6156 |

At `a = 1e-6` the critical curve sits at α = ±5.1969 against the exact
Schwarzschild value 3√3 = 5.19615 — agreement to 1.5e-4. So a numerical
stand-in is *available*, and adopting one is a change to the registered geometry
grid, which is the reviewer's call and not the agent's. No AART source was
modified and no substitute spin was used.

Three dispositions are open, in the reviewer's hands:

1. amend the registry to `a* = 1e-6` for the Schwarzschild point, recording the
   1.5e-4 critical-curve deviation as a declared systematic;
2. generate that one geometry with kgeo, accepting a different backend for one
   of twelve points and the provenance asymmetry that creates;
3. drop `a* = 0` from the registered grid and state the coverage limit.

## Edge canary 2 — one registered gate fails

| gate | measured | frozen tolerance | verdict |
|---|---:|---:|---|
| `G7_grid_convergence` | **6.472e-02** | 2e-02 | **FAIL** |
| `G8_cross_tracer` | 1.693e-12 | 1e-09 | PASS |
| `G8t_retarded_time` | 4.781e-06 M | 1e-03 M | PASS |
| `G8phi_rigid_origin_alignment` | 2.971e-11 rad | 1e-08 rad | PASS |
| `G9c_per_order_ray_count` | 9804 | 1536 | PASS |
| `EDGE2_finite_transfer_weights_and_masks` | – | – | PASS |
| `EDGE2_memory_budget` | ~3 GiB | 15.7 GiB | PASS |

Ray counts: n0 = 9995, n1 = 20139, n2 = 9804 at the core profile. Source radii
reach 1.199 M, the a\* = 0.98 horizon, exactly as they should.

### The failure is carried by one metric

Every convergence metric at this geometry is within 1.2e-02 **except one**: the
n = 1 deepest retarded age, which moves 161.8 M → 173.0 M between core and fine.

That is an extreme-value statistic over rays — a maximum, populated by the band
edge — and it converges far more slowly than any integral. The tolerance was
frozen from a pilot geometry where the same statistic behaved well.

**The tolerance was not adjusted and the metric was not re-specified as a high
quantile.** Either would be post-hoc loosening after seeing a failure.

### The operator, meanwhile, does converge

The quadrature-weighted information matrix — the object the inverse problem
actually consumes — was also measured at this geometry:

| step | relative change in G |
|---|---:|
| coarse → core | 6.081e-02 |
| core → fine | **3.088e-02** |

That passes `G7b` at 5e-02, with refinement halving the change. So the
high-spin edge is converged in the operator and not converged in one
extreme-value ray statistic.

This is decision-relevant and is offered as diagnosis, not as grounds to
proceed: `G7_grid_convergence` is a registered gate and it failed.

## What the reviewer needs to decide

1. the Schwarzschild point — one of the three dispositions above;
2. whether `G7_grid_convergence` should keep a raw maximum among its metrics, or
   whether extreme-value statistics belong in a separate gate with their own
   tolerance. Re-specifying it now, having seen the failure, is not the agent's
   call.

Until both are settled the production grid stays unstarted.
