"""Source-linear deployed Kerr-chart tuple consumer; no ray solver or neural library.
This consumes frozen coefficient bytes, not an unknown-region light estimate.
Only the registered chart/order/finite-observer/source-velocity model is supported.
"""
from pathlib import Path
import hashlib
import numpy as np
from scipy.interpolate import NdBSpline

class FrozenChart:
    def __init__(self,path,expected_sha256):
        data=Path(path).read_bytes()
        if hashlib.sha256(data).hexdigest()!=expected_sha256:raise ValueError('Coefficient hash mismatch')
        f=np.load(path,allow_pickle=False);tx,ty=f['tx0'],f['ty0'];nx,ny=len(tx)-4,len(ty)-4
        if int(f['kx'])!=3 or int(f['ky'])!=3:raise ValueError('Expected cubic representation')
        arrays=[]
        for k in range(3):
            if not np.array_equal(tx,f[f'tx{k}']) or not np.array_equal(ty,f[f'ty{k}']):raise ValueError('Channel knots mismatch')
            arrays.append(f[f'coeff{k}'].reshape(nx,ny))
        c=np.stack(arrays,axis=-1)
        if not np.isfinite(c).all():raise ValueError('Missing coefficient is not zero light')
        self.fn=NdBSpline((tx,ty),c,(3,3),extrapolate=False)
        self.lo=np.array([tx[3],ty[3]]);self.hi=np.array([tx[-4],ty[-4]])
    def tuples(self,coordinates):
        xy=np.asarray(coordinates,float)
        if xy.ndim!=2 or xy.shape[1]!=2 or not np.isfinite(xy).all():raise ValueError('Finite (N,2) coordinates required')
        if np.any(xy<self.lo) or np.any(xy>self.hi):raise ValueError('OUTSIDE_CHART: unknown, not zero')
        out=self.fn(xy);r=out[:,0];lam=xy[:,0];a=.5
        if not np.isfinite(out).all() or np.any((r<6)|(r>20)):raise ValueError('Tuple not supported by registered annulus')
        om=1/(r**1.5+a);ut=(1+a/r**1.5)/np.sqrt(1-3/r+2*a/r**1.5)
        uo=1/np.sqrt(1-200/(10000+a*a*np.cos(np.deg2rad(50))**2))
        g=uo/(ut*(1-om*lam))
        if np.any(g<=0) or not np.isfinite(g).all():raise ValueError('Invalid redshift')
        return np.column_stack([out,g])
