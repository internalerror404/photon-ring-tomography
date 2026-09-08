"""Supplementary zero-training check, added AFTER the original fits/results.

Remove the artificial positive offset and score the joint (cos,sin) phase-pair.
This is a distinct diagnostic, NOT substitution of a more favorable criterion.
Frozen candidates, meshes, seeds and original metrics are all preserved.
A rigorous lower bound on the exact reference phase-pair norm follows from the
known phase spread inside each pixel, without using numerical truth norms.
"""
from fractions import Fraction as Q
import json
import numpy as np
from numpy.polynomial.legendre import leggauss
from train import ROOT,exact
from certify import rational_coefficients,spline_evaluate

def phase_detector(fn,q):
 edges=np.linspace(0,1,13);u,w=leggauss(q);s=(edges[:-1,None]+edges[1:,None])/2+np.diff(edges)[:,None]/2*u
 z=3*(8*s+fn(s));ww=np.diff(edges)[:,None]/2*w*8*np.exp(-8*s)
 F=np.stack([np.cos(z),np.sin(z)],axis=-1)
 area=np.exp(-8*edges[:-1])-np.exp(-8*edges[1:])
 return (ww[...,None]*F).sum(1)/np.sqrt(area[:,None])

def run():
 old=json.loads((ROOT/'certificate_results.json').read_text());data=np.load(ROOT/'certified_spline_knots.npz')
 ref=phase_detector(exact,256);reference_check=np.max(abs(ref-phase_detector(exact,128)))
 # q <= 3/25 + 3/10 + 1/10 = 13/25; tau' <= 213/25.
 # Every pixel has s-width 1/12, so phase halfspread <= 213/200.
 halfspread=Q(213,200);kappa=1-halfspread**2/2
 assert kappa==Q(34631,80000) and kappa>0
 rows=[]
 for r in old['results']:
  key=f"classical_{r['cells']}" if r['seed'] is None else f"{r['seed']}_{r['arm']}_knots_{r['cells']}"
  kn=data[key];c=rational_coefficients(kn);fn=lambda s:spline_evaluate(s,kn,c)
  y=phase_detector(fn,256);quadcheck=np.max(abs(y-phase_detector(fn,128)))
  measured=float(np.linalg.norm(y-ref)/np.linalg.norm(ref))
  bound=Q(int(r['bound_exact_numerator']),int(r['bound_exact_denominator']))/kappa
  assert measured<=float(bound)+1e-12
  rows.append({'seed':r['seed'],'arm':r['arm'],'cells':r['cells'],
    'measured_joint_phase_relative_error':measured,'certified_exact_phase_relative_bound':float(bound),
    'certified_pass_below_5e_minus4':bound<=Q(1,2000),'bound_numerator':str(bound.numerator),'bound_denominator':str(bound.denominator),'quadrature_q128_256_max_abs':float(quadcheck)})
 (ROOT/'phase_pair_results.json').write_text(json.dumps({'scope':__doc__,'normalization':'joint Euclidean norm across 12 whitened detector pixels and 2 signed channels; not max individual-channel relative error','derived_after_main_results':True,'reference_norm_lower_fraction_of_sqrt_area':str(kappa),'half_phase_spread_upper':str(halfspread),'reference_q128_256':float(reference_check),'rows':rows,'certificate_includes_float_detector_quadrature':False},indent=2)+'\n')
 for name in ['continued','boost_fixed','boost_residual','classical_Hermite_ODE']:
  rr=[r for r in rows if r['arm']==name and r['cells']==128];print(name,np.median([r['measured_joint_phase_relative_error'] for r in rr]),np.median([r['certified_exact_phase_relative_bound'] for r in rr]))
if __name__=='__main__':run()
