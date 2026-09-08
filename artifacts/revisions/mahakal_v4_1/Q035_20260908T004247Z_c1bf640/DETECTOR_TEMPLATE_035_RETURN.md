# DETECTOR_TEMPLATE_035_RETURN

Status: **DETECTOR_TEMPLATE_035_REVIEW_READY**

Ruling: PAPER_I_CANCELLATION_RULING_035  
Commit: c1bf64023fe70b40753b3d2c4b383c7e463062b9  
New rays, path integrals, hull roots, target operators: **0**. 854 units remain, none spent. No file from 029-034 is edited.

## 1. The export defect, confirmed and repaired

The 034 archive holds three keys -- `n0_reference`, `n1_reference`, `n2_reference` -- and nothing else. The writer popped the dictionary carrying both vectors and stored only its reference member, so the estimated vectors and signed residuals were never written. Regenerated here from cached inputs into a new directory: reference, baseline and candidate vectors, signed residuals, channel labels and times, supported node ids and coordinates, template arrays, the CSR overlap triple, reference norms and the bound hierarchy, and the omitted masks. Read back and validated before this summary was written. The 034 directory is byte-identical.

## 2. The 034 gap, decomposed

| order | A/E cancellation | T/A detector structure | T/E | U / max E |
| --- | --- | --- | --- | --- |
| n0 | 1.10 | 20.02 | 20.6 | 9.8 |
| n1 | 4.57 | 9.02 | 41.0 | 56.9 |
| n2 | 4.71 | 6.73 | 31.4 | 28.4 |

The 034 claim that the 10x-to-57x gap was conservatism from cancellation is withdrawn. The U/max-E column reproduces that range, and decomposing it shows cancellation is the smallest term at order 0 -- 1.10x -- and never the largest anywhere. The dominant factor is T/A, from 6.7x to 20x: replacing the detector vector with a sum of per-column magnitudes. That is removable by arithmetic, with no correlation model, and removing it aims refinement better without making any approximation more accurate.

Every channel now carries its own reference norm. The 034 scenario divided by the largest reference norm across channels, which is not the same test.

## 3. The five-template identity

Verified: `H0`, `Re H20`, `Im H20`, `Re H40`, `Im H40` reconstruct all 40 transferred columns at the eight observer times, to a maximum pointwise discrepancy of 6.68e-15 and 1.12e-13 after the detector map, against a 1e-12 tolerance.

It is an algebraic reduction of these declared diagnostic fields. It is not a ray speedup, it does not reduce the L224 source space, and it says nothing about arbitrary source movies.

## 4. The one authorised representation test, and its answer

Baseline interpolates the redshift and the coordinate time and then cubes and phases. The candidate forms the five templates at the coarse nodes first and interpolates those. Same support, same overlap operator, same noise, same clock, same periods and times.

| order | baseline max relative | candidate max relative | verdict |
| --- | --- | --- | --- |
| n0 | 9.5939e-03 | 9.7177e-03 | worse |
| n1 | 4.2744e-02 | 8.4795e-02 | worse |
| n2 | 5.1160e-01 | 6.5364e-01 | worse |

**The candidate is worse at all three orders on the criterion.** Composite-first does not fix order 2; it makes the worst channel worse by 28%, order 1 worse by a factor of two, and order 0 worse by 1.3%. One detail is worth recording rather than burying: at order 2 the candidate's *median* channel error is better (1.700e-01 against 2.630e-01) while its maximum is worse. The criterion is the maximum, so the candidate fails; the median is reported because it is what the archive says, not because it rescues anything.

This closes the test. No interpolant sweep follows, and the budget is not adjusted to produce a pass. Every one of the 40 transferred channels is above 5e-4 at every order under both representations.

## 5. Scope, unchanged

The screen channels return exactly zero absolute residual under both representations. That is an equal-input consistency control -- both sides receive identical screen fields through the same operator -- not an absolute geometry validation.

Coverage is unchanged and still the harder problem: order 2 compares 61.7% of emitting nodes and 62.8% of emitting area, leaving 0.6092 M^2 with no response bound. No cancellation argument on the compared subset touches it.

The 034 same-leg flag is relabelled a small-radius-span heuristic; physical branch membership stays unverified where the archived metadata does not establish it. The 308,656 figure is relabelled an oracle-zero-head scenario over the cached defect.

## 6. Status

| item | status |
| --- | --- |
| cached discrepancy | MEASURED_AND_OUTSIDE_BUDGET_UNCHANGED |
| bound decomposition | E_A_T_U_MEASURED_PER_CHANNEL |
| template identity | VERIFIED_TO_6.7e-15 |
| candidate comparison | WORSE_AT_ALL_THREE_ORDERS_TEST_CLOSED |
| missing support | UNBOUNDED_0.6092_M2_AT_ORDER_2 |
| physical quadrature | NOT_QUALIFIED (C13 open) |
| claim routes | SECTION_10.1_CORRECTED_NOT_MERELY_PENDING |
| governance | COMPLETE |

Suite: 691 passed, 2 warnings in 228.54s (0:03:48), run in a disposable worktree.

This return authorizes nothing. R3B, target spectra, estimators and a submission freeze remain unauthorized, and no physical query has been made.
