# Fractional coverage return: H0, H1 and H2

Status: **R3A_FRACTIONAL_QUADRATURE_NOT_YET_QUALIFIED**  
Blockers: **MISSING_TRANSFER_SUPPORT, TRANSFER_ACCURACY_UNQUALIFIED, HULL_ACCURACY_UNQUALIFIED, BUDGET_EXHAUSTED**

| component | status |
| --- | --- |
| kernel and units | **CORRECT** |
| hull geometry | **UNQUALIFIED** |
| transferred field accuracy | **UNQUALIFIED** |
| total quadrature | **NOT_YET_QUALIFIED** |
| governance | **COMPLETE_WITH_DISCLOSED_REGISTRATION_GAP** |

R3B is not authorized and was not begun. No target spectrum, operational count or estimator was inspected.

## 1. Corrections accepted

**"Provably cannot qualify" is withdrawn.** The 11.7x figure came from a rate fitted to two comparisons plus a cost model for boundary refinement. It is a projection under that model, not a lower bound over all representations, and it is now labelled `MODEL_BASED_BINARY_RASTER_COST_PROJECTION`. The numbers stand; the universal wording does not. The qualification matters precisely because fractional coverage changes the representation the extrapolation rested on.

**The overlap is the triple intersection, not a scaled fraction.** `O[d,p] = |D_d ^ C_p ^ Omega_n|` is what is implemented. The whole-cell emitting fraction is computed as a diagnostic and never used as a weight. Canary F1 is the reviewer's counterexample as a standing test: the clipped overlap puts (0.2, 0) across two half-width pixels and the substitution puts (0.1, 0.1) -- identical totals, different image. A conservation check alone would have passed the wrong construction.

**Geometry is not availability is not accuracy.** Those three are separated throughout, and the finding below is that the second is the binding one.

## 2. H0: the kernel, the hulls, and what the hulls do not cover

`tests/revision_v4_1/test_polyclip.py` and `tests/revision_v4_1/test_fractional_027.py`: 22 passed in 0.69s. The clipping kernel integrates the vertical slice length with breakpoints at vertices, at grid lines in x, and wherever the boundary crosses a grid line in y, so midpoint times width is exact -- including across vertical edges and repeated vertices. Canaries cover non-convex polygons split into two components by one cell, holes that stay empty, slivers of area 1e-9 that are kept, and invariance under orientation, vertex rotation and grid refinement.

Hull provenance is verified rather than asserted: regenerating the level-60 hulls from the pinned equations reproduces the archived arrays bitwise for every order ({'0': True, '1': True, '2': True}). Topology is valid in every profile -- simple boundaries, consistent nesting -- and the AART conventions are preserved: the direct-order outer boundary is the screen square, its inner boundary is the apparent horizon, and the photon-ring boundaries are radial scalings of the critical-curve directions.

**The three archived profiles carry the same hulls.** All were built at npointsS=60, so the fractional band areas are identical across them (2475.2788, 71.9615, 2.0029 M^2) and the archive does not exercise hull refinement at all. H1 had to generate new levels.

Every fragment with positive geometric area is classified against the transfer data that exists for it. Area shares:

| profile | order | supported | outside annulus | solver unresolved | no data |
| --- | --- | ---: | ---: | ---: | ---: |
| coarse | 0 | 0.9911 | 0.0000 | 0.0000 | 0.0089 |
| coarse | 1 | 0.7595 | 0.2075 | 0.0135 | 0.0195 |
| coarse | 2 | 0.7416 | 0.0533 | 0.0494 | 0.1557 |
| core | 0 | 0.9957 | 0.0000 | 0.0000 | 0.0043 |
| core | 1 | 0.7621 | 0.2123 | 0.0152 | 0.0104 |
| core | 2 | 0.8058 | 0.0587 | 0.0547 | 0.0808 |
| fine | 0 | 0.9978 | 0.0000 | 0.0000 | 0.0022 |
| fine | 1 | 0.7642 | 0.2135 | 0.0172 | 0.0050 |
| fine | 2 | 0.8251 | 0.0687 | 0.0682 | 0.0380 |

This is the finding that governs everything after it. **Order 0 is essentially solved by fractional coverage**: its geometric band is profile-independent and its supported share converges 0.991, 0.996, 0.998. **Orders 1 and 2 are not, and not because of the hull.** About 21% of order 1's band area lies outside the declared emission annulus and 1.5% is solver-unresolved; order 2 runs 5-7% and 5-7%. Those boundaries are properties of solved rays, not of any curve, so a perfect hull cannot resolve them. Masked zeros, failed solves and unsampled exteriors are held in three separate categories and none is treated as zero emission.

## 3. H1: the hull hierarchy

Levels [60, 120, 240, 480], each re-running the pinned root equations at more arclength marks -- 5 solves per direction, so new vertices are new boundary solutions and not points inserted along old edges. 18000 boundary solves of the 30000 authorized; zero transfer rays.

| pair | order | band symdiff | boundaries | hull-only response | angular quadrature |
| --- | --- | ---: | ---: | ---: | ---: |
| 60->120 | 0 | 4.993e-06 | 4.993e-06 | 9.709e-05 | 8.21e-13 |
| 60->120 ** | 1 | 1.249e-03 | 1.249e-03 | 2.910e-03 | 2.13e-10 |
| 60->120 ** | 2 | 3.025e-02 | 3.025e-02 | 5.978e-03 | 5.62e-09 |
| 120->240 | 0 | 1.225e-06 | 1.225e-06 | 2.383e-05 | 7.62e-13 |
| 120->240 ** | 1 | 3.065e-04 | 3.065e-04 | 6.902e-04 | 2.17e-10 |
| 120->240 ** | 2 | 7.505e-03 | 7.505e-03 | 1.361e-03 | 5.31e-09 |
| 240->480 | 0 | 3.034e-07 | 3.034e-07 | 5.887e-06 | 8.80e-13 |
| 240->480 | 1 | 7.592e-05 | 7.592e-05 | 1.720e-04 | 2.17e-10 |
| 240->480 ** | 2 | 1.864e-03 | 1.864e-03 | 3.336e-04 | 5.45e-09 |

Budgets: band 2.5e-04, boundaries 2.5e-04, hull-only response 2.5e-04, all taken verbatim from the ruling. The angular-quadrature column is a self-check against the 1e-06 aggregate budget: the sample set contains every vertex angle, which makes the swept-area integration exact on the polygons themselves, so only radius crossings contribute and doubling the uniform fill measures what they leave.

Accepted level: **None** -- no level reached two successive qualifying pairs.

Order 0 qualifies at every pair. Order 1 qualifies at 240->480 (band 7.6e-5, response 1.7e-4) but its previous pair misses at 3.1e-4, so it has one qualifying pair and not two. Order 2 misses at 1.9e-3 on the band criterion.

The band symmetric difference falls by almost exactly a factor of four per doubling in every order, so the boundary is converging second order and the ladder is behaving. What it needs is more levels than the allowance holds, and that is a projection under the observed rate rather than a bound:

| order | ratio per doubling | level needed for two successive pairs | further boundary solves |
| --- | ---: | ---: | ---: |
| 0 | 4.04 | 960 | 9,600 |
| 1 | 4.04 | 960 | 9,600 |
| 2 | 4.03 | 3840 | 67,200 |

Against 12,000 remaining solves, and before the two independent checks that promotion also requires. Order 2 is the binding one. The band criterion is severe for a thin annulus by design -- a small radial shift moves a large share of a band two to three cells thick -- and it is the criterion the ruling chose precisely so that inner and outer errors cannot compensate. Its response counterpart is much closer: order 2's hull-only response change is 3.3e-4 against a 2.5e-4 budget.

Orders 0 and 1 alone would fit the remaining allowance at level 960, but promotion also needs the shifted-sample and tighter-root checks at the accepted level, which would not fit, and the criterion is required of every order in any case. So the allowance was not spent on a level that could not be promoted. What would settle it is a larger boundary-solve authorization -- roughly 220,000 including the checks at level 3840 under the observed rate -- or a decision that the band criterion should be read differently for a band only two to three cells thick.

Independent checks:

- not run: no level was accepted, and the checks are defined at an accepted level. Not run is recorded as not run, not as a pass.

The shifted check moves the sample locations half a step along the generator's own arclength parameter with the endpoints preserved, so it is a different set of boundary solves and not a resampling of the same polygon.

## 4. H2: transfer and emission-boundary accuracy at a fixed hull

The hull is held at level 480, so anything that moves is the ray sampling and the emission-validity boundary. Detector, observer times, sigma and the common absolute clock are the ones already pinned in the Q2 freeze. Zero transfer rays: the finding did not require any.

| pair | order | worst field | relative | active area | supported area |
| --- | --- | --- | ---: | ---: | ---: |
| coarse->core | 0 | transferred:g^3*cos20 | 6.436e-02 ** | 0.000e+00 | 4.596e-03 |
| coarse->core | 1 | transferred:g^3*sin20 | 2.376e-01 ** | 1.105e-14 | 3.445e-03 |
| coarse->core | 2 | transferred:g^3*cos20 | 8.551e-01 ** | 9.795e-14 | 7.623e-02 |
| core->fine | 0 | transferred:g^3*cos20 | 2.523e-02 ** | 0.000e+00 | 2.093e-03 |
| core->fine | 1 | transferred:g^3*sin20 | 7.755e-02 ** | 1.579e-15 | 2.827e-03 |
| core->fine | 2 | transferred:g^3*cos20 | 3.827e-01 ** | 2.101e-13 | 2.294e-02 |

Component budget 5e-04, total 1e-03. Worst unsupported area fraction across all profiles and orders: 0.2618.

The active area -- the geometric band inside the aperture -- is now profile-independent by construction, because the hull no longer moves. What still moves is the supported area, and it moves because the set of rays with valid transfer data changes with the sampling. That is the residual the fractional representation cannot remove on its own.

## 5. What blocks a full qualification

`MISSING_TRANSFER_SUPPORT`. Fractional coverage gives an exact geometric band, and for order 0 that is nearly the whole answer. For orders 1 and 2 a fifth to a quarter of the band area has no valid transfer data behind it, because the emission-annulus contour and the solver-failure region cut through cells and neither is a hull. Refining the hull to machine precision would not move those numbers.

What would: locating the `r_source = 50` contour and the solver-validity boundary by targeted root solves along screen rays, using the same pinned equations. Those are transfer-ray evaluations and would count against the 250,000 carried forward, which is ample -- a contour needs thousands, not millions. It is a different construction from the one authorized here, so it is reported and not attempted.

`HULL_ACCURACY_UNQUALIFIED`: the hull ladder did not reach two successive qualifying pairs within the authorized boundary-solve allowance. The measured sequence is above; no tolerance was relaxed to close it.

## 6. R2: the permitted readback, and a claim of mine it withdraws

The readback was run within its permitted scope: an inventory of the weights the sampler actually produces. No operator was built, no Fisher matrix formed, no SVD run and no target column touched. The same seed retains the same rays under both measures, verified ray by ray, and both draws go through the same rescale and common-count trimming.

| order | rows | per-order total ratio | row ratios |
| --- | ---: | ---: | --- |
| 0 | 1536 | 0.987978457 | [0.500081210, 1.000162421] |
| 1 | 1536 | 1.008048257 | [1.008048257, 1.008048257] |
| 2 | 1536 | 1.002863277 | [1.002863277, 1.002863277] |

**The reviewer was right that a per-order total does not bound every row, and the gap is not small.** Order 0's total ratio is 0.987978 while its row ratios span a factor of two: rays whose cells sit on the declared screen edge get half-width or quarter cells, so their individual weights halve while interior rays are unchanged. Over all rows r lies in [0.500081210, 1.008048257], which is wider than any per-order total.

| direction | certified interval from the row bound |
| --- | --- |
| 1 | [1.016311573, 1.442936648] -- above rho |
| 2 | [0.951753398, 1.351278382] -- **straddles rho** |
| 3 | [0.570172664, 0.809518512] -- below rho |

So the count certified by this bound is 1, not two: direction 2 is undetermined. **I withdraw the reading I recorded in Q1** that the adopted measure's indicative interval still gave exactly two directions above rho with none straddling: that was computed from per-order totals, which the row inventory now shows do not bound the rows. The bound is sufficient rather than tight, so this does not say the count changes -- it says the count is not certified, and the status is `ROW_BOUND_DOES_NOT_SEPARATE_RHO`.

The certified interior-pitch bound from ruling 026 is untouched and still gives two, under its own stated assumptions. R2 remains accepted under its frozen legacy measure; nothing here recomputes or replaces it.

## 7. Governance

**Preexecution registration was not satisfied for H0 and H1.** this record was written after H0 and H1 ran, so it is an input record and not a preexecution registration for those stages. Every tolerance used is taken verbatim from ruling 027 and none was chosen or changed after seeing a result, but the level ladder, the angular sampling and the decision rule were committed after their first execution. Under the ruling's own H2 launch clause the H1 outcome is therefore reported as an explicitly separated diagnostic rather than a registered qualification. re-running H1 under a registered freeze would spend a second full boundary-solve allowance on an identical computation, and the ruling has already directed that a wasteful run must not be performed merely to justify a record.

The gap does not change this return's outcome: the hull geometry is **UNQUALIFIED** on its own measurements, so nothing here rests on treating an unregistered run as a qualification. H2 was run at the finest measured level under the ruling's explicitly-separated-diagnostic clause and is labelled as such. If the reviewer wants the geometry ladder itself registered before it is believed, that has to come with a boundary-solve allowance large enough to reach a qualifying level, since the current one does not.

Budget: 18000 of 30000 boundary solves; 0 transfer rays of the 250000 carried forward; no paid resources.

Completion is fail-closed over 17 conditions with 0 failed and 0 unrecorded. Whole suite: 574 passed in 107.58s (0:01:47), return code 0.


No archive rewritten, no operator rebuilt, no endpoint recomputed or rescaled, no tolerance adjusted after a result, no geometry added, no paid resource acquired. R3B remains unauthorized.
