"""Face-on Schwarzschild razor-thin annulus renderer, M=1.
Independent formulations: turning-point regularized radial quadrature; orbital ODE.
Finite observer r=100; isotropic surface brightness j; no absorption. Not Kerr.
"""
from pathlib import Path
import json, time, warnings
import numpy as np
from scipy.integrate import quad, solve_ivp, IntegrationWarning
from scipy.optimize import brentq
ROOT=Path(__file__).resolve().parent.parent
RO=100.; RI=6.; RE=12.; FO=1-2/RO; BC=3*np.sqrt(3.)
LEDGER=ROOT/'results'/'physical_ledger.jsonl'
CAP=6000


def charge(method,b=None,n=None):
    LEDGER.parent.mkdir(exist_ok=True,parents=True)
    count=sum(1 for _ in LEDGER.open()) if LEDGER.exists() else 0
    if count>=CAP: raise RuntimeError('Physical evaluation cap exceeded before launch')
    with LEDGER.open('a') as f:f.write(json.dumps(dict(id=count+1,method=method,b=b,n=n,time=time.time()))+'\n')


def roots(b):
    if b<=BC: raise ValueError('This wrapper is restricted to exterior scattering rays')
    rt=brentq(lambda r:r/np.sqrt(1-2/r)-b,3.,b,xtol=5e-14,rtol=1e-14)
    disc=np.sqrt(4*b*b-3*rt*rt)
    rp=(-rt+disc)/2; rm=(-rt-disc)/2
    return rt,rp,rm


def integrals(b,rt,rp,rm,s,eps=2e-11):
    def denominator(x):
        r=rt+x*x;return np.sqrt(r*(r-rp)*(r-rm))
    with warnings.catch_warnings():
        warnings.simplefilter('error',IntegrationWarning)
        j,e1=quad(lambda x:2*b/denominator(x),0,s,epsabs=eps,epsrel=eps,limit=160)
        t,e2=quad(lambda x:2*(rt+x*x)**2/((1-2/(rt+x*x))*denominator(x)),0,s,epsabs=eps,epsrel=eps,limit=160)
    return j,t,e1,e2


def source_angle_at_r(b,n,r):
    """Analytic-branch boundary residual for r in annulus, always inside allowed path."""
    charge('boundary_angle',float(b),int(n))
    rt,rp,rm=roots(b)
    if rt>r: raise ValueError('Requested source below turning radius')
    def jj(s):return quad(lambda x:2*b/np.sqrt((rt+x*x)*(rt+x*x-rp)*(rt+x*x-rm)),0,s,epsabs=3e-12,epsrel=3e-12)[0]
    jo=jj(np.sqrt(RO-rt));jr=jj(np.sqrt(r-rt))
    return jo-jr if n==0 else jo+jr


def band_edge(n,r):
    if n==0:
        # Inward source expression admits b <= r/sqrt(f(r)); lower b>BC suffices here.
        hi=r/np.sqrt(1-2/r)*(1-2e-13)
        lo=BC*(1+1e-10)
    else:
        lo=BC*(1+1e-10);hi=r/np.sqrt(1-2/r)*(1-2e-13)
    return brentq(lambda b:source_angle_at_r(b,n,r)-(n+.5)*np.pi,lo,hi,xtol=5e-14,rtol=1e-14)


def trace_quad(b,n):
    charge('radial_quad',float(b),int(n));rt,rp,rm=roots(b)
    so=np.sqrt(RO-rt);jo,to,_,eo=integrals(b,rt,rp,rm,so)
    target=(n+.5)*np.pi;need=abs(target-jo);leg=-1 if target<jo else 1
    if need>=jo:raise ValueError('Source event outside observer sphere under this pilot')
    def fn(s):return integrals(b,rt,rp,rm,s)[0]-need
    ss=brentq(fn,0,so,xtol=2e-13,rtol=2e-13)
    jr,tr,er,et=integrals(b,rt,rp,rm,ss)
    r=rt+ss*ss;T=to+leg*tr;g=np.sqrt((1-3/r)/FO)
    return np.array([r,T,g,leg,abs(jo+leg*jr-target),eo+et])


def trace_ode(b,n,rtol=2e-11):
    charge('orbital_ode',float(b),int(n));u0=1/RO;v0=np.sqrt(1/b**2-u0**2+2*u0**3)
    def rhs(psi,y):
        u,v,T=y
        return [v,-u+3*u*u,1/(b*u*u*(1-2*u))]
    target=(n+.5)*np.pi
    sol=solve_ivp(rhs,(0,target),[u0,v0,0.],method='DOP853',rtol=rtol,atol=[rtol/100,rtol/100,rtol],max_step=.06)
    if not sol.success:raise RuntimeError(sol.message)
    u,v,T=sol.y[:,-1];r=1/u
    if r<=3 or r>=RO:raise ValueError('Endpoint not in intended exterior source-domain pilot')
    # Frequency measured by static observer divided by circular geodesic emitter frequency.
    ut_obs=1/np.sqrt(FO);ut_em=1/np.sqrt(1-3/r)
    g=ut_obs/ut_em
    conserved=sol.y[1]**2+sol.y[0]**2-2*sol.y[0]**3-1/b**2
    return np.array([r,T,g,float(-np.sign(v)),np.max(abs(conserved)),len(sol.t)])


def camera_area(b0,b1,theta_width):
    # rescaled true solid angle: (RO^2/FO)*dOmega, projection coordinate b=L/E
    a=FO/RO**2
    return theta_width*(b1*b1-b0*b0)/(np.sqrt(1-a*b0*b0)+np.sqrt(1-a*b1*b1))


def weight_jacobian(b): return b/np.sqrt(1-FO*b*b/RO**2)


if __name__=='__main__':
    out={}
    for n in range(3):
        edges=[band_edge(n,r) for r in [RI,RE]];b=np.mean(edges)
        qa=trace_quad(b,n);ob=trace_ode(b,n)
        out[n]=dict(band=edges,quad=qa.tolist(),ode=ob.tolist(),difference=(qa[:3]-ob[:3]).tolist())
    (ROOT/'results'/'engineering_preflight.json').write_text(json.dumps(out,indent=2))
    print(json.dumps(out,indent=2))
