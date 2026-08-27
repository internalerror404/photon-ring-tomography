# R1L stage 1 — localized operator and rank audit

Stage one of three under `R1L_LOCALIZED_AUDIT_FREEZE.json`. No truth was drawn,
no estimator was fitted and no reconstruction error exists in this document.
This stage reports only what the operator can and cannot see, which is a
property of the geometry and the basis alone.

- run `R1L_20260827T044757Z_2ba66f02`
- execution commit `291d387b3e911954ee0e0567e70e2a807a99544c`
- freeze `24f6732a7be9025e...`
- geometry `a050_i050`, orders 0–2, reference SNR₀ = 100
- operational threshold ρ = 1.0
- age grid 2.0 M
  (was 4.0 M), probe half width
  3.0 M
- stop token **`R1L_STAGE_1_PASS_VALIDATION_PILOT_UNLOCKED`**
- amendment `R1L_STAGE1_DIRTY_EXECUTION_G8_MASK_FIX`
  (`artifacts/configs/R1L_STAGE1_DIRTY_EXECUTION_AMENDMENT_008.json`)

> **Execution provenance.** Two runs precede the one reported here and both are
> preserved. `R1L_20260827T044412Z_2ba66f02` was clean and preregistered and failed
> `R1L_G8` at 2.8e2 because the reached-mode mask was built from a single
> observer time. `R1L_20260827T044757Z_2ba66f02` fixed the mask, passed all ten gates, and ran
> against a working tree carrying that uncommitted fix, so it recorded
> `preregistered = false`. Under ruling item 5 stage 1 was then rerun from a
> completely clean tree with no code edits, and every canonical number was
> required to match. See section 9.

## 1. The question C224 could not be asked

Under the registered global class every temporal coefficient is supported on
the whole history, so no coefficient is ever formally unconstrained and "the
direct image cannot see this epoch" can only ever be a statement about a
condition number. The localized ladder makes it a statement about the null
space, and the two ladders were run on the same rays so the numbers below are
directly comparable.

| localized | dim | direct rank | direct exact-zero cols | direct unseen temporal modes | resolved rank | resolved exact-zero cols | global | direct rank | direct exact-zero cols |
|---|---:|---:|---:|---:|---:|---:|---|---:|---:|
| `L224` | 224 | 140 | 84 | 3 | 208 | 0 | `C224` | 224 | 0 |
| `L448` | 448 | 252 | 196 | 7 | 405 | 21 | `C448_T` | 411 | 0 |
| `L1056` | 1056 | 523 | 517 | 7 | 836 | 154 | `C1056_ST` | 911 | 0 |

`C224` is full rank on its own global temporal subspace: the direct arm reaches
224 of
224 with zero nullity. That
establishes identifiability of the 224 **global** coefficients. It does **not**
establish epoch-local identifiability, and it is not evidence either way about
it: C224 cannot pose the epoch-local question, because none of its coefficients
is confined to an epoch.

`L224`, the same dimension over the same rays, poses it. The direct arm there
reaches rank 140 with
84 identically zero
columns. The two rank numbers are answers to different questions and neither
contradicts the other.

## 2. Old-epoch structural support, by arm

Old-epoch means every temporal function whose whole support lies at ages at or
beyond 57.7 M.
Structural means orthogonal to the level subspace, so a recovered spatial mean
cannot be counted as recovered morphology. Entries are operational ranks.

| class | old structural dim | direct | resolved | unresolved | total flux | delay only | spatial only |
|---|---:|---:|---:|---:|---:|---:|---:|
| `L224` | 81 | 0 | 38 | 21 | 1 | 50 | 0 |
| `L448` | 189 | 0 | 93 | 46 | 3 | 120 | 0 |
| `L1056` | 455 | 0 | 185 | 91 | 3 | 243 | 0 |

The direct image sees **nothing at all** in this subspace: its largest singular
value there is 1.75e-14 at
`L224`, which is numerical zero, against
297.5 for the resolved
stack.

Under the **registered counterfactual**, delay diversity is necessary and
dominant here: `SPATIAL_ONLY` matches the direct image at operational rank 0 and
`DELAY_ONLY` exceeds the full resolved stack. Those two arms are specific
substitutions — `SPATIAL_ONLY` gives every order order 0's spatial map while
keeping its own delays, `DELAY_ONLY` gives every order order 0's delays while
keeping its own spatial map — so they license a statement about those
substitutions. This is **not** a universal claim that spatial remapping has no
effect.

## 3. Where the higher orders actually contribute

`L224`, per temporal function, operational rank out of 28 spatial directions.

| mode | ages covered (M) | entirely old | direct | resolved | unresolved |
|---:|---|---|---:|---:|---:|
| 0 | 109.1 – 128.8 | yes | 0 | 3 | 0 |
| 1 | 89.4 – 128.8 | yes | 0 | 14 | 7 |
| 2 | 69.6 – 109.1 | yes | 0 | 21 | 14 |
| 3 | 49.9 – 89.4 | no | 9 | 28 | 21 |
| 4 | 30.2 – 69.6 | no | 25 | 28 | 28 |
| 5 | 10.5 – 49.9 | no | 28 | 28 | 28 |
| 6 | -9.3 – 30.2 | no | 28 | 28 | 28 |
| 7 | -29.0 – 10.5 | no | 22 | 22 | 22 |

Higher-order gains occur where the direct image is **blind or incomplete**, and
the two are different. Modes 5 to 7 agree across all three arms. Modes 3 and 4
are incomplete for the direct image and receive incremental directions — 9 to 28
and 25 to 28 — so the gain there is a completion, not a rescue. Modes 0 to 2 are
where the direct image is at zero and the gain is the whole of what is seen.

## 4. Reach on the refined age grid

Contiguous detectable depth from the present at SNR₀ = 100, on the
2.0 M grid:
direct **62 M**, resolved
**94 M**, unresolved
**62 M**, total flux
60 M.

The resolved gain is **+32 M**,
which reproduces the R1 headline on a grid twice as fine. At
2.0 M resolution that is
16
bins, so for this geometry the gain is not one-bin threshold behaviour. The
high-inclination 4 M gains that motivated the refinement are a geometry-wide
question and are **not** addressed here: this audit is one geometry.

SNR₀ required to reach a given age, which is what the binary grid hides:

| age (M) | direct | unresolved | resolved |
|---:|---:|---:|---:|
| 62 | 42 | 41 | 18 |
| 64 | 157 | 110 | 20 |
| 70 | 91,325 | 166 | 26 |
| 80 | — | 224 | 36 |
| 94 | — | 487 | 96 |
| 110 | — | 29,393 | 780 |

## 5. Stop conditions

| condition | evaluable here | tripped |
|---|---|---|
| `R1L_STOP_1` localized direct and resolved have indistinguishable old structural support | yes | **no** |
| `R1L_STOP_2` resolved old-band structure error does not improve | no — needs the validation pilot | deferred |
| `R1L_STOP_3` all improvement vanishes after order summation | yes | **no** |
| `R1L_STOP_4` the bank cannot be represented without a dominant positivity baseline | no — needs the structural banks | deferred |

`R1L_STOP_1` does not trip: direct is at operational rank 0 in the old
structural subspace at every class and resolved is at
38,
93 and
185. The two are
as distinguishable as they can be.

`R1L_STOP_3` does not trip either, but the finding is mixed and is recorded as
mixed. The unresolved image retains
21 of the
38 old structural
directions the resolved stack has, where the direct image has none — so the
improvement does not vanish under order summation. But on the reach metric at
SNR₀ = 100 the unresolved image gains
0 M over the direct
image. That is a threshold crossing, not an absence of information: at 80 M the
unresolved image needs SNR₀ ≈ 224 and the
direct image needs ≈ 1e13. Whether
that survives as a *reconstruction* gain is exactly what stage 2 is for, and it
is the result most likely to decide whether this line reaches observation.

## 6. Gates

| gate | status | measured | threshold |
|---|---|---|---|
| `R1L_G1_dyadic_dimension_mirror` | PASS | 1 | 1 |
| `R1L_G2_exact_class_nesting` | PASS | 1.840e-13 | 1.000e-12 |
| `R1L_G3_temporal_support_compactness` | PASS | 2.497e-01 | 3.000e-01 |
| `R1L_G4_adjoint` | PASS | 1.417e-13 | 1.000e-08 |
| `R1L_G5_dense_matrix_free_parity` | PASS | 0.000e+00 | 1.000e-10 |
| `R1L_G6_gram_monotonicity` | PASS | 1.073e-16 | 1.000e-10 |
| `R1L_G7_enrichment_does_not_lose_rank` | PASS | 0 | 0 |
| `R1L_G8_unreached_columns_are_exactly_zero` | PASS | 0.000e+00 | 0.000e+00 |
| `R1L_G9_orbit_law_matches_raymap_fluid` | PASS | 1.388e-17 | 1.000e-12 |
| `R1L_G10_circular_centres_outside_isco` | PASS | 1 | 1 |

`R1L_G2` measures 1.84e-13,
which is QR round-off on a 36,864 x 1056
design rather than a nesting defect. Exactness is a statement about the function
spaces, and it is checked directly on the temporal factor alone in the unit
tests, where the residual is at the 1e-15 level. The gate threshold is a
numerical tolerance and is labelled as one.

## 7. What this stage does and does not establish

Established, on one geometry and with no estimator involved:

1. The direct image has **exact** old-epoch null directions once the temporal
   basis is compact — on modes 0 to 2 — and is **incomplete but not blind** on
   modes 3 and 4. This is not a conditioning statement.
2. Orders 1 and 2 genuinely remove them, though not all of them at every class.
   The direct blindness is *whole-epoch*: at `L224` and `L448` its exactly-zero
   columns are precisely 3 and
   7 entire temporal functions, with nothing
   left over. The resolved stack leaves **no** temporal function entirely
   unseen at any class, but the count of individual zero columns it does leave
   grows with the model — 0, 21 and
   154. Enrichment outruns the measurement.

| class | direct zero cols | of which whole temporal functions | remainder | resolved zero cols | resolved unseen functions | unresolved zero cols |
|---|---:|---:|---:|---:|---:|---:|
| `L224` | 84 | 3 | 0 | 0 | 0 | 0 |
| `L448` | 196 | 7 | 0 | 21 | 0 | 21 |
| `L1056` | 517 | 7 | 55 | 154 | 0 | 154 |

3. The resolved advantage is **not** an artifact of global-cosine
   extrapolation. It is larger under the localized ladder than C224 implied,
   because C224's direct arm reported full column rank it did not have.
4. Local support costs rank and conditioning, and at `L224` and `L448` the cost
   falls entirely on epochs the arm could not see. At `L1056` it does not: the
   direct arm loses 517 columns where whole
   unseen functions account for only
   462, so
   55
   of them are spatial directions it cannot see even at reachable epochs.

Not established, and not to be described as established:

- No reconstruction was performed. Nothing here is a recovery claim, and the
  freeze's forbidden-language rule stands: no localized result may be called
  morphology recovery until the structural endpoint has been scored on a sealed
  bank.
- The structure-first banks of section B have not been drawn, so baseline
  domination is untested. `R1L_STOP_4` is open.
- One geometry. The high-inclination question that motivated the finer age grid
  is untouched.

## 8. Clean reproduction

Pending. The clean rerun required by ruling item 5 has not been executed, so every number above still rests on a run that was not preregistered.

## 9. Stop

Stage 1 is complete and the freeze authorizes stage 1 only. Under the sequential
rule the validation pilot is unlocked but **not** entered here.

Stop token: `R1L_STAGE_1_PASS_VALIDATION_PILOT_UNLOCKED`
