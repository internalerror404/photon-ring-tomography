# HMT-1 sealed held-out main

Freeze `HMT1_SEALED_HELD_OUT_MAIN_FREEZE_V1` (v2 bank seed), run `HMT1M_20260828T005146Z_2ba66f02`.
Execution commit `0f570d318689`, tree clean:
true, preregistered: true.

## Disposition

`HMT1_MAIN_IMPLEMENTATION_DEFECT`

17 of 18 gates pass. The failure is
`HMT1M_G10b_truth_extraction_recovers_generative_parameters`.

> **The science reading of this run is withheld, and withheld means unseen.**
>
> The endpoint tables were not written and the regime verdicts were not
> printed. Nobody, including the author of this report, has seen how the
> held-out bank scores. That is deliberate: labelling a defective run's
> numbers "diagnostic only" still puts them in the record, which spends the
> bank and means no corrected rerun on it could honestly be called sealed.
> The bank is intact and a corrected rerun on it is still a sealed run.

## What failed

`HMT1M_G10b` asks whether the feature extractor, pointed at the truth itself
with no operator and no noise in the way, returns the feature that was actually
put there. Worst displacement over the 96 held-out truths, in
evaluation-grid cells:

| family | worst displacement (cells) |
|---|---|
| `two_hotspot_trajectories` | 1.201 |
| `plunging_feature` | 0.496 |
| `m2_structural_mode` | 0.445 |
| `m1_rotating_crescent` | 0.391 |
| `flare_birth_motion_decay` | 0.343 |
| `circular_hotspot_trajectory` | 0.303 |

1 truth of 96 exceeds the sealed threshold of one cell. It is a
`two_hotspot_trajectories` draw whose two spots are well separated -- 12.6
azimuthal cells and 5.7 M radially, so this is not the near-tie that an earlier
version of this label got wrong -- but whose angular rates differ by a factor of
three. The faster spot sweeps about 2.5 azimuthal cells inside the declared 3 M
probe window, and the peak of the smeared arc lands about 1.2 cells from the
generative centre.

So the extractor is not misreading the field. The generative *label* for a
multi-feature family is imprecise: it names the declared centres, and for a
feature that moves appreciably within the probe window the peak of the windowed
field is not at the centre the window is centred on.

**This was not repaired, deliberately.** The threshold is sealed and item 8 of
the ruling forbids changing a tolerance. The label could be made exact -- the
generative reference for any family is the argmax of the analytic windowed
field, which is computable and would remove the family-specific candidate logic
entirely -- but that change would have been made after seeing the held-out
bank, which is tuning until the gate goes green. Having a principled
justification for such a change makes it more dangerous, not less. The run was
executed exactly as sealed and reports what it gives.

## Deviation on this freeze

Recorded in full in `HMT1_SEALED_MAIN_BANK_V1_RETIREMENT_016`. Stage B was
smoke tested on the first sealed bank, which is an operator evaluation on
held-out truths and therefore a peek, however small. That bank was retired and
redrawn under a new seed rather than defended, and the runner gained a scratch
mode that draws a throwaway bank and writes nothing canonical -- which is what
the smoke test should have used. Run against a substituted bank it fails
`HMT1M_G2` and `HMT1M_G16` exactly as it should, which is the first
demonstration that the seal check can fail.

That smoke run also falsified `HMT1M_G15` as originally written. It required
the noiseless control to score a lower endpoint error than the noisy draws;
with the sealed hyperparameters the feature error is bias dominated rather than
noise dominated, so removing the noise barely moves it. The gate now measures
what it was for -- that the noise path is live -- in the reconstruction rather
than in the endpoint, and the endpoint direction is reported below and not
gated, because no correct direction for it was established in advance.

## Controls, which carry no endpoint information

Held-out bank: 96 truths, worst azimuthal mean
1.89e-16, most negative total emissivity
0.061, local contrast
0.31 to
0.79 of the local background. Zero
overlap with the validation seeds.

Background error by regime:

| regime | median relative | worst |
|---|---|---|
| `estimated_from_data` | 0.0148 | 0.0577 |
| `joint_inversion` | 0.0148 | 0.0577 |
| `oracle_known` | 0.0000 | 0.0000 |

Noise path, as displacement between the noisy and noiseless reconstructions
relative to the noiseless one:

| regime | arm | estimator | median displacement | noiseless endpoint lower |
|---|---|---|---|---|
| `estimated_from_data` | `DIRECT_PHYSICAL` | RIDGE_IDENTITY | 0.0639 | yes |
| `estimated_from_data` | `DIRECT_PHYSICAL` | TSVD | 0.0732 | yes |
| `estimated_from_data` | `RESOLVED_PHYSICAL` | RIDGE_IDENTITY | 0.1362 | no |
| `estimated_from_data` | `RESOLVED_PHYSICAL` | TSVD | 0.1187 | no |
| `estimated_from_data` | `TOTAL_FLUX` | RIDGE_IDENTITY | 4.0763 | no |
| `estimated_from_data` | `TOTAL_FLUX` | TSVD | 4.0764 | no |
| `estimated_from_data` | `UNRESOLVED_IMAGE` | RIDGE_IDENTITY | 0.0988 | no |
| `estimated_from_data` | `UNRESOLVED_IMAGE` | TSVD | 0.0606 | no |
| `joint_inversion` | `DIRECT_PHYSICAL` | RIDGE_IDENTITY | 0.0780 | yes |
| `joint_inversion` | `DIRECT_PHYSICAL` | TSVD | 0.0258 | no |
| `joint_inversion` | `RESOLVED_PHYSICAL` | RIDGE_IDENTITY | 0.1362 | no |
| `joint_inversion` | `RESOLVED_PHYSICAL` | TSVD | 0.1187 | no |
| `joint_inversion` | `TOTAL_FLUX` | RIDGE_IDENTITY | 4.0734 | no |
| `joint_inversion` | `TOTAL_FLUX` | TSVD | 4.0764 | no |
| `joint_inversion` | `UNRESOLVED_IMAGE` | RIDGE_IDENTITY | 0.0761 | no |
| `joint_inversion` | `UNRESOLVED_IMAGE` | TSVD | 0.0606 | no |
| `oracle_known` | `DIRECT_PHYSICAL` | RIDGE_IDENTITY | 0.0929 | yes |
| `oracle_known` | `DIRECT_PHYSICAL` | TSVD | 0.0574 | no |
| `oracle_known` | `RESOLVED_PHYSICAL` | RIDGE_IDENTITY | 0.1704 | no |
| `oracle_known` | `RESOLVED_PHYSICAL` | TSVD | 0.1232 | no |
| `oracle_known` | `TOTAL_FLUX` | RIDGE_IDENTITY | 4.7091 | no |
| `oracle_known` | `TOTAL_FLUX` | TSVD | 4.7092 | no |
| `oracle_known` | `UNRESOLVED_IMAGE` | RIDGE_IDENTITY | 0.0978 | no |
| `oracle_known` | `UNRESOLVED_IMAGE` | TSVD | 0.0608 | no |

Null-pair controls: worst realized-versus-target separation error
1.55e-15 over 96 near-null feature pairs.

## Open gap, not closed here

The validation freeze declares a `NONNEGATIVE_CONSTRAINED` control estimator,
scoped to the primary SNR and the estimated-background regime, which the
validation never implemented. It has no sealed hyperparameter because it was
never selected, and choosing one now is the selection item 8 forbids. It is
left unimplemented and reported rather than smuggled in behind a prohibited
selection. It needs a ruling.

## What a corrected rerun would need

A ruling on one question: may the `HMT1M_G10b` generative label be redefined as
the argmax of the analytic windowed field, for every family, before the sealed
main is re-executed on the same untouched bank. That is a change to how the
truth is *labelled*, not to the tolerance, the endpoint, the estimators, the
hyperparameters or the family set, all of which stay sealed. If the answer is
no, the alternative reading is that this bank contains one truth the declared
extraction procedure cannot label to within its own grid, and the run stands as
a defect.

**STOP.** No further stage is authorized. Order leakage, geometry mismatch,
VLBI, machine learning and a new pixel-movie reconstruction campaign all remain
unauthorized, and the R1L stop and its sealed commitments are untouched.
