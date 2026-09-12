"""Postplanned readback only. Does not call any ray or optimizer.
Audits source freeze, complete ledger, every deposited quadrature node,
all basis metrics, all analytic metrics and extra random matrix contractions.
"""
import os
os.environ['OPENBLAS_NUM_THREADS']='1'
import collections,gzip,hashlib,json,sys
from pathlib import Path
import numpy as np
import basis001 as b
import numerical_fields as fields
ROOT=Path(__file__).resolve().parents[1];RES=ROOT/'results'

def conv(x):
    if isinstance(x,np.generic):return x.item()
    if isinstance(x,np.ndarray):return x.tolist()
    raise TypeError(type(x).__name__)

def run():
    done=json.loads((RES/'COMPLETION.json').read_text())
    assert done['status'] in ('KNOT_QUADRATURE_002_PASS','KNOT_QUADRATURE_002_COMPLETE_GATE_FAIL')
    for p,h in json.loads((ROOT/'provenance/SOURCE_FREEZE.json').read_text())['sha256'].items():assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h
    tail='0'*64;pending=None;count=0;lookup={};phases=collections.Counter()
    with gzip.open(ROOT/'attempts/physical_calls.jsonl.gz','rt') as f:
        for i,line in enumerate(f):
            o=json.loads(line);ev=o['event'];assert ev['sequence']==i and ev['previous_sha256']==tail
            raw=json.dumps(ev,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
            assert hashlib.sha256(raw).hexdigest()==o['sha256'];tail=o['sha256']
            if ev['kind']=='BEGIN':
                assert pending is None;count+=1;assert ev['ordinal']==count;pending=ev;phases[ev['phase']]+=1
            else:
                assert ev['kind']=='END' and pending and pending['ordinal']==ev['ordinal']
                key=(pending['order'],pending['lam'],pending['z']);assert key not in lookup
                lookup[key]=(ev['tuple'],ev['jac']);pending=None
    assert pending is None and count==done['physical_calls'] and tail==done['ledger_tail'] and i+1==done['ledger_events']
    assert dict(phases)==done['physical_phase_counts']
    with np.load(ROOT/'inputs/REBUILT_PHYSICAL_AND_OPERATOR_ARRAYS.npz') as z:old={key:z[key] for key in z.files}
    ss={n:float(old['sigma300'])*np.tile(np.sqrt(old[f'area_n{n}']),13) for n in (0,1)}
    new=np.load(RES/'OPERATORS.npz');groups={};node_checks=0;max_chart_area_error=0
    for method in ('UNIFORM2','KNOT'):
        for q in (8,12):
            for n in (0,1):
                with np.load(RES/f'{method}_q{q}_n{n}_RAYS.npz') as z:g={key:z[key] for key in z.files}
                groups[method,q,n]=g
                assert len(g['tuple'])==done['methods'][method]['nodes'][f'q{q}_n{n}']['quadrature_nodes']
                jac=[]
                for row,(ll,zz),pix in zip(g['tuple'],g['chart_points'],g['pixels']):
                    val,j=lookup[n,float(ll),float(zz)];assert np.array_equal(row,val);jac.append(j)
                    ip,jp=divmod(int(pix),8)
                    assert .5+ip*2.5/8-1e-12<=ll<=.5+(ip+1)*2.5/8+1e-12
                    assert .3+jp*.4/8-1e-12<=zz<=.3+(jp+1)*.4/8+1e-12
                    node_checks+=1
                assert np.all(g['weights']>0)
                chart_area=np.bincount(g['pixels'],weights=g['weights']/np.array(jac),minlength=64)
                max_chart_area_error=max(max_chart_area_error,float(np.max(np.abs(chart_area-1/64))))
    assert max_chart_area_error<1e-12
    del lookup
    basis_count=0;basis_diff=0;decision_errors=0
    for method in ('UNIFORM2','KNOT'):
        rows=json.loads((RES/f'{method}_BASIS.json').read_text());assert len(rows)==1785
        for arm,ns in [('direct',(0,)),('order1',(1,)),('labelled',(0,1))]:
            a=np.vstack([new[f'{method}_q8_n{n}'] for n in ns]);c=np.vstack([new[f'{method}_q12_n{n}'] for n in ns]);st=np.concatenate([ss[n] for n in ns])
            d=a-c;rel=np.sqrt((d*d).sum(axis=0))/np.maximum(np.sqrt((c*c).sum(axis=0)),1e-15);wh=np.sqrt(((d/st[:,None])**2).sum(axis=0))
            reported=[x for x in rows if x['arm']==arm];assert len(reported)==595
            for j,row in enumerate(reported):
                assert row['column']==j
                basis_diff=max(basis_diff,abs(row['relative']-rel[j]),abs(row['whitened']-wh[j]))
                decision_errors+=row['passed']!=bool(rel[j]<=5e-4 and wh[j]<=.1);basis_count+=1
    assert basis_diff<=1e-12 and decision_errors==0
    # Independent analytic accumulation: per-pixel segmented sum, not producer bincount.
    specs=json.loads((RES/'NUMERICAL_PROBE_SPECS.json').read_text());assert len(specs)==178 and len({s['id'] for s in specs})==178
    analytic_count=0;analytic_diff=0;direct_null=0
    for method in ('UNIFORM2','KNOT'):
        rr=json.loads((RES/f'{method}_ANALYTIC.json').read_text());assert len(rr)==534
        reference={(x['id'],x['arm']):x for x in rr}
        for spec in specs:
            fun=fields.make(spec);resp={}
            for q in (8,12):
                for n in (0,1):
                    g=groups[method,q,n];t=g['tuple'];w=g['weights']*t[:,3]**3
                    starts=np.searchsorted(g['pixels'],np.arange(64));assert len(np.unique(g['pixels']))==64
                    resp[q,n]=np.concatenate([np.add.reduceat(w*fun(t[:,0],t[:,1],to-t[:,2]+100),starts) for to in b.OBS])
                    if spec['kind']=='feature' and n==0:direct_null=max(direct_null,float(np.max(np.abs(resp[q,n]/ss[n]))))
            for arm,ns in [('direct',(0,)),('order1',(1,)),('labelled',(0,1))]:
                a=np.concatenate([resp[8,n] for n in ns]);c=np.concatenate([resp[12,n] for n in ns]);st=np.concatenate([ss[n] for n in ns]);d=a-c
                rel=np.sqrt(d@d)/max(np.sqrt(c@c),1e-15);wh=np.sqrt(np.sum((d/st)**2));row=reference[spec['id'],arm]
                analytic_diff=max(analytic_diff,abs(rel-row['relative']),abs(wh-row['whitened']))
                decision_errors+=row['passed']!=bool(rel<=5e-4 and wh<=.1);analytic_count+=1
    assert analytic_diff<1e-9 and decision_errors==0 and direct_null==0
    # Four random complete fields, identical across methods/rules, no inverse fitting.
    rng=np.random.default_rng(2026091205);err=0;contractions=0
    for j in range(4):
        c=rng.normal(size=595)*.02
        for (method,q,n),g in groups.items():
            v=b.response(g,lambda rr,pp,tt:b.evaluate(c,rr,pp,tt))
            err=max(err,float(np.max(np.abs(v-new[f'{method}_q{q}_n{n}']@c))));contractions+=1
    assert err<1e-12
    return {'status':'POSTPLANNED_KNOT002_READBACK_PASS','original_status':done['status'],'physical_calls':0,'ledger_calls_checked':count,'ledger_events_checked':i+1,'quadrature_nodes_checked':node_checks,'basis_arm_checks':basis_count,'analytic_arm_checks':analytic_count,'gate_mismatches':decision_errors,'basis_metric_max_abs_difference':basis_diff,'analytic_metric_max_abs_difference':analytic_diff,'max_chart_area_abs_error':max_chart_area_error,'random_field_contractions':contractions,'random_contraction_max_abs_error':err,'direct_feature_whitened_max':direct_null,'source_hashes_unchanged':True,'scope':'New summation and saved-node auditing; no independent source physics or continuum certification.'}
if __name__=='__main__':
    val=run()
    with (RES/'POSTPLANNED_READBACK.json').open('x') as f:json.dump(val,f,indent=2,default=conv);f.write('\n')
    print(json.dumps(val,indent=2,default=conv))
