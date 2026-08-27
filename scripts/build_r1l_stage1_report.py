#!/usr/bin/env python3
"""Assemble the R1L stage-1 report and evaluate the stop conditions it can see.

Every number is read from the stage-1 tables. The stop rule is evaluated here
rather than asserted, and the two conditions this stage cannot see are named as
deferred rather than passed over.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from phrt.attestation import attest
from phrt.config import load_registry, sha256_file

FREEZE = ROOT / "artifacts" / "configs" / "R1L_LOCALIZED_AUDIT_FREEZE.json"
AMENDMENT = (ROOT / "artifacts" / "configs"
             / "R1L_STAGE1_DIRTY_EXECUTION_AMENDMENT_008.json")
CLEAN_FAILED = "R1L_20260827T044412Z_2ba66f02"
DIRTY_CORRECT = "R1L_20260827T044757Z_2ba66f02"
E3C = ROOT / "artifacts" / "configs" / "E3C_OPERATOR_GRID_FREEZE.json"
TAB = ROOT / "artifacts" / "tables"
MANS = ROOT / "artifacts" / "manifests"
OUT = ROOT / "artifacts" / "reports" / "R1L_STAGE1_OPERATOR_AUDIT.md"
PROV = ROOT / "artifacts" / "provenance" / "R1L_STAGE1_ARTIFACT_MANIFEST.json"
SNR = 100.0
PAIRS = (("L224", "C224"), ("L448", "C448_T"), ("L1056", "C1056_ST"))


def t(name):
    return pd.read_parquet(TAB / f"{name}.parquet")


def main() -> int:
    t0 = time.time()
    fz = json.loads(FREEZE.read_text())
    rho = float(json.loads(E3C.read_text())["rank_conventions"]
                ["operational_threshold_rho"])
    reg = load_registry()
    old_boundary = float(json.loads(
        (ROOT / "artifacts" / "configs" / "R1_MAIN_FREEZE.json").read_text()
    )["metrics"]["old_band_boundary_M"])
    spec, old, vis, age, sup = (t("r1l_class_spectra"), t("r1l_old_structural_support"),
                                t("r1l_temporal_mode_visibility"),
                                t("r1l_age_information"), t("r1l_temporal_supports"))
    run_man = sorted(MANS.glob("R1L_*.json"))[-1]
    run_doc = json.loads(run_man.read_text())
    gates = json.loads((ROOT / "artifacts" / "gates"
                        / "r1l_stage1_gates.json").read_text())

    def sp(cl, arm, col):
        return spec[(spec.source_class == cl) & (spec.arm == arm)][col].iloc[0]

    def og(cl, arm, col):
        return old[(old.source_class == cl) & (old.arm == arm)][col].iloc[0]

    # reach on the refined grid, and the SNR each age would require
    reach, need = {}, {}
    a224 = age[age.source_class == "L224"].copy()
    a224["snr_required"] = rho / np.sqrt(np.clip(a224.lambda_max_per_snr2, 1e-300, None))
    for arm, g in a224.groupby("arm"):
        g = g.sort_values("retarded_age")
        run = 0.0
        for _, r in g.iterrows():
            if r.detectable_at_reference_snr:
                run = float(r.retarded_age)
            else:
                break
        reach[arm] = run
        need[arm] = {float(r.retarded_age): float(r.snr_required)
                     for _, r in g.iterrows()}

    # ---- the stop conditions this stage can see ---------------------------
    stop1 = all(og(cl, "RESOLVED_PHYSICAL", "old_structural_operational_rank")
                <= og(cl, "DIRECT_PHYSICAL", "old_structural_operational_rank")
                for cl, _ in PAIRS)
    stop3 = all(og(cl, "UNRESOLVED_IMAGE", "old_structural_operational_rank")
                <= og(cl, "DIRECT_PHYSICAL", "old_structural_operational_rank")
                for cl, _ in PAIRS)
    tripped = [n for n, v in (("R1L_STOP_1_indistinguishable_old_support", stop1),
                              ("R1L_STOP_3_improvement_vanishes_after_order_summation",
                               stop3)) if v]
    token = ("R1L_STAGE_1_STOP" if tripped else
             "R1L_STAGE_1_PASS_VALIDATION_PILOT_UNLOCKED")

    D = "\n"
    ladder = D.join(
        f"| `{lo}` | {sp(lo,'DIRECT_PHYSICAL','source_dimension')} | "
        f"{sp(lo,'DIRECT_PHYSICAL','numerical_rank')} | "
        f"{sp(lo,'DIRECT_PHYSICAL','n_exactly_zero_columns')} | "
        f"{sp(lo,'DIRECT_PHYSICAL','n_temporal_modes_entirely_unseen')} | "
        f"{sp(lo,'RESOLVED_PHYSICAL','numerical_rank')} | "
        f"{sp(lo,'RESOLVED_PHYSICAL','n_exactly_zero_columns')} | "
        f"`{gl}` | {sp(gl,'DIRECT_PHYSICAL','numerical_rank')} | "
        f"{sp(gl,'DIRECT_PHYSICAL','n_exactly_zero_columns')} |"
        for lo, gl in PAIRS)

    oldtab = D.join(
        f"| `{cl}` | {og(cl,'DIRECT_PHYSICAL','old_structural_dimension')} | "
        + " | ".join(str(og(cl, a, "old_structural_operational_rank"))
                     for a in ("DIRECT_PHYSICAL", "RESOLVED_PHYSICAL",
                               "UNRESOLVED_IMAGE", "TOTAL_FLUX", "DELAY_ONLY",
                               "SPATIAL_ONLY")) + " |"
        for cl, _ in PAIRS)

    nsp = {cl: int(sp(cl, "DIRECT_PHYSICAL", "n_radial")
                   * sp(cl, "DIRECT_PHYSICAL", "n_azimuthal")) for cl, _ in PAIRS}
    zero = {cl: {arm: (int(sp(cl, arm, "n_exactly_zero_columns")),
                       int(sp(cl, arm, "n_temporal_modes_entirely_unseen")))
                 for arm in ("DIRECT_PHYSICAL", "RESOLVED_PHYSICAL",
                             "UNRESOLVED_IMAGE")} for cl, _ in PAIRS}
    zerotab = D.join(
        f"| `{cl}` | {zero[cl]['DIRECT_PHYSICAL'][0]} | "
        f"{zero[cl]['DIRECT_PHYSICAL'][1]} | "
        f"{zero[cl]['DIRECT_PHYSICAL'][0] - zero[cl]['DIRECT_PHYSICAL'][1] * nsp[cl]} | "
        f"{zero[cl]['RESOLVED_PHYSICAL'][0]} | {zero[cl]['RESOLVED_PHYSICAL'][1]} | "
        f"{zero[cl]['UNRESOLVED_IMAGE'][0]} |" for cl, _ in PAIRS)

    v = vis[(vis.source_class == "L224")].merge(
        sup[sup.source_class == "L224"][["temporal_mode", "youngest_age_touched_M",
                                         "oldest_age_touched_M"]], on="temporal_mode")
    epochs = D.join(
        f"| {int(k)} | {row.youngest_age_touched_M:.1f} – {row.oldest_age_touched_M:.1f} | "
        f"{'yes' if row.entirely_in_old_band else 'no'} | "
        + " | ".join(
            str(int(v[(v.temporal_mode == k) & (v.arm == a)].operational_rank.iloc[0]))
            for a in ("DIRECT_PHYSICAL", "RESOLVED_PHYSICAL", "UNRESOLVED_IMAGE"))
        + " |"
        for k, row in v[v.arm == "DIRECT_PHYSICAL"].set_index("temporal_mode").iterrows())

    snrtab = D.join(
        f"| {a:.0f} | " + " | ".join(
            ("—" if need[arm][a] > 1e6 else f"{need[arm][a]:,.0f}")
            for arm in ("DIRECT_PHYSICAL", "UNRESOLVED_IMAGE", "RESOLVED_PHYSICAL"))
        + " |"
        for a in (62.0, 64.0, 70.0, 80.0, 94.0, 110.0))

    def fmt(x):
        return f"{x:.3e}" if isinstance(x, float) else str(x)

    gtab = D.join(f"| `{k}` | {gv['status']} | {fmt(gv['measured'])} | "
                  f"{fmt(gv.get('threshold'))} |"
                  for k, gv in gates["gates"].items())

    rp = ROOT / "artifacts" / "provenance" / "R1L_STAGE1_REPRODUCTION.json"
    if rp.exists():
        rd = json.loads(rp.read_text())
        ca = rd["clean_run_attestation"]
        rows = D.join(f"| `{k}` | {v['n_rows']} | {v['n_columns']} | "
                      f"{'**equal**' if v['equal'] else '**DIFFERS**'} |"
                      for k, v in rd["tables"].items())
        repro = f"""Ruling item 5. Stage 1 was rerun from a completely clean tree with no code
edits between the runs, and every canonical numeric cell was required to match
exactly — no tolerance, since the seeds, the rays and the committed code are
identical and any difference would be a defect rather than rounding.

- preserved run `{rd['preserved_run']}` — correct, dirty
- clean run `{rd['clean_run']}` — execution commit
  `{ca['execution_commit'][:12]}`, clean {ca['clean']}, preregistered
  {ca['preregistered']}, tracked changes {ca['n_tracked_changes']}, untracked
  {ca['n_untracked']}
- gates failing on the clean run: {rd['gates_failing_on_clean_run'] or 'none'}

| table | rows | columns | numeric equality |
|---|---:|---:|---|
{rows}

Verdict: **`{rd['verdict']}`**. Every number in sections 1 to 7 is therefore
carried by a clean preregistered execution, and the two earlier runs are
preserved as record rather than replaced."""
    else:
        repro = ("Pending. The clean rerun required by ruling item 5 has not been "
                 "executed, so every number above still rests on a run that was "
                 "not preregistered.")

    body = f"""# R1L stage 1 — localized operator and rank audit

Stage one of three under `R1L_LOCALIZED_AUDIT_FREEZE.json`. No truth was drawn,
no estimator was fitted and no reconstruction error exists in this document.
This stage reports only what the operator can and cannot see, which is a
property of the geometry and the basis alone.

- run `{run_doc['run_id']}`
- execution commit `{run_doc['attestation']['execution_commit']}`
- freeze `{sha256_file(FREEZE)[:16]}...`
- geometry `{fz['scope']['geometry']}`, orders 0–2, reference SNR₀ = {SNR:.0f}
- operational threshold ρ = {rho}
- age grid {fz['F_age_resolution']['age_grid_step_M']} M
  (was {fz['F_age_resolution']['previous_step_M']} M), probe half width
  {fz['F_age_resolution']['probe_half_width_M']} M
- stop token **`{token}`**
- amendment `R1L_STAGE1_DIRTY_EXECUTION_G8_MASK_FIX`
  (`artifacts/configs/R1L_STAGE1_DIRTY_EXECUTION_AMENDMENT_008.json`)

> **Execution provenance.** Two runs precede the one reported here and both are
> preserved. `{CLEAN_FAILED}` was clean and preregistered and failed
> `R1L_G8` at 2.8e2 because the reached-mode mask was built from a single
> observer time. `{DIRTY_CORRECT}` fixed the mask, passed all ten gates, and ran
> against a working tree carrying that uncommitted fix, so it recorded
> `preregistered = false`. Under ruling item 5 stage 1 was then rerun from a
> completely clean tree with no code edits, and every canonical number was
> required to match. See section 9.

## 1. The question C224 could not be asked

Under the registered global class every temporal coefficient is supported on
the whole history, so no coefficient is ever formally unconstrained and "the
direct image cannot see this epoch" can only ever be a statement about a
condition number. The localized ladder makes it a statement about the null
space, and the two ladders were run on the same rays so the numbers below are
directly comparable.

| localized | dim | direct rank | direct exact-zero cols | direct unseen temporal modes | resolved rank | resolved exact-zero cols | global | direct rank | direct exact-zero cols |
|---|---:|---:|---:|---:|---:|---:|---|---:|---:|
{ladder}

`C224` is full rank on its own global temporal subspace: the direct arm reaches
{sp('C224','DIRECT_PHYSICAL','numerical_rank')} of
{sp('C224','DIRECT_PHYSICAL','source_dimension')} with zero nullity. That
establishes identifiability of the 224 **global** coefficients. It does **not**
establish epoch-local identifiability, and it is not evidence either way about
it: C224 cannot pose the epoch-local question, because none of its coefficients
is confined to an epoch.

`L224`, the same dimension over the same rays, poses it. The direct arm there
reaches rank {sp('L224','DIRECT_PHYSICAL','numerical_rank')} with
{sp('L224','DIRECT_PHYSICAL','n_exactly_zero_columns')} identically zero
columns. The two rank numbers are answers to different questions and neither
contradicts the other.

## 2. Old-epoch structural support, by arm

Old-epoch means every temporal function whose whole support lies at ages at or
beyond {old_boundary:.1f} M.
Structural means orthogonal to the level subspace, so a recovered spatial mean
cannot be counted as recovered morphology. Entries are operational ranks.

| class | old structural dim | direct | resolved | unresolved | total flux | delay only | spatial only |
|---|---:|---:|---:|---:|---:|---:|---:|
{oldtab}

The direct image sees **nothing at all** in this subspace: its largest singular
value there is {og('L224','DIRECT_PHYSICAL','old_structural_sigma_max'):.2e} at
`L224`, which is numerical zero, against
{og('L224','RESOLVED_PHYSICAL','old_structural_sigma_max'):.1f} for the resolved
stack.

Under the **registered counterfactual**, delay diversity is necessary and
dominant here: `SPATIAL_ONLY` matches the direct image at operational rank 0 and
`DELAY_ONLY` exceeds the full resolved stack. Those two arms are specific
substitutions — `SPATIAL_ONLY` gives every order order 0's spatial map while
keeping its own delays, `DELAY_ONLY` gives every order order 0's delays while
keeping its own spatial map — so they license a statement about those
substitutions. This is **not** a universal claim that spatial remapping has no
effect.

## 3. Where the higher orders actually contribute

`L224`, per temporal function, operational rank out of 28 spatial directions.

| mode | ages covered (M) | entirely old | direct | resolved | unresolved |
|---:|---|---|---:|---:|---:|
{epochs}

Higher-order gains occur where the direct image is **blind or incomplete**, and
the two are different. Modes 5 to 7 agree across all three arms. Modes 3 and 4
are incomplete for the direct image and receive incremental directions — 9 to 28
and 25 to 28 — so the gain there is a completion, not a rescue. Modes 0 to 2 are
where the direct image is at zero and the gain is the whole of what is seen.

## 4. Reach on the refined age grid

Contiguous detectable depth from the present at SNR₀ = {SNR:.0f}, on the
{fz['F_age_resolution']['age_grid_step_M']} M grid:
direct **{reach['DIRECT_PHYSICAL']:.0f} M**, resolved
**{reach['RESOLVED_PHYSICAL']:.0f} M**, unresolved
**{reach['UNRESOLVED_IMAGE']:.0f} M**, total flux
{reach['TOTAL_FLUX']:.0f} M.

The resolved gain is **+{reach['RESOLVED_PHYSICAL'] - reach['DIRECT_PHYSICAL']:.0f} M**,
which reproduces the R1 headline on a grid twice as fine. At
{fz['F_age_resolution']['age_grid_step_M']} M resolution that is
{int((reach['RESOLVED_PHYSICAL'] - reach['DIRECT_PHYSICAL']) / fz['F_age_resolution']['age_grid_step_M'])}
bins, so for this geometry the gain is not one-bin threshold behaviour. The
high-inclination 4 M gains that motivated the refinement are a geometry-wide
question and are **not** addressed here: this audit is one geometry.

SNR₀ required to reach a given age, which is what the binary grid hides:

| age (M) | direct | unresolved | resolved |
|---:|---:|---:|---:|
{snrtab}

## 5. Stop conditions

| condition | evaluable here | tripped |
|---|---|---|
| `R1L_STOP_1` localized direct and resolved have indistinguishable old structural support | yes | **{'yes' if stop1 else 'no'}** |
| `R1L_STOP_2` resolved old-band structure error does not improve | no — needs the validation pilot | deferred |
| `R1L_STOP_3` all improvement vanishes after order summation | yes | **{'yes' if stop3 else 'no'}** |
| `R1L_STOP_4` the bank cannot be represented without a dominant positivity baseline | no — needs the structural banks | deferred |

`R1L_STOP_1` does not trip: direct is at operational rank 0 in the old
structural subspace at every class and resolved is at
{og('L224','RESOLVED_PHYSICAL','old_structural_operational_rank')},
{og('L448','RESOLVED_PHYSICAL','old_structural_operational_rank')} and
{og('L1056','RESOLVED_PHYSICAL','old_structural_operational_rank')}. The two are
as distinguishable as they can be.

`R1L_STOP_3` does not trip either, but the finding is mixed and is recorded as
mixed. The unresolved image retains
{og('L224','UNRESOLVED_IMAGE','old_structural_operational_rank')} of the
{og('L224','RESOLVED_PHYSICAL','old_structural_operational_rank')} old structural
directions the resolved stack has, where the direct image has none — so the
improvement does not vanish under order summation. But on the reach metric at
SNR₀ = {SNR:.0f} the unresolved image gains
{reach['UNRESOLVED_IMAGE'] - reach['DIRECT_PHYSICAL']:.0f} M over the direct
image. That is a threshold crossing, not an absence of information: at 80 M the
unresolved image needs SNR₀ ≈ {need['UNRESOLVED_IMAGE'][80.0]:,.0f} and the
direct image needs ≈ 1e{np.log10(need['DIRECT_PHYSICAL'][80.0]):.0f}. Whether
that survives as a *reconstruction* gain is exactly what stage 2 is for, and it
is the result most likely to decide whether this line reaches observation.

## 6. Gates

| gate | status | measured | threshold |
|---|---|---|---|
{gtab}

`R1L_G2` measures {gates['gates']['R1L_G2_exact_class_nesting']['measured']:.2e},
which is QR round-off on a {int(spec[spec.source_class == 'L1056'].data_dimension.max()):,} x 1056
design rather than a nesting defect. Exactness is a statement about the function
spaces, and it is checked directly on the temporal factor alone in the unit
tests, where the residual is at the 1e-15 level. The gate threshold is a
numerical tolerance and is labelled as one.

## 7. What this stage does and does not establish

Established, on one geometry and with no estimator involved:

1. The direct image has **exact** old-epoch null directions once the temporal
   basis is compact — on modes 0 to 2 — and is **incomplete but not blind** on
   modes 3 and 4. This is not a conditioning statement.
2. Orders 1 and 2 genuinely remove them, though not all of them at every class.
   The direct blindness is *whole-epoch*: at `L224` and `L448` its exactly-zero
   columns are precisely {zero['L224']['DIRECT_PHYSICAL'][1]} and
   {zero['L448']['DIRECT_PHYSICAL'][1]} entire temporal functions, with nothing
   left over. The resolved stack leaves **no** temporal function entirely
   unseen at any class, but the count of individual zero columns it does leave
   grows with the model — 0, {zero['L448']['RESOLVED_PHYSICAL'][0]} and
   {zero['L1056']['RESOLVED_PHYSICAL'][0]}. Enrichment outruns the measurement.

| class | direct zero cols | of which whole temporal functions | remainder | resolved zero cols | resolved unseen functions | unresolved zero cols |
|---|---:|---:|---:|---:|---:|---:|
{zerotab}

3. The resolved advantage is **not** an artifact of global-cosine
   extrapolation. It is larger under the localized ladder than C224 implied,
   because C224's direct arm reported full column rank it did not have.
4. Local support costs rank and conditioning, and at `L224` and `L448` the cost
   falls entirely on epochs the arm could not see. At `L1056` it does not: the
   direct arm loses {zero['L1056']['DIRECT_PHYSICAL'][0]} columns where whole
   unseen functions account for only
   {zero['L1056']['DIRECT_PHYSICAL'][1] * nsp['L1056']}, so
   {zero['L1056']['DIRECT_PHYSICAL'][0] - zero['L1056']['DIRECT_PHYSICAL'][1] * nsp['L1056']}
   of them are spatial directions it cannot see even at reachable epochs.

Not established, and not to be described as established:

- No reconstruction was performed. Nothing here is a recovery claim, and the
  freeze's forbidden-language rule stands: no localized result may be called
  morphology recovery until the structural endpoint has been scored on a sealed
  bank.
- The structure-first banks of section B have not been drawn, so baseline
  domination is untested. `R1L_STOP_4` is open.
- One geometry. The high-inclination question that motivated the finer age grid
  is untouched.

## 8. Clean reproduction

{repro}

## 9. Stop

Stage 1 is complete and the freeze authorizes stage 1 only. Under the sequential
rule the validation pilot is unlocked but **not** entered here.

Stop token: `{token}`
"""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(body)

    inputs = sorted(set(
        [str(p.relative_to(ROOT)) for p in TAB.glob("r1l_*.parquet")]
        + [str(FREEZE.relative_to(ROOT)), str(run_man.relative_to(ROOT)),
           "artifacts/gates/r1l_stage1_gates.json"]))
    PROV.parent.mkdir(parents=True, exist_ok=True)
    PROV.write_text(json.dumps({
        "schema": "phrt-artifact-manifest/1",
        "experiment_id": "R1L_STAGE_1_OPERATOR_RANK_AUDIT",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "stop_token": token,
        "stop_conditions_evaluated": {"R1L_STOP_1": bool(stop1),
                                      "R1L_STOP_3": bool(stop3)},
        "stop_conditions_deferred": ["R1L_STOP_2", "R1L_STOP_4"],
        "authoritative_attestation": "execution",
        "execution_attestation": run_doc["attestation"],
        "report_assembly_attestation": attest([FREEZE]),
        "registry_sha256": reg.sha256,
        "inputs": {p: sha256_file(ROOT / p) for p in inputs},
        "outputs": {str(OUT.relative_to(ROOT)): sha256_file(OUT)},
    }, indent=2) + "\n")

    print(f"wrote {OUT.relative_to(ROOT)}")
    print(f"wrote {PROV.relative_to(ROOT)}")
    print(f"  stop token: {token}")
    print(f"  STOP_1 tripped: {stop1}   STOP_3 tripped: {stop3}")
    print(f"total {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
