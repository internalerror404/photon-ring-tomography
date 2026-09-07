# PAPER_I_PATH_DOMAIN_RULING_030

Repository: internalerror404/photon-ring-tomography  
Branch: research/mahakal_v4_1  
Reviewed commit: b6c3873b22f945ce20c40c3c55e80f516954cb00  
Disposition: G1_NUMERICAL_CLOSEOUT_ACCEPTED_T2_PATH_DOMAIN_VALIDATION_AUTHORIZED

Author-directed project review, not a journal referee decision. The review inspected
connected records and source and executed 20 independent scalar radial-domain and
arithmetic checks. It did not evaluate the campaign's 680 rays, run a full transfer
pipeline, or independently execute the reported 589-test suite.

## 1. Decisions

ACCEPT G1's numerical qualification for the same 237-mark curved candidate at the
registered resolution and tolerances. The delivered record includes both late pairs,
shifted band/boundary/response comparisons, the tighter-root comparison, band-normalized
tessellation, sampled local nesting, topology diagnostics, and an exported array hash.
All nine completion conditions are recorded. No further hull ladder, closeout replay,
or physical boundary-root query is required or authorized here. This is numerical
qualification under the declared tests, not a continuum proof about every point.

ACCEPT the discovery that the recorded NaNs arise from a final library marker after
sanitization/clamping, not from the previously claimed failed floating-point primitive
in the tested radius path. Withdraw the earlier deterministic-solver-failure account.

DO NOT yet accept the proposed split into 532 recoverable numerical errors and 148
physical plunges. Negative radius and a finite subhorizon radius are observations of
the analytic continuation, not independent certificates of the physical trajectory.

AUTHORIZE T2 as a path-domain/existence predicate for the SAME equations and same image
order, followed by independent validation. Do not switch source_radius2 to source_radius3
because one returned a negative number, force a positive radius, change order n, or
continue a physical trajectory through its horizon/infinity endpoint. The full transfer
and complete common-sky quadrature remain unqualified; R3B and new target spectra remain
blocked. C13 and all earlier immutable records retain their existing scope.

## 2. What the sources establish, and what the new inference adds

Repository evidence: t1_first_invalid_primitive.py records finite intermediate checks
and raw radii before the clamp. It labels positive masked raw values PHYSICAL_LANDING...
and negative masked values NUMERICAL_FINITE_BUT_NONPHYSICAL... using their sign, without
an independent path-duration test. Preserve those arrays; add sign-neutral aliases:
RAW_NONPOSITIVE_RADIUS_MASKED and RAW_POSITIVE_SUBHORIZON_RADIUS_MASKED. The source mask2
only tests whether r4 has a small imaginary part. That alone does not prove an accessible
EXTERIOR turning point: four-real-root capture orbits also exist. Require root ordering,
observer-connected allowed intervals and horizon comparison before naming a physical leg.

External primary theory checked: AART (Cardenas-Avendano, Lupsasca and Zhu, 2023),
section II.3 equation (32), restricts the nth equatorial crossing to the physical Mino-time
interval. Section II.4 explicitly notes that the analytic source-radius function can
return a negative or even apparently plausible value when the requested crossing does
not exist. Gralla and Lupsasca (2020), section IV.2, distinguishes four-real-root escape
orbits from four-real-root capture orbits by root position relative to the horizon.
These are physical-domain conditions, not a new repair invented to fit the 680 outputs.

Therefore a plausible explanation for SOME OR ALL of the negative-radius points is an
angular crossing requested after the observer-connected ray has already escaped the
exterior branch. A plausible explanation for a subhorizon value is a requested crossing
after horizon termination. Neither has been measured on this cohort in this review.
If verified, the order contribution is physically absent and its exclusion is correct;
there is no missing exterior value to recover by choosing a different analytic expression.
A captured ray can still contribute at EARLIER exterior crossings. Never blank the entire
ray or its other orders merely because one requested crossing is absent.

AART's official README also describes enlarged sampling hulls whose extra points are
masked analytically. Numerical convergence of those envelope curves does not imply that
every enclosed sample has every requested crossing. Preserve their safety-factor and
clamp conventions; distinguish sampling envelope, physical crossing domain, and the
finite emitting annulus. No defect in AART's physical predictions is established merely
by finding its intentional sentinel. The project needs explicit reasons, not an
interpretation that every NaN means a failed solve.

## 3. The requested domain condition

Use s for increasing backward Mino parameter, with s=0 at the actual observer. It is NOT
Boyer-Lindquist coordinate time, source age, or the retarded delay Delta. Match its energy
normalization to the pinned angular and radial formulas. For each order n obtain s_n
from the actual angular travel, including polar turns and the registered beta convention.

At M=1 the radial potential is

    R(r) = [r^2+a^2-a*lambda]^2 - (r^2-2r+a^2)*[(lambda-a)^2+eta].

First determine the observer-connected real allowed trajectory using its conserved
quantities, radial root multiplicities/order, initial direction, and the horizon. Root
reality tests alone and raw output signs are insufficient, especially near critical
or nearly degenerate roots. There are TWO separate questions:

    existence: s_n lies before termination of that exterior trajectory;
    emission: the crossing lies in r_plus < r(s_n) <= 50.

For an ordinary capturing ray with no accessible exterior radial turn,

    s_H = integral[r_plus,r_obs] dr/sqrt(R(r)),
    s_50 = integral[50,r_obs] dr/sqrt(R(r)),
    emitting Mino interval = [s_50,s_H).

For an ordinary scattering ray with accessible simple turn r_t > r_plus, define

    J(r) = integral[r_t,r] dr/sqrt(R(r)),  J_o=J(r_obs).

If r_t < 50 < r_obs, its emitting interval is

    [J_o-J(50), J_o+J(50)].

If the turn lies strictly outside 50 there is no emitting interval. Equality/grazing
and uncertain endpoints require their own boundary status, not forced classification.
The inward/outward leg changes at s=J_o; both legs belong to the SAME root branch.
For reference, escape to infinity occurs at s=J_o+J(infinity); a finite-radius outgoing
termination is a different convention and must be stated. The annulus-exit test avoids
that endpoint ambiguity for a source bounded by r<=50. Do not mix finite r_obs=1000
with an infinite-observer turn time without a documented approximation/error analysis.

The equations above are definite-integral constructions from the radial ODE, not a
copy of any potentially convention-dependent displayed antiderivative endpoint.
Critical/double-root cases, ambiguous root sorting, non-equatorial-access polar motion,
near-horizon endpoints, and unverified event counts return DOMAIN_UNRESOLVED until
independently checked. Use the existing physical cutoffs and source norm; no new cutoff.

Compare the angular crossing interval with radial path/source intervals using recorded
numerical error enclosures and signed margins. Outside intervals means absence only when
the uncertainty intervals separate. Touching/overlapping bounds remain unresolved. Store
whether an enclosure is a rigorous bound or a convergence-qualified numerical estimate;
do not call a quadrature error estimate a theorem. A simple same-equation event integration
or independent definite quadrature is the validation reference, not the raw-radius sign.

Only after establishing a valid emitting event compute r, phi, common-origin coordinate
time, radial sign and g^3. If the event is independently known to exist but the pinned
closed form still gives an inadmissible value, that is evidence for a cause-specific
implementation repair under the SAME branch and order. Record and validate that repair
separately. Do not invent another branch to supply a missing event.

## 4. Status vocabulary and numerical evidence

Return explicit reason codes, at least:
- VALID_EMITTING_EVENT
- EXTERIOR_EVENT_OUTSIDE_SOURCE_ANNULUS
- NO_NTH_EXTERIOR_CROSSING_CAPTURE
- NO_NTH_EXTERIOR_CROSSING_ESCAPE
- NO_ANNULUS_INTERSECTION_ON_PATH
- DOMAIN_UNRESOLVED
- VALID_EVENT_NUMERICALLY_UNRESOLVED.

A physically absent contribution can be zero without assigning a fake source position,
time or redshift. Keep the legacy NaN and raw continuation value as diagnostic fields,
not as physical coordinates. Invalid downstream finite redshift is not a field envelope.
Check the predicate on previously FINITE outputs too: elliptic continuation can become
positive again beyond the physical path. Choosing between type-(2) and type-(3) formulas
is based on the verified roots; deciding whether a crossing exists is a separate step.

The review's independent radial fixtures demonstrate this directly. For a Schwarzschild
radial potential with impact parameter 6 and observer radius 1000, the elliptic inversion
agrees with independent definite quadrature on the physical branch (largest radius
comparison error 8.53e-14 in this fixture). The same formula gives about -1000.006 at
Mino parameter 0.810163, after its physical escape at 0.809163; a later periodic argument
returns a positive radius near 1000, also outside that original physical path. No
alternative radial formula is needed to explain the negative or revived positive value.
These are scalar equation fixtures, NOT classifications of the project's 680 samples.

## 5. Authorized T2 implementation and validation

D0: write the derivation, source-unit dictionary, radius/horizon/observer conventions,
source-domain interval definitions, and versioned status overlay. Freeze code, pinned
backend source hashes, datasets, immutable curve arrays, candidate selection, numerical
error policy and the independent validation plan before new outcome-bearing evaluations.
The current 680 plus inspected controls are development/reproduction inputs, not a fresh
holdout. Their classification is required, but cannot be advertised as independent
confirmation merely because the evaluator changed.

D1: construct one explicit-domain wrapper and apply it to the diagnostic cohort plus
healthy controls, including direct order, both radial types/legs, mask boundaries,
near-critical points and finite outputs outside the source annulus. Allow at most 3000
new charged evaluations before this stage's decision point. Save full complex roots,
constants of motion, angular travel, path limits, source intervals, error margins, raw
and masked outputs, and status reasons. No target information is inspected. If the domain
logic is not resolved, stop rather than using the remaining batch for unregistered guesses.

D2: evaluate a frozen independent holdout with independent quadrature/event tracking or
multiprecision methods solving the same equations. Retain the second batch's >=4000
validation reserve as budget; actual executed counts must be reported, not rounded up.
No production backend substitution is allowed. Assess missed and invented events as
well as accuracy of r, exp(i*phi), coordinate time and g^3 for events known to exist.
Keep numerical error policies tied to the unchanged response budgets; a zero count of
invented/missed events outside declared uncertainty regions is required on the tested
holdout, not claimed globally. Record confidence scope and unresolved boundary cases.

D3: compare old and explicit statuses on all available core maps without silently
regenerating them. If all audited masked points are physically absent, report that outcome;
no positive recovery count is required. If an admissible event was lost, inventory its
measure and rerun only the versioned affected validation later. Do not claim any old
endpoint or reconstruction moved without computing it. Kernel, event existence,
source-domain integration, transfer-field accuracy and detector quadrature remain
separate qualification layers. Event classification alone does not solve within-cell
variation of delay, source azimuth or g^3.

Prioritize this domain determination before paying to regenerate all dropped contour
arrays. After D2 passes, bounded contour re-derivation using the same wrapper may proceed
only inside the REMAINING second batch and its frozen selection rule. Export actual
points/endpoints, branches and uncertainty this time; no contour claim from counts alone.
No new boundary-hull queries or hull refits are authorized; use the accepted payload.
Stop for review before R3B, target spectra, estimator tuning or any new submission freeze.

## 6. Correct the stage counter before launch

The final return/RESOURCE_LEDGER_029 reports 1080, but committed attempt ledgers show:
T1_20260907T074951Z_3d42022 = 480;
T1_20260907T075031Z_c35cb34 = 1080;
T1_20260907T075138Z_1113f3e = 1080.
That is 2640 second-batch evaluations and 20552 cumulative transfer evaluations including
17912 from the first pilot. The G1-closeout guard already reconciles those three runs
and reports 17360 second-batch evaluations remaining. Use that reconciled value unless
an actual byte-backed accounting error is demonstrated. Unique points are not a cost
counter: repeated attempts count. The discrepancy is a summary correction, not grounds
for repeating the physical runs. Preserve both source records with an additive overlay.

No new transfer allowance is created: D1/D2/any permitted D3 share those 17360 remaining
calls under the existing 20000 second batch and lifetime ceiling 250000. Reserve before
all independent-validator as well as primary evaluations. End-to-end point/order solves,
failed calls, retries and alternate-precision checks all count. Cached read-only algebra
is distinguished from reevaluating the physical integrals. Keep the 8 GiB and remaining
part of the inherited cumulative two-hour limit after runtime reconciliation. No paid
resources, no third batch. Boundary spend is 33410 and 890 remain unused under 34300;
this ruling does not spend or expand that remainder.

## 7. Sources and relationship to the manuscript

Repository primary inputs at reviewed commit:
- scripts/revision_v4_1/t1_first_invalid_primitive.py.
- G1C_20260907T075203Z_d252697/{GEOMETRY_CLOSEOUT_029.json,TRANSFER_AUDIT_029_RETURN.md,RESOURCE_LEDGER_029.json}.
- The three T1 ATTEMPT_LEDGER_029.json files named above.
- G1C CLOSEOUT_ARRAYS_029.npz is reported with SHA256
  192eb9598c27ed2f96811ba8a8c27bbae2e09d2ac17769f4143a60771332e634.
The review read metadata and the JSON record, not the entire binary payload locally.

Primary external theory consulted for the new domain reasoning:
- Cardenas-Avendano, Lupsasca & Zhu, Adaptive Analytical Ray Tracing of Black Hole Photon
  Rings, arXiv:2211.07469, sections II.3-II.4, equation (32), appendix A.2.
  https://arxiv.org/html/2211.07469
- Gralla & Lupsasca, Null Geodesics of the Kerr Exterior, arXiv:1910.12881,
  sections IV.2-IV.3 and VI. https://arxiv.org/html/1910.12881
- AART official README, sampling-envelope/masking explanation:
  https://github.com/iAART/aart
These references motivate a mathematically defined next test, not unperformed per-ray
results or replacement of the pinned backend with the current upstream version.

The user-supplied manuscript equation (2), page 6, already includes the physical validity
factor chi. Explicitly validating chi is consistent with that model. The older manuscript
is not the source of the new hull or marker diagnosis, and its old image-order/physical
claims are not automatically revalidated by this ruling.
