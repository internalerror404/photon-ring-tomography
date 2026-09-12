from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import os
import sys
import time
import traceback
from pathlib import Path
from typing import Any

os.environ.setdefault("OMP_NUM_THREADS","1")
os.environ.setdefault("OPENBLAS_NUM_THREADS","1")
os.environ.setdefault("MKL_NUM_THREADS","1")
os.environ.setdefault("NUMEXPR_NUM_THREADS","1")

import numpy as np
import pandas as pd
import scipy.linalg as sla

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/"source"; INP=ROOT/"inputs"; RES=ROOT/"results"; LOG=ROOT/"logs"; ART=ROOT/"artifacts"
for d in (RES,LOG,ART): d.mkdir(parents=True,exist_ok=True)

REGISTRATION_COMMIT="a0b5bbf7726c2722bf80bbcf1b95603ae2c78660"
AMENDMENT_COMMIT="5169259718ca8920681bdfad3b5dd0e6298ecfda"
EXPECTED={
"PHYSICAL_AND_OPERATOR_ARRAYS.npz":"54204f14b8c834fb3c54dc012c9827e711f339fc6c30251802fea71ac6d8274e",
"SUPPORT_WEIGHTS.npz":"72080e09e722b01a821d2989d706f21eccfc9ce7671d1fa2f18f66bcd56a7952",
"REGULARIZATION_SELECTION.json":"f3739497a08973bec6ed0b5c174188ad1b2321b469efa06750de2b43bcddf090",
"movie007_run.py":"8b80d533cd48400570e505423053a6557e4a2ea6f3d82367adfd5c88b34e5cf1",
"kerr.py":"12abafb39f6d5a6ebf4626e0a05c021d3bd0c5c5ca6ae0abd22632656c8f28cf",
}
VAL_COUNTS={"narrow_hotspot":8,"shearing_spiral":8,"split_merge":8}
TEST_COUNTS={"narrow_hotspot":16,"shearing_spiral":16,"split_merge":16,"radial_plume":16}
VAL_DRAWS=2; TEST_DRAWS=4; SNR_LEVELS=(300,100)
LIB_PER_FAMILY=512; SHORTLIST_PER_FAMILY=32
BEAM_DIRECTIONS=12; BEAM_SIGMA=1.5; BEAM_KEEP=16; JOINT_KEEP=8
FAMILIES=("narrow_hotspot","shearing_spiral","split_merge","radial_plume")
BG_EXPONENTS=np.arange(-6,4)

def sha256(p:Path)->str: return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p:Path,obj:Any)->None:
    def default(x):
        if isinstance(x,np.ndarray): return x.tolist()
        if isinstance(x,np.generic): return x.item()
        raise TypeError(type(x).__name__)
    p.write_text(json.dumps(obj,indent=2,allow_nan=False,default=default)+"\n")

def load_module(path:Path,name:str):
    spec=importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None: raise RuntimeError(path)
    mod=importlib.util.module_from_spec(spec); sys.modules[name]=mod; spec.loader.exec_module(mod); return mod

def authenticate()->dict[str,str]:
    got={}
    for n,e in EXPECTED.items():
        p=(SRC/n) if n.endswith(".py") else (INP/n)
        if not p.is_file(): raise FileNotFoundError(p)
        d=sha256(p)
        if d!=e: raise RuntimeError(f"hash mismatch {n}: {d} != {e}")
        got[n]=d
    return got

def background_beam(B0:np.ndarray,B1:np.ndarray,P:np.ndarray,lam:float,xmap:np.ndarray,y0w:np.ndarray,eigvecs:np.ndarray)->tuple[np.ndarray,np.ndarray]:
    cand=[xmap]
    for j in range(eigvecs.shape[1]):
        cand.append(xmap+BEAM_SIGMA*eigvecs[:,j]); cand.append(xmap-BEAM_SIGMA*eigvecs[:,j])
    X=np.column_stack(cand); R=y0w[:,None]-B0@X
    scores=np.sum(R*R,axis=0)+lam*np.einsum("ik,ij,jk->k",X,P,X,optimize=True)
    order=np.lexsort((np.arange(len(scores)),scores))[:BEAM_KEEP]
    return X[:,order],scores[order]

def posterior_directions(B0:np.ndarray,B1:np.ndarray,P:np.ndarray,lam:float)->np.ndarray:
    H0=B0.T@B0+lam*P; F1=B1.T@B1; n=H0.shape[0]
    vals,vecs=sla.eigh(F1,H0,subset_by_index=[n-BEAM_DIRECTIONS,n-1],check_finite=False)
    return vecs[:,np.argsort(vals)[::-1]]

def library(r2,arrays,m7)->dict[str,Any]:
    rng=np.random.default_rng(140090); specs=[]; famidx=[]; variants=[]
    for fi,fam in enumerate(FAMILIES):
        for _ in range(LIB_PER_FAMILY):
            p=r2.draw_feature_params(fam,rng)
            for v in (0,1): specs.append({"feature":p,"variant":v,"family":fam}); famidx.append(fi); variants.append(v)
    q8=r2.render_many_features(arrays,specs,8,1,m7.OBS_TIMES); q12=r2.render_many_features(arrays,specs,12,1,m7.OBS_TIMES)
    return {"specs":specs,"family_index":np.asarray(famidx),"variant":np.asarray(variants),"q8":q8,"q12":q12}

def choose_shortlist(T:np.ndarray,r:np.ndarray,famidx:np.ndarray)->np.ndarray:
    dot=T.T@r; n2=np.sum(T*T,axis=0); alpha=np.clip(dot/np.maximum(n2,1e-15),.5,1.5)
    score=np.dot(r,r)-2*alpha*dot+alpha*alpha*n2+((alpha-1.0)/0.3)**2; keep=[]
    for fi in range(len(FAMILIES)):
        ids=np.where(famidx==fi)[0]; ord_=np.lexsort((ids,score[ids]))[:SHORTLIST_PER_FAMILY]; keep.extend(ids[ord_].tolist())
    return np.asarray(keep,dtype=int)

def reconstruct_one(r2,m7,arrays,lib,W,eval_mesh,L,B0,B1,P,lam,eigvecs,y0,y1,std0,std1,true_bg_coeff=None)->dict[str,Any]:
    y0w=(y0-arrays["base_q8_n0"])/std0; y1w=(y1-arrays["base_q8_n1"])/std1
    H=B0.T@B0+lam*P; xmap=sla.solve(H,B0.T@y0w,assume_a="pos",check_finite=False)
    X,ds=background_beam(B0,B1,P,lam,xmap,y0w,eigvecs); rmap=y1w-B1@X[:,0]
    T=lib["q8"]/std1[:,None]; shortlist=choose_shortlist(T,rmap,lib["family_index"]); Ts=T[:,shortlist]; tnorm=np.sum(Ts*Ts,axis=0)
    candidates=[]
    for kb in range(X.shape[1]):
        rr=y1w-B1@X[:,kb]; dots=Ts.T@rr; alphas=np.clip(dots/np.maximum(tnorm,1e-15),.5,1.5)
        fs=np.dot(rr,rr)-2*alphas*dots+alphas*alphas*tnorm+((alphas-1.0)/0.3)**2; total=ds[kb]+fs
        for j in range(len(shortlist)): candidates.append((float(total[j]),kb,int(shortlist[j]),float(alphas[j])))
    candidates.sort(key=lambda x:(x[0],x[1],x[2])); top=candidates[:JOINT_KEEP]
    sc=np.asarray([q[0] for q in top]); w=np.exp(-.5*(sc-sc.min())); w/=w.sum()
    xbar=sum(wi*X[:,q[1]] for wi,q in zip(w,top)); cbar=r2.x_to_coeff(xbar,L)
    feat=np.zeros((len(m7.MOVIE_TIMES),len(m7.R_EVAL),len(m7.PHI_EVAL))); fq8=np.zeros(832); fq12=np.zeros(832); famprob={f:0.0 for f in FAMILIES}
    for wi,q in zip(w,top):
        idx=q[2]; a=q[3]; spec=lib["specs"][idx]
        feat+=wi*a*r2.source_grid_values(spec["feature"],int(spec["variant"]),eval_mesh); fq8+=wi*a*lib["q8"][:,idx]; fq12+=wi*a*lib["q12"][:,idx]; famprob[spec["family"]]+=float(wi)
    q0=top[0]; cpoint=r2.x_to_coeff(X[:,q0[1]],L); sp0=lib["specs"][q0[2]]; fpoint=q0[3]*r2.source_grid_values(sp0["feature"],int(sp0["variant"]),eval_mesh)
    coverage=None
    if true_bg_coeff is not None:
        xtrue=r2.coeff_to_x(true_bg_coeff[:,None],L)[:,0]; coverage=float(np.linalg.norm(B1@(X-xtrue[:,None]),axis=0).min())
    entropy=float(-np.sum(w*np.log(np.maximum(w,1e-300))))
    return {"background_coeff":cbar,"feature_eval":feat,"feature_q8":fq8,"feature_q12":fq12,"point_background_coeff":cpoint,"point_feature_eval":fpoint,"top":top,"weights":w,"family_probability":famprob,"entropy":entropy,"effective_hypotheses":float(np.exp(entropy)),"beam_forecast_coverage":coverage,"shortlist":shortlist}

def eval_method(r2,m7,split,obs,bg_coeff,feat_eval,W,fullW,method,arm,snr): return r2.evaluate_predictions(m7,split,obs,bg_coeff,feat_eval,W,fullW,method,arm,snr)

def self_test()->dict[str,Any]:
    got=authenticate(); r2=load_module(SRC/"movie009_r2_source.py","movie009_r2_m14"); m7=r2.load_m7(); arrays=np.load(INP/"PHYSICAL_AND_OPERATOR_ARRAYS.npz",allow_pickle=False)
    sigma,sh0,sh1=r2.noise_calibration(arrays); L=np.asarray(arrays["H_chol"]); P=np.asarray(arrays["penalty"]); bm=r2.background_map(arrays["A_q8_n0"],sigma*sh0,L,P,0)
    B1=sla.solve_triangular(L,(arrays["A_q8_n1"]/(sigma*sh1)[:,None]).T,lower=True,check_finite=False).T; lam=bm["scale"]; V=posterior_directions(bm["B"],B1,P,lam)
    err=np.max(np.abs(V.T@(bm["B"].T@bm["B"]+lam*P)@V-np.eye(BEAM_DIRECTIONS)))
    return {"hashes":got,"directions_shape":V.shape,"H_orthonormality_error":float(err),"pass":bool(err<1e-8)}

# The full registered main function is deposited in the accompanying artifact package and hash-frozen before execution.
# This repository source records all scientific mechanics and the mechanical self-test; execution uses the identical full source bytes.

if __name__=="__main__":
    if "--self-test" in sys.argv: print(json.dumps(self_test(),indent=2))
    else: raise RuntimeError("Use the full hash-frozen Movie014 source from the registered artifact package for execution.")
