"""Explicit normalized defensive mixture densities and importance weights.
Optimization constructs proposals; proposal residual scores are NOT probabilities.
All Student-t draws outside the uniform-prior cube retain zero target weight.
"""
import numpy as np
from scipy.special import logsumexp,gammaln
from scipy.optimize import least_squares

DF=5.;DEFENSIVE=.15

def normalized(logw):
    finite=np.isfinite(logw)
    if not finite.any():raise RuntimeError('zero finite posterior weight')
    z=float(logsumexp(logw)); w=np.exp(np.asarray(logw)-z)
    w /= w.sum()
    return w,z-np.log(len(w))

def ess(w):return float(1/np.dot(w,w))
def quantile(v,w,q):
    i=np.argsort(v,axis=0);sv=np.take_along_axis(v,i,axis=0)
    weights=np.broadcast_to(w.reshape((-1,)+(1,)*(v.ndim-1)),v.shape)
    cw=np.cumsum(np.take_along_axis(weights,i,axis=0),axis=0)
    j=np.argmax(cw>=q,axis=0)
    return np.take_along_axis(sv,np.expand_dims(j,0),axis=0)[0]

def tlogpdf(x,mu,L):
    d=len(mu);delta=np.linalg.solve(L,(np.atleast_2d(x)-mu).T).T;r=np.sum(delta*delta,axis=1)
    return gammaln((DF+d)/2)-gammaln(DF/2)-.5*d*np.log(DF*np.pi)-np.log(np.diag(L)).sum()-(DF+d)/2*np.log1p(r/DF)

def shape_from_jac(J):
    d=J.shape[1];G=J.T@J+np.eye(d)/.25**2
    val,vec=np.linalg.eigh(G);C=(vec/val[None,:])@vec.T
    return np.linalg.cholesky((C+C.T)/2)

def fit(fun,x,max_nfev):
    z=least_squares(fun,np.clip(x,1e-5,1-1e-5),bounds=(np.full(len(x),1e-6),np.full(len(x),1-1e-6)),max_nfev=max_nfev,ftol=1e-7,xtol=1e-7,gtol=1e-7)
    return {'x':z.x,'L':shape_from_jac(z.jac),'cost':float(2*z.cost),'success':bool(z.success),'nfev':int(z.nfev),'status':int(z.status),'optimality':float(z.optimality)}

def sample(modes,N,rng):
    d=len(modes[0]['x']);x=np.empty((N,d));comp=np.empty(N,int)
    for i in range(N):
        if rng.random()<DEFENSIVE:x[i]=rng.random(d);comp[i]=-1
        else:
            k=int(rng.integers(len(modes)));m=modes[k]
            x[i]=m['x']+m['L']@rng.normal(size=d)/np.sqrt(rng.chisquare(DF)/DF);comp[i]=k
    valid=np.all((x>=0)&(x<=1),axis=1)
    logq=density(x,modes)
    return x,valid,logq,comp

def density(x,modes):
    valid=np.all((np.atleast_2d(x)>=0)&(np.atleast_2d(x)<=1),axis=1)
    rows=[np.where(valid,np.log(DEFENSIVE),-np.inf)]
    for m in modes:rows.append(np.log((1-DEFENSIVE)/len(modes))+tlogpdf(x,m['x'],m['L']))
    return logsumexp(rows,axis=0)
