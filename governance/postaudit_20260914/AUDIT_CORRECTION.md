# Mahakal Paper II: additive post-audit correction

Date: 2026-09-14
Scope: photon-ring historical movie recovery, not CovQ/QFIC.
Disposition: CORRECTNESS_REPAIR_REQUIRED; no new experiment authorized or executed.

## Historical record and current correction

The historical canonical record remains unchanged at commit `05b465529a905252051b155209a6b134df605f07`, path `experiments/smc006_006r/within_family_slice_smc006r/CANONICAL_COMPLETION.json`.

Preserve `WITHIN_FAMILY_SLICE_SMC_006R_COMPLETE_DIAGNOSTIC_FAIL`, its 128 datasets and 480 method-case runs, failed release gates, and descriptive as-coded metrics. Withdraw the interpretation `within_family_slice_exploration = ACCEPTED_AT_SYNTHETIC_BENCHMARK_SCOPE`. HOLD the existing `FAMILY_EVIDENCE_BRIDGE_007` instruction to freeze the conditional sampler and change only evidence estimation. The old completion and next-stage documents are historical records, not current execution authority.

The corrective audit is `MAHAKAL_II_READ_ONLY_AUDIT_20260913`. Its original report SHA-256 is `56117b82e1984cd727f721b775dfa1f487c28102532dccade86666ea9f20edac`; its original FINDINGS.json SHA-256 is `209f9ffbbc183c349b65b9cc88d60123ca63692c6ff61aa7d2438a4548197005`.

A01: the frozen sampler draws in logit coordinates, maps with expit, and clips to INTERIOR_EPS, while scoring an ordinary continuous transformed density. Sampling and scoring therefore specify different measures. Archived family-0 initial-draw clipping was 4508/32768 particles in 8D and 3409/16384 in 16D. These are not terminal-weight frequencies or estimates of final posterior bias. Omitted uniform-prior mass does not bound proposal clipping mass.

A02: the initial slice right endpoint is computed from the already-clipped left endpoint. The registered forensic check gives uniform-target second moment 0.33275462969631137 rather than 1/3, although the mean remains 0.5. The isolated corrected-bracket control is not a fully repaired sampler and does not fix A01.

The exact defective source is 13881 bytes, SHA-256 `57ac52629d5c17ed871fd5bbbcd1f2dcd511508b85c07a6a8e38a7c7c62c3e90`. Its production caller SHA-256 is `f192ed44747ac3d93f82cee2a6a5437f0dfe30242fb4d3518242b81f147e3791`.

## Preserved evidence and limits

- Movie007 retains 28M partial measured-support in-class span95 at SNR0=300 versus 0M direct, on one chart with ideal order labels.
- KNOT002 retains its finite-panel numerical PASS at `c783d46d0567a6300ce99c2fdedfe55051b91ffd`; not a continuum certificate or movie result.
- Physical 003 remains local provisional COMPLETE_DIAGNOSTIC_FAIL: eight observations/four independent twin-history clusters have supported 28M point reconstructions; posterior weights collapse and coverage fails. The matched single-best control also passes with slightly lower aggregate error. No marginalization advantage or population/off-family/full-annulus success is established. The truths have three double-hotspot backgrounds and one single-hotspot background, not flare-drift backgrounds.
- 004/005 are failed algorithm stages; 006 remains incomplete after 11/128, with no subset promotion.
- Lower 006R mean errors remain descriptive, not validation of conditional distributions. Slice R1 used approximately 4.41 times all and 11.97 times native likelihood evaluations versus the parent. The factorized 8D/16D reference family decision depends only on its first 2D block; shared nuisance evidence cancels.
- Neither defect establishes physical impossibility or quantifies its share of final 006R bias. No evidence-complete percentage is assigned.

## Intake and deposition boundary

The supplied Archive.zip SHA-256 is `67d1b5084ce4e4c0b1582d513c10e4911264a4a6adef401d1419b200305d0bc6`. Available original manifests passed 8337 size/hash checks; 8344 checksum-file entries also passed. The unmodified supplied 003 read-only verifier passed. These are integrity checks, not new scientific runs.

The available handoff is `Mahakal_PaperII_PostAudit_Handoff_20260914.md` (prepared September 13), SHA-256 `10dd3505069553774a0fe10e695b088dfb514197acde17960af38a3a2d29ae50`. Its exact September-13-named counterpart, PROJECT_STATE.json, CLAIM_LEDGER.json, CORRECTNESS_REPAIR_PROTOCOL_DRAFT.yaml, SOURCE_INDEX.json, EVIDENCE_COPY_INDEX.json, ORIGINAL_PACKAGE_INDEX.json, READ_FIRST.md and described transfer verifier were not found. The delivered compact ZIP has seven files rather than the described indexed evidence tree. Eight original research/audit ZIPs are available; the ninth research_archives ZIP is a duplicate new handoff, not an authenticated ninth original package. No missing index or original record has been reconstructed under its old identity.

The 006/006R original ZIP matches the canonical 69778629-byte SHA-256 `37035c10fa9972af9c6593b1c6bd13dbb3fe9bbddead4a3933dd3ceba670d08c`. The canonical 006R directory contains only three compact files. Full remote source/raw-bank deposition is not established by those hashes. Exact FINDINGS.json and the defective slice source are deposited separately alongside this correction; they do not constitute a full raw-data deposit. Verify actual commit readback before claiming either deposit succeeded.

The separately discovered `research/mahakal_II_logit_slice_smc007_20260913` points to `3c27fd335b7f349364c225997a98395cdcbdfd5a`; its inspected experiment directory contains a source_archive with chunks 00 and 01, and no completion. This is an occupied identity, not an accepted repair or authority to execute.

## Correct next sequence

Close provenance/deposition gaps additively. Specify matching target, proposal and mutation laws, including boundaries and Jacobians. Register actual source, environment, independent references, seeds, sample sizes, accuracy requirements, thresholds, logging and work budgets BEFORE new outcomes. Test known normalizers, sample-versus-density consistency, uniform stationarity moments/tails and nonuniform bounded targets, both transitions and the entire initialized/tempered/recombined pipeline. Then compare validated methods at matched work on fresh cases, retaining exact nuisance cancellation as a diagnostic and adding a genuinely coupled nonlinear bounded target. Record actual proposals, rejected candidates, ancestry, increments, RNG and failures. Only after this decide whether a different evidence estimator is needed. Physical calibration and adequately sized fresh confirmation remain separate later stages.

Preserve non-oracle joint background/history family and parameter inference, multiple hypotheses and joint uncertainty, direct likelihood counted once, and no final single plug-in background subtraction. Preserve all inherited movie/identification/differential/family/direct-control and clean-AND-actual-fitted q8/q12 gates. Define calibrated 90/95 percent sets, widths and independent cluster counts. Admission may not depend on detector response or reconstruction success.

Paper I remains protected at `research/mahakal_v4_1`, commit `084fb45fedae99f203393dbc1e9cdda9ab250c2d`. This correction is on a separate branch, with no changes to original scientific records, no new rays/observations/sampler populations and zero Paper-I units. Original R2 source `93d990c11e39a5cb7bd127967bf65bff07fe28d3c118630077e88d4457c26c2a` and exact execution records remain missing; V4 `39cfbcf12c1918eb86a1ef842714fa900bb3204ed0078e692d243740ce4cadff` and rebuilt caches do not authenticate them.
