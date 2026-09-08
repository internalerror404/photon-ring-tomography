# Method dependencies recovered from archived source — review 039

Reviewed head: `1a6075512f714ca2b8a52173227b88a73cdad19b`.
This is source readback and interpretation, not a rerun of either experiment.
The passages below can replace the two unresolved-method boxes in Appendix A
of manuscript038, with the remaining eta limitation retained explicitly.

## 1. R1 evaluation-grid shape is recoverable from the executed call

The run manifest `artifacts/manifests/R1_20260826T022951Z_2ba66f02.json`
identifies execution commit `5f557fb606b76a95093cbf8e98d89d6f1dab9664`.
At that commit `scripts/run_r1_main.py` imports `evaluation_grid` from
`phrt.metrics.scoring` and calls it with exactly four arguments:

```python
rq, pq, tq = evaluation_grid(basis.r_inner, basis.r_outer,
                             basis.t_min, basis.t_max)
```

The imported function at the same commit is:

```python
def evaluation_grid(r_in, r_out, t_lo, t_hi,
                    n_r=10, n_phi=12, n_t=40):
    r = np.exp(np.linspace(np.log(r_in), np.log(r_out), n_r))
    phi = np.linspace(0.0, 2.0*np.pi, n_phi, endpoint=False)
    t = np.linspace(t_lo, t_hi, n_t)
    R, P, T = np.meshgrid(r, phi, t, indexing="ij")
    return R.ravel(), P.ravel(), T.ravel()
```

The function default ALONE would not identify the executed configuration.
The pinned caller, its explicit import, the omitted size arguments, and the
execution manifest together do identify the source-defined grid: **10 radial
x 12 azimuthal x 40 temporal points = 4,800 evaluation points**. This resolves
the grid definition without regenerating a source, estimator, or observation.
It does not claim an independent hash of a persisted evaluation-array payload.

The executed freeze supplies the domains:

- radius: `[1.8660386527060988, 49.98205255591607] M`, log-spaced,
  both endpoints included;
- azimuth: `[0, 2*pi)`, 12 uniformly spaced points;
- source time: `[-128.82234649196255, 29.0] M`, 40 uniform points,
  both endpoints included;
- flattening: `meshgrid(indexing="ij")`, default C-order ravel,
  i.e. time varies fastest, then azimuth, then radius.

The established Gaussian window, equal-grid-weight scoring convention and field
loss remain unchanged. This grid is NOT a physical-volume quadrature.

Source identities:

| File | Execution commit | Git blob |
|---|---|---|
| `scripts/run_r1_main.py` | `5f557fb606b76a95093cbf8e98d89d6f1dab9664` | `291adbf720007a300000ea570e6acbfceaacd3e1` |
| `src/phrt/metrics/scoring.py` | same | `0b04245c73ac80d63e3a6b8c2d2e67c2fef17dbc` |
| `artifacts/configs/R1_MAIN_FREEZE.json` | same | `b0b3b46dad00fb7f3bdf1d230505ca694cd1389d` |

The R1 caller blob was also read at the reviewed head and matches. The manifest
records the source-freeze SHA256 as
`4ef162320e09086a16f1e130b09a507d399438740647147560f339cd2aa60069`.

### Proposed replacement for the grid-dependency sentence

> The evaluation grid is fixed by the archived R1 caller and scorer at execution
> commit 5f557fb6: 10 logarithmically spaced radii, 12 uniformly spaced azimuths
> with the repeated endpoint omitted, and 40 uniformly spaced source times,
> using the support bounds in the executed freeze. Thus the field is scored at
> 4,800 points with the declared equal grid weights. This is a source-code-defined
> scoring grid; no independent continuum quadrature accuracy is implied.

## 2. Eta is a different kind of unresolved input

The same R1 caller computes eta before scoring the main bank, from the regenerated
prior-fit bank and its existing normalized age windows:

```python
eta = freeze_eta(
    np.sqrt(np.einsum("ap,np->na", Wn**2, pf**2)).ravel()
)
```

It then passes eta into the main scorer and prints it to six significant digits.
The freeze retains `metrics.eta_value: null`; the inspected run manifest does
not store a numerical eta value. Its rule is therefore resolved, but the precise
realized scalar was **not located in the inspected records**. This is not a claim
that no copy exists anywhere in the archive. A search on the connector's default
branch was not useful for this research-branch run and is not evidence of absence.

Use a bounded lookup of recorded stdout, run sidecars, or authenticated cached
fit norms. An old rounded stdout value must be labeled with its actual precision.
A scalar derived now from authentic saved fit norms would be a derived readback,
not a newly discovered contemporaneous record. Do not fabricate eta, use another
experiment's eta, or silently rebuild the truth bank to fill this field.

If no record is recovered, retain `REALIZED_ETA_NOT_LOCATED` as a reproducibility
limitation and let the authors decide how to restrict the numerical presentation.
The archived rule is not absent, but the scalar's absence must not be hidden by
marking every execution-specific metric input resolved.

## 3. HMT2 paired reduction: the full caller-to-helper chain is now read

The HMT2 manifest identifies execution commit
`9713af2caf3f1035622b09c8026ea31f75c0275e` and the 60-history/four-draw bank.
The following three file blobs match at that execution commit and the reviewed
head; both versions were fetched through the connector:

| File | Git blob |
|---|---|
| `scripts/run_hmt2_sealed_main.py` | `0e65135fa2f4bfb83e36c7f65b23d4ef8c62704d` |
| `scripts/run_hmt2_sealed_main_score.py` | `3b1f5f983a9204b856bbabcbd446dc629c9dc01f` |
| `scripts/run_hmt1_score.py` | `03f13ef1a2c1e47807f125feaf4785f871df0fda` |

For fixed class, estimator, SNR and target, denote the state-dependent error for
history j, draw b, arm a, and declared age k by e[j,b,a,k]. The caller first uses
`aggregate_all_states` to average all age/state errors for each draw, then
averages those draw-level values for each history:

    ebar[j,a] = mean_b( mean_k e[j,b,a,k] ).

Every state belongs to the primary endpoint; non-DEAD scores are separate
companions. The endpoint writer pairs direct and comparison histories by
`(family,index)` and sends these per-history scores to `paired_relative`:

    r[j] = (ebar[j,direct] - ebar[j,a]) /
           max(abs(ebar[j,direct]), 1e-300),
    reported point estimate = median_j r[j].

Thus the paired ratios are formed **after** within-history averaging, and the
headline is the **median across histories**. It is not the relative reduction
of the two population mean errors, nor a median of per-state ratios. With an
equal number of ages and draws, the two within-history arithmetic means commute;
the nonlinear ratio and outer median do not generally commute with averaging.

The helper also computes a cell/family-balanced mean, but the main endpoint
writer uses its `median` and `median_ci_low` fields for the declared headline
and materiality test. Do not substitute the other estimand.

For the median interval, `paired_relative` draws 10,000 bootstrap count vectors
at helper seed `boot.seed + 1`, recomputes the median of the resampled history
ratios, and uses the 2.5th and 97.5th percentiles. The HMT2 caller supplies
`boot.seed = 20260953`, so this median path uses **20260954**. The history is the
independent resampling unit; the four draws are already contained in its score.
The reported lower endpoint is the lower end of that 95% percentile interval,
not an independently chosen one-sided confidence convention.

The paired wrapper intersects history IDs and masks nonfinite paired scores.
Do not turn this into evidence that there were no missing pairs without the
saved endpoint counts. The reported main count is 60; that outcome was not
independently recomputed from the parquet arrays in this review.

### Proposed replacement for Appendix A.2's dependency box

> For each history and arm, we average the state-dependent error over the declared
> ages for each draw, then over its four noise draws. Histories are paired across
> arms by their fixed IDs. We compute the direct-relative reduction of each pair
> using the direct history's mean error as denominator (with the recorded numerical
> floor), and report the median of these history-level reductions. The median's
> 95% percentile interval uses 10,000 bootstrap resamples of histories. The
> separately computed family-balanced mean is not the primary estimand.

## 4. A remaining estimator-source sentence needs its experiment qualifier

Manuscript038 section 3 says the recovery estimators were tuned on R0C and then
frozen. That is the R1 lineage, not the common lineage of every recovery program.
The HMT2 sealed freeze explicitly says its 16 hyperparameters were inherited
from its own stage-1 selection and that the main runner performs no sweep.
Replace the global sentence with:

> R1 reuses its R0C validation-selected hyperparameters. HMT2 reuses its own
> stage-1 selection through the HMT2 sealed-main freeze. Neither main experiment
> tunes on its held-out bank. The estimator family, source representation,
> regularization convention and selection split are specified per experiment.

This is a prose/source-identity correction. No estimator or selected value is
changed. Preserve the separate R1 posterior-calibration withdrawal.
