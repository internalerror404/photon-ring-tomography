"""Claim-to-artifact ledger: no number reaches the manuscript unrecorded.

Every quantity the manuscript states is registered here together with a
machine-executable description of where it came from. Two properties follow,
and both are checked by ``scripts/verify_manuscript.py`` rather than trusted:

* **Every number is re-derivable.** The ledger stores the artifact path, the
  row filter, the column and the aggregation, so the verifier can recompute the
  value from the frozen bytes without running the builder.
* **No superseded artifact can be cited.** A lookup against a path outside the
  canonical freeze raises at build time, so a pre-G10q table cannot reach a
  table in the paper by accident.

The rendered string is stored alongside the raw value, because the failure mode
that matters is not usually a wrong lookup -- it is a correct lookup formatted
into prose that says something else.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

AGGREGATIONS = ("first", "median", "mean", "min", "max", "sum", "count",
                "nunique", "all", "any")


def _jsonable(v: Any) -> Any:
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.floating,)):
        return float(v)
    if isinstance(v, (np.bool_,)):
        return bool(v)
    return v


@dataclass
class ClaimLedger:
    """Registry of every manuscript number and where it came from."""

    root: Path
    freeze: dict                       # canonical artifact path -> sha256
    claims: list[dict] = field(default_factory=list)
    _seen: set[str] = field(default_factory=set)
    _frames: dict[str, pd.DataFrame] = field(default_factory=dict)

    # -- inputs ------------------------------------------------------------
    def _check_canonical(self, path: str) -> str:
        if path not in self.freeze:
            raise KeyError(
                f"{path} is not in the canonical artifact freeze. Either it is "
                "superseded, or the freeze needs rebuilding; the manuscript may "
                "not cite it either way.")
        return self.freeze[path]

    def frame(self, path: str) -> pd.DataFrame:
        self._check_canonical(path)
        if path not in self._frames:
            self._frames[path] = pd.read_parquet(self.root / path)
        return self._frames[path]

    # -- claims ------------------------------------------------------------
    def _register(self, cid: str, value: Any, rendered: str, source: dict,
                  prose: str | None) -> str:
        if cid in self._seen:
            raise ValueError(f"duplicate claim id {cid!r}")
        self._seen.add(cid)
        self.claims.append({"id": cid, "value": _jsonable(value),
                            "rendered": rendered, "source": source,
                            "prose": prose})
        return rendered

    def table(self, cid: str, path: str, column: str, *, agg: str = "first",
              fmt: str = "{:.3f}", prose: str | None = None,
              where: dict | None = None) -> str:
        """A number read out of a canonical parquet table."""
        if agg not in AGGREGATIONS:
            raise ValueError(f"unknown aggregation {agg!r}")
        df = self.frame(path)
        where = where or {}
        for k, v in where.items():
            df = df[df[k] == v]
        if df.empty:
            raise LookupError(f"{cid}: no rows in {path} matching {where}")
        s = df[column]
        value = s.iloc[0] if agg == "first" else getattr(s, agg)()
        return self._register(
            cid, value, fmt.format(value),
            {"kind": "parquet", "path": path, "sha256": self.freeze[path],
             "where": {k: _jsonable(v) for k, v in where.items()},
             "column": column, "aggregation": agg, "format": fmt}, prose)

    def count(self, cid: str, path: str, *, fmt: str = "{:d}",
              prose: str | None = None, where: dict | None = None) -> str:
        """How many rows of a canonical table satisfy a condition."""
        df = self.frame(path)
        where = where or {}
        for k, v in where.items():
            df = df[df[k] == v]
        return self._register(
            cid, int(len(df)), fmt.format(len(df)),
            {"kind": "parquet_count", "path": path, "sha256": self.freeze[path],
             "where": {k: _jsonable(v) for k, v in where.items()},
             "format": fmt}, prose)

    def json(self, cid: str, path: str, pointer: str, *, fmt: str = "{}",
             prose: str | None = None) -> str:
        """A value read out of a canonical JSON artifact by slash pointer."""
        self._check_canonical(path)
        doc = json.loads((self.root / path).read_text())
        cur: Any = doc
        for part in [p for p in pointer.split("/") if p]:
            cur = cur[int(part)] if isinstance(cur, list) else cur[part]
        return self._register(
            cid, cur, fmt.format(cur),
            {"kind": "json", "path": path, "sha256": self.freeze[path],
             "pointer": pointer, "format": fmt}, prose)

    def derived(self, cid: str, value: Any, rendered: str, *, inputs: list[str],
                expression: str, prose: str | None = None) -> str:
        """A quantity computed from other claims, named by their ids.

        Kept separate from a table lookup so the verifier can tell the two apart:
        a derived claim is re-evaluated from its named inputs, and a claim whose
        inputs are not themselves registered is rejected.
        """
        missing = [i for i in inputs if i not in self._seen]
        if missing:
            raise ValueError(f"{cid}: derived from unregistered claims {missing}")
        return self._register(
            cid, value, rendered,
            {"kind": "derived", "inputs": inputs, "expression": expression}, prose)

    def literal(self, cid: str, value: Any, rendered: str, *, source: str,
                prose: str | None = None) -> str:
        """A structural fact -- a protocol constant, a registered convention.

        Not a measurement, so there is nothing to recompute; the ledger records
        where the reader can check it.
        """
        return self._register(cid, value, rendered,
                              {"kind": "literal", "source": source}, prose)

    # -- output ------------------------------------------------------------
    def to_dict(self, extra: dict | None = None) -> dict:
        kinds: dict[str, int] = {}
        for c in self.claims:
            kinds[c["source"]["kind"]] = kinds.get(c["source"]["kind"], 0) + 1
        paths = sorted({c["source"]["path"] for c in self.claims
                        if "path" in c["source"]})
        return {"schema": "phrt-claim-ledger/1",
                "n_claims": len(self.claims),
                "claims_by_kind": kinds,
                "artifacts_cited": paths,
                **(extra or {}),
                "claims": self.claims}
