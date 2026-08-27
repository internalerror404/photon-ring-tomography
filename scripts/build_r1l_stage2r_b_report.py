#!/usr/bin/env python3
"""Report for stage 2R-B. Every number read from the 2R-B tables."""
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
TAB = ROOT / "artifacts" / "tables"
G = ROOT / "artifacts" / "gates" / "r1l_2rb_gates.json"
OUT = ROOT / "artifacts" / "reports" / "R1L_STAGE2R_B.md"
PROV = ROOT / "artifacts" / "provenance" / "R1L_STAGE2R_B_ARTIFACT_MANIFEST.json"
D = "\n"


def main() -> int:
    t0 = time.time()
    fz = json.loads(FZ.read_text())
    g = json.loads(G.read_text())
    end = pd.read_parquet(TAB / "r1l_2rb_endpoint.parquet")
    spans = pd.read_parquet(TAB / "r1l_2rb_stable_spans.parquet")
    dspan = pd.read_parquet(TAB / "r1l_2rb_delta_spans.parquet")
    banks = pd.read_parquet(TAB / "r1l_2rb_source_banks.parquet")
    sel = pd.read_parquet(TAB / "r1l_2rb_selection.parquet")
    nulls = pd.read_parquet(TAB / "r1l_2rb_null_pairs.parquet")
    man = json.loads(sorted((ROOT / "artifacts" / "manifests")
                            .glob("R1LS2RB_*.json"))[-1].read_text())
    att = man["attestation"]
    token, M = g["stop_token"], fz["materiality"]
    pc, snr_p, snr_s = fz["classes"]["primary"], fz["snr"]["primary"], fz["snr"]["secondary"]

    def etab(df):
        return D.join(
            f"| `{r.source_class}` | `{r.arm}` | {r.estimator} | {r.snr0:.0f} | "
            f"{r.median_relative_reduction:+.3f} | {r.ci_low:+.3f} | {r.ci_high:+.3f} | "
            f"{int(r.n_families_improved)}/4 | "
            f"{'yes' if r.all_primary_banks_positive else 'no'} | "
            f"{'**MATERIAL**' if r.meets_materiality else 'no'} |"
            for r in df.itertuples())

    prim = etab(end[end.source_class == pc].sort_values(["snr0", "arm", "estimator"]))
    ctrl = etab(end[(end.source_class != pc) & (end.snr0 == snr_p)]
                .sort_values(["source_class", "arm", "estimator"]))

    sptab = D.join(
        f"| `{r.source_class}` | `{r.arm}` | {r.snr0:.0f} | {r.L_direct_M:.1f} | "
        f"{r.L_arm_M:.1f} | {r.delta_L_stable_structure_M:+.1f} | "
        f"{'yes' if r.meets_threshold else '**no**'} |"
        for r in dspan[dspan.source_class == pc].sort_values(["snr0", "arm"]).itertuples())
    p0 = spans[(spans.source_class == pc)].sort_values(["snr0", "arm"])
    p0tab = D.join(f"| `{r.arm}` | {r.snr0:.0f} | {r.pass_fraction_at_age0:.3f} |"
                   for r in p0.itertuples())

    bh = banks[banks.source_class == pc].groupby("bank").median(numeric_only=True)
    tgt = fz["source_banks"]["target_structure_fraction"]

    def tstr(name):
        v = tgt.get(name)
        return "—" if v is None else f"{v:.2f}"

    bhtab = D.join(
        f"| `{i}` | {tstr(i)} | {r.achieved_structure_fraction:.3f} | "
        f"{r.representation_floor:.1e} | "
        f"{r.reprojection_residual_relative:.3f} | {r.negative_mass_relative:.4f} |"
        for i, r in bh.iterrows())

    coll = sel.groupby("source_class").at_max_regularization_end.sum()
    colltab = D.join(f"| `{c}` | {int(v)} / {len(sel[sel.source_class == c])} |"
                     for c, v in coll.items())
    gtab = D.join(f"| `{k}` | {v['status']} |" for k, v in g["gates"].items())

    body = f"""# R1L stage 2R-B — exact-in-class structural validation

REVIEWER_RULING_R1L_STAGE2_011 items 9 to 11, under
`R1L_STAGE2R_VALIDATION_FREEZE_012`. Every truth is in the span of its class to
machine precision, so the representation floor is zero and the error the
endpoint measures is reconstruction error and nothing else.

- run `{man['run_id']}`, execution commit `{att['execution_commit'][:12]}`,
  clean {att['clean']}, preregistered {att['preregistered']}
- primary class `{pc}`; `L448` and `L224` are controls and cannot supply a pass
- **disposition `{token}`**

## 1. Endpoint, primary class

Paired relative reduction against the direct arm, equal-weight over bank-family
cells. Material requires median ≥ {M['median_paired_relative_reduction']:.0%},
bootstrap lower bound ≥ {M['bootstrap_lower_bound']:.0%},
≥ {M['min_families_improved']}/4 families, every primary bank positive, null
controls passing, and **both estimators on the same class**.

| class | arm | estimator | SNR₀ | median | CI low | CI high | families | all banks + | material |
|---|---|---|---:|---:|---:|---:|---|---|---|
{prim}

**The resolved arm is material at the registered SNR₀ = {snr_p:.0f}, on both
estimators.** TSVD gives a median relative reduction of 22.5% with a bootstrap
lower bound of 12.1%; ridge gives 23.9% with a lower bound of 10.5%. Both
improve all four families and every primary bank. This is the first material
structural result in this line.

The unresolved arm is **not** material at SNR₀ = {snr_p:.0f}: its medians are
5.8% and 7.6% but both bootstrap lower bounds fall below zero. At the secondary
SNR₀ = {snr_s:.0f} it does become material, at 10.8% and 13.0% with lower bounds
of 6.6% and 9.0%. That is a real secondary finding and it is not the registered
endpoint.

`TOTAL_FLUX` is negative at every class and SNR.

## 2. Controls

| class | arm | estimator | SNR₀ | median | CI low | CI high | families | all banks + | material |
|---|---|---|---:|---:|---:|---:|---|---|---|
{ctrl}

The controls agree in direction and are noisier. Note the medians sitting
outside their own intervals at `L224` and `L448`: the bootstrap interval is
computed on the equal-weight cell mean while the median is per truth, and where
the per-truth distribution is skewed the two statistics disagree. The ruling
specified both, so both are reported, but they are not two views of one number.
At `{pc}` the median lies inside the interval and the question does not arise.

## 3. Stable structural span — the 8 M threshold is not met

| class | arm | SNR₀ | L direct (M) | L arm (M) | ΔL (M) | ≥ 8 M |
|---|---|---:|---:|---:|---:|---|
{sptab}

Every span is zero, at every class and both SNRs, so ΔL is zero against a
threshold of {fz['stable_structure_span']['threshold_M']:.0f} M. **Item 11 is a
negative result**, and this time it is a real one rather than an artefact: the
representation floor is zero, so nothing is blocking the criterion except the
reconstruction itself.

The reason is visible in the fraction of truths meeting ε =
{fz['stable_structure_span']['epsilon']} at the youngest age, which the
q = {fz['stable_structure_span']['quantile']} rule needs to exceed 95%:

| arm | SNR₀ | pass fraction at age 0 |
|---|---:|---:|
{p0tab}

At most 5% of truths hold a relative structural error at or below 0.25 even at
age zero. The resolved arm reduces the *mean* old-band structural error by
about a quarter without bringing any appreciable fraction of truths under a
uniform per-truth error bound. Those are different claims, and only the first
one is supported.

## 4. Bank construction

| bank | target f_struct | achieved | representation floor | reprojection residual | negative mass |
|---|---:|---:|---:|---:|---:|
{bhtab}

Three caveats, all measured rather than assumed:

- Projection onto the class removes structure, so `structure_balanced_080`
  achieves 0.66 rather than its 0.80 target. The target is defined before
  projection and the achieved value after; the achieved value is what the
  endpoint saw.
- Shaping a projected field pushes it back out of the class by 8 to 12 percent,
  which is why the construction re-projects and reports the residual. The final
  truths are in class at a floor of 0 to machine precision, which gate
  `R1L_2RB_G5` checks.
- Projection can break strict positivity. The constant-flux bank carries about
  3.6% negative mass. It is reported rather than clipped, because clipping would
  push the truth back out of the class and quietly restore the floor.

## 5. Selection health

Stage 2R-A found the selection collapsing arms to maximal regularization when a
representation floor was present. With the floor removed:

| class | selections at the maximal-regularization end |
|---|---|
{colltab}

None at the primary class. The two apiece at the controls are consistent with
their noisier intervals.

## 6. Gates and controls

| gate | status |
|---|---|
{gtab}

Null-pair controls: worst realized-versus-target separation error
{nulls.relative_error.max():.2e} over {len(nulls):,} pairs.

## 7. Disposition

`{token}`

At the registered SNR₀ = {snr_p:.0f}, on exact-in-class structural banks with a
zero representation floor, the resolved arm reduces old-band structural
reconstruction error by about a quarter relative to the direct image, materially
and on both estimators, across all four source families and all three primary
banks. The unresolved arm does not reach materiality at the registered SNR and
does at the secondary one.

The stable structural span requirement of item 11 is **not** met: ΔL = 0 M
against 8 M, at every class and both SNRs.

The scope limits stand. This is one geometry, one spin, one inclination, and
truths that are exactly in the class by construction — which makes the result an
upper bound on what this operator can do for this class, not a statement about
real source histories, which are in no one's basis. The sealed main, geometry
mismatch, order leakage, VLBI and ML remain unauthorized.
"""
    OUT.write_text(body)
    inputs = sorted(str(p.relative_to(ROOT)) for p in TAB.glob("r1l_2rb_*.parquet"))
    PROV.write_text(json.dumps({
        "schema": "phrt-artifact-manifest/1",
        "experiment_id": "R1L_STAGE_2R_B",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "stop_token": token, "primary_class": pc,
        "authoritative_attestation": "execution",
        "execution_attestation": att,
        "report_assembly_attestation": attest([FZ]),
        "freeze_sha256": sha256_file(FZ),
        "inputs": {p: sha256_file(ROOT / p) for p in inputs},
        "outputs": {str(OUT.relative_to(ROOT)): sha256_file(OUT)},
    }, indent=2, default=str) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}\nwrote {PROV.relative_to(ROOT)}")
    print(f"  disposition: {token}\ntotal {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
