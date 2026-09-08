# Photon-Ring Retarded-Time Tomography: The Mahakal Phenomenon

**Hina Dixit and Abhinav Chauhan**

**Working draft 037 — for semantic review. Not a submission draft.**

Produced under ruling `PAPER_I_MANUSCRIPT_REVIEW_037`. Additive: the archived
Shiva-era manuscript at `artifacts/manuscript/PAPER_I.md`, the working revision
036, the canonical freeze and every run directory are unchanged. Every number
below is traced in `CLAIM_EVIDENCE_MATRIX_037.json` to a primary artifact, a
commit, a hash and a row selector, with the ten experiment-specific pins
resolved or explicitly marked not-applicable or unresolved.

**Preprint draft — theory and controlled synthetic computation only.** No
telescope detection, no laboratory result, and no recovery from a resolved real
photon ring is claimed anywhere.

---

## Abstract

Near-critical black-hole light paths sample a variable source at distributed
retarded times. We distinguish **historical reach**, the number of **source
directions supported** by a declared observation model, and **held-out
recovery** of a specified historical object. We call their separation the
Mahakal phenomenon.

For a separable source representation, a temporal factor whose support is
disjoint from the direct retarded-time footprint generates exactly zero direct
columns; higher-order samples can make such columns nonzero without necessarily
making them independent or recoverable.

In the archived 12-geometry finite-model audit, ideal order-labelled
observations extend the anchor-connected detectable interval beyond direct
imaging. At the reference geometry the sampled direct operator annihilates a
72-dimensional old-contrast target, while the order-labelled stack retains two
operational combinations after profiling the other 152 coefficients of the full
L224 model. That count uses the frozen legacy measure; the available
row-reweighting bound permits one to two combinations under its stated
assumptions.

Two sealed reconstruction benchmarks address different objects.
Baseline-inclusive emissivity-level span increases from 48 to 80 M in the
reported in-class regimes and the mild-mismatch diagnostic, while severe
mismatch remains 0 to 0 M. A separate 60-history morphology benchmark reports
paired gains of 0.133 for TSVD and 0.164 for ridge in its registered
error-reduction metric, with lower confidence bounds 0.101 and 0.116. These
aggregate gains do not establish reliable multiple-feature recovery or a
nonzero stable morphology interval.

The numerical results are conditional on the specified finite operators, source
spaces, noise conventions and evaluation metrics. Continuous transfer
quadrature remains unqualified, and the archived index-sum control does not
establish a physical order-resolution advantage. The study delineates a bounded
information and recovery problem rather than demonstrating reconstruction of a
physical movie.

---

## 1. Introduction

A photon emitted near the equatorial plane of a Kerr black hole can reach a
distant observer directly or after one or more near-critical windings. Each
additional half-orbit adds delay, so the n-th image shows the source as it was
further in the past.

Three questions are easy to conflate, and this paper keeps them apart:

1. **Historical reach** (section 5) — which earlier source times are sampled at
   all, and which of those are detectable at a declared SNR.
2. **Historical dimension** (section 6) — how many directions of a declared
   finite source model the observation supports, before and after profiling
   nuisance coefficients.
3. **Historical recovery** (section 7) — whether a held-out truth can be
   reconstructed to a preregistered materiality floor.

### 1.1 The Mahakal phenomenon

We use the name for the separation itself. Higher-order paths can sample
source-time regions the direct image misses. Increasing source resolution can
expose null or weak directions a coarser model cannot represent. **Neither
statement says that source enrichment always destroys injectivity, or that
compact temporal support alone makes a mode invisible.** The support result of
section 4 is conditional on disjointness from the direct footprint, and the
rank behaviour of section 6 is a finding about the tested models.

### 1.2 What is not claimed

- No detection; every number is synthetic.
- No recovery of a historical movie.
- No qualified continuum accuracy for the transfer integral (section 8).
- No physical order-resolution advantage. The `UNRESOLVED_IMAGE` arm is a
  named **compression control**, not a physically unresolved image.
- No claim that conditioning is evidence of physical content: a pairing-permuted
  control is better conditioned than the physical operator at 12 of 12
  geometries across 16 frozen seeds.

---

## 2. Forward model

For a fixed geometry, the order-n transfer model maps emissivity `j` to an
order-specific field on the screen,

    (T_n j)(xi, t_o) = chi_n(xi) w_n(xi) j( r_n(xi), phi_n(xi), t_o - Delta_n(xi) )

where `chi_n` is the order's domain mask, `w_n` the ray weight, and `Delta_n`
the retarded delay. The ray-intensity factor contains `g^3` under the declared
model; geometric area and measurement noise are specified separately.

**Time convention.** Delays are referred to one absolute clock reference
`T_REF = -978.6055123201214` M. Three archived profiles had each recentred
their own reference, differing by up to 0.69 M; they are reconciled to the
single reference.

**Measurement convention.** The whitened row carries `sqrt(dOmega) g^3`. An
earlier flat-per-row convention made Fisher information scale with pixel count
— a discretisation artefact — and is retired. Results computed under it are
recomputed or labelled legacy in place, never silently reinterpreted.

**Acquisition unit.** For detector cell `D_d` and source cell `C_p` intersected
with the order's effective domain `Omega_n`,

    O[d,p] = | D_d ∩ C_p ∩ Omega_n |,     an area
    C_inherited = sigma^2 O diag(1/a) O^T,   a_p = |P_p|

so brightness maps to integrated flux. The whole-cell emitting fraction times
the uncut overlap is **not** the clipped overlap: a unit cell emitting on its
leftmost fifth and straddling two half-width pixels owes (0.2, 0) and that
substitution pays (0.1, 0.1).

---

## 3. Source spaces, metrics and estimators

Each experiment pins its own. They are not interchangeable, and no single noise
convention covers all of them.

| experiment | source space | evaluation | noise convention |
| --- | --- | --- | --- |
| E3C geometry audit | declared temporal/spatial product class | age-threshold detectability masks | order-labelled ideal observations, per-geometry SNR sweep |
| R2 reference geometry | full L224, 72-dim old-contrast target, 152-dim nuisance | normalised Fisher traces and operational counts | frozen legacy measure, `sigma = 0.011341986814407566` |
| R1 sealed main | C224 | baseline-inclusive field metric, anchored stable span | `SNR_0 = 100` reference, order-labelled arms |
| R1L stage-2R | localized L224/L448/L1056 | aggregate structural materiality | `SNR_0 = 1000` |
| HMT-2 sealed main | L448_contrast, L896_radial_enriched | registered morphology error-reduction, paired draws | four paired noise draws per truth |
| D026 acquisition audit | detector-space response | whitened detector-vector relative error | single-sky `sigma^2` over full pixel area once |

*R2's ideal order-labelled comparison is not the later single-sky detector
experiment, and the two must not be described under one noise pin.*

**Estimators.** TSVD and ridge, both prior-free, are used throughout the
recovery experiments; each result names which produced it.

**Three rank notions**, kept distinct: *numerical rank* (singular values above
a tolerance), *operational count* (singular values above a declared amplitude
threshold `rho` after nuisance projection), and *stable recovery* (a held-out
error criterion met over an anchored span). A nonzero column is none of these.

---

## 4. The support result

Let sampled source functions be separable, `q_lk(r,phi,t) = psi_l(r,phi) tau_k(t)`,
and let `W_n` be the set of retarded times reached by the actual observer times
and retained rays of order n with nonzero transfer weight.

> **Proposition 4.1 (sampled support-nullity).** If `supp(tau_k) ∩ W_0 = ∅`
> then `A_0 q_lk = 0` for every spatial factor `l`. If a retained higher-order
> row has nonzero weight, nonzero spatial value and nonzero temporal value,
> the corresponding stacked column is nonzero. If m such temporal functions and
> `d_s` spatial factors are independent, they supply `m d_s` linearly
> independent coefficient directions in the direct null space.

*Proof.* Each row of `A_0` is the product of the ray weight, the spatial value
at the ray's landing point and the temporal value at the ray's retarded time.
Disjoint temporal support makes the last factor zero at every direct sample, so
every such row vanishes and the column is identically zero. Conversely a single
retained higher-order row with all three factors nonzero has a nonzero product,
so that stacked column is nonzero. Independence of the selected basis products
gives the nullity count. ∎

**What the proposition does not say.** Nonzero columns are not independent
output directions, and are not recoverable directions. No independence among
the newly nonzero columns follows from this proof.

> **Corollary 4.2 (conditional continuum statement).** Under the assumed
> transfer map, a temporal factor whose support is disjoint from the full
> supported screen-time footprint — not its finite sampled proxy — produces zero
> response almost everywhere. A nonzero continuum response requires
> non-vanishing on a set of positive measure, not an isolated support
> intersection.

Corollary 4.2 is a statement about the assumed map. It is **not** a validation
of that map's discretisation; see section 8.

---

## 5. Historical reach

### 5.1 Reach is three statistics, not one

Following the age-interval semantics amendment, we report:

- **oldest detectable age probe** — the supremum of the detectable age set. A
  supremum cannot distinguish history detectable all the way back from a
  detectable island beyond a gap.
- **longest detectable run** — the longest run of consecutive detectable ages
  anywhere on the grid; not a depth from the present.
- **anchor-connected span** — the stretch that reaches the frozen anchor, and
  the only one of the three that may be described as continuous history from
  the present.

Each geometry is anchored at its own youngest fully supported probe centre,
fixed before any detectability curve was read. In 8 of 12 geometries that
centre is age zero; at the four 75-degree geometries it is 32, 28, 28 and 28 M,
because the minimum delay in the frozen ray set exceeds the last observer
sample.

### 5.2 The archived reach statistics

**Oldest detectable age probe (M), resolved stack, then direct:** 60, 84, 144
at i = 20, 50, 75 for all four spins; 20, 60, 140 for the direct image.

**Anchor-connected span (M), resolved stack:** 60 and 84 at 20 and 50 degrees,
and at 75 degrees 112 M at spin 0 and 116 M at spins 0.50, 0.90 and 0.98.
**Direct:** 20 and 60, and at 75 degrees 108 M at spin 0 and 112 M at the other
three.

At the reference SNR the resolved stack's oldest detectable probe exceeds the
direct image's at 12 of 12 geometries, and the threshold-independent innovation
is positive at 12 of 12.

> **Scope.** 144 M is a supremum of a threshold mask. It is not an estimator
> recovery depth and not an anchored interval. **A common oldest passing grid
> point across four spins does not establish physical spin independence** — the
> anchor-connected quantities themselves vary with spin at 75 degrees. The
> earlier statement that reach is "set by inclination rather than spin" is
> withdrawn as written.

### 5.3 Delay and spatial substitutions

The archived 0.98 and 0.57 comparisons transplant independently sampled arrays
by index. We retain them as **index-paired counterfactuals**. They do not
isolate the physical contributions of co-registered delay and spatial
remapping, and no mechanism claim is made from them. The earlier sentence
concluding that history is carried by *when* rather than *where* the orders
sample is withdrawn.

---

## 6. Historical dimension

### 6.1 Definitions

Write `y = A_T c_T + A_N c_N + eps` with the declared positive-definite noise
model `C`, and set `B_T = C^(-1/2) A_T`, `B_N = C^(-1/2) A_N`. Let `H_T = R^T R`
be the target source Gram and `Pi_N` the orthogonal projector onto `range(B_N)`.
In source-normalised target coordinates,

    B_known = B_T R^(-1)
    B_cond  = (I - Pi_N) B_T R^(-1)
    F_known = B_known^T B_known
    F_cond  = B_cond^T B_cond

The quoted information totals are traces of these normalised Fisher matrices.
Operational directions are counted from the singular values at the declared
amplitude threshold. **If `sigma` is already inside `C`, the singular values are
not multiplied by the SNR label a second time.** This is a target/nuisance
information calculation, not a reconstruction estimator.

### 6.2 The reference geometry

At `a050_i050`, target dimension 72, nuisance rank 152, `sigma =
0.011341986814407566`:

| arm | tr F known | tr F conditional | operational at rho = 1 |
| --- | ---: | ---: | ---: |
| `DIRECT_PHYSICAL` | 0 | 0 | 0 |
| `RESOLVED_PHYSICAL` | 11.053660 | 7.198318 | 3 → 2 |

Singular values 1.4371649, 1.3458733, 0.8062804; the third misses `rho = 1` by
a clear margin, and subspace angles are exactly zero across all three rank
tolerances, so neither the count nor the subspace is a tolerance artefact.

> **Measure pin.** The count 2 belongs to the **frozen legacy measure**. The
> available row-reweighting bound permits **one to two** combinations under its
> stated row-noise and metric assumptions, because the per-order totals do not
> bound the individual rows: the order-0 row ratios span [0.500081, 1.000162].
> `tr F_cond / tr F_known = 0.6512158` is a ratio of normalised Fisher traces in
> the declared source norm — not bits, not a fraction of a history.

### 6.3 Where the two combinations live

The two operational combinations are **temporally broad rather than confined to
one epoch**. Using their exported source coefficients and retaining the cross
terms of the source Gram, their squared source norms place

| source-time interval (M) | first mode | second mode |
| --- | ---: | ---: |
| [-128.82, -109.09] oldest third | 2.44% | 2.35% |
| [-109.09, -89.37] middle third | 43.81% | 43.92% |
| [-89.37, -69.64] youngest third | 53.75% | 53.73% |

About 97.6% lies in the younger two thirds, **but the oldest-third contribution
is not zero.**

> **Withdrawn.** The earlier "99.8% in one epoch, exactly zero in the oldest"
> statement grouped Cholesky-normalised coordinates. That is not an energy
> fraction in a physical time interval, and the interpretation is withdrawn.
> These localizations describe signed source perturbations, not separately
> recovered frames.

### 6.4 Rank behaviour under enrichment

Enriching the declared temporal class from 224 to 1056 dimensions drives the
resolved operational-rank fraction down 16.8 percentage points and the smallest
determined singular value down five orders of magnitude, while the oldest
detectable probe moves by at most one grid step of 4 M. **This is a finding for
the tested models, not a theorem that enrichment destroys injectivity.**

---

## 7. Historical recovery

### 7.1 Level: the R1 sealed main

The bank holds 640 histories across four regimes, committed by hash before
scoring. At `SNR_0 = 100`, with both TSVD and ridge, the anchored
baseline-inclusive level span moves:

| regime | direct (M) | resolved (M) | gain (M) | material |
| --- | ---: | ---: | ---: | --- |
| `IN_CLASS_ID` | 48 | 80 | 32 | yes |
| `IN_CLASS_OOD` | 48 | 80 | 32 | yes |
| `OFF_GRID_OOD` (mild) | 48 | 80 | 32 | yes |
| `OFF_GRID_ID` (severe) | 0 | 0 | 0 | **no** |

against a materiality threshold of 8 M. **"640 truths" describes the bank, not
uniform success across its regimes**; severe mismatch remains negative. The
four fitting-family successes are a separate breakdown and are not a
restatement of the regime result.

The metric is the **registered baseline-inclusive field metric**, level
dominated: the level fraction of the truth is 0.9838 under the level/structure
projector split. It is a field metric, not a coefficient-space metric — an
estimator that operates on coefficients does not thereby determine what its
evaluation loss measures.

### 7.2 Structure is a separate, later onset

The structure-only stable span is **zero at `SNR_0 = 100` for every arm** and
first becomes nonzero at `SNR_0 = 30000`, with 40 M direct and 76 M resolved.
This is not "cleared at ten times the reference SNR."

Separately, R1L stage-2R validation at `SNR_0 = 1000` meets its aggregate
structural-materiality conditions while its stable-span gain remains zero. It
is neither a sealed main nor a stable-history-span success, and it does not
replace the onset above.

### 7.3 Morphology: the HMT-2 sealed main

60 held-out histories, four paired noise draws per truth, materiality fixed
before the bank was drawn (median ≥ 0.10 and bootstrap lower bound ≥ 0.05).
On `L896_radial_enriched`, `RESOLVED_PHYSICAL`, against the analytic source
target:

| estimator | gain | lower bound | material |
| --- | ---: | ---: | --- |
| Ridge | +0.164 | +0.116 | yes |
| TSVD | +0.133 | +0.101 | yes |

The tested all-order flux readout does not reproduce the material improvement,
and the index-sum arm reaches at most +0.015 with a negative lower bound.

> **Attribution, stated carefully.** The labelled-stack estimates improve in
> this declared experiment. The tested flux readout does not reproduce that
> gain. The index-sum control does not establish how a physically unresolved
> image would perform. No causal claim about physical order resolution follows.

### 7.4 The qualifications that are part of the result

- `MULTI_FEATURE_RECOVERY_NEGATIVE` — reliable multi-feature recovery not achieved.
- `STABLE_MORPHOLOGY_INTERVAL_NEGATIVE` — the stable morphology interval is zero.
- `FAMILY_HETEROGENEITY` — on `L448_contrast` the TSVD gain (+0.061, lower bound
  +0.033) is not material; the effect is not uniform across families.
- `DIRECT_BASELINE_SATURATION_QUALIFICATION` — part of the margin comes from
  where the direct baseline saturates.
- Posterior calibration failed and is preserved as a failure.

---

## 8. Numerical validation, and what it does not cover

| component | state |
| --- | --- |
| Hull tessellation | 9.592e-08 band-normalised. This is the **tessellation component**, not the entire hull error. |
| Cell measure (C13) | Repaired. Distinct from the G10q and C02 conventions; the repaired sidecars did **not** reweight all historical results. |
| Leaf assembly | Parent overlap reproduced per (detector cell, parent) to 6.9e-18. |
| Sign-aware envelopes | The four-endpoint product is *a* valid enclosure for supplied intervals; it is not the only one. |
| Path-domain comparator | Validated on 66 development and 192 confirmation IDs, zero forced labels. Bounded independence: primary and reference share roots, angular crossing and path classification. |
| **Transfer quadrature** | **Not qualified.** |

Measured as whitened detector vectors on identical supported geometry, the
coarse and fine representations of the transferred field differ by 9.594e-03,
4.274e-02 and 5.116e-01 relative at orders 0, 1 and 2, against a 5e-4 component
budget, on all 40 transferred diagnostic channels. **This is a discrepancy
between two discretisations, not a measured continuum error**, and the
agreement of neither establishes the accuracy of either.

Coverage: the order-2 comparison covers 61.7% of emitting nodes and 62.8% of
emitting area; 0.6092 M² carries no response bound of any kind.

Error-bound decomposition, channelwise maxima with `K = W O`: `A/E` is 1.10,
4.57 and 4.71 and `T/A` is 20.02, 9.02 and 6.73. These are separate maxima, so
their product is not the maximum of the product and they do not identify the
dominant factor for any single channel. Cancellation is not the whole story and
is not absent. Group remainder radii are *one* route to a cancellation-aware
certificate, not a universal requirement.

---

## 9. Limitations and dependencies

1. **Transfer quadrature.** Section 8. Qualification needs a signed per-channel
   response comparison inside 5e-4, full-domain coverage or a bounded
   remainder, a stated accuracy for the reference, remainder radii from outside
   the certified pair, and a funded independent validation budget.
2. **Order-resolution attribution.** Requires a comparison against an
   appropriate physical control and a new result. A quadrature pass elsewhere
   does not supply it.
3. **R2 count.** Legacy measure; corrected-measure recomputation not performed.
4. **Reach.** Detectability is not estimator recovery.
5. **Enrichment.** Rank findings are model-specific, not a theorem.
6. **Negative results retained**: severe off-grid 0 → 0 M, zero stable
   morphology interval, negative multi-feature recovery, family heterogeneity,
   failed posterior calibration, and the closed negative composite-representation
   test.

---

## 10. Conclusion

The calculations distinguish access to earlier source times, finite-model
identifiability, and recovery of a declared source object. Support-disjoint
temporal functions generate exact blind directions for the sampled direct
operator, while added order-labelled observations can provide nonzero
historical responses. The finite-SNR dimension and estimator performance still
depend on source resolution, noise, nuisance parameters and the specified loss.

The archived level and aggregate morphology improvements are bounded
computational results. They neither recover a stable historical movie nor
establish the unresolved-image attribution. The physical transfer-integral
accuracy and an appropriate matched physical control remain separate
requirements for any stronger acquisition claim.

---

## References

Sources actually consulted for this draft, all within the repository or its
review record. No external reference is cited that has not been read.

1. `artifacts/reports/E3C_GEOMETRY_WIDE_OPERATOR_AUDIT.md` — geometry-wide
   operator audit; reach statistics and their definitions.
2. `artifacts/reports/E3C_MECHANISM_DECOMPOSITION.md` — delay and spatial
   substitutions.
3. `artifacts/reports/R1_HELD_OUT_MAIN.md` — sealed level main, regime table,
   level/structure split, structural onset.
4. `docs/Paper_I_v1_Current_Evidence_Ledger.md` — R1L stage-2R and HMT-2
   sealed-main entries.
5. `artifacts/revisions/mahakal_v4_1/R2REPLAY_20260906T144528Z_b873908/` —
   reference-geometry information and replay.
6. `artifacts/revisions/mahakal_v4_1/LOC025_20260906T184213Z/LOCALIZATION_READBACK.json`
   — source-function localization of the two modes.
7. `docs/revisions/mahakal_v4_1/PAPER_I_DEFECT_AMENDMENT_023.md` — control
   interpretation dispositions.
8. Rulings 026–037 under `docs/revisions/mahakal_v4_1/`.

**A full external bibliography is outstanding.** The archived manuscript carries
one; it has not been re-audited against this draft's text, and no reference is
carried over unread.

---

## 11. Reproducibility

Every number is registered in `CLAIM_EVIDENCE_MATRIX_037.json` with its primary
artifact path, commit, sha256 and row selector, and with the ten pins resolved
per experiment. A hash proves which bytes were read; it does not prove the
prose describes the experiment correctly, and the matrix records that
distinction.

**Author review is required before any scope or submission decision.**
