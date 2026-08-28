#!/usr/bin/env python3
"""Report for the HMT-1 sealed held-out main.

If the run withheld its science reading, this report withholds it too. It reads
only the gate file and the diagnostic tables, and never opens an endpoint table
even if one exists, so building the report cannot itself spend the bank.
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
RET = ROOT / "artifacts" / "configs" / "HMT1_SEALED_MAIN_BANK_V1_RETIREMENT_016.json"
G = ROOT / "artifacts" / "gates" / "hmt1_main_gates.json"
TAB = ROOT / "artifacts" / "tables"
OUT = ROOT / "artifacts" / "reports" / "HMT1_SEALED_MAIN.md"
PROV = ROOT / "artifacts" / "provenance" / "HMT1_SEALED_MAIN_ARTIFACT_MANIFEST.json"
D = "\n"


def main() -> int:
    t0 = time.time()
    fz = json.loads(FZ.read_text())
    g = json.loads(G.read_text())
    token = g["stop_token"]
    withheld = bool(g.get("science_reading_withheld"))
    failed = g.get("failed_gates", [])
    banks = pd.read_parquet(TAB / "hmt1_main_source_banks.parquet")
    nulls = pd.read_parquet(TAB / "hmt1_main_null_pairs.parquet")
    nc = pd.read_parquet(TAB / "hmt1_main_noiseless_control.parquet")
    bg = pd.read_parquet(TAB / "hmt1_main_background_error.parquet")
    man = json.loads(sorted((ROOT / "artifacts" / "manifests")
                            .glob("HMT1M_*.json"))[-1].read_text())
    att = man["attestation"]

    def _num(x):
        return f"{x:.4g}" if isinstance(x, float) else str(x)

    gtab = D.join(f"| `{k}` | {v['status']} | {_num(v.get('measured'))} | "
                  f"{_num(v.get('threshold'))} |" for k, v in g["gates"].items())
    gnotes = D.join(f"- `{k}` — {v['note']}"
                    for k, v in g["gates"].items() if v.get("note"))

    banks["worst"] = banks[["generative_radial_cells",
                            "generative_azimuthal_cells"]].max(axis=1)
    fam = banks.groupby("family").worst.max().sort_values(ascending=False)
    ftab = D.join(f"| `{k}` | {v:.3f} |" for k, v in fam.items())
    off = int(banks.worst.gt(1.0).sum())

    bgt = bg.groupby("regime").agg(
        median_relative=("relative_error", "median"),
        worst_relative=("relative_error", "max")).reset_index()
    bgtab = D.join(f"| `{r.regime}` | {r.median_relative:.4f} | "
                   f"{r.worst_relative:.4f} |" for r in bgt.itertuples())

    nct = D.join(
        f"| `{r.regime}` | `{r.arm}` | {r.estimator} | "
        f"{r.median_noise_displacement_relative:.4f} | "
        f"{'yes' if r.noiseless_endpoint_is_lower else 'no'} |"
        for r in nc.sort_values(["regime", "arm", "estimator"]).itertuples())

    body = f"""# HMT-1 sealed held-out main

Freeze `{fz['id']}` ({fz.get('revision', 'v1')}), run `{g['run_id']}`.
Execution commit `{att['execution_commit'][:12]}`, tree clean:
{str(att['clean']).lower()}, preregistered: {str(att['preregistered']).lower()}.

## Disposition

`{token}`

{len(g['gates']) - len(failed)} of {len(g['gates'])} gates pass. The failure is
{', '.join(f'`{x}`' for x in failed)}.

> **The science reading of this run is withheld, and withheld means unseen.**
>
> The endpoint tables were not written and the regime verdicts were not
> printed. Nobody, including the author of this report, has seen how the
> held-out bank scores. That is deliberate: labelling a defective run's
> numbers "diagnostic only" still puts them in the record, which spends the
> bank and means no corrected rerun on it could honestly be called sealed.
> The bank is intact and a corrected rerun on it is still a sealed run.

## What failed

`HMT1M_G10b` asks whether the feature extractor, pointed at the truth itself
with no operator and no noise in the way, returns the feature that was actually
put there. Worst displacement over the {len(banks):,} held-out truths, in
evaluation-grid cells:

| family | worst displacement (cells) |
|---|---|
{ftab}

{off} truth of {len(banks):,} exceeds the sealed threshold of one cell. It is a
`two_hotspot_trajectories` draw whose two spots are well separated -- 12.6
azimuthal cells and 5.7 M radially, so this is not the near-tie that an earlier
version of this label got wrong -- but whose angular rates differ by a factor of
three. The faster spot sweeps about 2.5 azimuthal cells inside the declared 3 M
probe window, and the peak of the smeared arc lands about 1.2 cells from the
generative centre.

So the extractor is not misreading the field. The generative *label* for a
multi-feature family is imprecise: it names the declared centres, and for a
feature that moves appreciably within the probe window the peak of the windowed
field is not at the centre the window is centred on.

**This was not repaired, deliberately.** The threshold is sealed and item 8 of
the ruling forbids changing a tolerance. The label could be made exact -- the
generative reference for any family is the argmax of the analytic windowed
field, which is computable and would remove the family-specific candidate logic
entirely -- but that change would have been made after seeing the held-out
bank, which is tuning until the gate goes green. Having a principled
justification for such a change makes it more dangerous, not less. The run was
executed exactly as sealed and reports what it gives.

## Deviation on this freeze

Recorded in full in `HMT1_SEALED_MAIN_BANK_V1_RETIREMENT_016`. Stage B was
smoke tested on the first sealed bank, which is an operator evaluation on
held-out truths and therefore a peek, however small. That bank was retired and
redrawn under a new seed rather than defended, and the runner gained a scratch
mode that draws a throwaway bank and writes nothing canonical -- which is what
the smoke test should have used. Run against a substituted bank it fails
`HMT1M_G2` and `HMT1M_G16` exactly as it should, which is the first
demonstration that the seal check can fail.

That smoke run also falsified `HMT1M_G15` as originally written. It required
the noiseless control to score a lower endpoint error than the noisy draws;
with the sealed hyperparameters the feature error is bias dominated rather than
noise dominated, so removing the noise barely moves it. The gate now measures
what it was for -- that the noise path is live -- in the reconstruction rather
than in the endpoint, and the endpoint direction is reported below and not
gated, because no correct direction for it was established in advance.

## Controls, which carry no endpoint information

Held-out bank: {len(banks):,} truths, worst azimuthal mean
{banks.azimuthal_mean_max_abs.max():.2e}, most negative total emissivity
{banks.min_total.min():.3f}, local contrast
{banks.peak_fraction_of_background.min():.2f} to
{banks.peak_fraction_of_background.max():.2f} of the local background. Zero
overlap with the validation seeds.

Background error by regime:

| regime | median relative | worst |
|---|---|---|
{bgtab}

Noise path, as displacement between the noisy and noiseless reconstructions
relative to the noiseless one:

| regime | arm | estimator | median displacement | noiseless endpoint lower |
|---|---|---|---|---|
{nct}

Null-pair controls: worst realized-versus-target separation error
{nulls.relative_error.max():.2e} over {len(nulls):,} near-null feature pairs.

## Open gap, not closed here

The validation freeze declares a `NONNEGATIVE_CONSTRAINED` control estimator,
scoped to the primary SNR and the estimated-background regime, which the
validation never implemented. It has no sealed hyperparameter because it was
never selected, and choosing one now is the selection item 8 forbids. It is
left unimplemented and reported rather than smuggled in behind a prohibited
selection. It needs a ruling.

## What a corrected rerun would need

A ruling on one question: may the `HMT1M_G10b` generative label be redefined as
the argmax of the analytic windowed field, for every family, before the sealed
main is re-executed on the same untouched bank. That is a change to how the
truth is *labelled*, not to the tolerance, the endpoint, the estimators, the
hyperparameters or the family set, all of which stay sealed. If the answer is
no, the alternative reading is that this bank contains one truth the declared
extraction procedure cannot label to within its own grid, and the run stands as
a defect.

**STOP.** No further stage is authorized. Order leakage, geometry mismatch,
VLBI, machine learning and a new pixel-movie reconstruction campaign all remain
unauthorized, and the R1L stop and its sealed commitments are untouched.
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
        "science_reading_withheld": withheld,
        "authoritative_attestation": "execution",
        "execution_attestation": att,
        "report_assembly_attestation": attest([FZ, RET]),
        "freeze_sha256": sha256_file(FZ),
        "retirement_record_sha256": sha256_file(RET),
        "inputs": {p: sha256_file(ROOT / p) for p in inputs},
        "outputs": {str(OUT.relative_to(ROOT)): sha256_file(OUT)},
    }, indent=2, default=str) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}\nwrote {PROV.relative_to(ROOT)}")
    print(f"  disposition: {token}  withheld: {withheld}")
    print(f"total {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
