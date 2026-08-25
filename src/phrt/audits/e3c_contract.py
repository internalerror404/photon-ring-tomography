"""The E3C v2 return contract.

PAPER_I_V2_PRE_E3C_AMENDMENT_001 pins what an E3C evaluation may and may not
return. Four of its clauses are enforced here rather than left to the discipline
of whoever edits a table builder later.

Item 3 -- notation
    The physical operator is ``mathcal A``: a continuum map from a source
    function to whitened observations, with no matrix representation of its
    own. What every spectrum in E3C actually describes is

        A_C = mathcal A Q_C

    the restricted coefficient matrix, where ``Q_C`` synthesises a source
    function from a coefficient vector of the declared class C. Every spectral
    field therefore carries the class it belongs to. A statement about
    ``mathcal A`` does not follow from a spectrum of ``A_C``.

Item 5 -- exact rank
    For a float64 physical operator, ``exact_rank`` is ``NOT_APPLICABLE``. The
    transfer coefficients are finite-precision, so a computed spectrum supports
    a decision at a stated tolerance and nothing stronger. Only a structural
    certificate -- an exactly constructed null vector, or a dimension count
    forced by the class and the row structure -- can license an exact claim,
    and none is available for these operators. ``numerical_rank`` is retained
    under a name that says what it is.

Item 6 -- reserved names
    ``D_hist`` and ``d_eff`` belong to E3D. ``effective_rank`` is the
    spectral-entropy effective dimension, i.e. ``d_eff`` under another name, and
    is stripped from every E3C return. ``check_no_reserved_fields`` fails a run
    that reintroduces either.

Item 8 -- dispositions
    A cell is ``SUPPORTED`` or carries a disposition naming why it is not, and
    it counts toward its denominator either way.
"""
from __future__ import annotations

from typing import Any, Iterable

RESERVED_FOR_E3D = ("D_hist", "d_eff", "effective_rank")

DISPOSITIONS = ("SUPPORTED", "UNDEFINED_NO_COMMON_MATCHED_SUPPORT",
                "NOT_APPLICABLE", "NOT_RUN")

EXACT_RANK_VALUE = "NOT_APPLICABLE"
EXACT_RANK_REASON = ("float64 physical operator with no structural certificate; "
                     "the spectrum is computed from finite-precision transfer "
                     "coefficients, so rank is a decision at a stated tolerance "
                     "and not an algebraic fact")

# The spectral fields E3C is allowed to return, and what each one is a property
# of. Every one describes A_C = mathcal A Q_C, never mathcal A.
SPECTRAL_FIELDS = (
    "numerical_rank", "operational_rank", "nullity", "operational_nullity",
    "sigma_max", "sigma_min_positive", "kappa_positive", "stable_rank",
    "trace_information",
)
# Rank under a sweep of relative cut-offs travels with every spectrum, prefixed
# ``rank_rel_``. It is the instrumentation behind ``exact_rank = NOT_APPLICABLE``.


def restrict_spectrum(summary: dict[str, Any], source_class: str) -> dict[str, Any]:
    """Take a raw Spectrum summary to an E3C v2 spectral record.

    Drops the reserved effective dimension, attaches the exact-rank disposition,
    and names the class every field belongs to.
    """
    out = {k: summary[k] for k in SPECTRAL_FIELDS if k in summary}
    # Rank under a sweep of relative cut-offs. Item 5 says exact rank is not
    # available; these columns are the evidence for that rather than a footnote
    # to it, because they show how far the answer moves with the tolerance.
    out.update({k: v for k, v in summary.items() if k.startswith("rank_rel_")})
    if "primary_threshold" in summary:
        out["numerical_rank_threshold"] = summary["primary_threshold"]
    out["exact_rank"] = EXACT_RANK_VALUE
    out["exact_rank_reason"] = EXACT_RANK_REASON
    out["structural_certificate"] = None
    out["source_class"] = source_class
    out["operator_notation"] = "A_C = mathcal A Q_C"
    out["spectrum_describes"] = ("the restricted coefficient matrix A_C, not the "
                                 "continuum operator mathcal A")
    return out


def check_no_reserved_fields(columns: Iterable[str], where: str) -> None:
    """Fail the run if a name reserved for E3D appears in an E3C return."""
    bad = sorted(set(columns) & set(RESERVED_FOR_E3D))
    if bad:
        raise ValueError(
            f"{where}: {bad} are reserved for E3D by "
            f"PAPER_I_V2_PRE_E3C_AMENDMENT_001 item 6 and must not appear in an "
            "E3C return")


def check_disposition(value: str, where: str) -> str:
    if value not in DISPOSITIONS:
        raise ValueError(f"{where}: disposition {value!r} is not one of "
                         f"{DISPOSITIONS}")
    return value


def detectability(ages, detectable, a_anchor: float) -> dict[str, Any]:
    """The full depth contract of item 4, under AGE_INTERVAL_SEMANTICS_AMENDMENT_003.

    Three different observables, which the pre-amendment contract collapsed into
    two and named ambiguously:

    ``oldest_detectable_age_probe``
        the reach. A supremum over a possibly non-contiguous set, so on its own
        it can describe a detectable island sitting beyond an undetectable gap.

    ``longest_detectable_run_span_M`` (with ``_start_M`` and ``_end_M``)
        the longest run of consecutive detectable ages anywhere on the grid.
        This is the quantity previously called
        ``largest_contiguous_detectable_depth``; the name is changed because a
        span length is not a depth from the present, and at high inclination the
        longest run can sit entirely in the past.

    ``contiguous_detectable_span_from_anchor_M`` (with ``_end_from_anchor_M``)
        the stretch that actually connects to ``a_anchor``. Only this one may be
        described as continuous history from the anchor.

    ``a_anchor`` is required rather than defaulted: defaulting it to zero is
    exactly the silent assumption the amendment exists to remove.
    """
    from phrt.metrics.age_intervals import interval_statistics

    import numpy as np

    ages = np.asarray(ages, dtype=float)
    ok = np.asarray(detectable, dtype=bool)
    st = interval_statistics(ages, ok, a_anchor)
    idx = np.flatnonzero(ok)
    return {"oldest_detectable_age_probe": st["oldest_detectable_age_probe"],
            "shallowest_detectable_age": float(ages[idx[0]]) if idx.size else -1.0,
            "n_detectable_ages": int(ok.sum()),
            "n_detectable_runs": st["n_detectable_runs"],
            "a_anchor_M": st["a_anchor_M"],
            "longest_detectable_run_span_M": st["longest_detectable_run_span_M"],
            "longest_detectable_run_start_M": st["longest_detectable_run_start_M"],
            "longest_detectable_run_end_M": st["longest_detectable_run_end_M"],
            "contiguous_detectable_end_from_anchor_M":
                st["contiguous_detectable_end_from_anchor_M"],
            "contiguous_detectable_span_from_anchor_M":
                st["contiguous_detectable_span_from_anchor_M"],
            "anchor_is_detectable": st["anchor_is_detectable"],
            "detectable_set_is_contiguous": st["is_contiguous"],
            "age_threshold_mask": st["age_mask"]}
