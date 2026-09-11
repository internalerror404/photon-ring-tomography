# Repository audit before Movie009

Date: 2026-09-10. Audited Paper-II base: `research/mahakal_II_movie008_twins_20260910`, based on Movie007 head `60caf340c90d8ea5c64d792cc1f2e1d7e23af2a1` and Movie008 closeout `bdaf9fc2c4fabfe10b4b2d055f7e73c4a46f2f14`.

## Repository inventory and lineage

The root tree, `src/phrt`, `tests`, `configs`, `artifacts`, `scripts`, and all Paper-II experiment directories through Movie008 were inventoried through the GitHub connector. The deep review covered every repository component that can change the Movie009 observation, source metric, inverse, or causal interpretation:

- `src/phrt/operators/physical.py`: pixel-integrated flux, `sqrt(dOmega) g^3 / sigmaOmega` whitening, per-ray source positions and delays, derived readout covariance;
- `src/phrt/operators/whitening.py`: explicit separation of physical operator and noise, source singular values on `C^{-1/2}A`;
- `src/phrt/operators/historical.py`: matrix-free distributed-delay forward map and hand-written adjoint;
- `src/phrt/inverse/ridge.py`, `reduced.py`, `smoothness.py`, `tsvd.py`, and `wiener.py`;
- `src/phrt/metrics/data_prior_split.py`, `cluster_bootstrap.py`, age-interval and morphology metrics;
- `src/phrt/audits/subspaces.py`, rank/tolerance gates, `governance.py`, and `attestation.py`;
- the complete Paper-II lineage `neural_feasibility_001`, `neural_pilot002`, `kerr_chart003`, `kerr_inverse004`, `supported005`, `movie006`, `movie007_support`, and the locally preserved Movie008 source/result package;
- relevant tests for adjoint parity, dense-operator parity, age semantics, source features, constrained backgrounds, and revision-v4.1 gates.

This is a repository-wide inventory plus a line-by-line review of the Movie009 dependency cone, not a claim that every unrelated manuscript paragraph or archived binary was semantically rederived.

## Input and result replay

All Movie009 inputs are copied from the full Movie008/Movie007 package and hash to the registered values. Movie007 q8/q12 operator shapes are `(832,595)` for each order. The stored source Gram replays from its Cholesky factor, support weights sum to one per movie frame, and Movie007's direct 0M / labelled 28M ridge endpoints and Movie008's direct-null causal result were checked from their saved arrays and compact records.

The repository's root README is Paper-I-era and must not be treated as the current Paper-II status page. The Movie007/008 experiment directories are the authoritative Paper-II lineage. GitHub exposes no workflow runs or status checks on the Movie007 head, so this audit makes no CI or fresh full-suite claim.

## Design implications carried into Movie009

1. Analytic truth must be evaluated directly at physical rays; projecting it into the reconstruction basis would erase the off-basis test.
2. Direct nullity is imposed by strict temporal support ending at -6M, not by choosing a small numerical singular vector.
3. The old 595-dimensional ridge remains a frozen baseline. A richer 1617-dimensional classical class is declared before outcomes.
4. The Retarded Neural Field learns only the source inverse; it cannot alter the Kerr renderer or the instrument noise.
5. Movie metrics use histories as bootstrap clusters. Direct and labelled arms share direct noise.
6. Completion outside the old finite class is reported separately and never silently relabelled as likelihood information.

Disposition: `MOVIE009_REPO_AUDIT_PASS_WITH_NO_CI_CLAIM`.
