# Transfer audit return: T0, T1 and the G1 closeout

Status: **TRANSFER_AUDIT_029_REVIEW_READY**

| component | status |
| --- | --- |
| curved refinement | **DEMONSTRATED** |
| full hull qualification | **QUALIFIED** |
| contour brackets | **LOCAL_BRACKETS_RESOLVED** |
| domain completeness | **PENDING_ARRAYS_NOT_PRESERVED** |
| primitive diagnosis | **CAUSE_IDENTIFIED** |
| repair validation | **NOT_RUN** |
| transfer accuracy | **NOT_QUALIFIED** |
| overall quadrature | **NOT_QUALIFIED** |
| governance | **COMPLETE** |

R3B is not authorized and was not begun.

## 1. The four G1 gaps were real

All four hold, and I accept them. The tighter-root comparison was declared and never executed. The shifted check measured radius error over mean radius, not band and response. The tessellation check normalised each shape's area change by that shape's own area. The final boolean took the last pair and the shifted radius and ignored the rest, and its width flag tested a positive total area rather than local nesting.

The tessellation arithmetic is confirmed exactly. At 4096 samples the band-normalised error is 2.456e-05 against a 1e-6 budget -- your 2.46e-5, not the 3e-7 I reported. **That reported pass was wrong.** Refining the tessellation, which costs no physical roots, fixes it:

| samples | band-normalised | detector response |
| --- | ---: | ---: |
| 4096 | 2.456e-05 | 4.606e-06 |
| 16384 | 1.535e-06 | 2.879e-07 |
| 65536 | 9.592e-08 | 1.800e-08 |

Chosen: 65536. The convergence is second order, as an inscribed polygon on a smooth curve should be.

The missing checks now run, on the same candidate and the same 237 marks, with no new ladder and no new fit family:

| check | order | band symdiff | inner+outer | response | budget | pass |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| shifted | 0 | 4.123e-12 | 4.123e-12 | 1.189e-10 | 2.5e-04 | yes |
| shifted | 1 | 7.143e-10 | 7.143e-10 | 1.203e-09 | 2.5e-04 | yes |
| shifted | 2 | 9.383e-09 | 9.383e-09 | 5.718e-10 | 2.5e-04 | yes |
| tighter root | 0 | 3.674e-16 | 1.362e-16 | 3.459e-15 | 2.5e-05 | yes |
| tighter root | 1 | 5.842e-14 | 5.825e-14 | 3.695e-13 | 2.5e-05 | yes |
| tighter root | 2 | 1.665e-11 | 1.664e-11 | 4.987e-11 | 2.5e-05 | yes |

| order | min local band width (M) | positive at every angle | total area positive |
| --- | ---: | --- | --- |
| 0 | 2.1227e+01 | True | True |
| 1 | 4.6974e-01 | True | True |
| 2 | 2.5904e-02 | True | True |

The final boolean is now the conjunction of every requirement: `two_late_pairs_all_metrics`=True, `shifted_band_and_response`=True, `tighter_root_executed`=True, `tighter_root_passes`=True, `tessellation_band_normalised`=True, `tessellation_response`=True, `local_nesting_positive_width`=True, `topology_simple`=True, `arrays_exported`=True.

Hull geometry: **QUALIFIED**. Arrays are exported and hashed (`CLOSEOUT_ARRAYS_029.npz`, `192eb9598c27ed2f`) so the next stage does not regenerate them.

