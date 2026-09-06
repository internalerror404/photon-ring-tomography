#!/usr/bin/env python3
"""H0 of ruling 027: hull provenance, clipped overlaps, missing support.

Zero transfer-ray calls. Nothing is regenerated: the archived lensing-band
hulls are read, their provenance and topology recorded, the triple
intersection built against them, and every fragment with positive geometric
area classified against the transfer data that exists for it.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

import h5py
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from phrt.geometry.raymap import read, horizon_radius        # noqa: E402
from phrt.revision_v4_1 import fractional as FR              # noqa: E402
from phrt.revision_v4_1 import measure as M                  # noqa: E402
from phrt.revision_v4_1 import polyclip as PC                # noqa: E402
from phrt.revision_v4_1.common_sky import DetectorGrid       # noqa: E402

MAPS = ROOT / "artifacts" / "raymaps"
AART = ROOT / "artifacts" / "e3_pilot" / "aart_out"
GEOMETRY, SPIN, INC = "a050_i050", 0.5, 50.0
ORDERS = (0, 1, 2)
R_OUTER = 50.0
BANDS = {
    "coarse": AART / "coarse" / "LensingBands_a_0.5_i_50.0_dx0_0.8_dx1_0.16_dx2_0.04.h5",
    "core": AART / "core" / "LensingBands_a_0.5_i_50.0_dx0_0.4_dx1_0.08_dx2_0.02.h5",
    "fine": AART / "fine" / "LensingBands_a_0.5_i_50.0_dx0_0.2_dx1_0.04_dx2_0.01.h5",
}
DETECTOR = dict(alpha=(-25.0, 25.0), beta=(-25.0, 25.0), pitch=0.4)


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def hull_record(f, n: int) -> dict:
    hi, he = f[f"hull_{n}i"][:], f[f"hull_{n}e"][:]
    rec = {"order": n,
           "outer_vertices": int(he.shape[0]),
           "inner_vertices": int(hi.shape[0]),
           "outer_signed_area": PC.signed_area(he),
           "inner_signed_area": PC.signed_area(hi),
           "band_area": abs(PC.signed_area(he)) - abs(PC.signed_area(hi)),
           "outer_simple": PC.is_simple(he),
           "inner_simple": PC.is_simple(hi),
           "outer_unique_vertices": int(np.unique(he, axis=0).shape[0]),
           "inner_unique_vertices": int(np.unique(hi, axis=0).shape[0]),
           "inner_strictly_inside_outer": bool(
               PC.grid_coverage(hi, np.array([he[:, 0].min() - 1,
                                              he[:, 0].max() + 1]),
                                np.array([he[:, 1].min() - 1,
                                          he[:, 1].max() + 1])).sum() > 0)}
    # nesting by area arithmetic: |outer| - |outer minus inner| must equal
    # |inner| exactly when the inner hull lies wholly inside the outer one
    X = np.array([min(he[:, 0].min(), hi[:, 0].min()) - 1.0,
                  max(he[:, 0].max(), hi[:, 0].max()) + 1.0])
    Y = np.array([min(he[:, 1].min(), hi[:, 1].min()) - 1.0,
                  max(he[:, 1].max(), hi[:, 1].max()) + 1.0])
    band = float(PC.band_coverage(he, hi, X, Y).sum())
    rec["nesting_consistent"] = bool(
        abs(band - rec["band_area"]) < 1e-9 * max(1.0, rec["band_area"]))
    rec["band_area_by_clipping"] = band
    return rec


def main(out_dir: Path) -> int:
    t0 = time.time()
    out_dir.mkdir(parents=True, exist_ok=False)
    rh = horizon_radius(SPIN)
    grid = DetectorGrid(*DETECTOR["alpha"], *DETECTOR["beta"],
                        DETECTOR["pitch"])

    manifest = {
        "stage": "H0", "ruling": "PAPER_I_FRACTIONAL_COVERAGE_RULING_027",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "commit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                 capture_output=True, text=True).stdout.strip(),
        "transfer_ray_calls": 0, "boundary_point_solves": 0,
        "hulls_regenerated": False,
        "hull_source": "archived AART lensing-band files, read not rebuilt",
        "pinned_convention": {
            "band": "interior(hull_ne) minus interior(hull_ni), matching "
                    "lensingbands.grid_mask's indexes = in_hull(grid, "
                    "hull2) & ~in_hull(grid, hull)",
            "order_0_outer": "the four-corner screen square at +/-limits",
            "order_0_inner": "the apparent horizon curve, not the critical "
                             "curve",
            "orders_1_2": "radial scalings of the 120 critical-curve "
                          "directions, each a root of nlayers at that "
                          "direction",
            "directions": "npointsS arclength marks on the upper critical "
                          "curve, mirrored to 2*npointsS directions",
        },
        "validity_predicate": {
            "source": "src/phrt/geometry/raymap.py::validity",
            "clauses": ["band membership", "finite source_r, source_phi, "
                        "coordinate_time", f"source_r > r_+ = {rh}",
                        f"source_r <= {R_OUTER}"],
            "hull_alone_is_the_predicate": False,
        },
        "files": {}, "per_profile": {},
    }

    support_out = {"stage": "H0", "categories": {
        FR.SUPPORTED: "the cell centre is a valid ray; its transfer values "
                      "apply to the fragment",
        FR.OUTSIDE_ANNULUS: "the centre lands outside the declared emission "
                            "annulus. Zero by the emission model, but the "
                            "annulus boundary cuts cells and that cut is not "
                            "resolved here",
        FR.SOLVER_UNRESOLVED: "the centre is in the band and the solver "
                              "returned a non-finite landing. Unresolved, "
                              "not zero emission",
        FR.NO_BAND_DATA: "the fragment is in the band but its cell centre is "
                         "not, so no transfer values were ever computed for "
                         "it",
    }, "per_profile": {}}

    clip_tests = {"stage": "H0", "suite": "tests/revision_v4_1/test_polyclip.py",
                  "plus": "tests/revision_v4_1/test_fractional_027.py"}

    for prof, bpath in BANDS.items():
        if not bpath.exists():
            raise SystemExit(f"archived lensing bands absent: {bpath}")
        manifest["files"][str(bpath.relative_to(ROOT))] = sha(bpath)
        with h5py.File(bpath, "r") as f:
            hulls = {n: (f[f"hull_{n}e"][:], f[f"hull_{n}i"][:])
                     for n in ORDERS}
            recs = [hull_record(f, n) for n in ORDERS]
            marks = int(f["alpha"].shape[0])
        manifest["per_profile"][prof] = {
            "npointsS_marks": marks,
            "directions": 2 * marks,
            "hulls": recs}
        rows = []
        for n in ORDERS:
            mp = MAPS / f"{GEOMETRY}_n{n}_{prof}.h5"
            manifest["files"][str(mp.relative_to(ROOT))] = sha(mp)
            rm = read(mp)
            cells = M.build_ray_cells(rm.alpha, rm.beta, M.NODAL_DUAL_CLIPPED)
            he, hi = hulls[n]
            ov = FR.triple_overlap(cells, grid, he, hi)
            with h5py.File(bpath, "r") as f:
                band_mask = f[f"mask{n}"][:]
            finite = (np.isfinite(rm.source_r) & np.isfinite(rm.source_phi)
                      & np.isfinite(rm.coordinate_time))
            label, tally = FR.classify_support(
                ov.active_area, band_mask, rm.valid, rm.source_r, finite,
                rh, R_OUTER)
            legacy = float(cells.area[rm.valid].sum())
            rows.append({
                "order": n,
                "legacy_binary_valid_area": legacy,
                "fractional_active_area": tally["total_active_area"],
                "ratio_fractional_over_binary":
                    tally["total_active_area"] / legacy if legacy else None,
                **ov.accounting, **tally})
        support_out["per_profile"][prof] = rows

    (out_dir / "HULL_SOURCE_AND_VALIDITY_MANIFEST_027.json").write_text(
        json.dumps(manifest, indent=2) + "\n")
    (out_dir / "MISSING_TRANSFER_SUPPORT_027.json").write_text(
        json.dumps(support_out, indent=2) + "\n")

    proc = subprocess.run(["python3", "-m", "pytest",
                           "tests/revision_v4_1/test_polyclip.py",
                           "tests/revision_v4_1/test_fractional_027.py",
                           "-q", "--no-header"], cwd=ROOT,
                          capture_output=True, text=True)
    tail = [l for l in proc.stdout.strip().splitlines()
            if "passed" in l or "failed" in l or "error" in l]
    clip_tests.update({"returncode": proc.returncode,
                       "passed": proc.returncode == 0,
                       "summary": tail[-1] if tail else proc.stdout[-200:]})
    (out_dir / "FRACTIONAL_CLIPPING_TESTS_027.json").write_text(
        json.dumps(clip_tests, indent=2) + "\n")

    for prof, rows in support_out["per_profile"].items():
        for r in rows:
            b = r["by_category"]
            print(f"{prof:<7} n{r['order']}  binary {r['legacy_binary_valid_area']:>10.4f}"
                  f"  fractional {r['fractional_active_area']:>10.4f}"
                  f"  x{r['ratio_fractional_over_binary']:.4f}"
                  f"  frags {r['active_fragments']:>6d}"
                  f" (part {r['partially_covered_fragments']:>5d})")
            print(f"{'':>12}support: "
                  + "  ".join(f"{k.split('_')[0].lower()}"
                              f"={v['area_fraction']:.4f}"
                              for k, v in b.items()))
    print(f"tests: {clip_tests['summary']}")
    print(f"runtime {time.time() - t0:.0f}s")
    return 0 if proc.returncode == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main((ROOT / sys.argv[1]).resolve()))
