# Photon-Ring Retarded-Time Tomography I — Mac protocol v0.2, executed

Reproducible, matrix-free computational campaign for **Paper I: Null Spaces,
Identifiability, and Stability of Historical Inversion from Near-Critical Null
Geodesics**, implementing `docs/Paper_I_Comprehensive_Experiment_Protocol_Mac_v0.2.md`
and `docs/Paper_I_Mac_Coding_Agent_Handoff_v0.2.md`.

Theory and controlled synthetic computation only. No telescope detection, no
laboratory result, and no recovery from a resolved real photon ring is claimed
anywhere in this tree.

## Status

| phase | state |
|---|---|
| P0 governance, environment lock, provenance | **done** |
| P1 E0 / G1 canonical reproduction | **BLOCKED_PENDING_TOLERANCE_RULING**, see below |
| P2 matrix-free operator library + gates G2–G6, G9, G13 | **done**, 125 tests |
| P3 E1 factorial + E2 mode atlas | **done** |
| AMENDMENT_001 localized historical support | **done** |
| P4+ physical Kerr (E3–E10) | blocked on G1 |

## Two live blockers

**B1 — G1 is substantively reproduced but one cell misses the ruled criterion.**
The generator arrived, hash-verified, and was run unmodified. All 48 integer
rank comparisons agree exactly; every signal-bearing float agrees to 1.5e-13.

One cell of 24 exceeds the 1e-8 relative criterion at 1.31e-8: the noise-free
resolved arm, whose operator is injective on the subspace, so its exact
reconstruction error is zero and both numbers are pure ridge round-off. The two
implementations agree there to 7.3e-18 — 0.033 machine epsilon — but a relative
test on a quantity whose true value is 0 divides by noise.

The ruled tolerance was **not** loosened and no gate was retrofitted to convert
the failure into a pass. Diagnostics were added beside it. The verdict is
`BLOCKED_PENDING_TOLERANCE_RULING`: the agent does not award itself a pass the
registered criterion does not give. E3 stays unauthorized.

Two secondary findings: the generator aborts under pandas 3.x (copy-on-write
makes `to_numpy()` read-only) and was run in a pinned venv rather than patched;
and the canonical ZIP never arrived, so the *cross-machine* execution check is
unperformed.

**B2 — no independent geodesic tracer.** AART 2.1.10 installs and imports from
PyPI, so the primary ray tracer is available. `kgeo` is not on PyPI, so the
registered cross-tracer gate G8 needs a vendored or hand-written second
implementation before any physical ray map is trusted.

## Protocol deviations

Recorded in every manifest under `protocol_deviations`, and in
`artifacts/reports/TASK0_ENVIRONMENT.md`:

- **D1_platform** — the protocol targets macOS; this runs on Linux x86_64. All
  float64 CPU numerics are platform-portable; runtime and peak-RSS rows describe
  this host, and no macOS-specific claim is made.
- **D2_no_mps** — no Apple-Silicon device, so gate G11 (CPU/MPS inference
  parity) is `NOT_RUN`. CUDA is deliberately **not** substituted for MPS in any
  registered gate.
- **D3_missing_v01_generator** — see B1.
- **PROTOCOL_DEVIATION_001_E1E2_BEFORE_G1** — E1 and E2 were run and published
  while G1 stood at `NOT_RUN`. Full record, including what was deliberately not
  done, in `artifacts/PROTOCOL_DEVIATION_001_E1E2_BEFORE_G1.json`.

## Withdrawn results

`artifacts/PREFIX_INVALIDATION_LEDGER.json` withdraws every artifact produced
before three material defects were corrected: flat-sigma whitening that gave
the unresolved channel a free sqrt(6) gain, a reflected retarded-age axis, and
the 4 x 6 restricted-class misinference. Each superseded file is paired with
its replacement hash.

## Layout

```
configs/     frozen registry (sha256 travels in every manifest)
schemas/     run-manifest JSON schema
src/phrt/    library: config, provenance, seeds, operators, audits, inverse, io
scripts/     one runner per experiment, plus the report generator
tests/       73 tests, including gate tests that assert the gates catch failures
artifacts/   manifests, gates, tables (parquet + csv twin), reports, figures
docs/        the protocol and handoff, vendored unchanged
```

## Running

```bash
cd photon-ring
python -m pytest tests -q
python scripts/reproduce_v01.py        # E0
python scripts/build_report.py         # regenerate reports from artifacts
```

Every reported number is read back out of a canonical table; none is typed into
a report or a plotting script by hand.
