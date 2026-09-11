# Mahakal II Movie013 — controlled operator tournament

**Return:** `MOVIE013_OPERATOR_TOURNAMENT_COMPLETE_NO_WINNER`

Four formulations were evaluated on the exact same Movie007 in-basis and off-basis histories, observations, noise, validation budget, and movie metrics. The original ray–pixel 595-dimensional operator-plus-prior package remains the strongest tested configuration.

The retarded-time DCT is an exact orthogonal row-coordinate control and reproduces the baseline. The exact nested 1,445-dimensional source representation and the old/recent block-regularized formulation both worsen in-basis and off-basis recovery and erase the baseline's 28M in-basis reliable span. A postplanned exact-sample readback also disqualifies the historical-innovation variant on its off-basis fitted q8/q12 whitened gate.

Start with `RESULTS.md` and `COMPLETION.json`. Compact deterministic tables and the exact-sample numerical closeout are under `results/`. The final executable source and verification source are deposited in `source/Movie013_Final_Source.tar.xz`.

No new physical call or Paper-I unit was used. No delay-resolved or visibility-domain acquisition was run; those would be different data experiments rather than equivalent operator representations.
