"""KNOT_QUADRATURE_002: frozen, coefficient-independent pixel integration.
No noisy data, inference, movie recovery, or tuning of scientific endpoints.
"""
from __future__ import annotations
import os
for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[key]='1'
import argparse,collections,gzip,hashlib,json,resource,signal,sys,time,traceback
from pathlib import Path
import numpy as np
import scipy
from scipy.optimize import brentq,minimize_scalar
from scipy.linalg import solve_triangular
import basis001 as b
import kerr_chart003_original as k
import numerical_fields as fields
ROOT=Path(__file__).resolve().parents[1]
LEVELS=np.unique((b.OBS[:,None]+100-b.TC[None,:]).ravel())
LAMBDA_EDGES=np.linspace(.5,3.,9)
Z_EDGES=np.linspace(.3,.7,9)
REL_TOL=5e-4
WHITE_TOL=.1
RAY_CAP=600000
WALL=1200

def convert(x):
    if isinstance(x,np.ndarray):return x.tolist()
    if isinstance(x,np.generic):return x.item()
    raise TypeError(type(x).__name__)

def save(path,value):
    with Path(path).open('x') as f:json.dump(value,f,indent=2,sort_keys=True,default=convert,allow_nan=False);f.write('\n')

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def gauss(q,lo,hi):
    x,w=k.rule(q)
    return (lo+hi)/2+(hi-lo)/2*x,(hi-lo)/2*w

def unique_breaks(values,lo,hi):
    """Merge only coordinate-roundoff duplicate interior roots; retain bounds."""
    vals=sorted(v for v in values if lo+2e-12<v<hi-2e-12)
    out=[float(lo)]
    for v in vals:
        if v-out[-1]>2e-12:out.append(float(v))
    out.append(float(hi))
    return out

def line_roots(fn,levels,lo,hi):
    """Deterministic sampled isolation plus bounded extrema; no global certificate."""
    xx=list(np.linspace(lo,hi,17));yy=[float(fn(x)) for x in xx]
    extras=[]
    for i in range(1,16):
        dl=yy[i]-yy[i-1];dr=yy[i+1]-yy[i]
        if dl*dr<0:
            sign=1 if dl<0 else -1
            opt=minimize_scalar(lambda x:sign*fn(x),bounds=(xx[i-1],xx[i+1]),method='bounded',options={'xatol':1e-13,'maxiter':100})
            if not opt.success:raise RuntimeError('edge extremum solver failed')
            extras.append(float(opt.x))
    grid=sorted(set(xx+extras));vv=[float(fn(x)) for x in grid];roots=[]
    for target in levels:
        if target<min(vv) or target>max(vv):continue
        for i in range(len(grid)-1):
            fa=vv[i]-target;fb=vv[i+1]-target
            if abs(fa)<=1e-12:roots.append(grid[i])
            if fa*fb<0:
                rt=brentq(lambda x:fn(x)-target,grid[i],grid[i+1],xtol=2e-13,rtol=1e-14,maxiter=100)
                if abs(fn(rt)-target)>2e-9:raise RuntimeError('edge root residual')
                roots.append(rt)
        if abs(vv[-1]-target)<=1e-12:roots.append(grid[-1])
    return roots

class Rays:
    def __init__(self):
        self.cache={};self.calls=0;self.hits=0;self.seq=0;self.tail='0'*64;self.start=time.monotonic()
        self.phase='initial';self.phase_counts=collections.Counter()
        self.raw=(ROOT/'attempts/physical_calls.jsonl.gz').open('xb')
        self.f=gzip.GzipFile(fileobj=self.raw,mode='wb',mtime=0)
    def event(self,d):
        d.update(sequence=self.seq,previous_sha256=self.tail)
        text=json.dumps(d,sort_keys=True,separators=(',',':'),allow_nan=False,default=convert)
        self.tail=hashlib.sha256(text.encode()).hexdigest();self.seq+=1
        self.f.write((json.dumps({'event':d,'sha256':self.tail},separators=(',',':'),default=convert)+'\n').encode())
        if self.seq%512==0:self.f.flush();self.raw.flush()
    def get(self,n,l,z):
        key=(int(n),float(l),float(z))
        if key in self.cache:self.hits+=1;return self.cache[key]
        if self.calls>=RAY_CAP or time.monotonic()-self.start>WALL:raise RuntimeError('registered physical/time cap')
        self.calls+=1;self.phase_counts[self.phase]+=1
        self.event(dict(kind='BEGIN',ordinal=self.calls,order=n,lam=l,z=z,phase=self.phase))
        try:
            r=k.quad_transfer(float(l),float(z),order=n,n=64,record=False)
            t=np.asarray(r.get('tuple',[]),float);jac=r['meta']['jac']
            if r['status']!='EMITTING' or t.shape!=(4,) or not np.isfinite(t).all() or not 6<=t[0]<=13 or min(t[2],t[3],jac)<=0:raise RuntimeError('invalid ray')
            self.event(dict(kind='END',ordinal=self.calls,tuple=t,jac=jac,leg=r['leg'],status=r['status']))
            ans=(t,float(jac));self.cache[key]=ans;return ans
        except Exception as exc:
            self.event(dict(kind='ERROR',ordinal=self.calls,type=type(exc).__name__,message=str(exc)));raise
    def close(self):self.f.close();self.raw.close()

def outer_breaks(ray,n,lo,hi,zlo,zhi):
    vals=[]
    for zz in (zlo,zhi):
        vals+=line_roots(lambda ll:ray.get(n,ll,zz)[0][2],LEVELS,lo,hi)
        vals+=line_roots(lambda ll:ray.get(n,ll,zz)[0][0],[9.5],lo,hi)
    return unique_breaks(vals,lo,hi)

def inner_breaks(ray,n,ll,lo,hi):
    zz=np.linspace(lo,hi,5);tt=np.array([ray.get(n,ll,z)[0] for z in zz]);vals=[]
    for col,levels,sign in [(2,LEVELS,-1 if n==0 else 1),(0,[9.5],1)]:
        v=tt[:,col]
        if np.any(sign*np.diff(v)<=0):raise RuntimeError('sampled inner monotonicity failed')
        for level in levels:
            if min(v[0],v[-1])<level<max(v[0],v[-1]):
                fn=lambda z:ray.get(n,ll,z)[0][col]-level
                rt=brentq(fn,lo,hi,xtol=2e-13,rtol=1e-14,maxiter=100)
                if abs(fn(rt))>2e-9:raise RuntimeError('inner root residual')
                vals.append(rt)
    return unique_breaks(vals,lo,hi)

def generate(ray,n,q,method,partitions):
    tuples=[];weights=[];pixels=[];nodes=[];panelcount=0;maxpanels=0
    ray.phase=f'{method}_q{q}_n{n}'
    for i in range(8):
        for j in range(8):
            pix=i*8+j;lo,hi=LAMBDA_EDGES[i:i+2];zlo,zhi=Z_EDGES[j:j+2]
            outer=partitions[n,pix] if method=='KNOT' else np.linspace(lo,hi,3)
            start=len(tuples)
            for al,ah in zip(outer[:-1],outer[1:]):
                ls,lw=gauss(q,al,ah)
                for ll,wl in zip(ls,lw):
                    inner=inner_breaks(ray,n,float(ll),zlo,zhi) if method=='KNOT' else np.linspace(zlo,zhi,3)
                    maxpanels=max(maxpanels,len(inner)-1)
                    for zl,zh in zip(inner[:-1],inner[1:]):
                        zs,zw=gauss(q,zl,zh);panelcount+=1
                        for zz,wz in zip(zs,zw):
                            t,jac=ray.get(n,float(ll),float(zz));tuples.append(t);weights.append(wl*wz*jac);pixels.append(pix);nodes.append((ll,zz))
            if pix%16==15:print(method,q,n,'pixel',pix,'nodes',len(tuples),'new physical',ray.calls,flush=True)
    g={'tuple':np.array(tuples),'weights':np.array(weights),'pixels':np.array(pixels,dtype=np.int64),'chart_points':np.array(nodes)}
    np.savez_compressed(ROOT/f'results/{method}_q{q}_n{n}_RAYS.npz',**g)
    return g,dict(quadrature_nodes=len(tuples),inner_panels=panelcount,max_inner_panels=maxpanels)

def operator(g):
    ans=np.zeros((13,64,595))
    pix=g['pixels'];starts=np.searchsorted(pix,np.arange(65))
    for p in range(64):
        sl=slice(starts[p],starts[p+1]);t=g['tuple'][sl];ww=g['weights'][sl]*t[:,3]**3
        space=(b.radial(t[:,0])[:,:,None]*b.angular(t[:,1])[:,None,:]).reshape(-1,35)
        for it,to in enumerate(b.OBS):ans[it,p]=(space.T@(ww[:,None]*b.temporal(to-t[:,2]+100))).ravel()
    return ans.reshape(832,595)

def stats(rows):
    return dict(checks=len(rows),failures=sum(not r['passed'] for r in rows),relative_failures=sum(r['relative']>REL_TOL for r in rows),whitened_failures=sum(r['whitened']>WHITE_TOL for r in rows),max_relative=max(r['relative'] for r in rows),max_whitened=max(r['whitened'] for r in rows))

def basis_checks(a8,a12,std):
    rows=[]
    for arm,ns in [('direct',(0,)),('order1',(1,)),('labelled',(0,1))]:
        aa=np.vstack([a8[n] for n in ns]);bb=np.vstack([a12[n] for n in ns]);ss=np.concatenate([std[n] for n in ns])
        rel=np.linalg.norm(aa-bb,axis=0)/np.maximum(np.linalg.norm(bb,axis=0),1e-15);wh=np.linalg.norm((aa-bb)/ss[:,None],axis=0)
        rows += [dict(arm=arm,column=c,relative=rel[c],whitened=wh[c],passed=bool(rel[c]<=REL_TOL and wh[c]<=WHITE_TOL)) for c in range(595)]
    return rows

def run():
    freeze=json.loads((ROOT/'provenance/SOURCE_FREEZE.json').read_text())
    for p,h in freeze['sha256'].items():
        if sha(ROOT/p)!=h:raise RuntimeError('hash mismatch '+p)
    receipt=json.loads((ROOT/'provenance/REGISTRATION_RECEIPT.json').read_text())
    if not receipt.get('commit'):raise RuntimeError('registration receipt missing')
    if list((ROOT/'results').iterdir()) or list((ROOT/'attempts').iterdir()):raise RuntimeError('refuse nonempty experiment')
    # Prevent any call into the ancestor's filesystem accounting.
    def forbidden(*a,**kw):raise RuntimeError('old physical logger forbidden')
    k.log_attempt=forbidden
    started=time.monotonic();ray=Rays();out={'experiment':'KNOT_QUADRATURE_002','registration':receipt['commit'],'paper1_units':0,'movie_fits':0,'posterior_fits':0}
    save(ROOT/'results/ENVIRONMENT.json',dict(python=sys.version,numpy=np.__version__,scipy=scipy.__version__,blas_threads=1))
    try:
        with np.load(ROOT/'inputs/REBUILT_PHYSICAL_AND_OPERATOR_ARRAYS.npz',allow_pickle=False) as fp:old={kk:fp[kk] for kk in fp.files}
        std={n:float(old['sigma300'])*np.tile(np.sqrt(old[f'area_n{n}']),13) for n in (0,1)}
        baseline=basis_checks({n:old[f'A_q8_n{n}'] for n in (0,1)},{n:old[f'A_q12_n{n}'] for n in (0,1)},std)
        target=json.loads((ROOT/'inputs/BASIS_Q8_Q12.json').read_text())
        if any(x['passed']!=y['passed'] or max(abs(x['relative']-y['relative']),abs(x['whitened']-y['whitened']))>1e-12 for x,y in zip(baseline,target)):raise RuntimeError('baseline replay')
        if len(target)!=1785 or stats(baseline)['failures']!=142:raise RuntimeError('baseline counts')
        partitions={};ray.phase='edge_partitions'
        for n in (0,1):
            for i in range(8):
                for j in range(8):partitions[n,i*8+j]=outer_breaks(ray,n,*LAMBDA_EDGES[i:i+2],*Z_EDGES[j:j+2])
        save(ROOT/'results/OUTER_PARTITIONS.json',{f'{n}_{p}':v for (n,p),v in partitions.items()})
        method_results={};alloperators={};area_checks=[]
        specs=json.loads((ROOT/'inputs/NUMERICAL_PROBE_SPECS.json').read_text())
        fresh=fields.specifications(2026091204)
        for s in fresh:s['id']='fresh_'+s['id']
        specs+=fresh;save(ROOT/'results/NUMERICAL_PROBE_SPECS.json',specs)
        for method in ('UNIFORM2','KNOT'):
            groups={};ops={};node_stats={}
            for q in (8,12):
                for n in (0,1):
                    groups[q,n],node_stats[f'q{q}_n{n}']=generate(ray,n,q,method,partitions)
                    ops[q,n]=operator(groups[q,n]);alloperators[f'{method}_q{q}_n{n}']=ops[q,n]
                    area=np.bincount(groups[q,n]['pixels'],groups[q,n]['weights'],minlength=64)
                    ar=float(np.max(np.abs(area/old[f'area_n{n}']-1)))
                    area_checks.append(dict(method=method,q=q,order=n,maximum_relative=ar,passed=ar<=1e-8))
            checks=basis_checks({n:ops[8,n] for n in (0,1)},{n:ops[12,n] for n in (0,1)},std)
            save(ROOT/f'results/{method}_BASIS.json',checks)
            analytic=[];nullmax=0
            for spec in specs:
                fn=fields.make(spec);rr={(q,n):b.response(groups[q,n],fn) for q in (8,12) for n in (0,1)}
                for arm,ns in [('direct',(0,)),('order1',(1,)),('labelled',(0,1))]:
                    d=b.discrepancy(np.concatenate([rr[8,n] for n in ns]),np.concatenate([rr[12,n] for n in ns]),np.concatenate([std[n] for n in ns]))
                    analytic.append(dict(id=spec['id'],arm=arm,**d,passed=d['relative']<=REL_TOL and d['whitened']<=WHITE_TOL))
                if spec['kind']=='feature':nullmax=max(nullmax,*[float(np.max(np.abs(rr[q,0]/std[0]))) for q in (8,12)])
            save(ROOT/f'results/{method}_ANALYTIC.json',analytic)
            # Difference bound over source-norm unit ball. Not a continuum certificate.
            ds=np.vstack([(ops[8,n]-ops[12,n])/std[n][:,None] for n in (0,1)])
            normalized=solve_triangular(old['H_chol'],ds.T,lower=True).T
            spectral=float(np.linalg.svd(normalized,compute_uv=False)[0])
            method_results[method]=dict(basis=stats(checks),basis_by_arm={a:stats([r for r in checks if r['arm']==a]) for a in ('direct','order1','labelled')},analytic=stats(analytic),direct_null_max=nullmax,nodes=node_stats,source_norm_q8_q12_spectral=spectral)
            print(method,json.dumps(method_results[method],default=convert),flush=True)
        np.savez_compressed(ROOT/'results/OPERATORS.npz',**alloperators)
        save(ROOT/'results/AREA_CHECKS.json',area_checks)
        exact=True
        with np.load(ROOT/'results/OPERATORS.npz') as fp:
            exact=all(np.array_equal(fp[kk],vv) for kk,vv in alloperators.items())
        good=all(r['passed'] for r in area_checks) and exact and method_results['KNOT']['basis']['failures']==0 and method_results['KNOT']['analytic']['failures']==0 and method_results['KNOT']['direct_null_max']<=1e-10
        out.update(status='KNOT_QUADRATURE_002_PASS' if good else 'KNOT_QUADRATURE_002_COMPLETE_GATE_FAIL',methods=method_results,baseline=stats(baseline),area_checks_pass=all(r['passed'] for r in area_checks),saved_arrays_exact=exact,physical_calls=ray.calls,physical_phase_counts=dict(ray.phase_counts),memoized_hits=ray.hits,ledger_tail=ray.tail,ledger_events=ray.seq,seconds=time.monotonic()-started,peak_rss_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        save(ROOT/'results/COMPLETION.json',out)
        print(json.dumps(out,indent=2,default=convert),flush=True)
    except Exception as exc:
        out.update(status='KNOT_QUADRATURE_002_INCOMPLETE',exception=type(exc).__name__,message=str(exc),traceback=traceback.format_exc(),physical_calls=ray.calls,physical_phase_counts=dict(ray.phase_counts),ledger_tail=ray.tail,ledger_events=ray.seq,seconds=time.monotonic()-started)
        save(ROOT/'results/FAILURE.json',out);raise
    finally:ray.close()

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--run',action='store_true');a=ap.parse_args()
    if not a.run:ap.error('--run required')
    resource.setrlimit(resource.RLIMIT_AS,(8*1024**3,8*1024**3))
    def timeout(*args):raise TimeoutError('1200 second limit')
    signal.signal(signal.SIGALRM,timeout);signal.alarm(WALL)
    run()
