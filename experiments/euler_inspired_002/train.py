"""Fixed manufactured study. Neither Euler's equations nor Kerr maps are run."""
import os
os.environ.setdefault('OMP_NUM_THREADS','1');os.environ.setdefault('MKL_NUM_THREADS','1')
import copy,json,time,hashlib,platform
from pathlib import Path
import numpy as np
import torch
from torch import nn
from numpy.polynomial.legendre import leggauss
ROOT=Path(__file__).resolve().parent
CFG=json.loads((ROOT/'protocol.json').read_text())
torch.set_num_threads(1);torch.set_default_dtype(torch.float64)

def forcing(s):return .12+.3/(1+400*(s-.37)**2)+.1/(1+1600*(s-.78)**2)
def exact(s):return .12*s+.015*(np.arctan(20*(s-.37))+np.arctan(7.4))+.0025*(np.arctan(40*(s-.78))+np.arctan(31.2))
class Model(nn.Module):
 def __init__(self):
  super().__init__();self.net=nn.Sequential(nn.Linear(1,32),nn.Tanh(),nn.Linear(32,32),nn.Tanh(),nn.Linear(32,1))
  with torch.no_grad():self.net[-1].weight.mul_(.1);self.net[-1].bias.zero_()
 def forward(self,s):return s*self.net((2*s-1)[:,None]).squeeze(-1)
class Additive(nn.Module):
 def __init__(self,base):
  super().__init__();self.base=copy.deepcopy(base)
  for p in self.base.parameters():p.requires_grad_(False)
  self.correction=Model()
  with torch.no_grad():self.correction.net[-1].weight.zero_();self.correction.net[-1].bias.zero_()
 def forward(self,s):return self.base(s)+self.correction(s)

def value_deriv(model,s):
 x=torch.as_tensor(s).detach().clone().requires_grad_(True);v=model(x)
 d=torch.autograd.grad(v.sum(),x)[0]
 return v.detach().numpy(),d.detach().numpy()

def choose_coll(model):
 pool=np.linspace(0,1,2049);v,d=value_deriv(model,pool);err=np.abs(d-forcing(pool))
 # Fixed at start of stage: retain global coverage, add distinct high residual points.
 fixed=np.linspace(0,1,96);sel=[]
 for j in np.argsort(-err):
  if np.min(np.abs(fixed-pool[j]))>1e-12:
   sel.append(pool[j])
   if len(sel)==96:break
 return np.r_[fixed,sel], {'screened_points':2049,'selected_extra':96}

def fit(model,coll,adam_steps,lbfgs_steps):
 xlab=np.linspace(np.exp(-8),1,24);slab=-np.log(xlab)/8
 sx=torch.tensor(slab);yy=torch.tensor(exact(slab));c=torch.tensor(coll)
 pars=[p for p in model.parameters() if p.requires_grad]
 calls=0;trace=[];tic=time.perf_counter()
 def loss():
  nonlocal calls
  calls+=1;xx=c.detach().clone().requires_grad_(True);v=model(xx)
  dv=torch.autograd.grad(v.sum(),xx,create_graph=True)[0]
  residual=(dv-forcing(xx))/.2
  return residual.square().mean()+.1*((model(sx)-yy)/.2).square().mean()
 opt=torch.optim.Adam(pars,lr=.002)
 for i in range(adam_steps):
  opt.zero_grad(set_to_none=True);l=loss()
  if not torch.isfinite(l):raise FloatingPointError('Nonfinite loss')
  l.backward();opt.step()
  if i%100==0:trace.append([i,float(l.detach())])
 opt=torch.optim.LBFGS(pars,lr=.8,max_iter=lbfgs_steps,history_size=40,tolerance_grad=1e-12,tolerance_change=1e-15,line_search_fn='strong_wolfe')
 def closure():
  opt.zero_grad(set_to_none=True);l=loss();l.backward();return l
 opt.step(closure)
 return {'loss':float(loss().detach()),'calls':calls,'seconds':time.perf_counter()-tic,'trace':trace,'parameters':sum(p.numel() for p in pars),'total_parameters':sum(p.numel() for p in model.parameters())}

def detector(fn,q):
 edges=np.linspace(0,1,13);u,w=leggauss(q);s=(edges[:-1,None]+edges[1:,None])/2+np.diff(edges)[:,None]/2*u
 tau=8*s+fn(s);weight=np.diff(edges)[:,None]/2*w*8*np.exp(-8*s)
 F=np.stack([2+np.cos(3*tau),2+np.sin(3*tau)],axis=-1)
 area=np.exp(-8*edges[:-1])-np.exp(-8*edges[1:])
 return (weight[...,None]*F).sum(1)/np.sqrt(area[:,None])

def run():
 if (ROOT/'neural_results.json').exists():raise RuntimeError('Existing results; choose fresh directory')
 rows=[];saved={};grid=np.linspace(0,1,8193);truth=exact(grid);ref=detector(exact,128)
 for seed in CFG['seeds']:
  torch.manual_seed(seed);base=Model();coll=np.linspace(0,1,192)
  initial=fit(base,coll,900,100);torch.save(base.state_dict(),ROOT/f'initial_{seed}.pt')
  for kind in ['continued','boost_fixed','boost_residual']:
   torch.manual_seed(seed+1000)
   model=copy.deepcopy(base) if kind=='continued' else Additive(base)
   points,allocation=(choose_coll(base) if kind=='boost_residual' else (coll,{'screened_points':0,'selected_extra':0}))
   out=fit(model,points,900,140)
   v,d=value_deriv(model,grid)
   def fn(ss):
    with torch.no_grad():return model(torch.as_tensor(ss.reshape(-1))).numpy().reshape(ss.shape)
   y=detector(fn,64);ys=detector(fn,128)
   norms=np.linalg.norm(ref,axis=0);errors=np.linalg.norm(y-ref,axis=0)/norms
   out.update(seed=seed,arm=kind,initial_training=initial,allocation=allocation,max_r_error=float(np.max(np.abs(v-truth))),pde_rms=float(np.sqrt(np.mean((d-forcing(grid))**2))),pde_linf=float(np.max(abs(d-forcing(grid)))),detector_relative_by_channel=errors.tolist(),max_detector_relative=float(max(errors)),detector_q64_128=float(np.max(abs(y-ys))))
   rows.append(out);saved[f'{seed}_{kind}_values']=v;saved[f'{seed}_{kind}_derivatives']=d;saved[f'{seed}_{kind}_training_points']=points
   for N in [32,64,128]:
    kk=np.linspace(0,1,N+1); vv,dd=value_deriv(model,kk)
    saved[f'{seed}_{kind}_knots_{N}']=np.stack([kk,vv,dd])
   torch.save(model.state_dict(),ROOT/f'{kind}_{seed}.pt')
   (ROOT/'neural_results.json').write_text(json.dumps({'results':rows,'reference_q64_128':float(np.max(abs(detector(exact,64)-ref))),'environment':{'torch':torch.__version__,'numpy':np.__version__,'python':platform.python_version(),'cpu_threads':1,'dtype':'float64'},'protocol_sha256':hashlib.sha256((ROOT/'protocol.json').read_bytes()).hexdigest()},indent=2)+'\n')
   print(seed,kind,'det',out['max_detector_relative'],'rmax',out['max_r_error'],'pde',out['pde_rms'],'seconds',out['seconds'],flush=True)
 saved.update(grid=grid,truth=truth,reference=ref);np.savez_compressed(ROOT/'neural_arrays.npz',**saved)
if __name__=='__main__':run()
