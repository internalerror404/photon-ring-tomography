"""CPU float64 training and integrated manufactured acquisition for pilot002."""
import os, json, time, random
from pathlib import Path
os.environ.setdefault('OMP_NUM_THREADS','1');os.environ.setdefault('MKL_NUM_THREADS','1')
import numpy as np
from numpy.polynomial.legendre import leggauss
import torch
from torch import nn
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results';OUT.mkdir(exist_ok=True)
torch.set_num_threads(1);torch.set_default_dtype(torch.float64)
def tensor(x):return torch.as_tensor(x,dtype=torch.float64)
def seed(s):random.seed(s);np.random.seed(s);torch.manual_seed(s)
def save(name,obj):
    p=OUT/name;p.write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n');return p
def relative(x,y):return float(np.linalg.norm(np.asarray(x)-y)/max(np.linalg.norm(y),1e-15))
def mlp(nin,nout=1):
    m=nn.Sequential(nn.Linear(nin,32),nn.Tanh(),nn.Linear(32,32),nn.Tanh(),nn.Linear(32,nout))
    with torch.no_grad():m[-1].weight.mul_(.2);m[-1].bias.zero_()
    return m
def fit(m,closure,steps=700,lbsteps=60):
    start=time.perf_counter();opt=torch.optim.Adam(m.parameters(),lr=.002);trace=[]
    for k in range(steps):
        opt.zero_grad(set_to_none=True);loss=closure()
        if not torch.isfinite(loss):raise FloatingPointError('Nonfinite loss')
        loss.backward();opt.step()
        if k%100==0:trace.append([k,float(loss.detach())])
    op=torch.optim.LBFGS(m.parameters(),lr=.8,max_iter=lbsteps,history_size=30,tolerance_grad=1e-10,tolerance_change=1e-13,line_search_fn='strong_wolfe');calls=0
    def cl():
        nonlocal calls
        calls+=1;op.zero_grad(set_to_none=True);l=closure()
        if not torch.isfinite(l):raise FloatingPointError('Nonfinite LBFGS')
        l.backward();return l
    op.step(cl)
    return dict(seconds=time.perf_counter()-start,loss=float(closure().detach()),lbfgs_calls=calls,trace=trace)
def design(orders,q=8,npix=16,times=None):
    if times is None:times=np.linspace(0,.24,5)
    u,w=leggauss(q);edges=np.linspace(0,2*np.pi,npix+1);dx=np.diff(edges);x=(edges[:-1]+edges[1:])[:,None]/2+dx[:,None]*u/2
    cw=dx[:,None]*w/2;coords=[];weights=[];areas=[];oid=[]
    for n in orders:
        phi=x+[0,.7,1.3][n]+.10*n*np.sin(x)
        delay=[.10,.50,.90][n]+.06*np.cos(x)+.025*n*np.sin(2*x)
        amp=[1.,.55,.28][n]*(1+.08*np.cos(x))
        for t in times:
            coords.append(np.stack([phi,t-delay],-1));weights.append(cw*amp);areas.extend(dx);oid.extend([n]*npix)
    return np.concatenate(coords),np.concatenate(weights),np.array(areas),np.array(oid)
def parameters(s):
    rng=np.random.default_rng(s)
    return dict(amplitudes=(np.array([.22,.15,.09])*rng.uniform(.8,1.2,3)).tolist(),phases=rng.uniform(-np.pi,np.pi,3).tolist(),event_phase=float(rng.uniform(-np.pi,np.pi)),seed=s)
def source(x,pars,kind):
    phi,t=x[...,0],x[...,1];z=phi-.8*t;out=np.ones_like(t)
    for k,(a,ph) in enumerate(zip(pars['amplitudes'],pars['phases']),1):out+=a*np.cos(k*z+ph)
    if kind!='matched':
        center=-.70+.025*np.sin(pars['event_phase']);width=.18 if kind=='double' else .22
        b=np.maximum(1-((t-center)/width)**2,0)**3
        out+=.52*b*(1+.6*np.cos(2*z+pars['event_phase']))/1.6
    if kind=='double':
        b=np.maximum(1-((t+.43)/.14)**2,0)**3
        out+=.38*b*np.exp(2*(np.cos(phi+1.1*t-pars['event_phase'])-1))
    return out
def response(d,p,k):return np.sum(d[1]*source(d[0],p,k),axis=1)
class Field(nn.Module):
    def __init__(self):super().__init__();self.net=mlp(9)
    def forward(self,x):
        phi,t=x[...,0],x[...,1];feat=[]
        for k in range(1,5):feat.extend([torch.cos(k*phi),torch.sin(k*phi)])
        return 1+self.net(torch.stack(feat+[t],-1)).squeeze(-1)
def predict(m,d):
    with torch.no_grad():return (m(tensor(d[0]))*tensor(d[1])).sum(1).numpy()
def train_field(p,kind,method,lam,ss,orders,tag):
    seed(ss);m=Field();d=design(orders);dr=design(orders,48)
    truth=response(dr,p,kind);alln=np.random.default_rng(ss+313*p['seed']).normal(size=240)
    use=np.arange(80) if len(orders)==1 else np.arange(240)
    sd=.01*np.sqrt(d[2]);y=truth+sd*alln[use]
    x,w,yt,sig=tensor(d[0]),tensor(d[1]),tensor(y),tensor(sd)
    rng=np.random.default_rng(ss+12001);coll=tensor(np.stack([rng.uniform(0,2*np.pi,256),rng.uniform(-.98,.25,256)],-1))
    def closure():
        loss=(((m(x)*w).sum(1)-yt)/sig).square().mean()
        if method!='data':
            c=coll.detach().clone().requires_grad_(True);f=m(c);g=torch.autograd.grad(f.sum(),c,create_graph=True)[0];z=(g[:,1]+.8*g[:,0])/.05
            reg=z.square() if method=='quadratic' else torch.where(abs(z)<=1,z.square(),2*abs(z)-1)
            loss=loss+lam*reg.mean()
        return loss
    info=fit(m,closure);torch.save(m.state_dict(),OUT/f'{tag}.pt')
    return m,info,dict(y=y,clean=truth,sigma=sd,coords=d[0],weights=d[1])
