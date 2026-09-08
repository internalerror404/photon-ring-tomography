"""Schwarzschild scattering primitive; units G=c=M=1.
Ray begins and ends on r=100, with closest approach rt>3. Total angular
sweep and coordinate flight time are independently evaluated by a factored
radial quadrature and by integration of the Binet geodesic equation.
Not an equatorial disk/order-resolved image renderer or Paper I replay.
"""
import numpy as np
from scipy.integrate import quad, solve_ivp
from math import sqrt
RO=100.
BC=3*sqrt(3)
def impact(rt):return rt/np.sqrt(1-2/rt)
def roots(rt):
    b=impact(rt)
    disc=np.sqrt(4*b*b-3*rt*rt)
    return (-rt+disc)/2,(-rt-disc)/2

def radial_quad(rt,eps=2e-11):
    if not 3<rt<RO:raise ValueError('Require accessible simple exterior turning point')
    b=impact(rt);r2,rn=roots(rt);sm=np.sqrt(RO-rt)
    def reduced(s):
        r=rt+s*s
        Q=r*(r-r2)*(r-rn)
        if Q<=0 or not np.isfinite(Q):raise FloatingPointError('Invalid allowed interval')
        return r,np.sqrt(Q)
    def angle(s):
        r,q=reduced(s);return 2*b/q
    def time(s):
        r,q=reduced(s);return 2*r**3/((r-2)*q)
    vphi,ephi=quad(angle,0,sm,epsabs=eps,epsrel=eps,limit=250)
    vtime,etime=quad(time,0,sm,epsabs=eps,epsrel=eps,limit=250)
    return np.array([2*vphi,2*vtime]),np.array([2*ephi,2*etime])

def orbit_ode(rt,rtol=2e-11):
    b=impact(rt)
    def rhs(psi,z):
        u,v,t=z
        return [v,3*u*u-u,1/(b*u*u*(1-2*u))]
    def endpoint(psi,z):return z[0]-1/RO
    endpoint.terminal=True;endpoint.direction=-1
    sol=solve_ivp(rhs,[0,30],[1/rt,0,0],method='DOP853',rtol=rtol,atol=rtol*.02,events=endpoint)
    if not sol.success or len(sol.t_events[0])!=1:raise RuntimeError('No valid returned endpoint')
    psi=sol.t_events[0][0];u,v,t=sol.y_events[0][0]
    # First integral: v^2=1/b^2-u^2+2u^3.
    cons=sol.y[1]**2+sol.y[0]**2-2*sol.y[0]**3-1/b**2
    return np.array([2*psi,2*t]),float(np.max(abs(cons))),len(sol.t)
