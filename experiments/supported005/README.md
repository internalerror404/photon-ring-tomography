# Mahakal II: source-supported modes versus neural completion (005)

Start with RUN_RECORD_CORE.json. The complete REPORT.md, original/final numerical outputs, inherited inputs, and model checkpoints are in the accompanying full/source-input packages. This directory contains the exact executable source, preregistration and compact results; it does not claim binary inputs are already in the GitHub tree.

No neural model was trained and no new ray, physical path integral or root was computed. Twelve saved q8 inverse004 neural fields were read. Three new finite source-response matrices and144 fixed spectral corrections were evaluated under two separately documented source norms. Paper I and its854-unit remainder are unchanged.

## Main findings

1. Exact fitting of nominally high-response modes decreases the noisy data residual but worsens source error in all12 primary full-box comparisons and all72 full-box variants. For the pulse source with robust PINN, median original-chart error rises15.42% to16.36%; the data residual drops8.85 to7.84 in whitened norm. Background PINN error rises21.87% to30.70%. The candidate is not promoted.
2. In the primary135-dimensional full-box model, mean squared-error fractions in remaining weak/null dictionary modes are83.9–84.2% for the background and95.1–95.5% for pulse histories. This is a DIFFERENT source-domain norm from the old4736-point chart loss; it is not a claim that old15% local errors became80% merely from a changed estimator.
3. The old known-pulse inference is conditional on seven nuisance functions. Adding72 spline nuisance factors reduces target singular values from49.95/41.65 to2.96/2.02. With315 flexible factors, the nuisance data space has full128-row rank and pulse amplitudes are zero-compatible after profiling. These are signed unbounded nuisance calculations, not positive-source constrained inference.
4. Two explicit polynomial source histories on the declared box are uniformly positive by a coefficient envelope, yet have negligible data differences under three numerical renderings. Source-box RMS separation0.05494 in units of the unit baseline; old chart RMS separation0.007742. Largest checked data difference1.43e-5 in noise-whitened norm. This is a local numerical ambiguity witness, not a globally certified exact Kerr null mode.

## Original failed gates remain

The first sample-norm normalization of135 columns is ill-conditioned; its4.54e-8 orthogonality residual fails1e-8. Two fixed QR reorthogonalizations with extended-precision products close that arithmetic issue on the same retained span, with unchanged mode counts. They do not fix the metric's missing control of unsampled integration points. The full-box norm is a separately registered postplanned diagnostic, not a silent repair.

Three low-threshold field-correction comparisons failed the0.1 whitened response criterion and remain failed. The coarsest72 full-box source-loss6/8 quadrature comparison initially failed; a fixed12/16 readback of unchanged fields passes with8.75e-6 maximum RMS change. A reporting-only relative-error helper argument in two box chart columns was corrected additively; raw files and the corrective finalize.py preserve the exact history.

## Reproduction

Use the full or source-input artifact package, which supplies inputs/parent004, INPUT_MANIFEST.json, saved physical arrays and neural checkpoints. The inherited package identity and source hashes are checked before computing. From a NEW unpacked source-input copy:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python source/run_all.py
```

The runner reproduces the first-pass failures, numerical closeout, alternate-metric analysis and final reporting correction. It refuses existing primary outputs. Expected environment: Python3.13, NumPy2.3.5, SciPy1.17, PyTorch2.10CPU, pandas; matplotlib only for figures. No paid resources, production-suite run, Kiran deployment, additional source training, R3B or submission occurs.

## Interpretation

For B=USV^T in a declared source norm, exact mode correction uses V_k S_k^-1 U_k^T on the whitened residual. It removes that data residual but transmits noise with variance1/s_k^2. A hypothetical0.10-RMS mode having high response does not imply the actual source coefficient is larger than its noise. The original nonlinear estimate already contains regularization choices.

Next algorithms should use noise-aware shrinkage/regularization validated independently, not unrestricted mode overwrite or an uncalibrated pixel recoverability mask. Prior completion can be useful but is not extra light information. The analysis does not prove an algorithm-independent15% lower bound for the actual pulse source or rule out a better inverse method.

Primary methodological context: Hansen, Truncated Singular Value Decomposition Solutions to Discrete Ill-Posed Problems with Ill-Determined Numerical Rank, DOI10.1137/0911028; official SciPy1.17 BSpline documentation. Only their narrow metadata/abstract/documentation uses were checked, not a novelty audit. New numerical values belong to this local experiment.
