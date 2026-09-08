#!/usr/bin/env python3
"""Ruling 039: regenerate the two figures whose assets assert corrected claims.

New output paths; the canonical figures are untouched. Nothing is computed here
beyond selecting and aggregating archived table rows -- no operator, no
reconstruction, no new sampling. Every selector is recorded in
FIGURE_MANIFEST_039.json.

Figure 1 asserted "recoverable depth ... flat across four spins" in its own
title. It plotted the oldest detectable age probe, which is a supremum of a
threshold mask, and the anchor-connected span -- the statistic that is history
from the geometry's anchor -- does vary with spin at 75 degrees. Both are now
drawn, named, and the spin claim is confined to the statistic that supports it.

Figure 2 said "enriching the declared temporal class". The E3D ladder changes
both spatial and temporal factors, and its depth panel plotted the localized
directional depth under the label "recoverable depth". Both are corrected.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt          # noqa: E402
import pandas as pd                       # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
T = ROOT / "artifacts" / "tables"
OUT = ROOT / "docs/revisions/mahakal_v4_1/manuscript039/figures"
REF = 100.0
INK, BLUE, ORANGE, GREY = "#1b1b1b", "#2166ac", "#d6604d", "#8c8c8c"
plt.rcParams.update({"font.size": 8.5, "axes.edgecolor": INK,
                     "axes.labelcolor": INK, "text.color": INK,
                     "xtick.color": INK, "ytick.color": INK,
                     "figure.dpi": 200, "savefig.bbox": "tight"})


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def fig1() -> dict:
    src = T / "e3c_depth_curves.parquet"
    d = pd.read_parquet(src)
    sel = ("snr0 == 100 and arm in (DIRECT_PHYSICAL, RESOLVED_PHYSICAL); "
           "median over source_class within (inclination_deg, spin, arm)")
    d = d[(d.snr0 == REF)
          & d.arm.isin(["DIRECT_PHYSICAL", "RESOLVED_PHYSICAL"])]
    g = (d.groupby(["inclination_deg", "spin", "arm"])[
        ["oldest_detectable_age_probe",
         "contiguous_detectable_span_from_anchor_M"]].median().reset_index())
    incs = sorted(g.inclination_deg.unique())
    spins = sorted(g.spin.unique())
    pos = {v: i for i, v in enumerate(spins)}

    fig, axes = plt.subplots(2, len(incs), figsize=(7.2, 4.4), sharey="row",
                             sharex=True)
    rows = (("oldest_detectable_age_probe",
             "oldest detectable\nage probe (M)"),
            ("contiguous_detectable_span_from_anchor_M",
             "anchor-connected\nspan (M)"))
    for r, (col, ylab) in enumerate(rows):
        for c, inc in enumerate(incs):
            ax = axes[r, c]
            sub = g[g.inclination_deg == inc]
            for arm, colour, lab in (("RESOLVED_PHYSICAL", BLUE, "resolved"),
                                     ("DIRECT_PHYSICAL", ORANGE, "direct")):
                row = sub[sub.arm == arm].sort_values("spin")
                ax.plot([pos[v] for v in row.spin], row[col], "o-",
                        color=colour, markersize=4.5, label=lab,
                        clip_on=False, zorder=3)
            if r == 0:
                ax.set_title(f"$i = {inc:.0f}^\\circ$", color=INK)
            if r == 1:
                ax.set_xlabel("spin $a^*$")
                ax.set_xticks(list(pos.values()))
                ax.set_xticklabels([f"{v:g}" for v in spins])
            ax.set_xlim(-0.4, len(spins) - 0.6)
            for side in ("top", "right"):
                ax.spines[side].set_visible(False)
        axes[r, 0].set_ylabel(ylab)
    axes[0, 0].set_ylim(0, 165)
    axes[1, 0].set_ylim(0, 165)
    axes[0, 0].legend(frameon=False, loc="upper left", fontsize=7.5)
    axes[1, 2].annotate("varies with spin", (pos[0.0], 112),
                        textcoords="offset points", xytext=(4, -14),
                        color=GREY, fontsize=7.5)
    fig.suptitle("Two reach statistics, and only one of them is flat in spin",
                 fontsize=9.5, color=INK, y=1.0)
    p = OUT / "fig1_reach_two_statistics_039.png"
    fig.savefig(p)
    plt.close(fig)
    return {
        "file": p.name, "sha256": sha(p),
        "source_table": str(src.relative_to(ROOT)),
        "source_sha256": sha(src), "selector": sel,
        "plotted": ["oldest_detectable_age_probe",
                    "contiguous_detectable_span_from_anchor_M"],
        "replaces": "artifacts/manuscript/figures/"
                    "fig1_depth_inclination_not_spin.png",
        "why": "the old asset asserted 'recoverable depth ... flat across four "
               "spins' in its own title while plotting a threshold supremum; "
               "the anchor-connected span varies with spin at 75 degrees",
        "caption": "**Two reach statistics.** Top: the oldest detectable age "
                   "probe, the supremum of the detectable age set, which is "
                   "flat across the four sampled spins at every inclination. "
                   "Bottom: the anchor-connected span, the contiguous passing "
                   "interval from each geometry's own anchor, which is not - "
                   "at 75 degrees the resolved span is 112 M at spin 0 and "
                   "116 M at the other three. A supremum being flat in spin "
                   "does not establish spin independence of the reach that "
                   "connects to the anchor. Reference SNR; median over source "
                   "class.",
    }


def fig2() -> dict:
    sp_src, dc_src = (T / "e3d_class_spectra.parquet",
                      T / "e3d_depth_by_class.parquet")
    sp = pd.read_parquet(sp_src)
    dc = pd.read_parquet(dc_src)
    sp = sp[sp.arm == "RESOLVED_PHYSICAL"]
    frac = (sp.assign(f=sp.operational_rank / sp.source_dimension)
            .groupby(["source_class", "source_dimension", "n_radial",
                      "n_azimuthal", "n_temporal"])
            .agg(f=("f", "median"), rank=("operational_rank", "median"))
            .reset_index().sort_values("source_dimension"))
    dep = (dc[(dc.snr0 == REF)
              & dc.arm.isin(["DIRECT_PHYSICAL", "RESOLVED_PHYSICAL"])]
           .groupby(["source_class", "arm"])
           .T_rec_best_mode.median().reset_index())
    order = list(frac.source_class)
    x = list(range(len(order)))

    fig, (a1, a2, a3) = plt.subplots(3, 1, figsize=(5.4, 5.8), sharex=True)
    a1.plot(x, frac.f, "o-", color=ORANGE, markersize=5, clip_on=False,
            zorder=3)
    a1.set_ylabel("operational rank,\nas a fraction")
    a1.set_ylim(0.6, 1.0)
    a1.annotate("0.897", (x[0], frac.f.iloc[0]), textcoords="offset points",
                xytext=(6, 4), fontsize=7.5, color=ORANGE)
    a1.annotate("0.729", (x[-1], frac.f.iloc[-1]), textcoords="offset points",
                xytext=(-24, 6), fontsize=7.5, color=ORANGE)
    a2.plot(x, frac["rank"], "o-", color=GREY, markersize=5, clip_on=False,
            zorder=3)
    a2.set_ylabel("operational rank,\ncount")
    a2.set_ylim(0, 900)
    a2.annotate("201", (x[0], frac["rank"].iloc[0]),
                textcoords="offset points", xytext=(6, 5), fontsize=7.5,
                color=GREY)
    a2.annotate("770", (x[-1], frac["rank"].iloc[-1]),
                textcoords="offset points", xytext=(-22, 6), fontsize=7.5,
                color=GREY)
    for arm, colour, lab in (("RESOLVED_PHYSICAL", BLUE, "resolved"),
                             ("DIRECT_PHYSICAL", ORANGE, "direct")):
        row = dep[dep.arm == arm].set_index("source_class").loc[order]
        a3.plot(x, row.T_rec_best_mode.to_numpy(), "o-", color=colour,
                markersize=5, label=lab, clip_on=False, zorder=3)
    a3.set_ylabel("localized-directional\ndepth (M)")
    a3.set_ylim(0, 160)
    a3.legend(frameon=False, loc="upper right", fontsize=7.5, ncol=2)
    a3.set_xlabel("declared source class\n"
                  "(both the spatial and the temporal factor change)")
    for ax in (a1, a2, a3):
        ax.set_xticks(x)
        ax.set_xticklabels(
            [f"{c}\n{r:g}x{p_:g}x{t:g}" for c, r, p_, t in
             zip(frac.source_class, frac.n_radial, frac.n_azimuthal,
                 frac.n_temporal)], fontsize=7)
        ax.set_xlim(-0.25, len(x) - 0.75)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
    fig.suptitle("The supported fraction falls while the count rises",
                 fontsize=9.5, color=INK, y=0.985)
    fig.subplots_adjust(bottom=0.13)
    p = OUT / "fig2_enrichment_three_panels_039.png"
    fig.savefig(p)
    plt.close(fig)
    return {
        "file": p.name, "sha256": sha(p),
        "source_tables": [str(sp_src.relative_to(ROOT)),
                          str(dc_src.relative_to(ROOT))],
        "source_sha256": [sha(sp_src), sha(dc_src)],
        "selector": "e3d_class_spectra: arm == RESOLVED_PHYSICAL, median over "
                    "the 12 geometries of operational_rank/source_dimension "
                    "and of operational_rank, by source_class; "
                    "e3d_depth_by_class: snr0 == 100, arm in "
                    "(DIRECT_PHYSICAL, RESOLVED_PHYSICAL), median over the 12 "
                    "geometries of T_rec_best_mode, by source_class and arm",
        "plotted": ["operational_rank / source_dimension",
                    "operational_rank", "T_rec_best_mode"],
        "replaces": "artifacts/manuscript/figures/fig2_shiva_effect.png",
        "why": "the old asset said 'temporal class' for a ladder that changes "
               "both factors, and labelled the localized-directional depth "
               "'recoverable depth'",
        "caption": "**Enrichment across the four declared source classes.** "
                   "The ladder C224, C448_T, C528_S, C1056_ST changes both "
                   "the spatial and the temporal factor; the tick labels give "
                   "radial x azimuthal x temporal. Top: the median "
                   "operational rank as a fraction of class dimension falls "
                   "0.897 to 0.729. Middle: the operational rank itself "
                   "rises, 201 to 770 - a falling supported fraction is "
                   "compatible with a rising absolute count, and the two must "
                   "not be quoted as one statement. Bottom: the "
                   "localized-directional depth, the deepest retarded age "
                   "whose best-determined localized mode clears the "
                   "operational threshold at the reference SNR, which is flat "
                   "across the ladder for both physical arms. Across all "
                   "physical and mechanism arms the largest move anywhere in "
                   "this table is a single 4 M grid step. This is not the "
                   "scalar detectability probe of figure 1, and the two must "
                   "not be identified because both are quoted in M.",
    }


def main() -> int:
    t0 = time.time()
    OUT.mkdir(parents=True, exist_ok=True)
    figs = [fig1(), fig2()]
    man = {
        "ruling": "PAPER_I_FINAL_TEXT_REVIEW_039",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "commit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                 capture_output=True, text=True).stdout.strip(),
        "regenerated_from_saved_tables_only": True,
        "new_operator_or_reconstruction_inside_the_builder": False,
        "canonical_figures_overwritten": False,
        "in_figure_titles_and_axis_labels_corrected": True,
        "figures": figs,
        "runtime_seconds": time.time() - t0,
    }
    (OUT.parent / "FIGURE_MANIFEST_039.json").write_text(
        json.dumps(man, indent=2) + "\n")
    print(json.dumps({"figures": [f["file"] for f in figs]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
