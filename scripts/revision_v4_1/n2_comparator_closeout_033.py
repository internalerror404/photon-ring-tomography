#!/usr/bin/env python3
"""N2 of ruling 033: the capped comparator closeout. The only physical stage.

Phase A re-reads the 66 records ruling 031 left unresolved and keeps what I1
threw away -- the reference's own failure reason, its integral values, its
error estimates and the decision margins. Phase B, gated on Phase A, runs a
confirmation panel whose IDs were frozen before any of this ran.

Charging follows convention B, settled by ruling 033. One native tracer
evaluation is one unit even on a known coordinate. Each independent end-to-end
reference evaluation is its own unit. The primary path integration rides
inside the native bundle and is recorded as a component, not charged again.
Three units per point: native, reference A, reference B.

Nothing here decides an ambiguous case. A point inside the decision margin
comes back unresolved with its margin attached, whichever way the archived
mask happens to point.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts" / "revision_v4_1"))
from phrt.geometry.raymap import horizon_radius, read            # noqa: E402
from phrt.revision_v4_1 import pathdomain as PD                  # noqa: E402
from phrt.revision_v4_1 import pathdomain2 as P2                 # noqa: E402
from phrt.revision_v4_1 import pathdomain3 as P3                 # noqa: E402
from phrt.revision_v4_1 import query as Q                        # noqa: E402
from phrt.revision_v4_1 import rootcheck as RC                   # noqa: E402
from t1_first_invalid_primitive import instrument                # noqa: E402

MAPS = ROOT / "artifacts" / "raymaps"
GEOMETRY, SPIN, INC, D_OBS, R_OUTER = "a050_i050", 0.5, 50.0, 1000.0, 50.0


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _clean(d: dict) -> dict:
    """JSON-safe copy of one adjudication, with nothing dropped."""
    out = {}
    for k, v in d.items():
        if isinstance(v, (np.floating, np.integer)):
            out[k] = v.item()
        elif isinstance(v, np.ndarray):
            out[k] = v.tolist()
        elif isinstance(v, dict):
            out[k] = _clean(v)
        else:
            out[k] = v
    return out


def run_phase(name: str, ids: list[dict], guard: Q.Guard, rh: float,
              out: Path) -> dict:
    rows: list[dict] = []
    payload: dict[str, np.ndarray] = {}
    orders = sorted({int(x["order"]) for x in ids})
    for n in orders:
        sel = [x for x in ids if int(x["order"]) == n]
        idx = np.array([int(x["index"]) for x in sel])
        rm = read(MAPS / f"{GEOMETRY}_n{n}_{sel[0]['profile']}.h5")
        a, b = rm.alpha[idx], rm.beta[idx]

        tok = guard.reserve(Q.TRANSFER, idx.size, f"{name}_native_n{n}")
        try:
            rec = instrument(a, b, n)
        except BaseException as exc:                              # noqa: BLE001
            guard.abort(tok, f"{type(exc).__name__}: {exc}")
            raise
        nan = np.asarray(rec["output_is_nan"], bool)
        guard.complete(tok, int(idx.size - nan.sum()), int(nan.sum()))

        roots = np.asarray(rec["roots"])
        gth = np.asarray(rec["G_theta"], float)
        lam, eta = np.asarray(rec["lam_eta"], float)

        # the primary rides inside the native bundle: a component, not a charge
        primary = [P2.adjudicate(roots[:, j], float(gth[j]), rh, D_OBS,
                                 R_OUTER) for j in range(idx.size)]

        tok = guard.reserve(Q.TRANSFER, idx.size, f"{name}_referenceA_n{n}")
        try:
            refA = [P2.adjudicate(roots[:, j], float(gth[j]), rh, D_OBS,
                                  R_OUTER, reference=True)
                    for j in range(idx.size)]
        except BaseException as exc:                              # noqa: BLE001
            guard.abort(tok, f"{type(exc).__name__}: {exc}")
            raise
        guard.complete(tok, idx.size, 0)

        tok = guard.reserve(Q.TRANSFER, idx.size, f"{name}_referenceB_n{n}")
        try:
            refB = [P3.adjudicate(roots[:, j], float(gth[j]), rh, D_OBS,
                                  R_OUTER, lam=float(lam[j]),
                                  eta=float(eta[j]), spin=SPIN)
                    for j in range(idx.size)]
        except BaseException as exc:                              # noqa: BLE001
            guard.abort(tok, f"{type(exc).__name__}: {exc}")
            raise
        guard.complete(tok, idx.size, 0)

        for j, s in enumerate(sel):
            k = RC.turning_index(roots[:, j], rh, D_OBS)
            sep = None
            if k is not None:
                sep = float(np.min(np.abs(
                    np.delete(roots[:, j], k) - roots[k, j])))
            rows.append({
                "phase": name, "profile": s["profile"], "order": n,
                "index": int(idx[j]), "stratum": s.get("stratum")
                or s.get("strata"),
                "alpha": float(a[j]), "beta": float(b[j]),
                "lam": float(lam[j]), "eta": float(eta[j]),
                "G_theta": float(gth[j]),
                "library_emitted_nan": bool(nan[j]),
                "archived_source_r": float(rm.source_r[idx[j]])
                if np.isfinite(rm.source_r[idx[j]]) else None,
                "turn_separation": sep,
                "primary": _clean(primary[j]),
                "reference_A": _clean(refA[j]),
                "reference_B": _clean(refB[j]),
                "prior_primary": s.get("prior_primary"),
                "prior_reference": s.get("prior_reference"),
            })
        payload[f"n{n}_alpha"] = a
        payload[f"n{n}_beta"] = b
        payload[f"n{n}_index"] = idx
        payload[f"n{n}_roots_real"] = roots.real
        payload[f"n{n}_roots_imag"] = roots.imag
        payload[f"n{n}_G_theta"] = gth
        payload[f"n{n}_lam"] = lam
        payload[f"n{n}_eta"] = eta
        payload[f"n{n}_nan"] = nan
        print(f"  {name} n{n}: {idx.size} ids, charged {3 * idx.size}, "
              f"remaining {guard.remaining(Q.TRANSFER)}", flush=True)

    # payload and hash BEFORE any summary, so an abort leaves values behind
    blob = out / f"CHUNK_{name}_033.npz"
    np.savez_compressed(blob, **payload)
    rowsf = out / f"CHUNK_{name}_rows_033.json"
    rowsf.write_text(json.dumps(rows, indent=1) + "\n")
    (out / f"CHUNK_{name}_033.sha256").write_text(
        f"{sha(blob)}  {blob.name}\n{sha(rowsf)}  {rowsf.name}\n")
    return {"rows": rows, "payload": blob.name, "rows_file": rowsf.name,
            "payload_sha256": sha(blob), "rows_sha256": sha(rowsf)}


def tally(rows: list[dict]) -> dict:
    def codes(key):
        c: dict[str, int] = {}
        for r in rows:
            c[r[key]["code"]] = c.get(r[key]["code"], 0) + 1
        return c

    reasons: dict[str, int] = {}
    for r in rows:
        if r["reference_A"]["code"] == PD.UNRESOLVED:
            w = r["reference_A"].get("why", "(none recorded)")
            reasons[w] = reasons.get(w, 0) + 1
    agreeAB = sum(r["primary"]["code"] == r["reference_B"]["code"]
                  for r in rows)
    return {
        "n": len(rows),
        "primary_codes": codes("primary"),
        "reference_A_codes": codes("reference_A"),
        "reference_B_codes": codes("reference_B"),
        "reference_A_failure_reasons": reasons,
        "reference_B_unresolved": sum(
            r["reference_B"]["code"] == PD.UNRESOLVED for r in rows),
        "primary_agrees_with_reference_B": int(agreeAB),
        "primary_agrees_with_reference_A": int(sum(
            r["primary"]["code"] == r["reference_A"]["code"] for r in rows)),
        "valid_where_the_library_marked_nan": int(sum(
            r["library_emitted_nan"] and r["reference_B"]["code"] == PD.VALID
            for r in rows)),
        "absent_where_the_library_gave_a_value": int(sum(
            (not r["library_emitted_nan"])
            and r["reference_B"]["code"] in (PD.NO_CROSSING_ESCAPE,
                                             PD.NO_CROSSING_CAPTURE)
            for r in rows)),
    }


def main(out: Path, freeze: Path) -> int:
    t0 = time.time()
    out.mkdir(parents=True, exist_ok=True)
    fz = json.loads(Path(freeze).read_text())
    guard = Q.Guard(freeze, ledger_path=out / "ATTEMPT_LEDGER_033.json")
    led = fz["ledger"]
    rh = horizon_radius(SPIN)

    dev_ids = fz["development_ids"]
    conf_ids = fz["confirmation_ids"]
    if 3 * len(dev_ids) > led["development_charged_max"]:
        raise SystemExit("the development phase exceeds its own cap")
    if len(conf_ids) > led["confirmation_points_max"]:
        raise SystemExit("the confirmation panel exceeds its point cap")
    if 3 * (len(dev_ids) + len(conf_ids)) > led["diagnostic_total_max"]:
        raise SystemExit("the diagnostic exceeds its total cap")

    dev = run_phase("development", dev_ids, guard, rh, out)
    dev_t = tally(dev["rows"])

    # the registered gate: reference B must resolve every development case and
    # agree with the primary on all of them, and reference A's failures must
    # concentrate in one identified cause
    reasons = dev_t["reference_A_failure_reasons"]
    dominant = max(reasons.values()) / max(len(dev["rows"]), 1) if reasons \
        else 0.0
    gate = {
        "reference_B_resolves_every_development_case":
            dev_t["reference_B_unresolved"] == 0,
        "reference_B_agrees_with_the_primary_on_every_case":
            dev_t["primary_agrees_with_reference_B"] == len(dev["rows"]),
        "reference_A_failures_concentrate_in_one_cause": dominant >= 0.90,
        "dominant_cause_share": dominant,
    }
    gate["continue_to_confirmation"] = all(
        v for k, v in gate.items() if isinstance(v, bool))

    conf: dict | None = None
    conf_t: dict | None = None
    if gate["continue_to_confirmation"]:
        conf = run_phase("confirmation", conf_ids, guard, rh, out)
        conf_t = tally(conf["rows"])
    else:
        print("  development gate not met; stopping before confirmation",
              flush=True)

    rep = {
        "stage": "N2", "ruling": "PAPER_I_FEASIBILITY_AND_CLOSEOUT_RULING_033",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "commit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                 capture_output=True, text=True).stdout.strip(),
        "charging_convention": led["convention"],
        "units_per_point": {"native": 1, "reference_A": 1, "reference_B": 1,
                            "primary_path_integration":
                                "component of the native bundle, not charged"},
        "development": {"ids": len(dev_ids), "tally": dev_t,
                        "payload": dev["payload"],
                        "payload_sha256": dev["payload_sha256"],
                        "rows_file": dev["rows_file"],
                        "rows_sha256": dev["rows_sha256"]},
        "development_gate": gate,
        "confirmation": None if conf is None else {
            "ids": len(conf_ids), "tally": conf_t, "payload": conf["payload"],
            "payload_sha256": conf["payload_sha256"],
            "rows_file": conf["rows_file"],
            "rows_sha256": conf["rows_sha256"]},
        "confirmation_skipped_reason": None if conf is not None else
            "the development gate was not met; the frozen stopping rule stops "
            "here rather than spending the confirmation reserve",
        "forced_labels": 0,
        "ambiguous_cases_resolved_toward_the_archived_mask": 0,
        "comparator_status": None,
        "guard": guard.snapshot(),
        "runtime_seconds": time.time() - t0,
    }
    if conf_t is not None:
        ok = (conf_t["reference_B_unresolved"] == 0
              and conf_t["primary_agrees_with_reference_B"] == conf_t["n"])
        rep["comparator_status"] = (
            "COMPARATOR_NUMERICALLY_VALIDATED_ON_TESTED_COHORTS" if ok
            else "COMPARATOR_UNRESOLVED_ON_THE_CONFIRMATION_PANEL")
    else:
        rep["comparator_status"] = "COMPARATOR_UNRESOLVED_ON_DEVELOPMENT"
    rep["comparator_pass_authorizes_integration"] = False

    (out / "COMPARATOR_CAUSE_AND_CONFIRMATION_033.json").write_text(
        json.dumps(rep, indent=2) + "\n")
    man = {
        "chunks": [f for f in sorted(p.name for p in out.iterdir())
                   if f.startswith("CHUNK_")],
        "written_before_the_summary": True,
        "cache_identity": fz["payload_requirements"]["cache_identity"],
        "hashes": {p.name: sha(p) for p in sorted(out.iterdir())
                   if p.name.startswith("CHUNK_")},
    }
    (out / "COMPARATOR_PAYLOAD_MANIFEST_033.json").write_text(
        json.dumps(man, indent=2) + "\n")
    print(json.dumps({"stage": "N2", "status": rep["comparator_status"],
                      "gate": gate["continue_to_confirmation"],
                      "charged": guard.spent[Q.TRANSFER],
                      "remaining": guard.remaining(Q.TRANSFER),
                      "dev": dev_t["reference_B_unresolved"],
                      "seconds": round(time.time() - t0)}))
    return 0


if __name__ == "__main__":
    a = [(ROOT / x).resolve() for x in sys.argv[1:3]]
    raise SystemExit(main(*a))
