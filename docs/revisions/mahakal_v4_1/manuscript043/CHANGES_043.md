# Manuscript revision 043 — what changed from 042

One scientific addition, promoted at the author's direction after the
order-attribution triage. Nothing else in the paper was rewritten, no
numerical result was recomputed for this revision, and manuscript042 is left
intact in its own directory.

## Added

1. **Abstract** — one sentence: the two operational combinations are not
   driven by the numerically weakest image; omitting $n=2$ leaves both above
   threshold, with 96.90% and 95.64% of their residualized response energy in
   $n=1$.

2. **Section \ref{sec:orderattr}, inside the nuisance-adjusted results** — the
   order-attribution paragraph, the compact four-row table
   (`tab:orderattr`), and a separate paragraph on the direct order's role: its
   target columns are identically zero, yet it raises the conditional trace
   from 6.0738 to 6.2768 by constraining nuisance coefficients. A channel can
   improve identifiability of a target it does not observe.

3. **Conclusion** — one clause: the first indirect image is the load-bearing
   historical channel; the direct image contributes through nuisance
   constraints.

4. **Appendix \ref{app:orderattr}** — all seven order subsets with singular
   values, operational counts, conditional traces, nuisance ranks and
   principal angles; the per-mode order-block energy fractions; and the
   statement that the rebuild reproduced every archived reference-geometry
   endpoint before any subset was reported.

## Scope wording held

Every added statement is scoped as order dependence **inside the frozen finite
operator** at one geometry and one SNR label. Nothing added claims validation
of the continuous acquisition, and the unqualified transfer quadrature,
finite-model scope, unrecovered R1 eta and nonphysical index-sum control all
remain stated exactly as in 042.

## Not added

The cached-map core/fine/coarse feasibility results are **not** in this
revision. They are a separate return awaiting author review, and unreviewed
results are not promoted into the manuscript.

## Source

Order-attribution numbers:
`artifacts/revisions/mahakal_v4_1/T041_20260910T214157Z_e3c4d0d/`
— `ORDER_ATTRIBUTION_041.csv`, `ORDER_ENERGY_FRACTIONS_041.json`,
`REPRODUCTION_GATE_041.json`.
