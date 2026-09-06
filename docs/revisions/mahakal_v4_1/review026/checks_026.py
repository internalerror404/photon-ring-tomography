#!/usr/bin/env python3
"""Review-026 arithmetic and independent finite-volume fixtures.
Not a Kerr run, raw-HDF5 validation, or execution of the repository test suite.
The rational grid inputs and candidate singular values are transcribed from
repository records at 5d56f7e9ef30087fee2eef6ef8c4c6306615adcb and review 024.
Usage: python checks_026.py --output NEW_PATH.json
"""
from __future__ import annotations
import argparse
from fractions import Fraction as Q
import hashlib
import json
import math
from pathlib import Path
import platform
import numpy as np


def overlaps(src: np.ndarray, det: np.ndarray) -> np.ndarray:
    if np.any(np.diff(src) <= 0) or np.any(np.diff(det) <= 0):
        raise ValueError('Edges must be strictly increasing.')
    return np.maximum(0., np.minimum(det[1:, None], src[None, 1:])
                      - np.maximum(det[:-1, None], src[None, :-1]))


def information(src: np.ndarray, f: np.ndarray, det: np.ndarray) -> tuple:
    O = overlaps(src, det)
    y = O @ f
    return float(np.sum(y*y/np.diff(det))), y


def profiled(B: np.ndarray, N: np.ndarray) -> np.ndarray:
    U = np.linalg.qr(N, mode='reduced')[0]
    R = B - U @ (U.T @ B)
    return R.T @ R


def run() -> dict:
    results, checks = {}, []
    def check(name: str, ok: bool):
        checks.append({'name': name, 'passed': bool(ok)})
        if not ok:
            raise AssertionError(name)
    pitch = [Q(50,125), Q(20,249), Q(14,699)]
    den = math.lcm(*(p.denominator for p in pitch))
    gcd = Q(math.gcd(*(p.numerator*(den//p.denominator) for p in pitch)), den)
    check('rational_pitches_have_common_divisor', all((p/gcd).denominator == 1 for p in pitch))
    results['rational_lattice'] = {
        'pitches_M': [str(p) for p in pitch],
        'common_pitch_divisor_M': str(gcd),
        'integer_pitch_multiples': [int(p/gcd) for p in pitch],
        'origin_alignment_requires_separate_check': True,
        'uniform_cells_50_by_50_at_common_pitch': float((Q(50)/gcd)**2),
        'rectilinear_overlay_axis_edge_count_upper_bound': 127+251+701,
        'overlay_cell_count_before_padding_upper_bound': (127+251+701-1)**2,
        'overlay_is_integration_mesh_not_detector': True}
    rows = [('coarse',0,64,50,Q(4,5)), ('coarse',1,126,20,Q(4,25)),
            ('coarse',2,350,14,Q(1,25)), ('core',0,126,50,Q(2,5)),
            ('core',1,250,20,Q(2,25)), ('core',2,700,14,Q(1,50)),
            ('fine',0,250,50,Q(1,5)), ('fine',1,500,20,Q(1,25)),
            ('fine',2,1200,12,Q(1,100))]
    factors = {(p,n): (Q(span,count-1)/dx)**2 for p,n,count,span,dx in rows}
    results['reported_square_grid_area_factors'] = [
        {'profile':p, 'order':n, 'factor_exact':str(factors[p,n]),
         'factor':float(factors[p,n])} for p,n,*_ in rows]
    check('exact_nominal_spacing_matches_two_of_nine', sum(f == 1 for f in factors.values()) == 2)
    areas = [Q('2554.88'),Q('2495.52'),Q('2465.40')]
    corrected = [a*factors[p,0] for a,p in zip(areas,['coarse','core','fine'])]
    results['reported_order0_area_only_correction'] = {
        'legacy_area_M2':[float(a) for a in areas],
        'spacing_only_area_M2':[float(a) for a in corrected],
        'last_pair_relative_to_fine':float(abs(corrected[-1]-corrected[-2])/corrected[-1]),
        'boundary_clipping_or_mask_correction_applied':False,
        'inference':'These three levels do not establish asymptotic nonconvergence.'}
    src=np.array([0.,.5,1.]); f=np.array([1.,3.]); det=np.array([0.,.3,.6,.9,1.])
    I,y=information(src,f,det); I_full=float(np.dot(np.diff(src),f*f))
    check('unaligned_exact_overlap_conserves_flux', abs(y.sum()-2.) < 1e-14)
    check('unaligned_detector_has_legitimate_information_loss', 0 < I < I_full)
    exact,_=information(src,f,np.array([0.,.25,.5,.75,1.]))
    check('aligned_detector_reaches_piecewise_field_norm', abs(exact-I_full)<1e-14)
    error2=0.
    O=overlaps(src,det)
    for d in range(len(det)-1):
        error2 += float(np.dot(O[d], (f-y[d]/np.diff(det)[d])**2))
    check('projection_variance_identity', abs(I_full-I-error2)<1e-14)
    worst=0.
    for k in [2,4,8,16]:
        refined=np.unique(np.concatenate([np.linspace(a,b,k+1) for a,b in zip(src[:-1],src[1:])]))
        _, yr=information(refined,np.repeat(f,k),det)
        worst=max(worst,float(np.max(np.abs(yr-y))))
    check('same_detector_same_field_subdivision_is_invariant', worst<1e-12)
    results['projection_fixture']={'ray_field_norm_squared':I_full,'detector_norm_squared':I,
        'unresolved_within_cell_variance':error2,'fixed_detector_split_max_abs':worst}
    src2=np.array([0.,.2,1.]); O=overlaps(src2,det); a=np.diff(src2)
    L=O/a[None,:]
    C1=O@np.diag(1/a)@O.T
    C2=L@np.diag(a)@L.T
    bad=O@np.diag(a)@O.T
    check('brightness_and_flux_covariance_conventions_agree', np.max(np.abs(C1-C2))<1e-14)
    check('area_matrix_is_not_flux_fraction_matrix', np.max(np.abs(C1-bad))>.01)
    results['covariance_fixture']={'correct_max_abs':float(np.max(np.abs(C1-C2))),
        'incorrect_area_times_flux_covariance_error':float(np.max(np.abs(C1-bad)))}
    nodes=np.linspace(0.,1.,5)
    edges=np.r_[0.,.5*(nodes[:-1]+nodes[1:]),1.]
    check('node_dual_boundary_weights_sum_to_domain', abs(np.diff(edges).sum()-1.)<1e-15)
    check('unclipped_equal_node_cells_enlarge_domain', abs(len(nodes)*.25-1.)>.2)
    # Equal total mask area can coexist with different detector response.
    _, ya=information(src,np.array([1.,0.]),src)
    _, yb=information(src,np.array([0.,1.]),src)
    check('equal_area_does_not_imply_mask_or_response_convergence', ya.sum()==yb.sum() and np.linalg.norm(ya-yb)>.5)
    lo,hi=1.,float(factors['core',1]); minimum=0.
    for seed in range(32):
        rng=np.random.default_rng(seed)
        B=rng.normal(size=(36,4)); N=rng.normal(size=(36,7))
        d=np.repeat([1.,hi,float(factors['core',2])],12)
        F0=profiled(B,N); F1=profiled(np.sqrt(d)[:,None]*B,np.sqrt(d)[:,None]*N)
        minimum=min(minimum,float(np.linalg.eigvalsh(F1-lo*F0).min()),float(np.linalg.eigvalsh(hi*F0-F1).min()))
    check('profiled_fisher_inherits_weight_bounds_32_fixtures', minimum>=-1e-10)
    s=np.array([1.4371649013558634,1.3458732686433825,.8062804378838909])
    upper=s*np.sqrt(hi)
    check('isolated_core_uniform_weight_change_keeps_two_directions', s[1]>1 and upper[2]<1)
    results['isolated_core_weight_bound']={'area_factor_min':lo,'area_factor_max':hi,
        'conditional_singular_value_lower':s.tolist(),'conditional_singular_value_upper':upper.tolist(),
        'conditional_trace_interval':[7.198318097661488,7.198318097661488*hi],
        'fixture_min_bound_eigenvalue':minimum,
        'conditions':['same rays and validity masks','same source metric and nuisance family',
            'same sigma; direct core multiplier is 1','uniform positive per-order spacing correction only'],
        'does_not_cover':['boundary clipping','ray refinement','mask changes','new detector','estimator error']}
    # Fixed detector, improved ray quadrature for a continuous test function.
    exact_y=(det[1:]**3-det[:-1]**3)/3
    seq=[]
    for n in [20,40,80,160]:
        e=np.linspace(0.,1.,n+1); fv=((e[1:]+e[:-1])/2)**2
        _, val=information(e,fv,det)
        seq.append(float(np.linalg.norm(val-exact_y)/np.linalg.norm(exact_y)))
    check('fixed_detector_ray_quadrature_converges_for_smooth_fixture', all(a>b for a,b in zip(seq[:-1],seq[1:])) and seq[-1]<1e-3)
    results['fixed_detector_ray_refinement_fixture']={'ray_counts':[20,40,80,160],'relative_response_error':seq}
    results.update(scope=__doc__.strip(),reviewed_commit='5d56f7e9ef30087fee2eef6ef8c4c6306615adcb',
        checks=checks,n_checks=len(checks),all_passed=all(c['passed'] for c in checks),
        environment={'python':platform.python_version(),'numpy':np.__version__},
        physical_operator_or_repository_suite_rerun=False)
    return results


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():
        parser.error('Refusing to overwrite existing output.')
    result=run()
    result['script_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('x') as fh:
        json.dump(result,fh,indent=2,allow_nan=False); fh.write('\n')
    print(f"{result['n_checks']} independent checks passed; no physical operator was run.")

if __name__=='__main__':
    main()
