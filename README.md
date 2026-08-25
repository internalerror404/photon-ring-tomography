# Photon-Ring Retarded-Time Tomography I — Mac protocol v0.2, executed

Reproducible, matrix-free computational campaign for **Paper I: Class-Dependent
Identifiability and the Separation of Historical Reach from Algebraic Rank in
Near-Critical Null Geodesics**, implementing
`docs/Paper_I_Comprehensive_Experiment_Protocol_Mac_v0.2.md` and
`docs/Paper_I_Mac_Coding_Agent_Handoff_v0.2.md`.

Theory and controlled synthetic computation only. No telescope detection, no
laboratory result, and no recovery from a resolved real photon ring is claimed
anywhere in this tree.

**The registered experiments are complete.** Campaign tag `paper-I-campaign-final`,
commit `03b0d1c9c631`. The manuscript is at
`artifacts/manuscript/PAPER_I.md` (compiled: `PAPER_I.pdf`).

## Governance counts

```
    gates passing:              121
    active blocking failures:   0
    preserved literal failures: 7
    future-phase not run:       11
```

A preserved literal failure is a FAIL that has been adjudicated and kept on the
record rather than reinterpreted; the mechanical status is never edited to match
the disposition. A not-run gate belongs to a phase that is not in scope. Neither
is an unresolved scientific failure. Full roll:
`artifacts/reports/GATE_DASHBOARD.md`.

## Status

| phase | state |
|---|---|
| P0 governance, environment lock, provenance | **done** |
| P1 E0 / G1 canonical reproduction | **PASS**, cross-machine verified |
| P2 matrix-free operator library, gates G2–G6, G9, G13 | **done** |
| P3 E1 factorial + E2 mode atlas | **done** |
| Amendment 001, localized historical support | **done** |
| P4 E3 pilot, single geometry | **PASS** |
| S0 exact Schwarzschild backend | **PASS**, 19/19 |
| 12-geometry ray-map grid | **PASS** |
| G10q measurement-convention gate | **PASS**, E3B regenerated |
| E3C geometry-wide operator audit | **PASS** with Amendment 002 |
| E3D nested source-class stress | **PASS** |
| Manuscript, claim ledger, source bundle | **done** |
| ML, geometry mismatch, order leakage, further classes or geometries | **not authorized** |

## The measurement-model correction

The physical operator originally used `c = g^3` with a flat per-row sigma, which
makes Fisher information scale with the number of rows: splitting one pixel into
k identical children multiplied the Gram by k. Since the lensing bands differ in
solid angle by ~1500x, that silently reweighted them against each other.

The corrected model is pixel-integrated,
`z_p = dOmega_p g_p^3 j + eta_p` with `Var(eta_p) = sigma_Omega^2 dOmega_p`, so
the whitened row is `sqrt(dOmega)/sigma_Omega * g^3 * B`. Gate
`G10q_continuum_noise_quadrature_invariance` locks it at 5.4e-15 under
split/merge; the retired convention is preserved as a literal FAIL with
disposition `RETIRED_PIXELIZATION_DEPENDENT`.

What it moved is recorded in the ledger as
`D-H_flat_sigma_measurement_convention`, and 33 pre-correction artifacts are
marked `SUPERSEDED_MEASUREMENT_MODEL_DEFECT` in
`artifacts/SUPERSEDED_PRE_G10Q.json`. Section 9 of the manuscript states which
conclusions changed and which did not.

## Amendments

- **001 — localized historical support.** Archive depth is set by attenuation,
  not by the longest ray. `docs/amendments/`, `artifacts/reports/`.
- **002 — localized-class mechanism diagnostic.** The registered H2 statistic is
  identically zero for the delay-only substitution because the registered probe
  is spatially flat; that is an algebraic identity, not evidence. The literal
  values are preserved, a gate asserts the identity, and the comparison that can
  discriminate is added on the registered 28-dimensional localized class.
  `artifacts/configs/AMENDMENT_002_LOCALIZED_CLASS_MECHANISM_DIAGNOSTIC.json`.

## Protocol deviations

Recorded in every manifest under `protocol_deviations`, and in
`artifacts/reports/TASK0_ENVIRONMENT.md`:

- **D1_platform** — the protocol targets macOS; this runs on Linux x86_64. All
  float64 CPU numerics are platform-portable; runtime and peak-RSS rows describe
  this host, and no macOS-specific claim is made.
- **D2_no_mps** — no Apple-Silicon device, so gate G11 (CPU/MPS inference
  parity) is `NOT_RUN`. CUDA is deliberately **not** substituted for MPS in any
  registered gate.
- **PROTOCOL_DEVIATION_001_E1E2_BEFORE_G1** — E1 and E2 were run and published
  while G1 stood at `NOT_RUN`. Full record, including what was deliberately not
  done, in `artifacts/PROTOCOL_DEVIATION_001_E1E2_BEFORE_G1.json`.

## Withdrawn and superseded results

`artifacts/PREFIX_INVALIDATION_LEDGER.json` withdraws every artifact produced
before four material defects were corrected: flat-sigma whitening of the mixer,
a reflected retarded-age axis, the 4 x 6 restricted-class misinference, and the
flat-sigma measurement convention. Each superseded file is paired with its
replacement hash.

## Layout

```
configs/            frozen registry (sha256 travels in every manifest)
schemas/            run-manifest JSON schema
src/phrt/           library: config, provenance, operators, audits, io, manuscript
scripts/            one runner per experiment, plus report and manuscript builders
tests/              188 tests, including gate tests that assert the gates catch failures
artifacts/          manifests, gates, tables (parquet + csv twin), reports, freezes
artifacts/manuscript/  the paper, claim ledger, source bundle
docs/               the protocol and handoff, vendored unchanged
```

## Reproducing the manuscript

```bash
python -m pytest tests -q
python scripts/build_canonical_freeze.py   # freeze the citable artifact set
python scripts/build_manuscript.py         # PAPER_I.md, .html, CLAIM_LEDGER.json
python scripts/compile_manuscript.py       # PAPER_I.pdf + page images
python scripts/verify_manuscript.py        # re-derive every number, independently
python scripts/build_source_bundle.py      # PAPER_I_SOURCE_BUNDLE.tar.gz
```

`verify_manuscript.py` runs five independent checks: freeze integrity, claim
re-derivation from the frozen bytes, presence of every rendered value in the
text, regeneration of the headline quantities from the raw per-geometry run
records, and that no claim cites pre-correction bytes. It also cross-checks
every gate row quoted in every report against the gate ledger.

Every reported number is read back out of a canonical table; none is typed into
a report, a plotting script, or the manuscript by hand.
