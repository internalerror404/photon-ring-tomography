# Mahakal II Movie009 — fresh-seed direct-null movie signal ladder

**Return:** `MOVIE009_CAUSAL_MOVIE_THRESHOLD_PASS`  
**Registered threshold:** `alpha_star = 0.32`, bracketed on the predeclared grid as `(0.24, 0.32]`.

Movie009 follows Movie008 without reusing its nuisance backgrounds, target directions, or Gaussian noise. It keeps the same frozen Movie007 physical operators, the same four source-orthonormal old nonaxisymmetric direct-null modes, the declared 385-dimensional nuisance movie, the same conditional-GLS estimator, and the same frame/movie criteria.

At direct-reference `SNR0=300`, the direct observations remain exactly identical for the two positive twins at every amplitude, so direct identity is exactly 50% and direct movie pass is 0%. Direct plus the first indirect image identifies the correct twin in 100% of cases throughout the ladder.

| Target source norm `alpha` | Labelled identity | Median coefficient error | P90 coefficient error | All-active-frame movie pass | Bootstrap 95% interval |
|---:|---:|---:|---:|---:|---:|
| 0.08 | 100% | 0.2505 | 0.3752 | 15.42% | 10.83–20.00% |
| 0.16 | 100% | 0.1253 | 0.1876 | 61.25% | 54.58–67.50% |
| 0.24 | 100% | 0.0835 | 0.1251 | 86.46% | 82.08–90.63% |
| **0.32** | **100%** | **0.0626** | **0.0938** | **95.42%** | **92.92–97.50%** |
| 0.40 | 100% | 0.0501 | 0.0750 | 100% | 100–100% |
| 0.48 | 100% | 0.0418 | 0.0625 | 100% | 100–100% |

The preceding point, `alpha=0.24`, fails the aggregate 95% requirement, the bootstrap-lower requirement, and the per-complexity requirement. The result is therefore the tested bracket `(0.24,0.32]`, not a fitted continuous critical amplitude.

At `alpha=0.32`, all three fresh complexity groups pass independently:

| Group | Identity | Median coefficient error | All-frame movie pass |
|---|---:|---:|---:|
| Two-mode | 100% | 0.0616 | 96.25% |
| Three-mode | 100% | 0.0618 | 97.50% |
| Four-mode | 100% | 0.0638 | 92.50% |

At `SNR0=100`, no reliable-movie threshold is reached by `alpha=0.48`; the largest pass rate is 62.92%.

The observed coefficient error follows the conditional Gaussian `1/alpha` scaling. At the fresh threshold, observed median error is 0.0626 versus predicted RMS 0.0697, indicating a signal-to-noise transition rather than an optimizer transition.

Numerical and governance checks:

- frozen Movie008 mode-bank hash reproduced exactly;
- 60 fresh target directions: 20 each with two, three, and four nonzero modes;
- target source-Gram error `3.41e-14`;
- direct q8 and q12 target responses exactly zero;
- paired noisy direct observations byte-identical;
- maximum q8/q12 twin discrepancy `1.464e-4` relative and `1.265e-2` whitened, below the registered `5e-4/0.1` gates;
- minimum analytic emissivity lower bound across the ladder `0.5842`; at the threshold `0.6395`;
- independent conditional-GLS readback maximum difference below `6e-11`;
- all 19 final verification checks pass;
- new physical calls: zero; Paper-I units used: zero.

The first independent verifier run stopped after reproducing the scientific threshold because the initial summary listed threshold booleans only through the first passing point, while the verifier listed all six amplitudes. A committed record-only amendment preserved the original summary and failed verification, appended the two already computed rows, and changed no source, noise, estimate, bootstrap, or scientific table. The final readback passes.

## Supported claim

> On one Kerr chart with ideal order labels and a frozen four-mode old target under a declared 385-dimensional nuisance movie, first-indirect light reconstructs a 95%-reliable direct-null historical movie for fresh positive twins once the tested target source norm lies in `(0.24,0.32]` at `SNR0=300`; direct data remain exactly unable to distinguish the twins.

This does not establish arbitrary, off-basis, full-annulus, multi-chart, visibility-domain, telescope, or observational black-hole movie recovery. Movie007's full-annulus and off-basis negatives remain standing.
