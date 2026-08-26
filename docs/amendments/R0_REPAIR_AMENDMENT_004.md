# R0_REPAIR_AMENDMENT_004

The R0B canary reconstruction pilot is accepted as positive validation
evidence. Three things it measured were not quite what they claimed to be, and
one thing it asserted was never actually checked. This amendment fixes all four
before any new truth is generated, and is committed with a clean working tree so
that the attestation means something this time.

Accepted pilot artifact commit, preserved:

```text
8345068676b15ce8f96a76da9d92b159db215f1d
```

## 1. The endpoint moves, and is labelled as what it is

`(epsilon, q) = (0.50, 0.90)` is retired under

```text
NONDISCRIMINATING_RIGHT_CENSORED_ENDPOINT
```

Not failed. At that tolerance the best reconstruction in every arm reached the
120 M physical ceiling at every SNR, so the arm comparison was between censored
values. The ceiling cannot be raised: the oldest ray in the frozen canary
observation carries 119.8 M. The cell stays in every table.

`(epsilon, q) = (0.25, 0.95)` becomes the primary under

```text
VALIDATION_SELECTED_PRIMARY_FROM_PREREGISTERED_SURFACE
```

which is the accurate name and not "the original preregistered primary". R0B was
validation only, the whole 3 x 3 surface was frozen before it ran, this cell is
a member of that surface, and no main-test truth was scored. No further cell may
be selected after R0C.

## 2. The "in-class" bank was not in class

The consequential repair. Every pilot family was rendered analytically at
roughly the class's resolvable scale, so the exact least-squares projection onto
C224 still left a structure-normalized residual of **0.406 to 0.426** and the
structure-normalized stable span of the class *itself* was zero at every
registered `q`. An experiment on that bank measures basis mismatch and
reconstruction quality together and cannot separate them.

Membership is now a property of the truth rather than a hope about its
parameters. An in-span truth is *defined* as `Q_C x`: sample an analytic family,
project it into C224 on the declared evaluation grid, keep the coefficient
vector, and treat the synthesised movie as the truth. It is then in span at
every coordinate, not merely on the grid it was projected on.

Four regimes, so family shift and representation mismatch are orthogonal axes:

| regime | family | basis |
|---|---|---|
| `IN_CLASS_ID` | prior-fit families | exactly in C224 |
| `IN_CLASS_OOD` | held-out flare family | exactly in C224 |
| `OFF_GRID_ID` | prior-fit families | analytic, outside C224 |
| `OFF_GRID_OOD` | held-out flare family | analytic, outside C224 |

Positivity survives projection because a constant is itself in the class: the
projection of the unit function has a relative residual of **1.46e-15** on this
basis, so a negative excursion is lifted by a multiple of that coefficient
vector without leaving the span. The lift is recorded per truth, and positivity
and the structure companion are still checked afterwards.

Gate `R0_G14_in_span_membership` requires, for every `IN_CLASS_ID` and
`IN_CLASS_OOD` truth,

```text
|| j_truth - Q_C x_truth || / max(1, || j_truth ||) < 1e-10
```

measured rather than assumed, on coordinates other than the ones the truth was
projected on.

## 3. Nothing is carried over from the pilot bank

The source covariance, the Wiener prior, the state-space process noise, the
normalization floors `eta` and `eta_structure`, the selected regularization
values and the representation floors all depend on the source bank, and the
bank's generator semantics changed. Every one is refitted on the repaired bank.
Carrying the pilot's values across would tune the repaired experiment on a
distribution it no longer uses.

The pilot's future-test commitment is preserved permanently as

```text
SUPERSEDED_R0_PILOT_TEST_COMMITMENT
```

It recorded 320 parameter hashes under a construction in which no truth was in
the span of C224, so it can no longer describe the bank it names. The new
commitment hashes the generator version, the source-family parameter record, the
projection and in-span rule, the coefficient hash of every exact-in-class truth,
the analytic-rendering rule for off-grid truths, the regime label and the
positivity rule.

An exact-in-class truth cannot be hashed without being projected, and projection
requires rendering. Rendering is where it stops: the commitment records
explicitly that no operator was applied, no sufficient statistic was formed and
no score exists.

## 4. Uncertainty passes separately or disappears

The pilot's joint calibration was off by a factor of 5.8 for Wiener, in the
narrow direction, and by 40 to 60 in the wide direction for the state-space
model, consistently across arms and with no clipped singular directions. The
marginals looked acceptable, which is exactly why the joint statistic is the one
that decides.

The repair is one declared covariance-scaling rule per estimator family,
`cov -> s * cov` with a single scalar `s`, fitted on a separate
`uncertainty_calibration` split and evaluated on `repair_validation`. Not one
scale per arm, per SNR and per family — that would make the uncertainty layer
flexible enough to fit anything. The acceptance band is a joint ratio in
`[0.5, 2.0]`, frozen before any repair-validation truth exists. Outside it:

```text
UNCERTAINTY_WITHDRAWN
```

and Wiener and the state-space model are retained as point estimators only. The
deterministic reconstruction experiment still proceeds. No credible interval,
posterior movie or coverage statement enters Paper I from an uncalibrated model.

## Two governance defects in the pilot record

### A. `R0B_FREEZE_COMMIT_ATTESTATION_INCONSISTENCY`

Disposition `PILOT_USABLE_MAIN_TEST_NOT_AUTHORIZED`.

The R0B manifest reports `git_commit = e1619fa`, `dirty_tree = false` and a
610 s run, but the freeze it names was committed later, in `8345068`. The freeze
existed uncommitted during execution.

The root cause is worse than the symptom. `provenance.git_dirty` used pathspecs
from an earlier layout in which the package sat under `photon-ring/`, and
`git status` returns nothing at all for a pathspec that matches nothing. The
check was vacuous: **every manifest in the campaign reported a clean tree
whatever the state of the working copy.**

Repaired by correcting the pathspecs, adding `artifacts/configs` to them — a
freeze is a registered configuration, not a generated artifact — and replacing
the claim with a record. `phrt.attestation` captures, at the start of a run and
before anything is written:

```text
execution commit
head tree SHA
committed blob SHA and working blob SHA of every registered file
freeze file SHA-256
the exact git status --porcelain text and its SHA-256
tracked-change and untracked counts, and whether both are zero
```

Gate `R0_G13_freeze_commit_attestation` fails a run whose freeze is not
committed at the commit it reports.

Separately, `started_at` was the moment the manifest object was constructed,
which for the pilot was after the run finished — hence a manifest showing
identical start and finish timestamps beside 610 s of runtime. Runners now pass
their own `t0`.

### B. `R0_G6_GATE_SEMANTICS_MISMATCH`

Disposition `CORRECTED_NO_RERUN_REQUIRED`.

One record carried the name `R0_G6_age_probe_normalization` and the freeze's
`1e-12` threshold while measuring a 4001-point quadrature cross-check at `5e-3`,
reporting `5.551e-5`. The canonical table therefore read as though
`5.551e-5 < 1e-12`. The probe itself was correct; the record was not. Split:

```text
R0_G6a_declared_probe_unit_norm            measured 0        threshold 1e-12
R0_G6b_independent_quadrature_crosscheck   measured 5.551e-5 threshold frozen before R0C
```

No physical rerun follows from this correction.

## Canonical artifact freeze v2

`artifacts/CANONICAL_ARTIFACT_FREEZE.json` was built at the E3C v1 amendment
commit and mismatches 42 of its own entries against the accepted E3C v2 artifact
commit, which is why `verify_manuscript.py` could not run at all. It is
preserved verbatim, together with its snapshot under `artifacts/v1_line/`, as
the record of the v1 manuscript line, and is **not** rewritten.

`artifacts/CANONICAL_ARTIFACT_FREEZE_V2.json` covers the accepted post-E3C-v2
set at the accepted pilot artifact commit. It carries the accepted line, the two
governance deviations above, and a citation policy: the R0 pilot artifacts are
canonical — reproducible and hashed — and are marked

```text
PILOT_USABLE_MAIN_TEST_NOT_AUTHORIZED
```

so that being listed cannot be mistaken for being citable as a reconstruction
result.

`verify_manuscript.py` verifies against v2 when it exists and translates the
names the E3C v2 contract and Amendment 003 changed, plus the one table
relocation Amendment 001 item 7 made. The translation lives in the verifier
rather than in the claim ledger: the ledger is the record of what the v1
manuscript claimed, and editing it to match new tables would erase the thing it
exists to preserve. Digests that moved with the v2 re-execution are counted and
reported separately, and are only tolerated where the file is canonical under v2
*and* the claim's value still re-derives.
