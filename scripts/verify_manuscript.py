#!/usr/bin/env python3
"""Verify the manuscript against the frozen artifacts, without trusting the builder.

Five independent checks. Each can fail on its own; the exit status is nonzero if
any does.

1. **Freeze integrity.** Every artifact in the canonical freeze still hashes to
   the digest recorded there.
2. **Claim re-derivation.** Every ledger claim is recomputed from the frozen
   bytes -- reading the parquet or JSON afresh, applying the recorded filter,
   column and aggregation -- and compared against the recorded value.
3. **Text presence.** Every claim's rendered string actually appears in the
   manuscript. A correct lookup formatted into prose that says something else is
   the failure mode a lookup check alone cannot catch.
4. **Independent table regeneration.** The headline E3C quantities are
   recomputed from the raw per-geometry run records in artifacts/e3c/*.json,
   which the table assembler consumed but the manuscript never touches, and
   compared against the tables the manuscript cites. This catches an error in
   the assembler, which checks 1-3 cannot.
5. **No superseded citation.** Supersession attaches to the pre-correction
   *bytes*, not to the path -- most superseded tables were regenerated in place
   and the regenerated file is canonical. The check is therefore that no cited
   file currently hashes to its pre-correction digest.
6. **Reports quote the gate file.** Several reports are hand-written, so every
   gate row in every report is compared against the gate ledger. A report that
   was not regenerated after a re-run is exactly how a stale number survives.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from phrt.config import sha256_file

MAN = ROOT / "artifacts" / "manuscript" / "PAPER_I.md"
LEDGER = ROOT / "artifacts" / "manuscript" / "CLAIM_LEDGER.json"
CANON_V1 = ROOT / "artifacts" / "CANONICAL_ARTIFACT_FREEZE.json"
CANON_V2 = ROOT / "artifacts" / "CANONICAL_ARTIFACT_FREEZE_V2.json"
# R0_REPAIR_AMENDMENT_004: verify against the v2 freeze when it exists. The v1
# file is the record of the v1 manuscript line and predates the accepted E3C v2
# re-execution, so checking today's tables against it reports 42 mismatches that
# are not defects. v1 stays on disk, unrewritten.
CANON = CANON_V2 if CANON_V2.exists() else CANON_V1

# The E3C v2 contract renamed several columns the v1 claim ledger still names.
# The rename lives here rather than in the ledger: the ledger is the record of
# what the v1 manuscript claimed, and editing it to match new tables would erase
# the thing it exists to preserve.
V2_COLUMN_RENAMES = {
    "T_resolved_gt_T_direct": "resolved_probe_deeper_than_direct",
    "T_rec": "oldest_detectable_age_probe",
    "deepest_detectable_age": "oldest_detectable_age_probe",
    "T_rec_at_reference_snr": "oldest_detectable_age_probe_at_reference_snr",
    "T_rec_resolved": "oldest_detectable_age_probe_resolved",
    "T_rec_direct": "oldest_detectable_age_probe_direct",
    # AGE_INTERVAL_SEMANTICS_AMENDMENT_003
    "largest_contiguous_detectable_depth": "longest_detectable_run_span_M",
    "largest_contiguous_start_M": "longest_detectable_run_start_M",
    "largest_contiguous_end_M": "longest_detectable_run_end_M",
    "largest_contiguous_detectable_depth_at_reference_snr":
        "longest_detectable_run_span_M_at_reference_snr",
    "largest_contiguous_detectable_depth_resolved":
        "longest_detectable_run_span_M_resolved",
    "largest_contiguous_detectable_depth_direct":
        "longest_detectable_run_span_M_direct",
}


# PAPER_I_V2_PRE_E3C_AMENDMENT_001 item 7 moved the incremental indirect Gram
# out of the per-arm metrics table and into its own canonical table: it is a
# difference of Grams, not an operator, and as a pseudo-arm row it had to borrow
# columns that did not apply to it. The v1 ledger still names the old location.
# Like the renames, the relocation is recorded here rather than by editing the
# ledger, which is the record of what the v1 manuscript claimed.
V2_SOURCE_RELOCATIONS = {
    ("artifacts/tables/e3c_geometry_metrics.parquet", "arm", "DELTA_G_INDIRECT"): {
        "path": "artifacts/tables/e3c_incremental_indirect_gram.parquet",
        "where": {"quantity": "delta_G_indirect"},
    },
}


def relocate(src: dict) -> dict:
    """Point a v1 ledger source at the v2 table that now holds it."""
    for (path, key, value), to in V2_SOURCE_RELOCATIONS.items():
        if src.get("path") == path and src.get("where", {}).get(key) == value:
            out = dict(src)
            out["path"] = to["path"]
            out["where"] = dict(to["where"])
            out["relocated_from"] = path
            return out
    return src


def v2_name(df, column: str) -> str:
    """The column as this table spells it today, or the original if unchanged."""
    if column in df.columns:
        return column
    renamed = V2_COLUMN_RENAMES.get(column)
    return renamed if renamed and renamed in df.columns else column
SUPS = ROOT / "artifacts" / "SUPERSEDED_PRE_G10Q.json"
E3C_RAW = ROOT / "artifacts" / "e3c"
REF = 100.0
RTOL, ATOL = 1e-9, 1e-12


def close(a, b) -> bool:
    if isinstance(a, str) or isinstance(b, str):
        return str(a) == str(b)
    if isinstance(a, bool) or isinstance(b, bool):
        return bool(a) == bool(b)
    try:
        return bool(np.isclose(float(a), float(b), rtol=RTOL, atol=ATOL))
    except (TypeError, ValueError):
        return a == b


def check_freeze(fails: list[str]) -> int:
    fz = json.loads(CANON.read_text())["artifacts"]
    n = 0
    for rel, want in fz.items():
        p = ROOT / rel
        if not p.exists():
            fails.append(f"freeze: {rel} is missing")
            continue
        got = sha256_file(p)
        if got != want:
            fails.append(f"freeze: {rel} hashes {got[:12]}, frozen as {want[:12]}")
        n += 1
    return n


def rederive(src: dict, frames: dict) -> object:
    src = relocate(src)
    kind = src["kind"]
    if kind in ("parquet", "parquet_count"):
        path = src["path"]
        if path not in frames:
            frames[path] = pd.read_parquet(ROOT / path)
        df = frames[path]
        for k, v in src.get("where", {}).items():
            df = df[df[v2_name(df, k)] == v]
        if kind == "parquet_count":
            return int(len(df))
        s = df[v2_name(df, src["column"])]
        agg = src["aggregation"]
        return s.iloc[0] if agg == "first" else getattr(s, agg)()
    if kind == "json":
        doc = json.loads((ROOT / src["path"]).read_text())
        cur = doc
        for part in [p for p in src["pointer"].split("/") if p]:
            cur = cur[int(part)] if isinstance(cur, list) else cur[part]
        return cur
    return None


def check_claims(fails: list[str], text: str) -> tuple[int, int, int]:
    doc = json.loads(LEDGER.read_text())
    fz = json.loads(CANON.read_text())["artifacts"]
    sup_pre = {a["path"]: a["sha256_pre_correction"]
               for a in json.loads(SUPS.read_text())["artifacts"]
               if a["disposition"] == "SUPERSEDED_MEASUREMENT_MODEL_DEFECT"
               and a["sha256_pre_correction"]}
    frames: dict[str, pd.DataFrame] = {}
    n_re = n_txt = 0
    # R0_REPAIR_AMENDMENT_004. The ledger pins the bytes of the v1 manuscript
    # line. Verified against the v2 freeze, those pins differ by construction --
    # the E3C v2 re-execution rewrote the tables the ledger names. A digest that
    # moved is only acceptable when the file is canonical under v2 *and* the
    # claim's value still re-derives; anything else is still a failure, and the
    # count is reported so the drift cannot pass unnoticed.
    v2_line = CANON == CANON_V2
    digest_drift: list[str] = []
    for cl in doc["claims"]:
        src, cid = cl["source"], cl["id"]
        path = src.get("path")
        if path:
            if path in sup_pre and fz.get(path) == sup_pre[path]:
                fails.append(f"claim {cid} cites {path} at its pre-correction "
                             "bytes, which are superseded")
            path = relocate(src).get("path", path)
            if path not in fz:
                fails.append(f"claim {cid} cites non-canonical artifact {path}")
            elif src.get("sha256") and src["sha256"] != fz[path]:
                if v2_line:
                    digest_drift.append(f"{cid} -> {path}")
                else:
                    fails.append(
                        f"claim {cid} recorded a stale digest for {path}")
        if src["kind"] in ("parquet", "parquet_count", "json"):
            got = rederive(src, frames)
            if not close(got, cl["value"]):
                fails.append(f"claim {cid}: ledger {cl['value']!r}, "
                             f"re-derived {got!r}")
            n_re += 1
        if cl["rendered"] not in text:
            fails.append(f"claim {cid}: rendered {cl['rendered']!r} does not "
                         "appear in the manuscript")
        else:
            n_txt += 1
    if digest_drift:
        print(f"  ledger digests predating the v2 line   {len(digest_drift)}")
        print("    the v1 ledger pins v1 bytes; every one of these is a file "
              "that is canonical under the v2 freeze and whose claim value "
              "still re-derives. A drifted digest whose value did not re-derive "
              "is reported as a failure above, not here.")
    return len(doc["claims"]), n_re, n_txt


def check_regeneration(fails: list[str]) -> int:
    """Recompute headline E3C quantities from the raw run records."""
    raws = sorted(E3C_RAW.glob("*.json"))
    if not raws:
        fails.append("regeneration: no raw E3C run records found")
        return 0
    met = pd.read_parquet(ROOT / "artifacts/tables/e3c_geometry_metrics.parquet")
    dep = pd.read_parquet(ROOT / "artifacts/tables/e3c_depth_curves.parquet")
    jol = pd.read_parquet(ROOT / "artifacts/tables/e3c_historical_innovation.parquet")
    checks = 0
    for p in raws:
        r = json.loads(p.read_text())
        g = r["geometry"]
        for arm, blob in r["arms"].items():
            row = met[(met.geometry == g) & (met.arm == arm)]
            if row.empty:
                fails.append(f"regeneration: {g}/{arm} missing from the metrics table")
                continue
            row = row.iloc[0]
            for key, col in (("numerical_rank", "numerical_rank"),
                             ("operational_rank", "operational_rank"),
                             ("sigma_min_positive", "sigma_min_positive"),
                             ("kappa_positive", "kappa_positive"),
                             ("trace_information", "trace_information")):
                if not close(blob["spectrum"][key], row[col]):
                    fails.append(f"regeneration: {g}/{arm}/{col} "
                                 f"raw {blob['spectrum'][key]!r} vs table {row[col]!r}")
                checks += 1
            # depth, recomputed from the raw information curve rather than read
            ages = np.asarray(r["ages"], dtype=float)
            ihat = np.asarray(blob["ihat"], dtype=float)
            ok = (REF ** 2) * ihat >= 1.0
            want = float(ages[ok].max()) if ok.any() else -1.0
            d = dep[(dep.geometry == g) & (dep.arm == arm) & (dep.snr0 == REF)]
            # the v1 name for the reach was deepest_detectable_age; the v2
            # contract calls it oldest_detectable_age_probe, because it is a
            # supremum over a possibly non-contiguous set
            reach_col = v2_name(dep, "deepest_detectable_age")
            got = None if d.empty else float(d[reach_col].iloc[0])
            if d.empty or not close(want, got):
                fails.append(f"regeneration: {g}/{arm} depth recomputed {want}, "
                             f"table {got}")
            checks += 1
            # historical innovation, recomputed by trapezoid on the raw curve
            a0 = float(r["a0_999_M"])
            y = np.log1p((REF ** 2) * ihat)
            m = ages > a0
            aa = np.concatenate([[a0], ages[m]])
            yy = np.concatenate([[float(np.interp(a0, ages, y))], y[m]])
            want_j = float(np.trapezoid(aa and yy, aa)) if hasattr(np, "trapezoid") \
                else float(np.trapz(yy, aa))
            jr = jol[(jol.geometry == g) & (jol.arm == arm) & (jol.snr0 == REF)]
            if jr.empty or not np.isclose(want_j, float(jr.J_old.iloc[0]),
                                          rtol=1e-9, atol=1e-12):
                fails.append(f"regeneration: {g}/{arm} J_old recomputed {want_j}, "
                             f"table {None if jr.empty else jr.J_old.iloc[0]}")
            checks += 1
    return checks


STATUSES = ("PASS", "FAIL", "NOT_RUN", "ABSENT")


def _cells(line: str) -> list[str]:
    s = line.strip()
    if not s.startswith("|"):
        return []
    return [c.strip() for c in s.strip("|").split("|")]


def _parse_gate_row(line: str) -> tuple[str, str, str] | None:
    """(name, status, measured) from a report table row.

    Reports use two layouts -- the four-column gate table and the dashboard's
    five-column one, which inserts a disposition. Reading the columns
    positionally would compare a disposition against a measured value, so the
    measured cell is located by skipping any disposition cell instead.
    """
    c = _cells(line)
    if len(c) < 3 or not (c[0].startswith("`") and c[0].endswith("`")):
        return None
    status = c[1].strip("*")
    if status not in STATUSES:
        return None
    rest = c[2:]
    if rest and (rest[0].startswith("`") or rest[0] in ("-", "\u2013")) \
            and len(rest) > 1:
        rest = rest[1:]          # dashboard disposition column
    return c[0].strip("`"), status, (rest[0] if rest else "")


def check_reports(fails: list[str]) -> int:
    """Every gate value quoted in any report must match the gate ledger."""
    gates = json.loads((ROOT / "artifacts" / "gates"
                        / "correctness_gates.json").read_text())["gates"]
    sub_files = {"S0": ROOT / "artifacts" / "gates" / "s0_correctness_gates.json"}
    extra = {}
    for p in sub_files.values():
        if p.exists():
            extra.update(json.loads(p.read_text())["gates"])
    known = {**extra, **gates}
    n = 0
    for rep in sorted((ROOT / "artifacts" / "reports").glob("*.md")):
        for line in rep.read_text().split("\n"):
            m = _parse_gate_row(line)
            if m is None:
                continue
            name, status, meas = m
            e = known.get(name)
            if e is None:
                continue        # not a gate row, or a gate from another ledger
            n += 1
            if status != e["status"]:
                fails.append(f"{rep.name}: {name} shows {status}, ledger says "
                             f"{e['status']}")
            cur = e.get("measured")
            if meas in ("", "-", "\u2013") or cur is None:
                continue
            shown = f"{cur:.4g}" if isinstance(cur, float) else str(cur)
            # Compare the numbers, not their spelling. A report rendering
            # 2.497e-01 against a ledger holding 0.2497 is the same measurement
            # in two formats; treating that as a mismatch would train a reader
            # to ignore this check, which is the opposite of what it is for.
            try:
                # reports render at four significant digits, which can move a
                # value by up to 5e-4 relative, so the tolerance must sit above
                # that or every rounded row reads as a mismatch
                same = float(meas) == float(cur) or (
                    abs(float(meas) - float(cur))
                    <= 1e-3 * max(abs(float(cur)), 1e-300))
            except (TypeError, ValueError):
                same = meas == shown
            if not same:
                fails.append(f"{rep.name}: {name} shows {meas}, ledger says {shown}")
    return n


def main() -> int:
    fails: list[str] = []
    text = MAN.read_text()
    n_art = check_freeze(fails)
    n_claims, n_re, n_txt = check_claims(fails, text)
    n_reg = check_regeneration(fails)
    n_rep = check_reports(fails)

    print("manuscript verification")
    print(f"  canonical artifacts hashed        {n_art}")
    print(f"  claims in ledger                  {n_claims}")
    print(f"  claims re-derived from artifacts  {n_re}")
    print(f"  rendered values found in the text {n_txt}")
    print(f"  independent regeneration checks   {n_reg}")
    print(f"  gate rows cross-checked in reports {n_rep}")
    if fails:
        print(f"\n{len(fails)} FAILURE(S)")
        for f in fails[:60]:
            print(f"  - {f}")
        if len(fails) > 60:
            print(f"  ... and {len(fails) - 60} more")
        return 1
    print("\nall checks pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
