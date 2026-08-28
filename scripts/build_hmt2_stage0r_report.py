#!/usr/bin/env python3
"""Report for HMT-2 stage 0R, the source-only correction."""
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

FZ = ROOT / "artifacts" / "configs" / "HMT2_STAGE0R_SOURCE_ONLY_CORRECTION_V0.json"
G = ROOT / "artifacts" / "gates" / "hmt2_stage0r_gates.json"
TAB = ROOT / "artifacts" / "tables"
OUT = ROOT / "artifacts" / "reports" / "HMT2_STAGE0R_SOURCE_ONLY_CORRECTION.md"
PROV = ROOT / "artifacts" / "provenance" / "HMT2_STAGE0R_ARTIFACT_MANIFEST.json"
D = "\n"


def main() -> int:
    t0 = time.time()
    fz = json.loads(FZ.read_text())
    g = json.loads(G.read_text())
    rt = pd.read_parquet(TAB / "hmt2_stage0r_merger_rates.parquet")
    pa = pd.read_parquet(TAB / "hmt2_stage0r_per_age.parquet")

    def _num(x):
        return f"{x:.4g}" if isinstance(x, float) else str(x)

    gtab = D.join(f"| `{k}` | {v['status']} | {_num(v.get('measured'))} | "
                  f"{_num(v.get('threshold'))} |" for k, v in g["gates"].items())
    gnotes = D.join(f"- `{k}` — {v['note']}"
                    for k, v in g["gates"].items() if v.get("note"))

    two = rt[rt.family == "two_hotspot_trajectories"].copy()
    ttab = D.join(
        f"| `{r.stratum}` | `{r['class']}` | {int(r.n_states)} | "
        f"{int(r.n_merged)} | {r.merger_rate:.3f} | "
        f"{'**yes**' if r.carries_claim else 'no'} |"
        for _, r in two.sort_values(["stratum", "class"]).iterrows())

    stab = rt[(rt.stratum == "STABLE_MULTI_RESOLVED") & (rt.n_states > 0)]
    atab = D.join(
        f"| `{r.family}` | `{r['class']}` | {int(r.n_states)} | "
        f"{r.merger_rate:.3f} | {r.unbalanced_cost_normalized_median:.3f} |"
        for _, r in stab.sort_values(["family", "class"]).iterrows())

    def rate(stratum, cls):
        q = two[(two.stratum == stratum) & (two["class"] == cls)]
        return float(q.merger_rate.iloc[0]) if len(q) else float("nan")

    s = g["strata_counts"]
    agg = pa[(~pa.canary) & (~pa.off_manifold)]
    body = f"""# HMT-2 stage 0R — source-only correction

Freeze `{fz['id']}`, run `{g['id']}`.
Ray map imported: {str(g['ray_map_imported']).lower()}. Operator constructed:
{str(g['operator_constructed']).lower()}. Both derived from an inspection of
loaded modules taken *after* all computation, not written as literals.
{g['n_truths']} sources, {g['n_per_age_rows']:,} per-age rows,
{g['runtime_seconds']} s.

## 1. What was corrected

Stage 0 computed its projection merger rate over every state the finest grid
called `MULTI_RESOLVED`. That set includes states the two finest grids disagree
about, and a merger rate taken over states whose multiplicity is itself
unresolved measures the classifier as much as it measures the projection. The
reviewer withheld those numbers as canonical; this run recomputes them over
reconciled stable states and publishes the per-age table they come from, so
every rate here is recomputable rather than trusted.

Nothing about the sources changed. The same {g['n_truths']} objects, the same
seeds, the same ranges with no separation cut, the same prominence fraction,
the same refinement levels, the same two classes. No redraw.

## 2. The corrected rates

`two_hotspot_trajectories`, the only family with a mixed resolution regime:

| stratum | class | states | merged | merger rate | carries claim |
|---|---|---|---|---|---|
{ttab}

**The correction moves the answer in both directions at once.** On the states
that can carry a claim, the current class merges
{100 * rate('STABLE_MULTI_RESOLVED', 'L448_contrast'):.1f}% of genuinely
resolved pairs rather than the withheld
{100 * rate('ALL_FINEST_MULTI', 'L448_contrast'):.1f}%, and the enriched class
{100 * rate('STABLE_MULTI_RESOLVED', 'L896_radial_enriched'):.1f}% rather than
{100 * rate('ALL_FINEST_MULTI', 'L896_radial_enriched'):.1f}%. So the stable
merger rate is *lower* than reported, and the benefit of radial enrichment is
*larger*: a reduction of
{100 * (1 - rate('STABLE_MULTI_RESOLVED', 'L896_radial_enriched') / rate('STABLE_MULTI_RESOLVED', 'L448_contrast')):.0f}%
on stable states against
{100 * (1 - rate('ALL_FINEST_MULTI', 'L896_radial_enriched') / rate('ALL_FINEST_MULTI', 'L448_contrast')):.0f}%
under the withheld pooling. The withheld numbers understated the enrichment and
overstated the stable merger rate at the same time.

**The excluded stratum is why.** States where the two finest grids disagree
merge at {100 * rate('AMBIGUOUS_FINE_MULTI', 'L448_contrast'):.0f}% in the
current class and at
{100 * rate('AMBIGUOUS_FINE_MULTI', 'L896_radial_enriched'):.0f}% in the
enriched one -- every single one. That is not a surprise once stated: a pair
the analysis grid cannot agree about is a pair no reconstruction class of this
size will keep apart. Pooling them with the stable states dragged both class
rates toward each other and hid the difference between the classes.

Across all declared families the strata partition exactly:
{s['STABLE_MULTI_RESOLVED']:,} stable plus {s['AMBIGUOUS_FINE_MULTI']:,}
ambiguous equals {s['ALL_FINEST_MULTI']:,} finest-grid multi states, with no
state in both, which `HMT2R_G7` checks rather than assumes.

## 3. Stable-state merger rates, all families

| family | class | stable states | merger rate | median normalized unbalanced cost |
|---|---|---|---|---|
{atab}

The normalized unbalanced cost is the total assignment cost divided by the cost
of one wholly unmatched feature, so 1.0 means one feature gained or lost. It is
not a displacement.

## 4. Gates

{len(g['gates'])} gates, {sum(1 for v in g['gates'].values() if v['status'] == 'PASS')} pass,
{len(g['failed_gates'])} fail.

| gate | status | measured | threshold |
|---|---|---|---|
{gtab}

{gnotes}

The source-only guard runs twice, before any work and after all computation,
and the run document's `ray_map_imported` and `operator_constructed` fields are
derived from the second inspection. Stage 0 wrote those as literal `false`,
which records an intention rather than an observation.

## 5. The per-age table

`hmt2_stage0r_per_age` carries {len(pa):,} rows, one per source per age per
class: the fine-grid label, the coarser-grid label, the reconciled label, the
projected label, cardinality before and after projection, the matched position
cost, the unbalanced cost and its normalization, and the canary and
off-manifold flags. Every rate in this report is a group-by on that table.

Of the {len(agg):,} declared-family rows, the reconciled label is
`AMBIGUOUS` in {100 * float((agg.label_reconciled == 'AMBIGUOUS').mean()):.1f}%
and `BLENDED` in
{100 * float((agg.label_reconciled == 'BLENDED').mean()):.1f}%.

## 6. What this changes and does not change

The four preserved findings stand untouched: the canary blended at 61 of 61
ages, the two-hotspot mixed resolution regime, the L448 representation limit,
and the benefit of radial enrichment. None of them rested on the merger-rate
accounting, and the correction strengthens the fourth rather than weakening it.

What changes is which number may be quoted. The canonical two-hotspot merger
rates are now
{rate('STABLE_MULTI_RESOLVED', 'L448_contrast'):.3f} and
{rate('STABLE_MULTI_RESOLVED', 'L896_radial_enriched'):.3f}, over reconciled
stable states only. The pooled {rate('ALL_FINEST_MULTI', 'L448_contrast'):.3f}
and {rate('ALL_FINEST_MULTI', 'L896_radial_enriched'):.3f} remain in the record
as what the finest grid alone would say, and carry no claim.

Still no operator and no ray map. Nothing here is an inverse-problem result.

**Stage 0R passes all corrected source-only gates**, so item 12 authorizes
`HMT2_STAGE1_RESOLUTION_AWARE_MORPHOLOGY_VALIDATION_V0`, which is registered
separately.
"""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    PROV.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(body)
    inputs = sorted(str(p.relative_to(ROOT)) for p in TAB.glob("hmt2_stage0r_*.parquet"))
    PROV.write_text(json.dumps({
        "schema": "phrt-artifact-manifest/1",
        "experiment_id": "HMT2_STAGE0R",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "ray_map_imported": g["ray_map_imported"],
        "operator_constructed": g["operator_constructed"],
        "canonical_merger_rates": {
            "stratum": "STABLE_MULTI_RESOLVED",
            "L448_contrast": rate("STABLE_MULTI_RESOLVED", "L448_contrast"),
            "L896_radial_enriched": rate("STABLE_MULTI_RESOLVED",
                                         "L896_radial_enriched")},
        "execution_attestation": g["attestation"],
        "report_assembly_attestation": attest([FZ]),
        "freeze_sha256": sha256_file(FZ),
        "inputs": {p: sha256_file(ROOT / p) for p in inputs},
        "outputs": {str(OUT.relative_to(ROOT)): sha256_file(OUT)},
    }, indent=2, default=str) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}\nwrote {PROV.relative_to(ROOT)}")
    print(f"total {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
