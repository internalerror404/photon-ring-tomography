# Mahakal II: Euler-inspired learn/freeze/verify experiment 002

Executed manufactured scalar forward problem, 8 September 2026. NOT a Kerr trace, an Euler singularity reproduction, or an implementation of NeRF/FNO/Kiran. Paper I and the previous experiments are unchanged. No production budget was used.

The source paper is Ganeshram, Duruisseaux and Anandkumar, *Stable Singularity of the Euler Equations on R^3*: https://anima-ai.org/wp-content/uploads/2026/09/Euler.pdf . The motivating ingredient is a separate polynomial verification representation after neural fitting. This study does not implement its SS-eSOAP/SS-Broyden optimizers or its stability proof.

Three seeds train one base and three successors each: continue a structured PINN, add a frozen-base residual correction, or add that correction at residual-focused collocation points. The rational forcing, hard boundary, grids, methods and stopping ceilings are in protocol.json, written before fitting locally (not externally preregistered). Nine successor fits and three initial fits were executed in float64 on CPU. Each final neural field was frozen into cubic Hermite surrogates at 32, 64 and 128 cells. Three classical ODE-derived spline controls were also tested.

## Result

Median held-out equation residual RMS falls from 0.008994 to 0.004460 with residual-focused correction, but the original detector error increases from 0.00007213 to 0.0001108. Residual improvement is not an automatic observable improvement. No successor sweep was used to reverse this negative result.

A supplementary signed-phase readback (no new fits) removes the constant positive readout offset. For 128-cell surrogates, median measured joint detector error / verified analytic upper bound:

- Continued PINN: 0.0002404 / 0.03793.
- Fixed-point correction: 0.0002603 / 0.04979.
- Focused-point correction: 0.0003397 / 0.02597.
- Classical ODE Hermite: 1.139e-8 / 3.890e-5.

The criterion is 0.0005. The classical 64- and 128-cell surrogates are certified for this manufactured exact-integral problem. The neural bounds do not establish the criterion; that is NOT proof their actual errors exceed it. This simple directly integrable equation favors the classical solver, which remains in the comparison.

## The certificate

The checker constructs exactly continuous cubic Hermite polynomials with rational coefficients from saved binary64 knot values and derivatives. It bounds the rational differential residual on every cell using exact Fraction polynomial/Bernstein arithmetic and positive denominator bounds. Integrating the residual from the fixed initial condition bounds the delay error. A known phase-spread lower bound for the joint cosine/sine reference response converts that bound to relative detector error without trusting measured truth norms.

This certifies the explicit polynomial surrogate, not the original neural network between its knots. The ideal detector integral is mathematically bounded; the floating-point quadrature implementation was checked at two resolutions, not interval-certified. These are not real Kerr error bounds or source-history recovery.

Eleven implementation/identity checks pass. All 30 spline candidates and all seeds are retained. The complete checkpoint, prediction, cell-bound and report package is delivered with the conversation; the files here reproduce it in a fresh directory:

```sh
python run_all.py
```

Requires numpy, scipy and torch. Do not overwrite prior results. Source/ray/canonical artifacts and the 854-unit physical remainder are untouched. Treat the table as a development result, not a sealed-main or publication-readiness claim.
