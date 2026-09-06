# Mahakal v4.1 - R0 to R2 return report

**Return token: `R0_R2_COMPLETE_REFERENCE_GEOMETRY`**

Amendment `PAPER_I_DEFECT_AMENDMENT_023`. Execution commit
`38e1f8a758e6` on `research/mahakal_v4_1`,
delivery commit `38e1f8a758e6`, inspected base
`7961e5bd7d46`.

Freeze 022 is untouched: all 13 of its
deliverables re-hash to the digests it pinned. Everything new is additive,
under `artifacts/revisions/mahakal_v4_1/`. No new geodesics, no new truths, no
estimator was retuned, and no old FAIL became a PASS.

## What was established, and what was not

**The direct image carries exactly zero information about the target, and the
resolved stack carries some that the nuisance cannot mimic.** At
`a* = 0.5, i = 50` degrees, SNR label 100, on the 72
non-axisymmetric compact temporal coefficients whose support no direct-order
ray reaches:

| arm | known-remainder | nuisance-adjusted | operational at rho=1 | nuisance rank |
|---|---:|---:|---:|---:|
| `DIRECT_PHYSICAL` | 0 | 0 | 0 -> 0 | 140 |
| `RESOLVED_PHYSICAL` | 11.053660 | 7.198318 | 3 -> 2 | 152 |

Profiling out all 152 remaining coefficients -- the old
axisymmetric baseline, every recent-emission factor and the boundary-overlap
factors -- removes 34.9% of the resolved arm's target
information and leaves 65.1% standing. The operational
count at unit effect amplitude falls from 3 to
2 directions, out of a target of
72.

So the hypothesis the protocol registered is supported at this geometry, and
it is supported thinly. Two directions is not a history. The direct arm's zero
is exact rather than small: those columns are identically zero, which is a
support fact and not a conditioning one.

**This is an operator calculation.** It says what the likelihood separates
under unconstrained linear nuisance amplitudes at fixed known geometry. It is
not a reconstruction, it does not license an estimator claim, and no
positivity or geometry-uncertainty conclusion follows from it.

## Numerical standing of that result

- Rank tolerances ['1e-13', '1e-12', '1e-11'] give the same
  nuisance rank and the same operational count. Not tolerance-selected.
- The source Gram converges to a relative change of
  3.01e-07 at
  12800 nodes per axis, below the 1e-6 bar,
  and the endpoints are stable across the last two refinements. Promoted:
  true.
- Target Gram condition 1.786e+03. The metric is a
  declared model norm on a nondimensional domain, not a proper volume.
- Target and nuisance were fixed from support geometry alone and written to
  `R2_TARGET_AND_NUISANCE_MANIFEST.json` before any spectrum was computed.
- The common-count calibration and the archived one coincide exactly at this
  geometry, which carries 1536 rays, so the R2 numbers do not depend on the
  normalization repair.

## R0: twelve dispositions

13 items, C05 split into C05a and C05b. Two
corrections to the delivered ledger are recorded as corrections:

- C02: the ledger's repair target list omitted 4 physical sites found by the call-graph inventory, and NoiseModel.from_snr is toy-only, so the count is 10 physical sites not 6
- C07: confirmed against e3d_class_spectra and found to bite on the repository's own current introduction and contribution list, not only on the uploaded paper's Table 5

The claim scan found occurrences in 39 files,
against the four positions reported from the first pass.

## R1: the repair reaches the physical path

The versioned calibration was routed through the same `PhysicalOperator` the
archived runner builds, from the frozen maps and the registered sampler seed.
All 12 geometries reproduce their archived `s_ref`, worst
relative error
4.4e-16.
12 legacy sites are mapped;
10/10 physical
sites are covered and `NoiseModel.from_snr` is left intact and classified
toy-only.

**One archived endpoint moves.** Every one of the 1152 archived masks
was rebuilt from the stored curves and reproduced bit for bit before any factor
was applied. Under the common count, 1 endpoint changes:

- `a000_i020` / `PAIRING_DESTROYED` at SNR 100.0: oldest 44.0 -> 48.0 M, longest run 48.0 -> 52.0 M, anchor span 28.0 -> 32.0 M

That arm is the nonphysical permutation control. No physical arm moves. The
amendment was right that quantization proves nothing, and the crossing it
warned about is real -- in the one arm that carries no claim.

`J_old` is recomputed from the rescaled curves rather than scaled, and shifts
by one to two percent in that single geometry with its sign unchanged.

21 passed in 0.55s. G05, G16 and G17 pass by detecting the archived
defects rather than by hiding them.

## What is still not done

- A physical common-sky acquisition. `OrderRays` carries no screen
  coordinates, so no co-registered unresolved image can be built from the
  archived objects. Deferred to R3 as the amendment specifies.
- The unknown-background reconstruction companion, and any estimator built on
  the source metric. Both are new analyses.
- The uploaded Mahakal PDF's lineage: `UNRESOLVED_DISTINCT_DOCUMENTS`.
  It is a different document from the repository PDF and is not on this
  machine, so nothing here claims to reproduce it.
- Wider probe widths, refined age grids, other geometries, and the
  twelve-geometry nuisance sweep: all deferred, none authorized here.

Generated 2026-09-06T07:28:33Z. Stopping for
review, as the protocol requires.
