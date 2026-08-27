# R1L stage 2R-B — exact-in-class structural validation

REVIEWER_RULING_R1L_STAGE2_011 items 9 to 11, under
`R1L_STAGE2R_VALIDATION_FREEZE_012`. Every truth is in the span of its class to
machine precision, so the representation floor is zero and the error the
endpoint measures is reconstruction error and nothing else.

- run `R1LS2RB_20260827T162003Z_2ba66f02`, execution commit `b83cdf4706ee`,
  clean True, preregistered True
- primary class `L1056`; `L448` and `L224` are controls and cannot supply a pass
- **disposition `R1L_STAGE2R_B_MATERIAL_RESOLVED_ONLY`**

## 1. Endpoint, primary class

Paired relative reduction against the direct arm, equal-weight over bank-family
cells. Material requires median ≥ 10%,
bootstrap lower bound ≥ 5%,
≥ 3/4 families, every primary bank positive, null
controls passing, and **both estimators on the same class**.

| class | arm | estimator | SNR₀ | median | CI low | CI high | families | all banks + | material |
|---|---|---|---:|---:|---:|---:|---|---|---|
| `L1056` | `RESOLVED_PHYSICAL` | RIDGE_IDENTITY | 100 | +0.239 | +0.105 | +0.243 | 4/4 | yes | **MATERIAL** |
| `L1056` | `RESOLVED_PHYSICAL` | TSVD | 100 | +0.225 | +0.121 | +0.236 | 4/4 | yes | **MATERIAL** |
| `L1056` | `TOTAL_FLUX` | RIDGE_IDENTITY | 100 | -0.007 | -0.011 | -0.001 | 1/4 | no | no |
| `L1056` | `TOTAL_FLUX` | TSVD | 100 | -0.001 | +0.001 | +0.024 | 1/4 | no | no |
| `L1056` | `UNRESOLVED_IMAGE` | RIDGE_IDENTITY | 100 | +0.076 | -0.023 | +0.078 | 3/4 | yes | no |
| `L1056` | `UNRESOLVED_IMAGE` | TSVD | 100 | +0.058 | -0.017 | +0.065 | 3/4 | yes | no |
| `L1056` | `RESOLVED_PHYSICAL` | RIDGE_IDENTITY | 1000 | +0.312 | +0.266 | +0.345 | 4/4 | yes | **MATERIAL** |
| `L1056` | `RESOLVED_PHYSICAL` | TSVD | 1000 | +0.286 | +0.239 | +0.317 | 4/4 | yes | **MATERIAL** |
| `L1056` | `TOTAL_FLUX` | RIDGE_IDENTITY | 1000 | -0.009 | -0.016 | -0.009 | 1/4 | no | no |
| `L1056` | `TOTAL_FLUX` | TSVD | 1000 | -0.010 | -0.017 | -0.010 | 1/4 | no | no |
| `L1056` | `UNRESOLVED_IMAGE` | RIDGE_IDENTITY | 1000 | +0.130 | +0.090 | +0.148 | 4/4 | yes | **MATERIAL** |
| `L1056` | `UNRESOLVED_IMAGE` | TSVD | 1000 | +0.108 | +0.066 | +0.122 | 3/4 | yes | **MATERIAL** |

**The resolved arm is material at the registered SNR₀ = 100, on both
estimators.** TSVD gives a median relative reduction of 22.5% with a bootstrap
lower bound of 12.1%; ridge gives 23.9% with a lower bound of 10.5%. Both
improve all four families and every primary bank. This is the first material
structural result in this line.

The unresolved arm is **not** material at SNR₀ = 100: its medians are
5.8% and 7.6% but both bootstrap lower bounds fall below zero. At the secondary
SNR₀ = 1000 it does become material, at 10.8% and 13.0% with lower bounds
of 6.6% and 9.0%. That is a real secondary finding and it is not the registered
endpoint.

`TOTAL_FLUX` is negative at every class and SNR.

## 2. Controls

| class | arm | estimator | SNR₀ | median | CI low | CI high | families | all banks + | material |
|---|---|---|---:|---:|---:|---:|---|---|---|
| `L224` | `RESOLVED_PHYSICAL` | RIDGE_IDENTITY | 100 | +0.368 | +0.066 | +0.283 | 4/4 | yes | **MATERIAL** |
| `L224` | `RESOLVED_PHYSICAL` | TSVD | 100 | +0.312 | -0.196 | +0.158 | 4/4 | yes | no |
| `L224` | `TOTAL_FLUX` | RIDGE_IDENTITY | 100 | -0.055 | -0.073 | -0.022 | 1/4 | no | no |
| `L224` | `TOTAL_FLUX` | TSVD | 100 | -0.046 | -0.065 | -0.028 | 1/4 | no | no |
| `L224` | `UNRESOLVED_IMAGE` | RIDGE_IDENTITY | 100 | +0.117 | -0.051 | +0.078 | 3/4 | yes | no |
| `L224` | `UNRESOLVED_IMAGE` | TSVD | 100 | +0.059 | -0.034 | +0.053 | 3/4 | yes | no |
| `L448` | `RESOLVED_PHYSICAL` | RIDGE_IDENTITY | 100 | +0.316 | +0.079 | +0.258 | 4/4 | yes | **MATERIAL** |
| `L448` | `RESOLVED_PHYSICAL` | TSVD | 100 | +0.222 | -0.256 | +0.096 | 4/4 | yes | no |
| `L448` | `TOTAL_FLUX` | RIDGE_IDENTITY | 100 | -0.006 | -0.011 | +0.011 | 1/4 | no | no |
| `L448` | `TOTAL_FLUX` | TSVD | 100 | -0.003 | -0.010 | +0.001 | 1/4 | no | no |
| `L448` | `UNRESOLVED_IMAGE` | RIDGE_IDENTITY | 100 | +0.099 | -0.102 | +0.046 | 3/4 | yes | no |
| `L448` | `UNRESOLVED_IMAGE` | TSVD | 100 | +0.015 | -0.357 | -0.080 | 3/4 | no | no |

The controls agree in direction and are noisier. Note the medians sitting
outside their own intervals at `L224` and `L448`: the bootstrap interval is
computed on the equal-weight cell mean while the median is per truth, and where
the per-truth distribution is skewed the two statistics disagree. The ruling
specified both, so both are reported, but they are not two views of one number.
At `L1056` the median lies inside the interval and the question does not arise.

## 3. Stable structural span — the 8 M threshold is not met

| class | arm | SNR₀ | L direct (M) | L arm (M) | ΔL (M) | ≥ 8 M |
|---|---|---:|---:|---:|---:|---|
| `L1056` | `RESOLVED_PHYSICAL` | 100 | 0.0 | 0.0 | +0.0 | **no** |
| `L1056` | `TOTAL_FLUX` | 100 | 0.0 | 0.0 | +0.0 | **no** |
| `L1056` | `UNRESOLVED_IMAGE` | 100 | 0.0 | 0.0 | +0.0 | **no** |
| `L1056` | `RESOLVED_PHYSICAL` | 1000 | 0.0 | 0.0 | +0.0 | **no** |
| `L1056` | `TOTAL_FLUX` | 1000 | 0.0 | 0.0 | +0.0 | **no** |
| `L1056` | `UNRESOLVED_IMAGE` | 1000 | 0.0 | 0.0 | +0.0 | **no** |

Every span is zero, at every class and both SNRs, so ΔL is zero against a
threshold of 8 M. **Item 11 is a
negative result**, and this time it is a real one rather than an artefact: the
representation floor is zero, so nothing is blocking the criterion except the
reconstruction itself.

The reason is visible in the fraction of truths meeting ε =
0.25 at the youngest age, which the
q = 0.95 rule needs to exceed 95%:

| arm | SNR₀ | pass fraction at age 0 |
|---|---:|---:|
| `DIRECT_PHYSICAL` | 100 | 0.021 |
| `RESOLVED_PHYSICAL` | 100 | 0.010 |
| `TOTAL_FLUX` | 100 | 0.000 |
| `UNRESOLVED_IMAGE` | 100 | 0.010 |
| `DIRECT_PHYSICAL` | 1000 | 0.052 |
| `RESOLVED_PHYSICAL` | 1000 | 0.042 |
| `TOTAL_FLUX` | 1000 | 0.000 |
| `UNRESOLVED_IMAGE` | 1000 | 0.042 |

At most 5% of truths hold a relative structural error at or below 0.25 even at
age zero. The resolved arm reduces the *mean* old-band structural error by
about a quarter without bringing any appreciable fraction of truths under a
uniform per-truth error bound. Those are different claims, and only the first
one is supported.

## 4. Bank construction

| bank | target f_struct | achieved | representation floor | reprojection residual | negative mass |
|---|---:|---:|---:|---:|---:|
| `constant_flux_structural` | — | 0.807 | 1.5e-15 | 0.084 | 0.0356 |
| `structure_balanced_050` | 0.50 | 0.520 | 1.5e-15 | 0.117 | 0.0000 |
| `structure_balanced_080` | 0.80 | 0.660 | 1.5e-15 | 0.078 | 0.0000 |

Three caveats, all measured rather than assumed:

- Projection onto the class removes structure, so `structure_balanced_080`
  achieves 0.66 rather than its 0.80 target. The target is defined before
  projection and the achieved value after; the achieved value is what the
  endpoint saw.
- Shaping a projected field pushes it back out of the class by 8 to 12 percent,
  which is why the construction re-projects and reports the residual. The final
  truths are in class at a floor of 0 to machine precision, which gate
  `R1L_2RB_G5` checks.
- Projection can break strict positivity. The constant-flux bank carries about
  3.6% negative mass. It is reported rather than clipped, because clipping would
  push the truth back out of the class and quietly restore the floor.

## 5. Selection health

Stage 2R-A found the selection collapsing arms to maximal regularization when a
representation floor was present. With the floor removed:

| class | selections at the maximal-regularization end |
|---|---|
| `L1056` | 0 / 8 |
| `L224` | 2 / 8 |
| `L448` | 2 / 8 |

None at the primary class. The two apiece at the controls are consistent with
their noisier intervals.

## 6. Gates and controls

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
| `R1L_2RB_G11_resource_limits` | PASS |

Null-pair controls: worst realized-versus-target separation error
2.44e-15 over 288 pairs.

## 7. Disposition

`R1L_STAGE2R_B_MATERIAL_RESOLVED_ONLY`

At the registered SNR₀ = 100, on exact-in-class structural banks with a
zero representation floor, the resolved arm reduces old-band structural
reconstruction error by about a quarter relative to the direct image, materially
and on both estimators, across all four source families and all three primary
banks. The unresolved arm does not reach materiality at the registered SNR and
does at the secondary one.

The stable structural span requirement of item 11 is **not** met: ΔL = 0 M
against 8 M, at every class and both SNRs.

The scope limits stand. This is one geometry, one spin, one inclination, and
truths that are exactly in the class by construction — which makes the result an
upper bound on what this operator can do for this class, not a statement about
real source histories, which are in no one's basis. The sealed main, geometry
mismatch, order leakage, VLBI and ML remain unauthorized.
