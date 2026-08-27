# R1L stage 2R-A — corrected endpoint from existing artifacts

REVIEWER_RULING_R1L_STAGE2_011 item 7. No new source truth was generated. The
committed banks were regenerated from their frozen seeds and every one hashed to
the value stage 2 recorded, so these are the same objects, recomputed.

- run `R1LS2RA_20260827T160902Z_2ba66f02`, execution commit `8ce513fd0f3d`,
  clean False, preregistered False
- `baseline_one_positive` excluded from every endpoint row
- **corrected disposition `R1L_STAGE2R_A_NO_MATERIAL_EFFECT`**

## 1. Endpoint, pooled over the primary banks

Paired relative reduction against the direct arm, equal-weight over bank-family
cells, at SNR₀ = 100. Material requires median ≥
10%, bootstrap lower bound ≥
5%, ≥ 3/4 families, every primary bank
positive, and null controls passing — **and both estimators on the same class**.

| class | arm | estimator | median | CI low | CI high | families | all banks + | material |
|---|---|---|---:|---:|---:|---|---|---|
| `L1056` | `RESOLVED_PHYSICAL` | RIDGE_IDENTITY | +0.1417 | +0.0990 | +0.1595 | 4/4 | yes | **MATERIAL** |
| `L1056` | `RESOLVED_PHYSICAL` | TSVD | +0.0003 | +0.0009 | +0.0021 | 3/4 | yes | no |
| `L224` | `RESOLVED_PHYSICAL` | RIDGE_IDENTITY | +0.0924 | +0.0546 | +0.0933 | 3/4 | yes | no |
| `L224` | `RESOLVED_PHYSICAL` | TSVD | -0.0010 | -0.0038 | +0.0017 | 2/4 | no | no |
| `L448` | `RESOLVED_PHYSICAL` | RIDGE_IDENTITY | +0.0002 | +0.0002 | +0.0004 | 3/4 | yes | no |
| `L448` | `RESOLVED_PHYSICAL` | TSVD | +0.0000 | +0.0000 | +0.0000 | 3/4 | yes | no |
| `L1056` | `TOTAL_FLUX` | RIDGE_IDENTITY | -0.0000 | -0.0001 | +0.0002 | 2/4 | no | no |
| `L1056` | `TOTAL_FLUX` | TSVD | -0.0000 | +0.0002 | +0.0012 | 3/4 | no | no |
| `L224` | `TOTAL_FLUX` | RIDGE_IDENTITY | -0.0010 | -0.0019 | -0.0011 | 0/4 | no | no |
| `L224` | `TOTAL_FLUX` | TSVD | -0.0046 | -0.0082 | -0.0020 | 1/4 | no | no |
| `L448` | `TOTAL_FLUX` | RIDGE_IDENTITY | -0.0001 | -0.0004 | -0.0000 | 1/4 | no | no |
| `L448` | `TOTAL_FLUX` | TSVD | -0.0003 | -0.0005 | +0.0005 | 3/4 | no | no |
| `L1056` | `UNRESOLVED_IMAGE` | RIDGE_IDENTITY | +0.0001 | +0.0001 | +0.0002 | 3/4 | yes | no |
| `L1056` | `UNRESOLVED_IMAGE` | TSVD | -0.0000 | +0.0001 | +0.0002 | 3/4 | yes | no |
| `L224` | `UNRESOLVED_IMAGE` | RIDGE_IDENTITY | -0.0000 | -0.0000 | +0.0002 | 3/4 | no | no |
| `L224` | `UNRESOLVED_IMAGE` | TSVD | -0.0000 | -0.0002 | +0.0007 | 3/4 | no | no |
| `L448` | `UNRESOLVED_IMAGE` | RIDGE_IDENTITY | -0.0000 | -0.0000 | +0.0001 | 3/4 | no | no |
| `L448` | `UNRESOLVED_IMAGE` | TSVD | -0.0000 | -0.0000 | +0.0001 | 3/4 | no | no |

## 2. Every primary bank separately, resolved arm

| class | estimator | bank | median | CI low | CI high |
|---|---|---|---:|---:|---:|
| `L1056` | RIDGE_IDENTITY | `constant_flux_structural` | +0.1648 | +0.1364 | +0.2243 |
| `L1056` | RIDGE_IDENTITY | `structure_balanced_050` | +0.0646 | -0.0051 | +0.1023 |
| `L1056` | RIDGE_IDENTITY | `structure_balanced_080` | +0.1754 | +0.1143 | +0.2032 |
| `L1056` | TSVD | `constant_flux_structural` | +0.0009 | +0.0015 | +0.0035 |
| `L1056` | TSVD | `structure_balanced_050` | -0.0000 | +0.0000 | +0.0026 |
| `L1056` | TSVD | `structure_balanced_080` | -0.0001 | +0.0002 | +0.0013 |
| `L224` | RIDGE_IDENTITY | `constant_flux_structural` | +0.0930 | +0.0729 | +0.1278 |
| `L224` | RIDGE_IDENTITY | `structure_balanced_050` | +0.0395 | -0.0108 | +0.0645 |
| `L224` | RIDGE_IDENTITY | `structure_balanced_080` | +0.1163 | +0.0668 | +0.1221 |
| `L224` | TSVD | `constant_flux_structural` | -0.0007 | -0.0050 | +0.0064 |
| `L224` | TSVD | `structure_balanced_050` | +0.0003 | -0.0024 | +0.0062 |
| `L224` | TSVD | `structure_balanced_080` | -0.0014 | -0.0095 | -0.0019 |
| `L448` | RIDGE_IDENTITY | `constant_flux_structural` | +0.0003 | +0.0003 | +0.0006 |
| `L448` | RIDGE_IDENTITY | `structure_balanced_050` | +0.0001 | -0.0000 | +0.0005 |
| `L448` | RIDGE_IDENTITY | `structure_balanced_080` | +0.0001 | +0.0001 | +0.0003 |
| `L448` | TSVD | `constant_flux_structural` | +0.0000 | +0.0000 | +0.0000 |
| `L448` | TSVD | `structure_balanced_050` | +0.0000 | -0.0000 | +0.0000 |
| `L448` | TSVD | `structure_balanced_080` | -0.0000 | -0.0000 | +0.0000 |

## 3. Why the two estimators disagree by three orders of magnitude

This is the finding of stage 2R-A, and it is a selection pathology rather than
physics.

| class | arm | ridge cut | TSVD cut |
|---|---|---:|---:|
| `L1056` | `DIRECT_PHYSICAL` | 1.000e+00 | 1.000e+00 |
| `L1056` | `RESOLVED_PHYSICAL` | 3.162e-05 | 3.162e-01 |
| `L1056` | `TOTAL_FLUX` | 1.000e+00 | 3.162e-01 |
| `L1056` | `UNRESOLVED_IMAGE` | 1.000e+00 | 1.000e+00 |
| `L224` | `DIRECT_PHYSICAL` | 1.000e+00 | 1.000e-01 |
| `L224` | `RESOLVED_PHYSICAL` | 3.162e-04 | 3.162e-01 |
| `L224` | `TOTAL_FLUX` | 1.000e+00 | 1.000e+00 |
| `L224` | `UNRESOLVED_IMAGE` | 1.000e+00 | 1.000e-01 |
| `L448` | `DIRECT_PHYSICAL` | 1.000e+00 | 1.000e+00 |
| `L448` | `RESOLVED_PHYSICAL` | 1.000e+00 | 1.000e+00 |
| `L448` | `TOTAL_FLUX` | 1.000e+00 | 3.162e-01 |
| `L448` | `UNRESOLVED_IMAGE` | 1.000e+00 | 1.000e+00 |

The selection rule minimizes old-band structure error on the selection split.
When the representation floor is high, the lowest achievable error is obtained
by reconstructing **almost nothing** — the null estimator scores
`||truth||`, and any honest attempt scores worse. So the selection drives the
direct arm to maximal regularization at every class, and at `L448` it drives
*every* arm there. The endpoint then compares one near-null estimator against
another, which is why those deltas sit at 1e-4 to 1e-6.

The single exception is ridge on the resolved arm at `L1056`, where the
selection chose a light cut of 3.2e-05 because the resolved operator at 1056
dimensions can actually reconstruct. That configuration shows a median relative
reduction of 14.2% with a bootstrap interval of [9.9%, 16.0%], 4/4 families and
every primary bank positive — it meets every materiality threshold on its own.
It fails the corrected rule only because TSVD, the declared primary estimator,
was truncated to 0.316 on the same class and shows 0.03%.

I read that as one real configuration surrounded by degenerate ones, not as a
material result. Reporting it as a pass would mean reporting the one cell where
the selection happened not to collapse.

## 4. Exact age-local oracle representation floors

Fraction of age cells where the ε = 0.25 criterion is reachable **at all**, by a
perfect estimator restricted to the class:

| class | band | reachable fraction |
|---|---|---:|
| `L1056` | younger | 0.566 |
| `L1056` | old band | 0.580 |
| `L224` | younger | 0.094 |
| `L224` | old band | 0.137 |
| `L448` | younger | 0.204 |
| `L448` | old band | 0.217 |

At `L224` the criterion is unreachable in over 90% of age cells and at `L1056`
in more than 40%. The span endpoint was never testable on analytic banks.

## 5. Canonical ensemble stable spans

`T_stable_anchor` at ε = 0.25, q = 0.95,
supremum inside the probability, over the stored TSVD / SNR₀ = 100 ensemble.

| class | arm | T_stable_anchor (M) | pass fraction at the youngest age |
|---|---|---:|---:|
| `L1056` | `DIRECT_PHYSICAL` | 0.0 | 0.00 |
| `L1056` | `RESOLVED_PHYSICAL` | 0.0 | 0.00 |
| `L1056` | `TOTAL_FLUX` | 0.0 | 0.00 |
| `L1056` | `UNRESOLVED_IMAGE` | 0.0 | 0.00 |
| `L224` | `DIRECT_PHYSICAL` | 0.0 | 0.00 |
| `L224` | `RESOLVED_PHYSICAL` | 0.0 | 0.00 |
| `L224` | `TOTAL_FLUX` | 0.0 | 0.00 |
| `L224` | `UNRESOLVED_IMAGE` | 0.0 | 0.00 |
| `L448` | `DIRECT_PHYSICAL` | 0.0 | 0.00 |
| `L448` | `RESOLVED_PHYSICAL` | 0.0 | 0.00 |
| `L448` | `TOTAL_FLUX` | 0.0 | 0.00 |
| `L448` | `UNRESOLVED_IMAGE` | 0.0 | 0.00 |

Every span is zero, and the reason is visible in the last column: no truth
reaches ε = 0.25 even at age 0. This is not a statement about depth.

## 6. Gates

| gate | status |
|---|---|
| `R1L_2RA_G1_no_new_truths` | PASS |
| `R1L_2RA_G2_truth_content_hashes_match` | PASS |
| `R1L_2RA_G3_secondary_bank_excluded` | PASS |
| `R1L_2RA_G4_pinned_numerical_environment` | PASS |
| `R1L_2RA_G5_null_controls` | PASS |

## 7. Corrected scientific disposition

`R1L_STAGE2R_A_NO_MATERIAL_EFFECT`

The stage-2 formal token `R1L_STAGE2_RESOLVED_AND_UNRESOLVED_PASS` is preserved
and classified `FORMAL_PROTOCOL_TOKEN_UNDER_NONMATERIAL_CRITERIA`. Under the
materiality standard, with the secondary bank excluded, banks reported
separately, equal-weight aggregation and same-class estimator confirmation,
**no arm shows a material old-band structural advantage**.

Three separate reasons, all recorded:

1. The analytic banks put the ε = 0.25 criterion below the representation floor
   over most of the age grid, so the span endpoint could not be tested.
2. The selection rule collapses the direct arm — and at `L448` every arm — to
   the null estimator, so the endpoint compares nothing against nothing.
3. Where the selection did not collapse, ridge on resolved at `L1056`, the
   effect is 14.2% and material on its own but unconfirmed by TSVD.

All three are addressed by exact-in-class banks, which remove the floor and with
it the incentive for the selection to collapse. That is stage 2R-B.
