# Photon-Ring Retarded-Time Tomography I: The Shiva Effect — Null Spaces, Multi-Geometry Observability, and Bounded Inference of Historical Emissivity Level and Morphology

**Hina Dixit and Abhinav Chauhan**

**Working revision 036 — for author review. Not a submission draft.**

This revision is produced under ruling `PAPER_I_TEMPLATE_CLOSEOUT_AND_REVISION_036`.
It supersedes nothing: the pinned manuscript at
`artifacts/manuscript/PAPER_I.md` and the canonical freeze are unchanged, and
this file is additive. Every claim retained here is tagged with the level of
evidence that supports it, and the claims that the numerical audit of rulings
026–035 has restricted or suspended are marked in place rather than deleted.

**Preprint draft — theory and controlled synthetic computation only.**
No telescope detection, no laboratory result, and no recovery from a resolved
real photon ring is claimed anywhere.

## How to read the evidence tags

Three levels appear throughout, and they are not interchangeable.

| tag | meaning |
| --- | --- |
| **[S]** structural mathematics | A statement about a declared operator and a declared model class, true under stated assumptions on domain, regularity, support and non-vanishing. It is not a statement about the continuum sky. |
| **[D]** reproduced discrete benchmark | A number computed from a pinned operator, source basis, source Gram, sampled ray set, quadrature, covariance, noise normalisation, target/nuisance partition, estimator and metric. It is reproducible from the archive. It is not an instrument result, and it does not survive a change of any of those ten pins without being recomputed. |
| **[P]** physical acquisition or continuum accuracy | A statement about what a real resolved photon ring would yield, or about the accuracy of the continuum integral the discrete operator approximates. **No claim at this level is currently supported.** Where the original manuscript made one, it is marked RESTRICTED or CORRECTED here. |

A number carrying **[D]** is a fact about a computation we performed. Reading
it as **[P]** is the single most common way this paper could be misused, and
the corrections in section 8 are almost all instances of us having done that
ourselves in the pinned version.

---

## Abstract

Light passing near the photon shell of a Kerr black hole reaches a distant
observer along a family of increasingly delayed null geodesics, so one image
superposes many source epochs. We ask what of that history is recoverable, and
separate three quantities that are routinely conflated: **historical reach** —
how far into the past a localized source change is detectable at a given
signal-to-noise ratio; **historical dimension** — how many independent
directions of a declared source class the operator determines; and
**historical recovery** — whether a held-out truth can actually be
reconstructed. The paper is organised around those three questions.

They separate, and they separate in one particular way, which we name the
**Shiva effect**: the enrichment of the source model that creates recoverable
history destroys identifiability, and the compactness that makes an epoch well
posed makes the direct image exactly blind to it. **[S]**

On reach, the resolved stack sees deeper than the direct image at 12 of 12
registered geometries, with median recoverable depth 60, 84 and 144 M at
i = 20, 50 and 75 degrees and a single value across four spins; retarded-time
diversity supplies more of that reach than spatial remapping, with flattening
the delays costing 0.98 of the higher orders' contribution against 0.57 for
transplanting the spatial map. **[D]**

On dimension, enriching the declared class from 224 to 1056 dimensions drives
the resolved operational-rank fraction down 16.8 percentage points and the
smallest determined singular value down five orders of magnitude, while the
deepest recoverable epoch moves by at most one grid step of 4 M; compact
temporal support turns the direct image's old-epoch blindness into 84
identically zero columns rather than a large condition number. **[S][D]**

On recovery, two sealed held-out results stand, each judged against a
materiality floor fixed before its bank was drawn.
`STABLE_BASELINE_INCLUSIVE_EMISSIVITY_LEVEL_RECONSTRUCTION`: on 640 truths
committed by hash before an operator existed for them, stacking orders extends
the anchored stable span from 48 to 80 M at `SNR_0 = 100`, a gain of 32 M
against a threshold of 8 M, on both prior-free estimators and 4 of 4 source
families. It is a statement about the age-local emissivity *level*: 98.4% of
the field norm is its spatially constant part.
`AGGREGATE_RESOLUTION_AWARE_MORPHOLOGY_ERROR_REDUCTION`: on 60 further held-out
truths, the resolved stack reduces morphology error against the analytic source
by 0.164 and 0.133, lower bounds 0.116 and 0.101. Four qualifications travel
with that result rather than after it: `MULTI_FEATURE_RECOVERY_NEGATIVE`,
`STABLE_MORPHOLOGY_INTERVAL_NEGATIVE`, `FAMILY_HETEROGENEITY` and
`DIRECT_BASELINE_SATURATION_QUALIFICATION`. **[D]**

Between the two, age-local *structure* under our preregistered standard is a
bar not cleared at the reference SNR rather than an effect shown to be zero,
and it is cleared at ten times that SNR as a secondary result. **[D]**

**What this revision withdraws.** The pinned version described the
computational operator as validated and attributed an order-resolution effect
to physical order labels. Neither is supported. A sixteen-month numerical audit
(sections 8 and 9) established that the fixed-detector transfer integral has
**not** been qualified to the declared accuracy: measured as whitened detector
vectors on identical supported geometry, the coarse and fine representations of
the transferred field differ by 9.6e-03, 4.3e-02 and 5.1e-01 relative at orders
0, 1 and 2, against a 5e-4 component budget, and at order 2 the comparison
covers only 62.8% of the emitting area, leaving 0.6092 M² with no error bound
at all. Every **[D]** result below is a statement about the discrete operator
we built. None of them is upgraded to **[P]** by this revision, and section 9
states exactly what each would need.

---

## 1. Introduction

A photon emitted from the equatorial plane near a Kerr black hole can reach a
distant observer directly, or after one or more near-critical windings around
the photon shell. Each additional half-orbit adds delay, so the n-th image of a
time-varying source shows that source as it was further in the past. This is
the observation behind every proposal to read accretion history out of a
resolved photon ring.

Whether that history can be *recovered* is a different question from whether it
is *present*, and the difference is where the difficulty lives. This paper
measures three quantities that are easy to conflate and shows that they
separate:

1. **Historical reach** (section 4) — how far back a localized change is
   detectable at a given SNR. A property of where the operator's sensitivity
   lives in retarded time.
2. **Historical dimension** (section 5) — how many directions of a declared
   source class the operator determines, and how that count moves when the
   class is enriched. A property of the pair (operator, class).
3. **Historical recovery** (section 6) — whether a truth drawn from a sealed
   bank can be reconstructed to a preregistered materiality floor.

### 1.1 What is not claimed

- No detection. Every number is synthetic, computed on validated ray maps under
  a declared noise model.
- No recovery of a historical movie. The two positive results are a level
  reconstruction and an aggregate morphology error reduction, and we repeat
  that wherever they appear.
- No qualified continuum accuracy. The discrete operator has not been shown to
  approximate the fixed-detector integral to the declared budget; see section 8.
- No claim that the reported conditioning is evidence of physical content. Our
  own negative control beats the physical operator on conditioning at 12 of 12
  geometries across 16 frozen seeds. **[D]**

### 1.2 Contributions

- A separation of reach, dimension and recovery on 12 registered
  spin–inclination geometries, with orders n = 0, 1, 2. **[S][D]**
- The Shiva effect: a structural statement that source enrichment and
  identifiability move against each other, with 84 identically zero direct-image
  columns as its sharpest instance. **[S]**
- Two sealed held-out inverse results with preregistered floors, delivered with
  their four negative qualifications attached. **[D]**
- A measurement-convention correction found and applied mid-campaign, with
  everything it moved recorded rather than absorbed (section 8.1). **[D]**
- A full numerical audit of the transfer quadrature that does *not* qualify it,
  and that states what qualification would cost (sections 8.2 and 9). **[D]**

---

## 2. Forward model and measurement convention

The forward operator is matrix-free and whitened, built from per-ray Kerr
transfer maps under a pixel-integrated measurement model whose whitened row
carries `sqrt(dOmega) g^3`.

### 2.1 The measurement convention, and the defect it replaced

An earlier flat-per-row convention made Fisher information scale with pixel
count — a purely numerical artefact of the discretisation. It is retired.
Every result computed under it is either recomputed or explicitly labelled as
belonging to the legacy measure; none is silently reinterpreted. Section 8.1
lists what moved.

### 2.2 The acquisition unit

For detector cell `D_d` and source cell `C_p` intersected with the order's
effective domain `Omega_n`,

    O[d, p] = | D_d ∩ C_p ∩ Omega_n |,        an area
    L       = O diag(a)^-1,                   a = |P_p|
    C_inherited = sigma^2 O diag(1/a) O^T

so brightness maps to integrated flux and the detector noise is
`sigma^2 |D_d|`, charged once per cell per observer time under the single-sky
convention. **[S]**

One substitution is *not* valid and is worth stating because we made it: the
whole-cell emitting fraction times the uncut overlap is not the clipped
overlap. A unit cell emitting only on its leftmost fifth, straddling two
half-width pixels, contributes (0.2, 0); the substitution pays (0.1, 0.1). The
total survives and the image does not. Section 8.2 records where this entered
our own pipeline and how it was repaired.

---

## 3. Geometries, ray maps, and the common age grid

Twelve registered spin–inclination geometries, four spins × three
inclinations, orders n = 0, 1, 2, on validated Kerr and Schwarzschild ray maps.
Delays are referred to one absolute clock reference; the three archived delay
profiles had each recentred their own, differing by up to 0.69 M, and are
reconciled to the single reference `T_REF = -978.6055123201214` M. **[D]**

---

## 4. Historical reach

### 4.1 Reach is real, modest, and set by inclination rather than spin **[D]**

At the reference SNR the resolved stack sees deeper than the direct image at
12 of 12 geometries and carries strictly positive historical innovation beyond
the direct channel's own 99.9% throughput-weighted age boundary at 12 of 12.

Recoverable depth (M), resolved stack, then direct image alone:

| a* \ i | 20° | 50° | 75° |
| --- | ---: | ---: | ---: |
| 0.00 / 0.50 / 0.90 / 0.98 | 60 | 84 | 144 |
| direct image, all four spins | 20 | 60 | 140 |

The surface is flat in spin and steep in inclination: at each inclination the
four spins give a single value. What sets reach in this operator is the
geometry of the retarded windows at a given viewing angle, not the spin.

*Scope.* Depth is a threshold statement at a declared SNR against a declared
noise model on a declared class. It is **[D]**, and it does not transfer to a
different source class or a different instrument without recomputation.

### 4.2 Retarded-time diversity supplies more reach than spatial remapping **[D]**

Flattening the delays costs 0.98 of the higher orders' entire contribution;
transplanting the spatial map costs 0.57. The history is carried by *when* the
orders sample, not by *where* they land.

### 4.3 What the order labels are worth **[D] — scope corrected**

`UNRESOLVED_IMAGE` sums the orders into a single image plane and pays the
summed noise. Depth degrades gracefully — the ratio runs 0.33 to 0.97 — while
historical innovation does not, running 0.23 to 0.44. Explicit order labels are
close to dispensable for *how far back* one can see and load-bearing for *how
much* is learned about that history.

> **CORRECTED SCOPE.** The pinned manuscript read this comparison as evidence
> about physical order resolution. It is not. `UNRESOLVED_IMAGE` is a declared
> synthetic control constructed by summing index-labelled rows; it is not a
> physically unresolved image, and no instrument produces it. The comparison is
> a statement about two constructions of our own operator. Restoring a physical
> order-resolution attribution requires a comparison against an appropriate
> physical control and a new result — a later quadrature pass elsewhere cannot
> retroactively change what this control was. See section 9.3.

---

## 5. Historical dimension

### 5.1 Compact temporal support, and what it costs the direct image **[S]**

Under compact temporal support the direct image's old-epoch blindness is not a
large condition number: it is 84 identically zero columns. A zero column is a
statement about the sampled operator on the declared class. It is not, on its
own, a statement that the corresponding continuum direction is unobservable,
and we do not make that extension.

Symmetrically, a *nonzero* added column is not automatically an independent or
operationally recoverable direction. Enrichment of the source model and
augmentation of the observation set are different operations with different
consequences, and adding matched observations with fixed unknowns does not lose
information.

### 5.2 The Shiva effect **[S][D]**

Enriching the declared temporal class from 224 to 1056 dimensions drives the
resolved operational-rank fraction down 16.8 percentage points and the smallest
determined singular value down five orders of magnitude, while the deepest
recoverable epoch moves by at most one grid step of 4 M. Identifiability and
historical reach are different quantities and they move independently.

### 5.3 Nuisance-adjusted information at the reference geometry **[D] — legacy measure**

At the reference geometry `a050_i050`, with sigma = 0.011341986814407566, the
direct arm determines nothing about the declared target: trace F known 0,
conditional 0, nuisance rank 140, zero operational directions at rho = 1. The
resolved arm has trace F known 11.053660 and conditional 7.198318, nuisance
rank 152, and **two** operational directions at rho = 1 (three known-remainder
directions reduce to two once the nuisance is conditioned out). Singular values
1.4371649, 1.3458733, 0.8062804 against rho = 1; the third misses by a clear
margin, and subspace angles are exactly zero across all three rank tolerances,
so neither the count nor the subspace is a tolerance artefact.

Both surviving directions live almost entirely in one epoch, and it is the
youngest of the three: 99.8% of squared weight in temporal hat 2 with support
[-109.1, -69.6] M, and exactly zero in hat 0, the oldest.

> **SCOPE PIN.** This is the **legacy frozen measure**. It is a ratio of
> normalised Fisher traces in the declared source norm — not bits, not a
> fraction of a history. Under the corrected measure the reweighting bound
> certifies only **1 ≤ N ≤ 2** operational directions, because the per-order
> totals do not bound the individual rows: the order-0 row ratios span
> [0.500081, 1.000162]. The number 2 belongs to the legacy measure and must not
> be restated as two corrected-measure directions. A corrected-measure
> recomputation is not authorised in this revision and is listed in section 9.

---

## 6. Historical recovery

### 6.1 Held-out reconstruction of age-local emissivity level **[D]**

`STABLE_BASELINE_INCLUSIVE_EMISSIVITY_LEVEL_RECONSTRUCTION`. On 640 truths
committed by hash before an operator existed for them, stacking orders extends
the anchored stable span from 48 to 80 M at `SNR_0 = 100` — a gain of 32 M
against a preregistered materiality threshold of 8 M — on both prior-free
estimators and 4 of 4 source families.

The quantity recovered is the age-local emissivity **level**: 98.4% of the
field norm is its spatially constant part. This is a coefficient-space result
under the declared source norm; it is not a source-function metric, and the two
are reported separately throughout.

### 6.2 Age-local structure: a bar not cleared **[D]**

Under our preregistered standard, age-local structure is not established at the
reference SNR. That is a bar not cleared, not an effect shown to be zero. It is
cleared at ten times the reference SNR, reported as a secondary result.

### 6.3 Held-out morphology at the resolution the grid actually has **[D]**

`AGGREGATE_RESOLUTION_AWARE_MORPHOLOGY_ERROR_REDUCTION`. On 60 further held-out
truths, scored by whichever measure the state's own resolved label selects and
with no state excluded, the resolved stack reduces morphology error against the
analytic source by 0.164 and 0.133, lower bounds 0.116 and 0.101.

Neither an unresolved second image nor total flux reaches materiality, so
within this construction the gain is attributable to resolving the orders
rather than to the photons they carry — where "resolving" means the declared
index-labelled construction of section 4.3, not a physical resolution claim.

### 6.4 The four qualifications that travel with it **[D]**

These are not caveats appended after the result. They are part of it.

- `MULTI_FEATURE_RECOVERY_NEGATIVE` — reliable multi-feature recovery was not
  achieved.
- `STABLE_MORPHOLOGY_INTERVAL_NEGATIVE` — the stable morphology interval is
  zero.
- `FAMILY_HETEROGENEITY` — the effect is not uniform across source families.
- `DIRECT_BASELINE_SATURATION_QUALIFICATION` — part of the margin comes from
  where the direct baseline saturates.

### 6.5 The negative control **[D]**

Permuting each order's delays, positions and weights independently preserves
all three marginals and destroys only their pairing. It yields a
better-conditioned operator than the physical one at 12 of 12 geometries across
16 frozen seeds. Conditioning is not evidence of physical content, and no
conclusion here rests on it. The pairing control retains its declared synthetic
meaning and is not read as a physical statement.

---

## 7. Correctness and reproducibility of the discrete pipeline

The geometric machinery below is qualified; the physical quadrature it feeds is
not (section 8.2).

- **Hull geometry.** The curved band boundary is qualified at 9.592e-08
  band-normalised against a 2.5e-4 budget. **[D]**
- **Cell measure.** Ray cells use the nodal dual clipped to the declared
  domain, which tiles the declared screen exactly. The earlier nominal-square
  measure agreed with the realized node spacing in only 16 of 63 archived maps,
  worst case 2.03% in cell area. **[D]**
- **Leaf assembly.** The detector response is assembled leaf by leaf, each
  child keeping its own detector and hull overlap. On archived order-0 core
  geometry the leaf overlaps reproduce the parent overlap per (detector cell,
  parent) to 6.9e-18. **[D]**
- **Sign-aware envelopes.** Unresolved contributions are carried as an interval
  whose endpoints are the extreme of the four products of the indicator and
  field endpoints. For a signed field this is the only valid form; a one-sided
  pile excludes true values. **[S]**
- **Path-domain comparator.** Numerically validated on its tested cohorts: 66
  development cases and 192 previously unused confirmation IDs, with zero
  forced labels. Its independence is bounded — primary and reference share the
  roots, the angular crossing and the path classification. **[D]**

---

## 8. What the corrections changed

### 8.1 The measurement convention

The flat-per-row convention made Fisher information scale with pixel count.
Every conclusion that rested on it was either recomputed under the corrected
convention or is labelled legacy in place. Coefficient metrics and
source-function metrics are reported separately; actual noise and SNR labels
are not interchanged.

### 8.2 The transfer quadrature audit, and what it did not establish

A sustained audit (rulings 026–035) produced these findings, all **[D]**:

- **C13, quadrature geometry mismatch.** The stored pixel area used the
  requested pitch while the ray grid used the realized endpoint-inclusive
  spacing. Repaired; the corrected measure is adopted.
- **The parent-fraction substitution** of section 2.2 had entered the
  integration pilot. Repaired by leaf-correct assembly.
- **Detector-response error, measured.** Carrying the coarse representation of
  the transferred field onto the fine nodes and comparing as whitened detector
  vectors on identical supported geometry: relative error 9.594e-03, 4.274e-02
  and 5.116e-01 at orders 0, 1 and 2, against the 5e-4 component budget. All 40
  transferred diagnostic channels are above budget at every order. The six
  screen channels return exactly zero, which is an equal-input consistency
  control and not an absolute geometry validation.
- **Coverage.** The order-2 comparison covers 61.7% of emitting nodes and 62.8%
  of emitting area; 0.6092 M² of emitting area carries no response bound of any
  kind. Missing support is not zero.
- **Error-bound decomposition.** Writing K = W O, the signed residual E, the
  pixelwise-absolute bound A and the column-triangle bound T satisfy E ≤ A ≤ T.
  Channelwise maxima: A/E is 1.10, 4.57 and 4.71 and T/A is 20.02, 9.02 and
  6.73 at orders 0, 1 and 2. Sign cancellation is therefore *not* the whole
  story — retaining the detector-vector structure removes a large part of the
  conservatism without any correlation model — but it is not absent either, and
  these are separate channelwise maxima, so their product is not the maximum of
  the product and they do not identify which factor dominates any single
  channel.
- **One representation test, negative.** Forming the five harmonic templates at
  the coarse nodes before interpolating is *worse* than interpolating the
  primitives first, at all three orders on the registered maximum-error
  criterion. The test is closed; the order-2 median improves, which is recorded
  as a secondary result and is not a new success criterion.
- **A harmonic identity, verified.** Five real templates reproduce all 40
  declared transferred diagnostic columns at the eight observer times, to
  6.68e-15 pointwise and 1.12e-13 after the detector map, against a 1e-12
  tolerance. This is an algebraic reduction of *these declared diagnostic
  fields* only. It is not a ray speedup, not a reduction of the L224 source
  space, and not a statement about arbitrary source movies.

None of this qualifies the physical quadrature. It measures how far from
qualification the current representation is.

### 8.3 Governance corrections carried on the record

Four protocol deviations from the integration pilot are preserved rather than
tidied: an allocation error that consumed a cap on two arms of six, a 302-point
overrun of a declared cap, an unmet reference-confirmation gate, and a partial
and mismatched comparison. A summary-based spend count also missed an aborted
execution; reconciling every attempt ledger rather than the result files
recovered it.

---

## 9. Limitations, and what each would require

### 9.1 The physical quadrature is not qualified

Section 8.2 gives the measured gap. Qualification requires a response
comparison whose signed per-channel relative error is inside 5e-4 — not a bound
tightened until it fits — with full-domain coverage or an explicit bounded
remainder, a statement of the reference's own accuracy, group remainder radii
obtained from something other than the pair being certified, and a funded
independent validation budget decided before launch. None of the five exists.

### 9.2 The fine reference is not truth

Every comparison in section 8.2 is between two discretisations. Their agreement
does not establish the accuracy of either against the continuum.

### 9.3 The order-resolution attribution is corrected, not merely pending

The pinned manuscript attributed an order-resolution effect using the
`UNRESOLVED_IMAGE` control. That control is an index-sum construction, not a
physically unresolved image. A quadrature pass elsewhere would not retroactively
change what it was. Restoring the attribution requires a new comparison against
an appropriate physical control and a new result.

### 9.4 The R2 count is a legacy-measure count

Section 5.3. Two operational directions under the frozen legacy measure; only
1 ≤ N ≤ 2 is certified under the corrected measure.

### 9.5 Scope of the class-based statements

Full rank on a declared class is a statement about that class. Sampled
discrete rank, operational count and held-out recovery are three different
quantities and are reported as such.

### 9.6 The negative results stay

`MULTI_FEATURE_RECOVERY_NEGATIVE`, `STABLE_MORPHOLOGY_INTERVAL_NEGATIVE`,
`FAMILY_HETEROGENEITY`, `DIRECT_BASELINE_SATURATION_QUALIFICATION`, the
withdrawn uncertainty statement, and the closed negative composite-representation
test. They are reported beside the positive estimates, not after them.

---

## 10. Conclusion

Reach, dimension and recovery separate, and the way they separate is the Shiva
effect: enriching the source model to create recoverable history destroys
identifiability, and the compactness that makes an epoch well posed makes the
direct image exactly blind to it.

Within a declared finite source class and a declared noise model, two held-out
historical inverse results stand — a level reconstruction and an aggregate
morphology error reduction — each with its preregistered floor and its four
negative qualifications attached. Neither is recovery of a historical movie.

What we cannot yet say is whether the discrete operator that produced those
results approximates the physical acquisition to the accuracy the results would
need if read as physics. The audit that asked the question answered it
negatively and quantified the gap. Calling the work finite-model does not
convert an unresolved physical claim into a publishable one; it identifies
exactly which statements are safe and which are waiting on an experiment we
have costed and not run.

---

## 11. Reproducibility and governance

Every number tagged **[D]** is registered in `CLAIM_EVIDENCE_MATRIX_036.json`
beside this file with its source commit, artifact path and hash, the row or
theorem it was read from, and the ten pins (operator, source basis, source
Gram, sampled rays, quadrature, covariance, noise normalisation,
target/nuisance partition, estimator, metric) under which it holds.

The pinned manuscript, the canonical artifact freeze, and every historical run
directory are unchanged by this revision. Corrections are additive overlays.

**Author review is required before any scope or submission decision.** This
revision proposes dispositions; it does not make them.
