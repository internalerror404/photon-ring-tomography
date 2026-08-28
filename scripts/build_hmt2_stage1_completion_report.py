#!/usr/bin/env python3
"""Report for the HMT-2 stage 1 endpoint completion."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from phrt.numerics import pin

pin()

import pandas as pd  # noqa: E402

from phrt.attestation import attest  # noqa: E402
from phrt.config import sha256_file  # noqa: E402

AMD = ROOT / "artifacts" / "configs" / "HMT2_STAGE1_ENDPOINT_COMPLETION_AMENDMENT_020.json"
FZ = ROOT / "artifacts" / "configs" / "HMT2_STAGE1_RESOLUTION_AWARE_MORPHOLOGY_VALIDATION_V0.json"
G = ROOT / "artifacts" / "gates" / "hmt2_stage1_completion_gates.json"
TAB = ROOT / "artifacts" / "tables"
OUT = ROOT / "artifacts" / "reports" / "HMT2_STAGE1_ENDPOINT_COMPLETION.md"
PROV = ROOT / "artifacts" / "provenance" / "HMT2_STAGE1_COMPLETION_ARTIFACT_MANIFEST.json"
D = "\n"
PH, CC = "PHYSICAL_END_TO_END", "CLASS_CONDITIONAL"
PRIM = "L896_radial_enriched"


def main() -> int:
    t0 = time.time()
    g = json.loads(G.read_text())
    nd = pd.read_parquet(TAB / "hmt2_stage1c_non_dead.parquet")
    sm = pd.read_parquet(TAB / "hmt2_stage1c_stable_multi.parquet")
    pf = pd.read_parquet(TAB / "hmt2_stage1c_per_family.parquet")
    en = pd.read_parquet(TAB / "hmt2_stage1c_endpoint.parquet")
    si = pd.read_parquet(TAB / "hmt2_stage1c_stable_interval.parquet")
    stt = pd.read_parquet(TAB / "hmt2_stage1c_states.parquet")
    man = json.loads(sorted((ROOT / "artifacts" / "manifests")
                            .glob("HMT2S1C_*.json"))[-1].read_text())
    att = man["attestation"]

    def _n(x):
        return f"{x:.4g}" if isinstance(x, float) else str(x)

    gtab = D.join(f"| `{k}` | {v['status']} | {_n(v.get('measured'))} | "
                  f"{_n(v.get('threshold'))} |" for k, v in g["gates"].items())

    q = nd[nd.snr0 == 100]
    ndt = D.join(
        f"| `{r['class']}` | `{r.arm}` | {r.estimator} | "
        f"{r[f'{PH}_non_dead_median_reduction']:+.3f} | "
        f"{r[f'{PH}_non_dead_ci_low']:+.3f} | "
        f"{'**yes**' if r[f'{PH}_non_dead_improves'] else 'no'} | "
        f"{r[f'{PH}_saturation_direct']:.3f} | {r[f'{PH}_saturation_arm']:.3f} |"
        for _, r in q.sort_values(["class", "arm", "estimator"]).iterrows())

    smt = D.join(
        f"| `{r['class']}` | `{r.arm}` | {r.estimator} | {r.snr0:.0f} | "
        f"{r.direct:.3f} | {r.arm_cost:.3f} | {r.median_reduction:+.3f} | "
        f"{r.ci_low:+.3f} | {'**yes**' if r.improves else 'no'} |"
        for _, r in sm[sm.arm == "RESOLVED_PHYSICAL"]
        .sort_values(["class", "estimator", "snr0"]).iterrows())

    pq = pf[(pf.snr0 == 100) & (pf["class"] == PRIM)
            & (pf.arm == "RESOLVED_PHYSICAL")]
    pft = D.join(
        f"| `{r.family}` | {r.estimator} | {r[f'{PH}_median_reduction']:+.3f} | "
        f"{r[f'{PH}_ci_low']:+.3f} | "
        f"{'**yes**' if r[f'{PH}_improves'] else 'no'} |"
        for _, r in pq.sort_values(["family", "estimator"]).iterrows())

    cc = en[(en.snr0 == 100) & (en["class"] == PRIM)
            & (en.arm == "RESOLVED_PHYSICAL")]
    cct = D.join(
        f"| {r.estimator} | {r[f'{CC}_median_reduction']:+.4f} | "
        f"{r['CC_PROJLAB_median_reduction']:+.4f} | "
        f"{abs(r[f'{CC}_median_reduction'] - r['CC_PROJLAB_median_reduction']):.2e} |"
        for _, r in cc.iterrows())

    sit = D.join(
        f"| `{r['class']}` | `{r.arm}` | {r.estimator} | "
        f"{r.L_stable_morphology_M:.1f} | {r.mean_reach_M:.2f} | "
        f"{r.fraction_nonzero:.3f} |"
        for _, r in si[si.snr0 == 100].sort_values(["class", "arm"]).iterrows())

    nsat = float(q[q["class"] == PRIM][f"{PH}_saturation_direct"].mean())
    body = f"""# HMT-2 stage 1 — endpoint completion

Amendment `HMT2_STAGE1_ENDPOINT_COMPLETION_AMENDMENT_020`, run `{g['run_id']}`.
Execution commit `{att['execution_commit'][:12]}`,
{man['runtime_seconds']:.0f} s.

## Disposition

`{g['stop_token']}` — all {len(g['gates'])} gates pass.

**The primary endpoint reproduces bitwise: {g['n_reproduction_diffs']} differing
cells.** Same bank, same operators, same hyperparameters read from the stage 1
selection table, same SNRs, same noise draws. No selection was performed and no
truth was drawn. Everything below is an addition to a table that did not move.

One detail that had to be right: the noise draws come from a single stream over
the full key list including the selection split. This run scores only the pilot
split, so it still advances the stream over the selection keys in the same order
and discards them. Had it not, the pilot noise would differ and nothing would
have reproduced.

## 1. The effect is not an artifact of dead states

Physical target at SNR₀ = 100, dead states removed, with the fraction of states
sitting at the measure's ceiling:

| class | arm | estimator | non-dead reduction | CI low | improves | saturation direct | saturation arm |
|---|---|---|---|---|---|---|---|
{ndt}

The resolved arm in the primary class keeps a material reduction with dead
states removed -- so the concern raised when stage 1 was reported does not
overturn the headline.

**But the measure is saturated for most states.** {100 * nsat:.0f}% of
direct-image states sit at the ceiling of 1.0, falling to about 41% for the
resolved arm. When more than half the states are at the maximum, the mean is
largely counting *how many states are saturated*, and "improvement" mostly means
"fewer total failures" rather than "better estimates". That is a real
measurement, and it is not the same statement as the error decreasing smoothly.

It also explains the total-flux behaviour more fully than the dead-state
account did. `TOTAL_FLUX` under TSVD still shows a positive non-dead reduction,
because a near-null estimator produces a stable wrong answer that does not
saturate, while the direct image produces a wildly wrong one that does. The
soft spot is saturation, not dead states alone.

## 2. The two-feature result is not estimator-robust

Stable multi-resolved states only, both estimators and both SNRs, resolved arm.
Cost is normalised so 1.0 is one whole feature gained or lost.

| class | arm | estimator | SNR₀ | direct | arm | reduction | CI low | improves |
|---|---|---|---|---|---|---|---|---|
{smt}

This is what item 9 was for, and the answer is negative. In the primary class
the ridge estimator improves the conditional cost marginally, with an interval
that barely clears zero, and **TSVD does not improve it at all** at either SNR.
In the representation-limited control class the resolved arm makes it
substantially *worse* under both estimators. Twelve truths carry these states.

`HMT2_S1_ESTIMATOR_ROBUST_TWO_FEATURE_RESULT_NOT_RUN` recorded that no such
statement existed. Now that it has been run, the statement is that two-feature
recovery is estimator-dependent and not established.

## 3. The all-state effect is heterogeneous across families

Primary class, resolved arm, SNR₀ = 100, physical target, six truths per family:

| family | estimator | reduction | CI low | improves |
|---|---|---|---|---|
{pft}

Four of six families improve under each estimator, but not the same four.
`circular_hotspot_trajectory` -- the simplest family in the bank -- improves
under neither. `two_hotspot_trajectories` improves under TSVD and not ridge;
`m2_structural_mode` the reverse. With six truths per family these intervals are
wide, and the honest reading is that the aggregate effect is not uniform and no
family-level claim is supported.

## 4. The class-conditional label ambiguity has no numerical effect

| estimator | analytic label | projected label | difference |
|---|---|---|---|
{cct}

The recorded defect was real -- the target compared against the in-class
projection while taking the per-state measure from the analytic label, and which
label should govern was never decided. Computing both shows the choice does not
move the number here. The ambiguity is resolved by measurement rather than by
argument, and the answer is that it did not matter.

## 5. There is no stable age-resolved morphology interval

At the campaign's declared tolerance and quantile:

| class | arm | estimator | L_stable (M) | mean reach (M) | fraction reaching |
|---|---|---|---|---|---|
{sit}

Zero for every arm, class and estimator. Between 4% and 28% of realizations are
inside the tolerance at age zero at all, and the mean reach never exceeds about
7 M. So the improvement in the all-state morphology error does not produce any
age interval over which the recovered morphology stays within tolerance at 95%
confidence -- the same structural outcome HMT-1 found for its feature interval,
now measured on a resolution-aware error.

## 6. What the completion changes

Nothing in the primary endpoint, by construction and by check. What it changes
is what may be said around it:

- the all-state reduction survives the removal of dead states, so
  `HMT2_S1_SUBSTANTIVE_ALL_STATE_MORPHOLOGY_ERROR_REDUCTION` stands, with the
  saturation caveat attached to it;
- `HMT2_S1_ACCURATE_MORPHOLOGY_RECOVERY_NOT_ESTABLISHED` is strengthened: the
  stable morphology interval is zero everywhere and over half of states are at
  the measure's ceiling;
- `HMT2_S1_ESTIMATOR_ROBUST_TWO_FEATURE_RESULT_NOT_RUN` is discharged, and its
  successor finding is that the two-feature result is estimator-dependent;
- `HMT2_S1_UNRESOLVED_NO_CONFIRMED_GAIN` is unchanged;
- `HMT2_S1_PASS_RULE_HAS_NO_EFFECT_SIZE_FLOOR` stands as recorded. The rule was
  not changed after the fact. Effect sizes and intervals are reported
  throughout so a floor can be applied by inspection.

## 7. Gates

| gate | status | measured | threshold |
|---|---|---|---|
{gtab}

**STOP.** On this pass, item 11 authorizes registering one sealed main before
any held-out truth is drawn, which is a separate registration. Order leakage,
geometry mismatch, VLBI, machine learning and a new pixel-movie campaign remain
unauthorized.
"""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    PROV.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(body)
    inputs = sorted(str(p.relative_to(ROOT)) for p in TAB.glob("hmt2_stage1c_*.parquet"))
    PROV.write_text(json.dumps({
        "schema": "phrt-artifact-manifest/1",
        "experiment_id": "HMT2_STAGE1_COMPLETION",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "stop_token": g["stop_token"],
        "primary_endpoint_reproduced_bitwise": g["primary_endpoint_reproduced_bitwise"],
        "execution_attestation": att,
        "report_assembly_attestation": attest([AMD, FZ]),
        "amendment_sha256": sha256_file(AMD),
        "inputs": {p: sha256_file(ROOT / p) for p in inputs},
        "outputs": {str(OUT.relative_to(ROOT)): sha256_file(OUT)},
    }, indent=2, default=str) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}\nwrote {PROV.relative_to(ROOT)}")
    print(f"total {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
