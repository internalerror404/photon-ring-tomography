# R3A-QC return: C13 repair and fixed-detector quadrature

Status: **R3A_QUADRATURE_NOT_YET_QUALIFIED**  
Refinement route: **R3A_QC_REFINEMENT_BUDGET_OR_CAPABILITY_BLOCKED**  
Constructor and units: **CORRECT**

These are three findings, not one. The corrected constructor and its units are right; the quadrature built on the existing ray sampling is not accurate enough for the newly registered budget; and the refinement that would fix it does not fit the authorized cap. R3B stays blocked.

## 1. Corrections accepted

Two statements in the R3A return were wrong and are withdrawn.

**The spacings are commensurate.** 50/125, 20/249 and 14/699 M are rational and share the divisor h = 2/290085 M as 58017h, 11650h and 2905h. The claim of mathematical impossibility from the three pitches alone is withdrawn. What remains true is only that a uniform aligned grid at that pitch is impractical, and no such grid was built.

**Detector refinement is not quadrature refinement.** Averaging a field over detector cells genuinely loses information, `I_ray - I_detector = sigma^-2 ||f - P_D f||^2 >= 0`, and a finer detector is a different measurement that may legitimately recover some of it. Calling that whole difference an artefact was too strong. The invariance that does deserve a machine-precision test is subdivision of cells carrying the same field at a fixed detector, and that is now canary P6, passing at 1e-12 on a fixture and on an archived order.

The old 1e-12 detector-pitch result stays FAIL_AS_WRITTEN and is retired prospectively, not relaxed into a pass. The new 1e-3 budget is a different criterion for a different quantity, registered before the first Q2 outcome existed.

## 2. C13, and what the repair actually is

Both generators are traced rather than inferred. `aart.lensingbands.grid_mask` uses `linspace(-lims, lims, round_up_to_even(2*lims/dx))` and the Schwarzschild cross-tracer uses `linspace(-lim, lim, ceil(2*lim/dx))`. Both rules reproduce every observed node count across all 63 archived maps, so the samples are endpoint-inclusive nodes on a declared finite domain, not cell centres. Both axes were audited separately; every axis is uniform and alpha and beta share a spacing in every archived map, now measured rather than assumed.

The stored weight matches the realized geometry in 16 of 63 maps, worst error 2.0304% in cell area, across both generators.

The repair is not `delta_alpha**2`. The adopted measure is the dual cell of each node clipped to the declared domain: rectangular, three distinct areas per map, half-width along an edge and a quarter at a corner, tiling the declared screen exactly. Full centre cells are implemented and measured but not adopted, because they integrate a domain that grows as the pitch shrinks. The legacy nominal square is kept for replay and never stands in for the corrected measure.

At the reference geometry, the correction splits into causes the audit keeps apart:

| order | legacy total | interior weight | domain boundary | corrected | net | band-edge area share |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 2495.5200 | +0.0000 | -30.0000 | 2465.5200 | -1.2022% | 1.49% |
| 1 | 54.5984 | +0.4394 | -0.0000 | 55.0378 | +0.8048% | 9.40% |
| 2 | 1.6716 | +0.0048 | +0.0000 | 1.6764 | +0.2863% | 57.84% |

Order 0's core spacing is exactly 0.4 M, so its interior term is identically zero and its whole -1.20% comes from boundary clipping where the valid band reaches the declared screen edge. That effect was invisible to the interior-pitch analysis and it is the larger one for that order.

Of nineteen files that read the stored weight, only `geometry/sampling.py` carries it into an operator, and it preserves each order's *total* solid angle rather than any ray's footprint. Six quantities are now kept distinct in the records: requested pitch, realized nodes, cell edges, geometric area, validity mask, and effective quadrature weight after subsampling.

## 3. What C13 does and does not do to R2

The certified bound reproduces the ruling exactly. With rays, masks, source metric, target and nuisance spaces and sigma all fixed and only the interior weights changed, r in [1.000000000, 1.008048257] gives

| direction | certified interval | adopted-measure interval (not certified) |
| --- | --- | --- |
| 1 | [1.437164901, 1.442936648] | [1.428500313, 1.442936648] |
| 2 | [1.345873269, 1.351278382] | [1.337759072, 1.351278382] |
| 3 | [0.806280438, 0.809518512] | [0.801419417, 0.809518512] |

Exactly 2 directions stay above rho = 1, and the conditional trace lies in [7.198318, 7.256252].

Recorded beside it, and explicitly not certified, is the wider interval the adopted measure implies through each order's total, r in [0.987978457, 1.008048257]: still exactly 2 directions above rho, none straddling it, trace in [7.111783, 7.256252]. It is uncertified because clipped dual cells are not uniform within an order, so the reweighting they induce through `stratified_subsample` is only approximately uniform. It widens the interval and does not change the count.

R2 stays accepted for its frozen legacy measure. It is not thereby a revalidated corrected-measure physical result, and no replay was repeated to erase a defect label.

## 4. The fixed-detector comparison, and why it fails

D026: alpha and beta in [-25.0, 25.0] M, pitch 0.4 M, 125x125 cells, the eight inherited observer times, sigma 0.011341986814407566 held fixed. The detector does not move; the rays refine into it.

One absolute clock replaced three. Every archived map had recentred its delays on its own latest order-0 arrival, so the three references differ by up to 0.69 M and the profiles were never on a comparable origin. The core reference is adopted; under it the fine profile's earliest arrival is -0.2333 M, recorded signed and not clipped.

| pair | order | worst field response | area | mask symmetric difference |
| --- | --- | --- | --- | --- |
| coarse->core | 0 | 9.805e-02 **fail** | 4.282e-03 **fail** | 5.635e-03 **fail** |
| coarse->core | 1 | 2.386e-01 **fail** | 2.822e-03 **fail** | 5.397e-02 **fail** |
| coarse->core | 2 | 9.019e-01 **fail** | 4.572e-03 **fail** | 3.450e-01 **fail** |
| core->fine | 0 | 5.023e-02 **fail** | 1.887e-03 **fail** | 2.690e-03 **fail** |
| core->fine | 1 | 7.755e-02 **fail** | 4.906e-04 pass | 2.786e-02 **fail** |
| core->fine | 2 | 3.859e-01 **fail** | 3.820e-03 **fail** | 1.920e-01 **fail** |

17 of 18 checks fail against the 1e-3 budget. The diagnosis is single: a node is either inside a region or outside it, so the represented boundary moves in whole cells and the error falls like the spacing. The measured convergence orders are 0.26 to 1.62, clustered near one.

The response metric is far more sensitive than the totals, exactly as the ruling anticipated. Order 0's areas agree to 0.19% while its responses differ by 5.0%: a boundary cell that flips contributes its whole amplitude to an L2 difference and almost nothing to a sum. A scalar total would have concealed it.

## 5. The authorized refinement cannot reach the criterion

No ray was traced. Before planning a batch, the requirement was computed from the observed rates and compared with the cap of 250000 new evaluations:

| order | metric | late error | required spacing (M) | uniform | adaptive lower bound |
| --- | --- | ---: | ---: | ---: | ---: |
| 0 | response | 5.023e-02 | 0.00347 | 828x cap | 0.135x cap |
| 0 | mask | 2.690e-03 | 0.0795 | 1.57x cap | 0.00589x cap |
| 0 | area | 1.887e-03 | 0.117 | 0.722x cap | 0.00399x cap |
| 1 | response | 7.755e-02 | 0.00274 | 29.3x cap | 0.0941x cap |
| 1 | mask | 2.786e-02 | 0.00122 | 147x cap | 0.21x cap |
| 1 | area | 4.906e-04 | already met | - | - |
| 2 | response | 3.859e-01 | 7.73e-05 | 1.12e+03x cap | 3x cap |
| 2 | mask | 1.920e-01 | 1.99e-05 | 1.68e+04x cap | 11.7x cap |
| 2 | area | 3.820e-03 | 5.68e-05 | 2.07e+03x cap | 4.09x cap |

Uniform refinement misses by up to 1.68e+04 times the cap. Even an idealized boundary-adaptive lower bound -- which ignores the required independent shifted holdout and every overhead -- still misses by 11.7 times on order 2. Orders 0 and 1 would fit that idealized model; order 2 does not, and the criterion is required of every order.

This is a budget blocker, not a capability one. `aart.raytracing.raytrace` passes its point array straight to `rt.rt`, which accepts an arbitrary screen point set; only the generator insists on a uniform grid. The pinned backend would do the work. There is no authorized allowance large enough to ask it for, so the allowance was not spent on a refinement that provably cannot qualify.

## 6. The cheapest identified route, not adopted

The deficit is first order because the band boundary is represented by binary node classification. Fractional cell coverage at that boundary would change the order rather than the sample count, and the information already exists: `aart.lensingbands.hulls` returns the inner and outer band curves that `grid_mask` already tests membership against. Cutting boundary cells against those curves needs no new rays at all.

What is not claimed is that it would pass. The hulls are themselves polygons from a finite number of marks on the critical curve, sixty here, so their own resolution would become the limiting error and has not been measured. Changing the representation is not a bounded refinement of the existing one and is outside what ruling 026 authorizes, so it is reported and not adopted.

## 7. Boundary, domain and coverage

Order 0's valid rays sit on the declared screen edge in all three profiles, so emission beyond 25 M is **absent from the archive and not certified zero**. Orders 1 and 2 have no valid node on their declared boundary, so outside their domains order-n emission is certified zero by the band hull. Order 2's fine profile declares a 6 M half-width against 7 M for coarse and core; the band fits inside both, so no band is cropped, but the domains differ and that is recorded.

Against the archived padded screen, D026 crops nothing the archive holds: every profile and order is captured at a fraction of 1.000000 or better, because under the corrected measure an order's cells stop at its declared domain and the older padding covered ground the maps never sampled.

## 8. Governance

The preexecution freeze was committed at `a2620f179317` with every frozen file clean in git, before any Q2 output existed; the runner verifies all 20 hashes and refuses a freeze written over uncommitted files. Completion is fail-closed over 19 conditions.

Constructor and units: **CORRECT** (13 passed in 4.21s). Quadrature: **R3A_QUADRATURE_NOT_YET_QUALIFIED**. These are recorded separately; neither substitutes for the other.

Prerequisites: the whole test suite was run to completion for this record -- 552 passed in 44.10s, return code 0 -- so nothing is inferred from a subset and no prerequisite is skipped.

No archive was rewritten, no operator rebuilt, no endpoint recomputed or rescaled, no tolerance adjusted after a result, no target spectrum or operational count inspected, and no paid resource acquired. R3B is not authorized and was not begun.

Two decisions are needed before this can move: whether to authorize the fractional-coverage representation, and if so what accuracy to require of the hull polygons themselves.
