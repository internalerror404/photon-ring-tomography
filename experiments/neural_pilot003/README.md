# Mahakal II pilot003: physical source-crossing camera and Euler-inspired inverse tests

The next experiment is executed, not merely proposed. It connects actual Schwarzschild null-ray source crossings, redshift and pixel integration to the inverse data. Earlier pilot002 used physical scattering delays but manufactured inverse maps; this pilot removes that separation for its stated face-on setup.

## Scope and reproducibility

Face-on static observer at r=100M, Schwarzschild, equatorial surface-brightness annulus r=[6,12]M, circular emitting material, no absorption, three crossing orders, ideal separately resolved annuli. Not rotating Kerr, volumetric NeRF, VLBI, PSF, deployed Kiran, or a rigorous interval certificate. Every result below concerns this model and these synthetic histories.

Seven executable Python files and the committed protocol are provided. Run in a fresh writable copy:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python source/run_all003.py
```

The launcher was composed after its individual phases ran and was not rerun end-to-end. Full checkpoints, camera arrays, source predictions, query ledger, failed-export logs and full-precision results accompany the downloadable experiment package. The compact CSV rounds derived per-seed metrics to nine significant figures.

## Physical camera

The primary solver regularizes the radial turning point and inverts a radial angular integral. The independent solver integrates u''+u=3u^2 and dT/dpsi=1/[b*u^2*(1-2u)] from the observer. Crossings are psi=pi/2+n*pi. The common face-on frequency law is g=sqrt(1-3/r_source)/sqrt(1-2/r_observer). The methods compute endpoints separately but do not independently derive this radiation law.

On 96 preselected positions, maximum disagreements are 1.8705e-12M in source radius, 3.0462e-10M in flight time and 8.6819e-14 in g. Detector comparisons at 32 vs 64 radial quadrature nodes differ by at most 7.2163e-10 relatively; the two formulations at q8 differ by 1.6001e-11. Fitted neural fields re-rendered at q4 versus q16 differ by at most 6.2059e-7. Nine forward and twelve post-fit checks pass, at finite-tested numerical scope.

The exact finite-observer solid-angle Jacobian is used, with pixel noise variance sigma^2 times the full declared pixel area. A single absolute density calibrated on the direct unit-source reference is shared across orders. Main inverse SNR label: 1000, not an observational feasibility forecast. There are 240 direct rows or 720 all-order rows.

The source-time envelopes under the fixed clock subtraction of 100M are [-7.012,2.204], [-33.643,-19.254], and [-50.418,-35.831] M. They are envelopes of rays and five exposures, not continuous coverage. Relative per-order areas are 1, 0.02077 and 0.000672. The raw forward summary contains a misnamed delay_min field derived from source-time envelopes; it is not used by the renderer. Actual flight-time ranges are supplied in verification.json in the full archive.

## Old events: positive known-template inverse result

One smooth source is compared with variants containing a compact event at -26M and two events at -26/-43M. Every variant has exactly identical direct data. At SNR1000 the first and additional second event produce whitened data distances 327.05 and 62.10 in their respective indirect orders. These are deterministic noise-model distances, not statistical significance claims.

When the two event SHAPES are supplied, with their amplitudes and six background coefficients unknown, the nuisance-adjusted event singular values are 326.70 and 62.10. Direct-only target rank is zero; direct plus first order sees one; all orders see two. Three noisy estimates of true amplitudes (1,1) are (1.00186,1.00303), (1.00080,0.98116), and (1.00383,0.99765). Model standard errors are 0.00306 and 0.01610. This is a restricted known-template inverse result, not recovered unknown morphology or a movie.

## Neural reconstruction remains inadequate for the events

Median radially weighted old-source contrast error across seeds 11,22,33:

| Method | Smooth source | One unexpected event | Two unexpected events |
|---|---:|---:|---:|
| Data-only co-moving neural field |4.87%|77.45%|65.97%|
| Robust co-moving PINN |4.86%|79.41%|67.87%|
| Staged residual PINN |2.90%|67.63%|66.06%|
| Fourier/time-spline ridge |20.84%|450.18%|421.68%|

The old region is [-52,-12]M and includes unobserved times. A separate observer-window-envelope score makes the spline's event errors about 29%, versus 422-450% globally; the actual observations are still only five exposures. Its good data fit does not control extrapolation. The spline is an unconstrained fixed comparator, not a claim to be the best possible classical method.

The staged method improves the smooth source but does not solve event recovery. It changes parameter allocation and representation in addition to training sequence; this is not an isolated pure-boosting effect. The two joint methods have 1377 parameters, while the staged pair has 1258. Physics weight 0.03 and all budgets were fixed before outcomes. One background with two variants and three noise/initialization seeds is not a broad source population.

Neural event data residuals have mean squared whitened values about 77-82 instead of near one. The known-template fits attain about one. A declared post-test frozen-hidden-feature readout solve only reduces the former median by 4.5%, leaving about 60-91. Thus a last-layer correction alone is insufficient; it does not prove all neural optimization or representations must fail. Unlike the first manufactured pilot, the robust PDE penalty is numerically tiny and the data-only model fails similarly, so attributing this entire failure to an excessively strong physics penalty is unsupported.

## Euler paper: borrowed strategy, not a replication

The linked paper by Ganeshram, Duruisseaux and Anandkumar uses adapted ansatz/coordinates, residual boosting and high-precision optimization, with a separate spline/interval-verification stage. It explicitly records remaining nonlinear-stability certification. We tested co-moving coordinates and one staged correction; we did not implement SS-eSOAP, SS-Broyden, adaptive collocation, Euler blowup or interval proof. Numerical agreement is not rigorous certification.

Primary source read: https://anima-ai.org/wp-content/uploads/2026/09/Euler.pdf . See its methods and Remaining Work to Complete the Proof. Our proposed use is a transfer of numerical organization, not the application of Euler equations to photons.

## Accounting and disclosures

The registration committed code hashes after 86 declared engineering evaluations and before independent validation or inverse training. The fixed point cohort was re-evaluated after a NumPy-bool JSON export error; 192 lost-runtime evaluations remain charged, and the exporter repair was committed before the replay. It changed output handling, not physical formulas, cases or tolerances. Source and payload identities are preserved.

Total separate pilot charge: 2054 of 6000 (80 boundary-angle, 1683 radial-quadrature, 291 ODE attempts). The experiment trained 36 neural reconstructions in 48 optimizer stages, plus 12 classical fits, 18 known-template fits and 18 supplementary readout solves. The direct neural fit is reused across observationally identical source twins, not counted three times. Paper I and its remaining 854 units are untouched; its production suite was not rerun. No paid resources.

The complete report and full arrays/checkpoints are in the accompanying chat experiment package. The important outcome is a checked physical forward bridge and a positive restricted event-information result, alongside a clearly unresolved general neural inversion problem—not a claim that the full NeRF/PINO/Kiran architecture is already solved.
