# Photon-Ring Retarded-Time Tomography: The Mahakal Phenomenon

**Hina Dixit and Abhinav Chauhan**

**Publication candidate 039 — for author review. Not a submission draft, and not
an authorization to submit.**

Prepared under ruling `PAPER_I_FINAL_TEXT_REVIEW_039`, which accepted the 038
method corrections, resolved two archived method dependencies from source, and
authorized a bounded publication-preparation pass. The archived Shiva-era
manuscript at `artifacts/manuscript/PAPER_I.md`, the working revisions 036, 037
and 038, the canonical freeze and every run directory are unchanged. Every
number below is traced in `CLAIM_EVIDENCE_MATRIX_039.json` to a primary
artifact, a commit, a hash and a row selector. One execution input — the
realized value of the R1 metric floor — remains unlocated and is carried as a
named limitation rather than filled in; see section 9 and `METHOD_DEPENDENCY_STATUS_039.json`.

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
columns; higher-order samples can make such columns nonzero, but those nonzero
columns need not be independent or operationally recoverable.

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

### 1.2 Relation to prior work

The demagnified, rotated and delayed higher-order image hierarchy is
established by Kerr-lensing studies [GL2020], and its interferometric
signatures have been analyzed independently [J2020]. AART provides the
ray-tracing framework underlying the archived maps [AART2023]. Photon-ring
correlation methods [H2021], hotspot-based spacetime tomography [T2020],
dynamic VLBI reconstruction [B2018], and orbital polarimetric flare tomography
[L2024] address related temporal or inverse problems. Here we isolate, in a
declared finite source representation and fixed observation model, the
distinction between source-time sensitivity, nuisance-adjusted supported
directions, and held-out recovery of specified source objects.

That last sentence describes this paper's scope. It is not a priority claim.
Section 11 states exactly which parts of each cited record were read; no
external paper validates the computations reported here, and none is described
as fully read where only its abstract and metadata were verified.

### 1.3 What is not claimed

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

$$ (T_n j)(ξ, t_o) = χ_n(ξ) · w_n(ξ) · j( r_n(ξ), φ_n(ξ), t_o − Δ_n(ξ) ) $$

where `χ_n` is the order's domain mask, `w_n` the ray weight, and `Δ_n` the
retarded delay. The ray-intensity factor contains `g³` under the declared
model; geometric area and measurement noise are specified separately.

**Time convention.** Within the D026 acquisition audit of section 8, delays are
referred to one absolute clock reference `T_REF = −978.6055123201214` M: three
archived profiles had each recentred their own reference, differing by up to
0.69 M, and that audit reconciles them. This is a convention **imposed in that
audit**. It does not mean every legacy result was retrospectively recentred, and
the earlier experiments retain the clock they were run under.

**Measurement convention.** The whitened row carries `sqrt(dΩ) · g³`. An earlier
flat-per-row convention made Fisher information scale with pixel count — a
discretisation artefact — and is retired. Results computed under it are
recomputed or labelled legacy in place, never silently reinterpreted.

**Acquisition unit.** For detector cell `D_d` and **screen integration cell**
`C_p` intersected with the order's effective domain `Ω_n` — both live in the same
screen coordinate space; the source-plane map appears inside the transfer
function and is not a set intersected directly with the observer's pixel —

$$ O[d,p] = | D_d ∩ C_p ∩ Ω_n |,  an area $$
$$ C_inherited = σ² · O · diag(1/a) · Oᵀ,  a_p = |P_p| $$

so brightness maps to integrated flux. The whole-cell emitting fraction times
the uncut overlap is **not** the clipped overlap: a unit cell emitting on its
leftmost fifth and straddling two half-width pixels owes (0.2, 0) and that
substitution pays (0.1, 0.1).

---

## 3. Source spaces, observation model, metrics and estimators

Each experiment pins its own. They are not interchangeable, and no single noise
convention covers all of them.

| experiment | source space | evaluation | noise convention |
| --- | --- | --- | --- |
| E3C geometry audit | declared temporal/spatial product class on the common age grid | age-threshold detectability masks | white noise of density `σ_Ω` per unit solid angle, `Var(η_p) = σ_Ω² dΩ_p`, one density for the whole audit; per-geometry SNR sweep |
| R2 reference geometry | full L224, 72-dim old-contrast target, 152-dim nuisance | normalised Fisher traces and operational counts | frozen legacy measure, `σ = 0.011341986814407566` |
| R1 sealed main | C224 | baseline-inclusive field metric, anchored stable span | one resolved Gaussian draw per (truth, SNR, draw index) at `SNR_0 = 100`; the direct, unresolved and total-flux observations are declared linear readouts of that same draw |
| R1L stage-2R | localized L224/L448/L1056 | aggregate structural materiality | as R1, at `SNR_0 = 1000` |
| HMT-2 sealed main | L448_contrast, L896_radial_enriched | registered morphology error-reduction, paired draws | one standard-normal tensor of shape (orders, rays, observer times) per truth and draw, mapped to `σ_Ω sqrt(dΩ) z` on each order's pixels and then through each arm's declared readout, whitened by the channel variance |
| D026 acquisition audit | detector-space response | whitened detector-vector relative error | single-sky `σ²` over full pixel area once |

*R2's ideal order-labelled comparison is not the later single-sky detector
experiment, and the two must not be described under one noise pin.* Replication
is a separate axis from the noise law: R1 draws eight noisy realisations per
truth plus one noiseless control that the endpoint excludes, and HMT-2 draws
four paired realisations per truth. A draw count is not an observation
covariance.

### 3.1 The declared source class and observation schedule

`C224` is `4 × 7 × 8 = 224`: four cubic B-splines in `log r`, seven real Fourier
modes in azimuth (`|m| ≤ 3`), and eight DCT modes in source time, ordered
radial-major then azimuthal then temporal. Its declared support is
`r ∈ [1.8660386527060988, 49.98205255591607] M` and
`t ∈ [−128.82234649196255, 29.0] M`. The reference observer schedule is eight
samples uniformly spaced from 0 to 20 M, with 1536 retained rays per order at
orders `n = 0, 1, 2`.

The localized `L`-classes replace the DCT temporal factor by a compactly
supported temporal representation; they are a different temporal
representation, not a renaming of `C224`, and each carries its own definition.
`L896_radial_enriched` is `8 × 7 × 16` and `L448_contrast` is `4 × 7 × 16`; the
HMT-2 runner removes `m = 0` before inversion, leaving 768 and 384 fitted
contrast coefficients.

### 3.2 The age probe and the detectability convention

The E3C localized probe is Gaussian in retarded age and flat in the emission
annulus, with half width `h = 3.0 M`, **normalised to unit `L²` norm over the
emission region** so that the reported Fisher information is not in units of an
arbitrary peak amplitude. The common age grid has step 4 M and maximum 252 M,
fixed source-independently before any geometry was evaluated.

Detectability is a threshold on the operator scaled to the reference SNR:

$$ oldest detectable age probe = sup { a : SNR_0² · I(a) ≥ ρ² },  ρ = 1 $$

with `I(a)` the Fisher information for the unit-norm probe at age `a`. `SNR_0`
is a scaling of the whitened operator; the noise density `σ_Ω` is fixed once,
from the direct arm's clean response to the declared reference source, and no
arm chooses its own `σ`. The reference value is `SNR_0 = 100`, and the frozen
sweep runs `1` to `10⁶` in half-decades. Reporting a reference SNR alone would
not define the experiment; the definition above is what the retained E3C
quantities use.

### 3.3 Estimators and where their tuning came from

TSVD and ridge are non-Bayesian spectral estimators with a fixed representation
and validation-selected regularization. **The tuning lineage is per experiment,
not global.** R1 reuses the hyperparameters selected on the R0C
repair-validation bank and frozen before any main-test truth. HMT-2 reuses its
own stage-1 selection, inherited unchanged through the HMT-2 sealed-main
freeze, whose runner performs no sweep. Neither main experiment tunes on its
held-out bank. Each result names which estimator produced it. (The earlier word
"prior-free" is replaced; no estimator and no selected value changed.)

**Three rank notions**, kept distinct, and recovery is not one of them.
*Structural algebraic rank* where it is exactly justified; *numerical rank* at a
stated floating-point tolerance; *operational rank* at the declared SNR, source
normalisation and decision threshold. **Estimator recovery** is a separate
criterion — a declared loss and a reliability requirement on held-out histories.
A nonzero column is none of the four.

Nuisance projection is part of the stated R2 target calculation in section 6. It
is not an automatic step applied to the earlier E3C and E3D operational counts,
which are taken at their own thresholds without a target/nuisance split.

---

## 4. The support result

Let sampled source functions be separable, `q_lk(r,φ,t) = ψ_l(r,φ) τ_k(t)`,
and let `W_n` be the set of retarded times reached by the actual observer times
and retained rays of order n with nonzero transfer weight.

> **Proposition 4.1 (sampled support-nullity).** If `supp(τ_k) ∩ W_0 = ∅`
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

**What the proposition does not say.** A nonzero column need not be an
independent output direction, and need not be an operationally recoverable one.
The proof establishes nonvanishing, not sufficiency: no independence among the
newly nonzero columns follows from it. The theorem and its nonvanishing
assumptions are unchanged.

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
- **anchor-connected span** — the stretch that reaches the frozen anchor: a
  contiguous passing interval beginning at the geometry-specific anchor. It
  begins at age zero only where the recorded anchor is zero, which is 8 of the
  12 geometries; at the four 75-degree geometries the anchor is 32, 28, 28 and
  28 M and the interval begins there.

Each geometry is anchored at its own youngest fully supported probe centre,
fixed before any detectability curve was read, because there the minimum delay
in the frozen ray set exceeds the last observer sample.

### 5.2 The archived reach statistics

**Oldest detectable age probe (M), resolved stack, then direct:** 60, 84, 144
at i = 20, 50, 75 for all four spins; 20, 60, 140 for the direct image.

**Anchor-connected span (M), resolved stack:** 60 and 84 at 20 and 50 degrees,
and at 75 degrees 112 M at spin 0 and 116 M at spins 0.50, 0.90 and 0.98.
**Direct:** 20 and 60, and at 75 degrees 108 M at spin 0 and 112 M at the other
three.

At the reference SNR the resolved stack's oldest detectable probe exceeds the
direct image's at 12 of 12 geometries, and the threshold-independent innovation
is positive at 12 of 12. Figure 1 plots the two statistics side by side.

![**Figure 1. Two reach statistics, and only one of them is flat in spin.** Top row: the oldest detectable age probe, the supremum of the detectable age set, which is flat across the four sampled spins at every inclination. Bottom row: the anchor-connected span, the contiguous passing interval from each geometry's own anchor, which is not — at 75 degrees the resolved span is 112 M at spin 0 and 116 M at the other three. A supremum being flat in spin does not establish spin independence of the reach that connects to the anchor. Reference SNR, median over source class; regenerated from `artifacts/tables/e3c_depth_curves.parquet` with the selector recorded in `FIGURE_MANIFEST_039.json`.](figures/fig1_reach_two_statistics_039.png)

> **Scope.** 144 M is a supremum of a threshold mask. It is not an estimator
> recovery depth and not an anchored interval. **A common oldest passing grid
> point across four spins does not establish physical spin independence** — the
> anchor-connected quantities themselves vary with spin at 75 degrees.

### 5.3 Delay and spatial substitutions

The archived 0.98 and 0.57 comparisons transplant independently sampled arrays
by index. We retain them as **index-paired counterfactuals**. They do not
isolate the physical contributions of co-registered delay and spatial
remapping, and no mechanism claim is made from them.

---

## 6. Historical dimension

### 6.1 Definitions

Write `y = A_T c_T + A_N c_N + ε` with the declared positive-definite noise
model `C`, and set `B_T = C^(−1/2) A_T`, `B_N = C^(−1/2) A_N`. Let `H_T = Rᵀ R`
be the target source Gram and `Π_N` the orthogonal projector onto `range(B_N)`.
In source-normalised target coordinates,

$$ B_known = B_T R^(−1) $$
$$ B_cond  = (I − Π_N) B_T R^(−1) $$
$$ F_known = B_knownᵀ B_known,  F_cond = B_condᵀ B_cond $$

The quoted information totals are traces of these normalised Fisher matrices.
Operational directions are counted from the singular values at the declared
amplitude threshold. **If `σ` is already inside `C`, the singular values are
not multiplied by the SNR label a second time.** This is a target/nuisance
information calculation, not a reconstruction estimator.

### 6.2 The reference geometry

At `a050_i050`, target dimension 72, `σ = 0.011341986814407566`. The nuisance
space has **152 columns**; its sampled rank is **140 in the direct arm** and
**152 in the stacked resolved arm**. Column count and arm-specific rank are
different numbers and are labelled separately:

| arm | tr F known | tr F conditional | operational at ρ = 1 |
| --- | ---: | ---: | ---: |
| `DIRECT_PHYSICAL` | 0 | 0 | 0 |
| `RESOLVED_PHYSICAL` | 11.053660 | 7.198318 | 3 → 2 |

Singular values 1.4371649, 1.3458733, 0.8062804; the third misses `ρ = 1` by a
clear margin, and subspace angles are exactly zero across all three rank
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
| [−128.82, −109.09] oldest third | 2.44% | 2.35% |
| [−109.09, −89.37] middle third | 43.81% | 43.92% |
| [−89.37, −69.64] youngest third | 53.75% | 53.73% |

About 97.6% lies in the younger two thirds, **but the oldest-third contribution
is not zero.** These localizations describe signed source perturbations, not
separately recovered frames.

### 6.4 Rank behaviour under enrichment

The E3D ladder is four classes, and it changes **both** spatial and temporal
factors — it is not temporal enrichment alone:

| class | radial × azimuthal × temporal | dimension | median operational rank | as a fraction | σ_min+ |
| --- | --- | ---: | ---: | ---: | ---: |
| `C224` | 4 × 7 × 8 | 224 | 201 | 0.897 | 1.635e-02 |
| `C448_T` | 4 × 7 × 16 | 448 | 365 | 0.815 | 7.164e-05 |
| `C528_S` | 6 × 11 × 8 | 528 | 441 | 0.835 | 2.871e-04 |
| `C1056_ST` | 6 × 11 × 16 | 1056 | 770 | 0.729 | 1.332e-07 |

Over the full ladder `C224` to `C1056_ST` the median operational-rank
**fraction** falls 0.897 to 0.729 — the 16.8 percentage points — while the
operational rank itself **rises**, 201 to 770. A falling supported fraction is
compatible with an increasing absolute rank, and the two must not be quoted as
one statement. `σ_min+` falls about five orders of magnitude across the same
ladder. The resolved operator's *numerical*-rank fraction falls by up to 3.3%,
with the largest fall over any arm 25.1% at `DIRECT_PHYSICAL`, `a000_i020` — a
different quantity again. Figure 2 plots the fraction, the count and the
localized-directional depth across the same four classes.

![**Figure 2. The supported fraction falls while the count rises.** Enrichment across the four declared source classes; tick labels give radial × azimuthal × temporal, so both factors are visibly changing along the ladder. Top: the median operational rank as a fraction of class dimension falls 0.897 to 0.729. Middle: the operational rank itself rises, 201 to 770. Bottom: the localized-directional depth, the deepest retarded age whose best-determined localized mode clears the operational threshold at the reference SNR, which is flat across the ladder for both physical arms; across all physical and mechanism arms the largest move anywhere in this table is a single 4 M grid step. This is not the scalar detectability probe of figure 1, and the two must not be identified because both are quoted in M. Regenerated from `artifacts/tables/e3d_class_spectra.parquet` and `artifacts/tables/e3d_depth_by_class.parquet`; selectors in `FIGURE_MANIFEST_039.json`.](figures/fig2_enrichment_three_panels_039.png)

Over the same ladder the localized-directional depth moves by at most one grid
step of 4 M among the physical and mechanism arms. This is not the scalar E3C
detectability probe of section 5.2, and the two must not be identified because
both are quoted in M.

The asymmetry is worth stating in its own right: every move in that depth table
appears at the **spatial** enrichment steps (`C224` to `C528_S`, `C448_T` to
`C1056_ST`) and none at the temporal one. Temporal enrichment exposes null
directions without extending reach; spatial enrichment extends reach without
exposing many.

**These are findings for the tested models, not a theorem that enrichment
destroys injectivity.**

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

The metric is the **registered baseline-inclusive field metric** of appendix
A.1, level dominated: the level fraction of the truth is 0.9838 under the
level/structure projector split. It is a field metric, not a coefficient-space
metric — an estimator that operates on coefficients does not thereby determine
what its evaluation loss measures.

### 7.2 Structure is a separate, later onset

The structure-only stable span is **zero at `SNR_0 = 100` for every arm** and
first becomes nonzero at `SNR_0 = 30000`, with 40 M direct and 76 M resolved.
This is not "cleared at ten times the reference SNR."

Separately, R1L stage-2R validation at `SNR_0 = 1000` meets its aggregate
structural-materiality conditions while its stable-span gain remains zero. It
is neither a sealed main nor a stable-history-span success, and it does not
replace the onset above.

### 7.3 Morphology: the HMT-2 sealed main

60 held-out histories — ten per family across six families — with four paired
noise draws each. The draws are not 240 independent histories: the independent
resampling unit is the truth. Materiality was fixed before the bank was drawn:
median relative reduction ≥ 0.10 and bootstrap lower bound ≥ 0.05. On
`L896_radial_enriched`, `RESOLVED_PHYSICAL`, against the analytic source target:

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
- `FAMILY_HETEROGENEITY` — the genuine same-class per-family result: **5 of 12
  family-estimator cells** are material on the physical end-to-end target and
  **4 of 12** on both targets. `circular_hotspot_trajectory` is **negative under
  both estimators** (−0.022 ridge, −0.051 TSVD). Ten truths per family makes
  every interval wide, so these point estimates and intervals are reported as
  measured while no strong universal family claim follows in either direction;
  the heterogeneity is what is recorded, not a ranking.
- `CLASS_DEPENDENCE` — a separate result, not family heterogeneity. On the
  representation-limited control class `L448_contrast` the TSVD gain is +0.061
  with lower bound +0.033 and is not material, against +0.133 / +0.101 on
  `L896_radial_enriched`. This changes the representation class, not the source
  family.
- `DIRECT_BASELINE_SATURATION_QUALIFICATION` — part of the margin comes from
  where the direct baseline saturates.
- Posterior calibration failed and is preserved as a failure. That failure
  belongs to the **R1 probabilistic estimator program** — the state-space and
  Wiener branch, whose joint calibration gate failed literally at 0.497 against
  a frozen lower bound of 0.5. It is not a posterior supplied by TSVD or ridge,
  which are retained as point estimators.

---

## 8. Numerical validation, and what it does not cover

| component | state |
| --- | --- |
| Hull tessellation | 9.592e-08 band-normalised geometric discrepancy between the named tessellation refinement levels, against the 1e-6 numerical-integration component budget. This is the **tessellation component**, not the entire hull error. |
| Cell measure (C13) | Repaired. Distinct from the G10q and C02 conventions; the repaired sidecars did **not** reweight all historical results. |
| Leaf assembly | Parent overlap reproduced per (detector cell, parent) to 6.9e-18. |
| Sign-aware envelopes | The four-endpoint product is *a* valid enclosure for supplied intervals; it is not the only one. |
| Path-domain comparator | Validated on 66 development and 192 confirmation IDs, zero forced labels. Bounded independence: primary and reference share roots, angular crossing and path classification. |
| **Transfer quadrature** | **Not qualified.** |

Measured as whitened detector vectors on identical supported geometry, the
coarse and fine representations of the transferred field differ by a **maximum
relative same-support discrepancy over the 40 transferred diagnostic columns**
of 9.594e-03, 4.274e-02 and 5.116e-01 at orders 0, 1 and 2, against a 5e-4
component budget. These are per-order maxima over 40 correlated columns, not one
identical error on every column; separately, every one of those columns exceeds
the tested threshold at every order. **This is a discrepancy between two
discretisations, not a measured continuum error**, and the agreement of neither
establishes the accuracy of either.

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
   remainder, a stated accuracy for the reference, and a funded independent
   validation budget. Group remainder radii from outside the certified pair are
   **one possible** numerical certificate, consistent with section 8; any
   alternative construction still needs a justified reference error, controlled
   omitted support, and validation appropriate to itself.
2. **Order-resolution attribution.** Requires a comparison against an
   appropriate physical control and a new result. A quadrature pass elsewhere
   does not supply it.
3. **R2 count.** Legacy measure; corrected-measure recomputation not performed.
4. **The realized R1 metric floor `η`.** The rule is source-resolved and
   restated in appendix A.1: `η` is 0.05 times the median positive windowed
   truth norm on the prior-fit split, frozen before scoring, common to all
   truths. **The realized scalar has not been located in the inspected
   records.** `metrics.eta_value` is `null` in the executed freeze; the runner
   computes `η` from the regenerated prior-fit bank and prints it to six
   significant digits, and no stdout capture, run sidecar or cached prior-fit
   norm carrying it was found. The saved main outputs record medians of the
   normalised and absolute errors separately, and a quotient of two independent
   medians is not the per-row denominator, so `η` cannot be read back from them
   either. This limits exact reproducibility of the R1 normalisation for the
   claims in sections 7.1 and 7.2 and appendix A.1. It does not change the
   archived benchmark values, which were computed with the frozen scalar, and
   the floor binds only where the windowed truth norm falls below it.
5. **Reach.** Detectability is not estimator recovery.
6. **Enrichment.** Rank findings are model-specific, not a theorem.
7. **Negative results retained**: severe off-grid 0 → 0 M, zero stable
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

## 11. References

### External literature

Verified in review 039 at the level stated for each entry. Metadata and
author-posted abstracts were read; full texts were not, and the narrow use
listed is what each citation supports here. `BIBLIOGRAPHY_VERIFICATION_039.json`
records the verification level entry by entry.

- **[GL2020]** S. E. Gralla and A. Lupsasca, *Lensing by Kerr Black Holes*,
  arXiv:1910.12873v2; Phys. Rev. D **101**, 044031 (2020);
  DOI 10.1103/PhysRevD.101.044031. Used for: the highly bent Kerr-image
  hierarchy has demagnification, rotation and relative-delay structure.
- **[J2020]** M. D. Johnson et al., *Universal Interferometric Signatures of a
  Black Hole's Photon Ring*, arXiv:1907.04329v2; Science Advances **6**,
  eaaz1310 (2020); DOI 10.1126/sciadv.aaz1310. Used for: photon subrings have
  characteristic long-baseline interferometric signatures.
- **[AART2023]** A. Cárdenas-Avendaño, A. Lupsasca and H. Zhu, *Adaptive
  Analytical Ray Tracing of Black Hole Photon Rings*, arXiv:2211.07469v4;
  Phys. Rev. D **107**, 043030 (2023); DOI 10.1103/PhysRevD.107.043030. Used
  for: the analytic Kerr ray-tracing framework with adaptive image sampling
  underlying the archived maps.
- **[H2021]** S. Hadar, M. D. Johnson, A. Lupsasca and G. N. Wong, *Photon Ring
  Autocorrelations*, arXiv:2010.03683v3; Phys. Rev. D **103**, 104038 (2021);
  DOI 10.1103/PhysRevD.103.104038. Used for: a photon-ring
  intensity-correlation observable for stochastic equatorial emission whose
  structure contains lens and source information.
- **[T2020]** P. Tiede, H.-Y. Pu, A. E. Broderick, R. Gold, M. Karami and
  J. A. Preciado-López, *Spacetime Tomography Using The Event Horizon
  Telescope*, arXiv:2002.05735v2; linked DOI 10.3847/1538-4357/ab744c. Used
  for: related tomography work using a constrained hotspot model in simulated
  recovery and spacetime inference. Journal volume and page fields were not
  separately verified.
- **[B2018]** K. L. Bouman, M. D. Johnson, A. V. Dalca, A. A. Chael,
  F. Roelofs, S. S. Doeleman and W. T. Freeman, *Reconstructing Video from
  Interferometric Measurements of Time-Varying Sources*, arXiv:1711.01357v2.
  Used for: related dynamic VLBI imaging of evolving sources under a Gaussian
  Markov model. Journal pagination was not verified.
- **[L2024]** A. Levis, A. A. Chael, K. L. Bouman, M. Wielgus and
  P. P. Srinivasan, *Orbital Polarimetric Tomography of a Flare Near the
  Sagittarius A\* Supermassive Black Hole*, arXiv:2310.07687v2. Used for:
  model-dependent 3-D flare-emission reconstruction combining a neural
  representation with a gravitational model. Journal metadata was not verified.

**Scope of the literature audit.** Seven primary arXiv records were verified in
review 039 at metadata and abstract level. This is not a full-text audit, not a
systematic novelty survey, and not a verification of the remaining entries of
the archived manuscript's older reference list. No novelty or priority claim in
this paper rests on that audit; the outstanding items are listed in
`SUBMISSION_GAPS_039.md`.

### Repository evidence

1. `artifacts/reports/E3C_GEOMETRY_WIDE_OPERATOR_AUDIT.md` — geometry-wide
   operator audit; reach statistics and their definitions.
2. `artifacts/reports/E3C_MECHANISM_DECOMPOSITION.md` — delay and spatial
   substitutions.
3. `artifacts/reports/E3D_SOURCE_CLASS_STRESS.md` — the four-class enrichment
   ladder.
4. `artifacts/reports/R1_HELD_OUT_MAIN.md` — sealed level main, regime table,
   level/structure split, structural onset.
5. `docs/Paper_I_v1_Current_Evidence_Ledger.md` — R1L stage-2R and HMT-2
   sealed-main entries.
6. `artifacts/revisions/mahakal_v4_1/R2REPLAY_20260906T144528Z_b873908/` —
   reference-geometry information and replay.
7. `artifacts/revisions/mahakal_v4_1/LOC025_20260906T184213Z/LOCALIZATION_READBACK.json`
   — source-function localization of the two modes.
8. `artifacts/configs/R1_MAIN_FREEZE.json`, `artifacts/configs/E3C_OPERATOR_GRID_FREEZE.json`
   and `artifacts/configs/HMT2_SEALED_MAIN_V1.json` — the executed freezes.
9. `docs/revisions/mahakal_v4_1/PAPER_I_DEFECT_AMENDMENT_023.md` — control
   interpretation dispositions.
10. Rulings 026–039 under `docs/revisions/mahakal_v4_1/`.

---

## 12. Reproducibility

Every number is registered in `CLAIM_EVIDENCE_MATRIX_039.json` with its primary
artifact path, commit, sha256 and row selector, and with the ten pins resolved
per experiment. A hash proves which bytes were read; it does not prove the
prose describes the experiment correctly, and the matrix records that
distinction. `METHOD_DEPENDENCY_STATUS_039.json` carries the method-input
status separately, including the one input — the realized `η` of section 9 —
that a schema pass must not mark complete.

The editorial history of this text, including the passages withdrawn in
revisions 036 through 038 and the reasons for each, is preserved in
`MANUSCRIPT_CORRECTION_LEDGER_039.md` rather than in the body above.

**Author review is required before any scope or submission decision.**

---

## Appendix A. Methods

Definitions recovered from the implementations that produced the results, at
the commits recorded in `CLAIM_EVIDENCE_MATRIX_039.json`. Nothing here is
reconstructed from general convention, and a value absent from the execution
record is marked as a dependency rather than filled from a function default.

### A.1 The R1 baseline-inclusive field metric

Let `D` be the C224 synthesis matrix on the fixed source evaluation grid and
`v_j` the rendered truth on that same grid. For age `a`, the normalised Gaussian
window weights are

$$ w_ap = exp[ −(t_p + a)² / (2h²) ] / ‖ exp[ −(t + a)² / (2h²) ] ‖₂,  h = 3 M $$

and with `W_a = diag(w_ap)` the registered relative error is

$$ E_jb(a) = ‖ W_a ( D ĉ_jb − v_j ) ‖₂ / max( ‖ W_a v_j ‖₂ , η ) $$

where `b` labels the noisy realisation. This is a **weighted field loss on a
finite evaluation grid**. The implementation computes it through the
algebraically equivalent quadratic form

$$ ‖ W_a (D ĉ − v) ‖² = ĉᵀ M_a ĉ − 2 ĉᵀ p_a(v) + s_a(v) $$
$$ M_a = Dᵀ W_a² D,  p_a(v) = Dᵀ W_a² v,  s_a(v) = vᵀ W_a² v $$

for speed. That shortcut does not make it a coefficient-space loss.

**The evaluation grid.** The grid is fixed by the archived R1 caller and scorer
at execution commit `5f557fb6`: `scripts/run_r1_main.py` calls
`evaluation_grid(basis.r_inner, basis.r_outer, basis.t_min, basis.t_max)` with
no size overrides, and the imported `phrt.metrics.scoring.evaluation_grid` at
that same commit takes `n_r = 10`, `n_phi = 12`, `n_t = 40`. The field is
therefore scored at **10 × 12 × 40 = 4,800 evaluation points** with the declared
equal grid weights: ten radii logarithmically spaced over
`[1.8660386527060988, 49.98205255591607] M` with both endpoints included, twelve
azimuths uniformly spaced over `[0, 2π)` with the repeated endpoint omitted, and
forty source times uniformly spaced over `[−128.82234649196255, 29.0] M` with
both endpoints included, flattened in `meshgrid(indexing="ij")` C order so that
time varies fastest, then azimuth, then radius. This is a source-code-defined
scoring grid; it is not by construction an approximation to a continuum
`r dr dφ dt` norm, and no independent continuum quadrature accuracy is implied.
`M_a` is the scoring matrix and must not be confused with `H_T`, the
source-function Gram of section 6, or with geometric screen-cell areas.

**Endpoint.** On the fixed 4 M age grid (half width 3.0 M, grid maximum 120 M),
the primary endpoint is the largest passing span connected to the frozen anchor,
with `ε = 0.25` and `q = 0.95`: the running maximum of `E_jb` over the interval
must be at most `ε` on at least `q` of the empirical joint truth/noise
evaluations. Eight noisy draws per truth, plus one noiseless control that the
endpoint excludes. Uncertainty is paired truth-cluster resampling — every draw
travels with its sampled truth — 10,000 resamples, 95% intervals, frozen seed
20260901. The prespecified improvement floor is 8 M. `IN_CLASS_ID` is the
primary regime; the sealed bank is 640 records split 256 / 64 / 256 / 64 across
`IN_CLASS_ID`, `IN_CLASS_OOD`, `OFF_GRID_ID`, `OFF_GRID_OOD`.

**Remaining dependency.** `η` is a common floor fixed from the prior-fit split
by the registered rule — 0.05 times the median positive windowed truth norm on
that split — not chosen per truth and not taken from the test set. Its realized
scalar is **not located in the inspected records**, as set out in section 9 and
`METHOD_DEPENDENCY_STATUS_039.json`. The rule is resolved; the number is not.

### A.2 The HMT-2 morphology metric

The metric is **state dependent**, not a single norm. Each truth-age state
receives its reconciled source-side label before any arm comparison, and every
state contributes to the primary endpoint:

| reconciled state | error |
| --- | --- |
| `SINGLE_RESOLVED`, `MULTI_RESOLVED` | unbalanced assignment cost, normalised and clipped to its declared worst-case scale |
| `BLENDED`, `AMBIGUOUS` | normalised centroid, size, azimuthal-mode and contrast descriptor discrepancies |
| `DEAD` | amplitude error |

`all_state_error` is a mean over state errors. The `TOTAL_FLUX` control is built
with an all-ones order mixer plus a total-flux collapse, which is not the E3C
per-order flux readout despite the shared word.

**The paired reduction, and the order it is taken in.** Write `e[j,b,a,k]` for
the state-dependent error of history `j`, draw `b`, arm `a` and declared age
`k`, at fixed class, estimator, SNR and target. The caller averages the state
errors over the declared ages for each draw, then averages those per-draw
scores over the four noise draws of that history:

$$ ē[j,a] = mean_b( mean_k e[j,b,a,k] ) $$

Histories are paired across arms by their fixed `(family, index)` identifiers,
and the direct-relative reduction of each pair uses the direct history's mean
error as denominator, with the recorded numerical floor:

$$ r[j] = ( ē[j,direct] − ē[j,a] ) / max( |ē[j,direct]| , 1e−300 ) $$
$$ reported point estimate = median_j r[j] $$

The paired ratios are therefore formed **after** within-history averaging, and
the headline is the **median across histories** — not the relative reduction of
two population mean errors, and not a median of per-state ratios. With an equal
number of ages and draws the two within-history arithmetic means commute; the
nonlinear ratio and the outer median do not generally commute with averaging.
The median's 95% interval is the 2.5th and 97.5th percentiles of 10,000
bootstrap resamples of histories at helper seed 20260954 (the supplied bank seed
20260953 plus one); the history is the independent resampling unit and its four
draws are already contained in its score. The helper also computes a
cell-balanced mean, which is a separate estimand and is not the declared
headline. The paired wrapper intersects history identifiers and masks nonfinite
paired scores; the reported main count is 60, and that count was not
independently recomputed from the stored arrays here.

**Scope.** The archived `PHYSICAL_END_TO_END` label means fidelity to the
analytic source. It is not validation of a real instrument and not validation of
the continuous transfer quadrature.

### A.3 Nuisance-adjusted information

As in section 6.1, with `H_T = Rᵀ R` the Gram matrix of the specified target
source functions **under the declared source measure** — distinct from `M_a`
above and from screen-cell areas. Operational directions are counted from the
singular values at the declared amplitude threshold; if `σ` is already inside
`C` they are not multiplied by an SNR label again.
