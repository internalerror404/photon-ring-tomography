# TASK 3 — P1-E1 STRUCTURED FACTORIAL AND P1-E2 MODE ATLAS

## Identity
- branch: `claude/experiment-review-mac-rthiz1`
- commit: `72f7c8807752dd1219fe3c17fae5153252422752`  (source tree dirty: False)
- config: `paper1_experiment_registry_v0.2.yaml`  sha256 `2ba66f0209fe1cdec97b8cf5862494c22fb94704318f9601a7a1f9eb4b783796`
- environment sha256: `2a20e241e1761eea7769c0c2d6d1b2c0a47388deba3f9875fe68cba909b1c9dd`
- hardware: Linux x86_64, 4 cores, 15.7 GiB
- python 3.11.15; numpy 2.4.6, scipy 1.17.1, torch 2.13.0, aart 2.1.10

## Mechanical gate result
**PASS.** All E1 and E2 gates pass. No black-hole language appears below: this
is an abstract structured operator, and E1/E2 cannot support a Kerr-specific
claim by themselves.

## Inputs
- factorial: 4 delay structures x 4 spatial structures
  x 4 attenuations x 20 registered seeds = 1,280 operator cells, each evaluated
  under 4 readouts and 4 source classes (20,480 rows)
- controls: 360 rows
- atlas: 1,073 labelled modes, 1,073 injections
- operational threshold: 1.0 whitened singular value, i.e. a unit-amplitude
  source produces a response at the noise level. Fixed before any main-grid
  number was inspected.

## Results

### E1.1 Mechanism — delays alone remove nothing

Restricted **algebraic** rank out of 24 on the smooth separable class, resolved
readout, exponential attenuation Gamma = 0.6, median over 20 seeds:

| delay structure | identical | independent | rotation | rotation_shear |
|---|---:|---:|---:|---:|
| `none` | 16 | 24 | 24 | 24 |
| `constant` | 16 | 24 | 24 | 24 |
| `perturbed` | 16 | 24 | 24 | 24 |
| `cell_dependent` | 23 | 24 | 24 | 24 |

This is the central E1 result and it is negative for the delay mechanism.
With one source-plane sampler shared across orders, the rank is **16 whether
the delay ladder is present or absent**. Stacking six delayed orders is worth
exactly as much as stacking none.

The reason is closed-form, not empirical. The sampler `P` maps 6 source cells
to 2 screen channels, so it annihilates 4 source-plane directions. If every
order uses the same `P`, the visible source-plane subspace is that one fixed
2-dimensional image no matter how many delayed copies are observed. The class
is separable with RS = 3 spatial and RT = 8 temporal modes, so the restricted
rank is exactly

> rank(P) x RT = 2 x 8 = 16

and `tests/test_e1_analytic_predictions.py` asserts this identity rather than
the measured number.

The one cell that escapes the cap is `cell_dependent` delay (23 of 24). That is
not a counterexample: a delay that varies across source cells is no longer a
pure delay. It couples the spatial and temporal axes, and the gain belongs to
the interaction, not to retarded time.

Against the protocol's own inference table (section 7, P1-E4):

| registered inference | verdict in E1 |
|---|---|
| gain in FULL and DELAY-ONLY implies temporal diversity is sufficient | **not supported** |
| gain in FULL and SPATIAL-ONLY implies spatial remapping is sufficient | **supported** |
| gain only in FULL implies a genuine interaction | supported only for cell-dependent delays |

### E1.2 The same grid, operational rank

| delay structure | identical | independent | rotation | rotation_shear |
|---|---:|---:|---:|---:|
| `none` | 8 | 0 | 8 | 8 |
| `constant` | 7 | 0 | 7 | 7 |
| `perturbed` | 7 | 0 | 7 | 7 |
| `cell_dependent` | 7 | 0 | 7 | 7 |

Algebraic rank 24 of 24 coexists with operational rank 5 of 24. Reporting the
rank alone would state that the smooth class is fully identified, when in fact
19 of its 24 directions respond below the noise level at unit amplitude.

Note also that `independent` — the matched-rank control with order-specific but
geometrically unstructured sampling — reaches the same algebraic rank as the
rotation and shear arms while scoring *lower* operationally (2 versus 5). The
geometry is invisible to rank and visible to conditioning.

### E1.3 Attenuation converts structure into uselessness

Resolved readout, constant delay, rotation+shear:

| attenuation | algebraic rank /24 | operational rank /24 | restricted sigma_min |
|---|---:|---:|---:|
| equalized | 24 | 20 | 0.1681 |
| exp, Gamma = 0.3 | 24 | 10 | 0.0971 |
| exp, Gamma = 0.6 | 24 | 7 | 0.0309 |
| exp, Gamma = 0.9 | 24 | 7 | 0.0099 |

Attenuation never changes the algebraic rank. It removes two thirds of the
operationally visible modes between the equalized ablation and Gamma = 0.6. Any
statement about what higher orders make identifiable is therefore a statement
about the attenuation model, and the equalized arm must be labelled an ablation
wherever it appears.

### E1.4 Readout — order collapse is worse than discarding the orders

| readout | algebraic rank /24 | operational rank /24 | restricted sigma_min | kappa+ |
|---|---:|---:|---:|---:|
| `direct_only` | 16 | 4 | 3.2422e-05 | 3.2399e+04 |
| `resolved` | 24 | 7 | 3.0941e-02 | 4.2195e+01 |
| `partial_leakage_eps0.1` | 24 | 7 | 3.0691e-02 | 4.3470e+01 |
| `unresolved_sum` | 23 | 0 | 6.9092e-08 | 1.2461e+07 |

The unresolved sum retains algebraic rank 22 of 24 and has **operational rank
zero**: not one direction of the smooth class clears detection once the order
labels are destroyed. It is outperformed by `direct_only`, which simply throws
the higher orders away and keeps 3.

This comparison is only meaningful because the noise is propagated through the
mixer. Channel c observes `sum_n L[c,n](A_n x + eta_n)`, so it carries noise
`sigma * ||L[c,:]||_2`; the unresolved channel therefore carries `sqrt(6)`
times the per-order detector noise. Whitening every readout at a flat sigma —
which an earlier revision of this code did — hands the unresolved arm a free
`sqrt(6)` amplitude gain and reports its operational rank as 6, i.e. *better*
than resolved. That number was an artifact of the whitening convention and is
retracted; `tests/test_mixing_identity.py` now locks the propagation.

### E1.5 Leakage phase diagram

| eps | mixer rank | kappa(L) | algebraic rank /24 | operational rank /24 | sigma_min |
|---|---:|---:|---:|---:|---:|
| 0 | 6 | 1 | 24 | 7 | 3.0941e-02 |
| 0.02 | 6 | 1.02 | 24 | 7 | 3.0899e-02 |
| 0.05 | 6 | 1.053 | 24 | 7 | 3.0828e-02 |
| 0.1 | 6 | 1.111 | 24 | 7 | 3.0691e-02 |
| 0.2 | 6 | 1.25 | 24 | 7 | 3.0321e-02 |
| 0.4 | 6 | 1.667 | 24 | 7 | 2.8945e-02 |
| 0.7 | 6 | 3.333 | 24 | 6 | 2.3026e-02 |
| 1 | 1 | 4.191e+142 | 23 | 6 | 1.6924e-07 |

### E1.6 Source class dominates everything else

| source class | dim | algebraic rank | operational rank | sigma_min | kappa+ |
|---|---:|---:|---:|---:|---:|
| `full` | 264 | 216 | 44 | 2.6507e-04 | 4980 |
| `localized_atoms` | 24 | 24 | 2 | 1.9771e-02 | 59.4 |
| `orbit_tangent` | 24 | 24 | 0 | 1.7211e-01 | 5.519 |
| `smooth_separable` | 24 | 24 | 7 | 3.0941e-02 | 42.2 |

The orbit-tangent class is the best conditioned of the four (kappa+ 5.5) and
has operational rank 0: uniformly weak rather than unevenly weak. Conditioning
and detectability are independent axes and neither substitutes for the other.

### E1.7 Negative controls

| arm | algebraic rank /24 | operational rank /24 | sigma_min |
|---|---:|---:|---:|
| `control_duplicate_order` | 16 | 8 | 3.8771e-05 |
| `control_gaussian_spatial` | 24 | 0.5 | 1.6448e-02 |
| `control_shuffled_delays` | 24 | 7 | 3.0941e-02 |
| `control_zero_amplitude_high` | 16 | 4 | 3.2422e-05 |
| `reference_structured` | 24 | 7 | 3.0941e-02 |

The duplicate-order and zero-amplitude controls add no rank over direct-only
(both gates measured 0.0), so the factorial is not crediting redundancy or
silence as *identifiability*.

The duplicate control does raise the operational rank, 3 to 6, and that is
correct rather than a leak: scaled copies of order zero put more photons on the
same twelve directions, which makes them easier to detect without making any
new direction identifiable. It is a clean illustration of why the two rank
notions are reported side by side — redundancy buys detectability and buys no
information at all.

The Gaussian control matches the structured arms on rank, which is the honest
reading: at the level of rank, structured spatial diversity is not
distinguishable from an unstructured matched-norm operator. It separates only
operationally, 3 versus 5.

### E2.1 Where the rank actually arrives

`resolved|constant|rotation_shear`:

| max order | algebraic rank | operational rank | new algebraic | new operational | sigma_min |
|---:|---:|---:|---:|---:|---:|
| 0 | 16 | 4 | 16 | 4 | 3.2422e-05 |
| 1 | 24 | 7 | 8 | 3 | 1.3961e-05 |
| 2 | 24 | 7 | 0 | 0 | 2.6565e-04 |
| 3 | 24 | 7 | 0 | 0 | 2.0951e-03 |
| 4 | 24 | 7 | 0 | 0 | 1.0703e-02 |
| 5 | 24 | 7 | 0 | 0 | 3.0941e-02 |

Every algebraic and operational gain lands at order 1. Orders 2 through 5 add
nothing at all. The registered order range n in {0,1,2} is not a limitation
for this operator — it is already past the point of return.

`unresolved_sum|constant|rotation_shear`:

| max order | algebraic rank | operational rank | new algebraic | new operational | sigma_min |
|---:|---:|---:|---:|---:|---:|
| 0 | 16 | 4 | 16 | 4 | 3.2422e-05 |
| 1 | 23 | 3 | 7 | -1 | 2.2012e-10 |
| 2 | 23 | 1 | 0 | -2 | 5.4092e-09 |
| 3 | 23 | 1 | 0 | 0 | 9.0402e-08 |
| 4 | 23 | 0 | 0 | -1 | 5.6518e-08 |
| 5 | 23 | 0 | 0 | 0 | 6.9092e-08 |

Adding orders to an unresolved sum **destroys** detectable modes: operational
rank falls 3, 3, 2, 1, 0, 0. Each new order contributes noise through the
mixer while its signal is attenuated by `exp(-Gamma n)`. This does not
contradict gate G6: information monotonicity is a theorem about nested
whitened Gram matrices under a *resolved* readout, and the unresolved arm is
not nested — its mixer, and hence its noise, changes with every order added.
The two statements should be quoted together, because "adding an order cannot
lose information" is false as soon as the orders are summed.

### E2.2 The null space has an age

Exact nullity on the restricted class, by arm:

| arm | restricted nullity | median retarded age of null modes |
|---|---:|---:|
| `direct_only|constant|rotation_shear` | 8 | 18.9 |
| `resolved|constant|identical` | 8 | 20.3 |
| `unresolved_sum|constant|rotation_shear` | 1 | 21.5 |

All 841 injected exact-null vectors move the source by a relative
separation of 2.0 and change the clean data by at most **3.615e-16**.
The predicted indistinguishability holds to machine precision.

Labelled near-null modes for `resolved|constant|rotation_shear`:

| | singular value | retarded age | temporal freq (of Nyquist) | azimuthal harmonic |
|---|---:|---:|---:|---:|
| weakest | 0.03094 | 40.9 | 0.000 | 1 |
| weakest | 0.08173 | 25.6 | 0.091 | 1 |
| weakest | 0.08666 | 18.3 | 0.000 | 1 |
| weakest | 0.1003 | 35.7 | 0.000 | 1 |
| weakest | 0.1129 | 39.9 | 0.000 | 0 |
| weakest | 0.1969 | 33.3 | 0.091 | 1 |
| strongest | 1.121 | 14.3 | 0.091 | 1 |
| strongest | 1.097 | 8.8 | 0.136 | 1 |
| strongest | 1.075 | 2.8 | 0.136 | 0 |

Across every arm, the correlation between log10 of the singular value and the
mode's retarded age is **r = -0.570**, while the correlation with dominant
temporal frequency is only **r = 0.226**.

That asymmetry is the E2 headline. This operator's weak directions are
preferentially **old**, not preferentially oscillatory. The deep past is
reached only through the high orders, and the high orders are exactly the ones
`a_n = exp(-Gamma n)` suppresses. The protocol's interpretation rule applies in
its age form: a new order that raises rank by revealing very old modes with
vanishing sigma is structural but unstable, and must not be described as usable
history recovery.

## Diagnostics
| gate | status | measured | threshold | note |
|---|---|---|---|---|
| E1_rank_monotone_in_order | **PASS** | 0 | 0 | largest decrease in cumulative restricted rank when an order is added |
| E1_duplicate_order_adds_no_rank | **PASS** | 0 | 0 | rank of the scaled-duplicate control minus rank of direct-only; a positive value would mean the factorial credits redundancy as information |
| E1_zero_amplitude_adds_no_rank | **PASS** | 0 | 0 | rank when higher orders carry no signal, minus direct-only rank |
| E2_null_injection_invisible | **PASS** | 3.61543e-16 | 1e-08 | 841 injected exact-null vectors; worst relative data change |
| E2_null_injection_moves_source | **PASS** | -2 | -1e-06 | every exact-null injection must actually change the source |
| E2_near_null_is_not_null | **PASS** | -6.90924e-08 | 0 | smallest retained near-null singular value must be strictly positive |

84 tests pass, including four analytic predictions that assert the closed-form
rank cap rather than a recorded number.

## Deviations
**D1_platform** — registered: macos_native (execution_target in registry); actual: Linux x86_64.

  Effect: No macOS-specific or Apple-Silicon-specific result can be claimed. All float64 CPU numerics are platform-portable and unaffected; runtime and peak-RSS rows describe this Linux host, not a Mac.

**D2_no_mps** — registered: optional Apple-Silicon MPS for compact neural models; actual: no MPS device present.

  Effect: Gate G11 (CPU/MPS inference parity) cannot be executed and is recorded NOT_RUN. Neural training runs on CPU float32. CUDA is not substituted for MPS in any registered gate.

## Claim effect
Permits: classifying the abstract structured operator as **conditioning-limited
with a strict spatial-diversity rank gain** — C1 for spatial remapping, and no
C1 at all for pure retarded-time diversity.
Demotes: any statement that delay diversity by itself enlarges the identifiable
class. In this construction it does not.
Forbids: every black-hole-specific reading of the above. E1 and E2 are
mathematics. Whether physical Kerr maps behave the same way is E3 and E4, and
those remain blocked on G1.

## Artifacts
- `artifacts/tables/e1_identifiability_factorial.parquet` (20,480 rows)
- `artifacts/tables/e1_mode_onset.parquet`, `e1_controls.parquet`
- `artifacts/tables/e2_mode_atlas.parquet` (1,073 rows)
- `artifacts/tables/e2_injection.parquet`, `e2_mode_onset.parquet`
- `artifacts/gates/correctness_gates.json`

## Next authorized step
STOP pending the v0.1 generator. P4 (E3 AART ray maps) is blocked by G1 under
the protocol's own rule. If the block is lifted, the next phase is P4; the AART
backend is installed and imports, but the registered cross-tracer gate G8 has
no second implementation yet (`kgeo` is not distributed on PyPI).
