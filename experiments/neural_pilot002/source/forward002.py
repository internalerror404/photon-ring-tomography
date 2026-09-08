"""Independently calibrated Schwarzschild delay surrogate. No source inference.
The differential-equation solution supplies an independent reference, not a
physics residual used to tune against the heldout observations.
"""
from support import *
from physical_kernel import *
from scipy.interpolate import CubicSpline
import hashlib
LO=-5.;HI=np.log(2.);CAP=2500
COUNTS={'radial_quad':0,'orbit_ode':0,'preflight':10}
EVENTS=OUT/'physical_attempts.jsonl'
def call(method,rt,**kw):
    if sum(COUNTS.values())>=CAP:raise RuntimeError('Physical pilot allocation exhausted')
    COUNTS[method]+=1
    with EVENTS.open('a') as f:f.write(json.dumps(dict(method=method,rt=float(rt),options=kw,phase='reserved',count=sum(COUNTS.values())))+'\n')
    val=radial_quad(rt,**kw) if method=='radial_quad' else orbit_ode(rt,**kw)
    return val

def detector_grid(q):
    from numpy.polynomial.legendre import leggauss
    u,w=leggauss(q);e=np.linspace(LO,HI,13);h=(e[1:]-e[:-1])/2
    z=(e[1:]+e[:-1])[:,None]/2+h[:,None]*u
    d=np.exp(z);rt=3+d;b=impact(rt)
    jac=d*(1-3/rt)/(1-2/rt)**1.5
    ww=h[:,None]*w*jac;areas=np.diff(impact(3+np.exp(e)))
    return d,ww,areas

def fields(delay):
    return np.stack([np.ones_like(delay),np.cos(2*np.pi*delay/20),np.sin(2*np.pi*delay/20),np.cos(2*np.pi*delay/40),np.sin(2*np.pi*delay/40)],-1)
def detector(delay,w,areas):return np.sum(w[...,None]*fields(delay),axis=1)/np.sqrt(areas[:,None])

class Surrogate(nn.Module):
    def __init__(self,kind):super().__init__();self.kind=kind;self.net=mlp(1)
    def forward(self,d):
        if self.kind=='raw':
            r=3+d;b=r/torch.sqrt(1-2/r);v=(b-impact(3+np.exp(LO)))/(impact(5.)-impact(3+np.exp(LO)))
        else:v=(torch.log(d)-LO)/(HI-LO)
        out=(1-v)*self.net((2*v-1)[:,None]).squeeze(-1)
        return -6*np.sqrt(3)*torch.log(d/2)+10*out if self.kind=='structured' else 60*out

def run():
    if (OUT/'forward_results.json').exists():raise RuntimeError('Refuse overwrite results')
    ds=np.exp(np.linspace(LO,HI,24));train=[]
    for d in ds:train.append(call('radial_quad',3+d)[0])
    train=np.array(train);Tref=train[-1,1];dy=train[:,1]-Tref
    dh=np.exp(np.random.default_rng(802001).uniform(LO,HI,96));reference=[];primary=[];conservation=[]
    for d in dh:
        q,_=call('radial_quad',3+d);o,c,n=call('orbit_ode',3+d);primary.append(q);reference.append(o);conservation.append(c)
    reference=np.array(reference);primary=np.array(primary)
    diff=np.abs(reference-primary)
    save('physical_reference_check.json',dict(max_angle_discrepancy=float(diff[:,0].max()),max_time_discrepancy_M=float(diff[:,1].max()),max_orbit_first_integral_residual=float(max(conservation)),time_gate_M=2e-6,gate_pass=bool(diff[:,1].max()<2e-6),counts=COUNTS))
    if diff[:,1].max()>=2e-6:raise RuntimeError('Independent geodesic reference gate failed')
    D,W,A=detector_grid(48);rtvals=[]
    for d in D.ravel():rtvals.append(call('orbit_ode',3+d)[0][1])
    dtref=np.array(rtvals).reshape(D.shape)-Tref;yref=detector(dtref,W,A)
    D2,W2,A2=detector_grid(24);rtvals2=[]
    for d in D2.ravel():rtvals2.append(call('radial_quad',3+d)[0][1])
    y24=detector(np.array(rtvals2).reshape(D2.shape)-Tref,W2,A2)
    qrel=np.linalg.norm(yref-y24,axis=0)/np.linalg.norm(yref,axis=0)
    arrays=dict(train_d=ds,train_delay=dy,holdout_d=dh,holdout_primary=primary,holdout_reference=reference,detector_d=D,weights=W,areas=A,reference_delay=dtref,reference_vectors=yref)
    rows=[];spline=CubicSpline(np.log(ds),dy);residual=CubicSpline(np.log(ds),dy+6*np.sqrt(3)*np.log(ds/2))
    cases={'cubic_log':lambda x:spline(np.log(x)),'residual_cubic':lambda x:-6*np.sqrt(3)*np.log(x/2)+residual(np.log(x))}
    def assess(name,fn,ss=None,info={}):
        predpoint=fn(dh);predD=fn(D.ravel()).reshape(D.shape);yhat=detector(predD,W,A)
        rel=np.linalg.norm(yhat-yref,axis=0)/np.linalg.norm(yref,axis=0)
        rows.append(dict(model=name,seed=ss,max_channel_detector_relative_error=float(max(rel)),per_channel_relative_error=rel.tolist(),max_point_delay_error_M=float(np.max(abs(predpoint-(reference[:,1]-Tref)))),relative_delay_error=relative(predpoint,reference[:,1]-Tref),**info))
        arrays[f'holdout_{name}_{ss}']=predpoint;arrays[f'vectors_{name}_{ss}']=yhat
        save('forward_results.json',dict(rows=rows,quadrature_24_vs48_perchannel=qrel.tolist(),counts=COUNTS,scope='actual Schwarzschild round-trip primitive; no disk image-order forward operator',reference_clock_Tref=float(Tref)))
        print('FORWARD',name,ss,rows[-1]['max_channel_detector_relative_error'],rows[-1]['max_point_delay_error_M'],flush=True)
    for k,fn in cases.items():assess(k,fn)
    for ss in [101,202,303]:
      for kind in ['raw','log','structured']:
        seed(ss);m=Surrogate(kind);x=tensor(ds);y=tensor(dy)
        def loss():return ((m(x)-y)/60).square().mean()
        inf=fit(m,loss,1600,100);torch.save(m.state_dict(),OUT/f'forward_{kind}_{ss}.pt')
        def fn(d):
            with torch.no_grad():return m(tensor(np.asarray(d).ravel())).numpy().reshape(np.shape(d))
        assess(kind,fn,ss,{k:v for k,v in inf.items() if k!='trace'})
    np.savez_compressed(OUT/'forward_arrays.npz',**arrays)
    save('physical_final_ledger.json',dict(counts=COUNTS,total=sum(COUNTS.values()),cap=CAP,Paper_I_charged=0,partial_evaluations_are_not_full_raymap=True))
    print('FORWARD COMPLETE',COUNTS,flush=True)
if __name__=='__main__':run()
