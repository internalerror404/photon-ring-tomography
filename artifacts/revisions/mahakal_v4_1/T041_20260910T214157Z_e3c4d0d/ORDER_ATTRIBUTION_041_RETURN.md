# Order-attribution triage — return report

**Return token: `ORDER_ATTRIBUTION_TRIAGE_041_COMPLETE`**

Instruction: `ORDER_ATTRIBUTION_TRIAGE_FIRST`. Zero convention-B units spent:
no ray was traced, no truth or estimator was generated, no spectrum target was
created. The cached reference-geometry maps were read and the archived R2
operator was rebuilt under its own frozen measure, then decomposed.

Convention B unchanged: 19146 spent, 854 unspent; boundary spend 33410.

## 1. Fidelity gate

The subset results are worthless unless the rebuild is the archived operator.
It is. Every archived endpoint reproduces:

| quantity | archived | rebuilt | match |
|---|---:|---:|:--:|
| resolved s1, s2, s3 | 1.4371649, 1.3458733, 0.8062804 | identical to 1e-6 | yes |
| resolved tr F_known | 11.053660 | 11.053660 | yes |
| resolved tr F_cond | 7.198318 | 7.198318 | yes |
| resolved count known -> profiled | 3 -> 2 | 3 -> 2 | yes |
| resolved nuisance rank | 152 | 152 | yes |
| direct information, both | 0 | 0 | yes |
| direct nuisance rank | 140 | 140 | yes |

Recorded in `REPRODUCTION_GATE_041.json`.

The whitened operator's rows are grouped by order and each order's whitening
uses only its own quadrature, so an order subset's operator is exactly a
row-block of the full one. Every subset therefore shares one sigma, one
target/nuisance split and one source Gram; nothing is recalibrated per subset.
The nuisance projector *is* rebuilt for each subset.

## 2. The seven subsets

Frozen legacy measure, sigma = 0.011341986814407568, rho = 1, rtol 1e-12,
72 target columns and 152 nuisance columns throughout.

| subset | s1 | s2 | s3 | ops | tr F_cond | nuisance rank | principal angles vs full two-mode |
|---|---:|---:|---:|:--:|---:|---:|---|
| {0} | 0 | 0 | 0 | 0 | 0.000000 | 140 | — |
| {1} | 1.3947 | 1.2706 | 0.7491 | **2** | 6.073790 | 120 | 2.44 deg, 1.63 deg |
| {2} | 0.2257 | 0.2210 | 0.1971 | 0 | 0.417208 | 96 | — |
| {0,1} | 1.4098 | 1.2954 | 0.7606 | **2** | 6.276810 | 148 | 3.21 deg, 1.36 deg |
| {0,2} | 0.2356 | 0.2262 | 0.2103 | 0 | 0.454620 | 152 | — |
| {1,2} | 1.4166 | 1.3210 | 0.7926 | **2** | 6.983964 | 124 | 1.91 deg, 0.45 deg |
| {0,1,2} | 1.4372 | 1.3459 | 0.8063 | **2** | 7.198318 | 152 | 0, 0 |

## 3. The answer

**The two surviving combinations do not require order 2.** Dropping it
entirely leaves `{0,1}` with two singular values above threshold, 1.4098 and
1.2954, retaining 87.2% of the conditional Fisher trace, spanning a subspace
that sits at most 3.21 degrees from the full-stack two-mode subspace. The
count does not change and the mode identity does not change.

Per-mode order-block energy fractions of the full-stack conditional modes:

| mode | singular value | order 0 | order 1 | order 2 |
|---|---:|---:|---:|---:|
| 1 | 1.4372 | 1.78% | **96.90%** | 1.32% |
| 2 | 1.3459 | 1.60% | **95.64%** | 2.76% |
| 3 | 0.8063 | 1.56% | 91.82% | 6.63% |
| 4 | 0.7117 | 0.61% | 95.64% | 3.75% |
| 5 | 0.6531 | 0.88% | 88.84% | 10.28% |

Both passing modes are order-1 dominated. Order 2's share *rises* down the
spectrum — 1.3% and 2.8% in the two passing modes against 6.6% and 10.3% in
the third and fifth — so its contribution is concentrated in the directions
that fail the threshold anyway.

Leave-one-order-out on the conditional Fisher trace:

| removed | tr F_cond retained | share of 7.198318 | ops |
|---|---:|---:|:--:|
| order 0 | 6.983964 | 97.02% | 2 |
| order 1 | 0.454620 | 6.32% | **0** |
| order 2 | 6.276810 | 87.20% | 2 |

**Order 1 is the load-bearing order.** Without it the result collapses to zero
operational directions.

## 4. The direct order earns its place without a single target row

Order 0's target columns are identically zero, yet adding it to `{1}` raises
the conditional trace from 6.073790 to 6.276810, and adding it to `{1,2}`
raises 6.983964 to 7.198318 — about +3% each time. It contributes by
constraining nuisance coefficients that would otherwise absorb target
response, not by responding to the target. Measuring target energy per order
alone would have missed this, which is why the leave-one-out was run.

## 5. What this does not establish

This is dependence **inside the frozen model**, at one geometry, one SNR
label and one source class. It is not robustness to the physical-operator
error, and nothing here qualifies the transfer quadrature.

Specifically, the 0.5116 order-2 figure is a maximum relative whitened
detector discrepancy over forty diagnostic columns on 62% of emitting support.
It is not `||Delta B_cond||_2` for this 72/152 source-normalized operator, and
no Weyl margin may be read against it. The triage says where the risk sits; it
does not size the error.

Dropping order 2 removes its target signal *and* its nuisance rows together.
`{0,1}` is therefore the experiment one would have run without order 2, not
the full experiment with the order-2 error set to zero.

## 6. What follows for the acquisition question

The burden moves to the orders that carry the modes. From the 034 audit, on
matched support: order 1 has a 0.042744 maximum relative discrepancy with
97.3% node and 97.4% area coverage; order 0 has 0.009594 with 99.4% and 99.4%.
Order 2's 0.511603 with 61.7% and 62.8% coverage is the worst block, and it is
the block the two surviving modes barely use.

That is a materially cheaper validation target than the full three-order
campaign. It is not a qualification: 0.042744 is still about 85x the 5e-4
component criterion, and it remains a diagnostic-column discrepancy rather
than a bound on the conditional operator.

## 7. Files

- `REPRODUCTION_GATE_041.json` — archived-vs-rebuilt endpoint gate
- `ORDER_ATTRIBUTION_041.csv` — the seven subsets, five singular values each
- `ORDER_ENERGY_FRACTIONS_041.json` — per-mode order-block energy fractions
- `run.log` — execution transcript
- generator: `scripts/revision_v4_1/t041_order_attribution.py`

Nothing under `artifacts/revisions/mahakal_v4_1/R0_20260906T070540Z_38e1f8a/`
or any other archived run directory was written to. This return authorizes
nothing: no funded replay, no support extension, no submission.
