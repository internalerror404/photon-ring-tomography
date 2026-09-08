# Source-grounded replacement passages for manuscript037

These are editorial replacements for the identified regressions, not a complete
new manuscript or a new numerical result. Use them with the review's evidence
requirements. Preserve original labels in the archive, not as unqualified prose.
All repository sources below are read at 8c309ff6736e8933df37b9f8e61bcdb495980aec.

## Title and framing

# Photon-Ring Retarded-Time Tomography: The Mahakal Phenomenon

Hina Dixit and Abhinav Chauhan

We use the Mahakal phenomenon to name the separation between access to earlier
source times, the number of supported source directions, and successful recovery
of a specified historical object. Higher-order light paths can sample source-time
regions missed by the direct image. Increasing source resolution can expose null
or weak directions that a coarser model cannot represent. Neither statement says
that source enrichment always destroys injectivity, or that compact temporal
support alone makes a mode invisible.

Source: supplied PDF, definition 1.1 and theorem 4.1; its PDF SHA256 is recorded
in PAPER_I_MANUSCRIPT_REVIEW_037.md. This restores the author-facing Mahakal title;
it does not rename or overwrite the archived Shiva-era manuscript.

## Candidate abstract (subject to completed per-result lineage)

Near-critical black-hole light paths sample a variable source at distributed
retarded times. We distinguish historical reach, the number of source directions
supported by a declared observation model, and held-out recovery of a specified
historical object. For a separable source representation, a temporal factor whose
support is disjoint from the direct retarded-time footprint generates exactly zero
direct columns; higher-order samples can make such columns nonzero without
necessarily making them independent or recoverable. In the archived 12-geometry
finite-model audit, ideal order-labeled observations extend the anchor-connected
detectable interval beyond direct imaging. At the reference geometry, the sampled
direct operator annihilates a 72-dimensional old-contrast target, while the
order-labeled stack retains two operational combinations after profiling the other
152 coefficients of the full L224 model. This count uses the frozen legacy measure;
the available row-reweighting bound permits one to two combinations under its
stated assumptions. Two sealed reconstruction benchmarks address different
objects. Baseline-inclusive emissivity-level span increases from 48 to 80 M in
the reported in-class regimes and mild-mismatch diagnostic, but severe mismatch
remains negative. A separate 60-history morphology benchmark reports paired gains
of 0.133 for TSVD and 0.164 for ridge in its registered error-reduction metric,
with lower confidence bounds 0.101 and 0.116. These aggregate gains do not establish
reliable multiple-feature recovery or a nonzero stable morphology interval. The
numerical results are conditional on the specified finite operators, source spaces,
noise conventions and evaluation metrics. Continuous transfer quadrature remains
unqualified, and the archived index-sum control does not establish a physical
order-resolution advantage. The study therefore delineates a bounded information
and recovery problem rather than demonstrating reconstruction of a physical movie.

Source map: E3C report; R2 replay reference_geometry_information.csv; R1 report;
HMT2 entries in the current evidence ledger, to be linked to its primary endpoint
and family tables before final headline approval. Do not use this candidate
abstract to bypass those links.

## Mathematical spine: the support and nuisance statements

Let a fixed-geometry transfer model map emissivity j to an order-specific field,

    (T_n j)(xi,t_o) = chi_n(xi) w_n(xi)
                     j(r_n(xi), phi_n(xi), t_o - Delta_n(xi)).

The ray-intensity factor contains g^3 under the declared model; geometric area
and measurement noise are specified separately. For sampled source functions
q_lk(r,phi,t)=psi_l(r,phi) tau_k(t), let W_n be the set of retarded times reached
by the actual observer times and retained rays with nonzero transfer weight.

**Proposition (sampled support-nullity).** If supp(tau_k) intersects W_0 in the
empty set, then A_0 q_lk=0 for every spatial factor l. If a retained higher-order
row has nonzero weight, spatial factor and temporal factor, its corresponding
stacked column is nonzero. If m such temporal functions and d_s spatial factors
are independent, they supply m d_s linearly independent coefficient directions
in the direct null space.

*Proof.* Each row is the product of the weight, spatial value and temporal value.
Disjoint temporal support sets the latter to zero at every direct sample. A
nonzero product in one added row proves that column is nonzero. Independence of
the selected basis products supplies the nullity count. No independence among
the newly nonzero output columns follows from this proof.

A corresponding conditional continuum statement uses the full supported
screen-time footprint, not its finite sampled proxy. Disjoint support implies
zero response almost everywhere. A nonzero continuum field requires nonvanishing
on positive measure, not an isolated support intersection. This is a mathematical
statement about the assumed transfer map, not a validation of its discretization.

For the nuisance-adjusted calculation, write y=A_T c_T+A_N c_N+epsilon and
B_T=C^(-1/2) A_T, B_N=C^(-1/2) A_N under the declared positive-definite noise
model. Let H_T=R^T R be the target source Gram matrix and Pi_N the orthogonal
projector onto range(B_N). In source-normalized target coordinates,

    B_known = B_T R^(-1),
    B_cond  = (I-Pi_N) B_T R^(-1),
    F_known = B_known^T B_known,
    F_cond  = B_cond^T B_cond.

The quoted information totals are traces of these normalized Fisher matrices.
Operational directions are counted from the singular values at the declared
amplitude and threshold. If sigma is already included in C, do not multiply the
singular values by the SNR label a second time. This formulation describes the
accepted finite target/nuisance calculation; it is not a reconstruction estimator.
The complete draft must additionally define the source basis, observer schedule,
noise calibration, rank tolerances and recovery metrics for each experiment.

Sources: supplied PDF equations (2), (7), (20)-(27); R2 conditioning/source-metric
records and replay manifest. This restores definitions; no operator was computed.

## Replace section 5.3's physical-localization paragraph

The two operational combinations are temporally broad rather than confined to one
independent epoch. Using their exported source coefficients and retaining the
cross terms of the source Gram matrix, their squared source norms place about
2.44% and 2.35% in [-128.82,-109.09] M, 43.81% and 43.92% in
[-109.09,-89.37] M, and 53.75% and 53.73% in [-89.37,-69.64] M. Thus approximately
97.6% lies in the younger two thirds of this target interval, but the oldest-third
contribution is not zero. The earlier 99.8% statistic groups Cholesky-normalized
coordinates; it is not an energy fraction in a physical time interval. These
localizations describe signed source perturbations, not separately recovered frames.

Source: artifacts/revisions/mahakal_v4_1/LOC025_20260906T184213Z/LOCALIZATION_READBACK.json,
keys intervals[*].source_energy_fraction and note. No new integration is needed.

## Replace the reach interpretation

The archived oldest detectable probe age is 60, 84 and 144 M at inclinations
20, 50 and 75 degrees on the declared grid. This is a supremum of a threshold
mask, not an estimator recovery depth. The corresponding anchor-connected resolved
spans are 60 and 84 M at the first two inclinations and, at 75 degrees, 112 M for
spin zero and 116 M for the other three sampled spins. The high-inclination direct
spans are 108 and 112 M. A common oldest passing grid point across four spins does
not establish spin independence; the anchor-connected quantities themselves vary.

The delay and spatial substitutions giving the archived 0.98 and 0.57 comparisons
transplant independently sampled arrays by index. We retain those results as
index-paired counterfactuals. They do not isolate the physical contributions of
co-registered delay and spatial remapping. Likewise the index-sum compression is
not a physically unresolved spatial image.

Sources: E3C_GEOMETRY_WIDE_OPERATOR_AUDIT.md, H1 tables and interval semantics;
PAPER_I_DEFECT_AMENDMENT_023.md and its control-interpretation dispositions.

## Recovery: preserve the distinct targets and regimes

The R1 sealed bank contains 640 histories across several regimes. At the declared
reference point, TSVD and ridge yield 48 -> 80 M anchor-connected baseline-inclusive
level spans in IN_CLASS_ID and IN_CLASS_OOD and in the mild OFF_GRID_OOD diagnostic.
The severe OFF_GRID_ID result remains 0 -> 0 M. The four fitting-family successes
are a separate breakdown, not a replacement for the regime result. The metric is
level dominated, and its formula and evaluation map must accompany the result.

R1's structure-only stable span is zero at SNR_0=100 and first becomes nonzero at
30000, with 40 M direct and 76 M resolved. Separately, R1L stage-2R validation at
1000 meets its aggregate structural-materiality conditions, while its stable-span
gain remains zero. The latter is neither a sealed main nor a replacement for the
former stable-span endpoint.

The morphology benchmark uses 60 histories and four paired noise draws. In its
registered reduction metric the reported analytic-source-target gains are 0.164
for ridge (lower bound 0.116) and 0.133 for TSVD (0.101). The tested all-order
flux readout does not reproduce the material improvement. The index-sum comparison
is retained as a compression control, not evidence that a physically unresolved
image would fail. Family heterogeneity, unreliable multi-feature recovery, a zero
stable morphology interval and baseline saturation remain part of the result.

Sources: R1_HELD_OUT_MAIN.md; current evidence ledger R1, R1L stage-2R and HMT2
sections, followed to their primary tables and freezes in the claim matrix.

## Revised conclusion direction

The calculations distinguish access to earlier source times, finite-model
identifiability and recovery of a declared source object. Support-disjoint temporal
functions generate exact blind directions for the sampled direct operator, while
added order-labeled observations can provide nonzero historical responses. The
finite-SNR dimension and estimator performance still depend on source resolution,
noise, nuisance parameters and the specified loss. The archived level and aggregate
morphology improvements are therefore bounded computational results; they neither
recover a stable historical movie nor establish the unresolved-image attribution.
The physical transfer-integral accuracy and the appropriate matched physical
control remain separate requirements for stronger acquisition claims.
