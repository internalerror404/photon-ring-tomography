"""A firewall between a failed run and its endpoint.

Item 11 of REVIEWER_RULING_HMT1_MAIN_017.

When a sealed run fails a gate its science reading is withheld, and withheld
has to mean *unseen*. The first attempt at this withheld a list of table names,
which is the wrong unit: ``hmt1_main_noiseless_control`` was classified as a
control table and written, and it carried ``median_noisy`` and
``median_noiseless`` -- per-arm medians of the old-band feature error for the
direct and resolved arms. That is the endpoint, under a filename that did not
look like it.

So the firewall works on **lineage, not filenames**. A column is blocked
because of what it is derived from, whatever table it appears in and whatever
that table is called. Adding a new table cannot open a new hole, and renaming
one cannot close it.

The list is deliberately over-broad. A blocked diagnostic costs a rerun after a
repair; a leaked endpoint costs the bank, because a held-out result nobody has
seen is the only thing a sealed rerun can still be.
"""
from __future__ import annotations

from typing import Iterable

# Whole names that are endpoint-derived wherever they appear.
ENDPOINT_NAMES = frozenset({
    "median", "cell_mean", "mean_direct", "mean_arm",
    "median_noisy", "median_noiseless",
    "selection_error", "t_birth_error", "tau_decay_error",
    "n_families_improved", "n_truths", "n_cells",
})

# Substrings that make a column endpoint-derived. Matched case-insensitively
# against the whole column name.
ENDPOINT_PATTERNS = (
    "feature_error",        # old_band_feature_error and every relative of it
    "_error_old",           # radial_error_old, angular_error_old_rad
    "materiality",
    "improved",             # improved_<family>
    "stable_features",      # L_stable_features_M
    "pass_to_age",
    "ci_low", "ci_high",
    "relative_reduction",
    "endpoint",             # noiseless_endpoint_is_lower
)


def offending(columns: Iterable[str]) -> list[str]:
    """Which of these column names carry endpoint lineage."""
    out = []
    for c in columns:
        k = str(c).lower()
        if k in ENDPOINT_NAMES or any(p in k for p in ENDPOINT_PATTERNS):
            out.append(str(c))
    return sorted(set(out))


def rows_offending(rows) -> list[str]:
    """Endpoint-derived columns present in a list-of-dicts table."""
    cols: set[str] = set()
    for r in rows or ():
        cols.update(r.keys())
    return offending(cols)


def screen(name: str, rows, withheld: bool) -> tuple[bool, list[str]]:
    """Whether this table may be written, and what blocked it.

    ``withheld`` is the run's own verdict that a gate failed. When it is set,
    any table carrying endpoint lineage is refused outright rather than trimmed:
    silently dropping the offending columns would emit a table that looks
    complete and is not, and the next reader would not know.
    """
    bad = rows_offending(rows)
    if withheld and bad:
        return False, bad
    return True, bad
