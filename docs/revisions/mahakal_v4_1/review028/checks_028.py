#!/usr/bin/env python3
"""Review 028: independent synthetic tests, not real Kerr calculations.

No raw ray maps, target operator, repository test suite or network access.
Tests distinguish physical level sets, numerical failures, thin-band geometry,
and approximation error. --output must name a new file.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import platform

import numpy as np
import scipy
from scipy.interpolate import CubicSpline
from scipy.optimize import brentq


def radial_polygon(theta: np.ndarray, nodes: np.ndarray, radii: np.ndarray) -> np.ndarray:
    """Radial intersection with a polygon on sorted, uniform angular nodes."""
    h = 2 * np.pi / len(nodes)
    k = np.floor((theta % (2*np.pi)) / h).astype(int) % len(nodes)
    j = (k + 1) % len(nodes)
    vertices = np.column_stack((radii * np.cos(nodes), radii * np.sin(nodes)))
    a, b = vertices[k], vertices[j]
    d = b - a
    u = np.column_stack((np.cos(theta), np.sin(theta)))
    numerator = a[:, 0] * d[:, 1] - a[:, 1] * d[:, 0]
    denominator = u[:, 0] * d[:, 1] - u[:, 1] * d[:, 0]
    return numerator / denominator


def band_error(outer: np.ndarray, inner: np.ndarray,
               ref_outer: np.ndarray, ref_inner: np.ndarray) -> dict:
    measure = lambda v: float(np.mean(v) * np.pi)  # half the angular integral
    a = measure(outer**2 - inner**2)
    b = measure(ref_outer**2 - ref_inner**2)
    intersection = measure(np.maximum(np.minimum(outer**2, ref_outer**2)
                                      - np.maximum(inner**2, ref_inner**2), 0))
    union = a+b-intersection
    return {
        'band_symdiff_relative': (a+b-2*intersection)/union,
        'boundaries_symdiff_relative': measure(np.abs(outer**2-ref_outer**2)
                                               + np.abs(inner**2-ref_inner**2))/union,
        'min_width': float(np.min(outer-inner)),
    }


def run() -> dict:
    checks = []
    def require(name: str, passed: bool) -> None:
        checks.append({'name': name, 'passed': bool(passed)})
        if not passed:
            raise AssertionError(name)

    root = brentq(lambda x: 40 + 20*x - 50, 0., 1., xtol=1e-13)
    require('physical_emission_contour_root', abs(root-.5) < 1e-12)
    x = np.array([.1, .25, .4, .6, .9])
    truth_radius = 40 + 20*x
    observed_radius = truth_radius.copy()
    observed_radius[1] = np.nan
    statuses = ['UNKNOWN_SOLVER' if not np.isfinite(r) else
                'PHYSICAL_OUTSIDE_AT_EVALUATED_POINT' if r > 50 else
                'PHYSICAL_INSIDE_AT_EVALUATED_POINT' for r in observed_radius]
    require('numerical_failure_remains_unknown_not_outside', statuses[1] == 'UNKNOWN_SOLVER' and truth_radius[1] < 50)
    require('verified_outside_sample_is_not_missing_transfer', statuses[-1] == 'PHYSICAL_OUTSIDE_AT_EVALUATED_POINT')
    require('one_outside_cell_center_does_not_exclude_whole_cell',
            (40+20*.75 > 50) and (40+20*.25 < 50))

    # Sign-changing endpoints across a pole do not satisfy continuity.
    pole = .123456789
    f = lambda z: 1.0/(z-pole)
    p = brentq(f, 0., 1., xtol=1e-13)
    require('bracket_sign_change_across_pole_is_not_physical_root', abs(f(p)) > 1e8)
    f_two = lambda z: (z-.25)*(z-.75)
    r_a, r_b = brentq(f_two, 0., .5), brentq(f_two, .5, 1.)
    require('equal_endpoint_signs_can_hide_two_roots', f_two(0)*f_two(1) > 0 and np.allclose([r_a,r_b],[.25,.75]))
    require('tangency_is_not_detected_by_sign_change_only', (.4-.5)**2 > 0 and (.6-.5)**2 > 0 and (.5-.5)**2 == 0)
    residual = 1e-8*(.6-.5)
    require('small_scalar_residual_does_not_bound_screen_position_without_gradient', abs(residual)<1.1e-9 and abs(.6-.5)>.09)

    original_error = np.array([.05, 0.])
    new_error = np.array([0., .025])
    removed = float(np.linalg.norm(original_error-new_error))
    decrease = float(np.linalg.norm(original_error)-np.linalg.norm(new_error))
    require('response_norm_reduction_is_not_additive_causal_decomposition', abs(removed-decrease) > .03)

    width, displacement = .03, .0001
    relative_band_difference = 2*displacement/(width+displacement)
    require('thin_band_geometry_budget_depends_on_width_not_ray_cell_count', relative_band_difference > 2.5e-4)
    require('same_detector_flux_can_hide_band_disagreement', width == width and relative_band_difference > 0)
    circle_area_error = 1 - math.sin(2*math.pi/60)/(2*math.pi/60)
    require('same_fixed_polygon_across_profiles_is_not_continuum_convergence', circle_area_error > 1e-3)
    vertex_only_trapezoid_square_area = 2*math.pi
    require('vertex_angle_trapezoid_is_not_exact_polygon_area', abs(vertex_only_trapezoid_square_area-4) > 2)

    # Fresh synthetic evaluations of smooth inner/outer boundary functions.
    theta = 2*np.pi*(np.arange(131072)+.5)/131072
    center = lambda t: 5 + .2*np.cos(t) + .1*np.sin(3*t)
    thickness = lambda t: .02*(1+.2*np.cos(2*t))
    r_in = lambda t: center(t)-thickness(t)/2
    r_out = lambda t: center(t)+thickness(t)/2
    reference_inner, reference_outer = r_in(theta), r_out(theta)
    rows = []
    for n in (32, 64, 128):
        nodes = np.linspace(0., 2*np.pi, n+1)
        inner_nodes, outer_nodes = r_in(nodes), r_out(nodes)
        inner_nodes[-1], outer_nodes[-1] = inner_nodes[0], outer_nodes[0]
        ci = CubicSpline(nodes, inner_nodes, bc_type='periodic')
        co = CubicSpline(nodes, outer_nodes, bc_type='periodic')
        curved = band_error(co(theta), ci(theta), reference_outer, reference_inner)
        polygon = band_error(radial_polygon(theta,nodes[:-1],outer_nodes[:-1]),
                             radial_polygon(theta,nodes[:-1],inner_nodes[:-1]),
                             reference_outer,reference_inner)
        # Independent midpoint values, not agreement at interpolation nodes.
        mid = .5*(nodes[1:]+nodes[:-1])
        heldout = float(max(np.max(np.abs(ci(mid)-r_in(mid))), np.max(np.abs(co(mid)-r_out(mid)))))
        require(f'curved_boundary_{n}_tested_at_fresh_parameters', heldout > 0 and curved['min_width'] > 0)
        rows.append({'vertices_per_boundary':n, 'straight_polygon':polygon,
                     'periodic_cubic':curved, 'independent_midpoint_max_error':heldout})
    require('validated_curved_representation_can_reduce_error_at_same_nodes_in_fixture',
            rows[-1]['periodic_cubic']['boundaries_symdiff_relative'] <
            rows[-1]['straight_polygon']['boundaries_symdiff_relative']/100)
    require('synthetic_curved_thin_band_meets_original_geometry_budget',
            rows[-1]['periodic_cubic']['boundaries_symdiff_relative'] < 2.5e-4)
    require('synthetic_straight_thin_band_remains_unqualified_same_nodes',
            rows[-1]['straight_polygon']['boundaries_symdiff_relative'] > 2.5e-4)

    sigma = np.array([1.4371649013558634,1.3458732686433825,.8062804378838909])
    lo, hi = .500081210, (250/249)**2
    lower, upper = sigma*np.sqrt(lo), sigma*np.sqrt(hi)
    require('row_bound_proves_at_least_one_and_at_most_two_not_exactly_one',
            lower[0]>1 and lower[1]<1<upper[1] and upper[2]<1)
    # Uncertain area requires a field bound, not omission from signal.
    uncertain_area, bound_M = .01, 100.
    response_bound = uncertain_area*bound_M  # sigma=sqrt(detector area)=1
    require('small_unknown_area_need_not_have_small_response', response_bound > .1)
    require('remaining_budget_is_not_literal_exhaustion', 30000-18000 == 12000 and 250000-0 == 250000)
    return {
        'scope':'Synthetic tests and arithmetic only; no real hull, ray, target-operator, or repository-suite execution.',
        'reviewed_commit':'6f76ee56f024f4e5895b89325dc43d4db08863b3',
        'checks':checks,'n_checks':len(checks),'all_passed':all(c['passed'] for c in checks),
        'physical_root_fixture':{'root':root,'point_statuses':statuses},
        'pole_fixture':{'returned_point':p,'residual_magnitude':abs(f(p))},
        'response_norm_fixture':{'norm_decrease':decrease,'removed_vector_norm':removed},
        'thin_band_fixture':{'width':width,'displacement':displacement,'relative_symdiff':relative_band_difference},
        'fixed_polygon_true_disk_area_error':circle_area_error,
        'vertex_angle_trapezoid_square_area':vertex_only_trapezoid_square_area,
        'synthetic_curved_boundary_comparison':rows,
        'row_bound':{'ratio_min':lo,'ratio_max':hi,'singular_lower':lower.tolist(),'singular_upper':upper.tolist(),
                     'operational_count_lower':1,'operational_count_upper':2,'actual_corrected_count_measured':False},
        'remaining_counters_reported_by_agent':{'boundary_solves':12000,'transfer_evaluations':250000},
        'environment':{'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True,type=Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Refusing to overwrite an existing output.')
    result=run()
    result['script_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('x') as out:
        json.dump(result,out,indent=2,allow_nan=False)
        out.write('\n')
    print(f"{result['n_checks']} independent synthetic checks passed; no physical campaign executed.")

if __name__=='__main__':
    main()
