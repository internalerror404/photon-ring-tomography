# TASK 1 — P1-E0 / GATE G1 CANONICAL REPRODUCTION

## Identity
- branch: `claude/experiment-review-mac-rthiz1`
- commit: `d8fd5ca840268538493733211b319a458fb9b416`  (source tree dirty: False)
- config: `paper1_experiment_registry_v0.2.yaml`  sha256 `2ba66f0209fe1cdec97b8cf5862494c22fb94704318f9601a7a1f9eb4b783796`
- environment sha256: `2a20e241e1761eea7769c0c2d6d1b2c0a47388deba3f9875fe68cba909b1c9dd`
- hardware: Linux x86_64, 4 cores, 15.7 GiB
- python 3.11.15; numpy 2.4.6, scipy 1.17.1, torch 2.13.0, aart 2.1.10
- run_id: `G1_20260825T003703Z_2ba66f02`
- generator sha256: `9e93848f306c646a84da204c6b1be0508620f83ba860b7c8a51f94e039bf3d51` (matches the supplied artifact)

## Mechanical gate result
**BLOCKED_PENDING_TOLERANCE_RULING**

All 48 integer rank comparisons agree exactly. Every signal-bearing float
agrees to **1.485e-13**, five orders
inside the 1e-8 criterion. One cell of 24 exceeds the ruled relative criterion
at **1.313e-08**, and it is the one cell where a
relative criterion is not well posed.

## What was executed

1. The supplied generator was hashed, matched, and copied byte-for-byte to
   `archive/v0.1/generate_synthetic_results.py`. It was **not** edited,
   reformatted, import-wrapped, or parameterized.
2. It was executed unmodified in an isolated output directory.
3. An independent matrix-free reimplementation
   (`src/phrt/operators/v01_toy.py`) was compared against its outputs.

### Reference-execution defect, resolved without touching the source

The generator aborts under this session's default **pandas 3.0.5** at line 124:

```text
vals = d.prior_subspace_smallest_singular_value.to_numpy()
vals[vals <= 0] = np.nan
ValueError: assignment destination is read-only
```

Under copy-on-write, `DataFrame.to_numpy()` returns a read-only array. This is
an environment incompatibility in a **figure** block, not a defect in the
science, and it occurs after `paper1_identifiability.csv` is written.

The source was not patched. A pinned interpreter matching the generator's
expectations was supplied instead — numpy 2.2.6, pandas 2.2.3, matplotlib
3.10.9 — under which it runs to completion. The archived source hash is
unchanged.

## Results

### Canonical identifiability table at N = 5

| arm | rank (ref / independent) | restricted rank (ref / independent) | restricted sigma_min (ref) | (independent) |
|---|---:|---:|---:|---:|
| `identical` / `resolved` | 88 / 88 | 16 / 16 | 0.000000e+00 | 0.000000e+00 |
| `identical` / `unresolved` | 48 / 48 | 16 / 16 | 0.000000e+00 | 0.000000e+00 |
| `diverse` / `resolved` | 216 / 216 | 24 / 24 | 1.876416e-02 | 1.876416e-02 |
| `diverse` / `unresolved` | 48 / 48 | 23 / 23 | 0.000000e+00 | 0.000000e+00 |

Every rank matches. Note `prior_subspace_rank = 16` for the identical arm: that
is exactly the analytic cap this repository derived before the generator
arrived, **rank(P) x RT = 2 x 8 = 16**, and it holds at every N in the
reference table.

The independent implementation reaches these numbers by a different route: a
matrix-free operator with a hand-written adjoint, not the original's dense
row-assembly loop. Parity between the two constructions is exact (0.0) and the
adjoint identity holds to 1.1e-14.

### The one exceedance

| | |
|---|---|
| cell | `resolved`, `relative_noise = 0.0`, `prior_subspace_oracle_ridge_error` |
| reference | `5.57692292754989478e-10` |
| independent | `5.57692300078700935e-10` |
| absolute difference | **7.324e-18** |
| in machine epsilon | **0.0330 x** |
| relative difference | 1.313e-08 |

This is the noise-free arm of an operator that is injective on the
24-dimensional subspace. Its exact reconstruction error is **zero**. Both
numbers are therefore pure Tikhonov round-off at lambda = 1e-12, and their
ratio measures nothing: two correct implementations differ in the last bits of
a quantity whose true value is 0, and a relative test divides by that noise.

The two implementations agree to **three hundredths of one machine epsilon**.

## Diagnostics
| gate | status | measured | threshold | note |
|---|---|---|---|---|
| G1_generator_sha256 | **PASS** | 9e93848f306c646a84da204c6b1be0508620f83ba860b7c8a51f94e039bf3d51 | 9e93848f306c646a84da204c6b1be0508620f83ba860b7c8a51f94e039bf3d51 | archived generator is byte-for-byte the supplied artifact |
| G1_matrixfree_dense_parity | **PASS** | 0 | 1e-10 | matrix-free operator vs original-style dense assembly, all 24 arms |
| G1_matrixfree_adjoint | **PASS** | 1.14785e-14 | 1e-08 | hand-written rmatvec, 5 probes per arm |
| G1_identifiability_row_keys | **PASS** | 0 | 0 | 24 canonical rows; missing []; extra [] |
| G1_identifiability_ranks_exact | **PASS** | 0 | 0 | largest absolute integer-rank disagreement across 24 rows x 2 rank columns |
| G1_identifiability_floats_relative | **PASS** | 1.41444e-13 | 1e-08 | worst at prior_subspace_smallest_singular_value @ diverse | resolved | 2 |
| G1_reconstruction_row_keys | **PASS** | 0 | 0 | 12 canonical rows; missing []; extra [] |
| G1_reconstruction_floats_relative | **FAIL** | 1.31322e-08 | 1e-08 | worst at prior_subspace_oracle_ridge_error @ resolved | 0.0 |
| G1_exact_zero_cell_absolute | **PASS** | 7.32371e-18 | 1e-15 | absolute disagreement on the cells whose exact value is structurally zero, = 0.0330 x double epsilon. Cells: ['resolved | 0.0 :: prior_subspace_oracle_ridge_error'] |
| G1_reproduction_relative_signal_bearing | **PASS** | 1.48452e-13 | 1e-08 | the ruled relative criterion over every cell whose exact value is not structurally zero. Excluded by construction (noise-free arm, operator injective on the subspace, so the exact error is 0 and the reference value is ridge round-off): ['resolved | 0.0 :: prior_subspace_oracle_ridge_error'] |
| G1_v01_reproduction_relative | **FAIL** | 1.31322e-08 | 1e-08 | worst relative disagreement over both canonical tables; integer ranks disagree in 0 places |

The ruled gate `G1_v01_reproduction_relative` is recorded **FAIL**. Its
tolerance was not loosened after the failure was seen, and no gate was
retrofitted to convert it into a pass. Two diagnostics were added *beside* it:
the relative criterion over cells whose exact value is not structurally zero,
and absolute agreement on the cell where absolute is the only meaningful
measure. Both pass with large margins.

An earlier revision of this run declared a single global absolute tolerance
across all float cells. That was ill-posed — the cells span ten orders of
magnitude, so one absolute threshold is simultaneously too tight and too loose
— and it was replaced by the targeted measure above.

## Deviations
**D1_platform** — registered: macos_native (execution_target in registry); actual: Linux x86_64.

  Effect: No macOS-specific or Apple-Silicon-specific result can be claimed. All float64 CPU numerics are platform-portable and unaffected; runtime and peak-RSS rows describe this Linux host, not a Mac.

**D2_no_mps** — registered: optional Apple-Silicon MPS for compact neural models; actual: no MPS device present.

  Effect: Gate G11 (CPU/MPS inference parity) cannot be executed and is recorded NOT_RUN. Neural training runs on CPU float32. CUDA is not substituted for MPS in any registered gate.

**REFERENCE_EXECUTION_ENVIRONMENT** — the generator requires pandas < 3.0. A
pinned venv was supplied rather than editing the source. Recorded in
`artifacts/g1_run/G1_VERDICT.json`.

**MISSING_REFERENCE_CSVS** — the ruling's step 6 compares against
`reference_results/paper1_identifiability.csv` and
`paper1_reconstruction.csv`, shipped in the canonical ZIP. Only the `.py`
arrived; the ZIP and `.txt` did not. The comparison therefore runs against
outputs generated *on this host* from the hash-verified source, so the
independent implementation is fully checked, but the cross-machine question —
does the generator produce identical bytes on the reviewer's Mac and on this
Linux host? — is **unperformed**. QR and SVD sign and ordering conventions can
differ between LAPACK builds, so this is not a formality.

## Claim effect
Permits: nothing new yet. The reproduction is substantively complete but the
registered criterion was not met as written, and the agent does not award
itself the pass.
Forbids: starting the E3 pilot, which the ruling authorizes only "once G1
passes".

## Artifacts
- `archive/v0.1/generate_synthetic_results.py` (byte-for-byte, sha256 verified)
- `artifacts/g1_run/results/*.csv`, `artifacts/g1_run/G1_VERDICT.json`
- `artifacts/tables/g1_identifiability_comparison.parquet`
- `artifacts/tables/e0_reproduction_independent.parquet`
- `artifacts/tables/g1_disagreements.parquet`

## Next authorized step
A reviewer ruling on one question: does the 1e-8 relative criterion carry an
absolute floor for cells whose exact value is structurally zero? If yes, G1 is
a pass on the evidence already produced and the E3 pilot is authorized. If no,
G1 stands FAIL and the deficiency is a comparison convention, not a defect in
either implementation.

Also outstanding: send the canonical ZIP so the cross-machine execution check
can run.
