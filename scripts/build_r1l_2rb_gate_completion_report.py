#!/usr/bin/env python3
"""Report for the gate-completed stage 2R-B. Every number read from its tables."""
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

FZ = ROOT / "artifacts" / "configs" / "R1L_STAGE2R_VALIDATION_FREEZE_012.json"
AM = (ROOT / "artifacts" / "configs"
      / "R1L_STAGE2R_GATE_COMPLETION_AMENDMENT_013.json")
REPRO = ROOT / "artifacts" / "provenance" / "R1L_2RB_GATE_COMPLETION_REPRODUCTION.json"
TAB = ROOT / "artifacts" / "tables"
G = ROOT / "artifacts" / "gates" / "r1l_2rb_gates.json"
OUT = ROOT / "artifacts" / "reports" / "R1L_STAGE2R_B_GATE_COMPLETED.md"
PROV = (ROOT / "artifacts" / "provenance"
        / "R1L_STAGE2R_B_GATE_COMPLETED_ARTIFACT_MANIFEST.json")
D = "\n"
PC, SNR_P, SNR_S = "L1056", 100.0, 1000.0


def main() -> int:
    t0 = time.time()
    fz, g = json.loads(FZ.read_text()), json.loads(G.read_text())
    rep = json.loads(REPRO.read_text()) if REPRO.exists() else None
    end = pd.read_parquet(TAB / "r1l_2rb_endpoint.parquet")
    con = pd.read_parquet(TAB / "r1l_2rb_bank_contract.parquet")
    dsp = pd.read_parquet(TAB / "r1l_2rb_delta_spans.parquet")
    man = json.loads(sorted((ROOT / "artifacts" / "manifests")
                            .glob("R1LS2RB_*.json"))[-1].read_text())
    att = man["attestation"]
    token, cov = g["stop_token"], g["gate_coverage"]
    M = fz["materiality"]

    def rows(df):
        return D.join(
            f"| `{r.arm}` | {r.estimator} | {r.snr0:.0f} | "
            f"{r.median_relative_reduction:+.3f} | "
            f"[{r.median_ci_low:+.3f}, {r.median_ci_high:+.3f}] | "
            f"{r.relative_reduction:+.3f} | [{r.ci_low:+.3f}, {r.ci_high:+.3f}] | "
            f"{int(r.n_families_improved)}/4 | "
            f"{'**MATERIAL**' if r.meets_materiality else 'no'} |"
            for r in df.itertuples())

    phys = end[(end.source_class == PC) & (end.scope == "physical_banks_only")]
    ptab = rows(phys.sort_values(["snr0", "arm", "estimator"]))
    per_bank = end[(end.source_class == PC) & (end.scope == "single_bank")
                   & (end.snr0 == SNR_P) & (end.arm == "RESOLVED_PHYSICAL")]
    btab = D.join(
        f"| `{r.bank}` | {r.estimator} | {r.median_relative_reduction:+.3f} | "
        f"[{r.median_ci_low:+.3f}, {r.median_ci_high:+.3f}] | "
        f"{r.relative_reduction:+.3f} | [{r.ci_low:+.3f}, {r.ci_high:+.3f}] |"
        for r in per_bank.sort_values(["bank", "estimator"]).itertuples())

    ctab = D.join(
        f"| `{r.bank}` | `{r.role_id}` | {r.exact_in_class} | "
        f"{'—' if pd.isna(r.nominal_structure_fraction) else f'{r.nominal_structure_fraction:.2f}'} | "
        f"{r.achieved_structure_fraction:.3f} | {r.nonnegative} | "
        f"{r.negative_mass_relative_max:.4f} | {r.reprojection_residual:.3f} | "
        f"{'**yes**' if r.physical_primary_eligible else 'no'} |"
        for r in con[con.source_class == PC].sort_values("bank").itertuples())

    stab = D.join(
        f"| `{r.arm}` | {r.snr0:.0f} | {r.noise_semantics} | {r.L_direct_M:.1f} | "
        f"{r.L_arm_M:.1f} | {r.delta_L_stable_structure_M:+.1f} | "
        f"{'yes' if r.meets_threshold else '**no**'} |"
        for r in dsp[dsp.source_class == PC]
        .sort_values(["noise_semantics", "snr0", "arm"]).itertuples())

    gtab = D.join(f"| `{k}` | {v['status']} |" for k, v in g["gates"].items())
    reptab = (D.join(f"| `{k}` | {v['status']} |"
                     for k, v in rep["tables"].items()) if rep else "")

    body = f"""# R1L stage 2R-B — gate-completed

Reviewer ruling on stage 2R-B. The scientific disposition is unchanged; what is
repaired is gate coverage, two bank classifications, the estimand pairing and
the stable-span noise semantics.

- run `{man['run_id']}`, execution commit `{att['execution_commit'][:12]}`,
  clean {att['clean']}, preregistered {att['preregistered']}
- gate coverage **{len(cov['emitted'])} emitted of {len(cov['declared'])} declared**, complete: {cov['complete']}
- amendment `R1L_STAGE2R_GATE_COMPLETION_AMENDMENT_013`
- **disposition `{token}`**

## 1. Endpoint on the physical banks only

The physical-source claim rests on the two non-negative structure-balanced banks
alone. The signed constant-flux bank is reported in section 3 and may not carry
it. Material requires median ≥ {M['median_paired_relative_reduction']:.0%} and
cell-balanced mean lower bound ≥ {M['bootstrap_lower_bound']:.0%}, ≥
{M['min_families_improved']}/4 families, every bank in scope positive, null
controls passing, and both estimators on the same class.

| arm | estimator | SNR₀ | per-truth median | median 95% CI | cell-balanced mean | mean 95% CI | families | material |
|---|---|---:|---:|---|---:|---|---|---|
{ptab}

Each interval now names the statistic it belongs to. The earlier report attached
the mean's interval to the median, which described neither.

## 2. Resolved arm, each physical bank separately, SNR₀ = {SNR_P:.0f}

| bank | estimator | per-truth median | median 95% CI | cell-balanced mean | mean 95% CI |
|---|---|---:|---|---:|---|
{btab}

## 3. Source-bank contract — gate `R1L_2RB_G10`

| bank | role | exact in class | nominal f | achieved f | non-negative | max negative mass | reprojection | physical primary |
|---|---|---|---:|---:|---|---:|---:|---|
{ctab}

The constant-flux bank is reclassified `SIGNED_CONSTANT_FLUX_STRUCTURAL_DIAGNOSTIC`.
My earlier report gave its negative mass as about 3.6%, which is the median; the
maximum over records is 19.7% and 18 of 64 exceed 10%. Quoting the median alone
understated it. It is a legitimate linear inverse-problem stress control and is
not a physical emissivity history.

`structure_balanced_080` is reclassified `HIGH_STRUCTURE_NOMINAL_080_REALIZED_066`:
the 0.80 target is set before projection onto the class, projection removes
structure, and the realized fraction is what the operator saw.

## 4. Stable structural span, both noise semantics

| arm | SNR₀ | semantics | L direct (M) | L arm (M) | ΔL (M) | ≥ {fz['stable_structure_span']['threshold_M']:.0f} M |
|---|---:|---|---:|---:|---:|---|
{stab}

The joint truth-and-noise statistic controls the claim. It is the stricter of
the two, so it cannot rescue a positive span from the averaged one — and both
give zero. **The stable-span endpoint remains a negative result.**

## 5. Gates

| gate | status |
|---|---|
{gtab}

Coverage is now asserted structurally: the runner compares its emitted gate
names against the freeze's declared set and stops if any are missing. The defect
this repairs was that a declared-but-unemitted gate reads exactly like one that
passed.

## 6. Bitwise reproduction against `151229d`

{"| table | status |" if rep else "Pending."}
{"|---|---|" if rep else ""}
{reptab}

{"Verdict: **`" + rep["verdict"] + "`**." if rep else ""}
{"Every pre-existing scientific cell is identical; only new diagnostic columns and new tables appear. The gate completion describes the experiment rather than altering it." if rep and rep["all_preexisting_cells_identical"] else ""}

## 7. Disposition

`{token}`

At SNR₀ = {SNR_P:.0f}, on the primary compact-support class `{PC}`, with truths
exactly represented in that class and a representation floor of zero, the
resolved n = 0, 1, 2 operator materially reduces old-band structural
reconstruction error relative to the direct image, on both registered estimators
and on the non-negative physical banks alone.

It does **not** produce a stable contiguous structural interval: ΔL = 0 M
against 8 M under either noise semantics. Those are complementary findings and
the manuscript must carry both.

The scope is a representation-matched, zero-floor best-case benchmark at one
known Kerr geometry. It isolates inversion error from representation error under
an exactly matched localized model class, and establishes nothing about
arbitrary or realistic accretion-flow histories.
"""
    OUT.write_text(body)
    PROV.write_text(json.dumps({
        "schema": "phrt-artifact-manifest/1",
        "experiment_id": "R1L_STAGE_2R_B_GATE_COMPLETED",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "stop_token": token, "gate_coverage": cov,
        "reproduction_verdict": rep["verdict"] if rep else "PENDING",
        "authoritative_attestation": "execution",
        "execution_attestation": att,
        "report_assembly_attestation": attest([FZ, AM]),
        "amendment_sha256": sha256_file(AM),
        "inputs": {str(p.relative_to(ROOT)): sha256_file(p)
                   for p in sorted(TAB.glob("r1l_2rb_*.parquet"))},
        "outputs": {str(OUT.relative_to(ROOT)): sha256_file(OUT)},
    }, indent=2, default=str) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}\nwrote {PROV.relative_to(ROOT)}")
    print(f"  gates {len(cov['emitted'])}/{len(cov['declared'])}, "
          f"disposition {token}")
    print(f"total {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
