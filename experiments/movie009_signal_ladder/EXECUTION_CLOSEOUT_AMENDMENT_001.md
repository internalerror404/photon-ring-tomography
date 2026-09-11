# Movie009 closeout amendment 001 — record-only threshold-row completion

The scientific execution completed and wrote all six amplitude conditions, the fresh source/noise arrays, estimates, per-case and per-frame tables, bootstraps, and an initial summary. The registered result was `alpha_star=0.32` with bracket `(0.24,0.32]`.

The independent verifier then stopped on one reporting-schema check: `run_signal_ladder.py` stopped appending `threshold_rows` after the first passing amplitude, while the verifier reconstructed threshold booleans for all six amplitudes. All six amplitudes are present in `AGGREGATE.csv`, `GROUP_RESULTS.csv`, `CONSTRUCTION_GATES.csv`, and the saved dense arrays. Every numerical and scientific readback—including the independently recomputed alpha threshold—passed.

This amendment authorizes only a record-level closeout from existing outputs:

- preserve the original summary and failed verification record;
- append threshold rows for alpha 0.40 and 0.48 from the existing tables;
- rerun the same independent readback;
- do not regenerate sources, directions, noise, estimates, bootstraps, or physical data;
- do not change the threshold, pass criteria, or outcome.

No new physical call or Paper-I unit is authorized.
