# AMENDMENT 002 — Age-resolved information matrix on the registered localized class

## Identity
- branch `claude/experiment-review-mac-rthiz1`, commit `d6869f8d1c08889fee34e91d392c2bbc1bc9a62f`
- registry sha256 `2ba66f0209fe1cdec97b8cf5862494c22fb94704318f9601a7a1f9eb4b783796`
- freeze `artifacts/configs/E3C_OPERATOR_GRID_FREEZE.json` sha256 `818199a7ac4f3f90cf592f568d2a550dfd575aba1d539b0966a3a5c6521473d2`
- 12 registered geometries, orders n = 0, 1, 2, profile `core`
- source class `C224` (224 dimensions), unmodified
- common age grid 0 to 252 M in steps of 4 M
- amendment record `artifacts/configs/AMENDMENT_002_LOCALIZED_CLASS_MECHANISM_DIAGNOSTIC.json`
- status **ADOPTED_WITH_LITERAL_RESULT_PRESERVED**

## What went wrong with the registered statistic

The registered hypotheses H2 and H3 compare the full and substituted age-information curves through D = ||log(1+I_full) - log(1+I_sub)||_2 / max(1, ||log(1+I_full)||_2). Under the registered localized probe -- Gaussian in retarded age, flat in the emission annulus -- this comparison is degenerate for the delay-only substitution.

substitute_spatial replaces only source_r and source_phi, keeping delay, redshift and quadrature. The flat probe has no spatial structure, so the scalar curve I(a) = q_a^T A^T C^-1 A q_a cannot depend on where the rays land. D_delay is therefore identically zero as an algebraic identity of the diagnostic, not as evidence for the delay mechanism. Reporting it as support for the delay mechanism would have been a circular claim.

Verified: RESOLVED_PHYSICAL and DELAY_ONLY age-information curves compared elementwise on all 12 geometries under the first E3C pass — bitwise identical at every geometry and every age; D_delay = 0.000e+00 in all 12 cells. Gate
`E3C_H2_registered_statistic_is_an_identity` re-checks this at assembly time, so
the zero is recorded as an identity and can never be re-read as evidence.

The freeze file is **not** edited. `E3C_OPERATOR_GRID_FREEZE.json` records the
pre-evaluation state and amending it after the grid ran would defeat its
purpose; this amendment stands beside it and is referenced from the reports.

## What the amendment adds

M(a) = P(a)^T P(a), where P(a) is the whitened operator applied to the 28 unit-L2 probes of the registered localized class -- the same radial B-spline and real-Fourier factors as C224, crossed with one compact temporal bump at retarded age a.

It is not a new class. src/phrt/sources/physical_basis.py already registers the localized class as radial x azimuthal x one bump, and the flat scalar probe is its m=0 partition-of-unity contraction. The amendment stops contracting it before the mechanism comparison.

Normalization: each probe divided by its analytic L2 norm over the emission region, int R_a^2 Phi_b^2 r dr dphi times w sqrt(pi), so the eigenvalues of M(a) are Fisher informations per unit source amplitude and no basis normalisation can masquerade as an information difference.

Derived quantities:

* log_information_volume(a) = sum_k log(1 + SNR^2 lambda_k(a)), which reduces to log(1 + SNR^2 I(a)) when the localized class is scalar
* lambda_max(a) and lambda_min(a), the best- and worst-determined localized modes at epoch a
* H2m / H3m: the registered D statistic recomputed on log_information_volume instead of the scalar curve
* T_rec_best_mode: the depth of the best-determined localized mode
* J_old_best_mode and J_old_log_volume

## What it does not change

* the registered primary source class C224
* the scalar localized probe, its half width, or its normalization
* the common age grid, the SNR grid, the operational threshold, the censoring rule
* T_rec and J_old as registered, which continue to be computed on the scalar probe
* the measurement and noise convention
* the eight registered arms or the sixteen permutation seeds
* the ray maps, whose sha256 remain those pinned in E3C_OPERATOR_GRID_FREEZE.json

## Effect on the reported conclusion

Under the registered scalar statistic the delay-only arm reproduced the full
age-information curve exactly, which reads as "delay diversity supplies all of
the historical reach". On the localized class the same substitution is a median
0.165 relative departure against the spatial-only arm's
0.310, with the direct arm at 0.303. Delay diversity is
the larger of the two contributions in every cell, not the
whole of it. The direction of the canary's conclusion survives; its strength
does not.

This is a diagnostic amendment. It adds a way to see a mechanism difference that the registered statistic cannot see; it does not change any registered measurement, gate or threshold, and it is not evidence for either mechanism by itself.
