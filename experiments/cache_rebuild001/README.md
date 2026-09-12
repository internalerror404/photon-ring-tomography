# Mahakal Paper II - CACHE_REBUILD_001

This is a complete, source-frozen, newly executed physical-cache reconstruction. It is not the missing R2 archive. Read `RESULTS.md` first: the broad basis qualification FAILED, while the independent ray and tested analytic-field checks passed. No movie or posterior was fitted.

## Read existing results without physical calls

Use Python 3.13.5, NumPy 2.3.5, SciPy 1.17.0 (the recorded run environment). From this directory:

```sh
OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 python source/test_rebuild.py
```

There are 17 model-free checks. The two `source/audit_*.py` programs read cached records only and perform no physical calls. They refuse to overwrite their original audit JSON outputs: run them against an isolated copy with those specific audit outputs absent to reproduce them. Do not delete the archive's original files.

## Reproduce the physical computation

This spends NEW Paper-II physical calls; it is not required just to inspect results. Use a new isolated directory, copy `source/`, `REGISTRATION.md`, and `provenance/SOURCE_FREEZE.json`; create empty `results/`, `attempts/` and `logs/` directories, and add an explicit, dated `provenance/EXECUTION_AUTHORIZATION.json` identifying the authorized replay. Do not copy or overwrite the original results. The program checks source/registration hashes and rejects nonempty results or attempts directories.

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  PYTHONDONTWRITEBYTECODE=1 python source/rebuild.py --run
```

The code caps this replay at 28,000 separated and 80 ODE transfer calls, 900 seconds and 8GiB address space. It runs on CPU and has no network or GitHub-write actions. Its imported original Kerr logger is redirected to the new bounded Paper-II-only ledger. No Paper-I path or ledger is opened.

Successful process termination is NOT a scientific pass. Inspect `results/COMPLETION.json`: the recorded run completes with `CACHE_REBUILD_001_COMPLETE_NUMERICAL_GATE_FAIL`. Physical errors/timeouts preserve `FAILURE.json` and incomplete data rather than successful subsets.

## Artifact boundary

`ARTIFACT_MANIFEST.json` hashes the delivered source, raw cache arrays, ledger, numerical panels, and audit records. `SHA256SUMS.txt` additionally covers that manifest. GitHub's compact deposition is documented in `GITHUB_RECEIPT.json`; the full binary cache and per-ray ledger are in this ZIP, not claimed to be GitHub blobs.
