# HMT-1 — historical feature and contrast tomography, validation

Freeze `HMT_1_HISTORICAL_FEATURE_AND_CONTRAST_TOMOGRAPHY_V0`, run `HMT1_20260827T222531Z_2ba66f02`.
Execution commit `1ecd067586c3`, tree clean:
true, preregistered: true.


## 1. What this run asked

R1L established what a compact temporal basis can and cannot recover about the
past, and it stopped on a structural endpoint measured in reconstruction error.
That endpoint is a norm on a coefficient vector. It is not the thing anyone
actually wants to know, which is whether the *description* of the past survives:
where a feature was, how it moved, how bright it was, when it appeared and when
it faded.

HMT-1 changes the endpoint to those quantities and changes the source model to
one that can carry them honestly. The field is a positive axisymmetric
background carrying a signed fluctuation, `j = b(r,t) + dj(r,phi,t)`, with
`b > 0`, `dj` of zero azimuthal mean at every radius and age, and `b + dj >= 0`.
The operator sees the total. Only `dj` is reconstructed, and every `m = 0`
direction is projected out of the reconstruction class, so a background error
cannot hide inside a feature result.

That split is what separates this from the signed constant-flux bank R1L had to
disqualify. There the *emissivity* went negative, which is not a source. Here
the physical field is positive by construction and the modelled fluctuation is
free to change sign, which is what a fluctuation does.

Geometry: spin a* = 0.5, inclination
50.0 deg. 6 declared feature families,
3 background regimes, 4 arms,
288 truths.

## 1b. Three runs, and what the first two found

This is the third execution of this freeze. The first two are not reported as
results, and what they caught is worth recording, because in each case the run
would have produced a publishable-looking number.

**Run 1** failed `HMT1_G13`, the coverage gate, which exists to catch a gate the
freeze declares and the scorer never emits. It caught two, in opposite
directions: `G10b` had been registered with its reading written into the
threshold field as prose and was never implemented, and `G4b` was emitted
without being declared, with a hard-coded exemption in the coverage
computation keeping it quiet. `G10b` was implemented rather than withdrawn --
`G10` only asks that extraction be repeatable, which an extractor reading the
wrong position also satisfies.

**Run 2** failed `G12`: 22 of 24 arm-estimator cells pinned their selection at
the most-regularized end of the grid, every arm collapsed onto the same
near-null estimator, and the endpoint came out null. The tempting reading is
that this endpoint has a representation floor and the selection rule is
degenerate for it, which is the pathology R1L already met. That reading was
wrong. Recording the whole selection sweep rather than only its argmin showed
selection errors of order 1e12 to 1e17, and a normalised error cannot be 1e12.

The freeze defines the aggregate over "the family's declared normalised
parameter errors" and declares a different parameter list per family. The
scorer used one global list for all six. A pure `cos(2 phi)` pattern has no
`m = 1` content -- measured at 1.6e-17, which is round-off -- so dividing by
"max over ages of `|a_m1|`" divided by round-off. An estimator can only shrink
a term like that by driving its reconstruction to zero, so the selection rule
was not degenerate: it was correctly minimising an error dominated by a
division by zero.

Run 2 also revealed that the oracle regime was not an oracle. The freeze says
`b` is supplied *exactly*, but every regime was routed through the same
least-squares design fit, leaving a 9% background residual inside the regime
whose entire purpose is to have none. Its background error is now exactly zero,
which is visible in section 4.

Both runs are the reason the disposition logic changed. The stop token was
selected from the science before any gate had been emitted, so run 2 failed two
gates and still reported `HMT1_NO_MATERIAL_EFFECT`. A null result is exactly
what a broken run looks like from the outside, and that one would have reported
a null produced by a divide-by-zero. A failed gate now forces
`HMT1_IMPLEMENTATION_DEFECT` and the science reading is withheld.

## 2. Primary endpoint at SNR₀ = 100

Median relative reduction in old-band feature error against the direct image,
with a paired truth-cluster bootstrap interval. Materiality is a median
relative reduction of at least 0.10 with a
bootstrap lower bound above 0.05, on both
classical estimators -- the same numeric standard R1L used, so the two studies
are comparable.

| regime | arm | estimator | SNR₀ | median | CI low | CI high | families | truths | material |
|---|---|---|---|---|---|---|---|---|---|
| `estimated_from_data` | `RESOLVED_PHYSICAL` | RIDGE_IDENTITY | 100 | +0.217 | +0.170 | +0.263 | 5/6 | 48 | **MATERIAL** |
| `estimated_from_data` | `RESOLVED_PHYSICAL` | TSVD | 100 | +0.156 | +0.105 | +0.213 | 6/6 | 48 | **MATERIAL** |
| `estimated_from_data` | `TOTAL_FLUX` | RIDGE_IDENTITY | 100 | -0.087 | -0.125 | -0.056 | 1/6 | 48 | no |
| `estimated_from_data` | `TOTAL_FLUX` | TSVD | 100 | -0.109 | -0.187 | -0.038 | 2/6 | 48 | no |
| `estimated_from_data` | `UNRESOLVED_IMAGE` | RIDGE_IDENTITY | 100 | +0.063 | -0.000 | +0.176 | 4/6 | 48 | no |
| `estimated_from_data` | `UNRESOLVED_IMAGE` | TSVD | 100 | +0.072 | -0.100 | +0.122 | 5/6 | 48 | no |
| `joint_inversion` | `RESOLVED_PHYSICAL` | RIDGE_IDENTITY | 100 | +0.202 | +0.156 | +0.260 | 6/6 | 48 | **MATERIAL** |
| `joint_inversion` | `RESOLVED_PHYSICAL` | TSVD | 100 | +0.180 | +0.143 | +0.234 | 6/6 | 48 | **MATERIAL** |
| `joint_inversion` | `TOTAL_FLUX` | RIDGE_IDENTITY | 100 | -0.070 | -0.106 | -0.033 | 3/6 | 48 | no |
| `joint_inversion` | `TOTAL_FLUX` | TSVD | 100 | -0.030 | -0.077 | +0.008 | 2/6 | 48 | no |
| `joint_inversion` | `UNRESOLVED_IMAGE` | RIDGE_IDENTITY | 100 | +0.071 | -0.010 | +0.186 | 5/6 | 48 | no |
| `joint_inversion` | `UNRESOLVED_IMAGE` | TSVD | 100 | +0.101 | +0.031 | +0.174 | 5/6 | 48 | no |
| `oracle_known` | `RESOLVED_PHYSICAL` | RIDGE_IDENTITY | 100 | +0.251 | +0.218 | +0.291 | 6/6 | 48 | **MATERIAL** |
| `oracle_known` | `RESOLVED_PHYSICAL` | TSVD | 100 | +0.182 | +0.145 | +0.214 | 6/6 | 48 | **MATERIAL** |
| `oracle_known` | `TOTAL_FLUX` | RIDGE_IDENTITY | 100 | -0.037 | -0.076 | -0.006 | 3/6 | 48 | no |
| `oracle_known` | `TOTAL_FLUX` | TSVD | 100 | -0.045 | -0.098 | -0.007 | 2/6 | 48 | no |
| `oracle_known` | `UNRESOLVED_IMAGE` | RIDGE_IDENTITY | 100 | +0.111 | +0.067 | +0.180 | 5/6 | 48 | no |
| `oracle_known` | `UNRESOLVED_IMAGE` | TSVD | 100 | +0.086 | +0.015 | +0.149 | 5/6 | 48 | no |

At the secondary SNR₀ = 1000:

| regime | arm | estimator | SNR₀ | median | CI low | CI high | families | truths | material |
|---|---|---|---|---|---|---|---|---|---|
| `estimated_from_data` | `RESOLVED_PHYSICAL` | RIDGE_IDENTITY | 1000 | +0.178 | +0.126 | +0.225 | 6/6 | 48 | **MATERIAL** |
| `estimated_from_data` | `RESOLVED_PHYSICAL` | TSVD | 1000 | +0.144 | +0.068 | +0.189 | 6/6 | 48 | **MATERIAL** |
| `estimated_from_data` | `TOTAL_FLUX` | RIDGE_IDENTITY | 1000 | -0.101 | -0.120 | -0.073 | 0/6 | 48 | no |
| `estimated_from_data` | `TOTAL_FLUX` | TSVD | 1000 | -0.104 | -0.161 | -0.038 | 2/6 | 48 | no |
| `estimated_from_data` | `UNRESOLVED_IMAGE` | RIDGE_IDENTITY | 1000 | +0.045 | -0.035 | +0.175 | 4/6 | 48 | no |
| `estimated_from_data` | `UNRESOLVED_IMAGE` | TSVD | 1000 | +0.050 | -0.064 | +0.135 | 5/6 | 48 | no |
| `joint_inversion` | `RESOLVED_PHYSICAL` | RIDGE_IDENTITY | 1000 | +0.207 | +0.166 | +0.284 | 6/6 | 48 | **MATERIAL** |
| `joint_inversion` | `RESOLVED_PHYSICAL` | TSVD | 1000 | +0.207 | +0.148 | +0.259 | 6/6 | 48 | **MATERIAL** |
| `joint_inversion` | `TOTAL_FLUX` | RIDGE_IDENTITY | 1000 | -0.066 | -0.129 | -0.038 | 1/6 | 48 | no |
| `joint_inversion` | `TOTAL_FLUX` | TSVD | 1000 | -0.035 | -0.072 | -0.002 | 2/6 | 48 | no |
| `joint_inversion` | `UNRESOLVED_IMAGE` | RIDGE_IDENTITY | 1000 | +0.060 | +0.015 | +0.149 | 5/6 | 48 | no |
| `joint_inversion` | `UNRESOLVED_IMAGE` | TSVD | 1000 | +0.097 | +0.027 | +0.163 | 5/6 | 48 | no |
| `oracle_known` | `RESOLVED_PHYSICAL` | RIDGE_IDENTITY | 1000 | +0.224 | +0.188 | +0.283 | 6/6 | 48 | **MATERIAL** |
| `oracle_known` | `RESOLVED_PHYSICAL` | TSVD | 1000 | +0.171 | +0.113 | +0.205 | 6/6 | 48 | **MATERIAL** |
| `oracle_known` | `TOTAL_FLUX` | RIDGE_IDENTITY | 1000 | -0.057 | -0.091 | -0.008 | 2/6 | 48 | no |
| `oracle_known` | `TOTAL_FLUX` | TSVD | 1000 | -0.059 | -0.089 | -0.018 | 1/6 | 48 | no |
| `oracle_known` | `UNRESOLVED_IMAGE` | RIDGE_IDENTITY | 1000 | +0.126 | +0.032 | +0.188 | 5/6 | 48 | no |
| `oracle_known` | `UNRESOLVED_IMAGE` | TSVD | 1000 | +0.080 | +0.016 | +0.155 | 5/6 | 48 | no |

## 3. Stable historical feature interval

The co-primary endpoint. How far back the recovered feature history stays
inside the registered tolerance, with the supremum taken *inside* the
probability, so the interval is one over which the description holds
throughout rather than one it merely touches.

| regime | arm | SNR₀ | epsilon | quantile | L_stable (M) | realizations |
|---|---|---|---|---|---|---|
| `estimated_from_data` | `DIRECT_PHYSICAL` | 100 | 0.25 | 0.95 | 0.0 | 192 |
| `estimated_from_data` | `RESOLVED_PHYSICAL` | 100 | 0.25 | 0.95 | 0.0 | 192 |
| `estimated_from_data` | `TOTAL_FLUX` | 100 | 0.25 | 0.95 | 0.0 | 192 |
| `estimated_from_data` | `UNRESOLVED_IMAGE` | 100 | 0.25 | 0.95 | 0.0 | 192 |
| `joint_inversion` | `DIRECT_PHYSICAL` | 100 | 0.25 | 0.95 | 0.0 | 192 |
| `joint_inversion` | `RESOLVED_PHYSICAL` | 100 | 0.25 | 0.95 | 0.0 | 192 |
| `joint_inversion` | `TOTAL_FLUX` | 100 | 0.25 | 0.95 | 0.0 | 192 |
| `joint_inversion` | `UNRESOLVED_IMAGE` | 100 | 0.25 | 0.95 | 0.0 | 192 |
| `oracle_known` | `DIRECT_PHYSICAL` | 100 | 0.25 | 0.95 | 0.0 | 192 |
| `oracle_known` | `RESOLVED_PHYSICAL` | 100 | 0.25 | 0.95 | 0.0 | 192 |
| `oracle_known` | `TOTAL_FLUX` | 100 | 0.25 | 0.95 | 0.0 | 192 |
| `oracle_known` | `UNRESOLVED_IMAGE` | 100 | 0.25 | 0.95 | 0.0 | 192 |

## 4. Background regimes

The regime that decides whether this is a paper-grade result is
`estimated_from_data`, where `b` is fit by a fixed low-order axisymmetric design
through the arm's own operator against the arm's own data. The oracle regime is
a ceiling, not a claim.

| regime | median rel. error | worst | worst bias | min estimate |
|---|---|---|---|---|
| `estimated_from_data` | 0.0154 | 0.0565 | 8.68e-15 | 0.175 |
| `joint_inversion` | 0.0145 | 0.0738 | 8.37e-15 | 0.183 |
| `oracle_known` | 0.0000 | 0.0000 | 0.00e+00 | 0.176 |

## 5. Verdicts by regime

Family agreement is read two ways, both declared before the run: as a fraction
(5 of 6) and as a count (3 of
6). Both are reported because they can disagree, and picking the one that
gives the nicer answer after seeing them is how a preregistration gets spent.

| regime | families improved | material | stable interval | pass |
|---|---|---|---|---|
| `oracle_known` | 6/6 | yes | no | no |
| `estimated_from_data` | 5/6 | yes | no | no |
| `joint_inversion` | 6/6 | yes | no | no |

## 6. Gates and controls

16 gates, 16 pass, 0 not.

| gate | status | measured | threshold |
|---|---|---|---|
| `HMT1_G1_pinned_numerical_environment` | PASS | 1 | 1 |
| `HMT1_G2_split_commitments_reproduce` | PASS | 1 | 1 |
| `HMT1_G3_split_disjointness` | PASS | 1 | 1 |
| `HMT1_G4_contrast_zero_spatial_mean` | PASS | 2.65e-17 | 1e-10 |
| `HMT1_G5_total_emissivity_nonnegative` | PASS | 0 | 0 |
| `HMT1_G6_background_strictly_positive` | PASS | 0 | 0 |
| `HMT1_G7_adjoint` | PASS | 3.193e-15 | 1e-08 |
| `HMT1_G8_operator_truth_identity` | PASS | 6.405e-16 | 1e-09 |
| `HMT1_G9_null_controls` | PASS | 0 | 0.05 |
| `HMT1_G10_feature_extraction_deterministic` | PASS | 0 | 1e-09 |
| `HMT1_G11_off_manifold_excluded_from_endpoints` | PASS | 0 | 0 |
| `HMT1_G12_no_maximal_regularization_collapse` | PASS | 0 | 0 |
| `HMT1_G4b_azimuthal_zero_mean` | PASS | 2.116e-16 | 1e-10 |
| `HMT1_G10b_truth_extraction_recovers_generative_parameters` | PASS | 0.8489 | 1 |
| `HMT1_G14_resource_limits` | PASS | 882 | 10800 |
| `HMT1_G13_declared_gate_coverage` | PASS | 0 | 0 |

- `HMT1_G3_split_disjointness` — selection and pilot derive from different commitment strings, so no truth seed can appear in both
- `HMT1_G9_null_controls` — feature-pair separation controls are reported in the null-pair table
- `HMT1_G11_off_manifold_excluded_from_endpoints` — no off-manifold family contributes a row to the endpoint table
- `HMT1_G10b_truth_extraction_recovers_generative_parameters` — worst peak displacement from the generating trajectory, in evaluation-grid cells: radial 0.523, azimuthal 0.849
- `HMT1_G13_declared_gate_coverage` — complete

`HMT1_G10b` is the check that the feature extractor, pointed at the truth itself
with no operator and no noise in the way, returns the feature that was actually
put there: worst displacement 0.849 evaluation-grid cells
against a threshold of 1.0. It exists because `HMT1_G10`
only asks that extraction be repeatable, and an extractor that reads the wrong
position reads it repeatably. It was declared in the freeze and not implemented
until `HMT1_G13` caught it on the first end-to-end run.

### Regularization collapse

0 of 24 selections landed at the maximal end of their grid.
`HMT1_G12` exists because a selection rule that drives every arm to maximal
regularization is the signature of a degenerate endpoint, and because the
result it produces is a *null* -- every arm collapsed onto nearly the same
near-null estimator will of course show no difference between arms. A null
endpoint read from a collapsed selection is not evidence of no effect; it is
evidence that the selection rule did not select.

The full sweep is recorded, not just its argmin, because a selection pinned at
a grid endpoint and one with a genuine interior optimum produce the same single
number:

| regime | arm | estimator | error at most-regularized end | best on grid | at least-regularized end | pinned |
|---|---|---|---|---|---|---|
| `estimated_from_data` | `DIRECT_PHYSICAL` | RIDGE_IDENTITY | 0.6828 | 0.6509 | 13.5072 | no |
| `estimated_from_data` | `DIRECT_PHYSICAL` | TSVD | 0.6832 | 0.6613 | 831.2992 | no |
| `estimated_from_data` | `RESOLVED_PHYSICAL` | RIDGE_IDENTITY | 0.6905 | 0.4985 | 24.2646 | no |
| `estimated_from_data` | `RESOLVED_PHYSICAL` | TSVD | 0.6935 | 0.5354 | 819.8921 | no |
| `estimated_from_data` | `TOTAL_FLUX` | RIDGE_IDENTITY | 0.7212 | 0.7015 | 0.7015 | no |
| `estimated_from_data` | `TOTAL_FLUX` | TSVD | 0.7193 | 0.7015 | 0.7015 | no |
| `estimated_from_data` | `UNRESOLVED_IMAGE` | RIDGE_IDENTITY | 0.7014 | 0.6160 | 73.3730 | no |
| `estimated_from_data` | `UNRESOLVED_IMAGE` | TSVD | 0.7034 | 0.6428 | 2799.9936 | no |
| `joint_inversion` | `DIRECT_PHYSICAL` | RIDGE_IDENTITY | 0.6851 | 0.6588 | 19.4497 | no |
| `joint_inversion` | `DIRECT_PHYSICAL` | TSVD | 0.6827 | 0.6700 | 712.7122 | no |
| `joint_inversion` | `RESOLVED_PHYSICAL` | RIDGE_IDENTITY | 0.6863 | 0.5068 | 24.6307 | no |
| `joint_inversion` | `RESOLVED_PHYSICAL` | TSVD | 0.6849 | 0.5495 | 682.8647 | no |
| `joint_inversion` | `TOTAL_FLUX` | RIDGE_IDENTITY | 0.7121 | 0.6892 | 0.6892 | no |
| `joint_inversion` | `TOTAL_FLUX` | TSVD | 0.7118 | 0.6892 | 0.6892 | no |
| `joint_inversion` | `UNRESOLVED_IMAGE` | RIDGE_IDENTITY | 0.6887 | 0.5899 | 72.8163 | no |
| `joint_inversion` | `UNRESOLVED_IMAGE` | TSVD | 0.6940 | 0.6167 | 2672.9371 | no |
| `oracle_known` | `DIRECT_PHYSICAL` | RIDGE_IDENTITY | 0.6968 | 0.6719 | 9.3628 | no |
| `oracle_known` | `DIRECT_PHYSICAL` | TSVD | 0.7118 | 0.6815 | 381.7160 | no |
| `oracle_known` | `RESOLVED_PHYSICAL` | RIDGE_IDENTITY | 0.6888 | 0.5022 | 19.5051 | no |
| `oracle_known` | `RESOLVED_PHYSICAL` | TSVD | 0.7194 | 0.5393 | 677.3185 | no |
| `oracle_known` | `TOTAL_FLUX` | RIDGE_IDENTITY | 0.7137 | 0.7055 | 0.7055 | no |
| `oracle_known` | `TOTAL_FLUX` | TSVD | 0.7087 | 0.7055 | 0.7055 | no |
| `oracle_known` | `UNRESOLVED_IMAGE` | RIDGE_IDENTITY | 0.7108 | 0.5980 | 55.6772 | no |
| `oracle_known` | `UNRESOLVED_IMAGE` | TSVD | 0.7212 | 0.6568 | 2377.2047 | no |

Worst source-bank residuals across all 288 truths: azimuthal mean
2.12e-16, spatial mean
2.65e-17, most negative total emissivity
0.055, smallest background 0.171.
Local contrast amplitude spans
0.30 to
0.80 of the local background.

## 7. Disposition

`HMT1_MATERIAL_ERROR_REDUCTION_NO_STABLE_INTERVAL`

Feature error improves materially in the resolved arm, and there is no age interval over which the recovered history stays inside the registered tolerance. Both halves are the result. A material reduction in a time-averaged error is not the same claim as a history that holds together over a stretch of the past, and this run separates them.

All gates pass, so the disposition is read from the science.

### Why the interval is zero

An interval of zero can mean two different things -- the recovered history left
the tolerance early, or it was never inside it -- and only the second is true
here. Under the estimated background, the resolved arm's median old-band
feature error is 0.545 against the direct image's 0.675. Both
sit well above the registered tolerance of epsilon = 0.25. Only
7.8% of resolved-arm realizations are inside the tolerance even
at age zero, and the furthest any of them reaches is 4 M, so at the
registered 95% quantile the interval is 0.0 M for every arm including the
direct one.

So the improvement is real and the absolute accuracy is not sufficient. A
16% relative reduction in an error of 0.67 leaves
an error of 0.54, and the tolerance asks for 0.25. The resolved
arm is better than the direct image at describing the past; it is not yet good
enough to describe it within the accuracy this endpoint demanded.

## 8. What this does not show

One geometry, one spin, one inclination. The truths are drawn from six declared
analytic families, so they are in the reconstruction class by construction up to
the projection, and the result is an upper bound on what this operator can do
for this class rather than a statement about real source histories, which are in
no one's basis. Nothing here licenses a claim about an observed source: that
would need the geometry-mismatch, order-leakage and instrument stages, none of
which are authorized.

The R1L stop stands, and its sealed commitments remain unscored.

**STOP.** Validation is complete and no further stage is authorized without a
new ruling.
