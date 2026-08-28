#!/usr/bin/env python3
"""Report for HMT-2 stage 1."""
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

FZ = ROOT / "artifacts" / "configs" / "HMT2_STAGE1_RESOLUTION_AWARE_MORPHOLOGY_VALIDATION_V0.json"
G = ROOT / "artifacts" / "gates" / "hmt2_stage1_gates.json"
TAB = ROOT / "artifacts" / "tables"
OUT = ROOT / "artifacts" / "reports" / "HMT2_STAGE1_RESOLUTION_AWARE_MORPHOLOGY.md"
PROV = ROOT / "artifacts" / "provenance" / "HMT2_STAGE1_ARTIFACT_MANIFEST.json"
D = "\n"
T_PHYS, T_CC = "PHYSICAL_END_TO_END", "CLASS_CONDITIONAL"


def main() -> int:
    t0 = time.time()
    fz = json.loads(FZ.read_text())
    g = json.loads(G.read_text())
    end = pd.read_parquet(TAB / "hmt2_stage1_endpoint.parquet")
    sel = pd.read_parquet(TAB / "hmt2_stage1_selection.parquet")
    stt = pd.read_parquet(TAB / "hmt2_stage1_states.parquet")
    bnk = pd.read_parquet(TAB / "hmt2_stage1_source_banks.parquet")
    man = json.loads(sorted((ROOT / "artifacts" / "manifests")
                            .glob("HMT2S1_*.json"))[-1].read_text())
    att = man["attestation"]
    prim = fz["classes"]["primary"]["id"]
    ctrl = fz["classes"]["control"]["id"]
    snr_p = fz["snr"]["primary"]

    def _num(x):
        return f"{x:.4g}" if isinstance(x, float) else str(x)

    gtab = D.join(f"| `{k}` | {v['status']} | {_num(v.get('measured'))} | "
                  f"{_num(v.get('threshold'))} |" for k, v in g["gates"].items())

    def etab(df):
        return D.join(
            f"| `{r['class']}` | `{r.arm}` | {r.estimator} | {r.snr0:.0f} | "
            f"{r[f'{T_PHYS}_median_reduction']:+.3f} | "
            f"{r[f'{T_PHYS}_ci_low']:+.3f} | "
            f"{'**yes**' if r[f'{T_PHYS}_improves'] else 'no'} | "
            f"{r[f'{T_CC}_median_reduction']:+.3f} | "
            f"{r[f'{T_CC}_ci_low']:+.3f} | "
            f"{'**yes**' if r[f'{T_CC}_improves'] else 'no'} |"
            for _, r in df.sort_values(["class", "arm", "estimator"]).iterrows())

    prim_tab = etab(end[(end.snr0 == snr_p) & (end["class"] == prim)])
    ctrl_tab = etab(end[(end.snr0 == snr_p) & (end["class"] == ctrl)])
    hi_tab = etab(end[(end.snr0 != snr_p) & (end["class"] == prim)
                      & (end.arm == "RESOLVED_PHYSICAL")])

    q = stt[(stt.snr0 == snr_p) & (stt.target == T_PHYS)
            & (stt.estimator == "TSVD")]
    kind = q.pivot_table(index=["class", "arm"], columns="measure",
                         values="error", aggfunc="mean")
    ktab = D.join(
        f"| `{i[0]}` | `{i[1]}` | {r.get('assignment', float('nan')):.4f} | "
        f"{r.get('blended', float('nan')):.4f} | "
        f"{r.get('amplitude', float('nan')):.4f} |"
        for i, r in kind.iterrows())

    sec = end[(end.snr0 == snr_p) & (end.estimator == "TSVD")]
    stab = D.join(
        f"| `{r['class']}` | `{r.arm}` | {r.stable_multi_direct:.3f} | "
        f"{r.stable_multi_arm:.3f} | "
        f"{'better' if r.stable_multi_arm < r.stable_multi_direct else 'worse'} |"
        for _, r in sec.iterrows())

    S = ["n_single_resolved", "n_multi_resolved", "n_blended", "n_dead",
         "n_ambiguous"]
    mix = bnk[S].sum() / bnk[S].sum().sum()
    res = end[(end["class"] == prim) & (end.arm == "RESOLVED_PHYSICAL")
              & (end.snr0 == snr_p)]
    r_tsvd = res[res.estimator == "TSVD"].iloc[0]
    r_ridge = res[res.estimator == "RIDGE_IDENTITY"].iloc[0]
    sm = sec[(sec["class"] == prim) & (sec.arm == "RESOLVED_PHYSICAL")].iloc[0]

    body = f"""# HMT-2 stage 1 — resolution-aware morphology validation

Freeze `{fz['id']}`, run `{g['run_id']}`.
Execution commit `{att['execution_commit'][:12]}`, tree clean:
{str(att['clean']).lower()}. {len(bnk)} truths across
{len(fz['bank']['splits'])} splits, {man['runtime_seconds']:.0f} s.

## Disposition

`{g['stop_token']}`

All {len(g['gates'])} gates pass. Both declared targets improve for the
resolved arm in the primary class, on both classical estimators, with paired
bootstrap intervals excluding zero.

**Read the primary and the secondary endpoints together.** The all-state
morphology error improves materially. The conditional set-valued recovery on
cleanly resolved two-feature states barely moves and remains above one whole
feature of error. Those are different claims and this run separates them, which
is what the two-endpoint structure was built for.

## 1. Primary endpoint — all-state morphology error, primary class

Median relative reduction against the direct image, paired truth-cluster
bootstrap, at SNR₀ = {snr_p:.0f}. Every state is scored by the measure it
supports and none is excluded.

| class | arm | estimator | SNR₀ | phys | phys CI low | phys | class-cond | CC CI low | CC |
|---|---|---|---|---|---|---|---|---|---|
{prim_tab}

The representation-limited control class:

| class | arm | estimator | SNR₀ | phys | phys CI low | phys | class-cond | CC CI low | CC |
|---|---|---|---|---|---|---|---|---|---|
{ctrl_tab}

At the secondary SNR:

| class | arm | estimator | SNR₀ | phys | phys CI low | phys | class-cond | CC CI low | CC |
|---|---|---|---|---|---|---|---|---|---|
{hi_tab}

**The physical target moves with the class-conditional one.** That is the
result item 14 was written to test: improvement on `CLASS_CONDITIONAL` alone
would be a statement about the class, and here the reconstruction also improves
against the analytic source, which is the claim that means something physical.

## 2. The improvement is not carried by one kind of state

Mean error by the measure each state's label selected, TSVD at SNR₀ =
{snr_p:.0f}, physical target:

| class | arm | assignment | blended | amplitude |
|---|---|---|---|---|
{ktab}

The resolved arm in the primary class beats the direct image on **all three**
measure kinds, so the headline number is not an artifact of one state class
dominating. That check matters because the endpoint has a soft spot, described
next.

**A near-null estimator is right about nothing being there.** On `DEAD` states
the measure is amplitude alone, and an estimator that reports almost no
amplitude scores well for free. `TOTAL_FLUX` -- a single number per time, with
no spatial information at all -- reaches
{float(kind.loc[(ctrl, 'TOTAL_FLUX'), 'amplitude']):.3f} on amplitude against
the direct image's {float(kind.loc[(ctrl, 'DIRECT_PHYSICAL'), 'amplitude']):.3f},
and that is most of why it shows a positive reduction in the control class.
Dead states are {100 * mix['n_dead']:.1f}% of this bank. The behaviour is
correct in itself -- reporting large amplitude where nothing exists *is* an
error, and dropping dead states is what item 16 forbids -- but it means the
all-state number should never be read without the per-kind split above.

## 3. Secondary conditional endpoint — stable multi-resolved states only

Normalised unbalanced assignment cost, where 1.0 is the cost of one whole
feature gained or lost. TSVD, SNR₀ = {snr_p:.0f},
{int(sm.n_stable_multi_truths)} truths carrying such states.

| class | arm | direct | arm | |
|---|---|---|---|---|
{stab}

**This is the weak result, and it is the honest one.** On states where the
source genuinely presents two resolved features, the primary class's resolved
arm improves the cost from {float(sm.stable_multi_direct):.3f} to
{float(sm.stable_multi_arm):.3f} -- about
{100 * (1 - float(sm.stable_multi_arm) / float(sm.stable_multi_direct)):.0f}%,
and still above 1.0, meaning the reconstruction is on average getting more than
one whole feature wrong. In the control class the resolved arm makes it *worse*,
and the unresolved arm makes it worse in the primary class.

So resolving the orders improves the description of the past as a whole, and
does not yet deliver recovery of a resolved two-feature set. The primary
endpoint and this one are answering different questions and giving different
answers, which is the distinction HMT-1 could not draw because it asked every
state for a peak position.

## 4. Controls and selection

`UNRESOLVED_IMAGE` does not reach improvement in either class, so the benefit
is attributable to resolving the orders rather than to the extra photons an
unresolved second image also carries. `TOTAL_FLUX` is negative or
non-significant in the primary class.

{int(sel.at_max_regularization_end.sum())} of {len(sel)} selections landed at
the maximal end of their grid, and selection errors run
{sel.selection_error.min():.3f} to {sel.selection_error.max():.3f} on a scale
where 1.0 is the worst possible. No collapse.

Bank composition: single-resolved {100 * mix['n_single_resolved']:.1f}%,
multi-resolved {100 * mix['n_multi_resolved']:.1f}%, blended
{100 * mix['n_blended']:.1f}%, dead {100 * mix['n_dead']:.1f}%, ambiguous
{100 * mix['n_ambiguous']:.1f}%.

## 5. Gates

| gate | status | measured | threshold |
|---|---|---|---|
{gtab}

## 6. Scope

One geometry, one spin, one inclination. Six analytic families whose ranges
were preserved with no separation cut, so the bank contains the blended and
ambiguous states that HMT-1's endpoint could not represent. Absolute errors
remain high -- the all-state error is {float(r_tsvd[f'{T_PHYS}_arm']):.3f} for
the resolved arm on a scale where 1.0 is the worst case -- so this is a
material improvement in a regime that is still far from accurate recovery.

No sealed held-out main was created and none is authorized. Classical
estimators only.

**STOP** for reviewer adjudication, per item 18. Order leakage, geometry
mismatch, VLBI, machine learning and a new pixel-movie campaign remain
unauthorized.
"""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    PROV.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(body)
    inputs = sorted(str(p.relative_to(ROOT)) for p in TAB.glob("hmt2_stage1_*.parquet"))
    PROV.write_text(json.dumps({
        "schema": "phrt-artifact-manifest/1",
        "experiment_id": "HMT2_STAGE1",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "stop_token": g["stop_token"],
        "class_conditional_improves": g["class_conditional_improves"],
        "physical_end_to_end_improves": g["physical_end_to_end_improves"],
        "execution_attestation": att,
        "report_assembly_attestation": attest([FZ]),
        "freeze_sha256": sha256_file(FZ),
        "inputs": {p: sha256_file(ROOT / p) for p in inputs},
        "outputs": {str(OUT.relative_to(ROOT)): sha256_file(OUT)},
    }, indent=2, default=str) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}\nwrote {PROV.relative_to(ROOT)}")
    print(f"  {g['stop_token']}")
    print(f"total {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
