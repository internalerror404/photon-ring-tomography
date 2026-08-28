# HMT-1 sealed held-out main

Freeze `HMT1_SEALED_HELD_OUT_MAIN_FREEZE_V2`, bank seed 20260921.
Execution commit `707c4b998ea1`, tree clean:
false, preregistered: false.

## Disposition

`HMT1_MAIN_IMPLEMENTATION_DEFECT`

Stage A failed one source gate, so **no operator was imported and no held-out
truth was evaluated**. There is no endpoint to withhold this time, because none
was ever computed. The bank is untouched in the strongest available sense.

That is the two-stage split doing what ruling 017 item 10 asked of it. On the
previous attempt the same class of problem was found only after the operator
had run, which is what spent that bank.

## Stage A — the source gates

| gate | status | measured | threshold |
|---|---|---|---|
| `HMT1M_G1_pinned_numerical_environment` | PASS | 1 | 1 |
| `HMT1M_G2_held_out_commitment_reproduces` | PASS | 1 | 1 |
| `HMT1M_G3_disjoint_from_validation_and_retired_truths` | PASS | 0 | 0 |
| `HMT1M_G4_contrast_zero_spatial_mean` | PASS | 2.046e-17 | 1e-10 |
| `HMT1M_G4b_azimuthal_zero_mean` | PASS | 2.706e-16 | 1e-10 |
| `HMT1M_G5_total_emissivity_nonnegative` | PASS | 0 | 0 |
| `HMT1M_G6_background_strictly_positive` | PASS | 0 | 0 |
| `HMT1M_G10_feature_extraction_deterministic` | PASS | 0 | 1e-09 |
| `HMT1M_G10c_truth_extraction_matches_independent_windowed_reference` | FAIL | 2.576 | 1 |
| `HMT1M_G17_off_manifold_bank_built` | PASS | 12 | 12 |

- `HMT1M_G2_held_out_commitment_reproduces` — all six declared commitments, not only the families run
- `HMT1M_G3_disjoint_from_validation_and_retired_truths` — held-out seeds also appearing in the validation bank or in any bank this freeze has retired
- `HMT1M_G10c_truth_extraction_matches_independent_windowed_reference` — worst displacement from the independent windowed reference, in evaluation-grid cells: radial 0.476, azimuthal 2.576
- `HMT1M_G17_off_manifold_bank_built` — built here and marked unscored. Stage B checks that none reaches an endpoint

## Stage B — the operator gates

| _(stage B did not run: no operator was imported)_ | | | |

## What failed, and what it is not

`HMT1M_G10c` compares the extracted peak against an independent windowed
reference, at the frozen one-cell threshold. Worst displacement per family over
the 96 held-out truths:

| family | worst displacement (cells) |
|---|---|
| `two_hotspot_trajectories` | 2.576 |
| `plunging_feature` | 0.516 |
| `m2_structural_mode` | 0.476 |
| `circular_hotspot_trajectory` | 0.476 |
| `m1_rotating_crescent` | 0.476 |
| `flare_birth_motion_decay` | 0.450 |

| family | index | radial cells | azimuthal cells |
|---|---|---|---|
| `two_hotspot_trajectories` | 5 | 0.475 | 2.576 |

One truth of 96. Getting to the real number took separating two
different things.

**A defect in G10c itself**, which this bank exposed and the
396-truth validation had not. A field that is numerically
zero away from its feature still has local maxima there, and the reference was
offering them as candidates. Here a dust maximum at amplitude 0.00000 sat at
the extractor's azimuth and absorbed a real 2.4-cell azimuthal disagreement,
reporting 1.2 radial cells instead. Candidates now have to clear the birth
fraction the campaign already uses for a feature being detectable. The
correction moves reported errors *up*, not down -- this truth went from 1.251
to 2.576 cells, and an off-manifold control from 0.578 to 10.157 -- which is
the direction a correction to a gate should move.

**What remains is neither the extractor's error nor the reference's.** The
failing truth has two spots separated by 0.34 radial cells, with radial widths
of 0.23 and 0.32 cells. Both blobs, and the gap between them, are sub-cell on
the 16-point log-radial evaluation grid. They are radially unresolved: the
extractor sees a blend and reports its azimuth, the reference resolves the
dominant spot, and the two answers differ by more than a cell. The declared
`two_hotspot_trajectories` range admits configurations the declared evaluation
grid cannot resolve.

**Not redrawn and not relaxed.** Item 9 forbids a seed search and a
redraw-until-pass loop, item 6 forbids changing family ranges, and item 5 froze
the threshold at one cell. The bank stands as drawn.

## Controls, which carry no endpoint information

96 held-out truths, worst azimuthal mean
2.71e-16, most negative total emissivity
0.073, local contrast
0.30 to
0.79 of the local background. Zero
overlap with the validation bank or with either retired bank.
12 off-manifold truths built and marked unscored.

## Estimator scope

`TSVD` and `RIDGE_IDENTITY` authorized. `NONNEGATIVE_CONSTRAINED` recorded
`WITHDRAWN_UNSELECTED`: it was declared as a control in the validation freeze,
never implemented, and has no selected hyperparameter, so running it now would
require the selection ruling 015 item 8 forbids. `ML` remains `NOT_AUTHORIZED`.
`HMT1M_G19` refuses any run whose estimator set differs from the authorized
one.

## What a further attempt would need

A ruling on the declared `two_hotspot_trajectories` radial range. The family
draws both spots independently across the full radial support, so a pair can
land within a fraction of a log-radial cell of each other at large radius,
where a cell is about 10 M and the blob widths are 2 to 3 M. Any of these would
resolve it, and all of them are changes item 6 currently forbids:

- require a minimum radial separation between the two spots, in cells;
- refine the radial evaluation grid so that widths of 2 to 3 M are resolved at
  large radius;
- score `G10c` for multi-feature families against the blend the grid can
  actually represent rather than the resolved reference.

The third is the only one that touches no declared quantity, but it also
weakens the gate, and choosing it after seeing which truth failed is the move
this campaign has repeatedly had to refuse.

**STOP.** Item 14: stopped after this execution regardless of disposition.
Geometry mismatch, order leakage, VLBI, machine learning and a new pixel-movie
campaign remain unauthorized, and the R1L stop and its sealed commitments are
untouched.
