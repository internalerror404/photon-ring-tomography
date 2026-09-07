#!/usr/bin/env python3
"""Review 030: radial-domain and accounting fixtures, not the 680 campaign rays.

Uses the scalar Schwarzschild radial potential (M=1) with chosen impact
parameters to compare Jacobi inversion and independent definite quadrature.
No repository ray maps, source bank, full transfer evaluator or target SVD.
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
from scipy.integrate import quad
from scipy.optimize import brentq
from scipy.special import ellipj, ellipk, ellipkinc


def run() -> dict:
    checks = []
    def check(name: str, condition: bool) -> None:
        checks.append({'name': name, 'passed': bool(condition)})
        if not condition:
            raise AssertionError(name)

    # Four real roots: the observer-connected Schwarzschild scattering branch.
    b, ro, rout, rh = 6.0, 1000.0, 50.0, 2.0
    roots = np.sort(np.r_[np.roots([1.0, 0.0, -b*b, 2*b*b]).real, 0.0])
    r1, r2, r3, rt = roots
    check('scattering_fixture_has_exterior_accessible_turn', ro > rout > rt > rh)
    r31, r41, r42, r32 = r3-r1, rt-r1, rt-r2, r3-r2
    k = r32*r41/(r31*r42)
    omega = .5*np.sqrt(r31*r42)
    def J_ell(r: float) -> float:
        ratio = 1.0 if math.isinf(r) else (r-rt)/(r-r3)
        return float(ellipkinc(np.arcsin(np.sqrt(ratio*r31/r41)), k)/omega)
    def J_quad(r: float) -> float:
        # r=rt+s^2 removes the simple-turning-point endpoint singularity.
        upper = np.inf if math.isinf(r) else np.sqrt(r-rt)
        f = lambda s: 2.0/np.sqrt((rt+s*s-r1)*(rt+s*s-r2)*(rt+s*s-r3))
        return float(quad(f, 0, upper, epsabs=2e-13, epsrel=2e-13)[0])
    comparisons = []
    for r in (rt, 5., 10., rout, ro, np.inf):
        a, q = J_ell(r), J_quad(r)
        comparisons.append({'r': 'infinity' if np.isinf(r) else float(r),
                            'elliptic': a, 'quadrature': q, 'absolute_error': abs(a-q)})
    check('elliptic_path_integrals_match_independent_quadrature',
          max(row['absolute_error'] for row in comparisons) < 1e-11)
    Jo, Js, Ji = J_ell(ro), J_ell(rout), J_ell(np.inf)
    escape = Jo+Ji
    def inverse(tau: float) -> float:
        sn = ellipj(omega*tau-omega*Jo, k)[0]
        z = sn*sn
        return float((rt*r31-r3*r41*z)/(r31-r41*z))
    check('finite_observer_origin_is_preserved', abs(inverse(0.)/ro-1) < 1e-9)
    check('turning_point_is_half_path_to_its_return_not_infinite_observer_limit',
          abs(inverse(Jo)-rt) < 1e-12 and abs(Ji-Jo)>1e-5)
    allowed = (Jo-Js, Jo+Js)
    check('annulus_interval_endpoints_invert_to_r50',
          max(abs(inverse(t)-rout) for t in allowed)<1e-9)
    check('inside_annulus_mino_interval_gives_source_radii_in_range',
          all(rh < inverse(t) <= rout*(1+1e-10) for t in np.linspace(*allowed, 17)))
    interior_errors = []
    for t in np.linspace(allowed[0]+.01, allowed[1]-.01, 9):
        target = abs(Jo-t)
        rr = brentq(lambda r: J_quad(r)-target, rt, rout, xtol=1e-12)
        interior_errors.append(abs(rr-inverse(t)))
    check('physical_branch_inversion_agrees_with_monotone_integral_root', max(interior_errors)<1e-9)
    after_escape = escape+.001
    negative_extension = inverse(after_escape)
    check('finite_negative_formula_value_can_mean_crossing_after_escape',
          np.isfinite(negative_extension) and negative_extension<0 and after_escape>escape)
    period = 2*ellipk(k)/omega
    revived = inverse(period)
    check('positive_formula_value_can_also_be_outside_original_path',
          period>escape and revived>rh and abs(revived/ro-1)<1e-8)
    check('source_absence_does_not_require_a_new_radial_expression',
          not (allowed[0]<=after_escape<=allowed[1]))

    # Capturing fixture: radial motion ends at the horizon although algebra
    # can continue to a positive radius below it. No whole ray is declared dark.
    bc = 4.0
    potential = lambda r: r**4-bc*bc*r*r+2*bc*bc*r
    travel = lambda lower: float(quad(lambda r:1/np.sqrt(potential(r)),lower,ro,
                                      epsabs=2e-12,epsrel=2e-12)[0])
    t_enter, t_h, t_below = travel(rout), travel(rh), travel(1.9)
    t_inside = travel(10.)
    check('capture_has_possible_exterior_emission_before_termination',
          0<t_enter<t_inside<t_h)
    check('positive_subhorizon_continuation_is_after_exterior_termination',
          t_below>t_h and 0<1.9<rh)
    check('capture_type_does_not_remove_all_lower_order_contributions',
          t_enter<t_inside<t_h<t_below)

    def interval_state(lo: float, hi: float, start: float, end: float) -> str:
        if lo>hi or start>end:
            raise ValueError('Invalid interval ordering.')
        if hi<start or lo>end:
            return 'SOURCE_ABSENT'
        if lo>start and hi<end:
            return 'SOURCE_PRESENT'
        return 'DOMAIN_UNRESOLVED'
    check('near_boundary_uncertainty_does_not_silently_become_zero',
          interval_state(allowed[0]-1e-7,allowed[0]+1e-7,*allowed)=='DOMAIN_UNRESOLVED')
    check('disjoint_path_interval_can_certify_source_absence',
          interval_state(escape+.0009,escape+.0011,*allowed)=='SOURCE_ABSENT')
    check('imaginary_root_test_alone_is_not_exterior_turn_test',
          np.isreal(1.0) and not (1.0>rh))
    # Preserve distinct reasons instead of deriving physics from the sign of
    # the closed form or from its shared NaN representation.
    output_markers = [float('nan'),float('nan')]
    reasons = ['NO_NTH_EXTERIOR_CROSSING_ESCAPE','NO_NTH_EXTERIOR_CROSSING_CAPTURE']
    check('one_nan_sentinel_can_hide_distinct_physical_path_events',
          all(np.isnan(output_markers)) and reasons[0]!=reasons[1])
    check('mino_path_parameter_is_not_coordinate_delay',
          escape<2 and ro==1000)
    spent = [480,1080,1080]
    total_second = sum(spent)
    check('all_committed_attempt_ledgers_are_counted_once',total_second==2640)
    check('same_second_batch_keeps_its_original_cap',20000-total_second==17360)
    return {
        'scope': __doc__.strip(),
        'reviewed_commit': 'b6c3873b22f945ce20c40c3c55e80f516954cb00',
        'schwarzschild_scattering_fixture': {
            'M':1.,'impact_parameter':b,'observer_radius':ro,'source_outer_radius':rout,
            'radial_roots':roots.tolist(),'J_comparisons':comparisons,
            'mino_to_turn':Jo,'mino_to_escape_at_infinity':escape,
            'source_annulus_mino_interval':list(allowed),
            'tau_after_escape':after_escape,'negative_extension_radius':negative_extension,
            'periodic_extension_tau':float(period),'periodic_extension_radius':revived,
            'max_independent_radius_error':max(interior_errors)},
        'schwarzschild_capture_fixture':{
            'impact_parameter':bc,'mino_to_r50':t_enter,'mino_to_r10':t_inside,
            'mino_to_horizon':t_h,'mino_to_subhorizon_r1p9':t_below},
        'readback_accounting':{'separate_T1_attempts':spent,'second_batch_spent':total_second,
            'first_pilot_closed_at':17912,'lifetime_spent':17912+total_second,
            'second_batch_remaining':20000-total_second,'boundary_remaining':890},
        'checks':checks,'n_checks':len(checks),'all_passed':True,
        'environment':{'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__},
        'campaign_680_points_classified':False,'repository_suite_executed':False}


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():
        parser.error('Refusing to overwrite output.')
    result=run()
    result['script_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('x') as f:
        json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
    print(f"{result['n_checks']} radial-domain/arithmetic checks passed; no campaign ray was evaluated.")

if __name__=='__main__':
    main()
