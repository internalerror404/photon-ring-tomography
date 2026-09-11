# Movie013 postplanned exact-sample numerical verification

This readback was executed after the tournament outcome and cannot promote any failed variant. It completes the registered q8/q12 checks on the exact archived off-basis histories and noise.

- Clean direct: relative 1.433e-15, whitened 1.516e-11, PASS.
- Clean labelled: relative 6.425e-12, whitened 7.094e-08, PASS.
- Baseline/DCT labelled fitted: whitened 0.05235, PASS.
- Nested1445 labelled fitted: whitened 0.06519, PASS.
- Historical-innovation labelled fitted: whitened **0.12512**, FAIL against 0.1.
- Winner calculation independently matches the deterministic tournament summary.
- No new physical calls or Paper-I units.
