#!/usr/bin/env python3
"""Review 027: synthetic cut-cell and error-budget checks, not a Kerr run.
Requires NumPy and Shapely. Uses no network, ray maps, source banks or target SVD.
All domains below are explicit synthetic fixtures. Output must be a new file.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import platform
import numpy as np
import shapely
from shapely.geometry import Polygon, box


def regular_polygon(n: int, r: float = 1.0, phase: float = 0.0) -> Polygon:
    t = 2 * np.pi * (np.arange(n) + phase) / n
    return Polygon(np.column_stack((r * np.cos(t), r * np.sin(t))))


def area_vector(region, detectors) -> np.ndarray:
    return np.array([region.intersection(d).area for d in detectors])


def run() -> dict:
    checks = []
    def require(name, condition):
        checks.append({'name': name, 'passed': bool(condition)})
        if not condition:
            raise AssertionError(name)

    cell = box(0, 0, 1, 1)
    region = box(0, 0, .2, 1)
    detectors = [box(0, 0, .5, 1), box(.5, 0, 1, 1)]
    true = area_vector(cell.intersection(region), detectors)
    fraction_times_overlap = region.area / cell.area * area_vector(cell, detectors)
    require('triple_intersection_is_not_fraction_times_overlap',
            np.max(np.abs(true - fraction_times_overlap)) > .09)
    require('positive_cut_area_with_exterior_cell_center',
            not region.contains(cell.centroid) and region.area > 0)
    require('cut_flux_conserved_on_detector_partition',
            abs(true.sum() - region.area) < 1e-12)
    pieces = [box(i / 4, j / 4, (i + 1) / 4, (j + 1) / 4)
              for i in range(4) for j in range(4)]
    split = sum((area_vector(p.intersection(region), detectors) for p in pieces),
                start=np.zeros(2))
    require('same_field_fixed_detector_cut_cell_subdivision',
            np.max(np.abs(split - true)) < 1e-12)
    # Fractions are between 0 and 1; holes and disconnected pieces are retained.
    ring = box(0, 0, 1, 1).difference(box(.25, .25, .75, .75))
    clipped = np.array([p.intersection(ring).area for p in pieces])
    require('holes_not_filled_by_outer_hull', abs(clipped.sum() - .75) < 1e-12)
    require('all_cut_fractions_in_unit_interval',
            np.min(clipped) >= 0 and np.max(clipped / pieces[0].area) <= 1 + 1e-12)
    whole_band = box(0, 0, 1, 1)
    emission_domain = box(0, 0, .4, 1)
    require('band_domain_is_not_full_source_validity',
            whole_band.intersection(emission_domain).area < whole_band.area)
    # A known geometric fraction does not supply a missing transfer value.
    exact_linear_flux = region.area * region.centroid.x
    outside_node_transfer = .5
    wrong_linear_flux = region.area * outside_node_transfer
    require('constant_extension_can_bias_nonconstant_transfer',
            abs(exact_linear_flux - wrong_linear_flux) > .07)

    sigma = 2.0
    O = true[:, None]
    a_cut = np.array([region.area])
    L = O / a_cut[None, :]
    C_brightness = sigma ** 2 * O @ np.diag(1 / a_cut) @ O.T
    C_flux = L @ np.diag(sigma ** 2 * a_cut) @ L.T
    require('cut_parent_brightness_flux_covariance_identity',
            np.max(np.abs(C_brightness - C_flux)) < 1e-12)
    C_detector = sigma ** 2 * np.diag([d.area for d in detectors])
    require('detector_noise_uses_full_detector_area_not_emitting_fraction',
            not np.allclose(C_detector, C_flux) and np.all(np.diag(C_detector) == 2.0))

    # Relative outer-area accuracy is not relative thin-band support accuracy.
    outer, inner = box(0, 0, 1, 1), box(.001, .001, .999, .999)
    band = outer.difference(inner)
    outer_shifted = box(.0001, 0, 1.0001, 1)
    new_band = outer_shifted.difference(inner)
    outer_relative = outer.symmetric_difference(outer_shifted).area / outer.area
    band_relative = band.symmetric_difference(new_band).area / band.union(new_band).area
    require('thin_band_amplifies_outer_boundary_error',
            outer_relative < 2.1e-4 and band_relative > .04)

    # Exact polygon integration is not exact integration over the true circle.
    polygon_errors = []
    for n in (60, 120, 240, 480, 960):
        p = regular_polygon(n)
        relative = 1 - p.area / math.pi
        formula = 1 - n * math.sin(2 * math.pi / n) / (2 * math.pi)
        require(f'regular_polygon_{n}_shoelace_matches_formula', abs(relative - formula) < 1e-12)
        polygon_errors.append({'vertices': n, 'area_error_against_unit_disk': relative})
    require('sixty_vertex_exact_polygon_can_miss_hull_budget',
            polygon_errors[0]['area_error_against_unit_disk'] > 2.5e-4)
    p = regular_polygon(60)
    coords = np.asarray(p.exterior.coords)[:-1]
    interleaved = np.empty((120, 2))
    interleaved[::2] = coords
    interleaved[1::2] = .5 * (coords + np.roll(coords, -1, axis=0))
    fake_refined = Polygon(interleaved)
    require('interpolating_old_polygon_edges_is_not_hull_refinement',
            p.symmetric_difference(fake_refined).area < 1e-12
            and abs(fake_refined.area / math.pi - 1) > 1e-3)
    shifted = regular_polygon(60, phase=.5)
    require('equal_total_polygon_area_hides_boundary_disagreement',
            abs(p.area - shifted.area) < 1e-12
            and p.symmetric_difference(shifted).area > 1e-3)

    # Boundary-response bound for a fixed bounded field on two compared masks.
    grid = [box(x, y, x + .5, y + .5)
            for x in (-1., -.5, 0., .5) for y in (-1., -.5, 0., .5)]
    A, B = regular_polygon(30, .9), regular_polygon(60, .9)
    dif = A.symmetric_difference(B)
    field = np.linspace(-2, 2, len(grid))  # piecewise constant on the detector
    yA, yB = area_vector(A, grid) * field, area_vector(B, grid) * field
    delta_areas = area_vector(dif, grid)
    bound = np.linalg.norm(np.abs(field) * delta_areas / np.sqrt(.25))
    measured = np.linalg.norm((yA - yB) / np.sqrt(.25))
    require('symmetric_difference_envelope_bounds_whitened_response', measured <= bound + 1e-12)

    # Scalar total-weight ratios cannot bound every Fisher direction.
    old = np.eye(2)
    reweighted = np.diag([1.9, .1])
    require('total_area_ratio_not_pointwise_fisher_bound',
            np.trace(old) == np.trace(reweighted)
            and np.linalg.eigvalsh(reweighted).min() < .2)
    # A fitted cost for binary masks is not a lower bound for all representations.
    e_early, e_late, boundary_cells, cap = .34504011323063843, .1920444069738653, 5796, 250000
    order = math.log(e_early / e_late, 2)
    factor = (e_late / .001) ** (1 / order)
    estimated_calls = boundary_cells * factor
    require('reported_binary_model_cost_arithmetic_reproduced', abs(estimated_calls / cap - 11.652058512042373) < 1e-10)
    return {
        'scope': 'Synthetic arithmetic and geometry checks only; no HDF5, Kerr operator, or 552-test suite was run.',
        'reviewed_commit': '37cbb76ad8e00b8461e67dff68ddf5becd949e7e',
        'checks': checks, 'n_checks': len(checks), 'all_passed': True,
        'triple_intersection_fixture': {'correct_flux': true.tolist(), 'incorrect_fraction_times_overlap': fraction_times_overlap.tolist()},
        'missing_transfer_fixture': {'true_linear_flux': exact_linear_flux, 'outside_node_extension_flux': wrong_linear_flux},
        'thin_band_fixture': {'outer_relative_symmetric_difference': outer_relative, 'band_relative_symmetric_difference': band_relative},
        'unit_circle_polygon_errors_not_Kerr_hulls': polygon_errors,
        'boundary_response_fixture': {'measured_norm': measured, 'upper_envelope_norm': bound},
        'binary_cost_model': {'fitted_order': order, 'estimated_calls': estimated_calls, 'cap_multiple': estimated_calls / cap, 'a_universal_lower_bound': False},
        'environment': {'python': platform.python_version(), 'numpy': np.__version__, 'shapely': shapely.__version__}
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Choose a fresh output path.')
    result = run()
    result['script_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x') as f:
        json.dump(result, f, indent=2, allow_nan=False)
        f.write('\n')
    print(f"{result['n_checks']} synthetic checks passed; no physical campaign run.")

if __name__ == '__main__':
    main()
