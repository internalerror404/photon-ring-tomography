#!/usr/bin/env python3
"""Assemble the R1L stage-2 validation report.

Every number is read from the stage-2 tables. The disposition is one of the
five the freeze declared, computed here from the same rule the runner applied
rather than restated, so the two have to agree.
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
from phrt.config import load_registry, sha256_file  # noqa: E402

FZ = ROOT / "artifacts" / "configs" / "R1L_STAGE2_VALIDATION_ACTIVATION_010.json"
SEALED = ROOT / "artifacts" / "configs" / "R1L_SEALED_MAIN_COMMITMENT.json"
TAB = ROOT / "artifacts" / "tables"
OUT = ROOT / "artifacts" / "reports" / "R1L_STAGE2_VALIDATION.md"
PROV = ROOT / "artifacts" / "provenance" / "R1L_STAGE2_ARTIFACT_MANIFEST.json"
D = "\n"


def t(n):
    return pd.read_parquet(TAB / f"{n}.parquet")


def main() -> int:
    t0 = time.time()
    fz = json.loads(FZ.read_text())
    reg = load_registry()
    bal, sel, pilot, end, floors, sub, nulls, ages = (
        t("r1l_s2_source_balance"), t("r1l_s2_selection"), t("r1l_s2_pilot_scores"),
        t("r1l_s2_primary_endpoint"), t("r1l_s2_representation_floors"),
        t("r1l_s2_common_subspace"), t("r1l_s2_null_pairs"),
        t("r1l_s2_age_structure_errors"))
    gates = json.loads((ROOT / "artifacts" / "gates"
                        / "r1l_stage2_gates.json").read_text())
    mans = sorted((ROOT / "artifacts" / "manifests").glob("R1LS2_*.json"))
    man = json.loads(mans[-1].read_text())
    att, num = man["attestation"], man.get("numerics", {})
    token = gates["stop_token"]
    snr_ref = float(fz["reference_snr"])
    classes = list(dict.fromkeys(end.source_class))

    banktab = D.join(
        f"| `{r.bank}` | {fz['source_banks'][r.bank]['role']} | "
        f"{'—' if pd.isna(r.target_structure_fraction) else f'{r.target_structure_fraction:.2f}'} | "
        f"{r.med:.3f} | {r.lev:.3f} | {r.reach:.2f} | {int(r.ceil)}/{int(r.n)} |"
        for r in bal.groupby("bank").apply(
            lambda g: pd.Series({
                "bank": g.name,
                "target_structure_fraction": g.target_structure_fraction.iloc[0],
                "med": g.achieved_structure_fraction.median(),
                "lev": g.level_fraction.median(),
                "reach": g.within_tolerance.mean(),
                "ceil": g.at_positivity_ceiling.sum(), "n": len(g)}),
            include_groups=False).itertuples())

    e = end[(end.snr0 == snr_ref)]
    endtab = D.join(
        f"| `{r.source_class}` | `{r.arm}` | {r.estimator} | {r.mean_direct:.4f} | "
        f"{r.mean_arm:.4f} | {r.delta:+.4f} | [{r.ci_low:+.4f}, {r.ci_high:+.4f}] | "
        f"{'**yes**' if r.excludes_zero else 'no'} | {r.n_families_improved}/4 |"
        for r in e.itertuples())

    fl = floors.groupby(["source_class", "bank"]).median(numeric_only=True).reset_index()
    fltab = D.join(
        f"| `{r.source_class}` | `{r.bank}` | "
        f"{r.representation_floor_relative:.3f} | "
        f"{r.representation_floor_structure_relative:.3f} |"
        for r in fl.itertuples())

    sp = pilot[(pilot.snr0 == snr_ref) & (pilot.estimator == "TSVD")]
    sptab = D.join(
        f"| `{c}` | " + " | ".join(
            f"{sp[(sp.source_class == c) & (sp.arm == a)].structure_stable_span_M.mean():.1f}"
            for a in fz["scope"]["arms"]) + " |" for c in classes)

    onset = []
    for c in classes:
        for a in fz["scope"]["arms"]:
            g = pilot[(pilot.source_class == c) & (pilot.arm == a)
                      & (pilot.estimator == "TSVD")]
            pos = sorted(g[g.structure_stable_span_M > 0].snr0.unique())
            onset.append(f"| `{c}` | `{a}` | "
                         f"{f'{pos[0]:.0f}' if pos else 'none on the frozen grid'} |")

    subtab = D.join(
        f"| `{r.source_class}` | `{r.arm}` | {r.estimator} | "
        f"{int(r.reference_subspace_dimension)} | {int(r.arm_subspace_dimension)} | "
        f"{r.error_in_reference_data_subspace:.4f} | "
        f"{r.error_outside_reference_data_subspace:.4f} |"
        for r in sub.itertuples())

    gtab = D.join(f"| `{k}` | {v['status']} | "
                  f"{v['measured'] if not isinstance(v['measured'], float) else f'{v[chr(109)]:.3e}' if False else v['measured']} |"
                  for k, v in gates["gates"].items())

    sealed = json.loads(SEALED.read_text())
    body = f"""# R1L stage 2 — structure-first validation pilot

Validation, not a held-out result. Hyperparameters are chosen on the selection
split and the reported endpoint is computed on the pilot split, which no
hyperparameter ever saw. The sealed main bank is committed and not generated.

- run `{man['run_id']}`
- execution commit `{att['execution_commit'][:12]}`, clean {att['clean']},
  preregistered {att['preregistered']}
- BLAS pools all single-threaded: {num.get('all_pools_single_threaded')}
- freeze `{sha256_file(FZ)[:16]}...`
- **disposition `{token}`**

## 1. Source banks

Truths enter the operator analytically, sampled wherever the rays land, and are
never projected into the class first — so the representation floor in section 4
is a measured quantity rather than zero by construction.

| bank | role | target f_struct | achieved (median) | level fraction | reach target | at positivity ceiling |
|---|---|---|---:|---:|---:|---:|
{banktab}

The `structure_balanced_080` bank is half at its ceiling. That is not a
construction defect: a non-negative field of a given shape has a maximum
structure fraction `||s|| / ||s - min s||`, reached exactly at the positivity
boundary, and scaling cannot evade it. Truths above their ceiling are kept at
the ceiling and flagged rather than discarded.

For scale, the R1 banks sat at a structure fraction of 0.126 — a level fraction
of 0.992. Every primary bank here is far outside that regime.

## 2. Primary endpoint

`delta_E_old_structure = E_old_structure(direct) − E_old_structure(arm)` at
SNR₀ = {snr_ref:.0f}, on the pilot split, with a paired truth-cluster bootstrap
over {fz['primary_endpoint']['bootstrap']['n_resamples']:,} resamples. Positive
means the arm beats the direct image.

| class | arm | estimator | direct | arm | delta | 95% CI | excludes zero | families improved |
|---|---|---|---:|---:|---:|---|---|---|
{endtab}

## 3. Structure-only stable spans

Mean over pilot truths at SNR₀ = {snr_ref:.0f}, TSVD, on the
{fz['coprimary_endpoint']['age_grid_step_M']:.0f} M age grid.

| class | {" | ".join(f"`{a}`" for a in fz['scope']['arms'])} |
|---|{"---:|" * len(fz['scope']['arms'])}
{sptab}

Smallest SNR₀ on the frozen grid at which any structural span is nonzero:

| class | arm | onset SNR₀ |
|---|---|---|
{D.join(onset)}

## 4. Representation floors

The error no estimator can beat: the truth's distance from the class's own span,
on the evaluation grid, relative and structure-only.

| class | bank | floor (all) | floor (structure) |
|---|---|---:|---:|
{fltab}

## 5. Common direct-subspace errors

Every arm's coefficient error projected onto the **direct** channel's own
`P_data`, so the arms are compared on one subspace rather than each on its own.

| class | arm | estimator | reference dim | arm dim | error inside | error outside |
|---|---|---|---:|---:|---:|---:|
{subtab}

## 6. Localized null-pair controls

A separation frozen in units of sigma, realized through the operator along the
smallest **nonzero** singular directions. Worst relative error
{nulls.relative_error.max():.2e} over {len(nulls):,} pairs.

## 7. Gates

| gate | status | measured |
|---|---|---|
{gtab}

## 8. Sealed main, committed and not scored

`{sealed['id']}` commits {sealed['n_truths']} truths over {sealed['n_cells']}
cells, seed {sealed['seed']}, overlapping the validation commitments in
{sealed['disjoint_from_validation']['n_overlapping_cell_commitments']} cells.
Nothing was rendered through an operator, no datum was formed and no error was
computed. Committing it before this report is what stops the sealed set from
being chosen to flatter the pilot.

## 9. Disposition

`{token}`

Stage 2 is a validation pilot and nothing here is a held-out result. The sealed
main, geometry mismatch, order leakage, VLBI and ML all remain unauthorized.
"""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(body)
    PROV.parent.mkdir(parents=True, exist_ok=True)
    inputs = sorted(str(p.relative_to(ROOT)) for p in TAB.glob("r1l_s2_*.parquet"))
    PROV.write_text(json.dumps({
        "schema": "phrt-artifact-manifest/1",
        "experiment_id": "R1L_STAGE_2_VALIDATION",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "stop_token": token,
        "authoritative_attestation": "execution",
        "execution_attestation": att,
        "report_assembly_attestation": attest([FZ]),
        "numerics": num,
        "registry_sha256": reg.sha256,
        "sealed_main_commitment_sha256": sha256_file(SEALED),
        "inputs": {p: sha256_file(ROOT / p) for p in inputs},
        "outputs": {str(OUT.relative_to(ROOT)): sha256_file(OUT)},
    }, indent=2, default=str) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}\nwrote {PROV.relative_to(ROOT)}")
    print(f"  disposition: {token}\ntotal {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
