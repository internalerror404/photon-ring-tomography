# Movie009-R5 execution failure 001 — non-applicable direct diagnostics serialized as NaN

All registered candidate-bank variants completed and wrote `AGGREGATE.csv`, `FAMILY.csv`, `Q8_Q12.csv`, per-reconstruction/frame tables, and selections. The final `SUMMARY.json` writer then rejected the direct-control row because `inferred_family_accuracy`, candidate margin, and fitted amplitude are non-applicable there and pandas represented them as NaN.

This is a reporting-only failure. The repair maps only non-applicable scalar fields to JSON null and derives the registered gate from the already written deterministic CSVs. No candidate, observation, amplitude fit, selected index, movie, metric, q8/q12 value, or success threshold changes. The scientific tables and their hashes are preserved.