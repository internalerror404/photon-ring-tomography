"""Cached, source-linear Kerr-patch rendering. No physical ray or root calls.
Input bytes are authenticated before use. The Jacobian and transfer surrogates
are deliberately separate from the cached physical reference.
"""
from __future__ import annotations
import os
os.environ.setdefault('OMP_NUM_THREADS','1')
os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
os.environ.setdefault('MKL_NUM_THREADS','1')
import json, hashlib, time, sys
from pathlib import Path
import numpy as np
from numpy.polynomial.legendre import leggauss
from scipy.interpolate import NdBSpline, RectBivariateSpline
ROOT=Path(__file__).resolve().parents[1]
CFG=json.loads((ROOT/'protocol.json').read_text())
TIMES=np.linspace(0.,20.,8)
LOW=np.array([.5,-1.5]); HIGH=np.array([2.,-1.3])

def dump(rel, obj):
    def default(x):
        if isinstance(x,np.ndarray):return x.tolist()
        if isinstance(x,np.generic):return x.item()
        raise TypeError(type(x).__name__)
    (ROOT/rel).write_text(json.dumps(obj,indent=2,allow_nan=False,default=default)+'\n')

def authenticate():
    manifest=json.loads((ROOT/'INPUT_MANIFEST.json').read_text())
    for item in manifest['files']:
        p=ROOT/item['local_path']
        if hashlib.sha256(p.read_bytes()).hexdigest()!=item['sha256']:
            raise RuntimeError('Input hash mismatch: '+str(p))
    return manifest

class CachedRenderer:
    def __init__(self):
        authenticate()
        self.cache=np.load(ROOT/'inputs/ALL_EVALUATION_ARRAYS.npz',allow_pickle=False)
        self.areas=self.cache['pixel_areas'].copy()
        self.splines={}
        for n in [9,17,33]:
            f=np.load(ROOT/f'inputs/coeff_classical{n}.npz',allow_pickle=False)
            tx,ty=f['tx0'],f['ty0'];nx,ny=len(tx)-4,len(ty)-4
            co=np.stack([f[f'coeff{j}'].reshape(nx,ny) for j in range(3)],axis=-1)
            self.splines[n]=NdBSpline((tx,ty),co,(3,3),extrapolate=False)
        geo=np.load(ROOT/'inputs/freeze_setup.npz',allow_pickle=False)
        xy=geo['coordinates'];xx=np.unique(xy[:,0]);zz=np.unique(xy[:,1])
        if not np.array_equal(xy,np.stack(np.meshgrid(xx,zz,indexing='ij'),-1).reshape(-1,2)):
            raise RuntimeError('Metadata is not the recorded tensor grid')
        self.jac=RectBivariateSpline(xx,zz,geo['meta'][:,3].reshape(33,33),kx=3,ky=3,s=0)
    def tuples(self,xy,n=33):
        xy=np.asarray(xy)
        if not np.isfinite(xy).all() or np.any(xy<LOW) or np.any(xy>HIGH):
            raise ValueError('Outside supported chart, never zero filled')
        p=self.splines[n](xy);r=p[:,0];a=.5
        if not np.isfinite(p).all() or np.any((r<6)|(r>20)):raise ValueError('Invalid source tuple')
        om=1/(r**1.5+a);ut=(1+a/r**1.5)/np.sqrt(1-3/r+2*a/r**1.5)
        uo=1/np.sqrt(1-200/(10000+a*a*np.cos(np.deg2rad(50))**2))
        g=uo/(ut*(1-om*xy[:,0]))
        return np.column_stack([p,g])
    def design(self,q,n=33,reference=False,exact_saved_weights=False):
        if reference or exact_saved_weights:
            if q not in (6,10,16):raise ValueError('No cached physical reference for this rule')
            xy=self.cache[f'detector_xy_q{q}'];w=self.cache[f'weights_q{q}'];pix=self.cache[f'pixels_q{q}']
            vals=self.cache[f'reference_tuples_q{q}'] if reference else self.tuples(xy,n)
        else:
            u,ww=leggauss(q);ex=np.linspace(.5,2.,5);ez=np.linspace(-1.5,-1.3,5)
            p=[];weights=[];px=[]
            for i in range(4):
                for j in range(4):
                    xx=(ex[i]+ex[i+1])/2+(ex[i+1]-ex[i])*u/2
                    zz=(ez[j]+ez[j+1])/2+(ez[j+1]-ez[j])*u/2
                    xy=np.stack(np.meshgrid(xx,zz,indexing='ij'),-1).reshape(-1,2)
                    w=((ex[i+1]-ex[i])*(ez[j+1]-ez[j])/4*np.outer(ww,ww)).ravel()
                    jac=self.jac.ev(xy[:,0],xy[:,1])
                    if np.any(jac<=0):raise ValueError('Nonpositive Jacobian')
                    p.append(xy);weights.append(w*jac);px.extend([4*i+j]*len(xy))
            xy=np.concatenate(p);w=np.concatenate(weights);pix=np.array(px)
            vals=self.tuples(xy,n)
        assert np.array_equal(pix,np.repeat(np.arange(16),q*q))
        # [time, pixel, quadrature-node, source coordinate]
        r,phi,T,g=vals.T
        coords=np.stack([np.broadcast_to(r,(8,len(r))),np.broadcast_to(phi,(8,len(r))),TIMES[:,None]-T+145.],-1).reshape(8,16,q*q,3)
        kernel=(w*g**3).reshape(16,q*q)
        return {'q':q,'xy':xy,'weights':w,'pixel':pix,'tuples':vals,'coords':coords,'kernel':kernel,'areas':self.areas}

def omega(r):return 1/(r**1.5+.5)

def basis(coords):
    r,phi,t=np.moveaxis(coords,-1,0);R=(r-11)/5;psi=phi-omega(r)*t
    bg=[np.ones_like(r),R,R*R,np.cos(psi),np.sin(psi),np.cos(2*psi),np.sin(2*psi)]
    e1=np.exp(-.5*((r-8.5)/1.5)**2-.5*((t-1)/3)**2)
    e2=np.exp(-.5*((r-13.5)/1.7)**2-.5*((t-13)/3)**2)
    return np.stack(bg+[e1,e2],-1)

def fields(coords,c):return 1+np.einsum('...k,k->...',basis(coords),c)

def response(design,values):
    # Preserve node integration then pixel/time observation ordering.
    return (values*design['kernel'][None,:,:]).sum(axis=2).reshape(128)

def linear_components(d):
    A=np.einsum('tpqk,pq->tpk',basis(d['coords']),d['kernel']).reshape(128,9)
    base=np.broadcast_to(d['kernel'].sum(axis=1),(8,16)).reshape(128).copy()
    return base,A

def truth_coefficients(events=False):
    c=np.r_[np.random.default_rng(1729).normal(0,.08,7),[.5,.35] if events else [0.,0.]]
    return c

def noise_std(areas,sigma):return np.tile(sigma*np.sqrt(areas),8)

def relative(a,b):return float(np.linalg.norm(a-b)/max(np.linalg.norm(b),1e-15))

if __name__=='__main__':
    print(authenticate()['base_commit'])
