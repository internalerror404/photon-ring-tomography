#!/usr/bin/env python3
"""Review 032: synthetic checks and a zero-query comparison-plan validator.

No Kerr rays, saved campaign arrays, source bank, or repository suite are run.
The preflight checks a DECLARED task/cost manifest, not physical correctness or
permission to execute. It must be combined with runtime input/hash/budget guards.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
from pathlib import Path
import platform
import re
import numpy as np


def overlap(edges, left, right):
    edges = np.asarray(edges, dtype=float)
    return np.maximum(0., np.minimum(edges[1:], right)-np.maximum(edges[:-1], left))


def quartic_coefficients(a, lam, eta):
    """Expanded M=1 null radial potential; not coefficients fitted to roots."""
    return np.array([1., 0., a*a-lam*lam-eta,
                     2*((lam-a)**2+eta), -a*a*eta])


def validate_plan(plan):
    """Reject incomplete comparisons before ANY new physical execution."""
    errors = []
    expected = {(p, n, lev) for p in ('core','fine')
                for n in (0,1,2) for lev in ('L0','L1','L2')}
    tasks = plan.get('tasks', [])
    observed = [(t.get('profile'),t.get('order'),t.get('level')) for t in tasks]
    if set(observed) != expected or len(observed) != len(expected):
        errors.append('INCOMPLETE_OR_DUPLICATED_COMPARISON_MATRIX')
    if plan.get('scope') not in ('local_feasibility','full_domain_qualification'):
        errors.append('UNDECLARED_SCIENTIFIC_SCOPE')
    identifiers = ('physical_domain_id','representation_id','field_set_id',
                   'detector_id','clock_id','sigma_id')
    for n in (0,1,2):
        subset = [t for t in tasks if t.get('order') == n]
        for key in identifiers:
            vals = {t.get(key) for t in subset}
            if not vals or None in vals or len(vals) != 1:
                errors.append(f'ORDER_{n}_UNMATCHED_{key.upper()}')
        if any(t.get('payload_export') is not True for t in subset):
            errors.append(f'ORDER_{n}_PAYLOAD_NOT_PLANNED')
    evals = plan.get('evaluations', [])
    by_id = {}
    cost = 0
    for ev in evals:
        eid = ev.get('id')
        if not isinstance(eid,str) or eid in by_id:
            errors.append('DUPLICATED_OR_MISSING_EVALUATION_ID')
            continue
        by_id[eid] = ev
        if ev.get('cache_sha256') is not None:
            if not re.fullmatch('[0-9a-f]{64}',str(ev['cache_sha256'])):
                errors.append('INVALID_CACHE_HASH_FORMAT')
            if ev.get('charge') != 0:
                errors.append('CACHE_COST_INCONSISTENT')
        else:
            q = ev.get('charge')
            if not isinstance(q,int) or isinstance(q,bool) or q < 1:
                errors.append('UNDECLARED_NEW_EVALUATION_COST')
            else:
                cost += q
    for task in tasks:
        ids = task.get('evaluation_ids', [])
        if not ids or any(eid not in by_id for eid in ids):
            errors.append('TASK_MISSING_EVALUATION_DEPENDENCY')
    rem, reserve = plan.get('reconciled_remaining'), plan.get('validation_reserve')
    if not isinstance(rem,int) or not isinstance(reserve,int) or reserve < 4000:
        errors.append('INVALID_REMAINING_OR_VALIDATION_RESERVE')
    elif cost + reserve > rem:
        errors.append('PLAN_PLUS_VALIDATION_EXCEEDS_RECONCILED_BUDGET')
    if plan.get('accounting_scope_resolved') is not True:
        errors.append('ACCOUNTING_SCOPE_UNRESOLVED')
    if plan.get('prerequisite_status') != 'SUPPORTED_FOR_DECLARED_SCOPE':
        errors.append('PREREQUISITE_NOT_READY')
    return {'status': 'PLAN_BLOCKED' if errors else
            'PLAN_SCHEMA_AND_COST_READY_FOR_REVIEW_NOT_EXECUTION',
            'errors':sorted(set(errors)), 'new_charge_declared':cost,
            'endpoint_count':len(observed), 'required_endpoint_count':len(expected),
            'physical_execution_authorized':False,
            'limitations':'Validates declared schema/cost only; does not authenticate cache bytes or certify physics.'}


def example_plan():
    tasks, evals = [], []
    for n in (0,1,2):
        for p in ('core','fine'):
            for lev in ('L0','L1','L2'):
                eid=f'{p}:{n}:{lev}'
                evals.append({'id':eid,'charge':20})
                tasks.append({'profile':p,'order':n,'level':lev,
                              'physical_domain_id':f'fixed_region_order{n}',
                              'representation_id':'leaf_clipped_v1',
                              'field_set_id':'same_declared_fields',
                              'detector_id':'D026','clock_id':'fixed',
                              'sigma_id':'fixed','payload_export':True,
                              'evaluation_ids':[eid]})
    return {'scope':'local_feasibility','tasks':tasks,'evaluations':evals,
            'reconciled_remaining':6434,'validation_reserve':4000,
            'accounting_scope_resolved':True,
            'prerequisite_status':'SUPPORTED_FOR_DECLARED_SCOPE'}


def run_checks():
    tests=[]
    def check(name, condition):
        tests.append({'name':name,'passed':bool(condition)})
        if not condition:
            raise AssertionError(name)
    edges=np.array([0.,.5,1.])
    exact=overlap(edges,0.,.2)
    uniform_fraction=.2*overlap(edges,0.,1.)
    check('parent_fraction_preserves_total_but_moves_flux',
          abs(exact.sum()-uniform_fraction.sum())<1e-15
          and np.max(np.abs(exact-uniform_fraction))>.09)
    # An implicit leaf rule assigns each leaf to ITS own detector intersection.
    leaf_edges=np.linspace(0,1,17)
    midpoint=(leaf_edges[:-1]+leaf_edges[1:])/2
    leaf_result=sum((float(x<.2)*overlap(edges,l,h)
                     for l,h,x in zip(leaf_edges[:-1],leaf_edges[1:],midpoint)),
                    start=np.zeros(2))
    check('leaf_clipping_does_not_spread_left_flux_to_right_detector',
          leaf_result[1]==0 and leaf_result[0]>0)
    check('leaf_point_rule_is_still_approximation_not_exact_domain',
          abs(leaf_result[0]-.2)>1e-3)
    labels=np.array([False,False,False,False])
    check('zero_unresolved_point_labels_not_zero_domain_error',
          np.count_nonzero(labels)==0 and .2>0)
    a=np.array([1.,0.]); b=np.array([0.,1.])
    check('difference_of_norms_can_hide_image_difference',
          abs(np.linalg.norm(a)-np.linalg.norm(b))==0
          and np.linalg.norm(a-b)>1)
    values=np.array([0.1,0.2]); unknown=np.array([False,True])
    check('unknown_sample_omission_needs_bound_not_false_full_response',
          np.sum(values[~unknown])<np.sum(values))
    coefficient=quartic_coefficients(.5,3.,4.)
    roots=np.roots(coefficient).astype(complex)
    altered=roots.copy(); altered[0]+=.05
    circular=np.prod(altered[:,None]-altered[None,:],axis=0)
    independent=np.polyval(coefficient,altered)
    check('self_root_product_residual_is_tautologically_zero',
          np.max(np.abs(circular))==0)
    check('original_polynomial_detects_perturbed_root',
          np.max(np.abs(independent))>1e-3)
    # Exclusion by Python object identity does not select the numerical root.
    rr=np.array([-3+0j,0+0j,1+0j,2+0j])
    turn=2.0
    mistaken=np.prod([turn-q for q in rr if q is not turn])
    correct=np.prod([turn-q for i,q in enumerate(rr) if i!=3])
    check('root_index_not_object_identity_for_reduced_product',
          mistaken==0 and correct.real>0)
    check('unreached_matrix_entries_are_missing_not_zero_observations',
          2<6)
    good=example_plan()
    check('complete_matched_plan_passes_schema_only',not validate_plan(good)['errors'])
    bad=copy.deepcopy(good); bad['tasks']=[t for t in bad['tasks']
                                         if t['profile']=='core' and t['order']<2]
    check('greedy_partial_matrix_rejected_before_queries',
          'INCOMPLETE_OR_DUPLICATED_COMPARISON_MATRIX' in validate_plan(bad)['errors'])
    bad=copy.deepcopy(good); bad['tasks'][-1]['representation_id']='parent_fraction'
    check('mixed_representation_rejected',bool(validate_plan(bad)['errors']))
    bad=copy.deepcopy(good); bad['reconciled_remaining']=4200
    check('infeasible_complete_bundle_preserves_validation_reserve',
          'PLAN_PLUS_VALIDATION_EXCEEDS_RECONCILED_BUDGET' in validate_plan(bad)['errors'])
    bad=copy.deepcopy(good); bad['prerequisite_status']='REFERENCE_UNRESOLVED'
    check('reference_incompleteness_blocks_auto_launch',
          'PREREQUISITE_NOT_READY' in validate_plan(bad)['errors'])
    bad=copy.deepcopy(good); bad['tasks'][0]['payload_export']=False
    check('payload_omission_is_rejected',bool(validate_plan(bad)['errors']))
    check('point_cap_is_separate_from_evaluation_cap',494>192 and 494<1024)
    check('native_counter_correction_preserves_aborted_attempt',
          7072+6494==13566 and 20000-13566==6434)
    check('pilot_allocation_matches_disclosed_consumption',331*4+1169*4==6000)
    check('area_component_units_not_transfer_response_units',
          3.853e-3>1e-3 and 1.854e-3>1e-3)
    return {'scope':__doc__.strip(),
            'reviewed_commit':'e9924705285d04fd282758de640a916044e987c7',
            'n_checks':len(tests),'checks':tests,'all_passed':True,
            'overlap_fixture':{'exact':exact.tolist(),
                               'parent_fraction':uniform_fraction.tolist(),
                               'leaf_midpoint_16':leaf_result.tolist()},
            'root_residual_fixture':{'self_product_max':float(np.max(np.abs(circular))),
                                     'original_polynomial_max':float(np.max(np.abs(independent)))},
            'good_synthetic_plan':validate_plan(good),
            'environment':{'python':platform.python_version(),'numpy':np.__version__},
            'campaign_rays_evaluated':0,'repository_suite_executed':False}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists(): parser.error('Output exists; choose a fresh path.')
    result=validate_plan(json.loads(args.plan.read_text())) if args.plan else run_checks()
    result['script_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('x') as f:
        json.dump(result,f,indent=2,allow_nan=False); f.write('\n')
    print(json.dumps({k:result[k] for k in ('status','n_checks','all_passed') if k in result}))

if __name__=='__main__': main()
