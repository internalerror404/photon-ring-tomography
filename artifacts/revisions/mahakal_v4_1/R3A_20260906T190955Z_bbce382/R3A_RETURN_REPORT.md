# R3A return: common-sky construction and correctness

Status: **R3A_CONSTRUCTION_BLOCKED**

Geometry a050_i050, orders [0, 1, 2], run `R3A_20260906T190955Z_bbce382`, commit at freeze `bbce3822bea4`.

The construction is built and its correctness canaries pass. It is returned blocked, not delivered, because the registered convergence criterion fails for two of three orders and because the audit that diagnosed the failure turned up a defect in the archived ray maps that has to be adjudicated before any common-sky information is compared to anything. Nothing has been retuned to make either go away: the tolerance is unchanged, and no operator, weight or archived endpoint has been touched.

## 1. What was built

One detector grid, 2540 x 2520 = 6400800 cells at pitch 0.02 M, spanning alpha [-25.4, 25.4] and beta [-25.0, 25.4]. The field of view is the union of every valid ray cell plus a declared pad; the pitch is the finest order's own cell. Both were fixed from geometry before any target quantity existed, and neither was revised afterwards.

Each order is placed on that grid by conservative area overlap: a ray cell and a detector cell are both axis-aligned rectangles, so their intersection is a product of interval intersections and is exact. Invalid rays are masked out, never interpolated into signal. Area that leaves the field of view is measured, not dropped quietly.

The cross-order time origin was verified rather than assumed: `coordinate_time + delay` is one constant across every ray of every order, with a measured drift of 0.000e+00 M between orders.

Two acquisition models are specified and kept apart, because they answer different questions and do not share a covariance: `POSTPROCESSING_INHERITED_NOISE`, where `C_sky = L C L^T` and information must contract, and `SINGLE_SKY_DETECTOR_NOISE`, where the orders are summed on the screen first and noise is assigned once afterwards. No positive-semidefinite ordering is asserted between the second and the ideal order-labeled stack, and no telescope feasibility claim is made for either.

## 2. The registered convergence criterion fails

Registered before any refinement ran: relative change in the declared-field whitened information proxy between successive detector pitches, below 1e-12. The refinement ladder is [4, 2, 1, 0.5, 0.25, 0.125, 0.0625] times each order's ray pitch.

| order | ray pitch (M) | last pair | converged | deficit at finest pitch | ceiling respected |
| --- | --- | --- | --- | --- | --- |
| 0 | 0.4 | 1.110e-15 | yes | -9.437e-15 | yes |
| 1 | 0.08 | 1.410e-03 | **no** | -8.644e-03 | yes |
| 2 | 0.02 | 1.004e-02 | **no** | -1.219e-02 | yes |

The first R3A run stopped the ladder at the ray pitch itself and so compared two pitches that both still straddled ray cells. It could not have met its own criterion whatever the construction did. Extending the ladder below the ray pitch makes the criterion harder to satisfy, not easier, and it is the extension that lets order 0 reach it. Orders 1 and 2 still do not.

The substantive canary behind that criterion does pass. In every order the proxy is monotone non-decreasing under refinement and never passes the ray-level ceiling -- the value a detector that fully resolved the rays would return. Refinement recovers information; it does not manufacture it (`no_information_manufactured_by_quadrature_refinement`: True).

## 3. Why it fails, measured rather than argued

The overlap arithmetic is exact. The proxy is inexact only where a detector cell straddles two ray cells, which needs the detector lattice to be commensurate with the ray lattice. Two independent things break commensurability here, so each was switched on alone.

Relative deficit against the ray-level value, at the order's own pitch:

| order | stored footprint, shared origin | realized footprint, shared origin | realized footprint, lattice-aligned origin |
| --- | --- | --- | --- |
| 0 | -9.074e-03 | -9.074e-03 | -9.770e-15 |
| 1 | -2.980e-02 | -2.155e-02 | -1.887e-14 |
| 2 | -1.760e-01 | -1.401e-01 | +9.548e-15 |

Give the detector the order's own footprint and its own origin and the same overlap rule reproduces the ray-level value to about 1e-14 at every pitch tested, in all three orders. The error in the shared grid is lattice misalignment, not the overlap rule. Canary C12 holds that conclusion in the test suite.

That is also why it cannot simply be fixed by choosing a better shared pitch. The three realized spacings are 0.4, 0.0803212851406 and 0.0200286123033 M -- 50/125, 20/249 and 14/699. They are mutually incommensurate at any feasible detector pitch, so **no single uniform Cartesian detector is exact for more than one order at a time**. At the natural pitch the resulting loss is not order-neutral: it runs 0.9%, 3.0% and 17.6% by order. That is a beat between two discretizations, not a physical compression loss, and it falls hardest on exactly the order comparison R3B would be asked to make. Proceeding to R3B on this grid would compare an artifact.

## 4. Defect found in the archived ray maps

Diagnosing the above required comparing the stored solid angle per ray against the grid it was measured on. They disagree.

`build_raymaps.py` stores `pixel_area = dx**2`, the cell size AART was *asked* for. AART lays `npoints` samples across the band, so the realized spacing is `span/(npoints-1)`, which equals `dx` only when the division comes out even. It does so in 2 of 9 profile/order combinations (coarse_n1, core_n0).

| profile / order | points per axis | nominal dx | realized spacing | realized/stored cell area |
| --- | --- | --- | --- | --- |
| coarse_n0 ** | 64 | 0.8 | 0.7936507937 | 0.984189972 (-1.5810%) |
| coarse_n1 | 126 | 0.16 | 0.16 | 1.000000000 (+0.0000%) |
| coarse_n2 ** | 350 | 0.04 | 0.04011461318 | 1.005738869 (+0.5739%) |
| core_n0 | 126 | 0.4 | 0.4 | 1.000000000 (+0.0000%) |
| core_n1 ** | 250 | 0.08 | 0.08032128514 | 1.008048257 (+0.8048%) |
| core_n2 ** | 700 | 0.02 | 0.0200286123 | 1.002863277 (+0.2863%) |
| fine_n0 ** | 250 | 0.2 | 0.2008032129 | 1.008048257 (+0.8048%) |
| fine_n1 ** | 500 | 0.04 | 0.04008016032 | 1.004012032 (+0.4012%) |
| fine_n2 ** | 1200 | 0.01 | 0.01000834028 | 1.001668752 (+0.1669%) |

The worst case is 1.5810% in cell area. The error is small, but it is order-dependent and profile-dependent, and it enters the whitened row as `sqrt(dOmega)`, so it is a differential miscalibration between image orders -- the one kind an order-resolved experiment cannot absorb. In the core profile it is 0.0000%, +0.8048% and +0.2863% for orders 0, 1 and 2, biasing order-to-order comparisons by roughly 0.4% and 0.14% in amplitude.

No existing gate catches it. `run_s0_backend_canary.py` compares the stored total against `metadata['dx']**2`, which is where the stored value came from, so the check is satisfied by construction. `run_g7b_field_convergence.py` explicitly marks `pixel_area` as `expected_to_differ` between profiles and excludes it.

Nothing was repaired. No operator, weight, table or archived endpoint has been altered, and no endpoint is claimed to move. This is reported as a new defect candidate for the reviewer to number and disposition, alongside C01-C12.

## 5. What is not proposed

The registered tolerance stands at 1e-12 and was not relaxed after the failure. No replacement criterion has been adopted. Three routes exist and each has a measured cost; the choice belongs to the reviewer, and none is applied here.

1. **Per-order aligned detectors.** Exact to 1e-14, as measured above, but it abandons the single common sky that R3A was asked to build.

2. **A shared grid with a declared, measured discretization error.** Keeps the common sky and states the deficit as a known bias, but the bias is order-dependent at the percent level and would have to be carried into every downstream comparison.

3. **A detector coarse relative to the rays, converged in the ray sampling instead.** Physically the right ordering, and the coarse, core and fine profiles exist for this geometry. It was measured and it does not converge either at present: the valid lensing-band area itself still moves between profiles (order 0: 2554.88, 2495.52, 2465.40 M^2), so the ray sampling is not converged at the band edge and the quadrature defect above contaminates the comparison.

Route 3 cannot be assessed honestly until the defect in section 4 is dispositioned, which is the main reason this return is blocked rather than merely incomplete.

## 6. Correctness canaries

`tests/revision_v4_1/test_r3a_construction.py`: 15 passed in 3.78s.

- **C1** registration uses screen coordinates, not equal counts
- **C2** invariance to independent input row permutations
- **C3** flux conservation with explicit boundary accounting
- **C4** single-sky all-order total flux equals the sum of orders
- **C5** detector refinement converges on the real tiled geometry, on a lattice-aligned grid
- **C5b** the two noise models are recorded as different, with no ordering asserted between them
- **C6** block forward and adjoint consistency
- **C7** inherited-noise postprocessing contracts information
- **C7b** identity mixing is an exact re-expression
- **C8** detector noise is assigned once, not once per order
- **C9** one geometry-wide time origin, verified from the raw maps
- **C9b** delay is non-negative and increases with image order
- **C10** stored pixel_area is checked against the realized grid spacing, so no construction can adopt one silently
- **C11** refinement approaches the ray-level ceiling and never passes it: no information manufactured by quadrature
- **C12** the same overlap rule is exact to machine precision on a commensurate lattice, which locates the deficit

C10, C11 and C12 are new in this run. C10 measures the quadrature discrepancy and fails if it silently disappears from the maps, because a repair is something to record and re-review rather than to inherit. C11 is the ceiling check. C12 is the exactness proof on a commensurate lattice that entitles section 3 to its conclusion.

## 7. Localization overlay, carried forward from review 025

The two localization deliverables were produced under the corrected interpretation and are unchanged by this run:

- `artifacts/revisions/mahakal_v4_1/LOC025_20260906T184213Z/localization_interpretation_overlay.md` sha256 `01d2c66b8b81e771`
- `artifacts/revisions/mahakal_v4_1/LOC025_20260906T184213Z/saved_mode_physical_localization.json` sha256 `2274967aab041d22`

The Cholesky coordinate groups are recorded as `CHOLESKY_COORDINATE_GROUP_DIAGNOSTIC`, not as a physical epoch partition. The withdrawn readings stay withdrawn.

## 8. Scope

Delivered: the acquisition specification, the constructor and its canaries, the convergence study, the commensurability diagnosis and the input freeze. Not done, and not started: any common-sky target spectrum, any target-spectrum sweep, any new source bank, any nuisance enrichment, any reconstruction estimator, any submission freeze, and any R3B information comparison. Target column selection is untouched at the accepted 72.

Returned as **R3A_CONSTRUCTION_BLOCKED**, pending a disposition on the quadrature-weight defect and a decision on the convergence criterion.
