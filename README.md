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
| P1 E0 toy reproduction | **partial — G1 blocked**, see below |
| P2 matrix-free operator library + gates G2–G6, G9, G13 | **done**, 86 tests |
| P3 E1 factorial + E2 mode atlas | **done** |
| AMENDMENT_001 localized historical support | **done** |
| P4+ physical Kerr (E3–E10) | blocked on G1 |

## Two live blockers

**B1 — the v0.1 generator has still not arrived.** The reviewer ruling of the
G1 unblock states that it is supplied, but no file accompanied the message and
the session upload directory contains nothing newer than the environment YAMLs.
Steps 1–5 of that ruling — import byte-for-byte under `archive/v0.1/`, run
unmodified, compare against the canonical CSVs, require exact rank equality and
1e-8 relative agreement, emit G1 — cannot start. Gate G1 remains `NOT_RUN`, not
passed, and no reproduction is claimed. The physical Kerr phases stay blocked.

The ruling did however pin `RT = 8` and `RS = 3`, and that settles the (K, M)
ambiguity without the generator: a separable class with three spatial modes
cannot be built over two source-plane cells, so `K = 6` counts source cells and
`M = 2` counts screen channels. The previously inferred 4 x 6 class was wrong;
everything has been regenerated against 3 x 8.

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
