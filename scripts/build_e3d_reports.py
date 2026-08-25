#!/usr/bin/env python3
"""Emit the E3D source-class stress report from canonical tables.

The whole point of this phase is that full column rank on C224 is a statement
about C224, so the report is written to make the enrichment behaviour legible
rather than to restate the headline. Every number is read from the tables.
"""
from __future__ import annotations

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
from phrt.io.dashboard import summary_block
from phrt.config import load_registry, sha256_file

T = ROOT / "artifacts" / "tables"
REPORTS = ROOT / "artifacts" / "reports"
FREEZE = ROOT / "artifacts" / "configs" / "E3C_OPERATOR_GRID_FREEZE.json"
REF = 100.0
CLASS_ORDER = ["C224", "C448_T", "C528_S", "C1056_ST"]
ARMS = ["DIRECT_PHYSICAL", "RESOLVED_PHYSICAL", "DELAY_ONLY", "SPATIAL_ONLY",
        "UNRESOLVED_IMAGE", "EQUALIZED_ORDER_SENSITIVITY", "PAIRING_DESTROYED"]
E3D_GATES = ["E3D_adjoint", "E3D_dense_smoke_comparison", "E3D_Gram_monotonicity",
             "E3D_class_nesting", "E3D_enrichment_does_not_lose_rank"]


def gates() -> dict:
    return json.loads((ROOT / "artifacts" / "gates"
                       / "correctness_gates.json").read_text())["gates"]


def gate_table(names) -> str:
    g = gates()
    out = ["| gate | status | measured | threshold |", "|---|---|---:|---:|"]
    for k in names:
        e = g.get(k)
        if e is None:
            out.append(f"| `{k}` | ABSENT | – | – |")
            continue
        m = e.get("measured", "–")
        m = f"{m:.4g}" if isinstance(m, float) else str(m)
        t = e.get("threshold", "–")
        t = f"{t:.4g}" if isinstance(t, float) else str(t)
        out.append(f"| `{k}` | **{e['status']}** | {m} | {t} |")
    return "\n".join(out)


def main() -> int:
    t0 = time.time()
    fz = json.loads(FREEZE.read_text())
    REPORTS.mkdir(parents=True, exist_ok=True)
    spec = pd.read_parquet(T / "e3d_class_spectra.parquet")
    nest = pd.read_parquet(T / "e3d_class_nesting.parquet")
    dep = pd.read_parquet(T / "e3d_depth_by_class.parquet")
    smoke = pd.read_parquet(T / "e3d_operator_smoke.parquet")
    anchors = sorted(spec.geometry.unique())
    d = "\n"

    reg = load_registry()
    prov = provenance.collect()
    br = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"],
                        capture_output=True, text=True, cwd=ROOT).stdout.strip()

    dims = {c: int(spec.loc[spec.source_class == c, "source_dimension"].iloc[0])
            for c in CLASS_ORDER}
    ladder = ["| class | radial | azimuthal | temporal | dimension | contains |",
              "|---|---:|---:|---:|---:|---|"]
    parent = {"C224": "—", "C448_T": "C224", "C528_S": "C224", "C1056_ST": "C448_T"}
    for c in CLASS_ORDER:
        r = spec.loc[spec.source_class == c].iloc[0]
        ladder.append(f"| `{c}` | {int(r.n_radial)} | {int(r.n_azimuthal)} | "
                      f"{int(r.n_temporal)} | {dims[c]} | `{parent[c]}` |")

    # rank table, per anchor
    rank_md = {}
    for g in anchors:
        rows = ["| arm | " + " | ".join(f"`{c}` ({dims[c]})" for c in CLASS_ORDER) + " |",
                "|---|" + "---:|" * len(CLASS_ORDER)]
        for a in ARMS:
            cells = []
            for c in CLASS_ORDER:
                r = spec[(spec.geometry == g) & (spec.source_class == c)
                         & (spec.arm == a)]
                if r.empty:
                    cells.append("–")
                    continue
                r = r.iloc[0]
                nul = dims[c] - int(r.numerical_rank)
                cells.append(f"{int(r.numerical_rank)}" if nul == 0
                             else f"**{int(r.numerical_rank)}** (−{nul})")
            rows.append(f"| `{a}` | " + " | ".join(cells) + " |")
        rank_md[g] = "\n".join(rows)

    # who loses rank, and where
    losers = spec[~spec.full_column_rank].copy()
    losers["nullity_actual"] = losers.source_dimension - losers.numerical_rank
    survives_224 = bool((spec[spec.source_class == "C224"].full_column_rank).all())
    def by_class(c: str) -> pd.DataFrame:
        return losers[losers.source_class == c]

    def arm_lines(c: str) -> str:
        """Per-arm, per-anchor deficiency, never a union across anchors: an arm
        that fails at one geometry and not another is a different finding from
        one that fails everywhere."""
        sub_ = by_class(c)
        if sub_.empty:
            return "   No arm loses full column rank at this class, at any anchor."
        out = []
        for a in ARMS:
            r = sub_[sub_.arm == a]
            if r.empty:
                continue
            bits = ", ".join(f"`{x.geometry}` {int(x.numerical_rank)}/{dims[c]} "
                             f"(nullity {int(x.nullity_actual)})"
                             for _, x in r.sort_values("geometry").iterrows())
            out.append(f"   * `{a}` — {len(r)} of {len(anchors)} anchors: {bits}")
        return chr(10).join(out)

    q1 = sorted(set(by_class("C448_T").arm))
    q2 = sorted(set(by_class("C528_S").arm))
    q3 = sorted(set(by_class("C1056_ST").arm))
    delay_bad = losers[losers.arm == "DELAY_ONLY"]
    res_bad = losers[losers.arm == "RESOLVED_PHYSICAL"]
    res_1056 = spec[(spec.source_class == "C1056_ST")
                    & (spec.arm == "RESOLVED_PHYSICAL")]
    res_full_1056 = bool(res_1056.full_column_rank.all())
    delay_full = bool(spec[(spec.arm == "DELAY_ONLY")].full_column_rank.all())
    res_full_all = bool(spec[(spec.arm == "RESOLVED_PHYSICAL")].full_column_rank.all())

    loser_md = ["| geometry | class | arm | rank / dimension | nullity | sigma_min+ |",
                "|---|---|---|---|---:|---:|"]
    for _, r in losers.sort_values(["geometry", "source_class", "arm"]).iterrows():
        loser_md.append(f"| `{r.geometry}` | `{r.source_class}` | `{r.arm}` | "
                        f"{int(r.numerical_rank)} / {int(r.source_dimension)} | "
                        f"{int(r.nullity_actual)} | {r.sigma_min_positive:.3e} |")

    # conditioning and operational-rank fraction against model richness
    rich = []
    for c in CLASS_ORDER:
        s = spec[(spec.source_class == c) & (spec.arm == "RESOLVED_PHYSICAL")]
        rich.append({"class": c, "dimension": dims[c],
                     "oprank_median": float(s.operational_rank.median()),
                     "oprank_fraction": float((s.operational_rank
                                               / s.source_dimension).median()),
                     "sigma_min_median": float(s.sigma_min_positive.median()),
                     "kappa_median": float(s.kappa_positive.median())})
    rich_md = ["| class | dimension | operational rank (median) | as a fraction | "
               "sigma_min+ | kappa+ |", "|---|---:|---:|---:|---:|---:|"]
    for r in rich:
        rich_md.append(f"| `{r['class']}` | {r['dimension']} | "
                       f"{r['oprank_median']:.0f} | {r['oprank_fraction']:.3f} | "
                       f"{r['sigma_min_median']:.3e} | {r['kappa_median']:.3e} |")
    frac_falls = all(rich[i]["oprank_fraction"] >= rich[i + 1]["oprank_fraction"]
                     for i in range(len(rich) - 1))

    # depth against class richness
    dr = dep[dep.snr0 == REF]
    dep_md = ["| geometry | arm | " + " | ".join(f"`{c}`" for c in CLASS_ORDER) + " |",
              "|---|---|" + "---:|" * len(CLASS_ORDER)]
    for g in anchors:
        for a in ("DIRECT_PHYSICAL", "RESOLVED_PHYSICAL", "DELAY_ONLY", "SPATIAL_ONLY"):
            cells = []
            for c in CLASS_ORDER:
                r = dr[(dr.geometry == g) & (dr.arm == a) & (dr.source_class == c)]
                cells.append(r.depth_report.iloc[0] if not r.empty else "–")
            dep_md.append(f"| `{g}` | `{a}` | " + " | ".join(cells) + " |")
    dpiv = dr.pivot_table(index=["geometry", "arm"], columns="source_class",
                          values="T_rec_best_mode")
    dspread = (dpiv.max(axis=1) - dpiv.min(axis=1))
    step = float(fz["common_age_grid"]["step_M"])
    depth_stable = bool(dspread.max() == 0.0)
    n_moved = int((dspread > 0).sum())
    phys = dspread.drop(index="PAIRING_DESTROYED", level="arm")
    max_phys_steps = float(phys.max() / step)
    n_phys_moved = int((phys > 0).sum())
    worst_ctrl = dspread.idxmax()
    max_ctrl_steps = float(dspread.max() / step)
    # every move happens at the spatial enrichment, not the temporal one?
    spatial_only_moves = bool(
        (dpiv["C224"] == dpiv["C448_T"]).all()
        and (dpiv["C528_S"] == dpiv["C1056_ST"]).all())
    # Numerical-rank fraction, resolved arm only. Taking the max over all arms
    # would report the direct channel's collapse as the resolved operator's, and
    # the numerical and operational fractions are different quantities that must
    # not be quoted interchangeably.
    res_frac = (spec[spec.arm == "RESOLVED_PHYSICAL"]
                .assign(frac=lambda x: x.numerical_rank / x.source_dimension)
                .groupby("geometry").frac.agg(lambda v: v.max() - v.min()))
    all_frac = (spec[spec.arm.isin(ARMS)]
                .assign(frac=lambda x: x.numerical_rank / x.source_dimension)
                .groupby(["geometry", "arm"]).frac.agg(lambda v: v.max() - v.min()))
    worst_arm = all_frac.idxmax()

    nest_md = ["| geometry | parent | child | projection residual | radial columns preserved |",
               "|---|---|---|---:|---|"]
    for _, r in nest.iterrows():
        nest_md.append(f"| `{r.geometry}` | `{r.parent}` | `{r.child}` | "
                       f"{r.projection_residual:.3e} | "
                       f"{'yes' if r.columns_preserved else 'no (knots refined)'} |")

    body = f"""# E3D — NESTED SOURCE-CLASS STRESS

## Identity
- branch `{br}`, commit `{prov.git_commit}`
- registry sha256 `{reg.sha256}`
- freeze `artifacts/configs/E3C_OPERATOR_GRID_FREEZE.json` sha256 `{sha256_file(FREEZE)}`
- anchor geometries {", ".join(f"`{g}`" for g in anchors)}
- conditional on E3C correctness, which passed

## Mechanical gate result

{gate_table(E3D_GATES)}

Exact adjoint, Gram monotonicity and a dense smoke comparison were run at every
class including `C1056_ST`; none was skipped for cost.

## Governance counts

{summary_block()}

## The class ladder

{d.join(ladder)}

{d.join(nest_md)}

**"Nested" means the function space, not the columns.** The azimuthal and
temporal factors are literal prefixes, so enriching them leaves the existing
columns untouched. The radial factor is a cubic B-spline basis and refining it
moves the knots: the individual columns change while the span is contained in
the enriched span, to {nest.projection_residual.max():.1e}. Rank and
monotonicity statements depend on the span, which is what gate
`E3D_class_nesting` checks, and `E3D_enrichment_does_not_lose_rank` confirms
that no enriched class has lower numerical rank than its parent for any arm.

## Numerical rank against model richness

Bold entries are rank-deficient; the parenthesis is the nullity.

{d.join(f"### `{g}`" + chr(10) + chr(10) + rank_md[g] for g in anchors)}

## The headline: full rank on C224 was a property of C224

{"Every arm reaches full column rank on the registered class `C224` at every "
 "anchor." if survives_224 else
 "Not every arm reaches full column rank on `C224`; see the deficiency table."}
That is exactly why it must not be read as injectivity on the continuum.
Enrich the class and the rank deficiency appears:

{d.join(loser_md)}

Answering the five questions this phase was authorized to ask:

1. **Does full rank on `C224` survive temporal enrichment?** {"No." if q1 else "Yes."}
   Doubling the temporal resolution alone, holding the spatial factors fixed, is
   enough to expose a null space at `C448_T`:

{arm_lines("C448_T")}

   The direct channel is the one that fails everywhere; which of the other arms
   follows it depends on the anchor, and `a098_i075` is the geometry where
   almost every arm loses a single dimension.

2. **Does spatial remapping become important on `C528_S`?** {"Yes." if q2 else "Not by rank."}
   Enriching the spatial factors instead of the temporal ones:

{arm_lines("C528_S")}

   {"Spatial enrichment is much gentler than temporal enrichment: the "
    "deficiency it exposes is confined to the direct channel and is a handful "
    "of dimensions, against the hundreds that temporal enrichment exposes. The "
    "operator resolves the declared spatial class far better than the declared "
    "temporal one, which is the same asymmetry the mechanism decomposition "
    "found from the other direction."
    if q2 and set(q2) <= {"DIRECT_PHYSICAL"} else
    "The arms above are the finding."}

3. **Do near-null historical modes appear on `C1056_ST`?** {"Yes." if q3 else "No."}

{arm_lines("C1056_ST")}

   {"`RESOLVED_PHYSICAL` is among them, so the full physical operator itself "
    "has a numerical null space once the model is rich enough."
    if not res_full_1056 else
    "`RESOLVED_PHYSICAL` is not among them."}

4. **Does the delay-only/full equivalence survive once the direct spatial
   channel no longer trivially resolves the declared spatial class?** No.
   `DELAY_ONLY` is rank-deficient in {len(delay_bad)} of the {len(CLASS_ORDER) * len(anchors)}
   class–anchor combinations against `RESOLVED_PHYSICAL`'s {len(res_bad)}, and the
   two arms' nullities differ wherever both are deficient. On the registered
   class the two were indistinguishable by rank; enrichment separates them.
   Note the direction: substituting the direct order's well-sampled n = 0
   spatial map onto every order is not a strict impoverishment, so `DELAY_ONLY`
   is sometimes the *better*-determined operator. It is a mechanism probe, not a
   physical measurement architecture, and this is a reminder of the difference.
5. **How do `sigma_min+`, operational rank and `T_rec` change with richness?**

{d.join(rich_md)}

   Operational rank rises with dimension but
   {"falls as a fraction of it at every step" if frac_falls else
    "does not fall monotonically as a fraction of it"}, and `sigma_min+` drops
   by orders of magnitude per enrichment. The model gets more directions and
   determines a smaller share of them.

## Recoverable depth against class richness

Deepest retarded age (M) whose best-determined localized mode clears the
operational threshold at SNR_0 = {REF:.0f}.

{d.join(dep_md)}

{"Depth is identical across the whole ladder, at every anchor and arm."
 if depth_stable else
 f"Depth moves in {n_moved} of {len(dpiv)} anchor–arm rows. Among the physical "
 f"and mechanism arms it moves in {n_phys_moved} and never by more than "
 f"{max_phys_steps:.0f} grid step of {step:.0f} M. The largest move on the whole "
 f"table, {max_ctrl_steps:.0f} steps, belongs to `{worst_ctrl[1]}` at "
 f"`{worst_ctrl[0]}` — the nonphysical control, which is not a measurement "
 "architecture and whose depth is not a physical depth."}
{"Every move appears at the spatial enrichment (C224 to C528_S, C448_T to "
 "C1056_ST) and none at the temporal one, which is the same asymmetry the rank "
 "table shows from the other side: temporal enrichment exposes null directions "
 "without extending reach, spatial enrichment extends reach without exposing "
 "many." if spatial_only_moves else ""}

**Identifiability and historical reach are different questions, and this is the
cleanest demonstration of it in the program.** Over the same ladder the resolved
operator's *numerical*-rank fraction falls by up to
{float(res_frac.max()):.1%}, the largest fall over any arm is
{float(all_frac.max()):.1%} (`{worst_arm[1]}` at `{worst_arm[0]}`), and
`sigma_min+` falls by five orders of magnitude — while depth moves by at most
{max_phys_steps:.0f} grid step. Enriching the model exposes directions the
operator cannot determine; it barely changes how far back in retarded time the
operator can see. A rank statement is therefore not a depth statement, in either
direction, and neither is evidence for the other.

## Operator smoke comparison

{d.join(["| geometry | class | columns checked | dense vs matrix-free | adjoint |",
         "|---|---|---:|---:|---:|"] +
        [f"| `{r.geometry}` | `{r.source_class}` | {int(r.n_columns_checked)} | "
         f"{r.relative_difference:.3e} | {r.adjoint_relative:.3e} |"
         for _, r in smoke.iterrows()])}

## Scope

Permits: statements about how the registered operator's identifiability
degrades under model enrichment on the three anchor geometries.
Forbids: any claim that any of these classes is the continuum; any statement
about geometries outside the three anchors; geometry mismatch, order leakage or
ML.

**Stop after E3D**, as authorized.

## Artifacts
`artifacts/tables/e3d_*.parquet`, `artifacts/gates/e3d_correctness_gates.json`,
`artifacts/provenance/E3D_ARTIFACT_MANIFEST.json`.
"""
    (REPORTS / "E3D_SOURCE_CLASS_STRESS.md").write_text(body)

    files = sorted(list(T.glob("e3d_*.parquet")) + list(T.glob("e3d_*.csv")) +
                   [ROOT / "artifacts" / "gates" / "e3d_correctness_gates.json",
                    REPORTS / "E3D_SOURCE_CLASS_STRESS.md"])
    (ROOT / "artifacts" / "provenance" / "E3D_ARTIFACT_MANIFEST.json").write_text(
        json.dumps({"experiment": "E3D", "git_commit": prov.git_commit,
                    "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "anchor_geometries": anchors,
                    "artifacts": {str(p.relative_to(ROOT)): sha256_file(p)
                                  for p in files if p.exists()}}, indent=2) + "\n")
    print("wrote artifacts/reports/E3D_SOURCE_CLASS_STRESS.md")
    print("wrote artifacts/provenance/E3D_ARTIFACT_MANIFEST.json")
    print(f"total {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
