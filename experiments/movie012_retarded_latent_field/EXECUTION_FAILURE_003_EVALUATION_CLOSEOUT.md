# Movie012 reimplementation failure 003 — evaluation closeout namespace shadowing

The frozen held-out evaluation computed the registered predictions and metrics in memory, then stopped at the first result-table construction before writing `PER_RECONSTRUCTION.csv`, `PER_FRAME.csv`, `DIFFERENTIAL.csv`, `FITTED_RESPONSE_GATES.csv`, `SUBSPACE_DECOMPOSITION.csv`, `PRIMARY_PREDICTIONS.npz`, `AGGREGATE.csv`, `FAMILY.csv`, or `SUMMARY.json`.

Inside the differential-movie loop, a local NumPy array was named `pd`, shadowing the imported pandas module. The later call `pd.DataFrame(records)` therefore raised `AttributeError: 'numpy.ndarray' object has no attribute 'DataFrame'`.

No persisted held-out result table or success-gate endpoint was available for inspection. The repair renames only that local array to `pred_diff`. The frozen populations, PCA objects, ridge choices, six neural checkpoints, test noise, predictions, metrics, thresholds, and success-gate logic are unchanged. The deterministic evaluation is rerun from the sealed inputs and checkpoints; corrected source is re-hashed before rerun. No new physical call or Paper-I unit is used.
