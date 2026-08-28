# HMT-2 stage 1 — resolution-aware morphology validation

Freeze `HMT2_STAGE1_RESOLUTION_AWARE_MORPHOLOGY_VALIDATION_V0`, run `HMT2S1_20260828T050457Z_2ba66f02`.
Execution commit `c7698040a726`, tree clean:
true. 72 truths across
2 splits, 2715 s.

## Disposition

`HMT2_S1_PHYSICAL_MORPHOLOGY_RECOVERY_PASS`

All 15 gates pass. Both declared targets improve for the
resolved arm in the primary class, on both classical estimators, with paired
bootstrap intervals excluding zero.

**Read the primary and the secondary endpoints together.** The all-state
morphology error improves materially. The conditional set-valued recovery on
cleanly resolved two-feature states barely moves and remains above one whole
feature of error. Those are different claims and this run separates them, which
is what the two-endpoint structure was built for.

## 1. Primary endpoint — all-state morphology error, primary class

Median relative reduction against the direct image, paired truth-cluster
bootstrap, at SNR₀ = 100. Every state is scored by the measure it
supports and none is excluded.

| class | arm | estimator | SNR₀ | phys | phys CI low | phys | class-cond | CC CI low | CC |
|---|---|---|---|---|---|---|---|---|---|
| `L896_radial_enriched` | `RESOLVED_PHYSICAL` | RIDGE_IDENTITY | 100 | +0.130 | +0.083 | **yes** | +0.146 | +0.093 | **yes** |
| `L896_radial_enriched` | `RESOLVED_PHYSICAL` | TSVD | 100 | +0.120 | +0.071 | **yes** | +0.122 | +0.068 | **yes** |
| `L896_radial_enriched` | `TOTAL_FLUX` | RIDGE_IDENTITY | 100 | -0.028 | -0.070 | no | -0.029 | -0.071 | no |
| `L896_radial_enriched` | `TOTAL_FLUX` | TSVD | 100 | +0.037 | -0.000 | no | +0.038 | -0.007 | no |
| `L896_radial_enriched` | `UNRESOLVED_IMAGE` | RIDGE_IDENTITY | 100 | +0.000 | +0.000 | no | +0.000 | +0.000 | no |
| `L896_radial_enriched` | `UNRESOLVED_IMAGE` | TSVD | 100 | +0.030 | -0.041 | no | +0.014 | -0.057 | no |

The representation-limited control class:

| class | arm | estimator | SNR₀ | phys | phys CI low | phys | class-cond | CC CI low | CC |
|---|---|---|---|---|---|---|---|---|---|
| `L448_contrast` | `RESOLVED_PHYSICAL` | RIDGE_IDENTITY | 100 | +0.071 | +0.038 | **yes** | +0.095 | +0.074 | **yes** |
| `L448_contrast` | `RESOLVED_PHYSICAL` | TSVD | 100 | +0.089 | +0.028 | **yes** | +0.116 | +0.050 | **yes** |
| `L448_contrast` | `TOTAL_FLUX` | RIDGE_IDENTITY | 100 | +0.003 | -0.068 | no | -0.004 | -0.078 | no |
| `L448_contrast` | `TOTAL_FLUX` | TSVD | 100 | +0.054 | +0.026 | **yes** | +0.052 | +0.030 | **yes** |
| `L448_contrast` | `UNRESOLVED_IMAGE` | RIDGE_IDENTITY | 100 | +0.000 | -0.000 | no | +0.000 | -0.000 | no |
| `L448_contrast` | `UNRESOLVED_IMAGE` | TSVD | 100 | +0.000 | -0.000 | no | +0.000 | -0.000 | no |

At the secondary SNR:

| class | arm | estimator | SNR₀ | phys | phys CI low | phys | class-cond | CC CI low | CC |
|---|---|---|---|---|---|---|---|---|---|
| `L896_radial_enriched` | `RESOLVED_PHYSICAL` | RIDGE_IDENTITY | 1000 | +0.141 | +0.111 | **yes** | +0.150 | +0.112 | **yes** |
| `L896_radial_enriched` | `RESOLVED_PHYSICAL` | TSVD | 1000 | +0.122 | +0.101 | **yes** | +0.119 | +0.100 | **yes** |

**The physical target moves with the class-conditional one.** That is the
result item 14 was written to test: improvement on `CLASS_CONDITIONAL` alone
would be a statement about the class, and here the reconstruction also improves
against the analytic source, which is the claim that means something physical.

## 2. The improvement is not carried by one kind of state

Mean error by the measure each state's label selected, TSVD at SNR₀ =
100, physical target:

| class | arm | assignment | blended | amplitude |
|---|---|---|---|---|
| `L448_contrast` | `DIRECT_PHYSICAL` | 0.8165 | 0.4636 | 0.9197 |
| `L448_contrast` | `RESOLVED_PHYSICAL` | 0.7730 | 0.3863 | 0.5745 |
| `L448_contrast` | `TOTAL_FLUX` | 0.7848 | 0.5147 | 0.6764 |
| `L448_contrast` | `UNRESOLVED_IMAGE` | 0.8171 | 0.4786 | 0.8136 |
| `L896_radial_enriched` | `DIRECT_PHYSICAL` | 0.7637 | 0.4697 | 0.7938 |
| `L896_radial_enriched` | `RESOLVED_PHYSICAL` | 0.6822 | 0.3749 | 0.5601 |
| `L896_radial_enriched` | `TOTAL_FLUX` | 0.7403 | 0.5177 | 0.7283 |
| `L896_radial_enriched` | `UNRESOLVED_IMAGE` | 0.7397 | 0.3999 | 0.7336 |

The resolved arm in the primary class beats the direct image on **all three**
measure kinds, so the headline number is not an artifact of one state class
dominating. That check matters because the endpoint has a soft spot, described
next.

**A near-null estimator is right about nothing being there.** On `DEAD` states
the measure is amplitude alone, and an estimator that reports almost no
amplitude scores well for free. `TOTAL_FLUX` -- a single number per time, with
no spatial information at all -- reaches
0.676 on amplitude against
the direct image's 0.920,
and that is most of why it shows a positive reduction in the control class.
Dead states are 9.0% of this bank. The behaviour is
correct in itself -- reporting large amplitude where nothing exists *is* an
error, and dropping dead states is what item 16 forbids -- but it means the
all-state number should never be read without the per-kind split above.

## 3. Secondary conditional endpoint — stable multi-resolved states only

Normalised unbalanced assignment cost, where 1.0 is the cost of one whole
feature gained or lost. TSVD, SNR₀ = 100,
12 truths carrying such states.

| class | arm | direct | arm | |
|---|---|---|---|---|
| `L896_radial_enriched` | `RESOLVED_PHYSICAL` | 1.451 | 1.376 | better |
| `L896_radial_enriched` | `TOTAL_FLUX` | 1.451 | 1.449 | better |
| `L896_radial_enriched` | `UNRESOLVED_IMAGE` | 1.451 | 1.720 | worse |
| `L448_contrast` | `RESOLVED_PHYSICAL` | 1.493 | 1.869 | worse |
| `L448_contrast` | `TOTAL_FLUX` | 1.493 | 1.479 | better |
| `L448_contrast` | `UNRESOLVED_IMAGE` | 1.493 | 1.495 | worse |

**This is the weak result, and it is the honest one.** On states where the
source genuinely presents two resolved features, the primary class's resolved
arm improves the cost from 1.451 to
1.376 -- about
5%,
and still above 1.0, meaning the reconstruction is on average getting more than
one whole feature wrong. In the control class the resolved arm makes it *worse*,
and the unresolved arm makes it worse in the primary class.

So resolving the orders improves the description of the past as a whole, and
does not yet deliver recovery of a resolved two-feature set. The primary
endpoint and this one are answering different questions and giving different
answers, which is the distinction HMT-1 could not draw because it asked every
state for a peak position.

## 4. Controls and selection

`UNRESOLVED_IMAGE` does not reach improvement in either class, so the benefit
is attributable to resolving the orders rather than to the extra photons an
unresolved second image also carries. `TOTAL_FLUX` is negative or
non-significant in the primary class.

0 of 16 selections landed at
the maximal end of their grid, and selection errors run
0.668 to 0.797 on a scale
where 1.0 is the worst possible. No collapse.

Bank composition: single-resolved 57.7%,
multi-resolved 29.1%, blended
3.4%, dead 9.0%, ambiguous
0.9%.

## 5. Gates

| gate | status | measured | threshold |
|---|---|---|---|
| `HMT2S1_G1_pinned_numerical_environment` | PASS | 1 | 1 |
| `HMT2S1_G2_commitments_reproduce` | PASS | 1 | 1 |
| `HMT2S1_G3_bank_disjoint_from_stage_0_and_hmt1` | PASS | 0 | 0 |
| `HMT2S1_G4_contrast_zero_spatial_mean` | PASS | 1.798e-17 | 1e-10 |
| `HMT2S1_G5_total_emissivity_nonnegative` | PASS | 0 | 0 |
| `HMT2S1_G6_adjoint` | PASS | 2.379e-15 | 1e-08 |
| `HMT2S1_G7_operator_truth_identity` | PASS | 7.759e-16 | 1e-09 |
| `HMT2S1_G8_both_targets_reported` | PASS | 0 | 0 |
| `HMT2S1_G9_no_state_excluded_from_primary` | PASS | 0 | 0 |
| `HMT2S1_G10_blended_not_forced_into_two_tracks` | PASS | 0 | 0 |
| `HMT2S1_G11_secondary_restricted_to_stable_states` | PASS | 0 | 0 |
| `HMT2S1_G12_estimator_scope` | PASS | 0 | 0 |
| `HMT2S1_G13_no_sealed_bank_created` | PASS | 0 | 0 |
| `HMT2S1_G15_resource_limits` | PASS | 2713 | 14400 |
| `HMT2S1_G14_declared_gate_coverage` | PASS | 0 | 0 |

## 6. Scope

One geometry, one spin, one inclination. Six analytic families whose ranges
were preserved with no separation cut, so the bank contains the blended and
ambiguous states that HMT-1's endpoint could not represent. Absolute errors
remain high -- the all-state error is 0.660 for
the resolved arm on a scale where 1.0 is the worst case -- so this is a
material improvement in a regime that is still far from accurate recovery.

No sealed held-out main was created and none is authorized. Classical
estimators only.

**STOP** for reviewer adjudication, per item 18. Order leakage, geometry
mismatch, VLBI, machine learning and a new pixel-movie campaign remain
unauthorized.
