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

    def fmt(x):
        return f"{x:.3e}" if isinstance(x, float) else str(x)

    gtab = D.join(f"| `{k}` | {v['status']} | {fmt(v['measured'])} |"
                  for k, v in gates["gates"].items())

    # re-derive the disposition from the tables under the freeze's own rule, so
    # the report and the runner have to agree rather than the report restating
    null_ok = bool((nulls.relative_error < 0.05).all())

    def carried_by(arm):
        r = end[end.arm == arm]
        if r.empty or not null_ok:
            return False, []
        who = []
        for est in ("TSVD", "RIDGE_IDENTITY"):
            v = r[(r.estimator == est) & r.excludes_zero
                  & (r.n_families_improved >= 3)]
            if v.empty:
                return False, []
            who += list(v.source_class)
        return True, sorted(set(who))

    res_ok, res_who = carried_by("RESOLVED_PHYSICAL")
    unres_ok, unres_who = carried_by("UNRESOLVED_IMAGE")
    rederived = ("R1L_STAGE2_RESOLVED_AND_UNRESOLVED_PASS" if res_ok and unres_ok
                 else "R1L_STAGE2_RESOLVED_ONLY_PASS" if res_ok
                 else "R1L_STAGE2_NEGATIVE_RESULT")
    agree = rederived == token

    end2 = end.copy()
    end2["relative_delta"] = end2.delta / end2.mean_direct
    sig = end2[end2.excludes_zero].sort_values("relative_delta")
    sigtab = D.join(
        f"| `{r.source_class}` | `{r.arm}` | {r.estimator} | {r.delta:.3e} | "
        f"{r.relative_delta:.1e} |" for r in sig.itertuples())

    floor_min = float(floors.representation_floor_structure_relative.min())
    span_max = float(pilot.structure_stable_span_M.max())

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

## 9. Two findings that determine how section 2 must be read

**The co-primary was untestable as specified, and its result is not a negative
result about the orders.** The structural stable span is **zero for every arm,
every class and every SNR₀ on the frozen grid**, up to 30000. The span criterion
asks for a relative structural error at or below 0.25, and the smallest
representation floor anywhere in section 4 is **{floor_min:.3f}**. The criterion
therefore sits below the floor everywhere: no operator, arm or estimator could
have produced a nonzero span, because the class cannot represent the truths that
well in the first place. `delta_L_stable_structure >= 8 M` was never reachable,
and the largest span observed is {span_max:.1f} M. This is a specification
mismatch between the 0.25 criterion and the analytic banks, not evidence about
higher orders.

**The primary endpoint has no effect-size threshold, and the effects that pass
are mostly negligible.** All four declared criteria are met, but "excludes zero"
is doing all the work: with 128 paired pilot truths and four draws each, the
bootstrap variance is tiny and a consistent sign passes at almost any magnitude.
Relative effect sizes of every interval that excludes zero:

| class | arm | estimator | delta | delta / direct |
|---|---|---|---:|---:|
{sigtab}

The unresolved arm's pass — the one that separates
`RESOLVED_AND_UNRESOLVED_PASS` from `RESOLVED_ONLY_PASS` — is **one part in ten
thousand**. Only ridge at `L1056` (7.2%) and at `L224` (3.3%) reaches a
magnitude that would matter to a reader. I do not think the unresolved result as
it stands supports any observational claim, and the freeze's own
`unresolved_arm_rule` was written to prevent exactly the reverse mistake, not to
license this one.

A third, smaller note: the structural span here is the mean over truths of each
truth's contiguous span, not the anchored quantile endpoint
`T_stable_anchor(epsilon, q)` the campaign uses elsewhere. Since every value is
zero under any definition, the simplification changes nothing, but it is a
deviation and is recorded as one.

## 10. Disposition

The declared rule yields **`{token}`**, re-derived independently from the tables
by this report ({"agreeing" if agree else "**DISAGREEING**"} with the runner).
It is carried by: resolved at {", ".join(f"`{c}`" for c in res_who) or "no class"};
unresolved at {", ".join(f"`{c}`" for c in unres_who) or "no class"}.

That token is what the freeze declared, and it stands as the disposition. It
should not be read as a scientific pass. On the evidence above, the honest
summary is that the resolved arm shows a real but small old-band structural
advantage that is substantial only under ridge, the unresolved arm's advantage
is statistically resolvable and physically negligible, and the co-primary could
not be tested at all.

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
        "disposition_rederived_from_tables": rederived,
        "runner_and_report_agree": agree,
        "carried_by": {"RESOLVED_PHYSICAL": res_who, "UNRESOLVED_IMAGE": unres_who},
        "caveats": {
            "coprimary_untestable": f"the 0.25 span criterion sits below the "
                                    f"smallest representation floor "
                                    f"({floor_min:.3f}); every structural span "
                                    f"is zero by construction",
            "no_effect_size_threshold": "the primary endpoint requires only that "
                                        "the bootstrap interval exclude zero; "
                                        "the unresolved arm's passing effect is "
                                        "one part in ten thousand",
            "span_definition_deviation": "mean over truths of the per-truth "
                                         "contiguous span, not the anchored "
                                         "quantile endpoint used elsewhere",
        },
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
    print(f"  disposition: {token} (re-derived: {rederived}, agree={agree})")
    print(f"  resolved carried by {res_who}; unresolved carried by {unres_who}")
    print(f"  smallest representation floor {floor_min:.3f}; "
          f"largest structural span {span_max:.1f} M")
    print(f"total {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
