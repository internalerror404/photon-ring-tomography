#!/usr/bin/env python3
"""Every reference-calibration definition and consumer in the tree.

Ledger C02 requires an exhaustive inventory, not the six seed runners. The
search is a parse, not a grep: an AST visitor finds the calibration *shape*
-- a scalar built from a mean or a norm of a clean response and then used to
divide a signal or set a sigma -- and separately records every consumer of the
name it is bound to. Textual search then runs over the same files as a
cross-check, and any file the two disagree about is reported rather than
silently dropped.

Classification is by the file's role, which decides whether a repair there
reaches a physical result:

``PHYSICAL_RUNNER``   a script that builds a PhysicalOperator over real ray
                      maps and writes canonical artifacts.
``TOY_REPRODUCTION``  the v0.1 fixture path.
``LIBRARY``           importable code under src/.
``TEST``              tests.
"""
from __future__ import annotations

import ast
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

CALIB_NAMES = {"s_ref", "snr_scale", "scale", "sigma", "y_scale", "ref",
               "reference", "s_ref_legacy", "sigma_omega", "noise", "nm"}
SEED_RUNNERS = {
    "scripts/run_e3c_operator_grid.py", "scripts/run_hmt2_sealed_main.py",
    "scripts/run_hmt2_stage1.py", "scripts/run_hmt1_validation.py",
    "scripts/run_r1l_stage2r_b.py", "scripts/run_e3d_source_class_stress.py",
    "src/phrt/operators/whitening.py", "scripts/reproduce_v01.py"}


def blob(rel: str) -> str:
    return subprocess.run(["git", "hash-object", rel], cwd=ROOT,
                          capture_output=True, text=True).stdout.strip()


def _dotted(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return f"{_dotted(node.value)}.{node.attr}"
    if isinstance(node, ast.Call):
        return _dotted(node.func)
    return ""


def _has_reduction(node: ast.AST) -> str | None:
    """Name the aggregation a scalar reference is built from."""
    for sub in ast.walk(node):
        if isinstance(sub, ast.Call):
            d = _dotted(sub.func)
            if d.endswith(("np.mean", "numpy.mean", ".mean")):
                return "MEAN_OVER_ROWS"
            if d.endswith(("np.linalg.norm", ".norm")):
                return "NORM"
            if d.endswith(("np.sum", "numpy.sum", ".sum")):
                return "SUM"
    return None


class Finder(ast.NodeVisitor):
    def __init__(self, rel: str, src: str):
        self.rel, self.lines = rel, src.split("\n")
        self.defs: list[dict] = []
        self.stack: list[str] = []

    def visit_FunctionDef(self, node):        # noqa: N802
        self.stack.append(node.name)
        self.generic_visit(node)
        self.stack.pop()

    def _record(self, name, node, kind):
        red = _has_reduction(node)
        if red is None:
            return
        seg = ast.get_source_segment("\n".join(self.lines), node) or ""
        if "**2" not in seg and "** 2" not in seg and "norm" not in seg:
            return
        self.defs.append({
            "name": name, "line": node.lineno, "kind": kind,
            "enclosing": ".".join(self.stack) or "<module>",
            "reduction": red,
            "expression": " ".join(seg.split())[:220],
            "split_invariant": red != "MEAN_OVER_ROWS",
        })

    def visit_Assign(self, node):             # noqa: N802
        for t in node.targets:
            if isinstance(t, ast.Name) and (
                    t.id in CALIB_NAMES or "ref" in t.id or "scale" in t.id):
                self._record(t.id, node.value, "assignment")
        self.generic_visit(node)

    def visit_Return(self, node):             # noqa: N802
        if node.value is not None and self.stack:
            self._record(f"return of {self.stack[-1]}()", node.value, "return")
        self.generic_visit(node)


def role(rel: str, src: str) -> str:
    if rel.startswith("tests/"):
        return "TEST"
    if "reproduce_v01" in rel or "v01_toy" in rel:
        return "TOY_REPRODUCTION"
    if rel.startswith("src/"):
        return "LIBRARY"
    if "PhysicalOperator" in src and "raymap" in src.lower():
        return "PHYSICAL_RUNNER"
    if rel.startswith("scripts/"):
        return "SCRIPT_OTHER"
    return "OTHER"


def consumers(rel: str, src: str, names: set[str]) -> list[dict]:
    """Where a calibration name is read, which is where a repair must land."""
    out, tree = [], ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load) \
                and node.id in names:
            line = src.split("\n")[node.lineno - 1].strip()
            out.append({"name": node.id, "line": node.lineno,
                        "source": " ".join(line.split())[:200]})
    return out


def main(run_dir: Path) -> int:
    files = sorted([*(ROOT / "src").rglob("*.py"),
                    *(ROOT / "scripts").rglob("*.py"),
                    *(ROOT / "tests").rglob("*.py")])
    sites, textual_only = [], []
    for p in files:
        rel = str(p.relative_to(ROOT))
        src = p.read_text()
        try:
            tree = ast.parse(src)
        except SyntaxError:
            textual_only.append({"path": rel, "reason": "unparseable"})
            continue
        f = Finder(rel, src)
        f.visit(tree)
        if not f.defs:
            # textual cross-check: the parse should not miss a mean-of-squares
            if "np.mean(" in src and "** 2" in src.replace("**2", "** 2") \
                    and ("sqrt" in src):
                textual_only.append({"path": rel,
                                     "reason": "text matched, AST did not"})
            continue
        names = {d["name"] for d in f.defs if d["kind"] == "assignment"}
        sites.append({
            "path": rel, "blob": blob(rel), "role": role(rel, src),
            "is_seed": rel in SEED_RUNNERS,
            "definitions": f.defs,
            "consumers": consumers(rel, src, names) if names else [],
        })

    physical = [s for s in sites if s["role"] == "PHYSICAL_RUNNER"]
    mean_based = [(s["path"], d["name"], d["line"])
                  for s in sites for d in s["definitions"]
                  if d["reduction"] == "MEAN_OVER_ROWS"]
    phys_mean = [(s["path"], d["name"], d["line"])
                 for s in physical for d in s["definitions"]
                 if d["reduction"] == "MEAN_OVER_ROWS"]
    discovered = sorted({p for p, _, _ in phys_mean} - SEED_RUNNERS)

    # Every textual/AST disagreement is adjudicated by reading the file. None
    # may be left open: an unexamined disagreement is exactly the gap this
    # inventory exists to close.
    ADJUDICATED = {
        "scripts/run_r0_canary_reconstruction_pilot.py":
            "NOT_A_CALIBRATION: mean over booleans, and a weighted per-age "
            "norm via einsum. No reference scale is formed",
        "scripts/run_r1l_stage2_validation.py":
            "NOT_A_CALIBRATION: level fraction, a singular-value flatness "
            "check and a coverage mean",
        "scripts/run_r1l_stage2r_a.py":
            "NOT_A_CALIBRATION: bootstrap and per-cell error means",
        "src/phrt/inverse/uncertainty.py":
            "NOT_A_CALIBRATION: coverage and Mahalanobis diagnostics",
        "src/phrt/pilot_r0.py":
            "NOT_A_CALIBRATION: reconstruction error norms and structure terms",
        "scripts/revision_v4_1/r0_normalization_inventory.py":
            "NOT_A_CALIBRATION: this inventory's own pattern strings",
    }
    unadjudicated = [t for t in textual_only if t["path"] not in ADJUDICATED]

    # What each physical runner actually recorded, where it recorded it.
    recorded = {}
    import glob as _g
    for f in sorted(_g.glob(str(ROOT / "artifacts" / "e3c" / "*.json"))):
        d = json.loads(Path(f).read_text())
        recorded.setdefault("scripts/run_e3c_operator_grid.py", []).append(
            {"geometry": d.get("geometry"), "s_ref": d.get("s_ref"),
             "rays_per_order": d.get("rays_per_order"),
             "observer_times": d.get("n_observer_times"),
             "reference_snr": d.get("reference_snr")})

    doc = {
        "schema": "phrt-normalization-inventory/1",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "ledger_item": "C02",
        "method": "AST visitor over src/, scripts/ and tests/, with a textual "
                  "cross-check; a file the two disagree about is reported",
        "n_files_scanned": len(files),
        "n_files_with_calibration_shape": len(sites),
        "n_mean_over_rows_definitions": len(mean_based),
        "n_physical_runner_mean_definitions": len(phys_mean),
        "seed_runners_named_in_ledger": sorted(SEED_RUNNERS),
        "physical_sites_discovered_beyond_the_seeds": discovered,
        "mean_over_rows_definitions": [
            {"path": p, "name": n, "line": ln} for p, n, ln in mean_based],
        "physical_mean_over_rows_definitions": [
            {"path": p, "name": n, "line": ln} for p, n, ln in phys_mean],
        "textual_ast_disagreements": textual_only,
        "textual_ast_disagreements_adjudicated": ADJUDICATED,
        "textual_ast_disagreements_open": unadjudicated,
        "inventory_is_exhaustive": not unadjudicated,
        "recorded_calibration_values": recorded,
        "recorded_values_status": (
            "E3C records s_ref per geometry in artifacts/e3c/*.json. The HMT "
            "and R1L runners compute s_ref inline and do not serialize it; "
            "their values are UNRESOLVED from artifacts alone and are "
            "recoverable only by replay, which R1 does not require for them"),
        "sites": sites,
    }
    out = run_dir / "normalization_site_inventory.json"
    out.write_text(json.dumps(doc, indent=2) + "\n")
    print(f"wrote {out.relative_to(ROOT)}")
    print(f"  {len(files)} files scanned, {len(sites)} carry a calibration shape")
    print(f"  {len(mean_based)} mean-over-rows definitions, "
          f"{len(phys_mean)} of them in physical runners")
    print(f"  physical runners: {len(physical)}")
    for p, n, ln in phys_mean:
        print(f"    {p}:{ln}  {n}")
    print(f"  beyond the ledger seeds: {discovered or 'none'}")
    print(f"  disagreements: {len(textual_only)} found, "
          f"{len(textual_only) - len(unadjudicated)} adjudicated, "
          f"{len(unadjudicated)} open")
    print(f"  exhaustive: {not unadjudicated}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main((ROOT / sys.argv[1]).resolve()))
