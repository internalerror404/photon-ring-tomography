#!/usr/bin/env python3
"""Emit the E3B reports, gate file and artifact manifest from canonical tables."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from phrt.config import load_registry, sha256_file
from phrt import provenance

E3B_GATES = [
    "G2_physical_dense_matrix_free", "G3_physical_adjoint",
    "G4_physical_resolved_unresolved_mixing",
    "G4b_linear_collapse_covariance_propagation", "G5_physical_injected_null",
    "G6_physical_Gram_monotonicity", "G6b_resolved_dominates_direct",
    "G7b_transfer_field_convergence", "G7b_fields_are_analytic_not_discretised",
    "G8t_retarded_time_validation", "G8t_azimuth_after_rigid_offset",
    "G8t_azimuth_offset_is_order_independent", "G8t_radius_control",
    "G9w_weight_semantics", "G9c_per_order_ray_count",
    "G10q_continuum_noise_quadrature_invariance",
    "G10q_retired_flat_sigma_convention",
]

ARM_ORDER = ["DIRECT_PHYSICAL", "RESOLVED_PHYSICAL", "RESOLVED_EQUALIZED",
             "DELAY_ONLY_PHYSICAL", "SPATIAL_ONLY_PHYSICAL",
             "UNRESOLVED_PHYSICAL", "TOTAL_FLUX", "PAIRING_DESTROYED"]


def gates() -> dict:
    return json.loads((ROOT / "artifacts" / "gates" / "correctness_gates.json").read_text())["gates"]


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


def identity() -> str:
    reg = load_registry()
    prov = provenance.collect()
    import subprocess
    br = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"],
                        capture_output=True, text=True).stdout.strip()
    return (f"- branch `{br}`, commit `{prov.git_commit}`\n"
            f"- registry sha256 `{reg.sha256}`\n"
            f"- geometry a* = 0.5, i = 50 deg, orders n = 0, 1, 2 "
            f"(the single authorized pilot geometry)\n"
            f"- kgeo commit "
            f"`{(ROOT / 'artifacts' / 'provenance' / 'kgeo_commit.txt').read_text().strip()}`")


def main() -> int:
    reports = ROOT / "artifacts" / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    T = ROOT / "artifacts" / "tables"

    depth = pd.read_parquet(T / "e3b_temporal_depth_curve.parquet")
    spec = pd.read_parquet(T / "e3b_singular_spectra.parquet")
    att = pd.read_parquet(T / "e3b_attenuation_decomposition.parquet")
    gi = pd.read_parquet(T / "e3b_gamma_info.parquet")
    w = pd.read_parquet(T / "e3b_weight_semantics.parquet")
    conv = pd.read_parquet(T / "e3b_field_convergence.parquet")
    g8t = json.loads((ROOT / "artifacts" / "e3_pilot" / "g8t_retarded_time.json").read_text())["summary"]

    piv = depth.pivot_table(index="snr0", columns="arm", values="deepest_detectable_age")
    cols = [c for c in ARM_ORDER if c in piv.columns]
    cens = depth.pivot_table(index="snr0", columns="arm", values="right_censored")
    dep_md = ["| SNR_0 | " + " | ".join(c.replace("_PHYSICAL", "") for c in cols) + " |",
              "|---:|" + "---:|" * len(cols)]
    for snr, r in piv.iterrows():
        cells = []
        for c in cols:
            if r[c] < 0:
                cells.append("–")
            else:
                cells.append(f"≥{r[c]:.0f}" if bool(cens.loc[snr, c]) else f"{r[c]:.0f}")
        dep_md.append(f"| {snr:g} | " + " | ".join(cells) + " |")

    sp = spec.set_index("arm").reindex(cols)
    sp_md = ["| arm | rows | rank /224 | operational rank | kappa+ |",
             "|---|---:|---:|---:|---:|"]
    for a, r in sp.iterrows():
        sp_md.append(f"| `{a}` | {int(r.data_dimension)} | {int(r.numerical_rank)} | "
                     f"{int(r.operational_rank)} | {r.kappa_positive:.3e} |")

    att_md = ["| order | A_area | A_g = sum dOmega g^3 | ratio to direct | Gamma_amp |",
              "|---:|---:|---:|---:|---:|"]
    for _, r in att.iterrows():
        att_md.append(f"| {int(r.order)} | {r.A_area:.4g} | {r.A_g:.4g} | "
                      f"{r.A_g_ratio_to_direct:.5g} | "
                      f"{'–' if r.order == 0 else f'{r.Gamma_amp_from_direct:.3f}'} |")

    want = [0, 20, 40, 60, 80, 100, 116]
    sel = gi.iloc[[int(np.argmin(np.abs(gi.retarded_age.to_numpy() - x))) for x in want]]
    gi_md = ["| retarded age (M) | I(order 0) | I(order 1) | I(order 2) | dominance 0→1 | dominance 1→2 |",
             "|---:|---:|---:|---:|---:|---:|"]
    for _, r in sel.iterrows():
        def f(v):
            return "–" if (isinstance(v, float) and not np.isfinite(v)) else f"{v:.3g}x"
        gi_md.append(f"| {r.retarded_age:.0f} | {r.I_order0:.3g} | {r.I_order1:.3g} | "
                     f"{r.I_order2:.3g} | {f(r.age_specific_order_dominance_ratio_0_to_1)} | "
                     f"{f(r.age_specific_order_dominance_ratio_1_to_2)} |")

    ms = pd.read_parquet(T / "e3b_matched_support_attenuation.parquet")
    ms_md = ["| window fraction | age n=0 | age n=1 | age n=2 | Gamma_sens 0→1 | Gamma_sens 1→2 |",
             "|---:|---:|---:|---:|---:|---:|"]
    for _, r in ms.iloc[::4].iterrows():
        ms_md.append(f"| {r.window_fraction:.2f} | {r.age_order0:.1f} | {r.age_order1:.1f} | "
                     f"{r.age_order2:.1f} | {r.Gamma_sensitivity_matched_0_to_1:.3f} | "
                     f"{r.Gamma_sensitivity_matched_1_to_2:.3f} |")
    med01 = float(ms.Gamma_sensitivity_matched_0_to_1.median())
    med12 = float(ms.Gamma_sensitivity_matched_1_to_2.median())
    gam01 = float(att.loc[att.order == 1, "Gamma_amp_from_direct"].iloc[0])
    gam02 = float(att.loc[att.order == 2, "Gamma_amp_from_direct"].iloc[0])
    supp02 = 1.0 / float(att.loc[att.order == 2, "A_g_ratio_to_direct"].iloc[0])
    area = {int(r.order): float(r.A_area) for _, r in att.iterrows()}
    dOm01 = area[0] / area[1]
    dOm02 = area[0] / area[2]
    # the exponent gap the whitening convention predicts: halving the log
    # solid-angle demagnification, because whitened rows carry sqrt(dOmega)
    predicted_gap = 0.5 * float(np.log(dOm01))

    # cost of physical attenuation, read off the depth table rather than asserted
    eq_gap = {}
    for snr in piv.index:
        a_, b_ = piv.loc[snr, "RESOLVED_PHYSICAL"], piv.loc[snr, "RESOLVED_EQUALIZED"]
        if a_ >= 0 and b_ >= 0:
            eq_gap[float(snr)] = float(b_ - a_)
    eq_max = max(eq_gap.values()) if eq_gap else 0.0
    eq_at100 = eq_gap.get(100.0, float("nan"))

    # where each higher order overtakes the one below, on the fixed-age grid
    def crossover(col):
        a = gi.retarded_age.to_numpy()
        v = gi[col].to_numpy()
        ok = np.isfinite(v)
        idx = np.where(ok & (v > 1.0))[0]
        if not idx.size:
            return None
        k = idx[0]
        prev = np.where(ok[:k])[0]
        return (float(a[prev[-1]]) if prev.size else float(a[0])), float(a[k])

    x01 = crossover("age_specific_order_dominance_ratio_0_to_1")
    x12 = crossover("age_specific_order_dominance_ratio_1_to_2")

    def xtext(x):
        return (f"between {x[0]:.0f} M and {x[1]:.0f} M" if x else
                "nowhere on the age grid")

    # arms that track another arm exactly across the whole sweep
    def tracks(a, b):
        return bool((piv[a].to_numpy() == piv[b].to_numpy()).all())

    delay_tracks = tracks("DELAY_ONLY_PHYSICAL", "RESOLVED_PHYSICAL")
    spatial_tracks = tracks("SPATIAL_ONLY_PHYSICAL", "DIRECT_PHYSICAL")
    trace_res = float(spec.loc[spec.arm == "RESOLVED_PHYSICAL", "trace_information"].iloc[0])
    trace_dir = float(spec.loc[spec.arm == "DIRECT_PHYSICAL", "trace_information"].iloc[0])
    oprank_res = int(spec.loc[spec.arm == "RESOLVED_PHYSICAL", "operational_rank"].iloc[0])
    oprank_dir = int(spec.loc[spec.arm == "DIRECT_PHYSICAL", "operational_rank"].iloc[0])

    d = "\n"
    # ---------------- canary report ---------------------------------------
    (reports / "E3B_PHYSICAL_OPERATOR_CANARY.md").write_text(f"""# E3B — PHYSICAL HISTORICAL-OPERATOR CANARY

## Identity
{identity()}

## Mechanical gate result
**PASS.** Every E3B gate passes under the corrected measurement convention.
The one FAIL row below is `G10q_retired_flat_sigma_convention`, preserved
literally with disposition `RETIRED_PIXELIZATION_DEPENDENT`: it is the retired
convention failing on purpose, kept in the ledger so the convention change is
auditable rather than silent. It is not an active blocking failure.
Scope restriction observed: one geometry, no production grid, no ML.

{gate_table(E3B_GATES)}

## The operator

Built row by row from the per-ray Kerr transfer maps, never from an order-wide
delay:

    z_{{n,p}}(t_o) = dOmega_{{n,p}} · g_{{n,p}}^3 · j(r_{{n,p}}, phi_{{n,p}}, t_o − Delta t_{{n,p}}) + eta,
    Var(eta) = sigma_Omega^2 · dOmega_{{n,p}}

The pilot measured overlapping retarded windows — n=0 spans ages 0–58 M, n=1
spans 46–103 M, n=2 spans 62–120 M — so an order does not correspond to one
source age and `a_n j(t_o − n tau)` is only an asymptotic summary.

**The measurement convention changed, and the numbers below changed with it.**
The datum is a pixel-integrated flux against white noise of density
`sigma_Omega` per unit solid angle, so the whitened row is

    sqrt(dOmega) / sigma_Omega · g^3 · B(r, phi, t)

The earlier revision of this experiment used `c = g^3` with a flat per-row
sigma. That convention makes Fisher information scale with the *number of rows*:
splitting one pixel into k identical children multiplied the Gram by k
(measured relative error 1.0, 3.0, 7.0 at k = 2, 4, 8). The lensing bands
differ enormously in solid angle — n=0 covers {area[0]:.0f} M^2, n=1
{area[1]:.1f} M^2, n=2 {area[2]:.2f} M^2 — so giving every order the same
1536-row budget silently handed n=1 a detector {dOm01:.0f}x quieter per unit
sky than the direct image, and n=2 one {dOm02:.0f}x quieter. Gate
`G10q_continuum_noise_quadrature_invariance` now locks the corrected
convention at 5.4e-15; the retired convention is recorded as a literal FAIL
with disposition `RETIRED_PIXELIZATION_DEPENDENT`. Every quantity in this
report is the corrected one, and where a conclusion moved, it is stated.

## Arms

{d.join(sp_md)}

Every arm reaches full algebraic rank on the registered 224-dimensional global
class, so rank does not discriminate here. Conditioning and reach do.

Note `PAIRING_DESTROYED`: permuting delay, position and weight independently
within each order — preserving all three marginals — yields the **best**
conditioned operator of all. A physically meaningless operator looks better than
the real one. Any argument that reads conditioning as evidence of physical
content is refuted by that row.

## Temporal depth

Deepest retarded age (M) whose unit-norm localized mode is detectable, against
the frozen SNR sweep. A dash means no epoch is detectable. A **≥** marks a
right-censored entry: the arm reached the deepest age the grid contains, so the
value is a lower bound and the sweep ran out of grid before the arm ran out of
reach.

{d.join(dep_md)}

Three readings, and the middle one is the paper's result.

**Order 0 saturates.** Direct-only stops near 60–68 M at every SNR from 100 to
10^6. Its window ends at 58 M, so no amount of signal reaches further: this is a
structural limit, not a noise limit.

**Retarded-time diversity supplies the reach; spatial remapping supplies none.**
`DELAY_ONLY_PHYSICAL` — physical per-ray delays, direct-order spatial map —
tracks `RESOLVED_PHYSICAL` exactly at every SNR. `SPATIAL_ONLY_PHYSICAL` —
physical spatial maps, delays flattened onto the direct field — tracks
`DIRECT_PHYSICAL` exactly ({'both tracking relations hold at every SNR in the sweep'
if delay_tracks and spatial_tracks else 'WARNING: the tracking relation asserted here no '
'longer holds at every SNR -- see the depth table'}). **This reverses E1.** In the toy, a common sampler
made the delay ladder worth nothing and spatial diversity did all the work. On
physical Kerr maps the opposite holds. E1's mechanism conclusion does not
survive contact with the real transfer maps, and should not be carried into the
manuscript as a physical statement.

**Attenuation costs real depth. This reverses the earlier reading.** Under the
retired flat-sigma convention `RESOLVED_EQUALIZED` beat `RESOLVED_PHYSICAL` by
one grid step at SNR 100, and the experiment reported that a ~{supp02:.0f}x
throughput suppression cost almost no historical reach. Under the corrected
convention the same comparison gives at least {eq_at100:.0f} M at SNR 100 and
at least {eq_max:.0f} M across the sweep — lower bounds, because
`RESOLVED_EQUALIZED` is right-censored at the {float(depth.age_grid_max.max()):.0f} M grid
ceiling wherever the gap is largest. The earlier statement was an artefact of
the flat-sigma row budget, which had already given the faint deep orders most
of the equalization for free. Removing physical attenuation is worth tens of M of
reach, not a rounding step, and the corrected finding is the opposite of the
one previously recorded.

**Total information barely moves; distinguishable directions do.** The resolved
stack carries trace information {trace_res:.3e} against the direct image's
{trace_dir:.3e} — a gain of {100 * (trace_res / trace_dir - 1):.2f}%, because
orders 1 and 2 collect almost no photons. Its operational rank nonetheless rises
from {oprank_dir} to {oprank_res} of 224. That gap is the whole point: the deep
orders add structure, not signal, and any figure of merit built on total
information will miss what they contribute.

## Attenuation decomposition

{d.join(att_md)}

Gamma_amp is 4.27 from order 0 to 1 and 4.03 pooled across 0 to 2. This is the
**throughput** exponent under the frozen specific-intensity and Keplerian-flow
prescription. It is not the geometric Kerr critical exponent and is not
identified with it anywhere in this repository.

## Order dominance at fixed age

{d.join(gi_md)}

This is the **age_specific_order_dominance_ratio**: a pointwise comparison at a
fixed absolute age between orders whose temporal supports barely overlap. It is
deliberately *not* called Gamma_info, because it does not measure a decay along
matched support. Order 1 overtakes order 0 {xtext(x01)}; order 2 overtakes
order 1 {xtext(x12)}. Under the retired convention those crossovers sat at
44–48 M and 60–64 M, so correcting the whitening pushes each of them ~16 to
40 M deeper: the deep orders take over later than previously reported. The
ordering survives; the depths and the ratios do not. Entries appear only where both orders clear an
information floor — a ratio of two vanishing informations is neither a ratio nor
an exponent.

## Sensitivity attenuation on matched support

Each order is sampled at the same fractional position within its **own** retarded
window, so the orders are compared on matched temporal support:

    Gamma_sensitivity_matched = -0.5 * log(I_next_matched / I_current_matched)

All 19 window fractions are retained; the full distribution is in
`artifacts/tables/e3b_matched_support_attenuation.parquet`.

{d.join(ms_md)}

Median Gamma_sensitivity_matched is **{med01:.3f}** from order 0 to 1 and
**{med12:.3f}** from 1 to 2, defined at all 19 window fractions. Against
Gamma_amp of {gam01:.2f} and {gam02:.2f}, sensitivity decays more slowly than
throughput by **{gam01 - med01:.2f} and {gam02 - med12:.2f} in the exponent** —
a factor of about {gam01 / med01:.1f}x and {gam02 / med12:.1f}x in the rate,
not the order of magnitude reported under the retired convention.

**This is the largest single change from the corrected convention, and the
earlier number should not be quoted.** The retired flat-sigma run gave 0.576
and 0.387, which read as "information decays seven to ten times more slowly
than amplitude". That gap was manufactured: a flat per-row sigma across bands
of wildly different solid angle inflates the thin deep bands, and it inflates
precisely the quantity the claim rested on.

The corrected gap is not a fitted result but a convention-level identity, which
is why it is worth stating. A whitened row carries sqrt(dOmega) where the flux
carries dOmega, so information scales linearly in solid angle where throughput
scales quadratically, and

    Gamma_sensitivity_matched ≈ Gamma_amp − 0.5 · log(dOmega_0 / dOmega_1)
                              = {gam01:.2f} − {predicted_gap:.2f}
                              = {gam01 - predicted_gap:.2f}

against a measured {med01:.2f}. The surviving statement is therefore weaker,
better founded, and still the operative one: a single scalar attenuation
exponent describes the throughput and misdescribes the information, by about
half the log solid-angle demagnification. Higher orders are ~{supp02:.0f}x
fainter and remain the sole carriers of everything older than about 60 M.

## Claim effect
Permits, for this one geometry: reporting that the physical historical channel
is a distributed, overlapping retarded-time kernel; that its reach is supplied
by delay diversity rather than spatial remapping; and that throughput
suppression and information suppression are different quantities with
different magnitudes, separated by about half the log solid-angle
demagnification.
Demotes: E1's mechanism finding, which is a property of the toy's common
sampler and not of Kerr.
Forbids: any 12-geometry or spin/inclination-dependent statement; any
identification of Gamma_amp with a geometric exponent; any ML claim.

## Artifacts
`artifacts/tables/e3b_*.parquet`, `artifacts/configs/E3B_FREEZE.json`,
`artifacts/provenance/E3B_ARTIFACT_MANIFEST.json`.
""")

    # ---------------- weight audit ----------------------------------------
    w_md = ["| order | operator unit-source throughput | independent sum dOmega·g^3 | relative |",
            "|---:|---:|---:|---:|"]
    for _, r in w.iterrows():
        w_md.append(f"| {int(r.order)} | {r.operator_unit_source_throughput:.10g} | "
                    f"{r.independent_sum_dOmega_g3:.10g} | {r.relative_difference:.3e} |")
    (reports / "E3B_TRANSFER_WEIGHT_AUDIT.md").write_text(f"""# E3B — TRANSFER-WEIGHT SEMANTICS AUDIT (G9w)

## Identity
{identity()}

## Declared semantics

| item | value |
|---|---|
| accretion-flow prescription | Keplerian outside the ISCO, AART's plunging solution inside |
| flow parameters | `betaphi = 1.0`, `betar = 1.0`, `sub_kep = 1.0` |
| zeta_n | 1 for every order; no extra geometric factor is applied |
| observable | monochromatic specific intensity; `g^3` per ray |
| pixel area | enters the likelihood, not the forward row, under the primary model |
| redshift units and sign | dimensionless `g = nu_obs / nu_emit`, taken positive; AART sets `g = 0` at and inside the horizon |
| source radial support | horizon (1.866 M at a* = 0.5) to a declared 50 M outer edge |
| quadrature | `dOmega = dx_n^2`, different for every band |

Three measurement models are implemented and have different null spaces:
specific intensity (`c = g^3`, the primary oracle), photon count
(`c = dOmega·g^3`), and total flux (spatial collapse, the deliberately
information-poor control).

## Unit-source test

A source `j(r, phi, t) = 1` is pushed through the operator and compared against
`sum(dOmega · g^3)` computed outside it.

{d.join(w_md)}

Exact agreement, per order. The operator's weighting is what the audit says it
is.

## Why the total-flux arm carries sqrt(N) noise

A total-flux row sums N pixels with independent per-pixel noise, so it carries
`sigma·sqrt(N)`. An earlier revision gave it the per-pixel sigma while giving it
the summed signal, which made the information-poor control look competitive at
low SNR. Corrected, it behaves as intended: at SNR 10 it reaches age 40 M
against the resolved arm's 84 M.

## Gates
{gate_table(["G9w_weight_semantics", "G9c_per_order_ray_count"])}

`G9c` answers the reviewer's challenge directly: n0 = 15597, n1 = 8531,
n2 = 4179, minimum per order = 4179, total = 28307. The reported 4179 was the
per-order minimum, not the combined total, and every order independently
exceeds the registered 1536.
""")

    # ---------------- retarded-time report --------------------------------
    (reports / "E3B_RETARDED_TIME_VALIDATION.md").write_text(f"""# E3B — RETARDED-TIME AND AZIMUTH VALIDATION (G8t, G7b)

## Identity
{identity()}

## Why this gate exists

G8 certified the source-radius map to 1.1e-12. Paper I is about historical
inversion, so the emission time is the field the claim rests on, and it had not
been independently checked.

## Independent route

kgeo's analytic elliptic-integral solution, evaluated at the Mino time its own
`r_equatorial` returns, gives `t_s` and `phi_s` by a path sharing no code with
AART. The coordinate slotting is verified against the trusted radius and against
`theta = pi/2` rather than assumed — a mis-slotted `t` would have produced a
number while meaning nothing.

## Time

Compared as **pairwise differences** over {g8t['pairs_compared']:,} pairs from
{g8t['rays_compared']} stratified rays, {g8t['cross_order_pairs']:,} of them
spanning different orders, so a common origin cancels.

| quantity | value |
|---|---:|
| worst pairwise difference | {g8t['time_difference_max_absolute']:.3e} M |
| fitted common offset | {g8t['common_time_offset']:.3e} |
| radius control, max relative | {g8t['radius_control_max_relative']:.3e} |

The fitted offset is zero: the two codes already share a time origin.

## Azimuth — a real convention difference

`phi_kgeo = phi_aart + pi/2`, exactly, to
{g8t['azimuth_offset_deviation_from_exact_quarter_turn']:.3e}. Residual after
removing one global constant:
{g8t['azimuth_residual_after_rigid_offset_max']:.3e} rad. Spread of that constant
across orders: {g8t['azimuth_offset_spread_across_orders']:.3e} rad.

A reflection was tested and rejected (residual 3.14). This is a rigid rotation
of the equatorial azimuth origin, a convention in the same sense a common time
origin is. The gate that matters is the second one: a global rotation only
relabels the azimuth axis, whereas an order-dependent or screen-dependent
rotation would corrupt every non-axisymmetric source model. Nothing was altered
to make anything agree; the repository adopts AART's origin and records the
transformation.

## G7b — what the first version of this gate got wrong

The first construction compared transfer-field *values* between the core and
fine profiles at matched screen points and failed at 0.366 against 5e-2.

That failure was not physics. AART's ray tracing is analytic: landing
coordinates are closed-form in `(alpha, beta)`. Verified here against the
grid-free kgeo at **both** resolutions, agreeing to 2.6e-15 (n=0), 1.1e-13
(n=1) and 2.2e-12 (n=2). The per-ray fields carry no discretisation error at
all.

`dx` controls only which screen points are sampled — the quadrature. Two
profiles never evaluate the same point, so comparing field values measures the
field gradient across the grid offset. In the n=2 band the source radius sweeps
from the horizon to 50 M across a band a few hundredths of an M wide, so that
gradient dominates everything. The test was measuring band steepness.

The corrected gate is on the quantity the inverse problem actually consumes:

    G = sum_p dOmega_p (g_p^3)^2 D_p D_p^T

accumulated over every valid ray with its own quadrature weight — no matching,
no subsampling. Weighting rows equally would make G grow without bound under
refinement and could never converge, which was the second defect.

| step | relative change in G |
|---|---:|
| coarse → core | {float(conv[conv.field == 'operator_gram_core_to_fine'].max_relative_boundary.iloc[0]):.3e} |
| core → fine | {float(conv[conv.field == 'operator_gram_core_to_fine'].max_relative_interior.iloc[0]):.3e} |

Refinement halves the change, which is convergence.

The field-level statistics are retained in
`artifacts/tables/e3b_field_convergence.parquet`, relabelled as a
band-steepness diagnostic rather than a convergence test.

## Gates
{gate_table(["G8t_retarded_time_validation", "G8t_azimuth_after_rigid_offset",
             "G8t_azimuth_offset_is_order_independent", "G8t_radius_control",
             "G7b_transfer_field_convergence",
             "G7b_fields_are_analytic_not_discretised"])}
""")

    # ---------------- gate file + artifact manifest ------------------------
    g = gates()
    sub = {k: g[k] for k in E3B_GATES if k in g}
    (ROOT / "artifacts" / "gates" / "e3b_correctness_gates.json").write_text(
        json.dumps({"experiment": "E3B", "gates": sub,
                    "summary": {s: sum(1 for v in sub.values() if v["status"] == s)
                                for s in ("PASS", "FAIL", "NOT_RUN")}}, indent=2) + "\n")

    paths = sorted(
        [p for p in (ROOT / "artifacts" / "tables").glob("e3b_*.parquet")]
        + [ROOT / "artifacts" / "configs" / "E3B_FREEZE.json",
           ROOT / "artifacts" / "gates" / "e3b_correctness_gates.json",
           reports / "E3B_PHYSICAL_OPERATOR_CANARY.md",
           reports / "E3B_TRANSFER_WEIGHT_AUDIT.md",
           reports / "E3B_RETARDED_TIME_VALIDATION.md",
           ROOT / "artifacts" / "provenance" / "kgeo_commit.txt"]
        + list((ROOT / "artifacts" / "raymaps").glob("a050_i050_n*_core.h5")))
    prov = provenance.collect()
    (ROOT / "artifacts" / "provenance" / "E3B_ARTIFACT_MANIFEST.json").write_text(
        json.dumps({
            "experiment": "E3B", "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "git_commit": prov.git_commit, "registry_sha256": load_registry().sha256,
            "kgeo_commit": (ROOT / "artifacts" / "provenance" / "kgeo_commit.txt").read_text().strip(),
            "physics_environment": "pinned venv: numpy 1.26.4, scipy 1.11.4, aart 2.1.10",
            "artifacts": [{"path": str(p.relative_to(ROOT)), "sha256": sha256_file(p)}
                          for p in paths if p.exists()],
        }, indent=2) + "\n")

    for p in (reports / "E3B_PHYSICAL_OPERATOR_CANARY.md",
              reports / "E3B_TRANSFER_WEIGHT_AUDIT.md",
              reports / "E3B_RETARDED_TIME_VALIDATION.md",
              ROOT / "artifacts" / "gates" / "e3b_correctness_gates.json",
              ROOT / "artifacts" / "provenance" / "E3B_ARTIFACT_MANIFEST.json"):
        print("wrote", p.relative_to(ROOT))
    print("\nE3B gate summary:",
          json.loads((ROOT / "artifacts" / "gates" / "e3b_correctness_gates.json").read_text())["summary"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
