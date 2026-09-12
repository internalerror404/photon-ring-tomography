"""Postplanned replay using sum over pixel-major blocks, not producer bincount.
No new physical calls, no fitting, no changed source admission or thresholds.
"""
import json,os
from pathlib import Path
os.environ['OPENBLAS_NUM_THREADS']='1'
import numpy as np
import numerical_fields
ROOT=Path(__file__).resolve().parents[1];RES=ROOT/'results'

def run():
    specs=json.loads((RES/'NUMERICAL_PROBE_SPECS.json').read_text())
    original=json.loads((RES/'ANALYTIC_Q8_Q12.json').read_text())
    byid={(r['id'],r['arm']):r for r in original}
    groups={(q,n):np.load(RES/f'RAYS_q{q}_n{n}.npz',allow_pickle=False) for q in (8,12) for n in (0,1)}
    noise=json.loads((RES/'NOISE_CALIBRATION.json').read_text());sigma=noise['sigma300']
    std={n:np.tile(np.sqrt(groups[12,n]['weights'].reshape(64,144).sum(axis=1))*sigma,13) for n in (0,1)}
    max_metric_difference=0.;checked=0;gate_mismatches=0;min_value=float('inf');max_direct_feature=0.
    for spec in specs:
        fn=numerical_fields.make(spec);resp={}
        for (q,n),g in groups.items():
            tup=g['tuple'];obs=[]
            for to in np.arange(13)*2.:
                value=fn(tup[:,0],tup[:,1],to-tup[:,2]+100.)
                assert np.isfinite(value).all()
                min_value=min(min_value,float(value.min()))
                obs.append((g['weights']*tup[:,3]**3*value).reshape(64,q*q).sum(axis=1))
            resp[q,n]=np.array(obs).ravel()
            if spec['kind']=='feature' and n==0:max_direct_feature=max(max_direct_feature,float(np.max(np.abs(resp[q,n]/std[0]))))
        for arm,ns in [('direct',(0,)),('order1',(1,)),('labelled',(0,1))]:
            a=np.concatenate([resp[8,n] for n in ns]);b=np.concatenate([resp[12,n] for n in ns]);s=np.concatenate([std[n] for n in ns])
            rel=float(np.sqrt(np.dot(a-b,a-b))/max(np.sqrt(np.dot(b,b)),1e-15))
            white=float(np.sqrt(np.sum(((a-b)/s)**2)))
            row=byid[spec['id'],arm]
            max_metric_difference=max(max_metric_difference,abs(row['relative']-rel),abs(row['whitened']-white))
            gate_mismatches+=row['passed']!=(rel<=5e-4 and white<=.1);checked+=1
    assert checked==267 and gate_mismatches==0 and max_metric_difference<1e-10 and max_direct_feature==0
    return dict(status='POSTPLANNED_ANALYTIC_RESPONSE_REPLAY_PASS',numerical_fields=len(specs),arm_checks=checked,changed_gate_decisions=int(gate_mismatches),max_absolute_metric_difference=max_metric_difference,minimum_evaluated_source_probe_value=min_value,max_direct_feature_whitened=max_direct_feature,physical_calls=0,scope='Independent pixel-summation implementation; same source formulas and saved ray tuples. Not independent source-physics validation.')
if __name__=='__main__':
    value=run()
    with (RES/'POSTPLANNED_ANALYTIC_REPLAY.json').open('x') as f:json.dump(value,f,indent=2);f.write('\n')
    print(json.dumps(value,indent=2))
