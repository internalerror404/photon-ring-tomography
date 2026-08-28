# HMT-2 sealed held-out main

Freeze `HMT2_SEALED_MAIN_V1`, run `HMT2M_20260828T064757Z_2ba66f02`.
Execution commit `9713af2caf3f`, tree clean:
true. 60 held-out truths,
1234 s.

## Disposition

`HMT2_MAIN_PHYSICAL_MORPHOLOGY_RECOVERY_PASS` — all 19 gates pass.

The resolved arm in the claim-bearing class reduces the all-state morphology
error against the direct image on both targets and both classical estimators,
at a materiality floor declared before the bank was drawn: a median reduction
of at least 0.10 with a bootstrap lower bound
above 0.05.

**What that does and does not say is the substance of this report, and the
qualifications are as much a result as the token is.**

## 1. The sealing held

Stage A decided six source gates before any operator was imported, and the bank
hashes were committed before stage B ran. Stage B rebuilt the bank and matched
every hash: 0
mismatches. The 16 hyperparameters came from the stage 1 selection split
unchanged and this runner contains no sweep.

The first attempt at stage B reported 60 of 60 hash mismatches. The gate was
right and the bank was fine: the state labels had been hashed with Python's
builtin `hash`, which salts string hashing per process, so a hash written in
stage A could never match one recomputed in stage B. That is the third
appearance of this bug in the campaign, and it now has an automated check
rather than a memory of it.

## 2. Primary endpoint, claim-bearing class, SNR₀ = 100

| arm | estimator | physical | CI low | material | class-cond | material | non-dead | material |
|---|---|---|---|---|---|---|---|---|
| `RESOLVED_PHYSICAL` | RIDGE_IDENTITY | +0.164 | +0.116 | **MATERIAL** | +0.158 | **MATERIAL** | +0.158 | **MATERIAL** |
| `RESOLVED_PHYSICAL` | TSVD | +0.133 | +0.101 | **MATERIAL** | +0.160 | **MATERIAL** | +0.142 | **MATERIAL** |
| `TOTAL_FLUX` | RIDGE_IDENTITY | -0.020 | -0.050 | no | -0.024 | no | -0.023 | no |
| `TOTAL_FLUX` | TSVD | +0.036 | -0.025 | no | +0.045 | no | +0.045 | no |
| `UNRESOLVED_IMAGE` | RIDGE_IDENTITY | +0.000 | +0.000 | no | +0.000 | no | +0.000 | no |
| `UNRESOLVED_IMAGE` | TSVD | +0.015 | -0.042 | no | +0.009 | no | +0.015 | no |

The reduction survives removal of dead states at the same floor, so it is not
an artifact of a near-null estimator being right about nothing being there.
Both controls behave: `TOTAL_FLUX` is negative or non-material, and
`UNRESOLVED_IMAGE` reaches +0.0149
at best, so the benefit is attributable to resolving the orders rather than to
the extra photons an unresolved second image also carries.

The representation-limited control class:

| arm | estimator | physical | CI low | material |
|---|---|---|---|---|
| `RESOLVED_PHYSICAL` | RIDGE_IDENTITY | +0.101 | +0.064 | **MATERIAL** |
| `RESOLVED_PHYSICAL` | TSVD | +0.061 | +0.033 | no |
| `TOTAL_FLUX` | RIDGE_IDENTITY | +0.011 | -0.035 | no |
| `TOTAL_FLUX` | TSVD | +0.044 | +0.002 | no |
| `UNRESOLVED_IMAGE` | RIDGE_IDENTITY | +0.000 | +0.000 | no |
| `UNRESOLVED_IMAGE` | TSVD | +0.000 | +0.000 | no |

Its resolved arm reaches materiality under ridge and not under TSVD, which is
the representation limit showing up as a weaker and less robust effect in the
same run.

## 3. Two-feature recovery does not reach materiality anywhere

Stable multi-resolved states, resolved arm, both estimators and both SNRs. Cost
is normalised so 1.0 is one whole feature gained or lost.

| class | estimator | SNR₀ | direct | arm | reduction | CI low | material |
|---|---|---|---|---|---|---|---|
| `L448_contrast` | RIDGE_IDENTITY | 100 | 1.505 | 1.477 | -0.039 | -0.142 | no |
| `L448_contrast` | RIDGE_IDENTITY | 1000 | 1.505 | 1.477 | -0.033 | -0.122 | no |
| `L448_contrast` | TSVD | 100 | 1.545 | 1.572 | -0.060 | -0.142 | no |
| `L448_contrast` | TSVD | 1000 | 1.545 | 1.573 | -0.061 | -0.147 | no |
| `L896_radial_enriched` | RIDGE_IDENTITY | 100 | 1.432 | 1.208 | +0.137 | -0.014 | no |
| `L896_radial_enriched` | RIDGE_IDENTITY | 1000 | 1.428 | 1.203 | +0.159 | +0.024 | no |
| `L896_radial_enriched` | TSVD | 100 | 1.493 | 1.302 | +0.187 | -0.083 | no |
| `L896_radial_enriched` | TSVD | 1000 | 1.494 | 1.300 | +0.164 | -0.044 | no |

**Not one cell is material.** In the claim-bearing class the point estimates are
0.14 to 0.19, which looks encouraging, and every interval reaches below the
floor. The absolute cost stays between 1.20 and 1.30 -- the reconstruction is
still getting more than one whole feature wrong on average. In the control class
the resolved arm is negative.

So the sealed main reproduces, on held-out truths, exactly the split the stage 1
completion found: the description of the past improves materially; the recovery
of a resolved two-feature set does not.

## 4. The aggregate is carried by two families of six

| family | estimator | physical | CI low | material |
|---|---|---|---|---|
| `circular_hotspot_trajectory` | RIDGE_IDENTITY | -0.022 | -0.200 | no |
| `circular_hotspot_trajectory` | TSVD | -0.051 | -0.115 | no |
| `flare_birth_motion_decay` | RIDGE_IDENTITY | +0.381 | +0.191 | **MATERIAL** |
| `flare_birth_motion_decay` | TSVD | +0.377 | +0.065 | **MATERIAL** |
| `m1_rotating_crescent` | RIDGE_IDENTITY | +0.204 | +0.030 | no |
| `m1_rotating_crescent` | TSVD | +0.212 | +0.049 | no |
| `m2_structural_mode` | RIDGE_IDENTITY | +0.320 | +0.146 | **MATERIAL** |
| `m2_structural_mode` | TSVD | +0.243 | +0.165 | **MATERIAL** |
| `plunging_feature` | RIDGE_IDENTITY | +0.111 | +0.084 | **MATERIAL** |
| `plunging_feature` | TSVD | +0.097 | +0.071 | no |
| `two_hotspot_trajectories` | RIDGE_IDENTITY | +0.178 | -0.006 | no |
| `two_hotspot_trajectories` | TSVD | +0.135 | -0.087 | no |

5 of 12 family-estimator cells reach materiality, and they concentrate in
`flare_birth_motion_decay` and `m2_structural_mode`.
`circular_hotspot_trajectory` -- the simplest family in the bank, a single
moving spot -- is **negative** under both estimators. `two_hotspot_trajectories`
does not reach materiality under either.

With ten truths per family these intervals are wide and no family-level claim is
supported either way. But the headline is not a uniform improvement across the
source model; it is a large gain on two families and roughly nothing on the
simplest one, and it should not be quoted as though the operator helps
everywhere.

## 5. There is still no stable morphology interval

| arm | estimator | L_stable (M) | mean reach (M) | fraction reaching |
|---|---|---|---|---|
| `DIRECT_PHYSICAL` | RIDGE_IDENTITY | 0.0 | 4.20 | 0.196 |
| `DIRECT_PHYSICAL` | TSVD | 0.0 | 2.43 | 0.138 |
| `RESOLVED_PHYSICAL` | RIDGE_IDENTITY | 0.0 | 3.98 | 0.179 |
| `RESOLVED_PHYSICAL` | TSVD | 0.0 | 2.14 | 0.133 |
| `TOTAL_FLUX` | RIDGE_IDENTITY | 0.0 | 1.63 | 0.121 |
| `TOTAL_FLUX` | TSVD | 0.0 | 1.69 | 0.121 |
| `UNRESOLVED_IMAGE` | RIDGE_IDENTITY | 0.0 | 3.91 | 0.188 |
| `UNRESOLVED_IMAGE` | TSVD | 0.0 | 0.28 | 0.029 |

Zero for every arm at the declared tolerance and quantile. The resolved arm's
mean reach is *lower* than the direct image's under both estimators, so it does
not even extend how far back the morphology stays within tolerance on average.
A material reduction in a time-averaged error and a history that holds together
over an interval remain different things, and only the first is established.

## 6. Saturation

56% of direct-image states
sit at the measure's ceiling, falling to
42% for the resolved arm.
When more than half the states are at the maximum, the mean is substantially
counting how many states failed outright, and the improvement is mostly fewer
total failures rather than uniformly better estimates. This is disclosed per
cell because the freeze required it, and it qualifies the headline rather than
overturning it.

## 7. Gates

| gate | status | measured | threshold |
|---|---|---|---|
| `HMT2M_G7_adjoint` | PASS | 2.379e-15 | 1e-08 |
| `HMT2M_G8_operator_truth_identity` | PASS | 7.759e-16 | 1e-09 |
| `HMT2M_G9_stage_a_source_gates_passed` | PASS | 0 | 0 |
| `HMT2M_G10_bank_hashes_match_committed` | PASS | 0 | 0 |
| `HMT2M_G11_sealed_hyperparameters_used_unchanged` | PASS | 0 | 0 |
| `HMT2M_G12_both_targets_reported` | PASS | 0 | 0 |
| `HMT2M_G13_no_state_excluded_from_primary` | PASS | 0 | 0 |
| `HMT2M_G14_blended_not_forced_into_two_tracks` | PASS | 0 | 0 |
| `HMT2M_G15_all_required_companions_emitted` | PASS | 0 | 0 |
| `HMT2M_G16_estimator_scope` | PASS | 0 | 0 |
| `HMT2M_G19_resource_limits` | PASS | 1219 | 14400 |
| `HMT2M_G17_endpoint_lineage_firewall` | PASS | 0 | 0 |
| `HMT2M_G1_pinned_numerical_environment` | PASS | 1 | 1 |
| `HMT2M_G2_commitments_reproduce` | PASS | 1 | 1 |
| `HMT2M_G3_disjoint_from_every_earlier_bank` | PASS | 0 | 0 |
| `HMT2M_G4_contrast_zero_spatial_mean` | PASS | 2.352e-17 | 1e-10 |
| `HMT2M_G5_total_emissivity_nonnegative` | PASS | 0 | 0 |
| `HMT2M_G6_source_classification_stable` | PASS | 0 | 3660 |
| `HMT2M_G18_declared_gate_coverage` | PASS | 0 | 0 |

## 8. Scope

One geometry, one spin, one inclination. Six analytic families at their
original declared ranges with no separation cut, so the bank contains the
blended and ambiguous states the endpoint was built to score. Held-out truths,
disjoint from every earlier bank in the campaign. Classical estimators only.
Absolute all-state error for the resolved arm remains
0.598 on a scale whose worst case is 1.0.

The honest summary: resolving the photon-ring orders materially improves a
resolution-aware description of the past on held-out sources, driven mainly by
two of six families, without delivering resolved two-feature recovery and
without producing any interval over which the recovered morphology holds.

**STOP.** Item 12. Order leakage, geometry mismatch, VLBI, machine learning and
a new pixel-movie campaign remain unauthorized.
