"""Registered Kerr chart experiment; explicit separation of training and validation.
No historical inversion, no production ray inputs. See protocol and registration.
"""
from __future__ import annotations
import os
os.environ.setdefault('OMP_NUM_THREADS','1');os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
from pathlib import Path
import time,json,hashlib,sys
import numpy as np
import torch
from torch import nn
from scipy.interpolate import RectBivariateSpline
from numpy.polynomial.legendre import leggauss
import kerr
ROOT=kerr.ROOT;CFG=json.loads((ROOT/'protocol.json').read_text())
torch.set_default_dtype(torch.float64);torch.set_num_threads(1)
LOW=np.array([.5,-1.5]);HIGH=np.array([2.,-1.3])

def dump(path,obj):
    (ROOT/path).write_text(json.dumps(obj,indent=2,allow_nan=False,default=lambda x:x.tolist() if isinstance(x,np.ndarray) else x.item())+'\n')

def grid(n):
    xx=np.linspace(LOW[0],HIGH[0],n);yy=np.linspace(LOW[1],HIGH[1],n)
    mesh=np.meshgrid(xx,yy,indexing='ij');return xx,yy,np.stack([m.ravel() for m in mesh],-1)

def reference(xy,n=64,phase='reference'):
    tuples=[];meta=[];records=[]
    for x in xy:
        d=kerr.quad_transfer(*map(float,x),n=n,phase=phase)
        records.append(d)
        if d['status']!='EMITTING' or d['leg']!=1:raise RuntimeError(f'Unqualified chart point {x}: {d}')
        tuples.append(d['tuple']);meta.append([d['meta'][q] for q in ('lam','rt','eta','jac','alpha','beta')])
    return np.asarray(tuples),np.asarray(meta),records

def precompute(xy,phase):
    m=[];roots=[];angs=[];jos=[]
    for p in xy:
        kerr.log_attempt(phase,'equation_precompute',p)
        meta=kerr.invariants(*map(float,p));other,_=kerr.radial_setup(meta)
        ang=kerr.angular_integrals(meta,2,64);jo=kerr.radial_integrals(np.sqrt(kerr.RO-meta['rt']),meta,other,64)
        m.append([meta['lam'],meta['rt'],meta['eta'],meta['jac'],meta['alpha'],meta['beta']]);roots.append(other);angs.append(ang);jos.append(jo)
    return dict(meta=np.array(m),other=np.array(roots),angular=np.array(angs),jo=np.array(jos),coordinates=xy)

def torch_pre(d):return {k:torch.as_tensor(v,dtype=torch.float64) for k,v in d.items()}

def radial_torch(rs,pre,n=64):
    uu,ww=kerr.rule(n);uu=torch.tensor(uu);ww=torch.tensor(ww)
    lam,rt=pre['meta'][:,0],pre['meta'][:,1]
    if bool(torch.any(rs<=rt)):raise ValueError('Predicted source below turning point')
    v=torch.sqrt(rs-rt);q=.5*v[:,None]*(uu+1);r=rt[:,None]+q*q
    product=torch.prod(r[...,None]-pre['other'][:,None,:],dim=-1)
    if bool(torch.any(product<=0)):raise ValueError('Negative reduced radial potential')
    ds=2/torch.sqrt(product);P=r*r+kerr.A*kerr.A-kerr.A*lam[:,None];D=r*r-2*r+kerr.A*kerr.A
    out=torch.stack([ds,ds*kerr.A*P/D,ds*(r*r+kerr.A*kerr.A)*P/D],dim=-1)
    return .5*v[:,None]*(out*ww[None,:,None]).sum(1)

def complete_from_r(rs,pre):
    ints=radial_torch(rs,pre)
    phi=-(pre['jo'][:,1]+ints[:,1]+pre['angular'][:,1])
    T=pre['jo'][:,2]+ints[:,2]+pre['angular'][:,2]
    return torch.stack([rs,phi,T],-1)

class Net(nn.Module):
    def __init__(self,kind):
        super().__init__();self.kind=kind
        self.net=nn.Sequential(nn.Linear(2,32),nn.Tanh(),nn.Linear(32,32),nn.Tanh(),nn.Linear(32,1 if kind=='physics' else 3))
        self.register_buffer('low',torch.tensor(LOW));self.register_buffer('high',torch.tensor(HIGH))
    def forward(self,xy):
        out=self.net(2*(xy-self.low)/(self.high-self.low)-1)
        if self.kind=='physics':return 6+14*torch.sigmoid(out[:,0])
        return out*torch.tensor([10.,.5,20.])+torch.tensor([10.,-7.2,140.])

class Spline:
    def __init__(self,axes,values):
        self.x,self.y=axes;vals=np.asarray(values).reshape(len(self.x),len(self.y),-1)
        self.spl=[RectBivariateSpline(self.x,self.y,vals[:,:,j],kx=3,ky=3,s=0) for j in range(vals.shape[-1])]
    def __call__(self,xy):
        xy=np.asarray(xy)
        if np.any(xy<LOW-1e-13) or np.any(xy>HIGH+1e-13):raise ValueError('OUTSIDE_CHART_no_extrapolation')
        return np.column_stack([s.ev(xy[:,0],xy[:,1]) for s in self.spl])
    def save(self,path):
        out={'x':self.x,'y':self.y,'kx':np.array(3),'ky':np.array(3)}
        for j,s in enumerate(self.spl):
            tx,ty=s.get_knots();out[f'tx{j}']=tx;out[f'ty{j}']=ty;out[f'coeff{j}']=s.get_coeffs()
        np.savez_compressed(path,**out)

def augment(pred,xy):
    rs=pred[:,0];lam=xy[:,0];om=1/(rs**1.5+kerr.A)
    D=1-3/rs+2*kerr.A/rs**1.5
    if np.any(D<=0) or np.any((rs<6)|(rs>20)):raise ValueError('Predicted tuple outside source annulus')
    uts=(1+kerr.A/rs**1.5)/np.sqrt(D);uto=1/np.sqrt(1-2*kerr.RO/(kerr.RO**2+kerr.A**2*kerr.MU0**2))
    g=uto/(uts*(1-om*lam))
    return np.column_stack([pred,g])

def train():
    if (ROOT/'results'/'training.json').exists():raise RuntimeError('Refuse overwrite')
    x,y,xy=grid(9);Y,M,records=reference(xy,phase='calibration')
    np.savez_compressed(ROOT/'results'/'calibration81.npz',xy=xy,values=Y,meta=M)
    x17,y17,col=grid(17);pre=precompute(col,'training_precompute');np.savez_compressed(ROOT/'results'/'collocation_setup.npz',**pre);cp=torch_pre(pre)
    tx=torch.tensor(xy);ty=torch.tensor(Y[:,:3]);ts=torch.tensor(col);scales=torch.tensor([10.,.5,20.])
    logs=[]
    for seed in (11,22,33):
      for kind in ('data','physics'):
        torch.manual_seed(seed);model=Net(kind);t0=time.perf_counter();calls=0
        def closure():
            nonlocal calls
            if kind=='data':return (((model(tx)-ty)/scales)**2).mean()
            rs=model(ts);integ=radial_torch(rs,cp)[:,0]
            resid=(integ-(cp['angular'][:,0]-cp['jo'][:,0]))/.001
            calls+=len(ts)
            return ((model(tx)-ty[:,0])/10).square().mean()+resid.square().mean()
        opt=torch.optim.Adam(model.parameters(),lr=.003);trace=[]
        for step in range(2500):
            opt.zero_grad(set_to_none=True);v=closure()
            if not torch.isfinite(v):raise FloatingPointError('Nonfinite loss')
            v.backward();opt.step()
            if step%250==0:trace.append([step,float(v.detach())])
        opt=torch.optim.LBFGS(model.parameters(),lr=.8,max_iter=200,history_size=40,tolerance_grad=1e-11,tolerance_change=1e-14,line_search_fn='strong_wolfe')
        def lb():
            opt.zero_grad(set_to_none=True);v=closure();v.backward();return v
        opt.step(lb)
        v=float(closure().detach());torch.save(model.state_dict(),ROOT/'models'/f'{kind}_{seed}.pt')
        row={'seed':seed,'kind':kind,'loss':v,'seconds':time.perf_counter()-t0,'training_residual_integral_evaluations':calls,'trace':trace}
        logs.append(row);print(row,flush=True)
        dump('results/training_progress.json',logs)
    dump('results/training.json',logs)
    # Freeze a finite representation before test evaluation. No reference source tuples at these knots.
    x,y,knots=grid(33);kp=precompute(knots,'freeze_precompute');np.savez_compressed(ROOT/'results'/'freeze_setup.npz',**kp);tpk=torch_pre(kp)
    frozen=[]
    for row in logs:
        model=Net(row['kind']);model.load_state_dict(torch.load(ROOT/'models'/f"{row['kind']}_{row['seed']}.pt",weights_only=True))
        with torch.no_grad():
            vals=model(torch.tensor(knots))
            if row['kind']=='physics':vals=complete_from_r(vals,tpk)
            vals=vals.numpy()
        p=ROOT/'models'/f"frozen_{row['kind']}_{row['seed']}.npz"
        np.savez_compressed(p,knots=knots,values=vals,axes_x=x,axes_y=y)
        Spline((x,y),vals).save(ROOT/'models'/f"coeff_{row['kind']}_{row['seed']}.npz")
        frozen.append({'kind':row['kind'],'seed':row['seed'],'file':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    dump('results/FROZEN_MODELS.json',frozen)

if __name__=='__main__':train()
