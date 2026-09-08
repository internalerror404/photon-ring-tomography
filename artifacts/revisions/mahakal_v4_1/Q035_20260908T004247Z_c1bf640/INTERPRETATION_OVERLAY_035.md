# INTERPRETATION_OVERLAY_035

Ruling: PAPER_I_CANCELLATION_RULING_035
Reviewed commit: 67f3523c33d21468ad962a7fe19cd806ad76e53b

Additive. No file written under rulings 029-034 is edited and every earlier
token stands.

## 1. The 10x-to-57x gap was not pure cancellation

The 034 report divided a per-node aggregate by the largest measured channel
error and called the ratio conservatism from cancellation. It is not one
effect. Writing K = W O and delta_c for one channel's node discrepancies,

    E_c = ||K delta_c||        the actual signed detector residual
    A_c = ||K |delta_c| ||     cancellation removed inside each pixel only
    T_c = sum_p ||K[:,p]|| |delta_pc|    detector structure replaced by a sum
    U   = sum_p ||K[:,p]|| max_c |delta_pc|   the 034 aggregate

with E <= A <= T <= U. The 034 figure was U against max_c E_c, so it mixed
three separate reductions: channel aggregation (U over T), loss of the
detector vector structure (T over A), and sign cancellation (A over E). The
reviewer's counterexample settles the point: 324 positive contributions in 324
distinct pixels give T/E = 18 with A/E = 1 and no cancellation anywhere.

S1 measures all four quantities per channel, each against its own reference
norm. The 034 scenario used the largest reference norm across channels, which
is not the same as meeting every channel's relative requirement.

## 2. A tighter bound cannot reduce a measured discrepancy

The measured signed residuals -- 9.594e-03, 4.274e-02 and 5.116e-01 relative,
at orders 0, 1 and 2, against a 5e-4 budget -- already contain whatever
cancellation the comparison has. Removing conservatism from a bound changes
where refinement is spent. It does not make the unchanged approximation more
accurate, and nothing in this stage is allowed to present it as if it did.

## 3. The 308,656 figure

It is an ORACLE_ZERO_HEAD_CACHED_DEFECT scenario: it assumes refining a
selected node drives its discrepancy to exactly zero while every other
contribution and weight stays put. Four child evaluations establish no such
thing. It is not a sufficient physical sampling budget and is relabelled
accordingly.

Greedy refinement also has a trap the 034 report did not state: contributions
of 1 and -0.99 sum to 0.01, and perfectly correcting the first leaves -0.99.
A local improvement can raise a signed global residual by breaking
cancellation.

## 4. Two scope corrections

**The same-leg flag.** "No order-2 stencil passes" means none passed a
declared heuristic -- source radius spanning under a quarter of its own mean
across the coarse cell. That is a smoothness proxy, not a geodesic branch
test, and large variation can coexist with exact interpolation of a simple
field. The span statistics stand; physical branch membership stays unverified
where the archived metadata does not establish it.

**The zero screen residual.** It is an equal-input consistency control, not an
absolute geometry validation. Both sides receive identical screen fields
through the same overlap operator, so a shared geometry error would cancel
there too. It does not reopen the separately accepted geometry tests; it just
does not stand in for them.

## 5. The export defect

The 034 response writer saved only the reference vectors. The estimated
vectors and the signed residuals were popped and discarded. The archive keys
are inspected in the manifest beside this file, and the missing arrays are
regenerated from cached inputs into a new directory. No physical evaluation is
repeated; the old directory is left byte-identical.

## 6. What the missing support still is

The order-2 comparison covers 62.8% of the fine-centre-labelled emitting area,
leaving about 0.6092 M^2 with no response bound of any kind. No cancellation
argument on the compared subset says anything about that region.
