# AGE_INTERVAL_SEMANTICS_AMENDMENT_003

Nonblocking amendment required by the reviewer ruling that accepted E3C v2 and
activated the canary reconstruction pilot. It changes vocabulary and adds two
observables. **No physical operator is recomputed**: every value below is
re-derived from the `age_threshold_mask` already stored in the canonical
per-geometry E3C results, and the re-derivation is checked against the value
each row already carried.

## What was wrong

`largest_contiguous_detectable_depth` was implemented as the length of the
longest detectable run *anywhere* on the age grid. A span length is not a depth
from the present. A long run can sit entirely in the past with an undetectable
gap between it and now, and calling that "depth" would claim recoverable
history that the observation does not have.

## The four observables

| name | what it is |
|---|---|
| `oldest_detectable_age_probe` | the reach. A supremum, blind to holes. Retained unchanged. |
| `longest_detectable_run_span_M`, `_start_M`, `_end_M` | the longest run of consecutive detectable ages anywhere on the grid, with both endpoints. This is the quantity previously called `largest_contiguous_detectable_depth`. It is never labelled history from the present. |
| `contiguous_detectable_span_from_anchor_M`, `contiguous_detectable_end_from_anchor_M` | the stretch that actually connects to the anchor. The only one of the three that may be described as continuous history from the present. |
| `a_anchor_M` | the reconstruction anchor. |

`anchor_is_detectable` and `n_detectable_runs` are emitted alongside, so a
reader can tell a zero anchored span caused by an unobserved present from one
caused by an undetectable present.

## The anchor

A probe centred at age `a` occupies source time `-a` within three half widths.
The source times an observation can reach at all run from
`min(t_obs) - max(delay)` to `max(t_obs) - min(delay)`. The anchor is the
youngest age on the common grid whose **whole** probe support lies inside that
window. It is a property of the observation, computed before any detectability
or error curve is read.

Each geometry is anchored at its own value, because that is where its own
observable present begins. The grid anchor — the oldest of them, admissible
everywhere — is reported beside them for cross-geometry statements, never in
place of them.

On the registered E3C grid:

```text
a000_i020  0 M      a000_i050  0 M      a000_i075  32 M
a050_i020  0 M      a050_i050  0 M      a050_i075  28 M
a090_i020  0 M      a090_i050  0 M      a090_i075  28 M
a098_i020  0 M      a098_i050  0 M      a098_i075  28 M
grid anchor 32 M
```

The four `i = 75` geometries are exactly the case the ruling anticipated: the
minimum delay in the frozen ray set exceeds the last observer sample, so no
photon carries information about the present at all and the youngest
recoverable epoch is a positive age. That centre is recorded rather than
rounded down to zero.

## Anchored stable depth, for R0

```text
T_stable^anchor(eps, q) = sup { T >= a_anchor :
                                Pr[ sup_{a_anchor <= a <= T} E(a) <= eps ] >= q }
L_stable^anchor         = T_stable^anchor - a_anchor
```

The supremum over the age window is **inside** the probability and is taken per
truth: a truth counts only if the whole window from the anchor out to `T` is
good for that truth. The pre-amendment implementation thresholded the per-age
passing fraction, which asks a weaker question — it lets a different subset of
truths fail at each age and still calls the window stable.

A secondary unanchored longest stable interval may be reported with both
endpoints. It must not be called depth from the present.

## Where the amendment is applied

* `src/phrt/metrics/age_intervals.py` — the single implementation.
* `src/phrt/audits/e3c_contract.py` — `detectability()` delegates to it and now
  requires `a_anchor` rather than defaulting it, because defaulting it to zero
  is the silent assumption the amendment exists to remove.
* `scripts/build_e3c_tables.py` — applied at the one point where the canonical
  per-geometry results are read, so every derived table speaks one vocabulary.
* `scripts/apply_age_interval_amendment_003.py` — the independent check: it
  refuses to run unless the E3C freeze and registry on disk are the pinned ones,
  re-derives all 1152 depth rows from their own masks, requires exact agreement
  with the pre-amendment values, and records the before/after digest of every
  derived artifact it causes to be rewritten.

`scripts/build_e3c_freeze.py` is deliberately **not** edited. It reproduces the
pinned freeze byte for byte and the freeze digest is pinned in the R0
provenance block; the amendment is recorded alongside the freeze rather than
inside it.

## Result of the reassembly

```text
depth rows re-derived from their own masks   1152
max deviation, reach                         0.0
max deviation, longest-run span              0.0
rows where the anchored span is not the
  longest run anywhere                        316 of 1152
rows whose detectable set is not an interval    2 of 952 with any detection
rows with no detectable age at all            200
```

The two deviations being exactly zero is the point: the amendment is a rename
plus two additions, not a change of value.
