# Movie009-R3 execution failure 002 — forked workers shared a lazy NPZ ZIP handle

The parallel rerun authenticated every input, deterministically regenerated the registered validation/test populations, rendered the analytic q8/q12 truths, and rebuilt both proposal banks. It stopped as soon as validation workers began: the parent `numpy.load` object remained a lazy ZIP reader, and forked workers attempted concurrent access to the inherited file handle, producing `zipfile.BadZipFile: Bad magic number for file header`.

No validation rule or BMA temperature was selected, no test reconstruction ran, and no scientific endpoint exists from this attempt. The failure is an implementation/I/O defect, not a scientific pass or fail.

The correction materializes every authenticated NPZ array into an ordinary in-memory NumPy dictionary before any worker is forked. All source populations, candidate banks, deterministic ordering, optimizer starts and tolerances, objectives, metrics, thresholds, and success gates are unchanged. The failed attempt and its partial source/population records are preserved.