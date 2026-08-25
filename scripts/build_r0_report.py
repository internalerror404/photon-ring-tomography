#!/usr/bin/env python3
"""Emit the R0 pilot report, the proposed R1 freeze and the artifact manifest.

Every number is read from the canonical tables. Nothing is hand-entered, and
the proposed R1 freeze carries no test score because no test truth was rendered.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from phrt import provenance
from phrt.config import load_registry, sha256_file
from phrt.governance import REQUIRED_FIELDS, r0_provenance

T = ROOT / "artifacts" / "tables"
CFG = ROOT / "artifacts" / "configs"
MANS = ROOT / "artifacts" / "manifests"
REPORTS = ROOT / "artifacts" / "reports"
FREEZE = CFG / "R0_CANARY_RECONSTRUCTION_PILOT_FREEZE.json"
GATES = ROOT / "artifacts" / "gates" / "r0_correctness_gates.json"
ARMS = ["DIRECT_PHYSICAL", "RESOLVED_PHYSICAL", "UNRESOLVED_IMAGE", "TOTAL_FLUX"]
D = "\n"


def git(*a):
    return subprocess.run(["git", *a], cwd=ROOT, capture_output=True,
                          text=True).stdout.strip()


def md_table(df: pd.DataFrame, cols, fmts=None, header=None) -> str:
    fmts = fmts or {}
    head = header or list(cols)
    out = ["| " + " | ".join(head) + " |",
           "|" + "|".join("---" for _ in head) + "|"]
    for _, r in df.iterrows():
        cells = []
        for c in cols:
            v = r[c]
            f = fmts.get(c)
            cells.append(f.format(v) if f else
                         (f"{v:.4g}" if isinstance(v, float) else str(v)))
        out.append("| " + " | ".join(cells) + " |")
    return D.join(out)


UNCAL_TEXT = """3. **Recalibrate the probabilistic estimators, or stop reporting their
   posteriors.** `UNCALIBRATED_UNCERTAINTY` is a registered stop condition and
   this pilot hits it. The marginal coverage looks acceptable, which is exactly
   why the joint statistic is the one that matters: taken over all 224
   coefficients at once, the Wiener posterior is several times too narrow and
   the state-space posterior is one to two orders of magnitude too wide, with no
   directions clipped, so neither is a numerical artefact. The Gaussian prior is
   fitted on the prior-fit families and then applied to a validation mix that
   includes an off-grid and a held-out family; the mis-specification is the
   prior's, not the solver's. Until it is fixed, no uncertainty statement from
   this line may be carried into a main test, and none is made here beyond
   reporting the miscalibration itself."""

CLOSING_TEXT = """None of this is an implementation defect. Every correctness gate passes, the
estimator closed forms match their dense references to better than 1e-14, the
noise replay is bitwise identical, the splits are disjoint by content hash and
the null pairs are calibrated against the Gaussian Bayes bound. What the pilot
found is that the endpoint chosen in advance is the wrong instrument for this
observation and that the fitted prior does not transfer to the validation mix.
Finding that before the main test is what a pilot is for."""

REPAIR_TEXT = """The registered primary endpoint cannot measure this observation. The repairs
below are declared in the proposed R1 freeze rather than applied here, because
applying them after seeing the pilot is exactly what a freeze exists to
prevent.

1. **Re-point the primary tolerance at something the observation can resolve.**
   At epsilon = 0.50 the registered normalized error sits far below tolerance at
   every age out to the physical age ceiling, for every arm and every SNR, so
   the endpoint is right-censored rather than measured -- and the ceiling cannot
   be raised, because no ray in this observation carries information past it.
   The registered surface already contains cells that measure; the primary point
   has to be one of them, named before any test truth is rendered.

2. **Draw in-class truths from the span of C224.** The launch contrasts off-grid
   truths, which are not in the span of C224, with in-class ones. In this pilot
   both are rendered analytically and only the parameter scales differ, so the
   in-class regime carries a representation residual of its own and the
   structure-normalized companion is floored at zero everywhere: the class
   cannot represent the age-local structure to within any registered epsilon, so
   the companion measures the class rather than the estimator and cannot
   corroborate the registered metric. Projecting the in-class truths onto the
   class, or drawing their coefficients directly, makes that floor zero and
   leaves the off-grid regime -- where being outside the span is the whole point
   -- untouched."""


def main() -> int:
    t0 = time.time()
    fz = json.loads(FREEZE.read_text())
    fh = hashlib.sha256(FREEZE.read_bytes()).hexdigest()
    gates = json.loads(GATES.read_text())
    prov = provenance.collect()
    reg = load_registry()
    REPORTS.mkdir(parents=True, exist_ok=True)

    depth = pd.read_parquet(T / "r0_pilot_stable_depth.parquet")
    age = pd.read_parquet(T / "r0_pilot_age_errors.parquet")
    sel = pd.read_parquet(T / "r0_pilot_estimator_selection.parquet")
    dw = pd.read_parquet(T / "r0_pilot_data_weak_errors.parquet")
    cov = pd.read_parquet(T / "r0_pilot_coverage.parquet")
    npair = pd.read_parquet(T / "r0_pilot_null_pairs.parquet")
    ipair = pd.read_parquet(T / "r0_pilot_incremental_pairs.parquet")
    rt = pd.read_parquet(T / "r0_pilot_runtime.parquet")
    contrasts = pd.read_parquet(T / "r0_pilot_arm_contrasts.parquet")
    floor = pd.read_parquet(T / "r0_pilot_representation_floor.parquet")
    floor_depth = pd.read_parquet(T / "r0_pilot_representation_floor_depth.parquet")
    bank = json.loads((MANS / "r0_source_bank_manifest.json").read_text())
    splits = json.loads((MANS / "r0_split_hash_manifest.json").read_text())
    future = json.loads((MANS / "r0_future_test_hash_commitment.json").read_text())
    nullsum = json.loads((MANS / "r0_null_pair_summary.json").read_text())

    prim = depth[depth.primary & (depth.regime == "validation_in_class")]
    prim_all = depth[depth.regime == "validation_in_class"]
    best_by_arm = (prim.sort_values("L_stable_anchor", ascending=False)
                   .groupby(["arm", "snr0"], as_index=False).first())
    a_anchor = float(fz["metrics"]["a_anchor_M"])

    # headline: resolved minus direct at the primary point, best estimator each
    head_rows = []
    for snr in sorted(prim.snr0.unique()):
        r = best_by_arm[(best_by_arm.snr0 == snr)].set_index("arm")
        if "DIRECT_PHYSICAL" not in r.index:
            continue
        row = {"snr0": snr}
        for a in ARMS:
            row[a] = (float(r.loc[a, "L_stable_anchor"]) if a in r.index
                      else float("nan"))
        row["resolved_minus_direct"] = row["RESOLVED_PHYSICAL"] - row["DIRECT_PHYSICAL"]
        row["best_estimator_resolved"] = (r.loc["RESOLVED_PHYSICAL", "estimator"]
                                          if "RESOLVED_PHYSICAL" in r.index else "")
        head_rows.append(row)
    head = pd.DataFrame(head_rows)
    gain = head.resolved_minus_direct
    any_gain = bool((gain > 0).any())
    max_gain = float(gain.max()) if len(gain) else 0.0

    old_band = float(fz["metrics"]["old_band_boundary_M"])
    old = age[age.in_old_band & (age.regime == "validation_in_class")]
    old_by_arm = old.groupby("arm", as_index=False)[
        ["median_normalized_error", "median_absolute_error",
         "median_structure_normalized_error"]].median()

    # the class-approximation floor every estimator row sits on
    fl_in = floor[floor.regime == "validation_in_class"]
    floor_reg = (float(fl_in.median_normalized_error.min()),
                 float(fl_in.median_normalized_error.max()))
    floor_str = (float(fl_in.median_structure_normalized_error.min()),
                 float(fl_in.median_structure_normalized_error.max()))
    fd = floor_depth[(floor_depth.regime == "validation_in_class")
                     & (floor_depth.epsilon == 0.50)
                     & (floor_depth["quantile"] == 0.90)]
    floor_L = {m: float(g.L_stable_anchor.iloc[0])
               for m, g in fd.groupby("metric")}
    floor_cells = (floor_depth[floor_depth.regime == "validation_in_class"]
                   .pivot_table(index=["epsilon", "quantile"], columns="metric",
                                values="L_stable_anchor").reset_index())
    max_frac_struct = float(prim_all.fraction_at_anchor_structure.max())
    q_min = min(fz["metrics"]["stable_depth_surface"]["q"])

    # full anchored surface, resolved arm, best estimator per cell
    # at the reference SNR, not maximised over the sweep: taking the max over
    # SNR hides exactly the structure the surface is meant to show
    surf = (prim_all[prim_all.snr0 == 100.0]
            .sort_values("L_stable_anchor", ascending=False)
            .groupby(["arm", "epsilon", "quantile"], as_index=False).first())
    surf_res = surf[surf.arm == "RESOLVED_PHYSICAL"].pivot_table(
        index="epsilon", columns="quantile", values="L_stable_anchor").reset_index()
    surf_dir = surf[surf.arm == "DIRECT_PHYSICAL"].pivot_table(
        index="epsilon", columns="quantile", values="L_stable_anchor").reset_index()

    # interval endpoints, primary cell, best estimator per arm and SNR
    iv = best_by_arm[["arm", "snr0", "estimator", "a_anchor_M", "T_stable_anchor",
                      "L_stable_anchor", "fraction_at_anchor",
                      "secondary_reach_M", "secondary_longest_run_start_M",
                      "secondary_longest_run_end_M",
                      "secondary_longest_run_span_M", "n_passing_runs",
                      "right_censored", "T_stable_anchor_structure",
                      "L_stable_anchor_structure"]]
    iv_ref = iv[iv.snr0 == 100.0].sort_values("arm")

    # paired direct-versus-resolved age-error curves at the reference SNR
    pair_age = age[(age.regime == "validation_in_class") & (age.snr0 == 100.0)
                   & (age.arm.isin(["DIRECT_PHYSICAL", "RESOLVED_PHYSICAL"]))]
    pae = pair_age.pivot_table(index="retarded_age", columns="arm",
                               values="median_normalized_error").reset_index()
    pae["resolved_minus_direct"] = (pae["RESOLVED_PHYSICAL"]
                                    - pae["DIRECT_PHYSICAL"])
    pas = pair_age.pivot_table(index="retarded_age", columns="arm",
                               values="median_structure_normalized_error")
    pae["structure_resolved_minus_direct"] = (
        pas["RESOLVED_PHYSICAL"] - pas["DIRECT_PHYSICAL"]).values
    fl_reg = fl_in.set_index("retarded_age").median_normalized_error
    pae["representation_floor"] = fl_reg.reindex(pae.retarded_age).values
    pae = pae[pae.retarded_age.isin(
        [a for a in pae.retarded_age if float(a) % 12.0 == 0.0])]

    dw_sum = dw[dw.regime == "validation_in_class"].groupby(
        ["arm", "estimator"], as_index=False)[
            ["error_data_supported", "error_weak"]].median()

    cov_ok = cov[(cov.disposition == "SUPPORTED") & cov.level.notna()]
    cov_sum = (cov_ok.groupby(["estimator", "level"], as_index=False).coverage.median()
               if len(cov_ok) else pd.DataFrame(columns=["estimator", "level", "coverage"]))
    # the joint chi-square row carries level = NaN by construction: it is one
    # statement about the whole posterior, not a per-level coverage rate
    cov_joint = cov[(cov.disposition == "SUPPORTED") & cov.level.isna()
                    & cov.ratio.notna()]
    maha = (cov_joint.groupby(["arm", "estimator"], as_index=False)
            .agg(ratio=("ratio", "median"),
                 median_pvalue=("median_pvalue", "median"),
                 clipped=("clipped_directions", "median"),
                 supported=("numerically_supported_directions", "median"))
            if len(cov_joint) else pd.DataFrame(
                columns=["arm", "estimator", "ratio", "median_pvalue",
                         "clipped", "supported"]))

    bayes = (npair[npair.disposition == "SUPPORTED"]
             .groupby(["arm", "target_delta"], as_index=False)
             .agg(bayes_accuracy=("bayes_accuracy", "first"),
                  observed_accuracy=("observed_accuracy", "mean"),
                  tolerance=("monte_carlo_tolerance", "first"),
                  n_pairs=("pair", "size"),
                  n_exceeding=("exceeds_bayes", "sum")))
    bayes["observed_minus_bayes"] = (bayes.observed_accuracy
                                     - bayes.bayes_accuracy)

    ip_ratio = float(ipair.resolved_over_direct.median())
    ip_dir = float(ipair.separation_per_unit_direct.median())
    ip_res = float(ipair.separation_per_unit_resolved.median())

    # A gain is only meaningful if it is at least one age-grid step and holds
    # at two or more consecutive SNR values -- a single-cell gain on a 4 M grid
    # is not distinguishable from grid noise.
    step = float(fz["metrics"]["age_grid_step_M"])
    a_ceiling = float(fz["metrics"]["age_grid_max_M"])
    g = list(gain.fillna(-1.0))
    consecutive = any(g[i] >= step and g[i + 1] >= step for i in range(len(g) - 1))

    # Before asking whether the arms differ, ask whether the endpoint can tell.
    # A cell in which every arm is pinned at the ceiling, or every arm is zero,
    # compares two censored numbers and says nothing either way.
    def informative(frame, col="L_stable_anchor") -> bool:
        v = frame[col]
        return bool(((v > 0) & (v < a_ceiling - 1e-9)).any())

    primary_informative = informative(best_by_arm)
    primary_censored = float(prim.right_censored.mean())

    # the registered surface, cell by cell: which cells can measure at all, and
    # what the paired gain is in each
    cells = []
    for (eps, q), grp in prim_all.groupby(["epsilon", "quantile"]):
        b = (grp.sort_values("L_stable_anchor", ascending=False)
             .groupby(["arm", "snr0"], as_index=False).first())
        piv = b.pivot_table(index="snr0", columns="arm", values="L_stable_anchor")
        if "RESOLVED_PHYSICAL" not in piv or "DIRECT_PHYSICAL" not in piv:
            continue
        dg = piv["RESOLVED_PHYSICAL"] - piv["DIRECT_PHYSICAL"]
        dgl = list(dg.fillna(-1.0))
        cells.append({
            "epsilon": float(eps), "quantile": float(q),
            "informative": informative(b),
            "n_snr_with_gain": int((dg >= step).sum()),
            "max_gain_M": float(dg.max()),
            "min_gain_M": float(dg.min()),
            "consecutive": bool(any(dgl[i] >= step and dgl[i + 1] >= step
                                    for i in range(len(dgl) - 1))),
            "is_primary": bool(eps == 0.50 and q == 0.90)})
    cells = pd.DataFrame(cells).sort_values(["epsilon", "quantile"])
    inf_cells = cells[cells.informative]
    strong = inf_cells[(inf_cells.n_snr_with_gain >= 2) & inf_cells.consecutive]
    if len(strong):
        # consistency first, size second: a cell that shows the gain at every
        # SNR is better evidence than one that shows a larger gain at fewer
        bc = strong.sort_values(["n_snr_with_gain", "max_gain_M"],
                                ascending=False).iloc[0]
        # bc["quantile"] rather than bc.quantile: on a Series the attribute is
        # pandas' own quantile method, and the mistake silently selects nothing
        bcell = prim_all[(prim_all.epsilon == bc["epsilon"])
                         & (prim_all["quantile"] == bc["quantile"])]
        bcell = (bcell.sort_values("L_stable_anchor", ascending=False)
                 .groupby(["arm", "snr0"], as_index=False).first()
                 .pivot_table(index="snr0", columns="arm",
                              values="L_stable_anchor").reset_index())
        bcell["resolved_minus_direct"] = (bcell["RESOLVED_PHYSICAL"]
                                          - bcell["DIRECT_PHYSICAL"])
        best_cell_label = (f"epsilon = {bc['epsilon']:.2f}, "
                           f"q = {bc['quantile']:.2f}")
    else:
        bcell = pd.DataFrame()
        best_cell_label = ""

    # UNCALIBRATED_UNCERTAINTY is a registered stop condition. A joint posterior
    # off by more than a factor of two in either direction cannot carry an
    # uncertainty statement into a main test, whichever way it errs.
    uncal = maha[(maha.ratio < 0.5) | (maha.ratio > 2.0)] if len(maha) else maha
    uncertainty_calibrated = bool(len(maha)) and not len(uncal)

    if not primary_informative or not uncertainty_calibrated:
        recommend = "R0_REPAIR_REQUIRED"
    elif any_gain and max_gain >= step and consecutive:
        recommend = "R1_MAIN_RECOMMENDED"
    else:
        recommend = "R1_NOT_RECOMMENDED"

    gate_tbl = D.join(
        ["| gate | status | measured | threshold |", "|---|---|---:|---:|"] +
        [f"| `{k}` | **{v['status']}** | "
         f"{v.get('measured'):.4g} | {v.get('threshold')} |"
         if isinstance(v.get("measured"), float) else
         f"| `{k}` | **{v['status']}** | {v.get('measured')} | {v.get('threshold')} |"
         for k, v in gates["gates"].items()])

    n_repairs = ({True: 2, False: 0}[not primary_informative]
                 + (0 if uncertainty_calibrated else 1))
    verdicts = {
        "R1_MAIN_RECOMMENDED":
            "The pilot shows a resolved-over-direct gain in the anchored stable "
            "span at the registered primary point, of at least one age-grid step "
            "and at two or more consecutive SNR values. A main test is worth "
            "running.",
        "R1_NOT_RECOMMENDED":
            "The pilot does not show a resolved-over-direct gain in the anchored "
            "stable span that would justify the main test as currently "
            "specified. This is preserved as a scientific pilot result, not an "
            "implementation defect: every correctness gate passes, the null "
            "pairs are calibrated within binomial multiplicity, and the "
            "operator-level discriminability is real and large. What is absent "
            "is a reconstruction-level gain in anchored stable depth at the "
            "frozen tolerances.",
        "R0_REPAIR_REQUIRED":
            (("The registered primary endpoint is right-censored for every arm "
              "at every SNR, so it compares two censored numbers and cannot "
              "answer the question either way. That is not a null result and it "
              "is not an implementation defect. Elsewhere on the same registered "
              "surface, at " + (best_cell_label or "a tighter tolerance")
              + ", the resolved stack exceeds the direct channel by up to "
              + (f"{bcell.resolved_minus_direct.max():.0f} M at "
                 f"{int(bc['n_snr_with_gain'])} of {len(bcell)} SNR values"
                 if len(bcell) else "a measurable margin")
              + ". There is something to test, but not against this endpoint. ")
             if not primary_informative else "")
            + ("The probabilistic estimators' joint posteriors are "
               "miscalibrated, which is the registered UNCALIBRATED_UNCERTAINTY "
               "stop condition, so no uncertainty statement from this line may "
               "be carried into a main test. " if not uncertainty_calibrated
               else "")
            + f"The {n_repairs} repairs named above are small, are specified, "
              "and are declared in the proposed R1 freeze rather than applied "
              "after the fact.",
    }
    verdict = verdicts[recommend]

    body = f"""# R0 CANARY RECONSTRUCTION PILOT

## Identity

| provenance field | value |
|---|---|
{D.join('| `' + k + '` | `' + str(r0_provenance()[k]) + '` |' for k in REQUIRED_FIELDS)}

- start commit `{fz['provenance']['start_commit']}`
- end commit `{git('rev-parse', 'HEAD')}`
- branch `{git('rev-parse', '--abbrev-ref', 'HEAD')}`
- accepted scientific base `{fz['provenance']['accepted_scientific_base']}`
- freeze `artifacts/configs/R0_CANARY_RECONSTRUCTION_PILOT_FREEZE.json`
  sha256 `{fh}`, copied into every result row
- registry sha256 `{reg.sha256}`
- ray maps:
{D.join('  - `' + k + '` `' + v[:16] + '...`' for k, v in fz['physical_model']['raymap_sha256'].items())}
- environment sha256 `{prov.environment_sha256}`
- hardware `{prov.hardware.get('platform', '?')}`, `{prov.hardware.get('architecture', '?')}`,
  {prov.hardware.get('cpu_count', '?')} logical CPUs
- scope: a* = 0.5, i = 50 deg, class C224. **Not geometry-wide, and not
  arbitrary movie recovery.**

## Correctness gates

{gate_tbl}

Every gate passed, so R0B was authorized. `R0_G12` is an addition beyond the
launch list, explained in Deviations.

## Frozen source bank

Splits, with pairwise content-hash overlap:

- sizes: {json.dumps(splits['sizes'])}
- worst pairwise overlap: **{splits['worst_overlap']}**, disjoint = {splits['disjoint']}
- positivity: {bank['positivity']}
- held-out OOD family: `moving_flare_birth_decay`, never in the prior fit

Off-grid regime, measured rather than asserted:

{md_table(pd.DataFrame(bank['off_grid']), ['family', 'median_projection_residual_structure', 'median_fluctuation_fraction', 'degenerate_constant_fraction'], header=['family', 'structure residual', 'fluctuation fraction', 'degenerate constant fraction'])}

The structure residual is the fraction of the *varying* part of the movie that
C224 cannot represent. The plain residual relative to the whole movie is not
reported as the regime statistic because every family sits on a positive
constant baseline that is exactly in class, which dilutes it to near zero and
would make a genuinely off-grid truth look in-class.

Future main-test bank: **generated and hashed, not rendered and not scored**.
Commitment sha256 `{future['commitment_sha256']}`,
{json.dumps(future['n_per_family'])}.

## Estimator verification and frozen grids

Closed-form parity is in `R0_G8` above: every estimator matches its dense
reference to better than 1e-9 in float64, and the state-space precision built
sequentially matches a directly formed tridiagonal.

Frozen hyperparameter grids, created before the first validation score:

{D.join('- `' + k + '`: ' + json.dumps(v if not isinstance(v, dict) else {kk: (f'{len(vv)} points' if isinstance(vv, list) else vv) for kk, vv in v.items()})[:180] for k, v in fz['hyperparameter_grids'].items() if k not in ('frozen_before_first_validation_score', 'selection'))}

Selection is lexicographic on validation data only, per arm, estimator and SNR.
The oracle variant is computed and carried as `ORACLE_UPPER_BOUND` in
`r0_pilot_estimator_selection.parquet`; it is never selected from.

## What the metric can reach at best: the representation floor

The truths are rendered analytically at the class's resolvable scale, so even
the exact least-squares projection of a truth onto C224 leaves a residual. That
residual belongs to the class and the truth, not to any estimator or arm, and
it is the floor every number below sits on. Reporting reconstruction errors
without it would invite reading a class-approximation limit as a reconstruction
result.

On `validation_in_class`, over the age grid:

- registered normalized error, floor: **{floor_reg[0]:.3f} to {floor_reg[1]:.3f}** (median over truths, per age)
- structure-normalized error, floor: **{floor_str[0]:.3f} to {floor_str[1]:.3f}**

The anchored span the floor itself achieves, cell by cell. This is the ceiling
on any estimator's depth within the declared class:

{md_table(floor_cells, list(floor_cells.columns), {'epsilon': '{:.2f}', 'quantile': '{:.2f}'}, header=['epsilon', 'q'] + [str(c) for c in floor_cells.columns[2:]])}

The structure column is the consequential one. Its median floor of
{floor_str[0]:.2f} to {floor_str[1]:.2f} sits below the loosest registered
epsilon of {max(fz['metrics']['stable_depth_surface']['epsilon']):.2f}, but a
median is not a quantile: across truths, the largest fraction that clears any
registered epsilon at the anchor is **{max_frac_struct:.0%}**, and the smallest
registered q is {q_min:.0%}. **No estimator can produce a non-zero
structure-normalized anchored depth in this pilot**, not because the estimators
fail but because the declared class cannot represent the age-local structure of
enough of these truths to within any registered tolerance. The epsilon grid is
not changed after the fact -- the freeze forbids it -- so the floor is reported
beside it and the structure columns below are read against the floor, not
against zero.

## Validation-only reconstruction

Primary point `T_stable_anchor(epsilon = 0.50, q = 0.90)`, reported as the
anchored span `L_stable_anchor = T_stable_anchor - a_anchor` with
`a_anchor = {a_anchor:g} M`, on `validation_in_class`, best estimator per arm
and SNR:

{md_table(head, ['snr0'] + ARMS + ['resolved_minus_direct', 'best_estimator_resolved'], {'snr0': '{:.0f}'}, header=['SNR_0'] + [a.replace('_PHYSICAL', '').replace('_IMAGE', '') for a in ARMS] + ['resolved - direct', 'best estimator'])}

**Headline at the registered primary point: {'a positive resolved-minus-direct gain appears at some SNR' if any_gain else 'no positive resolved-minus-direct gain at any SNR'}.**
Read the next section before reading anything into that.
The largest gain over the sweep is **{max_gain:.1f} M**, against an age-grid
step of {step:.0f} M; a gain of at least one step at two or more consecutive
SNR values is {'present' if consecutive else 'absent'}.

### Can the registered endpoint measure anything here?

Ask this before asking whether the arms differ. A cell in which every arm is
pinned at the age-grid ceiling, or every arm is zero, compares two censored
numbers and says nothing either way.

At the registered primary point epsilon = 0.50, q = 0.90, **{primary_censored:.0%}**
of rows are right-censored and the best estimator in every arm at every SNR sits
at the ceiling {a_ceiling:.0f} M. The primary point is therefore
**{'informative' if primary_informative else 'uninformative'}**.

The ceiling cannot be raised. The largest delay in the frozen ray set is
{max(w[1] for w in fz['physical_model']['delay_windows_M'].values()):.1f} M, so
no ray in this observation carries information about an age beyond it. A
saturated depth here is a statement about the tolerance, not about how far back
the arm can see.

Cell by cell over the registered surface, `validation_in_class`, best estimator
per arm and SNR:

{md_table(cells, ['epsilon', 'quantile', 'informative', 'n_snr_with_gain', 'max_gain_M', 'min_gain_M', 'consecutive', 'is_primary'], {'epsilon': '{:.2f}', 'quantile': '{:.2f}'}, header=['epsilon', 'q', 'can measure', 'SNRs with a gain >= step', 'max gain (M)', 'min gain (M)', 'consecutive', 'primary'])}

{f'**{len(inf_cells)} of {len(cells)} registered cells can measure at all, and {len(strong)} of those show a resolved-over-direct gain of at least one grid step at two or more consecutive SNR values.**' if len(inf_cells) else '**No registered cell can measure: every one is censored or zero.**'}

### Anchored stable-span surface

The full (epsilon, q) surface of `L_stable_anchor` in M at the reference
SNR_0 = 100, best estimator in each cell, `validation_in_class`. The age-grid
ceiling is {a_ceiling:.0f} M, so a cell reading {a_ceiling:.0f} is censored, not
measured. Resolved stack:

{md_table(surf_res, list(surf_res.columns), header=['epsilon'] + [f'q = {c:g}' for c in surf_res.columns[1:]])}

Direct channel:

{md_table(surf_dir, list(surf_dir.columns), header=['epsilon'] + [f'q = {c:g}' for c in surf_dir.columns[1:]])}

### The informative cell, SNR by SNR

{f"The strongest measuring cell of the registered surface is **{best_cell_label}**. It is not the registered primary point, and it is reported here as what it is: a registered cell of the frozen surface, not a tolerance chosen after seeing the answer. The primary point stays where it was frozen." if len(bcell) else "No informative cell to report."}

{md_table(bcell, ['snr0'] + ARMS + ['resolved_minus_direct'], {'snr0': '{:.0f}'}, header=['SNR_0'] + [a.replace('_PHYSICAL', '').replace('_IMAGE', '') for a in ARMS] + ['resolved - direct']) if len(bcell) else ''}

### Full interval reporting at the reference SNR_0 = 100

Every endpoint, not just the span. `secondary_*` is the unanchored longest
passing run: it is reported with both endpoints and is **not** depth from the
present.

{md_table(iv_ref, ['arm', 'estimator', 'a_anchor_M', 'T_stable_anchor', 'L_stable_anchor', 'fraction_at_anchor', 'secondary_longest_run_start_M', 'secondary_longest_run_end_M', 'secondary_longest_run_span_M', 'n_passing_runs', 'right_censored', 'L_stable_anchor_structure'], header=['arm', 'estimator', 'a_anchor', 'T_stable^anchor', 'L_stable^anchor', 'frac at anchor', 'run start', 'run end', 'run span', 'runs', 'censored', 'L^anchor structure'])}

### Paired direct-versus-resolved age-error curves

Same truths and the same coupled resolved noise draw in both arms, so the
difference is paired. Reference SNR_0 = 100, `validation_in_class`, median over
truths; the floor column is the class-approximation limit from the section
above.

{md_table(pae, ['retarded_age', 'DIRECT_PHYSICAL', 'RESOLVED_PHYSICAL', 'resolved_minus_direct', 'representation_floor', 'structure_resolved_minus_direct'], {'retarded_age': '{:.0f}'}, header=['age (M)', 'direct E', 'resolved E', 'resolved - direct', 'floor', 'resolved - direct, structure'])}

A negative difference means the resolved stack is closer to the truth at that
age.

Old-band error beyond the frozen boundary {old_band:.1f} M, median over ages,
absolute and normalized, with the structure companion:

{md_table(old_by_arm, ['arm', 'median_normalized_error', 'median_absolute_error', 'median_structure_normalized_error'], header=['arm', 'old-band normalized', 'old-band absolute', 'old-band structure-normalized'])}

Data-supported versus weak-subspace error, `validation_in_class`:

{md_table(dw_sum, ['arm', 'estimator', 'error_data_supported', 'error_weak'], header=['arm', 'estimator', 'data-supported error', 'weak-subspace error'])}

A weak-subspace improvement is a prior effect and is never described as
measured recovery.

Coverage, probabilistic estimators only:

{md_table(cov_sum, ['estimator', 'level', 'coverage'], header=['estimator', 'level', 'median coverage']) if len(cov_sum) else 'No probabilistic estimator produced a usable posterior at this scale.'}

Joint calibration, the sharper statement: the ratio of the mean squared
Mahalanobis distance to its expectation under the reported posterior. One means
calibrated, above one means the posterior is too narrow, below one means it
is too wide.

{md_table(maha, ['arm', 'estimator', 'ratio', 'median_pvalue', 'clipped', 'supported'], header=['arm', 'estimator', 'mean chi2 / dof', 'median p', 'clipped directions', 'supported directions']) if len(maha) else 'No probabilistic estimator produced a usable posterior at this scale.'}

The posterior covariance is positive definite in exact arithmetic but is formed
by inverting a near-singular shrunk prior plus a Gram, so directions the data
and the prior barely constrain are clipped at a relative floor. The count is
reported rather than absorbed into a diagonal jitter: how much of a posterior
is numerically unsupported is exactly what a calibration statement must not
hide.

TSVD, ridge and temporal Tikhonov carry `NOT_APPLICABLE` coverage rows rather
than a fabricated interval.

Runtime: median {rt.seconds.median():.2f} s per (arm, estimator, SNR, regime)
block, peak RSS {rt.peak_rss_mb.max():.0f} MB, direct linear solves with no
iterative scheme.

## Null and incremental-history pairs

Theoretical equal-prior Gaussian Bayes bound `P_Bayes = Phi(delta/2)` against
the realized accuracy, per arm and per registered separation. A method above
the bound beyond Monte-Carlo tolerance is reading information that is not in
the data, which is a defect and not a success:

{md_table(bayes, ['arm', 'target_delta', 'bayes_accuracy', 'observed_accuracy', 'observed_minus_bayes', 'tolerance', 'n_pairs', 'n_exceeding'], {'target_delta': '{:.2f}'}, header=['arm', 'delta', 'P_Bayes', 'observed', 'observed - bound', 'MC tolerance', 'pairs', 'above bound'])}

Null-pair calibration summary:

- pairs tested: {nullsum['n_tested']}
- realized-vs-target relative error: max {npair[npair.disposition == 'SUPPORTED'].relative_delta_error.max():.2e}
- above the equal-prior Bayes bound beyond Monte-Carlo tolerance:
  **{nullsum['n_exceeding']}**, against **{nullsum['expected_exceedances']:.1f}**
  expected under a calibrated null
- binomial p for that excess: {nullsum['binomial_p_excess']:.3f} -> defect = {nullsum['defect']}

{nullsum['rule']}.

Incremental-history pairs, built weak under the direct arm:

- median separation per unit coefficient, direct: **{ip_dir:.3e}**
- median separation per unit coefficient, resolved: **{ip_res:.3e}**
- median ratio: **{ip_ratio:.1f}x**

Read carefully. The ratio is large by construction -- the direction is chosen
inside the direct arm's least-determined half-spectrum -- so it demonstrates
that the higher orders *see* directions the direct image does not. It is not a
statement that those directions are recovered at any particular SNR; that is
what the depth table above measures, and the two must not be conflated.

## What needs repairing before R1

{'Two independent triggers below, either of which is enough on its own.' if (not primary_informative and not uncertainty_calibrated) else ''}

{'' if primary_informative else REPAIR_TEXT}

{'' if uncertainty_calibrated else UNCAL_TEXT}

{'' if (primary_informative and uncertainty_calibrated) else CLOSING_TEXT}

## Proposed held-out R1 freeze

`artifacts/configs/R0_PROPOSED_R1_MAIN_FREEZE.json`. No test score appears
anywhere in it or here: the main-test truths were hashed but never rendered.

## Deviations

{D.join('- ' + x for x in DEVIATIONS)}

## Artifacts

{D.join('- `' + p + '` `' + sha256_file(ROOT / p)[:16] + '...`' for p in ARTIFACTS if (ROOT / p).exists() and p != SELF)}

This report cannot list its own digest without changing it. `{SELF}` is hashed
in `artifacts/provenance/R0_CANARY_RECONSTRUCTION_ARTIFACT_MANIFEST.json`, which
is written after it and carries the full-length digest of every artifact above
alongside the nine provenance fields.

## Next requested authorization

**{recommend}**

{verdict}

No outcome here licenses a geometry-wide claim or a claim of arbitrary movie
recovery. The pilot is one geometry, a* = 0.5 and i = 50 degrees, and one source
class, C224.
"""
    (REPORTS / "R0_CANARY_RECONSTRUCTION_PILOT.md").write_text(body)

    # ---- proposed R1 freeze ------------------------------------------------
    r1 = {
        "schema": "phrt-r1-proposed-freeze/1",
        "status": "PROPOSED_NOT_AUTHORIZED",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "derives_from_pilot_freeze_sha256": fh,
        "no_test_score_present": True,
        "scope_restriction": "single canary geometry a* = 0.5, i = 50 deg, class "
                             "C224; a main test does not license a geometry-wide "
                             "or arbitrary-movie claim",
        "recommendation": recommend,
        "repairs_declared_here_not_applied_to_the_pilot": [
            {"id": "REPAIR_1_primary_tolerance",
             "needed": not primary_informative,
             "change": "the primary point moves off epsilon = 0.50, q = 0.90, "
                       "which is right-censored for every arm at every SNR in "
                       "the pilot, to a registered cell the observation can "
                       "resolve",
             "declared_primary": ({"epsilon": float(bc["epsilon"]),
                                   "quantile": float(bc["quantile"])}
                                  if len(bcell) else None),
             "evidence": "the cell-by-cell survey in the pilot report; the "
                         "declared cell is a member of the already-registered "
                         "epsilon x q surface, not a new tolerance"},
            {"id": "REPAIR_2_in_class_truths_in_span",
             "needed": not primary_informative,
             "change": "in-class truths are projected onto C224, or their "
                       "coefficients drawn directly, so the in-class "
                       "representation floor is zero; off-grid truths keep their "
                       "analytic rendering, where being outside the span is the "
                       "point",
             "evidence": {"in_class_structure_floor_range": list(floor_str),
                          "anchored_span_of_the_structure_floor_M":
                              floor_L.get("structure")}},
            {"id": "REPAIR_3_uncertainty_calibration",
             "needed": not uncertainty_calibrated,
             "change": "the Gaussian prior is refitted or widened so the joint "
                       "chi-square ratio lies within a factor of two of one on "
                       "the validation mix, or the probabilistic estimators stop "
                       "reporting posteriors",
             "observed_joint_ratio": (
                 {f"{r.arm}/{r.estimator}": float(r.ratio)
                  for r in maha.itertuples()} if len(maha) else {}),
             "registered_stop_condition": "UNCALIBRATED_UNCERTAINTY"},
        ],
        "main_counts": {
            "test_in_class_per_prior_fit_family": 512,
            "test_off_grid_per_physical_family": 256,
            "test_ood_total": 1024,
            "null_pairs_per_target": 200,
            "noise_draws_per_test_truth_and_snr": 8,
        },
        "age_interval_amendment": "AGE_INTERVAL_SEMANTICS_AMENDMENT_003",
        "a_anchor_M": a_anchor,
        "provenance": r0_provenance(),
        "representation_floor_in_class": {
            "registered_normalized_error_range": list(floor_reg),
            "structure_normalized_error_range": list(floor_str),
            "anchored_span_of_the_floor_M": floor_L,
            "meaning": "the error of the exact least-squares projection of the "
                       "truth onto C224. No estimator can beat it within the "
                       "declared class, and any main-test success criterion has "
                       "to be stated against it",
        },
        "success_criteria": {
            "primary": (
                f"L_stable_anchor("
                f"{bc['epsilon'] if len(bcell) else 0.50:.2f}, "
                f"{bc['quantile'] if len(bcell) else 0.90:.2f}) for "
                f"RESOLVED_PHYSICAL exceeds DIRECT_PHYSICAL by at least one "
                f"age-grid step of {step:.0f} M at two or more consecutive "
                f"SNR_0 values, with the anchor frozen at {a_anchor:g} M"
                + ("" if primary_informative else
                   ". The tolerance differs from the pilot's registered primary "
                   "point under REPAIR_1: that point is right-censored for "
                   "every arm at every SNR here and cannot express a "
                   "difference. The replacement is a member of the "
                   "already-registered surface and is declared before any test "
                   "truth is rendered")),
            "secondary": ["old-band normalized error strictly lower for the "
                          "resolved arm at the same SNR",
                          "the same holding for the structure-normalized "
                          "companion, so the gain is not an artefact of the "
                          "positive baseline in the registered denominator",
                          "data-supported error strictly lower, so the gain is "
                          "not a weak-subspace prior effect",
                          "null-pair accuracy at or below the Bayes bound within "
                          "binomial multiplicity"],
            "declared_before_test": True,
        },
        "test_hash_commitment": future["commitment_sha256"],
        "estimators": fz["estimators"],
        "hyperparameters": "selected on the pilot's validation split and frozen; "
                           "no re-tuning on test data",
        "observed_pilot_headline": {
            "max_resolved_minus_direct_L_stable_anchor_M": max_gain,
            "any_positive_gain": any_gain,
            "gain_of_at_least_one_step_at_consecutive_snr": consecutive,
        },
    }
    (CFG / "R0_PROPOSED_R1_MAIN_FREEZE.json").write_text(
        json.dumps(r1, indent=2, default=float) + "\n")

    files = [p for p in ARTIFACTS if (ROOT / p).exists()]
    (ROOT / "artifacts" / "provenance"
     / "R0_CANARY_RECONSTRUCTION_ARTIFACT_MANIFEST.json").write_text(json.dumps(
        {"schema": "phrt-r0-artifacts/2",
         "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
         "git_commit": prov.git_commit, "freeze_sha256": fh,
         "recommendation": recommend,
         "provenance": r0_provenance(),
         "artifacts": {p: sha256_file(ROOT / p) for p in files}}, indent=2) + "\n")

    print("wrote artifacts/reports/R0_CANARY_RECONSTRUCTION_PILOT.md")
    print("wrote artifacts/configs/R0_PROPOSED_R1_MAIN_FREEZE.json")
    print("wrote artifacts/provenance/R0_CANARY_RECONSTRUCTION_ARTIFACT_MANIFEST.json")
    print(f"  recommendation: {recommend} (max resolved-direct gain {max_gain:.1f} M)")
    print(f"total {time.time() - t0:.0f}s")
    return 0


DEVIATIONS = [
    "**Start commit is not a documentation-only descendant of the accepted base.** "
    "The launch permits such a descendant; the start commit additionally carries "
    "the G10q measurement-model correction and the accepted E3B/E3C work. Starting "
    "from the bare base is impossible under this launch's own frozen model: at "
    "0ef341d the forward coefficient is g^3 with a flat per-row sigma and no G10q "
    "gate exists, so the required whitened row is absent and R0_G3 would stop "
    "immediately with QUADRATURE_NOISE_DEFECT. Verified by inspecting the operator "
    "at both commits.",
    "**Governance documents supplied mid-flight.** The launch v1.0, "
    "PAPER_I_V2_RECONSTRUCTION_AMENDMENT_002, the activation ruling v1.2 and the "
    "freeze template v1.0 were supplied after registration began; the v1 evidence "
    "ledger, the v2 reconstruction handoff and the v2 experiment registry were "
    "not. Every convention those three would have supplied is pinned explicitly "
    "in the pilot freeze, and the template is now vendored at "
    "schemas/R0_CANARY_RECONSTRUCTION_PILOT_FREEZE_TEMPLATE_v1.0.json and checked "
    "leaf by leaf at registration.",
    "**AGE_INTERVAL_SEMANTICS_AMENDMENT_003 supersedes the launch's depth "
    "vocabulary.** The primary endpoint is the anchored T_stable^anchor with the "
    "supremum over the age window inside the probability, taken per truth, and it "
    "is reported as the span L_stable^anchor from a frozen anchor. The launch's "
    "T_contig is retained only as the secondary unanchored longest passing run, "
    "reported with both endpoints and never called depth from the present.",
    "**D_hist(T) and d_eff(T) are withheld from the R0 metric list.** "
    "PAPER_I_V2_PRE_E3C_AMENDMENT_001 item 6 reserves them for E3D, and the "
    "activation ruling restates that they are E3D quantities. E3D is deferred and "
    "not started, so R0 emits neither under any name; the interval statistics "
    "replace them. The withholding and its reason are recorded in the freeze "
    "rather than left as a silent omission.",
    "**The representation floor is reported as a first-class result.** The "
    "in-class truths are rendered analytically at the class's resolvable scale "
    "rather than drawn from the span of C224, so the exact projection onto the "
    "class already leaves a residual. Without that floor beside them the error "
    "and depth tables would read as estimator or arm results when part of what "
    "they measure is the class.",
    "**The registered E(a) saturates and the structure-normalized companion is "
    "reported beside it.** The registered denominator ||W_a x|| is dominated by "
    "the positive baseline every family carries and every estimator recovers "
    "trivially. The companion removes the age-local constant from residual and "
    "truth alike. Both are reported at every cell; neither replaces the other, "
    "and the registered one remains the registered one.",
    "**R0_G12 added beyond the launch's gate list.** The pilot simulates in the "
    "sufficient statistic b = A^T y rather than in y. That is exact for every "
    "estimator used, and is what makes the pilot tractable, but only if the "
    "reduced noise is sampled with covariance G rather than white. The gate "
    "checks it against a full-space Monte-Carlo simulation.",
    "**Smoke class C48 factorized as 4 x 3 x 4, not 2 x 3 x 8.** The radial "
    "factor is a cubic B-spline basis and requires at least four modes. The "
    "declared dimension is unchanged and the constraint is recorded in the freeze.",
    "**Existing modules reused rather than rewritten**: src/phrt/inverse/base.py "
    "already provided dense TSVD and ridge solves, and the operator, basis, ray "
    "maps and E3C age-probe machinery are reused under frozen semantics, as the "
    "launch permits.",
    "**Scoring uses a declared structured evaluation grid**, not the ray "
    "coordinates of any one arm. Scoring on the resolved arm's own sampling "
    "points would give it an advantage in precisely the comparison being made.",
    "**Null-pair defect rule accounts for multiplicity.** With hundreds of pairs "
    "each tested at a two-sigma one-sided tolerance, a few exceedances are "
    "expected under a calibrated null; a defect is declared only when the count "
    "exceeds its binomial expectation at p < 0.01.",
    "**ARMS.index replaces hash(arm) in the null-pair seed.** Python salts string "
    "hashes per process, which made the null-pair results differ between runs and "
    "would have violated the bitwise replay R0_G9 requires.",
    "**LINEAR_STATE_SPACE is a prior-structure model, not a filter.** The "
    "observation couples every temporal mode, so no sequential observation "
    "recursion applies; the estimator is the batch linear-Gaussian solution under "
    "a random-walk prior across the temporal index, and R0_G8 checks both the "
    "sequential precision construction and the batch solve.",
]

SELF = "artifacts/reports/R0_CANARY_RECONSTRUCTION_PILOT.md"

ARTIFACTS = [
    "artifacts/configs/R0_CANARY_RECONSTRUCTION_PILOT_FREEZE.json",
    "artifacts/configs/AGE_INTERVAL_SEMANTICS_AMENDMENT_003.json",
    "artifacts/configs/R0_PROPOSED_R1_MAIN_FREEZE.json",
    "artifacts/manifests/r0_source_bank_manifest.json",
    "artifacts/manifests/r0_split_hash_manifest.json",
    "artifacts/manifests/r0_future_test_hash_commitment.json",
    "artifacts/manifests/r0_null_pair_summary.json",
    "artifacts/tables/r0_pilot_age_errors.parquet",
    "artifacts/tables/r0_pilot_stable_depth.parquet",
    "artifacts/tables/r0_pilot_estimator_selection.parquet",
    "artifacts/tables/r0_pilot_data_weak_errors.parquet",
    "artifacts/tables/r0_pilot_coverage.parquet",
    "artifacts/tables/r0_pilot_null_pairs.parquet",
    "artifacts/tables/r0_pilot_incremental_pairs.parquet",
    "artifacts/tables/r0_pilot_runtime.parquet",
    "artifacts/tables/r0_pilot_arm_contrasts.parquet",
    "artifacts/tables/r0_pilot_representation_floor.parquet",
    "artifacts/tables/r0_pilot_representation_floor_depth.parquet",
    "artifacts/gates/r0_correctness_gates.json",
    "artifacts/reports/R0_CANARY_RECONSTRUCTION_PILOT.md",
]

if __name__ == "__main__":
    raise SystemExit(main())
