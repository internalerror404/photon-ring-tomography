"""Canonical Parquet result tables.

Rule 14 of the handoff: every figure is generated from these tables.  Nothing
downstream may read a number that was not written here first.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Sequence

import pandas as pd

from phrt.config import repo_root

IDENTIFIABILITY_COLUMNS: Sequence[str] = (
    "run_id", "config_hash", "geometry_id", "spin", "inclination_deg",
    "source_class", "readout", "max_order", "leakage_level", "noise_model",
    "source_dimension", "data_dimension", "numerical_rank", "operational_rank",
    "nullity", "sigma_max", "sigma_min_positive", "restricted_sigma_min",
    "kappa_positive", "stable_rank", "effective_rank", "trace_information",
    "min_gram_eigenvalue", "runtime_seconds", "peak_rss_mb",
)

RECONSTRUCTION_EXTRA_COLUMNS: Sequence[str] = (
    "source_seed", "noise_seed", "method", "hyperparameter_rule", "nrmse",
    "nrmse_by_age_json", "mode_correlation", "spectral_error", "data_residual",
    "visible_component_error", "null_component_error", "coverage_90",
    "prior_data_fraction", "prior_swap_distance", "status",
)


def _check_columns(df: pd.DataFrame, required: Sequence[str], label: str) -> None:
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"{label} table missing required columns: {missing}")


# A CSV twin above this many rows is larger than a remote will accept and
# larger than anyone will grep. The parquet remains authoritative either way.
CSV_TWIN_MAX_ROWS = 250_000


def write_table(rows: Iterable[dict[str, Any]], name: str,
                required: Sequence[str] | None = None,
                out_dir: str | Path | None = None) -> Path:
    df = pd.DataFrame(list(rows))
    if required:
        _check_columns(df, required, name)
    d = Path(out_dir) if out_dir else repo_root() / "artifacts" / "tables"
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"{name}.parquet"
    df.to_parquet(p, index=False)
    # A CSV twin keeps every number greppable without a parquet reader, which
    # is worth having and is not worth 122 MB. One HMT-2 state table reached
    # exactly that -- a 70x blow-up over its 1.7 MB parquet -- and GitHub
    # refuses anything over 100 MB, so the push failed after the science was
    # already committed. Above the cap the parquet stands alone and a stub
    # says where the numbers are, rather than a large file being written and
    # then discovered to be unpushable.
    if len(df) <= CSV_TWIN_MAX_ROWS:
        df.to_csv(d / f"{name}.csv", index=False)
    else:
        (d / f"{name}.csv.skipped").write_text(
            f"{len(df)} rows exceeds the {CSV_TWIN_MAX_ROWS} row cap for the "
            f"CSV twin; read {name}.parquet\n")
    return p


def read_table(name: str, out_dir: str | Path | None = None) -> pd.DataFrame:
    d = Path(out_dir) if out_dir else repo_root() / "artifacts" / "tables"
    return pd.read_parquet(d / f"{name}.parquet")
