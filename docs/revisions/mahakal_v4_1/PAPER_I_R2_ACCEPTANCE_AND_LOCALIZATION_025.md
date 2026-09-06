# PAPER_I_R2_ACCEPTANCE_AND_LOCALIZATION_025

Reviewed commit: 1d99e99eec9c61eeece2d00b832b1e62e6047b2c.
Branch: research/mahakal_v4_1.
Delivered replay: artifacts/revisions/mahakal_v4_1/R2REPLAY_20260906T144528Z_b873908/.
Execution snapshot: b87390880a13e5967babb0ed876cdbe7a84fd416.

## Decision

R2_REFERENCE_GEOMETRY_ACCEPTED_WITH_LOCALIZATION_CORRECTION.

Accept the clean numerical reproduction of the fixed L224, known-geometry,
ideal-order-labeled likelihood result. Close review 024's replay requirement.
Do not start another spectrum replay solely for this review. The original run,
its provenance deviation, the first replay and the delivered replay remain
separate immutable records. This is an author-directed project ruling, not a
journal referee decision or a statement of independent empirical confirmation.

The saved-source temporal localization added after the original target analysis
needs correction. This does NOT change the accepted target, conditional spectra,
operational counts or original reconstruction results. It changes the physical
meaning assigned to coordinate-group percentages.

## Accepted core and execution record

At a*=0.5, i=50 degrees, normalized SNR 100, the 72 selected compact old contrast
columns are identically zero for the sampled direct operator. Profiling the other
152 full-L224 coefficients leaves two resolved operational directions at rho=1.
The normalized Fisher traces remain 11.053660 known-remainder and 7.198318
conditional, ratio 0.6512158. The leading conditional singular values remain
1.4371649, 1.3458733, 0.8062804. These are finite-model, specified-source-norm
likelihood quantities, not a recovery guarantee, bits, or a fraction of a movie.

The delivered phase provenance identifies b873908, a clean registered tree,
36 matching input files, and the correct target manifest. Use 36 for the
DELIVERED freeze, not the earlier 35-file count. The reported replay differences
4.441e-15 absolute and 1.974e-13 relative satisfy review 024's specified tolerance;
comparison of the two replays is recorded as bitwise identical. The completion
record has all seven required conditions true and none missing. The review
inspected records and source; it did not rerun the physical operator or 524-test
suite independently.

The coverage qualification is accepted: one integration-tested active physical
path, seven algebraically traced active paths, and four non-active entries
(two retired physical and two toy entries). Keep historical discovery of ten
physical sites separate from the eight non-retired physical sites; a changing
denominator must not hide the two retired sites. No closed historical main is
required to run again merely to increase a coverage count.

The merge/guard/refreeze event was handled by preserving both runs rather than
bypassing hashes. The original freeze 022 and submitted artifacts remain intact.
The raw HDF5 maps retain screen coordinates; losing them in OrderRays is not loss
of the original archive. Metadata readiness is accepted, not sky-model validation.

## Important correction: normalized coordinates are not temporal hats

r2b_hat_diagnostic.py first constructs

    B_o = A_old R^(-1),  H_old = R.T R,

then groups columns of B_o by the ORIGINAL temporal_mode labels. But column j of
B_o now acts on source function Q_old R^(-1) e_j, not Q_old e_j. The full Gram
has temporal cross terms because the three hats overlap. The triangular inverse
mixes temporal hats, so original support labels cannot simply be carried through.

An exact small illustration for these first three temporal functions is

    H_t = (w/6) [[2,1,0],[1,4,1],[0,1,4]].

The third Cholesky-orthogonalized temporal function is proportional to

    tau_2 - (2/7) tau_1 + (1/7) tau_0.

It is not supported only where tau_2 was supported. Radial whitening also mixes
radial B-splines, so coordinate indices are not physical radial locations either.

Consequences:

1. The 97.7% known-remainder fraction is a valid decomposition of total trace
   into groups of the chosen Cholesky coordinates. It is NOT an invariant
   epoch-local sensitivity fraction for the original hats or time intervals.
2. The 99.8% mode percentages are reproduced by grouping squared components of
   the NORMALIZED-coordinate right vectors. They do not equal the source L2
   energy in temporal hat 2 or in a time window.
3. A zero or rounded-near-zero coordinate weight in group 0 is not zero source
   energy on the oldest interval. Source coefficient vectors explicitly contain
   nonzero old-hat components. The epoch table itself also has nonzero hat-0
   known/conditional traces; distinguish a chosen mode from a whole block.
4. The phrase 'youngest fifth' is not established by the export. For the union
   of the selected hats, [-128.82234649,-69.63896656] M, hat 2 spans the youngest
   TWO THIRDS, not the youngest fifth. Concentration in normalized coordinates
   is not an additional reason to identify a fifth of physical source time.

Preserve epoch_breakdown_addition.json. Add an interpretation overlay:
CHOLESKY_COORDINATE_GROUP_DIAGNOSTIC, NOT PHYSICAL_EPOCH_PARTITION.
Do not replace or delete its numbers, and do not promote the post-hoc addition
to a preregistered physical result.

## Independent postprocessing of the exported source functions

For a saved mode with source coefficients c, define

    H_I[i,j] = integral over I of q_i q_j r dr dphi dt,
    p(I;c) = c.T H_I c / (c.T H c).

All cross terms are retained. Non-overlapping intervals partition energy;
overlapping original hats do not. This is localization of a signed source
perturbation, not information coming independently from each interval and not
an estimator output.

The review evaluated the first two saved source coefficient vectors using the
repository's four log-radius cubic B-splines, six nonconstant Fourier factors,
and the three selected temporal hats. Radial Gauss quadrature at 64/128/256
nodes converges; three-point temporal Gauss integration on each knot segment
integrates the quadratic products exactly up to floating point. This is a small
independent source-function calculation, not new ray tracing or an operator run.
The input was an explicitly transcribed connector-returned vector subset, not a
claim of having downloaded or rehashed the entire mode-export file locally.
The executable companion reads the full committed export directly on the agent's
machine and additionally checks its normalized-vector readback.

Percent of squared source-function norm:

| Disjoint interval (M) | Mode 1 | Mode 2 |
|---|---:|---:|
| [-128.82235,-109.09455] | 2.43965% | 2.35122% |
| [-109.09455,-89.36676] | 43.81078% | 43.92154% |
| [-89.36676,-69.63897] | 53.74957% | 53.72724% |

The full original hat-2 support contains 97.56035% and 97.64878% of these source
mode norms. The youngest FIFTH of the target union, [-81.47564,-69.63897] M,
contains about 11.60991% and 11.60508%, not almost all of either mode.
The generalized two-mode-subspace interval-energy extrema give the same broad
localization conclusion without selecting a particular rotation of the modes.

These approximate percentages support 'predominantly toward the younger part
of the old target, but temporally broad'. They do not support localization to its
youngest fifth or exact absence of the oldest interval. Small nonzero oldest
source energy does not independently demonstrate operational recovery there.

## Corrected manuscript language

After the companion postprocessing is read back on the committed full export:

"At the reference Kerr geometry, ideal order-labeled observations retain two
operational combinations in a 72-dimensional compact old-contrast target after
profiling the other 152 coefficients of the full L224 model. The direct sampled
operator annihilates the target. The two exported source-function combinations
are temporally broad: about 97.6% of their squared norm lies between -109.1 and
-69.6 M, with about 53.7% between -89.4 and -69.6 M. This establishes bounded
likelihood sensitivity within the declared representation, not reconstruction
of independently resolved epochs or a historical movie."

Do not interchange 'source energy', 'Fisher trace', 'coordinate weight' and
'recovered information'. All four measure different objects.

## Optional invariant trace localization

If a physical-time sensitivity density is desired, use the full source-metric
Fisher matrix F and E_I=R^(-T) H_I R^(-1). Then

    L_I = trace(F E_I)

is nonnegative and sums to trace(F) over a disjoint time partition. It is invariant
under consistent source-coordinate changes. Equivalently it is the sum over
ALL normalized source eigenmodes of lambda_k times their energy in I. Do not
approximate this total with only the leading two modes and call it complete.
It is a localization diagnostic of the information operator, not the Fisher
information of an independently parameterized time window or a new inverse
problem with all other epochs profiled out. A per-window inverse question needs
its own explicitly defined target and nuisance spaces.

This derived calculation is optional and may reuse the same fixed operator,
metric and nuisance projection; no target tuning or new physical campaign is
licensed by it.

## Next authorization

Proceed under NEXT_STAGE_025.yaml: first correct the localization interpretation
using saved vectors; then R3A common-sky geometry construction and correctness
validation at the same geometry. No outcome-bearing common-sky information or
reconstruction sweep is authorized yet. R3A must separate an inherited-noise
postprocessing benchmark from a single-sky detector-noise model, freeze the
acquisition specification without seeing its target spectra, and stop for review.
No new geodesics are needed unless the source archive demonstrably lacks a
required quantity; report such a blocker rather than substituting a new tracer.

No files named in freeze 022 or the accepted replay input freeze should be
rewritten to incorporate this review. Add new documents and outputs only.

## Sources

All at reviewed commit unless otherwise stated:
- scripts/revision_v4_1/r2b_replay.py: exported c=R^(-1)v and normalized vectors.
- scripts/revision_v4_1/r2b_hat_diagnostic.py: grouping AFTER source normalization.
- src/phrt/sources/localized_basis.py and physical_basis.py: basis definitions.
- artifacts/revisions/mahakal_v4_1/R2_REPLAY_INPUT_FREEZE.json.
- delivered run execution_provenance.json, completion.json, mode_export.json,
  epoch_breakdown_addition.json, candidate_vs_replay.csv and replay_cross_check.json.
- artifacts/revisions/mahakal_v4_1/R2_CLOSEOUT_RECORD_024.json.

The reported source mode-export Git blob is c706f93a6df644fb7a001000d4a81b76c1466c25.
