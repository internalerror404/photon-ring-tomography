# Localization interpretation overlay

Review `PAPER_I_R2_ACCEPTANCE_AND_LOCALIZATION_025`. Additive: nothing in
`epoch_breakdown_addition.json` is edited or deleted, and no accepted number
moves. What changes is the physical meaning attached to a set of percentages.

## Disposition

`epoch_breakdown_addition.json` is a **`CHOLESKY_COORDINATE_GROUP_DIAGNOSTIC`**,
not a `PHYSICAL_EPOCH_PARTITION`.

## What I got wrong

The diagnostic grouped the columns of `B_o = A_old R^-1` by the *original*
temporal hat labels. After that right-multiplication a column no longer belongs
to one hat. I verified the mechanism here rather than accepting it: the
three-hat temporal Gram is exactly proportional to

    [[2, 1, 0], [1, 4, 1], [0, 1, 4]]

and the third column of `R^-1` in the hat basis is exactly `[1/7, -2/7, 1]`.
Group 2 therefore contains all three hats. The arithmetic in that table was
right; calling it an epoch partition was not.

Three statements in my return are withdrawn: that 99.8% of each mode lies in
temporal hat 2 *as a time window*, that the oldest hat contributes *exactly*
zero, and that the surviving directions occupy the target's *youngest fifth*.

## What is true instead

**Source-function localization** of the two exported modes, from the reviewer's
committed diagnostic read back against the full export on this machine.
Coordinate readback `1.110e-15`, source
Gram refinement steps `[1.8346748276934313e-14, 4.332083858600331e-15]`:

| disjoint interval (M) | mode 1 | mode 2 |
|---|---:|---:|
| [-128.82235, -109.09455] | 2.43965% | 2.35122% |
| [-109.09455, -89.36676] | 43.81078% | 43.92154% |
| [-89.36676, -69.63897] | 53.74957% | 53.72724% |

The original hat-2 support holds 97.560% and 97.649%; the youngest fifth of the
target union holds 11.610% and 11.605%. Hat 2 spans the youngest **two thirds**
of the union, not its youngest fifth.

**Invariant trace localization**, the thing the broken table was reaching for,
computed here with the full target information matrix under the same operator,
metric, noise and nuisance projection: `L_I = tr(F E_I)` with
`E_I = R^-T H_I R^-1`.

| disjoint interval (M) | tr(F E_I) | share of tr F |
|---|---:|---:|
| [-128.82235, -109.09455] | 0.247806 | 3.4426% |
| [-109.09455, -89.36676] | 3.196779 | 44.4101% |
| [-89.36676, -69.63897] | 3.753732 | 52.1474% |

Total conditional trace 7.198317; the disjoint
partition sums to it with relative error
6.7e-16. The direct arm is zero in every
window, as it is on the whole target.

These two tables measure different objects -- squared source norm of the two
leading modes, and the trace of the whole information operator -- and they
agree on the shape: temporally broad, tilted young, oldest third small but
**not** zero.

## Corrected manuscript language

> At the reference Kerr geometry, ideal order-labeled observations retain two
> operational combinations in a 72-dimensional compact old-contrast target
> after profiling the other 152 coefficients of the full L224 model. The direct
> sampled operator annihilates the target. The two exported source-function
> combinations are temporally broad: about 97.6% of their squared norm lies
> between -109.1 and -69.6 M, with about 53.7% between -89.4 and -69.6 M. This
> establishes bounded likelihood sensitivity within the declared representation,
> not reconstruction of independently resolved epochs or a historical movie.

Source energy, Fisher trace, coordinate weight and recovered information are
four different objects and are not interchanged.
