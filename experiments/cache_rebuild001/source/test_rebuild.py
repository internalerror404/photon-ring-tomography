"""Data-independent pre-execution tests. No Kerr calls or scientific probes."""
import hashlib,json,sys,tempfile
from pathlib import Path
import numpy as np
import rebuild as r

def run():
    out=[]
    def check(name,predicate):
        passed=bool(predicate)
        out.append(dict(name=name,passed=passed))
        if not passed:raise AssertionError(name)
    x=np.linspace(6.,13.,101)
    check('radial_partition',np.max(np.abs(r.radial(x).sum(axis=-1)-1))<1e-14)
    check('radial_support',np.all(r.radial(np.array([5.,14.]))==0))
    t=np.linspace(-32.,28.,151)
    check('temporal_partition',np.max(np.abs(r.temporal(t).sum(axis=-1)-1))<2e-15)
    check('temporal_cardinality',np.max(np.abs(r.temporal(r.TC)-np.eye(17)))<1e-14)
    check('temporal_compact_support',np.all(r.temporal(np.array([-33.,29.]))==0))
    check('angular_periodicity',np.max(np.abs(r.angular(x)-r.angular(x+2*np.pi)))<1e-14)
    h=r.gram();ll=np.linalg.cholesky(h)
    check('gram_spd_and_cholesky',np.max(np.abs(h-ll@ll.T))<1e-12)
    # The reconstructed constant source has only m=0 coefficients equal to one.
    c=np.zeros((5,7,17));c[:,0,:]=1
    check('constant_source_partition',np.max(np.abs(r.evaluate(c,x,np.zeros_like(x),np.zeros_like(x))-1))<1e-14)
    for q in (8,12):
        pts,w,p=r.chart_rule(q)
        check(f'q{q}_count_area_pixel_assignment',len(pts)==64*q*q and abs(w.sum()-1.)<1e-14 and np.all(np.bincount(p)==q*q))
    # Artificial tuples; not a physical transfer calculation.
    q=2;pts,w,pix=r.chart_rule(q);n=len(pts)
    g=dict(tuple=np.c_[np.full(n,8.),np.linspace(-1.,1.,n),np.full(n,100.),np.ones(n)],weights=w,pixels=pix)
    cc=np.random.default_rng(123).normal(size=595)*.01
    direct=r.response(g,lambda a,b,c:r.evaluate(cc,a,b,c))
    check('toy_operator_linear_contraction',np.max(np.abs(direct-r.operator(g)@cc))<1e-14)
    win=r.fields.old_window(np.array([-32.,-31.,-29.,-10.,-6.,0.]))
    check('historical_support_window',np.array_equal(win,[0,0,1,1,0,0]))
    a=np.array([2.,np.pi-.01,3.,1.]);b=np.array([2.,-np.pi+.01,3.,1.])
    check('phase_wrapped_difference',abs(r.difference(a,b)[1]-.02)<1e-14)
    d=r.discrepancy(np.array([1.,3.]),np.array([1.,2.]),np.array([1.,2.]))
    check('whitened_norm_not_RMS',abs(d['whitened']-.5)<1e-15)
    with tempfile.TemporaryDirectory() as td:
        led=r.Ledger(Path(td));led.begin('toy','separated_quadrature',[0]);led.end({'status':'toy'});tail=led.tail;led.close()
        lines=Path(td,'physical_calls.jsonl').read_text().splitlines();prev='0'*64
        for seq,line in enumerate(lines):
            obj=json.loads(line);e=obj['event'];raw=json.dumps(e,sort_keys=True,separators=(',',':'),allow_nan=False)
            check(f'ledger_toy_event_{seq}',e['sequence']==seq and e['previous_sha256']==prev and hashlib.sha256(raw.encode()).hexdigest()==obj['sha256'])
            prev=obj['sha256']
        check('ledger_toy_final_tail',prev==tail and led.count['separated_quadrature']==1)
    return {'scope':'model-free software tests only; zero physical integrations', 'tests':out,'passed':all(x['passed'] for x in out),'count':len(out)}
if __name__=='__main__':
    result=run(); print(json.dumps(result,indent=2))
