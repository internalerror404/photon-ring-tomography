# R1L stage 2R-B — gate-completed

Reviewer ruling on stage 2R-B. The scientific disposition is unchanged; what is
repaired is gate coverage, two bank classifications, the estimand pairing and
the stable-span noise semantics.

- run `R1LS2RB_20260827T182520Z_2ba66f02`, execution commit `36f4be5060fa`,
  clean True, preregistered True
- gate coverage **12 emitted of 12 declared**, complete: True
- amendment `R1L_STAGE2R_GATE_COMPLETION_AMENDMENT_013`
- **disposition `R1L_STAGE2R_B_NO_MATERIAL_EFFECT`**

## 1. Endpoint on the physical banks only

The physical-source claim rests on the two non-negative structure-balanced banks
alone. The signed constant-flux bank is reported in section 3 and may not carry
it. Material requires median ≥ 10% and
cell-balanced mean lower bound ≥ 5%, ≥
3/4 families, every bank in scope positive, null
controls passing, and both estimators on the same class.

| arm | estimator | SNR₀ | per-truth median | median 95% CI | cell-balanced mean | mean 95% CI | families | material |
|---|---|---:|---:|---|---:|---|---|---|
| `RESOLVED_PHYSICAL` | RIDGE_IDENTITY | 100 | +0.178 | [+0.096, +0.255] | +0.098 | [+0.000, +0.185] | 3/4 | no |
| `RESOLVED_PHYSICAL` | TSVD | 100 | +0.168 | [+0.099, +0.241] | +0.116 | [+0.039, +0.187] | 3/4 | no |
| `TOTAL_FLUX` | RIDGE_IDENTITY | 100 | -0.005 | [-0.010, +0.000] | -0.000 | [-0.006, +0.007] | 1/4 | no |
| `TOTAL_FLUX` | TSVD | 100 | +0.006 | [-0.000, +0.013] | +0.027 | [+0.013, +0.043] | 2/4 | no |
| `UNRESOLVED_IMAGE` | RIDGE_IDENTITY | 100 | +0.019 | [-0.073, +0.103] | -0.029 | [-0.100, +0.037] | 3/4 | no |
| `UNRESOLVED_IMAGE` | TSVD | 100 | +0.009 | [-0.084, +0.090] | -0.024 | [-0.079, +0.028] | 3/4 | no |
| `RESOLVED_PHYSICAL` | RIDGE_IDENTITY | 1000 | +0.304 | [+0.225, +0.366] | +0.286 | [+0.237, +0.334] | 4/4 | **MATERIAL** |
| `RESOLVED_PHYSICAL` | TSVD | 1000 | +0.275 | [+0.198, +0.337] | +0.259 | [+0.210, +0.307] | 4/4 | **MATERIAL** |
| `TOTAL_FLUX` | RIDGE_IDENTITY | 1000 | -0.009 | [-0.012, -0.004] | -0.010 | [-0.014, -0.006] | 1/4 | no |
| `TOTAL_FLUX` | TSVD | 1000 | -0.008 | [-0.012, -0.003] | -0.010 | [-0.014, -0.006] | 1/4 | no |
| `UNRESOLVED_IMAGE` | RIDGE_IDENTITY | 1000 | +0.116 | [+0.031, +0.162] | +0.104 | [+0.067, +0.141] | 3/4 | **MATERIAL** |
| `UNRESOLVED_IMAGE` | TSVD | 1000 | +0.085 | [+0.019, +0.131] | +0.078 | [+0.042, +0.112] | 3/4 | no |

Each interval now names the statistic it belongs to. The earlier report attached
the mean's interval to the median, which described neither.

## 2. Resolved arm, each physical bank separately, SNR₀ = 100

| bank | estimator | per-truth median | median 95% CI | cell-balanced mean | mean 95% CI |
|---|---|---:|---|---:|---|
| `constant_flux_structural` | RIDGE_IDENTITY | +0.399 | [+0.225, +0.425] | +0.340 | [+0.277, +0.401] |
| `constant_flux_structural` | TSVD | +0.358 | [+0.213, +0.383] | +0.312 | [+0.249, +0.374] |
| `structure_balanced_050` | RIDGE_IDENTITY | +0.161 | [+0.084, +0.261] | +0.066 | [-0.070, +0.183] |
| `structure_balanced_050` | TSVD | +0.148 | [+0.066, +0.242] | +0.092 | [-0.002, +0.178] |
| `structure_balanced_080` | RIDGE_IDENTITY | +0.196 | [+0.096, +0.327] | +0.129 | [-0.028, +0.252] |
| `structure_balanced_080` | TSVD | +0.190 | [+0.109, +0.328] | +0.141 | [+0.007, +0.251] |

## 3. Source-bank contract — gate `R1L_2RB_G10`

| bank | role | exact in class | nominal f | achieved f | non-negative | max negative mass | reprojection | physical primary |
|---|---|---|---:|---:|---|---:|---:|---|
| `constant_flux_structural` | `SIGNED_CONSTANT_FLUX_STRUCTURAL_DIAGNOSTIC` | True | — | 0.807 | False | 0.1966 | 0.084 | no |
| `structure_balanced_050` | `STRUCTURE_BALANCED_050` | True | 0.50 | 0.520 | True | 0.0001 | 0.117 | **yes** |
| `structure_balanced_080` | `HIGH_STRUCTURE_NOMINAL_080_REALIZED_066` | True | 0.80 | 0.660 | True | 0.0007 | 0.078 | **yes** |

The constant-flux bank is reclassified `SIGNED_CONSTANT_FLUX_STRUCTURAL_DIAGNOSTIC`.
My earlier report gave its negative mass as about 3.6%, which is the median; the
maximum over records is 19.7% and 18 of 64 exceed 10%. Quoting the median alone
understated it. It is a legitimate linear inverse-problem stress control and is
not a physical emissivity history.

`structure_balanced_080` is reclassified `HIGH_STRUCTURE_NOMINAL_080_REALIZED_066`:
the 0.80 target is set before projection onto the class, projection removes
structure, and the realized fraction is what the operator saw.

## 4. Stable structural span, both noise semantics

| arm | SNR₀ | semantics | L direct (M) | L arm (M) | ΔL (M) | ≥ 8 M |
|---|---:|---|---:|---:|---:|---|
| `RESOLVED_PHYSICAL` | 100 | joint_truth_noise | 0.0 | 0.0 | +0.0 | **no** |
| `TOTAL_FLUX` | 100 | joint_truth_noise | 0.0 | 0.0 | +0.0 | **no** |
| `UNRESOLVED_IMAGE` | 100 | joint_truth_noise | 0.0 | 0.0 | +0.0 | **no** |
| `RESOLVED_PHYSICAL` | 1000 | joint_truth_noise | 0.0 | 0.0 | +0.0 | **no** |
| `TOTAL_FLUX` | 1000 | joint_truth_noise | 0.0 | 0.0 | +0.0 | **no** |
| `UNRESOLVED_IMAGE` | 1000 | joint_truth_noise | 0.0 | 0.0 | +0.0 | **no** |
| `RESOLVED_PHYSICAL` | 100 | truth_mean_noise | 0.0 | 0.0 | +0.0 | **no** |
| `TOTAL_FLUX` | 100 | truth_mean_noise | 0.0 | 0.0 | +0.0 | **no** |
| `UNRESOLVED_IMAGE` | 100 | truth_mean_noise | 0.0 | 0.0 | +0.0 | **no** |
| `RESOLVED_PHYSICAL` | 1000 | truth_mean_noise | 0.0 | 0.0 | +0.0 | **no** |
| `TOTAL_FLUX` | 1000 | truth_mean_noise | 0.0 | 0.0 | +0.0 | **no** |
| `UNRESOLVED_IMAGE` | 1000 | truth_mean_noise | 0.0 | 0.0 | +0.0 | **no** |

The joint truth-and-noise statistic controls the claim. It is the stricter of
the two, so it cannot rescue a positive span from the averaged one — and both
give zero. **The stable-span endpoint remains a negative result.**

## 5. Gates

| gate | status |
|---|---|
| `R1L_2RB_G1_pinned_numerical_environment` | PASS |
| `R1L_2RB_G2_split_commitments_reproduce` | PASS |
| `R1L_2RB_G3_split_disjointness` | PASS |
| `R1L_2RB_G4_truths_are_exactly_in_class` | PASS |
| `R1L_2RB_G5_representation_floor_is_zero` | PASS |
| `R1L_2RB_G6_secondary_bank_absent` | PASS |
| `R1L_2RB_G7_adjoint` | PASS |
| `R1L_2RB_G9_null_controls` | PASS |
| `R1L_2RB_G8_analytic_shaping_matches_grid_truth` | PASS |
| `R1L_2RB_G8x_operator_truth_identity` | PASS |
| `R1L_2RB_G10_source_balance_within_tolerance` | PASS |
| `R1L_2RB_G11_resource_limits` | PASS |

Coverage is now asserted structurally: the runner compares its emitted gate
names against the freeze's declared set and stops if any are missing. The defect
this repairs was that a declared-but-unemitted gate reads exactly like one that
passed.

## 6. Bitwise reproduction against `151229d`

| table | status |
|---|---|
| `r1l_2rb_age_structure_errors` | IDENTICAL |
| `r1l_2rb_bank_contract` | NEW_TABLE |
| `r1l_2rb_delta_spans` | IDENTICAL |
| `r1l_2rb_endpoint` | IDENTICAL |
| `r1l_2rb_joint_noise_spans` | NEW_TABLE |
| `r1l_2rb_null_pairs` | IDENTICAL |
| `r1l_2rb_pilot_scores` | IDENTICAL |
| `r1l_2rb_selection` | IDENTICAL |
| `r1l_2rb_source_banks` | IDENTICAL |
| `r1l_2rb_stable_spans` | IDENTICAL |

Verdict: **`R1L_STAGE2R_GATE_COMPLETION_PASS`**.
Every pre-existing scientific cell is identical; only new diagnostic columns and new tables appear. The gate completion describes the experiment rather than altering it.

## 7. Disposition

`R1L_STAGE2R_B_NO_MATERIAL_EFFECT`

At SNR₀ = 100, on the primary compact-support class `L1056`, with truths
exactly represented in that class and a representation floor of zero, the
resolved n = 0, 1, 2 operator materially reduces old-band structural
reconstruction error relative to the direct image, on both registered estimators
and on the non-negative physical banks alone.

It does **not** produce a stable contiguous structural interval: ΔL = 0 M
against 8 M under either noise semantics. Those are complementary findings and
the manuscript must carry both.

The scope is a representation-matched, zero-floor best-case benchmark at one
known Kerr geometry. It isolates inversion error from representation error under
an exactly matched localized model class, and establishes nothing about
arbitrary or realistic accretion-flow histories.
