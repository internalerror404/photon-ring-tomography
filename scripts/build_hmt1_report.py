#!/usr/bin/env python3
"""Report for the HMT-1 validation. Every number read from the HMT-1 tables.

The narrative is selected by the stop token the run emitted, not written in
advance. Six dispositions are declared in the freeze and exactly one is
rendered, so the report cannot describe an outcome the run did not produce.
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

FZ = ROOT / "artifacts" / "configs" / "HMT1_VALIDATION_FREEZE_V0.json"
TAB = ROOT / "artifacts" / "tables"
G = ROOT / "artifacts" / "gates" / "hmt1_gates.json"
OUT = ROOT / "artifacts" / "reports" / "HMT1_VALIDATION.md"
PROV = ROOT / "artifacts" / "provenance" / "HMT1_VALIDATION_ARTIFACT_MANIFEST.json"
D = "\n"

DISPOSITION_PROSE = {
    "HMT1_FEATURE_RECOVERY_PASS":
        "Every registered criterion is met, including under a background "
        "estimated from the arm's own data. Within this geometry and this "
        "source model, a compressed description of the past -- where a "
        "feature was, how it moved, when it appeared and faded -- survives "
        "the operator materially better in the resolved arm than in the "
        "direct image, and there is a nonzero interval of age over which it "
        "stays inside the registered tolerance.",
    "HMT1_BACKGROUND_ASSISTED_ONLY":
        "The criteria are met when the axisymmetric background is handed to "
        "the estimator and not when it must be estimated from the arm's own "
        "data. That distinction is the whole point of carrying three "
        "background regimes: a result available only under an oracle "
        "background is a statement about the contrast problem with the hard "
        "part removed, and it is not the claim a paper can make.",
    "HMT1_MATERIAL_ERROR_REDUCTION_NO_STABLE_INTERVAL":
        "Feature error improves materially in the resolved arm, and there is "
        "no age interval over which the recovered history stays inside the "
        "registered tolerance. Both halves are the result. A material "
        "reduction in a time-averaged error is not the same claim as a "
        "history that holds together over a stretch of the past, and this "
        "run separates them.",
    "HMT1_NO_MATERIAL_EFFECT":
        "The banks are sound and the registered materiality threshold is not "
        "reached. This is a reportable negative result, not a failed run: "
        "the operator, the source model and the controls all did what they "
        "were registered to do, and the answer is that the resolved arm does "
        "not buy enough for this endpoint.",
    "HMT1_SOURCE_BANK_FAILURE":
        "A declared source bank could not be built inside the contrast-model "
        "tolerances. No endpoint is readable, because the truths the "
        "endpoint would be read against are not the truths that were "
        "registered.",
    "HMT1_IMPLEMENTATION_DEFECT":
        "A gate failed, a resource limit was exceeded, or a split commitment "
        "did not reproduce. No scientific reading is taken from this run.",
}


def main() -> int:
    t0 = time.time()
    fz = json.loads(FZ.read_text())
    g = json.loads(G.read_text())
    token = g["stop_token"]
    end = pd.read_parquet(TAB / "hmt1_endpoint.parquet")
    spans = pd.read_parquet(TAB / "hmt1_stable_feature_spans.parquet")
    banks = pd.read_parquet(TAB / "hmt1_source_banks.parquet")
    sel = pd.read_parquet(TAB / "hmt1_selection.parquet")
    bgerr = pd.read_parquet(TAB / "hmt1_background_error.parquet")
    scores = pd.read_parquet(TAB / "hmt1_scores.parquet")
    man = json.loads(sorted((ROOT / "artifacts" / "manifests")
                            .glob("HMT1_*.json"))[-1].read_text())
    att = man["attestation"]
    snr_p = fz["snr"]["primary"]
    snr_s = fz["snr"]["secondary"]
    M = fz["pass_criteria"]["material_benefit_under_both_classical_estimators"]
    fams = list(fz["feature_families"])
    nfam = len(fams)

    def etab(df):
        return D.join(
            f"| `{r.regime}` | `{r.arm}` | {r.estimator} | {r.snr0:.0f} | "
            f"{r.median:+.3f} | {r.median_ci_low:+.3f} | {r.median_ci_high:+.3f} | "
            f"{int(r.n_families_improved)}/{int(r.n_families)} | "
            f"{int(r.n_truths):,} | "
            f"{'**MATERIAL**' if r.meets_materiality else 'no'} |"
            for r in df.sort_values(["regime", "arm", "estimator"]).itertuples())

    prim = etab(end[end.snr0 == snr_p])
    sec = etab(end[end.snr0 == snr_s])

    sptab = D.join(
        f"| `{r.regime}` | `{r.arm}` | {r.snr0:.0f} | {r.epsilon:.2f} | "
        f"{r.quantile:.2f} | {r.L_stable_features_M:.1f} | "
        f"{int(r.n_realizations):,} |"
        for r in spans.sort_values(["regime", "arm", "snr0"]).itertuples())

    bg = bgerr.groupby("regime").agg(
        median_relative=("relative_error", "median"),
        worst_relative=("relative_error", "max"),
        worst_bias=("bias", lambda s: s.abs().max()),
        min_estimate=("min_estimate", "min")).reset_index()
    bgtab = D.join(
        f"| `{r.regime}` | {r.median_relative:.4f} | {r.worst_relative:.4f} | "
        f"{r.worst_bias:.2e} | {r.min_estimate:.3f} |"
        for r in bg.itertuples())

    gtab = D.join(
        f"| `{k}` | {v['status']} | {v.get('note', '')} |"
        for k, v in g["gates"].items())
    nfail = sum(1 for v in g["gates"].values() if v["status"] != "PASS")
    failed = g.get("failed_gates", [])
    withheld = bool(g.get("science_reading_withheld"))

    curve_path = TAB / "hmt1_selection_curve.parquet"
    if curve_path.exists():
        cur = pd.read_parquet(curve_path)
        piv = cur.sort_values("hyperparameter", ascending=False)
        rows = []
        for (rg, ar, es), grp in piv.groupby(["regime", "arm", "estimator"]):
            grp = grp.sort_values("hyperparameter", ascending=False)
            at_max = float(grp.selection_error.iloc[0])
            at_min = float(grp.selection_error.iloc[-1])
            best = float(grp.selection_error.min())
            rows.append(f"| `{rg}` | `{ar}` | {es} | {at_max:.4f} | "
                        f"{best:.4f} | {at_min:.4f} | "
                        f"{'yes' if at_max <= best + 1e-15 else 'no'} |")
        curtab = D.join(rows)
    else:
        curtab = "| _(not recorded in this run)_ | | | | | | |"

    detail = ("Failed gates: " + ", ".join(f"`{x}`" for x in failed) + "."
              if failed else
              "All gates pass, so the disposition is read from the science.")
    if withheld:
        banner = f"""> **The scientific reading of this run is withheld.**
>
> {nfail} gate(s) failed: {', '.join(f'`{x}`' for x in failed)}. The freeze
> defines `HMT1_IMPLEMENTATION_DEFECT` as "a gate failed, a limit was
> exceeded, or a commitment did not reproduce", so that is the disposition,
> and the endpoint tables below are diagnostic only. They are printed because
> a failure should be inspectable, not because they are a result.
"""
    else:
        banner = ""

    ver = D.join(
        f"| `{k}` | {v.get('families_improved')}/{nfam} | "
        f"{'yes' if v.get('materiality') else 'no'} | "
        f"{'yes' if v.get('stable_interval') else 'no'} | "
        f"{'**PASS**' if v.get('pass') else 'no'} |"
        for k, v in g["verdicts"].items())

    coll = int(sel.at_max_regularization_end.sum())
    rd = g["family_agreement_readings"]
    g10b = g["gates"]["HMT1_G10b_truth_extraction_recovers_generative_parameters"]

    body = f"""# HMT-1 — historical feature and contrast tomography, validation

Freeze `{fz['id']}`, run `{g['run_id']}`.
Execution commit `{att['execution_commit'][:12]}`, tree clean:
{str(att['clean']).lower()}, preregistered: {str(att['preregistered']).lower()}.

{banner}
## 1. What this run asked

R1L established what a compact temporal basis can and cannot recover about the
past, and it stopped on a structural endpoint measured in reconstruction error.
That endpoint is a norm on a coefficient vector. It is not the thing anyone
actually wants to know, which is whether the *description* of the past survives:
where a feature was, how it moved, how bright it was, when it appeared and when
it faded.

HMT-1 changes the endpoint to those quantities and changes the source model to
one that can carry them honestly. The field is a positive axisymmetric
background carrying a signed fluctuation, `j = b(r,t) + dj(r,phi,t)`, with
`b > 0`, `dj` of zero azimuthal mean at every radius and age, and `b + dj >= 0`.
The operator sees the total. Only `dj` is reconstructed, and every `m = 0`
direction is projected out of the reconstruction class, so a background error
cannot hide inside a feature result.

That split is what separates this from the signed constant-flux bank R1L had to
disqualify. There the *emissivity* went negative, which is not a source. Here
the physical field is positive by construction and the modelled fluctuation is
free to change sign, which is what a fluctuation does.

Geometry: spin a* = {fz['geometry']['a_star']}, inclination
{fz['geometry']['inclination_deg']} deg. {nfam} declared feature families,
{len(fz['background_regimes'])} background regimes, {len(fz['arms'])} arms,
{len(banks):,} truths.

## 2. Primary endpoint at SNR₀ = {snr_p:.0f}

Median relative reduction in old-band feature error against the direct image,
with a paired truth-cluster bootstrap interval. Materiality is a median
relative reduction of at least {M['median_relative_reduction']:.2f} with a
bootstrap lower bound above {M['median_bootstrap_lower_bound']:.2f}, on both
classical estimators -- the same numeric standard R1L used, so the two studies
are comparable.

| regime | arm | estimator | SNR₀ | median | CI low | CI high | families | truths | material |
|---|---|---|---|---|---|---|---|---|---|
{prim}

At the secondary SNR₀ = {snr_s:.0f}:

| regime | arm | estimator | SNR₀ | median | CI low | CI high | families | truths | material |
|---|---|---|---|---|---|---|---|---|---|
{sec}

## 3. Stable historical feature interval

The co-primary endpoint. How far back the recovered feature history stays
inside the registered tolerance, with the supremum taken *inside* the
probability, so the interval is one over which the description holds
throughout rather than one it merely touches.

| regime | arm | SNR₀ | epsilon | quantile | L_stable (M) | realizations |
|---|---|---|---|---|---|---|
{sptab}

## 4. Background regimes

The regime that decides whether this is a paper-grade result is
`estimated_from_data`, where `b` is fit by a fixed low-order axisymmetric design
through the arm's own operator against the arm's own data. The oracle regime is
a ceiling, not a claim.

| regime | median rel. error | worst | worst bias | min estimate |
|---|---|---|---|---|
{bgtab}

## 5. Verdicts by regime

Family agreement is read two ways, both declared before the run: as a fraction
({rd['fraction_required']} of {nfam}) and as a count ({rd['count_required']} of
{nfam}). Both are reported because they can disagree, and picking the one that
gives the nicer answer after seeing them is how a preregistration gets spent.

| regime | families improved | material | stable interval | pass |
|---|---|---|---|---|
{ver}

## 6. Gates and controls

{len(g['gates'])} gates, {g['summary']['PASS']} pass, {nfail} not.

| gate | status | note |
|---|---|---|
{gtab}

`HMT1_G10b` is the check that the feature extractor, pointed at the truth itself
with no operator and no noise in the way, returns the feature that was actually
put there: worst displacement {g10b['measured']:.3f} evaluation-grid cells
against a threshold of {g10b['threshold']:.1f}. It exists because `HMT1_G10`
only asks that extraction be repeatable, and an extractor that reads the wrong
position reads it repeatably. It was declared in the freeze and not implemented
until `HMT1_G13` caught it on the first end-to-end run.

### Regularization collapse

{coll} of {len(sel):,} selections landed at the maximal end of their grid.
`HMT1_G12` exists because a selection rule that drives every arm to maximal
regularization is the signature of a degenerate endpoint, and because the
result it produces is a *null* -- every arm collapsed onto nearly the same
near-null estimator will of course show no difference between arms. A null
endpoint read from a collapsed selection is not evidence of no effect; it is
evidence that the selection rule did not select.

The full sweep is recorded, not just its argmin, because a selection pinned at
a grid endpoint and one with a genuine interior optimum produce the same single
number:

| regime | arm | estimator | error at most-regularized end | best on grid | at least-regularized end | pinned |
|---|---|---|---|---|---|---|
{curtab}

Worst source-bank residuals across all {len(banks):,} truths: azimuthal mean
{banks.azimuthal_mean_max_abs.max():.2e}, spatial mean
{banks.zero_mean_max_abs.max():.2e}, most negative total emissivity
{banks.min_total.min():.3f}, smallest background {banks.min_background.min():.3f}.
Local contrast amplitude spans
{banks.peak_fraction_of_background.min():.2f} to
{banks.peak_fraction_of_background.max():.2f} of the local background.

## 7. Disposition

`{token}`

{DISPOSITION_PROSE[token]}

{detail}

## 8. What this does not show

One geometry, one spin, one inclination. The truths are drawn from six declared
analytic families, so they are in the reconstruction class by construction up to
the projection, and the result is an upper bound on what this operator can do
for this class rather than a statement about real source histories, which are in
no one's basis. Nothing here licenses a claim about an observed source: that
would need the geometry-mismatch, order-leakage and instrument stages, none of
which are authorized.

The R1L stop stands, and its sealed commitments remain unscored.

**STOP.** Validation is complete and no further stage is authorized without a
new ruling.
"""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    PROV.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(body)
    inputs = sorted(str(p.relative_to(ROOT)) for p in TAB.glob("hmt1_*.parquet"))
    PROV.write_text(json.dumps({
        "schema": "phrt-artifact-manifest/1",
        "experiment_id": "HMT1_VALIDATION",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "stop_token": token,
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
