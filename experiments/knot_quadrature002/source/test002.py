"""Model-free preflight: no call to the Kerr solver or empirical source bank."""
import json
import numpy as np
import run002 as r

def run():
    checks=[]
    def chk(name,p):
        checks.append({'name':name,'passed':bool(p)})
        if not p:raise AssertionError(name)
    # Disable physical entry points even if a future edit accidentally calls one.
    def forbid(*a,**k):raise AssertionError('physical call in model-free test')
    r.k.quad_transfer=forbid;r.k.ode_transfer=forbid
    for q in (8,12):
        x,w=r.gauss(q,-.4,.7)
        chk(f'gauss_{q}_area',abs(w.sum()-1.1)<1e-14)
        chk(f'gauss_{q}_polynomial',abs(np.dot(w,x**6)-(.7**7-(-.4)**7)/7)<1e-14)
        ss=0
        for lo,hi in zip([-1,.3],[.3,1]):
            x,w=r.gauss(q,lo,hi);ss+=np.dot(w,np.abs(x-.3))
        chk(f'kink_split_integral_{q}',abs(ss-1.09)<1e-13)
    roots=r.line_roots(lambda x:x,[-.4,.2],-1,1)
    chk('linear_edge_roots',np.allclose(sorted(roots),[-.4,.2],atol=1e-12))
    roots=r.line_roots(lambda x:-x,[-.4,.2],-1,1)
    chk('decreasing_edge_roots',np.allclose(sorted(roots),[-.2,.4],atol=1e-12))
    roots=r.unique_breaks(r.line_roots(lambda x:(x-.02)**2,[.0025],-1,1),-1,1)
    chk('two_roots_near_extremum',np.allclose(roots,[-1,-.03,.07,1],atol=1e-11))
    chk('out_of_range_no_roots',len(r.line_roots(lambda x:x,[5.],-1,1))==0)
    chk('duplicate_boundary_merge',r.unique_breaks([0,0,1e-14,1,2],0,2)==[0.,1.,2.])
    # Variable node counts and independent direct summation against the operator.
    g={'tuple':np.array([[8.,.4,101.,1.],[9.,.2,102.,.9],[10.,-.3,124.,.8]]),
       'weights':np.array([.02,.03,.04]),'pixels':np.array([0,0,63])}
    c=np.random.default_rng(4401).normal(size=595)*.02
    direct=r.b.response(g,lambda rr,pp,tt:r.b.evaluate(c,rr,pp,tt))
    chk('variable_node_operator',np.max(abs(direct-r.operator(g)@c))<1e-14)
    aa={n:np.zeros((832,595)) for n in (0,1)}
    cc=r.basis_checks(aa,aa,{n:np.ones(832) for n in (0,1)})
    chk('zero_response_basis_gate',len(cc)==1785 and r.stats(cc)['failures']==0)
    bb={n:a.copy() for n,a in aa.items()};bb[1][0,0]=.2
    cc=r.basis_checks(aa,bb,{n:np.ones(832) for n in (0,1)})
    chk('whitened_failure_preserved',r.stats(cc)['whitened_failures']==2)
    chk('roundoff_unique_breaks',all(np.diff(r.unique_breaks([.5,.5+1e-14],0,1))>0))
    chk('thresholds_preserved',r.REL_TOL==5e-4 and r.WHITE_TOL==.1)
    chk('all_observer_time_knots',all(float(to+100-tc) in r.LEVELS for to in r.b.OBS for tc in r.b.TC))
    return {'scope':'Model-free tests only; no physical calls','count':len(checks),'passed':all(x['passed'] for x in checks),'checks':checks}
if __name__=='__main__':print(json.dumps(run(),indent=2))
