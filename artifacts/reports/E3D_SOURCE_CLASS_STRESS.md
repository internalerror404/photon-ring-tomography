# E3D — NESTED SOURCE-CLASS STRESS

## Identity
- branch `claude/experiment-review-mac-rthiz1`, commit `e766cfcd9c9340c40e969f90c322e04de01c8ba3`
- registry sha256 `2ba66f0209fe1cdec97b8cf5862494c22fb94704318f9601a7a1f9eb4b783796`
- freeze `artifacts/configs/E3C_OPERATOR_GRID_FREEZE.json` sha256 `818199a7ac4f3f90cf592f568d2a550dfd575aba1d539b0966a3a5c6521473d2`
- anchor geometries `a000_i020`, `a050_i050`, `a098_i075`
- conditional on E3C correctness, which passed

## Mechanical gate result

| gate | status | measured | threshold |
|---|---|---:|---:|
| `E3D_adjoint` | **PASS** | 4.89e-13 | 1e-08 |
| `E3D_dense_smoke_comparison` | **PASS** | 0 | 1e-10 |
| `E3D_Gram_monotonicity` | **PASS** | 1.136e-16 | 1e-10 |
| `E3D_class_nesting` | **PASS** | 2.73e-14 | 1e-10 |
| `E3D_enrichment_does_not_lose_rank` | **PASS** | 0 | 0 |

Exact adjoint, Gram monotonicity and a dense smoke comparison were run at every
class including `C1056_ST`; none was skipped for cost.

## Governance counts

```
    active_blocking_failures:   0
    preserved_literal_failures: 7
    future_phase_not_run:       11
```

A preserved literal failure is a FAIL that has been adjudicated and kept on the record rather than reinterpreted; the status is never edited to match the disposition. A not-run gate belongs to a phase that is not yet in scope. Neither is an unresolved scientific failure.

| preserved failure | disposition |
|---|---|
| `EDGE1_a000_i020_raymap_generation` | `RESOLVED_BY_S0_BACKEND` |
| `G10q_retired_flat_sigma_convention` | `RETIRED_PIXELIZATION_DEPENDENT` |
| `G1_v01_reproduction_relative` | `FAIL_AS_WRITTEN` |
| `G7_grid_convergence_a098_i075` | `RETIRED_NONCONVERGENT_EXTREME_STATISTIC` |
| `G7_grid_convergence_raw_max` | `RETIRED_NONCONVERGENT_EXTREME_STATISTIC` |
| `G7b_weighted_operator_discrepancy` | `WITHDRAWN_INVALID_CONVERGENCE_METRIC` |
| `GRID_AUTHORIZATION` | `SUPERSEDED_GRID_COMPLETE` |

## The class ladder

| class | radial | azimuthal | temporal | dimension | contains |
|---|---:|---:|---:|---:|---|
| `C224` | 4 | 7 | 8 | 224 | `—` |
| `C448_T` | 4 | 7 | 16 | 448 | `C224` |
| `C528_S` | 6 | 11 | 8 | 528 | `C224` |
| `C1056_ST` | 6 | 11 | 16 | 1056 | `C448_T` |

| geometry | parent | child | projection residual | radial columns preserved |
|---|---|---|---:|---|
| `a000_i020` | `C224` | `C448_T` | 2.730e-14 | yes |
| `a000_i020` | `C224` | `C528_S` | 1.080e-14 | no (knots refined) |
| `a000_i020` | `C448_T` | `C1056_ST` | 1.113e-14 | no (knots refined) |
| `a050_i050` | `C224` | `C448_T` | 2.136e-14 | yes |
| `a050_i050` | `C224` | `C528_S` | 1.308e-14 | no (knots refined) |
| `a050_i050` | `C448_T` | `C1056_ST` | 1.210e-14 | no (knots refined) |
| `a098_i075` | `C224` | `C448_T` | 2.368e-14 | yes |
| `a098_i075` | `C224` | `C528_S` | 1.707e-14 | no (knots refined) |
| `a098_i075` | `C448_T` | `C1056_ST` | 1.171e-14 | no (knots refined) |

**"Nested" means the function space, not the columns.** The azimuthal and
temporal factors are literal prefixes, so enriching them leaves the existing
columns untouched. The radial factor is a cubic B-spline basis and refining it
moves the knots: the individual columns change while the span is contained in
the enriched span, to 2.7e-14. Rank and
monotonicity statements depend on the span, which is what gate
`E3D_class_nesting` checks, and `E3D_enrichment_does_not_lose_rank` confirms
that no enriched class has lower numerical rank than its parent for any arm.

## Numerical rank against model richness

Bold entries are rank-deficient; the parenthesis is the nullity.

### `a000_i020`

| arm | `C224` (224) | `C448_T` (448) | `C528_S` (528) | `C1056_ST` (1056) |
|---|---:|---:|---:|---:|
| `DIRECT_PHYSICAL` | 224 | **348** (−100) | **522** (−6) | **791** (−265) |
| `RESOLVED_PHYSICAL` | 224 | 448 | 528 | **1045** (−11) |
| `DELAY_ONLY` | 224 | 448 | 528 | 1056 |
| `SPATIAL_ONLY` | 224 | **357** (−91) | 528 | **828** (−228) |
| `UNRESOLVED_IMAGE` | 224 | 448 | 528 | **1028** (−28) |
| `EQUALIZED_ORDER_SENSITIVITY` | 224 | 448 | 528 | **1045** (−11) |
| `PAIRING_DESTROYED` | 224 | 448 | 528 | 1056 |
### `a050_i050`

| arm | `C224` (224) | `C448_T` (448) | `C528_S` (528) | `C1056_ST` (1056) |
|---|---:|---:|---:|---:|
| `DIRECT_PHYSICAL` | 224 | **411** (−37) | 528 | **911** (−145) |
| `RESOLVED_PHYSICAL` | 224 | 448 | 528 | **1045** (−11) |
| `DELAY_ONLY` | 224 | 448 | 528 | 1056 |
| `SPATIAL_ONLY` | 224 | **425** (−23) | 528 | **996** (−60) |
| `UNRESOLVED_IMAGE` | 224 | 448 | 528 | **1042** (−14) |
| `EQUALIZED_ORDER_SENSITIVITY` | 224 | 448 | 528 | **1052** (−4) |
| `PAIRING_DESTROYED` | 224 | 448 | 528 | 1056 |
### `a098_i075`

| arm | `C224` (224) | `C448_T` (448) | `C528_S` (528) | `C1056_ST` (1056) |
|---|---:|---:|---:|---:|
| `DIRECT_PHYSICAL` | 224 | **444** (−4) | 528 | **947** (−109) |
| `RESOLVED_PHYSICAL` | 224 | **447** (−1) | 528 | **1021** (−35) |
| `DELAY_ONLY` | 224 | **447** (−1) | 528 | **1020** (−36) |
| `SPATIAL_ONLY` | 224 | 448 | 528 | 1056 |
| `UNRESOLVED_IMAGE` | 224 | **447** (−1) | 528 | **1021** (−35) |
| `EQUALIZED_ORDER_SENSITIVITY` | 224 | **447** (−1) | 528 | **1031** (−25) |
| `PAIRING_DESTROYED` | 224 | 448 | 528 | 1056 |

## The headline: full rank on C224 was a property of C224

Every arm reaches full column rank on the registered class `C224` at every anchor.
That is exactly why it must not be read as injectivity on the continuum.
Enrich the class and the rank deficiency appears:

| geometry | class | arm | rank / dimension | nullity | sigma_min+ |
|---|---|---|---|---:|---:|
| `a000_i020` | `C1056_ST` | `DIRECT_PHYSICAL` | 791 / 1056 | 265 | 3.577e-08 |
| `a000_i020` | `C1056_ST` | `EQUALIZED_ORDER_SENSITIVITY` | 1045 / 1056 | 11 | 2.098e-06 |
| `a000_i020` | `C1056_ST` | `RESOLVED_PHYSICAL` | 1045 / 1056 | 11 | 1.216e-07 |
| `a000_i020` | `C1056_ST` | `SPATIAL_ONLY` | 828 / 1056 | 228 | 1.031e-07 |
| `a000_i020` | `C1056_ST` | `UNRESOLVED_IMAGE` | 1028 / 1056 | 28 | 3.439e-08 |
| `a000_i020` | `C448_T` | `DIRECT_PHYSICAL` | 348 / 448 | 100 | 3.641e-08 |
| `a000_i020` | `C448_T` | `SPATIAL_ONLY` | 357 / 448 | 91 | 9.802e-08 |
| `a000_i020` | `C528_S` | `DIRECT_PHYSICAL` | 522 / 528 | 6 | 3.514e-08 |
| `a050_i050` | `C1056_ST` | `DIRECT_PHYSICAL` | 911 / 1056 | 145 | 4.005e-08 |
| `a050_i050` | `C1056_ST` | `EQUALIZED_ORDER_SENSITIVITY` | 1052 / 1056 | 4 | 1.555e-07 |
| `a050_i050` | `C1056_ST` | `RESOLVED_PHYSICAL` | 1045 / 1056 | 11 | 2.488e-07 |
| `a050_i050` | `C1056_ST` | `SPATIAL_ONLY` | 996 / 1056 | 60 | 1.074e-07 |
| `a050_i050` | `C1056_ST` | `UNRESOLVED_IMAGE` | 1042 / 1056 | 14 | 3.556e-08 |
| `a050_i050` | `C448_T` | `DIRECT_PHYSICAL` | 411 / 448 | 37 | 7.229e-08 |
| `a050_i050` | `C448_T` | `SPATIAL_ONLY` | 425 / 448 | 23 | 1.141e-07 |
| `a098_i075` | `C1056_ST` | `DELAY_ONLY` | 1020 / 1056 | 36 | 1.286e-07 |
| `a098_i075` | `C1056_ST` | `DIRECT_PHYSICAL` | 947 / 1056 | 109 | 4.067e-08 |
| `a098_i075` | `C1056_ST` | `EQUALIZED_ORDER_SENSITIVITY` | 1031 / 1056 | 25 | 2.030e-07 |
| `a098_i075` | `C1056_ST` | `RESOLVED_PHYSICAL` | 1021 / 1056 | 35 | 1.332e-07 |
| `a098_i075` | `C1056_ST` | `UNRESOLVED_IMAGE` | 1021 / 1056 | 35 | 4.981e-08 |
| `a098_i075` | `C448_T` | `DELAY_ONLY` | 447 / 448 | 1 | 2.556e-07 |
| `a098_i075` | `C448_T` | `DIRECT_PHYSICAL` | 444 / 448 | 4 | 7.786e-08 |
| `a098_i075` | `C448_T` | `EQUALIZED_ORDER_SENSITIVITY` | 447 / 448 | 1 | 3.783e-07 |
| `a098_i075` | `C448_T` | `RESOLVED_PHYSICAL` | 447 / 448 | 1 | 1.871e-07 |
| `a098_i075` | `C448_T` | `UNRESOLVED_IMAGE` | 447 / 448 | 1 | 1.112e-07 |

Answering the five questions this phase was authorized to ask:

1. **Does full rank on `C224` survive temporal enrichment?** No.
   Doubling the temporal resolution alone, holding the spatial factors fixed, is
   enough to expose a null space at `C448_T`:

   * `DIRECT_PHYSICAL` — 3 of 3 anchors: `a000_i020` 348/448 (nullity 100), `a050_i050` 411/448 (nullity 37), `a098_i075` 444/448 (nullity 4)
   * `RESOLVED_PHYSICAL` — 1 of 3 anchors: `a098_i075` 447/448 (nullity 1)
   * `DELAY_ONLY` — 1 of 3 anchors: `a098_i075` 447/448 (nullity 1)
   * `SPATIAL_ONLY` — 2 of 3 anchors: `a000_i020` 357/448 (nullity 91), `a050_i050` 425/448 (nullity 23)
   * `UNRESOLVED_IMAGE` — 1 of 3 anchors: `a098_i075` 447/448 (nullity 1)
   * `EQUALIZED_ORDER_SENSITIVITY` — 1 of 3 anchors: `a098_i075` 447/448 (nullity 1)

   The direct channel is the one that fails everywhere; which of the other arms
   follows it depends on the anchor, and `a098_i075` is the geometry where
   almost every arm loses a single dimension.

2. **Does spatial remapping become important on `C528_S`?** Yes.
   Enriching the spatial factors instead of the temporal ones:

   * `DIRECT_PHYSICAL` — 1 of 3 anchors: `a000_i020` 522/528 (nullity 6)

   Spatial enrichment is much gentler than temporal enrichment: the deficiency it exposes is confined to the direct channel and is a handful of dimensions, against the hundreds that temporal enrichment exposes. The operator resolves the declared spatial class far better than the declared temporal one, which is the same asymmetry the mechanism decomposition found from the other direction.

3. **Do near-null historical modes appear on `C1056_ST`?** Yes.

   * `DIRECT_PHYSICAL` — 3 of 3 anchors: `a000_i020` 791/1056 (nullity 265), `a050_i050` 911/1056 (nullity 145), `a098_i075` 947/1056 (nullity 109)
   * `RESOLVED_PHYSICAL` — 3 of 3 anchors: `a000_i020` 1045/1056 (nullity 11), `a050_i050` 1045/1056 (nullity 11), `a098_i075` 1021/1056 (nullity 35)
   * `DELAY_ONLY` — 1 of 3 anchors: `a098_i075` 1020/1056 (nullity 36)
   * `SPATIAL_ONLY` — 2 of 3 anchors: `a000_i020` 828/1056 (nullity 228), `a050_i050` 996/1056 (nullity 60)
   * `UNRESOLVED_IMAGE` — 3 of 3 anchors: `a000_i020` 1028/1056 (nullity 28), `a050_i050` 1042/1056 (nullity 14), `a098_i075` 1021/1056 (nullity 35)
   * `EQUALIZED_ORDER_SENSITIVITY` — 3 of 3 anchors: `a000_i020` 1045/1056 (nullity 11), `a050_i050` 1052/1056 (nullity 4), `a098_i075` 1031/1056 (nullity 25)

   `RESOLVED_PHYSICAL` is among them, so the full physical operator itself has a numerical null space once the model is rich enough.

4. **Does the delay-only/full equivalence survive once the direct spatial
   channel no longer trivially resolves the declared spatial class?** No.
   `DELAY_ONLY` is rank-deficient in 2 of the 12
   class–anchor combinations against `RESOLVED_PHYSICAL`'s 4, and the
   two arms' nullities differ wherever both are deficient. On the registered
   class the two were indistinguishable by rank; enrichment separates them.
   Note the direction: substituting the direct order's well-sampled n = 0
   spatial map onto every order is not a strict impoverishment, so `DELAY_ONLY`
   is sometimes the *better*-determined operator. It is a mechanism probe, not a
   physical measurement architecture, and this is a reminder of the difference.
5. **How do `sigma_min+`, operational rank and `T_rec` change with richness?**

| class | dimension | operational rank (median) | as a fraction | sigma_min+ | kappa+ |
|---|---:|---:|---:|---:|---:|
| `C224` | 224 | 201 | 0.897 | 1.635e-02 | 7.038e+05 |
| `C448_T` | 448 | 365 | 0.815 | 7.164e-05 | 1.799e+08 |
| `C528_S` | 528 | 441 | 0.835 | 2.871e-04 | 4.849e+07 |
| `C1056_ST` | 1056 | 770 | 0.729 | 1.332e-07 | 1.041e+11 |

   Operational rank rises with dimension but
   does not fall monotonically as a fraction of it, and `sigma_min+` drops
   by orders of magnitude per enrichment. The model gets more directions and
   determines a smaller share of them.

## Recoverable depth against class richness

Deepest retarded age (M) whose best-determined localized mode clears the
operational threshold at SNR_0 = 100.

| geometry | arm | `C224` | `C448_T` | `C528_S` | `C1056_ST` |
|---|---|---:|---:|---:|---:|
| `a000_i020` | `DIRECT_PHYSICAL` | 24.0 | 24.0 | 24.0 | 24.0 |
| `a000_i020` | `RESOLVED_PHYSICAL` | 68.0 | 68.0 | 72.0 | 72.0 |
| `a000_i020` | `DELAY_ONLY` | 80.0 | 80.0 | 80.0 | 80.0 |
| `a000_i020` | `SPATIAL_ONLY` | 24.0 | 24.0 | 24.0 | 24.0 |
| `a050_i050` | `DIRECT_PHYSICAL` | 60.0 | 60.0 | 60.0 | 60.0 |
| `a050_i050` | `RESOLVED_PHYSICAL` | 92.0 | 92.0 | 92.0 | 92.0 |
| `a050_i050` | `DELAY_ONLY` | 96.0 | 96.0 | 96.0 | 96.0 |
| `a050_i050` | `SPATIAL_ONLY` | 60.0 | 60.0 | 60.0 | 60.0 |
| `a098_i075` | `DIRECT_PHYSICAL` | 140.0 | 140.0 | 144.0 | 144.0 |
| `a098_i075` | `RESOLVED_PHYSICAL` | 152.0 | 152.0 | 156.0 | 156.0 |
| `a098_i075` | `DELAY_ONLY` | 160.0 | 160.0 | 160.0 | 160.0 |
| `a098_i075` | `SPATIAL_ONLY` | 140.0 | 140.0 | 144.0 | 144.0 |

Depth moves in 9 of 21 anchor–arm rows. Among the physical and mechanism arms it moves in 7 and never by more than 1 grid step of 4 M. The largest move on the whole table, 4 steps, belongs to `PAIRING_DESTROYED` at `a000_i020` — the nonphysical control, which is not a measurement architecture and whose depth is not a physical depth.
Every move appears at the spatial enrichment (C224 to C528_S, C448_T to C1056_ST) and none at the temporal one, which is the same asymmetry the rank table shows from the other side: temporal enrichment exposes null directions without extending reach, spatial enrichment extends reach without exposing many.

**Identifiability and historical reach are different questions, and this is the
cleanest demonstration of it in the program.** Over the same ladder the resolved
operator's rank fraction falls by up to 25.1% and
`sigma_min+` by five orders of magnitude, while depth moves by at most
1 grid step. Enriching the model exposes directions the
operator cannot determine; it barely changes how far back in retarded time the
operator can see. A rank statement is therefore not a depth statement, in either
direction, and neither is evidence for the other.

## Operator smoke comparison

| geometry | class | columns checked | dense vs matrix-free | adjoint |
|---|---|---:|---:|---:|
| `a000_i020` | `C224` | 48 | 0.000e+00 | 2.026e-14 |
| `a000_i020` | `C448_T` | 48 | 0.000e+00 | 4.890e-13 |
| `a000_i020` | `C528_S` | 48 | 0.000e+00 | 1.752e-14 |
| `a000_i020` | `C1056_ST` | 48 | 0.000e+00 | 5.445e-14 |
| `a050_i050` | `C224` | 48 | 0.000e+00 | 7.173e-14 |
| `a050_i050` | `C448_T` | 48 | 0.000e+00 | 3.048e-14 |
| `a050_i050` | `C528_S` | 48 | 0.000e+00 | 5.217e-14 |
| `a050_i050` | `C1056_ST` | 48 | 0.000e+00 | 3.910e-14 |
| `a098_i075` | `C224` | 48 | 0.000e+00 | 4.047e-14 |
| `a098_i075` | `C448_T` | 48 | 0.000e+00 | 9.199e-14 |
| `a098_i075` | `C528_S` | 48 | 0.000e+00 | 6.797e-14 |
| `a098_i075` | `C1056_ST` | 48 | 0.000e+00 | 3.240e-14 |

## Scope

Permits: statements about how the registered operator's identifiability
degrades under model enrichment on the three anchor geometries.
Forbids: any claim that any of these classes is the continuum; any statement
about geometries outside the three anchors; geometry mismatch, order leakage or
ML.

**Stop after E3D**, as authorized.

## Artifacts
`artifacts/tables/e3d_*.parquet`, `artifacts/gates/e3d_correctness_gates.json`,
`artifacts/provenance/E3D_ARTIFACT_MANIFEST.json`.
