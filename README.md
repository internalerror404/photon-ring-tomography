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
| P1 E0 / G1 canonical reproduction | **PASS** (cross-machine verified) |
| P2 matrix-free operator library + gates G2–G6, G9, G13 | **done**, 137 tests |
| P3 E1 factorial + E2 mode atlas | **done** |
| AMENDMENT_001 localized historical support | **done** |
| P4 E3 pilot, single geometry a\*=0.5 i=50° n∈{0,1,2} | **AUTHORIZED**, in progress |
| P5+ (E4–E10) and the 12-geometry grid | not authorized |

## Two live blockers

**B1 — closed.** G1 passes. The generator was hash-verified and run
unmodified; the canonical reference arrived three independent ways, all
byte-identical to its SHA-256 manifest, and is vendored at
`archive/v0.1/reference/`.

| gate | result |
|---|---|
| `G1_v01_reproduction_relative` | FAIL, disposition **FAIL_AS_WRITTEN**, tolerance unaltered |
| `G1_v01_reproduction_mixed_tolerance` | **PASS** — worst cell uses 7.32e-4 of allowance |
| `G1_scientific_reproduction` | **PASS_WITH_NUMERICAL_QUALIFICATION** |
| `G1_cross_machine_reference` | **PASS** |

The identifiability table is **bit-for-bit identical** between the reviewer's
machine and this Linux host — every rank and every singular value, utilisation
0.000e+00. The QR-convention contingency does not arise. Only the reconstruction
table moves, at 1.85e-4 of allowance, the anticipated finite-noise-sample
effect.

Reproduce with:

```bash
python scripts/run_g1_reproduction.py --reference-dir archive/v0.1/reference/reference_results
```

Diagnostic runs take `--gate-file` so they cannot write into the provenance
record.

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
