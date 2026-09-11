# Movie007 executed-source deposition and audit

This directory was added after Movie007 completion to close a reproducibility gap identified before Movie008. The exact executed Python sources had been hash-frozen before the source-bank/movie outcomes and shipped in the full artifact package, but were not browsable in GitHub.

`Movie007_Executed_Source.tar.gz` contains the four executed source files:

- `source/kerr.py`
- `source/movie007_run.py`
- `source/finalize.py`
- `source/offbasis.py`

Archive SHA256: `8b612decc04a4df9394083c60a7b5109cee1eb5cb3e8a5ee610481573cc3e2fd`.

The individual source hashes are recorded in `MOVIE007_REPOSITORY_AUDIT.json` and match the pre-outcome freeze / final artifact record. This is a post-execution deposition of already frozen bytes, not evidence that the source was committed before execution.

The audit independently replays the regularization selection, all saved reconstruction matrices, per-history and per-frame metrics, and 64 physical tuple/weight points. It also records that Movie006 has no final endpoint, Movie007 has no CI run, and Movie007's union-support endpoint mixes time reach with added source-plane coverage.
