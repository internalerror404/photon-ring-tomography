"""Exact-rational residual enclosures for a frozen piecewise polynomial.

No assertion about the neural function between points is needed: the certified
object is the explicitly frozen cubic surrogate, not the original neural net.
The specified rational differential equation is a manufactured known model.
Bernstein bounds and all certificate accumulation use Python Fraction arithmetic.
Reported detector simulations are high-order Gaussian quadrature, not certified
implementations of transcendental functions or of the physical Kerr renderer.
"""
from fractions import Fraction as Q
from math import comb
from pathlib import Path
import json,time
import numpy as np
from scipy.integrate import quad
from scipy.interpolate import CubicSpline
from train import ROOT,CFG,forcing,exact,detector

def add(a,b):
 out=[Q(0)]*max(len(a),len(b))
 for i,c in enumerate(a):out[i]+=c
 for i,c in enumerate(b):out[i]+=c
 return out

def scale(a,s):return [x*s for x in a]
def mul(a,b):
 out=[Q(0)]*(len(a)+len(b)-1)
 for i,x in enumerate(a):
  for j,y in enumerate(b):out[i+j]+=x*y
 return out

def horner(a,x):
 v=Q(0)
 for c in a[::-1]:v=v*x+c
 return v

def affine(a,lo,hi):
 # coefficient vector of a(lo+(hi-lo)*v)
 out=[Q(0)]*len(a)
 for i,c in enumerate(a):
  for j in range(i+1):out[j]+=c*comb(i,j)*lo**(i-j)*(hi-lo)**j
 return out

def bernstein_range(a):
 n=len(a)-1
 b=[sum((a[i]*Q(comb(k,i),comb(n,i)) for i in range(k+1)),Q(0)) for k in range(n+1)]
 return min(b),max(b)

def ceil_dyadic(x,bits=70):
 if x<0:raise ValueError('Nonnegative bound required')
 unit=1<<bits; nn=x.numerator*unit;dd=x.denominator
 return Q((nn+dd-1)//dd,unit)

def qfloat(x):return Q.from_float(float(x))
def rational_coefficients(knots):
 s,v,d=knots
 if not(np.isfinite(knots).all() and s[0]==0 and s[-1]==1 and np.all(np.diff(s)>0)):raise ValueError('Invalid domain or knots')
 coeff=[]
 for i in range(len(s)-1):
  h=qfloat(s[i+1])-qfloat(s[i]);v0,v1=qfloat(v[i]),qfloat(v[i+1]);d0,d1=qfloat(d[i]),qfloat(d[i+1])
  c=[v0,h*d0,3*(v1-v0)-h*(2*d0+d1),2*(v0-v1)+h*(d0+d1)]
  assert horner(c,Q(1))==v1
  assert sum(Q(j)*c[j] for j in range(1,4))==h*d1
  coeff.append(c)
 return coeff

def denom(s0,h,k,b):
 z=s0-b
 return [1+k*z*z,2*k*z*h,k*h*h]

def min_denom(lo,hi,k,b):
 distance=Q(0) if lo<=b<=hi else min(abs(lo-b),abs(hi-b))
 return 1+k*distance*distance

def residual_bound(s0,h,c,parts=8):
 D1=denom(s0,h,400,Q(37,100));D2=denom(s0,h,1600,Q(39,50));D=mul(D1,D2)
 slope=[c[1]/h,2*c[2]/h,3*c[3]/h]
 numerator=add(add(add(mul(slope,D),scale(D,-Q(3,25))),scale(D2,-Q(3,10))),scale(D1,-Q(1,10)))
 total=Q(0);M=Q(0)
 for j in range(parts):
  a=Q(j,parts);b=Q(j+1,parts)
  lb,ub=bernstein_range(affine(numerator,a,b));den=min_denom(s0+h*a,s0+h*b,400,Q(37,100))*min_denom(s0+h*a,s0+h*b,1600,Q(39,50))
  bound=ceil_dyadic(max(abs(lb),abs(ub))/den)
  M=max(M,bound);total+=h*(b-a)*bound
 return total,M

def spline_evaluate(s,knots,coefficient):
 edges=knots[0];a=np.asarray(s);flat=a.reshape(-1);ii=np.clip(np.searchsorted(edges,flat,side='right')-1,0,len(edges)-2)
 u=(flat-edges[ii])/(edges[ii+1]-edges[ii]);cc=np.asarray([[float(c) for c in row] for row in coefficient])
 v=((cc[ii,3]*u+cc[ii,2])*u+cc[ii,1])*u+cc[ii,0]
 return v.reshape(a.shape)

def certify_knots(knots,parts=8):
 tic=time.perf_counter();coefficient=rational_coefficients(knots);s=knots[0]
 cumulative=abs(qfloat(knots[1,0]));cell=[]
 for i,c in enumerate(coefficient):
  eps,M=residual_bound(qfloat(s[i]),qfloat(s[i+1])-qfloat(s[i]),c,parts)
  cumulative+=eps;cell.append({'cell':i,'local_integrated_residual_bound':float(eps),'residual_sup_bound':float(M),'cumulative_error_upper':float(cumulative)})
 bound=3*cumulative
 # Pass decision is EXACT rational, not a rounded displayed float.
 return {'delay_sup_error_bound':float(cumulative),'relative_exact_detector_error_bound':float(bound),
         'bound_exact_numerator':str(bound.numerator),'bound_exact_denominator':str(bound.denominator),
         'below_5e_minus4_exact':bool(bound<=Q(1,2000)),
         'all_cells_covered':len(coefficient),'subintervals_per_cell':parts,
         'boundary_error':float(abs(qfloat(knots[1,0]))),'certificate_seconds':time.perf_counter()-tic,
         'cell_bounds':cell},coefficient

def test_certifier():
 tests={}
 # The certificate's core inequalities can be checked on exact rational points.
 polys=[[Q(1),Q(-3),Q(2)],[Q(-2),Q(1),Q(-5),Q(7)],[Q(0)]]
 tests['bernstein_convex_hull_exact_rational_samples']=True
 for p in polys:
  lo,hi=bernstein_range(p)
  for x in [Q(j,41) for j in range(42)]:tests['bernstein_convex_hull_exact_rational_samples'] &= lo<=horner(p,x)<=hi
 tests['affine_polynomial_identity']=True
 for p in polys:
  a,b=Q(2,7),Q(5,6);trans=affine(p,a,b)
  for x in [Q(j,13) for j in range(14)]:tests['affine_polynomial_identity'] &= horner(trans,x)==horner(p,a+(b-a)*x)
 tests['outward_dyadic_rounding']=all(ceil_dyadic(x)>=x for x in [Q(1,3),Q(1,100001),Q(5,7)])
 # False low loss example: e=16 a s^2(1-s)^2 with e'=0 at 0,1/2,1.
 p=[Q(0),Q(0),Q(16,5),Q(-32,5),Q(16,5)]
 dp=[(i+1)*p[i+1] for i in range(len(p)-1)]
 tests['three_collocation_residuals_zero_do_not_bound_error']=all(horner(dp,x)==0 for x in [Q(0),Q(1,2),Q(1)]) and horner(p,Q(1,2))==Q(1,5)
 tests['interval_residual_detects_hidden_error']=max(abs(x) for x in bernstein_range(dp))>0
 if not all(tests.values()):raise AssertionError(tests)
 return tests

def run():
 if not(ROOT/'neural_arrays.npz').exists():raise RuntimeError('Run train.py first')
 raw=np.load(ROOT/'neural_arrays.npz');ref=detector(exact,128);grid=np.linspace(0,1,8193);rows=[];save={}
 print('tests',test_certifier(),flush=True)
 for seed in CFG['seeds']:
  for arm in ['continued','boost_fixed','boost_residual']:
   for N in [32,64,128]:
    name=f'{seed}_{arm}_knots_{N}';kn=raw[name];report,c=certify_knots(kn)
    fn=lambda x:spline_evaluate(x,kn,c)
    yy=detector(fn,128);zz=detector(fn,256);ev=fn(grid)
    report.update(seed=seed,arm=arm,cells=N,measured_delay_sup_error=float(np.max(abs(ev-exact(grid)))),
      measured_detector_max_relative=float(max(np.linalg.norm(yy-ref,axis=0)/np.linalg.norm(ref,axis=0))),
      numerical_detector_q128_256_max_abs=float(np.max(abs(yy-zz))),object='frozen_Hermite_surrogate_not_neural_function')
    if report['measured_delay_sup_error']>report['delay_sup_error_bound']+1e-13:raise AssertionError('Envelope violation')
    rows.append(report);save[name]=kn
    print(seed,arm,N,'bound',report['relative_exact_detector_error_bound'],'error',report['measured_detector_max_relative'],'pass',report['below_5e_minus4_exact'],flush=True)
 # Classical ODE solution: independently integrate q between successive knots;
 # certificate checks resulting spline, never trusting the integrator error estimate.
 for N in [32,64,128]:
  kk=np.linspace(0,1,N+1);vv=[0.];neval=0;errsum=0.
  for a,b in zip(kk[:-1],kk[1:]):
   val,err,info=quad(forcing,float(a),float(b),epsabs=1e-13,epsrel=1e-13,full_output=True)
   vv.append(vv[-1]+val);neval+=info['neval'];errsum+=err
  kn=np.stack([kk,np.array(vv),forcing(kk)]);report,c=certify_knots(kn)
  fn=lambda x:spline_evaluate(x,kn,c);yy=detector(fn,128)
  report.update(seed=None,arm='classical_Hermite_ODE',cells=N,measured_delay_sup_error=float(np.max(abs(fn(grid)-exact(grid)))),measured_detector_max_relative=float(max(np.linalg.norm(yy-ref,axis=0)/np.linalg.norm(ref,axis=0))),forcing_evaluations=neval+N+1,quadrature_error_estimate=errsum,object='frozen_Hermite_surrogate_not_neural_function')
  rows.append(report);save[f'classical_{N}']=kn;print('classical',N,report['relative_exact_detector_error_bound'],report['measured_detector_max_relative'],flush=True)
 # 24 labels only, classical interpolation baseline; no derivative supervision.
 ss=np.sort(-np.log(np.linspace(np.exp(-8),1,24))/8);cs=CubicSpline(ss,exact(ss))
 yy=detector(cs,128)
 baseline={'arm':'same_24_labels_cubic_spline','max_detector_relative':float(max(np.linalg.norm(yy-ref,axis=0)/np.linalg.norm(ref,axis=0))),'max_delay_error':float(max(abs(cs(grid)-exact(grid)))),'certificate':'not_requested_for_this_control'}
 (ROOT/'certificate_results.json').write_text(json.dumps({'tests':test_certifier(),'results':rows,'same_labels_control':baseline,'certification_scope':'Exact rational polynomial residual bound under the stated scalar ODE, continuous-Hermite and exact-endpoint assumptions. Certifies the mathematically integrated surrogate response for positive 2+sin/cos; numerical detector quadrature is convergence-checked, not interval-certified. No Kerr certification.'},indent=2)+'\n')
 np.savez_compressed(ROOT/'certified_spline_knots.npz',**save)
if __name__=='__main__':run()
