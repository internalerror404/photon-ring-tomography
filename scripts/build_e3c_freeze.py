#!/usr/bin/env python3
"""E3C step 1 -- freeze the operator grid before any geometry is evaluated.

Everything that could be tuned after seeing a result is pinned here: the source
class and its support rule, the localized probes, the observer sampling, the
common age grid, the noise convention, the SNR grid, the arms, the rank
conventions, the censoring rule and the permutation seeds. The freeze also
records the sha256 of every ray map it will consume, so a later map rebuild
cannot silently change what the audit ran on.

The common age endpoint is the one quantity that must be computed before the
freeze rather than declared in it, because choosing it from a favorable
geometry -- or from the retired sampled maximum -- would set the depth ceiling
to flatter the result. It is fixed from source-independent map summaries over
the *whole* grid:

    A_max = T_obs + 1.25 * max_{g,n} { Q_0.999^Omega, Q_0.999^I } + 2h

rounded up to a multiple of the age spacing. Q^Omega and Q^I depend only on the
ray maps. Q^F, the age-conditioned Fisher weighting, depends on the declared
source class and is therefore reported alongside them but never used to set the
grid.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from phrt.config import load_registry, sha256_file
from phrt.geometry.raymap import read
from phrt.io.tables import write_table
from phrt.provenance import collect as collect_provenance
from phrt.sources.physical_basis import (DEFAULT_N_AZIMUTHAL, DEFAULT_N_RADIAL,
                                         DEFAULT_N_TEMPORAL, SPLINE_DEGREE)

SPINS = (0.0, 0.5, 0.9, 0.98)
INCLINATIONS = (20, 50, 75)
ORDERS = (0, 1, 2)
PROFILE = "core"
ANCHORS = ("a000_i020", "a050_i050", "a098_i075")

RAYS_PER_ORDER = 1536
N_OBSERVER_TIMES = 8
OBSERVER_SPAN = 20.0            # M
PROBE_HALF_WIDTH = 3.0          # M, the localized historical probe sigma
AGE_STEP = 4.0                  # M
QUANTILES = (0.50, 0.90, 0.99, 0.999)
SNR_GRID = (1.0, 3.0, 10.0, 30.0, 100.0, 300.0, 1e3, 3e3, 1e4, 3e4, 1e5, 1e6)
OPERATIONAL_THRESHOLD = 1.0     # rho
SUBSAMPLE_SEED = 20260825
PERMUTATION_SEEDS = tuple(20260825 + 1000 * k for k in range(16))

ARMS = {
    "DIRECT_PHYSICAL": "order n=0 only",
    "RESOLVED_PHYSICAL": "orders n=0,1,2 as separately observed channels",
    "UNRESOLVED_IMAGE": "orders summed into one image plane, C_U = L C_R L^T",
    "TOTAL_FLUX": "all spatial information collapsed, C_F = S C_R S^T",
    "DELAY_ONLY": "physical per-ray delays, direct-order spatial mapping",
    "SPATIAL_ONLY": "physical spatial mappings, direct-order delay field",
    "EQUALIZED_ORDER_SENSITIVITY":
        "coordinates and delays preserved; only the declared order "
        "normalization altered",
    "PAIRING_DESTROYED":
        "delay, position and weight permuted independently within an order; "
        "a nonphysical negative control, never an alternative architecture",
}


def geometries() -> list[str]:
    return [f"a{int(round(s * 100)):03d}_i{i:03d}" for s in SPINS for i in INCLINATIONS]


def weighted_quantile(x: np.ndarray, w: np.ndarray, q: float) -> float:
    o = np.argsort(x)
    x, w = x[o], w[o]
    c = np.cumsum(w)
    if c[-1] <= 0:
        return float("nan")
    return float(np.interp(q * c[-1], c, x))


def main() -> int:
    t0 = time.time()
    reg = load_registry()
    maps = ROOT / "artifacts" / "raymaps"

    rows, hashes = [], {}
    for g in geometries():
        man = maps / f"{g}_{PROFILE}_manifest.json"
        if man.exists():
            hashes[man.name] = sha256_file(man)
        for n in ORDERS:
            p = maps / f"{g}_n{n}_{PROFILE}.h5"
            hashes[p.name] = sha256_file(p)
            rm = read(p)
            v = rm.valid
            d = rm.delay[v]
            dom = rm.pixel_area[v]
            g3 = np.power(np.abs(rm.redshift[v]), 3.0)
            weights = {
                # solid angle: where the band's area sits in retarded time
                "Omega": dom,
                # throughput: where its flux sits
                "I": dom * g3,
                # Fisher: the squared whitened transfer weight sqrt(dOmega) g^3.
                # This one is NOT a property of the spacetime alone -- it is the
                # row weight the declared measurement model and source class
                # produce, and it is reported as such.
                "F": dom * g3 ** 2,
            }
            row = {"geometry": g, "order": n, "profile": PROFILE,
                   "n_valid_rays": int(v.sum()),
                   "delay_min_M": float(d.min()), "delay_max_M": float(d.max())}
            for tag, w in weights.items():
                for q in QUANTILES:
                    row[f"Q_{q:g}_{tag}"] = weighted_quantile(d, w, q)
            rows.append(row)

    q999 = max(max(r["Q_0.999_Omega"], r["Q_0.999_I"]) for r in rows)
    raw = OBSERVER_SPAN + 1.25 * q999 + 2.0 * PROBE_HALF_WIDTH
    a_max = float(np.ceil(raw / AGE_STEP) * AGE_STEP)
    n_ages = int(round(a_max / AGE_STEP)) + 1

    # the direct channel's registered 99.9% throughput-weighted age boundary,
    # per geometry: the lower limit of the J_old integral
    a0_999 = {r["geometry"]: r["Q_0.999_I"] for r in rows if r["order"] == 0}

    write_table(rows, "e3c_weighted_delay_quantiles")

    prov = collect_provenance()
    freeze = {
        "schema": "phrt-e3c-freeze/2",
        "experiment_id": "E3C",
        "line": "PAPER_I_V2",
        "amendment": "PAPER_I_V2_PRE_E3C_AMENDMENT_001",
        "amendment_record":
            "artifacts/configs/PAPER_I_V2_PRE_E3C_AMENDMENT_001.json",
        "result_schema": "schemas/e3c_result_schema_v2.json",
        "accepted_base_commit": "0ef341dae3b21bc2bdd0e54a18971cff208af783",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "registry_sha256": reg.sha256,
        "git_commit": prov.git_commit,
        "geometries": geometries(),
        "anchor_geometries": list(ANCHORS),
        "orders": list(ORDERS),
        "profile": PROFILE,
        "raymap_sha256": hashes,

        "source_class": {
            "id": "C224",
            "n_radial": DEFAULT_N_RADIAL,
            "n_azimuthal": DEFAULT_N_AZIMUTHAL,
            "n_temporal": DEFAULT_N_TEMPORAL,
            "dimension": DEFAULT_N_RADIAL * DEFAULT_N_AZIMUTHAL * DEFAULT_N_TEMPORAL,
            "radial_basis": f"cubic B-spline, degree {SPLINE_DEGREE}, "
                            "uniform knots in log r, clamped at both ends",
            "azimuthal_basis": "real Fourier [1, cos phi, sin phi, cos 2phi, "
                               "sin 2phi, cos 3phi, sin 3phi]; phi is the "
                               "source-plane azimuth in the AART convention "
                               "after the registered rigid pi/2 offset",
            "temporal_basis": "DCT-II global cosine modes cos(pi k u), "
                              "u = (t - t_min)/(t_max - t_min), zero outside",
            "column_order": "radial-major, then azimuthal, then temporal",
            "normalization": "unnormalised design columns; every reported rank "
                             "and spectrum is of the whitened operator, not of "
                             "the basis",
            "modification_forbidden": "the registered primary class is not to "
                                      "be modified in E3C; enrichment happens "
                                      "only in E3D on nested classes",
        },

        "radial_support": {
            "primary_convention": "GEOMETRY_DEPENDENT",
            "rule": "r_inner = min over retained rays of source_r, r_outer = "
                    "max, taken across the three orders of that geometry after "
                    "subsampling",
            "why_this_is_stated": "if the primary radial knots move with spin, "
                    "a source-domain change is confounded with a spacetime "
                    "change. The primary class is preserved as registered and "
                    "the confound is measured, not assumed away, by the "
                    "common-support control below.",
            "control": {
                "id": "COMMON_RADIAL_SUPPORT",
                "geometries": list(ANCHORS),
                "rule": "one fixed interval in r/M contained in the valid "
                        "domain of all three anchors, with identical knot "
                        "locations in r/M; rays outside it are dropped from "
                        "the control operator only",
            },
            "emission_support_disclaimer":
                "near-horizon ray coverage does not imply the emissivity model "
                "physically emits to the horizon. Ray-map support and assumed "
                "source emission are separate objects.",
        },

        "localized_probe": {
            "form": "Gaussian in retarded age, flat in the emission annulus",
            "half_width_h_M": PROBE_HALF_WIDTH,
            "normalization": "unit L2 norm over the emission region, so the "
                             "reported Fisher information is not in units of "
                             "an arbitrary peak amplitude",
        },

        "observation": {
            "n_observer_times": N_OBSERVER_TIMES,
            "observer_span_M": OBSERVER_SPAN,
            "observer_times_M": list(np.linspace(0.0, OBSERVER_SPAN,
                                                 N_OBSERVER_TIMES)),
            "rays_per_order": RAYS_PER_ORDER,
            "subsample": "stratified in (screen azimuth, source radius, delay) "
                         "with quadrature rescaled so each band's total solid "
                         "angle is preserved",
            "subsample_seed": SUBSAMPLE_SEED,
        },

        "common_age_grid": {
            "step_M": AGE_STEP,
            "A_max_M": a_max,
            "n_ages": n_ages,
            "formula": "A_max = T_obs + 1.25 * max_{g,n} "
                       "{Q_0.999^Omega, Q_0.999^I} + 2h, rounded up to a "
                       "multiple of the age step",
            "max_Q_0999_over_grid_M": q999,
            "raw_before_rounding_M": raw,
            "source_independent": True,
            "direct_order_A_0_999_by_geometry_M": a0_999,
        },

        "measurement_model": {
            "id": "pixel_integrated",
            "datum": "z_p = dOmega_p * g_p^3 * j(r_p, phi_p, t_p) + eta_p",
            "noise": "Var(eta_p) = sigma_Omega^2 * dOmega_p, i.e. white noise "
                     "of density sigma_Omega per unit solid angle",
            "whitened_row": "sqrt(dOmega_p) / sigma_Omega * g_p^3 * "
                            "B(r_p, phi_p, t_p)",
            "equivalent_pixel_average_form":
                "y_p = g_p^3 j_p + eps_p with Var(eps_p) = sigma_Omega^2 / "
                "dOmega_p produces the same whitened row",
            "sigma_rule": "one noise density for the whole audit, fixed from "
                          "the direct arm's clean response to the declared "
                          "reference source. No arm may choose its own sigma.",
            "derived_arm_covariance": "y_U = L y_R with C_U = L C_R L^T; "
                                      "y_F = S y_R with C_F = S C_R S^T; "
                                      "C_R = sigma_Omega^2 diag(dOmega)",
            "invariance_gate": "G10q_continuum_noise_quadrature_invariance, "
                               "split/merge to 1e-10",
            "retired": "the flat per-row sigma convention with c = g^3 is "
                       "retired as pixelization-dependent",
        },

        "snr_grid": list(SNR_GRID),
        "arms": ARMS,
        "registered_gates": {
            "G9w_transfer_weight_semantics":
                "per order, the operator's response to the declared unit source "
                "with the declared row noise removed equals sum(dOmega * g^3) "
                "computed independently; tolerance 1e-10",
            "E3C_v2_no_reserved_e3d_fields": "no E3C table carries a name "
                                             "reserved for E3D",
            "E3C_v2_exact_rank_not_applicable": "every rank-reporting table "
                                                "carries exact_rank = NOT_APPLICABLE",
            "E3C_v2_dispositions_are_registered": "every disposition is one of "
                                                  "the registered values",
            "E3C_v2_depth_contract_complete": "the depth tables carry the "
                                              "supremum, the contiguous depth "
                                              "and the mask",
        },
        "canonical_tables": [
            "e3c_geometry_metrics", "e3c_age_information", "e3c_depth_curves",
            "e3c_historical_innovation", "e3c_incremental_indirect_gram",
            "e3c_matched_sensitivity_exponents", "e3c_matched_sensitivity_summary",
            "e3c_weighted_delay_quantiles", "e3c_weighted_delay_quantiles_long",
            "e3c_pairing_destroyed_distribution",
            "e3c_common_radial_support_control", "e3c_hypothesis_tests",
            "e3c_geometry_surface", "e3c_gate_detail",
        ],
        "permutation_seeds": list(PERMUTATION_SEEDS),

        "operator_notation": {
            "physical_operator": "mathcal A",
            "restricted_coefficient_matrix": "A_C = mathcal A Q_C",
            "Q_C": "the synthesis map of the declared class C",
            "rule": "every rank, nullity, singular value and conditioning "
                    "reported by E3C is a property of A_C. Nothing about "
                    "mathcal A follows from a spectrum of A_C.",
        },

        "depth_contract": {
            "oldest_detectable_age_probe":
                "sup { a : SNR_0^2 I(a) >= rho^2 }, a supremum over a possibly "
                "non-contiguous detectable set",
            "largest_contiguous_detectable_depth":
                "length in M of the longest run of consecutive detectable ages, "
                "reported with its endpoints; the span a reconstruction can use",
            "age_threshold_mask":
                "the complete boolean detectability mask over the common age grid",
            "retired_name": "T_rec, which did not say it was a supremum",
        },

        "reserved_for_e3d": ["D_hist", "d_eff", "effective_rank"],

        "rank_conventions": {
            "exact_rank": "NOT_APPLICABLE for float64 physical operators absent "
                          "a structural certificate; none exists here",
            "numerical_rank": "LAPACK default: sigma > max(m, d) * eps * "
                              "sigma_max, eps = binary64 machine epsilon. A "
                              "decision at a tolerance, not an algebraic rank",
            "operational_rank": "count of sigma >= rho with rho = "
                                f"{OPERATIONAL_THRESHOLD}, on the operator "
                                "scaled to the reference SNR",
            "operational_threshold_rho": OPERATIONAL_THRESHOLD,
            "effective_rank": "exp of the entropy of the normalised spectrum",
            "stable_rank": "||A||_F^2 / ||A||_2^2",
            "separation_required": "numerical, operational and effective rank "
                                   "are distinct quantities and are never "
                                   "substituted for one another",
        },

        "depth_definition": {
            "T_rec": "sup { a : SNR_0^2 * I(a) >= rho^2 }",
            "right_censoring": "a depth equal to A_max is right-censored and "
                               "reported as T_rec >= A_max; it is a lower "
                               "bound, not a measurement",
            "forbidden": "the raw maximum ray delay is not a historical depth",
        },

        "historical_innovation": {
            "J_old": "integral over a > A_0_0.999 of log(1 + I(a)) da, "
                     "trapezoidal on the common age grid",
            "lower_limit": "the direct order's registered 99.9% "
                           "throughput-weighted age boundary, per geometry",
            "delta_G_indirect": "G_resolved - G_direct; report rank, trace, "
                                "stable rank and smallest positive eigenvalue "
                                "on its image",
        },

        "aggregation_rules": {
            "surface": "the full 4x3 spin-by-inclination surface is reported "
                       "cell by cell",
            "statistics": "median, minimum, maximum, and whether the trend is "
                          "monotone; edge cases named",
            "forbidden_language": "these are deterministic registered "
                                  "geometries, not samples from a population. "
                                  "No p-values, no confidence intervals, no "
                                  "significance claims across cells.",
            "pairing_destroyed": "report the full 16-seed distribution, never "
                                 "a single favorable permutation",
            "matched_sensitivity": "all 19 aligned-window fractions retained, "
                                   "with median, IQR, overlap fraction and the "
                                   "count of unsupported fractions",
            "no_asymptotic_law": "n = 0, 1, 2 does not determine an asymptotic "
                                 "exponent and none is fitted",
        },

        "frozen_after": "no basis, support, SNR grid, age grid or threshold may "
                        "be changed after the first non-canary geometry is "
                        "evaluated",
    }

    out = ROOT / "artifacts" / "configs" / "E3C_OPERATOR_GRID_FREEZE.json"
    out.write_text(json.dumps(freeze, indent=2, sort_keys=False) + "\n")
    print(f"wrote {out.relative_to(ROOT)}")
    print(f"  geometries {len(freeze['geometries'])}, maps hashed {len(hashes)}")
    print(f"  max Q_0.999 over grid {q999:.3f} M -> A_max {a_max:.0f} M "
          f"({n_ages} ages at {AGE_STEP:g} M)")
    print(f"  total {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
