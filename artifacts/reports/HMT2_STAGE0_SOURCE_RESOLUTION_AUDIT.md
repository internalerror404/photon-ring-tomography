# HMT-2 stage 0 — source object and resolution audit

Freeze `HMT2_STAGE0_SOURCE_OBJECT_AND_RESOLUTION_AUDIT_V0`, run `HMT2_STAGE0_AUDIT`.
Ray map imported: false. Operator constructed:
false. 169 sources,
3 nested grids, 2 source classes,
2438 s.

## 1. The question

HMT-1 declared a source model and an evaluation grid separately and never
checked the contract between them. Its sealed main then failed on a truth whose
two hotspots sat 0.34 log-radial cells apart with sub-cell widths: the grid
could not separate them, the extractor reported the blend, and the reference
resolved the dominant one. Nothing was broken. Nobody had asked whether these
families put resolvable features on this grid.

Stage 0 asks. No ray map is imported and no operator is constructed, so nothing
below is an inverse-problem result, and none of it can be read as one.

## 2. What the sources actually contain

Fractions of (truth, age) states over the six declared families, classified by
topographic prominence at the frozen fraction
0.25, with `AMBIGUOUS` meaning the
label disagreed between the two finest grids.

| family | truths | single | multi | blended | dead | ambiguous | conv med | conv max | card err |
|---|---|---|---|---|---|---|---|---|---|
| `circular_hotspot_trajectory` | 24 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.207 | 0.427 | 0 |
| `flare_birth_motion_decay` | 24 | 0.426 | 0.000 | 0.000 | 0.574 | 0.000 | 0.254 | 0.362 | 0 |
| `m1_rotating_crescent` | 24 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.257 | 0.402 | 0 |
| `m2_structural_mode` | 24 | 0.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.252 | 0.367 | 0 |
| `plunging_feature` | 24 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.254 | 0.367 | 0 |
| `two_hotspot_trajectories` | 24 | 0.000 | 0.781 | 0.086 | 0.000 | 0.133 | 0.223 | 0.360 | 1 |

Off-manifold controls, reported separately and never pooled with the declared
families:

| family | truths | single | multi | blended | dead | ambiguous | conv med | conv max | card err |
|---|---|---|---|---|---|---|---|---|---|
| `counter_rotating_pair` | 8 | 0.000 | 0.574 | 0.279 | 0.000 | 0.148 | 0.219 | 0.384 | 1 |
| `radially_drifting_arc` | 8 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.127 | 0.420 | 0 |
| `three_hotspot_cluster` | 8 | 0.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.205 | 0.486 | 1 |

`conv` is the grid-convergence error between the two finest levels, in level-0
cells: how much the measured feature set moves when the analysis grid is
doubled. `card err` is the largest disagreement in how many features are
present.

## 3. What projection onto a reconstruction class destroys

The merger rate is the fraction of `MULTI_RESOLVED` states that stop being
multi-resolved once the field is projected onto the class. The representation
floor is the set-valued assignment error between the analytic field's features
and its own best in-class approximation -- the error an estimator starts with,
before any operator and before any noise.

| family | class | multi states | merger rate | floor median | floor max |
|---|---|---|---|---|---|
| `circular_hotspot_trajectory` | `L448_contrast` | 0 | -- | 1.786 | 44.401 |
| `circular_hotspot_trajectory` | `L896_radial_enriched` | 0 | -- | 0.238 | 22.277 |
| `flare_birth_motion_decay` | `L448_contrast` | 0 | -- | 0.000 | 43.863 |
| `flare_birth_motion_decay` | `L896_radial_enriched` | 0 | -- | 0.000 | 22.182 |
| `m1_rotating_crescent` | `L448_contrast` | 0 | -- | 2.262 | 66.033 |
| `m1_rotating_crescent` | `L896_radial_enriched` | 0 | -- | 0.238 | 22.277 |
| `m2_structural_mode` | `L448_contrast` | 1464 | 0.000 | 3.810 | 132.066 |
| `m2_structural_mode` | `L896_radial_enriched` | 1464 | 0.000 | 0.476 | 88.203 |
| `plunging_feature` | `L448_contrast` | 0 | -- | 2.556 | 23.875 |
| `plunging_feature` | `L896_radial_enriched` | 0 | -- | 1.068 | 23.039 |
| `two_hotspot_trajectories` | `L448_contrast` | 1338 | 0.356 | 22.796 | 24.833 |
| `two_hotspot_trajectories` | `L896_radial_enriched` | 1338 | 0.262 | 1.037 | 24.443 |

## 4. What the classes can represent at all

The narrowest radial feature each class keeps narrow, measured by projecting
Gaussians of decreasing width and reporting the input width at which the output
has broadened by a factor of two. This is a property of the class and needs no
source bank.

| class | r centre (M) | minimum representable width (M) |
|---|---|---|
| `L448_contrast` | 6 | 3.00 |
| `L448_contrast` | 20 | 4.00 |
| `L448_contrast` | 45 | 6.00 |
| `L896_radial_enriched` | 6 | 2.00 |
| `L896_radial_enriched` | 20 | 4.00 |
| `L896_radial_enriched` | 45 | 4.00 |

## 5. Blended states

323 (truth, age) states are blended across all sources. They are
reported as a centroid, a total contrast, second moments and mode amplitudes --
what a one-peak field supports -- and not as two trajectories forced through
it. Median second radial moment 0.0120 in log r,
median azimuthal 0.2304 in radians squared.

## 6. Tracks

Multi-resolved features are associated across age by the same assignment
metric used everywhere else, so a track break and a position error are measured
on one scale. Median distinct tracks per declared truth:
1.0.

## 7. The canary

`HMT1_SOURCE_RESOLUTION_FAILURE_CANARY`, the HMT-1 truth that failed the sealed
main. Named regression only: it appears in no aggregate above and in no
per-family fraction.

States over its 61 ages: single
0, multi
0, blended
61, dead
0, ambiguous
0.

| class | multi states | merger rate | representation floor median |
|---|---|---|---|
| `L448_contrast` | 0 | -- | 0.690 |
| `L896_radial_enriched` | 0 | -- | 0.538 |

## 8. What the audit found

**The problem is one family, and it is quantified.** Five of the six declared
families are clean: the single-feature families classify SINGLE_RESOLVED at
every live age with no ambiguity, and the m = 2 pattern classifies
MULTI_RESOLVED at every age, its two lobes being azimuthally separated and so
untouched by a radial grid. `two_hotspot_trajectories` is the exception. Across
its declared range it is MULTI_RESOLVED only
78% of the
time; the rest is BLENDED or AMBIGUOUS. HMT-1 asked for a resolved peak
position from that family at every age, and roughly a fifth of the time there
was no such thing to ask for.

**The grids themselves are converged.** Doubling the analysis grid moves the
measured feature set by 0.25 cells
at the median and 0.43 at the worst, with
the cardinality disagreeing at most once in the whole declared bank. The
resolution limit is in the source-grid contract, not in the arithmetic.

**Projection onto the current class destroys resolved structure.** Of the
two-hotspot states that are genuinely MULTI_RESOLVED in the analytic field,
36%
stop being multi-resolved once projected onto `L448_contrast`, the class HMT-1
used. Doubling the radial functions brings that to
26%.
An estimator working in the current class cannot recover two features that its
own class merges before the operator is even applied.

**Radial enrichment moves the representation floor by about an order of
magnitude.** The median floor -- the assignment error between the analytic
field and its own best in-class approximation, before any operator and any
noise -- falls from
2.41 cells to
0.36 across the
declared families.

**And the class cannot keep a narrow feature narrow.** `L448_contrast`
broadens anything below about 6 M at r = 45 M by a factor of two. The HMT-1
truth that failed had radial widths of 2.29 and 3.03 M at r = 46 and 43 M --
well under that floor. The enriched class improves it to about 4 M at the same
radius, which is better and still above those widths.

**The canary is blended at every age.** The HMT-1 truth that failed the sealed
main classifies BLENDED at all 61 ages, on every grid, with a grid
convergence of 0.25 cells and no
cardinality disagreement. It is not an unstable or marginal source: it is a
perfectly well-determined field with one peak, and HMT-1's gate was asking it
for a resolved peak position that does not exist. The gate was right to fail
and the reason was upstream of it.

## 9. What this does and does not establish

It establishes what these six families put on these grids and what survives
projection onto these two classes. It says nothing about any estimator, because
no operator exists in this run.

The audit does not impose a separation cut, per item 9. It measures what the
declared ranges contain so that a cut, a finer grid, or a resolution-aware
measure can be chosen on evidence rather than on the one truth that happened to
fail.

**STOP.** Item 18: the source-only audit is complete. HMT-2 validation, a new
sealed bank, order leakage, geometry mismatch, VLBI and machine learning all
remain unauthorized.
