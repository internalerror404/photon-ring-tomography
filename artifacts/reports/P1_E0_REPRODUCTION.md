# TASK 1 — P1-E0 / GATE G1 CANONICAL REPRODUCTION

## Identity
- branch: `claude/experiment-review-mac-rthiz1`
- commit: `5abbb08a4e5801248764d1dd015786951c840d3c`  (source tree dirty: False)
- config: `paper1_experiment_registry_v0.2.yaml`  sha256 `2ba66f0209fe1cdec97b8cf5862494c22fb94704318f9601a7a1f9eb4b783796`
- environment sha256: `2a20e241e1761eea7769c0c2d6d1b2c0a47388deba3f9875fe68cba909b1c9dd`
- hardware: Linux x86_64, 4 cores, 15.7 GiB
- python 3.11.15; numpy 2.4.6, scipy 1.17.1, torch 2.13.0, aart 2.1.10
- run_id: `G1_20260825T013544Z_2ba66f02`
- generator sha256: `9e93848f306c646a84da204c6b1be0508620f83ba860b7c8a51f94e039bf3d51` (matches the supplied artifact)

## Mechanical gate result
**CROSS_MACHINE_REPRODUCTION_DEFECT** — E3 pilot **NOT_AUTHORIZED**

Under the reviewer-adjudicated tolerance specification
`RELATIVE_ONLY_NEAR_ZERO_DEFECT`:

- `G1_v01_reproduction_relative` = **FAIL_AS_WRITTEN**, preserved unaltered with
  its original 1e-8 pure-relative tolerance;
- `G1_v01_reproduction_mixed_tolerance` = **PASS**;
- `G1_scientific_reproduction` = **PASS_WITH_NUMERICAL_QUALIFICATION**;
- `G1_cross_machine_reference` = **FAIL**.

Integer ranks, dimensions, row identities and arm labels agree exactly. Under
the ruled criterion

```text
abs(candidate - reference) <= 1e-14 + 1e-8 * max(abs(candidate), abs(reference))
```

applied uniformly to every floating cell with no exclusions, the worst cell
consumes **7.320e-04** of its allowance — a margin
of roughly 1366x.

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

### The zero-limit cell

| | |
|---|---|
| cell | `resolved`, `relative_noise = 0.0`, `prior_subspace_oracle_ridge_error` |
| reference | `5.57692292754989478e-10` |
| independent | `5.57692300078700935e-10` |
| absolute residual | **7.324e-18** |
| in unit-scale binary64 machine epsilon | **0.0330 x** |
| allowance under the ruled criterion | 1.001e-14 |
| fraction of allowance used | **7.320e-04** |
| pure relative difference | 1.313e-08 |

This is the noise-free arm of an operator injective on the 24-dimensional
subspace, so the reconstruction error tends to zero and what remains is set by
the Tikhonov regularizer at lambda = 1e-12. It is a **zero-limit,
regularization-dominated cell**: not a cell whose stored value is zero, but one
whose value is determined by the regularization rather than by any signal. A
relative test on such a cell divides one round-off residual by another and
measures the regularizer, not the agreement.

The residual is **7.324e-18**, which is **0.0330 times unit-scale binary64
machine epsilon**. That unit is deliberate: it is not a ULP, since a unit in the
last place is relative to each number's own magnitude and these cells span ten
orders of magnitude, so a ULP would mean something different in every row.

## Diagnostics
| gate | status | disposition | measured | threshold | note |
|---|---|---|---|---|---|
| G1_generator_sha256 | **PASS** | – | 9e93848f306c646a84da204c6b1be0508620f83ba860b7c8a51f94e039bf3d51 | 9e93848f306c646a84da204c6b1be0508620f83ba860b7c8a51f94e039bf3d51 | archived generator is byte-for-byte the supplied artifact |
| G1_tolerance_specification | **PASS** | – | RELATIVE_ONLY_NEAR_ZERO_DEFECT | RELATIVE_ONLY_NEAR_ZERO_DEFECT | reviewer-ruled adjudication. Criterion applied uniformly to every floating reproduction cell: abs(candidate - reference) <= 1e-14 + 1e-8 * max(abs(candidate), abs(reference)). Exact equality required for integer ranks, dimensions, row identities, and arm labels. |
| G1_matrixfree_dense_parity | **PASS** | – | 0 | 1e-10 | matrix-free operator vs original-style dense assembly, all 24 arms |
| G1_matrixfree_adjoint | **PASS** | – | 1.14785e-14 | 1e-08 | hand-written rmatvec, 5 probes per arm |
| G1_identifiability_row_identities | **PASS** | – | 0 | 0 | 24 canonical rows compared exactly on ['spatial_channels', 'readout', 'max_order']; missing []; extra [] |
| G1_identifiability_dimensions | **PASS** | – | 24 rows x 7 cols | 24 rows x 7 cols | 7 shared columns |
| G1_identifiability_ranks_exact | **PASS** | – | 0 | 0 | largest absolute integer-rank disagreement across 24 rows x 2 rank columns |
| G1_identifiability_mixed_tolerance | **PASS** | – | 1.4099e-05 | 1 | fraction of the ruled allowance used by the worst cell (prior_subspace_smallest_singular_value @ diverse | resolved | 2); residual 4.396e-17 = 0.1980 x unit-scale binary64 machine epsilon |
| G1_reconstruction_row_identities | **PASS** | – | 0 | 0 | 12 canonical rows compared exactly on ['readout', 'relative_noise']; missing []; extra [] |
| G1_reconstruction_dimensions | **PASS** | – | 12 rows x 6 cols | 12 rows x 6 cols | 6 shared columns |
| G1_reconstruction_ranks_exact | **PASS** | – | 0 | 0 | largest absolute integer-rank disagreement across 12 rows x 0 rank columns |
| G1_reconstruction_mixed_tolerance | **PASS** | – | 0.000731963 | 1 | fraction of the ruled allowance used by the worst cell (prior_subspace_oracle_ridge_error @ resolved | 0.0); residual 7.324e-18 = 0.0330 x unit-scale binary64 machine epsilon |
| G1_v01_reproduction_relative | **FAIL** | FAIL_AS_WRITTEN | 1.31322e-08 | 1e-08 | pure relative criterion, preserved unaltered on the record. It is not well posed on a zero-limit, regularization-dominated cell, where both values are round-off residuals of a quantity whose limit is zero; superseded for adjudication by G1_v01_reproduction_mixed_tolerance. |
| G1_v01_reproduction_mixed_tolerance | **PASS** | – | 0.000731963 | 1 | ruled criterion over every floating cell of both canonical tables, no exclusions. Worst cell uses 7.320e-04 of its allowance; worst residual 4.396e-17 = 0.1980 x unit-scale binary64 machine epsilon. Integer ranks disagree in 0 places. |
| G1_scientific_reproduction | **PASS** | PASS_WITH_NUMERICAL_QUALIFICATION | PASS_WITH_NUMERICAL_QUALIFICATION | PASS_WITH_NUMERICAL_QUALIFICATION | all integer ranks, dimensions, row identities and arm labels exact; all floating cells within the ruled mixed criterion. The qualification is that one cell is zero-limit and regularization-dominated, so its agreement is established absolutely rather than relatively. |
| G1_cross_machine_reference | **NOT_RUN** | – | - | 1 | the two standalone canonical CSVs were not supplied. The comparison harness is implemented and runs with --reference-dir; until it does, whether the generator emits identical values on the reviewer's machine and on this Linux host is untested. LAPACK QR and SVD sign and ordering conventions can differ between builds, and this generator's projections come directly from qr(). |

Retired entries, kept visible rather than deleted:

| gate | status | disposition | measured | threshold | note |
|---|---|---|---|---|---|
| G1_reproduction_relative_signal_bearing | **NOT_RUN** | WITHDRAWN | - | - | withdrawn: required classifying one cell as excluded. The ruled mixed criterion applies uniformly and needs no exclusion. Superseded by G1_v01_reproduction_mixed_tolerance. |
| G1_exact_zero_cell_absolute | **NOT_RUN** | WITHDRAWN | - | - | withdrawn: a bare absolute floor is only meaningful on the zero-limit cells it was scoped to. The ruled mixed criterion carries the same absolute floor for every cell. Superseded by G1_v01_reproduction_mixed_tolerance. |
| G1_identifiability_row_keys | **NOT_RUN** | RENAMED | - | - | renamed to G1_identifiability_row_identities when the adjudicated mixed criterion replaced the pure relative one |
| G1_reconstruction_row_keys | **NOT_RUN** | RENAMED | - | - | renamed to G1_reconstruction_row_identities when the adjudicated mixed criterion replaced the pure relative one |
| G1_identifiability_floats_relative | **NOT_RUN** | RENAMED | - | - | renamed to G1_identifiability_mixed_tolerance when the adjudicated mixed criterion replaced the pure relative one |
| G1_reconstruction_floats_relative | **NOT_RUN** | RENAMED | - | - | renamed to G1_reconstruction_mixed_tolerance when the adjudicated mixed criterion replaced the pure relative one |

`G1_v01_reproduction_relative` is preserved as **FAIL** with disposition
**FAIL_AS_WRITTEN**. Its tolerance is unchanged and its status was never edited
to match the adjudication; the mixed-tolerance gate stands beside it rather
than replacing it in the record.

Two earlier improvised diagnostics have been withdrawn in favour of the ruled
criterion, which needs no cell classification: a signal-bearing relative gate
that required excluding a cell, and a single global absolute tolerance that was
ill-posed across cells spanning ten orders of magnitude. The ruled mixed
criterion applies uniformly, which is why it is better than either.

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
The cross-machine comparison, which requires the two standalone canonical CSVs.
They were not supplied with the adjudication, so `G1_cross_machine_reference`
is **NOT_RUN** and the E3 pilot stays **NOT_AUTHORIZED**.

The harness is implemented and self-tested in both directions: against an
identical reference it returns PASS and authorizes E3; against a reference with
one rank altered by 1 and one float perturbed by 1e-6 relative it returns
CROSS_MACHINE_REPRODUCTION_DEFECT and withholds authorization. One command
closes it:

```bash
python scripts/run_g1_reproduction.py --reference-dir <path-to-canonical-csvs>
```
