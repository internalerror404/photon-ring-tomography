"""Fixed-budget inverse tests using the physical pilot003 source-crossing camera.
Euler-inspired staging is an ablation of a package, not a replication of Euler PINNs.
"""
import os
os.environ.setdefault('OMP_NUM_THREADS','1');os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
from build003 import *
import torch
from torch import nn
from scipy.interpolate import BSpline
import pandas as pd
import hashlib

torch.set_default_dtype(torch.float64);torch.set_num_threads(1)
D=ROOT/'results';CK=D/'models';CK.mkdir(exist_ok=True)

def ten(x):return torch.as_tensor(x,dtype=torch.float64)

def features(c,stationary=False):
    r,phi,t=c.unbind(-1);s=phi-r.pow(-1.5)*t
    xx=[(r-9)/3]
    for k in range(1,4):xx.extend([torch.cos(k*s),torch.sin(k*s)])
    if not stationary:xx.append((t+25)/30)
    return torch.stack(xx,-1)

class Field(nn.Module):
    def __init__(self,width=32,stationary=False):
        super().__init__();self.stationary=stationary
        self.net=nn.Sequential(nn.Linear(7 if stationary else 8,width),nn.Tanh(),nn.Linear(width,width),nn.Tanh(),nn.Linear(width,1))
        with torch.no_grad():self.net[-1].weight.mul_(.2);self.net[-1].bias.zero_()
    def forward(self,x):return self.net(features(x,self.stationary)).squeeze(-1)

class SumField(nn.Module):
    def __init__(self,base,res):super().__init__();self.base=base;self.res=res
    def forward(self,x):return self.base(x)+self.res(x)

def fit(model,closure,adam,lbfgs):
    start=time.perf_counter();params=[p for p in model.parameters() if p.requires_grad]
    opt=torch.optim.Adam(params,lr=.002);trace=[]
    for k in range(adam):
        opt.zero_grad(set_to_none=True);loss=closure()
        if not torch.isfinite(loss):raise RuntimeError('Nonfinite training objective')
        loss.backward();opt.step()
        if k%100==0 or k==adam-1:trace.append([k,float(loss.detach())])
    opt=torch.optim.LBFGS(params,lr=.8,max_iter=lbfgs,history_size=30,tolerance_change=1e-12,tolerance_grad=1e-9,line_search_fn='strong_wolfe')
    calls=0
    def cl():
        nonlocal calls
        calls+=1;opt.zero_grad(set_to_none=True);z=closure();z.backward();return z
    opt.step(cl)
    return dict(seconds=time.perf_counter()-start,loss=float(closure().detach()),lbfgs_evaluations=calls,trace=trace)


def noise_parameters():
    out=np.load(D/'observations.npz');sig=float(out['sigma'])*np.sqrt(out['areas']);return out,sig


def evaluation_grid():
    rr,pp,tt=np.meshgrid(np.linspace(6,12,13),np.linspace(0,2*np.pi,48,endpoint=False),np.linspace(-52,2,73),indexing='ij')
    return np.stack([rr.ravel(),pp.ravel(),tt.ravel()],-1)


def predict(model,xy):
    with torch.no_grad():return np.concatenate([(1+model(ten(x))).numpy() for x in np.array_split(xy,max(1,len(xy)//40000))])


def source_error(pred,truth,xy,mask):
    w=xy[mask,0]
    return float(np.sqrt(np.sum(w*(pred[mask]-truth[mask])**2)/np.sum(w*(truth[mask]-1)**2)))


def run():
    val=json.loads((D/'forward_validation.json').read_text())
    if not all(val['gates'].values()):raise RuntimeError('Forward prerequisites not satisfied')
    if (D/'inverse_results.json').exists():raise RuntimeError('Refuse overwriting inverse results')
    camera=dict(np.load(D/'camera_q4.npz'));obs,sig=noise_parameters();xy=evaluation_grid();old=xy[:,2]<=-12
    truth={v:src(xy[:,0],xy[:,1],xy[:,2],v) for v in ['matched','event1','event2']}
    arrays=dict(eval_coordinates=xy,old_mask=old,**{'truth_'+k:v for k,v in truth.items()});rows=[]
    np.savez_compressed(D/'evaluation_grid.npz',**arrays)
    for seed in [11,22,33]:
        noise=np.random.default_rng(seed).normal(size=len(sig))
        # Same one noise array across the source twins and exactly shared direct data.
        for method in ['comoving_data','comoving_robust_PINN','staged_residual_PINN']:
            for acq,variant in [('direct','matched'),('all','matched'),('all','event1'),('all','event2')]:
                torch.manual_seed(seed);sel=camera['orders']==0 if acq=='direct' else np.ones(len(sig),bool)
                c=ten(camera['coords'][sel]);w=ten(camera['weights'][sel]);std=ten(sig[sel]);
                yr=obs['y_'+variant][sel];yn=yr+sig[sel]*noise[sel]
                target=ten(yn-camera['weights'][sel].sum(1))
                rng=np.random.default_rng(seed+700);coll=ten(np.stack([rng.uniform(6,12,256),rng.uniform(0,2*np.pi,256),rng.uniform(-52,2,256)],-1))
                def objective(model,penalty):
                    def closure():
                        y=(model(c)*w).sum(1);loss=((y-target)/std).square().mean()
                        if penalty:
                            co=coll.clone().requires_grad_(True);field=model(co)
                            grad=torch.autograd.grad(field.sum(),co,create_graph=True)[0]
                            z=(grad[:,2]+co[:,0].pow(-1.5)*grad[:,1])/.03
                            h=torch.where(abs(z)<=1,z*z,2*abs(z)-1)
                            loss=loss+.03*h.mean()
                        return loss
                    return closure
                if method=='staged_residual_PINN':
                    base=Field(16,True);first=fit(base,objective(base,False),200,20)
                    for p in base.parameters():p.requires_grad_(False)
                    model=SumField(base,Field(24,False));second=fit(model,objective(model,True),400,40)
                    info=dict(seconds=first['seconds']+second['seconds'],loss=second['loss'],stages=[first,second])
                else:
                    model=Field(32);info=fit(model,objective(model,method!='comoving_data'),600,60)
                pred=predict(model,xy)
                with torch.no_grad():yh=(1+model(c))*w;yh=yh.sum(1).numpy()
                key=f'{seed}_{method}_{acq}_{variant}';np.save(D/f'prediction_{key}.npy',pred);torch.save(model.state_dict(),CK/f'{key}.pt')
                np.savez_compressed(D/f'fit_observations_{key}.npz',row_indices=np.where(sel)[0],predicted=yh,clean=yr,noisy=yn,std=sig[sel])
                evaluated=['matched','event1','event2'] if acq=='direct' else [variant]
                for v in evaluated:
                    event=(abs(xy[:,2]+26)<5)|((v=='event2')&(abs(xy[:,2]+43)<5))
                    rows.append(dict(seed=seed,method=method,acquisition=acq,source=v,
                        old_contrast_error=source_error(pred,truth[v],xy,old),
                        event_window_contrast_error=source_error(pred,truth[v],xy,event),
                        noisy_chi2=float(np.mean(((yh-yn)/sig[sel])**2)),clean_chi2=float(np.mean(((yh-yr)/sig[sel])**2)),
                        negative_fraction=float(np.mean(pred<0)),parameter_count=sum(p.numel() for p in model.parameters()),**info))
                (D/'inverse_results.json').write_text(json.dumps(dict(rows=rows,scope='One background with two designed old-event alternatives; three seeds; not independent astrophysical population'),indent=2))
                print(seed,method,acq,variant,round(rows[-1]['old_contrast_error'],4),round(info['seconds'],1),flush=True)
    pd.DataFrame([{k:v for k,v in r.items() if k not in ['stages','trace']} for r in rows]).to_csv(D/'inverse_per_seed.csv',index=False)


def spline_basis(xy):
    r,p,t=xy[...,0],xy[...,1],xy[...,2];s=p-r**(-1.5)*t
    rb=np.stack([(r-9)**k/3**k for k in range(4)],-1)
    knots=np.r_[[-54.]*4,np.linspace(-54,4,12)[1:-1],[4.]*4]
    tb=BSpline(knots,np.eye(len(knots)-4),3,extrapolate=True)(t)
    ab=np.stack([np.ones_like(s)]+[f(k*s) for k in range(1,4) for f in [np.cos,np.sin]],-1)
    return (rb[...,None,:,None]*ab[..., :,None,None]*tb[...,None,None,:]).reshape(*r.shape,-1)


def classical():
    from scipy.linalg import svd
    cam=dict(np.load(D/'camera_q4.npz'));obs,sig=noise_parameters();xy=evaluation_grid();old=xy[:,2]<=-12
    # Geometry/basis fixed, so build each design and decomposition once for all sources/seeds.
    rows=[]
    for acq in ['direct','all']:
        sel=cam['orders']==0 if acq=='direct' else np.ones(len(sig),bool)
        c=cam['coords'][sel];w=cam['weights'][sel];basis=spline_basis(c)
        A=np.einsum('nq,nqd->nd',w,basis)/sig[sel,None];del basis
        U,s,V=svd(A,full_matrices=False)
        E=spline_basis(xy)
        for seed in [11,22,33]:
            noise=np.random.default_rng(seed).normal(size=len(sig))[sel]
            for variant in (['matched'] if acq=='direct' else ['matched','event1','event2']):
                yr=obs['y_'+variant][sel];yn=yr+sig[sel]*noise;z=(yn-w.sum(1))/sig[sel];uz=U.T@z
                lambdas=s.max()**2*np.logspace(-12,-1,36)
                gcv=[]
                for l in lambdas:
                    f=s*s/(s*s+l);res=z-U@(f*uz)
                    gcv.append(float(res@res/max(len(z)-f.sum(),1e-5)**2))
                lam=lambdas[np.argmin(gcv)];coef=V.T@(s/(s*s+lam)*uz);pred=1+E@coef;yh=w.sum(1)+sig[sel]*(A@coef)
                key=f'{seed}_fourier_spline_ridge_{acq}_{variant}';np.save(D/f'prediction_{key}.npy',pred)
                np.savez_compressed(D/f'linear_fit_{key}.npz',coefficients=coef,alpha=lam,predicted=yh,clean=yr,noisy=yn,rows=np.where(sel)[0])
                for vv in (['matched','event1','event2'] if acq=='direct' else [variant]):
                    tr=src(xy[:,0],xy[:,1],xy[:,2],vv)
                    rows.append(dict(seed=seed,method='fourier_spline_ridge',acquisition=acq,source=vv,
                        old_contrast_error=source_error(pred,tr,xy,old),noisy_chi2=float(np.mean(((yh-yn)/sig[sel])**2)),
                        clean_chi2=float(np.mean(((yh-yr)/sig[sel])**2)),negative_fraction=float(np.mean(pred<0)),alpha=float(lam),coefficient_count=A.shape[1]))
                print('classical',seed,acq,variant,rows[-1]['old_contrast_error'],flush=True)
    pd.DataFrame(rows).to_csv(D/'classical_per_seed.csv',index=False)
    (D/'classical_results.json').write_text(json.dumps(rows,indent=2))

if __name__=='__main__':
    import sys
    classical() if '--classical' in sys.argv else run()
