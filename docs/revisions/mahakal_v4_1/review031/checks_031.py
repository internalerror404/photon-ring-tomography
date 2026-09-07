#!/usr/bin/env python3
"""Review 031 synthetic quadrature, fail-closed and accounting checks.
Not a run of the repository evaluator, its 680 rays, or its 597-test suite.
The endpoint-peaked integral below has an exact analytic answer. Source-level
control-flow fixtures reproduce only the quoted Boolean logic, not full rays.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import platform
import numpy as np
import scipy
from scipy.special import roots_legendre


def integrate_peak(delta: float, panels: int) -> float:
    x, w = roots_legendre(64)
    edges = np.linspace(0., 1., panels+1)**3
    lengths = np.diff(edges)
    points = edges[:-1, None] + .5*lengths[:, None]*(x+1)
    return float(np.sum(.5*lengths[:, None]*w/np.sqrt(points+delta)))


def unguarded_capture(s: float, horizon: float, source_edge: float) -> str:
    # Minimal reproduction of the final comparator's capture fall-through.
    if s >= horizon:
        return 'NO_CROSSING_CAPTURE'
    return 'OUTSIDE_ANNULUS' if s < source_edge else 'VALID'


def checked_capture(s: float, horizon: float, source_edge: float,
                    horizon_error: float, edge_error: float) -> str:
    vals = np.array([s, horizon, source_edge, horizon_error, edge_error])
    if not np.isfinite(vals).all() or s < 0 or min(horizon_error, edge_error) < 0:
        return 'UNRESOLVED'
    if source_edge < 0 or horizon <= source_edge:
        return 'UNRESOLVED'
    if abs(s-horizon) <= horizon_error or abs(s-source_edge) <= edge_error:
        return 'UNRESOLVED'
    if s > horizon:
        return 'NO_CROSSING_CAPTURE'
    return 'OUTSIDE_ANNULUS' if s < source_edge else 'VALID'


def run() -> dict:
    checks = []
    def require(name: str, condition: bool) -> None:
        checks.append({'name':name, 'passed':bool(condition)})
        if not condition:
            raise AssertionError(name)

    delta = 1e-8
    exact = 2/(np.sqrt(1+delta)+np.sqrt(delta))
    x,w = roots_legendre(64)
    global_rule = float(.5*np.dot(w, 1/np.sqrt(.5*(x+1)+delta)))
    panel_counts = [16,32,64,128]
    panel_results = [integrate_peak(delta,n) for n in panel_counts]
    errors = [abs(v-exact) for v in panel_results]
    require('global_rule_can_miss_resolved_endpoint_peak',abs(global_rule-exact)>1e-3)
    require('graded_panels_converge_against_exact_reference',all(a>b for a,b in zip(errors[:-1],errors[1:])))
    require('final_panel_error_against_exact_answer_is_small',errors[-1]<1e-12)
    harder_delta = 1e-12
    harder_exact = 2/(np.sqrt(1+harder_delta)+np.sqrt(harder_delta))
    harder_value = integrate_peak(harder_delta,64)
    require('fixed_panel_count_is_not_universal_error_certificate',abs(harder_value-harder_exact)>1e-6)

    require('nan_comparator_fallthrough_can_invent_valid_label',unguarded_capture(.5,np.nan,np.nan)=='VALID')
    require('finite_guards_prevent_nan_fallthrough',checked_capture(.5,np.nan,np.nan,0,0)=='UNRESOLVED')
    require('horizon_error_overlap_is_not_physical_absence',checked_capture(.5001,.5,.1,.001,.001)=='UNRESOLVED')
    require('well_separated_absence_is_classified',checked_capture(.8,.5,.1,.001,.001)=='NO_CROSSING_CAPTURE')
    require('well_separated_emission_is_classified',checked_capture(.3,.5,.1,.001,.001)=='VALID')
    require('negative_mino_parameter_is_not_valid_event',checked_capture(-.3,.5,.1,.001,.001)=='UNRESOLVED')

    q = -1e-5
    legacy_integrand = 1/np.sqrt(q) if q>0 else 0.
    require('invalid_potential_zero_substitution_is_not_domain_proof',legacy_integrand==0 and q<0)
    # Exact integral of a partly emitting cell with a varying field.
    edge=.3
    exact_flux=edge+.5*edge**2
    cell_center=.5
    center_rule=(1+cell_center) if cell_center<edge else 0.
    xg,wg=roots_legendre(2)
    clipped_points=.5*edge*(xg+1)
    clipped_rule=float(.5*edge*np.dot(wg,1+clipped_points))
    require('absent_center_does_not_make_entire_cell_nonemitting',center_rule==0 and exact_flux>0)
    require('domain_clipped_quadrature_can_resolve_same_cell',abs(clipped_rule-exact_flux)<1e-14)
    require('same_cell_subdivision_preserves_exact_clipped_integral',abs(sum((b+.5*b*b)-(a+.5*a*a) for a,b in [(0,.1),(.1,.2),(.2,.3)])-exact_flux)<1e-14)

    audited=680; escape=532; capture=148
    require('reported_absence_partition_adds_up',escape+capture==audited)
    require('reported_holdout_partition_adds_up',720+118+42==880)
    # Independent quadrature of shared inputs is not an independent input check.
    wrong_shared_crossing=.8
    two_codes=[checked_capture(wrong_shared_crossing,.5,.1,1e-8,1e-8)]*2
    correct_input_code=checked_capture(.3,.5,.1,1e-8,1e-8)
    require('shared_input_error_can_survive_two_quadrature_agreement',len(set(two_codes))==1 and two_codes[0]!=correct_input_code)
    # Sentinel masks and source-emission predicates ask different questions.
    exterior_event_exists=True; radius=70.; source_outer=50.
    source_emits=exterior_event_exists and radius<=source_outer
    marker_is_nan=not exterior_event_exists
    require('finite_exterior_outside_annulus_is_not_missed_emission',not marker_is_nan and not source_emits)

    first=2156; revised=2156; prior_second=2640
    recorded_second=prior_second+first+revised
    remaining=20000-recorded_second
    require('both_030_runs_must_be_charged',first+revised==4312)
    require('recorded_second_batch_remaining_is_13048',recorded_second==6952 and remaining==13048)
    require('reported_unresolved_count_exceeds_inband_domain',485480>4976)
    # Conservation of mask/state categories must use one domain.
    outside_envelope=480504; inside_unknown=4976
    require('outside_envelope_and_inband_unknown_are_distinct',outside_envelope+inside_unknown==485480 and inside_unknown<=4976)

    return {
        'scope':__doc__.strip(),
        'reviewed_commit':'aa3d187039a8cceef458cecd6f608dc06264cd04',
        'analytic_endpoint_peak':{
            'integrand':'1/sqrt(x+delta) on [0,1]', 'delta':delta,
            'exact_integral':float(exact), 'global_gauss64':global_rule,
            'global_absolute_error':abs(global_rule-exact),
            'graded_panel_counts':panel_counts,'graded_values':panel_results,
            'graded_absolute_errors':errors,
            'harder_delta':harder_delta,
            'harder_64_panel_absolute_error':abs(harder_value-harder_exact),
            'not_the_campaign_Kerr_integrand':True},
        'cut_cell_fixture':{'domain':[0,edge],'field':'1+x','full_cell':[0,1],
                            'center_rule':center_rule,'correct_integral':exact_flux,
                            'clipped_quadrature':clipped_rule},
        'accounting_from_reported_ledger_totals':{'prior_second_batch':prior_second,
            'first_030_run':first,'revised_030_run':revised,
            'recorded_second_batch_spend':recorded_second,
            'remaining_before_other_unmetered_comparator_reconciliation':remaining,
            'recorded_lifetime_transfer_spend':17912+recorded_second},
        'checks':checks,'n_checks':len(checks),'all_passed':True,
        'environment':{'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__},
        'campaign_rays_evaluated':0,'repository_suite_executed':False}


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    if args.output.exists(): parser.error('Refusing to overwrite an existing result.')
    result=run()
    result['script_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('x') as f: json.dump(result,f,indent=2,allow_nan=False); f.write('\n')
    print(f"{result['n_checks']} synthetic checks passed; no campaign ray or repository suite run.")

if __name__=='__main__': main()
