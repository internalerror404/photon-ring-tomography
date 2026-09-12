# Movie016 preexecution amendment 001 — explicit Movie014 module wiring

Before any nonlinear fit, reconstructed movie, or scientific endpoint existed, source inspection found that the frozen Movie016 implementation referenced `m15.m14.choose_shortlist` and `m15.m14.library`. In the imported Movie015 module, `m14` is created only as a local variable inside Movie015's `main()` and is not a module attribute. The pilot would therefore stop before its first fit.

The correction imports the frozen Movie014 source explicitly in Movie016, calls `m14.choose_shortlist` and `m14.library` directly, and passes that module through the worker context. No source population, pilot subset, physical operator, starting hypothesis, objective, bound, optimizer setting, metric, threshold, or success gate changes.

Corrected source SHA-256: `d3d8bb35db5853a9e35eed1cb1715d36d207d6f0d93e4057d2b4bd147399a647`. `python -m py_compile` and the registered 832-row finite-response self-test pass. No scientific fit had started and no outcome had been seen.