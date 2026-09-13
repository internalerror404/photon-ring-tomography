# BLOCK_SLICE_SMC_006 execution amendment 001 — receipt-key correction

The first launch stopped in the preflight before schedule generation because the external registration receipt used the field `commit`, while the already-frozen executable requires `github_commit`.

This is a record-only correction. No scientific source, benchmark configuration, RNG seed, proposal, mutation kernel, threshold, input population, or executable byte changes. The first failure, stderr, stdout, and supervisor exit record are preserved. The results directory remained empty; no 006 dataset, optimizer, posterior particle, evidence estimate, coverage result, or benchmark outcome existed.

Before the second launch, the receipt is rewritten to include `github_commit = ca598e2d4c48ccea5147d4fcea732b66703c1af6`, pointing to the already-deposited pre-outcome registration and exact source archive. The source-freeze hashes remain unchanged. Any subsequent scientific or implementation failure remains binding under the original registration.
