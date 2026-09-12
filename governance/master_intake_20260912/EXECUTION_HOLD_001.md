# Mahakal Paper II — execution hold 001

Date: 2026-09-12

Status: `R2_EXACT_EXECUTION_PROVENANCE_BLOCKED`

This is an additive governance record, NOT a scientific completion, NOT a repaired R2 deposit, and NOT a prospective executable R3 registration. No new source/noise generation, reconstruction, physical call, or Paper-I unit is authorized by this record.

## Protected branch

Paper I is frozen at `084fb45fedae99f203393dbc1e9cdda9ab250c2d` on `research/mahakal_v4_1`. Do not modify it or its ledgers. This governance branch starts from R2 commit `be7c49ea18c355fe3c13a5ebce0a0d03854fc316`; it does not modify the original R2 or either R3 branch.

## Intake

The uploaded handoff markdown was read completely: 827 lines, 42,536 bytes, SHA-256 `f6d4946cf250b6d63e08f307318aa5e9d11fe4086fb9049a988b03f46f4195cb`. All five accompanying checksum entries matched. The uploaded package contains documentation only, not the original R2 execution directory.

GitHub completion records govern their named executions. Conversation summaries are navigation, not evidence. A later completion describing reused R2 data does not substitute for the missing exact R2 source and original local records.

## Exact R2 mismatch

Required original registration: `db54e5b22b5ae317b0f774f10552e48a69cb86be`.

Required executed source: `source/run_movie009_r2.py`, 58,325 bytes, SHA-256 `93d990c11e39a5cb7bd127967bf65bff07fe28d3c118630077e88d4457c26c2a`.

At audited head `be7c49ea18c355fe3c13a5ebce0a0d03854fc316`, `experiments/movie009_r2_factorized/source/run_movie009_r2.py` is instead a launcher expecting patched executable SHA-256 `39cfbcf12c1918eb86a1ef842714fa900bb3204ed0078e692d243740ce4cadff`. The audited R2 subtree is `e41717f9644743482a987881cd26712712779709`. It contains a different source/archive/patch lineage, not the handoff's exact summary, original V3 freeze, or five listed postplanned JSON records.

Do not relabel this launcher as the handoff's executed source. Do not regenerate missing records from prose or rounded numbers. Preserve all existing source versions and failures.

## Required original byte identities

| Record | SHA-256 |
|---|---|
| `source/run_movie009_r2.py` | `93d990c11e39a5cb7bd127967bf65bff07fe28d3c118630077e88d4457c26c2a` |
| `SOURCE_FREEZE_V3.json` | `e51185d7ffb791a02d1075e1965fe136188479408e3df25913142cb7db378c4d` |
| `results/SUMMARY.json` | `6b91c3306d2fa0f64926b8ad7e28fe07c620b5a36d861766939668b209d4ddfc` |
| `POSTPLANNED_TRUE_BACKGROUND_DYNAMICS_ORACLE.json` | `f03f2a780616e8f09fbfceff33effff4c664a41ad68086c68f8b50ba7f3dc85d` |
| `POSTPLANNED_SEQUENTIAL_LOCAL_BASIN_ORACLE.json` | `1f67c27df4ad0c0ac7f1093b82acfc5fde28f3b50dc50ede85669518ff279a3e` |
| `POSTPLANNED_BACKGROUND_PARAMETER_MLP.json` | `890adb423e1846b133d6dcee9f3bd16f1228c1186379a6286482f5d52f585497` |
| `POSTPLANNED_PARAMETER_MLP_SEQUENTIAL_ORACLE.json` | `d78a7f08b999438bf2bf636fe34b0f85aa3147994adbc0b2ba61da8f3ad70781` |
| `POSTPLANNED_BACKGROUND_FORECAST_FISHER.json` | `eabfb7b8df7fa930a13b1ecd7770b9ebf7685b25cebe8b19a0a21b25079c4631` |

These are expected identities from the handoff, not claims that the bytes were recovered. The postplanned records have only basenames pinned; locate their actual paths by name and hash. Recover the whole original directory including raw arrays, populations/noise, logs, checkpoints, candidate ledger, and incomplete attempts, not just these eight files.

## Existing R3 records must remain distinct

1. At `122f8b9123bd619d0742ff9a808bc67471ad5828`, `experiments/movie009_r3_background_posterior/COMPLETION.json` explicitly reports a postplanned experiment on examined R2 data and returns `MOVIE009_R3_BACKGROUND_POSTERIOR_FAIL`. The K=65 Gaussian beam has 6M span95, 10M span90, differential pass 0.230469, and fitted whitened discrepancy 1.166158. It is not fresh confirmation. The same rank-96 representation with true background also fails, so background point estimation is not established as the sole bottleneck.
2. At `b9ba0514a2932cf12ccb2c194911756c02a33b84`, `experiments/movie009_r3_posterior_beam/REGISTRATION.md` describes a separate fresh population. `EXECUTION_FAILURE_002.md` records the forked lazy-NPZ handle defect, with no selected validation rule and no test reconstruction result. The compared branch additions contain no completion record. The existing MAP/temperature-scaled-fit averaging specification does not by itself establish calibrated posterior marginalization.

Do not overwrite either R3, recycle its sources/noise, or treat an incomplete attempt as a pass. Additional later branch names were visible but their scientific records were not audited in this intake; reconcile them before assigning a successor identity.

## Recovery sequence and future design requirements

First recover and byte-verify the original R2 records. Deposit them additively on an archival branch explicitly linked to registration `db54e5b...`; preserve failures and identify the deposit as retrospective. Pin the full archival commit, read its contents back, and verify raw hashes, dependency closure, original source-freeze relationships, and completion case counts. Hash matching alone does not prove historical timing or complete execution. Missing artifacts keep this hold open.

Only afterward authorize a separately identified, fully source-frozen successor. Its primary output must marginalize the joint background/history distribution, not one plug-in subtraction. Infer family labels and parameters from observations, carry within- and between-basin uncertainty, use normalized prior/proposal/evidence weights, count direct data exactly once, and prohibit truth labels or true-basin initialization in non-oracle arms. Calibrate and report 90%/95% coverage on held-out history clusters; distinguish pixelwise from whole-movie coverage and raw posterior from any conformal calibration. Preserve original movie, identification, differential, and q8/q12 gates; do not suppress numerically unstable samples after inspection.

Required controls include authenticated R2 plug-in, multi-start single-best, joint posterior, a separately labelled true-background oracle, and a registered timing/order negative control. Freeze actual generator, inference, prior, scorer, calibration, environment, resource limits, fresh RNG streams, and completion/failure validator before new outcomes. No placeholder source or incomplete-run promotion is permitted.

## Claim corrections retained

Movie007's 28M result is partial, in-class, one-chart, ideal-order-label recovery at SNR0=300. Movie008's alpha=0.08 movie-fidelity gate failed; no conversational 26M pass is accepted. Movie009's registered rich arm fails at 0M span. Movie010's rich arm fails at 0M, but its old595 control has a 4M span95 and must not be erased. Movie011 remains negative. Movie013 has no winning same-data representation variant. Movie012 is not promoted. No conversational Movie009 alpha-0.40 movie pass is accepted.
