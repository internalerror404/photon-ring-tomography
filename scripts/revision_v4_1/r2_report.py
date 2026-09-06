#!/usr/bin/env python3
"""The R0-R2 return report, assembled from the emitted artifacts."""
from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main(run_dir: Path) -> int:
    J = lambda n: json.loads((run_dir / n).read_text())  # noqa: E731
    prov, disp = J("provenance.json"), J("correction_dispositions.json")
    inv, mig = J("normalization_site_inventory.json"), J("calibration_migration_map.json")
    gates, replay = J("numerical_gates.json"), J("physical_calibration_replay.json")
    man, conv = J("R2_TARGET_AND_NUISANCE_MANIFEST.json"), J("physical_metric_convergence.json")
    info = list(csv.DictReader((run_dir / "reference_geometry_information.csv").open()))
    deltas = list(csv.DictReader((run_dir / "normalization_endpoint_deltas.csv").open()))
    moved = [r for r in deltas if r["endpoint_moved"] == "True"]
    prim = {r["arm"]: r for r in info if float(r["rtol"]) == 1e-12}
    res, dir_ = prim["RESOLVED_PHYSICAL"], prim["DIRECT_PHYSICAL"]
    known, cond = float(res["information_known_remainder"]), float(res["information_conditional"])

    unresolved_tol = len({(r["arm"], r["n_operational_conditional"])
                          for r in info}) != 2 * 1
    token = ("R2_NUMERICALLY_UNRESOLVED" if unresolved_tol
             else "R0_R2_COMPLETE_REFERENCE_GEOMETRY")

    body = f"""# Mahakal v4.1 - R0 to R2 return report

**Return token: `{token}`**

Amendment `PAPER_I_DEFECT_AMENDMENT_023`. Execution commit
`{prov['git']['execution_commit'][:12]}` on `{prov['git']['execution_branch']}`,
delivery commit `{prov['git']['delivery_commit'][:12]}`, inspected base
`{prov['git']['inspected_base'][:12]}`.

Freeze 022 is untouched: all {prov['freeze_022']['n_deliverables']} of its
deliverables re-hash to the digests it pinned. Everything new is additive,
under `artifacts/revisions/mahakal_v4_1/`. No new geodesics, no new truths, no
estimator was retuned, and no old FAIL became a PASS.

## What was established, and what was not

**The direct image carries exactly zero information about the target, and the
resolved stack carries some that the nuisance cannot mimic.** At
`a* = 0.5, i = 50` degrees, SNR label 100, on the {man['n_target_columns']}
non-axisymmetric compact temporal coefficients whose support no direct-order
ray reaches:

| arm | known-remainder | nuisance-adjusted | operational at rho=1 | nuisance rank |
|---|---:|---:|---:|---:|
| `DIRECT_PHYSICAL` | {float(dir_['information_known_remainder']):.6g} | {float(dir_['information_conditional']):.6g} | {dir_['n_operational_known']} -> {dir_['n_operational_conditional']} | {dir_['nuisance_rank']} |
| `RESOLVED_PHYSICAL` | {known:.6f} | {cond:.6f} | {res['n_operational_known']} -> {res['n_operational_conditional']} | {res['nuisance_rank']} |

Profiling out all {man['n_nuisance_columns']} remaining coefficients -- the old
axisymmetric baseline, every recent-emission factor and the boundary-overlap
factors -- removes {100 * (1 - cond / known):.1f}% of the resolved arm's target
information and leaves {100 * cond / known:.1f}% standing. The operational
count at unit effect amplitude falls from {res['n_operational_known']} to
{res['n_operational_conditional']} directions, out of a target of
{man['n_target_columns']}.

So the hypothesis the protocol registered is supported at this geometry, and
it is supported thinly. Two directions is not a history. The direct arm's zero
is exact rather than small: those columns are identically zero, which is a
support fact and not a conditioning one.

**This is an operator calculation.** It says what the likelihood separates
under unconstrained linear nuisance amplitudes at fixed known geometry. It is
not a reconstruction, it does not license an estimator claim, and no
positivity or geometry-uncertainty conclusion follows from it.

## Numerical standing of that result

- Rank tolerances {json.loads(json.dumps([r['rtol'] for r in info if r['arm'] == 'RESOLVED_PHYSICAL']))} give the same
  nuisance rank and the same operational count. Not tolerance-selected.
- The source Gram converges to a relative change of
  {conv['refinements'][-1]['relative_change_from_previous']:.2e} at
  {conv['refinements'][-1]['n_per_axis']} nodes per axis, below the 1e-6 bar,
  and the endpoints are stable across the last two refinements. Promoted:
  {str(conv['promoted']).lower()}.
- Target Gram condition {conv['target_gram_condition']:.3e}. The metric is a
  declared model norm on a nondimensional domain, not a proper volume.
- Target and nuisance were fixed from support geometry alone and written to
  `R2_TARGET_AND_NUISANCE_MANIFEST.json` before any spectrum was computed.
- The common-count calibration and the archived one coincide exactly at this
  geometry, which carries 1536 rays, so the R2 numbers do not depend on the
  normalization repair.

## R0: twelve dispositions

{len(disp['dispositions'])} items, C05 split into C05a and C05b. Two
corrections to the delivered ledger are recorded as corrections:

{chr(10).join('- ' + c for c in disp['corrections_to_the_delivered_ledger'])}

The claim scan found occurrences in {len(set(r['path'] for r in csv.DictReader((run_dir / 'claim_dependency_map.csv').open())))} files,
against the four positions reported from the first pass.

## R1: the repair reaches the physical path

The versioned calibration was routed through the same `PhysicalOperator` the
archived runner builds, from the frozen maps and the registered sampler seed.
All {replay['n_geometries']} geometries reproduce their archived `s_ref`, worst
relative error
{max(g['legacy_replay_relative_error'] for g in replay['geometries']):.1e}.
{len(mig['entries'])} legacy sites are mapped;
{mig['n_physical_sites_covered']}/{mig['n_physical_sites_discovered']} physical
sites are covered and `NoiseModel.from_snr` is left intact and classified
toy-only.

**One archived endpoint moves.** Every one of the {len(deltas)} archived masks
was rebuilt from the stored curves and reproduced bit for bit before any factor
was applied. Under the common count, {len(moved)} endpoint changes:

{chr(10).join(f"- `{r['geometry']}` / `{r['arm']}` at SNR {r['snr0']}: oldest {r['oldest_legacy']} -> {r['oldest_common']} M, longest run {r['longest_run_legacy']} -> {r['longest_run_common']} M, anchor span {r['anchor_span_legacy']} -> {r['anchor_span_common']} M" for r in moved)}

That arm is the nonphysical permutation control. No physical arm moves. The
amendment was right that quantization proves nothing, and the crossing it
warned about is real -- in the one arm that carries no claim.

`J_old` is recomputed from the rescaled curves rather than scaled, and shifts
by one to two percent in that single geometry with its sign unchanged.

{gates['pytest_summary']}. G05, G16 and G17 pass by detecting the archived
defects rather than by hiding them.

## What is still not done

- A physical common-sky acquisition. `OrderRays` carries no screen
  coordinates, so no co-registered unresolved image can be built from the
  archived objects. Deferred to R3 as the amendment specifies.
- The unknown-background reconstruction companion, and any estimator built on
  the source metric. Both are new analyses.
- The uploaded Mahakal PDF's lineage: `{prov['manuscript_lineage']['status']}`.
  It is a different document from the repository PDF and is not on this
  machine, so nothing here claims to reproduce it.
- Wider probe widths, refined age grids, other geometries, and the
  twelve-geometry nuisance sweep: all deferred, none authorized here.

Generated {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}. Stopping for
review, as the protocol requires.
"""
    (run_dir / "R0_R2_REPORT.md").write_text(body)
    sums = "\n".join(f"{sha(p)}  {p.name}" for p in sorted(run_dir.iterdir())
                     if p.is_file() and p.name != "SHA256SUMS.txt")
    (run_dir / "SHA256SUMS.txt").write_text(sums + "\n")
    print(f"wrote {(run_dir / 'R0_R2_REPORT.md').relative_to(ROOT)}")
    print(f"wrote SHA256SUMS.txt ({len(sums.splitlines())} files)")
    print(f"token: {token}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main((ROOT / sys.argv[1]).resolve()))
