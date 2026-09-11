# Movie013 execution failure 002 — completion readback column name

The corrected scientific execution completed all four operator variants, all validation selections, both SNR test evaluations, the exact archived off-basis population, q8/q12 fitted checks, and wrote `PER_CASE.csv`, `AGGREGATE.csv`, and `FAMILY.csv`. It then stopped before `SUMMARY.json` while comparing the newly written baseline aggregate with the archived Movie007 table.

The merge contains nonoverlapping columns named `median_error` and `median_support_error`; the reporter incorrectly requested `median_error_new`. This is a closeout/readback defect only. The saved scientific CSVs, selected hyperparameters, operator matrices, reconstructions, thresholds, and winner definitions are unchanged. The repair substitutes the actual column name and resumes from the already written deterministic tables; no source/noise population or inverse definition changes.
