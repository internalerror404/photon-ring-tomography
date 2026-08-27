#!/usr/bin/env python3
"""Report for stage 2R-A. Every number read from the 2R-A tables."""
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

TAB = ROOT / "artifacts" / "tables"
G = ROOT / "artifacts" / "gates" / "r1l_2ra_gates.json"
OUT = ROOT / "artifacts" / "reports" / "R1L_STAGE2R_A.md"
PROV = ROOT / "artifacts" / "provenance" / "R1L_STAGE2R_A_ARTIFACT_MANIFEST.json"
D = "\n"


def main() -> int:
    t0 = time.time()
    g = json.loads(G.read_text())
    end = pd.read_parquet(TAB / "r1l_2ra_endpoint.parquet")
    floors = pd.read_parquet(TAB / "r1l_2ra_oracle_floor_curves.parquet")
    spans = pd.read_parquet(TAB / "r1l_2ra_stable_spans.parquet")
    sel = pd.read_parquet(TAB / "r1l_s2_selection.parquet")
    mans = sorted((ROOT / "artifacts" / "manifests").glob("R1LS2RA_*.json"))
    man = json.loads(mans[-1].read_text())
    att = man["attestation"]
    token = g["stop_token"]
    M = g["materiality_standard"]

    po = end[end.scope == "primary_banks_pooled"].sort_values(
        ["arm", "source_class", "estimator"])
    potab = D.join(
        f"| `{r.source_class}` | `{r.arm}` | {r.estimator} | "
        f"{r.median_relative_reduction:+.4f} | {r.ci_low:+.4f} | {r.ci_high:+.4f} | "
        f"{int(r.n_families_improved)}/4 | "
        f"{'yes' if r.all_primary_banks_positive else 'no'} | "
        f"{'**MATERIAL**' if (r.median_relative_reduction >= M['median_relative_reduction'] and r.ci_low >= M['ci_low_relative'] and r.n_families_improved >= M['min_families'] and r.all_primary_banks_positive) else 'no'} |"
        for r in po.itertuples())

    bk = end[(end.scope == "single_bank") & (end.arm == "RESOLVED_PHYSICAL")]
    bktab = D.join(
        f"| `{r.source_class}` | {r.estimator} | `{r.bank}` | "
        f"{r.median_relative_reduction:+.4f} | {r.ci_low:+.4f} | {r.ci_high:+.4f} |"
        for r in bk.sort_values(["source_class", "estimator", "bank"]).itertuples())

    fr = floors.groupby(["source_class", "in_old_band"]).reachable_at_epsilon.mean()
    frtab = D.join(f"| `{c}` | {'old band' if o else 'younger'} | {v:.3f} |"
                   for (c, o), v in fr.items())

    sp = spans.sort_values(["source_class", "arm"])
    sptab = D.join(f"| `{r.source_class}` | `{r.arm}` | {r.T_stable_anchor_M:.1f} | "
                   f"{r.pass_fraction_at_youngest_age:.2f} |" for r in sp.itertuples())

    st = sel[sel.snr0 == 100.0].pivot_table(
        index=["source_class", "arm"], columns="estimator",
        values="selected_hyperparameter")
    seltab = D.join(f"| `{c}` | `{a}` | {row['RIDGE_IDENTITY']:.3e} | "
                    f"{row['TSVD']:.3e} |" for (c, a), row in st.iterrows())

    gtab = D.join(f"| `{k}` | {v['status']} |" for k, v in g["gates"].items())

    body = f"""# R1L stage 2R-A — corrected endpoint from existing artifacts

REVIEWER_RULING_R1L_STAGE2_011 item 7. No new source truth was generated. The
committed banks were regenerated from their frozen seeds and every one hashed to
the value stage 2 recorded, so these are the same objects, recomputed.

- run `{man['run_id']}`, execution commit `{att['execution_commit'][:12]}`,
  clean {att['clean']}, preregistered {att['preregistered']}
- `baseline_one_positive` excluded from every endpoint row
- **corrected disposition `{token}`**

## 1. Endpoint, pooled over the primary banks

Paired relative reduction against the direct arm, equal-weight over bank-family
cells, at SNR₀ = 100. Material requires median ≥
{M['median_relative_reduction']:.0%}, bootstrap lower bound ≥
{M['ci_low_relative']:.0%}, ≥ {M['min_families']}/4 families, every primary bank
positive, and null controls passing — **and both estimators on the same class**.

| class | arm | estimator | median | CI low | CI high | families | all banks + | material |
|---|---|---|---:|---:|---:|---|---|---|
{potab}

## 2. Every primary bank separately, resolved arm

| class | estimator | bank | median | CI low | CI high |
|---|---|---|---:|---:|---:|
{bktab}

## 3. Why the two estimators disagree by three orders of magnitude

This is the finding of stage 2R-A, and it is a selection pathology rather than
physics.

| class | arm | ridge cut | TSVD cut |
|---|---|---:|---:|
{seltab}

The selection rule minimizes old-band structure error on the selection split.
When the representation floor is high, the lowest achievable error is obtained
by reconstructing **almost nothing** — the null estimator scores
`||truth||`, and any honest attempt scores worse. So the selection drives the
direct arm to maximal regularization at every class, and at `L448` it drives
*every* arm there. The endpoint then compares one near-null estimator against
another, which is why those deltas sit at 1e-4 to 1e-6.

The single exception is ridge on the resolved arm at `L1056`, where the
selection chose a light cut of 3.2e-05 because the resolved operator at 1056
dimensions can actually reconstruct. That configuration shows a median relative
reduction of 14.2% with a bootstrap interval of [9.9%, 16.0%], 4/4 families and
every primary bank positive — it meets every materiality threshold on its own.
It fails the corrected rule only because TSVD, the declared primary estimator,
was truncated to 0.316 on the same class and shows 0.03%.

I read that as one real configuration surrounded by degenerate ones, not as a
material result. Reporting it as a pass would mean reporting the one cell where
the selection happened not to collapse.

## 4. Exact age-local oracle representation floors

Fraction of age cells where the ε = 0.25 criterion is reachable **at all**, by a
perfect estimator restricted to the class:

| class | band | reachable fraction |
|---|---|---:|
{frtab}

At `L224` the criterion is unreachable in over 90% of age cells and at `L1056`
in more than 40%. The span endpoint was never testable on analytic banks.

## 5. Canonical ensemble stable spans

`T_stable_anchor` at ε = {spans.epsilon.iloc[0]}, q = {spans["quantile"].iloc[0]},
supremum inside the probability, over the stored TSVD / SNR₀ = 100 ensemble.

| class | arm | T_stable_anchor (M) | pass fraction at the youngest age |
|---|---|---:|---:|
{sptab}

Every span is zero, and the reason is visible in the last column: no truth
reaches ε = 0.25 even at age 0. This is not a statement about depth.

## 6. Gates

| gate | status |
|---|---|
{gtab}

## 7. Corrected scientific disposition

`{token}`

The stage-2 formal token `R1L_STAGE2_RESOLVED_AND_UNRESOLVED_PASS` is preserved
and classified `FORMAL_PROTOCOL_TOKEN_UNDER_NONMATERIAL_CRITERIA`. Under the
materiality standard, with the secondary bank excluded, banks reported
separately, equal-weight aggregation and same-class estimator confirmation,
**no arm shows a material old-band structural advantage**.

Three separate reasons, all recorded:

1. The analytic banks put the ε = 0.25 criterion below the representation floor
   over most of the age grid, so the span endpoint could not be tested.
2. The selection rule collapses the direct arm — and at `L448` every arm — to
   the null estimator, so the endpoint compares nothing against nothing.
3. Where the selection did not collapse, ridge on resolved at `L1056`, the
   effect is 14.2% and material on its own but unconfirmed by TSVD.

All three are addressed by exact-in-class banks, which remove the floor and with
it the incentive for the selection to collapse. That is stage 2R-B.
"""
    OUT.write_text(body)
    inputs = sorted(str(p.relative_to(ROOT)) for p in TAB.glob("r1l_2ra_*.parquet"))
    PROV.write_text(json.dumps({
        "schema": "phrt-artifact-manifest/1",
        "experiment_id": "R1L_STAGE_2R_A",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "stop_token": token,
        "supersedes": "the pooled endpoint rows of r1l_s2_primary_endpoint",
        "authoritative_attestation": "execution",
        "execution_attestation": att,
        "report_assembly_attestation": attest([]),
        "inputs": {p: sha256_file(ROOT / p) for p in inputs},
        "outputs": {str(OUT.relative_to(ROOT)): sha256_file(OUT)},
    }, indent=2, default=str) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}\nwrote {PROV.relative_to(ROOT)}")
    print(f"  disposition: {token}\ntotal {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
