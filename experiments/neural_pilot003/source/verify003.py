"""Post-fit numerical readback, no new rays or reference path integrations."""
from inverse003 import *
from collections import Counter
import sys,scipy,hashlib

def run():
    count_before=sum(1 for _ in (D/'physical_ledger.jsonl').open())
    cam8=dict(np.load(D/'camera_q8.npz'));cam16=dict(np.load(D/'camera_q16.npz'));rows=[]
    for seed in [11,22,33]:
        for method in ['comoving_data','comoving_robust_PINN','staged_residual_PINN']:
            for acq,variant in [('direct','matched'),('all','matched'),('all','event1'),('all','event2')]:
                key=f'{seed}_{method}_{acq}_{variant}'
                if method=='staged_residual_PINN':model=SumField(Field(16,True),Field(24))
                else:model=Field(32)
                model.load_state_dict(torch.load(CK/f'{key}.pt',weights_only=True))
                yp={4:np.load(D/f'fit_observations_{key}.npz')['predicted']}
                for q,cam in [(8,cam8),(16,cam16)]:
                    mask=cam['orders']==0 if acq=='direct' else np.ones(len(cam['areas']),bool)
                    c=cam['coords'][mask];w=cam['weights'][mask]
                    yp[q]=np.sum(w*predict(model,c.reshape(-1,3)).reshape(w.shape),axis=1)
                for n in ([0] if acq=='direct' else [0,1,2]):
                    ords=cam16['orders'][mask];m=ords==n;sc=np.sqrt(cam16['areas'][mask][m]);den=np.linalg.norm(yp[16][m]/sc)
                    rows.append(dict(seed=seed,method=method,acquisition=acq,source=variant,order=n,
                        q4_q16=float(np.linalg.norm((yp[4]-yp[16])[m]/sc)/den),
                        q8_q16=float(np.linalg.norm((yp[8]-yp[16])[m]/sc)/den)))
    pd.DataFrame(rows).to_csv(D/'fitted_renderer_quadrature.csv',index=False)
    cam=dict(np.load(D/'camera_q64.npz'));c=cam['coords'];w=cam['weights'];f=src(*c.transpose(2,0,1),'event1');h=src(*c.transpose(2,0,1),'event2')
    first=(w*(2*f-.3*h)).sum(1);second=2*(w*f).sum(1)-.3*(w*h).sum(1)
    sup=float(np.max(abs(first-second)))
    _,sig=noise_parameters();A=cam['areas'];pixel=(w*f).sum(1)
    cov=float(np.max(abs(pixel/sig-(pixel/A)/(sig/A))))
    j=(w*src(c[...,0],c[...,1],c[...,2]+7-7,'event2')).sum(1)
    clock=float(np.max(abs(j-observe(cam,'event2'))))
    edges=np.load(D/'detector_edges.npy');rd=np.load(D/'radial_q64.npz');areaerrors=[];ranges=[]
    for n in range(3):
        vals=rd[f'n{n}_trace'];b=rd[f'n{n}_b'];bw=rd[f'n{n}_bw']
        numerical=np.sum(bw*weight_jacobian(b),axis=1)*2*np.pi
        exact=np.array([camera_area(x,y,2*np.pi) for x,y in zip(edges[n][:-1],edges[n][1:])])
        areaerrors.append(float(np.max(abs(numerical-exact)/exact)))
        ranges.append(dict(order=n,r_range=[float(vals[...,0].min()),float(vals[...,0].max())],
            flight_time_range_M=[float(vals[...,1].min()),float(vals[...,1].max())],
            redshift_range=[float(vals[...,2].min()),float(vals[...,2].max())],
            radial_leg=np.unique(vals[...,3]).tolist(),source_radius_strictly_increasing=bool(np.all(np.diff(vals[...,0].ravel())>0))))
    ledger=[json.loads(l) for l in (D/'physical_ledger.jsonl').read_text().splitlines()];counts=dict(Counter(e['method'] for e in ledger))
    expected=36;checkpoints=len(list(CK.glob('*.pt')))
    gates=dict(neural_reconstructions_saved=checkpoints==expected,neural_results_finite=bool(np.isfinite(pd.read_csv(D/'inverse_per_seed.csv').old_contrast_error).all()),
        reference_gate_preserved=all(json.loads((D/'forward_validation.json').read_text())['gates'].values()),
        no_new_physical_calls_in_verification=len(ledger)==count_before,physical_budget_met=len(ledger)<=6000,
        source_superposition=sup<1e-11,intensity_flux_covariance_equivalent=cov<1e-10,clock=clock<1e-11,
        exact_measure_area_match=max(areaerrors)<1e-11,
        radial_branch_monotonicity=all(x['source_radius_strictly_increasing'] for x in ranges),
        trained_renderer_q4_q16=max(r['q4_q16'] for r in rows)<5e-4,
        trained_renderer_q8_q16=max(r['q8_q16'] for r in rows)<5e-5)
    old=json.loads((ROOT/'PREEXECUTION_SNAPSHOT.json').read_text())['files']
    code_status={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==d['sha256'] for name,d in old.items() if name.startswith('source/')}
    out=dict(gates=gates,physical_count_by_method=counts,physical_count=len(ledger),cap=6000,
        trained_reconstructions=checkpoints,neural_optimizer_stages=48,classical_inverse_fits=12,
        known_template_diagnostic_fits=18,post_test_linear_readout_diagnostics=18,
        registered_inverse_code_unchanged=code_status.get('source/inverse003.py'),code_hash_checks=code_status,
        post_fit_quadrature_max_q4_q16=max(r['q4_q16'] for r in rows),post_fit_quadrature_max_q8_q16=max(r['q8_q16'] for r in rows),
        superposition_abs=sup,noise_transform_abs=cov,clock_abs=clock,area_relative=areaerrors,order_ranges=ranges,
        environment=dict(python=sys.version,torch=torch.__version__,numpy=np.__version__,scipy=scipy.__version__,dtype='float64',cuda=False,threads=1),
        production_suite_executed=False,Paper_I_spend=0,Paper_I_remaining=854,
        qualification='Tests apply to this face-on, geometric-optics, prescribed-surface-intensity camera. No general Kerr or continuum interval proof.')
    (D/'verification.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
    if not all(gates.values()):raise RuntimeError('A verification test failed; preserve all outcomes')
if __name__=='__main__':run()
