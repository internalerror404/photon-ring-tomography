# Mahakal Paper II - recovery and execution preflight 002

Date: 2026-09-12
Status: `EXECUTION_BLOCKED_MISSING_FROZEN_INPUTS`
Scope: additive recovery/preflight record, not a scientific completion, not an original-R2 provenance repair, and not authorization for new physical work.

## What was recovered and actually executed

From `experiments/movie009_r2_factorized/source/` at commit `be7c49ea18c355fe3c13a5ebce0a0d03854fc316`, the V2 text-encoded archive and the registered V3/V4 patches were materialized locally. The archive and patch Git blob identities were checked. Both patches applied with zero fuzz, and each resulting executable matched its recorded SHA-256.

- V2 source: 51,372 bytes; SHA-256 `04e2c39f3819cca96b2c8735c43fd7a849480251a458d981d1288539fb0f204d`.
- V3 source: 53,627 bytes; SHA-256 `4e4f3a54bb24dc9d6aab8db1ca270063b6a550643d6966c69f6913e33355b50f`.
- V4 source: 60,160 bytes; SHA-256 `39cfbcf12c1918eb86a1ef842714fa900bb3204ed0078e692d243740ce4cadff`.

The unmodified V4 entry point was executed in the local CPU environment. It exited with code 1 at `authenticate()`, before population generation, because `inputs/PHYSICAL_AND_OPERATOR_ARRAYS.npz` was absent. Its original `results/FAILURE.json` is preserved. No authentication predicate was bypassed.

Twelve separate data-independent tests of the recovered functions passed: compact window; interpolation partition; out-of-support zero; periodic values; scalar/batched joint solve; independent normal-equation solve; constant-field interpolation; toy exact-movie metric; toy anchor failure; inactive-frame rule; 90/95 percent tail distinction; and a toy neural forward/backward check. These are software tests, NOT the registered self-test or scientific movie gates. Any 28M values in toy metric tests are constructed software fixtures, not recovered movies.

The preflight harness was locally hash-frozen before testing: SHA-256 `e52be2b1724d573805e7d84ccf6605e2a51a096da22dbe2b962292a2e628608f`. The exact source, harness, freeze, environment, logs, failure, test records and hashes are retained in the delivered recovery package. This GitHub record does not claim that package's entire contents have been deposited in this subtree.

## What remains unrecovered

The handoff's original 58,325-byte source, SHA-256 `93d990c11e39a5cb7bd127967bf65bff07fe28d3c118630077e88d4457c26c2a`, was not recovered. Neither were its exact original completion and diagnostic records. The available V4 implementation is a different source identity and cannot authenticate the original R2 numerical claims.

Required scientific data still absent from the local run:

| File | Required SHA-256 |
|---|---|
| `PHYSICAL_AND_OPERATOR_ARRAYS.npz` | `54204f14b8c834fb3c54dc012c9827e711f339fc6c30251802fea71ac6d8274e` |
| `SUPPORT_WEIGHTS.npz` | `72080e09e722b01a821d2989d706f21eccfc9ce7671d1fa2f18f66bcd56a7952` |
| `REGULARIZATION_SELECTION.json` | `f3739497a08973bec6ed0b5c174188ad1b2321b469efa06750de2b43bcddf090` |

The required Movie007 and Kerr Python dependencies also remain unverified locally. Fresh GitHub contents inspection found `experiments/movie007_support/executed_source/Movie007_Executed_Source.tar.gz` at `e93c659f16ac1d8723968c13dea9f91e8bea66ef`. Its README lists the four executed Python sources and archive hash `8b612decc04a4df9394083c60a7b5109cee1eb5cb3e8a5ee610481573cc3e2fd`. This archive is listed, not claimed to have been decoded and hash-verified in this preflight. Binary fetches failed, and one returned text representation contained an omission marker; no guessed bytes were used.

Movie007's `SOURCE_AND_ARTIFACT_HASHES.json` explicitly says its full binary arrays and other raw results remain in separately delivered packages rather than the compact GitHub results.

## Search scope and limits

Inspected the R2 source lineage, relevant later branch trees, Movie007 contents and executed-source directory, archive/artifact trees, and release/workflow locations. An owner-scoped exact-hash code search returned no match; that search covers default branches and is NOT exhaustive across history. The inspected later R2 subtrees retained the same available V4 lineage. No exact original R2 deposit or authenticated input cache was found in these locations. This does not prove absence from every GitHub object, deleted ref, external store, or inaccessible attachment.

An auxiliary File Library search found an indexed `run_movie009_r2.py` with a different implementation. It was not available as authenticated original bytes and is not promoted to the handoff's executed source.

## Disposition

- Original R2: remains provisional; provenance hold remains open.
- Current execution: missing-input preflight failure, not a scientific failure of the hypothesis.
- Registered self-test: not passed; full movie experiment: not run.
- New physical calls: 0. Paper-I units: 0. Scientific population-generation calls: 0.
- Paper I remains protected at `084fb45fedae99f203393dbc1e9cdda9ab250c2d`.

A separately registered clean rebuild is a possible successor route if the old cache cannot be recovered. It requires explicit permission for new Paper-II-only physical integrations, source/dependency audit, a frozen finite resource budget and numerical checks, and fresh scientific sources/noise after registration. It must not replace old hashes, overwrite failures, retroactively validate R2, recycle the already occupied R3 identities, or weaken the movie, identification, differential or q8/q12 gates. No such rebuild was executed or authorized by this record.
