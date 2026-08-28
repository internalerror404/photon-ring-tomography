# Paper I — proof audit

PAPER_I_EDITORIAL_RULING_022 item 9. Every mathematical assertion in the
manuscript is listed here with its status. A statement is admissible only if it
is **proved** in the paper, **cited** to a source, or **computed** from a
canonical artifact under a registered gate. Anything that was none of the three
is named below as a defect, with what was done about it.

No endpoint, table, threshold or artifact was altered by this audit. The three
defects it found were defects of *statement*, and all three were repaired in the
prose.

## Assertions and status

| # | assertion | status | where it rests |
|---|---|---|---|
| 1 | `z = dOmega g^3 j + eta`, `Var(eta) = sigma_Omega^2 dOmega` | definition | forward model, section 2.1 |
| 2 | whitened row `Atilde = sqrt(dOmega)/sigma_Omega * g^3 * B` | **proved** | dividing 1 by `sd(eta) = sigma_Omega sqrt(dOmega)` gives exactly this; one line, checked in this audit |
| 3 | the retired `c = g^3` flat-noise convention multiplies the Gram by `k` under a `k`-way equal-area pixel split | **proved** | `k` identical rows of a constant transfer value contribute `k` times one row's outer product |
| 4 | the corrected convention is invariant under the same split | **proved** | each child carries `dOmega/k`, so its whitened row scales by `1/sqrt(k)` and `k` of them restore the original Gram |
| 5 | invariance is achieved numerically | computed, gated | gate `G10q`, corrected against retired convention |
| 6 | `y_U = L y_R`, `C_U = L C_R L^T`; likewise for total flux | **proved** | linear propagation of a Gaussian covariance |
| 7 | `C_R = sigma_Omega^2 diag(dOmega)` | **proved** | immediate from assertion 1 with independent rows |
| 8 | one noise density fixed once and shared by every arm | design constraint | stated in section 2.2; an arm choosing its own `sigma` would be measuring its own row count |
| 9 | age ceiling `A_max = T_obs + 1.25 max Q_0.999 + 2h` | construction | computed before any operator was evaluated; 0 of 1152 depth entries right-censored, so the ceiling did not bind |
| 10 | `J_old` as a threshold-independent integral | definition | section 5.1 |
| 11 | `Gamma_sensitivity_matched = -0.5 log(I ratio)` is commensurable with `Gamma_amp = -log(A ratio)` | **proved** | `I` is a Fisher information and scales as amplitude squared, so half its log ratio is the amplitude's log ratio |
| 12 | the registered delay-only discrepancy is identically zero | **proved** and computed | the registered probe is spatially flat and the substitution changes only `source_r` and `source_phi`, so the scalar curve cannot depend on it; verified bitwise at all 12 geometries and gated |
| 13 | a coefficient whose support contains no ray gives an identically zero column | **proved** | immediate from the row construction |
| 14 | old-epoch blindness of the direct image is a null space, not a condition number | computed | 84 exactly zero columns on `L224`, largest direct singular value in the old structural subspace 1.8e-14 |
| 15 | `P_level` is an orthogonal projection and `P_structure = I - P_level` | **proved** | orthonormal columns from a QR of the temporal design, rendered spatially uniform; orthogonality is under the plain Euclidean inner product on grid points, which is the inner product the age-window norms use |
| 16 | the level and structure errors are each normalised by their own component | definition, verified | absolute errors invert the normalised ordering: direct-arm level 0.327 against structure 0.166 while the normalised values are 0.266 and 0.927 |
| 17 | the resolution-aware morphology measure is normalised to its own worst case per state class | construction, tested | unmatched-feature cost is the grid diameter `sqrt((n_r-1)^2 + (n_phi/2)^2)`; unit tests pin the normalisation |
| 18 | a distributed delay kernel and a delay ladder need not share a null space | **proved**, as restated | the ladder's null space is fixed by three discrete lags, the kernel's by the whole within-window delay distribution |
| 19 | full column rank on a declared class does not imply injectivity on a continuum | **proved** by counterexample | enrichment from 224 to 1056 dimensions exposes a direct-channel null space of up to 100 dimensions while reach moves by at most one grid step |
| 20 | conditioning is not evidence of physical content | **proved** by counterexample | the pairing-destroyed control is better conditioned than the physical operator at 12 of 12 geometries |

## Defects found, and the repairs

1. **An unqualified universal.** The paper said a distributed delay kernel and a
   delay ladder "have different null spaces". That is false in general — the two
   coincide for sources the kernel cannot distinguish from the ladder. Restated
   as "need not have the same null space", with the reason they differ *on this
   operator* given. Assertion 18.
2. **An unexplained factor of one half.** `Gamma_sensitivity_matched` carried a
   `-0.5` against `Gamma_amp`'s `-1` with no derivation, which reads as a fudge
   until the reader works out that one is an information and the other an
   amplitude. The one-line reason is now in the text. Assertion 11.
3. **An incomplete projector definition, and an additivity trap.** The
   level/structure split was introduced with a sentence that named `P_level`,
   never gave `P_structure`, and never said which inner product made the
   projection orthogonal — all three are in the implementation and none reached
   the paper. Worse, the two normalised errors invite being read as parts of one
   unit budget, which they are not: each is divided by its own component's norm,
   and the absolute errors invert their ordering. Both are now stated where the
   table appears. Assertions 15 and 16.

## What this audit does not cover

Numerical results are not re-derived here; that is
`scripts/verify_manuscript.py`, which recomputes every claim from the frozen
bytes and is run as part of the release. This document covers only the
mathematical statements that surround those numbers.
