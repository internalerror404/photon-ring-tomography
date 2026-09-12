"""Postplanned readback of existing CACHE_REBUILD_001; ZERO physical calls.

This audits saved arrays, ledger completeness, count accounting, and numeric
thresholds. It neither repairs a failed gate nor launches any reconstruction.
"""
import collections, hashlib, json, os
from pathlib import Path
os.environ['OPENBLAS_NUM_THREADS']='1'
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
RES=ROOT/'results'

def read(name):return json.loads((RES/name).read_text())
def run():
    completion=read('COMPLETION.json')
    tail='0'*64; pending=None;counts=collections.Counter();phases=collections.Counter();ray_lists=collections.defaultdict(list)
    with (ROOT/'attempts/physical_calls.jsonl').open() as f:
        for seq,line in enumerate(f):
            record=json.loads(line);ev=record['event']
            raw=json.dumps(ev,sort_keys=True,separators=(',',':'),allow_nan=False)
            assert record['sha256']==hashlib.sha256(raw.encode()).hexdigest()
            assert ev['previous_sha256']==tail and ev['sequence']==seq
            tail=record['sha256']
            if ev['kind']=='BEGIN':
                assert pending is None
                counts[ev['method']]+=1;phases[ev['phase']]+=1
                assert counts[ev['method']]==ev['ordinal']
                pending=ev
            elif ev['kind']=='END':
                assert pending is not None and pending['method']==ev['method'] and pending['ordinal']==ev['ordinal']
                if pending['phase'].startswith('cache_'):ray_lists[pending['phase']].append(ev['result'])
                pending=None
            else:raise AssertionError('unexpected error/unfinished ledger event')
    assert pending is None and tail==completion['ledger_tail_sha256']
    assert counts==dict(separated_quadrature=26752,compactified_ode=64)
    z=np.load(RES/'REBUILT_PHYSICAL_AND_OPERATOR_ARRAYS.npz',allow_pickle=False)
    tuple_replay={};ranges={}
    for q in (8,12):
        for n in (0,1):
            g=np.load(RES/f'RAYS_q{q}_n{n}.npz',allow_pickle=False)
            rows=ray_lists[f'cache_q{q}_order{n}']
            assert len(rows)==64*q*q
            t=np.array([r['tuple'] for r in rows]);weights=np.array([r['meta']['jac'] for r in rows])*g['chart_weights']
            assert np.array_equal(t,g['tuple']) and np.array_equal(t,z[f'tuple_q{q}_n{n}'])
            assert np.array_equal(weights,g['weights'])
            assert np.array_equal(np.array([r['leg'] for r in rows]),g['leg'])
            tuple_replay[f'q{q}_n{n}']=len(rows)
            ranges[f'q{q}_n{n}']=dict(radius_min=float(t[:,0].min()),radius_max=float(t[:,0].max()),delay_min=float(t[:,2].min()),delay_max=float(t[:,2].max()),tobs0_source_time_min=float(100-t[:,2].max()),tobs0_source_time_max=float(100-t[:,2].min()))
    w=np.load(RES/'REBUILT_SUPPORT_WEIGHTS.npz',allow_pickle=False)
    assert w['support'].shape==(15,32,64) and w['full_annulus'].shape==(15,32,64)
    assert np.all(w['support']>=0) and np.max(abs(w['support'].sum((1,2))-1))<=1e-12
    sigma=float(z['sigma300']); summary={};max_delta=0.;basis=read('BASIS_Q8_Q12.json')
    assert len(basis)==1785
    for arm,ns in [('direct',(0,)),('order1',(1,)),('labelled',(0,1))]:
        a=np.vstack([z[f'A_q8_n{n}'] for n in ns]);b=np.vstack([z[f'A_q12_n{n}'] for n in ns])
        std=np.concatenate([sigma*np.tile(np.sqrt(z[f'area_n{n}']),13) for n in ns])
        delta=a-b
        relative=np.sqrt(np.sum(delta*delta,axis=0))/np.maximum(np.sqrt(np.sum(b*b,axis=0)),1e-15)
        whitened=np.sqrt(np.sum((delta/std[:,None])**2,axis=0))
        reported=[r for r in basis if r['arm']==arm]
        assert len(reported)==595 and [x['column'] for x in reported]==list(range(595))
        re=np.array([r['relative'] for r in reported]);wh=np.array([r['whitened'] for r in reported])
        max_delta=max(max_delta,float(np.max(abs(re-relative))),float(np.max(abs(wh-whitened))))
        rf=relative>5e-4;wf=whitened>.1
        assert np.array_equal(np.array([r['passed'] for r in reported]),~(rf|wf))
        j=int(np.argmax(relative));k=int(np.argmax(whitened))
        summary[arm]=dict(checks=595,passed=int(np.sum(~(rf|wf))),failed=int(np.sum(rf|wf)),relative_failed=int(rf.sum()),whitened_failed=int(wf.sum()),both_failed=int((rf&wf).sum()),max_relative=float(relative[j]),max_relative_column=j,max_relative_column_indices=np.unravel_index(j,(5,7,17)),max_relative_column_q12_raw_norm=float(np.linalg.norm(b[:,j])),max_relative_column_whitened=float(whitened[j]),max_whitened=float(whitened[k]),max_whitened_column=k,max_whitened_column_indices=np.unravel_index(k,(5,7,17)))
    assert max_delta<=1e-12
    analytic=read('ANALYTIC_Q8_Q12.json');null=read('DIRECT_NULL.json')
    assert len(analytic)==267 and len(null)==64
    assert len({(r['id'],r['arm']) for r in analytic})==267
    assert all(r['passed']==(r['relative']<=5e-4 and r['whitened']<=.1) for r in analytic)
    assert sum(not r['passed'] for r in analytic)==completion['analytic_failures']
    assert sum(s['failed'] for s in summary.values())==completion['basis_failures']
    assert all(r['max_direct_q8']==r['max_direct_q12']==0 for r in null)
    checks=read('RAY_VALIDATION.json'); assert len(checks)==64
    assert np.array_equal(np.max([r['ode_error'] for r in checks],axis=0),completion['ray_validation_max'])
    assert sum(not r['passed'] for r in checks)==0
    hashfreeze=json.loads((ROOT/'provenance/SOURCE_FREEZE.json').read_text())
    assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in hashfreeze['sha256'].items())
    return dict(status='POSTPLANNED_SAVED_ARRAY_AUDIT_PASS',original_registered_status_unchanged=completion['status'],physical_calls_in_audit=0,ledger_events=seq+1,ledger_all_matched=True,ledger_tail=tail,counts=dict(counts),phase_counts=dict(phases),ray_array_replay=tuple_replay,ranges=ranges,basis_by_arm=summary,basis_metric_replay_max=max_delta,unique_failed_basis_columns=len({r['column'] for r in basis if not r['passed']}),analytic_arm_checks=267,analytic_passed=267,direct_null_feature_checks=64,all_direct_feature_responses_exact_zero=True,source_hashes_unchanged=True,limit='Analytic metric counters checked from saved records; this audit does not independently regenerate their 89 source responses.')
if __name__=='__main__':
    out=run()
    with (RES/'POSTPLANNED_READBACK.json').open('x') as f:json.dump(out,f,indent=2,default=lambda x:x.item() if isinstance(x,np.generic) else list(x));f.write('\n')
    print(json.dumps(out,indent=2,default=lambda x:x.item() if isinstance(x,np.generic) else list(x)))
