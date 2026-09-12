"""CACHE_REBUILD_001: a NEW Paper-II cache, never a replacement for old R2 bytes.

Pure basis/metric definitions plus a fail-closed, source-frozen cache producer.
No inverse fit, model selection, historical reconstruction, or posterior is run.
"""
from __future__ import annotations
import argparse, collections, hashlib, json, os, platform, resource, signal, sys, time, traceback
from pathlib import Path
for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[key] = '1'
import numpy as np
import scipy
from scipy.interpolate import BSpline
from scipy.ndimage import gaussian_filter
import kerr_chart003_original as kerr
import numerical_fields as fields
ROOT = Path(__file__).resolve().parents[1]
R = np.linspace(6.,13.,32)
PHI = np.linspace(-np.pi,np.pi,64,endpoint=False)
T = np.linspace(-32.,28.,31)
FRAMES = -2.*np.arange(15)
OBS = 2.*np.arange(13)
TC = np.linspace(-32.,28.,17)
RK = np.r_[[6.]*4,9.5,[13.]*4]
LIMITS = {'separated_quadrature':28000,'compactified_ode':80}
TOLS = np.array([2e-6,2e-7,2e-6,2e-7])

def jsonable(x):
    if isinstance(x,np.ndarray): return x.tolist()
    if isinstance(x,np.generic): return x.item()
    raise TypeError(type(x).__name__)

def dump(p,obj):
    with Path(p).open('x',encoding='utf8') as f:
        json.dump(obj,f,indent=2,sort_keys=True,allow_nan=False,default=jsonable); f.write('\n')

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def radial(r):
    r=np.asarray(r,float); a=BSpline(RK,np.eye(5),3,extrapolate=False)(r)
    return np.where(np.isfinite(a),a,0.)

def angular(p):
    p=np.asarray(p,float)
    return np.stack([np.ones_like(p)]+[fn(m*p) for m in (1,2,3) for fn in (np.cos,np.sin)],axis=-1)

def temporal(t):
    t=np.asarray(t,float)
    return np.maximum(1.-np.abs(t[...,None]-TC)/(TC[1]-TC[0]),0.)*((t>=TC[0])&(t<=TC[-1]))[...,None]

def trap(x):
    w=np.empty(len(x)); w[0]=(x[1]-x[0])/2; w[-1]=(x[-1]-x[-2])/2
    w[1:-1]=(x[2:]-x[:-2])/2
    return w

def gram():
    br,ba,bt=radial(R),angular(PHI),temporal(T)
    hr=br.T@((R*trap(R))[:,None]*br)
    ha=ba.T@((2*np.pi/64)*ba)
    ht=bt.T@(trap(T)[:,None]*bt)
    return np.kron(np.kron(hr,ha),ht)

def evaluate(c,r,p,t):
    return np.einsum('...r,...a,...t,rat->...',radial(r),angular(p),temporal(t),np.asarray(c).reshape(5,7,17),optimize=True)

def chart_rule(q):
    x,w=np.polynomial.legendre.leggauss(q)
    le=np.linspace(.5,3.,9);ze=np.linspace(.3,.7,9)
    points=[];weights=[];pixels=[]
    for i in range(8):
        for j in range(8):
            ll=(le[i]+le[i+1])/2+(le[i+1]-le[i])/2*x
            zz=(ze[j]+ze[j+1])/2+(ze[j+1]-ze[j])/2*x
            for a in range(q):
                for b in range(q):
                    points.append((ll[a],zz[b]));weights.append((le[i+1]-le[i])*(ze[j+1]-ze[j])/4*w[a]*w[b]);pixels.append(8*i+j)
    return np.array(points),np.array(weights),np.array(pixels,dtype=np.int64)

class Ledger:
    def __init__(self,root):
        self.file=(root/'physical_calls.jsonl').open('x',buffering=1)
        self.count=collections.Counter();self.tail='0'*64;self.seq=0;self.pending=None;self.started=time.monotonic()
    def write(self,obj):
        obj.update(sequence=self.seq,previous_sha256=self.tail)
        payload=json.dumps(obj,sort_keys=True,separators=(',',':'),allow_nan=False,default=jsonable)
        self.tail=hashlib.sha256(payload.encode()).hexdigest()
        self.file.write(json.dumps({'event':obj,'sha256':self.tail},separators=(',',':'),default=jsonable)+'\n')
        self.file.flush()
        if self.seq%256==0:os.fsync(self.file.fileno())
        self.seq+=1
    def begin(self,phase,method,inputs):
        if self.pending is not None:raise RuntimeError('nested physical call')
        if method not in LIMITS or self.count[method]>=LIMITS[method]:raise RuntimeError('physical cap reached')
        if time.monotonic()-self.started>900:raise TimeoutError('900-second cache budget exhausted')
        self.count[method]+=1
        self.pending=(method,self.count[method])
        self.write(dict(kind='BEGIN',method=method,ordinal=self.count[method],phase=phase,inputs=inputs))
    def end(self,result):
        method,ordinal=self.pending
        self.write(dict(kind='END',method=method,ordinal=ordinal,result=result));self.pending=None
    def abort(self,exc):
        self.write(dict(kind='ERROR',pending=self.pending,error_type=type(exc).__name__,message=str(exc)))
        self.file.flush();os.fsync(self.file.fileno())
    def close(self):self.file.flush();os.fsync(self.file.fileno());self.file.close()

def trace(ledger,method,*args,**kwargs):
    try:
        answer=getattr(kerr,method)(*args,**kwargs)
        ledger.end(answer)
        tup=np.asarray(answer.get('tuple',[]))
        if answer.get('status')!='EMITTING' or tup.shape!=(4,) or not np.isfinite(tup).all():
            raise RuntimeError('non-emitting, missing or nonfinite physical tuple')
        if not (6.<=tup[0]<=13.) or tup[2]<=0 or tup[3]<=0 or answer['meta']['jac']<=0:
            raise RuntimeError('ray outside registered annulus/time/redshift/area domain')
        return answer
    except Exception as exc:
        ledger.abort(exc);raise

def difference(a,b):
    d=np.abs(np.asarray(a)-np.asarray(b));d[1]=abs((a[1]-b[1]+np.pi)%(2*np.pi)-np.pi)
    return d

def response(group,fn):
    tup=group['tuple'];weights=group['weights']*tup[:,3]**3;pix=group['pixels']
    return np.concatenate([np.bincount(pix,weights*fn(tup[:,0],tup[:,1],to-tup[:,2]+100.),minlength=64) for to in OBS])

def operator(group):
    tup=group['tuple']; n=len(tup);kernel=group['weights']*tup[:,3]**3
    space=(radial(tup[:,0])[:,:,None]*angular(tup[:,1])[:,None,:]).reshape(n,35)
    blocks=[]
    # Group ordering is pixel-major; each pixel has q^2 nodes.
    for to in OBS:
        bt=temporal(to-tup[:,2]+100.)
        basis=(space[:,:,None]*bt[:,None,:]).reshape(64,n//64,595)
        blocks.append(np.einsum('pq,pqk->pk',kernel.reshape(64,-1),basis,optimize=True))
    return np.vstack(blocks)

def support(groups):
    out=np.zeros((15,32,64))
    for order in (0,1):
        group=groups[12,order];tu=group['tuple']
        ir=np.clip(np.rint((tu[:,0]-6.)/(7./31.)).astype(int),0,31)
        ip=np.rint(((tu[:,1]+np.pi)%(2*np.pi))/(2*np.pi/64)).astype(int)%64
        pos=ir*64+ip;kw=group['weights']*tu[:,3]**6
        for to in OBS:
            tau=to-tu[:,2]+100.
            for k,f in enumerate(FRAMES):
                out[k]+=np.bincount(pos,kw*np.exp(-.5*((tau-f)/1.5)**2),minlength=2048).reshape(32,64)
    for k in range(15):
        out[k]=gaussian_filter(out[k],sigma=(2.,2.),mode=('nearest','wrap'),truncate=4.)
        if out[k].sum()<=0:raise RuntimeError('empty support frame')
        out[k]/=out[k].sum()
    full=np.broadcast_to((R*trap(R))[:,None],(32,64)).copy();full/=full.sum()
    return out,np.repeat(full[None,:,:],15,axis=0)

def discrepancy(a,b,std):
    # Observations are integrated raw pixel flux. Same q12 noise shape for both rules.
    return dict(relative=float(np.linalg.norm(a-b)/max(np.linalg.norm(b),1e-15)),whitened=float(np.linalg.norm((a-b)/std)))

def do_run():
    if not (ROOT/'provenance'/'EXECUTION_AUTHORIZATION.json').exists():raise RuntimeError('no registration receipt')
    freeze=json.loads((ROOT/'provenance'/'SOURCE_FREEZE.json').read_text())
    for name,expected in freeze['sha256'].items():
        if sha(ROOT/name)!=expected:raise RuntimeError('source/config hash mismatch: '+name)
    if list((ROOT/'results').iterdir()) or list((ROOT/'attempts').iterdir()):raise RuntimeError('refuse nonempty run')
    started=time.monotonic();ledger=Ledger(ROOT/'attempts');kerr.log_attempt=ledger.begin
    result={'experiment':'CACHE_REBUILD_001','status':'RUNNING','paper1_units':0,'original_R2_provenance_repaired':False}
    dump(ROOT/'results'/'ENVIRONMENT.json',dict(python=sys.version,numpy=np.__version__,scipy=scipy.__version__,platform=platform.platform(),blas_threads=1))
    try:
        # These points and seeds are fixed in the executable and registration before any calls.
        rng=np.random.default_rng(2026091201);vp=rng.uniform([.5,.3],[3.,.7],size=(32,2))
        checks=[]
        for order in (0,1):
            for i,(lam,z) in enumerate(vp):
                a=trace(ledger,'quad_transfer',float(lam),float(z),order=order,n=64,phase='independent_validation_q64')
                b=trace(ledger,'quad_transfer',float(lam),float(z),order=order,n=128,phase='independent_validation_q128')
                c=trace(ledger,'ode_transfer',float(lam),float(z),order=order,rtol=2e-11,atol=2e-12,phase='independent_validation_ode')
                d=difference(a['tuple'],c['tuple']);dr=difference(a['tuple'],b['tuple'])
                checks.append(dict(order=order,index=i,point=[lam,z],quad=a['tuple'],refined=b['tuple'],ode=c['tuple'],ode_error=d,refinement_error=dr,branches_match=a['leg']==b['leg']==c['leg'],passed=bool(np.all(d<=TOLS) and np.all(dr<=TOLS) and a['leg']==b['leg']==c['leg'])))
        dump(ROOT/'results'/'RAY_VALIDATION.json',checks)
        if not all(c['passed'] for c in checks):raise RuntimeError('independent ray-validation gate failed')
        print('Ray validation: 64/64 passed',flush=True)
        groups={}; saved={}
        for q in (8,12):
            pts,cw,pix=chart_rule(q)
            for order in (0,1):
                rows=[];weights=[];legs=[];metadata=[]
                for i,(lam,z) in enumerate(pts):
                    a=trace(ledger,'quad_transfer',float(lam),float(z),order=order,n=64,phase=f'cache_q{q}_order{order}')
                    rows.append(a['tuple']);weights.append(cw[i]*a['meta']['jac']);legs.append(a['leg'])
                    metadata.append([a['meta'][key] for key in ('alpha','beta','jac','rt','rc','eta')])
                g=dict(tuple=np.array(rows),weights=np.array(weights),pixels=pix,chart_points=pts,chart_weights=cw,leg=np.array(legs),metadata=np.array(metadata))
                groups[q,order]=g
                np.savez_compressed(ROOT/'results'/f'RAYS_q{q}_n{order}.npz',**g)
                for key,value in g.items():saved[f'{key}_q{q}_n{order}']=value
                print(f'Built q{q} order {order}: {len(rows)} rays',flush=True)
        area={n:np.bincount(groups[12,n]['pixels'],groups[12,n]['weights'],minlength=64) for n in (0,1)}
        base={(q,n):response(groups[q,n],lambda r,p,t:np.ones_like(r)) for q in (8,12) for n in (0,1)}
        sigma=float(np.sqrt(np.mean((base[12,0]/np.tile(np.sqrt(area[0]),13))**2))/300.)
        std={n:sigma*np.tile(np.sqrt(area[n]),13) for n in (0,1)}
        A={}
        for q in (8,12):
            for n in (0,1):
                A[q,n]=operator(groups[q,n]);saved[f'A_q{q}_n{n}']=A[q,n];saved[f'base_q{q}_n{n}']=base[q,n]
        H=gram();L=np.linalg.cholesky(H)
        saved.update(H=H,H_chol=L,radial_knots=RK,temporal_centers=TC,r_grid=R,phi_grid=PHI,t_gram_grid=T,movie_times=FRAMES,observer_times=OBS,sigma300=sigma,area_n0=area[0],area_n1=area[1])
        np.savez_compressed(ROOT/'results'/'REBUILT_PHYSICAL_AND_OPERATOR_ARRAYS.npz',**saved)
        W,FW=support(groups);np.savez_compressed(ROOT/'results'/'REBUILT_SUPPORT_WEIGHTS.npz',support=W,full_annulus=FW)
        dump(ROOT/'results'/'NOISE_CALIBRATION.json',dict(sigma300=sigma,sigma100=3*sigma,law='sigma_Omega * sqrt(q12 full pixel area); q12 direct constant-source whitened RMS is 300',source_time='tau=tobs-delay+100M'))
        print('Operators, source Gram, noise and support built',flush=True)
        # Fixed numerical fields only: no response-based source admission, no inverse fit.
        probes=fields.specifications(2026091202)
        dump(ROOT/'results'/'NUMERICAL_PROBE_SPECS.json',probes)
        clean=[];nulls=[]
        for probe in probes:
            fn=fields.make(probe); resps={(q,n):response(groups[q,n],fn) for q in (8,12) for n in (0,1)}
            for arm,ns in [('direct',(0,)),('order1',(1,)),('labelled',(0,1))]:
                d=discrepancy(np.concatenate([resps[8,n] for n in ns]),np.concatenate([resps[12,n] for n in ns]),np.concatenate([std[n] for n in ns]))
                clean.append(dict(id=probe['id'],arm=arm,**d,passed=d['relative']<=5e-4 and d['whitened']<=.1))
            if probe['kind']=='feature':
                nulls.append(dict(id=probe['id'],max_direct_q8=float(np.max(np.abs(resps[8,0]/std[0]))),max_direct_q12=float(np.max(np.abs(resps[12,0]/std[0])))))
        dump(ROOT/'results'/'ANALYTIC_Q8_Q12.json',clean);dump(ROOT/'results'/'DIRECT_NULL.json',nulls)
        # Complete raw unit-coefficient basis audit. Failures are not pruned or rescaled.
        basis=[]
        for arm,ns in [('direct',(0,)),('order1',(1,)),('labelled',(0,1))]:
            a=np.vstack([A[8,n] for n in ns]);b=np.vstack([A[12,n] for n in ns]);s=np.concatenate([std[n] for n in ns])
            dif=a-b;rel=np.linalg.norm(dif,axis=0)/np.maximum(np.linalg.norm(b,axis=0),1e-15);wh=np.linalg.norm(dif/s[:,None],axis=0)
            for col in range(595):basis.append(dict(arm=arm,column=col,relative=rel[col],whitened=wh[col],passed=bool(rel[col]<=5e-4 and wh[col]<=.1)))
        dump(ROOT/'results'/'BASIS_Q8_Q12.json',basis)
        # Independent operator contraction against per-ray basis contraction, no extra physical calls.
        cr=np.random.default_rng(2026091203).normal(size=595)*.02
        equiv=[]
        for q in (8,12):
            for n in (0,1):
                direct=response(groups[q,n],lambda r,p,t:evaluate(cr,r,p,t))
                equiv.append(float(np.max(np.abs(direct-A[q,n]@cr))))
        gram_error=float(np.linalg.norm(H-L@L.T)/np.linalg.norm(H))
        with np.load(ROOT/'results'/'REBUILT_PHYSICAL_AND_OPERATOR_ARRAYS.npz',allow_pickle=False) as readback:
            readback_ok=all(np.array_equal(readback[key],value) for key,value in saved.items())
        geometry_count_ok=ledger.count==collections.Counter(separated_quadrature=26752,compactified_ode=64)
        gates=dict(ray_validation=all(c['passed'] for c in checks),expected_physical_counts=geometry_count_ok,operator_contraction=max(equiv)<=1e-12,source_gram=gram_error<=1e-12,support_normalization=bool(np.max(np.abs(W.sum(axis=(1,2))-1))<=1e-12 and np.all(W>=0)),direct_null=all(max(x['max_direct_q8'],x['max_direct_q12'])<=1e-10 for x in nulls),analytic_q8_q12=all(x['passed'] for x in clean),basis_q8_q12=all(x['passed'] for x in basis),saved_array_readback=readback_ok)
        result.update(status='CACHE_REBUILD_001_PASS' if all(gates.values()) else 'CACHE_REBUILD_001_COMPLETE_NUMERICAL_GATE_FAIL',gates=gates,counts=dict(ledger.count),ray_validation_max=np.max([c['ode_error'] for c in checks],axis=0),ray_refinement_max=np.max([c['refinement_error'] for c in checks],axis=0),analytic_probe_count=len(probes),analytic_failures=sum(not c['passed'] for c in clean),basis_failures=sum(not c['passed'] for c in basis),analytic_max_relative=max(c['relative'] for c in clean),analytic_max_whitened=max(c['whitened'] for c in clean),basis_max_relative=max(c['relative'] for c in basis),basis_max_whitened=max(c['whitened'] for c in basis),operator_contraction_max=max(equiv),source_gram_error=gram_error,source_gram_condition=float(np.linalg.cond(H)),elapsed_seconds=time.monotonic()-started,peak_rss_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,scientific_movie_runs=0,posterior_runs=0,regularization_selection_performed=False,ledger_tail_sha256=ledger.tail)
        dump(ROOT/'results'/'COMPLETION.json',result)
        print(json.dumps(result,default=jsonable,indent=2),flush=True)
    except Exception as exc:
        result.update(status='CACHE_REBUILD_001_INCOMPLETE',exception=type(exc).__name__,message=str(exc),traceback=traceback.format_exc(),counts=dict(ledger.count),elapsed_seconds=time.monotonic()-started,ledger_tail_sha256=ledger.tail)
        dump(ROOT/'results'/'FAILURE.json',result)
        raise
    finally:ledger.close()

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--run',action='store_true');args=parser.parse_args()
    if not args.run:parser.error('Explicit --run required')
    resource.setrlimit(resource.RLIMIT_AS,(8*1024**3,8*1024**3))
    def stop_for_time(signum,frame):raise TimeoutError('registered 900-second wall limit')
    signal.signal(signal.SIGALRM,stop_for_time);signal.alarm(900)
    do_run()
