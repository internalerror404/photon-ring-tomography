# AMENDMENT_001 — LOCALIZED HISTORICAL SUPPORT

**Status:** registered amendment to the Mac protocol v0.2.
**Registry hash amended against:** `2ba66f0209fe1cdec97b8cf5862494c22fb94704318f9601a7a1f9eb4b783796`
**Relationship to the registered arm:** additive. The registered
24-dimensional smooth separable class (RS = 3 spatial × RT = 8 temporal DCT)
is unchanged and remains the primary reported class. This amendment adds a
diagnostic; it replaces nothing.

## Why the registered arm cannot answer the question

The paper's central claim is about a *historical archive*: whether order-resolved
channels let us see further back. That is a statement indexed by retarded epoch.

The registered class cannot be indexed by epoch. Its temporal factor is RT = 8
global DCT modes, every one of which spans the entire history. The best any
single registered temporal mode achieves is **0.2571** of its energy within
±3 samples of its own centre of mass — it is delocalized by construction. A
restricted σ_min computed on that class is therefore an average over all
epochs, and cannot distinguish "the recent past is well measured and the deep
past is not" from "everything is uniformly mediocre".

E2 measured a correlation between a mode's retarded age and its faintness
(r = −0.447), which is suggestive. But a DCT mode does not *have* an age, only
a centre of mass, so that correlation is a proxy rather than a measurement.

## What the amendment adds

For each retarded age *t* in the history, an RS-dimensional probe class is
built as the registered RS spatial modes crossed with a compact Gaussian
temporal bump centred at *t* (width 1.5 samples). Sweeping *t* over the full
history converts the averaged question into a curve.

Every probe concentrates at least **0.9994** of its energy within ±3 samples of
its centre, against 0.2571 for the sharpest registered mode.

## Registered outcome measures

For each (retarded age, readout, spatial structure, attenuation):

- `sigma_max`, `sigma_min_positive`, `kappa_positive` of the whitened
  restricted operator on the probe class;
- `detectable`: whether `sigma_max` reaches the operational threshold 1.0;
- `orders_covering`: how many order windows structurally contain that age;
- `shallowest_covering_order`: the least attenuated order that reaches it.

The headline derived quantity is the **archive depth**: the greatest retarded
age that remains detectable.

## Registered gates

| gate | requirement |
|---|---|
| `AMD001_probe_is_localized` | every probe concentrates ≥ 0.95 of its energy within ±3 samples |
| `AMD001_sharper_than_registered_dct` | the probe is strictly more localized than the best registered DCT mode |
| `AMD001_registered_arm_unchanged` | the registered class remains RS × RT = 24 |

## Claim discipline

Archive depth is a property of this abstract structured operator. It is not a
Kerr result and must not be quoted as one until E3 and E4 have run on physical
ray maps. The attenuation dependence in particular is a statement about the
declared `a_n = exp(−Γ n)` model, not about any measured photon-ring flux.
