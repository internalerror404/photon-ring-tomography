#!/usr/bin/env python3
"""Review 034: cached-response utilities and independent synthetic checks.

No campaign ray, path integral, hull root, or repository test suite is evaluated.
Source numbers below are explicit excerpts, not a full-file local rehash.
The utilities evaluate supplied finite arrays; they do not validate field
interpolation, source-domain coverage, or continuous field envelopes.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import platform
import numpy as np
import scipy
from scipy import sparse


def compare_cached(overlap, fields_hat, fields_ref, detector_area, sigma):
    """Same-support integrated response comparison under single-sky white noise.

    overlap[d,p] is a NONNEGATIVE area, fields are (p,channel), detector_area
    is the full pixel area, and sigma is the fixed noise density. Missing
    support must be handled separately; this routine refuses NaNs.
    """
    O = sparse.csr_matrix(overlap, dtype=float)
    H, R = np.asarray(fields_hat, float), np.asarray(fields_ref, float)
    A = np.asarray(detector_area, float)
    if H.ndim == 1: H = H[:, None]
    if R.ndim == 1: R = R[:, None]
    if H.shape != R.shape or H.ndim != 2 or H.shape[0] != O.shape[1]:
        raise ValueError('Matched support and channel shapes are required')
    if A.shape != (O.shape[0],) or not np.isfinite(A).all() or np.any(A <= 0):
        raise ValueError('Positive finite full detector areas required')
    if not np.isfinite(sigma) or sigma <= 0:
        raise ValueError('Positive finite fixed sigma required')
    if not all(np.isfinite(x).all() for x in (H, R, O.data)) or np.any(O.data < 0):
        raise ValueError('Unknown/nonfinite support is not zero emission')
    if np.any(np.asarray(O.sum(axis=1)).ravel() > A*(1+1e-12)):
        raise ValueError('Within-order integration cells overlap or exceed the detector')
    W = 1/(sigma*np.sqrt(A))
    yr = (O@R)*W[:, None]
    yh = (O@H)*W[:, None]
    absolute = np.linalg.norm(yh-yr, axis=0)
    denom = np.linalg.norm(yr, axis=0)
    rel = np.divide(absolute, denom, out=np.full_like(absolute, np.nan), where=denom>0)
    # Discrete Cauchy-Schwarz on each detector pixel; an upper bound for
    # the supplied piecewise field, not an error certificate for the sky.
    envelope_squared = np.sum(O@((H-R)**2), axis=0)/sigma**2
    return dict(absolute=absolute, relative=rel, reference_norm=denom,
                supplied_field_L2_upper=np.sqrt(envelope_squared),
                reference_response=yr, estimated_response=yh)


def box_radius_about(lower, upper, nominal, whitening):
    """Per-channel and joint Euclidean error bounds about a specified response.

    Bounds are only as valid as the supplied box. This is not a way of
    turning point samples into interval bounds over physical source cells.
    """
    lo, hi, nom = [np.asarray(x, float) for x in (lower, upper, nominal)]
    w = np.asarray(whitening, float)
    if lo.ndim != 2 or lo.shape != hi.shape or lo.shape != nom.shape:
        raise ValueError('Use matched (detector,channel) arrays')
    if w.shape != (lo.shape[0],) or np.any(w < 0):
        raise ValueError('Nonnegative diagonal whitening required')
    if not all(np.isfinite(x).all() for x in (lo,hi,nom,w)) or np.any(lo>hi):
        raise ValueError('Invalid enclosure')
    rad = np.maximum(np.abs(lo-nom), np.abs(hi-nom))*w[:,None]
    return np.linalg.norm(rad, axis=0), float(np.linalg.norm(rad))


def run():
    checks=[]
    def check(name, ok):
        checks.append(dict(name=name, passed=bool(ok)))
        if not ok: raise AssertionError(name)
    # Source excerpt: first development row, fine order 1 index 65785.
    a=dict(Jo=.5200302838631, J50=.5009986917817276,
           escape=1.0410604990353791, err=3.762317256050807e-5)
    b=dict(Jo=.5200302838630997, J50=.5009986917817275,
           escape=1.0410605717591273, err=1.7770814292392525e-13)
    dif={k:abs(a[k]-b[k]) for k in ('Jo','J50','escape')}
    check('near_machine_precision_agreement_applies_to_finite_path_values_in_excerpt',
          dif['Jo']<1e-14 and dif['J50']<1e-14)
    check('escape_quantity_is_not_equal_at_3e_16_in_excerpt', dif['escape']>1e-9)
    check('refinement_difference_and_observed_A_B_difference_are_distinct', a['err']>100*dif['escape'])
    check('authoritative_remaining_balance_854', 20000-18372-774==854)
    coverage=10284/(10284/.6168426103646834)
    check('order2_diagnostic_is_not_full_emitting_node_coverage', coverage<.62)
    g=np.array([.01,1.]); delta=np.array([.0001,.0001])
    global_scaled=delta/g.max(); point_relative=delta/g
    check('global_max_scaled_error_is_not_pointwise_relative_error',
          not np.allclose(global_scaled,point_relative))
    t=np.array([-1000.,-990.]); dt=np.array([.01,.01])
    scaled0=np.max(dt)/np.max(np.abs(t)); scaled1=np.max(dt)/np.max(np.abs(t+989.))
    check('raw_coordinate_time_normalization_depends_on_zero_point',scaled1>50*scaled0)
    phase0=np.sin(2*np.pi*(t+dt)/20)-np.sin(2*np.pi*t/20)
    phase1=np.sin(2*np.pi*((t+989.)-(989.)+dt)/20)-np.sin(2*np.pi*((t+989.)-989.)/20)
    check('composite_temporal_response_can_preserve_common_clock', np.max(abs(phase0-phase1))<1e-12)
    check('g_relative_error_does_not_equal_g_cubed_relative_error', (1.01**3-1)>3*.01)
    # Fine piecewise midpoint field with zero integral oscillation in each pixel.
    n=4096; p=4; x=(np.arange(n)+.5)/n
    O=sparse.csr_matrix((np.full(n,1/n),(np.arange(n)//(n//p),np.arange(n))),shape=(p,n))
    ref=np.ones(n); approx=ref+.1*np.sin(2*np.pi*16*x)
    cmp=compare_cached(O,approx,ref,np.full(p,.25),1.)
    count_fraction=float(np.mean(abs(approx-ref)>5e-4))
    check('large_pointwise_failure_fraction_does_not_lower_bound_detector_error',
          count_fraction>.99 and cmp['relative'][0]<1e-12)
    check('discrete_Cauchy_bound_holds_for_oscillatory_fixture',
          cmp['absolute'][0]<=cmp['supplied_field_L2_upper'][0]+1e-12)
    rng=np.random.default_rng(34)
    test=compare_cached(O,rng.normal(size=(n,3)),rng.normal(size=(n,3)),np.full(p,.25),.7)
    check('discrete_Cauchy_bound_holds_for_all_signed_channels',
          np.all(test['absolute']<=test['supplied_field_L2_upper']+1e-12))
    shift=compare_cached(O,ref+.001,ref,np.full(p,.25),1.)
    check('same_sign_field_error_survives_detector_averaging',abs(shift['relative'][0]-.001)<1e-12)
    caught=False
    try: compare_cached(O,ref*np.nan,ref,np.full(p,.25),1.)
    except ValueError: caught=True
    check('missing_fields_are_refused_not_zero_filled',caught)
    # Equal-valued endpoints do not specify an error radius about any nominal.
    lo=np.zeros((1,1)); hi=np.full((1,1),2.)
    about_zero,_=box_radius_about(lo,hi,lo,np.ones(1))
    about_mid,_=box_radius_about(lo,hi,(lo+hi)/2,np.ones(1))
    check('half_width_is_radius_about_midpoint_not_arbitrary_response',
          about_zero[0]==2 and about_mid[0]==1)
    lo=-np.ones((1,2)); hi=np.ones((1,2)); nom=np.zeros((1,2))
    per,joint=box_radius_about(lo,hi,nom,np.ones(1))
    matrix_one=float(np.linalg.norm((hi-lo)/2,ord=1))
    check('matrix_one_norm_is_not_joint_Euclidean_box_radius',joint>matrix_one)
    check('per_channel_box_radii_remain_one',np.array_equal(per,np.ones(2)))
    # Valid interpolated finite numbers can still draw on invalid-domain stencils.
    corners=np.array([1.,1.,100.,100.]); weights=np.full(4,.25)
    statuses=np.array([True,True,False,False])
    check('finite_only_stencil_is_not_same_emitting_domain_stencil',
          np.isfinite(corners).all() and not statuses.all() and weights@corners>1)
    boundaries=920+9219+42240; interiors=54+4653+44330
    check('reported_expected_cost_components_sum',boundaries+interiors==101416)
    check('model_does_not_show_zero_or_negligible_boundary_cost',boundaries>interiors)
    ratio=444720/101416
    check('fourfold_ratio_is_projection_arithmetic_not_measured_execution',4.38<ratio<4.39)
    return dict(scope=__doc__.strip(), reviewed_commit='d1617963d93713053a4ea374a8c78fcfa013448a',
                source_excerpt={'file':'CHUNK_development_rows_033.json','order':1,'index':65785,
                                'A':a,'B':b,'absolute_differences':dif,
                                'local_method':'explicit connector excerpt; not full file rehash'},
                synthetic_pointwise_vs_response={'fraction_above_5e_4':count_fraction,
                    'detector_relative_error':float(cmp['relative'][0]),
                    'field_L2_response_upper':float(cmp['supplied_field_L2_upper'][0])},
                cost_arithmetic={'boundary_projection':boundaries,'interior_projection':interiors,
                                 'expected_total':101416,'ratio':ratio},
                checks=checks,n_checks=len(checks),all_passed=True,
                environment={'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__},
                campaign_queries=0,repository_suite_run=False)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    if a.output.exists():p.error('Output exists')
    obj=run();obj['script_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open('x') as f:json.dump(obj,f,indent=2,allow_nan=False);f.write('\n')
    print(f"{obj['n_checks']} independent checks passed; zero campaign queries")

if __name__=='__main__':main()
