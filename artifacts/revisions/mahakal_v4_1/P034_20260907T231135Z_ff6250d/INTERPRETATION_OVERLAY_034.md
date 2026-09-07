# INTERPRETATION_OVERLAY_034

Ruling: PAPER_I_RESPONSE_ERROR_RULING_034
Reviewed commit: d1617963d93713053a4ea374a8c78fcfa013448a

Additive. No file written under rulings 029-033 is edited, the 033 renderer
keeps its bytes, and every earlier token stands.

## 1. Corrections to the 033 report

**The integrals do not all agree at 3e-16.** That sentence was true of the
finite-path values and false as a blanket statement. Recomputed per quantity
from the saved rows: `J_observer` and `J_50` agree between reference A and
reference B to within machine precision, while `s_escape` does not -- in the
first exported development case it differs by 7.27e-08. A third quantity again
is reference A's convergence estimate, ~3.76e-05 there. Finite-path values,
escape values and error estimates are three different things and the readback
now reports them separately.

**The summary numbers were narrative.** The 47/19 endpoint split, the median
endpoint distance and the equality sentence were literals in the renderer
rather than derivations from the payload. They are recomputed here from the
rows, and the report now quotes the recomputation.

**A quadrature error estimate is not the error.** SciPy documents it as an
estimate, and the distance from a decision endpoint is itself computed with
the same quadrature. Neither is ground truth, and neither is presented as
such.

**Root separation stays an association.** The population difference is real
and consistent with harder integration, but it is not a controlled
demonstration that separation is the sole mechanism.

**The indexed reduction was not shown to be necessary here.** It remains a
worthwhile algebraic safeguard. The delivered evidence does not show it was
required to decide these particular cases.

## 2. Corrections to the 033 field-error finding

The 94.7% and 98.1% figures are the fraction of comparable nodes at which

    |z_interpolated - z_fine| / max over comparable nodes |z_fine|

exceeds 5e-4, for a primitive field z. That is a **global-maximum-scaled
primitive bilinear discrepancy**. It is not a pointwise relative error and it
is not the whitened detector-response error the 5e-4 budget is written
against. Using the same number for both does not make them the same quantity.

Two scope limits go on the record with it. The 10,284 comparable order-2 nodes
are 61.68% of the fine map's emitting nodes, not the whole emitting domain.
And the comparison did not isolate smooth interior stencils: bilinear
interpolation there required finite radius and redshift at the corners, not
that every corner belong to the same emitting domain or the same radial leg,
so boundary-crossing and outside-annulus stencils could contribute.

The figures stay as evidence about that bilinear representation on those
comparable stencils. They do not establish that no mesh design can reduce the
cost, and the 033 sentence saying so is withdrawn.

## 3. Corrections to the 033 cost numbers

101,416 expected and 382,580 worst case are **scenarios**. The interior term
is a heuristic extrapolation -- the largest above-threshold node fraction times
the transition-parent count times four -- not a count of unresolved interior
leaves, and the worst case stipulates retries and multipliers rather than
proving a bound. The 4.385x figure is arithmetic between projected work and
the retired layout, not a measured speedup.

The 033 sentence "adaptivity fixes the boundary cost" is also withdrawn as
written: within that same model the boundary term is 52,379 and the interior
term 49,037, so the boundary is the larger half of the projection.

## 4. Correction to the interval error report

The interval propagation itself is accepted. Its scalar helper was wrong:
a box's half-width bounds the error about the box's midpoint and about nothing
else, and reducing a whitened half-width with a matrix one-norm is neither a
per-channel nor a joint Euclidean radius. `leaf2.box_radius_about` now takes an
explicit reference response, returns the per-channel Euclidean radius over the
whitened detector rows as the primary figure, and labels the joint
aggregation separately.

## 5. What stands

The comparator closeout stands at its stated cohort scope, with its bounded
independence. The recorded reason for reference A's refusal was its own
decision margin, not a disagreement about the physical event. The accounting
stands: 18,372 + 774 = 19,146 spent, 854 remaining, none of it spent under
this ruling.
