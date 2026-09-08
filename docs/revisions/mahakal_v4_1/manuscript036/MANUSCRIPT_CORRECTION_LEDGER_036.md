# MANUSCRIPT_CORRECTION_LEDGER_036

Every correction applied in the working revision, and where it came from. The
pinned manuscript and the canonical freeze are unchanged; this is an additive
record.

## Corrections carried into the draft

| id | what the pinned version said | what the revision says | source ruling |
| --- | --- | --- | --- |
| L01 | section 5 headed "Validated Computational Operator" | heading removed; section 7 lists what is qualified, section 8.2 states the quadrature is not | 032, 034 |
| L02 | order-resolution attributed using `UNRESOLVED_IMAGE` | retained as a comparison of two declared constructions, with a CORRECTED SCOPE box; restoring the physical attribution needs a new physical control and a new result | 035, 036 |
| L03 | R2's two operational directions read without a measure pin | pinned to the frozen legacy measure; corrected-measure interval 1 <= N <= 2 stated beside it | 026, 036 |
| L04 | flat-per-row measurement convention | retired; results recomputed or labelled legacy in place | 026 |
| L05 | four morphology qualifications trailing the result | moved beside it as part of the result | 036 |
| L06 | coefficient and source-function metrics not consistently separated | separated throughout; actual noise and SNR labels not interchanged | 036 |
| L07 | no statement of continuum accuracy | section 8.2 gives the measured detector-response error and the coverage gap | 034, 035 |

## Corrections to my own earlier reporting

| id | what I reported | what the record says |
| --- | --- | --- |
| L08 | "the integrals agree to about 3e-16" (033 return) | true of `J_observer`, `J_50` and the tail; false for `s_escape`, which differs by a median 2.94e-05 | 035 |
| L09 | "the 10x-to-57x gap was conservatism from sign cancellation" (034) | it is mostly loss of detector-vector structure; cancellation is 1.10 to 4.71 and is not absent | 035 |
| L10 | "the order-2 interior is where the cost lives" (033) | withdrawn; no order-2 stencil passes the smoothness proxy, so the figure measured that representation failing | 034 |
| L11 | "adaptivity fixes the boundary cost" (033) | withdrawn; the same model splits 52,379 boundary against 49,037 interior | 034 |
| L12 | "identity ... 6.4e-15 after the detector map" (035 commit message and chat summary) | the global post-detector maximum is 1.1191048088221578e-13; 6.4e-15 is the order-2 *pointwise* value. The 035 RETURN.md reported the detector maximum correctly; the commit message and my summary did not. Record-only correction; no replay required | 036 |
| L13 | "308,656 evaluations" presented as a cost scenario | relabelled ORACLE_ZERO_HEAD_CACHED_DEFECT: it assumes a refined node's discrepancy goes to exactly zero and everything else stays put | 035 |
| L14 | "no order-2 stencil passes the same-leg test" | relabelled a small-radius-span heuristic; physical branch membership is unverified | 035 |

## What was deliberately not changed

- The pinned manuscript bytes, the canonical artifact freeze, and every
  historical run directory.
- Every preserved literal failure and every governance deviation record.
- The original title, the author list, and the three organizing questions.
