#!/usr/bin/env python3
"""R1L stage 1 -- localized operator and rank audit.

Stage one of the sequential rule in ``R1L_LOCALIZED_AUDIT_FREEZE.json``. No
truth is drawn, no estimator is fitted and no reconstruction error exists here:
this stage asks only what the operator can and cannot see, which is a property
of the geometry and the basis alone.

The one question it exists to settle is whether the resolved advantage reported
in R0C and R1 is measurement or global-cosine extrapolation. Under C224 the
question cannot be asked, because every temporal coefficient is supported on the
whole history and no coefficient is ever formally unconstrained. Under the
localized ladder it can: a temporal function whose support contains no ray gives
an exactly zero column, so "the direct image cannot see this epoch" becomes a
statement about the null space rather than about a condition number.

Both ladders are run side by side on the same rays, so the localized and global
numbers in the output tables are directly comparable.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

# REVIEWER_RULING_R1L_REPRODUCIBILITY_009 items 5 and 6. Thread-pool sizes are
# read once, when the BLAS loads behind the first numeric import, so the pin has
# to happen above that import and nowhere else. `pin()` raises rather than
# silently no-opping if anything numeric is already loaded.
from phrt.numerics import pin, record as numerics_record, require_single_threaded

pin()

import numpy as np  # noqa: E402  -- must follow the pin

from phrt.attestation import attest
from phrt.audits.rank import spectrum_of
from phrt.config import load_registry
from phrt.geometry.raymap import read
from phrt.geometry.sampling import common_count, stratified_subsample
from phrt.geometry.schwarzschild import kerr_keplerian_u
from phrt.io.manifests import (Gate, RunManifest, gate_from_tolerance, make_run_id,
                               merge_gate_file)
from phrt.io.tables import write_table
from phrt.operators.physical import PhysicalOperator, substitute_delay, substitute_spatial
from phrt.sources.localized_basis import LocalizedBasis, temporal_supports
from phrt.sources.orbits import isco_radius, kerr_omega
from phrt.sources.physical_basis import (PhysicalBasis, age_probe_norms,
                                         age_probe_spatial)

FREEZE = ROOT / "artifacts" / "configs" / "R1L_LOCALIZED_AUDIT_FREEZE.json"
R1_FREEZE = ROOT / "artifacts" / "configs" / "R1_MAIN_FREEZE.json"
E3C_FREEZE = ROOT / "artifacts" / "configs" / "E3C_OPERATOR_GRID_FREEZE.json"
REFERENCE_SNR = 100.0

LOCAL = {"L224": dict(n_radial=4, n_azimuthal=7, n_temporal=8),
         "L448": dict(n_radial=4, n_azimuthal=7, n_temporal=16),
         "L1056": dict(n_radial=6, n_azimuthal=11, n_temporal=16)}
GLOBAL = {"C224": dict(n_radial=4, n_azimuthal=7, n_temporal=8),
          "C448_T": dict(n_radial=4, n_azimuthal=7, n_temporal=16),
          "C1056_ST": dict(n_radial=6, n_azimuthal=11, n_temporal=16)}
MIRROR = {"L224": "C224", "L448": "C448_T", "L1056": "C1056_ST"}
PARENT = {"L448": "L224", "L1056": "L448", "C448_T": "C224", "C1056_ST": "C448_T"}
ARMS = ("DIRECT_PHYSICAL", "RESOLVED_PHYSICAL", "UNRESOLVED_IMAGE", "TOTAL_FLUX",
        "DELAY_ONLY", "SPATIAL_ONLY")


def build_arms(base) -> dict:
    ones = np.ones((1, len(base)))
    return {
        "DIRECT_PHYSICAL": dict(orders=[base[0]]),
        "RESOLVED_PHYSICAL": dict(orders=base),
        "UNRESOLVED_IMAGE": dict(orders=base, mixer=ones),
        "TOTAL_FLUX": dict(orders=base, mixer=ones, collapse="total_flux"),
        "DELAY_ONLY": dict(orders=substitute_spatial(base, base[0])),
        "SPATIAL_ONLY": dict(orders=substitute_delay(base, base[0])),
    }


def unit_source(basis) -> np.ndarray:
    u = np.zeros(basis.dimension)
    for a in range(basis.n_radial):
        u[(a * basis.n_azimuthal + 0) * basis.n_temporal + 0] = 1.0
    return u


def level_directions(basis) -> np.ndarray:
    """Orthonormal coefficient directions spanning the spatially constant fields.

    A field constant in space at each source time is ``c(t) * 1(r) * 1(phi)``.
    ``1(phi)`` is azimuthal mode 0 and ``1(r)`` is the all-ones radial vector,
    since the clamped B-splines are a partition of unity. So the level subspace
    is spanned by one coefficient vector per temporal mode, and it lies inside
    the class rather than approximating it.
    """
    cols = []
    for c in range(basis.n_temporal):
        v = np.zeros(basis.dimension)
        for a in range(basis.n_radial):
            v[(a * basis.n_azimuthal + 0) * basis.n_temporal + c] = 1.0
        cols.append(v / np.linalg.norm(v))
    return np.column_stack(cols)


def old_band_temporal_modes(basis, old_boundary_M: float) -> np.ndarray:
    """Temporal modes whose whole support lies at ages at or beyond the boundary.

    Age ``a`` is source time ``-a``, so a support ``[lo, hi]`` covers ages
    ``[-hi, -lo]`` and is entirely old when ``hi <= -old_boundary``. Global DCT
    modes have no such restriction -- every one of them touches every age -- so
    for the global ladder this returns nothing and the old-band subspace is
    built from the level split alone.
    """
    if isinstance(basis, LocalizedBasis):
        sup = temporal_supports(basis.t_min, basis.t_max, basis.n_temporal)
        return np.where(sup[:, 1] <= -float(old_boundary_M))[0]
    return np.array([], dtype=int)


def old_structural_subspace(basis, old_boundary_M: float) -> np.ndarray:
    """Orthonormal coefficient directions that are old-epoch *and* structural.

    Old-epoch: only temporal modes whose support is entirely in the old band.
    Structural: orthogonal to the level subspace, so a recovered spatial mean
    cannot be counted as recovered morphology.
    """
    modes = old_band_temporal_modes(basis, old_boundary_M)
    if modes.size == 0:
        return np.zeros((basis.dimension, 0))
    keep = np.zeros(basis.dimension, dtype=bool)
    for a in range(basis.n_radial):
        for b in range(basis.n_azimuthal):
            for c in modes:
                keep[(a * basis.n_azimuthal + b) * basis.n_temporal + int(c)] = True
    E = np.eye(basis.dimension)[:, keep]
    L = level_directions(basis)
    E = E - L @ (L.T @ E)
    Q, R = np.linalg.qr(E)
    d = np.abs(np.diag(R))
    return np.ascontiguousarray(Q[:, d > 1e-10 * max(d.max(), 1e-300)])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--classes", default="")
    ap.add_argument("--promote", action="store_true",
                    help="also write the canonical artifacts/tables and the "
                         "canonical gate files. Refused for a partial ladder")
    args = ap.parse_args()

    t0 = time.time()
    # Item 6: measured, not assumed. Aborts unless every loaded pool is serial.
    numerics = require_single_threaded()
    started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    fz = json.loads(FREEZE.read_text())
    r1 = json.loads(R1_FREEZE.read_text())
    e3c = json.loads(E3C_FREEZE.read_text())
    reg = load_registry()

    g = fz["scope"]["geometry"]
    spin = float(r1["physical_model"]["spin"])
    orders = list(r1["physical_model"]["orders"])
    t_obs = np.asarray(r1["observation"]["observer_times_M"], dtype=float)
    n_rays = int(r1["observation"]["rays_per_order"])
    seed = int(r1["observation"]["subsample_seed"])
    h = float(fz["F_age_resolution"]["probe_half_width_M"])
    step = float(fz["F_age_resolution"]["age_grid_step_M"])
    a_max = float(r1["metrics"]["age_grid_max_M"])
    old_b = float(r1["metrics"]["old_band_boundary_M"])
    rho = float(e3c["rank_conventions"]["operational_threshold_rho"])
    ages = np.arange(0.0, a_max + 1e-9, step)

    want = set(args.classes.split(",")) if args.classes else None
    specs = {**{k: (LocalizedBasis, v, "localized") for k, v in LOCAL.items()},
             **{k: (PhysicalBasis, v, "global") for k, v in GLOBAL.items()}}
    if want:
        specs = {k: v for k, v in specs.items() if k in want}

    run_id = make_run_id("R1L", reg.sha256)
    # Item 7: every run writes to its own directory. The canonical tables and
    # gates are written only by an explicit --promote on a full six-class run,
    # so a diagnostic invocation restricted to one class physically cannot
    # overwrite them -- which is how the L224 probes corrupted the record last
    # time. A convention would not have prevented that; a separate path does.
    run_dir = ROOT / "artifacts" / "runs" / run_id
    (run_dir / "tables").mkdir(parents=True, exist_ok=True)
    (run_dir / "gates").mkdir(parents=True, exist_ok=True)
    full_ladder = len(specs) >= 6
    if args.promote and not full_ladder:
        raise SystemExit(f"--promote refused: {len(specs)} classes selected, "
                         "the canonical set is the full six-class ladder")

    man = RunManifest(run_id=run_id, experiment_id="R1L_STAGE_1_OPERATOR_RANK_AUDIT",
                      seeds={"subsample_seed": seed}, started_at=started,
                      attestation=attest([FREEZE, R1_FREEZE]),
                      extra={"stage": "operator_rank_audit", "geometry": g,
                             "reference_snr": REFERENCE_SNR,
                             "age_grid_step_M": step,
                             "old_band_boundary_M": old_b,
                             "classes": list(specs),
                             "full_ladder": full_ladder,
                             "promoted_to_canonical": bool(args.promote),
                             "run_dir": str(run_dir.relative_to(ROOT)),
                             "numerics": numerics_record()})
    man.add_input(reg.path)
    man.add_input(FREEZE)

    rng = np.random.default_rng(seed)
    maps = ROOT / "artifacts" / "raymaps"
    raw = [read(maps / f"{g}_n{n}_core.h5") for n in orders]
    base = common_count([stratified_subsample(rm, n_rays, rng) for rm in raw], rng)
    r_in = float(r1["physical_model"]["r_inner_M"])
    r_out = float(r1["physical_model"]["r_outer_M"])
    t_lo = float(r1["observation"]["basis_t_min"])
    t_hi = float(r1["observation"]["basis_t_max"])

    bases = {k: cls(r_in, r_out, t_lo, t_hi, **cfg) for k, (cls, cfg, _) in specs.items()}
    kind = {k: knd for k, (_, _, knd) in specs.items()}

    # The noise density is fixed once, on the *global* C224 direct arm, which is
    # the same scalar E3C, E3D and R1 used. Localizing the model must not
    # requantify the detector, and it cannot be fixed on a localized class: the
    # natural unit source there is the oldest temporal hat, whose support holds
    # no direct-order ray at all, so the reference would be exactly zero. That
    # is the result this stage is looking for, not a normalisation to divide by.
    ref_basis = PhysicalBasis(r_in, r_out, t_lo, t_hi, 4, 7, 8)
    ref_direct = PhysicalOperator(orders=[base[0]], observer_times=t_obs,
                                  design=ref_basis.design, dimension=ref_basis.dimension)
    s_ref = float(np.sqrt(np.mean(ref_direct.matvec(unit_source(ref_basis)) ** 2)))
    if not np.isfinite(s_ref) or s_ref < 1e-12:
        raise SystemExit(f"reference noise density is degenerate ({s_ref:.3e}); "
                         "every whitened operator would be meaningless")

    spec_rows, null_rows, old_rows, age_rows, nest_rows, sup_rows = [], [], [], [], [], []
    worst = {"adjoint": 0.0, "smoke": 0.0, "monotonicity": 0.0, "nesting": 0.0,
             "parent_rank": 0, "unreached": 0.0, "compactness": 0.0, "orbit": 0.0}

    # ---- A: the basis contract, before any operator is formed ---------------
    # every observer time, not just the first: the operator samples the source
    # at t_obs - delay for all eight, so a set built from one of them would call
    # the newest temporal modes unreached and turn a bookkeeping slip into a
    # false null-space claim -- the exact error this stage exists to avoid.
    sr = np.concatenate([np.tile(o.source_r, t_obs.size) for o in base])
    sp = np.concatenate([np.tile(o.source_phi, t_obs.size) for o in base])
    st = np.concatenate([np.concatenate([float(t) - o.delay for t in t_obs])
                         for o in base])
    for child, parent in PARENT.items():
        if child not in bases or parent not in bases:
            continue
        A, B = bases[parent].design(sr, sp, st), bases[child].design(sr, sp, st)
        Q, _ = np.linalg.qr(B)
        res = float(np.abs(A - Q @ (Q.T @ A)).max()) / max(float(np.abs(A).max()), 1e-300)
        worst["nesting"] = max(worst["nesting"], res)
        nest_rows.append({"geometry": g, "kind": kind[child], "parent": parent,
                          "child": child, "parent_dimension": bases[parent].dimension,
                          "child_dimension": bases[child].dimension,
                          "projection_residual": res})

    tt = np.linspace(t_lo, t_hi, 4001)
    for name, b in bases.items():
        if isinstance(b, LocalizedBasis):
            T = b.design(np.full(tt.size, 0.5 * (r_in + r_out)),
                         np.zeros(tt.size), tt)[:, :b.n_temporal]
            widths = b.support_widths()
            sup = b.supports()
        else:
            from phrt.sources.physical_basis import temporal_design as dct
            T = dct(tt, t_lo, t_hi, b.n_temporal)
            widths = np.full(b.n_temporal, t_hi - t_lo)
            sup = np.tile([t_lo, t_hi], (b.n_temporal, 1))
        occ = (np.abs(T) > 0).mean(axis=0)
        worst["compactness"] = max(worst["compactness"],
                                   float(occ.max()) if kind[name] == "localized" else 0.0)
        for c in range(b.n_temporal):
            sup_rows.append({"geometry": g, "source_class": name, "kind": kind[name],
                             "temporal_mode": c,
                             "support_lo_source_time_M": float(sup[c, 0]),
                             "support_hi_source_time_M": float(sup[c, 1]),
                             "support_width_M": float(widths[c]),
                             "fraction_of_history_occupied": float(occ[c]),
                             "oldest_age_touched_M": float(-sup[c, 0]),
                             "youngest_age_touched_M": float(-sup[c, 1]),
                             "entirely_in_old_band": bool(sup[c, 1] <= -old_b)})

    old_mode = {(r["source_class"], r["temporal_mode"]): r["entirely_in_old_band"]
                for r in sup_rows}

    # ---- C: the orbit law must agree with the fluid the ray maps used -------
    rr = np.unique(np.clip(sr, isco_radius(spin), r_out))
    u0, _, _, u3 = kerr_keplerian_u(spin, rr)
    worst["orbit"] = float(np.abs(u3 / u0 - kerr_omega(rr, spin)).max())
    isco_ok = float(fz["C_physically_consistent_source_motion"]
                    ["circular_family"]["r_centre_M"][0]) >= isco_radius(spin) - 1e-12

    # ---- the operators -----------------------------------------------------
    arms_cfg = build_arms(base)
    for cname, basis in bases.items():
        ops = {n: PhysicalOperator(design=basis.design, dimension=basis.dimension,
                                   observer_times=t_obs, **cfg)
               for n, cfg in arms_cfg.items()}
        ref = ops["RESOLVED_PHYSICAL"]

        wadj = 0.0
        for _ in range(20):
            x = rng.normal(size=ref.shape[1]); y = rng.normal(size=ref.shape[0])
            a_, b_ = float(y @ ref.matvec(x)), float(x @ ref.rmatvec(y))
            wadj = max(wadj, abs(a_ - b_) / max(abs(a_), abs(b_), 1e-300))
        worst["adjoint"] = max(worst["adjoint"], wadj)

        cols = rng.choice(basis.dimension, size=min(48, basis.dimension), replace=False)
        E = np.zeros((basis.dimension, cols.size))
        E[cols, np.arange(cols.size)] = 1.0
        dense = ref.to_dense()[:, cols]
        free = np.column_stack([ref.matvec(E[:, k]) for k in range(cols.size)])
        worst["smoke"] = max(worst["smoke"], float(np.abs(dense - free).max())
                             / max(float(np.abs(dense).max()), 1e-300))

        cum = [PhysicalOperator(orders=base[:k], observer_times=t_obs,
                                design=basis.design, dimension=basis.dimension).gram()
               for k in range(1, len(base) + 1)]
        for i in range(1, len(cum)):
            dd = 0.5 * (cum[i] - cum[i - 1] + (cum[i] - cum[i - 1]).T)
            lam = float(np.min(np.linalg.eigvalsh(dd)))
            worst["monotonicity"] = max(worst["monotonicity"], max(0.0, -lam)
                                        / max(1.0, float(np.linalg.norm(cum[i], 2))))

        Sold = old_structural_subspace(basis, old_b)
        Lvl = level_directions(basis)

        for aname, op in ops.items():
            B = op.to_dense() * (REFERENCE_SNR / s_ref)
            s = spectrum_of(B, basis.dimension, operational_threshold=rho).summary()

            colmax = np.abs(B).max(axis=0)
            exact_zero = colmax == 0.0
            per_mode = exact_zero.reshape(basis.n_radial * basis.n_azimuthal,
                                          basis.n_temporal).all(axis=0)
            if isinstance(basis, LocalizedBasis):
                reached = basis.temporal_columns_covering(st)
                unreached_cols = ~basis.columns_for_temporal_modes(reached)
                worst["unreached"] = max(worst["unreached"],
                                         float(np.abs(B[:, unreached_cols]).max())
                                         if unreached_cols.any() else 0.0)

            spec_rows.append({
                "geometry": g, "source_class": cname, "kind": kind[cname],
                "mirror_of": MIRROR.get(cname, ""), "arm": aname,
                "source_dimension": basis.dimension,
                "n_radial": basis.n_radial, "n_azimuthal": basis.n_azimuthal,
                "n_temporal": basis.n_temporal,
                "data_dimension": int(op.shape[0]),
                "full_column_rank": bool(s["numerical_rank"] == basis.dimension),
                "n_exactly_zero_columns": int(exact_zero.sum()),
                "n_temporal_modes_entirely_unseen": int(per_mode.sum()),
                **{k: s[k] for k in ("numerical_rank", "operational_rank", "nullity",
                                     "sigma_max", "sigma_min_positive",
                                     "kappa_positive", "stable_rank",
                                     "effective_rank", "trace_information")}})

            for c in range(basis.n_temporal):
                idx = [(a * basis.n_azimuthal + bq) * basis.n_temporal + c
                       for a in range(basis.n_radial)
                       for bq in range(basis.n_azimuthal)]
                sub = B[:, idx]
                sv = np.linalg.svd(sub, compute_uv=False)
                null_rows.append({
                    "geometry": g, "source_class": cname, "kind": kind[cname],
                    "arm": aname, "temporal_mode": c,
                    "entirely_in_old_band": bool(old_mode[(cname, c)]),
                    "n_columns": len(idx),
                    "column_max_abs": float(np.abs(sub).max()),
                    "exactly_zero_block": bool(np.abs(sub).max() == 0.0),
                    "sigma_max": float(sv[0]) if sv.size else 0.0,
                    "sigma_min": float(sv[-1]) if sv.size else 0.0,
                    "operational_rank": int((sv >= rho).sum()),
                    "exact_nullity": int((sv <= 0.0).sum())})

            if Sold.shape[1] > 0:
                Bo = B @ Sold
                svo = np.linalg.svd(Bo, compute_uv=False)
                op_rank = int((svo >= rho).sum())
                exact_null = int((svo <= 0.0).sum())
            else:
                svo = np.zeros(0)
                op_rank, exact_null = 0, 0
            Bl = B @ Lvl
            svl = np.linalg.svd(Bl, compute_uv=False)
            old_rows.append({
                "geometry": g, "source_class": cname, "kind": kind[cname],
                "arm": aname, "old_band_boundary_M": old_b,
                "old_structural_dimension": int(Sold.shape[1]),
                "old_structural_operational_rank": op_rank,
                "old_structural_exact_nullity": exact_null,
                "old_structural_sigma_max": float(svo[0]) if svo.size else 0.0,
                "old_structural_sigma_min": float(svo[-1]) if svo.size else 0.0,
                "old_structural_information_volume":
                    float(np.sum(np.log1p(np.clip(svo, 0.0, None) ** 2))),
                "level_operational_rank": int((svl >= rho).sum()),
                "level_information_volume":
                    float(np.sum(np.log1p(np.clip(svl, 0.0, None) ** 2)))})

            rp = [age_probe_spatial(o.source_r, o.source_phi, r_in, r_out,
                                    basis.n_radial, basis.n_azimuthal)
                  for o in op.orders]
            pn = age_probe_norms(r_in, r_out, h, basis.n_radial, basis.n_azimuthal)
            for a in ages:
                blocks = []
                for i, o in enumerate(op.orders):
                    c0 = o.coefficient()
                    for t in op.observer_times:
                        w = c0 * np.exp(-0.5 * ((float(t) - o.delay + a) / h) ** 2)
                        Bm = rp[i] * w[:, None]
                        blocks.append(Bm.sum(axis=0, keepdims=True)
                                      if op.collapse == "total_flux" else Bm)
                po = np.split(np.vstack(blocks), len(op.orders))
                P = np.vstack([sum(op.L[ch, k] * po[k] for k in range(len(op.orders)))
                               for ch in range(op.n_channels)])
                P = P / np.sqrt(op.channel_variance())[:, None] / (pn * s_ref)[None, :]
                M = P.T @ P
                lv = np.linalg.eigvalsh(0.5 * (M + M.T))
                age_rows.append({
                    "geometry": g, "source_class": cname, "kind": kind[cname],
                    "arm": aname, "retarded_age": float(a),
                    "lambda_max_per_snr2": float(lv[-1]),
                    "lambda_min_per_snr2": float(max(lv[0], 0.0)),
                    "detectable_at_reference_snr":
                        bool(REFERENCE_SNR ** 2 * lv[-1] >= rho ** 2),
                    "log_information_volume_at_reference_snr":
                        float(np.sum(np.log1p(REFERENCE_SNR ** 2
                                              * np.clip(lv, 0.0, None))))})
        print(f"  {cname:9s} done, {time.time() - t0:.0f}s")

    for child, parent in PARENT.items():
        if child not in bases or parent not in bases:
            continue
        for aname in ARMS:
            pk = [r for r in spec_rows if r["source_class"] == parent and r["arm"] == aname]
            ck = [r for r in spec_rows if r["source_class"] == child and r["arm"] == aname]
            if pk and ck:
                worst["parent_rank"] = max(worst["parent_rank"],
                                           max(0, pk[0]["numerical_rank"]
                                               - ck[0]["numerical_rank"]))

    dims_ok = all(bases[k].dimension == d for k, d in
                  (("L224", 224), ("L448", 448), ("L1056", 1056)) if k in bases)
    man.add_gate(Gate("R1L_G1_dyadic_dimension_mirror", "PASS" if dims_ok else "FAIL",
                      measured=int(dims_ok), threshold=1,
                      note="the localized ladder has exactly the E3D dimensions"))
    man.add_gate(gate_from_tolerance("R1L_G2_exact_class_nesting", worst["nesting"], 1e-12,
                                     note="dyadic nodes nest arithmetically, so this "
                                          "must be zero rather than small"))
    man.add_gate(gate_from_tolerance("R1L_G3_temporal_support_compactness",
                                     worst["compactness"], 0.30,
                                     note="largest fraction of the history any "
                                          "localized temporal function occupies"))
    man.add_gate(gate_from_tolerance("R1L_G4_adjoint", worst["adjoint"], 1e-8))
    man.add_gate(gate_from_tolerance("R1L_G5_dense_matrix_free_parity", worst["smoke"], 1e-10))
    man.add_gate(gate_from_tolerance("R1L_G6_gram_monotonicity", worst["monotonicity"], 1e-10))
    man.add_gate(Gate("R1L_G7_enrichment_does_not_lose_rank",
                      "PASS" if worst["parent_rank"] == 0 else "FAIL",
                      measured=worst["parent_rank"], threshold=0))
    man.add_gate(Gate("R1L_G8_unreached_columns_are_exactly_zero",
                      "PASS" if worst["unreached"] == 0.0 else "FAIL",
                      measured=worst["unreached"], threshold=0.0,
                      note="a temporal function whose support holds no ray must "
                           "give a literally zero column, which is the property "
                           "that makes an unseen epoch a null direction rather "
                           "than a confident extrapolation"))
    man.add_gate(gate_from_tolerance("R1L_G9_orbit_law_matches_raymap_fluid",
                                     worst["orbit"], 1e-12,
                                     note="pattern Omega against the Kerr fluid "
                                          "four-velocity the redshift was built from"))
    man.add_gate(Gate("R1L_G10_circular_centres_outside_isco",
                      "PASS" if isco_ok else "FAIL", measured=int(isco_ok), threshold=1))
    man.add_gate(Gate("R1L_G11_pinned_numerical_environment",
                      "PASS" if numerics["all_single_threaded"] else "FAIL",
                      measured=max((p.get("num_threads", 0)
                                    for p in numerics["pools"]), default=0),
                      threshold=1,
                      note="every loaded BLAS pool must report exactly one "
                           "thread, interrogated after the import rather than "
                           "inferred from the environment"))

    tables = (("r1l_class_spectra", spec_rows),
              ("r1l_temporal_mode_visibility", null_rows),
              ("r1l_old_structural_support", old_rows),
              ("r1l_age_information", age_rows),
              ("r1l_class_nesting", nest_rows),
              ("r1l_temporal_supports", sup_rows))
    for name, rows in tables:
        man.add_output(write_table(rows, name, out_dir=run_dir / "tables"))
        if args.promote:
            write_table(rows, name)

    sub = {gt.name: gt.to_dict() for gt in man.gates}
    gate_doc = json.dumps({"experiment": "R1L_STAGE_1_OPERATOR_RANK_AUDIT",
                           "run_id": run_id, "promoted": bool(args.promote),
                           "gates": sub,
                           "summary": {s: sum(1 for v in sub.values()
                                              if v["status"] == s)
                                       for s in ("PASS", "FAIL", "NOT_RUN")}},
                          indent=2) + "\n"
    (run_dir / "gates" / "r1l_stage1_gates.json").write_text(gate_doc)
    mp = man.write(reg.path, reg.sha256, runtime_seconds=time.time() - t0)
    if args.promote:
        merge_gate_file(man.gates, run_id)
        (ROOT / "artifacts" / "gates" / "r1l_stage1_gates.json").write_text(gate_doc)
    print("\ngates")
    for gt in man.gates:
        m = gt.measured
        print(f"  {gt.name:46s} {gt.status:6s} "
              f"{m:.3e}" if isinstance(m, float) else
              f"  {gt.name:46s} {gt.status:6s} {m}")
    print(f"\nrun dir  {run_dir.relative_to(ROOT)}"
          f"\nmanifest {mp}"
          f"\npools    {[p.get('num_threads') for p in numerics['pools']]}"
          f"\npromoted {bool(args.promote)}\ntotal {time.time() - t0:.0f}s")
    return 1 if man.failed_gates else 0


if __name__ == "__main__":
    raise SystemExit(main())
