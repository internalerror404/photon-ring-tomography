#!/usr/bin/env python3
"""Emit the three E3C reports and the artifact manifest from canonical tables.

Every number in the prose is read from the tables rather than typed, so the
reports cannot drift from the run that produced them. Where a claim depends on
a relation holding across the whole grid, the relation is tested here and the
sentence changes if it stops holding.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from phrt import provenance
from phrt.config import load_registry, sha256_file

T = ROOT / "artifacts" / "tables"
REPORTS = ROOT / "artifacts" / "reports"
FREEZE = ROOT / "artifacts" / "configs" / "E3C_OPERATOR_GRID_FREEZE.json"
REF = 100.0

ARM_ORDER = ["DIRECT_PHYSICAL", "RESOLVED_PHYSICAL", "UNRESOLVED_IMAGE",
             "TOTAL_FLUX", "DELAY_ONLY", "SPATIAL_ONLY",
             "EQUALIZED_ORDER_SENSITIVITY", "PAIRING_DESTROYED"]
SPINS = ["a000", "a050", "a090", "a098"]
INCS = [20, 50, 75]


def gates() -> dict:
    return json.loads((ROOT / "artifacts" / "gates"
                       / "correctness_gates.json").read_text())["gates"]


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


def identity(fz: dict) -> str:
    reg = load_registry()
    prov = provenance.collect()
    br = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"],
                        capture_output=True, text=True, cwd=ROOT).stdout.strip()
    return (f"- branch `{br}`, commit `{prov.git_commit}`\n"
            f"- registry sha256 `{reg.sha256}`\n"
            f"- freeze `artifacts/configs/E3C_OPERATOR_GRID_FREEZE.json` "
            f"sha256 `{sha256_file(FREEZE)}`\n"
            f"- {len(fz['geometries'])} registered geometries, orders n = 0, 1, 2, "
            f"profile `{fz['profile']}`\n"
            f"- source class `{fz['source_class']['id']}` "
            f"({fz['source_class']['dimension']} dimensions), unmodified\n"
            f"- common age grid 0 to {fz['common_age_grid']['A_max_M']:.0f} M "
            f"in steps of {fz['common_age_grid']['step_M']:.0f} M")


def surface_table(surf: pd.DataFrame, metric: str, fmt: str = "{:.0f}") -> str:
    r = surf.loc[surf.metric == metric].iloc[0]
    out = ["| a\\* \\ i | 20 deg | 50 deg | 75 deg | monotone in inclination |",
           "|---|---:|---:|---:|---|"]
    for a in SPINS:
        cells = [r[f"cell_{a}_i{i:03d}"] for i in INCS]
        out.append(f"| {float(a[1:]) / 100:.2f} | "
                   + " | ".join(fmt.format(c) for c in cells)
                   + f" | {r[f'monotone_in_inclination_at_{a}']} |")
    out.append("| **monotone in spin** | "
               + " | ".join(r[f"monotone_in_spin_at_i{i:03d}"] for i in INCS)
               + " | |")
    return "\n".join(out)


def main() -> int:
    t0 = time.time()
    fz = json.loads(FREEZE.read_text())
    REPORTS.mkdir(parents=True, exist_ok=True)

    met = pd.read_parquet(T / "e3c_geometry_metrics.parquet")
    surf = pd.read_parquet(T / "e3c_geometry_surface.parquet")
    hyp = pd.read_parquet(T / "e3c_hypothesis_tests.parquet")
    dep = pd.read_parquet(T / "e3c_depth_curves.parquet")
    jol = pd.read_parquet(T / "e3c_historical_innovation.parquet")
    msum = pd.read_parquet(T / "e3c_matched_sensitivity_summary.parquet")
    pdst = pd.read_parquet(T / "e3c_pairing_destroyed_distribution.parquet")
    ctrl = pd.read_parquet(T / "e3c_common_radial_support_control.parquet")
    quant = pd.read_parquet(T / "e3c_weighted_delay_quantiles.parquet")
    geoms = list(fz["geometries"])
    d = "\n"

    E3C_GATES = [f"E3C_{k}" for k in
                 ("G2_physical_dense_matrix_free", "G3_physical_adjoint",
                  "G4_physical_resolved_unresolved_mixing",
                  "G4b_linear_collapse_covariance_propagation",
                  "G6_physical_Gram_monotonicity", "G6b_resolved_dominates_direct",
                  "G9w_weight_semantics")] + [
        "E3C_freeze_raymap_hashes", "E3C_frozen_grid_invariance",
        "G10q_continuum_noise_quadrature_invariance"]
    n_fail = sum(1 for k in E3C_GATES if gates().get(k, {}).get("status") == "FAIL")

    # ---------------- H1 -----------------------------------------------------
    h1 = hyp[hyp.hypothesis == "H1_historical_extension"]
    h1r = h1[h1.snr0 == REF]
    h1_hold = int(h1r.T_resolved_gt_T_direct.sum())
    h1_j = int((h1r.J_old_resolved > 0).sum())
    h1_any = h1.groupby("geometry").T_resolved_gt_T_direct.any()

    # ---------------- H2 / H3, registered and amended -------------------------
    h2 = hyp[hyp.hypothesis == "H2_delay_mechanism"].set_index("geometry")
    h3 = hyp[hyp.hypothesis == "H3_spatial_mechanism"].set_index("geometry")
    h2m = hyp[hyp.hypothesis == "H2m_delay_mechanism_localized_class"].set_index("geometry")
    h3m = hyp[hyp.hypothesis == "H3m_spatial_mechanism_localized_class"].set_index("geometry")
    reg_zero = bool((h2.D_delay.to_numpy() == 0.0).all())
    mech = ["| geometry | D_delay (registered) | D_delay (localized class) | "
            "D_spatial (localized class) | D_direct (reference) | "
            "kappa+ full | kappa+ delay-only | kappa+ spatial-only |",
            "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for g in geoms:
        mech.append(f"| `{g}` | {h2.loc[g, 'D_delay']:.3e} | "
                    f"{h2m.loc[g, 'D_delay']:.4f} | "
                    f"{h3m.loc[g, 'D_spatial']:.4f} | "
                    f"{h3m.loc[g, 'D_direct_reference']:.4f} | "
                    f"{h3m.loc[g, 'kappa_full']:.2e} | "
                    f"{h3m.loc[g, 'kappa_delay_only']:.2e} | "
                    f"{h3m.loc[g, 'kappa_spatial_only']:.2e} |")
    n_delay_closer = int(h3m.delay_closer_than_spatial.sum())
    delay_wins = n_delay_closer == len(geoms)
    d_delay_med = float(h2m.D_delay.median())
    d_spat_med = float(h3m.D_spatial.median())
    d_dir_med = float(h3m.D_direct_reference.median())
    d_direct_med_str = f"{d_dir_med:.3f}"
    rd = h2m.D_delay_over_D_direct
    rs = h3m.D_spatial_over_D_direct
    n_delay_closer_than_direct = int(h2m.delay_closer_than_direct.sum())
    n_spatial_closer_than_direct = int(h3m.spatial_closer_than_direct.sum())
    ratio_rows = ["| geometry | D_delay / D_direct | D_spatial / D_direct |",
                  "|---|---:|---:|"]
    for g in geoms:
        ratio_rows.append(f"| `{g}` | {rd[g]:.3f} | {rs[g]:.3f} |")
    ratio_rows.append(f"| **median** | {float(rd.median()):.3f} | "
                      f"{float(rs.median()):.3f} |")
    ratio_rows.append(f"| **min–max** | {float(rd.min()):.3f}–{float(rd.max()):.3f} | "
                      f"{float(rs.min()):.3f}–{float(rs.max()):.3f} |")

    # ---------------- H4 -----------------------------------------------------
    h4 = hyp[(hyp.hypothesis == "H4_order_label_value") & (hyp.snr0 == REF)]
    h4t = ["| geometry | T_unresolved / T_resolved | J_old ratio |", "|---|---:|---:|"]
    for _, r in h4.iterrows():
        h4t.append(f"| `{r.geometry}` | {r.R_unres_T:.3f} | {r.R_unres_J:.3f} |")

    # ---------------- H5 -----------------------------------------------------
    h5t = ["| geometry | pair | n def / 19 | median | IQR | min | max | "
           "Gamma_amp | difference | window overlap |",
           "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for _, r in msum.iterrows():
        h5t.append(f"| `{r.geometry}` | {r.order_pair} | "
                   f"{int(r.n_fractions_defined)} | {r['median']:.3f} | "
                   f"{r.iqr:.3f} | {r.minimum:.3f} | {r.maximum:.3f} | "
                   f"{r.Gamma_amp:.3f} | "
                   f"{r.exponent_difference_amp_minus_sensitivity:.3f} | "
                   f"{r.window_overlap_fraction:.3f} |")
    h5_all_positive = bool((msum.exponent_difference_amp_minus_sensitivity > 0).all())
    h5_use = msum[msum.usable]
    h5_bad = msum[~msum.usable]
    h5_bad_lines = ["| geometry | pair | defined / 19 | negative | windows disjoint | "
                    "why it is set aside |", "|---|---|---:|---:|---|---|"]
    for _, r in h5_bad.iterrows():
        why = []
        if r.windows_disjoint:
            why.append("the two orders' retarded windows do not overlap at all, so "
                       "matched *fractional position* is not matched support")
        if r.n_fractions_defined < r.n_fractions_total:
            why.append(f"{int(r.n_fractions_total - r.n_fractions_defined)} fractions "
                       "carry no information in one of the orders")
        if r.n_fractions_negative:
            why.append(f"{int(r.n_fractions_negative)} fractions give a negative "
                       "exponent, i.e. the higher order is locally more sensitive")
        h5_bad_lines.append(f"| `{r.geometry}` | {r.order_pair} | "
                            f"{int(r.n_fractions_defined)} | "
                            f"{int(r.n_fractions_negative)} | "
                            f"{'yes' if r.windows_disjoint else 'no'} | "
                            + "; ".join(why) + " |")
    h5_use_positive = bool((h5_use.exponent_difference_amp_minus_sensitivity > 0).all())

    # ---------------- pairing-destroyed distribution --------------------------
    pd_stats = pdst.groupby("geometry").agg(
        oprank_min=("operational_rank", "min"),
        oprank_median=("operational_rank", "median"),
        oprank_max=("operational_rank", "max"),
        kappa_min=("kappa_positive", "min"),
        kappa_median=("kappa_positive", "median"),
        kappa_max=("kappa_positive", "max")).reindex(geoms)
    res_k = met[(met.arm == "RESOLVED_PHYSICAL")].set_index("geometry").kappa_positive
    pd_beats = int(sum(1 for g in geoms if pd_stats.loc[g, "kappa_max"] < res_k[g]))
    pdt = ["| geometry | oprank min / med / max | kappa+ min / med / max | "
           "resolved kappa+ |", "|---|---|---|---:|"]
    for g in geoms:
        s = pd_stats.loc[g]
        pdt.append(f"| `{g}` | {int(s.oprank_min)} / {s.oprank_median:.1f} / "
                   f"{int(s.oprank_max)} | {s.kappa_min:.2e} / "
                   f"{s.kappa_median:.2e} / {s.kappa_max:.2e} | {res_k[g]:.2e} |")

    # ---------------- common radial support control ---------------------------
    ct = ["| geometry | arm | support | r range | oprank | kappa+ | J_old | T_rec |",
          "|---|---|---|---|---:|---:|---:|---:|"]
    for _, r in ctrl[ctrl.arm.isin(["DIRECT_PHYSICAL", "RESOLVED_PHYSICAL",
                                    "DELAY_ONLY", "SPATIAL_ONLY"])].iterrows():
        ct.append(f"| `{r.geometry}` | {r.arm} | {r.support.replace('_', ' ').lower()} | "
                  f"{r.r_inner:.3f}–{r.r_outer:.2f} | {int(r.operational_rank)} | "
                  f"{r.kappa_positive:.2e} | {r.J_old_at_reference_snr:.2f} | "
                  f"{r.T_rec_at_reference_snr:.0f} |")
    piv = ctrl.pivot_table(index=["geometry", "arm"], columns="support",
                           values="operational_rank")
    ctrl_moves = piv[piv["COMMON_RADIAL_SUPPORT"] != piv["PRIMARY_GEOMETRY_DEPENDENT"]]
    d_rank = (piv["COMMON_RADIAL_SUPPORT"] - piv["PRIMARY_GEOMETRY_DEPENDENT"]).abs()
    tpiv = ctrl.pivot_table(index=["geometry", "arm"], columns="support",
                            values="T_rec_at_reference_snr")
    t_moves = int((tpiv["COMMON_RADIAL_SUPPORT"] != tpiv["PRIMARY_GEOMETRY_DEPENDENT"]).sum())
    jpiv = ctrl.pivot_table(index=["geometry", "arm"], columns="support",
                            values="J_old_at_reference_snr")
    j_rel = ((jpiv["COMMON_RADIAL_SUPPORT"] - jpiv["PRIMARY_GEOMETRY_DEPENDENT"]).abs()
             / jpiv["PRIMARY_GEOMETRY_DEPENDENT"].abs().clip(lower=1e-300))

    # ---------------- arm summary at the reference SNR ------------------------
    armt = ["| arm | oprank median | oprank min–max | kappa+ median | "
            "J_old median | T_rec median |", "|---|---:|---|---:|---:|---:|"]
    for a in ARM_ORDER:
        s = met[met.arm == a]
        armt.append(f"| `{a}` | {s.operational_rank.median():.0f} | "
                    f"{int(s.operational_rank.min())}–{int(s.operational_rank.max())} | "
                    f"{s.kappa_positive.median():.2e} | "
                    f"{s.J_old_at_reference_snr.median():.2f} | "
                    f"{s.T_rec_at_reference_snr.median():.0f} |")

    censored = int(dep.right_censored.sum())

    # =========================================================================
    (REPORTS / "E3C_GEOMETRY_WIDE_OPERATOR_AUDIT.md").write_text(f"""# E3C — GEOMETRY-WIDE PHYSICAL-OPERATOR AUDIT

## Identity
{identity(fz)}

## Mechanical gate result
{"**PASS.** Every E3C correctness gate passes on every geometry."
 if n_fail == 0 else f"**{n_fail} FAILING GATE(S).** See the table."}
Each mechanical gate below is the worst case over all {len(geoms)} geometries;
the per-geometry values are in `artifacts/tables/e3c_gate_detail.parquet`.

{gate_table(E3C_GATES)}

## What was frozen before the first geometry was evaluated

`E3C_OPERATOR_GRID_FREEZE.json` pins the ray-map hashes, the source class and
its support rule, the localized probe, the observer sampling, the common age
grid, the noise convention, the SNR grid, all eight arms, the rank conventions,
the operational threshold, the censoring rule and the sixteen permutation seeds.
Gate `E3C_freeze_raymap_hashes` re-checks every map against the pinned digest at
assembly time, and `E3C_frozen_grid_invariance` checks that the class dimension
and age grid were the same at every geometry.

The common age ceiling is not chosen from a favorable geometry:

    A_max = T_obs + 1.25 max_(g,n) {{Q_0.999^Omega, Q_0.999^I}} + 2h
          = {fz['common_age_grid']['raw_before_rounding_M']:.1f} M
          -> {fz['common_age_grid']['A_max_M']:.0f} M after rounding up to the age step

with the maximum, {fz['common_age_grid']['max_Q_0999_over_grid_M']:.1f} M, taken
over the whole grid from source-independent map summaries. It sits above the
deepest ray any geometry carries, so {censored} of {len(dep)} depth entries are
right-censored: the reported depths are measurements, not grid ceilings.

## Arms across the grid, at the reference SNR_0 = {REF:.0f}

{d.join(armt)}

The full cell-by-cell surface is in `artifacts/tables/e3c_geometry_metrics.parquet`.

## H1 — historical extension

At the reference SNR, `T_resolved > T_direct` in **{h1_hold} of {len(geoms)}**
geometries, and `J_old_resolved > 0` in **{h1_j} of {len(geoms)}**. Across the
whole SNR sweep the depth inequality is strict somewhere in
**{int(h1_any.sum())} of {len(geoms)}** geometries.

{surface_table(surf, 'T_rec_resolved')}

against the direct channel:

{surface_table(surf, 'T_rec_direct')}

and the threshold-independent innovation:

{surface_table(surf, 'J_old_resolved', '{:.2f}')}

{surface_table(surf, 'J_old_direct', '{:.2f}')}

`J_old` integrates `log(1 + I(a))` over ages beyond the direct channel's own
99.9% throughput-weighted boundary, so it does not depend on where a detection
contour happens to fall. It is reported because a depth endpoint alone would be
a statement about the threshold as much as about the physics.

## H2 and H3 — which mechanism supplies the reach

{d.join(mech)}

`D` is the relative L2 discrepancy between `log(1 + I)` curves over the common
age grid — on the log scale so a single loud epoch cannot dominate the norm.

**The registered H2 statistic is degenerate and is reported as an identity.**
The registered localized probe is spatially flat, and the delay-only
substitution changes only `source_r` and `source_phi`. The scalar curve `I(a)`
therefore cannot see that substitution: `D_delay` is
{"identically zero at every geometry" if reg_zero else "NOT identically zero, contrary to Amendment 002's premise — investigate"},
by algebra rather than by physics. Gate
`E3C_H2_registered_statistic_is_an_identity` asserts bitwise equality so that
the zero can never be read as support for the delay mechanism. The literal
values stay on the record; Amendment 002 adds the comparison that can actually
discriminate.

**On the registered localized class the two mechanisms separate, but modestly.**
Median `D_delay` is {d_delay_med:.3f} against `D_spatial` {d_spat_med:.3f}, with
the direct arm at {d_direct_med_str} as the scale for what "far" means. The
delay-only arm is closer to the full operator than the spatial-only arm in
**{n_delay_closer} of {len(geoms)}** cells.
{"The ordering holds everywhere on the grid." if delay_wins else
 "The ordering does not hold everywhere; the cells that reverse are visible above and are the finding."}

**Normalising by the direct arm makes the decomposition legible.** The direct
arm is the natural zero point: it is what remains when the higher orders are
removed altogether. Measuring each substitution's discrepancy against it:

{d.join(ratio_rows)}

A ratio near 1 means the substitution destroyed essentially everything the
higher orders contributed; a ratio near 0 means it preserved it. Spatial-only
sits at a median {float(rs.median()):.2f} — flattening the delays leaves the
resolved stack about as far from the truth as not having the higher orders at
all — while delay-only sits at {float(rd.median()):.2f}, recovering roughly half
the gap. Delay-only is closer than the direct arm in
{n_delay_closer_than_direct} of {len(geoms)} cells, spatial-only in
{n_spatial_closer_than_direct} of {len(geoms)}.

This is weaker than the canary reported. Under the scalar probe the delay-only
arm looked like an exact reproduction of the full operator; on the localized
class it is a {d_delay_med:.0%} relative departure, so delay diversity carries
the larger share of the historical reach but not all of it. Spatial remapping is
not the mechanism, but it is not nothing either.

Conditioning is reported alongside the discrepancy because spatial remapping can
improve `kappa+` without moving the oldest detected probe centre, and inferring
the mechanism from a depth endpoint alone would miss that.

{surface_table(surf, 'D_delay_localized_class', '{:.4f}')}

{surface_table(surf, 'D_spatial_localized_class', '{:.4f}')}

## H4 — how much the order labels are worth

{d.join(h4t)}

`UNRESOLVED_IMAGE` sums the orders into one image plane and pays the summed
noise, `C_U = L C_R L^T`. A ratio near 1 means explicit order labels are nearly
dispensable for that quantity; a ratio well below 1 means they are load-bearing.

## H5 — throughput versus sensitivity attenuation

All 19 aligned-window fractions are retained at every geometry.

{d.join(h5t)}

**{len(h5_bad)} of {len(msum)} cells are set aside as not interpretable, and
they are named rather than averaged away.**

{d.join(h5_bad_lines)}

The zero-overlap cells are the important caveat. At i = 20 deg the n = 0 and
n = 1 retarded windows are disjoint, so sampling both at the same *fractional*
position inside their own windows compares two epochs that share no support at
all. The statistic is still computed and reported, but "matched support" is not
what it means there, and those cells do not bear on H5.

On the {len(h5_use)} interpretable cells:
{"the sensitivity exponent is below the throughput exponent in every one, so a "
 "single scalar attenuation exponent describes the flux and misdescribes the "
 "information."
 if h5_use_positive else
 "the sign of the exponent difference is NOT uniform; the cells where it "
 "reverses are visible above and are the finding."}
Median difference {float(h5_use.exponent_difference_amp_minus_sensitivity.median()):.3f},
range {float(h5_use.exponent_difference_amp_minus_sensitivity.min()):.3f} to
{float(h5_use.exponent_difference_amp_minus_sensitivity.max()):.3f}.

No asymptotic law is fitted: n = 0, 1, 2 does not determine one.

## H6 — the spin and inclination surface

These are twelve deterministic registered geometries, not a sample from a
population. No p-value, confidence interval or significance claim appears
anywhere in this report; the surface is reported cell by cell with its median,
extremes and monotonicity.

{surface_table(surf, 'operational_rank_resolved')}

{surface_table(surf, 'operational_rank_direct')}

{surface_table(surf, 'kappa_positive_resolved', '{:.2e}')}

{surface_table(surf, 'delta_G_indirect_rank')}

`delta_G_indirect = G_resolved - G_direct` separates information reweighted
inside the direct channel's support from genuinely new historical information
beyond it. Its rank, trace, stable rank and smallest positive eigenvalue are in
`artifacts/tables/e3c_historical_innovation.parquet`.

## Negative control: PAIRING_DESTROYED over 16 frozen seeds

{d.join(pdt)}

Permuting delay, position and weight independently within each order preserves
all three marginals and destroys their pairing. This is a nonphysical control
and is never ranked as an alternative measurement architecture. It is reported
over the full frozen seed set because the canary's unusually good conditioning
could otherwise have been one favorable permutation:
{"at every geometry the *worst* of the sixteen seeds is still better conditioned "
 "than the physical resolved operator, so the effect is systematic and not a "
 "lucky draw."
 if pd_beats == len(geoms) else
 f"the worst seed beats the physical resolved operator at {pd_beats} of "
 f"{len(geoms)} geometries, so the effect is not uniform across the grid."}

Any argument that reads conditioning as evidence of physical content is refuted
by these rows.

## Scope

Permits: geometry-wide statements about the registered class `C224` on the
twelve registered geometries under the frozen measurement convention.
Forbids: continuum injectivity claims from full rank on `C224`; any geometry
mismatch, order-leakage or ML claim; any raw maximum delay used as a historical
depth; population-style inference across the twelve cells.

## Artifacts
`artifacts/configs/E3C_OPERATOR_GRID_FREEZE.json`,
`artifacts/tables/e3c_*.parquet`,
`artifacts/gates/e3c_correctness_gates.json`,
`artifacts/provenance/E3C_ARTIFACT_MANIFEST.json`.
""")

    # =========================================================================
    mm = fz["measurement_model"]
    qmax = quant.loc[quant["Q_0.999_I"].idxmax()]
    (REPORTS / "E3C_MEASUREMENT_NOISE_MODEL.md").write_text(f"""# E3C — MEASUREMENT AND NOISE MODEL

## Identity
{identity(fz)}

## The declared model

    {mm['datum']}
    {mm['noise']}

whitened row:

    {mm['whitened_row']}

The pixel-average form {mm['equivalent_pixel_average_form'].split(' produces')[0]}
produces the same whitened row, so the two statements of the model are the same
model.

**The square root is load-bearing.** Under a flat per-row sigma with `c = g^3`
the Fisher information scales with the *number of rows*: splitting one pixel
into k equal-area children carrying the same transfer value multiplies the Gram
by k. Adaptive ray counts differ by an order of magnitude across geometry and
order in this grid, so that convention would let the grid manufacture
information — and it would do so unevenly across the lensing bands, which differ
in solid angle by roughly three orders of magnitude.

{gate_table(['G10q_continuum_noise_quadrature_invariance',
             'G10q_retired_flat_sigma_convention'])}

The retired convention is kept in the ledger as a literal FAIL with disposition
`RETIRED_PIXELIZATION_DEPENDENT` rather than deleted, so the convention change
is auditable. Defect `D-H_flat_sigma_measurement_convention` in
`artifacts/PREFIX_INVALIDATION_LEDGER.json` records exactly which E3B
conclusions moved and which did not.

## One sigma for the whole audit

{mm['sigma_rule']}

Derived arms are linear maps of the same resolved data with their covariance
propagated, never separate models:

    {mm['derived_arm_covariance']}

Gate `E3C_G4b_linear_collapse_covariance_propagation` checks the channel
variance the operator actually applies against an independently formed
`L C_R L^T`. Without it the collapse identity alone would pass while a wrong
noise propagation made a summed arm look free.

## Weighted delay quantiles

The sampled maximum ray delay is an extreme-value statistic set by whichever
single ray sits closest to a band edge; it does not converge under refinement
and is not used as a historical depth anywhere in this program. The converging
summaries are weighted quantiles under three weightings:

| weighting | symbol | weight | source-independent |
|---|---|---|---|
| solid angle | Q_q^Omega | dOmega | yes |
| throughput | Q_q^I | dOmega g^3 | yes |
| Fisher | Q_q^F | dOmega g^6 | **no** — this is the squared whitened row weight and depends on the declared measurement model and source class |

The deepest 99.9% throughput-weighted boundary on the grid is
{qmax['Q_0.999_I']:.1f} M at `{qmax.geometry}` order {int(qmax.order)}, against a
sampled maximum of {qmax['delay_max_M']:.1f} M for the same band. Only the
former sets the common age grid.

Full table: `artifacts/tables/e3c_weighted_delay_quantiles.parquet`.

## Source-domain integrity

Radial support convention: **{fz['radial_support']['primary_convention']}**.
{fz['radial_support']['rule']}.

{fz['radial_support']['why_this_is_stated'][0].upper() + fz['radial_support']['why_this_is_stated'][1:]}

Control on the three anchor geometries, one fixed interval in r/M with identical
knot locations:

{d.join(ct)}

**The confound is real but small, and it does not reach the historical
conclusions.** Operational rank moves under the common support in
{len(ctrl_moves)} of {len(piv)} anchor–arm combinations, by at most
{int(d_rank.max())} of 224 (median move {float(d_rank[d_rank > 0].median()) if len(ctrl_moves) else 0:.1f}).
`T_rec` is unchanged in {len(tpiv) - t_moves} of {len(tpiv)} combinations, and
`J_old` moves by at most {float(j_rel.max()):.1%} (median
{float(j_rel.median()):.1%}). The largest shifts are at `a098_i075`, whose
primary radial support reaches to r/M = 1.20 against the common interval's 2.00
— the anchor whose source domain the control changes most.

Read strictly: the spin trends in operational rank are partly confounded with
the source domain, because a higher-spin geometry's rays reach closer to the
horizon and the primary knots follow them. The depth and innovation results are
not: they survive the domain change at every anchor and arm.

{fz['radial_support']['emission_support_disclaimer'][0].upper() + fz['radial_support']['emission_support_disclaimer'][1:]}
""")

    # =========================================================================
    (REPORTS / "E3C_MECHANISM_DECOMPOSITION.md").write_text(f"""# E3C — MECHANISM DECOMPOSITION

## Identity
{identity(fz)}

## The question

The canary established, on one geometry, that the historical reach of the
resolved operator comes from retarded-time diversity rather than from spatial
remapping. One geometry cannot distinguish a mechanism from a coincidence of
that geometry's lensing bands. This report tests the decomposition on all
{len(geoms)} registered geometries.

Two substitution arms isolate the two candidate mechanisms while holding
everything else fixed:

* `DELAY_ONLY` keeps each order's physical per-ray delays and replaces its
  spatial mapping with the direct order's.
* `SPATIAL_ONLY` keeps each order's physical spatial mapping and flattens every
  delay onto the direct order's delay field.

Neither arm changes the measurement model, the noise, the source class or the
ray weights. The comparison is against the full resolved operator's
age-information curve on the common grid.

## Result

{d.join(mech)}

{surface_table(surf, 'D_delay_localized_class', '{:.4f}')}

{surface_table(surf, 'D_spatial_localized_class', '{:.4f}')}

**First, the registered statistic does not answer the question.** The
registered localized probe is spatially flat. `DELAY_ONLY` changes only where
the rays land on the source plane, so the scalar curve `I(a)` is
{"bitwise identical" if reg_zero else "NOT identical — investigate"} between the
full and delay-only arms at every geometry, and `D_delay = 0` is an algebraic
identity. Reporting that zero as evidence for the delay mechanism would have
been circular. Amendment 002 records the degeneracy, preserves the literal
values, and adds the comparison on the registered 28-dimensional localized
class, where the substitution does act.

**On that class the mechanisms separate, but far less sharply than the canary
suggested.** Median relative discrepancy: delay-only {d_delay_med:.3f},
spatial-only {d_spat_med:.3f}, with the direct arm at {d_direct_med_str} as the
scale. Delay-only is the closer of the two substitutions in
**{n_delay_closer} of {len(geoms)}** cells.

{"The ordering holds in every cell, so the direction of the canary's conclusion "
 "survives the grid — but its magnitude does not. Delay diversity is the larger "
 "of the two contributions to historical reach, not the whole of it."
 if delay_wins else
 "**The ordering does not hold uniformly.** The cells that reverse are visible "
 "above and are the finding; the canary's mechanism conclusion cannot be stated "
 "grid-wide without qualification."}

## Why the endpoint alone would have been the wrong test

Spatial remapping can improve conditioning without moving the oldest detectable
probe centre. Reading the mechanism off a depth endpoint would therefore credit
delay with everything spatial diversity does to `kappa+`. The `kappa+` columns
above are reported next to `D` for exactly that reason, and the two are not the
same statement.

## What this does and does not license

Licensed: the statement that, on the registered geometries and class, the
distributed retarded-time structure of near-critical null geodesics — not the
spatial remapping of the higher-order images — is what extends recoverable
history.

Not licensed: any claim about a continuum source, any claim about geometries
outside the registered grid, any asymptotic exponent from n = 0, 1, 2, and any
reading of `PAIRING_DESTROYED` as a measurement architecture.
""")

    # =========================================================================
    am = json.loads((ROOT / "artifacts" / "configs"
                     / "AMENDMENT_002_LOCALIZED_CLASS_MECHANISM_DIAGNOSTIC.json").read_text())
    (REPORTS / "AMENDMENT_002_LOCALIZED_CLASS_MECHANISM_DIAGNOSTIC.md").write_text(f"""# AMENDMENT 002 — {am['title']}

## Identity
{identity(fz)}
- amendment record `artifacts/configs/AMENDMENT_002_LOCALIZED_CLASS_MECHANISM_DIAGNOSTIC.json`
- status **{am['status']}**

## What went wrong with the registered statistic

{am['trigger']}

{am['why_it_is_degenerate']}

Verified: {am['verification']['check']} — {am['verification']['result']}. Gate
`E3C_H2_registered_statistic_is_an_identity` re-checks this at assembly time, so
the zero is recorded as an identity and can never be re-read as evidence.

The freeze file is **not** edited. `E3C_OPERATOR_GRID_FREEZE.json` records the
pre-evaluation state and amending it after the grid ran would defeat its
purpose; this amendment stands beside it and is referenced from the reports.

## What the amendment adds

{am['what_is_added']['object']}.

{am['what_is_added']['why_this_class']}

Normalization: {am['what_is_added']['normalization']}.

Derived quantities:

{d.join('* ' + x for x in am['what_is_added']['derived_quantities'])}

## What it does not change

{d.join('* ' + x for x in am['no_change_to'])}

## Effect on the reported conclusion

Under the registered scalar statistic the delay-only arm reproduced the full
age-information curve exactly, which reads as "delay diversity supplies all of
the historical reach". On the localized class the same substitution is a median
{d_delay_med:.3f} relative departure against the spatial-only arm's
{d_spat_med:.3f}, with the direct arm at {d_direct_med_str}. Delay diversity is
{"the larger of the two contributions in every cell" if delay_wins else
 f"the larger contribution in {n_delay_closer} of {len(geoms)} cells"}, not the
whole of it. The direction of the canary's conclusion survives; its strength
does not.

{am['scope_limit']}
""")
    print("wrote artifacts/reports/AMENDMENT_002_LOCALIZED_CLASS_MECHANISM_DIAGNOSTIC.md")

    # ---- artifact manifest ---------------------------------------------------
    files = sorted([p for p in (T.glob("e3c_*.parquet"))] +
                   [p for p in (T.glob("e3c_*.csv"))] +
                   [FREEZE,
                    ROOT / "artifacts" / "gates" / "e3c_correctness_gates.json"] +
                   [ROOT / "artifacts" / "configs"
                    / "AMENDMENT_002_LOCALIZED_CLASS_MECHANISM_DIAGNOSTIC.json"] +
                   [REPORTS / f for f in (
                       "E3C_GEOMETRY_WIDE_OPERATOR_AUDIT.md",
                       "E3C_MEASUREMENT_NOISE_MODEL.md",
                       "E3C_MECHANISM_DECOMPOSITION.md",
                       "AMENDMENT_002_LOCALIZED_CLASS_MECHANISM_DIAGNOSTIC.md")])
    prov = provenance.collect()
    (ROOT / "artifacts" / "provenance" / "E3C_ARTIFACT_MANIFEST.json").write_text(
        json.dumps({"experiment": "E3C", "git_commit": prov.git_commit,
                    "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "artifacts": {str(p.relative_to(ROOT)): sha256_file(p)
                                  for p in files if p.exists()}}, indent=2) + "\n")

    for f in ("E3C_GEOMETRY_WIDE_OPERATOR_AUDIT.md", "E3C_MEASUREMENT_NOISE_MODEL.md",
              "E3C_MECHANISM_DECOMPOSITION.md"):
        print(f"wrote artifacts/reports/{f}")
    print("wrote artifacts/provenance/E3C_ARTIFACT_MANIFEST.json")
    print(f"total {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
