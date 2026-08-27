# R1L stage 2 — structure-first validation pilot

Validation, not a held-out result. Hyperparameters are chosen on the selection
split and the reported endpoint is computed on the pilot split, which no
hyperparameter ever saw. The sealed main bank is committed and not generated.

- run `R1LS2_20260827T072633Z_2ba66f02`
- execution commit `e7f55bf38805`, clean True,
  preregistered True
- BLAS pools all single-threaded: True
- freeze `09d82c19e3fdcc28...`
- **disposition `R1L_STAGE2_RESOLVED_AND_UNRESOLVED_PASS`**

## 1. Source banks

Truths enter the operator analytically, sampled wherever the rays land, and are
never projected into the class first — so the representation floor in section 4
is a measured quantity rather than zero by construction.

| bank | role | target f_struct | achieved (median) | level fraction | reach target | at positivity ceiling |
|---|---|---|---:|---:|---:|---:|
| `baseline_one_positive` | secondary control only | — | 0.219 | 0.976 | 1.00 | 0/64 |
| `constant_flux_structural` | primary | — | 0.823 | 0.568 | 1.00 | 0/64 |
| `structure_balanced_050` | primary | 0.50 | 0.500 | 0.866 | 0.98 | 2/64 |
| `structure_balanced_080` | primary | 0.80 | 0.799 | 0.601 | 0.55 | 32/64 |

The `structure_balanced_080` bank is half at its ceiling. That is not a
construction defect: a non-negative field of a given shape has a maximum
structure fraction `||s|| / ||s - min s||`, reached exactly at the positivity
boundary, and scaling cannot evade it. Truths above their ceiling are kept at
the ceiling and flagged rather than discarded.

For scale, the R1 banks sat at a structure fraction of 0.126 — a level fraction
of 0.992. Every primary bank here is far outside that regime.

## 2. Primary endpoint

`delta_E_old_structure = E_old_structure(direct) − E_old_structure(arm)` at
SNR₀ = 100, on the pilot split, with a paired truth-cluster bootstrap
over 10,000 resamples. Positive
means the arm beats the direct image.

| class | arm | estimator | direct | arm | delta | 95% CI | excludes zero | families improved |
|---|---|---|---:|---:|---:|---|---|---|
| `L224` | `RESOLVED_PHYSICAL` | TSVD | 8.4533 | 8.4364 | +0.0169 | [-0.0166, +0.0642] | no | 2/4 |
| `L224` | `UNRESOLVED_IMAGE` | TSVD | 8.4533 | 8.4533 | -0.0000 | [-0.0033, +0.0032] | no | 2/4 |
| `L224` | `TOTAL_FLUX` | TSVD | 8.4533 | 8.4736 | -0.0203 | [-0.0533, +0.0233] | no | 1/4 |
| `L224` | `RESOLVED_PHYSICAL` | RIDGE_IDENTITY | 8.4325 | 8.1518 | +0.2807 | [+0.0815, +0.4888] | **yes** | 3/4 |
| `L224` | `UNRESOLVED_IMAGE` | RIDGE_IDENTITY | 8.4325 | 8.4326 | -0.0000 | [-0.0008, +0.0008] | no | 3/4 |
| `L224` | `TOTAL_FLUX` | RIDGE_IDENTITY | 8.4325 | 8.4480 | -0.0155 | [-0.0223, -0.0104] | no | 0/4 |
| `L448` | `RESOLVED_PHYSICAL` | TSVD | 8.4487 | 8.4486 | +0.0001 | [+0.0000, +0.0002] | **yes** | 3/4 |
| `L448` | `UNRESOLVED_IMAGE` | TSVD | 8.4487 | 8.4487 | +0.0000 | [-0.0007, +0.0009] | no | 3/4 |
| `L448` | `TOTAL_FLUX` | TSVD | 8.4487 | 8.4523 | -0.0035 | [-0.0080, +0.0011] | no | 1/4 |
| `L448` | `RESOLVED_PHYSICAL` | RIDGE_IDENTITY | 8.4417 | 8.4400 | +0.0017 | [+0.0005, +0.0031] | **yes** | 3/4 |
| `L448` | `UNRESOLVED_IMAGE` | RIDGE_IDENTITY | 8.4417 | 8.4415 | +0.0003 | [-0.0004, +0.0010] | no | 3/4 |
| `L448` | `TOTAL_FLUX` | RIDGE_IDENTITY | 8.4417 | 8.4445 | -0.0028 | [-0.0046, -0.0010] | no | 0/4 |
| `L1056` | `RESOLVED_PHYSICAL` | TSVD | 8.4442 | 8.4341 | +0.0101 | [+0.0035, +0.0181] | **yes** | 3/4 |
| `L1056` | `UNRESOLVED_IMAGE` | TSVD | 8.4442 | 8.4434 | +0.0008 | [+0.0003, +0.0014] | **yes** | 3/4 |
| `L1056` | `TOTAL_FLUX` | TSVD | 8.4442 | 8.4409 | +0.0033 | [-0.0008, +0.0078] | no | 3/4 |
| `L1056` | `RESOLVED_PHYSICAL` | RIDGE_IDENTITY | 8.4393 | 7.8305 | +0.6088 | [+0.2700, +0.9633] | **yes** | 3/4 |
| `L1056` | `UNRESOLVED_IMAGE` | RIDGE_IDENTITY | 8.4393 | 8.4383 | +0.0009 | [+0.0004, +0.0015] | **yes** | 3/4 |
| `L1056` | `TOTAL_FLUX` | RIDGE_IDENTITY | 8.4393 | 8.4398 | -0.0005 | [-0.0022, +0.0010] | no | 1/4 |

## 3. Structure-only stable spans

Mean over pilot truths at SNR₀ = 100, TSVD, on the
2 M age grid.

| class | `DIRECT_PHYSICAL` | `RESOLVED_PHYSICAL` | `UNRESOLVED_IMAGE` | `TOTAL_FLUX` |
|---|---:|---:|---:|---:|
| `L224` | 0.0 | 0.0 | 0.0 | 0.0 |
| `L448` | 0.0 | 0.0 | 0.0 | 0.0 |
| `L1056` | 0.0 | 0.0 | 0.0 | 0.0 |

Smallest SNR₀ on the frozen grid at which any structural span is nonzero:

| class | arm | onset SNR₀ |
|---|---|---|
| `L224` | `DIRECT_PHYSICAL` | none on the frozen grid |
| `L224` | `RESOLVED_PHYSICAL` | none on the frozen grid |
| `L224` | `UNRESOLVED_IMAGE` | none on the frozen grid |
| `L224` | `TOTAL_FLUX` | none on the frozen grid |
| `L448` | `DIRECT_PHYSICAL` | none on the frozen grid |
| `L448` | `RESOLVED_PHYSICAL` | none on the frozen grid |
| `L448` | `UNRESOLVED_IMAGE` | none on the frozen grid |
| `L448` | `TOTAL_FLUX` | none on the frozen grid |
| `L1056` | `DIRECT_PHYSICAL` | none on the frozen grid |
| `L1056` | `RESOLVED_PHYSICAL` | none on the frozen grid |
| `L1056` | `UNRESOLVED_IMAGE` | none on the frozen grid |
| `L1056` | `TOTAL_FLUX` | none on the frozen grid |

## 4. Representation floors

The error no estimator can beat: the truth's distance from the class's own span,
on the evaluation grid, relative and structure-only.

| class | bank | floor (all) | floor (structure) |
|---|---|---:|---:|
| `L1056` | `baseline_one_positive` | 0.182 | 0.641 |
| `L1056` | `constant_flux_structural` | 0.245 | 0.325 |
| `L1056` | `structure_balanced_050` | 0.212 | 0.372 |
| `L1056` | `structure_balanced_080` | 0.225 | 0.288 |
| `L224` | `baseline_one_positive` | 0.233 | 0.597 |
| `L224` | `constant_flux_structural` | 0.430 | 0.508 |
| `L224` | `structure_balanced_050` | 0.331 | 0.562 |
| `L224` | `structure_balanced_080` | 0.364 | 0.464 |
| `L448` | `baseline_one_positive` | 0.191 | 0.739 |
| `L448` | `constant_flux_structural` | 0.366 | 0.453 |
| `L448` | `structure_balanced_050` | 0.280 | 0.522 |
| `L448` | `structure_balanced_080` | 0.313 | 0.403 |

## 5. Common direct-subspace errors

Every arm's coefficient error projected onto the **direct** channel's own
`P_data`, so the arms are compared on one subspace rather than each on its own.

| class | arm | estimator | reference dim | arm dim | error inside | error outside |
|---|---|---|---:|---:|---:|---:|
| `L224` | `RESOLVED_PHYSICAL` | TSVD | 140 | 208 | 8.2184 | 6.6675 |
| `L224` | `RESOLVED_PHYSICAL` | RIDGE_IDENTITY | 140 | 208 | 9.8291 | 6.5227 |
| `L224` | `UNRESOLVED_IMAGE` | TSVD | 140 | 208 | 8.0060 | 6.6663 |
| `L224` | `UNRESOLVED_IMAGE` | RIDGE_IDENTITY | 140 | 208 | 8.3478 | 6.6672 |
| `L224` | `TOTAL_FLUX` | TSVD | 140 | 8 | 8.2979 | 6.6667 |
| `L224` | `TOTAL_FLUX` | RIDGE_IDENTITY | 140 | 8 | 8.4042 | 6.6671 |
| `L448` | `RESOLVED_PHYSICAL` | TSVD | 252 | 405 | 12.0824 | 10.5346 |
| `L448` | `RESOLVED_PHYSICAL` | RIDGE_IDENTITY | 252 | 405 | 11.8035 | 10.5326 |
| `L448` | `UNRESOLVED_IMAGE` | TSVD | 252 | 405 | 12.0701 | 10.5336 |
| `L448` | `UNRESOLVED_IMAGE` | RIDGE_IDENTITY | 252 | 405 | 11.8034 | 10.5333 |
| `L448` | `TOTAL_FLUX` | TSVD | 252 | 8 | 11.7507 | 10.5315 |
| `L448` | `TOTAL_FLUX` | RIDGE_IDENTITY | 252 | 8 | 11.8604 | 10.5330 |
| `L1056` | `RESOLVED_PHYSICAL` | TSVD | 524 | 838 | 10.1268 | 11.2041 |
| `L1056` | `RESOLVED_PHYSICAL` | RIDGE_IDENTITY | 524 | 838 | 14.6152 | 10.2006 |
| `L1056` | `UNRESOLVED_IMAGE` | TSVD | 524 | 836 | 10.8328 | 11.2033 |
| `L1056` | `UNRESOLVED_IMAGE` | RIDGE_IDENTITY | 524 | 836 | 10.4798 | 11.2029 |
| `L1056` | `TOTAL_FLUX` | TSVD | 524 | 8 | 10.4101 | 11.2008 |
| `L1056` | `TOTAL_FLUX` | RIDGE_IDENTITY | 524 | 8 | 10.5556 | 11.2024 |

## 6. Localized null-pair controls

A separation frozen in units of sigma, realized through the operator along the
smallest **nonzero** singular directions. Worst relative error
2.44e-15 over 480 pairs.

## 7. Gates

| gate | status | measured |
|---|---|---|
| `R1L_S2_G1_pinned_numerical_environment` | PASS | 1 |
| `R1L_S2_G2_split_commitments_reproduce` | PASS | 1 |
| `R1L_S2_G3_split_disjointness_by_content_hash` | PASS | 1 |
| `R1L_S2_G4_source_balance_within_tolerance` | PASS | 1 |
| `R1L_S2_G5_positivity` | PASS | 0.000e+00 |
| `R1L_S2_G6_no_hyperparameter_touched_pilot` | PASS | 1 |
| `R1L_S2_G7_adjoint` | PASS | 5.478e-14 |
| `R1L_S2_G8_estimator_closed_form` | PASS | 7.597e-16 |
| `R1L_S2_G9_noise_replay_bitwise` | PASS | 1 |
| `R1L_S2_G10_sealed_main_not_scored` | PASS | 1 |
| `R1L_S2_G11_resource_limits` | PASS | 1756 |
| `R1L_S2_G12_constant_flux_slice_means` | PASS | 1 |
| `R1L_S2_G13_analytic_shaping_matches_grid_truth` | PASS | 1.457e-14 |
| `R1L_S2_G14_null_pair_separation_realized` | PASS | 2.442e-15 |

## 8. Sealed main, committed and not scored

`R1L_SEALED_MAIN_COMMITMENT` commits 384 truths over 16
cells, seed 20260905, overlapping the validation commitments in
0 cells.
Nothing was rendered through an operator, no datum was formed and no error was
computed. Committing it before this report is what stops the sealed set from
being chosen to flatter the pilot.

## 9. Two findings that determine how section 2 must be read

**The co-primary was untestable as specified, and its result is not a negative
result about the orders.** The structural stable span is **zero for every arm,
every class and every SNR₀ on the frozen grid**, up to 30000. The span criterion
asks for a relative structural error at or below 0.25, and the smallest
representation floor anywhere in section 4 is **0.208**. The criterion
therefore sits below the floor everywhere: no operator, arm or estimator could
have produced a nonzero span, because the class cannot represent the truths that
well in the first place. `delta_L_stable_structure >= 8 M` was never reachable,
and the largest span observed is 0.0 M. This is a specification
mismatch between the 0.25 criterion and the analytic banks, not evidence about
higher orders.

**The primary endpoint has no effect-size threshold, and the effects that pass
are mostly negligible.** All four declared criteria are met, but "excludes zero"
is doing all the work: with 128 paired pilot truths and four draws each, the
bootstrap variance is tiny and a consistent sign passes at almost any magnitude.
Relative effect sizes of every interval that excludes zero:

| class | arm | estimator | delta | delta / direct |
|---|---|---|---:|---:|
| `L448` | `RESOLVED_PHYSICAL` | TSVD | 1.118e-04 | 1.3e-05 |
| `L1056` | `UNRESOLVED_IMAGE` | TSVD | 7.994e-04 | 9.5e-05 |
| `L1056` | `UNRESOLVED_IMAGE` | RIDGE_IDENTITY | 9.318e-04 | 1.1e-04 |
| `L448` | `RESOLVED_PHYSICAL` | RIDGE_IDENTITY | 1.739e-03 | 2.1e-04 |
| `L1056` | `RESOLVED_PHYSICAL` | TSVD | 1.014e-02 | 1.2e-03 |
| `L224` | `RESOLVED_PHYSICAL` | RIDGE_IDENTITY | 2.807e-01 | 3.3e-02 |
| `L1056` | `RESOLVED_PHYSICAL` | RIDGE_IDENTITY | 6.088e-01 | 7.2e-02 |

The unresolved arm's pass — the one that separates
`RESOLVED_AND_UNRESOLVED_PASS` from `RESOLVED_ONLY_PASS` — is **one part in ten
thousand**. Only ridge at `L1056` (7.2%) and at `L224` (3.3%) reaches a
magnitude that would matter to a reader. I do not think the unresolved result as
it stands supports any observational claim, and the freeze's own
`unresolved_arm_rule` was written to prevent exactly the reverse mistake, not to
license this one.

A third, smaller note: the structural span here is the mean over truths of each
truth's contiguous span, not the anchored quantile endpoint
`T_stable_anchor(epsilon, q)` the campaign uses elsewhere. Since every value is
zero under any definition, the simplification changes nothing, but it is a
deviation and is recorded as one.

## 10. Disposition

The declared rule yields **`R1L_STAGE2_RESOLVED_AND_UNRESOLVED_PASS`**, re-derived independently from the tables
by this report (agreeing with the runner).
It is carried by: resolved at `L1056`, `L224`, `L448`;
unresolved at `L1056`.

That token is what the freeze declared, and it stands as the disposition. It
should not be read as a scientific pass. On the evidence above, the honest
summary is that the resolved arm shows a real but small old-band structural
advantage that is substantial only under ridge, the unresolved arm's advantage
is statistically resolvable and physically negligible, and the co-primary could
not be tested at all.

Stage 2 is a validation pilot and nothing here is a held-out result. The sealed
main, geometry mismatch, order leakage, VLBI and ML all remain unauthorized.
