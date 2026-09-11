# Movie009-R6 execution failure 001 — non-applicable direct mixture fields

All validation and test mixture calculations completed and wrote deterministic aggregate, family, frame, reconstruction, mixture, q8/q12, and validation tables. The final strict JSON writer rejected the direct-control row because its mixture-only diagnostics are non-applicable and represented as NaN.

This is reporting-only. The repair maps only those direct-control fields to JSON null and computes the registered gate from the already written CSVs. No bank candidate, validation score, selected K/exponent, NNLS weight, source movie, metric, q8/q12 value, or endpoint changes.