# Mahakal II Movie011 — nested enrichment for natural direct-null movies

**Lineage:** successor to the independently preserved Movie009 and Movie010 Stage-A failures. Movie009 showed perfect twin identification but mixed old-feature recovery with an off-basis shared background. Movie010 placed the shared background in the old class but used a comparison B-spline grid that did not contain that class. Movie011 corrects the representation relation in a new experiment; no earlier threshold or result is reinterpreted.

**Status at registration:** no Movie011 validation/test source, observation, regularization decision, reconstruction, or endpoint exists. New source seeds are used. No Kerr ray, path integral, hull/critical root, or Paper-I unit is authorized.

## Fixed acquisition and movie metric

Reuse the authenticated Movie007 q8 inverse and q12 reference Kerr arrays, common noise density, ideal direct/first-indirect order labels, and the registered 15-frame union measurement-support metric. Direct and labelled arms share the same direct data and direct noise. The q8/q12 clean and fitted response criteria remain `5e-4` relative and `0.1` whitened.

## Fresh source population

Use the Movie010 background-controlled construction with fresh seeds `110061`/`110062` for projected in-class backgrounds and `110071`/`110072` for natural analytic old features. The four feature families and compact C2 old-time plateau are unchanged: narrow hotspot, opposite-shear spiral, split/merge, and opposite radial plumes. The analytic feature alternatives are evaluated directly at physical ray points and are never projected before rendering or scoring. Use 8 validation and 16 held-out pairs per family; four matched noise draws at SNR0=300 primary and SNR0=100 secondary.

## Nested comparison class

Retain the frozen Movie007 595-dimensional ridge baseline. Replace Movie010's nonnested 1617-dimensional comparison by an exactly nested Fourier enrichment:

- the same 5 cubic radial B-splines and knots as Movie007;
- the same 17 linear temporal B-splines and knots as Movie007;
- real azimuthal Fourier factors through `m=8` rather than `m=3`;
- dimension `5 x 17 x 17 = 1445`.

The original 595 columns are therefore an exact coordinate subspace of the new class. A source-code gate must verify that embedding any old coefficient vector in the new tensor gives identical source values and q8/q12 detector responses to numerical precision.

Use the same source norm and positive penalty construction, now on the nested class. Select one ridge exponent per arm from `k=-7,...,3` using validation histories only and median support-weighted movie error at SNR0=300. Freeze before test evaluation. No family-specific tuning, no positivity projection, and no analytic feature parameters are supplied to the inverse.

## Endpoints and gate

Report direct-null replay, individual/pair twin identification, total and differential movie frame metrics, 95%/90% contiguous spans, per-family paired reductions, full-annulus control, old-subspace versus added-harmonic error, and q8/q12 clean/fitted discrepancies.

A positive Stage-A result requires: exact old-class nesting; direct identification at chance and pair-both at most 5%; labelled identification at least 90% and pair-both at least 80%; labelled 95%-reliable total-movie span at least 12M and at least 8M beyond direct; positive median paired improvement in at least three of four families including radial plume; and all numerical response gates passing.

A pass authorizes a separately frozen Retarded Neural Field experiment on the same physical acquisition but fresh source populations. A fail blocks neural execution and is retained.

## Scope

Movie011 tests whether an explicitly nested source-class expansion can reconstruct natural old structure outside the original angular bandwidth. It remains one Kerr chart, ideal order labels, synthetic sources, and a measurement-support movie metric—not full-annulus, interferometric, telescope, or observational recovery.