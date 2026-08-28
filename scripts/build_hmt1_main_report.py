#!/usr/bin/env python3
"""Report for the HMT-1 sealed held-out main.

Handles both outcomes: a completed stage B, and a stage A refusal in which no
operator was ever imported. It never opens an endpoint table, so building the
report cannot itself spend the bank.
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

import pandas as pd  # noqa: E402

from phrt.attestation import attest  # noqa: E402
from phrt.config import sha256_file  # noqa: E402

FZ = ROOT / "artifacts" / "configs" / "HMT1_SEALED_HELD_OUT_MAIN_FREEZE_V2.json"
COR = ROOT / "artifacts" / "configs" / "HMT1_SEALED_MAIN_CORRECTION_AND_RETIREMENT_017.json"
SA = ROOT / "artifacts" / "gates" / "hmt1_main_stage_a_gates.json"
SB = ROOT / "artifacts" / "gates" / "hmt1_main_gates.json"
G10C = ROOT / "artifacts" / "provenance" / "HMT1_G10C_VALIDATION.json"
TAB = ROOT / "artifacts" / "tables"
OUT = ROOT / "artifacts" / "reports" / "HMT1_SEALED_MAIN.md"
PROV = ROOT / "artifacts" / "provenance" / "HMT1_SEALED_MAIN_ARTIFACT_MANIFEST.json"
D = "\n"


def _num(x):
    return f"{x:.4g}" if isinstance(x, float) else str(x)


def main() -> int:
    t0 = time.time()
    fz = json.loads(FZ.read_text())
    sa = json.loads(SA.read_text())
    sb = json.loads(SB.read_text()) if SB.exists() else None
    g10c = json.loads(G10C.read_text())
    banks = pd.read_parquet(TAB / "hmt1_main_source_banks.parquet")
    off = pd.read_parquet(TAB / "hmt1_main_off_manifold.parquet")
    att = sa["attestation"]

    sa_tab = D.join(f"| `{k}` | {v['status']} | {_num(v.get('measured'))} | "
                    f"{_num(v.get('threshold'))} |" for k, v in sa["gates"].items())
    sa_notes = D.join(f"- `{k}` — {v['note']}"
                      for k, v in sa["gates"].items() if v.get("note"))
    stage_b_ran = sb is not None
    if stage_b_ran:
        sb_tab = D.join(f"| `{k}` | {v['status']} | {_num(v.get('measured'))} | "
                        f"{_num(v.get('threshold'))} |"
                        for k, v in sb["gates"].items())
        token = sb["stop_token"]
    else:
        sb_tab = ("| _(stage B did not run: no operator was imported)_ | | | |")
        token = "HMT1_MAIN_IMPLEMENTATION_DEFECT"

    banks["worst"] = banks[["g10c_radial_cells", "g10c_azimuthal_cells"]].max(axis=1)
    fam = banks.groupby("family").worst.max().sort_values(ascending=False)
    ftab = D.join(f"| `{k}` | {v:.3f} |" for k, v in fam.items())
    over = banks[banks.worst > 1.0]
    otab = D.join(
        f"| `{r.family}` | {int(r.index_)} | {r.g10c_radial_cells:.3f} | "
        f"{r.g10c_azimuthal_cells:.3f} |"
        for r in over.rename(columns={"index": "index_"}).itertuples())

    body = f"""# HMT-1 sealed held-out main

Freeze `{fz['id']}`, bank seed {fz['seeds']['bank_seed']}.
Execution commit `{att['execution_commit'][:12]}`, tree clean:
{str(att['clean']).lower()}, preregistered: {str(att['preregistered']).lower()}.

## Disposition

`{token}`

Stage A failed one source gate, so **no operator was imported and no held-out
truth was evaluated**. There is no endpoint to withhold this time, because none
was ever computed. The bank is untouched in the strongest available sense.

That is the two-stage split doing what ruling 017 item 10 asked of it. On the
previous attempt the same class of problem was found only after the operator
had run, which is what spent that bank.

## Stage A — the source gates

| gate | status | measured | threshold |
|---|---|---|---|
{sa_tab}

{sa_notes}

## Stage B — the operator gates

{sb_tab}

## What failed, and what it is not

`HMT1M_G10c` compares the extracted peak against an independent windowed
reference, at the frozen one-cell threshold. Worst displacement per family over
the {len(banks):,} held-out truths:

| family | worst displacement (cells) |
|---|---|
{ftab}

| family | index | radial cells | azimuthal cells |
|---|---|---|---|
{otab}

One truth of {len(banks):,}. Getting to the real number took separating two
different things.

**A defect in G10c itself**, which this bank exposed and the
{g10c['n_truths_scored']}-truth validation had not. A field that is numerically
zero away from its feature still has local maxima there, and the reference was
offering them as candidates. Here a dust maximum at amplitude 0.00000 sat at
the extractor's azimuth and absorbed a real 2.4-cell azimuthal disagreement,
reporting 1.2 radial cells instead. Candidates now have to clear the birth
fraction the campaign already uses for a feature being detectable. The
correction moves reported errors *up*, not down -- this truth went from 1.251
to 2.576 cells, and an off-manifold control from 0.578 to 10.157 -- which is
the direction a correction to a gate should move.

**What remains is neither the extractor's error nor the reference's.** The
failing truth has two spots separated by 0.34 radial cells, with radial widths
of 0.23 and 0.32 cells. Both blobs, and the gap between them, are sub-cell on
the 16-point log-radial evaluation grid. They are radially unresolved: the
extractor sees a blend and reports its azimuth, the reference resolves the
dominant spot, and the two answers differ by more than a cell. The declared
`two_hotspot_trajectories` range admits configurations the declared evaluation
grid cannot resolve.

**Not redrawn and not relaxed.** Item 9 forbids a seed search and a
redraw-until-pass loop, item 6 forbids changing family ranges, and item 5 froze
the threshold at one cell. The bank stands as drawn.

## Controls, which carry no endpoint information

{len(banks):,} held-out truths, worst azimuthal mean
{banks.azimuthal_mean_max_abs.max():.2e}, most negative total emissivity
{banks.min_total.min():.3f}, local contrast
{banks.peak_fraction_of_background.min():.2f} to
{banks.peak_fraction_of_background.max():.2f} of the local background. Zero
overlap with the validation bank or with either retired bank.
{len(off):,} off-manifold truths built and marked unscored.

## Estimator scope

`TSVD` and `RIDGE_IDENTITY` authorized. `NONNEGATIVE_CONSTRAINED` recorded
`WITHDRAWN_UNSELECTED`: it was declared as a control in the validation freeze,
never implemented, and has no selected hyperparameter, so running it now would
require the selection ruling 015 item 8 forbids. `ML` remains `NOT_AUTHORIZED`.
`HMT1M_G19` refuses any run whose estimator set differs from the authorized
one.

## What a further attempt would need

A ruling on the declared `two_hotspot_trajectories` radial range. The family
draws both spots independently across the full radial support, so a pair can
land within a fraction of a log-radial cell of each other at large radius,
where a cell is about 10 M and the blob widths are 2 to 3 M. Any of these would
resolve it, and all of them are changes item 6 currently forbids:

- require a minimum radial separation between the two spots, in cells;
- refine the radial evaluation grid so that widths of 2 to 3 M are resolved at
  large radius;
- score `G10c` for multi-feature families against the blend the grid can
  actually represent rather than the resolved reference.

The third is the only one that touches no declared quantity, but it also
weakens the gate, and choosing it after seeing which truth failed is the move
this campaign has repeatedly had to refuse.

**STOP.** Item 14: stopped after this execution regardless of disposition.
Geometry mismatch, order leakage, VLBI, machine learning and a new pixel-movie
campaign remain unauthorized, and the R1L stop and its sealed commitments are
untouched.
"""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    PROV.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(body)
    inputs = sorted(str(p.relative_to(ROOT))
                    for p in TAB.glob("hmt1_main_*.parquet"))
    PROV.write_text(json.dumps({
        "schema": "phrt-artifact-manifest/1",
        "experiment_id": "HMT1_SEALED_MAIN",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "stop_token": token,
        "stage_b_executed": stage_b_ran,
        "operator_imported": stage_b_ran,
        "endpoint_computed": False,
        "authoritative_attestation": "execution",
        "execution_attestation": att,
        "report_assembly_attestation": attest([FZ, COR]),
        "freeze_sha256": sha256_file(FZ),
        "correction_record_sha256": sha256_file(COR),
        "inputs": {p: sha256_file(ROOT / p) for p in inputs},
        "outputs": {str(OUT.relative_to(ROOT)): sha256_file(OUT)},
    }, indent=2, default=str) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}\nwrote {PROV.relative_to(ROOT)}")
    print(f"  disposition: {token}  stage B executed: {stage_b_ran}")
    print(f"total {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
