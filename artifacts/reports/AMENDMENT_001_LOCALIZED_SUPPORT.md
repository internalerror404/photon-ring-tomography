# AMENDMENT_001 — LOCALIZED HISTORICAL SUPPORT

## Identity
- branch: `claude/experiment-review-mac-rthiz1`
- commit: `a5f31a30bf96a7f5040f4adca711f32620e7d426`  (source tree dirty: False)
- config: `paper1_experiment_registry_v0.2.yaml`  sha256 `2ba66f0209fe1cdec97b8cf5862494c22fb94704318f9601a7a1f9eb4b783796`
- environment sha256: `2a20e241e1761eea7769c0c2d6d1b2c0a47388deba3f9875fe68cba909b1c9dd`
- hardware: Linux x86_64, 4 cores, 15.7 GiB
- python 3.11.15; numpy 2.4.6, scipy 1.17.1, torch 2.13.0, aart 2.1.10

## Mechanical gate result
**PASS** on all three amendment gates. The registered DCT arm is unchanged.

## Why this diagnostic exists

The registered 24-dimensional class is RS = 3 spatial modes crossed with
RT = 8 **global** temporal DCT modes. Every registered temporal mode spans the
whole history: the sharpest one concentrates only **0.2571** of its
energy within +-3 samples of its own centre of mass. A restricted sigma_min on
that class is an average over all retarded epochs and cannot separate "the
recent past is measured and the deep past is not" from "everything is uniformly
mediocre".

E2's correlation between mode age and faintness (r = -0.447) is a proxy, since
a DCT mode has a centre of mass but not an age. This amendment measures the
thing itself: an RS-dimensional probe on a compact bump at each retarded age,
swept across the history. Every probe concentrates at least **0.9994**
of its energy within +-3 samples.

## Results

### Archive depth versus attenuation (resolved, rotation+shear)

| attenuation Gamma | epochs detectable | deepest detectable age | deepest possible |
|---|---:|---:|---:|
| 0.0 | 44 / 44 | 43 | 43 |
| 0.3 | 32 / 44 | 31 | 43 |
| 0.6 | 24 / 44 | 23 | 43 |
| 0.9 | 24 / 44 | 23 | 43 |

Attenuation alone sets the depth of the archive. With the orders equalized --
an ablation, not a physical arm -- every epoch in the history is detectable. At
the registered Gamma = 0.6 the archive stops at age 23 of 43.

### Archive depth versus readout (Gamma = 0.6, rotation+shear)

| readout | epochs detectable | deepest detectable age | deepest possible |
|---|---:|---:|---:|
| direct_only | 23 / 44 | 22 | 43 |
| resolved | 24 / 44 | 23 | 43 |
| unresolved_sum | 0 / 44 | none | 43 |

This is the amendment's central number. Order zero's window covers ages 0
through 23. Direct-only reaches age 22; adding all five higher
orders reaches age 23.

**Five higher-order channels extend the historical archive by one time sample.**

The deepest order's window reaches age 43, so the structural
headroom is 20 samples. At the registered attenuation, 1 of
those 20 is realised. The higher orders are not failing to *cover* the deep
past; they cover it and are too faint to report it.

Destroying the order labels removes the archive entirely: the unresolved sum
detects no epoch at any depth.

### Coverage versus detectability (Gamma = 0.6, resolved, rotation+shear)

| retarded age | orders whose window reaches it | shallowest such order | sigma_max | detectable |
|---:|---:|---:|---:|---|
| 0 | 1 | 0 | 1.051 | yes |
| 8 | 3 | 0 | 1.275 | yes |
| 16 | 5 | 0 | 1.308 | yes |
| 23 | 6 | 0 | 1.174 | yes |
| 24 | 5 | 1 | 0.9843 | no |
| 32 | 3 | 3 | 0.3507 | no |
| 40 | 1 | 5 | 0.1263 | no |
| 43 | 1 | 5 | 0.09733 | no |

The two columns come apart exactly at the edge of order zero's window. Ages
past 23 are reached by three, four, five orders -- and by none that is
bright enough.

### Archive depth versus spatial structure (Gamma = 0.6, resolved)

| spatial structure | epochs detectable | deepest detectable age | deepest possible |
|---|---:|---:|---:|
| identical | 24 / 44 | 23 | 43 |
| rotation_shear | 24 / 44 | 23 | 43 |

Spatial diversity, which E1 showed is the only mechanism that raises restricted
rank, does not buy archive depth. Rank and reach are different resources: what
spatial remapping gives you is more directions within the epochs you can already
see, not more epochs.

## Diagnostics
| gate | status | disposition | measured | threshold | note |
|---|---|---|---|---|---|
| AMD001_probe_is_localized | **PASS** | – | 0.000625157 | 0.05 | worst fraction of probe energy within 3 samples of its centre: 0.9994 |
| AMD001_sharper_than_registered_dct | **PASS** | – | 0.257055 | 0.999375 | best single registered DCT temporal mode concentrates only 0.2571 of its energy within 3 samples; the probe concentrates at least 0.9994. The registered arm cannot resolve an epoch, which is why this amendment exists. |
| AMD001_registered_arm_unchanged | **PASS** | – | 24 | 24 | the registered DCT class is added to, never replaced |

## Deviations
**D1_platform** — registered: macos_native (execution_target in registry); actual: Linux x86_64.

  Effect: No macOS-specific or Apple-Silicon-specific result can be claimed. All float64 CPU numerics are platform-portable and unaffected; runtime and peak-RSS rows describe this Linux host, not a Mac.

**D2_no_mps** — registered: optional Apple-Silicon MPS for compact neural models; actual: no MPS device present.

  Effect: Gate G11 (CPU/MPS inference parity) cannot be executed and is recorded NOT_RUN. Neural training runs on CPU float32. CUDA is not substituted for MPS in any registered gate.

Also see `artifacts/PROTOCOL_DEVIATION_001_E1E2_BEFORE_G1.json`.

## Claim effect
Permits: reporting, for this abstract operator, that archive depth is set by
attenuation rather than by the order ladder, and that order collapse removes the
archive completely.
Demotes: any reading of E1's rank results as evidence about how far back the
method sees. Rank and depth are measured separately here and behave differently.
Forbids: quoting any depth number as a Kerr result. The attenuation dependence
is a statement about the declared exp(-Gamma n) model, not about photon-ring
flux. E3 and E4 decide whether physical maps behave this way, and remain blocked
on G1.

## Artifacts
- `artifacts/tables/amd001_localized_support.parquet` (1,056 rows)
- `docs/amendments/AMENDMENT_001_LOCALIZED_HISTORICAL_SUPPORT.md`

## Next authorized step
Return G1, regenerated E1/E2, and this amendment to the reviewer. E3 pilot is
authorized only if G1 passes; G1 cannot run until the v0.1 generator is
supplied.
