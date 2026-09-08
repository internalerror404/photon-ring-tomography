# CONDITIONAL_ERROR_MODEL_AND_DECISION_035

## 1. Where the conservatism actually lives

| order | A/E, cancellation only | T/A, detector structure | T/E | U / max E, the 034 figure |
| --- | --- | --- | --- | --- |
| n0 | 1.10 | 20.02 | 20.6 | 9.8 |
| n1 | 4.57 | 9.02 | 41.0 | 56.9 |
| n2 | 4.71 | 6.73 | 31.4 | 28.4 |

The 034 report attributed a 10x-to-57x gap to sign cancellation. Decomposed, cancellation is the smallest of the three effects at order 0 (1.10x) and never the largest anywhere. What dominates is T/A: replacing the detector vector by a sum of per-column magnitudes costs a factor of 6.7 to 20. That conservatism is removable by arithmetic alone -- no correlation model, no assumption -- and removing it changes only where refinement is aimed.

## 2. What a cancellation-aware certificate would still need

    ||W(y - y_true)|| <= ||sum of signed estimates||
                        + sum of validated group remainders
                        + the fine reference's own error
                        + the omitted-support contribution

Three of those four terms are not available from the cached pair. The core-to-fine residual is a difference between two discretisations, not a bound on the fine map's own error; no group remainder radii exist; and the omitted support has no bound at all. Fitting correlations to this same pair would supply a model assumption, not a numerical bound, and is not attempted.

## 3. The greedy trap, stated

Contributions of 1 and -0.99 sum to 0.01. Correcting the first perfectly leaves -0.99. A local improvement can raise a signed global residual by breaking cancellation, so a refinement schedule driven by |contribution| is a bound-reduction schedule, not an error-reduction schedule. The 308,656 figure is relabelled ORACLE_ZERO_HEAD_CACHED_DEFECT: it assumes a selected node's discrepancy goes to exactly zero and everything else stays put.

## 4. Decision table

| question | answer | evidence |
| --- | --- | --- |
| Is the 034 gap mainly cancellation? | No | A/E is 1.10 to 6.58; T/A is 6.7 to 20 |
| Does the five-template identity hold? | Yes | max pointwise 6.68e-15, max after the detector 1.12e-13 |
| Does forming templates before interpolating help? | No | worse at all three orders on the max-channel criterion |
| Is any representation here inside 5e-4? | No | every one of the 40 transferred channels is above budget at every order, for both |
| Is the missing support bounded? | No | 0.6092 M^2 of order-2 emitting area has no response bound |

## 5. Minimum evidence any future physical campaign needs

1. A response comparison whose *signed* per-channel relative error is inside 5e-4, not a bound that has been tightened until it fits.
2. Coverage of the full declared domain, or an explicit bounded remainder for what is left out -- currently absent at order 2.
3. A statement of the reference's own accuracy. Every number here compares two discretisations; neither is continuum truth.
4. Group remainder radii from something other than the pair being certified.
5. A funded independent validation budget, decided before launch.

None of those five exists today, which is why no campaign starts.
