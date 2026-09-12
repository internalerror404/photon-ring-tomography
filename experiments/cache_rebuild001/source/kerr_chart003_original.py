"""Kerr equatorial-crossing transfer chart, M=1, independently formulated solvers.
Backward Mino time s; lambda=L/E and Carter eta fixed. Beta<0 convention.
Solver B: separated turning-point-regularized quadratures and root inversion.
Solver A: compactified-radius and polar second-order ODE with event tracking.
Neither uses existing Mahakal maps. Source is prograde circular on r in [6,20].
"""
from __future__ import annotations
from functools import lru_cache
from pathlib import Path
import json,time,os
import numpy as np
from scipy.optimize import brentq
from scipy.integrate import solve_ivp
from numpy.polynomial.legendre import leggauss
A=.5; INC=np.deg2rad(50.); RO=100.; MU0=np.cos(INC); RP=1+np.sqrt(1-A*A)
ROOT=Path(__file__).resolve().parents[1]

_COUNTS=None
def log_attempt(phase,method,inputs):
    global _COUNTS
    from collections import Counter
    if _COUNTS is None:
        p=ROOT/'attempts'/'physical_calls.jsonl'
        _COUNTS=Counter(json.loads(x)['method'] for x in p.read_text().splitlines()) if p.exists() else Counter()
    limit={'separated_quadrature':10000,'compactified_ode':220,'equation_precompute':1600}[method]
    if _COUNTS[method]>=limit:raise RuntimeError('Physical attempt cap reached: '+method)
    _COUNTS[method]+=1
    record={'timestamp':time.time(),'phase':phase,'method':method,'inputs':np.asarray(inputs).tolist()}
    with (ROOT/'attempts'/'physical_calls.jsonl').open('a') as f:f.write(json.dumps(record)+'\n')

@lru_cache(None)
def rule(n):return leggauss(n)

def rc_of_lambda(lam):
    fun=lambda r:(r*r*(r-3)+A*A*(r+1))/(A*(1-r))-lam
    return brentq(fun,2.35,3.65,xtol=1e-14)

def invariants(lam,z):
    rc=rc_of_lambda(float(lam)); rt=rc+np.exp(z)
    P=rt*rt+A*A-A*lam; D=rt*rt-2*rt+A*A
    eta=P*P/D-(lam-A)**2
    eta_prime=4*rt*P/D-P*P*(2*rt-2)/(D*D)
    b2=eta+A*A*MU0*MU0-lam*lam*(MU0/np.sin(INC))**2
    if b2<=0:raise ValueError('Observer outside angular domain')
    alpha=-lam/np.sin(INC);beta=-np.sqrt(b2)
    jac=eta_prime*np.exp(z)/(2*np.sin(INC)*np.sqrt(b2))
    if jac<=0:raise ValueError('Nonpositive chart area')
    return dict(lam=lam,z=z,rc=rc,rt=rt,eta=eta,alpha=alpha,beta=beta,jac=jac)

def radial_setup(meta):
    lam,eta,rt=meta['lam'],meta['eta'],meta['rt']
    b=A*A-lam*lam-eta;c=2*((lam-A)**2+eta);d=-A*A*eta
    # Divide original quartic by known, checked turning root. No identity comparison.
    coeff=np.array([1.,0.,b,c,d]);quot,rem=np.polydiv(coeff,[1.,-rt]);others=np.roots(quot)
    norm=sum(abs(coeff[i])*abs(rt)**(4-i) for i in range(5))
    if abs(np.polyval(coeff,rt))>1e-11*norm:raise ValueError('Invalid turning root')
    if max(abs(others.imag))>1e-7 or max(others.real)>=rt-1e-10:raise ValueError('Not simple exterior scattering branch')
    return np.sort(others.real),coeff

def radial_integrals(v,meta,other,n=64):
    if v==0:return np.zeros(3)
    x,w=rule(n);u=.5*v*(x+1);r=meta['rt']+u*u
    product=np.prod(r[:,None]-other[None,:],axis=1)
    if np.any(product<=0):raise ValueError('Invalid radial interval')
    ds=2/np.sqrt(product);P=r*r+A*A-A*meta['lam'];D=r*r-2*r+A*A
    out=np.stack([ds,ds*A*P/D,ds*(r*r+A*A)*P/D],axis=-1)
    return .5*v*(w@out)

def angular_integrals(meta,order,n=64):
    lam,eta=meta['lam'],meta['eta'];b=A*A-eta-lam*lam
    up=(b+np.sqrt(b*b+4*A*A*eta))/(2*A*A)
    um=-eta/(A*A*up)  # stable negative root
    if not 0<MU0*MU0<up<1:raise ValueError('Angular turning point invalid')
    psi0=np.arcsin(MU0/np.sqrt(up));end=-order*np.pi
    # Fixed phase panels resolve the narrow polar azimuth integrand near a turn.
    # This was corrected in solver-development, before calibration/test freezing.
    knots=np.r_[end,np.arange(np.ceil(end/(np.pi/4)),np.floor(psi0/(np.pi/4))+1)*(np.pi/4),psi0]
    knots=np.unique(knots);x,w=rule(n)
    half=.5*np.diff(knots);psi=.5*(knots[:-1]+knots[1:])[:,None]+half[:,None]*x
    mu=np.sqrt(up)*np.sin(psi);ds=1/(A*np.sqrt(up*np.sin(psi)**2-um))
    pang=lam/(1-mu*mu)-A;tang=A*lam-A*A*(1-mu*mu)
    return np.sum(half[:,None]*(np.stack([ds,ds*pang,ds*tang],axis=-1)*w[None,:,None]).sum(axis=1),axis=0)

def transfer_from_crossing(meta,rs,ph,T):
    Omega=1/(rs**1.5+A)
    denom=1-3/rs+2*A/rs**1.5
    if denom<=0:return np.array([rs,ph,T,np.nan])
    uts=(1+A/rs**1.5)/np.sqrt(denom)
    uto=1/np.sqrt(1-2*RO/(RO*RO+A*A*MU0*MU0))
    g=uto/(uts*(1-Omega*meta['lam']))
    return np.array([rs,ph,T,g])

def quad_transfer(lam,z,order=2,n=64,phase='unspecified',record=True):
    if record:log_attempt(phase,'separated_quadrature',[lam,z,order,n])
    meta=invariants(lam,z);other,coeff=radial_setup(meta)
    ang=angular_integrals(meta,order,n);vo=np.sqrt(RO-meta['rt']);jo=radial_integrals(vo,meta,other,n)
    if ang[0]>=2*jo[0]:
        return {'status':'NO_CROSSING_BEFORE_OUTGOING_OBSERVER_RADIUS','meta':meta,'angular':ang,'radial_observer':jo}
    target=abs(ang[0]-jo[0]);leg=1 if ang[0]>jo[0] else -1
    vs=brentq(lambda v:radial_integrals(v,meta,other,n)[0]-target,0,vo,xtol=5e-13)
    js=radial_integrals(vs,meta,other,n);rad=jo+leg*js
    ph=-(rad[1]+ang[1]);T=rad[2]+ang[2];rs=meta['rt']+vs*vs
    status='EMITTING' if 6<=rs<=20 else 'EXTERIOR_OUTSIDE_ANNULUS'
    return {'status':status,'tuple':transfer_from_crossing(meta,rs,ph,T),'leg':leg,'meta':meta,
            'angular':ang,'radial_observer':jo,'crossing_mino':ang[0],
            'root_relative_residual':float(abs(np.polyval(coeff,meta['rt']))/sum(abs(coeff[i])*meta['rt']**(4-i) for i in range(5)))}

def ode_transfer(lam,z,order=2,rtol=2e-11,atol=2e-12,phase='validation'):
    log_attempt(phase,'compactified_ode',[lam,z,order,rtol,atol])
    meta=invariants(lam,z);eta=meta['eta'];b=A*A-lam*lam-eta;c=2*((lam-A)**2+eta);d=-A*A*eta
    uu=1/RO;pu=np.sqrt(1+b*uu**2+c*uu**3+d*uu**4);mu=MU0;pmu=meta['beta']*np.sin(INC)
    def rhs(s,y):
        u,pu,mu,pmu,phi,T=y;r=1/u;P=r*r+A*A-A*lam;D=r*r-2*r+A*A
        return [pu,b*u+1.5*c*u*u+2*d*u**3,pmu,(A*A-eta-lam*lam)*mu-2*A*A*mu**3,
                -(A*P/D+lam/(1-mu*mu)-A),(r*r+A*A)*P/D+A*lam-A*A*(1-mu*mu)]
    def equator(s,y):return y[2]
    equator.terminal=False;equator.direction=0
    def horizon(s,y):return y[0]-1/(RP+1e-5)
    horizon.terminal=True;horizon.direction=1
    def escaped(s,y):return y[0]-1/RO
    escaped.terminal=True;escaped.direction=-1
    initial=[uu,pu,mu,pmu,0.,0.]
    sol=solve_ivp(rhs,[0,6],initial,method='DOP853',rtol=rtol,atol=atol,
                  events=[equator,horizon,escaped],max_step=.015)
    if len(sol.t_events[0])<=order:return {'status':'NO_NTH_CROSSING','crossings':len(sol.t_events[0]),'nfev':sol.nfev}
    sy=sol.y_events[0][order];s=sol.t_events[0][order];rs=1/sy[0]
    U=1+b*sol.y[0]**2+c*sol.y[0]**3+d*sol.y[0]**4
    MM=eta+(A*A-eta-lam*lam)*sol.y[2]**2-A*A*sol.y[2]**4
    errrad=float(np.max(abs(sol.y[1]**2-U)));errang=float(np.max(abs(sol.y[3]**2-MM)))
    return {'status':'EMITTING' if 6<=rs<=20 else 'EXTERIOR_OUTSIDE_ANNULUS',
            'tuple':transfer_from_crossing(meta,rs,sy[4],sy[5]),'crossing_mino':s,
            'leg':1 if sy[1]<0 else -1,'radial_first_integral_error':errrad,
            'angular_first_integral_error':errang,'nfev':sol.nfev,'meta':meta}
