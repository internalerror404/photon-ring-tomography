"""Shared reproducible CPU utilities. No campaign data or geodesics are loaded."""
from __future__ import annotations
import os, json, time, hashlib, random
from pathlib import Path
os.environ.setdefault('OMP_NUM_THREADS','1')
os.environ.setdefault('MKL_NUM_THREADS','1')
import numpy as np
import torch
from torch import nn
ROOT=Path(__file__).resolve().parent
CFG=json.loads((ROOT/'protocol.json').read_text())
torch.set_num_threads(1)
torch.set_default_dtype(torch.float64)

def seed_all(seed:int)->None:
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)

def tensor(x): return torch.as_tensor(x,dtype=torch.float64)

def mlp(nin:int,nout:int,width:int=32):
    net=nn.Sequential(nn.Linear(nin,width),nn.Tanh(),nn.Linear(width,width),nn.Tanh(),nn.Linear(width,nout))
    # Modest initial output makes scale consistent across models.
    with torch.no_grad(): net[-1].weight.mul_(.2); net[-1].bias.zero_()
    return net

def fit(model, closure, adam_steps:int, lbfgs_steps:int):
    start=time.perf_counter(); opt=torch.optim.Adam(model.parameters(),lr=0.002)
    losses=[]
    for step in range(adam_steps):
        opt.zero_grad(set_to_none=True); loss=closure();
        if not torch.isfinite(loss): raise FloatingPointError(f'Nonfinite loss at {step}')
        loss.backward(); opt.step()
        if step%100==0 or step==adam_steps-1: losses.append([step,float(loss.detach())])
    opt2=torch.optim.LBFGS(model.parameters(),lr=0.8,max_iter=lbfgs_steps,history_size=30,
                          tolerance_grad=1e-10,tolerance_change=1e-13,line_search_fn='strong_wolfe')
    ncall=0
    def lb():
        nonlocal ncall
        ncall+=1; opt2.zero_grad(set_to_none=True); val=closure()
        if not torch.isfinite(val): raise FloatingPointError('Nonfinite LBFGS loss')
        val.backward(); return val
    opt2.step(lb)
    val=float(closure().detach())
    return dict(loss=val,seconds=time.perf_counter()-start,lbfgs_evaluations=ncall,adam_trace=losses)

def dump(name,obj):
    p=ROOT/name; p.write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n'); return p

def relative(a,b):
    return float(np.linalg.norm(np.asarray(a)-np.asarray(b))/max(np.linalg.norm(b),1e-15))
