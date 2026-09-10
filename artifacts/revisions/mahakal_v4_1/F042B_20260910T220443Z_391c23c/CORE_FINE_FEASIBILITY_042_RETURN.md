# Cached-data feasibility pass, orders 0 and 1 — return report

**Return token: `CORE_FINE_FEASIBILITY_042_FEASIBLE_AND_MEASURED`**

Zero convention-B units: three cached screen samplings of the reference
geometry were read, nothing was traced. 19146 spent, 854 unspent; boundary
33410.

## Step 1 — can the cached records synthesize the actual 72/152 columns? Yes

Both the core and fine maps for `a050_i050` at n = 0 and n = 1 carry
`source_r`, `source_phi`, `delay`, `redshift`, `pixel_area` and `valid`, which
is everything `PhysicalOperator` consumes. The actual source columns can
therefore be evaluated directly at each map's own landing coordinates. A
`coarse` map exists too, giving a three-level ladder at roughly 4x valid rays
per step.

Valid rays: n0 3992 / 15597 / 61635 and n1 2156 / 8531 / 34278 for coarse,
core and fine. The core and fine counts match the 034 audit's recorded
`fine_emitting_nodes` exactly.

**Nothing is interpolated between grids.** The 034 coverage problem came from
carrying core-derived values onto fine nodes; here each construction evaluates
the declared basis where its own rays actually land, so no support is
zero-filled and none is dropped.

## Step 2 — four constructions of the same {0,1} operator

One frozen sigma = 0.011341986814407568, one frozen 72/152 split, one frozen
source Gram at 12800 nodes per axis. The operators are never materialized: the
fine stack is 767,304 rows, so a streaming QR carries a 224x224 factor with
the same column geometry, which fixes the projector, the spectrum and the
Gram exactly.

Gate: the `ARCHIVED` construction reproduces the triage's {0,1} row —
1.4098, 1.2954, 0.7606, tr F_cond 6.276810, count 2, nuisance rank 148. PASS.

| construction | rays n0 / n1 | s1 | s2 | s3 | ops | tr F_cond |
|---|---|---:|---:|---:|:--:|---:|
| ARCHIVED (1536/order) | 1536 / 1536 | 1.4098 | 1.2954 | 0.7606 | **2** | 6.276810 |
| COARSE_ALL | 3992 / 2156 | 1.4523 | 1.2168 | 0.7587 | **2** | 5.974738 |
| CORE_ALL | 15597 / 8531 | 1.3973 | 1.2130 | 0.6776 | **2** | 5.977209 |
| FINE_ALL | 61635 / 34278 | 1.4079 | 1.2485 | 0.6805 | **2** | 6.317796 |

Nuisance rank is 148 in all four.

## Step 3 — target-specific differences

The four constructions have different row counts, so `B_fine - B_core` is not
an operator and has no norm. The comparable object is the 72x72 conditional
Gram in source-normalized target coordinates — the matrix the singular values
come from — and Weyl on its eigenvalues bounds every singular-value change.
This is a substitution for the requested operator norm and is reported as one.

| comparison | ‖ΔGram‖₂ | max abs Δs | ops | max principal angle |
|---|---:|---:|---|---:|
| subsample: ARCHIVED → CORE_ALL | 0.4954 | 0.0830 | 2 → 2 | 12.15° |
| refinement: COARSE_ALL → CORE_ALL | 0.3787 | 0.1112 | 2 → 2 | 17.90° |
| refinement: CORE_ALL → FINE_ALL | 0.2050 | 0.0524 | 2 → 2 | 6.30° |
| archived → refined | 0.5371 | 0.0801 | 2 → 2 | 16.90° |

**The count is two at every level.** The refinement change is shrinking:
0.3787 to 0.2050 across the ladder, a ratio of 0.541, with the subspace
rotation falling 17.90° to 6.30°. Two steps are a trend, not a measured order
of convergence, and neither step is a distance from the continuum.

Applying the measured last-step difference as if it bounded one further step
of the same size:

| mode | s (fine) | Weyl interval |
|---|---:|---|
| 1 | 1.4079 | [1.3331, 1.4789] |
| 2 | 1.2485 | [1.1635, 1.3281] |
| 3 | 0.6805 | [0.5080, 0.8174] |

The operational count is then bounded to exactly **[2, 2]** — both passing
modes stay above threshold and the third stays below. Within this
discretization family the two-mode count is bounded, not merely observed.

At `FINE_ALL` the target-specific margins are s2 − rho = 0.2485 and
rho − s3 = 0.3195.

## Step 4 — support kept separate, not folded in

| construction | dOmega sum, n0 | response mass n0 | dOmega sum, n1 | response mass n1 |
|---|---:|---:|---:|---:|
| ARCHIVED | 2495.520 | 1.9759e+03 | 54.5984 | 2.0892e+01 |
| COARSE_ALL | 2554.880 | 2.0434e+03 | 55.1936 | 2.1221e+01 |
| CORE_ALL | 2495.520 | 1.9920e+03 | 54.5984 | 2.0951e+01 |
| FINE_ALL | 2465.400 | 1.9666e+03 | 54.8448 | 2.1051e+01 |

The total valid solid angle is not identical across levels — about 2.4% high
at coarse and 1.2% low at fine relative to core for n0 — because each grid
resolves the emitting-support boundary differently. That residual is a
**support difference, carried separately**; it is not folded into the Gram
comparison and no level's missing edge is given a response bound here.

Two of the 34278 fine n1 rays land outside the declared annulus. Disclosed,
not removed.

## Step 5 — what a further extension would cost, and why it is not the buy

The ladder is roughly 4x screen samples per step: 4096, 15876, 62500 for n0
and 15876, 62500, 250000 for n1. A fourth level is 250000 and 1000000 samples,
about 1.25 million traces against 854 remaining units — roughly 1460x over.
Not affordable, and on this evidence not the right purchase.

**The largest removable error is not the screen resolution.** The 1536-ray
subsample moves the spectrum more than the last refinement does — ‖ΔGram‖₂
0.4954 against 0.2050, and 12.15° of subspace rotation against 6.30°. That
error costs nothing to remove: the cached maps already hold 15597 and 8531
core rays, and 61635 and 34278 fine ones.

So the affordable next step is a re-baseline of the R2 endpoint onto all
cached fine rays, not new geodesics. That is a separate authorization; this
pass does not perform it and does not restate any archived endpoint.

## What this does not establish

No level here bounds the distance to the continuum operator. A shrinking
difference across three discretizations is evidence of internal convergence,
not qualification of the transfer quadrature, which stays open. The Weyl
interval above uses a measured inter-level difference as a stand-in for a
further step of the same size; it is not a certified error bound.

The subspace is less well determined than the count: the two-mode identity
moves 12.15° under the subsample alone and 16.90° from archived to refined,
against the 3.21° that removing order 2 produced. Any statement about *which*
historical combinations survive should carry that, and it is a larger
uncertainty than the order-2 dependence the triage measured.

This return authorizes nothing: no re-baseline, no support extension, no
funded replay, no submission.

## Files

- `CORE_FINE_FEASIBILITY_042.json` — spectra, comparisons, support, bounds
- `run.log` — execution transcript
- generator: `scripts/revision_v4_1/t042_core_fine_feasibility.py`

An earlier two-level execution of this script, without the coarse level, is
left in place under its own `F042_...` directory. This three-level run
supersedes it and reproduces its numbers exactly.
