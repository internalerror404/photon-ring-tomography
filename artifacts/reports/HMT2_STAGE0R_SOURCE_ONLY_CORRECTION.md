# HMT-2 stage 0R — source-only correction

Freeze `HMT2_STAGE0R_SOURCE_ONLY_CORRECTION_V0`, run `HMT2_STAGE0R_CORRECTION`.
Ray map imported: false. Operator constructed:
false. Both derived from an inspection of
loaded modules taken *after* all computation, not written as literals.
169 sources, 20,618 per-age rows,
2343 s.

## 1. What was corrected

Stage 0 computed its projection merger rate over every state the finest grid
called `MULTI_RESOLVED`. That set includes states the two finest grids disagree
about, and a merger rate taken over states whose multiplicity is itself
unresolved measures the classifier as much as it measures the projection. The
reviewer withheld those numbers as canonical; this run recomputes them over
reconciled stable states and publishes the per-age table they come from, so
every rate here is recomputable rather than trusted.

Nothing about the sources changed. The same 169 objects, the same
seeds, the same ranges with no separation cut, the same prominence fraction,
the same refinement levels, the same two classes. No redraw.

## 2. The corrected rates

`two_hotspot_trajectories`, the only family with a mixed resolution regime:

| stratum | class | states | merged | merger rate | carries claim |
|---|---|---|---|---|---|
| `ALL_FINEST_MULTI` | `L448_contrast` | 1338 | 476 | 0.356 | no |
| `ALL_FINEST_MULTI` | `L896_radial_enriched` | 1338 | 351 | 0.262 | no |
| `AMBIGUOUS_FINE_MULTI` | `L448_contrast` | 195 | 134 | 0.687 | no |
| `AMBIGUOUS_FINE_MULTI` | `L896_radial_enriched` | 195 | 195 | 1.000 | no |
| `STABLE_MULTI_RESOLVED` | `L448_contrast` | 1143 | 342 | 0.299 | **yes** |
| `STABLE_MULTI_RESOLVED` | `L896_radial_enriched` | 1143 | 156 | 0.136 | **yes** |

**The correction moves the answer in both directions at once.** On the states
that can carry a claim, the current class merges
29.9% of genuinely
resolved pairs rather than the withheld
35.6%, and the enriched class
13.6% rather than
26.2%. So the stable
merger rate is *lower* than reported, and the benefit of radial enrichment is
*larger*: a reduction of
54%
on stable states against
26%
under the withheld pooling. The withheld numbers understated the enrichment and
overstated the stable merger rate at the same time.

**The excluded stratum is why.** States where the two finest grids disagree
merge at 69% in the
current class and at
100% in the
enriched one -- every single one. That is not a surprise once stated: a pair
the analysis grid cannot agree about is a pair no reconstruction class of this
size will keep apart. Pooling them with the stable states dragged both class
rates toward each other and hid the difference between the classes.

Across all declared families the strata partition exactly:
5,214 stable plus 390
ambiguous equals 5,604 finest-grid multi states, with no
state in both, which `HMT2R_G7` checks rather than assumes.

## 3. Stable-state merger rates, all families

| family | class | stable states | merger rate | median normalized unbalanced cost |
|---|---|---|---|---|
| `m2_structural_mode` | `L448_contrast` | 1464 | 0.000 | 0.174 |
| `m2_structural_mode` | `L896_radial_enriched` | 1464 | 0.000 | 0.022 |
| `two_hotspot_trajectories` | `L448_contrast` | 1143 | 0.299 | 1.033 |
| `two_hotspot_trajectories` | `L896_radial_enriched` | 1143 | 0.136 | 0.035 |

The normalized unbalanced cost is the total assignment cost divided by the cost
of one wholly unmatched feature, so 1.0 means one feature gained or lost. It is
not a displacement.

## 4. Gates

9 gates, 9 pass,
0 fail.

| gate | status | measured | threshold |
|---|---|---|---|
| `HMT2R_G1_pinned_numerical_environment` | PASS | 1 | 1 |
| `HMT2R_G2_source_only_before` | PASS | 0 | 0 |
| `HMT2R_G3_source_only_after` | PASS | 0 | 0 |
| `HMT2R_G4_same_sources_as_stage_0` | PASS | 0 | 0 |
| `HMT2R_G5_no_redraw` | PASS | 1 | 1 |
| `HMT2R_G6_per_age_table_complete` | PASS | 0 | 0 |
| `HMT2R_G7_strata_partition_the_finest_multi_states` | PASS | 0 | 0 |
| `HMT2R_G8_canary_excluded_from_aggregates` | PASS | 0 | 0 |
| `HMT2R_G9_declared_gate_coverage` | PASS | 0 | 0 |

- `HMT2R_G3_source_only_after` — inspected after all computation; the recorded booleans below are derived from this inspection
- `HMT2R_G4_same_sources_as_stage_0` — 169 truth seeds compared against the 169 stage 0 recorded, 0 differing, 0 present in one and not the other
- `HMT2R_G5_no_redraw` — no new bank seed exists in this stage
- `HMT2R_G6_per_age_table_complete` — 20618 rows against 20618 expected
- `HMT2R_G7_strata_partition_the_finest_multi_states` — stable 5214 + ambiguous 390 = 5604 finest-multi, overlap 0
- `HMT2R_G9_declared_gate_coverage` — complete

The source-only guard runs twice, before any work and after all computation,
and the run document's `ray_map_imported` and `operator_constructed` fields are
derived from the second inspection. Stage 0 wrote those as literal `false`,
which records an intention rather than an observation.

## 5. The per-age table

`hmt2_stage0r_per_age` carries 20,618 rows, one per source per age per
class: the fine-grid label, the coarser-grid label, the reconciled label, the
projected label, cardinality before and after projection, the matched position
cost, the unbalanced cost and its normalization, and the canary and
off-manifold flags. Every rate in this report is a group-by on that table.

Of the 17,568 declared-family rows, the reconciled label is
`AMBIGUOUS` in 2.2%
and `BLENDED` in
1.4%.

## 6. What this changes and does not change

The four preserved findings stand untouched: the canary blended at 61 of 61
ages, the two-hotspot mixed resolution regime, the L448 representation limit,
and the benefit of radial enrichment. None of them rested on the merger-rate
accounting, and the correction strengthens the fourth rather than weakening it.

What changes is which number may be quoted. The canonical two-hotspot merger
rates are now
0.299 and
0.136, over reconciled
stable states only. The pooled 0.356
and 0.262 remain in the record
as what the finest grid alone would say, and carry no claim.

Still no operator and no ray map. Nothing here is an inverse-problem result.

**Stage 0R passes all corrected source-only gates**, so item 12 authorizes
`HMT2_STAGE1_RESOLUTION_AWARE_MORPHOLOGY_VALIDATION_V0`, which is registered
separately.
