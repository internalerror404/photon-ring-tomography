#!/usr/bin/env python3
"""Review 029 checks: supplied G1 arithmetic and synthetic validation failures.
No real ray tracing, hull solving, or repository-suite execution.
Inputs transcribed from CURVED_HULL_VALIDATION_028.json at 7067c4e.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import platform
import numpy as np


def run() -> dict:
    checks=[]
    def check(name, condition):
        checks.append({'name':name,'passed':bool(condition)})
        if not condition:
            raise AssertionError(name)
    # Absolute area differences lower-bound polygon symmetric differences.
    ai0, ai1=82.64000863188306,82.64003294004084
    ao0, ao1=84.64388204814033,84.6439069465467
    inner_delta, outer_delta=abs(ai1-ai0),abs(ao1-ao0)
    a0,a1=ao0-ai0,ao1-ai1
    boundary_min=inner_delta+outer_delta
    # Union area <= sum of the two nonnegative band areas, without nesting assumptions.
    conservative_lb=boundary_min/(a0+a1)
    per_shape=max(inner_delta/ai1,outer_delta/ao1)
    check('quoted_per_shape_tessellation_changes_below_1e_6',per_shape<1e-6)
    check('band_normalized_boundary_change_need_not_be_below_1e_6',conservative_lb>1e-6)
    # Radius error versus thin-annulus domain error are different quantities.
    ri,ro,delta=4.99,5.0,5e-5
    old_area=math.pi*(ro**2-ri**2)
    new_area=math.pi*((ro+delta)**2-ri**2)
    radius_relative=delta/ro
    band_relative=(new_area-old_area)/new_area
    check('small_relative_radius_error_can_fail_band_error',radius_relative<2.5e-4<band_relative)
    # A deterministic unstable expression is not unrecoverable physics.
    x=np.float64(1e8)
    unstable=float(np.sqrt(x*x+1)-x)
    stable=float(1/(np.sqrt(x*x+1)+x))
    repeated=[float(np.sqrt(x*x+1)-x) for _ in range(5)]
    check('repeating_an_expression_reproduces_its_numerical_defect',unstable==0 and len(set(repeated))==1)
    check('equivalent_stable_expression_can_change_numeric_result',stable>0 and abs(stable-5e-9)<1e-23)
    # Exact radius readback is not whole transfer validation.
    transfer={'source_r':3.0,'source_phi':0.3,'coordinate_time':float('nan'),'redshift':0.8}
    first_bad=next(k for k,v in transfer.items() if not math.isfinite(v))
    check('radius_parity_does_not_certify_time_or_redshift',transfer['source_r']==3.0 and first_bad=='coordinate_time')
    # Independent-point comparisons must handle the azimuthal circle.
    phi1=2*np.pi-1e-8; phi2=-1e-8
    phase_error=float(abs(np.exp(1j*phi1)-np.exp(1j*phi2)))
    check('wrapped_azimuth_comparison_uses_phase',abs(phi1-phi2)>6 and phase_error<1e-14)
    # An output summary can report success while prescribed checks are missing.
    evidence={'two_late_pairs':True,'shift_radius':True,'shift_band':False,
              'shift_response':False,'tighter_root':False,'band_tessellation':False}
    required=('two_late_pairs','shift_band','shift_response','tighter_root','band_tessellation')
    ready=all(evidence.get(k,False) for k in required)
    check('missing_geometry_checks_prevent_full_qualification',not ready)
    # The previous last-pair-only aggregator misses an early-pair failure.
    rows=[False,True]
    check('one_good_late_pair_not_two_good_pairs',rows[-1] and not all(rows))
    # Positive total area does not ensure local band nesting/positive width.
    widths=np.array([.02,.02,-.001])
    check('positive_integrated_area_does_not_certify_local_band_width',widths.sum()>0 and widths.min()<0)
    # Narrow a few found roots without asserting a globally complete contour.
    success,total=1191,1212
    check('resolved_brackets_not_global_contour_certificate',success<total)
    f=lambda z:(z-.25)*(z-.75)
    check('equal_sign_interval_can_hold_two_unsearched_crossings',f(0)*f(1)>0 and f(.5)<0)
    # A same signed response on known support does not bound an omitted term.
    known=np.array([1.,2.]); missing=np.array([0.,10.])
    check('identical_partial_responses_do_not_bound_missing_signal',np.array_equal(known,known) and np.linalg.norm(missing)>np.linalg.norm(known))
    # Charge/reserve before a physical call, not after it.
    class Meter:
        def __init__(self,remaining): self.remaining=remaining; self.calls=0
        def evaluate(self,n):
            if n>self.remaining: raise RuntimeError('over budget')
            self.remaining-=n
            self.calls+=1
            return np.ones(n)
    m=Meter(2)
    try: m.evaluate(3)
    except RuntimeError: pass
    check('over_budget_query_is_refused_before_execution',m.calls==0 and m.remaining==2)
    # Runtime exceptions still consume a reserved attempted-query budget.
    remaining=2
    remaining-=1
    try: raise ArithmeticError('fixture primitive failed')
    except ArithmeticError: pass
    check('failed_attempt_remains_charged',remaining==1)
    return {'scope':__doc__.strip(),'reviewed_commit':'7067c4ed3a270648d54410d601dd63e053f780be',
      'source_path':'artifacts/revisions/mahakal_v4_1/G1_20260907T002858Z_ecddc92/CURVED_HULL_VALIDATION_028.json',
      'source_blob':'4cc167114fe734d15d50f28e7b8002fa2719ad37',
      'input_method':'Explicit transcription of four reported area values and summary counts, not a local full-file rehash.',
      'tessellation_order2':{'inner_area_n':ai0,'inner_area_2n':ai1,'outer_area_n':ao0,'outer_area_2n':ao1,
        'band_area_n':a0,'band_area_2n':a1,'max_per_shape_relative_change':per_shape,
        'sum_absolute_boundary_area_changes':boundary_min,
        'band_union_normalized_symdiff_lower_bound':conservative_lb,
        'using_finer_band_area_denominator':boundary_min/a1,
        'net_band_area_relative_change':abs(a1-a0)/a1,
        'not_a_direct_full_polygon_symdiff_computation':True},
      'radius_vs_band_fixture':{'relative_radius_error':radius_relative,'relative_band_symdiff':band_relative},
      'deterministic_cancellation_fixture':{'original_expression':unstable,'stable_equivalent':stable},
      'whole_transfer_fixture_first_nonfinite':first_bad,
      'reported_brackets':{'resolved':success,'total':total,'fraction':success/total},
      'counts_from_report':{'boundary_lifetime_spent':18000+8300,'boundary_left_under_30000':30000-18000-8300,
                           'transfer_lifetime_spent':17912,'transfer_left_under_250000':250000-17912,
                           'first_pilot_left_under_20000':20000-17912},
      'checks':checks,'n_checks':len(checks),'all_passed':all(c['passed'] for c in checks),
      'environment':{'python':platform.python_version(),'numpy':np.__version__},
      'physical_execution':False}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    if a.output.exists(): p.error('Output already exists.')
    result=run(); result['script_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open('x') as f: json.dump(result,f,indent=2,allow_nan=False); f.write('\n')
    print(f"{result['n_checks']} checks passed; no physical calculation executed.")

if __name__=='__main__': main()
