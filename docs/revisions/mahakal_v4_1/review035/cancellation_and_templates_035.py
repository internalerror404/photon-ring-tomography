#!/usr/bin/env python3
"""Review 035: exact cached-residual algebra and harmonic diagnostic templates.

No campaign maps, geodesics, path quadratures, target operators, or repository
suite are run. Bounds describe supplied finite arrays, not an unknown sky.
The 40-to-5 template identity applies ONLY to the declared diagnostic fields.
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


def residual_hierarchy(overlap, whitening, delta, reference=None):
    """E_c <= A_c <= T_c <= U, for nonnegative overlap and diagonal W.

    E: actual signed detector residual norm, per channel.
    A: sum magnitudes inside each detector first, then detector Euclidean norm.
    T: sum individual column-vector norms, per channel.
    U: old aggregate, taking max channel magnitude separately at every column.
    None of these bounds describes error relative to unsampled continuum truth.
    """
    O = sparse.csr_matrix(overlap, dtype=float)
    w = np.asarray(whitening, dtype=float)
    d = np.asarray(delta, dtype=float)
    if d.ndim == 1:
        d = d[:, None]
    if d.ndim != 2 or d.shape[0] != O.shape[1] or d.shape[1] == 0:
        raise ValueError('delta must have shape (supported nodes, channels)')
    if w.shape != (O.shape[0],) or np.any(w < 0):
        raise ValueError('nonnegative diagonal whitening required')
    if not all(np.isfinite(x).all() for x in (O.data, w, d)) or np.any(O.data < 0):
        raise ValueError('nonfinite or invalid contribution is not zero emission')
    K = O.multiply(w[:, None]).tocsr()
    r = np.asarray(K @ d)
    absolute = np.asarray(K @ np.abs(d))
    cn = np.sqrt(np.asarray(K.multiply(K).sum(axis=0)).ravel())
    E = np.linalg.norm(r, axis=0)
    A = np.linalg.norm(absolute, axis=0)
    T = cn @ np.abs(d)
    U = float(cn @ np.max(np.abs(d), axis=1))
    result = dict(E=E, A=A, T=T, U=U, residual=r, absolute_rows=absolute)
    if reference is not None:
        ref = np.asarray(reference, dtype=float)
        if ref.ndim == 1:
            ref = ref[:, None]
        if ref.shape != d.shape or not np.isfinite(ref).all():
            raise ValueError('reference must match supported nodes and channels')
        norms = np.linalg.norm(K @ ref, axis=0)
        result['reference_norm'] = norms
        result['relative_E'] = np.divide(E, norms, out=np.full(E.shape, np.nan), where=norms > 0)
        result['zero_reference_channels'] = norms == 0
    return result


def harmonic_templates(redshift, delay):
    """[g^3, Re H20, Im H20, Re H40, Im H40], H_T=g^3 exp(-i*2pi*delay/T).

    Positive finite redshift is required by this fixture. A production caller
    must retain the project's explicit redshift/sign convention and masks.
    """
    g, d = np.broadcast_arrays(np.asarray(redshift, float), np.asarray(delay, float))
    if not np.isfinite(g).all() or not np.isfinite(d).all() or np.any(g < 0):
        raise ValueError('finite valid-event tuples required; no missing-value filling')
    amplitude = g**3
    h20 = amplitude * np.exp(-2j * np.pi * d / 20)
    h40 = amplitude * np.exp(-2j * np.pi * d / 40)
    return np.stack((amplitude, h20.real, h20.imag, h40.real, h40.imag), axis=-1)


def expand_templates(templates, times):
    """Return original five transferred channels per observer time, flattened.

    Linear in the templates, so expansion commutes with a fixed linear detector.
    """
    h = np.asarray(templates, float)
    ts = np.asarray(times, float)
    if h.ndim != 2 or h.shape[1] != 5 or ts.ndim != 1 or ts.size == 0:
        raise ValueError('templates (locations,5) and nonempty times required')
    if not np.isfinite(h).all() or not np.isfinite(ts).all():
        raise ValueError('nonfinite input')
    out = []
    for t in ts:
        c20, s20 = np.cos(2*np.pi*t/20), np.sin(2*np.pi*t/20)
        c40, s40 = np.cos(2*np.pi*t/40), np.sin(2*np.pi*t/40)
        out.extend((h[:,0], c20*h[:,1]-s20*h[:,2], s20*h[:,1]+c20*h[:,2],
                    c40*h[:,3]-s40*h[:,4], s40*h[:,3]+c40*h[:,4]))
    return np.stack(out, axis=1)


def conditional_total_bound(estimated_response_error, group_remainder_radii,
                            fine_reference_radius, omitted_support_radius):
    """Norm(delta_hat)+sum(eps_group)+eps_fine+eps_missing, GIVEN valid radii.

    This is interval/triangle propagation, not inference of the input bounds.
    A known core-fine residual is not a supplied bound on the fine sky error.
    """
    d = np.asarray(estimated_response_error, float)
    r = np.asarray(group_remainder_radii, float)
    extra = np.array([fine_reference_radius, omitted_support_radius], float)
    if not all(np.isfinite(x).all() for x in (d,r,extra)) or np.any(r<0) or np.any(extra<0):
        raise ValueError('missing/negative uncertainty is not zero uncertainty')
    return float(np.linalg.norm(d) + np.sum(r) + np.sum(extra))


def run_checks():
    checks = []
    def ck(name, passed):
        checks.append(dict(name=name, passed=bool(passed)))
        if not passed:
            raise AssertionError(name)
    rng = np.random.default_rng(35)
    O = sparse.csr_matrix(rng.uniform(size=(19,61))*(rng.uniform(size=(19,61))>.8))
    w = rng.uniform(.3,2,19)
    delta = rng.normal(size=(61,9))
    h = residual_hierarchy(O,w,delta)
    ck('signed_sum_bounded_by_pixel_absolute_sum', np.all(h['E']<=h['A']+1e-12))
    ck('pixel_absolute_sum_bounded_by_column_triangle', np.all(h['A']<=h['T']+1e-12))
    ck('per_channel_triangle_bounded_by_channel_max_sum', np.all(h['T']<=h['U']+1e-12))
    # All values positive: no sign cancellation anywhere, yet old sum/norm is 18.
    orth = residual_hierarchy(sparse.eye(324),np.ones(324),np.ones(324))
    ck('orthogonal_detector_rows_create_large_gap_without_sign_cancellation',
       orth['T'][0]/orth['E'][0]==18 and orth['A'][0]==orth['E'][0])
    switch = residual_hierarchy([[1,1]],[1],np.eye(2))
    ck('columnwise_channel_max_creates_additional_gap', switch['U']==2 and np.max(switch['T'])==1)
    cancel = residual_hierarchy([[1,1]],[1],[1,-.99])
    ck('same_pixel_opposite_signs_create_real_cancellation', cancel['A'][0]>100*cancel['E'][0])
    refined = residual_hierarchy([[1,1]],[1],[0,-.99])
    ck('oracle_removal_of_largest_error_can_break_cancellation',refined['E'][0]>90*cancel['E'][0])
    # Same-error patch assumptions are needed to call a tail a post-refinement bound.
    assumed_tail = .01
    actual_after_change = .2
    ck('refinement_does_not_promise_zero_selected_error',actual_after_change>assumed_tail)
    aggregate = residual_hierarchy([[1]],[1],[[.01,.001]],[[100,1]])
    ck('max_reference_denominator_can_hide_failed_channel',
       np.max(aggregate['E'])<5e-4*np.max(aggregate['reference_norm'])
       and aggregate['relative_E'][1]>5e-4)
    r0 = residual_hierarchy([[1]],[1],[[0]],[[0]])
    ck('zero_reference_is_reported_not_silent_relative_pass',r0['zero_reference_channels'][0] and np.isnan(r0['relative_E'][0]))
    missing_rejected=False
    try: residual_hierarchy([[1]],[1],[[np.nan]])
    except ValueError: missing_rejected=True
    ck('nonfinite_cached_difference_rejected',missing_rejected)
    # Common bias is invisible to two approximation difference.
    physical = 1.; coarse=1.1001; fine=1.1
    ck('small_pair_difference_cannot_certify_reference_accuracy', abs(coarse-fine)<.001 and abs(coarse-physical)>.1)
    estimated=np.array([.01,-.02])
    bound=conditional_total_bound(estimated,[.001,.002],.004,.005)
    perturb=np.array([.003,0])+np.array([0,.004])+np.array([.005,0])
    ck('signed_estimate_plus_valid_remainder_bounds_total',np.linalg.norm(estimated+perturb)<=bound)
    missing_rejected=False
    try: conditional_total_bound(estimated,[.001],np.nan,.01)
    except ValueError: missing_rejected=True
    ck('unknown_fine_reference_error_is_not_zero',missing_rejected)
    missing_rejected=False
    try: conditional_total_bound(estimated,[.001],.01,np.nan)
    except ValueError: missing_rejected=True
    ck('unknown_omitted_support_error_is_not_zero',missing_rejected)
    # Exact algebraic compression of only the declared harmonic diagnostics.
    g=rng.uniform(.2,1.4,61); delay=rng.uniform(0,140,61); times=np.linspace(0,20,8)
    H=harmonic_templates(g,delay)
    F=expand_templates(H,times)
    direct=[]
    for t in times:
        ph=t-delay; a=g**3
        direct.extend((a,a*np.cos(2*np.pi*ph/20),a*np.sin(2*np.pi*ph/20),
                       a*np.cos(2*np.pi*ph/40),a*np.sin(2*np.pi*ph/40)))
    direct=np.stack(direct,axis=1)
    err=float(np.max(np.abs(F-direct)))
    ck('five_real_templates_reconstruct_forty_transferred_channels',F.shape==(61,40) and err<1e-12)
    operator_err=float(np.max(np.abs(O@F-expand_templates(O@H,times))))
    ck('template_expansion_commutes_with_fixed_detector_map',operator_err<1e-12)
    ck('static_g3_channel_is_reused_not_new_information',np.all(F[:,0]==F[:,5]))
    # Lift and interpolate do not generally commute: neither order universally wins.
    G=np.array([1.,3.]); mixed_primitive=np.mean(G)**3; mixed_lift=np.mean(G**3)
    ck('redshift_cubing_and_interpolation_do_not_commute',mixed_primitive==8 and mixed_lift==14)
    endpoints=harmonic_templates(np.ones(2),np.array([0.,20.]))
    direct_lift=np.mean(endpoints,axis=0)
    primitive_lift=harmonic_templates(np.ones(1),np.array([10.]))[0]
    ck('phase_interpolation_can_alias_even_with_matching_endpoint_phases',abs(direct_lift[1]-primitive_lift[1])>1.9)
    ck('one_composite_interpolant_is_not_guaranteed_better',abs(primitive_lift[1]+1)<1e-12 and abs(direct_lift[1]+1)>1)
    # High radius variation says nothing by itself about whether a linear field is exactly represented.
    corners=np.array([1.,2.]); mean=corners.mean(); span=np.ptp(corners)/mean
    x=np.array([.2,.6]); truth=1+x; interp=(1-x)*corners[0]+x*corners[1]
    ck('radius_span_heuristic_is_not_branch_or_accuracy_certificate',span>.25 and np.max(abs(truth-interp))<1e-15)
    reported=np.array([.00959392601984124,.0427435147361119,.511602956726496])
    ck('reported_signed_residuals_already_exceed_budget',np.all(reported/5e-4>19))
    ck('unchanged_second_batch_balance',20000-19146==854)
    # Equal-input control cannot detect a shared wrong matrix.
    wrong=np.array([[2.,0.],[0.,3.]])
    x=np.array([1.,2.])
    ck('identical_screen_control_does_not_certify_absolute_operator',np.all(wrong@x-wrong@x==0) and np.linalg.norm(wrong@x-x)>1)
    return dict(
        scope=__doc__.strip(), reviewed_commit='67f3523c33d21468ad962a7fe19cd806ad76e53b',
        checks=checks,n_checks=len(checks),all_passed=True,
        hierarchy_fixture={k:(float(v) if np.ndim(v)==0 else v.tolist()) for k,v in h.items() if k in ('E','A','T','U')},
        no_cancellation_fixture=dict(detector_rows=324,column_triangle_over_error=float(orth['T'][0]/orth['E'][0]),pixel_absolute_over_error=float(orth['A'][0]/orth['E'][0])),
        removal_fixture=dict(original_error=float(cancel['E'][0]),after_perfect_removal_of_one_contribution=float(refined['E'][0])),
        harmonic_identity=dict(max_point_error=err,max_detector_error=operator_err,real_templates=5,original_transferred_columns=40,physical_ray_savings_measured=False),
        reported_034_numbers_used_as_arithmetic_inputs=dict(max_signed_relative=reported.tolist(),ratio_to_5e_4=(reported/5e-4).tolist(),not_independently_recomputed_from_campaign_arrays=True),
        environment=dict(python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__),
        campaign_queries=0,repository_suite_executed=False)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args()
    if args.output.exists():ap.error('Output exists; select a new path')
    result=run_checks();result['script_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('x') as f:json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
    print(f"{result['n_checks']} synthetic checks passed; no campaign query executed")

if __name__=='__main__':main()
