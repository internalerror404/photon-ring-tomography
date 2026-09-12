# Mahakal II Movie016 — family-blind continuous dynamics refinement

**Base:** completed Movie015 at `492765f9d1fe219066aea03504f07e7232de5518`.  
**Status:** registered before any Movie016 nonlinear fit, reconstructed movie, or endpoint.  
**Purpose:** test whether continuous analysis-by-synthesis of the natural historical dynamics closes the gap left by Movie015's finite 4,096-template library.

Movie015 remains a registered failure. It showed that global multi-family background search reduces the order-1 background forecast error by 92.6% and crosses the causal identification gate, while a finite historical template library still yields only 2M 95%-reliable span. A true-background diagnostic with the same library reaches only 6M, isolating historical-template discretization as a major remaining approximation.

No new Kerr ray, path integral, ODE trajectory, hull/critical root, visibility sample, or Paper-I unit is authorized.

## 1. Frozen population and pilot subset

Reuse Movie015's exact deterministic test population, observations, paired noise, physical arrays, support metrics, and q8/q12 rules. Stage A is a prospectively fixed computational pilot consisting of:

- the first four accepted twin pairs in each of the four historical families;
- both siblings;
- the first two paired noise draws;
- SNR0=300 only;
- 64 observed movies total.

Pair order is the deterministic source-ledger order; no outcome enters subset selection. A Stage-A pass authorizes a separately registered full-population run using the same code and bounds.

## 2. Starting hypotheses

Rebuild the exact Movie015 3,072-background and 4,096-history libraries from seeds `150090` and `140090`. For every observation:

1. score all background candidates on direct data;
2. retain the best eight joint background/history hypotheses from the Movie015 objective;
3. collapse duplicate `(background family, historical family, sibling variant)` combinations, retaining the best start for each;
4. continuously refine at most four distinct starts.

The true background family, historical family, parameters, and sibling label are never supplied.

## 3. Joint continuous objective

For each start, optimize the analytic background and historical parameters together against the full q8 direct-plus-order-1 whitened residual:

`||y0 - A0 b(theta_b)||^2 + ||y1 - A1[b(theta_b)+h(theta_h)]||^2`.

- Background families and ranges are exactly those of Movie009-R2.
- Historical families and ranges are exactly those of Movie009-R2.
- The historical family and sibling variant are discrete per start; all families/variants are considered through the starting beam.
- Background scenes are projected into the old 595-dimensional class at every objective call before detector evaluation.
- Historical scenes are rendered directly at q8 ray coordinates.
- Bounds are fixed to the original generative ranges expanded by no more than 10% at each edge.
- `scipy.optimize.least_squares`, trust-region reflective, maximum 80 function evaluations, fixed tolerances `1e-6`.
- No truth-dependent initialization, label, regularization selection, or restart addition.

The final reconstruction is the minimum-objective refined hypothesis. A fixed Laplace-weighted average of refined hypotheses is reported secondarily but cannot rescue a failed MAP gate.

## 4. Controls

On the identical pilot rows report:

- Movie015 finite parametric MAP;
- Movie015 finite parametric beam;
- continuous historical refinement with background fixed at the parametric MAP;
- full joint background-plus-history refinement;
- true-background continuous family-blind fit as an oracle diagnostic only.

## 5. Stage-A endpoints and gate

Report identification, pair-both-correct, total- and differential-movie frame metrics, 95%/90% reliable spans, family results, recovered-family accuracy, parameter-bound hits, optimizer convergence, objective reduction, q8/q12 clean/fitted checks, runtime, and memory.

Stage A passes only if full joint refinement satisfies all:

1. authentication, deterministic subset replay, exact direct nullness, positivity, and q8/q12 gates pass;
2. labelled identification `>=0.95` and pair-both `>=0.90`;
3. 95%-reliable span `>=12M` and at least `8M` beyond direct;
4. differential all-active-frame pass `>=0.75` on the pilot;
5. positive median paired total-movie improvement in all four families;
6. at least 90% of fits converge without a bound-saturated historical amplitude;
7. median movie error is at least 20% lower than the finite Movie015 MAP on the same pilot;
8. fitted q8/q12 discrepancies remain `<=5e-4` relative and `<=0.1` whitened.

A Stage-A failure remains evidence and does not authorize changing the subset, starts, bounds, tolerances, maximum evaluations, or thresholds. A pass authorizes the exact frozen mechanics on the full Movie015 population.

## 6. Scope and resources

- zero new physical calls;
- zero Paper-I units;
- CPU float64; up to eight independent optimizer workers; one BLAS thread per worker;
- <=8GiB aggregate memory;
- <=45 minutes;
- preserve every start, final objective, convergence code, parameter vector, and failed fit.
