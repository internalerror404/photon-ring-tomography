#!/usr/bin/env python3
"""Build the manuscript figures from canonical parquet only.

PAPER_I_EDITORIAL_RULING_022 item 9. Four primary figures, one per claim the
paper actually rests on; there is no supplementary tier, because a figure that
is not worth placing in the argument is not worth carrying. Every value plotted
is read from a table the claim ledger already cites, so a figure cannot drift
from the text: if a number moves, the figure moves with it or the build fails.

Print first. The manuscript renders in a light and a dark theme, and a figure
that inverts with the theme would have to carry two colour sets and two
validations for a document whose PDF is the artifact of record. These are drawn
on an explicit white surface and the page keeps them on a white card in both
themes.

Palette: slots 1 and 2 of the validated categorical set (blue, orange), which
clear the all-pairs colour-vision and normal-vision floors on a white surface.
Every series is also direct-labelled, so identity never rests on colour.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from phrt.numerics import pin

pin()

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

T = ROOT / "artifacts" / "tables"
OUT = ROOT / "artifacts" / "manuscript" / "figures"

BLUE, ORANGE = "#2a78d6", "#eb6834"
INK, MUTED, RULE = "#14161a", "#5b6270", "#d8dce4"
REF = 100.0
CLAIM = "L896_radial_enriched"

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["DejaVu Serif"],
    "font.size": 8.5,
    "axes.titlesize": 9,
    "axes.labelsize": 8.5,
    "axes.edgecolor": RULE,
    "axes.labelcolor": INK,
    "text.color": INK,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "axes.grid": True,
    "grid.color": RULE,
    "grid.linewidth": 0.6,
    "grid.alpha": 0.9,
    "legend.frameon": False,
    "legend.fontsize": 8,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "savefig.facecolor": "white",
    "lines.linewidth": 1.6,
})


def _finish(fig, name: str, caption: str) -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    for ext in ("pdf", "png"):
        fig.savefig(OUT / f"{name}.{ext}", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"  {name}.png / .pdf")
    return {"name": name, "caption": caption}


def fig_depth() -> dict:
    """Recoverable depth: flat in spin, stepped in inclination."""
    d = pd.read_parquet(T / "e3c_depth_curves.parquet")
    d = d[(d.snr0 == REF) & d.arm.isin(["DIRECT_PHYSICAL", "RESOLVED_PHYSICAL"])]
    g = (d.groupby(["inclination_deg", "spin", "arm"])
         .oldest_detectable_age_probe.median().reset_index())
    incs = sorted(g.inclination_deg.unique())
    spins = sorted(g.spin.unique())
    # Spin is plotted on evenly spaced categorical positions: 0.90 and 0.98 are
    # 0.08 apart on a linear axis and their labels collide, which is a
    # rendering artefact of the sampling and not a fact about the physics.
    pos = {v: i for i, v in enumerate(spins)}
    fig, axes = plt.subplots(1, len(incs), figsize=(7.0, 2.5), sharey=True)
    for ax, inc in zip(axes, incs):
        sub = g[g.inclination_deg == inc]
        for arm, colour, label, dy in (("RESOLVED_PHYSICAL", BLUE, "resolved", 7),
                                       ("DIRECT_PHYSICAL", ORANGE, "direct", -13)):
            row = sub[sub.arm == arm].sort_values("spin")
            xs = [pos[v] for v in row.spin]
            ax.plot(xs, row.oldest_detectable_age_probe, "o-", color=colour,
                    markersize=4.5, label=label, clip_on=False, zorder=3)
            if inc == incs[0]:
                ax.annotate(label, (xs[0],
                                    row.oldest_detectable_age_probe.iloc[0]),
                            textcoords="offset points", xytext=(-2, dy),
                            color=colour, fontsize=8, ha="left")
        ax.set_title(f"$i = {inc:.0f}^\\circ$", color=INK)
        ax.set_xlabel("spin $a^*$")
        ax.set_xticks(list(pos.values()))
        ax.set_xticklabels([f"{v:g}" for v in spins])
        ax.set_xlim(-0.4, len(spins) - 0.6)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
    axes[0].set_ylabel("oldest detectable age (M)")
    axes[0].set_ylim(0, 165)
    return _finish(
        fig, "fig1_depth_inclination_not_spin",
        "Recoverable depth at the reference SNR is flat across four spins at "
        "every inclination and steps sharply with inclination. The resolved "
        "stack sees deeper than the direct image at all twelve geometries; "
        "the margin is largest where the direct image is shallowest.")


def fig_shiva() -> dict:
    """Identifiability falls under enrichment while reach does not move."""
    sp = pd.read_parquet(T / "e3d_class_spectra.parquet")
    dc = pd.read_parquet(T / "e3d_depth_by_class.parquet")
    sp = sp[sp.arm == "RESOLVED_PHYSICAL"]
    frac = (sp.assign(f=sp.operational_rank / sp.source_dimension)
            .groupby(["source_class", "source_dimension"]).f.median()
            .reset_index().sort_values("source_dimension"))
    dep = (dc[(dc.snr0 == REF) & (dc.arm == "RESOLVED_PHYSICAL")]
           .groupby("source_class").T_rec_best_mode.median().reset_index())
    dep = frac.merge(dep, on="source_class").sort_values("source_dimension")

    fig, (a1, a2) = plt.subplots(2, 1, figsize=(4.8, 4.2), sharex=True)
    a1.plot(frac.source_dimension, frac.f, "o-", color=ORANGE, markersize=5,
            clip_on=False, zorder=3)
    a1.set_ylabel("operational rank fraction")
    a1.set_ylim(0.6, 1.0)
    a1.annotate("identifiability falls", (frac.source_dimension.iloc[-1],
                                          frac.f.iloc[-1]),
                textcoords="offset points", xytext=(-6, 12), ha="right",
                color=ORANGE, fontsize=8)
    a2.plot(dep.source_dimension, dep.T_rec_best_mode, "o-", color=BLUE,
            markersize=5, clip_on=False, zorder=3)
    a2.set_ylabel("recoverable depth (M)")
    a2.set_ylim(0, 160)
    a2.set_xlabel("declared source-class dimension")
    a2.annotate("reach does not move", (dep.source_dimension.iloc[-1],
                                        dep.T_rec_best_mode.iloc[-1]),
                textcoords="offset points", xytext=(-6, 12), ha="right",
                color=BLUE, fontsize=8)
    for ax in (a1, a2):
        ax.set_xticks(sorted(frac.source_dimension))
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
    return _finish(
        fig, "fig2_shiva_effect",
        "The Shiva effect, in one geometry family. Enriching the declared "
        "temporal class drives the resolved arm's operational-rank fraction "
        "down while the deepest recoverable epoch is unchanged. "
        "Identifiability and historical reach are different quantities and "
        "they move independently.")


def fig_results() -> dict:
    """The two held-out results, each on its own axis and its own units."""
    sd = pd.read_parquet(T / "r1_stable_depth.parquet")
    r1 = sd[sd.primary & (sd.snr0 == REF) & (sd.estimator == "TSVD")
            & (sd.regime == "IN_CLASS_ID")]
    arms = ["DIRECT_PHYSICAL", "RESOLVED_PHYSICAL"]
    spans = [float(r1[r1.arm == a].L_stable_anchor.iloc[0]) for a in arms]

    ep = pd.read_parquet(T / "hmt2_main_endpoint.parquet")
    ep = ep[(ep["class"] == CLAIM) & (ep.snr0 == REF)
            & (ep.arm == "RESOLVED_PHYSICAL")]

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.2, 2.7),
                                 gridspec_kw={"width_ratios": [1, 1.5],
                                              "wspace": 0.55})
    a1.bar(["direct", "resolved"], spans, width=0.5,
           color=[ORANGE, BLUE], zorder=3)
    for x, v in enumerate(spans):
        a1.annotate(f"{v:.0f} M", (x, v), textcoords="offset points",
                    xytext=(0, 4), ha="center", fontsize=8, color=INK)
    a1.axhline(spans[0] + 8.0, color=MUTED, lw=1.0, ls=(0, (4, 3)), zorder=2)
    a1.annotate("declared +8 M threshold", (-0.45, spans[0] + 8.0), ha="left",
                va="bottom", fontsize=7.5, color=MUTED)
    a1.set_ylabel("anchored stable span (M)")
    a1.set_title("emissivity level", color=INK)
    a1.set_ylim(0, max(spans) * 1.25)
    a1.grid(axis="x", visible=False)

    rows, ys = [], []
    for i, (est, colour, lab) in enumerate((("RIDGE_IDENTITY", BLUE, "ridge"),
                                            ("TSVD", ORANGE, "TSVD"))):
        r = ep[ep.estimator == est].iloc[0]
        for j, (key, tag) in enumerate((("PHYSICAL_END_TO_END", "physical"),
                                        ("CLASS_CONDITIONAL", "class-cond."))):
            y = i * 2 + j
            med = float(r[f"{key}_median_reduction"])
            lo = float(r[f"{key}_ci_low"])
            a2.plot([lo, med], [y, y], color=colour, lw=1.8,
                    solid_capstyle="round", zorder=3)
            a2.plot([med], [y], "o", color=colour, markersize=5.5, zorder=4)
            rows.append(f"{lab}, {tag}")
            ys.append(y)
    a2.axvline(0.10, color=MUTED, lw=1.0, ls=(0, (4, 3)), zorder=2)
    a2.annotate("0.10 floor", (0.10, len(ys) - 0.3), fontsize=7.5,
                color=MUTED, ha="center", va="bottom")
    a2.axvline(0.0, color=INK, lw=0.8, zorder=2)
    a2.set_yticks(ys)
    a2.set_yticklabels(rows)
    a2.set_ylim(-0.6, len(ys) - 0.05)
    a2.set_xlim(0, 0.24)
    a2.set_xlabel("median morphology error reduction")
    a2.set_title("morphology", color=INK)
    a2.grid(axis="y", visible=False)
    for ax in (a1, a2):
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
    return _finish(
        fig, "fig3_two_held_out_results",
        "The two held-out historical inverse results, on separate axes because "
        "they measure different things in different units. Left: "
        "STABLE_BASELINE_INCLUSIVE_EMISSIVITY_LEVEL_RECONSTRUCTION, the "
        "anchored stable span against the threshold declared in advance. "
        "Right: AGGREGATE_RESOLUTION_AWARE_MORPHOLOGY_ERROR_REDUCTION, median "
        "reduction with the paired bootstrap lower bound as the bar, against "
        "the 0.10 materiality floor. Both estimators, both targets.")


def fig_families() -> dict:
    """Where the morphology aggregate comes from, and where it does not."""
    fam = pd.read_parquet(T / "hmt2_main_per_family.parquet")
    q = fam[(fam["class"] == CLAIM) & (fam.arm == "RESOLVED_PHYSICAL")
            & (fam.snr0 == REF)].sort_values(
                ["PHYSICAL_END_TO_END_median_reduction", "estimator"])
    order = (q.groupby("family").PHYSICAL_END_TO_END_median_reduction.max()
             .sort_values().index.tolist())

    fig, ax = plt.subplots(figsize=(6.0, 3.1))
    for i, family in enumerate(order):
        for k, (est, colour, lab) in enumerate(
                (("RIDGE_IDENTITY", BLUE, "ridge"), ("TSVD", ORANGE, "TSVD"))):
            r = q[(q.family == family) & (q.estimator == est)].iloc[0]
            y = i + (0.16 if k == 0 else -0.16)
            med = float(r.PHYSICAL_END_TO_END_median_reduction)
            lo = float(r.PHYSICAL_END_TO_END_ci_low)
            ax.plot([lo, med], [y, y], color=colour, lw=1.6,
                    solid_capstyle="round", zorder=3)
            ax.plot([med], [y], "o", color=colour, markersize=5,
                    zorder=4, label=lab if i == 0 else None)
            if bool(r.PHYSICAL_END_TO_END_material):
                ax.plot([med], [y], "o", markersize=9, markerfacecolor="none",
                        markeredgecolor=colour, markeredgewidth=1.0, zorder=4)
    ax.axvline(0.0, color=INK, lw=0.8, zorder=2)
    ax.axvline(0.10, color=MUTED, lw=1.0, ls=(0, (4, 3)), zorder=2)
    ax.annotate("0.10 floor", (0.10, len(order) - 0.32), fontsize=7.5,
                color=MUTED, ha="center", va="bottom")
    ax.set_yticks(range(len(order)))
    ax.set_yticklabels([f.replace("_", " ") for f in order])
    ax.set_ylim(-0.6, len(order) - 0.02)
    ax.set_xlabel("median morphology error reduction, physical target")
    ax.grid(axis="y", visible=False)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.legend(loc="lower right")
    return _finish(
        fig, "fig4_family_heterogeneity",
        "FAMILY_HETEROGENEITY. Per-family median reduction with the paired "
        "bootstrap lower bound as the bar; a ringed marker is a cell that "
        "clears the declared floor. Five of twelve family-estimator cells are "
        "material, the simplest source in the bank is negative under both "
        "estimators, and ten truths per family makes every interval here wide. "
        "The aggregate is an average over this spread, not a uniform gain.")


def main() -> int:
    print("figures:")
    figs = [fig_depth(), fig_shiva(), fig_results(), fig_families()]
    import json

    (OUT / "FIGURES.json").write_text(json.dumps(
        {"schema": "phrt-figures/1",
         "hierarchy": "all four are primary; the paper carries no "
                      "supplementary figure tier",
         "figures": [{"number": i + 1, **f} for i, f in enumerate(figs)]},
        indent=2) + "\n")
    print(f"wrote {(OUT / 'FIGURES.json').relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
