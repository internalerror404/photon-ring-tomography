"""Generate tables from measured payloads; do not hardcode favorable outcomes."""
import hashlib,json,platform
from pathlib import Path
import numpy as np
import scipy,torch
from train import ROOT

def run():
 n=json.loads((ROOT/'neural_results.json').read_text());c=json.loads((ROOT/'certificate_results.json').read_text());p=json.loads((ROOT/'phase_pair_results.json').read_text())
 aggregates=[]
 for arm in ['continued','boost_fixed','boost_residual']:
  fits=[r for r in n['results'] if r['arm']==arm];ph=[r for r in p['rows'] if r['arm']==arm and r['cells']==128]
  aggregates.append({'arm':arm,'seed_count':len(fits),'neural_measured_positive_channel_max_median':float(np.median([r['max_detector_relative'] for r in fits])),
   'uniform_holdout_PDE_RMS_median':float(np.median([r['pde_rms'] for r in fits])),
   'phase_pair_relative_median':float(np.median([r['measured_joint_phase_relative_error'] for r in ph])),
   'phase_pair_relative_min':float(min(r['measured_joint_phase_relative_error'] for r in ph)),
   'phase_pair_relative_max':float(max(r['measured_joint_phase_relative_error'] for r in ph)),
   'certified_phase_bound_median':float(np.median([r['certified_exact_phase_relative_bound'] for r in ph])),
   'certified_pass_count':sum(bool(r['certified_pass_below_5e_minus4']) for r in ph)})
 for r in p['rows']:
  if r['arm']=='classical_Hermite_ODE':aggregates.append(r)
 # More exact arithmetic tests, independent samples of core certificate identities.
 from certify import Q,denom,mul,add,scale,horner,residual_bound,min_denom,ceil_dyadic
 coeff=[Q(1,100),Q(-1,7),Q(2,13),Q(5,11)];a=Q(3,8);h=Q(1,16)
 D1=denom(a,h,400,Q(37,100));D2=denom(a,h,1600,Q(39,50));D=mul(D1,D2)
 slope=[coeff[1]/h,2*coeff[2]/h,3*coeff[3]/h]
 numerator=add(add(add(mul(slope,D),scale(D,-Q(3,25))),scale(D2,-Q(3,10))),scale(D1,-Q(1,10)))
 identities=[]
 for u in [Q(i,97) for i in range(98)]:
  s=a+h*u;f=Q(3,25)+Q(3,10)/(1+400*(s-Q(37,100))**2)+Q(1,10)/(1+1600*(s-Q(39,50))**2)
  identities.append(horner(numerator,u)/horner(D,u)==horner(slope,u)-f)
 checks=dict(c['tests']);checks.update({'rational_residual_numerator_identity':all(identities),
  'all_30_frozen_surrogates_observed_error_below_certified_delay_bound':all(r['measured_delay_sup_error']<=r['delay_sup_error_bound']+1e-13 for r in c['results']),
  'all_30_phase_pair_errors_below_analytic_certificate':all(r['measured_joint_phase_relative_error']<=r['certified_exact_phase_relative_bound']+1e-12 for r in p['rows']),
  'all_9_final_models_saved':len(list(ROOT.glob('continued_*.pt')))+len(list(ROOT.glob('boost_*.pt')))==9,
  '3_initial_models_saved':len(list(ROOT.glob('initial_*.pt')))==3,
  'reference_quadrature_convergence':p['reference_q128_256']<1e-12})
 if not all(checks.values()):raise AssertionError(checks)
 out={'scope':'Independent manufactured scalar ODE study; no Euler or Kerr production calculation; no source inversion',
 'protocol_sha256':hashlib.sha256((ROOT/'protocol.json').read_bytes()).hexdigest(),
 'neural_stages':{'initial':3,'successor':9},'frozen_cubic_certificates':len(c['results']),
 'aggregates':aggregates,'same_labels_classical_control':c['same_labels_control'],
 'checks':checks,'count_checks':len(checks),
 'quadrature':{'truth_max_abs_64_128':n['reference_q64_128'],'learned_spline_max_abs_128_256':max(r.get('numerical_detector_q128_256_max_abs',0) for r in c['results']),
 'interval_certified_numerical_pixel_quadrature':False},
 'environment':{'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__,'torch':torch.__version__,'dtype':'float64','cpu_threads':1},
 'no_data_hallucination':'Results loaded from saved fit and certificate payloads, not prospective thresholds',
 'study_limitations':['One manufactured rational ODE','Three seeds not population confidence intervals','Unequal parameter/FLOP counts across successors','No SS-eSOAP/SS-Broyden implementation','Signed phase-pair diagnostic was added after original fit results without any retraining or criterion replacement','Certificate applies to exact rational cubic object and exact detector integral; simulated quadrature convergence is separate','Classical control benefits from a simple directly integrable equation'],
 'production_budget':{'used':0,'remaining_unmodified':854}}
 (ROOT/'SUMMARY.json').write_text(json.dumps(out,indent=2)+'\n')
 print('Summary;',len(checks),'checks passed')
if __name__=='__main__':run()
