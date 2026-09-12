# Mahakal Paper II: KNOT_QUADRATURE_002

Read RESULTS.md and results/COMPLETION.json first. The primary NUMERICAL gate passed. No movie or posterior was fitted. CACHE_REBUILD_001's 142 failures and the new UNIFORM2 control's 34 failures remain unchanged. This is not the missing original R2 execution.

This complete package includes the frozen CACHE001 inputs needed by this stage, all five preregistered source files, the postplanned audit source, actual variable-node ray arrays, operators, panels, logs and full hash-linked physical ledger. The canonical GitHub commit is recorded in GITHUB_RECEIPT.json. GitHub's compact record is not a claim that these binary arrays are repository blobs.

## No-physics software check

Use the recorded Python 3.13.5 / NumPy 2.3.5 / SciPy 1.17.0 environment. In a separate process:

```sh
OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 python source/test002.py
```

This runs 17 model-free tests and cannot generate a movie endpoint. Tests deliberately disable physical solver functions in their own process.

## Saved-data audit

`source/audit002.py` verifies all frozen source/input hashes, all BEGIN/END hash-chain links, every saved node against its physical ledger, chart-pixel membership and area, every basis and analytic metric, and random complete-field contractions. It spends zero physical calls. It refuses to overwrite `results/POSTPLANNED_READBACK.json`; reproduce on an isolated copy without that audit output, not by deleting the original archive's record.

## Physical replay

A replay consumes NEW Paper-II physical calls. Create a separate empty run directory, copy `source/`, `inputs/`, `REGISTRATION.md`, and `provenance/SOURCE_FREEZE.json`. Create empty `results`, `attempts`, and `logs`. Put an explicit authorized replay receipt in `provenance/REGISTRATION_RECEIPT.json` naming its commit. Never overwrite this completed run or old failure records.

```sh
OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 python source/run002.py --run
```

The program caps itself at 600000 new ray calls, 1200 seconds and 8GiB address space, one BLAS thread. Incomplete/invalid runs are not scientific passes. Check the machine-readable completion, not just exit code.

## Next scientific consumer

Use CACHE_INTERFACE.md: KNOT ray counts vary between pixels, q8/q12 mean local composite quadrature, flux is area*g^3*j, source time is observer time minus delay plus 100M, and noise/support remain pinned. Do not silently reshape into old tensor-rule layouts or bypass old-loader hashes. NEXT_STAGE_DRAFT.md lists unregistered inference requirements; it is not an executable experiment authorization.
