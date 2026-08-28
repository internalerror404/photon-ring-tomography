#!/usr/bin/env python3
"""Report for the HMT-2 stage 0 source object and resolution audit.

Every number read from the stage 0 tables. The canary is reported by name and
excluded from every aggregate, per item 17.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from phrt.numerics import pin

pin()

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from phrt.attestation import attest  # noqa: E402
from phrt.config import sha256_file  # noqa: E402

FZ = ROOT / "artifacts" / "configs" / "HMT2_STAGE0_SOURCE_OBJECT_AND_RESOLUTION_AUDIT_V0.json"
G = ROOT / "artifacts" / "gates" / "hmt2_stage0_gates.json"
TAB = ROOT / "artifacts" / "tables"
OUT = ROOT / "artifacts" / "reports" / "HMT2_STAGE0_SOURCE_RESOLUTION_AUDIT.md"
PROV = ROOT / "artifacts" / "provenance" / "HMT2_STAGE0_ARTIFACT_MANIFEST.json"
D = "\n"
STATES = ("single_resolved", "multi_resolved", "blended", "dead", "ambiguous")


def main() -> int:
    t0 = time.time()
    fz = json.loads(FZ.read_text())
    g = json.loads(G.read_text())
    st = pd.read_parquet(TAB / "hmt2_stage0_states.parquet")
    pj = pd.read_parquet(TAB / "hmt2_stage0_projection.parquet")
    wd = pd.read_parquet(TAB / "hmt2_stage0_class_widths.parquet")
    bl = pd.read_parquet(TAB / "hmt2_stage0_blended.parquet")
    tr = pd.read_parquet(TAB / "hmt2_stage0_tracks.parquet")

    # item 17: the canary is named and never aggregated
    can = st[st.canary]
    can_pj = pj[pj.canary]
    agg = st[(~st.canary) & (~st.off_manifold)]
    offm = st[(~st.canary) & st.off_manifold]
    pj_agg = pj[(~pj.canary) & (~pj.off_manifold)]

    def frac_table(df):
        rows = []
        for fam, grp in df.groupby("family"):
            n = float(grp.n_ages.sum())
            cells = [f"{grp[f'n_{s}'].sum() / n:.3f}" for s in STATES]
            rows.append(f"| `{fam}` | {int(grp.shape[0])} | " + " | ".join(cells)
                        + f" | {grp.grid_convergence_cells_median.median():.3f} "
                        f"| {grp.grid_convergence_cells_max.max():.3f} "
                        f"| {int(grp.grid_convergence_cardinality_error_max.max())} |")
        return D.join(rows)

    ftab = frac_table(agg)
    otab = frac_table(offm)

    ptab = D.join(
        f"| `{r.family}` | `{r['class']}` | {int(r.n_multi_before)} | "
        f"{r.merger_rate:.3f} | {r.representation_floor_median:.3f} | "
        f"{r.representation_floor_max:.3f} |"
        for _, r in pj_agg.groupby(["family", "class"], as_index=False).agg(
            n_multi_before=("n_multi_before", "sum"),
            merger_rate=("merger_rate", "mean"),
            representation_floor_median=("representation_floor_median", "median"),
            representation_floor_max=("representation_floor_max", "max")).iterrows())

    mw = wd.dropna(subset=["minimum_representable_width_M"])
    mtab = D.join(
        f"| `{r['class']}` | {r.r_centre_M:.0f} | "
        f"{r.minimum_representable_width_M:.2f} |"
        for _, r in mw.sort_values(["class", "r_centre_M"]).iterrows())

    ctab = D.join(
        f"| `{r['class']}` | {r.merger_rate:.3f} | "
        f"{r.representation_floor_median:.3f} |"
        for _, r in can_pj.iterrows())
    c0 = can.iloc[0] if len(can) else None
    cn = float(c0.n_ages) if c0 is not None else 1.0

    n_tracks = tr[(~tr.canary) & (~tr.off_manifold)].groupby(
        ["family", "index"]).track_id.nunique()
    body = f"""# HMT-2 stage 0 — source object and resolution audit

Freeze `{fz['id']}`, run `{g['id']}`.
Ray map imported: {str(g['ray_map_imported']).lower()}. Operator constructed:
{str(g['operator_constructed']).lower()}. {g['n_truths']} sources,
{len(g['levels'])} nested grids, {len(g['classes'])} source classes,
{g['runtime_seconds']} s.

## 1. The question

HMT-1 declared a source model and an evaluation grid separately and never
checked the contract between them. Its sealed main then failed on a truth whose
two hotspots sat 0.34 log-radial cells apart with sub-cell widths: the grid
could not separate them, the extractor reported the blend, and the reference
resolved the dominant one. Nothing was broken. Nobody had asked whether these
families put resolvable features on this grid.

Stage 0 asks. No ray map is imported and no operator is constructed, so nothing
below is an inverse-problem result, and none of it can be read as one.

## 2. What the sources actually contain

Fractions of (truth, age) states over the six declared families, classified by
topographic prominence at the frozen fraction
{fz['classification']['prominence_fraction']}, with `AMBIGUOUS` meaning the
label disagreed between the two finest grids.

| family | truths | single | multi | blended | dead | ambiguous | conv med | conv max | card err |
|---|---|---|---|---|---|---|---|---|---|
{ftab}

Off-manifold controls, reported separately and never pooled with the declared
families:

| family | truths | single | multi | blended | dead | ambiguous | conv med | conv max | card err |
|---|---|---|---|---|---|---|---|---|---|
{otab}

`conv` is the grid-convergence error between the two finest levels, in level-0
cells: how much the measured feature set moves when the analysis grid is
doubled. `card err` is the largest disagreement in how many features are
present.

## 3. What projection onto a reconstruction class destroys

The merger rate is the fraction of `MULTI_RESOLVED` states that stop being
multi-resolved once the field is projected onto the class. The representation
floor is the set-valued assignment error between the analytic field's features
and its own best in-class approximation -- the error an estimator starts with,
before any operator and before any noise.

| family | class | multi states | merger rate | floor median | floor max |
|---|---|---|---|---|---|
{ptab}

## 4. What the classes can represent at all

The narrowest radial feature each class keeps narrow, measured by projecting
Gaussians of decreasing width and reporting the input width at which the output
has broadened by a factor of two. This is a property of the class and needs no
source bank.

| class | r centre (M) | minimum representable width (M) |
|---|---|---|
{mtab}

## 5. Blended states

{len(bl):,} (truth, age) states are blended across all sources. They are
reported as a centroid, a total contrast, second moments and mode amplitudes --
what a one-peak field supports -- and not as two trajectories forced through
it. Median second radial moment {bl.second_moment_rr.median():.4f} in log r,
median azimuthal {bl.second_moment_pp.median():.4f} in radians squared.

## 6. Tracks

Multi-resolved features are associated across age by the same assignment
metric used everywhere else, so a track break and a position error are measured
on one scale. Median distinct tracks per declared truth:
{float(n_tracks.median()) if len(n_tracks) else float('nan'):.1f}.

## 7. The canary

`HMT1_SOURCE_RESOLUTION_FAILURE_CANARY`, the HMT-1 truth that failed the sealed
main. Named regression only: it appears in no aggregate above and in no
per-family fraction.

States over its {int(cn)} ages: single
{int(c0.n_single_resolved) if c0 is not None else 0}, multi
{int(c0.n_multi_resolved) if c0 is not None else 0}, blended
{int(c0.n_blended) if c0 is not None else 0}, dead
{int(c0.n_dead) if c0 is not None else 0}, ambiguous
{int(c0.n_ambiguous) if c0 is not None else 0}.

| class | merger rate | representation floor median |
|---|---|---|
{ctab}

## 8. What this does and does not establish

It establishes what these six families put on these grids and what survives
projection onto these two classes. It says nothing about any estimator, because
no operator exists in this run.

The audit does not impose a separation cut, per item 9. It measures what the
declared ranges contain so that a cut, a finer grid, or a resolution-aware
measure can be chosen on evidence rather than on the one truth that happened to
fail.

**STOP.** Item 18: the source-only audit is complete. HMT-2 validation, a new
sealed bank, order leakage, geometry mismatch, VLBI and machine learning all
remain unauthorized.
"""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    PROV.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(body)
    inputs = sorted(str(p.relative_to(ROOT)) for p in TAB.glob("hmt2_stage0_*.parquet"))
    PROV.write_text(json.dumps({
        "schema": "phrt-artifact-manifest/1",
        "experiment_id": "HMT2_STAGE0",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "ray_map_imported": False, "operator_constructed": False,
        "canary_excluded_from_aggregates": True,
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
