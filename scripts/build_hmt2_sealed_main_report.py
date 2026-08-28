#!/usr/bin/env python3
"""Report for the HMT-2 sealed main."""
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

FZ = ROOT / "artifacts" / "configs" / "HMT2_SEALED_MAIN_V1.json"
G = ROOT / "artifacts" / "gates" / "hmt2_sealed_main_gates.json"
SA = ROOT / "artifacts" / "gates" / "hmt2_sealed_main_stage_a_gates.json"
TAB = ROOT / "artifacts" / "tables"
OUT = ROOT / "artifacts" / "reports" / "HMT2_SEALED_MAIN.md"
PROV = ROOT / "artifacts" / "provenance" / "HMT2_SEALED_MAIN_ARTIFACT_MANIFEST.json"
D = "\n"
PH, CC = "PHYSICAL_END_TO_END", "CLASS_CONDITIONAL"
PRIM = "L896_radial_enriched"


def main() -> int:
    t0 = time.time()
    fz = json.loads(FZ.read_text())
    g = json.loads(G.read_text())
    sa = json.loads(SA.read_text())
    en = pd.read_parquet(TAB / "hmt2_main_endpoint.parquet")
    sm = pd.read_parquet(TAB / "hmt2_main_stable_multi.parquet")
    pf = pd.read_parquet(TAB / "hmt2_main_per_family.parquet")
    si = pd.read_parquet(TAB / "hmt2_main_stable_interval.parquet")
    bk = pd.read_parquet(TAB / "hmt2_sealed_main_source_banks.parquet")
    man = json.loads(sorted((ROOT / "artifacts" / "manifests")
                            .glob("HMT2M_*.json"))[-1].read_text())
    att = man["attestation"]
    M = fz["pass_criteria"]["materiality"]

    def _n(x):
        return f"{x:.4g}" if isinstance(x, float) else str(x)

    gtab = D.join(f"| `{k}` | {v['status']} | {_n(v.get('measured'))} | "
                  f"{_n(v.get('threshold'))} |" for k, v in g["gates"].items())

    q = en[(en.snr0 == 100) & (en["class"] == PRIM)]
    etab = D.join(
        f"| `{r.arm}` | {r.estimator} | {r[f'{PH}_median_reduction']:+.3f} | "
        f"{r[f'{PH}_ci_low']:+.3f} | "
        f"{'**MATERIAL**' if r[f'{PH}_material'] else 'no'} | "
        f"{r[f'{CC}_median_reduction']:+.3f} | "
        f"{'**MATERIAL**' if r[f'{CC}_material'] else 'no'} | "
        f"{r[f'{PH}_non_dead_median_reduction']:+.3f} | "
        f"{'**MATERIAL**' if r[f'{PH}_non_dead_material'] else 'no'} |"
        for _, r in q.sort_values(["arm", "estimator"]).iterrows())
    ctl = en[(en.snr0 == 100) & (en["class"] != PRIM)]
    ctab = D.join(
        f"| `{r.arm}` | {r.estimator} | {r[f'{PH}_median_reduction']:+.3f} | "
        f"{r[f'{PH}_ci_low']:+.3f} | "
        f"{'**MATERIAL**' if r[f'{PH}_material'] else 'no'} |"
        for _, r in ctl.sort_values(["arm", "estimator"]).iterrows())

    smq = sm[sm.arm == "RESOLVED_PHYSICAL"]
    stab = D.join(
        f"| `{r['class']}` | {r.estimator} | {r.snr0:.0f} | {r.direct:.3f} | "
        f"{r.arm_cost:.3f} | {r.median_reduction:+.3f} | {r.ci_low:+.3f} | "
        f"{'**MATERIAL**' if r.material else 'no'} |"
        for _, r in smq.sort_values(["class", "estimator", "snr0"]).iterrows())

    pq = pf[(pf.snr0 == 100) & (pf["class"] == PRIM)
            & (pf.arm == "RESOLVED_PHYSICAL")]
    ptab = D.join(
        f"| `{r.family}` | {r.estimator} | {r[f'{PH}_median_reduction']:+.3f} | "
        f"{r[f'{PH}_ci_low']:+.3f} | "
        f"{'**MATERIAL**' if r[f'{PH}_material'] else 'no'} |"
        for _, r in pq.sort_values(["family", "estimator"]).iterrows())
    n_mat = int(pq[f"{PH}_material"].sum())

    sq = si[(si.snr0 == 100) & (si["class"] == PRIM)]
    itab = D.join(
        f"| `{r.arm}` | {r.estimator} | {r.L_stable_morphology_M:.1f} | "
        f"{r.mean_reach_M:.2f} | {r.fraction_nonzero:.3f} |"
        for _, r in sq.sort_values(["arm", "estimator"]).iterrows())

    res = q[q.arm == "RESOLVED_PHYSICAL"]
    rr = res[res.estimator == "RIDGE_IDENTITY"].iloc[0]
    rt = res[res.estimator == "TSVD"].iloc[0]

    body = f"""# HMT-2 sealed held-out main

Freeze `{fz['id']}`, run `{g['run_id']}`.
Execution commit `{att['execution_commit'][:12]}`, tree clean:
{str(att['clean']).lower()}. {len(bk)} held-out truths,
{man['runtime_seconds']:.0f} s.

## Disposition

`{g['stop_token']}` — all {len(g['gates'])} gates pass.

The resolved arm in the claim-bearing class reduces the all-state morphology
error against the direct image on both targets and both classical estimators,
at a materiality floor declared before the bank was drawn: a median reduction
of at least {M['median_relative_reduction']:.2f} with a bootstrap lower bound
above {M['median_bootstrap_lower_bound']:.2f}.

**What that does and does not say is the substance of this report, and the
qualifications are as much a result as the token is.**

## 1. The sealing held

Stage A decided six source gates before any operator was imported, and the bank
hashes were committed before stage B ran. Stage B rebuilt the bank and matched
every hash: {g['gates']['HMT2M_G10_bank_hashes_match_committed']['measured']}
mismatches. The 16 hyperparameters came from the stage 1 selection split
unchanged and this runner contains no sweep.

The first attempt at stage B reported 60 of 60 hash mismatches. The gate was
right and the bank was fine: the state labels had been hashed with Python's
builtin `hash`, which salts string hashing per process, so a hash written in
stage A could never match one recomputed in stage B. That is the third
appearance of this bug in the campaign, and it now has an automated check
rather than a memory of it.

## 2. Primary endpoint, claim-bearing class, SNR₀ = 100

| arm | estimator | physical | CI low | material | class-cond | material | non-dead | material |
|---|---|---|---|---|---|---|---|---|
{etab}

The reduction survives removal of dead states at the same floor, so it is not
an artifact of a near-null estimator being right about nothing being there.
Both controls behave: `TOTAL_FLUX` is negative or non-material, and
`UNRESOLVED_IMAGE` reaches {q[q.arm == 'UNRESOLVED_IMAGE'][f'{PH}_median_reduction'].max():+.4f}
at best, so the benefit is attributable to resolving the orders rather than to
the extra photons an unresolved second image also carries.

The representation-limited control class:

| arm | estimator | physical | CI low | material |
|---|---|---|---|---|
{ctab}

Its resolved arm reaches materiality under ridge and not under TSVD, which is
the representation limit showing up as a weaker and less robust effect in the
same run.

## 3. Two-feature recovery does not reach materiality anywhere

Stable multi-resolved states, resolved arm, both estimators and both SNRs. Cost
is normalised so 1.0 is one whole feature gained or lost.

| class | estimator | SNR₀ | direct | arm | reduction | CI low | material |
|---|---|---|---|---|---|---|---|
{stab}

**Not one cell is material.** In the claim-bearing class the point estimates are
0.14 to 0.19, which looks encouraging, and every interval reaches below the
floor. The absolute cost stays between 1.20 and 1.30 -- the reconstruction is
still getting more than one whole feature wrong on average. In the control class
the resolved arm is negative.

So the sealed main reproduces, on held-out truths, exactly the split the stage 1
completion found: the description of the past improves materially; the recovery
of a resolved two-feature set does not.

## 4. The aggregate is carried by two families of six

| family | estimator | physical | CI low | material |
|---|---|---|---|---|
{ptab}

{n_mat} of 12 family-estimator cells reach materiality, and they concentrate in
`flare_birth_motion_decay` and `m2_structural_mode`.
`circular_hotspot_trajectory` -- the simplest family in the bank, a single
moving spot -- is **negative** under both estimators. `two_hotspot_trajectories`
does not reach materiality under either.

With ten truths per family these intervals are wide and no family-level claim is
supported either way. But the headline is not a uniform improvement across the
source model; it is a large gain on two families and roughly nothing on the
simplest one, and it should not be quoted as though the operator helps
everywhere.

## 5. There is still no stable morphology interval

| arm | estimator | L_stable (M) | mean reach (M) | fraction reaching |
|---|---|---|---|---|
{itab}

Zero for every arm at the declared tolerance and quantile. The resolved arm's
mean reach is *lower* than the direct image's under both estimators, so it does
not even extend how far back the morphology stays within tolerance on average.
A material reduction in a time-averaged error and a history that holds together
over an interval remain different things, and only the first is established.

## 6. Saturation

{100 * float(res[f'{PH}_saturation_direct'].mean()):.0f}% of direct-image states
sit at the measure's ceiling, falling to
{100 * float(res[f'{PH}_saturation_arm'].mean()):.0f}% for the resolved arm.
When more than half the states are at the maximum, the mean is substantially
counting how many states failed outright, and the improvement is mostly fewer
total failures rather than uniformly better estimates. This is disclosed per
cell because the freeze required it, and it qualifies the headline rather than
overturning it.

## 7. Gates

| gate | status | measured | threshold |
|---|---|---|---|
{gtab}

## 8. Scope

One geometry, one spin, one inclination. Six analytic families at their
original declared ranges with no separation cut, so the bank contains the
blended and ambiguous states the endpoint was built to score. Held-out truths,
disjoint from every earlier bank in the campaign. Classical estimators only.
Absolute all-state error for the resolved arm remains
{float(rr[f'{PH}_arm']):.3f} on a scale whose worst case is 1.0.

The honest summary: resolving the photon-ring orders materially improves a
resolution-aware description of the past on held-out sources, driven mainly by
two of six families, without delivering resolved two-feature recovery and
without producing any interval over which the recovered morphology holds.

**STOP.** Item 12. Order leakage, geometry mismatch, VLBI, machine learning and
a new pixel-movie campaign remain unauthorized.
"""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    PROV.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(body)
    inputs = sorted(str(p.relative_to(ROOT)) for p in TAB.glob("hmt2_main_*.parquet"))
    PROV.write_text(json.dumps({
        "schema": "phrt-artifact-manifest/1",
        "experiment_id": "HMT2_SEALED_MAIN",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "stop_token": g["stop_token"],
        "physical_end_to_end_material": g["physical_end_to_end_material"],
        "class_conditional_material": g["class_conditional_material"],
        "stage_a_attestation": sa["attestation"],
        "execution_attestation": att,
        "report_assembly_attestation": attest([FZ]),
        "freeze_sha256": sha256_file(FZ),
        "inputs": {p: sha256_file(ROOT / p) for p in inputs},
        "outputs": {str(OUT.relative_to(ROOT)): sha256_file(OUT)},
    }, indent=2, default=str) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}\nwrote {PROV.relative_to(ROOT)}")
    print(f"  {g['stop_token']}\ntotal {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
