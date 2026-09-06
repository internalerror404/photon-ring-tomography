# R2 closeout: replay, mode export, and the corrected record

**Return token: `R2_REFERENCE_GEOMETRY_REPLAY_ACCEPTANCE_READY`**

Review `PAPER_I_R0_R2_REVIEW_024` accepted in full. All three findings were
verified against the repository before repair and none is disputed.

Delivered run: this directory, executed after the canonical ruling
bytes were merged and the input freeze re-cut; the earlier replay is
preserved and agrees bitwise (see replay_cross_check.json).

Execution commit `b87390880a13` on `research/mahakal_v4_1`,
registered tree clean at start: true.
Input freeze `36` files, all matching.
Runtime 16.8 s, peak RSS 496.6 MiB,
numpy 1.26.4, scipy 1.11.4, python 3.11.15.

## The replay reproduces the candidate

| comparison | worst absolute | worst relative above atol |
|---|---:|---:|
| all four spectra | 4.441e-15 | 1.974e-13 |

Against the declared atol 1e-12 and rtol 1e-10, with near-zero singular values
compared absolutely. Operational counts [0, 2],
matching the review's expected pair. This is numerical reproduction from a
pinned snapshot, not independent empirical confirmation.

| arm | tr F known | tr F conditional | operational at rho=1 | nuisance rank |
|---|---:|---:|---:|---:|
| `DIRECT_PHYSICAL` | 0 | 0 | 0 -> 0 | 140 |
| `RESOLVED_PHYSICAL` | 11.053660 | 7.198318 | 3 -> 2 | 152 |

tr F_conditional / tr F_known = 0.6512158. A ratio of normalized Fisher
traces in the declared source norm at sigma = 0.0113419868144. Not bits,
not a fraction of a history.

## What the two surviving directions are

Singular values [1.4371649, 1.3458733, 0.8062804], margins against
rho = 1 of [0.4371649, 0.3458733, -0.1937196]. The
third misses by a clear margin; this is not a rounding artefact.

Subspace angles are **exactly zero** across all three rank tolerances and
across the last two metric refinements, so the identified subspace is not a
tolerance artefact either.

**Both surviving directions live almost entirely in one epoch, and it is the
youngest of the three.** Share of squared weight in temporal hat 2, support
[-109.1, -69.6] M: 99.8% for mode 1 and 99.8% for mode 2. Hat 0, the oldest at
[-128.8, -109.1] M, contributes exactly zero. Azimuthal content is m = 2 and
m = 3 dominant with m = 1 weaker; radial modes 1 and 2, mid-annulus.

The epoch breakdown of the resolved arm's target trace, an addition beyond the
listed export contents and labelled as one:

| temporal hat | support (M) | tr F known | tr F conditional | retained |
|---|---|---:|---:|---:|
| 0 | [-128.8, -109.1] | 0.002639 | 0.000370 | 0.140 |
| 1 | [-128.8, -89.4] | 0.254207 | 0.226730 | 0.892 |
| 2 | [-109.1, -69.6] | 10.796814 | 6.971218 | 0.646 |

So the concentration is not created by profiling. Before any nuisance is
removed, 97.7% of the resolved arm's
target sensitivity already sits in the hat adjacent to the direct footprint,
which ends at -57.8 M. The genuinely oldest hat carries
0.024% of the known-remainder trace and
retains 0.140 of it.

**This sharpens the claim and narrows it.** What survives an unknown remainder
is not old-epoch information in general: it is information at the near edge of
the old band. Any statement about the oldest epochs is not supported by this
calculation.

## The three findings, repaired

**Provenance.** One provenance.json written at R0 stood for all three phases,
and the R1 freeze omitted the R2 runner and the target manifest. `git log
--diff-filter=A` confirms d15debb first added the runner. Recorded in
`R2_CLOSEOUT_RECORD_024.json`, never backdated; the original run keeps its
bytes and its token with the review disposition attached.

**Coverage.** "10/10 physical sites covered" was inventory coverage and is
withdrawn. Recut by evidence level: {'PRODUCTION_INTEGRATION_TESTED': 1, 'ALGEBRAICALLY_EQUIVALENT': 7, 'DEFERRED_OR_RETIRED': 4}. That is
1 of 8
physical sites production-integration tested, not ten of ten. Deferred and
retired paths are no longer counted as passes.

**Completion.** The token now comes from
`phrt.revision_v4_1.completion`, which computes it from the seven declared
conditions and fails closed on one never recorded. `guards` refuses to start on
a violated input freeze, a drifted target column set, or an existing output
directory. All seven injected failures are tested and none reaches success.
G11 and G14 restored to 1e-10 with residuals reported; G09 and G10 now check
the full Fisher matrix, invariance entrywise and contraction in the Loewner
order.

## Raw map readiness

Every field the review named is in the archive: `alpha`, `beta`, `pixel_area`,
`valid`, `coordinate_time`, `delay`, all exposed by the reader. My earlier
conclusion that new geodesics would be required is **withdrawn** -- the
reduction discards the screen coordinates, the archive does not. The
retained-index lineage is not stored but is reproducible from the recorded
subsample seed. This is a readiness inventory only; it validates no
interpolation, no common-sky summation and no detector model.

## Not run

R3 in any form; a common-sky operator; extra geometries; nuisance enrichment;
any reconstruction, bank or estimator; a new submission freeze. The uploaded
Mahakal PDF remains a different document, absent from this machine, and
nothing here claims to reproduce it. The review's own arithmetic check and its
statement that it did not rerun the 513-test suite are recorded as given.

Generated 2026-09-06T14:40:57Z. Stopping.
